"""Register decoding tests.

Every case here corresponds to a bug that reached users. The decoding path — scale,
signedness, 32-bit pairing, combined_scale — is where the integration converts raw
Modbus words into the numbers people see, and it has been the source of the most
user-visible failures.

Cases covered:
  * unsigned 32-bit pairing            (baseline)
  * SIGNED 32-bit pairing              v1.2.1 shipped AC power unsigned; a negative
                                       reading surfaced as 429,496,471 W  (#361)
  * high/low order independence        pairs are declared from both directions
  * combined_scale on the LOW word     the convention the profiles rely on
  * missing register -> None           must not decode as 0, which is what made a
                                       dead link look like a healthy inverter (#357)
"""
from __future__ import annotations

import importlib

import pytest

# conftest.py binds `growatt_under_test` to the component directory and stubs the
# unused homeassistant import; it runs before collection, so this resolves.
GrowattModbus = importlib.import_module("growatt_under_test.growatt_modbus").GrowattModbus


def _client(input_registers: dict, cache: dict) -> GrowattModbus:
    """Build a client with a synthetic register map and cache, no I/O."""
    client = GrowattModbus.__new__(GrowattModbus)  # bypass __init__ / no connection
    client.register_map = {"name": "TEST", "input_registers": input_registers}
    client._register_cache = dict(cache)
    return client


# --------------------------------------------------------------------------
# 32-bit pairing
# --------------------------------------------------------------------------

def test_unsigned_pair_combines_high_and_low():
    regs = {
        100: {"name": "power_high", "scale": 1, "pair": 101},
        101: {"name": "power_low", "scale": 1, "pair": 100,
              "combined_scale": 0.1, "combined_unit": "W"},
    }
    # (1 << 16) | 4464 = 70000 -> x0.1 = 7000.0 W
    client = _client(regs, {100: 1, 101: 4464})
    assert client._get_register_value(101) == pytest.approx(7000.0)


def test_pair_decodes_the_same_from_either_end():
    """A pair must decode identically whether addressed by its HIGH or LOW word."""
    regs = {
        100: {"name": "power_high", "scale": 1, "pair": 101},
        101: {"name": "power_low", "scale": 1, "pair": 100, "combined_scale": 0.1},
    }
    client = _client(regs, {100: 1, 101: 4464})
    assert client._get_register_value(100) == client._get_register_value(101)


# --------------------------------------------------------------------------
# Signedness — the #361 regression
# --------------------------------------------------------------------------

def test_signed_pair_decodes_negative_value():
    """Regression: MIN TL-XH2 AC power reported 429,496,471 W (Issue #361).

    A small negative active power (importing from grid) has 0xFFFF in the high word.
    Read unsigned it becomes ~4.29e9; scaled by 0.1 that is the number the user saw.
    """
    regs = {
        31100: {"name": "power_to_grid_high", "scale": 1, "pair": 31101},
        31101: {"name": "power_to_grid_low", "scale": 1, "pair": 31100,
                "combined_scale": 0.1, "signed": True},
    }
    # two's complement of -2586 in 32 bits -> high 0xFFFF, low 62950
    client = _client(regs, {31100: 0xFFFF, 31101: 62950})
    assert client._get_register_value(31101) == pytest.approx(-258.6)


def test_unsigned_pair_produces_the_reported_bad_value():
    """Documents the exact failure: same registers WITHOUT the signed flag.

    Guards against the flag being dropped again — this asserts the broken behaviour
    so the contrast with the test above is explicit.
    """
    regs = {
        31100: {"name": "power_to_grid_high", "scale": 1, "pair": 31101},
        31101: {"name": "power_to_grid_low", "scale": 1, "pair": 31100,
                "combined_scale": 0.1},  # no 'signed'
    }
    client = _client(regs, {31100: 0xFFFF, 31101: 62950})
    assert client._get_register_value(31101) == pytest.approx(429496471.0)


def test_signed_flag_on_either_register_of_the_pair_applies():
    """`signed` is honoured whether declared on the HIGH or the LOW word."""
    on_low = {
        200: {"name": "p_high", "scale": 1, "pair": 201},
        201: {"name": "p_low", "scale": 1, "pair": 200, "combined_scale": 0.1,
              "signed": True},
    }
    on_high = {
        200: {"name": "p_high", "scale": 1, "pair": 201, "signed": True},
        201: {"name": "p_low", "scale": 1, "pair": 200, "combined_scale": 0.1},
    }
    cache = {200: 0xFFFF, 201: 62950}
    assert _client(on_low, cache)._get_register_value(201) == pytest.approx(-258.6)
    assert _client(on_high, cache)._get_register_value(201) == pytest.approx(-258.6)


def test_signed_single_register_is_not_treated_as_negative_when_positive():
    regs = {300: {"name": "battery_current", "scale": 0.01, "signed": True}}
    assert _client(regs, {300: 1400})._get_register_value(300) == pytest.approx(14.0)


# --------------------------------------------------------------------------
# Missing data must NOT decode as zero — the #357 class of bug
# --------------------------------------------------------------------------

def test_register_absent_from_cache_returns_none_not_zero():
    """Regression guard for Issue #357.

    A register that was never read must decode to None. Returning 0.0 is what made a
    failed poll look like a healthy inverter reporting zeros, so no reconnect or
    backoff ever ran and entities stayed 'available' showing 0.
    """
    regs = {400: {"name": "pv1_voltage", "scale": 0.1}}
    client = _client(regs, {})  # empty cache — nothing was read
    assert client._get_register_value(400) is None


def test_register_not_in_profile_returns_none():
    client = _client({400: {"name": "pv1_voltage", "scale": 0.1}}, {999: 123})
    assert client._get_register_value(999) is None


def test_zero_is_a_real_value_and_distinct_from_missing():
    """A genuine zero reading must decode as 0.0, not None."""
    regs = {400: {"name": "pv1_voltage", "scale": 0.1}}
    assert _client(regs, {400: 0})._get_register_value(400) == 0.0


# --------------------------------------------------------------------------
# Scaling
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("raw", "scale", "expected"),
    [
        (2394, 0.1, 239.4),    # grid voltage
        (4996, 0.01, 49.96),   # grid frequency
        (95, 1, 95),           # battery SOC
        (4246, 0.1, 424.6),    # HV battery voltage
    ],
)
def test_single_register_scaling(raw, scale, expected):
    regs = {500: {"name": "value", "scale": scale}}
    assert _client(regs, {500: raw})._get_register_value(500) == pytest.approx(expected)
