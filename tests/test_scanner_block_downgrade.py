"""The register scanner falls back to single-register reads when blocks are refused (#389).

A reporter with a LoRa-bridged microinverter ran the built-in scanner four times and got
2425 consecutive `Gateway Target Failed to Respond` errors and a "Detected Model: Unknown"
report. He then sent the *same* requests as raw single-register Modbus frames and got valid
data back from 177 holding registers.

He concluded our scanner was broken, and he was right. It read 125 registers per request and
never tried anything smaller, so a bridge that cannot relay a block that large looked
exactly like a device that was not there. The `block_size` option existed the whole time;
nothing told him to reach for it, and the report gave no hint that block size was the
variable.

Exception 0x0B is the tell: it is only produced by a gateway that *is* answering, about a
target it could not reach. That is never a reason to give up on the whole scan.
"""
from __future__ import annotations

import importlib

import pytest

_diag = importlib.import_module("growatt_under_test.diagnostic")


class _Resp:
    def __init__(self, registers=None, error=False, exception_code=None):
        self.registers = registers or []
        self._error = error
        if exception_code is not None:
            self.exception_code = exception_code

    def isError(self):  # noqa: N802 - pymodbus spelling
        return self._error


class _NarrowGateway:
    """Answers single-register reads, refuses anything larger — a LoRa bridge."""

    def __init__(self, max_count=1, values=None):
        self.max_count = max_count
        self.values = values or {}
        self.requests = []

    def _read(self, address, count, device_id):
        self.requests.append((address, count))
        if count > self.max_count:
            return _Resp(error=True, exception_code=11)  # Gateway Target Failed to Respond
        return _Resp([self.values.get(address + i, 0) for i in range(count)])

    def read_holding_registers(self, address, count, device_id=1):
        return self._read(address, count, device_id)

    def read_input_registers(self, address, count, device_id=1):
        return self._read(address, count, device_id)


class _DeadDevice:
    def __init__(self):
        self.requests = []

    def _read(self, address, count, device_id):
        self.requests.append((address, count))
        return _Resp(error=True, exception_code=11)

    def read_holding_registers(self, address, count, device_id=1):
        return self._read(address, count, device_id)

    def read_input_registers(self, address, count, device_id=1):
        return self._read(address, count, device_id)


def test_a_narrow_gateway_still_yields_data():
    """The headline case. Before this, every register came back as an error."""
    client = _NarrowGateway(max_count=1, values={0: 111, 1: 222, 2: 333, 3: 444})
    data = _diag._read_registers_chunked(
        client, start=0, count=4, slave_id=1, chunk_size=125, register_type='holding'
    )

    assert len(data) == 4
    assert [data[a]['status'] for a in range(4)] == ['success'] * 4
    assert [data[a]['value'] for a in range(4)] == [111, 222, 333, 444]


def test_the_downgrade_happens_once_not_per_chunk():
    """Probing on every failed block would multiply the scan time on a dead range."""
    client = _NarrowGateway(max_count=1, values={a: a for a in range(10)})
    _diag._read_registers_chunked(
        client, start=0, count=10, slave_id=1, chunk_size=5, register_type='holding'
    )

    oversized = [r for r in client.requests if r[1] > 1]
    assert len(oversized) == 1, (
        f"expected one failed block read before downgrading, got {oversized}"
    )


def test_a_genuinely_dead_range_is_not_probed_repeatedly():
    """When single reads fail too, the device really is absent — record the errors and move
    on rather than retrying every register individually."""
    client = _DeadDevice()
    data = _diag._read_registers_chunked(
        client, start=0, count=250, slave_id=1, chunk_size=125, register_type='holding'
    )

    assert all(entry['status'] == 'error' for entry in data.values())
    # 2 blocks + 1 single probe. Anything near 250 means it degraded to single reads on a
    # device that answers nothing, which is how a scan takes an hour.
    assert len(client.requests) <= 4, f"probed too eagerly: {len(client.requests)} requests"


def test_a_healthy_device_never_downgrades():
    """No behaviour change for the overwhelming majority of setups."""
    client = _NarrowGateway(max_count=125, values={a: a for a in range(125)})
    _diag._read_registers_chunked(
        client, start=0, count=125, slave_id=1, chunk_size=125, register_type='holding'
    )
    assert client.requests == [(0, 125)]


@pytest.mark.parametrize("register_type", ["holding", "input"])
def test_the_probe_uses_the_same_register_space(register_type):
    """Probing holding when the range is input would answer the wrong question."""
    client = _NarrowGateway(max_count=1, values={5: 42})
    data = _diag._read_registers_chunked(
        client, start=5, count=1, slave_id=1, chunk_size=125, register_type=register_type
    )
    assert data[5]['value'] == 42
