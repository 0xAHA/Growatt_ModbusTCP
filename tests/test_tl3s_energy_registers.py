"""TL3-S energy counters and per-phase AC follow V3.14 (#508).

The profile read Energy Today from input 53 and Energy Total from 55 as standalone 16-bit
values. In V3.14 those are the LOW words of Epv2_today and Epv2_total: Energy Today showed
string 2 only (5.5 kWh where the app showed 11.1), and Energy Total wrapped every 6553.6 kWh.

The words below are the #299 TL3-S reference scan (DH1.0 firmware). Every pair agrees with
V3.14: PV1 + PV2 lifetime totals add up to the Epv_total register exactly.
"""
from __future__ import annotations

import importlib

import pytest

_gm = importlib.import_module("growatt_under_test.growatt_modbus")
_dp = importlib.import_module("growatt_under_test.device_profiles")
_profiles = importlib.import_module("growatt_under_test.profiles")

TL3S = _profiles.REGISTER_MAPS["TL3_S_3000_15000"]

SCAN_299 = {
    0: 1, 1: 0, 2: 60163, 3: 5103, 4: 58, 5: 0, 6: 29597, 7: 5270, 8: 58,
    26: 0, 27: 100, 28: 11, 29: 7811,
    48: 0, 49: 52, 50: 5, 51: 49703, 52: 0, 53: 54, 54: 5, 55: 61329,
    56: 11, 57: 45496,
}


def _poll(inputs: dict):
    client = _gm.GrowattModbus(connection_type="tcp", host="10.0.0.1", port=502,
                               slave_id=1, register_map="TL3_S_3000_15000")
    client.read_input_registers = (
        lambda start, count, log_errors=True: [inputs.get(a, 0) for a in range(start, start + count)]
    )
    client.read_holding_registers = lambda start, count: [0] * count
    return client.read_all_data()


def test_energy_today_is_the_inverter_total_not_string_two():
    """THE #508 regression: this read 5.4 kWh (PV2 today) instead of 10.0."""
    assert _poll(SCAN_299).energy_today == pytest.approx(10.0)


def test_energy_total_uses_both_words():
    """Was 6132.9 kWh: the low word of PV2's lifetime total."""
    assert _poll(SCAN_299).energy_total == pytest.approx(72870.7)


def test_per_string_counters():
    data = _poll(SCAN_299)
    assert data.pv1_energy_today == pytest.approx(5.2)
    assert data.pv2_energy_today == pytest.approx(5.4)
    assert data.pv1_energy_total == pytest.approx(37738.3)
    assert data.pv2_energy_total == pytest.approx(38900.9)
    assert data.pv_energy_total == pytest.approx(76639.2)


def test_string_totals_add_up_to_pv_total():
    """Internal consistency of the scan that justifies the mapping."""
    data = _poll(SCAN_299)
    assert data.pv1_energy_total + data.pv2_energy_total == pytest.approx(data.pv_energy_total)


@pytest.mark.parametrize("name", [
    "energy_today", "energy_total",
    "pv1_energy_today", "pv2_energy_today",
    "pv1_energy_total", "pv2_energy_total", "pv_energy_total",
])
def test_every_counter_is_a_pair_with_a_sensor(name):
    inputs = TL3S["input_registers"]
    low = next(a for a, r in inputs.items() if r["name"] == f"{name}_low")
    high = next(a for a, r in inputs.items() if r["name"] == f"{name}_high")
    assert inputs[low]["pair"] == high and inputs[high]["pair"] == low
    assert high == low - 1
    assert inputs[low]["combined_scale"] == 0.1
    assert name in _dp.INVERTER_PROFILES["tl3_s_3000_15000"]["sensors"]


# A 9000TL3-S, input 14-25 at 10:52, beside its app (#508): AC1 409.8 V / 4.1 A / 968 W,
# AC2 406.6 V / 4.2 A / 983.9 W, AC3 407.6 V / 4.4 A / 1033.3 W.
PHASES_1052 = {14: 4096, 15: 42, 16: 0, 17: 9912, 18: 4066, 19: 42, 20: 0, 21: 9839,
               22: 4074, 23: 44, 24: 0, 25: 10328}


def test_phase_groups_follow_v314_order():
    """Voltage and current were read one group late: R showed AC2, S showed AC3, T nothing."""
    data = _poll({**SCAN_299, **PHASES_1052})
    assert (data.ac_voltage_r, data.ac_current_r, data.ac_power_r) == pytest.approx((409.6, 4.2, 991.2))
    assert (data.ac_voltage_s, data.ac_current_s, data.ac_power_s) == pytest.approx((406.6, 4.2, 983.9))
    assert (data.ac_voltage_t, data.ac_current_t, data.ac_power_t) == pytest.approx((407.4, 4.4, 1032.8))


def test_generic_ac_voltage_and_current_stay_on_phase_one():
    data = _poll({**SCAN_299, **PHASES_1052})
    assert data.ac_voltage == pytest.approx(409.6)
    assert data.ac_current == pytest.approx(4.2)
