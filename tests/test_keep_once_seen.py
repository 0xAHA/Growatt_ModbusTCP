"""`keep_once_seen` only works on a gate that can actually fail (#500).

Sensors flagged `keep_once_seen` are created at setup when the entity registry already has
them, and report unavailable whenever their condition fails - a second pack in deep
standby reads 0 V and stops being reported. That only means anything if the condition
tests an attribute set dynamically. On a GrowattData field the hasattr() is always True
(CLAUDE.md rule 6), so the sensor would never go unavailable and would publish the
dataclass default instead.

The behaviour itself is covered in tests_ha/test_battery2_persistence.py, which needs Home
Assistant and runs in CI.
"""
from __future__ import annotations

import ast
import importlib
import re
from pathlib import Path

_dp = importlib.import_module("growatt_under_test.device_profiles")
COMPONENT_DIR = Path(_dp.__file__).parent
SENSOR_SOURCE = (COMPONENT_DIR / "sensor.py").read_text(encoding="utf-8")


def _dataclass_fields() -> set[str]:
    tree = ast.parse((COMPONENT_DIR / "growatt_modbus.py").read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "GrowattData":
            return {
                stmt.target.id for stmt in node.body
                if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name)
            }
    raise AssertionError("GrowattData not found")


def _flagged_conditions() -> list[str]:
    """The condition line written just before each keep_once_seen flag."""
    conditions = []
    for match in re.finditer(r'"keep_once_seen":\s*True', SENSOR_SOURCE):
        before = SENSOR_SOURCE[:match.start()]
        conditions.append(before[before.rindex('"condition"'):].splitlines()[0])
    return conditions


def test_the_battery_pack_sensors_are_flagged():
    # battery{2,3,4}_* (one generated block), battery1_* x4, battery2_full_charge_capacity
    assert len(_flagged_conditions()) == 6


def test_every_flagged_gate_is_on_a_dynamic_attribute():
    fields = _dataclass_fields()
    for condition in _flagged_conditions():
        attrs = re.findall(r'hasattr\(data, f?"([a-z0-9_{}]+)"\)', condition)
        assert attrs, f"no hasattr() gate in {condition!r}"
        for attr in attrs:
            assert attr.replace("{nn}", "2") not in fields, (
                f"{attr} is a GrowattData field; hasattr() cannot fail on it"
            )
