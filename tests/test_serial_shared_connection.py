"""The shared connection hub covers serial, not only TCP.

The hub exists to serialize Modbus transactions behind one lock and "prevent RS485
cross-talk". Until v1.7.0 it was created only for TCP entries, which had it backwards: an
RS485 bus is precisely where two uncoordinated masters collide.

Each serial config entry opened its own ModbusSerialClient on the same adapter and paced
itself with a per-instance `min_read_interval`, which says nothing about what the other
entry is doing. Two inverters on one USB-RS485 adapter — the normal way to wire a parallel
SPF stack — interleaved their frames on one physical bus with nothing serializing them,
producing random single-sample read failures on both units.

These tests exercise the serial connect path directly. That matters: the first cut of this
change called `ModbusSerialClient(...)`, a name that exists only under TYPE_CHECKING, so it
would have raised NameError on the first real connection. Every existing test passed,
because none of them ever asked a serial hub to connect.
"""
from __future__ import annotations

import importlib
from pathlib import Path

import pytest

_gm = importlib.import_module("growatt_under_test.growatt_modbus")
SharedModbusConnection = _gm.SharedModbusConnection


class _FakeSerial:
    """Stands in for pyserial's Serial object hanging off the client."""

    def __init__(self):
        self.in_waiting = 7
        self.reset_calls = 0

    def reset_input_buffer(self):
        self.reset_calls += 1
        self.in_waiting = 0


class _FakeSerialClient:
    """Captures the kwargs the hub builds its client with."""

    last_kwargs: dict = {}

    def __init__(self, **kwargs):
        type(self).last_kwargs = kwargs
        self.socket = _FakeSerial()
        self.connected = False

    def connect(self):
        self.connected = True
        return True

    def is_socket_open(self):
        return self.connected

    def close(self):
        self.connected = False


@pytest.fixture
def serial_hub(monkeypatch):
    monkeypatch.setattr(_gm, "ModbusClient", _FakeSerialClient, raising=False)
    monkeypatch.setattr(_gm, "SERIAL_AVAILABLE", True, raising=False)
    return SharedModbusConnection(device="/dev/ttyUSB0", baudrate=9600, timeout=10)


# --------------------------------------------------------------------------
# Identity
# --------------------------------------------------------------------------

def test_a_serial_hub_knows_it_is_serial():
    hub = SharedModbusConnection(device="/dev/ttyUSB0")
    assert hub.is_serial
    assert hub.connection_id == "/dev/ttyUSB0"


def test_a_tcp_hub_is_unchanged():
    """The whole point is that TCP behaviour does not move."""
    hub = SharedModbusConnection(host="10.0.0.1", port=502)
    assert not hub.is_serial
    assert hub.connection_id == "10.0.0.1:502"


# --------------------------------------------------------------------------
# The connect path — the part that was broken and untested
# --------------------------------------------------------------------------

def test_connecting_builds_a_serial_client_with_the_configured_settings(serial_hub):
    """Guards the NameError: ModbusSerialClient is a TYPE_CHECKING-only import, so the
    runtime name has to be ModbusClient. Nothing caught this because no test connected."""
    assert serial_hub.ensure_connected() is True

    kwargs = _FakeSerialClient.last_kwargs
    assert kwargs["port"] == "/dev/ttyUSB0"
    assert kwargs["baudrate"] == 9600
    # N/8/1 is what the non-shared path has always hardcoded; the hub must not differ,
    # or moving to a shared connection would silently change framing.
    assert kwargs["parity"] == "N"
    assert kwargs["stopbits"] == 1
    assert kwargs["bytesize"] == 8


def test_a_second_connect_reuses_the_open_client(serial_hub):
    serial_hub.ensure_connected()
    first = serial_hub._client
    serial_hub.ensure_connected()
    assert serial_hub._client is first, "reconnected while the port was already open"


def test_missing_pyserial_fails_cleanly_rather_than_raising(monkeypatch):
    monkeypatch.setattr(_gm, "SERIAL_AVAILABLE", False, raising=False)
    hub = SharedModbusConnection(device="/dev/ttyUSB0")
    assert hub.ensure_connected() is False


# --------------------------------------------------------------------------
# Buffer flushing
# --------------------------------------------------------------------------

