"""MIN TL-XH priority control and diagnostic readback must describe one state (#400).

The generic "Priority Mode" sensor reads `data.priority_mode`, a plain GrowattData field
with no gate at all - not even the decorative hasattr() kind rule 6 catalogues. This
profile has never had a register named 'priority_mode'; the real one is 3018,
`tl_xh_priority_mode`, with its own numeric encoding (0/2/3 rather than 0/1/2). So the
generic sensor sat at its dataclass default - 0, "Load First" - on every poll, forever,
while the correct state was being read all along into a field only the writable select
used.

A reporter selected Battery First and confirmed it on hardware: solar charged the battery
while the house imported its full consumption from the grid, unambiguous Battery First
behaviour. The diagnostic sensor kept reporting Load First throughout - two entities
describing different states from one inverter.

Root cause found, and a working fix proposed, by @GoncaloRibeiro11.
"""
from __future__ import annotations

import importlib

import pytest

_const = importlib.import_module("growatt_under_test.const")
_gm = importlib.import_module("growatt_under_test.growatt_modbus")

MAP = {
    "name": "MIN TL-XH test map",
    "holding_registers": {
        3018: {"name": "tl_xh_priority_mode", "maps_to": "priority_mode", "scale": 1, "unit": ""},
    },
    "input_registers": {},
}


def _client(cache: dict) -> _gm.GrowattModbus:
    c = _gm.GrowattModbus.__new__(_gm.GrowattModbus)
    c.register_map = MAP
    c.register_map_name = "MIN TL-XH test map"
    c._register_cache = cache
    c._holding_register_cache = dict(cache)
    c.read_holding_registers = lambda addr, count: [cache[addr]] if addr in cache else None
    return c


@pytest.mark.parametrize(
    ("raw_value", "standard_value", "label"),
    [(0, 0, "Load First"), (2, 1, "Battery First"), (3, 2, "Grid First")],
)
def test_the_generic_sensor_follows_register_3018(raw_value, standard_value, label):
    """The bug, reproduced directly: without the fix, priority_mode never moves off 0."""
    client = _client({3018: raw_value})
    data = _gm.GrowattData()

    client._read_device_info(data)

    assert data.tl_xh_priority_mode == raw_value, "the select's own field must still be raw"
    assert data.priority_mode == standard_value, (
        f"raw {raw_value} ({label}) did not translate into the generic sensor's encoding"
    )


def test_an_unread_register_does_not_fabricate_a_translated_state():
    """Not about tl_xh_priority_mode's own default (3, Grid First - unrelated to this bug) -
    only that a register that never answered must not cause priority_mode to move at all."""
    client = _client({})  # 3018 never answers this poll
    data = _gm.GrowattData()
    before = data.priority_mode

    client._read_device_info(data)

    assert data.priority_mode == before, "an unread register moved the translated sensor"


def test_the_translation_table_matches_the_sensor_value_map():
    """The two encodings have to agree, or a correct translation still displays the wrong
    label. sensor.py's value_map is the source of truth for what the UI shows."""
    assert _gm.TL_XH_PRIORITY_MODE_TO_STANDARD == {0: 0, 2: 1, 3: 2}


def test_the_register_feeds_diagnostics_as_a_backed_name():
    """profile_register_names() (#448) must list priority_mode for this profile now that it
    is genuinely populated - otherwise the diagnostics dump still implies it is a default."""
    register_map = _const.REGISTER_MAPS["MIN_TL_XH_3000_10000_V201"]
    register = register_map["holding_registers"][3018]

    assert register["name"] == "tl_xh_priority_mode"
    assert register["maps_to"] == "priority_mode"
    assert {"tl_xh_priority_mode", "priority_mode"}.issubset(
        _const.profile_register_names(register_map)
    )
