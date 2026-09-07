"""Remaining and full-charge capacity from the BMS fuel gauge (#403).

@Doprintityourself asked for these on an SPH-10000 TL3 BH-UP and read raw 4996 / 5250 from
input 1091 / 1092. They were mapped on `SPH_8000_10000_HU` only, unscaled and unitless, with
no sensor definition anywhere - so nothing surfaced them on any profile.

**Input, not holding.** Holding 1091 and 1092 in the very same profile are AC Charge Stop SOC
and AC Charge Enable. Reading the wrong space here would publish a percentage as amp-hours.

The scale is documented rather than measured. V1.39 names these `BMS_GaugeRM` and
`BMS_GaugeFCC` and defers units to the ESS Protocol, which documents 0x001A/0x001B in **10
mAh** - so 0.01 Ah, making his raws 49.96 Ah of 52.50 Ah. That suits a ~220 V ARK pack. It is
recorded as documented-not-confirmed because the same raws read as watt-hours would give
5.25 kWh, which is also a plausible battery, and only his nameplate separates the two.
"""
from __future__ import annotations

import importlib
import sys

import pytest

sys.path.insert(0, "tests")

PROFILES = importlib.import_module("growatt_under_test.profiles").REGISTER_MAPS
CONST = importlib.import_module("growatt_under_test.const")
GROUPS = importlib.import_module("growatt_under_test.device_profiles")

GAUGE_PROFILES = ["SPH_8000_10000_HU", "SPH_TL3_3000_10000", "SPH_TL3_3000_10000_V201"]


@pytest.mark.parametrize("profile", GAUGE_PROFILES)
def test_the_gauge_registers_are_mapped_as_input(profile):
    registers = PROFILES[profile]["input_registers"]

    assert registers[1091]["name"] == "bms_gauge_rm"
    assert registers[1092]["name"] == "bms_gauge_fcc"


@pytest.mark.parametrize("profile", GAUGE_PROFILES)
def test_the_documented_scale_is_used(profile):
    """10 mAh per the ESS Protocol. At scale 1 the reporter's 5250 would publish as 5250,
    which is not wrong in any obvious way and would simply have been believed."""
    registers = PROFILES[profile]["input_registers"]

    for address in (1091, 1092):
        assert registers[address]["scale"] == 0.01, (
            f"{profile} register {address} has scale {registers[address]['scale']}; the ESS "
            f"Protocol documents 10 mAh"
        )
        assert registers[address]["unit"] == "Ah"


@pytest.mark.parametrize("profile", GAUGE_PROFILES)
def test_the_gauge_never_leaks_into_the_holding_space(profile):
    """The overlap trap, live in the same file. Where holding 1091/1092 are mapped they are
    AC Charge Stop SOC and AC Charge Enable - a stop-SOC percentage published as remaining
    amp-hours is exactly the wrong-but-plausible value this protocol keeps producing.

    Asserted as "never the gauge" rather than "always the AC charge pair", because not every
    profile here maps that holding block at all.
    """
    holding = PROFILES[profile].get("holding_registers", {})

    for address in (1091, 1092):
        if address in holding:
            assert not holding[address]["name"].startswith("bms_gauge"), (
                f"{profile} maps the fuel gauge into the HOLDING space at {address}"
            )


@pytest.mark.parametrize("attr", ["bms_gauge_rm", "bms_gauge_fcc"])
def test_the_sensors_are_wired_up_end_to_end(attr):
    """All four places, because a register mapped and nothing else is what these were for
    months: present in the profile, absent from every list that creates an entity.

    sensor.py imports homeassistant.components, which this suite does not have, so the
    definitions are read from the source the way tests/test_sensor_conditions.py does.
    """
    from pathlib import Path

    source = (Path(GROUPS.__file__).parent / "sensor.py").read_text(encoding="utf-8")

    assert f'"{attr}": {{' in source, "no sensor definition"
    assert f'"attr": "{attr}"' in source, "the definition does not point at the attribute"
    assert attr in GROUPS.BATTERY_SENSORS, (
        "not in a sensor group, so no profile composes it and no entity is ever created"
    )
    assert attr in CONST.SENSOR_DEVICE_MAP[CONST.DEVICE_TYPE_BATTERY], (
        "not assigned to the battery device"
    )


@pytest.mark.parametrize("profile", GAUGE_PROFILES)
def test_every_profile_that_maps_them_also_creates_them(profile):
    """A register mapped but missing from the profile's sensor set produces nothing at all.
    The sensor set is the only hard filter (CLAUDE.md rule 6), and the register sitting in
    the map is exactly the state these two were already in.

    Sensor sets live on INVERTER_PROFILES, keyed by profile id, while register maps are
    keyed by map name - so the entries are matched through `register_map`.
    """
    entries = [
        (pid, entry) for pid, entry in GROUPS.INVERTER_PROFILES.items()
        if entry.get("register_map") == profile
    ]
    assert entries, f"no inverter profile uses register map {profile}"

    for pid, entry in entries:
        sensors = entry.get("sensors", set())
        assert "bms_gauge_rm" in sensors, (
            f"{pid} maps the gauge registers but lists no remaining-capacity sensor"
        )
        assert "bms_gauge_fcc" in sensors, (
            f"{pid} maps the gauge registers but lists no full-capacity sensor"
        )


def test_the_scale_is_confirmed_against_a_real_nameplate():
    """Rule 4 applied to the evidence rather than the code, and the check that settled it.

    The scale was documented (ESS Protocol, 10 mAh) but ambiguous in practice: raw 5250
    could be 52.50 Ah or 5.25 kWh, and both are plausible batteries. The reporter's pack
    decides it.

    4x Growatt ARK 2.5H-A2, in series. 2.56 kWh at 51.2 V is 50.0 Ah per module, and series
    adds volts rather than amp-hours - so the pack is 50.0 Ah at 204.8 V, which is the
    10.24 kWh he states.

    If this arithmetic stops holding, the mapping is wrong and this file should be revisited
    rather than quietly protecting it.
    """
    module_ah = 2.56 * 1000 / 51.2
    assert module_ah == pytest.approx(50.0)

    pack_ah = module_ah                      # four in SERIES: volts add, amp-hours do not
    pack_volts = 51.2 * 4
    assert pack_ah * pack_volts / 1000 == pytest.approx(10.24), (
        "the pack arithmetic no longer reproduces the stated nameplate"
    )

    full_ah = 5250 * 0.01
    assert full_ah == pytest.approx(52.50)
    assert 1.0 <= full_ah / pack_ah <= 1.15, (
        f"full charge capacity is {100 * full_ah / pack_ah:.0f}% of nameplate, which is not "
        f"what a healthy gauge reports"
    )

    # The reading this was checked against, kept so the refutation does not get lost.
    full_as_watt_hours_kwh = 5250 / 1000
    assert full_as_watt_hours_kwh / 10.24 < 0.6, (
        "the watt-hour reading is no longer clearly refuted by the nameplate"
    )


def test_remaining_over_full_is_a_plausible_state_of_charge():
    """The cross-check that works whatever the unit: the ratio is the gauge's own SOC."""
    remaining, full = 4996 * 0.01, 5250 * 0.01

    assert remaining <= full, "remaining capacity exceeds full charge capacity"
    assert 100 * remaining / full == pytest.approx(95.2, abs=0.1)
