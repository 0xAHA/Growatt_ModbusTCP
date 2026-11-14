"""MOD-X per-MPPT energy counters use input registers 59-66 (FC04)."""
from __future__ import annotations

import importlib

import pytest

from .test_register_decoding import _client

_profiles = importlib.import_module("growatt_under_test.profiles")
MOD_X = _profiles.get_profile("MOD_6000_15000TL3_X")
COUNTERS = (
    (59, 60, "pv1_energy_today"),
    (61, 62, "pv1_energy_total"),
    (63, 64, "pv2_energy_today"),
    (65, 66, "pv2_energy_total"),
)


@pytest.mark.parametrize("high_address,low_address,name", COUNTERS)
def test_mod_x_energy_counter_metadata(high_address, low_address, name):
    registers = MOD_X["input_registers"]
    high = registers[high_address]
    low = registers[low_address]
    assert high["name"] == f"{name}_high"
    assert low["name"] == f"{name}_low"
    assert high["pair"] == low_address
    assert low["pair"] == high_address
    assert high["scale"] == low["scale"] == 1
    assert "combined_scale" not in high
    assert low["combined_scale"] == 0.1
    assert low["combined_unit"] == "kWh"
    assert not high.get("signed") and not low.get("signed")


@pytest.mark.parametrize("high_address,low_address,name", COUNTERS)
@pytest.mark.parametrize("raw,expected", [(0, 0.0), (123, 12.3), (70000, 7000.0)])
def test_mod_x_energy_counter_decoding(high_address, low_address, name, raw, expected):
    client = _client(
        MOD_X["input_registers"],
        {high_address: raw >> 16, low_address: raw & 0xFFFF},
    )
    assert client._find_register_by_name(f"{name}_low") == low_address
    assert client._get_register_value(high_address) == pytest.approx(expected)
    assert client._get_register_value(low_address) == pytest.approx(expected)


@pytest.mark.parametrize("high_address,low_address,name", COUNTERS)
@pytest.mark.parametrize("missing_word", ["high", "low"])
def test_mod_x_incomplete_energy_counter_is_unread(
    high_address, low_address, name, missing_word
):
    cache = {high_address: 1, low_address: 4464}
    del cache[high_address if missing_word == "high" else low_address]
    client = _client(MOD_X["input_registers"], cache)
    assert client._get_register_value(high_address) is None
    assert client._get_register_value(low_address) is None
