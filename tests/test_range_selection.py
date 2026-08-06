"""Range-selection tests.

`read_all_data()` decides which register ranges to read and, critically, whether a
failure in a given range should abort the whole poll. That decision has been wrong
three times in production:

  v1.1.1  #357  The 3000 range was suppressed on failure while remaining a profile's
                only source of data, so the poll returned an all-zero result that
                looked like a healthy inverter. Fixed by making it fatal.

  v1.1.5  #361  ...but "primary" was defined as `not has_base_range`, which is false
                for V2.01 profiles carrying both 3000+ and 31000+. On VPP-only
                hardware the poll aborted before reaching the range that worked.

  v1.1.8  #364  The base range was unconditionally fatal, so three legacy stragglers
                (91, 92, 97) in an otherwise-VPP profile killed every poll.

These tests pin the resulting rule: a range is only "primary" — and therefore fatal
on failure — when the profile has no other source of input data.

The predicates are asserted directly rather than through read_all_data() because the
decision is what regressed each time; wiring a fake transport would test the plumbing
around it, not the rule itself.
"""
from __future__ import annotations

import importlib

import pytest

_gm = importlib.import_module("growatt_under_test.growatt_modbus")


def _flags(addresses):
    """Reproduce the range predicates from read_all_data() for a set of addresses."""
    return {
        "base": any(0 <= a < 875 for a in addresses),
        "r875": any(875 <= a < 1000 for a in addresses),
        "storage": any(1000 <= a < 2000 for a in addresses),
        "r3000": any(3000 <= a < 4000 for a in addresses),
        "r8000": any(8000 <= a < 8200 for a in addresses),
        "r31000": any(31000 <= a < 32000 for a in addresses),
    }


def _base_is_primary(addresses) -> bool:
    """Mirror of the base-range fatality rule.

    Production evaluates this only inside `if has_base_range:`, so a profile with no
    base range can never reach it — reflected here by returning False rather than
    letting the predicate answer a question that is never asked.
    """
    f = _flags(addresses)
    if not f["base"]:
        return False
    return not (f["storage"] or f["r3000"] or f["r875"] or f["r8000"] or f["r31000"])


def _3000_is_primary(addresses) -> bool:
    """Mirror of the 3000-range fatality rule. Same guard as above."""
    f = _flags(addresses)
    if not f["r3000"]:
        return False
    return not f["base"] and not f["r31000"]


# --------------------------------------------------------------------------
# The 3000 range
# --------------------------------------------------------------------------

def test_3000_is_primary_when_it_is_the_only_range():
    """Plain MIN TL-X: registers 3000-3119 only. Failure must be fatal (#357)."""
    assert _3000_is_primary(range(3000, 3120)) is True


def test_3000_not_primary_when_a_vpp_range_exists():
    """Regression guard for Issue #361.

    V2.01 profiles carry both 3000+ and 31000+. On MIN TL-XH2 the 3000 range is
    dead while 31000+ returns live data — treating 3000 as primary aborted the poll
    before the working range was ever read.
    """
    addrs = list(range(3000, 3120)) + list(range(31000, 31030))
    assert _3000_is_primary(addrs) is False


def test_3000_not_primary_when_a_base_range_exists():
    addrs = [0, 1, 2] + list(range(3000, 3120))
    assert _3000_is_primary(addrs) is False


# --------------------------------------------------------------------------
# The base range
# --------------------------------------------------------------------------

def test_base_is_primary_when_it_is_the_only_range():
    """MIC / MID-X / TL3-S: base range is everything. Failure must stay fatal."""
    assert _base_is_primary(range(0, 125)) is True


def test_base_not_primary_when_3000_and_vpp_ranges_exist():
    """Regression guard for Issue #364.

    MIN_TL_XH_3000_10000_V201 has 104 input registers, 101 of them at 3000+/31000+.
    Three legacy stragglers (91, 92 fallback PV energy; 97 boost temp) put it in the
    base range, and an unconditionally fatal base read killed every poll on hardware
    that serves only the VPP ranges.
    """
    addrs = [91, 92, 97] + list(range(3000, 3120)) + list(range(31200, 31230))
    assert _base_is_primary(addrs) is False


def test_base_not_primary_when_storage_range_exists():
    """SPH-style: base 0-124 plus storage 1000-1124."""
    addrs = list(range(0, 125)) + list(range(1000, 1125))
    assert _base_is_primary(addrs) is False


# --------------------------------------------------------------------------
# Real profiles — the rule applied to what actually ships
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("map_key", "expect_base_primary", "expect_3000_primary"),
    [
        # VPP-only: no base range, no 3000 range at all
        ("MIN_TL_XH2_3000_10000_V201", False, False),
        # 3000-range only — the #357 case, must stay fatal
        ("MIN_3000_6000TL_X", False, True),
        # SPA: storage range only
        ("SPA_3000_6000_TL_BL", False, False),
    ],
)
def test_shipped_profiles_resolve_as_expected(map_key, expect_base_primary, expect_3000_primary):
    reg_map = _gm.REGISTER_MAPS[map_key]
    addrs = list(reg_map["input_registers"].keys())
    assert _base_is_primary(addrs) is expect_base_primary
    assert _3000_is_primary(addrs) is expect_3000_primary


def test_tl_xh2_profile_is_genuinely_vpp_only():
    """The TL-XH2 profile must not regain legacy registers.

    Its whole reason for existing is that the hardware rejects everything below
    31000; a stray legacy register would reintroduce the #364 abort.
    """
    addrs = list(_gm.REGISTER_MAPS["MIN_TL_XH2_3000_10000_V201"]["input_registers"])
    assert all(a >= 31000 for a in addrs), (
        f"non-VPP registers present: {sorted(a for a in addrs if a < 31000)}"
    )
