"""SPF Bulk and Float Charge Voltage sit on the Battery device with the other charge settings.

They were placed on the Inverter device because no battery keyword matched
`bulk_charge_voltage` or `float_charge_voltage`. An SPF 6000 ES Plus owner looked for them
beside Max Charge Current and AC Charge Current on the Battery device, where every other
charging setting is, and concluded they did not exist (#468).
"""
from __future__ import annotations

import importlib

import pytest

_const = importlib.import_module("growatt_under_test.const")


@pytest.mark.parametrize("control", ["bulk_charge_voltage", "float_charge_voltage"])
def test_charge_voltages_are_battery_controls(control):
    assert _const.get_device_type_for_control(control) == _const.DEVICE_TYPE_BATTERY


def test_they_join_the_other_spf_charge_settings():
    for neighbour in ("max_charge_current", "ac_charge_current"):
        assert _const.get_device_type_for_control(neighbour) == _const.DEVICE_TYPE_BATTERY
