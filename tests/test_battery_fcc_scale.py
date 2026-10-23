"""Battery full-charge capacity, VPP input 31219-31220, is 0.1 Ah (#482).

A MID 25KTL3-XH with two APX clusters of four 5 kWh modules: module rated capacity 31228 =
1040 (104.0 Ah), cluster FCC 4160, then 3120, 2080 and 1040 as modules went to sleep. At a
scale of 1 that is a 4160 Ah cluster built from 104 Ah modules.
"""
from __future__ import annotations

import importlib

import pytest

_const = importlib.import_module("growatt_under_test.const")

MAPS_WITH_FCC = [name for name, m in _const.REGISTER_MAPS.items()
                 if m.get("input_registers", {}).get(31220, {}).get("name") == "bms_gauge_fcc"]


def test_some_profile_maps_fcc():
    assert MAPS_WITH_FCC


@pytest.mark.parametrize("map_name", MAPS_WITH_FCC)
def test_fcc_is_tenths_of_an_amp_hour(map_name):
    low = _const.REGISTER_MAPS[map_name]["input_registers"][31220]
    assert low["combined_unit"] == "Ah"
    assert 4160 * low["combined_scale"] == pytest.approx(4 * 104.0)


# ---------------------------------------------------------------------------
# Published per cluster on MOD/MID TL3-XH (#482)
# ---------------------------------------------------------------------------

_gm = importlib.import_module("growatt_under_test.growatt_modbus")
_dp = importlib.import_module("growatt_under_test.device_profiles")

MOD_MAP = "MOD_6000_15000TL3_XH"
MOD_PROFILES = [k for k, p in _dp.INVERTER_PROFILES.items() if p["register_map"] == MOD_MAP]

# Robin's scan 2: BMS 1 all four modules, BMS 2 with module 2.2 asleep.
SCAN_2 = {
    31214: 3743, 31219: 0, 31220: 4120, 31225: 2, 31226: 4, 31227: 512, 31228: 1040,
    31314: 3833, 31319: 0, 31320: 3120,
}


def _poll(inputs):
    client = _gm.GrowattModbus(connection_type="tcp", host="10.0.0.1", port=502,
                               slave_id=1, register_map=MOD_MAP)
    client.read_input_registers = (
        lambda start, count, log_errors=True: [inputs.get(a, 0) for a in range(start, start + count)]
    )
    client.read_holding_registers = lambda start, count: [0] * count
    return client.read_all_data()


def test_each_cluster_publishes_its_full_charge_capacity():
    data = _poll(SCAN_2)
    assert round(data.bms_gauge_fcc, 1) == 412.0
    assert round(data.battery2_full_charge_capacity, 1) == 312.0


def test_pack_description_is_read():
    data = _poll(SCAN_2)
    assert (data.battery_cluster_sum, data.battery_module_number) == (2, 4)
    assert round(data.battery_module_rated_capacity, 1) == 104.0


def test_no_battery_2_capacity_without_a_second_pack():
    single = {k: v for k, v in SCAN_2.items() if not 31300 <= k < 31400}
    assert not hasattr(_poll(single), "battery2_full_charge_capacity")


@pytest.mark.parametrize("key", MOD_PROFILES)
def test_mod_profiles_offer_the_pack_and_capacity_sensors(key):
    sensors = _dp.INVERTER_PROFILES[key]["sensors"]
    for name in ("bms_gauge_fcc", "battery2_full_charge_capacity", "battery_module_number",
                 "battery_cluster_sum", "battery_module_rated_capacity"):
        assert name in sensors, (key, name)
