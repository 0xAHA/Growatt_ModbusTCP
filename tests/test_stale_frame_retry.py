"""A discarded frame is re-read, not written off for the poll (#433).

Since v1.3.7 a response whose length does not match the request is thrown away, because
callers write registers into the cache positionally and a mismatched frame lands every word
on an address it does not belong to. That guard is right and stays.

What it did *not* do is ask again. The block was simply lost for that poll, so on a gateway
that does this regularly the symptom is entities dropping to unavailable in ones and twos
while the connection itself looks fine.

A ShineWiFi-X measured it precisely (#433): 17 of 200 requests came back as somebody else's
answer, 8%. The reporter had already applied smaller blocks, a longer timeout and more delay
between requests - and the frames arriving were 125 and 20 registers long when nothing in
the poll asks for either, so they are not truncations of our reads. A PUSR bridge managed
roughly one poll in three (#360, #367).

`_validate_registers` drains the receive buffer when it discards, so the retry asks into a
clean stream rather than the misaligned one that produced the bad frame. That is the whole
reason a plain re-read is worth anything.

Two things it must not become:

  * a retry of a **refusal**. An `isError()` response returns None from the same helper, and
    several profiles probe ranges their hardware rejects on every single poll - retrying
    those would double the requests forever for nothing.
  * unbounded. A pathological gateway must not double every request in the poll indefinitely.
"""
from __future__ import annotations

import importlib

import pytest

_gm = importlib.import_module("growatt_under_test.growatt_modbus")

SharedModbusConnection = _gm.SharedModbusConnection


class _Response:
    def __init__(self, registers=None, error=False):
        self.registers = registers or []
        self._error = error

    def isError(self):  # noqa: N802 - pymodbus spelling
        return self._error


class _FakeClient:
    def __init__(self, script):
        self.script = list(script)
        self.reads = 0
        self.closes = 0
        self.flushes = 0

    def close(self):
        self.closes += 1

    def connect(self):
        return True

    def is_socket_open(self):
        return self.closes == 0

    def _next(self):
        self.reads += 1
        outcome = self.script.pop(0) if self.script else _Response([1, 2, 3, 4])
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    def read_input_registers(self, *args, **kwargs):
        return self._next()

    def read_holding_registers(self, *args, **kwargs):
        return self._next()


def _hub(script):
    hub = SharedModbusConnection(host="10.0.0.1", port=502)
    client = _FakeClient(script)
    hub._client = client
    hub._flush_receive_buffer = lambda: None      # no real socket to drain
    hub.begin_poll()
    return hub, client


# The reporter's signature: a 125-register frame answering a request for 8.
STALE = _Response(list(range(125)))
GOOD = _Response([10, 20, 30, 40, 50, 60, 70, 80])


def test_a_stale_frame_is_re_read_and_the_block_survives():
    """THE regression. Before this, the return was None and the block was lost."""
    hub, client = _hub([STALE, GOOD])

    registers = hub.read_input_registers(1, 8, slave_id=1)

    assert registers == [10, 20, 30, 40, 50, 60, 70, 80], (
        "the block was still written off after one bad frame"
    )
    assert client.reads == 2, "the read was not retried"


def test_the_frame_is_still_discarded_rather_than_salvaged():
    """The retry must not become a reason to trust the bad frame - the 125 registers in it
    belong to a different request and would land on the wrong addresses."""
    hub, client = _hub([STALE, GOOD])

    registers = hub.read_input_registers(1, 8, slave_id=1)

    assert registers is not None and len(registers) == 8
    assert 124 not in registers, "a word from the discarded frame reached the caller"
    assert hub.malformed_reads == 1, "the frame was not counted as malformed"


def test_two_bad_frames_in_a_row_give_up_rather_than_loop():
    """One retry per read. The second bad frame returns None, as before."""
    hub, client = _hub([STALE, STALE, GOOD])

    registers = hub.read_input_registers(1, 8, slave_id=1)

    assert registers is None
    assert client.reads == 2, "read more than twice for a single block"


