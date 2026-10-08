"""MIN TL-XH time-of-use periods and battery working status (#400, #460).

On a MIN 4200TL-XH, period 1 set in ShinePhone as Battery First 00:00-07:00 read
3038 = 40960 and 3039 = 1792, and moving the end to 07:01 and 07:02 read back 1793 and
1794. That is the MOD TL3-XH packing exactly, and V1.39 documents the same nine "Time n
(xh)" periods for the XH family, so the profile reuses the MOD TOU entities.

Reads are confirmed; Modbus writes are not. The entities are therefore created disabled,
which the profile asks for with `tou_disabled_by_default`.

ShinePhone's Allow Grid Charge setting tracked holding register 3049 in both states:
Disabled read 0 and Enabled read 1. The control stays disabled by default pending a write test.

31001 is the VPP "Battery working status", which the shared status block had labelled a
fault word. The same inverter read 3 discharging, 2 charging and 1 asleep.
"""
from __future__ import annotations

import ast
import importlib
from pathlib import Path

import pytest

_gm = importlib.import_module("growatt_under_test.growatt_modbus")
_profiles = importlib.import_module("growatt_under_test.profiles")
_dp = importlib.import_module("growatt_under_test.device_profiles")

COMPONENT = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
MAP = "MIN_TL_XH_3000_10000_V201"
TOU_STARTS = (3038, 3040, 3042, 3044, 3050, 3052, 3054, 3056, 3058)

# Enough input data for a poll to count as live; holding reads only run after one.
LIVE = {31000: 6}


def _client(inputs: dict, holding: dict):
    client = _gm.GrowattModbus(connection_type="serial", register_map=MAP)

    def read_input(start, count, log_errors=True):
        if start not in inputs:
            return None
        return [inputs.get(a, 0) for a in range(start, start + count)]

    def read_holding(start, count):
        if start not in holding:
            return None
        return [holding.get(a, 0) for a in range(start, start + count)]

    client.read_input_registers = read_input
    client.read_holding_registers = read_holding
    return client


def test_all_nine_xh_periods_and_grid_charge_are_mapped():
    holding = _profiles.REGISTER_MAPS[MAP]["holding_registers"]
    for period, start in enumerate(TOU_STARTS, start=1):
        assert holding[start]["name"] == f"mod_tou_{period}_start"
        assert holding[start + 1]["name"] == f"mod_tou_{period}_end"
    assert holding[3049]["name"] == "allow_grid_charge"
    assert holding[3049]["access"] == "RW"


def test_reported_allow_grid_charge_value_is_read_from_3049():
    data = _client(LIVE, {3049: 1}).read_all_data()
    assert data.allow_grid_charge == 1


def test_reported_period_1_decodes_as_battery_first_00_00_to_07_00():
    data = _client(LIVE, {3038: 40960, 3039: 1792}).read_all_data()

    start, end = data.mod_tou_1_start, data.mod_tou_1_end
    assert (start >> 15) & 1 == 1, "enabled"
    assert (start >> 13) & 3 == 1, "Battery First"
    assert ((start >> 8) & 0x1F, start & 0xFF) == (0, 0)
    assert ((end >> 8) & 0x1F, end & 0xFF) == (7, 0)


@pytest.mark.parametrize("raw, minute", [(1793, 1), (1794, 2)])
def test_end_minute_steps_read_back(raw, minute):
    data = _client(LIVE, {3038: 40960, 3039: raw}).read_all_data()
    assert ((data.mod_tou_1_end >> 8) & 0x1F, data.mod_tou_1_end & 0xFF) == (7, minute)


def test_min_tl_xh_asks_for_tou_entities_disabled_and_mod_does_not():
    assert _profiles.REGISTER_MAPS[MAP].get("tou_disabled_by_default") is True
    assert not _profiles.REGISTER_MAPS["MOD_6000_15000TL3_XH"].get("tou_disabled_by_default")


def test_unconfirmed_min_grid_charge_control_starts_disabled():
    assert _profiles.REGISTER_MAPS[MAP].get("allow_grid_charge_disabled_by_default") is True


def test_select_honours_grid_charge_disabled_flag():
    """Keep the opt-in flag wired to the entity if select setup is reworked."""
    source = (COMPONENT / "select.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    setup = next(n for n in ast.walk(tree)
                 if isinstance(n, ast.AsyncFunctionDef) and n.name == "async_setup_entry")
    body = ast.get_source_segment(source, setup)
    assert "allow_grid_charge_disabled_by_default" in body
    assert "entity._attr_entity_registry_enabled_default = False" in body


@pytest.mark.parametrize("platform", ["time.py", "select.py"])
def test_both_tou_platforms_honour_the_disabled_flag(platform):
    """The flag is consulted, and it switches entity_registry_enabled_default off.

    Source-level, because these platforms import Home Assistant and this suite runs
    without it.
    """
    source = (COMPONENT / platform).read_text(encoding="utf-8")
    tree = ast.parse(source)
    setup = next(n for n in ast.walk(tree)
                 if isinstance(n, ast.AsyncFunctionDef) and n.name == "async_setup_entry")
    body = ast.get_source_segment(source, setup)
    assert "tou_disabled_by_default" in body
    assert "_attr_entity_registry_enabled_default = False" in body


@pytest.mark.parametrize("raw", [1, 2, 3])
def test_battery_working_status_is_read_from_31001(raw):
    data = _client({31000: 6, 31001: raw}, {}).read_all_data()
    assert data.battery_working_status == raw


def test_battery_working_status_is_in_the_min_tl_xh_sensor_set():
    assert "battery_working_status" in _dp.INVERTER_PROFILES["min_tl_xh_3000_10000_v201"]["sensors"]
