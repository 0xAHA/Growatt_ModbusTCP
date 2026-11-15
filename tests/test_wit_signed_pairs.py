"""Two WIT input pairs that the profile read with the wrong width or sign.

**Battery current, 31215-31216 (#481).** The VPP spec defines it as INT32. The WIT profile
read 31215 alone, which is the high word: 0 while charging, 65535 while discharging, so it
published -0.1 A under a 27 A (#247) and a 35 A (#430) discharge. A WIT 15K scan (#481):

    31215 = 0, 31216 = 466   ->  46.6 A charging   (8035 read -37.0 A)
    31215 = 0, 31216 = 664   ->  66.4 A charging   (8035 read -64.9 A)

VPP counts charging as positive; the integration and 8035 count it negative, so the decode
must flip it, or the battery-current candidates point opposite ways and disagree for ever.

**Extra Power to Grid, 8102-8103 (#503).** Power from an AC-coupled inverter on the GEN
port. A WIT 15 HU read [65535, 39483] and [65535, 37592] while the external inverter
produced about 2.6 and 2.8 kW. Read unsigned, that is ~429 million W.
"""
from __future__ import annotations

import importlib

import pytest

_gm = importlib.import_module("growatt_under_test.growatt_modbus")
_profiles = importlib.import_module("growatt_under_test.profiles")

WIT_MAPS = ("WIT_4000_15000TL3", "WIT_29900_50000TL3_XHU")


def _client(profile, cache):
    client = _gm.GrowattModbus.__new__(_gm.GrowattModbus)
    client.register_map = _profiles.REGISTER_MAPS[profile]
    client._register_cache = dict(cache)
    client._pair_shape_suspect = {}
    client._pair_shape_warned = set()
    client._underflow_warned = set()
    client._battery_power_scale_override = None
    return client


@pytest.mark.parametrize("profile", WIT_MAPS)
@pytest.mark.parametrize("low,amps", [(466, -46.6), (664, -66.4)])
def test_battery_current_is_the_32bit_pair_with_charging_negative(profile, low, amps):
    client = _client(profile, {31215: 0, 31216: low})
    assert client._get_register_value(31216) == pytest.approx(amps)


@pytest.mark.parametrize("profile", WIT_MAPS)
def test_a_discharge_reads_positive_not_minus_a_tenth(profile):
    """The #247 / #430 shape: high word 65535. -27.4 A in VPP terms is a 27.4 A discharge."""
    client = _client(profile, {31215: 65535, 31216: 65536 - 274})
    assert client._get_register_value(31216) == pytest.approx(27.4)


@pytest.mark.parametrize("profile", WIT_MAPS)
def test_battery_current_lookup_finds_the_pair_and_agrees_with_8035(profile):
    """The pair has to be a battery-current candidate, and on the #481 reading it has to
    agree with 8035 - same sign, same order of size - or scale detection is blocked."""
    client = _client(profile, {31215: 0, 31216: 664})
    addrs = client._find_all_registers_by_name("battery_current")
    assert 31216 in addrs and 31215 not in addrs
    vpp = client._get_register_value(31216)
    assert _gm.GrowattModbus._candidates_agree([vpp, -64.9])


@pytest.mark.parametrize("profile", WIT_MAPS)
@pytest.mark.parametrize("high,low,watts", [(65535, 39483, 2605.3), (65535, 37592, 2794.4)])
def test_extra_power_to_grid_is_signed_and_production_positive(profile, high, low, watts):
    client = _client(profile, {8102: high, 8103: low})
    assert client._get_register_value(8103) == pytest.approx(watts)


@pytest.mark.parametrize("profile", WIT_MAPS)
def test_extra_power_to_grid_reads_zero_without_an_external_inverter(profile):
    client = _client(profile, {8102: 0, 8103: 0})
    assert client._get_register_value(8103) == 0
