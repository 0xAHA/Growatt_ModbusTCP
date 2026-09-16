"""Hold selects the roster branch before writing into it (#400).

Register 30407 chooses between the two routes through the VPP control block:

    direct setpoint   30409 + 30408   selected when 30407 = 1
    roster            30412+ + 30411  selected when 30407 = 0

`Charge` and `Discharge` both set 30407 = 1 and never clear it. `Hold` writes the roster and
sets the period count, and did not touch 30407 at all. So the sequence **Charge -> Hold**
left the selector on the direct branch with 30409 still at +100 %, wrote the hold period into
the branch that was not selected, and held nothing - while the entity went on reporting
`Hold`, because `current_option` returns the last commanded mode rather than device state.

Found by @KevlarD-67 reading the Hold path against the 30407 behaviour he measured in #349,
during a roster experiment that confirmed something else:

    baseline   battery -0.93 kW (discharging)
    +1 %       battery -0.18 kW
    -1 %       battery -0.21 kW

Both signs collapse the discharge, so the `+1 %` roster hold does work on DTC 5400 - and it
worked in his rig **without 30407 being written**, because on his inverter the selector was
already 0. That is the state this change now makes explicit rather than inherited.

No failed hold was observed. This is a state-machine gap closed from a code reading, which
is why the test states what the sequence must do rather than claiming a symptom.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

COMPONENT = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
SOURCE = (COMPONENT / "select.py").read_text(encoding="utf-8")


def _mode_select() -> str:
    """The body of the WIT VPP mode select's write path."""
    tree = ast.parse(SOURCE)
    cls = next(
        node for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef) and node.name == "GrowattWitVppBatteryModeSelect"
    )
    return ast.unparse(cls)


def _branch(name: str) -> str:
    """Everything the named branch does, up to the next branch."""
    body = _mode_select()
    marker = f"option == '{name}'"
    assert marker in body, f"no {name} branch found"
    rest = body.split(marker, 1)[1]
    for following in ("elif option ==", "if option =="):
        if following in rest:
            rest = rest.split(following, 1)[0]
    return rest


def test_hold_clears_the_branch_selector():
    """THE regression. Without this, Hold after Charge writes into the unselected branch."""
    hold = _branch("Hold")

    assert "VPP_REMOTE_POWER_ENABLE, 0" in hold, (
        "the Hold branch does not clear 30407, so a Hold selected after Charge or Discharge "
        "leaves the direct setpoint selected at its previous percentage and holds nothing"
    )


def test_hold_clears_it_before_writing_the_roster():
    """Order matters. Writing the periods into an unselected branch and only then selecting
    it would work, but selecting first means the roster is never live with stale contents
    from a previous hold."""
    hold = _branch("Hold")

    select = hold.index("VPP_REMOTE_POWER_ENABLE, 0")
    write = hold.index("VPP_TOU_PERIOD1_BASE")
    assert select < write, (
        "30407 is cleared after the roster is written, so the previous roster contents are "
        "briefly in force on the newly selected branch"
    )


def test_charge_and_discharge_still_select_the_direct_branch():
    """Guard against over-correcting. Those two need 30407 = 1; clearing it there would
    break the modes this change is not about."""
    for name in ("Charge", "Discharge"):
        branch = _branch(name)
        assert "VPP_REMOTE_POWER_ENABLE, 1" in branch, (
            f"the {name} branch no longer selects the direct setpoint branch"
        )
        assert "VPP_REMOTE_POWER_ENABLE, 0" not in branch, (
            f"the {name} branch clears 30407, which deselects the branch it then writes to"
        )


def test_hold_still_writes_the_roster_and_the_count():
    """The hold itself, unchanged: the +1 % period is what stops the battery, and the count
    is what brings it into force."""
    hold = _branch("Hold")

    assert "VPP_TOU_PERIOD1_BASE" in hold
    assert "VPP_TOU_NUM_PERIODS" in hold
    assert "hold_tou_periods" in hold, (
        "the midnight-crossing split from #423 is gone - a hold selected late in the "
        "evening would expire at midnight"
    )


def test_the_failure_is_not_claimed_as_observed():
    """This came from a code reading, not a measurement. The comment must say so, or the
    next person will treat 'Charge -> Hold holds nothing' as a confirmed field report.
    """
    window = SOURCE[SOURCE.index("Select the roster branch"):][:2000]

    assert "not from a failed hold" in window or "rather than fixing an observed" in window, (
        "the comment does not record that this was reasoned rather than measured"
    )


# ---------------------------------------------------------------------------
# The 30 s cooldown must not veto part of a mode change (#400)
#
# 30407 is in _wit_control_registers, which refuses a second write to the same register
# within 30 seconds and returns False rather than raising. Charge writes 30407 = 1 and
# stamps it - so a Hold chosen within 30 s had its clear refused, logged as a warning, and
# then wrote the roster into the branch that was not selected, leaving the battery charging
# at 100 %. A fast Charge -> Hold is exactly how someone tries it.
#
# Driven rather than grepped: the gate is the behaviour, and a test that only reads the
# source would pass whether or not the bypass reaches it.
# ---------------------------------------------------------------------------

import importlib
import time

_gm = importlib.import_module("growatt_under_test.growatt_modbus")

VPP_REMOTE_POWER_ENABLE = 30407


class _FakeResult:
    @staticmethod
    def isError():
        return False


