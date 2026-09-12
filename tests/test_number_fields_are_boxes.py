"""The two narrow-range numbers are typed, not dragged.

Home Assistant renders `vol.All(vol.Coerce(int), vol.Range(min=..., max=...))` as a slider
when the range is **narrow**, and as a plain box when it is wide. Checked against the actual
rendered form, that split the fields on this options page cleanly:

    slave_id             1-247      slider   <- reported
    timeout              1-60       slider   <- reported
    scan_interval        5-300      box
    offline_scan_interval 60-3600   box
    modbus_delay         50-1000    box
    port                 1-65535    box

So only the first two need an explicit box, and the rest are deliberately left on their
original declarations. This file exists partly to record that: converting the others looked
like consistency and was churn, and without this note the next person will "finish the job".

A slider is the wrong control for the two that need it - both are values the owner knows and
types once, and dragging to 96 out of 247 is fiddly on a mouse and worse on a phone.

The subtle half is the coercion. `NumberSelector` hands back a **float**, and the unit ID is
interpolated into the config entry's unique_id at setup (`f"{host}:{port}_{slave_id}"`), so a
1.0 produces "…:502_1.0" against an existing "…:502_1" and the entry stops matching itself. It
also reaches pymodbus as the device id on every poll. `tests_ha/test_options_flow.py` submits a
unit ID through a real flow and asserts the stored value is an `int` - that half cannot run
here, and it is the one that matters most.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

COMPONENT = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
SOURCE = (COMPONENT / "config_flow.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)

# The fields that rendered as sliders, and the range each must keep.
BOXED = {
    "slave_id": (1, 247),                 # Modbus address range
    "timeout": (1, 60),                   # seconds
    "clock_drift_threshold_min": (0, 240),  # minutes, 0 = notice off (#439)
}

# Left as they were, because they already render as boxes.
LEFT_ALONE = ("scan_interval", "offline_scan_interval", "modbus_delay")


def _function(name: str) -> ast.FunctionDef:
    return next(
        node for node in ast.walk(TREE)
        if isinstance(node, ast.FunctionDef) and node.name == name
    )


def _returned(name: str) -> str:
    """What a helper returns, without its docstring.

    Not `ast.unparse(fn)`: the docstring quotes the slider declaration verbatim, so a naive
    search finds `vol.Coerce(int)` in the prose and concludes the wrong thing about the code.
    It did, on the first run of this file.
    """
    fn = _function(name)
    return ast.unparse(next(n for n in ast.walk(fn) if isinstance(n, ast.Return)))


def _declared_as(field: str) -> list[str]:
    """Every schema declaration for `field`, as the source of its validator.

    Parsed rather than matched. A schema entry is a dict key of `vol.Required(KEY, ...)`
    against the validator, and both parts can contain brackets and line breaks -
    `default=self.config_entry.data.get(CONF_PORT, DEFAULT_PORT)`. A regex written for that
    reached across into the *next* field's declaration and reported the host field's `str` as
    the timeout's validator, which is a convincing-looking wrong answer.
    """
    wanted = {field, f"CONF_{field.upper()}"}
    found = []

    for node in ast.walk(TREE):
        if not isinstance(node, ast.Dict):
            continue
        for key, value in zip(node.keys, node.values):
            if not isinstance(key, ast.Call) or not key.args:
                continue
            first = key.args[0]
            name = first.value if isinstance(first, ast.Constant) else (
                first.id if isinstance(first, ast.Name) else None
            )
            if name in wanted:
                found.append(ast.unparse(value))
    return found


def test_the_shared_builder_asks_for_a_box():
    body = _returned("_number_box")

    assert "NumberSelectorMode.BOX" in body, (
        "the helper no longer requests a box, so Home Assistant renders whatever it "
        "defaults to for a narrow bounded number - which is a slider"
    )
    assert "NumberSelectorConfig" in body


def test_the_shared_builder_coerces_back_to_int():
    """THE regression. NumberSelector yields 96.0, and the unit ID is interpolated into the
    entry's unique_id at setup."""
    body = _returned("_number_box")

    assert "vol.Coerce(int)" in body, (
        "the value is no longer coerced to int; NumberSelector returns a float and it "
        "reaches the unique_id and pymodbus that way"
    )
    assert body.index("NumberSelector") < body.index("vol.Coerce(int)"), (
        "vol.Coerce(int) runs before the selector, so the selector still hands back a float"
    )


def test_the_builder_passes_its_bounds_through():
    """A builder that ignored its arguments would put both fields on the same range, and the
    per-field checks below would still pass by inspecting the call site."""
    body = _returned("_number_box")

    assert "min=minimum" in body and "max=maximum" in body, (
        f"the bounds are not reaching the selector: {body}"
    )


def test_the_timeout_is_a_box_over_its_own_range():
    """The second field reported as a slider. 1-60 seconds, unchanged - this is about how
    the value is entered, not what is accepted."""
    declarations = _declared_as("timeout")

    assert declarations, "no declaration found for the connection timeout"
    for declared in declarations:
        assert declared == "_number_box(1, 60)", (
            f"the connection timeout is declared as {declared}, which renders as a slider"
        )


def test_the_unit_id_is_a_box_over_the_modbus_range():
    assert "_number_box(1, 247)" in _returned("_unit_id_field")

    for declared in _declared_as("slave_id"):
        assert declared == "_unit_id_field()", (
            f"a unit ID field is declared as {declared} rather than through the shared "
            f"helper, so it validates differently from the others"
        )


def test_all_three_unit_id_fields_share_one_declaration():
    """TCP setup, serial setup, options. Two were bare ints with no validation and one was
    the slider, which is how they came to disagree about what a valid unit ID is."""
    assert SOURCE.count(": _unit_id_field()") == 3, (
        f"expected three unit ID fields wired to the shared helper, found "
        f"{SOURCE.count(': _unit_id_field()')}"
    )


@pytest.mark.parametrize("field", LEFT_ALONE)
def test_the_wide_range_fields_are_left_alone(field):
    """Deliberate, and verified against the rendered form rather than assumed: these already
    appear as boxes. Converting them would be churn on fields that work, and it would put the
    unique_id-bearing coercion on values that do not need it."""
    declarations = _declared_as(field)

    assert declarations, f"no declaration found for {field}"
    for declared in declarations:
        assert "_number_box" not in declared, (
            f"{field} has been converted to an explicit number box. It already renders as "
            f"one - see this file's docstring. If the rendered form has changed, update the "
            f"table there rather than only this assertion."
        )


def test_the_helper_is_only_used_for_narrow_ranges():
    """Guard on the same point from the other side, by the rule rather than by a count.

    Home Assistant renders a bounded number as a slider only when the range is narrow, so
    the box is for narrow fields and the wide ones neither need it nor should carry it.
    An earlier version of this asserted "exactly one call site", which failed the moment a
    legitimately narrow field was added - a count is not the property being protected.
    """
    spans = [
        (int(low), int(high))
        for low, high in re.findall(r"_number_box\((\d+),\s*(\d+)\)", SOURCE)
    ]
    assert spans, "no _number_box call sites found at all"

    for low, high in spans:
        assert high - low <= 250, (
            f"_number_box({low}, {high}) spans {high - low}, which Home Assistant already "
            f"renders as a plain box - converting it is churn on a field that works"
        )
