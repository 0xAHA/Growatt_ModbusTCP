"""Battery temperature on firmware that reports whole degrees (#397).

V1.39 specifies register 1040 as 0.1 C and most hardware follows it. An SPH3600 reports
whole degrees, so the documented scale turns 25 C into 2.5 C. Confirmed on that unit
against an independent BMS temperature register reading the same 25.

The cases are ambiguous from one reading - raw 25 is 25 C on one firmware and 2.5 C on the
other - so the correction is deliberately narrow, and the cold-weather false positive is
what these tests mostly guard.
"""
import importlib
import sys

import pytest

sys.path.insert(0, "tests")

_gm = importlib.import_module("growatt_under_test.growatt_modbus")

REG = 1040


def _client():
    return _gm.GrowattModbus(connection_type="tcp", host="10.0.0.1", port=502,
                             register_map="SPH_3000_6000")


def _resolve(client, raw):
    """Feed a raw register value through the scale the profile declares."""
    scale = client.register_map['input_registers'][REG]['scale']
    return client._resolve_battery_temp_scale(REG, raw * scale)


def test_the_profile_still_declares_the_documented_scale():
    """The fix must not be a scale change - that would break every compliant inverter."""
    assert _client().register_map['input_registers'][REG]['scale'] == 0.1


def test_the_reporters_reading_is_corrected():
    """SPH3600: raw 25 is 25 C, not 2.5 C. Confirmed against a second register and a
    thermal camera."""
    assert _resolve(_client(), 25) == 25.0


def test_a_spec_compliant_reading_is_left_alone():
    """raw 240 is 24.0 C and must stay that way."""
    assert _resolve(_client(), 240) == pytest.approx(24.0)


@pytest.mark.parametrize("raw,expected", [
    (50, 5.0),    # 5.0 C - the case the "three digits" rule would have called 50 C
    (99, 9.9),    # just below the proof threshold
    (60, 6.0),
    (46, 4.6),    # just outside the correction window
])
def test_cold_weather_on_a_compliant_inverter_is_not_misread(raw, expected):
    """The failure mode of every simpler rule. A battery at 5.0 C sends raw 50; reporting
    that as 50 C is wrong in exactly the conditions where the sensor matters."""
    assert _resolve(_client(), raw) == pytest.approx(expected)


def test_tenths_proof_latches_and_survives_a_later_cold_reading():
    """Once the device has proven itself compliant, a cold morning later in the same
    session must not re-trigger the correction."""
    client = _client()
    assert _resolve(client, 240) == pytest.approx(24.0)   # proof seen
    assert client._battery_temp_scale_confirmed
    assert _resolve(client, 25) == pytest.approx(2.5)     # would otherwise be corrected


def test_a_whole_degree_device_stays_corrected_across_readings():
    client = _client()
    assert _resolve(client, 25) == 25.0
    assert _resolve(client, 31) == 31.0
    assert not client._battery_temp_scale_confirmed


def test_zero_and_none_are_passed_through():
    client = _client()
    assert _resolve(client, 0) == 0.0
    assert client._resolve_battery_temp_scale(REG, None) is None


def test_a_register_with_no_scale_is_untouched():
    """Nothing to undo when the profile already declares whole degrees.

    The register map is shared across every client and every test, so this works on a
    copy. Mutating it in place added a register to SPH_3000_6000 for the rest of the
    session and broke the profile-integrity checks.
    """
    import copy

    client = _client()
    client.register_map = copy.deepcopy(client.register_map)
    client.register_map['input_registers'][9999] = {'name': 'battery_temp', 'scale': 1}
    assert client._resolve_battery_temp_scale(9999, 3.0) == 3.0
