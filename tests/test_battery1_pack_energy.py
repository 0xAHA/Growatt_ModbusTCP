"""Battery 1's own energy counters on multi-pack MOD/MID (#451).

Battery Charge/Discharge Today/Total come from the inverter's own counters (3125-3132), which
cover every pack. On a MID 25KTL3-XH with two APX packs they equal pack 1 + pack 2 to the
decimal on all four. Battery 2 already had per-pack sensors, but pack 1 had none. Its own
counters are VPP 31202-31209, mapped as *_vpp_* registers that nothing published.

The registers below are the reporter's scan from 18 September 2026.
"""
from __future__ import annotations

import importlib

import pytest

_gm = importlib.import_module("growatt_under_test.growatt_modbus")
_dp = importlib.import_module("growatt_under_test.device_profiles")
_profiles = importlib.import_module("growatt_under_test.profiles")

MAP = "MOD_6000_15000TL3_XH"
FIELDS = ("charge_energy_today", "charge_energy_total",
          "discharge_energy_today", "discharge_energy_total")

SCAN = {
    # Inverter-wide counters (3125-3132)
    3125: 0, 3126: 60, 3127: 0, 3128: 39134, 3129: 0, 3130: 211, 3131: 0, 3132: 38227,
    # Pack 1 (31202-31209)
    31202: 0, 31203: 131, 31204: 0, 31205: 369, 31206: 0, 31207: 32, 31208: 0, 31209: 248,
    # Pack 1 / pack 2 voltage, and pack 2 counters (31302-31309)
    31214: 4018, 31314: 3976,
    31302: 0, 31303: 80, 31304: 0, 31305: 37858, 31306: 0, 31307: 28, 31308: 0, 31309: 38886,
}


def _poll(inputs: dict):
    client = _gm.GrowattModbus(connection_type="tcp", host="10.0.0.1", port=502,
                               slave_id=1, register_map=MAP)
    client.read_input_registers = (
        lambda start, count, log_errors=True: [inputs.get(a, 0) for a in range(start, start + count)]
    )
    client.read_holding_registers = lambda start, count: [0] * count
    return client.read_all_data()


def test_pack_1_reports_its_own_counters():
    data = _poll(SCAN)
    assert [round(getattr(data, f"battery1_{f}"), 1) for f in FIELDS] == [13.1, 36.9, 3.2, 24.8]


def test_pack_1_plus_pack_2_is_the_inverter_total():
    """The reporter's observation, held as a test: the main counters are the sum."""
    data = _poll(SCAN)
    pairs = (("charge_energy_today", 21.1), ("charge_energy_total", 3822.7),
             ("discharge_energy_today", 6.0), ("discharge_energy_total", 3913.4))
    for field, total in pairs:
        both = getattr(data, f"battery1_{field}") + getattr(data, f"battery2_{field}")
        assert round(both, 1) == total, field
        assert round(getattr(data, field), 1) == total, field


def test_a_single_pack_system_gets_no_battery_1_figures():
    """With one pack they would only duplicate the main counters."""
    single = {k: v for k, v in SCAN.items() if not 31300 <= k < 31400}
    data = _poll(single)
    assert not hasattr(data, "battery2_voltage")
    for field in FIELDS:
        assert not hasattr(data, f"battery1_{field}"), field


@pytest.mark.parametrize("key", sorted(_dp.INVERTER_PROFILES))
def test_offered_only_where_pack_1_counters_are_mapped(key):
    profile = _dp.INVERTER_PROFILES[key]
    inputs = _profiles.REGISTER_MAPS.get(profile.get("register_map", ""), {}).get("input_registers", {})
    mapped = any(r.get("name") == "charge_energy_today_vpp_low" for r in inputs.values())
    offered = "battery1_charge_energy_today" in profile["sensors"]
    assert offered == (mapped and "battery2_voltage" in profile["sensors"]), key
