"""SPH Battery First / Grid First slots 4-6 start at 1018 and 1027 (#484).

Protocol V1.39 and the SPH-HUB manual put them at 1017+3n and 1026+3n. An SPH3600 owner set
each slot in the Growatt app to a distinct marker time, all disabled, and scanned: every
start/end landed one register later than documented, and 1017 read 0. Enabling Battery
First 4 changed only 1020; enabling Grid First 4 changed only 1029. The document's table
ends with a stray second "Bat First Start Time 4" at 1035 - one register too many, which
is what a table numbered one off leaves behind.

Mapped as documented, the time entities wrote each slot as an FC16 triple at the wrong
base: a slot's end time into its start register, and the enable flag into its end.
"""
from __future__ import annotations

import importlib

import pytest

_gm = importlib.import_module("growatt_under_test.growatt_modbus")
_const = importlib.import_module("growatt_under_test.const")

EXPECTED = {f"{kind}_first_time_period_{p}_{part}": base + (p - 4) * 3 + i
            for kind, base in (("batt", 1018), ("grid", 1027))
            for p in (4, 5, 6)
            for i, part in enumerate(("start", "end", "enable"))}

MAPS = [name for name, m in _const.REGISTER_MAPS.items()
        if any(r.get("name") == "batt_first_time_period_4_start"
               for r in m.get("holding_registers", {}).values())]

# Holding 1015-1039 from the reporter's third scan: markers set, BF4 and GF4 enabled.
SCAN = {1018: 769, 1019: 770, 1020: 1, 1021: 779, 1022: 780, 1024: 789, 1025: 790,
        1027: 257, 1028: 258, 1029: 1, 1030: 267, 1031: 268, 1033: 277, 1034: 278,
        1039: 20}


def test_the_sph_maps_are_covered():
    assert MAPS


@pytest.mark.parametrize("map_name", MAPS)
def test_each_slot_register_is_where_the_inverter_put_it(map_name):
    holding = _const.REGISTER_MAPS[map_name]["holding_registers"]
    found = {r["name"]: addr for addr, r in holding.items() if r.get("name") in EXPECTED}
    assert found == EXPECTED
    assert 1017 not in holding or holding[1017].get("name") not in EXPECTED


def test_the_controls_write_the_same_registers():
    for name, addr in EXPECTED.items():
        assert _const.WRITABLE_REGISTERS[name]["register"] == addr, name


def test_the_reporters_scan_reads_back_as_set_in_the_app():
    client = _gm.GrowattModbus(connection_type="tcp", host="10.0.0.1", port=502,
                               slave_id=1, register_map="SPH_3000_6000")
    client.read_input_registers = lambda start, count, log_errors=True: [0] * count
    client.read_holding_registers = (
        lambda start, count: [SCAN.get(a, 0) for a in range(start, start + count)])
    data = client.read_all_data()

    assert (data.batt_first_time_period_4_start, data.batt_first_time_period_4_end,
            data.batt_first_time_period_4_enable) == (769, 770, 1)     # 03:01-03:02, on
    assert (data.batt_first_time_period_6_start, data.batt_first_time_period_6_end) == (789, 790)
    assert (data.grid_first_time_period_4_start, data.grid_first_time_period_4_enable) == (257, 1)
    assert (data.grid_first_time_period_6_end, data.grid_first_time_period_6_enable) == (278, 0)
