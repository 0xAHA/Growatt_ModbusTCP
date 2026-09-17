"""A field the profile cannot fill is not a reading, and diagnostics must say so (#448).

Diagnostics dumps the whole `GrowattData` dataclass with `asdict()`. A field whose register
the selected profile never maps keeps its **declared default**, and in the dump that is
indistinguishable from a live value.

A WIT HU15 owner hit this. His dump carried:

    "priority_mode": 0,
    "tl_xh_priority_mode": 3,

and he reasonably asked whether two registers were disagreeing - 3 matching the "Battery
First" his app was showing. They were not. Register 3018 is a MIN TL-XH address, absent from
every WIT map, so that read is skipped entirely; `tl_xh_priority_mode` is declared
`= 3` in the dataclass, and 3 was the default rather than a measurement. Same for
`time_period_1_enable`, which comes from the SPH 1100-1108 block that WIT does not map.

`unread_fields` cannot cover this: it records registers that were **attempted and failed**,
and a block the profile does not define is never attempted.

Rather than guess which fields are stale - many are legitimately derived by the coordinator,
and marking those "not populated" would mislead in a new way - the dump carries the list of
names the profile can actually fill, and a note saying how to use it.
"""
from __future__ import annotations

import ast
import importlib
from pathlib import Path

import pytest

_const = importlib.import_module("growatt_under_test.const")
_gm = importlib.import_module("growatt_under_test.growatt_modbus")

COMPONENT = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
names_for = _const.profile_register_names


# ---------------------------------------------------------------------------
# The reporter's two fields
# ---------------------------------------------------------------------------

def test_the_wit_profile_cannot_fill_the_fields_he_asked_about():
    """THE case. Neither register is in a WIT map, so neither value in his dump was read."""
    wit = _const.REGISTER_MAPS["WIT_4000_15000TL3"]
    holding = set(wit.get("holding_registers", {}))
    assert 3018 not in holding, "3018 is a MIN TL-XH register and must not be on a WIT map"
    assert 1100 not in holding, "1100-1108 is the SPH time-period block"
    assert 1102 not in holding


def test_those_values_were_the_declared_defaults():
    """3 and 0 are what the dataclass declares - which is exactly what he saw."""
    data = _gm.GrowattData()
    assert data.tl_xh_priority_mode == 3
    assert data.time_period_1_enable == 0


def test_the_field_he_could_trust_is_mapped():
    """priority_mode came from 30476, which WIT does map - so that one was a real reading
    and the guidance must not sweep it up with the others."""
    wit = _const.REGISTER_MAPS["WIT_4000_15000TL3"]
    assert 30476 in wit.get("holding_registers", {})
    assert "priority_mode" in names_for(wit)


def test_the_unfillable_names_are_absent_from_the_wit_list():
    wit_names = set(names_for(_const.REGISTER_MAPS["WIT_4000_15000TL3"]))
    assert "tl_xh_priority_mode" not in wit_names
    assert "time_period_1_enable" not in wit_names


# ---------------------------------------------------------------------------
# The helper itself
# ---------------------------------------------------------------------------

def test_it_collects_names_aliases_and_maps_to():
    """All three are how a field gets filled, so all three count as "can fill"."""
    register_map = {
        "input_registers": {
            1: {"name": "pv1_voltage"},
            2: {"name": "ac_voltage_r", "alias": "ac_voltage"},
            3: {"name": "battery_voltage_vpp", "maps_to": "battery_voltage"},
        },
        "holding_registers": {30476: {"name": "priority_mode"}},
    }
    assert names_for(register_map) == [
        "ac_voltage", "ac_voltage_r", "battery_voltage", "battery_voltage_vpp",
        "priority_mode", "pv1_voltage",
    ]


@pytest.mark.parametrize("junk", [None, "", 0, [], {"input_registers": None}])
def test_it_never_raises_on_odd_input(junk):
    """Diagnostics must not fail - a dump that raises is worse than one with a gap."""
    assert isinstance(names_for(junk), list)


def test_every_shipped_profile_produces_names():
    """A profile yielding nothing would make the note actively misleading."""
    for key, register_map in _const.REGISTER_MAPS.items():
        assert names_for(register_map), f"{key} produced no register names"


# ---------------------------------------------------------------------------
# That diagnostics actually carries it
# ---------------------------------------------------------------------------

def _diagnostics_source() -> str:
    return (COMPONENT / "diagnostics.py").read_text(encoding="utf-8")


def test_the_dump_carries_the_list_and_the_note():
    source = _diagnostics_source()
    assert "profile_register_names" in source, (
        "diagnostics does not include the list, so a reader still cannot tell a default "
        "from a reading"
    )
    assert "data_note" in source


def test_the_note_points_at_the_list_and_distinguishes_unread_fields():
    """The note has to be usable on its own - someone reading a pasted dump has no code."""
    source = _diagnostics_source()
    tree = ast.parse(source)
    note = ""
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if "dataclass default" in node.value:
                note = node.value
                break
    assert note, "no note explaining that unmapped fields hold defaults"
    assert "profile_register_names" in note
    assert "unread_fields" in note