def test_a_refusal_is_not_retried():
    """THE guard. An isError() response returns None from the same helper, and profiles
    that probe unsupported ranges hit it on every poll - retrying would double those
    requests permanently."""
    hub, client = _hub([_Response(error=True), GOOD])

    registers = hub.read_input_registers(1, 8, slave_id=1)

    assert registers is None
    assert client.reads == 1, "a protocol refusal was retried"
    assert hub.malformed_reads == 0


def test_a_clean_read_is_never_retried():
    hub, client = _hub([GOOD])

    assert hub.read_input_registers(1, 8, slave_id=1) is not None
    assert client.reads == 1


def test_holding_registers_get_the_same_treatment():
    """Both read paths carry their own copy of this logic - v1.3.5 shipped a fix to one of
    two fetch paths and the other raised on every poll."""
    hub, client = _hub([STALE, GOOD])

    registers = hub.read_holding_registers(1, 8, slave_id=1)

    assert registers == [10, 20, 30, 40, 50, 60, 70, 80]
    assert client.reads == 2


def test_the_buffer_is_drained_before_the_retry():
    """Without the flush the retry reads the next frame out of the same misaligned stream,
    which is how a stale stream stays stale."""
    hub, client = _hub([STALE, GOOD])
    order = []
    hub._flush_receive_buffer = lambda: order.append("flush")
    _original = hub._validate_registers

    def _watched(resp, start, count):
        result = _original(resp, start, count)
        order.append("validate")
        return result

    hub._validate_registers = _watched
    hub.read_input_registers(1, 8, slave_id=1)

    assert order[:2] == ["flush", "validate"], (
        f"the buffer was not drained before the re-read: {order}"
    )


def test_the_budget_bounds_a_pathological_gateway():
    """Every read bad, forever. The poll must stop re-reading rather than double itself
    without limit - but the ceiling has to be high enough for the gateways this exists for,
    which is why it is not the two-per-poll reset budget."""
    hub, client = _hub([])
    client.script = [STALE] * 400

    for _ in range(60):
        hub.read_input_registers(1, 8, slave_id=1)

    assert hub._stale_frame_retries_this_poll == _gm.MAX_STALE_FRAME_RETRIES_PER_POLL
    assert _gm.MAX_STALE_FRAME_RETRIES_PER_POLL >= 17, (
        "the budget is below the 17 stale frames per poll measured on the gateway that "
        "prompted this, so that reporter would still lose reads"
    )


def test_the_budget_is_separate_from_the_reset_budget():
    """Re-reading does not reset the connection, so it must not consume the allowance that
    exists to stop reset storms - two per poll would make this useless."""
    hub, client = _hub([STALE, GOOD])

    hub.read_input_registers(1, 8, slave_id=1)

    assert hub._recoveries_this_poll == 0, (
        "a stale-frame re-read consumed the transport-recovery budget, so two of them "
        "would block the reset+retry that #364 exists for"
    )
    assert _gm.MAX_STALE_FRAME_RETRIES_PER_POLL > hub._max_recoveries_per_poll


def test_the_budget_resets_between_polls():
    hub, client = _hub([])
    client.script = [STALE] * 400
    for _ in range(60):
        hub.read_input_registers(1, 8, slave_id=1)
    assert hub._stale_frame_retries_this_poll > 0

    hub.begin_poll()

    assert hub._stale_frame_retries_this_poll == 0


def test_the_counter_exists_before_any_poll_begins():
    """Reads happen outside a poll - the setup connection test and the device-identification
    reads both run before begin_poll(). An attribute created only by begin_poll() would
    raise AttributeError there."""
    hub = SharedModbusConnection(host="10.0.0.1", port=502)

    assert hasattr(hub, "_stale_frame_retries_this_poll")

    hub._client = _FakeClient([STALE, GOOD])
    hub._flush_receive_buffer = lambda: None
    assert hub.read_input_registers(1, 8, slave_id=1) is not None
