"""Max output power rate when the inverter will not store it (#501).

V1.39 holding 2 (PF CMD) decides whether a write to holding 3 is stored. When it is not,
the rate is applied but register 3 keeps reading its initial value. Two MOD TL3-X read
holding 2 as 65535 and register 3 as 100 while throttled, and the integration:
- skipped "write 100" as a no-op, because register 3 already read 100 - so the throttle
  could not be lifted from Home Assistant;
- reported every lower rate as reverted.

`number.py` imports Home Assistant, which this suite does not have, so the methods are
extracted with `ast` and run against stubs.
"""
from __future__ import annotations

import ast
import asyncio
import importlib
import logging
import types
from pathlib import Path

import pytest

_const = importlib.import_module("growatt_under_test.const")
SOURCE = (Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
          / "number.py").read_text(encoding="utf-8")
CONFIG = _const.WRITABLE_REGISTERS["max_output_power_rate"]


class _HomeAssistantError(Exception):
    pass


class _ModbusWriteError(Exception):
    pass


def _methods():
    tree = ast.parse(SOURCE)
    klass = next(n for n in tree.body
                 if isinstance(n, ast.ClassDef) and n.name == "GrowattGenericNumber")
    wanted = {"_write_is_stored", "async_set_native_value", "native_value"}
    funcs = [n for n in klass.body
             if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name in wanted]
    assert {f.name for f in funcs} == wanted
    for f in funcs:
        f.decorator_list = []
    ns = {"_LOGGER": logging.getLogger("test"), "HomeAssistantError": _HomeAssistantError,
          "ModbusWriteError": _ModbusWriteError, "RATE_LIMITED_MESSAGE": "{name}",
          "VPP_CONTROL_AVAILABILITY_FLAG": {}}
    exec(compile(ast.Module(body=funcs, type_ignores=[]), "number.py", "exec"), ns)
    return {name: ns[name] for name in wanted}


METHODS = _methods()


class _Client:
    """Holding 3 always reads 100, whatever was written - as on the reporter's MOD."""

    def __init__(self, holding2):
        self.holding = {2: holding2, 3: 100}
        self.writes = []

    def read_holding_registers(self, register, count):
        value = self.holding.get(register)
        return None if value is None else [value]

    def write_register_verified(self, register, value):
        self.writes.append((register, value))
        return True, self.holding[register] == value


class _Hass:
    async def async_add_executor_job(self, fn, *args):
        return fn(*args)


class _Entity:
    pass


def _entity(holding2):
    client = _Client(holding2)
    tracked = []

    async def refresh():
        return None

    data = types.SimpleNamespace(max_output_power_rate=100, unread_fields=())
    coordinator = types.SimpleNamespace(
        modbus_client=client, data=data, async_request_refresh=refresh,
        track_write=lambda *args: tracked.append(args))
    entity = _Entity()
    entity.hass = _Hass()
    entity.coordinator = coordinator
    entity._control_name = "max_output_power_rate"
    entity._control_config = CONFIG
    entity._unstored_write = None
    entity._attr_name = "Max Output Power Rate"
    entity._check_paired_constraint = lambda value: None
    entity.async_write_ha_state = lambda: None
    for name, fn in METHODS.items():
        setattr(entity, name, fn.__get__(entity))
    return entity, client, tracked


def _set(entity, value):
    asyncio.run(entity.async_set_native_value(value))


def _shown(entity):
    return entity.native_value()


@pytest.mark.parametrize("holding2", [0, 0xFFFF])
def test_writing_100_is_sent_when_not_stored(holding2):
    """The reporter's case: the throttle could not be lifted."""
    entity, client, _ = _entity(holding2)
    _set(entity, 100)
    assert client.writes == [(3, 100)]


@pytest.mark.parametrize("holding2", [0, 0xFFFF])
def test_a_lower_rate_is_not_reported_as_reverted(holding2):
    entity, client, tracked = _entity(holding2)
    _set(entity, 80)
    assert client.writes == [(3, 80)]
    assert tracked == [], "an unchanged register was queued for the reversion check"


def test_the_entity_shows_what_was_written():
    entity, _, _ = _entity(0xFFFF)
    _set(entity, 80)
    assert _shown(entity) == 80


def test_the_entity_follows_the_register_once_it_moves():
    """Something else changed the setting: the register is evidence again."""
    entity, _, _ = _entity(0xFFFF)
    _set(entity, 80)
    entity.coordinator.data.max_output_power_rate = 60
    assert _shown(entity) == 60
    entity.coordinator.data.max_output_power_rate = 100
    assert _shown(entity) == 100


def test_stored_keeps_the_no_op_skip():
    """Holding 2 = 1: register 3 is stored and the EEPROM saving still applies (#384)."""
    entity, client, _ = _entity(1)
    _set(entity, 100)
    assert client.writes == []


def test_stored_keeps_the_reversion_check():
    entity, client, tracked = _entity(1)
    _set(entity, 80)
    assert client.writes == [(3, 80)]
    assert tracked and tracked[0][:2] == (3, 80)
    assert _shown(entity) == 100


def test_unreadable_switch_keeps_the_normal_path():
    """Nothing is known, so nothing changes for models where holding 2 does not answer."""
    entity, client, tracked = _entity(None)
    _set(entity, 100)
    assert client.writes == []
    _set(entity, 80)
    assert tracked


def test_only_register_3_is_gated():
    gated = {name for name, cfg in _const.WRITABLE_REGISTERS.items()
             if cfg.get("stored_if_holding_reads")}
    assert gated == {"max_output_power_rate"}
    assert CONFIG["stored_if_holding_reads"] == (2, 1)
