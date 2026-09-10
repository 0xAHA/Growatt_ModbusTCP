"""Grid orientation detection must not report an unread inverter as 0 W of sun (#432).

A reporter set up a serial entry while another Growatt integration was already using the same
USB adapter. A serial port opens for one program at a time, so this integration never had a
single successful read. He ran `growatt_modbus.detect_grid_orientation` in full sun, with his
panels making over a kilowatt, and was told:

    Grid Orientation Detection: Insufficient Solar
    Current solar production: 0 W
    Please try again when: the sun is shining

Every number in that message was manufactured by the absence of data. `coordinator.data` is an
empty `GrowattData()` placeholder until the first successful poll, and a dataclass instance is
truthy - so the `if not coordinator.data` guard above it passed, every field read its 0.0
default, and the check for "enough sun" did the rest. It sent him to look at the weather.

This is the #384 defect in a new place: a failed read presented as a measurement. Both copies
of the detection carry it - the one in `diagnostic.py` behind the action, and the one in
`config_flow.py` that runs at setup - so both are checked here. v1.3.5 shipped a fix to one of
two paths and the other raised on every poll; that is the reason for the second half of this
file rather than a single test.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

COMPONENT = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
DIAGNOSTIC = (COMPONENT / "diagnostic.py").read_text(encoding="utf-8")
CONFIG_FLOW = (COMPONENT / "config_flow.py").read_text(encoding="utf-8")


def test_the_action_checks_for_real_data_before_judging_the_sun():
    """THE regression. The gate has to come before the production threshold, or the
    'Insufficient Solar' branch answers first - which is what happened."""
    assert "coordinator.has_real_data" in DIAGNOSTIC, (
        "the action no longer distinguishes 'never read' from 'no production', so an "
        "inverter that has never answered is reported as 0 W of solar"
    )

    gate = DIAGNOSTIC.index("coordinator.has_real_data")
    threshold = DIAGNOSTIC.index("Insufficient Solar")
    assert gate < threshold, (
        "the real-data check runs after the solar threshold, so an unread inverter still "
        "gets told to try again when the sun is shining"
    )


def test_the_action_names_the_held_port_among_the_causes():
    """The cause that produced this report is invisible from inside Home Assistant - two
    integrations, one adapter, and the other one working perfectly."""
    message = DIAGNOSTIC[DIAGNOSTIC.index("coordinator.has_real_data"):][:1600]
    assert "serial port" in message and "one at a time" in message, (
        "the failure message does not mention another program holding the adapter"
    )


def test_the_action_says_it_is_not_a_reading_of_zero():
    message = DIAGNOSTIC[DIAGNOSTIC.index("coordinator.has_real_data"):][:1600]
    assert "not** a reading of zero" in message or "not a reading of zero" in message, (
        "the message does not say that zero here means 'unread' rather than 'none'"
    )


def test_the_setup_path_has_the_same_gate():
    """The copy in config_flow.py runs during setup, where its `if not data` check has the
    same hole: a poll where nothing answered still returns an object."""
    detector = CONFIG_FLOW[CONFIG_FLOW.index("def _detect_grid_orientation"):]
    detector = detector[:detector.index("\ndef ")] if "\ndef " in detector else detector

    assert "unread_fields" in detector, (
        "setup-time detection does not check whether anything was actually read, so it "
        "reports 'solar production too low (0W)' for an inverter that never replied"
    )

    gate = detector.index("unread_fields")
    threshold = detector.index("too low to tell")
    assert gate < threshold, "the unread check runs after the production threshold"


def test_both_detectors_still_report_a_genuine_low_reading_normally():
    """Guard against over-correcting. A real inverter reading a real 200 W must still get
    the 'not enough sun' answer - the new branch is only for having read nothing at all."""
    for source, marker in ((DIAGNOSTIC, "Insufficient Solar"),
                           (CONFIG_FLOW, "too low to tell")):
        assert marker in source, (
            f"the genuine low-production message was removed along with the fix; a user in "
            f"weak sun now gets no explanation at all"
        )


def test_the_setup_gate_requires_unread_fields_not_just_zeros():
    """An inverter genuinely producing nothing at night reads real zeros with nothing marked
    unread. Keying the new branch on zeros alone would tell that user their inverter never
    answered, which is its own wrong answer."""
    detector = CONFIG_FLOW[CONFIG_FLOW.index("def _detect_grid_orientation"):]
    window = detector[detector.index("unread_fields") - 200:detector.index("unread_fields") + 400]

    assert "getattr(data, \"unread_fields\", None)" in window or \
           "getattr(data, 'unread_fields', None)" in window, (
        "the gate does not require unread fields, so a genuine night-time zero would be "
        "reported as a connection failure"
    )


def test_the_component_still_parses():
    """These edits are inside long service handlers; a syntax error would only show up when
    the action is called."""
    ast.parse(DIAGNOSTIC)
    ast.parse(CONFIG_FLOW)
