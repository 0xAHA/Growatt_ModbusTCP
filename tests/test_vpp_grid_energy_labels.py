"""VPP input 31118-31133 must carry the meaning every protocol version gives them.

V2.01 through V2.05 agree on 31118-31125: energy to user today / total, energy to grid
today / total, each UINT32 at 0.1 kWh. V2.01-V2.03 reserve 31126 onwards, and V2.04 puts
third-party, GEN-port, EPS and intelligent-load *power* at 31126-31133.

The single-phase profiles had labelled them otherwise: 31118 as load power (W), 31120 and
31122 as inverter energy today / total, and 31130-31132 as inverter, IPM and boost
temperatures, each with a `maps_to` onto a real sensor. None of it ever reached a sensor,
because the native register resolves first on every profile - but a V2.04 WIT read
31131 = 8168, its EPS power, which the old label would have shown as 816.8 C (#481), and
any profile without the native register would have published it.

MID, MOD and SPH-TL3 already used the spec names. This holds every profile to them.
"""
from __future__ import annotations

import importlib

import pytest

_const = importlib.import_module("growatt_under_test.const")
_profiles = importlib.import_module("growatt_under_test.device_profiles")

MAPS = sorted({p["register_map"] for p in _profiles.INVERTER_PROFILES.values()
               if p["register_map"] in _const.REGISTER_MAPS})

SPEC_PREFIX = {
    31118: "energy_to_user_today", 31119: "energy_to_user_today",
    31120: "energy_to_user_total", 31121: "energy_to_user_total",
    31122: "energy_to_grid_today", 31123: "energy_to_grid_today",
    31124: "energy_to_grid_total", 31125: "energy_to_grid_total",
}


def _inputs(name):
    return _const.REGISTER_MAPS[name]["input_registers"]


@pytest.mark.parametrize("map_name", MAPS)
def test_grid_energy_counters_carry_their_spec_names(map_name):
    regs = _inputs(map_name)
    wrong = {addr: regs[addr]["name"] for addr, prefix in SPEC_PREFIX.items()
             if addr in regs and not regs[addr]["name"].startswith(prefix)}
    assert not wrong, f"{map_name}: {wrong} - see the spec names in SPEC_PREFIX"


@pytest.mark.parametrize("map_name", MAPS)
def test_no_temperature_is_mapped_into_the_v204_power_block(map_name):
    regs = _inputs(map_name)
    temps = [a for a in range(31126, 31134)
             if a in regs and "°C" in (regs[a].get("unit"), regs[a].get("combined_unit"))]
    assert not temps, f"{map_name} maps temperatures at {temps}; V2.04 defines power there"


@pytest.mark.parametrize("map_name", MAPS)
def test_core_readings_never_resolve_into_that_range(map_name):
    """The lookup the poll uses: first match by name, alias or maps_to, in map order."""
    regs = _inputs(map_name)
    for wanted in ("inverter_temp", "ipm_temp", "boost_temp", "energy_today_low",
                   "energy_total_low", "power_to_load", "power_to_load_low", "load_power"):
        for addr, info in regs.items():
            if wanted in (info["name"], info.get("alias"), info.get("maps_to")):
                assert not 31118 <= addr <= 31133, (
                    f"{map_name}: {wanted} resolves to {addr}, a grid-energy / V2.04 power "
                    f"register")
                break
