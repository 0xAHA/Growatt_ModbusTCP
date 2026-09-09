"""A silent current register is not a dissenting one (#430, guarding #406).

The battery power scale on WIT is auto-detected by comparing the power register against
voltage x current. That is only meaningful if the current is right, so #406 added a
precondition: if the several registers claiming to be battery current disagree with each
other, infer nothing and use the profile's documented scale.

The precondition counted a register reading `0.0` as disagreement. On a WIT 4-15kW that is
permanent, not momentary:

    reg 31215 (VPP)   -0.1 A      never carries current on this model
    reg 3170  (3k)     0.0 A      never carries current on this model
    reg 8035  (base)  34.1 A      the real reading, and the one selected

So the candidates could never agree while discharging, the detector was blocked on every
poll for the life of the connection, and the documented 0.1 scale stood - which is wrong on
that unit. Battery power published ~180 W against a measured ~1.8 kW, a tenth of the truth,
and the reporter rolled production back to v1.8.14.

Both reporters' actual numbers are used below, because the fix has to satisfy them at once:
#430 must now detect, and #406 must still be refused. Anything that only checks one of them
would have passed at every point in this bug's history.
"""
from __future__ import annotations

import ast
import sys
import types
from pathlib import Path

import pytest

COMPONENT = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
SOURCE = (COMPONENT / "growatt_modbus.py").read_text(encoding="utf-8")

# @KevlarD-67's WIT, 2026-09-09, steady ~35 A discharge. Two dead registers, one real.
WIT_430_CANDIDATES = [-0.1, 34.1, 0.0]
# The #406 reporter's inverter: two registers each claiming a real current, contradicting.
WIT_406_CANDIDATES = [-0.1, 6.3, -4.3]


def _load():
    """Extract the agreement helper and the module constants it reads."""
    tree = ast.parse(SOURCE)
    fn = next(
        node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "_candidates_agree"
    )
    fn.decorator_list = []          # @staticmethod is applied on the stub instead

    constants = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.startswith("_BATTERY"):
                    constants[target.id] = node.value.value
    assert "_BATTERY_CURRENT_SILENT_A" in constants, (
        "the silent-register threshold is gone; agreement is judging dead registers again"
    )

    module = types.ModuleType("_agree")
    module.__dict__.update(constants)
    exec(compile(ast.Module(body=[fn], type_ignores=[]), "<agree>", "exec"), module.__dict__)
    return module._candidates_agree, constants


agree, CONSTANTS = _load()


def test_two_silent_registers_do_not_block_the_one_that_works():
    """THE regression. This is the exact set from the reporter's log under load."""
    assert agree(WIT_430_CANDIDATES), (
        "a register sitting at 0.0 is still being counted as disagreement, so the scale "
        "detector stays blocked and battery power keeps publishing a tenth of the truth"
    )


def test_the_406_case_is_still_refused():
    """The guard this precondition was built for, and the reason the fix is narrow.

    Two registers each reporting a real current in opposite directions is genuine conflict.
    Discarding the near-zero candidate leaves 6.3 A against -4.3 A, which must still be
    rejected - inferring a scale from either would repeat #406.
    """
    assert not agree(WIT_406_CANDIDATES), (
        "contradicting real currents are being treated as agreement; this is the input that "
        "produced 40 kW readings on a 6.5 kW battery"
    )


def test_conflicting_magnitudes_still_disagree():
    """Same direction is not enough - an order-of-magnitude gap is still conflict."""
    assert not agree([2.0, 45.0])


def test_readings_of_the_same_size_agree():
    """Guard against over-correcting: two registers that do carry the same current, with
    ordinary measurement scatter between them, must still validate."""
    assert agree([34.1, 34.4])
    assert agree([-12.0, -12.3])


def test_an_idle_battery_agrees_but_cannot_latch_a_scale():
    """With everything near zero there is nothing to contradict, so this returns True - and
    that is safe only because detection is separately gated on real load. If that threshold
    ever goes, an idle battery could latch a scale from noise, which is how #406 happened."""
    assert agree([0.0, -0.1, 0.05])
    assert CONSTANTS["_BATTERY_SCALE_MIN_POWER_W"] >= 500.0, (
        "the real-load gate has been lowered; the idle case above is no longer safe"
    )


def test_a_single_candidate_agrees_with_itself():
    assert agree([34.1])
    assert agree([])


def test_the_silent_threshold_stays_small():
    """It must exclude a dead register at 0.0 or -0.1 without swallowing a real low current.
    A battery trickling at 1 A is reporting; one at 0.1 A is not distinguishable from off."""
    threshold = CONSTANTS["_BATTERY_CURRENT_SILENT_A"]

    assert 0.0 < threshold <= 0.5, f"silent threshold {threshold} is outside a sane range"
    assert threshold < 1.0, "a 1 A reading would be discarded as silence"


@pytest.mark.parametrize("candidates,expected", [
    (WIT_430_CANDIDATES, True),
    (WIT_406_CANDIDATES, False),
])
def test_the_two_reporters_land_on_opposite_answers(candidates, expected):
    """Stated as one assertion because it is the whole point: the fix is only correct if it
    separates these two, and either one alone can be satisfied by the wrong change."""
    assert agree(candidates) is expected
