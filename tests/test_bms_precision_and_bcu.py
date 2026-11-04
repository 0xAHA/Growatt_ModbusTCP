"""Cell voltages keep their millivolts, and the battery firmware is read (#486).

Every volt value was rounded to one decimal, so 3.307 / 3.280 V cell voltages both showed
3.3 - hiding the imbalance the two sensors exist for. And VPP holding 30074-30076 (BCU
software version) read "QA", "Ab", 3010 - the "QAAb-3010" the Growatt portal shows for the
battery - while nothing in the integration read it.
"""
from __future__ import annotations

import ast
import importlib
from pathlib import Path

import pytest

_const = importlib.import_module("growatt_under_test.const")
COMPONENT = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
SENSOR_SRC = (COMPONENT / "sensor.py").read_text(encoding="utf-8")


def test_the_reporters_bcu_version():
    assert _const.decode_bcu_version([0x5141, 0x4162, 3010]) == "QAAb-3010"


@pytest.mark.parametrize("regs", [None, [], [0, 0, 0], [0x5141, 0x4162, 0],
                                  [0x5141, 0x4162, 0xFFFF], [0xFFFF, 0xFFFF, 1]])
def test_no_version_from_blank_or_garbage(regs):
    assert _const.decode_bcu_version(regs) is None


def _definition(key):
    tree = ast.parse(SENSOR_SRC)
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            for k, v in zip(node.keys, node.values):
                if isinstance(k, ast.Constant) and k.value == key and isinstance(v, ast.Dict):
                    return {kk.value: vv for kk, vv in zip(v.keys, v.values)
                            if isinstance(kk, ast.Constant)}
    raise AssertionError(key)


@pytest.mark.parametrize("key, places", [("bms_max_cell_volt", 3), ("bms_min_cell_volt", 3),
                                         ("bms_constant_volt", 2)])
def test_the_definitions_ask_for_their_precision(key, places):
    assert ast.literal_eval(_definition(key)["precision"]) == places


def test_the_rounding_honours_it_before_the_unit_default():
    i = SENSOR_SRC.index('if isinstance(value, float) and "precision" in self._sensor_def:')
    j = SENSOR_SRC.index("if self._sensor_def.get(\"unit\") == UnitOfElectricPotential.VOLT:")
    assert i < j
    assert "self._attr_suggested_display_precision = sensor_def[\"precision\"]" in SENSOR_SRC


def test_the_battery_device_carries_it():
    src = (COMPONENT / "coordinator.py").read_text(encoding="utf-8")
    assert "decode_bcu_version(self._read_holding(30074, 3))" in src
    assert '{"sw_version": self._battery_firmware}' in src
