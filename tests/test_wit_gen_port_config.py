"""WIT GEN port configuration, holding 781 and 898, as read-only sensors (#503).

Neither register is in Growatt's WIT protocol. mihaelko found them in a ShineTools
disassembly and confirmed both on a WIT 15K HU by switching each setting in ShineTools and
reading it back. With an AC-coupled PV inverter on the GEN port, both read 1.

They are read-only on purpose: the integration offers no write to either.

0 is a meaningful value for both ("Off", "Generator"), so a failed read must leave the field
None (unknown), never a default 0 that looks like a setting.
"""
from __future__ import annotations

import ast
import importlib
from pathlib import Path

import pytest

_gm = importlib.import_module("growatt_under_test.growatt_modbus")
_dp = importlib.import_module("growatt_under_test.device_profiles")
_profiles = importlib.import_module("growatt_under_test.profiles")
_PKG = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"

WIT_MAPS = ("WIT_4000_15000TL3", "WIT_29900_50000TL3_XHU")
KEYS = ("ac_couple_enable", "gen_port_device_type")


def _poll(register_map: str, holding: dict | None):
    client = _gm.GrowattModbus(connection_type="tcp", host="10.0.0.1", port=502,
                               slave_id=1, register_map=register_map)
    holding_calls: list[int] = []

    client.read_input_registers = lambda start, count, log_errors=True: [0] * count

    def read_holding_registers(start, count):
        holding_calls.append(start)
        if holding is None:
            return None
        return [holding.get(a, 0) for a in range(start, start + count)]

    client.read_holding_registers = read_holding_registers
    return client.read_all_data(), holding_calls


@pytest.mark.parametrize("register_map", WIT_MAPS)
def test_wit_reads_both_registers_from_holding(register_map):
    data, calls = _poll(register_map, {781: 1, 898: 1})
    assert 781 in calls and 898 in calls
    assert data.ac_couple_enable == 1
    assert data.gen_port_device_type == 1


@pytest.mark.parametrize("register_map", WIT_MAPS)
def test_zero_is_reported_as_read(register_map):
    data, _ = _poll(register_map, {781: 0, 898: 2})
    assert data.ac_couple_enable == 0
    assert data.gen_port_device_type == 2


@pytest.mark.parametrize("register_map", WIT_MAPS)
def test_failed_read_stays_unknown_not_zero(register_map):
    data, _ = _poll(register_map, None)
    assert data.ac_couple_enable is None
    assert data.gen_port_device_type is None


def test_profiles_without_the_registers_do_not_read_them():
    data, calls = _poll("SPH_7000_10000_V201", {781: 1, 898: 1})
    assert 781 not in calls and 898 not in calls
    assert data.ac_couple_enable is None


@pytest.mark.parametrize("register_map", WIT_MAPS)
def test_both_are_mapped_in_holding_not_input(register_map):
    regs = _profiles.REGISTER_MAPS[register_map]
    assert regs["holding_registers"][781]["name"] == "ac_couple_enable"
    assert regs["holding_registers"][898]["name"] == "gen_port_device_type"
    assert regs["holding_registers"][781]["access"] == "R"
    assert regs["holding_registers"][898]["access"] == "R"
    names = {r.get("name") for r in regs["input_registers"].values()}
    assert not names & set(KEYS)


@pytest.mark.parametrize("key", sorted(_dp.INVERTER_PROFILES))
def test_offered_exactly_where_mapped(key):
    profile = _dp.INVERTER_PROFILES[key]
    holding = _profiles.REGISTER_MAPS.get(profile.get("register_map", ""), {}).get(
        "holding_registers", {})
    mapped = {r.get("name") for r in holding.values()}
    for sensor_key in KEYS:
        assert (sensor_key in profile["sensors"]) == (sensor_key in mapped), (key, sensor_key)


def _sensor_definition(key: str) -> dict:
    """Literal fields of one SENSOR_DEFINITIONS entry, parsed from source.

    sensor.py imports Home Assistant, which the HA-free suite cannot load.
    """
    tree = ast.parse((_PKG / "sensor.py").read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == "SENSOR_DEFINITIONS"):
            for k, v in zip(node.value.keys, node.value.values):
                if isinstance(k, ast.Constant) and k.value == key:
                    out = {}
                    for fk, fv in zip(v.keys, v.values):
                        try:
                            out[fk.value] = ast.literal_eval(fv)
                        except ValueError:
                            pass
                    return out
    raise AssertionError(f"{key} not in SENSOR_DEFINITIONS")


def test_value_maps_match_the_shinetools_meanings():
    ac = _sensor_definition("ac_couple_enable")
    gen = _sensor_definition("gen_port_device_type")
    assert ac["value_map"] == {0: "Off", 1: "On"}
    assert gen["value_map"] == {0: "Generator", 1: "PV Inverter", 2: "Smart Load"}
    # On a WIT with nothing on the GEN port, 898 = 0 reads "Generator".
    assert ac["disabled_by_default"] is True
    assert gen["disabled_by_default"] is True


def test_no_write_control_exists_for_either_register():
    for module in ("number.py", "select.py", "switch.py", "button.py"):
        path = _PKG / module
        if not path.exists():
            continue
        source = path.read_text(encoding="utf-8")
        for sensor_key in KEYS:
            assert sensor_key not in source, (module, sensor_key)
        for addr in ("781", "898"):
            assert f"{addr}," not in source and f": {addr}" not in source, (module, addr)
