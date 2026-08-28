"""Actions that write fixed register addresses must refuse profiles that lack them.

Two of these shipped ungated. `set_battery_mode` was offered on a MIN TL-XH where its HOLD
mode charges the battery toward a stuck SOC limit - the opposite of standby - and imports
from the grid to do it (#400). `sync_tou_schedule` writes the VPP TOU block, which only the
two WIT maps carry, and was offered on every model (#396).

Both now check the profile and say what is missing. The check is on **register presence**
rather than on model family, because family checks are what produced the problem: MOD
carries the VPP control block and was excluded by a WIT-only gate (#373).
"""
import ast
import importlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, "tests")

REGISTER_MAPS = importlib.import_module("growatt_under_test.const").REGISTER_MAPS

COMPONENT = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"

# action -> the registers it cannot function without
GATED_ACTIONS = {
    "set_battery_mode": (30100, 30407, 30409),
    "sync_tou_schedule": (30411, 30412),
}


def _function_source(name: str) -> str:
    source = (COMPONENT / "diagnostic.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    func = next(
        n for n in ast.walk(tree)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name
    )
    return ast.get_source_segment(source, func)


@pytest.mark.parametrize("action,registers", GATED_ACTIONS.items())
def test_the_action_checks_the_profile_before_writing(action, registers):
    body = _function_source(action)
    assert "holding_registers" in body, f"{action} does not inspect the profile"
    assert "HomeAssistantError" in body, (
        f"{action} does not raise a user-visible error when unsupported"
    )
    for register in registers:
        assert str(register) in body, f"{action} does not mention register {register}"


@pytest.mark.parametrize("action,registers", GATED_ACTIONS.items())
def test_at_least_one_shipped_profile_supports_each_action(action, registers):
    """A gate tight enough to exclude everything would be a silent removal of the feature."""
    supported = [
        name for name, m in REGISTER_MAPS.items()
        if all(r in m.get("holding_registers", {}) for r in registers)
    ]
    assert supported, f"no profile satisfies the gate for {action}: {registers}"


def test_sync_tou_schedule_is_wit_only_and_that_is_expected():
    """Documents the scope rather than asserting a number for its own sake. If a non-WIT
    map gains these registers this fails, and the docs and the error message both need
    revisiting."""
    supported = sorted(
        name for name, m in REGISTER_MAPS.items()
        if all(r in m.get("holding_registers", {}) for r in (30411, 30412))
    )
    assert supported == ["WIT_29900_50000TL3_XHU", "WIT_4000_15000TL3"], supported


def test_the_tou_gate_does_not_depend_on_period_count():
    """The maps cover ten periods while the schema accepts twenty. Gating on the requested
    period count would refuse a profile that maps fewer periods than the hardware supports,
    which is a different failure from not supporting the action at all."""
    body = _function_source("sync_tou_schedule")
    gate = body[body.index("VPP_TOU_PERIOD_BASE = 30412"):body.index("try:")]
    assert "len(periods)" not in gate, "the gate refuses profiles by period count"
