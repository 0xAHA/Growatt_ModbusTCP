"""The optional full scan must cover complete vendor-defined VPP blocks."""

from __future__ import annotations

import importlib
from pathlib import Path


_diagnostic = importlib.import_module("growatt_under_test.diagnostic")


def test_full_vendor_scan_contains_complete_vpp_blocks() -> None:
    actual = {
        (
            range_config.get("register_type", "input"),
            range_config["start"],
            range_config["count"],
        )
        for range_config in _diagnostic.FULL_VENDOR_SCAN_RANGES
        if range_config.get("group") in {"vpp_control", "vpp_data"}
    }

    assert actual == {
        ("holding", 30000, 500),
        ("holding", 30500, 500),
        ("holding", 32000, 100),
        ("input", 31000, 300),
        ("input", 31300, 100),
        ("input", 31400, 100),
        ("input", 31500, 100),
    }


def test_standard_scan_contains_the_defined_legacy_extensions() -> None:
    actual = {
        (
            range_config.get("register_type", "input"),
            range_config["start"],
            range_config["count"],
        )
        for range_config in _diagnostic.UNIVERSAL_SCAN_RANGES
    }

    assert ("input", 875, 125) in actual
    assert ("input", 1125, 125) in actual


def test_full_vendor_scan_is_selected_by_service_option() -> None:
    source = _diagnostic.__file__
    assert source is not None
    text = Path(source).read_text(encoding="utf-8")
    assert 'call.data.get("scan_full_vendor_blocks", False)' in text
    assert "FULL_VENDOR_SCAN_RANGES if scan_full_vendor_blocks" in text
    assert "scan_delay_ms, scan_full_vendor_blocks" in text
