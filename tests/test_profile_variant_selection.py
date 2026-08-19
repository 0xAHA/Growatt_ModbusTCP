"""The legacy/VPP variant must stay hidden, but never become unchangeable (#385).

Ten families exist as two register maps. Which one is used comes from a flag set by
auto-detection, and the profile dropdown deliberately shows a single plain name for both -
the distinction is an implementation detail and most users never need it.

The failure this guards against is what happened on #377: when the stored flag disagreed
with the hardware there was no way back. Re-selecting the same family name resolved through
the same flag that was already wrong, so the only escape was deleting the config entry and
losing entity IDs, automations and statistics history. A fix was shipped into the profile the
reporter was not running and neither of us could see why for two days.

So: hidden by default, overridable on demand.
"""
from __future__ import annotations

import importlib
import re
from pathlib import Path

import pytest

_dp = importlib.import_module("growatt_under_test.device_profiles")
_const = importlib.import_module("growatt_under_test.const")

CONFIG_FLOW = (Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
               / "config_flow.py").read_text(encoding="utf-8")

PROFILE_DISPLAY_NAMES = _dp.PROFILE_DISPLAY_NAMES
PAIRED = {n: i for n, i in PROFILE_DISPLAY_NAMES.items() if i["base"] != i["v201"]}


def test_there_are_paired_families_to_protect():
    """If the pairing ever disappears, the tests below would pass vacuously."""
    assert PAIRED, "no family has two variants any more"


def test_the_dropdown_does_not_expose_the_variant():
    """The design intent: a user picks SPH and never learns the word VPP. Suffixed entries
    solved the correctability problem by pushing protocol internals at everyone."""
    for name in _dp.get_available_profiles():
        assert "V2.01" not in name and "V1.39" not in name, (
            f"profile entry {name!r} exposes the protocol variant in the dropdown"
        )


def test_one_entry_per_family():
    """A family must not appear twice - that is the same exposure by another route."""
    offered = _dp.get_available_profiles()
    assert len(offered) == len(PROFILE_DISPLAY_NAMES)


@pytest.mark.parametrize("family", sorted(PAIRED))
def test_both_variants_remain_reachable_through_the_flag(family):
    """Hidden is fine; unreachable is not. Each variant must be selectable via the override."""
    base, v201 = PAIRED[family]["base"], PAIRED[family]["v201"]
    assert _dp.resolve_profile_selection(family, supports_v201=False) == base
    assert _dp.resolve_profile_selection(family, supports_v201=True) == v201


def test_the_three_variant_choices_exist():
    assert _const.PROTOCOL_VARIANT_AUTO == "auto"
    assert _const.PROTOCOL_VARIANT_LEGACY == "legacy"
    assert _const.PROTOCOL_VARIANT_V201 == "v201"


def test_the_override_is_offered_on_the_options_form():
    """It has to be on the options flow, not just at setup - the whole point is correcting
    an entry that already exists without deleting it."""
    start = CONFIG_FLOW.index("options_schema = vol.Schema({")
    end = CONFIG_FLOW.index("return self.async_show_form", start)
    assert '"protocol_variant"' in CONFIG_FLOW[start:end], (
        "the Protocol variant field is not part of the options form"
    )


def test_an_explicit_choice_overrides_the_stored_flag():
    """Without this the field would render and change nothing, which is the decorative
    failure this project has shipped before."""
    save = CONFIG_FLOW[:CONFIG_FLOW.index("options_schema = vol.Schema({")]
    assert "PROTOCOL_VARIANT_LEGACY" in save and "supports_v201 = False" in save
    assert "PROTOCOL_VARIANT_V201" in save and "supports_v201 = True" in save


def test_the_override_is_persisted():
    """It must survive a later save that leaves the field alone, otherwise the correction
    lasts exactly one reload."""
    assert 'new_data["vpp_protocol_confirmed"] = supports_v201' in CONFIG_FLOW


def test_auto_changes_nothing():
    """Anyone who ignores the field must see identical behaviour to before."""
    save = CONFIG_FLOW[:CONFIG_FLOW.index("options_schema = vol.Schema({")]
    m = re.search(r'variant = user_input\.get\("protocol_variant", (\w+)\)', save)
    assert m and m.group(1) == "PROTOCOL_VARIANT_AUTO", (
        "the variant field does not default to Auto"
    )
    assert 'if variant != PROTOCOL_VARIANT_AUTO' in save, (
        "Auto is not excluded from writing the flag, so it would overwrite detection"
    )


def test_every_offered_profile_exists():
    for name, pid in _dp.get_available_profiles().items():
        assert pid in _dp.INVERTER_PROFILES, f"{name!r} offers {pid!r}, which is not a profile"


def test_the_options_page_states_the_loaded_map():
    """Naming the resolved register map is what turns "it did not work" into a diagnosis."""
    assert "Currently loaded register map:" in CONFIG_FLOW
