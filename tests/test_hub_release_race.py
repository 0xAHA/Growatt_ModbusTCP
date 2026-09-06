"""A released hub must not leave a connection behind (the 2026-09-06 outage).

The reference gateway **serialises a second TCP client for about 30 seconds**:
a read that normally takes 300 ms took 30,338 ms while another client held a
connection. That is longer than the read timeout, so a second connection does
not merely slow things down — it manufactures transport errors.

Which matters because of how the integration used to tear a hub down:

    release_ref()  closed the socket and set _client = None, with no lock,
                   while a poll was still running in an executor thread that
                   nothing cancels

    the orphaned poll then hit a transport error, called reset() ->
    ensure_connected(), found _client None, and BUILT A NEW CLIENT — a socket
    owned by a hub already dropped from the registry

    meanwhile the reload created the new hub, which opened its own socket

Two live clients, 30 s stalls, timeouts read as transport errors, each handled
by reconnecting. The cascade never ended: every outage that day began at a
restart or a reload, and only disabling the integration ever cleared it.

The fix is three small rules, one test each below.
"""
from __future__ import annotations

import importlib
import threading
import time

import pytest

_gm = importlib.import_module("growatt_under_test.growatt_modbus")
SharedModbusConnection = _gm.SharedModbusConnection


class _Response:
    """Stand-in for a pymodbus response, as tests/test_connection_recovery.py uses."""

    def __init__(self, registers=None, error=False):
        self.registers = registers or []
        self._error = error

    def isError(self):  # noqa: N802 - pymodbus spelling
        return self._error


class _FakeClient:
    def __init__(self):
        self.closes = 0
        self.connects = 0

    def close(self):
        self.closes += 1

    def connect(self):
        self.connects += 1
        return True

    def is_socket_open(self):
        return self.closes == 0


def _hub():
    hub = SharedModbusConnection(host="10.0.0.1", port=502)
    hub._client = _FakeClient()
    hub.acquire_ref()
    return hub


# ---------------------------------------------------------------------------
# 1. A released hub never builds another client
# ---------------------------------------------------------------------------

def test_a_released_hub_refuses_to_connect():
    """The orphaned poll's next move was to open a socket nobody owned."""
    hub = _hub()
    hub.release_ref()

    assert hub.ensure_connected() is False
    assert hub._client is None


def test_a_released_hub_builds_no_client_even_when_asked_repeatedly():
    hub = _hub()
    hub.release_ref()

    for _ in range(5):
        assert hub.ensure_connected() is False
    assert hub._client is None


def test_releasing_closes_the_socket():
    hub = _hub()
    client = hub._client

    hub.release_ref()

    assert client.closes == 1
    assert hub._client is None


def test_a_hub_with_other_users_is_not_torn_down():
    """Refcounting still governs: two coordinators, one release, still alive."""
    hub = _hub()
    hub.acquire_ref()

    hub.release_ref()

    assert hub._released is False
    assert hub._client is not None


# ---------------------------------------------------------------------------
# 2. Teardown waits for the poll rather than racing it
# ---------------------------------------------------------------------------

def test_release_waits_for_a_poll_that_holds_the_bus():
    """The socket must be closed BETWEEN reads, not underneath one."""
    hub = _hub()
    client = hub._client
    holding = threading.Event()
    release_may_proceed = threading.Event()
    closed_during_poll = []

    def poll():
        with hub._lock:
            holding.set()
            release_may_proceed.wait(2)
            # Whatever release_ref() did, it must not have closed our socket yet.
            closed_during_poll.append(client.closes)

    worker = threading.Thread(target=poll)
    worker.start()
    holding.wait(2)

    releaser = threading.Thread(target=lambda: hub.release_ref(lock_timeout=5))
    releaser.start()
    time.sleep(0.2)                     # give release_ref a chance to race us
    release_may_proceed.set()
    worker.join(3)
    releaser.join(3)

    assert closed_during_poll == [0], "the socket was closed under a running poll"
    assert client.closes == 1
    assert hub._client is None


def test_release_does_not_block_forever_on_a_long_poll():
    """A poll may legitimately hold the bus for tens of seconds. Unload must not
    hang on it — the released flag is what makes leaving the socket safe."""
    hub = _hub()
    started = threading.Event()

    def hog():
        with hub._lock:
            started.set()
            time.sleep(1.5)

    worker = threading.Thread(target=hog)
    worker.start()
    started.wait(2)

    began = time.monotonic()
    hub.release_ref(lock_timeout=0.2)
    took = time.monotonic() - began

    assert took < 1.0, f"release blocked for {took:.2f}s"
    assert hub._released is True          # the poll can no longer reconnect
    worker.join(3)


def test_end_poll_closes_a_hub_released_mid_poll():
    """The first safe moment to close an orphaned socket is when its poll ends."""
    hub = _hub()
    client = hub._client
    hub._released = True                  # as release_ref() would leave it

    hub.end_poll()

    assert client.closes == 1
    assert hub._client is None


# ---------------------------------------------------------------------------
# 3. A reset leaves the peer a moment of quiet
# ---------------------------------------------------------------------------

