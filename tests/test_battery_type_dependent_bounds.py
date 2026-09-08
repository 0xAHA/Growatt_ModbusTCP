"""Switchover thresholds must follow the battery type, live (#428).

On SPF, registers 37 and 95 mean two different things. On lead-acid and self-defined battery
types they are a **voltage** threshold, 20.0-64.0 V. On lithium they are a **percentage** of
state of charge, 0-100 %. One register, two units, two ranges.

The entity resolved that once in `__init__` and froze it as `_attr_` values. @eugeniodb, on an
SPF 5000 ES with 3x AXE 5.0 lithium, had `Utility to Battery Switchover` reading 75 - correct,
75 % - and validated against the lead-acid ceiling of 64 V, so it refused before he typed
anything and no target above 64 % could be set from Home Assistant at all. His diagnostics
confirm the register side was fine: `battery_type = 3`, `ac_to_bat_volt = 750` raw, which at
scale 0.1 is exactly the 75 % he sees the inverter act on.

The second failure is the one that would have outlived his: **battery_type is itself a
writable control here**, so changing it left both entities on the old unit and range until
Home Assistant restarted.

Resolved live instead. `number.py` imports `homeassistant.components.number`, so the methods
are extracted and bound to a stub rather than imported.
"""
from __future__ import annotations

import ast
import importlib
import sys
import types
from pathlib import Path

import pytest

sys.path.insert(0, "tests")

CONST = importlib.import_module("growatt_under_test.const")
COMPONENT = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
SOURCE = (COMPONENT / "number.py").read_text(encoding="utf-8")

BATTERY_DEPENDENT = ["bat_low_to_uti", "ac_to_bat_volt"]
LITHIUM = 3


def _load():
    tree = ast.parse(SOURCE)
    wanted = ("_battery_dependent_bounds", "_is_battery_dependent",
              "native_min_value", "native_max_value", "native_step",
              "native_unit_of_measurement", "_paired_bound")
    found = {n.name: n for n in ast.walk(tree)
             if isinstance(n, ast.FunctionDef) and n.name in wanted}
    missing = set(wanted) - set(found)
    assert not missing, f"missing from number.py: {sorted(missing)}"

    module = types.ModuleType("_bt")
    module.__dict__["HomeAssistantError"] = RuntimeError
    body = [found[n] for n in wanted]
    for node in body:
        node.decorator_list = []
    src = ast.unparse(ast.Module(body=body, type_ignores=[]))
    src = src.replace("from .const import WRITABLE_REGISTERS",
                      "from growatt_under_test.const import WRITABLE_REGISTERS")
    exec(compile(src, "<bt>", "exec"), module.__dict__)
    return module


M = _load()


class _Entity:
    _LITHIUM_BATTERY_TYPE = LITHIUM

    def __init__(self, control_name, battery_type=None, has_data=True):
        self._control_name = control_name
        self._control_config = CONST.WRITABLE_REGISTERS[control_name]
        self._attr_native_min_value = -1.0   # sentinel: must never be returned
        self._attr_native_max_value = -1.0
        self._attr_native_step = -1.0
        self._attr_native_unit_of_measurement = "SENTINEL"
        data = types.SimpleNamespace(battery_type=battery_type, unread_fields=set()) if has_data else None
        self.coordinator = types.SimpleNamespace(data=data)

    _battery_dependent_bounds = M._battery_dependent_bounds
    _paired_bound = M._paired_bound
    _is_battery_dependent = property(M._is_battery_dependent)
    min_value = property(M.native_min_value)
    max_value = property(M.native_max_value)
    step = property(M.native_step)
    unit = property(M.native_unit_of_measurement)


def test_both_switchover_registers_are_declared_battery_dependent():
    for name in BATTERY_DEPENDENT:
        assert CONST.WRITABLE_REGISTERS[name].get("battery_dependent") is True


@pytest.mark.parametrize("control", BATTERY_DEPENDENT)
def test_lithium_gets_percent_and_the_full_range(control):
    """THE regression. 75 is a valid state of charge and was being rejected against 64 V."""
    entity = _Entity(control, battery_type=LITHIUM)

    assert entity.unit == "%"
    assert (entity.min_value, entity.max_value) == (0.0, 100.0)
    assert 75.0 <= entity.max_value, "75 % is still outside the permitted range"


@pytest.mark.parametrize("control", BATTERY_DEPENDENT)
def test_non_lithium_keeps_volts(control):
    """Guard against over-correcting: lead-acid must keep the voltage range it had."""
    for battery_type in (0, 1, 2, 4):   # AGM, Flooded, User Defined, User Defined 2
        entity = _Entity(control, battery_type=battery_type)
        assert entity.unit == "V"
        assert (entity.min_value, entity.max_value) == (20.0, 64.0)


def test_the_bounds_follow_a_battery_type_change_without_a_restart():
    """battery_type is a writable control in this integration, so it can change at runtime.

    Frozen `_attr_` values meant switching to lithium left the entity on volts and 20-64
    until Home Assistant was restarted — a fault nobody would connect to the change they
    had just made.
    """
    entity = _Entity("ac_to_bat_volt", battery_type=0)
    assert entity.unit == "V"

    entity.coordinator.data.battery_type = LITHIUM

    assert entity.unit == "%", "the unit did not follow the battery type"
    assert entity.max_value == 100.0, "the range did not follow the battery type"


def test_the_frozen_attributes_are_never_returned_for_these_controls():
    """The sentinel values on the stub would surface if any property fell back to the
    `_attr_` set at construction — which is exactly the defect."""
    entity = _Entity("ac_to_bat_volt", battery_type=LITHIUM)

    assert entity.min_value != -1.0
    assert entity.max_value != -1.0
    assert entity.step != -1.0
    assert entity.unit != "SENTINEL"


def test_missing_coordinator_data_falls_back_to_volts():
    """During setup there may be no data yet. Volts and 20-64 is the safer default: it is
    the narrower range, so it cannot accept a value the inverter would reject outright."""
    entity = _Entity("ac_to_bat_volt", has_data=False)

    assert entity.unit == "V"
    assert (entity.min_value, entity.max_value) == (20.0, 64.0)


def test_the_reporters_values_decode_correctly_under_this_scale():
    """Rule 4 against the evidence rather than the code. From his diagnostics: raw 750 at
    scale 0.1 is 75, and he observes the inverter returning to battery at 75 % SOC. If that
    stops holding, the mapping is wrong rather than just the presentation."""
    scale = CONST.WRITABLE_REGISTERS["ac_to_bat_volt"]["scale"]

    assert scale == 0.1
    assert 750 * scale == 75.0
    assert 500 * scale == 50.0    # bat_low_to_uti, transfers to grid at 50 %


def test_no_other_control_is_battery_dependent():
    """Only these two registers change meaning with battery type. Inventing that behaviour
    elsewhere would silently retype a control."""
    declared = {n for n, c in CONST.WRITABLE_REGISTERS.items() if c.get("battery_dependent")}

    assert declared == set(BATTERY_DEPENDENT), f"unexpected battery-dependent controls: {declared}"
