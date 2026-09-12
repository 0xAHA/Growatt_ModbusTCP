"""Device identification stops asking once it has learned something (#438).

`_read_device_identification()` makes six holding reads - serial, firmware, inverter type,
protocol version. It is meant to run once per session, and both callers gated it on
`not self._serial_number`.

On hardware whose serial register answers with an **empty string** that condition is never
satisfied. From a WIT capture, one hour, debug on:

    56  Finished fetching ... (success: True)
    56  Inverter identified - model: WIT 4-15kW Hybrid | serial: unknown | firmware: YE1.0
    56  Read serial number:            <- empty, every time

Six reads x 56 polls is over three hundred holding reads an hour that had already been
answered, on an Elfin EW11 that was dropping connections - and every extra read is another
chance to hit the transport error the owner was chasing. It is also the same method whose
reads opened the orphan socket in #426, so it is not a path to run more often than needed.

The fix gates on whether anything was learned rather than on the serial specifically. The
distinction matters in both directions and this file pins both:

  * an inverter **asleep** at the first attempt answers none of the six, learns nothing,
    and must be asked again - that is what the original guard was protecting
  * one that answers **some** of them has said what it is going to say. Asking again every
    poll for the rest of the session buys a serial number that is never coming
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

COMPONENT = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
SOURCE = (COMPONENT / "coordinator.py").read_text(encoding="utf-8")


def _identification() -> ast.FunctionDef:
    return next(
        node for node in ast.walk(ast.parse(SOURCE))
        if isinstance(node, ast.FunctionDef) and node.name == "_read_device_identification"
    )


def test_no_caller_gates_on_the_serial_number():
    """THE regression. A blank serial made this condition permanently true."""
    assert "if not self._serial_number:" not in SOURCE, (
        "a caller still gates identification on the serial number, so hardware that "
        "answers it blank re-reads all six registers on every poll for ever"
    )


def test_both_callers_gate_on_the_completion_flag():
    """Two call sites - the shared path and the direct path. v1.3.5 shipped a fix to one
    of two fetch paths and the other raised on every poll."""
    assert SOURCE.count("if not self._identification_complete:") == 2, (
        f"expected two gated callers, found "
        f"{SOURCE.count('if not self._identification_complete:')}"
    )


def test_the_flag_starts_false():
    """Otherwise identification never runs at all and the device info stays empty."""
    assert "self._identification_complete = False" in SOURCE


def test_the_flag_is_set_from_what_was_learned_not_from_the_serial():
    body = ast.unparse(_identification())

    assert "self._identification_complete = any(" in body, (
        "the completion flag is no longer derived from what was read"
    )
    for field in ("self._serial_number", "self._firmware_version",
                  "self._inverter_type", "self._protocol_version"):
        assert field in body.split("_identification_complete = any(")[1][:400], (
            f"{field} is not counted towards identification being complete"
        )


def test_learning_nothing_leaves_it_incomplete():
    """The case the original guard existed for: an inverter asleep at the first poll
    answers none of the six and must be asked again when it wakes.

    Evaluated against the real expression rather than a reimplementation of it.
    """
    body = ast.unparse(_identification())
    expression = "any((" + body.split("_identification_complete = any((")[1].split("))")[0] + "))"

    class _Coordinator:
        _serial_number = None
        _firmware_version = None
        _inverter_type = None
        _protocol_version = None

    assert eval(expression, {}, {"self": _Coordinator()}) is False, (
        "an inverter that answered nothing is treated as identified, so it is never "
        "asked again and its model, firmware and protocol stay unknown for the session"
    )


@pytest.mark.parametrize("learned", [
    "_serial_number", "_firmware_version", "_inverter_type", "_protocol_version",
])
def test_learning_any_one_thing_completes_it(learned):
    """The reporter's case is `_firmware_version` alone: serial blank, firmware YE1.0.
    Any single answer is enough to stop asking."""
    body = ast.unparse(_identification())
    expression = "any((" + body.split("_identification_complete = any((")[1].split("))")[0] + "))"

    class _Coordinator:
        _serial_number = None
        _firmware_version = None
        _inverter_type = None
        _protocol_version = None

    coordinator = _Coordinator()
    setattr(coordinator, learned, "YE1.0")

    assert eval(expression, {}, {"self": coordinator}) is True, (
        f"{learned} was read but identification would still repeat every poll"
    )


def test_a_blank_serial_does_not_count_as_learned():
    """The exact value the reporter's inverter returns. An empty string is falsy, which is
    why the old guard failed - the flag must not be fooled by it either."""
    body = ast.unparse(_identification())
    expression = "any((" + body.split("_identification_complete = any((")[1].split("))")[0] + "))"

    class _Coordinator:
        _serial_number = ""          # what register 23/3000 answers on that WIT
        _firmware_version = None
        _inverter_type = None
        _protocol_version = None

    assert eval(expression, {}, {"self": _Coordinator()}) is False
