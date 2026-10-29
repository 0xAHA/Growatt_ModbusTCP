"""Mode (VPP) reports what the inverter's registers say, not a remembered command (#481).

The select showed the last mode chosen through it, kept in memory and defaulting to "Hold".
A WIT owner's detector caught it reading Hold twice during live sessions - once while
discharging at 9.6 kW (30409 = -60, 30474 = -60), once while charging at 9.3 kW (+60) -
with control authority and remote control both on. An automation that used it to ask "is a
charge running?" stopped watching, and the battery charged 10 % past its target.
"""
from __future__ import annotations

import ast
import importlib
import types
from pathlib import Path

import pytest

_const = importlib.import_module("growatt_under_test.const")
COMPONENT = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"


def _data(authority=1, remote=1, setpoint=0, available=True):
    return types.SimpleNamespace(
        vpp_control_authority_available=available, vpp_remote_power_available=available,
        control_authority=authority, remote_power_control_enable=remote,
        remote_charge_and_discharge_power=setpoint)


@pytest.mark.parametrize("setpoint, mode", [(-60, "Discharge"), (60, "Charge")])
def test_the_reporters_two_snapshots(setpoint, mode):
    assert _const.vpp_mode_from_registers(_data(setpoint=setpoint)) == mode


@pytest.mark.parametrize("kwargs", [
    {"authority": 0}, {"remote": 0}, {"setpoint": 0}, {"available": False},
])
def test_no_claim_when_the_registers_do_not_say(kwargs):
    assert _const.vpp_mode_from_registers(_data(setpoint=60, **kwargs) if "setpoint" not in kwargs
                                         else _data(**kwargs)) is None
    assert _const.vpp_mode_from_registers(None) is None


def _current_option_source():
    source = (COMPONENT / "select.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    klass = next(n for n in tree.body if isinstance(n, ast.ClassDef)
                 and n.name == "GrowattWitVppBatteryModeSelect")
    fn = next(n for n in klass.body if isinstance(n, ast.FunctionDef) and n.name == "current_option")
    return ast.get_source_segment(source, fn)


def test_the_select_asks_the_registers_first():
    body = _current_option_source()
    assert body.index("vpp_mode_from_registers(") < body.index("wit_vpp_last_mode")


def test_the_select_no_longer_invents_hold():
    assert 'return "Hold"' not in _current_option_source()
