"""Withholding a PV zero the inverter's own registers contradict (#384).

An off-grid SPF intermittently reports 0 in its PV registers while still producing. This is
not a failed read: the block arrives complete, the registers are present, their contents are
zero. The reporter's poll showed

    Successfully read 98 registers from 0
    AC Power from reg 10: 1907.0W
    Battery power (signed): -329.0W
    Read data: PV=0.0W

with grid voltage, AC input power and generator power all zero. 1,907 W was leaving the
inverter, 329 W came from the battery, and the missing ~1,578 W had nowhere to come from but
the panels. PV was not zero.

The real figure is unrecoverable — it is not in the response — but publishing zero writes a
fabricated measurement into long-term statistics, and misleads the SPF sign correction,
which compares PV against load and concluded from a false PV=0 that the battery must be
discharging.

Most of these tests are about **not** firing. Suppressing a genuine zero would be a worse
bug than the one being fixed, so the conditions are deliberately narrow.
"""
from __future__ import annotations

import importlib

import pytest

_gm = importlib.import_module("growatt_under_test.growatt_modbus")


def _client(offgrid=True):
    profile = "SPF_3000_6000_ES_PLUS" if offgrid else "SPH_3000_6000"
    client = _gm.GrowattModbus(connection_type="tcp", host="10.0.0.1", port=502,
                               register_map=profile)
    return client


def _data(**kw):
    data = _gm.GrowattData()
    for key, value in kw.items():
        setattr(data, key, value)
    return data


PV_FIELDS = ("pv_total_power", "pv1_power", "pv2_power", "pv3_power", "pv4_power")


# --------------------------------------------------------------------------
# The reported case
# --------------------------------------------------------------------------

def test_the_reporters_poll_is_suppressed():
    """1907 W out, 329 W from the battery, nothing else — PV cannot be zero."""
    client = _client()
    data = _data(pv_total_power=0.0, ac_power=1907.0, discharge_power=329.0)

    client._suppress_impossible_pv_zero(data)

    for field in PV_FIELDS:
        assert field in data.unread_fields, f"{field} was published as a real zero"


def test_the_field_keeps_a_usable_number():
    """Several fields are summed elsewhere, so the value stays 0.0 and only the unread flag
    changes — the same contract as a failed read."""
    client = _client()
    data = _data(pv_total_power=0.0, ac_power=1907.0, discharge_power=329.0)
    client._suppress_impossible_pv_zero(data)
    assert data.pv_total_power == 0.0
    assert isinstance(data.pv_total_power, float)


# --------------------------------------------------------------------------
# Must NOT fire — a suppressed genuine zero is worse than the bug
# --------------------------------------------------------------------------

def test_night_time_is_not_suppressed():
    """No output, no PV. The commonest genuine zero there is."""
    client = _client()
    data = _data(pv_total_power=0.0, ac_power=0.0, discharge_power=0.0)
    client._suppress_impossible_pv_zero(data)
    assert not data.unread_fields


def test_a_battery_carrying_the_whole_load_is_not_suppressed():
    """After dark the battery runs the house and PV is legitimately zero."""
    client = _client()
    data = _data(pv_total_power=0.0, ac_power=1900.0, discharge_power=1900.0)
    client._suppress_impossible_pv_zero(data)
    assert not data.unread_fields


def test_grid_passthrough_is_not_suppressed():
    """An SPF has an AC input. If the grid is carrying the load, PV need not be producing."""
    client = _client()
    data = _data(pv_total_power=0.0, ac_power=1900.0, ac_input_power=1900.0)
    client._suppress_impossible_pv_zero(data)
    assert not data.unread_fields


def test_generator_supply_is_not_suppressed():
    client = _client()
    data = _data(pv_total_power=0.0, ac_power=1900.0, generator_power=1900.0)
    client._suppress_impossible_pv_zero(data)
    assert not data.unread_fields


def test_a_small_shortfall_is_not_suppressed():
    """Measurement noise and conversion losses put a little daylight between output and
    sources. Below the margin it proves nothing."""
    client = _client()
    data = _data(pv_total_power=0.0, ac_power=1000.0, discharge_power=900.0)
    client._suppress_impossible_pv_zero(data)
    assert not data.unread_fields, "a 100 W gap was treated as proof"


def test_a_nonzero_pv_reading_is_never_touched():
    """Real curtailment produces a low but non-zero figure, and we have no basis to
    second-guess it."""
    client = _client()
    data = _data(pv_total_power=5.0, ac_power=1907.0, discharge_power=329.0)
    client._suppress_impossible_pv_zero(data)
    assert not data.unread_fields


def test_grid_tied_profiles_are_left_alone():
    """On a grid-tied hybrid the load can be met from the grid without that appearing in any
    register we read, so the balance is not conclusive."""
    client = _client(offgrid=False)
    data = _data(pv_total_power=0.0, ac_power=1907.0, discharge_power=329.0)
    client._suppress_impossible_pv_zero(data)
    assert not data.unread_fields


# --------------------------------------------------------------------------
# Wiring
# --------------------------------------------------------------------------

def test_it_runs_as_part_of_a_poll():
    """A helper nothing calls is decoration — this project has shipped that before."""
    from pathlib import Path

    source = (Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
              / "growatt_modbus.py").read_text(encoding="utf-8")
    assert "self._suppress_impossible_pv_zero(data)" in source
    assert source.index("self._suppress_impossible_pv_zero(data)") < source.index(
        'logger.debug(f"Read data: PV='
    ), "the check runs after the poll has already reported its values"


def test_the_margin_matches_the_sign_correction():
    """Both do power-balance reasoning on the same inverter. Disagreeing about what counts
    as a significant difference would let one fire while the other does not."""
    client = _client()
    assert client.PV_ZERO_BALANCE_MARGIN == 200.0


def test_the_suppression_warns_once_then_drops_to_debug(caplog):
    """The condition is a firmware fault we cannot cure, so one line tells the user their
    inverter does it and every further line is noise. The frequency is unbounded - nine in
    three days on the reporting hardware, but nothing stops a worse unit doing it on every
    poll, and it lands in Home Assistant's error log under "originated from a custom
    integration" (#384)."""
    import logging

    client = _client()
    with caplog.at_level(logging.DEBUG):
        for _ in range(6):
            data = _data(pv_total_power=0.0, ac_power=1907.0, discharge_power=329.0)
            client._suppress_impossible_pv_zero(data)

    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    debugs = [r for r in caplog.records
              if r.levelno == logging.DEBUG and "Impossible PV zero" in r.getMessage()]

    assert len(warnings) == 1, f"expected one warning across six suppressions, got {len(warnings)}"
    assert len(debugs) == 5, f"expected five debug lines, got {len(debugs)}"
    assert "further occurrences are logged at debug" in warnings[0].getMessage(), (
        "the warning does not tell the user the rest are suppressed"
    )


def test_suppression_still_withholds_every_time_not_just_the_first(caplog):
    """Quieter logging must not mean a quieter fix - the reading is withheld on every poll
    where the inverter contradicts itself, regardless of what is logged."""
    client = _client()
    for _ in range(4):
        data = _data(pv_total_power=0.0, ac_power=1907.0, discharge_power=329.0)
        client._suppress_impossible_pv_zero(data)
        assert "pv1_power" in data.unread_fields
        assert "pv_total_power" in data.unread_fields
