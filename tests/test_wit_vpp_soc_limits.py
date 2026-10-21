"""WIT VPP SOC limits and the 30474 setpoint mirror (#481).

A WIT 4-15K-HU owner read 30405 (on-grid discharge cut-off) at 30 % in a register scan and
in the diagnostics, while the "Discharge Cutoff SOC" control showed 10 %. The control never
displayed the register: it showed a copy kept on the coordinator, which started at a fixed
default (100 for charge, 10 for discharge) and changed only when written from Home
Assistant. 10 also happened to equal his off-grid floor (30475), so it looked like the
control was pointing at the wrong register.

The same report found 30474 mapped and polled on WIT with no entity.

number.py imports Home Assistant, so the helper is lifted out of the source and run, and the
entities' use of it is checked from source.
"""
from __future__ import annotations

import ast
import importlib
import types
from pathlib import Path

import pytest

COMPONENT = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
NUMBER_SRC = (COMPONENT / "number.py").read_text(encoding="utf-8")
NUMBER_TREE = ast.parse(NUMBER_SRC)

_const = importlib.import_module("growatt_under_test.const")
_profiles = importlib.import_module("growatt_under_test.device_profiles")


def _function(name: str):
    fn = next(n for n in NUMBER_TREE.body if isinstance(n, ast.FunctionDef) and n.name == name)
    namespace: dict = {}
    exec(compile(ast.Module(body=[fn], type_ignores=[]), "number.py", "exec"), namespace)
    return namespace[name]


def _method(cls: str, name: str) -> str:
    klass = next(n for n in NUMBER_TREE.body if isinstance(n, ast.ClassDef) and n.name == cls)
    fn = next(n for n in klass.body
              if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name)
    return ast.get_source_segment(NUMBER_SRC, fn)


# The reporter's values: 30404 = 100, 30405 = 30, 30475 = 10.
def _polled(**overrides):
    data = types.SimpleNamespace(vpp_charge_stop_soc=100, vpp_ongrid_discharge_soc=30,
                                 vpp_offgrid_discharge_soc=10, unread_fields=set())
    for key, value in overrides.items():
        setattr(data, key, value)
    return data


def test_the_polled_on_grid_floor_is_shown():
    polled_soc = _function("_polled_soc")
    assert polled_soc(_polled(), "vpp_ongrid_discharge_soc") == 30.0


def test_an_unread_limit_is_unknown_not_a_default():
    polled_soc = _function("_polled_soc")
    data = _polled(unread_fields={"vpp_ongrid_discharge_soc"})
    assert polled_soc(data, "vpp_ongrid_discharge_soc") is None
    assert polled_soc(None, "vpp_ongrid_discharge_soc") is None


@pytest.mark.parametrize("cls, field", [
    ("GrowattWitVppChargeCutoffSocNumber", "vpp_charge_stop_soc"),
    ("GrowattWitVppDischargeCutoffSocNumber", "vpp_ongrid_discharge_soc"),
])
def test_each_control_shows_its_own_polled_register(cls, field):
    body = _method(cls, "native_value")
    assert f'_polled_soc(self.coordinator.data, "{field}")' in body
    assert "wit_vpp_" not in body, "still showing the entity's own copy"


@pytest.mark.parametrize("cls, field", [
    ("GrowattWitVppChargeCutoffSocNumber", "vpp_charge_stop_soc"),
    ("GrowattWitVppDischargeCutoffSocNumber", "vpp_ongrid_discharge_soc"),
])
def test_a_write_updates_the_polled_field(cls, field):
    body = _method(cls, "async_set_native_value")
    assert f"self.coordinator.data.{field} = raw_value" in body
    assert "wit_vpp_" not in body


def test_the_fields_are_the_ones_the_poll_fills():
    """The read loop must assign the same names the controls display."""
    gm_src = (COMPONENT / "growatt_modbus.py").read_text(encoding="utf-8")
    assert "(30404, 'vpp_charge_stop_soc')" in gm_src
    assert "(30405, 'vpp_ongrid_discharge_soc')" in gm_src


def test_the_discharge_control_says_on_grid():
    body = _method("GrowattWitVppDischargeCutoffSocNumber", "__init__")
    assert 'self._attr_name = "On-Grid Discharge Cutoff SOC"' in body


@pytest.mark.parametrize("profile", ["wit_4000_15000tl3", "wit_29900_50000tl3_xhu"])
def test_wit_has_the_30474_sensor(profile):
    spec = _profiles.INVERTER_PROFILES[profile]
    assert 30474 in _const.REGISTER_MAPS[spec["register_map"]]["holding_registers"]
    assert "vpp_last_setpoint" in spec["sensors"]
