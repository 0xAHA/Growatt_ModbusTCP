"""The validated battery power scale survives a rebuilt client (#434).

A WIT 15K owner's Elfin EW11 drops idle connections. Something rebuilds the Modbus client
around those drops, and because the detected scale is instance state it goes back to None,
so the profile's documented 0.1 stands again on hardware whose register is already in
watts. His CSV caught it twice in one afternoon, either side of the detector's 500 W gate:

    13:09:31  1648 W        correct (x1.0)
    13:10:35  unavailable   <- connection dropped
    13:10:38   168 W        /10
    13:12:50  1664 W        correct again - above the gate, detection re-ran

    14:01:16   477 W        correct (x1.0)
    14:02:50  unavailable   <- connection dropped
    14:02:56  39.7 W        /10
    14:05:08  45.5 W        /10 ... and stays there

Below the gate the detector cannot run, so the tenth persists until load rises. Overnight
it never does. That is the whole of #434: not "it latched the wrong scale" but "it lost the
right one and could not re-earn it while gated".

Two rules carried over from #406, where a bad detection at low load latched the wrong scale
and produced 40 kW readings on a 6.5 kW battery:

  * only a fully validated scale is ever stored - never a restored one
  * a restored scale does not end detection, so real load can still overrule it
"""

from __future__ import annotations

import ast
import importlib
from pathlib import Path

import pytest

_gm = importlib.import_module("growatt_under_test.growatt_modbus")

COMPONENT = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"


def _client(documented=0.1):
    c = _gm.GrowattModbus.__new__(_gm.GrowattModbus)
    c._battery_power_scale_validated = False
    c._battery_power_scale_override = None
    c._battery_power_scale_samples = []
    c._battery_power_scale_input_warned = False
    c._battery_power_scale_disputed = False
    c._battery_power_scale_disputed_warned = False
    c._battery_power_scale_restored = False
    c._battery_current_candidates_agree = True
    c._documented_battery_power_scale = lambda: documented
    return c


def _validate(c, scale_is_one=True):
    """Drive three consistent samples at real load. Wojak129's own figures."""
    for _ in range(3):
        # 54.1 V x 41.1 A = 2224 W. Raw 2220 reads 222 W at 0.1 and 2220 W at 1.0.
        c._detect_battery_power_scale(54.1, 41.1, 2220)
    return c._battery_power_scale_override


# ---------------------------------------------------------------------------
# What may be stored
# ---------------------------------------------------------------------------

def test_a_validated_scale_is_offered_for_storage():
    c = _client()
    assert _validate(c) == 1.0
    assert c.validated_battery_power_scale == 1.0


def test_nothing_is_offered_before_validation():
    c = _client()
    assert c.validated_battery_power_scale is None
    c._detect_battery_power_scale(54.1, 41.1, 2220)  # one sample, not three
    assert c.validated_battery_power_scale is None


def test_a_restored_scale_is_not_offered_for_storage_again():
    """Otherwise a mis-detection copies itself forward for ever and #406 becomes
    permanent rather than clearing on the next restart."""
    c = _client()
    c.restore_battery_power_scale(1.0)
    assert c._battery_power_scale_override == 1.0
    assert c.validated_battery_power_scale is None


def test_a_nonsense_stored_value_is_ignored():
    c = _client()
    c.restore_battery_power_scale(0.5)
    assert c._battery_power_scale_override is None


# ---------------------------------------------------------------------------
# What a restored scale does and does not do
# ---------------------------------------------------------------------------

def test_restoring_puts_the_scale_straight_back_in_force():
    """THE fix. After the drop the override is None and 477 W reads as 39.7 W; with the
    scale restored at setup it is in force from the first poll, with no load requirement."""
    c = _client()
    c.restore_battery_power_scale(1.0)
    assert c._battery_power_scale_override == 1.0


def test_restoring_does_not_end_detection():
    c = _client()
    c.restore_battery_power_scale(1.0)
    assert c._battery_power_scale_validated is False


def test_real_load_can_overrule_a_wrongly_restored_scale():
    """The escape hatch. A stored 1.0 on hardware that wants 0.1 is corrected the next
    time the battery works hard enough for the detector to run."""
    c = _client()
    c.restore_battery_power_scale(1.0)
    for _ in range(3):
        # 53.2 V x 40 A = 2128 W; raw 21280 is 2128 W at 0.1, 21280 W at 1.0
        c._detect_battery_power_scale(53.2, 40.0, 21280)
    assert c._battery_power_scale_override == 0.1
    assert c.validated_battery_power_scale == 0.1, "the correction must be stored too"


