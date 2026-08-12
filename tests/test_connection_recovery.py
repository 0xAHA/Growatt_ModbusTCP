"""Connection recovery behaviour for the shared Modbus hub.

Covers the logic added in PR #365 (Issue #364) with a fake transport, so the
distinction it draws is verified rather than only field-observed.

The rule under test: a block read can fail two structurally different ways, and only
one of them means the connection is broken.

  Transport failure   raised exception — socket dropped, frame corruption.
                      pymodbus's sync client does not notice, so the connection must
                      be reset and the read retried once.

  Protocol refusal    isError() — Illegal Function/Address. The device answered and
                      declined; the socket is healthy. Resetting here would be a
                      permanent tax on profiles that legitimately probe ranges their
                      hardware rejects on every poll (#360, #361).

A per-poll budget caps recoveries so a genuinely dead gateway cannot turn one poll
into a chain of TCP reconnects — the mechanism suspected of producing the
FAILED_UNLOAD state seen in #361.
"""
from __future__ import annotations

import importlib

import pytest

_gm = importlib.import_module("growatt_under_test.growatt_modbus")
SharedModbusConnection = _gm.SharedModbusConnection


class _Response:
    """Stand-in for a pymodbus response."""

    def __init__(self, registers=None, error=False):
        self.registers = registers or []
        self._error = error

    def isError(self):  # noqa: N802 - pymodbus spelling
        return self._error


class _FakeClient:
    """Scriptable pymodbus client.

    `script` is a list of outcomes consumed per read: an Exception instance is
    raised, anything else is returned.
    """

    def __init__(self, script):
        self.script = list(script)
        self.closes = 0
        self.connects = 0
        self.reads = 0

    # -- lifecycle ---------------------------------------------------------
    def close(self):
        self.closes += 1

    def connect(self):
        self.connects += 1
        return True

    def is_socket_open(self):
        # False after a reset, so ensure_connected() performs a real reconnect.
        return self.closes == 0

    # -- reads -------------------------------------------------------------
    def _next(self):
        self.reads += 1
        outcome = self.script.pop(0) if self.script else _Response([1, 2, 3])
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    def read_input_registers(self, *args, **kwargs):
        return self._next()

    def read_holding_registers(self, *args, **kwargs):
        return self._next()

    # -- writes ------------------------------------------------------------
    # Consume the same script, so a test can say "fail once, then succeed" for a write
    # exactly as it does for a read.
    def write_register(self, *args, **kwargs):
        return self._next()

    def write_registers(self, *args, **kwargs):
        return self._next()


def _hub(script) -> tuple[SharedModbusConnection, _FakeClient]:
    hub = SharedModbusConnection(host="10.0.0.1", port=502)
    client = _FakeClient(script)
    hub._client = client
    hub.begin_poll()
    return hub, client


# --------------------------------------------------------------------------
# Transport failures — must reset and retry
# --------------------------------------------------------------------------

def test_transport_error_resets_and_retries_once():
    """Regression guard for Issue #364.

    The failure mode: pymodbus reconnects on the NEXT call rather than the failed
    one, so without an explicit reset the affected block stays empty while later
    blocks in the same poll succeed — a partially-successful poll that never
    triggers the poll-level recovery from #354.
    """
    hub, client = _hub([ConnectionError("socket closed"), _Response([7, 8])])
    result = hub.read_input_registers(0, 2, slave_id=1)

    assert result == [7, 8], "retry after reset should return the data"
    assert client.closes == 1, "connection should have been reset exactly once"
    assert client.reads == 2, "one failed read, one retry"


def test_transport_error_on_retry_gives_up_without_a_second_reset():
    hub, client = _hub([ConnectionError("down"), ConnectionError("still down")])
    assert hub.read_input_registers(0, 2, slave_id=1) is None
    assert client.closes == 1, "only the first attempt may trigger a reset"
    assert client.reads == 2


def test_holding_register_reads_recover_the_same_way():
    hub, client = _hub([ConnectionError("socket closed"), _Response([5])])
    assert hub.read_holding_registers(30000, 1, slave_id=1) == [5]
    assert client.closes == 1


# --------------------------------------------------------------------------
# Protocol refusals — must NOT reset
# --------------------------------------------------------------------------

def test_protocol_error_returns_none_without_resetting():
    """Illegal Function means the device replied. Resetting would be a permanent
    tax on TL-XH2 and SPA setups, which reject whole ranges on every poll.
    """
    hub, client = _hub([_Response(error=True)])
    assert hub.read_input_registers(3000, 10, slave_id=1) is None
    assert client.closes == 0, "a protocol refusal must not reset the connection"
    assert client.reads == 1, "and must not be retried"


def test_repeated_protocol_errors_never_reset():
    """A profile probing a rejected range does this every single poll."""
    hub, client = _hub([_Response(error=True) for _ in range(20)])
    for _ in range(20):
        hub.read_input_registers(3000, 10, slave_id=1)
    assert client.closes == 0
    assert client.reads == 20


# --------------------------------------------------------------------------
# Recovery budget
# --------------------------------------------------------------------------

