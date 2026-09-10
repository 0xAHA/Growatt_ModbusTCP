"""The Modbus unit ID is typed into a box, not dragged on a slider.

Home Assistant renders `vol.All(vol.Coerce(int), vol.Range(min=1, max=247))` as a slider.
For a unit ID that is the wrong control: 247 positions to drag through for a number the
owner already knows and types once. Setting 96 by hand is fiddly with a mouse and worse on
a phone.

The two setup steps had the opposite problem - a bare `int`, which renders as a box but
validates nothing, so 0 or 300 could be entered at setup and were then refused by the
options form, leaving an entry in a state it could not be edited out of. All three fields
now share one helper.

The behavioural half of this lives in `tests_ha/test_options_flow.py`, which submits a unit
ID through a real Home Assistant flow and asserts the stored value is an `int`. That is the
part that matters most and it cannot run here: NumberSelector returns a **float**, and this
value goes into the config entry's unique_id, so losing the coercion would stop an entry
matching itself and orphan its entities. What this file can do without Home Assistant is
hold the shape of the schema.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

COMPONENT = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
SOURCE = (COMPONENT / "config_flow.py").read_text(encoding="utf-8")


def _helper() -> ast.FunctionDef:
    return next(
        node for node in ast.walk(ast.parse(SOURCE))
        if isinstance(node, ast.FunctionDef) and node.name == "_unit_id_field"
    )


def _schema() -> str:
    """Just what the helper returns.

    Not `ast.unparse(helper)`: the docstring quotes the old slider declaration verbatim, so
    a naive search finds `vol.Coerce(int)` in the prose and concludes the wrong thing about
    the code. It did, on the first run of this file.
    """
    returned = next(
        node for node in ast.walk(_helper()) if isinstance(node, ast.Return)
    )
    return ast.unparse(returned)


def test_the_helper_exists_and_asks_for_a_box():
    body = _schema()

    assert "NumberSelectorMode.BOX" in body, (
        "the unit ID field no longer requests a box, so Home Assistant will render "
        "whatever it defaults to for the constraint - which for a bounded number is a slider"
    )
    assert "NumberSelectorConfig" in body


def test_the_helper_coerces_back_to_int():
    """THE regression, and the reason this is a helper rather than three inline schemas.

    NumberSelector yields 96.0. The unit ID is interpolated into the entry's unique_id, so
    a float produces "192.168.1.50:502_96.0" against an existing "..._96".
    """
    body = _schema()

    assert "vol.Coerce(int)" in body, (
        "the unit ID is no longer coerced to int; NumberSelector returns a float and it "
        "reaches the unique_id and pymodbus that way"
    )
    # Order matters: the selector validates first, the coercion cleans up after it.
    assert body.index("NumberSelector") < body.index("vol.Coerce(int)"), (
        "vol.Coerce(int) runs before the selector, so the selector still hands back a float"
    )


def test_the_range_is_the_modbus_one():
    body = _schema()
    assert "min=1" in body and "max=247" in body, (
        "valid Modbus unit IDs are 1-247; a wider range lets setup store a value the "
        "options form will then refuse"
    )


def test_every_unit_id_field_uses_the_helper():
    """Three of them: the TCP setup step, the serial setup step, and the options form.

    Two were bare ints with no validation and one was the slider, which is how they came to
    disagree about what a valid unit ID is.
    """
    # Matched by call site rather than by parsing each declaration: the three differ in
    # layout (one wraps across lines, one nests a prior.get() call) and a regex that copes
    # with all three is harder to trust than counting what they must all end in.
    assert SOURCE.count(": _unit_id_field()") == 3, (
        f"expected three unit ID fields wired to the shared helper, found "
        f"{SOURCE.count(': _unit_id_field()')}"
    )

    # And nothing declares one any other way. Each CONF_SLAVE_ID schema entry ends at the
    # `):` that closes its vol.Required, so take what follows that.
    for match in re.finditer(r"vol\.Required\(\s*CONF_SLAVE_ID.*?\)\s*:\s*([^,\n]+)",
                             SOURCE, re.S):
        declared = match.group(1).strip().rstrip(",")
        assert declared == "_unit_id_field()", (
            f"a unit ID field is declared as {declared!r} rather than through the shared "
            f"helper, so it validates differently from the other two"
        )


def test_no_slider_declaration_survives_anywhere():
    """A `vol.Range` on the unit ID is the slider, in whatever form it comes back."""
    for match in re.finditer(r"CONF_SLAVE_ID.{0,160}", SOURCE, re.S):
        assert "vol.Range" not in match.group(0), (
            "a unit ID field is back on vol.Range, which Home Assistant renders as a slider"
        )
