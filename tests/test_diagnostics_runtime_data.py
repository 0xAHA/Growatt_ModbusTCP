"""Diagnostics must include the values the read path sets dynamically (#500).

Battery 2/3/4 (batteryN_*) and similar values are assigned with setattr() only when the
pack reports, so they are not GrowattData dataclass fields. Diagnostics dumped the data
with asdict(), which sees declared fields only, so a dump from a two-pack system carried
nothing about pack 2 - awake or asleep. #500 had to be worked out from screenshots.
"""
from __future__ import annotations

import importlib
from dataclasses import asdict
from pathlib import Path

_const = importlib.import_module("growatt_under_test.const")
_gm = importlib.import_module("growatt_under_test.growatt_modbus")

runtime = _const.runtime_data_attributes
COMPONENT = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"


def _two_pack_data():
    data = _gm.GrowattData()
    data.battery_soc = 55.0
    setattr(data, "battery2_voltage", 52.4)
    setattr(data, "battery2_soc", 20.0)
    setattr(data, "battery2_current_low", -3.1)
    return data


def test_asdict_alone_misses_pack_two():
    """The gap: the thing diagnostics used to rely on cannot see these values."""
    assert "battery2_soc" not in asdict(_two_pack_data())


def test_pack_two_values_are_reported():
    assert runtime(_two_pack_data()) == {
        "battery2_current_low": -3.1,
        "battery2_soc": 20.0,
        "battery2_voltage": 52.4,
    }


def test_declared_fields_are_not_repeated():
    """Those are already in `data`; duplicating them would hide the difference."""
    out = runtime(_two_pack_data())
    assert "battery_soc" not in out
    assert "unread_fields" not in out


def test_a_sleeping_pack_is_simply_absent():
    """Pack 2 at 0 V never gets its attributes set - absence is the evidence."""
    assert runtime(_gm.GrowattData()) == {}


def test_private_and_non_dataclass_values_are_ignored():
    data = _gm.GrowattData()
    setattr(data, "_internal", 1)
    assert runtime(data) == {}
    assert runtime(None) == {}
    assert runtime({"battery2_soc": 1}) == {}


def test_diagnostics_dumps_it_and_lists_entities():
    """The consumer: diagnostics.py must actually call the helper and list the entities.
    (The full output is exercised in tests_ha, which needs Home Assistant.)"""
    source = (COMPONENT / "diagnostics.py").read_text(encoding="utf-8")
    assert 'diagnostics["runtime_data"] = _safe(runtime_data_attributes(data))' in source
    assert source.count('diagnostics["entities"] = _entity_summary(hass, entry)') == 2, (
        "the entity list must be in the dump whether or not the coordinator loaded"
    )
