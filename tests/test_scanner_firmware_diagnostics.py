"""Tests for the opt-in ZABA22 diagnostic dispatcher scan."""

from __future__ import annotations

import importlib

import pytest


_diag = importlib.import_module("growatt_under_test.diagnostic")


class _Response:
    def __init__(self, registers: list[int] | None = None, exception_code: int | None = None) -> None:
        self.registers = registers or []
        self.exception_code = exception_code

    def isError(self) -> bool:
        return self.exception_code is not None

    def __str__(self) -> str:
        return f"exception {self.exception_code}"


class _DiagnosticClient:
    def __init__(self, error_block: int | None = None) -> None:
        self.calls: list[tuple[int, int]] = []
        self.error_block = error_block
        self.close_count = 0
        self.connect_count = 0

    def read_holding_registers(self, address: int, count: int, device_id: int) -> _Response:
        self.calls.append((address, count))
        block_index = (
            _diag.FIRMWARE_DIAGNOSTIC_BLOCK_STARTS.index(address)
            if address in _diag.FIRMWARE_DIAGNOSTIC_BLOCK_STARTS
            else None
        )
        if block_index is not None and block_index == self.error_block:
            return _Response(exception_code=2)
        return _Response([0] * count)

    def close(self) -> None:
        self.close_count += 1

    def connect(self) -> bool:
        self.connect_count += 1
        return True


class _TransportRetryClient(_DiagnosticClient):
    def __init__(self) -> None:
        super().__init__()
        self.failed = False

    def read_holding_registers(self, address: int, count: int, device_id: int) -> _Response:
        if not self.failed:
            self.failed = True
            self.calls.append((address, count))
            raise ConnectionError("peer closed")
        return super().read_holding_registers(address, count, device_id)


def test_diagnostic_block_starts_and_request_size_are_exact() -> None:
    assert len(_diag.FIRMWARE_DIAGNOSTIC_BLOCK_STARTS) == 100
    assert _diag.FIRMWARE_DIAGNOSTIC_BLOCK_STARTS[0] == 32768
    assert _diag.FIRMWARE_DIAGNOSTIC_BLOCK_STARTS[1] == 32870
    assert _diag.FIRMWARE_DIAGNOSTIC_BLOCK_STARTS[99] == 42866

    client = _DiagnosticClient()
    records = _diag._read_firmware_diagnostic_blocks(client, slave_id=1)

    assert len(records) == 100
    assert all(count == 102 for _, count in client.calls)
    assert all(record["request_count"] == 102 for record in records)
    assert all(record["function_code"] == 3 for record in records)


def test_diagnostic_data_preserves_zero_values_and_identity() -> None:
    client = _DiagnosticClient()
    records = _diag._read_firmware_diagnostic_blocks(client, slave_id=1)
    first = records[0]

    assert first["scan_type"] == "firmware_diagnostic"
    assert first["diagnostic_block_index"] == 0
    assert first["request_start"] == 32768
    assert first["raw_values"] == [0] * 102
    assert first["words"][0]["register_address"] == 32768
    assert first["words"][0]["word_offset"] == 0
    assert first["words"][0]["raw_value"] == 0
    assert first["words"][-1]["register_address"] == 32869


def test_modbus_exception_is_recorded_without_single_register_fallback() -> None:
    client = _DiagnosticClient(error_block=1)
    records = _diag._read_firmware_diagnostic_blocks(client, slave_id=1)

    assert records[1]["status"] == "error"
    assert records[1]["exception_code"] == 2
    assert records[1]["error"] == "Illegal Data Address"
    assert len(client.calls) == 100
    assert client.close_count == 0
    assert client.connect_count == 0
    assert all(count == 102 for _, count in client.calls)


def test_transport_retry_repeats_the_exact_diagnostic_request(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _TransportRetryClient()
    monkeypatch.setattr(_diag.time, "sleep", lambda _delay: None)

    records = _diag._read_firmware_diagnostic_blocks(client, slave_id=1)

    assert records[0]["status"] == "success"
    assert client.calls[:2] == [(32768, 102), (32768, 102)]
    assert client.close_count == 1
    assert client.connect_count == 1
    assert all(count == 102 for _, count in client.calls)


def test_normal_fc03_reads_avoid_exact_diagnostic_count() -> None:
    assert _diag._safe_standard_chunk_count(40000, 102, 1001) == 101
    assert _diag._safe_standard_chunk_count(40000, 125, 1001) == 125
    assert _diag._safe_standard_chunk_count(30000, 102, 102) == 102
    assert _diag._safe_standard_chunk_count(40000, 102, 102, "input") == 102


def test_normal_h40000_chunking_never_uses_count_102(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _DiagnosticClient()
    monkeypatch.setattr(_diag.time, "sleep", lambda _delay: None)

    data = _diag._read_registers_chunked(
        client,
        start=40000,
        count=205,
        slave_id=1,
        chunk_size=102,
        register_type="holding",
    )

    assert len(data) == 205
    assert [count for _, count in client.calls] == [101, 101, 3]
    assert all(count != 102 for _, count in client.calls)


def test_diagnostic_service_is_opt_in_and_offgrid_safe() -> None:
    source = _diag.__file__
    assert source is not None
    text = open(source, encoding="utf-8").read()
    assert 'call.data.get("scan_firmware_diagnostics", False)' in text
    assert "Skipping ZABA22 firmware diagnostics in OffGrid mode" in text
    assert "read_holding_registers" in text
    assert "FIRMWARE_DIAGNOSTIC_REQUEST_COUNT" in text
