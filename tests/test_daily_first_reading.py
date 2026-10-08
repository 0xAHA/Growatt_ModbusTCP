"""A large daily total with no baseline is confirmed, not rejected until midnight (#464).

The spike guard compares each daily counter with the value it last accepted. With no
accepted value - after a Home Assistant restart or integration reload, or after the
counter read a single 0 - it rejected any reading above the spike threshold (20 kWh) as a
glitch and published unknown. Every following reading was above 20 kWh too, so on a
MID 25KTL3-XH Energy Today, PV1 or PV2 Energy Today stayed unknown from mid-afternoon to
midnight. The reporter's history shows PV1 climbing to about 22 kWh at 14:00, then a gap
for the rest of the day.

A glitch does not repeat; a real counter does, or grows a little. So the first such reading
is withheld for one poll and accepted when the next one agrees with it. Values at or above
6553.6 kWh (a non-zero high word, beyond any single inverter's day) are still never
accepted, however often they repeat.

Runs the real `_protect_energy_totals`, loaded the same way as test_energy_spike_guard.py.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from test_energy_spike_guard import (  # noqa: E402
    COMPONENT,
    GARBAGE_KWH,
    _Coordinator,
    _Data,
    _Logger,
    _is_published,
    _load_guard,
)

ATTR = "pv1_energy_today"


def _poll(guard, coordinator, value, **extra):
    data = _Data(**{ATTR: value}, **extra)
    guard(coordinator, data)
    return data


def test_a_mid_day_restart_recovers_after_one_poll():
    """THE regression: 22.3 kWh with no baseline stayed unknown until midnight."""
    guard = _load_guard(_Logger())
    coordinator = _Coordinator()

    first = _poll(guard, coordinator, 22.3)
    assert not _is_published(first, ATTR), "an unconfirmed large reading is withheld once"

    second = _poll(guard, coordinator, 22.4)
    assert _is_published(second, ATTR), "the next agreeing poll must be believed"
    assert second.pv1_energy_today == 22.4
    assert coordinator._retained_daily_totals[ATTR] == 22.4

    third = _poll(guard, coordinator, 22.6)
    assert _is_published(third, ATTR) and third.pv1_energy_today == 22.6


def test_an_unchanged_counter_also_confirms():
    """Evening: the counter stops moving once the sun is down."""
    guard = _load_guard(_Logger())
    coordinator = _Coordinator()
    _poll(guard, coordinator, 31.0)
    assert _is_published(_poll(guard, coordinator, 31.0), ATTR)


def test_a_one_off_glitch_is_still_rejected():
    """A torn read followed by the real value: the glitch never reaches the sensor."""
    guard = _load_guard(_Logger())
    coordinator = _Coordinator(retained_daily={ATTR: 12.0})

    glitch = _poll(guard, coordinator, 900.0)
    assert not (_is_published(glitch, ATTR) and glitch.pv1_energy_today == 900.0)

    real = _poll(guard, coordinator, 12.1)
    assert _is_published(real, ATTR) and real.pv1_energy_today == 12.1


def test_a_second_reading_far_from_the_first_does_not_confirm_it():
    guard = _load_guard(_Logger())
    coordinator = _Coordinator()
    _poll(guard, coordinator, 22.0)
    jumped = _poll(guard, coordinator, 500.0)
    assert not _is_published(jumped, ATTR)


def test_garbage_beyond_any_days_total_never_confirms():
    """#412 published the same 135,777,726 kWh every poll."""
    guard = _load_guard(_Logger())
    coordinator = _Coordinator()
    for _ in range(3):
        data = _Data(generator_discharge_today=GARBAGE_KWH)
        guard(coordinator, data)
        assert "generator_discharge_today" in data.unread_fields


def test_a_single_zero_read_no_longer_costs_the_rest_of_the_day():
    """A one-poll 0 is now held rather than accepted (#464), so retention survives it and
    the next real reading is believed straight away instead of losing the afternoon."""
    guard = _load_guard(_Logger())
    coordinator = _Coordinator(retained_daily={ATTR: 21.9})
    reporting = {"energy_total": 38173.8}

    held = _poll(guard, coordinator, 0.0, **reporting)
    assert held.pv1_energy_today == 21.9
    assert coordinator._retained_daily_totals[ATTR] == 21.9

    recovered = _poll(guard, coordinator, 22.0, **reporting)
    assert _is_published(recovered, ATTR) and recovered.pv1_energy_today == 22.0


def test_awaiting_confirmation_is_not_reported_as_a_glitch():
    """After a restart every large counter goes through this - a warning per counter
    saying "likely register glitch" would be wrong on every one of them."""
    logger = _Logger()
    guard = _load_guard(logger)
    _poll(guard, _Coordinator(), 22.3)
    assert logger.warnings == []


def test_midnight_clears_pending_candidates():
    """Yesterday's evening reading must not confirm today's first one."""
    source = (COMPONENT / "coordinator.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    fn = next(n for n in ast.walk(tree)
              if isinstance(n, ast.AsyncFunctionDef) and n.name == "_handle_midnight_reset")
    assert "self._daily_first_candidates = {}" in ast.get_source_segment(source, fn)
