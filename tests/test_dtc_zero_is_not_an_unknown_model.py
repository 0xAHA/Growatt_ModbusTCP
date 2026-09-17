"""An empty device type code is not an unsupported model (#449).

A MIN 5000TL-XH owner found this in their log after every restart, could never clear it,
and reasonably took it for a fault:

    WARNING  custom_components.growatt_modbus.auto_detection
    X DTC Detection - Unknown DTC code: 0 (not in supported models)

Their inverter is supported - DTC 5100 is CONFIRMED against issue #71. All that happened is
that holding register 30000 answered 0, which on that firmware it always will.

Both detection callers test `if dtc_code:` before calling, so a zero only ever arrives from
the once-per-session profile re-check in coordinator.py, which passes `int(regs[0])`
straight through. Reading 0 is "Read OK" with no value (CLAUDE.md rule 3) - it is not
evidence about the hardware, and must not be reported as a verdict on it.

These call the real function and read the log records it emits. The re-check itself is
source-checked in test_profile_recheck.py because the coordinator cannot be imported
without Home Assistant; this path can be, so it is tested by behaviour.
"""
from __future__ import annotations

import importlib
import logging

import pytest

_ad = importlib.import_module("growatt_under_test.auto_detection")

detect_profile_from_dtc = _ad.detect_profile_from_dtc
DTC_REGISTRY = _ad.DTC_REGISTRY

# Not in the registry, and not meant to be - the stand-in for a code we genuinely do not know.
UNKNOWN_CODE = 9999


def _warnings(caplog) -> list[str]:
    return [r.getMessage() for r in caplog.records if r.levelno >= logging.WARNING]


@pytest.mark.parametrize("empty", [0, None])
def test_an_empty_reading_is_not_called_an_unsupported_model(empty, caplog):
    """THE bug. Nothing above DEBUG may be said about a register that came back empty."""
    caplog.set_level(logging.DEBUG)

    assert detect_profile_from_dtc(empty) is None
    assert _warnings(caplog) == [], (
        f"an empty DTC ({empty!r}) is reported at WARNING, which is what #449 could not clear"
    )


@pytest.mark.parametrize("empty", [0, None])
def test_the_owners_model_is_never_named_as_unsupported(empty, caplog):
    """The wording is the harm, not the level: "not in supported models" is a claim about
    the inverter, and no such claim can be founded on an empty register."""
    caplog.set_level(logging.DEBUG)

    detect_profile_from_dtc(empty)
    assert not any("not in supported models" in m for m in caplog.messages)


def test_a_genuinely_unknown_code_still_warns(caplog):
    """The warning earns its place when a code was actually read and we cannot place it -
    that is a real gap in the registry and the user should find it in the log."""
    assert UNKNOWN_CODE not in DTC_REGISTRY, "pick a code that is genuinely unmapped"
    caplog.set_level(logging.DEBUG)

    assert detect_profile_from_dtc(UNKNOWN_CODE) is None
    assert any("not in supported models" in m for m in _warnings(caplog))


def test_a_known_code_is_unaffected(caplog):
    """Their own model, which is what the re-check exists to catch in the first place."""
    caplog.set_level(logging.DEBUG)

    assert detect_profile_from_dtc(5100) == "tl_xh_3000_10000_v201"
    assert not any("not in supported models" in m for m in caplog.messages)


def test_an_empty_reading_is_still_visible_at_debug(caplog):
    """Silencing it entirely would hide the one fact worth having when someone asks why no
    profile was suggested. Debug is where that belongs."""
    caplog.set_level(logging.DEBUG)

    detect_profile_from_dtc(0)
    assert any("device type code" in m.lower() for m in caplog.messages), (
        "an empty reading leaves no trace at all, so a support question cannot be answered"
    )
