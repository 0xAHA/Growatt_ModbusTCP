"""The wrong-profile notice must not fire when there is nothing to gain (#405).

A DTC can cover several model families and the registry has to resolve it to exactly one
profile. **5400** is `MOD 3-10KTL3-XH/BP; MID 11-30KTL3-XH; MID 8-15KTL3-XHL/JP`, resolved
to `mod_6000_15000tl3_xh_v201` - so every MID owner in that group was told their inverter
indicated a different profile from the one they were running.

There is nothing to move to. The two profiles declare the same `register_map` and the same
102 sensors, differing only in `name`, `description` and `max_power_kw`. Following the
advice would change no reading; it would only leave the owner on a profile named for
hardware they do not have, which then misleads whoever reads their next diagnostic report.

Reported by @as-wallpen on a MID 25KTL3-XH with 102 sensors present and nothing missing.

The notice claims "the profile in use maps fewer registers than your hardware supports".
That claim is false whenever the maps and sensor sets match, so the guard tests behaviour
rather than name identity.
"""
from __future__ import annotations

import ast
import importlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, "tests")

COMPONENT = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
PROFILES = importlib.import_module("growatt_under_test.device_profiles").INVERTER_PROFILES

MOD_XH = "mod_6000_15000tl3_xh_v201"
MID_XH = "mid_11000_30000tl3_xh_v201"


def _recheck_source() -> str:
    """Executable lines of the re-check, comments stripped.

    Stripped because the guard explains itself at length and names the very identifiers
    being asserted on, so prose would satisfy the checks below.
    """
    source = (COMPONENT / "coordinator.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    fn = next(
        n for n in ast.walk(tree)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        and n.name == "_recheck_profile_against_dtc"
    )
    body = ast.get_source_segment(source, fn)
    return "\n".join(
        line for line in body.splitlines() if not line.strip().startswith("#")
    )


def test_the_two_profiles_really_are_equivalent():
    """Rule 4 first: the whole premise depends on this, and if these profiles ever diverge
    the guard below starts suppressing a notice that would have been worth showing."""
    mod, mid = PROFILES[MOD_XH], PROFILES[MID_XH]

    assert mod["register_map"] == mid["register_map"] == "MOD_6000_15000TL3_XH"
    assert set(mod["sensors"]) == set(mid["sensors"])
    assert sorted(k for k in set(mod) | set(mid) if mod.get(k) != mid.get(k)) == [
        "description", "max_power_kw", "name",
    ]


def test_the_check_compares_behaviour_not_just_names():
    """The original guard returned early only on `suggested == configured`, which is name
    identity. Two differently-named profiles that behave identically slipped straight past
    it and raised a repair notice recommending a move with no effect."""
    body = _recheck_source()

    # Anchored on INVERTER_PROFILES rather than the bare token 'register_map': the method
    # already contains self._client.register_map for the unrelated off-grid guard, which
    # made an earlier version of this assertion pass without the fix present.
    assert "INVERTER_PROFILES" in body, (
        "the re-check never looks the two profiles up, so it cannot tell whether the one "
        "it is recommending would behave any differently"
    )
    assert "'register_map'" in body, (
        "the re-check does not compare register maps, so a DTC covering several model "
        "families will recommend a sibling profile that reads exactly the same registers"
    )
    assert "'sensors'" in body, (
        "the re-check does not compare sensor sets - two profiles sharing a register map "
        "can still differ in what they create"
    )


def test_the_equivalence_guard_runs_before_the_notice_is_raised():
    """Ordering matters: suppressing after the repair issue is created would still show it."""
    body = _recheck_source()

    guard = body.index("INVERTER_PROFILES")
    notice = body.index("_pending_profile_issue")
    assert guard < notice, (
        "the equivalence check happens after the repair notice is prepared"
    )


def test_dtc_5400_is_the_case_this_covers():
    """Pin the specific DTC, so that if its registry entry is ever repointed somewhere with
    a genuinely different map, this file is revisited rather than quietly still passing."""
    auto = importlib.import_module("growatt_under_test.auto_detection")
    entry = auto.DTC_REGISTRY[5400]

    assert entry.profile == MOD_XH
    assert "MID" in entry.model, (
        "DTC 5400 no longer names a MID family - re-read whether this suppression is still "
        "the right behaviour"
    )
