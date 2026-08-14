"""A multi-register control must hold the bus for its whole sequence (#331).

Some controls are not one register. The WIT VPP mode select writes six to eight — control
authority, AC charge enable, a TOU period, the period count, remote enable, the power
setpoint — and they only mean anything together.

Each write used to take the shared lock separately, from its own executor job, while a
poll holds that same lock for its entire duration. So a poll could land in the middle of
the sequence, and any single acquisition could time out after `SHARED_LOCK_TIMEOUT`,
leaving the inverter with control authority granted and no power setpoint, or a TOU period
with no count. Several branches `return` having already written 30100.

A half-applied VPP command is worse than one that plainly failed. It is also what drove a
user to bypass the integration and write an external MQTT proxy instead, reporting "locks
and timeouts and no usable shared connection".

Tested against the real `SharedModbusConnection` and a real `GrowattModbus` with a counting
fake, not by reading the source — the lesson of #374, where a test asserting a declaration
passed while the defect shipped.
"""
from __future__ import annotations

import importlib
import threading

import pytest

_gm = importlib.import_module("growatt_under_test.growatt_modbus")
SharedModbusConnection = _gm.SharedModbusConnection
GrowattModbus = _gm.GrowattModbus
ModbusWriteError = _gm.ModbusWriteError


class _Response:
    def isError(self):  # noqa: N802 - pymodbus spelling
        return False


class _CountingClient:
    """Counts writes and reports the socket as permanently healthy."""

    def __init__(self):
        self.writes = 0

    def close(self):
        pass

    def connect(self):
        return True

    def is_socket_open(self):
        return True

    def write_register(self, *args, **kwargs):
        self.writes += 1
        return _Response()

    def write_registers(self, *args, **kwargs):
        self.writes += 1
        return _Response()


def _client_with_hub():
    """A GrowattModbus wired to a shared hub."""
    hub = SharedModbusConnection(host="10.0.0.1", port=502)
    transport = _CountingClient()
    hub._client = transport

    client = GrowattModbus(connection_type="tcp", host="10.0.0.1", port=502, slave_id=1)
    client._shared_conn = hub
    return client, hub, transport


def _poll_can_get_in(hub, timeout=0.3) -> bool:
    """Could a poll take the bus right now?

    Asked from another thread on purpose. The hub lock is reentrant, so the writing
    thread can always re-enter it — the question that matters is whether a *different*
    thread, i.e. the poll, can slip in.

    An earlier version of these tests counted acquisitions instead and asserted one per
    sequence. That was wrong: the batch takes the lock, then each write re-enters it, so
    the count is N+1 while the bus is never actually released. Counting measured a proxy;
    exclusion is the property the bug was about.
    """
    result = []

    def _try():
        got = hub._lock.acquire(timeout=timeout)
        result.append(got)
        if got:
            hub._lock.release()

    t = threading.Thread(target=_try, daemon=True)
    t.start()
    t.join(timeout=timeout + 2)
    return bool(result and result[0])


# ---------------------------------------------------------------------------
# The behaviour the bug was about
# ---------------------------------------------------------------------------

def test_a_poll_cannot_interleave_inside_a_batch():
    client, hub, transport = _client_with_hub()
    midpoint = {}

    with client.write_batch("test sequence"):
        client.write_register(30100, 1)
        client.write_register(30410, 1)
        # Exactly where the damage happened: authority granted, setpoint not yet written.
        midpoint["poll_got_in"] = _poll_can_get_in(hub)
        client.write_register(30407, 1)
        client.write_register(30409, 100)

    assert transport.writes == 4, "all four writes should have reached the transport"
    assert midpoint["poll_got_in"] is False, (
        "a poll took the bus midway through the sequence — that is the window in which "
        "the inverter is left with control authority and no power setpoint (#331)"
    )
    assert _poll_can_get_in(hub) is True, "the bus should be free once the batch ends"


def test_without_a_batch_a_poll_can_interleave():
    """The contrast, so the test above cannot pass trivially — and a statement of what
    the old code did on every multi-register control."""
    client, hub, _ = _client_with_hub()

    client.write_register(30100, 1)
    assert _poll_can_get_in(hub) is True, (
        "between two unbatched writes the bus is free, which is correct for independent "
        "single-register controls and fatal for a sequence"
    )
    client.write_register(30407, 1)


def test_nested_acquisition_does_not_deadlock():
    """Guards the Lock -> RLock change. With a plain Lock this hangs forever rather than
    failing, so it is worth pinning explicitly."""
    client, hub, _ = _client_with_hub()

    finished = threading.Event()

    def _run():
        with client.write_batch("nested"):
            client.write_register(30100, 1)
        finished.set()

    worker = threading.Thread(target=_run, daemon=True)
    worker.start()
    worker.join(timeout=5)

    assert finished.is_set(), (
        "a write inside write_batch() deadlocked against the batch's own lock — the hub "
        "lock must be reentrant"
    )


def test_the_bus_is_released_when_a_write_inside_the_batch_raises():
    """A leaked lock would stall every subsequent poll on this connection, which is worse
    than the bug this method exists to prevent."""
    client, hub, _ = _client_with_hub()

    class _Boom(Exception):
        pass

    with pytest.raises(_Boom):
        with client.write_batch("failing sequence"):
            raise _Boom()

    # Acquirable again from this thread's perspective only if it was truly released;
    # a non-blocking acquire from another thread proves it.
    freed = []

    def _try():
        got = hub._lock.acquire(timeout=2)
        freed.append(got)
        if got:
            hub._lock.release()

    t = threading.Thread(target=_try, daemon=True)
    t.start()
    t.join(timeout=5)

    assert freed == [True], "the bus was not released after the batch raised"


def test_batch_is_a_no_op_without_a_shared_connection():
    """Direct connections own their socket outright — there is nothing to contend with,
    and the batch must not require a hub to exist."""
    client = GrowattModbus(connection_type="tcp", host="10.0.0.1", port=502, slave_id=1)
    client._shared_conn = None

    entered = False
    with client.write_batch("no hub"):
        entered = True
    assert entered


def test_a_busy_bus_fails_the_batch_before_any_write_lands():
    """The point of failing at the top: if the bus cannot be had, nothing is written, so
    there is no partial state to unpick."""
    client, hub, transport = _client_with_hub()

    holder_ready = threading.Event()
    release = threading.Event()

    def _hold():
        hub._lock.acquire()
        holder_ready.set()
        release.wait(timeout=10)
        hub._lock.release()

    t = threading.Thread(target=_hold, daemon=True)
    t.start()
    holder_ready.wait(timeout=5)

    import growatt_under_test.const as _const
    original = _const.SHARED_LOCK_TIMEOUT
    _const.SHARED_LOCK_TIMEOUT = 1
    try:
        with pytest.raises(ModbusWriteError):
            with client.write_batch("contended"):
                client.write_register(30100, 1)
    finally:
        _const.SHARED_LOCK_TIMEOUT = original
        release.set()
        t.join(timeout=5)

    assert transport.writes == 0, (
        "a batch that could not take the bus still wrote to the inverter — the whole "
        "point is that it fails before touching anything"
    )
