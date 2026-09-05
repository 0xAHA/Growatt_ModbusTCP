"""Active power is the inverter's AC output, not grid export (#415).

`MOD_6000_15000TL3_XH` mapped register 31101 (VPP 2.03 item 45, active power) to
`power_to_grid_low`, on the reasoning that hybrid firmware subtracts battery and load and
so reports true net grid exchange there. Two devices disproved it:

    MOD 10KTL3-HU   PV 2557.2 W, charging 1796 W, load 780.2 W  -> grid ~= 0
                    31101 read 702.7 and was published as 702.7 W of export
    MOD TL3-XH      PV 1635.9 W, discharging 2004 W, load 3647.8 W -> grid ~= 0
                    31101 read 3574 and was published as 3574 W of export

In both cases 31101 tracks PV minus battery minus conversion losses - the AC output - while
the house was self-consuming and nothing flowed to the grid.

**This surfaced as a regression.** Before v1.9.3, grid flow resolved through a
battery-range-gated lookup that happened not to reach 31101 on these devices. v1.9.3 changed
resolution to "whichever mapped register answers", to fix a batteryless MID whose meter was
unreachable (#228) - which made the bad mapping deterministic. One reporter has diagnostics
either side of the boundary: 0.0 W on v1.8.14, 702.7 W on v1.9.4, same inverter.

The MID grid-tied map corrected the identical mistake in v0.8.6. This map kept the old
mapping, so the correction was only ever half applied.
"""
from __future__ import annotations

import importlib
import sys

import pytest

sys.path.insert(0, "tests")

REGISTERS = importlib.import_module("growatt_under_test.profiles").REGISTER_MAPS

MOD_XH = "MOD_6000_15000TL3_XH"
MID_GRID_TIED = "MID_15000_25000TL3_X_V201"


def _sources_for(profile: str, target: str) -> set[int]:
    """Every register the coordinator would resolve for a given name."""
    return {
        addr for addr, info in REGISTERS[profile]["input_registers"].items()
        if info.get("name") == target
        or info.get("alias") == target
        or info.get("maps_to") == target
    }


def test_active_power_is_not_offered_as_grid_export():
    """THE regression. While 31101 answers `power_to_grid_low`, any MOD-XH whose 3043/3044
    read zero - which is what "no grid flow" looks like - falls through to the inverter's
    own output and reports it as export."""
    assert 31101 not in _sources_for(MOD_XH, "power_to_grid_low"), (
        "31101 claims to be grid export again; it is the inverter's AC output, and two "
        "devices measured it being published as export while nothing flowed to the grid"
    )


def test_grid_export_on_mod_xh_comes_only_from_the_3000_range():
    """Restores the behaviour that was correct on v1.8.14: with no grid flow, 3043/3044
    read zero and zero is what gets published."""
    assert _sources_for(MOD_XH, "power_to_grid_low") == {3044}


def test_active_power_is_still_mapped_under_its_own_name():
    """Removing the wrong `maps_to` must not lose the register. It is a real measurement -
    just of the inverter's output, not of the grid."""
    register = REGISTERS[MOD_XH]["input_registers"][31101]

    assert register["name"] == "ac_active_power_low"
    assert register.get("maps_to") is None
    assert register["signed"] is True


def test_the_batteryless_mid_fix_is_not_undone():
    """#228: a grid-tied MID with a real smart meter needs 31112/31113, because its
    3043/3044 return zero. That fallback must survive this correction - the two profiles are
    different maps and the mistake was only ever in one of them."""
    sources = _sources_for(MID_GRID_TIED, "power_to_grid_low")

    assert 31113 in sources, (
        "the MID meter fallback has been removed; a metered grid-tied MID would report no "
        "grid flow at all"
    )
    assert 31101 not in sources, "the MID map should never have offered active power either"


@pytest.mark.parametrize(
    "pv, battery_charge, battery_discharge, load, active_power",
    [
        (2557.2, 1796.0, 0.0, 780.2, 702.7),   # MOD 10KTL3-HU, v1.9.4 diagnostics
        (1635.9, 0.0, 2004.0, 3647.8, 3574.0),  # MOD TL3-XH
    ],
)
def test_the_reported_numbers_really_do_balance_without_grid_flow(
    pv, battery_charge, battery_discharge, load, active_power
):
    """Rule 4, applied to the evidence rather than the code.

    The claim is that these two systems were self-consuming, so a non-zero export was
    impossible. If that arithmetic does not hold, the whole diagnosis is wrong and this file
    should be revisited rather than quietly protecting a mistaken fix.
    """
    implied_grid = pv + battery_discharge - battery_charge - load
    assert abs(implied_grid) < 100, (
        f"the balance implies {implied_grid:.0f} W of grid flow, so export was not "
        f"impossible and the reasoning behind this fix needs re-checking"
    )
    assert active_power > 500, (
        "active power was not large enough to have been mistaken for export"
    )
