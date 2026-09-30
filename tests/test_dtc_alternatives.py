"""A DTC shared by hardware generations must not flag the other generation's profile (#461).

DTC 5100 covers MIN TL-XH and TL-XH2, and the registry has to resolve it to one profile.
The XH2 answers only the VPP ranges - the 3000 block the default profile reads returns
nothing - so an XH2 owner who correctly chose the VPP-only profile was told by the profile
re-check to switch to one that cannot read their inverter. Confirmed by register scan on two
XH2 units (#361, #461): every legacy range silent, 30000-30499 and 31000-31299 answering.
"""
from __future__ import annotations

import ast
import importlib
from pathlib import Path

import pytest

_auto = importlib.import_module("growatt_under_test.auto_detection")
PROFILES = importlib.import_module("growatt_under_test.device_profiles").INVERTER_PROFILES
COMPONENT = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"


def test_5100_recognises_both_generations():
    entry = _auto.DTC_REGISTRY[5100]
    assert "min_tl_xh2_3000_10000_v201" in entry.alternatives, (
        "an XH2 on its own VPP-only profile would be told to move to one it cannot read"
    )
    assert "min_tl_xh_3000_10000_v201" in entry.alternatives


def test_the_generations_really_do_need_different_profiles():
    """The premise: if the XH2 profile ever read the same map, the equivalence guard would
    already cover it and alternatives would be redundant for it."""
    default = PROFILES[_auto.DTC_REGISTRY[5100].profile]
    xh2 = PROFILES["min_tl_xh2_3000_10000_v201"]
    assert default["register_map"] != xh2["register_map"]


@pytest.mark.parametrize("dtc", sorted(_auto.DTC_REGISTRY))
def test_every_alternative_is_a_real_profile(dtc):
    for key in _auto.DTC_REGISTRY[dtc].alternatives:
        assert key in PROFILES, f"DTC {dtc} lists unknown profile {key!r} as an alternative"


def test_the_recheck_honours_alternatives_before_raising_a_notice():
    source = (COMPONENT / "coordinator.py").read_text(encoding="utf-8")
    fn = next(n for n in ast.walk(ast.parse(source))
              if isinstance(n, ast.FunctionDef) and n.name == "_recheck_profile_against_dtc")
    body = ast.get_source_segment(source, fn)
    check = body.index("configured in _entry.alternatives")
    notice = body.index("self._pending_profile_issue = {")
    assert check < notice, "alternatives are consulted after the notice is prepared"
    branch = body[check:body.index("return", check)]
    assert "self._pending_profile_issue_clear = True" in branch, (
        "a stale notice from before this fix would stay in the repair list"
    )
