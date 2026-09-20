"""Battery cluster 2 was read and thrown away (#451).

A MID 25kTL3-XH owner with two physical APX packs saw only one pack's power in Home
Assistant: 8,145 W against a raw Modbus dump showing 8,048 W (pack 1) + 3,951 W (pack 2).

The driver already reads a second battery cluster dynamically - growatt_modbus.py sets
batteryN_voltage/_power/_soc/etc. via setattr() whenever batteryN_voltage answers > 0
(31300-31399 on this register map, mirroring cluster 1 at 31200-31299) - and sensor.py
already has generated SENSOR_DEFINITIONS entries for all of it, gated by
`hasattr(data, 'batteryN_voltage')`, which is a genuine test per CLAUDE.md rule 6 because
the attribute is never declared on the GrowattData dataclass.

Two things stopped it reaching Home Assistant regardless:

1. mod_6000_15000tl3_xh_v201 and mid_11000_30000tl3_xh_v201 - which the profile's own
   comment says share this exact register map and hardware - never included
   BATTERY2_SENSORS in their `sensors` set, so the platform never created the entities at
   all, no matter what the driver read.
2. The generated sensor for the "current" field pointed its `attr` at `batteryN_current`,
   but the driver only ever sets `batteryN_current_low` (the 32-bit pair's combined value,
   same convention as `battery_current_low` on cluster 1). That sensor would have read
   unavailable forever, on any profile that already listed BATTERY2_SENSORS (WIT).

3. mod.py hand-copies the cluster-2 block instead of importing VPP_V201_BATTERY2 from
   vpp_v201.py the way every other consumer does (SPH, TL-XH, SPH-TL3, WIT-XHU, and MOD's
   own cluster 3/4 via `**VPP_V201_BATTERY3`/`**VPP_V201_BATTERY4`), and the copy had
   drifted: its four energy registers carried a `_low` suffix that battery2_power right
   above them does not, and that the driver's search list does not expect. The reporter's
   debug log proved this precisely - the block read for 31300-31323 succeeded on multiple
   polls, `Battery 2: 30.9V SOC=10% P=0W` logged correctly each time, and the four energy
   fields were still never set, because `_find_register_by_name` was asked for a name that
   existed nowhere in the map (#451, second report).
"""
from __future__ import annotations

import importlib
import re
from pathlib import Path

_gm = importlib.import_module("growatt_under_test.growatt_modbus")
_dp = importlib.import_module("growatt_under_test.device_profiles")
_const = importlib.import_module("growatt_under_test.const")

COMPONENT_DIR = Path(_dp.__file__).parent
REGISTER_MAPS = _const.REGISTER_MAPS

# Exactly the driver's own search list in _read_battery_data (growatt_modbus.py), so this
# test drifts with the code it is checking rather than needing to be kept in sync by hand.
_CLUSTER_FIELDS = (
    "power", "current_low", "soc", "soh", "temp",
    "charge_energy_today", "charge_energy_total",
    "discharge_energy_today", "discharge_energy_total",
)


def test_every_real_register_map_names_cluster_fields_the_way_the_driver_searches():
    """Whichever cluster N a register map offers (batteryN_voltage present), it must offer
    every field the driver's loop looks for, under the exact name the loop searches for -
    voltage is set separately and is not in _CLUSTER_FIELDS above, only gates the rest."""
    for map_key, register_map in REGISTER_MAPS.items():
        regs = register_map.get("input_registers", {})
        names = {info.get("name") for info in regs.values()} | {
            info.get("alias") for info in regs.values() if info.get("alias")
        } | {
            info.get("maps_to") for info in regs.values() if info.get("maps_to")
        }

        for n in (2, 3, 4):
            if f"battery{n}_voltage" not in names:
                continue  # this map doesn't offer cluster n at all - nothing to check
            missing = [
                f"battery{n}_{field}" for field in _CLUSTER_FIELDS
                if f"battery{n}_{field}" not in names
            ]
            assert not missing, (
                f"{map_key} offers battery{n}_voltage but not {missing} - the driver's "
                f"dynamic reader will never find these fields even on hardware that "
                f"populates the registers"
            )

# Battery cluster 2, at the same relative layout as cluster 1 (31200-31299).
CLUSTER2_MAP = {
    "name": "MOD-style test map",
    "input_registers": {
        31300: {"name": "battery2_power_high", "scale": 1, "unit": "", "pair": 31301},
        31301: {"name": "battery2_power", "scale": 1, "unit": "", "pair": 31300,
                "combined_scale": 0.1, "combined_unit": "W", "signed": True},
        31314: {"name": "battery2_voltage", "scale": 0.1, "unit": "V", "signed": True},
        31315: {"name": "battery2_current_high", "scale": 1, "unit": "", "pair": 31316},
        31316: {"name": "battery2_current_low", "scale": 1, "unit": "", "pair": 31315,
                "combined_scale": 0.1, "combined_unit": "A", "signed": True},
        31317: {"name": "battery2_soc", "scale": 1, "unit": "%"},
        31318: {"name": "battery2_soh", "scale": 1, "unit": "%"},
        31323: {"name": "battery2_temp", "scale": 0.1, "unit": "°C", "signed": True},
    },
}


