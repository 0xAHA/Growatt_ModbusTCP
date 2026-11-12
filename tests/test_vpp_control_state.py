"""VPP Control State: a read-only state derived from registers already polled (#481).

Mode (VPP) is a command surface and reads `unknown` when no session runs, which
monitoring flagged as a fault. The sensor reports the combination of 30100 (authority),
30407 (remote power control) and the sign of 30409 (setpoint), and must never guess:
a block that missed the poll is unavailable, not a plausible default.
"""
from __future__ import annotations

import ast
import importlib
import json
import types
from pathlib import Path

import pytest

_const = importlib.import_module("growatt_under_test.const")
COMPONENT = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"


def _data(authority=1, remote=1, setpoint=0, authority_read=True, remote_read=True):
    return types.SimpleNamespace(
        vpp_control_authority_available=authority_read,
        vpp_remote_power_available=remote_read,
        control_authority=authority, remote_power_control_enable=remote,
        remote_charge_and_discharge_power=setpoint)


@pytest.mark.parametrize("authority, remote, setpoint, state", [
    (1, 1, 68, "charge"),
    (1, 1, -60, "discharge"),
    # Armed but commanding nothing: the fault Wojak129's watchdog hunts for.
    (1, 1, 0, "armed_idle"),
    # Hold (schedule branch) or VPP standby; setpoint ignored while 30407 is off.
    (1, 0, 68, "authority_only"),
    # The 35 s transient inside the WIT stop sequence (#480 bad mode if left standing).
    (0, 1, 68, "remote_without_authority"),
    # His disarm leaves 30409 at +68: must read released, never Charge.
    (0, 0, 68, "released"),
    (0, 0, 0, "released"),
])
def test_each_register_combination(authority, remote, setpoint, state):
    assert _const.vpp_control_state_from_registers(
        _data(authority, remote, setpoint)) == state


@pytest.mark.parametrize("kwargs", [
    {"authority_read": False}, {"remote_read": False},
    {"authority": 2}, {"remote": 5},
])
def test_unread_or_unexpected_registers_give_no_state(kwargs):
    assert _const.vpp_control_state_from_registers(_data(**kwargs)) is None


def test_no_data_gives_no_state():
    assert _const.vpp_control_state_from_registers(None) is None


def test_every_returned_state_is_a_declared_option():
    seen = {
        _const.vpp_control_state_from_registers(_data(a, r, s))
        for a in (0, 1) for r in (0, 1) for s in (-1, 0, 1)
    }
    assert seen == set(_const.VPP_CONTROL_STATES)


@pytest.mark.parametrize("filename", ["strings.json", "translations/en.json"])
def test_every_state_is_named(filename):
    entry = json.loads((COMPONENT / filename).read_text(encoding="utf-8"))[
        "entity"]["sensor"]["vpp_control_state"]
    assert entry["name"] == "VPP Control State"
    assert set(entry["state"]) == set(_const.VPP_CONTROL_STATES)


def _sensor_source() -> str:
    return (COMPONENT / "sensor.py").read_text(encoding="utf-8")


def test_sensor_is_created_only_where_all_three_registers_are_mapped():
    source = _sensor_source()
    setup = next(
        node for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "async_setup_entry"
    )
    body = ast.get_source_segment(source, setup)
    assert "GrowattVppControlStateSensor(coordinator, config_entry)" in body
    assert "(30100, 30407, 30409)" in body


def test_sensor_is_unavailable_rather_than_guessing():
    source = _sensor_source()
    cls = next(
        node for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.ClassDef) and node.name == "GrowattVppControlStateSensor"
    )
    body = ast.get_source_segment(source, cls)
    assert "vpp_control_state_from_registers(self.coordinator.data) is not None" in body
    assert "wit_vpp_last_mode" not in body
