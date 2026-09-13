"""Battery temperature is VPP register 31223, not 31222 (#440).

An SPH 5000TL BL-UP reported **272.1 °C**. The VPP specification says why:

    31221 | Reserved | RO | UINT32 | AH | 2 | Reserved for Battery remaining capacity (RM)
    31223 | Battery environmental temperature | RO | INT16 | 0.1C | 1 | [-400,1250]

31221 occupies **two** registers, so 31222 is its low word - remaining capacity in Ah, not
a temperature. The reporter's scan confirms it from the other side: 31222 read `2727`, and
so did input register 1091, which V1.39 documents as `BMS_GaugeRM`. The same quantity in two
register spaces, published as degrees.

The project had already found this once. `tl_xh.py` carries the note in full - *"Spec puts
battery temperature at 31223, not 31222 - 31222 is the low word of the reserved UINT32 at
31221"* - and MID, MOD and WIT were corrected to 31223. The SPH family kept the old address,
which is how a fixed bug stayed shipped for the profiles nobody re-checked.

This file holds the spec address across every profile that resolves the entity, so the
correction cannot be half-applied again.
"""
from __future__ import annotations

import importlib

import pytest

_const = importlib.import_module("growatt_under_test.const")

# The reporter's readings, one scan.
HIS_31222 = 2727      # == input 1091, BMS_GaugeRM
HIS_1091 = 2727


def _maps() -> dict:
    return _const.REGISTER_MAPS


def test_no_profile_resolves_the_entity_from_31222():
    """THE regression, stated as narrowly as the evidence supports.

    The property is that nothing *resolves the battery temperature entity* from 31222 -
    not that no profile may mention the address. Three deliberate uses exist and must
    survive this:

      * **MID** reads 31222/31223 as a 32-bit pair, with 31222 as the high word. On that
        hardware it was measured as `0/415 -> 41.5 C`, which is the right answer by a
        different route.
      * **WIT** maps both under `_alt` names because the firmware genuinely varies - one
        build answers temperature at 31222, another at 31223, both recorded in `wit.py`.
      * **TL-XH** is left alone deliberately: `tl_xh.py` notes that 31223 reads 0 on MIN
        TL-XH and those profiles use 3176 instead, so moving them would remove a working
        sensor on the strength of a spec line and no device report.

    An earlier version of this test asserted that no profile could name 31222 as anything
    temperature-ish, and it failed all three - a rule broader than its evidence, which is
    how a correct mapping gets "fixed" into a wrong one.
    """
    # Known to have the same defect on spec grounds, and deliberately not moved yet.
    #
    # `tl_xh.py` records that 31223 reads 0 on MIN TL-XH, which is why those profiles use
    # 3176 instead. Without a scan from a TL-XH owner I cannot tell whether 31223 carries
    # a real temperature on these two or whether moving them would swap a visibly absurd
    # value for a plausible-looking 0.0 C - which is the worse of the two failures.
    #
    # This list must shrink, not grow. If you have a TL-XH scan, check 31222 and 31223 and
    # remove the entry rather than leaving it here.
    AWAITING_A_DEVICE_REPORT = {
        "TL_XH_3000_10000_V201",
        "TL_XH_US_3000_10000_V201",
    }

    offenders = {
        name
        for name, register_map in _maps().items()
        if register_map.get("input_registers", {}).get(31222, {}).get("maps_to")
        == "battery_temp"
    }

    assert offenders <= AWAITING_A_DEVICE_REPORT, (
        "31222 is the low word of the reserved UINT32 at 31221 (remaining capacity, Ah). "
        "These profiles newly publish it as the battery temperature: "
        f"{sorted(offenders - AWAITING_A_DEVICE_REPORT)}"
    )
    assert offenders == AWAITING_A_DEVICE_REPORT, (
        f"{sorted(AWAITING_A_DEVICE_REPORT - offenders)} no longer resolves temperature "
        f"from 31222 - good, now remove it from AWAITING_A_DEVICE_REPORT above"
    )


@pytest.mark.parametrize("map_name", [
    "SPH_3000_6000_V201",
    "SPH_TL3_3000_10000_V201",
])
def test_the_sph_family_resolves_temperature_from_31223(map_name):
    """The reporter's own map, and its three-phase sibling which carried the same error."""
    info = _maps()[map_name]["input_registers"].get(31223)

    assert info is not None, f"{map_name} no longer maps 31223 at all"
    assert info.get("maps_to") == "battery_temp", (
        f"{map_name} maps 31223 but does not resolve the battery temperature entity from it"
    )
    assert info.get("scale") == 0.1, "the VPP spec gives 31223 as INT16 in 0.1 C"
    assert info.get("signed") is True, "temperatures below zero would wrap to ~6500 C"


def test_any_profile_mapping_31223_uses_the_documented_scale():
    """MID, MOD and WIT already used 31223 before this. They must agree on the units."""
    for name, register_map in _maps().items():
        info = register_map.get("input_registers", {}).get(31223)
        if not info or "temp" not in str(info.get("name", "")):
            continue
        assert info.get("scale") == 0.1, (
            f"{name}: 31223 is INT16 in 0.1 C per the VPP spec, found scale "
            f"{info.get('scale')}"
        )


def test_the_reporters_value_is_capacity_not_degrees():
    """States the evidence rather than trusting the spec alone. His 31222 and his 1091 -
    which V1.39 documents as BMS_GaugeRM - read the same number in the same scan. A
    temperature register and a gauge register do not agree by chance."""
    assert HIS_31222 == HIS_1091

    as_degrees = HIS_31222 * 0.1
    assert as_degrees > 100, (
        "the reported value was 272.1 C, which is what made this visible at all - a "
        "plausible-looking wrong number would still be shipped"
    )


def test_31222_is_still_mapped_so_the_range_is_not_silently_dropped():
    """Kept under its real name rather than deleted: the register is read as part of the
    block either way, and naming it records what it is for the next person."""
    for map_name in ("SPH_3000_6000_V201", "SPH_TL3_3000_10000_V201"):
        info = _maps()[map_name]["input_registers"].get(31222)
        assert info is not None, f"{map_name} dropped 31222 entirely"
        assert "temp" not in str(info.get("name", ""))
        assert info.get("maps_to") is None
