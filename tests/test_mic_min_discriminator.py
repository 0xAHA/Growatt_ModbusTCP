"""MIC vs MIN discrimination for DTC 5200 (Issue #367).

Growatt Table 3-1 gives DTC 5200 to *both* families — "MIC 600-3300TL-X/X2" and
"MIN 2500-6000TL-X/X2" — so the code cannot identify the model and a runtime probe of
registers 59-62 has to. On a MIC those hold per-MPPT energy **today**; on a MIN the same
addresses hold something else.

The original probe accepted a pair as MIC energy when `high < 100 or (high == 0 and
low > 0)`, and stopped at the first pair that passed. That accepts any non-zero 16-bit
low word — up to 6553.5 kWh — as a plausible *daily* figure.

A MIN 5000TL-X2 read `[0, 2]` at 59-60, matched immediately, and was handed the MIC
profile. Its 61-62 held `[0, 15787]` = 1578.7 kWh — a lifetime DC total, obviously not a
daily per-MPPT figure — but the check had already short-circuited and never looked. The
user lost 18 entities, and ENERGY_GUARD rejected that register every poll for looking
implausible as a daily total, which it was.

The rule under test: read both pairs, and require *every* readable one to be plausible
as a daily per-MPPT energy, with at least one non-zero.
"""
from __future__ import annotations

import pytest

MAX_PLAUSIBLE_DAILY_KWH = 200.0


def classify(pair_59, pair_61):
    """Mirror of the probe in auto_detection.async_detect_inverter_series.

    Args are combined kWh values, or None when the register could not be read.
    Returns True for MIC, False for MIN.
    """
    readable = [v for v in (pair_59, pair_61) if v is not None]
    implausible = [v for v in readable if v > MAX_PLAUSIBLE_DAILY_KWH]
    return bool(readable) and not implausible and any(v > 0 for v in readable)


def kwh(high, low):
    """Decode a 32-bit register pair the way the probe does."""
    return ((high << 16) | low) * 0.1


# ---------------------------------------------------------------------------
# The regression
# ---------------------------------------------------------------------------

def test_min_5000tlx2_is_not_classified_as_mic():
    """The exact registers read off the #367 reporter's MIN 5000TL-X2.

    59-60 alone looks like a perfectly ordinary 0.2 kWh daily figure, which is why the
    old check matched. 61-62 is what gives it away.
    """
    assert kwh(0, 2) == pytest.approx(0.2)
    assert kwh(0, 15787) == pytest.approx(1578.7)

    assert classify(kwh(0, 2), kwh(0, 15787)) is False


def test_the_first_pair_alone_would_have_matched():
    """Documents why the old short-circuit was wrong: judged on its own, 59-60 is
    indistinguishable from a MIC reading. Only looking at both separates them."""
    assert classify(kwh(0, 2), None) is True


# ---------------------------------------------------------------------------
# Genuine MIC hardware must still be detected
# ---------------------------------------------------------------------------

def test_mic_with_both_strings_producing():
    assert classify(5.2, 4.8) is True


def test_mic_with_one_string_unconnected():
    """A zero is not implausible — it is an unused MPPT input. This is the case a naive
    "reject anything that isn't a sensible non-zero energy" bound would misclassify."""
    assert classify(5.2, 0.0) is True


def test_mic_at_the_very_start_of_the_day():
    """Both strings at zero means nothing has been produced yet, which tells us nothing
    either way — so it must not be claimed as MIC."""
    assert classify(0.0, 0.0) is False


def test_mic_on_a_large_production_day_is_still_plausible():
    """The bound has to clear a real day comfortably: 6 kW flat out for 24 h is ~144 kWh,
    so a legitimate reading must never trip it."""
    assert classify(48.0, 44.5) is True


# ---------------------------------------------------------------------------
# The other MIN failure modes
# ---------------------------------------------------------------------------

def test_min_returning_the_dtc_code_as_garbage():
    """The failure the original check was written for — a high word of 5200."""
    assert classify(kwh(5200, 0), kwh(5200, 0)) is False


def test_min_with_lifetime_totals_in_both_pairs():
    assert classify(1544.9, 1578.8) is False


def test_one_implausible_pair_condemns_the_whole_probe():
    """A single lifetime total is enough, even when its sibling looks reasonable —
    that combination is precisely the #367 case."""
    assert classify(0.2, 1578.7) is False
    assert classify(1578.7, 0.2) is False


# ---------------------------------------------------------------------------
# Unreadable registers
# ---------------------------------------------------------------------------

def test_both_unreadable_is_not_mic():
    """No evidence is not evidence of MIC. Falling through to the MIN path is right,
    since that check verifies the 3000 range independently."""
    assert classify(None, None) is False


def test_one_unreadable_one_plausible_is_mic():
    assert classify(None, 3.4) is True


def test_one_unreadable_one_implausible_is_not_mic():
    assert classify(None, 1578.7) is False


@pytest.mark.parametrize("value", [200.0, 199.9])
def test_values_at_or_below_the_bound_are_accepted(value):
    assert classify(value, 0.0) is True


@pytest.mark.parametrize("value", [200.1, 1000.0, 6553.5])
def test_values_above_the_bound_are_rejected(value):
    assert classify(value, 0.0) is False
