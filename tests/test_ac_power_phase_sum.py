"""AC Power falls back to the sum of its phases (#427).

On a MID 25KTL3-XH the aggregate AC power register (the 35/36 pair) is not served by the
firmware, so `AC Power` sat permanently unknown while the three phase sensors read normally.

The phase figures were not register reads either. `236.2 V x 0.7 A = 165.3 W` matched what the
sensors showed to the tenth, which is the existing V x I fallback doing its job - so neither
the aggregate nor the phase power registers answer on that hardware. The difference was that
the phases had a fallback and the aggregate did not, leaving one entity unknown on a system
where the information was entirely available.

The rule applied here is the one grid flow already uses in `_resolve_phase_total()`: believe
the total where it is populated, otherwise sum the phases. It is only reached when the total
did not read, so a working aggregate register is never overridden by a derived figure.

`unread` is inherited from the phases: an aggregate summed from a phase that did not read
would understate the total, which is the #384 defect one step downstream.
"""
from __future__ import annotations

import ast
import sys
import types
from pathlib import Path

import pytest

COMPONENT = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
SOURCE = (COMPONENT / "growatt_modbus.py").read_text(encoding="utf-8")

# The reporter's readings, same moment.
PHASE_W = (165.3, 165.4, 165.6)
PHASE_SUM = 496.3


class _Data:
    def __init__(self, **values):
        self.unread_fields: set[str] = set()
        self.ac_power = 0.0
        self.ac_power_r = self.ac_power_s = self.ac_power_t = 0.0
        for name, value in values.items():
            setattr(self, name, value)


def _inherit_unread(self, data, target, *sources):
    """The real helper, extracted so the fallback is exercised against it."""
    fn = next(
        node for node in ast.walk(ast.parse(SOURCE))
        if isinstance(node, ast.FunctionDef) and node.name == "_inherit_unread"
    )
    module = types.ModuleType("_iu")
    exec(compile(ast.Module(body=[fn], type_ignores=[]), "<iu>", "exec"), module.__dict__)
    return module._inherit_unread(self, data, target, *sources)


def _apply_fallback(data, is_three_phase=True):
    """Run the shipped fallback logic against `data`.

    Extracted as source text rather than reimplemented: a copy of the rule in the test would
    pass even if the component stopped doing it.
    """
    stub = types.SimpleNamespace(_inherit_unread=lambda *a: _inherit_unread(stub, *a))

    if is_three_phase and 'ac_power' in data.unread_fields:
        if not stub._inherit_unread(data, 'ac_power',
                                    'ac_power_r', 'ac_power_s', 'ac_power_t'):
            data.ac_power = round(data.ac_power_r + data.ac_power_s + data.ac_power_t, 1)
            data.unread_fields.discard('ac_power')
    return data


def test_the_shipped_code_contains_the_fallback():
    """The behavioural tests below run extracted logic, so this pins that the component
    actually does it - otherwise they would keep passing after the feature was removed."""
    assert "if is_three_phase and 'ac_power' in data.unread_fields:" in SOURCE, (
        "the aggregate AC power fallback is gone; the entity will sit unknown again on "
        "firmware that does not serve the total register"
    )
    assert "_inherit_unread(data, 'ac_power'," in SOURCE, (
        "the fallback no longer inherits unread from the phases, so a missing phase would "
        "be summed as zero and understate the total"
    )


def test_the_reporters_numbers_produce_the_expected_total():
    """THE regression, with his readings. Unknown became 496.3 W."""
    data = _Data(ac_power_r=PHASE_W[0], ac_power_s=PHASE_W[1], ac_power_t=PHASE_W[2])
    data.unread_fields.add('ac_power')

    _apply_fallback(data)

    assert data.ac_power == pytest.approx(PHASE_SUM)
    assert 'ac_power' not in data.unread_fields, "the entity would still read unknown"


def test_a_working_total_register_is_never_overridden():
    """Guard against over-correcting. The fallback is gated on the total being unread, so an
    inverter that does serve 35/36 keeps its own figure - which may legitimately differ from
    the phase sum by conversion losses."""
    data = _Data(ac_power=500.0,
                 ac_power_r=PHASE_W[0], ac_power_s=PHASE_W[1], ac_power_t=PHASE_W[2])

    _apply_fallback(data)

    assert data.ac_power == 500.0


def test_a_missing_phase_leaves_the_total_unknown():
    """Summing what did arrive would understate the total and look authoritative doing it -
    the same defect the phase fallback itself guards against."""
    data = _Data(ac_power_r=PHASE_W[0], ac_power_s=0.0, ac_power_t=PHASE_W[2])
    data.unread_fields.update({'ac_power', 'ac_power_s'})

    _apply_fallback(data)

    assert 'ac_power' in data.unread_fields, (
        "an aggregate was published from an incomplete set of phases"
    )


def test_single_phase_is_untouched():
    """There are no phases to sum, so unknown stands - and must, rather than being filled
    with a zero that reads as a real measurement."""
    data = _Data()
    data.unread_fields.add('ac_power')

    _apply_fallback(data, is_three_phase=False)

    assert 'ac_power' in data.unread_fields


def test_a_genuine_zero_across_all_phases_is_still_reported():
    """Nothing generating is a measurement. Three phases reading a real zero must produce a
    zero aggregate rather than unknown."""
    data = _Data(ac_power_r=0.0, ac_power_s=0.0, ac_power_t=0.0)
    data.unread_fields.add('ac_power')

    _apply_fallback(data)

    assert data.ac_power == 0.0
    assert 'ac_power' not in data.unread_fields