def test_the_serial_buffer_is_drained_with_pyserials_own_method(serial_hub):
    """The TCP path calls sock.recv() in a loop. A pyserial Serial has no recv() and no
    gettimeout(), so the TCP branch would raise and silently skip the flush."""
    serial_hub.ensure_connected()
    fake = serial_hub._client.socket
    assert fake.reset_calls >= 1, "stale bytes were never drained on a serial connection"


def test_a_serial_port_is_released_between_polls(serial_hub):
    """A serial port is exclusive. Holding it open across polls denies it to every other
    process, including a second config entry naming the same adapter by a different path —
    which turned an intermittent collision into a permanent 'Could not exclusively lock
    port' for one of them (#384)."""
    serial_hub.ensure_connected()
    assert serial_hub._client is not None

    serial_hub.end_poll()
    assert serial_hub._client is None, "the serial port is still held after the poll ended"

    # ...and the next poll must be able to open it again.
    assert serial_hub.ensure_connected() is True


def test_a_tcp_socket_is_kept_open_between_polls():
    """The opposite rule for TCP: a socket costs nothing to hold and reconnecting costs a
    round trip, so end_poll() must leave it alone."""
    hub = SharedModbusConnection(host="10.0.0.1", port=502)
    hub._client = object()
    hub.end_poll()
    assert hub._client is not None, "TCP connections should persist across polls"


def test_ending_a_poll_is_safe_before_anything_connected(serial_hub):
    serial_hub.end_poll()  # must not raise


def test_flushing_never_propagates_an_error(serial_hub):
    """A failed flush is non-critical and must not take down the poll."""
    serial_hub.ensure_connected()

    class _Exploding:
        in_waiting = 1

        def reset_input_buffer(self):
            raise OSError("device disappeared")

    serial_hub._client.socket = _Exploding()
    serial_hub._flush_receive_buffer()  # must not raise


# --------------------------------------------------------------------------
# The wiring in __init__.py
# --------------------------------------------------------------------------

def test_setup_does_not_create_a_hub_for_serial_entries():
    """Reverted in v1.7.5, and this test exists to stop it coming back by halves.

    v1.7.0 created a hub for serial entries here. But `_fetch_data` routes every poll through
    `_fetch_data_shared()` whenever a hub exists, and that opens the hub's connection — while
    coordinator.py builds the serial client WITHOUT `shared_conn`, so the client kept its own
    ModbusSerialClient and opened the same port a second time. A serial port is exclusive, so
    every read failed with 'Could not exclusively lock port' and every serial user went
    offline, not only multi-entry ones (#384).

    Re-enabling serial hubs requires coordinator.py's serial branch to pass
    `shared_conn=self._hub` in the same change. Until it does, creating one here is harmful.
    """
    source = (Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
              / "__init__.py").read_text(encoding="utf-8")

    assert "hub_key = f\"serial:" not in source, (
        "a hub is being created for serial entries again — check that coordinator.py's "
        "serial branch passes shared_conn=self._hub, or the port is opened twice"
    )
    # Hub creation must stay inside the TCP-only branch.
    assert 'if connection_type == "tcp":' in source
    assert source.index("hub.acquire_ref()") > source.index('if connection_type == "tcp":'), (
        "hub refcounting has escaped the TCP branch"
    )


def test_the_coordinator_would_have_to_be_wired_up_too():
    """The half that was missed. If someone re-adds serial hub creation without this, the
    double-open returns — so the two halves are pinned together here rather than in a
    comment nobody reads."""
    source = (Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
              / "coordinator.py").read_text(encoding="utf-8")

    serial_branch = source[source.index('else:  # serial'):]
    serial_branch = serial_branch[:serial_branch.index("_LOGGER.debug")]
    creates_serial_hub = "hub_key = f\"serial:" in (
        Path(__file__).parent.parent / "custom_components" / "growatt_modbus" / "__init__.py"
    ).read_text(encoding="utf-8")

    if creates_serial_hub:
        assert "shared_conn=self._hub" in serial_branch, (
            "serial hubs are created but the serial client is not given one — it will open "
            "the port a second time and every read will fail with Errno 11 (#384)"
        )
