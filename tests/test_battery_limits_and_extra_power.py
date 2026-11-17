"""Battery power limits and pack description (#507); WIT extra power reaching its sensor (#503).

**#507.** VPP input 31210-31213 (maximum allowable battery charge / discharge power) was
mapped on WIT and MOD TL3-XH and polled, but had no sensor. Field readings:

    WIT 15K (#507)            11426.4 W / 12140.5 W   1 cluster, 2 modules, 51.2 V
    WIT 4-15K (#226 scan)      7891.2 W / 14796.0 W   1 cluster, 3 modules, 51.2 V
    MID 17KTL3-XH (#240 scan)  7500.0 W /  1875.0 W   1 cluster, 3 modules, 51.2 V, 99.9 Ah

Module rated capacity (31228) read 0 on both WITs, so it is not mapped there.

**#503 follow-up.** v2.0.7 decoded WIT 8102-8103 correctly, and its tests checked the decode,
but nothing copied the decoded pair into `extra_power_to_grid`: the sensor published its
0.0 default whatever the register said. Extra Energy Today / Total had the same gap. These
tests poll through `read_all_data`, so they check the value that reaches the data the
sensors read, not only the decode.
"""
from __future__ import annotations

import importlib

import pytest

_gm = importlib.import_module("growatt_under_test.growatt_modbus")
_dp = importlib.import_module("growatt_under_test.device_profiles")
_profiles = importlib.import_module("growatt_under_test.profiles")

LIMITS = {"battery_max_charge_power", "battery_max_discharge_power"}
WIT_PACK = {"battery_cluster_sum", "battery_module_number", "battery_module_rated_voltage"}


def _poll(register_map: str, inputs: dict, failing: tuple = ()):
    """Poll once. A read whose range covers an address in `failing` returns None."""
    client = _gm.GrowattModbus(connection_type="tcp", host="10.0.0.1", port=502,
                               slave_id=1, register_map=register_map)

    def read_input_registers(start, count, log_errors=True):
        if any(start <= a < start + count for a in failing):
            return None
        return [inputs.get(a, 0) for a in range(start, start + count)]

    client.read_input_registers = read_input_registers
    client.read_holding_registers = lambda start, count: [0] * count
    return client.read_all_data()


# Wojak129's WIT 15K (#507), plus mihaelko's 8102-8103 words (#503).
WIT_15K = {31210: 1, 31211: 48728, 31212: 1, 31213: 55869,
           31225: 1, 31226: 2, 31227: 512, 31228: 0,
           8102: 65535, 8103: 39483, 8104: 0, 8105: 55, 8106: 0, 8107: 12345}

# MID 17KTL3-XH scan from #240 (DTC 5400, served by the MOD TL3-XH map).
MID_17K = {31210: 1, 31211: 9464, 31212: 0, 31213: 18750,
           31225: 1, 31226: 3, 31227: 512, 31228: 999}


def test_wit_battery_power_limits_reach_the_data():
    data = _poll("WIT_4000_15000TL3", WIT_15K)
    assert data.battery_max_charge_power == pytest.approx(11426.4)
    assert data.battery_max_discharge_power == pytest.approx(12140.5)


def test_wit_pack_description_reaches_the_data():
    data = _poll("WIT_4000_15000TL3", WIT_15K)
    assert data.battery_cluster_sum == 1
    assert data.battery_module_number == 2
    assert data.battery_module_rated_voltage == pytest.approx(51.2)


def test_wit_does_not_map_module_rated_capacity():
    inputs = _profiles.REGISTER_MAPS["WIT_4000_15000TL3"]["input_registers"]
    assert 31228 not in inputs


def test_wit_extra_power_to_grid_reaches_the_data():
    """THE #503 regression: decoded as 2605.3 W, published as 0.0 W."""
    data = _poll("WIT_4000_15000TL3", WIT_15K)
    assert data.extra_power_to_grid == pytest.approx(2605.3)


def test_wit_extra_energy_reaches_the_data():
    data = _poll("WIT_4000_15000TL3", WIT_15K)
    assert data.extra_energy_today == pytest.approx(5.5)
    assert data.extra_energy_total == pytest.approx(1234.5)


def test_mod_xh_battery_power_limits_reach_the_data():
    data = _poll("MOD_6000_15000TL3_XH", MID_17K)
    assert data.battery_max_charge_power == pytest.approx(7500.0)
    assert data.battery_max_discharge_power == pytest.approx(1875.0)
    assert data.battery_module_rated_capacity == pytest.approx(99.9)


def test_failed_read_is_unknown_not_zero():
    # The 8000 block and the VPP battery block fail; the base range still answers.
    data = _poll("WIT_4000_15000TL3", WIT_15K, failing=(8103, 31211, 31213))
    for field in LIMITS | {"extra_power_to_grid"}:
        assert field in data.unread_fields, field


@pytest.mark.parametrize("key", sorted(_dp.INVERTER_PROFILES))
def test_limit_sensors_offered_only_where_confirmed(key):
    profile = _dp.INVERTER_PROFILES[key]
    confirmed = profile.get("register_map") in ("WIT_4000_15000TL3", "MOD_6000_15000TL3_XH")
    offered = LIMITS & profile["sensors"]
    assert offered == (LIMITS if confirmed else set()), key


def test_wit_xhu_is_not_offered_the_new_sensors():
    sensors = _dp.INVERTER_PROFILES["wit_29900_50000tl3_xhu"]["sensors"]
    assert not (LIMITS | WIT_PACK) & sensors


def test_wit_4_15k_gets_the_pack_description_but_not_capacity():
    sensors = _dp.INVERTER_PROFILES["wit_4000_15000tl3"]["sensors"]
    assert WIT_PACK <= sensors
    assert "battery_module_rated_capacity" not in sensors
