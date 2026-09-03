"""Daily counters must survive midnight without inventing or freezing values (#410).

Two defects, both visible in one debug log from an SPF 3000-6000 ES PLUS.

**Retention treated a real zero as a dormant inverter.** Retention exists because some
inverters answer Modbus but return 0 for everything, and a lifetime total dropping to 0
makes Home Assistant record a phantom counter reset. It was extended to daily counters by
analogy (v0.6.6b2, "Daily totals: same logic"), and the analogy fails: a daily counter
reading 0 is not a silence, it is a day with no activity of that kind. Register 65 read
`0.0` on all 54 polls of the capture while the sensor published yesterday's **2.90 kWh**.

**The midnight transition hung on a timer.** The grace window is 10 minutes, on the
assumption that an inverter clears its counters 30-90 s after midnight. That SPF cleared
`energy_today` between **00:15:08 and 00:16:10** - roughly 16 minutes. In the six-minute
gap, yesterday's totals were adopted as today's: `discharge_energy_today` took on 11.8 kWh,
while `energy_today` escaped only because 28.9 happened to exceed the 20 kWh spike
threshold. Which counter survived was decided by an unrelated constant.

The discriminator for the first is in the same snapshot at no cost: lifetime totals. A
dormant inverter returns 0 for those too, so a non-zero one proves the device is answering
with real values. In that log `ac_discharge_energy_total` read 2775.6 kWh throughout.

The fix for the second is to test the value rather than the clock, which needs no
per-device timing constant - and so does not depend on having more than this one device.

Like test_energy_spike_guard.py, these execute the real method rather than reading it.
"""
from __future__ import annotations

import importlib
import sys

import pytest

sys.path.insert(0, "tests")

CONST = importlib.import_module("growatt_under_test.const")

from test_energy_spike_guard import _Coordinator, _Data, _Logger, _load_guard  # noqa: E402

# The reporter's figures.
AC_DISCHARGE = "ac_discharge_energy_today"
YESTERDAY_KWH = 2.90
LIFETIME_ATTR = "ac_discharge_energy_total"
LIFETIME_KWH = 2775.6


def _awake(**daily):
    """A snapshot from an inverter that is plainly answering: lifetime totals non-zero."""
    return _Data(**{LIFETIME_ATTR: LIFETIME_KWH}, **daily)


def _silent(**daily):
    """A dormant inverter: every register, lifetime included, reads 0."""
    return _Data(**daily)


def test_a_working_inverter_reporting_zero_is_believed():
    """THE #410 regression. Register 65 read 0 all day on a quiet day; the sensor showed
    2.90 kWh because retention decided the inverter must be dormant."""
    logger = _Logger()
    guard = _load_guard(logger)
    data = _awake(**{AC_DISCHARGE: 0.0})

    guard(_Coordinator(retained_daily={AC_DISCHARGE: YESTERDAY_KWH}), data)

    assert getattr(data, AC_DISCHARGE) == 0.0, (
        "yesterday's total was re-published over a real zero from a working inverter"
    )


def test_retention_is_dropped_once_a_real_zero_arrives():
    """Otherwise the same substitution returns on the next poll and the next."""
    logger = _Logger()
    guard = _load_guard(logger)
    coordinator = _Coordinator(retained_daily={AC_DISCHARGE: YESTERDAY_KWH})

    guard(coordinator, _awake(**{AC_DISCHARGE: 0.0}))

    assert AC_DISCHARGE not in coordinator._retained_daily_totals


def test_a_dormant_inverter_still_gets_retention():
    """The case retention was built for must keep working: every register reads 0,
    including lifetime totals, so the zero carries no information."""
    logger = _Logger()
    guard = _load_guard(logger)
    data = _silent(**{AC_DISCHARGE: 0.0})

    guard(_Coordinator(retained_daily={AC_DISCHARGE: YESTERDAY_KWH}), data)

    assert getattr(data, AC_DISCHARGE) == YESTERDAY_KWH, (
        "a genuinely dormant inverter lost its retained value - this reintroduces the "
        "phantom counter reset retention exists to prevent"
    )


def test_a_counter_still_holding_yesterdays_value_reports_zero():
    """The inverter had not cleared it yet. 16 minutes after midnight, in the reporter's
    case - long after any fixed grace window had closed."""
    logger = _Logger()
    guard = _load_guard(logger)
    data = _awake(energy_today=28.9)

    guard(_Coordinator(pre_midnight={"energy_today": 28.9}), data)

    assert data.energy_today == 0.0


def test_it_does_not_depend_on_how_long_the_inverter_takes():
    """The point of the change. No grace window is open here at all - the old code would
    have accepted the stale value outright."""
    logger = _Logger()
    guard = _load_guard(logger)
    coordinator = _Coordinator(pre_midnight={"discharge_energy_today": 11.8})

    # An hour of polls, all still reading yesterday's figure.
    for _ in range(60):
        data = _awake(discharge_energy_today=11.8)
        guard(coordinator, data)
        assert data.discharge_energy_today == 0.0


def test_once_the_counter_moves_it_is_trusted_again():
    """The inverter cleared and the new day began. 0.4 kWh is today's, not a leftover."""
    logger = _Logger()
    guard = _load_guard(logger)
    coordinator = _Coordinator(pre_midnight={"discharge_energy_today": 11.8})

    data = _awake(discharge_energy_today=0.4)
    guard(coordinator, data)

    assert data.discharge_energy_today == 0.4
    assert "discharge_energy_today" not in coordinator._pre_midnight_daily_totals


def test_a_counter_climbing_back_to_yesterdays_figure_is_not_suppressed_twice():
    """Once the register has moved, the day's watch on it is over. Otherwise a counter that
    legitimately reached yesterday's total again would blink to 0."""
    logger = _Logger()
    guard = _load_guard(logger)
    coordinator = _Coordinator(pre_midnight={"discharge_energy_today": 11.8})

    guard(coordinator, _awake(discharge_energy_today=0.4))   # moved: watch released
    data = _awake(discharge_energy_today=11.8)               # coincidence later that day
    guard(coordinator, data)

    assert data.discharge_energy_today == 11.8


def test_the_counters_under_test_are_really_tracked():
    """Rule 4: the sweep has to have been able to find them."""
    for attr in (AC_DISCHARGE, "energy_today", "discharge_energy_today"):
        assert attr in CONST.DAILY_TOTAL_ATTRS
    assert LIFETIME_ATTR in CONST.LIFETIME_TOTAL_ATTRS
