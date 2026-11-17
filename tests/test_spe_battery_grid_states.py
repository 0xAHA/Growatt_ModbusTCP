"""SPE states 29 and 30: the battery is discharging, whatever sign the register carries.

An SPE 8000 ES spends most of the day in two states the off-grid table did not know:

    29  battery and grid supporting loads
    30  PV, battery and grid supporting loads

Both were rendered as "Unknown (29)" / "Unknown (30)". Worse, on this unit the battery power
register arrives with the opposite sign to the one the SPE profile assumes, and the sign
check only knew state 2 as a discharging state. So every watt the battery delivered in
states 29 and 30 was published as Battery Charge Power, Battery Discharge Power stayed at 0,
and a Riemann sum on charge power recorded 447 kWh into the battery against 138 kWh out of
it over sixteen days.

Field data from that unit, read against Growatt's portal for the same period:

    state                                  portal                published before
    Grid Charging+Grid Bypass (10)         pBat -1020 W          -1017 W, corrected to charge
    PV&Battery&Grid Supporting Loads (30)  discharging 483 W     +404 W charge, discharge 0
    states 30 then 29, one evening         SOC 58 % -> 14 %      +586 / +1853 / +2201 W charge

The status is the reliable signal, as it already is for states 2 and 5-10, so the fix is to
teach the existing check these two states rather than to flip the profile's scale - which
would break the SPE 12000 the profile was verified against.
"""
from __future__ import annotations

import importlib
from types import SimpleNamespace

import pytest

_const = importlib.import_module("growatt_under_test.const")
_gm = importlib.import_module("growatt_under_test.growatt_modbus")

BATTERY_GRID_STATES = (29, 30)


def _corrected(status: int, battery_power: float) -> float:
    """The shipped check. It reads nothing from the client, so no client is needed."""
    data = SimpleNamespace(status=status, pv1_power=0.0, pv2_power=0.0, ac_power=1500.0)
    return _gm.GrowattModbus._validate_spf_battery_power_sign(None, battery_power, data)


@pytest.mark.parametrize("status", BATTERY_GRID_STATES)
def test_a_positive_reading_is_published_as_discharge(status):
    """THE regression: +1853 W while the state of charge fell was the battery feeding the house."""
    assert _corrected(status, 1853.0) == -1853.0


@pytest.mark.parametrize("status", BATTERY_GRID_STATES)
def test_a_unit_with_the_expected_sign_is_left_alone(status):
    """An SPE whose register already reads negative on discharge must not be flipped."""
    assert _corrected(status, -1853.0) == -1853.0


@pytest.mark.parametrize("status", BATTERY_GRID_STATES)
def test_readings_inside_the_dead_band_are_not_touched(status):
    assert _corrected(status, 6.0) == 6.0


def test_the_charging_states_still_correct_the_other_way():
    """Night grid charging on the same unit: state 10, register negative, battery filling."""
    assert _corrected(10, -1017.0) == 1017.0


@pytest.mark.parametrize("status", BATTERY_GRID_STATES)
def test_the_states_have_a_name(status):
    assert status in _const.SPF_STATUS_CODES
    assert "Unknown" not in _const.SPF_STATUS_CODES[status]["name"]


@pytest.mark.parametrize("status", BATTERY_GRID_STATES)
def test_the_grid_is_reported_connected_without_consulting_the_voltage(status):
    assert _const.offgrid_grid_connection_status(status, 0.0, True) == "On-grid"


@pytest.mark.parametrize("status", BATTERY_GRID_STATES)
def test_routine_29_30_correction_is_not_a_warning(status, caplog):
    """The unit sits in 29/30 most of the day: at warning, every poll lands in HA's error log."""
    import logging
    caplog.set_level(logging.DEBUG)
    _corrected(status, 1853.0)
    records = [r for r in caplog.records if "SPF sign correction" in r.getMessage()]
    assert records, "the correction should still be logged"
    assert all(r.levelno == logging.DEBUG for r in records)


def test_state_2_correction_still_warns(caplog):
    """Plain Discharge with a positive reading is not routine, so it stays visible."""
    import logging
    caplog.set_level(logging.DEBUG)
    _corrected(2, 1853.0)
    records = [r for r in caplog.records if "SPF sign correction" in r.getMessage()]
    assert records and all(r.levelno == logging.WARNING for r in records)
