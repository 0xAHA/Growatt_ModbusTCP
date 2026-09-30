"""Set Battery Mode can hand control back to the inverter (#460).

Charge, Discharge and Hold all set VPP control authority (30100) to 1 and never clear it.
Authority with no active command is not "back to normal": on a MIN TL-XH, 30100 = 1 with
30407 = 0 and 30411 = 0 held the inverter in VPP standby with Load First selected - the
battery gave ~102 W while the grid carried the house - and clearing 30100 restored Load
First at once, battery ~1,348 W (@GoncaloRibeiro11). Release is the way out that did not
exist: clear what is armed, then the authority, last.
"""
from __future__ import annotations

import importlib
from pathlib import Path

import pytest

_diag = importlib.import_module("growatt_under_test.diagnostic")
REGISTER_MAPS = importlib.import_module("growatt_under_test.const").REGISTER_MAPS
COMPONENT = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"


class _Client:
    def __init__(self, fail_at=None):
        self.writes: list[tuple] = []
        self.fail_at = fail_at

    def write_register(self, register, value, bypass_rate_limit=False):
        self.writes.append((register, value, bypass_rate_limit))
        return register != self.fail_at


def test_everything_armed_is_cleared_and_authority_goes_last():
    holding = {30100: {}, 30407: {}, 30409: {}, 30411: {}}
    client = _Client()
    assert _diag.release_vpp_control(client, holding) == [30407, 30411, 30100]
    assert client.writes == [(30407, 0, True), (30411, 0, True), (30100, 0, True)]


def test_on_min_tl_xh_it_is_exactly_the_measured_fix():
    """MIN TL-XH maps 30100 but not 30407/30411 - so Release writes 30100 = 0 and nothing
    else, which is the step that restored Load First on the reporter's inverter."""
    holding = REGISTER_MAPS["MIN_TL_XH_3000_10000_V201"]["holding_registers"]
    client = _Client()
    assert _diag.release_vpp_control(client, holding) == [30100]
    assert client.writes == [(30100, 0, True)]


def test_a_failed_write_stops_and_says_what_was_cleared():
    holding = {30100: {}, 30407: {}, 30411: {}}
    client = _Client(fail_at=30411)
    with pytest.raises(Exception, match=r"30411.*cleared so far: \[30407\]"):
        _diag.release_vpp_control(client, holding)
    assert (30100, 0, True) not in client.writes


def test_release_is_accepted_by_the_action_and_bypasses_the_three_register_guard():
    source = (COMPONENT / "diagnostic.py").read_text(encoding="utf-8")
    assert 'vol.In(["charge", "discharge", "hold", "release"])' in source
    release_at = source.index('if mode == "release":')
    guard_at = source.index("missing = [r for r in (30100, 30407, 30409) if r not in holding]")
    assert release_at < guard_at, (
        "Release is checked after the 30407/30409 guard, so MIN TL-XH - which maps only "
        "30100 - is refused the one mode it needs"
    )


def test_the_ui_offers_it():
    services = (COMPONENT / "services.yaml").read_text(encoding="utf-8")
    assert 'value: "release"' in services