def test_a_reconnect_inside_the_quiet_window_is_refused_not_delayed():
    """REFUSED, never slept on. ensure_connected() runs with the hub lock held for
    the whole poll, so waiting here would block every other user of the gateway —
    a second config entry's poll, and any user-initiated write. Failing fast gives
    the bus back and the coordinator retries on its next cycle, which is the same
    spacing without the blocking."""
    hub = _hub()
    client = hub._client
    hub.reset("first — this one is allowed through, see #364")
    connects_before = client.connects

    hub.reset("second consecutive failure")

    began = time.monotonic()
    assert hub.ensure_connected() is False
    elapsed = time.monotonic() - began

    assert elapsed < 0.1, f"ensure_connected blocked for {elapsed:.2f}s"
    assert client.connects == connects_before, "it opened a socket anyway"


def test_the_window_expires_and_the_reconnect_then_proceeds():
    hub = _hub()
    hub.reset("first")
    hub.reset("second")
    hub._reset_at -= _gm.RECONNECT_QUIET_BASE_SECONDS + 0.01   # window has passed

    assert hub.ensure_connected() is True


def test_the_first_reset_still_reconnects_immediately():
    """#364's recovery must survive this change: a single transport error is a
    silently-dropped socket, and resetting and retrying once is the cheap fix."""
    hub = _hub()
    hub.reset("one transport error")

    assert hub._quiet_period() == 0.0
    assert hub.ensure_connected() is True


def test_a_connect_with_no_preceding_reset_is_immediate():
    """The quiet window is a response to failure, not a tax on every poll."""
    hub = _hub()
    hub._client.close()                   # socket shut, but nothing was reset

    began = time.monotonic()
    assert hub.ensure_connected() is True
    assert time.monotonic() - began < 0.5


def test_a_write_refused_by_the_window_says_so():
    """"Could not connect" would send someone to check the wiring. This is a
    "try again shortly" failure and should read like one."""
    hub = _hub()
    hub.reset("first")
    hub.reset("second")

    reason = hub.connect_refusal_reason()

    assert "quiet period" in reason
    assert "retry in" in reason


def test_a_released_hub_says_that_instead():
    hub = _hub()
    hub.release_ref()

    assert "released" in hub.connect_refusal_reason()


# --- the wait escalates while failures continue ----------------------------

def test_the_wait_doubles_for_each_consecutive_reset():
    """A fixed short wait cannot outlast a peer that stalls a second client for
    tens of seconds: the reconnects keep landing inside the stall. Doubling gets
    past it within a few attempts."""
    hub = _hub()
    base = _gm.RECONNECT_QUIET_BASE_SECONDS

    waits = []
    for _ in range(5):
        hub.reset("still failing")
        waits.append(hub._quiet_period())

    # The first reset is #364's immediate retry and is not delayed at all.
    assert waits == [0.0, base, base * 2, base * 4, base * 8]


def test_the_wait_is_capped():
    """Bounded, so a dead gateway cannot push a poll out to minutes."""
    hub = _hub()
    for _ in range(20):
        hub.reset("still failing")

    assert hub._quiet_period() == _gm.RECONNECT_QUIET_MAX_SECONDS


def test_a_successful_read_starts_the_escalation_over():
    """Keyed to a successful READ rather than a successful connect. In the failure
    this addresses, connects succeed and reads time out — so clearing on connect
    would reset the escalation on every attempt and never escalate at all."""
    hub = _hub()
    hub.reset("first")
    hub.reset("second")
    hub.reset("third")
    assert hub._quiet_period() > _gm.RECONNECT_QUIET_BASE_SECONDS

    hub._validate_registers(_Response([1, 2, 3]), start=0, count=3)

    assert hub._consecutive_resets == 0
    # Fully cleared: the next single failure is #364's immediate retry again.
    assert hub._quiet_period() == 0.0


def test_a_successful_connect_alone_does_not_reset_the_escalation():
    hub = _hub()
    hub.reset("first")
    hub.reset("second")
    hub._reset_at -= _gm.RECONNECT_QUIET_MAX_SECONDS          # let it through

    assert hub.ensure_connected() is True

    assert hub._consecutive_resets == 2


# --- the poll must actually call end_poll() --------------------------------

def test_the_shared_poll_closes_a_released_hub_in_its_finally():
    """end_poll() is what closes a hub released mid-poll — release_ref() only
    marks it and takes the lock best-effort. If the shared poll never calls
    end_poll(), a hub released while a poll held the bus is never closed by
    anything, and the socket outlives its owner.

    Checked against the source because reaching _fetch_data_shared() needs a
    coordinator and a running Home Assistant, while the guarantee is one call in
    one finally block. Read as text rather than parsed: coordinator.py uses a
    PEP 695 `type` alias, so ast.parse() raises on Python < 3.12.
    """
    from pathlib import Path

    source = (Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
              / "coordinator.py").read_text(encoding="utf-8")

    marker = "def _fetch_data_shared"
    assert marker in source, "_fetch_data_shared has been renamed"
    body = source[source.index(marker):]
    end = body.find("\n    def ", 1)
    body = body[:end] if end != -1 else body

    assert "finally:" in body, "_fetch_data_shared has no finally block"
    finally_block = body[body.index("finally:"):]

    assert "end_poll()" in finally_block, (
        "the shared poll never calls hub.end_poll() in its finally; a hub "
        "released mid-poll would never be closed")
    assert "release()" in finally_block, (
        "the shared poll must still release the bus lock")
