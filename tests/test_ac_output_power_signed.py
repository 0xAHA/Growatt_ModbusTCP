"""AC output power (registers 35/36) is a signed 32-bit pair (#429).

@rj6zs826fn-web reported repeated UNDERFLOW warnings on this pair from a MOD-000TL3-XH. That
is what an unsigned decode of a negative value looks like: the sign bit is read as magnitude,
the combined value comes out near 4.29 billion, and the guard added in #401 withholds it
rather than publishing a plausible-looking number.

`wit.py` has declared this pair signed since before the report; the other five maps did not.
Same register, same quantity, and one profile already knew.

Withholding means the reading is *missing*, not wrong, so the visible symptom is a gap rather
than a bad number - which is why it survived so long without anyone noticing.
"""
from __future__ import annotations

import importlib
import sys

import pytest

sys.path.insert(0, "tests")

PROFILES = importlib.import_module("growatt_under_test.profiles").REGISTER_MAPS

# 2^31: the boundary an unsigned decode gets wrong.
SIGN_BIT = 0x80000000


# The legacy AC-output pair. Deliberately scoped to this address rather than to every
# register called `output_power_low`.
#
# MIN maps its own output power at 3024 and that one stays unsigned: a grid-tied string
# inverter generates and never draws through the same register, so there is no negative to
# represent. The reporter's evidence is a hybrid on the 35/36 pair, and extending a fix past
# the evidence that justifies it is how a working register gets "corrected" into a broken one.
LEGACY_AC_POWER_LOW = 36


def _legacy_pairs():
    """(profile, register) for the 35/36 AC output pair wherever it is mapped."""
    for name, profile in PROFILES.items():
        register = profile.get("input_registers", {}).get(LEGACY_AC_POWER_LOW)
        if not register or not register.get("combined_scale"):
            continue
        names = {register.get("name"), register.get("alias")}
        if names & {"output_power_low", "ac_power_low"}:
            yield name, register


def test_every_ac_output_power_low_word_is_signed():
    """THE regression. An unsigned pair cannot represent an inverter drawing from the grid,
    and the value is discarded rather than shown wrong."""
    unsigned = [profile for profile, register in _legacy_pairs() if not register.get("signed")]

    assert not unsigned, (
        "AC output power is decoded unsigned, so a negative reading underflows and is "
        "withheld:\n  " + "\n  ".join(unsigned)
    )


def test_the_grid_tied_output_register_is_left_alone():
    """MIN's own output power at 3024 stays unsigned, on purpose.

    This guards the boundary of the fix rather than the fix. Nothing in the report says a
    grid-tied string inverter reports negative generation - it generates and never draws
    through that register - so there is no negative to represent. A later sweep adding the
    flag "for consistency" would be changing a register nobody has evidence about, which is
    how a working mapping gets corrected into a broken one.
    """
    for name in ("MIN_7000_10000TL_X", "MIN_7000_10000TL_X_V201"):
        register = PROFILES[name]["input_registers"].get(3024)
        if register:
            assert not register.get("signed"), (
                f"{name} register 3024 has gained a signed flag with no evidence behind it"
            )


def test_the_pair_still_points_at_itself():
    """A 32-bit value combines as (high << 16) | low. Adding a flag must not disturb the
    pairing - a pair pointing at the wrong partner produces a large, plausible, rising
    number, which is the hardest kind of wrong to notice."""
    for profile, register in _legacy_pairs():
        partner = register["pair"]
        high = PROFILES[profile]["input_registers"][partner]
        assert high["pair"] == LEGACY_AC_POWER_LOW, (
            f"{profile}: {partner} does not pair back to {LEGACY_AC_POWER_LOW}"
        )


def test_the_scale_is_untouched():
    """Only the sign interpretation changes. A scale change here would move every AC power
    reading on five profiles by a factor of ten."""
    for profile, register in _legacy_pairs():
        assert register["combined_scale"] == 0.1, (
            f"{profile} register 36 combined_scale is {register['combined_scale']}"
        )
        assert register["combined_unit"] == "W"


def test_an_unsigned_decode_really_does_produce_the_reported_symptom():
    """Rule 4 against the evidence rather than the code.

    The reporter saw UNDERFLOW warnings, not wrong values. That is only consistent with the
    combined figure landing above the 32-bit signed boundary, which is exactly what an
    unsigned read of a small negative power gives.
    """
    watts = -500.0
    raw = int(watts / 0.1)                      # -5000, as the inverter sends it
    unsigned = raw & 0xFFFFFFFF                 # what an unsigned decode sees

    assert unsigned > SIGN_BIT, "an unsigned decode would not have tripped the guard"
    assert unsigned * 0.1 > 400_000_000, "the symptom is an absurd magnitude, as reported"

    signed = unsigned - 0x100000000 if unsigned >= SIGN_BIT else unsigned
    assert signed * 0.1 == pytest.approx(watts), "the signed decode does not recover the value"


def test_wit_kept_the_flag_it_already_had():
    """wit.py declared this signed before the report. If that regressed, the evidence that
    signed is correct for this register would go with it."""
    wit = PROFILES["WIT_4000_15000TL3"]["input_registers"][36]

    assert wit.get("signed") is True
    assert wit.get("alias") == "output_power_low" or wit.get("name") == "output_power_low"