# ---------------------------------------------------------------------------
# Withholding a reading the arithmetic has just contradicted
# ---------------------------------------------------------------------------

def test_a_contradiction_is_flagged_before_the_override_commits():
    """His 12:25:19: first poll of a session, 42.7 A at 54.1 V, register 2300 published as
    230 W because the documented 0.1 stood while detection waited for three samples."""
    c = _client(documented=0.1)
    c._detect_battery_power_scale(54.1, 42.7, 2310)
    assert c._battery_power_scale_disputed is True


def test_agreement_with_the_documented_scale_is_not_a_dispute():
    """The 95%+ of WIT owners for whom 0.1 is right must not lose their sensor."""
    c = _client(documented=0.1)
    c._detect_battery_power_scale(53.2, 40.0, 21280)
    assert c._battery_power_scale_disputed is False


def test_the_dispute_clears_once_the_scale_is_validated():
    c = _client(documented=0.1)
    _validate(c)
    assert c._battery_power_scale_disputed is False


def test_nothing_is_disputed_below_the_load_gate():
    """8.2 A x 52.5 V = 430 W, under the 500 W gate. Detection must not run, so it cannot
    contradict anything - which is why persistence rather than detection is the cure for
    the overnight case."""
    c = _client(documented=0.1)
    c._detect_battery_power_scale(52.5, 8.2, 4300)
    assert c._battery_power_scale_disputed is False


def test_nothing_is_disputed_when_the_current_registers_disagree():
    """#406's owner must keep a battery power sensor. Detection refuses there, so there is
    never positive evidence of a contradiction and the documented scale still publishes."""
    c = _client(documented=0.1)
    c._battery_current_candidates_agree = False
    c._detect_battery_power_scale(53.5, 2.7, 1590)
    assert c._battery_power_scale_disputed is False


def test_the_decode_withholds_a_disputed_reading():
    source = (COMPONENT / "growatt_modbus.py").read_text(encoding="utf-8")
    assert "elif self._battery_power_scale_disputed:" in source, (
        "battery power is still published while its scale is contradicted"
    )
    marker = source.index("elif self._battery_power_scale_disputed:")
    block = source[marker:marker + 900]
    for field in ("battery_power", "charge_power", "discharge_power"):
        assert field in block, (
            f"{field} is not marked unread, so it would publish 0 and look like an idle "
            "battery rather than an unknown one (#384)"
        )


# ---------------------------------------------------------------------------
# The coordinator side
# ---------------------------------------------------------------------------

def _coordinator_source() -> str:
    return (COMPONENT / "coordinator.py").read_text(encoding="utf-8")


def test_the_scale_is_restored_at_setup():
    """Setup is what runs again after a reload, so whatever rebuilds the client, the
    scale comes back with it."""
    source = _coordinator_source()
    tree = ast.parse(source)
    loader = next(
        node for node in ast.walk(tree)
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "_async_load_energy_totals"
    )
    body = ast.get_source_segment(source, loader) or ""
    assert "_restore_battery_power_scale" in body


def test_a_stored_scale_from_another_profile_is_discarded():
    """A scale validated against one register map means nothing for another."""
    source = _coordinator_source()
    tree = ast.parse(source)
    fn = next(
        node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "_restore_battery_power_scale"
    )
    body = ast.get_source_segment(source, fn) or ""
    assert "battery_power_scale_profile" in body
    assert "return" in body


def test_only_a_validated_scale_reaches_storage():
    source = _coordinator_source()
    tree = ast.parse(source)
    fn = next(
        node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "_note_validated_battery_power_scale"
    )
    body = ast.get_source_segment(source, fn) or ""
    assert "validated_battery_power_scale" in body, (
        "the coordinator reads the raw override rather than the validated-only property, "
        "so a restored scale would be written back as if it had been confirmed"
    )


def test_the_scale_rides_the_existing_energy_write():
    """A second store file would double the disk traffic to persist one float."""
    source = _coordinator_source()
    tree = ast.parse(source)
    fn = next(
        node for node in ast.walk(tree)
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "_async_save_energy_totals"
    )
    body = ast.get_source_segment(source, fn) or ""
    assert "battery_power_scale" in body
    assert "battery_power_scale_profile" in body
