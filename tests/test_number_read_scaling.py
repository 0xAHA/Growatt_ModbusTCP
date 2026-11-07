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


NATIVE_VALUE = _load_native_value()


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
