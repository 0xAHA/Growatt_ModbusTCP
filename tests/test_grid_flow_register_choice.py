"""A grid meter register must not be chosen by battery detection (#228).

`power_to_grid` and `power_to_user` used to resolve through
`_find_register_by_name_with_fallback()`, which picks a register range using
`_detect_battery_register_range()`. That detector scores battery sensors - voltage, SOC,
power, charge and discharge counters - and on an inverter with **no battery** every one of
them reads zero, so it takes its "both ranges are zero, default to fallback" branch.

'fallback' filters the candidate addresses down to the 1000-3999 range, which drops the VPP
meter address. The resolved address is then the same 3000-range one the caller already had,
and the guard `if vpp_addr != power_to_grid_addr` refuses to fire.

So on a batteryless grid-tied inverter the metered value at 31112/31113 was unreachable no
matter how good the meter. @majliSK has a working DTSU666 reading -211.2 W from exactly
those registers with his own script, while the integration fell through to estimating grid
flow from solar.

The pairing of a battery heuristic with a grid meter is the defect. These tests pin the
property that matters: the choice depends on which register answers, not on whether a
battery exists.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

COMPONENT = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
SOURCE = (COMPONENT / "growatt_modbus.py").read_text(encoding="utf-8")


def _read_all_data_body() -> str:
    """The executable lines of the grid-flow block.

    Comments are stripped deliberately: the block explains at length what it no longer
    does, and naming the old helper in prose must not read as calling it.
    """
    start = SOURCE.index("            # Grid flow: take the first address carrying a reading")
    end = SOURCE.index("            if power_to_load_addr:", start)
    return "\n".join(
        line for line in SOURCE[start:end].splitlines()
        if not line.strip().startswith("#")
    )


def test_grid_flow_does_not_consult_battery_range_detection():
    """THE regression, stated as the property rather than the symptom. Battery detection
    decides nothing about where a grid meter lives, and on a batteryless inverter it
    actively excludes the only address that carries the reading."""
    block = _read_all_data_body()

    assert "_find_register_by_name_with_fallback" not in block, (
        "grid flow is resolving through the battery-range-gated helper again — on an "
        "inverter with no battery that filters out the VPP meter address"
    )
    assert "_find_all_registers_by_name" in block, (
        "grid flow should consider every address mapped to the name, then pick by which "
        "one answers"
    )


def test_the_battery_detector_really_does_default_to_fallback_when_nothing_answers():
    """Rule 4: the failure above only exists if this branch behaves as claimed. If the
    detector stops defaulting to 'fallback' on an all-zero read, the reasoning in this
    file needs revisiting rather than silently passing."""
    tree = ast.parse(SOURCE)
    fn = next(
        n for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef) and n.name == "_detect_battery_register_range"
    )
    body = ast.get_source_segment(SOURCE, fn)

    assert "Both ranges are zero" in body and "'fallback'" in body, (
        "the all-zero default in _detect_battery_register_range has changed shape"
    )


def test_the_vpp_meter_address_is_reachable_for_grid_power():
    """The concrete case: on MID V2.01, 31113 carries maps_to='power_to_grid_low', so a
    name lookup must offer it as a candidate alongside the 3000-range register."""
    import importlib
    import sys

    sys.path.insert(0, "tests")
    profiles = importlib.import_module("growatt_under_test.profiles")
    register_map = profiles.REGISTER_MAPS["MID_15000_25000TL3_X_V201"]
    inputs = register_map["input_registers"]

    candidates = [
        addr for addr, info in inputs.items()
        if info.get("name") == "power_to_grid_low"
        or info.get("alias") == "power_to_grid_low"
        or info.get("maps_to") == "power_to_grid_low"
    ]

    assert 31113 in candidates, "the meter register no longer resolves to power_to_grid_low"
    assert any(a < 4000 for a in candidates), (
        "expected a 3000-range candidate too — this test is meant to cover the case where "
        "two ranges compete"
    )


def test_the_meter_register_is_signed_and_negated():
    """Import arrives as a negative power_to_grid by design, which is what sensor.py's
    _signed_grid_power has to understand. If the negation were dropped, the direction would
    silently invert for every metered MID user."""
    import importlib
    import sys

    sys.path.insert(0, "tests")
    profiles = importlib.import_module("growatt_under_test.profiles")
    meter_low = profiles.REGISTER_MAPS["MID_15000_25000TL3_X_V201"]["input_registers"][31113]

    assert meter_low.get("signed") is True
    assert meter_low.get("combined_scale") == -0.1, (
        "meter_power is no longer negated on combine — VPP reports positive for import, so "
        "without this the export/import direction flips"
    )
