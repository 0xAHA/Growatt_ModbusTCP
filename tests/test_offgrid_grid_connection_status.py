"""Grid Connection Status reads the off-grid status codes, not the grid-tied ones (#443).

Register 0 carries `inverter_status` on both families and means entirely different things
in each. The grid-tied reading is "0 = Waiting, 1 = Normal", both of which imply a grid
connection. The off-grid set, which `SPF_STATUS_CODES` already spells out, is:

    0  Standby              7  Combine Charge
    1  No Use               8  Combine+Bypass
    2  Discharge            9  PV Charge+Bypass
    3  Fault               10  AC Charge+Bypass
    4  Flash               11  Bypass
    5  PV Charge           12  PV Charge+Discharge
    6  AC Charge

So the two codes that used to return "On-grid" mean Standby and No Use, and every state an
SPF actually runs in fell through to "Unknown". @takisbg reported the sensor showing
Unknown permanently on an SPF 6000 ES PLUS with a working grid connection, and that is why.

Anything with AC in it - charging from the AC input, or bypassing it straight to the load -
proves the utility is carrying the system. Discharge, PV Charge and PV Charge+Discharge
prove it is not. Standby, No Use, Fault and Flash say nothing either way, so they defer to
the AC input voltage, which is measured rather than inferred.
"""

from __future__ import annotations

import ast
import importlib
from pathlib import Path

import pytest

COMPONENT = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"

# The off-grid codes, and what each one settles about the AC input.
ON_GRID = (6, 7, 8, 9, 10, 11)
OFF_GRID = (2, 5, 12)
UNDECIDED = (0, 1, 3, 4)


_const = importlib.import_module("growatt_under_test.const")


def _branch_source() -> str:
    """The grid_connection_status branch, as written."""
    source = (COMPONENT / "sensor.py").read_text(encoding="utf-8")
    start = source.index('elif self._sensor_key == "grid_connection_status":')
    end = source.index("return None", start)
    return source[start:end]


def _evaluate(status: int, grid_voltage: float = 0.0, unread=()) -> str:
    """The real decision, not a transcription of it.

    It lives in const.py precisely so this can call it. A copy of the logic here would
    inherit whatever the original got wrong and pass anyway.
    """
    return _const.offgrid_grid_connection_status(
        status, grid_voltage, "grid_voltage" in unread
    )


# ---------------------------------------------------------------------------
# The decision itself
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("status", ON_GRID)
def test_ac_input_states_report_on_grid(status):
    """AC Charge, Combine Charge and every Bypass variant all run off the utility."""
    assert _evaluate(status) == "On-grid"


@pytest.mark.parametrize("status", OFF_GRID)
def test_battery_and_pv_only_states_report_off_grid(status):
    assert _evaluate(status, grid_voltage=235.0) == "Off-grid", (
        "a state that proves the AC input is not carrying the system must not be "
        "overridden by the mere presence of voltage at the input"
    )


@pytest.mark.parametrize("status", UNDECIDED)
def test_indeterminate_states_fall_through_to_the_voltage(status):
    assert _evaluate(status, grid_voltage=235.0) == "On-grid"
    assert _evaluate(status, grid_voltage=0.0) == "Off-grid"


def test_an_unread_voltage_is_unknown_rather_than_off_grid():
    """A failed read must not be published as a mains failure."""
    assert _evaluate(0, grid_voltage=0.0, unread=("grid_voltage",)) == "Unknown"


def test_the_old_reading_was_wrong_in_both_directions():
    """THE regression, stated as the two errors it made on off-grid hardware."""
    # Standby returned "On-grid" because grid-tied 0 means Waiting.
    assert _evaluate(0, grid_voltage=0.0) == "Off-grid"
    # And a genuinely grid-fed state returned "Unknown" because it was not 0 or 1.
    assert _evaluate(11) == "On-grid"
    assert _evaluate(6) == "On-grid"


# ---------------------------------------------------------------------------
# That the source actually implements it
# ---------------------------------------------------------------------------

def test_the_branch_is_gated_on_the_off_grid_profiles():
    branch = _branch_source()
    assert 'startswith(("spf_", "spe_"))' in branch, (
        "the off-grid reading is not gated to off-grid profiles, so it would change what "
        "grid-tied inverters report"
    )
    assert "offgrid_grid_connection_status" in branch, (
        "the entity no longer calls the shared decision, so these tests would be checking "
        "a function nothing uses"
    )


def test_the_grid_tied_reading_is_untouched():
    """SPH, MIN, MOD and the rest keep 0/1 -> On-grid. Only SPF/SPE diverge."""
    branch = _branch_source()
    assert "if status in (0, 1):" in branch


def test_the_groups_here_match_the_ones_that_ship():
    """These tests name the codes independently of the module. If the two drift apart the
    parametrised cases above would be asserting against the wrong set and still pass."""
    assert set(ON_GRID) == set(_const.SPF_STATUS_AC_INPUT_ACTIVE)
    assert set(OFF_GRID) == set(_const.SPF_STATUS_AC_INPUT_IDLE)


def test_the_codes_match_the_shipped_status_table():
    """Every code decided on must exist in SPF_STATUS_CODES, or the table and the sensor
    disagree about what the inverter can report."""
    known = set(_const.SPF_STATUS_CODES)
    for status in ON_GRID + OFF_GRID + UNDECIDED:
        assert status in known, f"status {status} is not in SPF_STATUS_CODES"


def test_no_off_grid_code_is_left_unclassified():
    """A code in the table that appears in none of the three groups would be an oversight
    rather than a decision."""
    covered = set(ON_GRID) | set(OFF_GRID) | set(UNDECIDED)
    missing = sorted(set(_const.SPF_STATUS_CODES) - covered)
    assert not missing, f"off-grid status codes not accounted for: {missing}"


def test_the_ast_parses_after_the_change():
    ast.parse((COMPONENT / "sensor.py").read_text(encoding="utf-8"))
