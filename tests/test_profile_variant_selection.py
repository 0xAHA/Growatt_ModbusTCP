"""Every profile dropdown entry must name exactly one register map (#385).

Families with two protocol variants shared a single entry - "SPH (3-6kW)" meant either
`sph_3000_6000` or `sph_3000_6000_v201`, decided by a flag stored on the config entry. Two
consequences, and the second is the one that hurt:

1. You could not see which variant you were running. On #377 a fix was shipped into the
   profile the reporter was *not* on, and neither of us could tell for two days - his own
   detection output said "no VPP support" while his entry ran the V2.01 map.
2. You could not change it. Re-selecting the same name re-resolved through the same flag,
   so a wrong flag was permanent short of deleting the config entry and losing history.
"""
from __future__ import annotations

import importlib

import pytest

_dp = importlib.import_module("growatt_under_test.device_profiles")

PROFILE_DISPLAY_NAMES = _dp.PROFILE_DISPLAY_NAMES
INVERTER_PROFILES = _dp.INVERTER_PROFILES
PAIRED = {n: i for n, i in PROFILE_DISPLAY_NAMES.items() if i["base"] != i["v201"]}


def test_there_are_still_paired_families_to_protect():
    """Guards the tests below: if the pairing ever disappears they would pass vacuously."""
    assert PAIRED, "no family has two variants any more - these tests no longer test anything"


def test_every_dropdown_entry_resolves_to_exactly_one_profile():
    """The core property. No entry may depend on a stored flag to know what it means."""
    for name, expected in _dp.get_available_profiles().items():
        assert _dp.resolve_profile_selection(name, supports_v201=True) == expected
        assert _dp.resolve_profile_selection(name, supports_v201=False) == expected, (
            f"{name!r} still resolves differently depending on the stored flag"
        )


@pytest.mark.parametrize("family", sorted(PAIRED))
def test_both_variants_are_reachable(family):
    """The half that makes a wrong flag correctable - each variant has its own entry."""
    offered = _dp.get_available_profiles()
    base, v201 = PAIRED[family]["base"], PAIRED[family]["v201"]
    assert base in offered.values(), f"{family}: the legacy variant cannot be selected"
    assert v201 in offered.values(), f"{family}: the V2.01 variant cannot be selected"


@pytest.mark.parametrize("profile_id", sorted(
    {i[k] for i in PROFILE_DISPLAY_NAMES.values() for k in ("base", "v201")}
))
def test_display_name_round_trips(profile_id):
    """The options form uses the display name as its default. If a profile's name does not
    resolve back to it, saving the form silently moves the user to a different map."""
    name = _dp.get_display_name_for_profile(profile_id)
    assert _dp.resolve_profile_selection(name, supports_v201=True) == profile_id
    assert _dp.resolve_profile_selection(name, supports_v201=False) == profile_id


@pytest.mark.parametrize("profile_id", sorted(
    {i[k] for i in PAIRED.values() for k in ("base", "v201")}
))
def test_a_paired_profile_names_its_variant(profile_id):
    """The visibility half: the name has to say which map it is."""
    name = _dp.get_display_name_for_profile(profile_id)
    assert name.endswith((_dp.LEGACY_SUFFIX, _dp.V201_SUFFIX)), (
        f"{profile_id} displays as {name!r}, which does not identify the variant"
    )


def test_single_variant_families_keep_their_plain_name():
    """Only the ten paired families gain a suffix. Suffixing SPF or WIT would be noise."""
    for name, info in PROFILE_DISPLAY_NAMES.items():
        if info["base"] == info["v201"]:
            assert name in _dp.get_available_profiles()


def test_plain_family_names_are_still_accepted():
    """Values stored before the suffixes existed must keep working, and the setup path
    still resolves through detection rather than a user's explicit choice."""
    assert _dp.resolve_profile_selection("SPH (3-6kW)", supports_v201=True) == "sph_3000_6000_v201"
    assert _dp.resolve_profile_selection("SPH (3-6kW)", supports_v201=False) == "sph_3000_6000"


def test_every_offered_profile_actually_exists():
    for name, pid in _dp.get_available_profiles().items():
        assert pid in INVERTER_PROFILES, f"{name!r} offers {pid!r}, which is not a profile"


def test_the_options_page_states_the_loaded_map():
    """A name on the dropdown is not enough on its own - the page should say what is
    loaded now, which is what a user pastes into an issue."""
    from pathlib import Path

    source = (Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
              / "config_flow.py").read_text(encoding="utf-8")
    assert "Currently loaded register map:" in source