def _client(cache: dict) -> _gm.GrowattModbus:
    c = _gm.GrowattModbus.__new__(_gm.GrowattModbus)
    c.register_map = CLUSTER2_MAP
    c._register_cache = cache
    c._battery_voltage_range = "Auto-detect"
    c._cached_battery_soc = None
    c._pair_shape_suspect = {}
    c._pair_shape_warned = set()
    c._underflow_warned = set()
    c._battery_power_scale_override = None
    return c


# ---------------------------------------------------------------------------
# 1. The driver genuinely reads cluster 2, under the names sensor.py must use.
# ---------------------------------------------------------------------------

def test_a_populated_cluster_2_is_read_dynamically():
    """Rocko84's pack 2, at the moment his scan caught it: 397.6 V, -47.3 W (discharging)."""
    client = _client({
        31314: 3976,                       # battery2_voltage -> 397.6 V
        31315: 0xFFFF, 31316: 60396,       # battery2_current_low, signed -> -47.3 A ish
        31300: 0xFFFF, 31301: 60396,       # battery2_power, signed
        31317: 97, 31318: 100, 31323: 438,
    })
    data = _gm.GrowattData()
    client._read_battery_data(data)

    assert data.battery2_voltage == 397.6
    # THE bug: the value lives under battery2_current_low, never battery2_current.
    assert hasattr(data, "battery2_current_low")
    assert not hasattr(data, "battery2_current")
    assert hasattr(data, "battery2_power")
    assert data.battery2_soc == 97.0


def test_an_absent_cluster_2_sets_nothing():
    """A single-pack installation must not grow phantom cluster-2 attributes."""
    client = _client({})  # cluster 2's own voltage register never answers
    data = _gm.GrowattData()
    client._read_battery_data(data)

    assert not hasattr(data, "battery2_voltage")
    assert not hasattr(data, "battery2_power")


def test_a_zero_voltage_cluster_2_is_treated_as_not_present():
    """Same firmware, no second pack fitted: the register answers, but with 0."""
    client = _client({31314: 0})
    data = _gm.GrowattData()
    client._read_battery_data(data)

    assert not hasattr(data, "battery2_voltage")


# ---------------------------------------------------------------------------
# 2. sensor.py: the generated "current" sensor must point at the name above.
# ---------------------------------------------------------------------------

def _sensor_py_text() -> str:
    return (COMPONENT_DIR / "sensor.py").read_text(encoding="utf-8")


def test_the_generated_current_sensor_points_at_the_low_suffixed_attr():
    """Source-level, like test_sensor_conditions.py - sensor.py needs a real Home
    Assistant install to import, so this is the only way to check it without one."""
    text = _sensor_py_text()
    start = text.index("Battery clusters 2 / 3 / 4")
    block = text[start:start + 2000]
    assert '"_low" if field == "current"' in block, (
        "the current field's attr no longer accounts for the _low suffix the driver uses "
        "- battery2_current/battery3_current/battery4_current would read unavailable"
    )


# ---------------------------------------------------------------------------
# 3. device_profiles.py: MOD/MID's shared register map must offer cluster 2.
# ---------------------------------------------------------------------------

def _profile_sensors(profile_id: str) -> set[str]:
    return set(_dp.INVERTER_PROFILES[profile_id]["sensors"])


def test_mod_and_mid_v201_both_offer_battery_cluster_2():
    """Both profile keys point at MOD_6000_15000TL3_XH, which defines the cluster-2
    registers - the sensor set must actually offer them, on both aliases (#451)."""
    battery2_keys = set(_dp.BATTERY2_SENSORS)
    assert battery2_keys, "BATTERY2_SENSORS is empty - nothing to test against"

    for profile_id in ("mod_6000_15000tl3_xh_v201", "mid_11000_30000tl3_xh_v201"):
        sensors = _profile_sensors(profile_id)
        missing = battery2_keys - sensors
        assert not missing, (
            f"{profile_id} is missing battery cluster 2 sensors despite sharing MOD's "
            f"register map, which defines the registers: {sorted(missing)}"
        )


def test_mod_and_mid_share_the_same_register_map():
    """The premise the fix depends on: if this ever diverges, adding BATTERY2_SENSORS to
    one and not the other would need reconsidering."""
    mod = _dp.INVERTER_PROFILES["mod_6000_15000tl3_xh_v201"]["register_map"]
    mid = _dp.INVERTER_PROFILES["mid_11000_30000tl3_xh_v201"]["register_map"]
    assert mod == mid == "MOD_6000_15000TL3_XH"
