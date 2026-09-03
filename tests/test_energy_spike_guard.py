"""The energy spike guard must withhold the value it rejects, not publish it (#412).

`_protect_energy_totals()` exists to stop a `total_increasing` sensor recording an
impossible jump, because Home Assistant reads that as a counter reset and flattens the
energy dashboard. On detecting a spike it logged a warning, declined to write the value
into `_retained_daily_totals`, and then **left `data` untouched** - so the rejected reading
went straight to the sensor and into long-term statistics exactly as read. "Rejected"
meant only "not remembered".

A reporter on #410 was publishing `generator_discharge_today` at 135,777,726.3 kWh on every
poll while this guard fired, for a generator input with nothing connected to it.

These tests **execute the real method** rather than inspecting its source. That is the
whole point: the broken version read correctly - it carried a comment saying "do not
persist the garbage value", which was true and irrelevant, because persisting was never
what reached the user. Only running it and looking at what lands on `data` shows the gap.

The tests/ suite runs without Home Assistant, so the coordinator module cannot be
imported. The method is extracted with `ast` and executed against stub collaborators;
`const.py` is loaded for real through the synthetic package conftest.py provides, so the
attribute lists under test are the shipped ones.
"""
from __future__ import annotations

import ast
import importlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, "tests")

COMPONENT = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
CONST = importlib.import_module("growatt_under_test.const")


class _Logger:
    """Records calls so the warn-once behaviour can be asserted on."""

    def __init__(self):
        self.warnings: list[str] = []
        self.debugs: list[str] = []

    def warning(self, msg, *args):
        self.warnings.append(msg % args if args else msg)

    def debug(self, msg, *args):
        self.debugs.append(msg % args if args else msg)


def _load_guard(logger):
    """Extract _protect_energy_totals and execute it against stubs.

    The method does `from .const import ...` at call time, which has no package context
    here. That one line is redirected at the real const module loaded above; the
    substitution is asserted so a change to the import fails loudly rather than quietly
    testing nothing.
    """
    source = (COMPONENT / "coordinator.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    fn = next(
        n for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef) and n.name == "_protect_energy_totals"
    )
    body = ast.get_source_segment(source, fn)

    original = "from .const import LIFETIME_TOTAL_ATTRS, DAILY_TOTAL_ATTRS"
    assert original in body, (
        "the const import in _protect_energy_totals has changed shape - this test is no "
        "longer executing what it thinks it is"
    )
    body = body.replace(
        original,
        "from growatt_under_test.const import LIFETIME_TOTAL_ATTRS, DAILY_TOTAL_ATTRS",
    )

    from datetime import datetime

    namespace = {"_LOGGER": logger, "datetime": datetime}
    exec(compile(ast.parse(body), "<guard>", "exec"), namespace)
    return namespace["_protect_energy_totals"]


class _Coordinator:
    def __init__(self, retained_daily=None, pre_midnight=None):
        self._retained_lifetime_totals: dict[str, float] = {}
        self._retained_daily_totals: dict[str, float] = dict(retained_daily or {})
        self._midnight_grace_expires = None
        self._pre_midnight_daily_totals: dict[str, float] = dict(pre_midnight or {})
        self._register_map_key = "spf_3000_6000_es_plus"
        self._spike_warned: set[str] = set()


class _Data:
    """Stands in for GrowattData: every tracked attribute plus the unread-field set."""

    def __init__(self, **values):
        for attr in set(CONST.DAILY_TOTAL_ATTRS) | set(CONST.LIFETIME_TOTAL_ATTRS):
            setattr(self, attr, 0.0)
        for attr, value in values.items():
            setattr(self, attr, value)
        self.unread_fields: set[str] = set()


# The reporter's actual reading, from registers 92/93 on an SPF with no generator attached.
GARBAGE_KWH = 135_777_726.3
SPIKE_ATTR = "generator_discharge_today"


def _is_published(data, attr):
    """What the sensor would actually report.

    `sensor.py` checks `unread_fields` before reading the attribute and returns None when
    the name is listed, so withholding does not require overwriting the value - matching
    `_set_from_register`, which also leaves the field alone when a read fails.
    """
    return attr not in data.unread_fields


def test_a_rejected_spike_is_not_published():
    """THE regression. The old code left `data` untouched and listed nothing as unread,
    so the sensor received the spike and it entered long-term statistics."""
    logger = _Logger()
    guard = _load_guard(logger)
    coordinator = _Coordinator()
    data = _Data(**{SPIKE_ATTR: GARBAGE_KWH})

    guard(coordinator, data)

    assert not (_is_published(data, SPIKE_ATTR) and getattr(data, SPIKE_ATTR) == GARBAGE_KWH), (
        "the rejected value reached the sensor - the guard keeps it out of retention but "
        "not out of Home Assistant"
    )


def test_with_no_good_value_to_fall_back_on_it_reports_nothing():
    """A gap is honest; a number the inverter never meaningfully produced is not (#384)."""
    logger = _Logger()
    guard = _load_guard(logger)
    data = _Data(**{SPIKE_ATTR: GARBAGE_KWH})

    guard(_Coordinator(), data)

    assert SPIKE_ATTR in data.unread_fields, (
        "with no retained value the attribute should be withheld so the sensor reads "
        "unknown"
    )


def test_the_last_real_value_is_preferred_over_a_gap():
    """A counter that was reading 12.4 kWh and glitches should hold 12.4, not vanish."""
    logger = _Logger()
    guard = _load_guard(logger)
    data = _Data(**{SPIKE_ATTR: GARBAGE_KWH})

    guard(_Coordinator(retained_daily={SPIKE_ATTR: 12.4}), data)

    assert getattr(data, SPIKE_ATTR) == 12.4
    assert SPIKE_ATTR not in data.unread_fields


def test_a_good_value_is_still_passed_through_untouched():
    """Guard against over-correcting: normal readings must be unaffected."""
    logger = _Logger()
    guard = _load_guard(logger)
    data = _Data(**{SPIKE_ATTR: 3.2})

    guard(_Coordinator(retained_daily={SPIKE_ATTR: 3.1}), data)

    assert getattr(data, SPIKE_ATTR) == 3.2
    assert not data.unread_fields
    assert logger.warnings == []


def test_it_warns_once_and_then_drops_to_debug():
    """The condition persists for every poll of a session when a register is never
    populated. One reporter's error log carried this line every 62 seconds indefinitely,
    which reads as a fault rather than as a guard doing its job."""
    logger = _Logger()
    guard = _load_guard(logger)
    coordinator = _Coordinator()

    for _ in range(5):
        guard(coordinator, _Data(**{SPIKE_ATTR: GARBAGE_KWH}))

    assert len(logger.warnings) == 1, (
        f"expected one warning across five polls, got {len(logger.warnings)}"
    )
    assert len(logger.debugs) >= 4, "subsequent occurrences should still be recorded at debug"


def test_a_different_attribute_gets_its_own_warning():
    """Warn-once is per attribute — silencing one counter must not silence another."""
    logger = _Logger()
    guard = _load_guard(logger)
    coordinator = _Coordinator()

    guard(coordinator, _Data(**{SPIKE_ATTR: GARBAGE_KWH}))
    guard(coordinator, _Data(energy_today=99_999.0))

    assert len(logger.warnings) == 2


def test_the_attributes_under_test_are_really_shipped():
    """Rule 4: absence of evidence needs the evidence to have been possible. If these
    names stopped being tracked, every assertion above would pass without exercising
    anything."""
    assert SPIKE_ATTR in CONST.DAILY_TOTAL_ATTRS
    assert "energy_today" in CONST.DAILY_TOTAL_ATTRS
