"""AC charge/discharge energy on storage models (#390).

Protocol V1.39 gives input registers 112-115 two meanings, selected by device class:

  | Reg | MAX-class string inverter | Storage Power (SPH, SPA) |
  |-----|---------------------------|--------------------------|
  | 112 | Warn Maincode             | EACharge_Today_H         |
  | 113 | real Power Percent        | EACharge_Today_L         |
  | 114 | inv start delay time      | EACharge_Total_H         |
  | 115 | bINVAllFaultCode          | EACharge_Total_L         |

The SPH profiles used to read **both** interpretations at once — 112 as `warning_code` and
115 alone as `ac_charge_energy_total` — which cannot both be right on one device. Reading
115 without its high word also capped the lifetime total at 6553.5 kWh.

A reporter's scan read 114=1, 115=5462, i.e. (1<<16)|5462 = 70998 → 7099.8 kWh, where 115
alone said 546.2. His entity meanwhile showed 13820.7, which is registers 1058/1059 —
battery charge total — copied over the top by the decode path.

And there is no AC-*discharge* counter anywhere in V1.39. It exists only in the off-grid
protocol, so it belongs to SPF and SPE alone.
"""
from __future__ import annotations

import importlib

import pytest

_const = importlib.import_module("growatt_under_test.const")
_dp = importlib.import_module("growatt_under_test.device_profiles")

REGISTER_MAPS = _const.REGISTER_MAPS

# Every profile in this file's scope: SPH is unambiguously a "Storage Power" model.
SPH_MAPS = [k for k in REGISTER_MAPS if k.startswith("SPH_")]

# Deliberately untouched. The MAX-class ones legitimately read warn/fault codes there, and
# for the XH hybrids there is no evidence either way — guessing is how wrong-but-plausible
# values get shipped.
NOT_IN_SCOPE = ("MIN_", "MID_", "MOD_", "MIC_", "TL3_S", "TL_XH")


def _names(map_key):
    regs = REGISTER_MAPS[map_key]["input_registers"]
    return {a: regs[a]["name"] for a in (112, 113, 114, 115) if a in regs}


def test_every_sph_profile_is_in_scope():
    """Guards the parametrisation itself — an empty list would make this file vacuous."""
    assert len(SPH_MAPS) >= 6, f"expected the SPH family, found {SPH_MAPS}"


@pytest.mark.parametrize("map_key", SPH_MAPS)
def test_sph_reads_112_to_115_as_energy(map_key):
    assert _names(map_key) == {
        112: "ac_charge_energy_today_high",
        113: "ac_charge_energy_today_low",
        114: "ac_charge_energy_total_high",
        115: "ac_charge_energy_total_low",
    }, f"{map_key} does not read 112-115 under the Storage Power interpretation"


@pytest.mark.parametrize("map_key", SPH_MAPS)
def test_sph_no_longer_reads_a_warning_code_from_an_energy_register(map_key):
    """The specific contradiction: one block, two interpretations."""
    assert "warning_code" not in _names(map_key).values()


@pytest.mark.parametrize("map_key", SPH_MAPS)
def test_the_total_is_a_pair_not_a_lone_low_word(map_key):
    """115 alone at scale 0.1 wraps above 6553.5 kWh. The reporter was at 7099.8."""
    regs = REGISTER_MAPS[map_key]["input_registers"]
    assert regs[114]["pair"] == 115
    assert regs[115]["pair"] == 114
    assert regs[115]["combined_scale"] == 0.1
    assert regs[115]["combined_unit"] == "kWh"
    assert "scale" not in regs[115] or regs[115]["scale"] == 1, (
        "the low word still carries a 0.1 scale of its own, which would be applied "
        "before combining"
    )


def test_the_reporters_values_decode_to_the_portal_figure():
    """Arithmetic check against the real scan: 114=1, 115=5462."""
    high, low = 1, 5462
    assert ((high << 16) | low) * 0.1 == pytest.approx(7099.8)
    # ...and what the old mapping would have reported instead.
    assert low * 0.1 == pytest.approx(546.2)


@pytest.mark.parametrize("prefix", NOT_IN_SCOPE)
def test_out_of_scope_families_are_untouched(prefix):
    """These were not part of the change and must not have been swept up by it."""
    affected = [
        k for k in REGISTER_MAPS
        if k.startswith(prefix)
        and REGISTER_MAPS[k]["input_registers"].get(112, {}).get("name")
        == "ac_charge_energy_today_high"
    ]
    assert not affected, (
        f"{prefix}* profiles were changed to the Storage Power reading without evidence "
        f"that they use it: {affected}"
    )


# --------------------------------------------------------------------------
# ac_discharge_energy_total — off-grid only
# --------------------------------------------------------------------------

def _profile_keys():
    keys = set()
    for value in _dp.PROFILE_DISPLAY_NAMES.values():
        if isinstance(value, dict):
            keys.update(v for v in value.values() if isinstance(v, str))
        else:
            keys.add(value)
    return sorted(keys)


def test_no_profile_claims_ac_discharge_total_without_a_register():
    """It sat in the shared BATTERY_SENSORS group, so 21 grid-tied profiles created the
    sensor with nothing to populate it. It read 0.0, and the coordinator's lifetime-total
    retention latched one garbage frame and restored it forever — 21,069,824 kWh on a 12 kWh
    battery, unclearable."""
    offenders = []
    for key in _profile_keys():
        profile = _dp.get_profile(key)
        regs = REGISTER_MAPS.get(profile.get("register_map", ""), {}).get(
            "input_registers", {}
        )
        has_register = any(
            r.get("name") == "ac_discharge_energy_total_low" for r in regs.values()
        )
        if "ac_discharge_energy_total" in profile.get("sensors", ()) and not has_register:
            offenders.append(key)

    assert not offenders, (
        "these profiles expose AC Discharge Energy Total with no register behind it: "
        f"{offenders}"
    )


def test_the_off_grid_profiles_that_do_have_it_keep_it():
    """The other half — removing it from the shared group must not strip SPF and SPE, which
    genuinely map registers 66/67."""
    for key in _profile_keys():
        profile = _dp.get_profile(key)
        regs = REGISTER_MAPS.get(profile.get("register_map", ""), {}).get(
            "input_registers", {}
        )
        if any(r.get("name") == "ac_discharge_energy_total_low" for r in regs.values()):
            assert "ac_discharge_energy_total" in profile.get("sensors", ()), (
                f"{key} maps the register but no longer exposes the sensor"
            )
