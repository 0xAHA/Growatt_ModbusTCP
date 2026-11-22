"""WIT VPP SOC cut-offs skip a write that would change nothing (#384, #509).

30404 (charge cut-off) and 30405 (on-grid discharge cut-off) are stored registers. #509 asks
how to block discharge for an idle period, and the documented answer is to raise 30405 for
the period and restore it afterwards - something an optimizer will re-apply on a schedule.
The generic number path already compared a fresh read against the value before writing; the
two WIT classes wrote unconditionally, spending an EEPROM cycle on every repeat.

`number.py` imports Home Assistant, which this suite does not have, so the helper and the two
`async_set_native_value` methods are extracted with `ast` and run against stubs.
"""
from __future__ import annotations

import ast
import asyncio
import logging
import types
from pathlib import Path

import pytest

SOURCE = (Path(__file__).parent.parent / "custom_components" / "growatt_modbus" / "number.py").read_text(encoding="utf-8")
CLASSES = {"GrowattWitVppChargeCutoffSocNumber": (30404, "vpp_charge_stop_soc"),
           "GrowattWitVppDischargeCutoffSocNumber": (30405, "vpp_ongrid_discharge_soc")}


def _namespace():
    tree = ast.parse(SOURCE)
    ns = {"_LOGGER": logging.getLogger("test"), "int": int, "len": len, "Exception": Exception}
    helper = next(n for n in tree.body if isinstance(n, ast.AsyncFunctionDef)
                  and n.name == "_inverter_already_holds")
    exec(compile(ast.Module(body=[helper], type_ignores=[]), "number.py", "exec"), ns)
    methods = {}
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name in CLASSES:
            fn = next(n for n in node.body if isinstance(n, ast.AsyncFunctionDef)
                      and n.name == "async_set_native_value")
            local = dict(ns)
            exec(compile(ast.Module(body=[fn], type_ignores=[]), "number.py", "exec"), local)
            methods[node.name] = local["async_set_native_value"]
    assert set(methods) == set(CLASSES)
    return methods


METHODS = _namespace()


class _Client:
    def __init__(self, current):
        self.current = current
        self.writes = []

    def read_holding_registers(self, register, count):
        return None if self.current is None else [self.current]

    def write_register(self, register, value):
        self.writes.append((register, value))
        return True


class _Hass:
    async def async_add_executor_job(self, fn, *args):
        return fn(*args)


def _entity(class_name, current):
    register, _field = CLASSES[class_name]
    client = _Client(current)

    async def refresh():
        return None

    coordinator = types.SimpleNamespace(modbus_client=client, data=None,
                                        async_update_listeners=lambda: None,
                                        async_request_refresh=refresh)
    entity = types.SimpleNamespace(hass=_Hass(), coordinator=coordinator,
                                   VPP_CHARGE_CUTOFF_SOC=30404, VPP_DISCHARGE_CUTOFF_SOC=30405)
    return entity, client, register


@pytest.mark.parametrize("class_name", CLASSES)
def test_unchanged_value_is_not_written(class_name):
    entity, client, _ = _entity(class_name, current=60)
    asyncio.run(METHODS[class_name](entity, 60.0))
    assert client.writes == []


@pytest.mark.parametrize("class_name", CLASSES)
def test_changed_value_is_written(class_name):
    entity, client, register = _entity(class_name, current=10)
    asyncio.run(METHODS[class_name](entity, 60.0))
    assert client.writes == [(register, 60)]


@pytest.mark.parametrize("class_name", CLASSES)
def test_unreadable_register_still_writes(class_name):
    """A skipped write that should have happened is worse than a redundant one."""
    entity, client, register = _entity(class_name, current=None)
    asyncio.run(METHODS[class_name](entity, 60.0))
    assert client.writes == [(register, 60)]
