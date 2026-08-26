"""Serial connections must serialise bus access (#398).

The shared-connection hub is TCP-only, and deliberately so - v1.7.0 extended it to serial
and every serial user went offline with `Could not exclusively lock port`, because the hub
opened the port and the client opened it again. That was reverted in v1.7.5.

The revert left serial with no serialisation at all. A coordinator poll and a service-call
write could use the same client concurrently, and when one path hit a transport timeout and
reconnected, the other was left holding a closed file descriptor:

    OSError: [Errno 9] Bad file descriptor

roughly ten times a day for a reporter running TOU automations on a 15-minute cycle.

The fix is a per-client lock, NOT a serial hub. Nothing here opens the port; the client
still owns its own socket. These tests pin that distinction, because the obvious "fix" is
to give serial a hub and that reintroduces v1.7.0.
"""
import importlib
import sys
import threading
import time

import pytest

sys.path.insert(0, "tests")

_gm = importlib.import_module("growatt_under_test.growatt_modbus")


def _client():
    return _gm.GrowattModbus(
        connection_type="serial", port="/dev/ttyUSB0", baudrate=9600,
        register_map="SPH_3000_6000",
    )


def test_a_serial_client_has_its_own_bus_lock():
    """Without a hub there is nothing else to serialise against."""
    client = _client()
    assert client._shared_conn is None, "serial must not be given a hub - see v1.7.0"
    assert isinstance(client._local_bus_lock, type(threading.RLock())), (
        "serial client has no bus lock; reads and writes can interleave"
    )


def test_the_lock_is_reentrant():
    """write_batch() holds the bus across a sequence while the individual writes still take
    it themselves. A plain Lock deadlocks on the first nested write."""
    client = _client()
    with client._bus("outer"):
        with client._bus("inner"):
            pass  # a non-reentrant lock never reaches here


def test_the_bus_is_actually_exclusive():
    """The point of the exercise: two threads must not hold it at once."""
    client = _client()
    overlaps = []
    inside = threading.Event()

    def hold():
        with client._bus("holder"):
            inside.set()
            time.sleep(0.2)

    t = threading.Thread(target=hold)
    t.start()
    assert inside.wait(2), "holder thread never acquired the bus"

    acquired_immediately = client._local_bus_lock.acquire(timeout=0.05)
    if acquired_immediately:
        client._local_bus_lock.release()
        overlaps.append("second caller acquired the bus while it was held")

    t.join()
    assert not overlaps, overlaps[0]


def test_the_bus_is_released_when_the_block_raises():
    """A leaked lock would stall every subsequent poll - worse than the bug being fixed."""
    client = _client()
    with pytest.raises(ValueError):
        with client._bus("failing"):
            raise ValueError("boom")

    assert client._local_bus_lock.acquire(timeout=0.5), "the bus was not released"
    client._local_bus_lock.release()


@pytest.mark.parametrize("method", [
    "read_input_registers", "read_holding_registers", "write_register", "write_registers",
])
def test_every_entry_point_takes_the_bus(method):
    """Each public method delegates to a _locked implementation inside self._bus(). If one
    is added later that bypasses it, the race returns for that path only - which is the
    hardest version of this bug to find."""
    import inspect
    source = inspect.getsource(getattr(_gm.GrowattModbus, method))
    assert "self._bus(" in source, f"{method} does not take the bus lock"


def test_serial_still_gets_no_shared_hub():
    """The guard against re-introducing v1.7.0. A hub for serial means the hub opens the
    port while the client opens it again, and every serial user goes offline."""
    from pathlib import Path
    init = (Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
            / "__init__.py").read_text(encoding="utf-8")

    block = init[init.index("hub: SharedModbusConnection | None = None"):]
    block = block[:block.index("coordinator = GrowattModbusCoordinator")]
    assert 'if connection_type == "tcp":' in block, (
        "hub creation is no longer gated on TCP - this is the v1.7.0 regression"
    )
