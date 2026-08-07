"""Options-flow schema consistency.

The `max_block_size` selector shipped in v1.2.0 declared as `vol.In({int: str})`.
Home Assistant's frontend submits select values as strings, so "25" never matched the
integer 25: validation failed, the option could never be saved, and the dropdown showed
nothing selected because the integer default matched no rendered choice.

It went unnoticed for four releases because the *read path* was wired correctly — the
option simply never reached it. Two users reported it as two different symptoms (#360
"nothing is selected", #367 "the option had zero effect").

Every other selector in the same form uses a plain list of strings, which is why they
work. These tests pin that convention.
"""
from __future__ import annotations

import importlib
import re
from pathlib import Path

import pytest

_const = importlib.import_module("growatt_under_test.const")

BLOCK_SIZE_OPTIONS = _const.BLOCK_SIZE_OPTIONS
resolve_block_size = _const.resolve_block_size

CONFIG_FLOW = Path(__file__).parent.parent / "custom_components" / "growatt_modbus" / "config_flow.py"


# --------------------------------------------------------------------------
# The regression itself
# --------------------------------------------------------------------------

def test_max_block_size_selector_does_not_use_integer_dict_keys():
    """Regression guard for #360 / #367.

    The selector shipped as `vol.In({0: "...", 25: "..."})` and could not be saved. Two
    mechanisms are plausible and I could not distinguish them without a running HA:

      1. integer dict keys not round-tripping through the frontend, or
      2. `default=0` being falsy, so the form rendered with nothing pre-selected and a
         Required field with no value refused to submit.

    The fix — a list of string labels with a truthy default — addresses both, so the
    exact mechanism doesn't change what the code should look like.

    Note this checks ONLY the block-size selector. `config_flow.py` also has an
    integer-keyed baudrate selector that has shipped for many releases and appears to
    work, which is what makes mechanism 1 doubtful. It is deliberately left alone.
    """
    source = CONFIG_FLOW.read_text(encoding="utf-8")
    match = re.search(r'"max_block_size".*?\)\s*,', source, re.DOTALL)
    assert match, "max_block_size selector not found in config_flow.py"
    assert not re.search(r"vol\.In\(\{\s*\d+\s*:", match.group(0)), (
        "max_block_size is declared with integer dict keys again — it could not be saved "
        "in v1.2.0-v1.3.4 in that form (#360, #367)"
    )


def test_max_block_size_default_is_truthy():
    """A falsy default is one of the two candidate causes; keep it a label."""
    source = CONFIG_FLOW.read_text(encoding="utf-8")
    assert "current_max_block_size" in source
    assert '"Auto (recommended)"' in source, (
        "the resolved default should fall back to a label, not to 0"
    )


def test_block_size_options_are_string_keyed():
    for key in BLOCK_SIZE_OPTIONS:
        assert isinstance(key, str), f"option key {key!r} must be a string, not {type(key)}"


def test_block_size_option_labels_are_offered_by_the_form():
    """The schema must offer exactly the labels the resolver understands.

    A mismatch here is silent: the form would accept a value the coordinator maps to 0.
    """
    source = CONFIG_FLOW.read_text(encoding="utf-8")
    assert "vol.In(list(BLOCK_SIZE_OPTIONS))" in source, (
        "the max_block_size selector should be built from BLOCK_SIZE_OPTIONS so the form "
        "and the resolver cannot drift apart"
    )


# --------------------------------------------------------------------------
# The resolver
# --------------------------------------------------------------------------

@pytest.mark.parametrize(("label", "expected"), list(BLOCK_SIZE_OPTIONS.items()))
def test_every_label_resolves_to_its_size(label, expected):
    assert resolve_block_size(label) == expected


def test_auto_resolves_to_zero_meaning_defer_to_profile():
    assert resolve_block_size("Auto (recommended)") == 0


@pytest.mark.parametrize("stored", [0, 1, 10, 25, 50])
def test_integers_from_the_broken_selector_still_resolve(stored):
    """Entries written by v1.2.0-v1.3.4 must not need migrating."""
    assert resolve_block_size(stored) == stored


@pytest.mark.parametrize("junk", [None, "", "nonsense", [], {}])
def test_unrecognised_values_fall_back_to_auto(junk):
    """Never raise from a stored option — a bad value must degrade to profile default."""
    assert resolve_block_size(junk) == 0


def test_one_register_is_offered_as_the_most_compatible_choice():
    """#360's SPA needed exactly this: 25 still failed, 1 worked."""
    assert 1 in BLOCK_SIZE_OPTIONS.values()
