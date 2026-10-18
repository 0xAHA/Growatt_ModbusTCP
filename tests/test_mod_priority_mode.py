"""MOD/MID-XH Priority Mode comes from the live input register (#475).

A MID 25KTL3-XH showed Priority Mode = Load First in every mode. Three scans, one per mode
set in the Growatt web interface:

    mode            input 3144   input 31002   holding 30476
    Load First           0            0              0
    Grid First           2            2              0
    Battery First        1            1              0

The profile has mapped input 3144 as `priority_mode` from the start, but nothing read it into
the field. Meanwhile the holding-register fallback for SPH/WIT read 30476, which on this map
is the VPP *default* mode and is 0 in all three, so it set Load First on every poll.

Driven through the real poll with the reporter's registers.
"""
from __future__ import annotations

import importlib

import pytest

_gm = importlib.import_module("growatt_under_test.growatt_modbus")

MAP = "MOD_6000_15000TL3_XH"


def _poll(input_3144: int):
    inputs = {3144: input_3144, 31002: input_3144}
    holding = {30476: 0}
    client = _gm.GrowattModbus(connection_type="tcp", host="10.0.0.1", port=502,
                               slave_id=1, register_map=MAP)
    client.read_input_registers = (
        lambda start, count, log_errors=True: [inputs.get(a, 0) for a in range(start, start + count)]
    )
    client.read_holding_registers = (
        lambda start, count: [holding.get(a, 0) for a in range(start, start + count)]
    )
    return client.read_all_data()


@pytest.mark.parametrize("raw, mode", [(0, "Load First"), (2, "Grid First"), (1, "Battery First")])
def test_priority_mode_follows_the_inverter(raw, mode):
    data = _poll(raw)
    assert data.priority_mode == raw, f"{mode}: read {data.priority_mode}"


def test_a_failed_read_is_unknown_not_load_first():
    client = _gm.GrowattModbus(connection_type="tcp", host="10.0.0.1", port=502,
                               slave_id=1, register_map=MAP)

    def read_input_registers(start, count, log_errors=True):
        if start <= 3144 < start + count:
            return None
        return [0] * count

    client.read_input_registers = read_input_registers
    client.read_holding_registers = lambda start, count: [0] * count
    data = client.read_all_data()
    assert data is None or "priority_mode" in data.unread_fields
