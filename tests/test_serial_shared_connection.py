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

def test_setup_creates_a_hub_for_serial_entries_too():
    """The regression this fixes was a single `if connection_type == "tcp":` guard around
    hub creation. Asserted against the source because building a real config entry needs
    Home Assistant, which cannot be imported here (see tests_ha/)."""
    source = (Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
              / "__init__.py").read_text(encoding="utf-8")

    assert 'hub_key = f"serial:{resolved_device}"' in source, (
        "serial entries do not get a connection hub, so two entries on one adapter still "
        "open independent clients on the same bus"
    )
    assert "SharedModbusConnection(\n            device=device" in source, (
        "the serial hub is not constructed with the device path"
    )
    # The old shape: hub creation nested inside a TCP-only branch.
    assert 'if connection_type == "tcp":\n        from homeassistant.const import CONF_HOST' in source
    assert "hub.acquire_ref()" in source
    assert source.index("hub.acquire_ref()") > source.index("hub_key = f\"serial:{resolved_device}\""), (
        "refcounting runs before the serial branch can set hub_key"
    )


def test_the_hub_key_uses_the_resolved_device_path():
    """One adapter answers to /dev/ttyUSB2, /dev/serial/by-id/... and /dev/serial/by-path/...
    at the same time, and the docs recommend the by-id form — so two entries naming one port
    differently is normal, not exotic.

    A reporter's debug log showed exactly this shape: one entry logging as
    /dev/serial/by-path/pci-0000:00:14.0-usb-0:5:1.0-port0 and another as /dev/ttyUSB2,
    interleaving reads. Keying the hub on the raw string gives them separate connections and
    lets them collide on one bus, which defeats the whole point of sharing.
    """
    source = (Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
              / "__init__.py").read_text(encoding="utf-8")

    assert 'hub_key = f"serial:{device}"' not in source, (
        "the hub is keyed on the configured path, so by-id and /dev/ttyUSBn forms of one "
        "adapter get separate connections"
    )
    assert "os.path.realpath" in source, "the device path is never resolved"
    assert 'hub_key = f"serial:{resolved_device}"' in source

    # Must not run on the event loop - that is the bug #384 reported against this file.
    assert "async_add_executor_job(os.path.realpath" in source, (
        "realpath is a filesystem call and is being made on the event loop"
    )
