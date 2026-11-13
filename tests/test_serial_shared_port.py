"""Several config entries on one serial adapter must queue, not collide (#501).

Two MOD TL3-X inverters on one USB-RS485 adapter, slave IDs 1 and 2, one config entry each.
Polling worked for both. `sync_inverter_time` and `get_register_data` worked for entry 1 and
failed every time for entry 2 with "Could not open the serial port".

Two things combined:

* each serial entry had its own bus lock, so nothing stopped entry 2 opening the port while
  entry 1 had it, and a serial port is exclusive;
* pymodbus opens the port on any request and only the poll path closed it again, so a write
  or a service read left the port held after its lock was released.

Polling hid both by retrying three times. A service call does not retry.

The fix shares one lock per physical port and, when more than one client is on the port,
closes the port as the outermost holder lets go. These tests hold both halves, plus the
clock error that blamed the inverter's firmware for a port that never opened.
"""
from __future__ import annotations

import importlib
import itertools
import threading
from datetime import datetime

import pytest

_gm = importlib.import_module("growatt_under_test.growatt_modbus")

_ports = itertools.count()


def _device() -> str:
    """A fresh port name per test, so the module-level registry cannot leak between tests."""
    return f"/dev/test-501-{next(_ports)}"


class _RawClient:
    """Stands in for pymodbus's client: counts closes."""

    def __init__(self) -> None:
        self.closes = 0

    def close(self) -> None:
        self.closes += 1


def _serial(device: str, slave_id: int = 1):
    client = _gm.GrowattModbus(connection_type="serial", device=device, baudrate=9600,
                               slave_id=slave_id, register_map="SPH_3000_6000")
    client.client = _RawClient()
    return client


# --------------------------------------------------------------------------
# One lock per port
# --------------------------------------------------------------------------

def test_entries_on_one_port_share_a_bus_lock():
    device = _device()
    first, second = _serial(device, 1), _serial(device, 2)
    assert first._local_bus_lock is second._local_bus_lock


def test_entries_on_different_ports_do_not():
    assert _serial(_device())._local_bus_lock is not _serial(_device())._local_bus_lock


def test_a_port_named_two_ways_is_one_port(monkeypatch):
    """by-id and by-path names are symlinks to the same /dev/ttyUSBn (#384)."""
    aliases = {"/dev/serial/by-id/usb-1a86-501": "/dev/ttyUSB501",
               "/dev/serial/by-path/pci-501": "/dev/ttyUSB501"}
    monkeypatch.setattr(_gm.os.path, "realpath", lambda p: aliases.get(p, p))
    first = _serial("/dev/serial/by-id/usb-1a86-501", 1)
    second = _serial("/dev/serial/by-path/pci-501", 2)
    assert first._local_bus_lock is second._local_bus_lock


def test_tcp_clients_are_untouched():
    client = _gm.GrowattModbus(connection_type="tcp", host="10.0.0.1", port=502,
                               register_map="SPH_3000_6000")
    assert client._serial_bus is None


def test_entry_two_waits_for_entry_one():
    """The reported failure: entry 2 acting while entry 1 holds the port."""
    device = _device()
    first, second = _serial(device, 1), _serial(device, 2)
    inside, release = threading.Event(), threading.Event()

    def hold():
        with first._bus("poll"):
            inside.set()
            release.wait(2)

    holder = threading.Thread(target=hold)
    holder.start()
    assert inside.wait(2)
    try:
        assert not second._local_bus_lock.acquire(timeout=0.05), (
            "entry 2 took the bus while entry 1 held the port"
        )
    finally:
        release.set()
        holder.join()
    assert second._local_bus_lock.acquire(timeout=1)
    second._local_bus_lock.release()


# --------------------------------------------------------------------------
# Giving the port back
# --------------------------------------------------------------------------

def test_a_shared_port_is_closed_when_the_holder_lets_go():
    device = _device()
    first, _second = _serial(device, 1), _serial(device, 2)
    with first._bus("read"):
        pass
    assert first.client.closes == 1


def test_it_is_closed_once_at_the_outermost_level():
    """write_batch() holds the bus while each write takes it again. Closing at the inner
    level would drop the port between two registers of one sequence."""
    device = _device()
    first, _second = _serial(device, 1), _serial(device, 2)
    with first.write_batch("sequence"):
        with first._bus("write"):
            pass
        assert first.client.closes == 0, "port closed in the middle of a batch"
        with first._bus("write"):
            pass
    assert first.client.closes == 1


def test_it_is_closed_even_when_the_block_raises():
    device = _device()
    first, _second = _serial(device, 1), _serial(device, 2)
    with pytest.raises(ValueError):
        with first._bus("read"):
            raise ValueError("boom")
    assert first.client.closes == 1
    assert first._local_bus_lock.acquire(timeout=0.5)
    first._local_bus_lock.release()


def test_a_single_entry_keeps_its_port_open():
    """Unchanged behaviour for the common case of one inverter per adapter."""
    only = _serial(_device())
    with only._bus("read"):
        pass
    assert only.client.closes == 0


# --------------------------------------------------------------------------
# The clock error
# --------------------------------------------------------------------------

def test_an_unreachable_inverter_is_not_blamed_for_refusing_the_clock():
    """"the inverter refused register 45 ... may not allow its clock to be set" sent the
    reporter comparing firmware on two identical inverters. Nothing had been sent."""
    client = _serial(_device())
    client.connect = lambda: False
    attempted = []
    client.write_single_register_any_fc = lambda reg, value: attempted.append(reg) or False

    with pytest.raises(_gm.ModbusConnectionError) as caught:
        client.write_inverter_time(datetime(2026, 11, 13, 12, 0, 5))

    assert attempted == [], "a write was attempted with no connection"
    assert "refused" not in str(caught.value)
    assert "could not open the connection" in str(caught.value)


def test_a_connection_error_is_still_a_modbus_write_error():
    """Existing `except ModbusWriteError` handlers must keep catching it."""
    assert issubclass(_gm.ModbusConnectionError, _gm.ModbusWriteError)
