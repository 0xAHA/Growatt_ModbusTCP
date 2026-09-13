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
