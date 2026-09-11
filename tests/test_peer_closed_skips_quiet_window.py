"""A peer that hangs up is reconnected to at once, not backed off from (#433).

v1.10.0 added a post-failure quiet window to the shared connection: after consecutive
failures the hub refuses to reopen the socket for 2 s, doubling to 32 s. It exists for a
gateway that serialises clients, where opening another socket queues behind whatever is
already stalling it and makes things worse.

It does not distinguish *why* the last attempt failed, and there are two different faults:

    the peer stopped answering   -> backing off is right; this is what the window is for
    the peer closed the socket   -> there is nothing to back off from. pymodbus calls
                                    close() before raising, so the transport is gone, and
                                    the only way back is a new connection

Treating the second as the first is a regression. A ShineWiFi-X that drops its end regularly
had every recovery refused from the second consecutive failure onward, so a blip that used to
be recovered mid-poll took the entities offline instead. The reporter's debug trace, which is
what this file is built from:

    08:11:51 read_input_registers(0, 7) transport error ... Connection unexpectedly closed
             ... - resetting and retrying once
             not reconnecting yet: 2.0s of the post-failure quiet window remain (2 reset(s))
             not reconnecting yet: 4.0s of the post-failure quiet window remain (3 reset(s))
             Failed to read register block (0-6)
             Resetting connection: poll returned no data
             -> Inverter unavailable

Three minutes earlier the same fault on a different register *did* recover, because the
counter was still at one and the first reset is deliberately exempt. So the recovery worked
right up until it was needed twice.

The exemption is typed, not matched on the message: pymodbus raises `ConnectionException`
for a closed socket and `ModbusIOException` for a timeout. The per-poll recovery budget still
bounds how many reconnects a poll can make, so exempting the window cannot produce a storm.
"""
from __future__ import annotations

import importlib

import pytest

_gm = importlib.import_module("growatt_under_test.growatt_modbus")

SharedModbusConnection = _gm.SharedModbusConnection

try:
    from pymodbus.exceptions import ConnectionException, ModbusIOException
except ImportError:                      # pymodbus is not installed in the HA-free suite
    ConnectionException = ModbusIOException = None

# The reporter's exact wording, as pymodbus builds it.
CLOSED_MESSAGE = (
    "ModbusTcpClient(192.168.178.10:502): Connection unexpectedly closed "
    "0.412 seconds into read of 8 bytes without response from device before it closed "
    "connection"
)


class _Response:
    def __init__(self, registers=None):
        self.registers = registers or []

    def isError(self):  # noqa: N802 - pymodbus spelling
        return False


class _FakeClient:
    """Raises the scripted failure on the first read, then answers normally."""

    def __init__(self, failure):
        self.failure = failure
        self.reads = 0
        self.closes = 0
        self.connects = 0

    def close(self):
        self.closes += 1

    def connect(self):
        self.connects += 1
        return True

    def is_socket_open(self):
        return self.closes == 0

    def _next(self):
        self.reads += 1
        if self.reads == 1 and self.failure is not None:
            raise self.failure
        return _Response([1, 2, 3, 4, 5, 6, 7])

    def read_input_registers(self, *args, **kwargs):
        return self._next()

    def read_holding_registers(self, *args, **kwargs):
        return self._next()


def _hub(failure, consecutive_resets: int):
    """A hub already carrying `consecutive_resets` failures, as his was."""
    hub = SharedModbusConnection(host="192.168.178.10", port=502)
    client = _FakeClient(failure)
    hub._client = client
    hub._flush_receive_buffer = lambda: None
    hub.begin_poll()
    hub._consecutive_resets = consecutive_resets
    return hub, client


# --------------------------------------------------------------------------
# Classifying the failure
# --------------------------------------------------------------------------

@pytest.mark.skipif(ConnectionException is None, reason="pymodbus not installed")
def test_a_closed_connection_is_recognised():
    assert _gm._peer_closed_the_connection(ConnectionException(CLOSED_MESSAGE))


@pytest.mark.skipif(ModbusIOException is None, reason="pymodbus not installed")
def test_a_timeout_is_not():
    """THE guard. This is the fault the quiet window exists for, and it must keep it."""
    assert not _gm._peer_closed_the_connection(
        ModbusIOException("No response received after 3 retries")
    )


