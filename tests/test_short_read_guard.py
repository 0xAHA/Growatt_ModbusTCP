"""Response-length validation on the shared connection hub (Issue #367).

The defect this covers produced the worst class of bug in this integration: not a
crash, not a missing sensor, but a *plausible-looking wrong number* written into Home
Assistant's long-term statistics.

Registers are written into the cache positionally — `regs[0]` is assumed to be the
block's start address, across 11 call sites. If a response is short, or is a stale
frame from a different request, the words still get written sequentially from
`start`, landing on addresses they never belonged to. The reporter decoded their own
corrupt values and found 0x33325354 = "32ST" — four characters of the inverter's
serial number — published as 85,893,614.8 W of AC power.

The non-shared path has checked response length since v1.3.5. The shared hub did not,
and because a hub is created for *every* TCP entry (not only genuinely shared ones),
the guard in practice only ever covered serial/RTU users.

Length is compared with != rather than <: a response longer than requested is an
equally strong sign of a misaligned frame.
"""
from __future__ import annotations

import importlib

import pytest

_gm = importlib.import_module("growatt_under_test.growatt_modbus")
SharedModbusConnection = _gm.SharedModbusConnection


class _Response:
    def __init__(self, registers=None, error=False):
        self.registers = [] if registers is None else registers
        self._error = error

    def isError(self):  # noqa: N802 - pymodbus spelling
        return self._error


class _FakeClient:
    def __init__(self, response):
        self.response = response

    def close(self):
        pass

    def connect(self):
        return True

    def is_socket_open(self):
        return True

    def read_input_registers(self, *args, **kwargs):
        return self.response

    def read_holding_registers(self, *args, **kwargs):
        return self.response


def _hub(response) -> SharedModbusConnection:
    hub = SharedModbusConnection(host="10.0.0.1", port=502)
    hub._client = _FakeClient(response)
    hub.begin_poll()
    return hub


def _count_flushes(hub, monkeypatch) -> list:
    calls = []
    monkeypatch.setattr(hub, "_flush_receive_buffer", lambda: calls.append(1))
    return calls


# --------------------------------------------------------------------------
# The exact-length case must still work
# --------------------------------------------------------------------------

@pytest.mark.parametrize("reader", ["read_input_registers", "read_holding_registers"])
def test_exact_length_response_is_returned(reader):
    hub = _hub(_Response([10, 20, 30, 40]))
    assert getattr(hub, reader)(100, 4, 1) == [10, 20, 30, 40]


# --------------------------------------------------------------------------
# Short reads — the truncation case
# --------------------------------------------------------------------------

@pytest.mark.parametrize("reader", ["read_input_registers", "read_holding_registers"])
def test_short_response_is_rejected(reader):
    """Two of four registers arrived. Salvaging them would map regs[0..1] onto the
    right addresses but leave the rest stale — and the caller cannot tell."""
    hub = _hub(_Response([10, 20]))
    assert getattr(hub, reader)(100, 4, 1) is None


@pytest.mark.parametrize("reader", ["read_input_registers", "read_holding_registers"])
def test_empty_response_is_rejected(reader):
    hub = _hub(_Response([]))
    assert getattr(hub, reader)(100, 4, 1) is None


# --------------------------------------------------------------------------
# Long reads — the stale/misaligned frame case
# --------------------------------------------------------------------------

@pytest.mark.parametrize("reader", ["read_input_registers", "read_holding_registers"])
def test_overlong_response_is_rejected(reader):
    """A response longer than requested cannot be a valid answer to this request.

    This is the case `< count` would have let through, and it is exactly the shape a
    stale frame from a *different* (larger) request takes.
    """
    hub = _hub(_Response([10, 20, 30, 40, 50, 60]))
    assert getattr(hub, reader)(100, 4, 1) is None


# --------------------------------------------------------------------------
# A misaligned stream must be drained, not inherited
# --------------------------------------------------------------------------

@pytest.mark.parametrize("reader", ["read_input_registers", "read_holding_registers"])
def test_length_mismatch_flushes_the_buffer(reader, monkeypatch):
    """Why the corrupt values repeated byte-for-byte rather than varying: the same
    stale bytes sat at the same offset on every poll."""
    hub = _hub(_Response([10, 20]))
    flushes = _count_flushes(hub, monkeypatch)

    getattr(hub, reader)(100, 4, 1)

    assert len(flushes) == 1


@pytest.mark.parametrize("reader", ["read_input_registers", "read_holding_registers"])
def test_good_read_does_not_flush(reader, monkeypatch):
    """The flush is a recovery action, not a per-read tax."""
    hub = _hub(_Response([10, 20, 30, 40]))
    flushes = _count_flushes(hub, monkeypatch)

    getattr(hub, reader)(100, 4, 1)

    assert flushes == []


# --------------------------------------------------------------------------
# Protocol refusals keep their existing behaviour (#360, #361)
# --------------------------------------------------------------------------

@pytest.mark.parametrize("reader", ["read_input_registers", "read_holding_registers"])
def test_error_response_still_returns_none_without_flushing(reader, monkeypatch):
    """An Illegal Address reply means the device answered and declined. Several
    profiles probe ranges their hardware rejects on every poll, so this path must
    stay cheap — no flush, no reset."""
    hub = _hub(_Response([], error=True))
    flushes = _count_flushes(hub, monkeypatch)

    assert getattr(hub, reader)(100, 4, 1) is None
    assert flushes == []


# --------------------------------------------------------------------------
# The regression, stated in the reporter's own terms
# --------------------------------------------------------------------------

# --------------------------------------------------------------------------
# The counters behind the gateway repair issue
# --------------------------------------------------------------------------
#
# tests/test_gateway_health.py pins the thresholds, but that mirrors the arithmetic. These
# assert the tallies actually move, which is what feeds it.

def test_good_read_increments_the_good_counter():
    hub = _hub(_Response([10, 20, 30, 40]))
    hub.read_input_registers(100, 4, 1)
    assert (hub.good_reads, hub.malformed_reads) == (1, 0)


def test_mismatched_read_increments_the_malformed_counter():
    hub = _hub(_Response([10, 20]))
    hub.read_input_registers(100, 4, 1)
    assert (hub.good_reads, hub.malformed_reads) == (0, 1)


def test_protocol_refusal_counts_as_neither():
    """An Illegal Address reply is the device declining, not the gateway misbehaving.
    Several profiles probe ranges their hardware rejects on every poll, so counting those
    as malformed would flag a healthy gateway on every affected model."""
    hub = _hub(_Response([], error=True))
    hub.read_input_registers(100, 4, 1)
    assert (hub.good_reads, hub.malformed_reads) == (0, 0)


def test_counters_are_per_hub_not_global():
    a = _hub(_Response([10, 20]))
    b = _hub(_Response([10, 20, 30, 40]))
    a.read_input_registers(100, 4, 1)
    b.read_input_registers(100, 4, 1)
    assert (a.good_reads, a.malformed_reads) == (0, 1)
    assert (b.good_reads, b.malformed_reads) == (1, 0)


def test_serial_number_frame_cannot_reach_the_register_cache():
    """0x33325354 = "32ST" — characters 9-12 of the reporter's serial number, which
    were published as 85,893,614.8 W of AC power.

    A stale frame carrying string-register content is rejected on length before any
    positional write can occur, so those words never reach the addresses that decode
    as power.
    """
    hub = _hub(_Response([0x3332, 0x5354]))  # "32" "ST"

    # A four-register power block was requested; two words came back.
    assert hub.read_input_registers(3004, 4, 1) is None
