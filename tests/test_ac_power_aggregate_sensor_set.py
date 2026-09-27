"""An aggregate AC Power entity exists exactly where its register map can support one (#427).

Two fixes were aimed at this sensor on a MID 25KTL3-XH and neither reached it, because the
entity was never created on that profile at all:

    35/36 signed             (#429, v2.0.1)   -> the decode
    phase-sum fallback       (#427, v2.0.2-b3) -> the value when 35/36 is not served
    sensor-set membership    <- what was actually missing

`ac_power` lived in BASIC_AC_SENSORS, and THREE_PHASE_SENSORS *replaces* that set rather than
extending it, so no three-phase profile built from it created the entity. The reporter had one
in his registry from an older version, which is why he could watch it sit unknown while the
data behind it was being computed correctly. Rule 6 in the long form: sensor-set membership is
the only hard filter, in both directions.

The membership cannot be decided by phase count, and that is the point of this file. Whether
an aggregate is meaningful depends on what `ac_power_low` resolves to on the profile's own map,
and across the three-phase maps it lands in three different places:

    MOD_6000_15000TL3_X / _XH    reg 36, a distinct total          -> sensor is correct
    WIT_*, TL3_S_*               a distinct total                  -> sensor is correct
    SPH_TL3_*                    reg 36 (Pac) since #447           -> sensor is correct
    MID_15000_25000TL3_X(_V201)  no total, no phase powers either  -> nothing to read or sum

SPH_TL3 used to alias reg 41 as the total, and was excluded here because that would have
published it as the whole system. #447 found 41 to be the three-phase apparent power and
mapped the documented real power, 35/36, confirmed on two units.

So the test derives the expectation from each map and asserts against it. A new three-phase
profile inherits the right answer, and an alias change on any map fails here rather than
shipping one phase as a whole-system reading.
"""
from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

_dp = importlib.import_module("growatt_under_test.device_profiles")
_const = importlib.import_module("growatt_under_test.const")

COMPONENT = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"

THREE_PHASE = {
    key: profile for key, profile in _dp.INVERTER_PROFILES.items()
    if profile.get("phases") == 3
}


def _resolve(register_map: str, name: str):
    """What `_find_register_by_name` would return: exact name, then alias, then maps_to."""
    rmap = _const.REGISTER_MAPS.get(register_map)
    if not rmap:
        return None
    for address, info in rmap["input_registers"].items():
        if info["name"] == name or info.get("alias") == name or info.get("maps_to") == name:
            return address
    return None


def _aggregate_is_supportable(register_map: str) -> bool:
    """True when the map offers a real total, or phases the total can be summed from."""
    total = _resolve(register_map, "ac_power_low")
    phase_r = _resolve(register_map, "ac_power_r_low")

    if total is not None and total != phase_r:
        return True                      # a genuine total register
    if total is not None and total == phase_r:
        return False                     # the alias trap: reg 41 is phase R, not the sum
    # No total. The phase-sum fallback needs phase power registers to sum.
    return all(_resolve(register_map, f"ac_power_{p}_low") is not None for p in "rst")


def test_the_reporters_profile_has_the_entity():
    """THE regression: MID 25KTL3-XH, the profile the two earlier fixes could not reach."""
    profile = _dp.INVERTER_PROFILES["mid_11000_30000tl3_xh_v201"]
    assert "ac_power" in profile["sensors"], (
        "AC Power is still not in this profile's sensor set, so the entity is never created "
        "and no decode fix can reach it - which is what made #427 look unfixed twice"
    )


# Supportable by the map but deliberately not offered. SPA-TL3 shares the SPH-TL3 map, and
# 35/36 has only been confirmed on SPH-TL3 hardware - an AC-coupled SPA answering 0 there
# would publish a plausible wrong number. Remove once an SPA-TL3 reading confirms it.
UNCONFIRMED_ON_THIS_HARDWARE = {"spa_tl3_4000_10000_v201"}


@pytest.mark.parametrize("key", sorted(THREE_PHASE))
def test_membership_matches_what_the_map_can_support(key):
    profile = THREE_PHASE[key]
    register_map = profile["register_map"]
    present = "ac_power" in profile["sensors"]
    supportable = _aggregate_is_supportable(register_map)
    if key in UNCONFIRMED_ON_THIS_HARDWARE:
        assert supportable and not present, f"{key}: re-check the exemption - it no longer applies"
        return

    assert present == supportable, (
        f"{key} ({register_map}): ac_power {'is' if present else 'is not'} in the sensor set "
        f"but the map {'can' if supportable else 'cannot'} support an aggregate. Either the "
        f"membership or the map's ac_power_low alias is wrong."
    )


def test_membership_stays_per_profile():
    """The guard that stops the obvious shortcut. Adding `ac_power` to THREE_PHASE_SENSORS
    would be one line and would give the entity to maps with nothing behind it (MID) and to
    SPA-TL3, where the total is unconfirmed."""
    assert "ac_power" not in _dp.THREE_PHASE_SENSORS, (
        "ac_power has been added to THREE_PHASE_SENSORS, which gives it to every three-phase "
        "profile regardless of what its map can support"
    )


def test_sph_tl3_now_reads_a_genuine_total_not_phase_r():
    """#447: the total is Pac (35/36), distinct from phase R (40/41) - which is what made
    the SPH-TL3 entity safe to offer."""
    for key, profile in THREE_PHASE.items():
        if not profile["register_map"].startswith("SPH_TL3"):
            continue
        total = _resolve(profile["register_map"], "ac_power_low")
        phase_r = _resolve(profile["register_map"], "ac_power_r_low")
        assert total == 36 and phase_r == 41, (
            f"{key}: ac_power_low resolves to {total}, phase R to {phase_r}"
        )


@pytest.mark.parametrize("key", sorted(THREE_PHASE))
def test_no_profile_claims_an_aggregate_it_cannot_fill(key):
    """A sensor in the set with neither a total nor phases to sum reports a confident 0.0 -
    the #384 defect, reached through the sensor set instead of the decode."""
    profile = THREE_PHASE[key]
    if "ac_power" not in profile["sensors"]:
        return
    register_map = profile["register_map"]
    total = _resolve(register_map, "ac_power_low")
    phases = [_resolve(register_map, f"ac_power_{p}_low") for p in "rst"]

    assert total is not None or all(p is not None for p in phases), (
        f"{key} ({register_map}) exposes AC Power with no total register and no complete set "
        f"of phase registers to sum, so it can only ever publish 0.0"
    )


def test_the_entity_plumbing_was_already_in_place():
    """Adding a key to a sensor set is only step 5 of 7. The other steps were already done
    for the single-phase profiles, so this records that rather than assuming it."""
    _sensor = (COMPONENT / "sensor.py").read_text(encoding="utf-8")
    assert '"ac_power": {' in _sensor, "no SENSOR_DEFINITIONS entry"

    assert any("ac_power" in keys for keys in _const.SENSOR_DEVICE_MAP.values()), (
        "ac_power is in no device's sensor set, so the entity would land on the wrong device"
    )

    for name in ("strings.json", "translations/en.json"):
        data = json.loads((COMPONENT / name).read_text(encoding="utf-8"))
        entry = data["entity"]["sensor"].get("ac_power")
        assert entry and entry.get("name"), (
            f"{name} has no name for ac_power - the entity would show the device name alone"
        )
