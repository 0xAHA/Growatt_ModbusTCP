"""SPH-TL3 AC Voltage RS/ST/TR get a real source on V2.01, and none on legacy (#447).

The read path fills ac_voltage_rs/st/tr from registers named line_voltage_rs/st/tr. Neither
SPH-TL3 profile had any, so all three sensors published their 0.0 default for ever. An
SPH 10000 TL3 BH-UP owner reported exactly that while the portal's meter showed 230 V per
phase.

His register scan answered where the values live. On the V2.01 map, VPP 31106-31108 read
3964 / 3971 / 3966 - the three line voltages, as the VPP input table documents them. The
V1.39 addresses for the same quantity, input 50-52, read 0.0 on his unit and on a second
owner's (#442), both on live grids, so they are not an alternative.

The same scan showed the V2.01 map's old entries at 31100-31103 were mapped against the
table: 31100/31101 read 0/55417 (5541.7 W of active power, not a voltage) and frequency sat
at 31105 (5001), not 31103. Those entries were never consulted - lookup walks the map in
order and the legacy 37/38/42/46 match first - which is pinned here so the correction
cannot quietly change what the phase voltage and frequency sensors publish.
"""
from __future__ import annotations

import importlib

import pytest

_gm = importlib.import_module("growatt_under_test.growatt_modbus")
_dp = importlib.import_module("growatt_under_test.device_profiles")

V201_MAP = "SPH_TL3_3000_10000_V201"
LEGACY_MAP = "SPH_TL3_3000_10000"
LINE_VOLTAGES = ("ac_voltage_rs", "ac_voltage_st", "ac_voltage_tr")

# His raw values, from the #447 register scan.
SCAN = {
    37: 5001,            # legacy grid frequency, 50.01 Hz
    38: 3959, 42: 3948, 46: 3966,
    50: 0, 51: 0, 52: 0,
    31100: 0, 31101: 55417,
    31102: 65535, 31103: 64731,
    31105: 5001,
    31106: 3964, 31107: 3971, 31108: 3966,
}


def _client(map_name: str):
    client = _gm.GrowattModbus(connection_type="tcp", host="10.0.0.1", port=502,
                               register_map=map_name)
    client._register_cache = dict(SCAN)
    return client


# ---------------------------------------------------------------------------
# V2.01: the three sensors now have somewhere to come from
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("line,address,expected", [
    ("rs", 31106, 396.4),
    ("st", 31107, 397.1),
    ("tr", 31108, 396.6),
])
def test_v201_line_voltages_decode_from_the_vpp_block(line, address, expected):
    """THE fix, through the same lookup and assignment read_all_data uses."""
    client = _client(V201_MAP)
    addr = client._find_register_by_name(f"line_voltage_{line}")
    assert addr == address, f"line_voltage_{line} resolves to {addr}, not {address}"

    data = _gm.GrowattData()
    client._set_from_register(data, f"ac_voltage_{line}", addr)
    assert f"ac_voltage_{line}" not in data.unread_fields
    assert getattr(data, f"ac_voltage_{line}") == pytest.approx(expected)


def test_v201_keeps_the_line_voltage_sensors():
    assert set(LINE_VOLTAGES) <= _dp.INVERTER_PROFILES["sph_tl3_3000_10000_v201"]["sensors"]


# ---------------------------------------------------------------------------
# Legacy: no source, so no sensors
# ---------------------------------------------------------------------------

def test_legacy_map_has_nothing_to_fill_them():
    client = _client(LEGACY_MAP)
    for line in ("rs", "st", "tr"):
        assert client._find_register_by_name(f"line_voltage_{line}") is None


def test_legacy_drops_the_line_voltage_sensors():
    """Otherwise they are created from THREE_PHASE_SENSORS and publish 0.0 V for ever."""
    sensors = _dp.INVERTER_PROFILES["sph_tl3_3000_10000"]["sensors"]
    assert not (set(LINE_VOLTAGES) & sensors)


def test_legacy_keeps_the_phase_voltages():
    """Only the line voltages had no source. The phase voltages are a separate question
    (see the note on registers 38-49) and must not be caught by this removal."""
    sensors = _dp.INVERTER_PROFILES["sph_tl3_3000_10000"]["sensors"]
    assert {"ac_voltage_r", "ac_voltage_s", "ac_voltage_t", "ac_frequency"} <= sensors


# ---------------------------------------------------------------------------
# The 31100-31103 correction changes nothing that is published
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("name,address", [
    ("ac_voltage_r", 38), ("ac_voltage_s", 42), ("ac_voltage_t", 46), ("ac_frequency", 37),
])
def test_v201_phase_voltage_and_frequency_still_come_from_the_legacy_block(name, address):
    assert _client(V201_MAP)._find_register_by_name(name) == address


def test_no_power_register_is_mapped_as_a_voltage_or_frequency():
    """31100-31103 are active and reactive power. A voltage or frequency fallback there
    would publish 5541.7 V or 647.31 Hz on this scan the moment it was consulted."""
    from growatt_under_test.profiles import get_profile
    inputs = get_profile(V201_MAP)["input_registers"]
    for address in (31100, 31101, 31102, 31103):
        reg = inputs.get(address)
        if reg is None:
            continue
        target = reg.get("maps_to") or reg["name"]
        assert "voltage" not in target and "frequency" not in target, (
            f"{address} is mapped to {target!r}, but the VPP table gives it as power"
        )


def test_frequency_fallback_is_at_the_documented_address():
    client = _client(V201_MAP)
    assert client._get_register_value(31105) == pytest.approx(50.01)
