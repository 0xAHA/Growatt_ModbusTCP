"""A write the WIT control cooldown refused is not a write (#481).

A WIT owner armed VPP (30100 = 1) and disarmed it 22 s later. The 30 s cooldown refused the
disarm, correctly by its own rule, and returned False. write_register_verified ignored that,
read the register back, found the old 1 and reported "write succeeded but value reverted";
the select then tracked it and the coordinator raised a write-reversion notice blaming the
Growatt cloud. Nothing had been sent. The service call returned normally, the automation
moved on, and the inverter stayed under VPP control.

Three things follow, each held here:
- a refused write is reported as not written, and is never verified or tracked;
- the entity raises, so the automation sees the failure;
- a release (30100 or 30407 set to 0) is never refused - refusing the "off" half of an
  on/off pair leaves the inverter in the state the user was leaving.

And one from the same report: VPP 30408/30409 are "not stored", so the no-op skip that
protects EEPROM registers must not drop a repeated write to them.
"""
from __future__ import annotations

import ast
import importlib
import time
from pathlib import Path

import pytest

_gm = importlib.import_module("growatt_under_test.growatt_modbus")
_const = importlib.import_module("growatt_under_test.const")
COMPONENT = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"


class _FakeResult:
    @staticmethod
    def isError():
        return False


class _FakePymodbus:
    def __init__(self):
        self.writes = []

    def write_register(self, address=None, value=None, **kwargs):
        self.writes.append((address, value))
        return _FakeResult()


def _client():
    client = _gm.GrowattModbus(connection_type="tcp", host="10.0.0.1", port=502,
                               register_map="WIT_4000_15000TL3")
    client._shared_conn = None
    client._ensure_connection = lambda *args, **kwargs: None
    client.client = _FakePymodbus()
    client.reads = []

    def read(register, count):
        client.reads.append(register)
        return [1]          # the inverter still holds the armed value
    client.read_holding_registers = read
    return client


def test_a_refused_write_is_reported_as_not_written():
    client = _client()
    client._wit_control_last_write[30409] = time.time()      # written 22 s ago, say

    assert client.write_register_verified(30409, 50) == (False, False)
    assert client.client.writes == [], "the refused write reached the inverter"
    assert client.reads == [], "a write that never left was read back as if it had"


@pytest.mark.parametrize("register", [30100, 30407])
def test_a_release_gets_through_the_cooldown(register):
    """The reporter's case: disarm inside 30 s of arming."""
    client = _client()
    client._wit_control_last_write[register] = time.time()

    assert client.write_register(register, 0) is True
    assert client.client.writes == [(register, 0)]


@pytest.mark.parametrize("register", [30100, 30407])
def test_arming_inside_the_cooldown_is_still_refused(register):
    client = _client()
    client._wit_control_last_write[register] = time.time()

    assert client.write_register(register, 1) is False
    assert client.client.writes == []


def test_only_those_two_registers_release_on_zero():
    """0 on 30409 is a power setpoint, not a release - it stays limited."""
    client = _client()
    client._wit_control_last_write[30409] = time.time()
    assert client.write_register(30409, 0) is False


# ---------------------------------------------------------------------------
# Every entity that uses the verified write raises when it was refused
# ---------------------------------------------------------------------------

def _callers():
    found = []
    for path in ("select.py", "number.py", "time.py"):
        source = (COMPONENT / path).read_text(encoding="utf-8")
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                body = ast.get_source_segment(source, node)
                if "write_register_verified" in body and node.name != "write_register_verified":
                    found.append((path, node.name, body))
    return found


CALLERS = _callers()


def test_there_are_callers_to_check():
    assert len(CALLERS) >= 6


@pytest.mark.parametrize("path, name, body", CALLERS, ids=[f"{p}:{n}" for p, n, _ in CALLERS])
def test_a_refused_write_raises_to_the_caller(path, name, body):
    assert "if not write_ok:" in body, f"{path}:{name} ignores a refused write"
    after = body.split("if not write_ok:", 1)[1].split("if write_ok:", 1)[0]
    assert "raise HomeAssistantError(RATE_LIMITED_MESSAGE" in after, (
        f"{path}:{name} returns normally when the cooldown refused its write")


# ---------------------------------------------------------------------------
# Not-stored command registers are never skipped as no-ops
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("control", ["remote_power_control_charging_time",
                                     "remote_charge_and_discharge_power"])
def test_vpp_command_registers_are_marked_not_stored(control):
    assert _const.WRITABLE_REGISTERS[control].get("not_stored") is True


def test_the_no_op_skip_honours_not_stored():
    source = (COMPONENT / "number.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    klass = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "GrowattGenericNumber")
    fn = next(n for n in klass.body if isinstance(n, ast.AsyncFunctionDef) and n.name == "async_set_native_value")
    body = ast.get_source_segment(source, fn)
    skip = body.index("skipping write to register")
    guard = body.index("self._control_config.get('not_stored')")
    assert guard < skip, "the not_stored guard must come before the no-op skip"
