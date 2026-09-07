"""A HOLD window crossing midnight must not be silently truncated (#423).

TOU period words are minutes since midnight and do not wrap - 1440 is out of range, not
00:00 tomorrow. The HOLD path used to clamp the end word to 1439, which is correct as
arithmetic and wrong as behaviour: it turned a two-hour hold selected at 23:50 into nine
minutes, expiring at midnight.

Nothing surfaced that. `current_option` returns `coordinator.wit_vpp_last_mode` - what was
last commanded, not what the inverter is doing - so after the period lapsed the battery
resumed discharging into the house while Home Assistant still showed `Hold`. An automation
reading that state read a value that stopped being true at midnight.

Overnight is when a hold is most wanted, so the window where the clamp bit hardest is the
window it would actually be used in.

`select.py` imports Home Assistant, which this suite does not have, so the helper is compiled
in isolation. It is a pure function of the clock, which is why it was worth extracting from
the write sequence rather than testing through it.
"""
from __future__ import annotations

import ast
import types
from pathlib import Path

import pytest

SOURCE = (Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
          / "select.py").read_text(encoding="utf-8")


def _load_helper():
    fn = next(
        node for node in ast.parse(SOURCE).body
        if isinstance(node, ast.FunctionDef) and node.name == "hold_tou_periods"
    )
    module = types.ModuleType("_hold")
    exec(compile(ast.Module(body=[fn], type_ignores=[]), "<hold>", "exec"), module.__dict__)
    return module.hold_tou_periods


hold_tou_periods = _load_helper()

MIDNIGHT_MINUS_TEN = 23 * 60 + 50   # 1430
LAST_MINUTE = 23 * 60 + 59          # 1439


def _total_minutes(periods):
    """Minutes actually covered. Both words are inclusive-ish bounds on the same day, so a
    period is end - start; a wrapped pair sums across the two."""
    return sum(end - start for start, end in periods)


def test_a_midday_hold_is_a_single_two_hour_period():
    """Guard against over-correcting: the common case must not gain a second period."""
    periods = hold_tou_periods(14 * 60)

    assert periods == [(14 * 60 - 5, 16 * 60)]


def test_a_late_evening_hold_is_not_truncated_to_nine_minutes():
    """THE regression. At 23:50 the old code wrote a single period 1425-1439."""
    periods = hold_tou_periods(MIDNIGHT_MINUS_TEN)

    assert len(periods) == 2, (
        f"the hold was written as {len(periods)} period(s); a window crossing midnight needs "
        f"two, or it expires at 23:59"
    )
    assert _total_minutes(periods) >= 120, (
        f"the hold covers only {_total_minutes(periods)} minutes of the 125 requested"
    )


def test_the_two_periods_meet_at_midnight():
    """The first must run to the last minute of the day and the second start at the first,
    or the battery is unheld across the boundary."""
    first, second = hold_tou_periods(MIDNIGHT_MINUS_TEN)

    assert first[1] == 1439, "the first period does not run to 23:59"
    assert second[0] == 0, "the second period does not start at 00:00"


def test_no_period_word_is_ever_out_of_range():
    """1440 is not a valid period word. Writing one is what the original clamp existed to
    prevent, and the fix must not reintroduce it at any minute of the day."""
    for minute in range(0, 1440):
        for start, end in hold_tou_periods(minute):
            assert 0 <= start <= 1439, f"start {start} out of range at {minute}"
            assert 0 <= end <= 1439, f"end {end} out of range at {minute}"
            assert start <= end, f"period {start}-{end} runs backwards at {minute}"


def test_a_window_ending_exactly_at_midnight_writes_one_period():
    """22:00 + 2h lands on 1440. There is no second period to write, and a 0-0 period would
    be degenerate - the count would claim a period that covers nothing."""
    periods = hold_tou_periods(22 * 60)

    assert len(periods) == 1
    assert periods[0][1] == 1439


def test_the_last_minute_of_the_day_still_produces_a_usable_hold():
    """23:59 was the worst case - a one-minute period, indistinguishable from a failed
    hold."""
    periods = hold_tou_periods(LAST_MINUTE)

    assert _total_minutes(periods) >= 120, (
        f"a hold selected at 23:59 covers {_total_minutes(periods)} minutes"
    )


@pytest.mark.parametrize("minute", range(0, 1440, 7))
def test_every_start_time_gets_the_full_duration(minute):
    """Swept rather than spot-checked: the bug was a boundary, and a boundary is exactly what
    a handful of chosen times misses. 7 is coprime with 60 so the sweep does not sit on the
    hour."""
    covered = _total_minutes(hold_tou_periods(minute))

    assert covered >= 120, (
        f"a hold selected at {minute // 60:02d}:{minute % 60:02d} covers only {covered} "
        f"minutes"
    )


def test_the_write_loop_uses_the_helper_and_sets_the_count_to_match():
    """The arithmetic being right is not enough - the sequence has to write every period it
    returns and tell the inverter how many there are. Writing two periods while 30411 still
    said 1 would leave the second one inert."""
    assert "periods = hold_tou_periods(current_minutes)" in SOURCE, (
        "the HOLD path no longer uses the helper these tests exercise"
    )
    assert "self.VPP_TOU_PERIOD1_BASE + (index * 3)" in SOURCE, (
        "the write loop does not stride by 3 registers per period"
    )
    assert "client.write_register(self.VPP_TOU_NUM_PERIODS, len(periods))" in SOURCE, (
        "the period count is not set from the number of periods actually written"
    )
