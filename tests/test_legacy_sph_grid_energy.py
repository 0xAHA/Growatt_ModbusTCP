"""Legacy SPH profiles must map the grid import/export energy block (#395).

`SPH_3000_6000` and `SPH_7000_10000` had no grid or user *energy* register at all - only
*power* registers - while their V2.01 siblings mapped 1044-1051. The lookup is by name, so
it found nothing and the field kept its dataclass default: Export Energy Today and Total
were not reading the wrong register, they were reading nothing, and published a plausible
small number that never moved.

Confirmed on an SPH 5000 against ShinePhone and the Growatt cloud, and corroborated by a
second user's diagnostics showing `energy_to_grid_total = 3.4 kWh` on an installed unit.
"""
import importlib
import sys

import pytest

sys.path.insert(0, "tests")

_sph = importlib.import_module("growatt_under_test.profiles.sph")

GRID_ENERGY_BLOCK = {
    1044: "energy_to_user_today_high",
    1045: "energy_to_user_today_low",
    1046: "energy_to_user_total_high",
    1047: "energy_to_user_total_low",
    1048: "energy_to_grid_today_high",
    1049: "energy_to_grid_today_low",
    1050: "energy_to_grid_total_high",
    1051: "energy_to_grid_total_low",
}

# Every SPH map that carries the 1000-range storage block, legacy and V2.01 alike. The
# legacy pair is the point of this test; the V2.01 ones are here so the two cannot drift
# apart again without something failing.
PROFILES = [
    "SPH_3000_6000",
    "SPH_7000_10000",
    "SPH_3000_6000_V201",
    "SPH_7000_10000_V201",
]


@pytest.mark.parametrize("profile_name", PROFILES)
def test_grid_energy_registers_are_mapped(profile_name):
    registers = getattr(_sph, profile_name)["input_registers"]
    missing = [r for r in GRID_ENERGY_BLOCK if r not in registers]
    assert not missing, (
        f"{profile_name} does not map {missing} - grid import/export energy will publish "
        f"a default rather than a reading"
    )


@pytest.mark.parametrize("profile_name", PROFILES)
def test_the_names_match_what_the_lookup_searches_for(profile_name):
    """The coordinator finds these by name, not by address. A suffixed name here would map
    the register and still leave the sensor reading its default."""
    registers = getattr(_sph, profile_name)["input_registers"]
    for address, expected in GRID_ENERGY_BLOCK.items():
        assert registers[address]["name"] == expected, (
            f"{profile_name} register {address} is named "
            f"{registers[address]['name']!r}, so the lookup for {expected!r} will miss it"
        )


@pytest.mark.parametrize("profile_name", PROFILES)
def test_the_pairs_point_at_each_other(profile_name):
    """32-bit values combine as (high << 16) | low. A pair pointing at the wrong partner
    produces a large, plausible, monotonically rising number - the hardest kind to notice."""
    registers = getattr(_sph, profile_name)["input_registers"]
    for high in (1044, 1046, 1048, 1050):
        low = high + 1
        assert registers[high]["pair"] == low, f"{profile_name}: {high} does not pair to {low}"
        assert registers[low]["pair"] == high, f"{profile_name}: {low} does not pair to {high}"
        assert registers[low]["combined_scale"] == 0.1, (
            f"{profile_name}: {low} is missing the 0.1 combined scale"
        )


@pytest.mark.parametrize("profile_name", PROFILES)
def test_input_1044_and_holding_1044_stay_distinct(profile_name):
    """Input and holding overlap throughout this protocol. Holding 1044 is Priority Mode;
    input 1044 is grid import energy. Two separate issues landed on the same day naming
    "register 1044", one meaning each - so this is worth pinning."""
    profile = getattr(_sph, profile_name)
    assert profile["input_registers"][1044]["name"] == "energy_to_user_today_high"
    assert profile["holding_registers"][1044]["name"] == "priority_mode"
