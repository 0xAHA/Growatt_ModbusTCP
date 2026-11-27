"""Every mapped input register is actually requested; SPA 2000-2124 decodes (#510).

The SPA profile mapped input 2000-2124 (status, AC power, current, energy, temperatures)
from v1.5.2, but `read_all_data` only reads fixed windows - 0-874, 875-999, 1000-1999,
3000-3999, 8000-8199, 31000-31999 - and none covered 2000. Those fields were unread on
every poll on every SPA, and nothing noticed: unread is a normal outcome for an optional
range. A SPA3000TL-BL scan then showed the range populated.

The first test is the general guard: poll every profile with a fake bus and check that
each mapped input address fell inside some request.

The rest use the #510 scan (SPA2, firmware RHAA081005, two discharge levels). The same
scan shows 1105/1113, which the profile had as AC voltage and frequency (#249), reading
256 and 3239 - BMS fields, per the protocol - so those are now a guarded fallback only.
"""
from __future__ import annotations

import importlib

import pytest

_gm = importlib.import_module("growatt_under_test.growatt_modbus")
_profiles = importlib.import_module("growatt_under_test.profiles")

SPA = "SPA_3000_6000_TL_BL"


def _poll(register_map: str, inputs: dict, failing: tuple = ()):
    client = _gm.GrowattModbus(connection_type="tcp", host="10.0.0.1", port=502,
                               slave_id=1, register_map=register_map)
    requested: set[int] = set()

    def read_input_registers(start, count, log_errors=True):
        requested.update(range(start, start + count))
        if any(start <= a < start + count for a in failing):
            return None
        return [inputs.get(a, 0) for a in range(start, start + count)]

    client.read_input_registers = read_input_registers
    client.read_holding_registers = lambda start, count, *a, **k: [0] * count
    return client.read_all_data(), requested


@pytest.mark.parametrize("register_map", sorted(_profiles.REGISTER_MAPS))
def test_every_mapped_input_register_is_requested(register_map):
    """THE #510 regression, for every profile: a mapping no window reads is decorative."""
    mapped = set(_profiles.REGISTER_MAPS[register_map].get("input_registers", {}))
    _, requested = _poll(register_map, {})
    missing = sorted(mapped - requested)
    assert not missing, f"{register_map}: mapped but never requested: {missing[:10]}"


# SPA2 (#510), raw words. 1100-1119 included because the fallback reads them.
SCAN_1 = {2000: 6, 2035: 0, 2036: 6340, 2037: 4990, 2038: 2408, 2039: 26,
          2053: 0, 2054: 43, 2055: 1, 2056: 19858,
          2093: 231, 2094: 203, 2095: 200, 1105: 256, 1113: 3239}
SCAN_2 = {**SCAN_1, 2036: 19929, 2037: 4991, 2038: 2419, 2039: 81, 2054: 44,
          2056: 19859, 2093: 234, 2094: 205}


@pytest.mark.parametrize("scan, power, volts, hz, amps", [
    (SCAN_1, 634.0, 240.8, 49.90, 2.6),
    (SCAN_2, 1992.9, 241.9, 49.91, 8.1),
])
def test_spa_ac_side_decodes_from_2000(scan, power, volts, hz, amps):
    data, _ = _poll(SPA, scan)
    assert data.ac_power == pytest.approx(power)
    assert data.ac_voltage == pytest.approx(volts)
    assert data.ac_frequency == pytest.approx(hz)
    assert data.ac_current == pytest.approx(amps)
    for field in ("ac_power", "ac_voltage", "ac_frequency", "ac_current"):
        assert field not in data.unread_fields


# SPA2 (#510), 2035-2039 discharging and then grid charging, read through Shine mode
# changes. The charging pair [65535, 62272] is the first sample with power flowing in.
DISCHARGING = {**SCAN_1, 2035: 0, 2036: 5311, 2037: 5004, 2038: 2432, 2039: 21}
CHARGING = {**SCAN_1, 2035: 65535, 2036: 62272, 2037: 5008, 2038: 2416, 2039: 13}


@pytest.mark.parametrize("scan, power, volts, hz, amps", [
    (DISCHARGING, 531.1, 243.2, 50.04, 2.1),
    (CHARGING, -326.4, 241.6, 50.08, 1.3),
])
def test_spa_ac_power_is_signed_32_bit(scan, power, volts, hz, amps):
    """Positive while the SPA supplies AC, negative while it charges from the grid - not
    the 429 MW an unsigned decode of 0xFFFF_F340 would give."""
    data, _ = _poll(SPA, scan)
    assert data.ac_power == pytest.approx(power)
    assert data.ac_voltage == pytest.approx(volts)
    assert data.ac_frequency == pytest.approx(hz)
    assert data.ac_current == pytest.approx(amps)


def test_spa_status_temperatures_and_energy_are_read():
    data, _ = _poll(SPA, SCAN_1)
    assert data.status == 6                      # Bat On-Grid while discharging
    assert data.inverter_temp == pytest.approx(23.1)
    assert data.ipm_temp == pytest.approx(20.3)
    assert data.boost_temp == pytest.approx(20.0)
    assert data.energy_today == pytest.approx(4.3)
    assert data.energy_total == pytest.approx(((1 << 16) | 19858) * 0.1)
    for field in ("inverter_temp", "ipm_temp", "boost_temp", "energy_today", "energy_total"):
        assert field not in data.unread_fields


def test_spa_bms_block_values_never_become_ac_voltage():
    """2000 range unread, 1105/1113 hold #510's BMS values: unknown, not 2.56 V / 32 Hz."""
    data, _ = _poll(SPA, SCAN_1, failing=(2038,))
    assert "ac_voltage" in data.unread_fields
    assert "ac_frequency" in data.unread_fields


def test_spa_fallback_keeps_249_readings_when_2000_does_not_answer():
    """#249's firmware read mains-like values at 1105/1113; its 2000 range is untested."""
    inputs = {1105: 21575, 1113: 4986}
    data, _ = _poll(SPA, inputs, failing=(2038,))
    assert data.ac_voltage == pytest.approx(215.75)
    assert data.ac_frequency == pytest.approx(49.86)
    assert "ac_voltage" not in data.unread_fields
