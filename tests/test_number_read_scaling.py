"""Writable numbers must not rescale values already decoded by the coordinator."""
from __future__ import annotations

import ast
import importlib
import types
from pathlib import Path

import pytest


CONST = importlib.import_module("growatt_under_test.const")
SOURCE = (
    Path(__file__).parent.parent / "custom_components" / "growatt_modbus" / "number.py"
).read_text(encoding="utf-8")


def _load_native_value():
    tree = ast.parse(SOURCE)
    node = next(
        node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "native_value"
    )
    node.decorator_list = []
    module = types.ModuleType("_number_read_scaling")
    module.__dict__["VPP_CONTROL_AVAILABILITY_FLAG"] = {}
    code = compile(ast.Module(body=[node], type_ignores=[]), "<native_value>", "exec")
    exec(code, module.__dict__)
    return module.native_value


def _load_raw_value_from_display():
    tree = ast.parse(SOURCE)
    node = next(
        node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "_raw_value_from_display"
    )
    module = types.ModuleType("_number_write_scaling")
    code = compile(ast.Module(body=[node], type_ignores=[]), "<raw_value>", "exec")
    exec(code, module.__dict__)
    return module._raw_value_from_display


NATIVE_VALUE = _load_native_value()
RAW_VALUE_FROM_DISPLAY = _load_raw_value_from_display()


class _Entity:
    native_value = property(NATIVE_VALUE)

    def __init__(self, control_name: str, **values: float) -> None:
        self._control_name = control_name
        self._control_config = CONST.WRITABLE_REGISTERS[control_name]
        self.coordinator = types.SimpleNamespace(
            data=types.SimpleNamespace(unread_fields=set(), **values)
        )


@pytest.mark.parametrize(
    ("control_name", "value", "expected"),
    [
        pytest.param("ac_charge_max_power", 1.3, 1.3, id="h3311-already-decoded"),
        pytest.param("ac_to_bat_volt", 540, 54.0, id="raw-value-still-scaled"),
    ],
)
def test_native_value_applies_read_scale_once(
    control_name: str, value: float, expected: float
) -> None:
    """H3311 is decoded to kW before the generic number entity reads it."""
    assert _Entity(control_name, **{control_name: value}).native_value == expected


@pytest.mark.parametrize(
    ("display_value", "expected_raw"),
    [
        pytest.param(1.2, 12),
        pytest.param(1.3, 13),
        pytest.param(1.9, 19),
        pytest.param(2.9, 29),
        pytest.param(5.1, 51),
    ],
)
def test_decimal_power_values_round_to_the_expected_raw_register(
    display_value: float, expected_raw: int
) -> None:
    """Binary floating point must not truncate a tenth of a kW."""
    assert RAW_VALUE_FROM_DISPLAY(display_value, 0.1) == expected_raw


def test_generic_number_write_uses_the_rounding_helper() -> None:
    assert "raw_value = _raw_value_from_display(value, scale)" in SOURCE
