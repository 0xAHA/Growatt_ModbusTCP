"""Dry Contact State only where a register exists; SPH V2.01 no longer reads 3000+ (#470).

**Dry Contact State** sat in STATUS_SENSORS, which nearly every profile includes, while its
register (input 3119) was mapped on six. `dry_contact_state` is a dataclass field, so on the
other 24 profiles the entity existed with nothing behind it and showed a permanent "Off".
Profile membership is the only real filter (CLAUDE.md rule 6), so the sensor is now offered
exactly where the register is mapped.

**SPH V2.01** mapped 3071-3078 and 3119 in the 3000 input range. The storage range supplies
the same energy counters and is found first, so those addresses were never used for a value.
On three DTC 3501 units the range held only zeros or one value repeated (3293). The read they
caused, 3000-3119, came back from one SPH6000's bridge as an 89-register frame on every
retry.
"""
from __future__ import annotations

import importlib

import pytest

_gm = importlib.import_module("growatt_under_test.growatt_modbus")
_dp = importlib.import_module("growatt_under_test.device_profiles")
_profiles = importlib.import_module("growatt_under_test.profiles")

SPH_V201 = ("SPH_3000_6000_V201", "SPH_7000_10000_V201")


def _maps_dry_contact(register_map: str) -> bool:
    inputs = _profiles.REGISTER_MAPS.get(register_map, {}).get("input_registers", {})
    return any(r.get("name") == "dry_contact_state" for r in inputs.values())


@pytest.mark.parametrize("key", sorted(_dp.INVERTER_PROFILES))
def test_dry_contact_state_is_offered_exactly_where_it_is_mapped(key):
    profile = _dp.INVERTER_PROFILES[key]
    offered = "dry_contact_state" in profile["sensors"]
    mapped = _maps_dry_contact(profile.get("register_map", ""))
    assert offered == mapped, (
        f"{key}: offered={offered} but register mapped={mapped} - an unmapped sensor reads a "
        f"permanent default, a mapped one should be offered"
    )


@pytest.mark.parametrize("register_map", SPH_V201)
def test_sph_v201_maps_nothing_in_the_3000_input_range(register_map):
    inputs = _profiles.REGISTER_MAPS[register_map]["input_registers"]
    assert not [a for a in inputs if 3000 <= a < 4000]


def _poll(register_map: str, inputs: dict):
    client = _gm.GrowattModbus(connection_type="tcp", host="10.0.0.1", port=502,
                               slave_id=1, register_map=register_map)
    calls: list[int] = []

    def read_input_registers(start, count, log_errors=True):
        calls.append(start)
        return [inputs.get(a, 0) for a in range(start, start + count)]

    client.read_input_registers = read_input_registers
    client.read_holding_registers = lambda start, count: [0] * count
    return client.read_all_data(), calls


@pytest.mark.parametrize("register_map", SPH_V201)
def test_sph_v201_poll_never_requests_3000_and_still_has_its_energy(register_map):
    # Storage range: grid export today 1049 = 12.3 kWh, load today 1061 = 8.4 kWh.
    data, calls = _poll(register_map, {1049: 123, 1061: 84})
    assert not [s for s in calls if 3000 <= s < 4000], calls
    assert round(data.energy_to_grid_today, 1) == 12.3
    assert round(data.load_energy_today, 1) == 8.4
