"""The diagnostic scanner retries a block after a transport disconnect."""

from __future__ import annotations

import importlib

import pytest

_diag = importlib.import_module("growatt_under_test.diagnostic")


class _Response:
    def __init__(self, registers: list[int]) -> None:
        self.registers = registers

    def isError(self) -> bool:  # noqa: N802 - pymodbus spelling
        return False


class _ReconnectableClient:
    def __init__(self) -> None:
        self.read_count = 0
        self.close_count = 0
        self.connect_count = 0

    def read_input_registers(self, address: int, count: int, device_id: int) -> _Response:
        self.read_count += 1
        if self.read_count == 1:
            raise ConnectionError("peer closed the socket")
        return _Response(list(range(address, address + count)))

    def close(self) -> None:
        self.close_count += 1

    def connect(self) -> bool:
        self.connect_count += 1
        return True


def test_transport_exception_reconnects_and_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _ReconnectableClient()
    monkeypatch.setattr(_diag.time, "sleep", lambda _delay: None)

    data = _diag._read_registers_chunked(
        client,
        start=10,
        count=2,
        slave_id=1,
        chunk_size=2,
        register_type="input",
    )

    assert data == {
        10: {"value": 10, "status": "success", "error": None},
        11: {"value": 11, "status": "success", "error": None},
    }
    assert client.read_count == 2
    assert client.close_count == 1
    assert client.connect_count == 1
