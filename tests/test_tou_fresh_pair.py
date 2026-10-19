"""TOU period edits must not undo each other (#475).

A period's start word packs enable (bit 15), priority (bits 13-14) and start time. The
Priority and Enable selects rebuilt it from the coordinator's last poll, so two changes to
one period inside a poll interval collided: the second write was based on the word before
the first, and put it back. A MID 25KTL3-XH owner setting several TOU values in a row found
it hit and miss.

The packing and the choice of source live in tou_packing.py, which is importable here; the
selects and time entities import Home Assistant, so their use of it is checked from source.
"""
from __future__ import annotations

import ast
import importlib
import types
from pathlib import Path

import pytest

tou = importlib.import_module("growatt_under_test.tou_packing")
COMPONENT = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"

# Period 3 from the reporter's scans: 0xCF00 = enabled, Grid, 15:00; end 0x1000 = 16:00.
GRID_ON_1500 = 0xCF00
END_1600 = 0x1000


def test_priority_keeps_time_and_enable():
    assert tou.with_priority(GRID_ON_1500, 1) == 0xAF00   # Battery, still enabled, 15:00


def test_enable_keeps_time_and_priority():
    assert tou.with_enable(GRID_ON_1500, False) == 0x4F00  # Grid, disabled, 15:00
    assert tou.with_enable(0x4F00, True) == GRID_ON_1500


def test_time_keeps_enable_and_priority():
    assert tou.with_time(GRID_ON_1500, 7, 30) == 0xC71E


def test_the_fresh_pair_wins_over_the_last_poll():
    stale = types.SimpleNamespace(mod_tou_3_start=0, mod_tou_3_end=0)
    start, end, fresh = tou.current_pair([GRID_ON_1500, END_1600], stale,
                                         "mod_tou_3_start", "mod_tou_3_end")
    assert (start, end, fresh) == (GRID_ON_1500, END_1600, True)


def test_a_failed_read_falls_back_to_the_last_poll():
    data = types.SimpleNamespace(mod_tou_3_start=GRID_ON_1500, mod_tou_3_end=END_1600)
    assert tou.current_pair(None, data, "mod_tou_3_start", "mod_tou_3_end") == (
        GRID_ON_1500, END_1600, False)


def test_the_reporters_sequence_no_longer_reverts():
    """Priority -> Battery, then Enable -> Disabled before the next poll.

    The poll still says Grid. Built from it, the second write sends Grid back. Built from
    the inverter, it keeps the Battery written a moment earlier."""
    inverter = {"start": GRID_ON_1500, "end": END_1600}
    last_poll = types.SimpleNamespace(mod_tou_3_start=GRID_ON_1500, mod_tou_3_end=END_1600)

    def change(apply):
        start, end, _ = tou.current_pair([inverter["start"], inverter["end"]], last_poll,
                                         "mod_tou_3_start", "mod_tou_3_end")
        inverter["start"] = apply(start)

    change(lambda s: tou.with_priority(s, 1))       # Battery
    change(lambda s: tou.with_enable(s, False))     # Disabled

    assert (inverter["start"] >> 13) & 0x3 == 1, "the priority change was undone"
    assert inverter["start"] >> 15 == 0


def test_publish_updates_the_shared_data():
    data = types.SimpleNamespace(mod_tou_3_start=0, mod_tou_3_end=0)
    tou.publish(data, "mod_tou_3_start", "mod_tou_3_end", GRID_ON_1500, END_1600)
    assert (data.mod_tou_3_start, data.mod_tou_3_end) == (GRID_ON_1500, END_1600)


def _method(path: str, cls: str, name: str) -> str:
    source = (COMPONENT / path).read_text(encoding="utf-8")
    tree = ast.parse(source)
    klass = next(n for n in ast.walk(tree) if isinstance(n, ast.ClassDef) and n.name == cls)
    fn = next(n for n in klass.body
              if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name)
    return ast.get_source_segment(source, fn)


@pytest.mark.parametrize("cls", ["GrowattModTouPriority", "GrowattModTouEnable"])
def test_the_selects_read_fresh_before_modifying(cls):
    body = _method("select.py", cls, "async_select_option")
    assert "read_holding_registers" in body
    assert "tou_current_pair(" in body
    assert body.index("read_holding_registers") < body.index("write_registers")
    assert "getattr(data, self._start_field" not in body, "still building from the last poll"


@pytest.mark.parametrize("path, cls, name", [
    ("select.py", "GrowattModTouPriority", "async_select_option"),
    ("select.py", "GrowattModTouEnable", "async_select_option"),
    ("time.py", "GrowattModTouTime", "async_set_value"),
])
def test_every_tou_entity_publishes_what_it_wrote(path, cls, name):
    body = _method(path, cls, name)
    assert "tou_publish(" in body
    assert "async_update_listeners()" in body
