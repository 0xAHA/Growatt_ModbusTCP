"""MIN TL-XH2 battery power stays at its confirmed 0.1 W (#488).

A MIN 4200TL-XH2 showed Battery Power -14,520 W while the Growatt portal showed 1,466 W of
discharge. Its register read 0xFFFF:0xC676 = -14730, i.e. -1473.0 W at the documented
0.1 W - the portal's figure. The x10 came from the runtime V x I scale detector: this
unit's battery current register read -90.9 A at 397 V, the detector chose 1.0, and the
choice was persisted. On a profile whose scale is confirmed on hardware neither the
detector nor a stored scale may override it.
"""
from __future__ import annotations

import importlib

import pytest

_gm = importlib.import_module("growatt_under_test.growatt_modbus")

XH2 = "MIN_TL_XH2_3000_10000_V201"

# The reporter's scan, 3 Nov 21:37.
SCAN = {31200: 65535, 31201: 50806, 31214: 3971, 31215: 65535, 31216: 64623, 31217: 34,
        31000: 6, 31001: 3}


def _settled(client, polls=4):
    """The pair-shape guard holds back a new 0xFFFF-high reading until it repeats."""
    for _ in range(polls):
        data = client.read_all_data()
    return data


def _client(register_map, scan=SCAN):
    client = _gm.GrowattModbus(connection_type="tcp", host="10.0.0.1", port=502,
                               slave_id=1, register_map=register_map)
    client.read_input_registers = (
        lambda start, count, log_errors=True: [scan.get(a, 0) for a in range(start, start + count)])
    client.read_holding_registers = lambda start, count: [0] * count
    return client


def test_the_reporters_scan_reads_as_the_portal_does():
    data = _settled(_client(XH2))
    assert (data.discharge_power, data.charge_power) == (pytest.approx(1473.0), 0.0)


def test_a_stored_1_0_scale_is_ignored_on_xh2():
    client = _client(XH2)
    client.restore_battery_power_scale(1.0)
    data = _settled(client)
    assert (data.discharge_power, data.charge_power) == (pytest.approx(1473.0), 0.0)


def test_repeated_polls_never_latch_a_scale_on_xh2():
    client = _client(XH2)
    for _ in range(5):
        client.read_all_data()
    assert client.validated_battery_power_scale is None
    assert client._battery_power_scale_override is None


def test_wit_still_restores_its_detected_scale():
    """The detector exists for WIT firmware that disagrees with the spec (#75, #406)."""
    client = _client("WIT_4000_15000TL3")
    client.restore_battery_power_scale(1.0)
    assert client._battery_power_scale_override == 1.0


def test_a_misleading_current_cannot_latch_x10_on_xh2():
    """The latch itself. This unit's current register is unreliable; at an operating point
    where it reads ~37 A, V x I (~14.7 kW) matches the power register at 1.0 W, and the
    detector used to take three such polls as proof and switch to 1.0 - the reporter's x10."""
    misleading = {**SCAN, 31216: 65536 - 371}          # -37.1 A at 397.1 V
    client = _client(XH2, misleading)
    for _ in range(5):
        data = client.read_all_data()
    assert client.validated_battery_power_scale is None
    assert data.discharge_power == pytest.approx(1473.0)
