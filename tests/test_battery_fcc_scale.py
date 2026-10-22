"""Battery full-charge capacity, VPP input 31219-31220, is 0.1 Ah (#482).

A MID 25KTL3-XH with two APX clusters of four 5 kWh modules: module rated capacity 31228 =
1040 (104.0 Ah), cluster FCC 4160, then 3120, 2080 and 1040 as modules went to sleep. At a
scale of 1 that is a 4160 Ah cluster built from 104 Ah modules.
"""
from __future__ import annotations

import importlib

import pytest

_const = importlib.import_module("growatt_under_test.const")

MAPS_WITH_FCC = [name for name, m in _const.REGISTER_MAPS.items()
                 if m.get("input_registers", {}).get(31220, {}).get("name") == "battery_fcc_low"]


def test_some_profile_maps_fcc():
    assert MAPS_WITH_FCC


@pytest.mark.parametrize("map_name", MAPS_WITH_FCC)
def test_fcc_is_tenths_of_an_amp_hour(map_name):
    low = _const.REGISTER_MAPS[map_name]["input_registers"][31220]
    assert low["combined_unit"] == "Ah"
    assert 4160 * low["combined_scale"] == pytest.approx(4 * 104.0)
