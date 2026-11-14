"""WIT Mode (VPP): setpoint before remote enable, and a rate that survives restarts (#481).

Wojak129 measured 57-77 s at 100 % on each of six armings of a WIT 15KTL3, before his own
68 % write landed. Two things fed it:

* Charge and Discharge wrote 30407 = 1 (remote control on, direct branch selected) before
  30409, the setpoint. For the gap between the two writes, the inverter could act on
  whatever 30409 already held. The guide's own write order puts the setpoint first.
* The setpoint is VPP Power Rate, held only in memory, and it returned to 100 % on every
  restart.

number.py and select.py need Home Assistant to import, so the order is read from the source
and the restore helper is extracted and run on its own.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

COMPONENT = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"


def _branch(option: str) -> str:
    """The source of `elif option == "<option>":` in the WIT VPP mode select."""
    tree = ast.parse((COMPONENT / "select.py").read_text(encoding="utf-8"))
    cls = next(n for n in ast.walk(tree)
               if isinstance(n, ast.ClassDef) and n.name == "GrowattWitVppBatteryModeSelect")
    for node in ast.walk(cls):
        if (isinstance(node, ast.If) and isinstance(node.test, ast.Compare)
                and isinstance(node.test.comparators[0], ast.Constant)
                and node.test.comparators[0].value == option):
            return "\n".join(ast.unparse(stmt) for stmt in node.body)
    raise AssertionError(f"no {option!r} branch found")


@pytest.mark.parametrize("option", ["Charge", "Discharge"])
def test_the_setpoint_is_written_before_remote_control_is_enabled(option):
    body = _branch(option)
    setpoint = body.index("self.VPP_REMOTE_POWER_PERCENT")
    enable = body.index("self.VPP_REMOTE_POWER_ENABLE")
    assert setpoint < enable, (
        f"{option} enables 30407 before writing 30409 - the inverter can act on a stale "
        f"setpoint until it lands"
    )


def _restore_helper():
    tree = ast.parse((COMPONENT / "number.py").read_text(encoding="utf-8"))
    func = next(n for n in tree.body
                if isinstance(n, ast.FunctionDef) and n.name == "restore_vpp_power_percent")
    namespace: dict = {"Any": object}
    exec(compile(ast.Module(body=[func], type_ignores=[]), "number.py", "exec"), namespace)
    return namespace["restore_vpp_power_percent"]


@pytest.mark.parametrize("stored, expected", [
    (68.0, 68), (1, 1), (100, 100), ("68", 68),
    (None, None), (0, None), (101, None), (-5, None), ("abc", None),
])
def test_a_stored_rate_is_restored_only_when_it_is_usable(stored, expected):
    assert _restore_helper()(stored) == expected


def test_the_rate_entity_restores_and_persists():
    """RestoreNumber is what gives the entity a last value to read, and writing state on
    set is what makes that last value the one the user chose."""
    source = (COMPONENT / "number.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    cls = next(n for n in ast.walk(tree)
               if isinstance(n, ast.ClassDef) and n.name == "GrowattWitVppPowerPercentNumber")
    assert "RestoreNumber" in [ast.unparse(b) for b in cls.bases]
    methods = {n.name: ast.unparse(n) for n in cls.body if isinstance(n, ast.AsyncFunctionDef)}
    assert "async_get_last_number_data" in methods["async_added_to_hass"]
    assert "restore_vpp_power_percent" in methods["async_added_to_hass"]
    assert "async_write_ha_state" in methods["async_set_native_value"]