class _FakePymodbus:
    """Records writes; accepts whichever keyword this pymodbus generation uses."""

    def __init__(self):
        self.writes = []

    def write_register(self, address=None, value=None, **kwargs):
        self.writes.append((address, value))
        return _FakeResult()


def _writable_client():
    client = _gm.GrowattModbus(connection_type="tcp", host="10.0.0.1", port=502,
                               register_map="WIT_4000_15000TL3")
    client._shared_conn = None
    client._ensure_connection = lambda *args, **kwargs: None
    client.client = _FakePymodbus()
    return client


def test_a_second_write_inside_the_cooldown_is_refused():
    """The limiter still does its job - this is the behaviour being worked around, and it
    must keep working for everything that is not a mode change."""
    client = _writable_client()
    client._wit_control_last_write[VPP_REMOTE_POWER_ENABLE] = time.time()

    assert client.write_register(VPP_REMOTE_POWER_ENABLE, 0) is False
    assert client.client.writes == [], "the refused write still reached the inverter"


def test_the_mode_change_clear_gets_through_the_cooldown():
    """THE gap. Charge stamps 30407; Hold must still be able to deselect that branch."""
    client = _writable_client()
    client._wit_control_last_write[VPP_REMOTE_POWER_ENABLE] = time.time()

    assert client.write_register(VPP_REMOTE_POWER_ENABLE, 0, bypass_rate_limit=True) is True
    assert client.client.writes == [(VPP_REMOTE_POWER_ENABLE, 0)]


def test_a_bypassed_write_still_stamps_the_limiter():
    """Otherwise the bypass would blind the limiter for the next caller."""
    client = _writable_client()
    before = time.time() - 29
    client._wit_control_last_write[VPP_REMOTE_POWER_ENABLE] = before

    client.write_register(VPP_REMOTE_POWER_ENABLE, 0, bypass_rate_limit=True)
    assert client._wit_control_last_write[VPP_REMOTE_POWER_ENABLE] > before


def test_the_bypass_is_off_by_default():
    """It has to be asked for explicitly, or the limit is no limit."""
    import inspect
    sig = inspect.signature(_gm.GrowattModbus.write_register)
    assert sig.parameters["bypass_rate_limit"].default is False


# ---------------------------------------------------------------------------
# The select's clear, and the same clear in the action
# ---------------------------------------------------------------------------

DIAGNOSTIC = (COMPONENT / "diagnostic.py").read_text(encoding="utf-8")


def test_the_select_clear_bypasses_the_cooldown():
    hold = _branch("Hold")
    clear = hold.index("VPP_REMOTE_POWER_ENABLE, 0")
    window = hold[clear - 200:clear + 200]
    assert "bypass_rate_limit" in window, (
        "the Hold branch clears 30407 without bypassing the 30 s limiter, so a Hold within "
        "30 s of Charge is silently refused and writes into the unselected branch"
    )


def test_the_select_aborts_rather_than_warning_when_the_clear_fails():
    """A hold that cannot deselect the direct branch is not a hold. Continuing leaves the
    previous mode's setpoint in force while the entity reports Hold."""
    hold = _branch("Hold")
    clear = hold.index("VPP_REMOTE_POWER_ENABLE, 0")
    assert "HomeAssistantError" in hold[clear:clear + 600], (
        "a failed 30407 clear only warns, and the roster is written anyway"
    )


def _action_branch(mode: str) -> str:
    """What set_battery_mode does for one mode, up to the next branch."""
    marker = f'mode == "{mode}"'
    assert marker in DIAGNOSTIC, f"no {mode} branch in set_battery_mode"
    rest = DIAGNOSTIC.split(marker, 1)[1]
    for following in ('elif mode ==', '_LOGGER.info("Successfully set battery mode'):
        if following in rest:
            rest = rest.split(following, 1)[0]
    return rest


def test_the_action_hold_clears_the_branch_selector_too():
    """The action is reachable on MOD - its guard only asks for 30100/30407/30409, which
    MOD_6000_15000TL3_XH carries - so the select's fix did not cover it (#400)."""
    hold = _action_branch("hold")
    assert "VPP_REMOTE_POWER_ENABLE, 0" in hold, (
        "set_battery_mode's hold branch does not clear 30407, so charge -> hold through "
        "the action still writes its roster into the unselected branch"
    )
    select = hold.index("VPP_REMOTE_POWER_ENABLE, 0")
    roster = hold.index("VPP_TOU_PERIOD1_BASE")
    assert select < roster, "30407 is cleared after the roster is written"


def test_the_action_clear_bypasses_the_cooldown_and_aborts_on_failure():
    hold = _action_branch("hold")
    clear = hold.index("VPP_REMOTE_POWER_ENABLE, 0")
    window = hold[clear:clear + 500]
    assert "0, True" in hold[clear - 80:clear + 120] or "bypass_rate_limit" in window, (
        "the action's clear does not bypass the 30 s limiter"
    )
    assert "HomeAssistantError" in window, (
        "a failed clear in the action does not stop the hold being written"
    )


def test_the_action_charge_and_discharge_still_select_the_direct_branch():
    for mode in ("charge", "discharge"):
        branch = _action_branch(mode)
        assert "VPP_REMOTE_POWER_ENABLE, 1" in branch, (
            f"set_battery_mode's {mode} branch no longer selects the direct setpoint"
        )
        assert "VPP_REMOTE_POWER_ENABLE, 0" not in branch, (
            f"set_battery_mode's {mode} branch clears the branch it then writes to"
        )
