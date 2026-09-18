"""A failed backup box register read must not be reported as a genuine 0 (#450).

box_connect_flag lives at register 3320, outside the 3281-3298 sub-range that carries
box_work_mode, box_temperature, box_grid_power and box_load_power. A reporter's debug log
showed a block timeout on 3281-3298 landing right next to a successful read of 3320:

    connect=1 bypass=0 mode=0 temp=0C grid=0W load=0W relay=0    <- sub-range timed out
    connect=1 bypass=0 mode=1 temp=44C grid=45W load=2104W       <- next poll, all fine

`GrowattData()` is constructed fresh every poll (growatt_modbus.py:2942), so a field that
`_read_backup_box_data` skips on a failed read is not "the last known value" - it is the
dataclass default, 0. box_work_mode's value_map reads 0 as "Off-Grid", identical to what a
genuine off-grid reading would show, so a transport hiccup on a unit that has never lost the
grid was reported as having done so.

`_set_from_register` already solves exactly this shape elsewhere (#384): mark the field
unread rather than publish its default. `_read_backup_box_data` predates that helper and
used a bare setattr-on-success with no failure branch. This proves the fields it reads are
now marked unread the same way.
"""
from __future__ import annotations

import importlib

import pytest

_gm = importlib.import_module("growatt_under_test.growatt_modbus")

GrowattData = _gm.GrowattData

# box_connect_flag (3320) is deliberately a separate sub-range from the rest (3281-3298),
# matching the real profile layout that produced the report.
MAP = {
    "name": "backup box test",
    "input_registers": {
        3320: {"name": "box_connect_flag", "scale": 1, "unit": ""},
        3281: {"name": "box_bypass_status", "scale": 1, "unit": ""},
        3282: {"name": "box_work_mode", "scale": 1, "unit": ""},
        3283: {"name": "box_error_code", "scale": 1, "unit": ""},
        3284: {"name": "box_warning_code", "scale": 1, "unit": ""},
        3285: {"name": "box_relay_status", "scale": 1, "unit": ""},
        3286: {"name": "box_temperature", "scale": 1, "unit": ""},
        3287: {"name": "box_grid_voltage", "scale": 0.1, "unit": ""},
        3289: {"name": "box_grid_power_high", "scale": 1, "unit": "", "pair": 3290},
        3290: {"name": "box_grid_power_low", "scale": 1, "unit": "", "pair": 3289,
               "combined_scale": 0.1, "combined_unit": "W"},
        3297: {"name": "box_load_power_high", "scale": 1, "unit": "", "pair": 3298},
        3298: {"name": "box_load_power_low", "scale": 1, "unit": "", "pair": 3297,
               "combined_scale": 0.1, "combined_unit": "W"},
    },
}

FULL_CACHE = {
    3320: 1, 3281: 0, 3282: 1, 3283: 0, 3284: 0, 3285: 0,
    3286: 44, 3287: 2300,
    3289: 0, 3290: 450,     # -> 45.0 W
    3297: 0, 3298: 21040,   # -> 2104.0 W
}


def _client(cache: dict) -> _gm.GrowattModbus:
    c = _gm.GrowattModbus.__new__(_gm.GrowattModbus)
    c.register_map = MAP
    c._register_cache = cache
    c._pair_shape_suspect = {}
    c._pair_shape_warned = set()
    c._underflow_warned = set()
    c._battery_power_scale_override = None
    return c


def test_a_healthy_poll_reads_everything_and_marks_nothing_unread():
    client = _client(FULL_CACHE)
    data = GrowattData()
    client._read_backup_box_data(data)

    assert data.box_connect_flag == 1
    assert data.box_work_mode == 1
    assert data.box_temperature == 44.0
    assert data.box_grid_power == pytest.approx(45.0)
    assert data.box_load_power == pytest.approx(2104.0)
    assert data.unread_fields == set()


def test_the_reported_timeout_marks_work_mode_unread_rather_than_off_grid():
    """THE bug. The 3281-3298 sub-range never arrives; 3320 does, exactly as logged."""
    cache = {3320: 1}  # only the connect flag answered this poll
    client = _client(cache)
    data = GrowattData()
    client._read_backup_box_data(data)

    assert data.box_connect_flag == 1, "the one register that did answer must still be used"
    assert "box_work_mode" in data.unread_fields, (
        "a failed read of box_work_mode must not silently pass as the dataclass default"
    )
    # The default is 0, and 0 decodes as Off-Grid - that value must never reach the sensor.
    # unread_fields is what stops it; asserting the flag is the point of this test.


def test_every_field_in_the_failed_sub_range_is_marked_unread():
    cache = {3320: 1}
    client = _client(cache)
    data = GrowattData()
    client._read_backup_box_data(data)

    for attr in (
        "box_bypass_status", "box_work_mode", "box_error_code", "box_warning_code",
        "box_relay_status", "box_temperature", "box_grid_voltage",
        "box_grid_power", "box_load_power",
    ):
        assert attr in data.unread_fields, f"{attr} read failed but was not marked unread"


def test_a_partial_failure_only_marks_what_actually_failed():
    """Not every field in the block failed on the reporter's own second poll - the fix must
    not become a blanket withholder that marks fields unread even when they did read."""
    cache = dict(FULL_CACHE)
    del cache[3282]  # only box_work_mode's register failed to arrive this poll

    client = _client(cache)
    data = GrowattData()
    client._read_backup_box_data(data)

    assert data.unread_fields == {"box_work_mode"}
    assert data.box_temperature == 44.0
    assert data.box_grid_power == pytest.approx(45.0)
