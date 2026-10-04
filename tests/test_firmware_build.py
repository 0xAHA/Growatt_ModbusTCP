"""The firmware build string is shown alongside the firmware version (#458, #400, #449).

V1.39 holding 9-11 is "Firmware version", and it reads "AL1.0" on MIN TL-XH units whose
builds behave differently: ALBA130101 drops low SOC-limit writes where ALBA180101 accepts
them, and ALBA10010129 has no VPP at all where ALBA18010122 does. The string that separates
them is holding 82-87, "FW Build No." - what the Growatt portal shows as Version, decoded
from a live capture by @l4m4re.
"""
from __future__ import annotations

import importlib
from pathlib import Path

import pytest

decode = importlib.import_module("growatt_under_test.const").decode_firmware_build
COMPONENT = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"


def test_l4m4res_captured_words_decode_to_the_portal_version():
    words = [0x414C, 0x4241, 0x3138, 0x3031, 0x3031, 0x3232]
    assert decode(words) == "ALBA18010122"


def test_an_absent_trailing_component_is_dropped_not_fatal():
    """87 is the M3 build; an SPH-TL3 with none reads 0 there (#446, @acsel91)."""
    assert decode([22850, 16705, 12339, 12339, 12344, 0]) == "YBAA030308"


@pytest.mark.parametrize("words", [
    [100, 0, 0, 0, 0, 0],                               # TL3-S: settings, not a string
    [0x414C, 0x4241, 0, 0, 0, 0],                       # model letters only, no build
    [0x414C, 0x0000, 0x3138, 0x3031, 0x3031, 0x3232],   # NUL mid-string: a fragment
    [0x414C, 0x4241, 0x3100, 0x3031, 0x3031, 0x3232],   # half-empty register
    [0x414C, 0x4241, 0x3138],                           # short read
    None,                                               # no answer
])
def test_anything_but_a_complete_printable_string_is_not_a_version(words):
    """A fragment shown as a version is worse than none - it looks like data."""
    assert decode(words) is None


def test_the_coordinator_reads_it_except_on_off_grid_profiles():
    source = (COMPONENT / "coordinator.py").read_text(encoding="utf-8")
    assert "decode_firmware_build(self._read_holding(82, 6))" in source
    read_at = source.index("decode_firmware_build(self._read_holding(82, 6))")
    guard = source.rfind('if not profile.get("offgrid_protocol", False):', 0, read_at)
    assert guard != -1 and read_at - guard < 200, (
        "the build read is not guarded against off-grid profiles, whose 82+ are settings"
    )


def test_it_reaches_the_device_page_and_diagnostics():
    coordinator = (COMPONENT / "coordinator.py").read_text(encoding="utf-8")
    assert 'f"{self._firmware_version} ({self._firmware_build})"' in coordinator
    diagnostics = (COMPONENT / "diagnostics.py").read_text(encoding="utf-8")
    assert '"firmware_build"' in diagnostics
