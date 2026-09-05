"""SPH-HU must not publish register 1088 as battery current (#420).

V1.39 documents input 1088 as `BMS_BatteryCurr` for the storage block generally, and that
holds on the profiles where it has been measured. It does **not** hold on SPH 8000-10000
TL-HU.

Measured on an SPH-10000-US, firmware UL2.21. A direct scan read 1088 = 1400 while the
battery was doing 355 W at 53.0 V - 6.70 A - which no scale reconciles: 0.1 gives 140 A,
0.01 gives 14 A. In the same scan 1090 (`BMS_MaxCurr`) read 0 and 1089 read 334 = 33.4 C,
so the block is not shifted; 1088 is the documented address carrying something else.

A month of Recorder history settles what it carries. Over 53 samples it holds 140.0 exactly
22 times and 40.0 exactly 8 times, sits flat near 140 below 94% SOC, tapers through the
mid-90s, floors at 40 above 98%, and is **never negative** across a month in which the
battery certainly discharged. A measurement does not repeat to a tenth of an amp thirty
times in fifty-three samples; a setpoint does.

Reported and evidenced by @risco21-dot.
"""
from __future__ import annotations

import importlib
import sys

import pytest

sys.path.insert(0, "tests")

REGISTERS = importlib.import_module("growatt_under_test.profiles").REGISTER_MAPS
PROFILES = importlib.import_module("growatt_under_test.device_profiles").INVERTER_PROFILES

HU_MAP = "SPH_8000_10000_HU"
HU_PROFILE = "sph_8000_10000_hu"

# 1088 is real battery current here, confirmed against instruments.
MEASURED_PROFILES = [
    "SPH_3000_6000", "SPH_3000_6000_V201",          # clamp meter, #397
    "SPH_TL3_3000_10000", "SPH_TL3_3000_10000_V201",  # 5170 W discharge, #403
]


def test_hu_does_not_map_1088_as_battery_current():
    """THE regression. The name is what the coordinator resolves, so leaving it as
    battery_current is what published a charge limit as a measurement."""
    register = REGISTERS[HU_MAP]["input_registers"][1088]

    assert register["name"] != "battery_current", (
        "SPH-HU maps 1088 as battery current again; on this family it is a BMS charge "
        "current limit that tapers with state of charge"
    )
    assert register["name"] == "bms_charge_current_limit"


def test_the_sensor_is_removed_from_the_hu_set_not_just_the_register():
    """CLAUDE.md rule 6, and the trap this fix could easily have fallen into.

    `battery_current` is a GrowattData dataclass field, so it always exists with a 0.0
    default. Unmapping the register does not stop the sensor being created - the platform
    builds whatever the profile's sensor set lists - and it would publish a confident zero
    amps, which is worse than the wrong-but-obviously-odd value it replaced. The sensor set
    is the only hard filter.
    """
    assert "battery_current" not in PROFILES[HU_PROFILE]["sensors"], (
        "battery_current is still in the HU sensor set, so the entity is created and "
        "publishes the dataclass default as a real reading"
    )


def test_the_limit_keeps_the_scale_the_evidence_supports():
    """140.0 and 40.0 at 0.1 A, against a ~53 V pack, is a 7.4 kW envelope falling to
    2.1 kW - a sane charge limit for a 10 kW hybrid. At 0.01 it would be 14 A / 4 A, which
    is neither the observed plateau nor a plausible envelope."""
    register = REGISTERS[HU_MAP]["input_registers"][1088]

    assert register["scale"] == 0.1
    assert not register.get("signed"), (
        "the limit was never observed negative across a month of samples; marking it "
        "signed would invite a two's-complement reading of a value that has no sign"
    )


@pytest.mark.parametrize("profile", MEASURED_PROFILES)
def test_the_measured_profiles_are_untouched(profile):
    """Scope. The block is not wrong generally - only on HU. Two families have 1088
    confirmed against instruments and must keep it."""
    register = REGISTERS[profile]["input_registers"][1088]

    assert register["name"] == "battery_current"
    assert register["scale"] == 0.01


@pytest.mark.parametrize("profile", MEASURED_PROFILES)
def test_the_measured_profiles_still_publish_it(profile):
    """A withheld sensor on the wrong profile would be as bad as a wrong value."""
    key = profile.lower()
    if key not in PROFILES:
        pytest.skip(f"{profile} has no matching entry in INVERTER_PROFILES")
    assert "battery_current" in PROFILES[key]["sensors"]


def test_evidence_claims_name_the_model_they_came_from():
    """Rule 13's distinction, applied to register descriptions.

    Five profiles carried 'confirmed vs clamp meter, #397' when #397 was a single SPH3620 -
    a 3-6kW unit. The 7-10kW maps inherited the sentence along with the register, and a
    doc-derived guess thereby acquired the appearance of a measurement. That is exactly how
    the HU mapping came to look confirmed when it never was.
    """
    for profile in ("SPH_7000_10000", "SPH_7000_10000_V201"):
        desc = REGISTERS[profile]["input_registers"][1088].get("desc", "")
        assert "confirmed vs clamp meter, #397" not in desc, (
            f"{profile} claims a measurement taken on a different model"
        )