def test_recovery_budget_caps_resets_within_one_poll():
    """A dead gateway must not produce one reconnect per block."""
    hub, client = _hub([ConnectionError("dead")] * 40)
    for _ in range(10):
        hub.read_input_registers(0, 2, slave_id=1)
    assert client.closes <= hub._max_recoveries_per_poll, (
        f"expected at most {hub._max_recoveries_per_poll} resets, got {client.closes}"
    )


def test_begin_poll_restores_the_budget():
    """Each poll gets a fresh allowance; the budget must not leak across cycles."""
    hub, client = _hub([ConnectionError("dead")] * 40)
    for _ in range(10):
        hub.read_input_registers(0, 2, slave_id=1)
    first = client.closes

    hub.begin_poll()
    for _ in range(10):
        hub.read_input_registers(0, 2, slave_id=1)

    assert client.closes > first, "begin_poll() should re-arm the recovery budget"


def test_successful_reads_consume_no_budget():
    hub, client = _hub([_Response([1])] * 10)
    for _ in range(10):
        hub.read_input_registers(0, 1, slave_id=1)
    assert hub._recoveries_this_poll == 0
    assert client.closes == 0


# --------------------------------------------------------------------------
# Writes must recover the same way reads do (#375)
# --------------------------------------------------------------------------
#
# They did not until v1.6.x. Reads reset and retried inside the same call; writes dropped
# the socket and returned False, leaving the *next* call to reconnect. On a datalogger
# that reaps idle sockets that is a visible difference: the first read after a drop
# succeeds silently, the first write after a drop fails and the control does not take
# effect. Reported by @alanmk on #358 and split out as #375.


@pytest.mark.parametrize("method,args", [
    ("write_register", (1092, 1)),
    ("write_registers", (3038, [512, 286])),
])
def test_write_transport_error_resets_and_retries_once(method, args):
    hub, client = _hub([ConnectionError("broken pipe"), _Response()])
    assert getattr(hub, method)(*args, slave_id=1) is True, (
        "a write that fails on transport should reconnect and succeed on the retry"
    )
    assert client.closes == 1, "the failed attempt should have reset the connection"
    assert client.reads == 2, "the write should have been attempted twice"


@pytest.mark.parametrize("method,args", [
    ("write_register", (1092, 1)),
    ("write_registers", (3038, [512, 286])),
])
def test_write_transport_error_on_retry_gives_up(method, args):
    """One reset per write, not a loop. A genuinely dead gateway must not turn a single
    write into a chain of reconnects."""
    hub, client = _hub([ConnectionError("broken pipe"), ConnectionError("still broken")])
    assert getattr(hub, method)(*args, slave_id=1) is False
    assert client.closes >= 1
    assert client.reads == 2, "no third attempt"


@pytest.mark.parametrize("method,args", [
    ("write_register", (1090, 40)),
    ("write_registers", (1090, [40])),
])
def test_write_protocol_error_does_not_retry(method, args):
    """A register-level refusal arrives as an isError() response, not an exception.

    Retrying achieves nothing — the register will refuse again — and on the addresses
    known to reject writes (#371, exception 2 on MOD holding 1090/1092) it would double
    the log volume for no benefit.
    """
    hub, client = _hub([_Response(error=True)])
    assert getattr(hub, method)(*args, slave_id=1) is False
    assert client.closes == 0, "a protocol refusal must not reset the connection"
    assert client.reads == 1, "a protocol refusal must not be retried"


def test_write_recovery_shares_the_poll_budget():
    """Writes draw on the same per-poll recovery budget as reads, so a failing link
    cannot spend it twice over."""
    hub, client = _hub([ConnectionError("a"), _Response(),
                        ConnectionError("b"), _Response(),
                        ConnectionError("c")])
    assert hub.write_register(3049, 1, slave_id=1) is True
    assert hub.write_register(3049, 1, slave_id=1) is True
    # Budget is 2 per poll; the third failure has none left and must not reset again.
    closes_before = client.closes
    assert hub.write_register(3049, 1, slave_id=1) is False
    assert client.closes == closes_before + 1, (
        "with the budget spent the write should disconnect once and give up, not recover"
    )


def test_write_without_a_client_returns_false():
    hub = SharedModbusConnection(host="10.0.0.1", port=502)
    hub._client = None
    assert hub.write_register(1, 1, slave_id=1) is False
    assert hub.write_registers(1, [1], slave_id=1) is False


# --------------------------------------------------------------------------
# Guards
# --------------------------------------------------------------------------

def test_read_without_a_client_returns_none():
    hub = SharedModbusConnection(host="10.0.0.1", port=502)
    hub._client = None
    assert hub.read_input_registers(0, 1, slave_id=1) is None


@pytest.mark.parametrize("attr", ["_recoveries_this_poll", "_max_recoveries_per_poll"])
def test_budget_attributes_exist(attr):
    """Pin the interface PR #365 introduced, so a refactor cannot quietly drop it."""
    assert hasattr(SharedModbusConnection(host="h", port=1), attr)
