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
_const = importlib.import_module("growatt_under_test.const")

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


# The decode's withholding is tested in test_withheld_battery_is_unknown.py, by running
# the read path and handing its output to the sensors.
#
# A test used to live here that read growatt_modbus.py and confirmed the withholding branch
# marked the fields unread. It did, and the test passed throughout the bug it was meant to
# prevent: Battery Power is a calculated sensor that never consulted those marks, and
# published 0 W at two withheld polls on the reporter's WIT. Checking that a value is
# flagged says nothing about whether anything reads the flag (#434).


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


def test_the_coordinator_uses_the_shared_decision():
    """The rules below are only worth testing if the coordinator actually runs them."""
    source = _coordinator_source()
    assert "battery_power_scale_from_store" in source
    assert "battery_power_scale_into_payload" in source


def test_a_skipped_restore_is_reported_at_info():
    """A reporter whose scale did not come back must be able to say which branch fired
    without being asked to enable debug and restart again (#434)."""
    source = _coordinator_source()
    tree = ast.parse(source)
    fn = next(
        node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "_restore_battery_power_scale"
    )
    body = ast.get_source_segment(source, fn) or ""
    assert "_LOGGER.info" in body and "reason" in body


# ---------------------------------------------------------------------------
# The store round trip, run rather than read
#
# The tests above check that the coordinator calls the right things. They cannot check
# what those things decide, because coordinator.py imports Home Assistant and this suite
# does not - which is why the decision lives in const.py. Three source-level tests stood
# here through a restore that did not fire on a reporter's inverter (#434); these run it.
# ---------------------------------------------------------------------------

PROFILE = "WIT 4-15kW Hybrid"


def _saved(scale, profile=PROFILE, previous=None):
    """A payload as _async_save_energy_totals would write it."""
    payload = {"lifetime_totals": {"energy_total": 1234.5}, "daily_totals": {},
               "daily_totals_date": "2026-09-16"}
    return _const.battery_power_scale_into_payload(payload, scale, profile, previous=previous)


def test_a_saved_scale_comes_back():
    """THE round trip. Save 1.0, load it, get 1.0."""
    stored = _saved(1.0)
    scale, reason = _const.battery_power_scale_from_store(stored, PROFILE)
    assert scale == 1.0, reason


def test_a_save_with_nothing_in_hand_keeps_what_is_already_stored():
    """THE wipe. Every save rebuilds the payload, so a write in a session that has not
    restored yet used to drop the stored scale permanently - and the next restart then had
    nothing to restore, which is what a reporter saw after upgrading."""
    already = _saved(1.0)
    rewritten = _saved(None, previous=already)

    scale, reason = _const.battery_power_scale_from_store(rewritten, PROFILE)
    assert scale == 1.0, f"the stored scale was dropped by a later save: {reason}"


def test_a_save_with_nothing_stored_and_nothing_in_hand_writes_nothing():
    payload = _saved(None, previous=None)
    assert _const.BATTERY_SCALE_STORE_KEY not in payload


def test_a_new_scale_overwrites_the_carried_one():
    already = _saved(1.0)
    rewritten = _saved(0.1, previous=already)
    assert _const.battery_power_scale_from_store(rewritten, PROFILE)[0] == 0.1


def test_a_scale_from_another_profile_is_refused_and_says_so():
    stored = _saved(1.0, profile="SPH-TL3 Series 3-10kW (V2.01)")
    scale, reason = _const.battery_power_scale_from_store(stored, PROFILE)
    assert scale is None
    assert "SPH-TL3" in reason and PROFILE in reason, reason


def test_nothing_stored_says_so():
    scale, reason = _const.battery_power_scale_from_store({"lifetime_totals": {}}, PROFILE)
    assert scale is None
    assert "no scale" in reason


def test_an_empty_store_says_so():
    scale, reason = _const.battery_power_scale_from_store(None, PROFILE)
    assert scale is None
    assert "no stored data" in reason


@pytest.mark.parametrize("junk", ["1.0", None, True, 0.5, 10, [], {}])
def test_only_a_scale_this_integration_writes_is_accepted(junk):
    """0.1 and 1.0 are the only two the detector can validate. A bool would otherwise
    arrive as 1.0, because bool is a subclass of int."""
    stored = {_const.BATTERY_SCALE_STORE_KEY: junk,
              _const.BATTERY_SCALE_PROFILE_KEY: PROFILE}
    assert _const.battery_power_scale_from_store(stored, PROFILE)[0] is None


def test_a_restored_scale_reaches_the_client_unchanged():
    """End to end: what comes out of the store is what the client adopts, and it stays
    open to correction by real load."""
    scale, _ = _const.battery_power_scale_from_store(_saved(1.0), PROFILE)
    client = _client()
    client.restore_battery_power_scale(scale)
    assert client._battery_power_scale_override == 1.0
    assert client.validated_battery_power_scale is None
