"""A V2.01 profile on V1.39 hardware must still read battery energy (#377).

The V2.01 SPH profiles are selected by display name, and "SPH (3-6kW)" resolves to the
V2.01 variant whenever `vpp_protocol_confirmed` is set on the entry. A device whose DTC came
from holding 43 - no VPP support - can therefore end up on a V2.01 profile, and its poll
never touches the 31000 range at all.

With the canonical names on the VPP side, that produced a permanent 0.0 for battery charge
and discharge energy: the only register under the name the coordinator looks for was one the
hardware never answers. Battery voltage and SOC worked on the same device, because 1013/1014
carry the canonical names and 31214/31217 carry `_vpp` plus `maps_to`.

Values below are from the reporting SPH 3600, cross-checked against ShinePhone.
"""
from __future__ import annotations

import importlib

import pytest

_gm = importlib.import_module("growatt_under_test.growatt_modbus")
_profiles = importlib.import_module("growatt_under_test.profiles")

V201_MAPS = ["SPH_3000_6000_V201", "SPH_7000_10000_V201"]

# His registers, and what ShinePhone showed for them.
LEGACY_CACHE = {
    1052: 0, 1053: 7,       # discharge today  0.7
    1054: 1, 1055: 4319,    # discharge total  6985.5
    1056: 0, 1057: 20,      # charge today     2.0
    1058: 0, 1059: 65165,   # charge total     6516.5
    1013: 532, 1014: 98,
}

VPP_CACHE = {
    31202: 0, 31203: 111,   # charge today     11.1
    31204: 0, 31205: 2222,  # charge total     222.2
    31206: 0, 31207: 333,   # discharge today  33.3
    31208: 0, 31209: 4444,  # discharge total  444.4
    31214: 532, 31217: 98,
}


def _read(map_name: str, cache: dict):
    client = _gm.GrowattModbus(connection_type="tcp", host="10.0.0.1", port=502,
                              register_map=map_name)
    client._register_cache = dict(cache)
    data = _gm.GrowattData()
    client._read_battery_data(data)
    return data


@pytest.mark.parametrize("map_name", V201_MAPS)
def test_legacy_hardware_on_a_v201_profile_reads_battery_energy(map_name):
    """The reported failure. No VPP range in the cache, because the poll never reads it."""
    data = _read(map_name, LEGACY_CACHE)
    assert data.charge_energy_today == pytest.approx(2.0), (
        "battery charge energy is still 0.0 for a V1.39 device on a V2.01 profile"
    )
    assert data.charge_energy_total == pytest.approx(6516.5)
    assert data.discharge_energy_today == pytest.approx(0.7)
    assert data.discharge_energy_total == pytest.approx(6985.5)


@pytest.mark.parametrize("map_name", V201_MAPS)
def test_a_real_v201_device_is_unaffected(map_name):
    """The fallback must not steal from hardware that does answer the VPP range."""
    data = _read(map_name, VPP_CACHE)
    assert data.charge_energy_today == pytest.approx(11.1)
    assert data.charge_energy_total == pytest.approx(222.2)
    assert data.discharge_energy_today == pytest.approx(33.3)
    assert data.discharge_energy_total == pytest.approx(444.4)


@pytest.mark.parametrize("map_name", V201_MAPS)
def test_the_canonical_name_is_on_the_legacy_side(map_name):
    """The convention, stated as a rule rather than left implicit: the 1000-range register
    carries the name the coordinator looks for, the VPP one carries _vpp plus maps_to.
    battery_voltage and battery_soc already do this in the same profiles."""
    regs = _profiles.get_profile(map_name)["input_registers"]
    assert regs[1057]["name"] == "battery_charge_today_low"
    assert regs[31203]["name"] == "battery_charge_today_vpp_low"
    assert regs[31203]["maps_to"] == "battery_charge_today_low"


@pytest.mark.parametrize("map_name", V201_MAPS)
def test_every_vpp_energy_register_has_a_route_back(map_name):
    """A _vpp name with no maps_to is unreachable — the coordinator would never look it up
    under that name, so the VPP side would silently stop working."""
    regs = _profiles.get_profile(map_name)["input_registers"]
    for addr in (31203, 31205, 31207, 31209):
        assert "maps_to" in regs[addr], f"{addr} has no maps_to, so the VPP fallback is dead"
