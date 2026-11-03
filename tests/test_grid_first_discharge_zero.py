"""MOD/MID-XH Grid First Discharge Power Rate (holding 3036) accepts 0 % (#487).

V1.39 prints 1-255 for 3036, but the Growatt app sets 0 and an owner with a second battery
needs it. Both the control and the profile carry the range, and the number entity takes its
minimum from it.
"""
from __future__ import annotations

import importlib

_const = importlib.import_module("growatt_under_test.const")


def test_the_control_allows_zero():
    assert _const.WRITABLE_REGISTERS["grid_first_discharge_power_rate"]["valid_range"] == (0, 100)


def test_the_profile_allows_zero():
    reg = _const.REGISTER_MAPS["MOD_6000_15000TL3_XH"]["holding_registers"][3036]
    assert reg["name"] == "grid_first_discharge_power_rate"
    assert reg["valid_range"] == (0, 100)
