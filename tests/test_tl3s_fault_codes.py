"""TL3-S fault and warning codes come from the live registers, not the fault history (#432).

The profile read Fault Code from input 105 and Warning Code from 112. In protocol V3.14
those sit inside the grid fault history at 90-114: five records of code, year|month,
day|hour, min|sec and value. A TL3-S therefore showed "Fault Code 30" and "Warning Code
1042" permanently. That is record 4's code (30 = "AC V Outrange", at 253.0 V) and record 5's
day|hour (0x0412), both from 2022.

V3.14 puts the live fault code at input 40 and the warning code at 64. The base block below
is the reporter's own scan, so the poll decodes exactly what that inverter returned.
"""
from __future__ import annotations

import importlib

_gm = importlib.import_module("growatt_under_test.growatt_modbus")

# Reporter's scan, base input range: live codes clear, history full of a 2022 over-voltage.
SCAN = {
    40: 0, 41: 433, 64: 0,
    90: 30, 91: 5641, 92: 1041, 93: 1044, 94: 2530,
    95: 30, 96: 5640, 97: 2066, 98: 2072, 99: 144,
    100: 30, 101: 5640, 102: 1808, 103: 2836, 104: 2530,
    105: 30, 106: 5640, 107: 1295, 108: 11058, 109: 2530,
    110: 30, 111: 5640, 112: 1042, 113: 1590, 114: 2530,
}


def _poll(registers: dict):
    client = _gm.GrowattModbus(connection_type="tcp", host="10.0.0.1", port=502,
                               slave_id=1, register_map="TL3_S_3000_15000")

    def read_input_registers(start, count, log_errors=True):
        return [registers.get(a, 0) for a in range(start, start + count)]

    client.read_input_registers = read_input_registers
    client.read_holding_registers = lambda start, count: [0] * count
    return client.read_all_data()


def test_a_clear_inverter_reports_no_fault_and_no_warning():
    data = _poll(SCAN)
    assert data.fault_code == 0, "fault code is being read from the fault history"
    assert data.warning_code == 0, "warning code is a fault-record timestamp"


def test_a_live_fault_is_reported():
    data = _poll({**SCAN, 40: 30, 64: 4})
    assert data.fault_code == 30
    assert data.warning_code == 4
