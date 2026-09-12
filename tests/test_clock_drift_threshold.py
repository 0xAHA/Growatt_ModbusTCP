"""A whole-hour offset is a timezone, and the drift notice can be turned off (#439).

An owner in Åland could not clear the clock-drift notification. Pressing Inverter Clock Sync
worked, and the datalogger overwrote it about a minute later:

    17:08:38   inverter clock 16:08:17
    17:09:17   inverter clock 17:09:16   <- sync, correct
    17:10:20   inverter clock 16:10:01   <- reverted, exactly one hour back

The Growatt portal's plant timezone field offers fixed UTC offsets with no daylight-saving
zones. His is UTC+2: right in winter, an hour behind from late March to late October. The
datalogger pushes that to the inverter, so the offset is **structural** - there is no portal
setting that fixes it, and a scheduled sync would fight the dongle indefinitely and burn
EEPROM writes for nothing.

Two changes, and the first matters more than the escape hatch:

  * **A whole-hour offset is reported as a timezone, not as drift.** An RTC drifts
    gradually and does not arrive at exactly 3600 s. Telling this owner to press Sync was
    advice that could not work on his hardware; the notice now says so and explains why.

  * **The threshold is configurable, and 0 turns the notice off.** For a plant where the
    offset cannot be corrected at all, the only honest answer is a way to stop asking.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

COMPONENT = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
COORDINATOR = (COMPONENT / "coordinator.py").read_text(encoding="utf-8")
CONFIG_FLOW = (COMPONENT / "config_flow.py").read_text(encoding="utf-8")

OPTION = "clock_drift_threshold_min"


def _check() -> str:
    fn = next(
        node for node in ast.walk(ast.parse(COORDINATOR))
        if isinstance(node, ast.FunctionDef) and node.name == "_check_inverter_clock"
    )
    return ast.unparse(fn)


def test_the_threshold_comes_from_the_options():
    body = _check()

    assert OPTION in body, (
        "the drift threshold is no longer configurable, so a plant that cannot correct its "
        "offset has no way to stop the notice"
    )


def test_zero_turns_the_notice_off():
    """THE escape hatch. Without an early return, 0 would warn on any drift at all."""
    body = _check()

    assert "if threshold_s <= 0:" in body, (
        "a threshold of 0 no longer suppresses the notice - it would warn on every poll "
        "with any drift whatsoever, which is the opposite of what 0 should mean"
    )


def test_the_default_is_unchanged_at_five_minutes():
    """Nobody who has not set the option should see a change in behaviour."""
    body = _check()

    assert "_CLOCK_DRIFT_THRESHOLD_S / 60" in body, (
        "the default no longer derives from the original 5-minute constant"
    )
    assert "_CLOCK_DRIFT_THRESHOLD_S = 300" in COORDINATOR


@pytest.mark.parametrize("drift_s,expected", [
    (3600, True),      # the reporter's case, exactly one hour
    (-3600, True),     # and the other direction
    (3601, True),      # a second out is still a timezone
    (3660, True),      # a minute out, at the edge of the tolerance
    (7200, True),      # two hours
    (-10800, True),    # three
    (3720, False),     # two minutes out is not a whole hour
    (1800, False),     # half an hour
    (600, False),      # ten minutes: ordinary drift
    (301, False),      # just over the default threshold
])
def test_whole_hour_offsets_are_recognised(drift_s, expected):
    """Evaluated against the real expression rather than a reimplementation of it."""
    body = _check()
    match = re.search(r"looks_like_timezone = (.+)", body)
    assert match, "the timezone discriminator is gone"

    hours_expr = re.search(r"hours_off = (.+)", body).group(1)
    scope = {"drift_abs": abs(drift_s), "round": round, "abs": abs}
    scope["hours_off"] = eval(hours_expr, {}, scope)

    assert eval(match.group(1), {}, scope) is expected, (
        f"a drift of {drift_s}s was {'not ' if expected else ''}treated as a timezone offset"
    )


def test_a_half_hour_zone_is_not_claimed_as_drift_either():
    """India, South Australia and Newfoundland run half-hour offsets. This does not detect
    those, and that is a known limit rather than an oversight - a 30-minute discrepancy is
    equally consistent with a badly drifted clock, and calling it a timezone would be a
    guess. They still have the threshold option.
    """
    body = _check()
    hours_expr = re.search(r"hours_off = (.+)", body).group(1)
    scope = {"drift_abs": 1800, "round": round, "abs": abs}
    scope["hours_off"] = eval(hours_expr, {}, scope)

    assert eval(re.search(r"looks_like_timezone = (.+)", body).group(1), {}, scope) is False


def test_the_timezone_message_does_not_tell_them_to_press_sync():
    """The substance of the fix. On this hardware the sync works and is then reverted by
    the datalogger within a minute, so the old advice was actively wrong."""
    body = _check()
    timezone_branch = body.split("looks_like_timezone:")[1].split("else:")[0]

    assert "timezone offset rather than clock drift" in timezone_branch
    assert "will not hold" in timezone_branch, (
        "the message does not warn that a sync gets overwritten by the datalogger"
    )
    assert "daylight-saving" in timezone_branch or "daylight saving" in timezone_branch


def test_the_ordinary_drift_message_still_offers_the_sync():
    """Guard against over-correcting: a genuinely drifting clock should still be told how
    to fix it."""
    body = _check()
    ordinary = body.split("looks_like_timezone:")[1].split("else:")[1]

    assert "Inverter Clock Sync" in ordinary


def test_the_option_is_offered_in_the_config_flow():
    assert OPTION in CONFIG_FLOW, "the option exists in the coordinator but nothing sets it"
    assert f'"{OPTION}",' in CONFIG_FLOW


@pytest.mark.parametrize("path", ["strings.json", "translations/en.json"])
def test_the_option_is_labelled_and_explained(path):
    """An unlabelled option renders as its raw key, and this one needs its description:
    that 0 means off is not guessable from the name."""
    import json

    data = json.loads((COMPONENT / path).read_text(encoding="utf-8"))
    step = data["options"]["step"]["init"]

    assert step["data"].get(OPTION), f"{path} has no label for {OPTION}"
    description = step["data_description"].get(OPTION, "")
    assert "0" in description, f"{path} does not say what 0 does"
