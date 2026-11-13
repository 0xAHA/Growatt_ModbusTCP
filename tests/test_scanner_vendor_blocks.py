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
    assert ("holding", 875, 125) in actual
    assert ("holding", 1125, 125) in actual
    assert ("input", 8000, 140) in actual


def test_full_vendor_scan_inherits_complete_legacy_blocks() -> None:
    actual = {
        (
            range_config.get("register_type", "input"),
            range_config["start"],
            range_config["count"],
        )
        for range_config in _diagnostic.FULL_VENDOR_SCAN_RANGES
    }

    assert ("holding", 875, 125) in actual
    assert ("holding", 1125, 125) in actual
    assert ("input", 8000, 140) in actual


def test_full_vendor_scan_is_selected_by_service_option() -> None:
    source = _diagnostic.__file__
    assert source is not None
    text = Path(source).read_text(encoding="utf-8")
    assert 'call.data.get("scan_full_vendor_blocks", False)' in text
    assert "FULL_VENDOR_SCAN_RANGES if scan_full_vendor_blocks" in text
    assert "scan_delay_ms, scan_full_vendor_blocks" in text


def test_firmware_discovered_ranges_match_zaba22_dispatcher() -> None:
    actual = {
        (
            range_config.get("register_type", "input"),
            range_config["start"],
            range_config["start"] + range_config["count"] - 1,
        )
        for range_config in _diagnostic.FIRMWARE_DISCOVERED_SCAN_RANGES
    }

    assert actual == {
        ("holding", 5000, 5079),
        ("holding", 5400, 7959),
        ("holding", 10000, 10125),
        ("holding", 40000, 41000),
        ("input", 4000, 4107),
        ("input", 5080, 5319),
    }
    assert _diagnostic.FIRMWARE_DISCOVERED_REGISTER_COUNT == 4115
    assert all(
        range_config["source"] == "ZABA22 firmware reconstruction"
        for range_config in _diagnostic.FIRMWARE_DISCOVERED_SCAN_RANGES
    )


def test_firmware_discovered_ranges_are_opt_in_and_do_not_overlap() -> None:
    selected = _diagnostic._select_scan_ranges(False, set(), False, True)
    assert selected == _diagnostic.FIRMWARE_DISCOVERED_SCAN_RANGES

    for register_type in {"input", "holding"}:
        intervals = sorted(
            (
                range_config["start"],
                range_config["start"] + range_config["count"],
            )
            for range_config in selected
            if range_config.get("register_type", "input") == register_type
        )
        assert all(left[1] <= right[0] for left, right in zip(intervals, intervals[1:]))


def test_standard_and_full_catalogs_are_unchanged_without_firmware_option() -> None:
    standard = _diagnostic._select_scan_ranges(False, None, False, False)
    full = _diagnostic._select_scan_ranges(False, None, True, False)
    assert standard == _diagnostic.UNIVERSAL_SCAN_RANGES
    assert full == _diagnostic.FULL_VENDOR_SCAN_RANGES
