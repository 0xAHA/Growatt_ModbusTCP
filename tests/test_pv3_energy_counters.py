"""A profile that declares three strings must count three strings (#381).

`use_mppt_energy_today` sums the per-string DC energy counters instead of the AC register,
because the AC one includes battery discharge. That is right, but it means a string with no
mapped counter is silently dropped from the daily solar figure while its power sensors keep
working — nothing errors, and the shortfall looks like under-generation.

Measured on a MID 25KTL3-XH: daily solar 17.6 kWh against the portal's 29.5, the difference
being PV3 exactly. `MOD_6000_15000TL3_XH` jumped from register 66 to 91 with no PV3 entry.

The mapping was established by prediction rather than by pattern-matching: PV3 lifetime was
derived as 91/92 minus PV1 minus PV2 = 1542.4 kWh, predicting a raw 15424 at 69/70, and the
scan returned 15424. 67/68 returned 119, and 9.4 + 8.2 + 11.9 = 29.5 reconciled the daily
figure to the portal to the decimal.
"""
from __future__ import annotations

import importlib

import pytest

_dp = importlib.import_module("growatt_under_test.device_profiles")
_profiles = importlib.import_module("growatt_under_test.profiles")

INVERTER_PROFILES = _dp.INVERTER_PROFILES

# The reporting device, so the numbers below are a real reading rather than an example.
MID_PV1_TOTAL = 1268.4
MID_PV2_TOTAL = 801.1
MID_PV3_TOTAL = 1542.4
MID_PV_TOTAL_ALL_STRINGS = 3611.9


def _input_names(map_name: str) -> set[str]:
    rmap = _profiles.get_profile(map_name)
    assert rmap is not None, f"{map_name} does not resolve"
    return {r["name"] for r in rmap.get("input_registers", {}).values()}


def test_the_mod_map_maps_pv3_energy():
    """The confirmed case."""
    names = _input_names("MOD_6000_15000TL3_XH")
    for name in ("pv3_energy_today_high", "pv3_energy_today_low",
                 "pv3_energy_total_high", "pv3_energy_total_low"):
        assert name in names, f"MOD_6000_15000TL3_XH is missing {name}"


def test_pv3_energy_sits_at_the_documented_addresses():
    """Protocol V1.39: 67/68 Epv3_today, 69/70 Epv3_total — input registers. Holding 67-70
    are grid protection limits, which is why the space matters."""
    regs = _profiles.get_profile("MOD_6000_15000TL3_XH")["input_registers"]
    assert regs[67]["name"] == "pv3_energy_today_high"
    assert regs[68]["name"] == "pv3_energy_today_low"
    assert regs[69]["name"] == "pv3_energy_total_high"
    assert regs[70]["name"] == "pv3_energy_total_low"


def test_the_pairing_follows_the_maps_own_convention():
    """High word pairs with low, low carries the combined scale. Getting this backwards
    produces a number 65536 times too large, which is the shape of several past bugs."""
    regs = _profiles.get_profile("MOD_6000_15000TL3_XH")["input_registers"]
    assert regs[67]["pair"] == 68 and regs[68]["pair"] == 67
    assert regs[69]["pair"] == 70 and regs[70]["pair"] == 69
    assert regs[68]["combined_scale"] == 0.1
    assert regs[70]["combined_scale"] == 0.1
    assert "combined_scale" not in regs[67]
    assert "combined_scale" not in regs[69]


def test_the_reported_values_reconcile():
    """Guards the arithmetic the mapping was derived from, so a future edit that changes
    the scale cannot quietly break the relationship that identified these registers."""
    assert MID_PV1_TOTAL + MID_PV2_TOTAL + MID_PV3_TOTAL == pytest.approx(
        MID_PV_TOTAL_ALL_STRINGS
    ), "per-string totals no longer sum to the all-strings register"

    raw_high, raw_low = 0, 15424
    assert round(((raw_high << 16) | raw_low) * 0.1, 1) == MID_PV3_TOTAL


@pytest.mark.parametrize(
    "profile_key",
    sorted(k for k, p in INVERTER_PROFILES.items() if p.get("has_pv3")),
)
def test_every_three_string_profile_can_count_its_third_string(profile_key):
    """The general rule. A profile claiming PV3 while summing only two strings under-reports
    daily solar for the life of the install, with nothing to indicate it.

    Excluded: profiles whose map already uses 67-70 for something else. TL_XH_3000_10000
    maps 69/70 as energy_to_grid_today, which contradicts Protocol V1.39 and needs its own
    evidence before either mapping is disturbed.
    """
    map_name = INVERTER_PROFILES[profile_key]["register_map"]
    names = _input_names(map_name)

    if not {"pv1_energy_total_high", "pv2_energy_total_high"} <= names:
        pytest.skip(f"{map_name} does not use per-string energy counters")

    if "energy_to_grid_today_high" in names:
        rmap = _profiles.get_profile(map_name)["input_registers"]
        if rmap.get(69, {}).get("name") == "energy_to_grid_today_high":
            pytest.skip(f"{map_name} maps 69/70 as grid export — see the TL-XH conflict")

    assert "pv3_energy_total_high" in names, (
        f"{profile_key} declares has_pv3 and sums per-string energy, but {map_name} has no "
        f"PV3 energy counter — its third string is missing from the daily solar total"
    )
