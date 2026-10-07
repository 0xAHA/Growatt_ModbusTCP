"""AC charge energy cannot exceed the battery's total charge energy (#463).

Energy charged from the grid into the battery is part of all energy charged into it. Protocol
V1.39 gives input 112-115 two meanings, and SPH reads them as AC charge energy, which is
confirmed on an SPH 3000-6000 (#390). An SPM 6000TL-HU uses the other meaning: 114 holds the
inverter's 60 s start delay and 115 holds 0. AC Charge Energy Total therefore decoded as
393,216 kWh, against a battery charge total of 1.2 kWh, on a system configured never to
charge from the grid.

The reporter's own registers drive a real poll of the shared SPH/SPM HU profile. Other units
on that profile, where 112-115 may well be genuine, keep their reading, because a genuine
counter can never exceed the battery's own charge.
"""
from __future__ import annotations

import importlib

_gm = importlib.import_module("growatt_under_test.growatt_modbus")

MAP = "SPH_8000_10000_HU"

# Reporter's input registers (#463): 112-117 all 0 except 114 = 60; battery charge today
# 1057 = 1 (0.1 kWh) and total 1059 = 12 (1.2 kWh).
BASE = {112: 0, 113: 0, 114: 60, 115: 0, 116: 0, 117: 0, 1057: 1, 1059: 12}


def _poll(inputs: dict, polls: int = 4):
    """Several polls of one client, returning the last.

    114/115 = 60/0 also matches the word-corruption guard's pattern, which withholds it -
    but publishes a value whose high word holds steady for three polls (#446). A start
    delay never changes, so from the third poll on it reached the dashboard as 393,216 kWh.
    The state that matters is the steady one.
    """
    client = _gm.GrowattModbus(connection_type="tcp", host="10.0.0.1", port=502,
                               slave_id=1, register_map=MAP)

    def read_input_registers(start, count, log_errors=True):
        return [inputs.get(a, 0) for a in range(start, start + count)]

    client.read_input_registers = read_input_registers
    client.read_holding_registers = lambda start, count: [0] * count
    data = None
    for _ in range(polls):
        data = client.read_all_data()
    return data


def test_a_start_delay_read_as_ac_charge_is_withheld():
    data = _poll(BASE)
    assert round(data.charge_energy_total, 1) == 1.2
    assert "ac_charge_energy_total" in data.unread_fields, (
        "393,216 kWh of grid charging published against 1.2 kWh of battery charge"
    )


def test_a_genuine_ac_charge_counter_is_kept():
    """SPH 3000-6000 (#390) read 114 = 1, 115 = 5462: 7,099.8 kWh. Against a battery that
    has charged more than that in total, it stays."""
    data = _poll({**BASE, 114: 1, 115: 5462, 1058: 1, 1059: 30000})  # battery 9,553.6 kWh
    assert "ac_charge_energy_total" not in data.unread_fields
    assert round(data.ac_charge_energy_total, 1) == 7099.8


def test_conversion_loss_headroom_does_not_trip_it():
    """AC-side grid energy runs a little ahead of battery-side charge by conversion loss."""
    data = _poll({**BASE, 114: 0, 115: 130, 1059: 120})  # 13.0 kWh AC vs 12.0 kWh battery
    assert "ac_charge_energy_total" not in data.unread_fields


def test_nothing_is_judged_without_a_battery_figure():
    data = _poll({**BASE, 1057: 0, 1059: 0})
    assert "ac_charge_energy_total" not in data.unread_fields
