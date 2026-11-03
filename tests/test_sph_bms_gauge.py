"""SPH 3000-6000: BMS fuel gauge at input 1091-1092, 0.1 Ah (#486).

An SPH 5000TL BL-UP with 3 x 5 kWh 48 V packs read FCC 3000 and RM 2131. At 0.1 Ah that is
300 Ah - the 15 kWh nameplate at ~50 V - and 213.1 Ah. The ESS protocol's 10 mAh holds on
SPH-TL3's high-voltage ARK stacks (#403), and would make this one 1.5 kWh.
"""
from __future__ import annotations

import importlib

import pytest

_gm = importlib.import_module("growatt_under_test.growatt_modbus")
_const = importlib.import_module("growatt_under_test.const")


def _poll(map_name, inputs):
    client = _gm.GrowattModbus(connection_type="tcp", host="10.0.0.1", port=502,
                               slave_id=1, register_map=map_name)
    client.read_input_registers = (
        lambda start, count, log_errors=True: [inputs.get(a, 0) for a in range(start, start + count)])
    client.read_holding_registers = lambda start, count: [0] * count
    return client.read_all_data()


@pytest.mark.parametrize("map_name", ["SPH_3000_6000", "SPH_3000_6000_V201"])
def test_the_reporters_readings(map_name):
    data = _poll(map_name, {1091: 2131, 1092: 3000})
    assert round(data.bms_gauge_rm, 1) == 213.1
    assert round(data.bms_gauge_fcc, 1) == 300.0


def test_sph_tl3_keeps_its_confirmed_scale():
    holding = _const.REGISTER_MAPS["SPH_TL3_3000_10000_V201"]["input_registers"]
    assert holding[1092]["scale"] == 0.01
