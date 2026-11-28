"""SPA priority mode (holding 1044) and CT2 power (input 2102/2103), #510.

Priority mode: V1.39 lists holding 1044 as R. A SPA3000TL-BL read 0 / 1 / 0 as Load
First / Battery First / Load First were set in Shine, so the SPA profile marks it RW and
gets a disabled-by-default select. A Modbus write is untested, and every other profile
keeps 1044 read-only. 1044 is a stored setting, so the select reads it first and does not
send a value it already holds (#504: Growatt support's guidance is 5-10 writes a day).

CT2: both SPA3000TL-BL read 0 at night and 1600-1800 raw in daylight with the clamp on a
Solis output. The 0.1 W scale is inferred from Pac next to it, not documented.

`select.py` imports Home Assistant, which this suite does not have, so the write method is
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
_gm = importlib.import_module("growatt_under_test.growatt_modbus")
_dp = importlib.import_module("growatt_under_test.device_profiles")
REGISTER_MAPS = _const.REGISTER_MAPS
SPA = "SPA_3000_6000_TL_BL"
CONFIG = _const.WRITABLE_REGISTERS["priority_mode"]
SOURCE = (Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
          / "select.py").read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Which profiles get a writable priority mode
# ---------------------------------------------------------------------------

def _offered(name: str) -> bool:
    """Mirror of select.py's generic gate for one control."""
    holding = REGISTER_MAPS[name].get("holding_registers", {})
    if CONFIG["register"] not in holding:
        return False
    if _const.is_read_only_register(holding[CONFIG["register"]]):
        return False
    only = CONFIG.get("only_profiles")
    return not only or name in only


@pytest.mark.parametrize("name", sorted(REGISTER_MAPS))
def test_priority_mode_is_writable_on_spa_only(name):
    assert _offered(name) is (name == SPA), name


def test_other_1044_profiles_keep_it_read_only():
    """SPH and SPH-TL3 map holding 1044 too - the SPA override must not leak to them."""
    for name in ("SPH_3000_6000", "SPH_TL3_3000_10000"):
        assert _const.is_read_only_register(REGISTER_MAPS[name]["holding_registers"][1044]), name


def test_select_is_disabled_by_default_and_skips_unchanged():
    assert CONFIG["disabled_by_default"] is True
    assert CONFIG["skip_unchanged"] is True
    assert CONFIG["options"] == {0: "Load First", 1: "Battery First", 2: "Grid First"}


def test_spa_has_no_input_register_named_priority_mode():
    """select.py resolves the write address by name through the *input* map first. An
    input named priority_mode would send the write to that address instead of 1044."""
    names = {r["name"] for r in REGISTER_MAPS[SPA]["input_registers"].values()}
    assert "priority_mode" not in names


# ---------------------------------------------------------------------------
# The write
# ---------------------------------------------------------------------------

class _HomeAssistantError(Exception):
    pass


class _ModbusWriteError(Exception):
    pass


def _select_option():
    tree = ast.parse(SOURCE)
    klass = next(n for n in tree.body
                 if isinstance(n, ast.ClassDef) and n.name == "GrowattGenericSelect")
    func = next(n for n in klass.body
                if isinstance(n, ast.AsyncFunctionDef) and n.name == "async_select_option")
    ns = {"_LOGGER": logging.getLogger("test"), "HomeAssistantError": _HomeAssistantError,
          "ModbusWriteError": _ModbusWriteError, "RATE_LIMITED_MESSAGE": "{name}",
          "asyncio": asyncio}
    exec(compile(ast.Module(body=[func], type_ignores=[]), "select.py", "exec"), ns)
    return ns["async_select_option"]


SELECT_OPTION = _select_option()


class _Client:
    def __init__(self, reads_1044):
        self.reads_1044 = reads_1044
        self.writes: list = []
        self.register_map = {"name": "SPA 3000-6000TL-BL"}

    def _find_register_by_name(self, name):
        return None                      # SPA: no input register of that name

    def read_holding_registers(self, register, count):
        assert register == 1044
        return None if self.reads_1044 is None else [self.reads_1044]

    def write_register_verified(self, register, value):
        self.writes.append((register, value))
        return True, True


class _Hass:
    async def async_add_executor_job(self, fn, *args):
        return fn(*args)


def _entity(reads_1044):
    client = _Client(reads_1044)

    async def refresh():
        return None

    coordinator = types.SimpleNamespace(modbus_client=client, async_request_refresh=refresh,
                                        track_write=lambda *a: None)
    entity = types.SimpleNamespace(_control_config=CONFIG, _control_name="priority_mode",
                                   coordinator=coordinator, hass=_Hass())
    return entity, client


def _select(reads_1044, option):
    entity, client = _entity(reads_1044)
    asyncio.run(SELECT_OPTION(entity, option))
    return client.writes


def test_an_unchanged_mode_is_not_written():
    assert _select(1, "Battery First") == []


@pytest.mark.parametrize("current, option, value", [
    (0, "Battery First", 1), (1, "Load First", 0), (0, "Grid First", 2),
])
def test_a_changed_mode_is_written_to_1044(current, option, value):
    assert _select(current, option) == [(1044, value)]


def test_a_failed_read_still_writes():
    """Skipping on a failed read would silently drop the request."""
    assert _select(None, "Battery First") == [(1044, 1)]


def test_controls_without_the_flag_are_not_read_first():
    entity, client = _entity(reads_1044=1)
    entity._control_config = {k: v for k, v in CONFIG.items() if k != "skip_unchanged"}
    asyncio.run(SELECT_OPTION(entity, "Battery First"))
    assert client.writes == [(1044, 1)]


# ---------------------------------------------------------------------------
# CT2 power
# ---------------------------------------------------------------------------

def _poll(inputs: dict):
    client = _gm.GrowattModbus(connection_type="tcp", host="10.0.0.1", port=502,
                               slave_id=1, register_map=SPA)
    client.read_input_registers = lambda start, count, log_errors=True: [
        inputs.get(a, 0) for a in range(start, start + count)]
    client.read_holding_registers = lambda start, count, *a, **k: [0] * count
    return client.read_all_data()


@pytest.mark.parametrize("high, low, watts", [
    (0, 0, 0.0),            # night, SPA2
    (0, 1800, 180.0),       # daylight, SPA2
    (0, 1600, 160.0),       # daylight, SPA1 and SPA2 at the same minute
    (65535, 65436, -10.0),  # a reversed clamp reads small and negative, not ~429 MW
])
def test_ct2_power_decodes(high, low, watts):
    data = _poll({2000: 6, 2102: high, 2103: low})
    assert data.extra_inverter_power == pytest.approx(watts)
    assert "extra_inverter_power" not in data.unread_fields


def test_ct2_sensor_is_in_the_spa_sensor_set_only():
    owners = {k for k, p in _dp.INVERTER_PROFILES.items()
              if "extra_inverter_power" in p.get("sensors", set())}
    assert owners and all(_dp.INVERTER_PROFILES[k]["register_map"] == SPA for k in owners)
