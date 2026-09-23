"""A read timeout must not be reported as a write failure (#432).

`_bus()` serialises reads, writes and whole polls on one lock and raises `ModbusWriteError`
on a timeout no matter which one was waiting - the read and write paths share it so every
caller that only distinguishes it from other exceptions keeps working. But the exception's
message used to be hardcoded to "Failed to write registers X-Y" regardless of what actually
timed out, so a plain register *read* that hit a busy bus surfaced as a write failure.

Reported by @JHPHendriks on issue #432: `growatt_modbus.read_register` (a read-only
diagnostic service) failed with "ModbusWriteError: Failed to write registers 0-1: Modbus
bus busy (lock timeout after 60s on read)" - the "on read" fragment proved the code already
knew which operation was waiting, but the exception's own constructor discarded that and
always spoke as if a write had failed, sending a plain read timeout into the wrong half of
the driver's error handling in the reader's head.
"""
from __future__ import annotations

import importlib
import threading

import pytest

_gm = importlib.import_module("growatt_under_test.growatt_modbus")
GrowattModbus = _gm.GrowattModbus
ModbusWriteError = _gm.ModbusWriteError


def _client_with_held_local_bus():
    """A direct-mode client whose local bus lock is already held by another thread."""
    client = GrowattModbus(connection_type="tcp", host="10.0.0.1", port=502, slave_id=1)
    client._shared_conn = None

    held = threading.Event()
    release = threading.Event()

    def _hold():
        client._local_bus_lock.acquire()
        held.set()
        release.wait(timeout=10)
        client._local_bus_lock.release()

    t = threading.Thread(target=_hold, daemon=True)
    t.start()
    held.wait(timeout=5)
    return client, t, release


def test_a_read_timeout_says_read_not_write():
    """The exact bug: a read-path lock timeout must not claim to be a write failure."""
    client, holder, release = _client_with_held_local_bus()

    import growatt_under_test.const as _const
    original = _const.SHARED_LOCK_TIMEOUT
    _const.SHARED_LOCK_TIMEOUT = 1
    try:
        with pytest.raises(ModbusWriteError) as excinfo:
            with client._bus("read"):
                raise AssertionError("the block must not run on a busy bus")
    finally:
        _const.SHARED_LOCK_TIMEOUT = original
        release.set()
        holder.join(timeout=5)

    message = str(excinfo.value)
    assert "Failed to read" in message, f"expected a read failure, got: {message}"
    assert "write" not in message.lower(), (
        f"a read timeout must not mention writing at all: {message}"
    )


def test_a_poll_timeout_says_poll_not_write():
    """The whole-poll bus hold (#398) goes through the same `_bus()` call and must not be
    mislabelled either - it is neither a read nor a write on its own."""
    client, holder, release = _client_with_held_local_bus()

    import growatt_under_test.const as _const
    original = _const.SHARED_LOCK_TIMEOUT
    _const.SHARED_LOCK_TIMEOUT = 1
    try:
        with pytest.raises(ModbusWriteError) as excinfo:
            with client._bus("poll"):
                raise AssertionError("the block must not run on a busy bus")
    finally:
        _const.SHARED_LOCK_TIMEOUT = original
        release.set()
        holder.join(timeout=5)

    assert "Failed to poll" in str(excinfo.value)


def test_a_write_timeout_still_says_write():
    """Backward compatibility: nothing about the write-path message should change."""
    client, holder, release = _client_with_held_local_bus()

    import growatt_under_test.const as _const
    original = _const.SHARED_LOCK_TIMEOUT
    _const.SHARED_LOCK_TIMEOUT = 1
    try:
        with pytest.raises(ModbusWriteError) as excinfo:
            with client._bus("write"):
                raise AssertionError("the block must not run on a busy bus")
    finally:
        _const.SHARED_LOCK_TIMEOUT = original
        release.set()
        holder.join(timeout=5)

    assert "write" in str(excinfo.value).lower()


def test_a_real_write_failure_still_names_the_register_range():
    """The operation parameter must not swallow the useful detail real write failures
    already carry - only the genuinely generic `_bus()` timeout, which never has a real
    register or value list, should fall back to the plain operation-name message."""
    err = ModbusWriteError(30100, [1], "device refused")
    assert "Failed to write registers 30100-30100: device refused" in str(err)
