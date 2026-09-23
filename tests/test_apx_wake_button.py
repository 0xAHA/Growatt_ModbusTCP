"""The MIN TL-XH APX wake pulse is bounded, reversible and opt-in."""
from __future__ import annotations

import ast
import contextlib
import importlib
import json
from pathlib import Path

import pytest

_wake = importlib.import_module("growatt_under_test.battery_wake")

COMPONENT = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"


class _FakeClient:
    def __init__(
        self,
        *,
        authority: int = 0,
        remote_enabled: int = 0,
        fail_stop: bool = False,
        fail_parameter_restore: bool = False,
        unavailable_remote_block: bool = False,
    ):
        self.registers = {
            30100: authority,
            30407: remote_enabled,
            30408: 45,
            30409: 37,
            30410: 1,
        }
        self.fail_stop = fail_stop
        self.fail_parameter_restore = fail_parameter_restore
        self.unavailable_remote_block = unavailable_remote_block
        self.writes: list[tuple] = []
        self.batches: list[str] = []

    @contextlib.contextmanager
    def write_batch(self, label):
        self.batches.append(label)
        yield

    def read_holding_registers(self, start, count):
        if start == 30407 and self.unavailable_remote_block:
            return None
        return [self.registers[address] for address in range(start, start + count)]

    def write_register(self, register, value, bypass_rate_limit=False):
        self.writes.append((register, value, bypass_rate_limit))
        if register == 30407 and value == 0 and self.fail_stop:
            return False
        self.registers[register] = value
        return True

    def write_registers(self, register, values):
        self.writes.append((register, list(values)))
        if self.fail_parameter_restore and list(values) == [45, 37, 1]:
            return False
        for offset, value in enumerate(values):
            self.registers[register + offset] = value
        return True


def test_wake_pulse_is_low_bounded_and_restores_previous_state():
    client = _FakeClient()
    sleeps = []

    _wake.wake_apx_battery(client, sleep_fn=sleeps.append)

    assert sleeps == [12]
    assert (30408, [1, 5, 1]) in client.writes
    assert (30407, 1, False) in client.writes
    assert (30407, 0, True) in client.writes
    assert client.registers == {
        30100: 0,
        30407: 0,
        30408: 45,
        30409: 37,
        30410: 1,
    }


def test_active_vpp_session_is_paused_and_restored():
    client = _FakeClient(authority=1, remote_enabled=1)
    sleeps = []

    _wake.wake_apx_battery(client, sleep_fn=sleeps.append)

    assert sleeps == [12]
    assert client.writes[0] == (30407, 0, True)
    assert (30100, 1, False) not in client.writes
    assert (30408, [1, 5, 1]) in client.writes
    assert client.registers == {
        30100: 1,
        30407: 1,
        30408: 45,
        30409: 37,
        30410: 1,
    }


def test_stale_remote_selector_without_authority_is_restored():
    client = _FakeClient(authority=0, remote_enabled=1)

    _wake.wake_apx_battery(client, sleep_fn=lambda _: None)

    assert client.writes[0] == (30407, 0, True)
    assert (30100, 1, False) in client.writes
    assert client.registers == {
        30100: 0,
        30407: 1,
        30408: 45,
        30409: 37,
        30410: 1,
    }


def test_existing_vpp_roster_authority_is_preserved():
    client = _FakeClient(authority=1)

    _wake.wake_apx_battery(client, sleep_fn=lambda _: None)

    assert (30100, 1, False) not in client.writes
    assert client.registers == {
        30100: 1,
        30407: 0,
        30408: 45,
        30409: 37,
        30410: 1,
    }


def test_unavailable_remote_block_fails_before_any_write():
    client = _FakeClient(unavailable_remote_block=True)

    with pytest.raises(_wake.BatteryWakeError, match="not available"):
        _wake.wake_apx_battery(client, sleep_fn=lambda _: None)

    assert client.writes == []


def test_failed_stop_keeps_the_one_minute_five_percent_safety_limit():
    client = _FakeClient(fail_stop=True)

    with pytest.raises(_wake.BatteryWakeError, match="at most one minute"):
        _wake.wake_apx_battery(client, sleep_fn=lambda _: None)

    assert client.registers[30100] == 0
    assert client.registers[30407] == 1
    assert [client.registers[register] for register in (30408, 30409, 30410)] == [1, 5, 1]


def test_failed_parameter_restore_leaves_direct_branch_deselected():
    client = _FakeClient(
        authority=1,
        remote_enabled=1,
        fail_parameter_restore=True,
    )

    with pytest.raises(_wake.BatteryWakeError, match="parameters"):
        _wake.wake_apx_battery(client, sleep_fn=lambda _: None)

    assert client.registers[30100] == 1
    assert client.registers[30407] == 0


def test_button_is_profile_specific_and_disabled_by_default():
    source = (COMPONENT / "button.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    button = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef)
        and node.name == "GrowattWakeApxBatteryButton"
    )
    assignments = {
        target.id: ast.get_source_segment(source, statement.value)
        for statement in button.body
        if isinstance(statement, ast.Assign)
        for target in statement.targets
        if isinstance(target, ast.Name)
    }

    assert 'MIN_TL_XH_WAKE_PROFILE = "MIN_TL_XH_3000_10000_V201"' in source
    assert "config_entry.data.get(CONF_REGISTER_MAP) == MIN_TL_XH_WAKE_PROFILE" in source
    assert assignments.get("_attr_entity_registry_enabled_default") == "False"
    assert assignments.get("_attr_translation_key") == '"wake_apx_battery"'


def test_button_name_exists_in_both_string_files():
    for relative_path in ("strings.json", "translations/en.json"):
        data = json.loads((COMPONENT / relative_path).read_text(encoding="utf-8"))
        assert (
            data["entity"]["button"]["wake_apx_battery"]["name"]
            == "Wake APX Battery"
        ), relative_path