def test_the_socket_level_errors_count_as_closed():
    for err in (ConnectionResetError(), BrokenPipeError(), ConnectionAbortedError()):
        assert _gm._peer_closed_the_connection(err), type(err).__name__


def test_an_unrelated_error_is_not_treated_as_closed():
    assert not _gm._peer_closed_the_connection(ValueError("something else"))
    assert not _gm._peer_closed_the_connection(TimeoutError())


# --------------------------------------------------------------------------
# What reset() does with it
# --------------------------------------------------------------------------

def test_a_closed_peer_leaves_no_quiet_window():
    hub = SharedModbusConnection(host="192.168.178.10", port=502)
    hub._client = _FakeClient(None)
    hub._consecutive_resets = 3          # deep into escalation

    hub.reset("transport error during block read", peer_closed=True)

    assert hub._quiet_remaining() == 0.0, (
        "a closed socket still opens a quiet window, so the reconnect that is the only "
        "way back is refused"
    )


def test_a_closed_peer_does_not_escalate_the_window():
    """Repeated hang-ups are not evidence the gateway is overloaded, which is the state
    the escalation meters. If they counted, a later genuine stall would start at 32s."""
    hub = SharedModbusConnection(host="192.168.178.10", port=502)
    hub._client = _FakeClient(None)

    for _ in range(5):
        hub.reset("transport error during block read", peer_closed=True)

    assert hub._consecutive_resets == 0


def test_a_stalled_peer_still_gets_the_window():
    """The #422 behaviour, unchanged. Without this the fix is just a revert."""
    hub = SharedModbusConnection(host="192.168.178.10", port=502)
    hub._client = _FakeClient(None)
    hub.reset("poll returned no data")          # first reset: deliberately exempt
    hub.reset("poll returned no data")          # second: the window starts

    assert hub._consecutive_resets == 2
    assert hub._quiet_remaining() > 0.0, (
        "the post-failure quiet window is gone for stalled gateways too"
    )


# --------------------------------------------------------------------------
# End to end, at his numbers
# --------------------------------------------------------------------------

@pytest.mark.skipif(ConnectionException is None, reason="pymodbus not installed")
def test_the_block_recovers_where_his_went_unavailable():
    """THE regression, with the reporter's state: two resets already behind it, so the
    window was 2.0s and his retry never happened."""
    hub, client = _hub(ConnectionException(CLOSED_MESSAGE), consecutive_resets=2)

    registers = hub.read_input_registers(0, 7, slave_id=1)

    assert registers == [1, 2, 3, 4, 5, 6, 7], (
        "the block is still lost - the reconnect after a hang-up is being refused by the "
        "quiet window, which is what took his entities offline"
    )
    assert client.reads == 2, "the read was not retried"
    assert client.connects >= 1, "no reconnect was made"


@pytest.mark.skipif(ModbusIOException is None, reason="pymodbus not installed")
def test_a_stalled_gateway_is_still_left_alone_mid_poll():
    """The other half: with the window running, a timeout must NOT reconnect immediately.
    Asserting both directions in one place because the fix is only correct if it separates
    them - either alone can be satisfied by the wrong change."""
    hub, client = _hub(ModbusIOException("No response received after 3 retries"),
                       consecutive_resets=2)

    registers = hub.read_input_registers(0, 7, slave_id=1)

    assert registers is None
    assert client.reads == 1, "a stalled gateway was hammered with an immediate reconnect"


@pytest.mark.skipif(ConnectionException is None, reason="pymodbus not installed")
def test_the_recovery_budget_still_bounds_it():
    """Exempting the window must not remove the other limit. Two reconnects per poll is
    what stops a gateway that closes every socket from being reconnected to forever."""
    hub, client = _hub(ConnectionException(CLOSED_MESSAGE), consecutive_resets=0)
    hub._recoveries_this_poll = hub._max_recoveries_per_poll     # budget already spent

    assert hub.read_input_registers(0, 7, slave_id=1) is None
    assert client.reads == 1, "the per-poll recovery budget was ignored"
