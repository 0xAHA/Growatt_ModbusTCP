"""A _V201 variant must not silently drop a top-level flag from its base (#441).

A V2.01 variant is built as a fresh dict that merges its base's registers:

    SPH_TL3_3000_10000_V201 = {
        'name': ...,
        'description': ...,
        'notes': ...,
        'input_registers': {
            **SPH_TL3_3000_10000['input_registers'],
            ...
        },
    }

The registers come through. **Every other top-level key does not.** So a behaviour flag added
to a base profile is silently absent from its V2.01 variant unless somebody remembers to
repeat it, and nothing fails when they do not.

`use_mppt_energy_today` was added to `SPH_TL3_3000_10000` for #307 - register 53/54 counts
all AC output including battery discharge, so the per-MPPT DC registers are summed instead.
The flag never reached the V2.01 variant, and `protocol_variant: auto` selects that variant
on this hardware, so the **default configuration landed on the path #307 had fixed**:

    01:00   solar_energy_today 0.6 kWh   solar_total_power 0.0 W   battery_discharge 0.8 kWh
    01:47   solar_energy_today 0.9 kWh   solar_total_power 0.0 W   battery_discharge 1.1 kWh

+0.3 kWh of "solar" overnight, in lockstep with the battery. Reported by @acsel91 with the
root cause already found, and his closing suggestion - *"it may be worth checking the other
_V201 variants for the same pattern"* - turned up a second profile with the same omission.

This file is that check, kept. It compares each variant against its base rather than against
a list, so a flag invented next year is covered without anyone updating it.
"""
from __future__ import annotations

import importlib

import pytest

_const = importlib.import_module("growatt_under_test.const")

# Keys a variant is expected to define for itself.
OWN_KEYS = {"name", "description", "notes", "input_registers", "holding_registers"}


def _pairs():
    """Every (base, variant) map pair where the variant is the base's V2.01 form."""
    maps = _const.REGISTER_MAPS
    return [
        (name[:-5], name)
        for name in sorted(maps)
        if name.endswith("_V201") and name[:-5] in maps
    ]


def test_there_are_variants_to_check():
    assert _pairs(), "no base/_V201 pairs found - has the naming convention changed?"


@pytest.mark.parametrize("base_name,variant_name", _pairs())
def test_the_variant_carries_every_behaviour_flag_of_its_base(base_name, variant_name):
    """THE regression, generalised. A flag on the base and absent on the variant means the
    variant quietly behaves differently, and the variant is what auto-detection usually
    picks."""
    maps = _const.REGISTER_MAPS
    base, variant = maps[base_name], maps[variant_name]

    dropped = {
        key: value for key, value in base.items()
        if key not in OWN_KEYS and key not in variant
    }

    assert not dropped, (
        f"{variant_name} does not carry {sorted(dropped)} from {base_name}. A V2.01 variant "
        f"merges its base's registers but writes its own top-level keys, so a flag has to be "
        f"repeated or it is lost - and `protocol_variant: auto` usually selects the variant."
    )


@pytest.mark.parametrize("base_name,variant_name", _pairs())
def test_a_variant_does_not_contradict_its_base(base_name, variant_name):
    """The opposite direction. A variant may legitimately set a flag its base does not, but
    setting the *same* flag to a *different* value is almost certainly an accident rather
    than a decision - and this catches it while it is still one line to check."""
    maps = _const.REGISTER_MAPS
    base, variant = maps[base_name], maps[variant_name]

    conflicting = {
        key: (base[key], variant[key])
        for key in base
        if key not in OWN_KEYS and key in variant and base[key] != variant[key]
    }

    assert not conflicting, (
        f"{variant_name} disagrees with {base_name} on {conflicting}. If that is deliberate, "
        f"say so in a comment on the variant and add the key to this test's allowance."
    )


def test_the_reported_profile_sums_the_per_mppt_registers():
    """The specific case, named so the issue stays findable from the test."""
    variant = _const.REGISTER_MAPS["SPH_TL3_3000_10000_V201"]

    assert variant.get("use_mppt_energy_today") is True, (
        "solar energy today will be read from register 53/54, which counts AC output "
        "including battery discharge - it rises overnight"
    )

    names = {info.get("name") for info in variant["input_registers"].values()}
    assert "pv1_energy_today_low" in names, (
        "the flag is set but the registers it needs are not mapped, so the fallback to "
        "53/54 happens anyway and the flag is decoration"
    )
