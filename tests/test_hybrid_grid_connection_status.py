"""Grid Connection Status on hybrids without register 31000 reads the hybrid table (#474).

The fallback branch applied the grid-tied reading of the status register: 0 Waiting or
1 Normal means On-grid, anything else Unknown. Hybrids (SPH, SPH-TL3, SPA, MIN TL-XH2) use
the hybrid table instead, where 5 PV On-Grid and 6 Bat On-Grid are the normal running states.
An SPH therefore showed Unknown all day while exporting, and On-grid only for the two minutes
it spent in Waiting at dawn.

The decision is a function in const.py, tested here against the shipped status table. The
sensor's routing to it is checked from source, because sensor.py imports Home Assistant.
"""
from __future__ import annotations

import ast
import importlib
from pathlib import Path

import pytest

CONST = importlib.import_module("growatt_under_test.const")
SENSOR = (Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
          / "sensor.py").read_text(encoding="utf-8")

decide = CONST.hybrid_grid_connection_status
NAMES = {code: entry["name"] for code, entry in CONST.HYBRID_STATUS_CODES.items()}


@pytest.mark.parametrize("code", [5, 6])
def test_the_running_states_are_on_grid(code):
    """The reporter's day: Bat On-Grid overnight, PV On-Grid from 08:43."""
    assert "On-Grid" in NAMES[code]
    assert decide(code) == "On-grid"


@pytest.mark.parametrize("code", [7, 8])
def test_the_off_grid_states_are_off_grid(code):
    assert "Off-Grid" in NAMES[code]
    assert decide(code) == "Off-grid"


@pytest.mark.parametrize("code", [0, 1, 2, 3, 4, 9])
def test_states_that_do_not_settle_it_are_unknown(code):
    """Waiting, Self-Test, Reserved, Fault, Updating, Bypass. Waiting used to read On-grid."""
    assert decide(code) == "Unknown"


def test_the_sph_profiles_use_the_hybrid_table():
    for key in ("SPH_3000_6000", "SPH_7000_10000", "SPH_3000_6000_V201",
                "SPH_7000_10000_V201", "SPH_8000_10000_HU", "SPH_TL3_3000_10000_V201"):
        assert CONST.PROFILE_STATUS_MAP.get(key) == "hybrid", key


def test_the_sensor_sends_hybrids_to_the_hybrid_table_before_the_grid_tied_fallback():
    tree = ast.parse(SENSOR)
    branch = next(
        n for n in ast.walk(tree)
        if isinstance(n, ast.If)
        and isinstance(n.test, ast.Compare)
        and "grid_connection_status" in ast.get_source_segment(SENSOR, n.test)
    )
    body = ast.get_source_segment(SENSOR, branch)
    hybrid_at = body.index("hybrid_grid_connection_status(data.status)")
    fallback_at = body.index("if status in (0, 1):")
    assert hybrid_at < fallback_at, "hybrids must not reach the grid-tied 0/1 reading"
    assert '== "hybrid"' in body
