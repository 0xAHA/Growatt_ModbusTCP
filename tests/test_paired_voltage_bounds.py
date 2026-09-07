"""Bulk and Float charge voltage must not be settable across each other (#387).

On SPF, Bulk (Program 19, register 35) is the constant-voltage stage and Float (Program 20,
register 36) the maintenance stage. The firmware refuses a bulk voltage below the float
voltage - and refuses it *silently*: the write is acknowledged, the register reverts, and the
read-back check then raises **"settings are being reverted"**.

So a user who asked for something the hardware will never accept was shown a repair notice
suggesting the integration or the Growatt cloud was at fault. @dinkalin-ux hit this on an SPF
6000ES Plus with no datalogger attached, which is what ruled out the cloud and left the
firmware's own rejection as the only explanation. He confirmed it himself: he had set Bulk to
a much lower voltage and the inverter firmly rejected the command.

Both controls spanned the same 48.0-58.4 V independently, so nothing stopped the two crossing.

`number.py` imports `homeassistant.components.number`, which this suite does not have, so the
logic is exercised through extracted methods bound to a stub. The alternative - asserting the
constraint exists in `const.py` and trusting the entity to honour it - would pass against an
entity that ignored it completely.
"""
from __future__ import annotations

import ast
import importlib
import sys
import types
from pathlib import Path

import pytest

sys.path.insert(0, "tests")

CONST = importlib.import_module("growatt_under_test.const")
COMPONENT = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
SOURCE = (COMPONENT / "number.py").read_text(encoding="utf-8")

STATIC_MIN, STATIC_MAX = 48.0, 58.4


class _HomeAssistantError(Exception):
    pass


def _load_methods():
    """Bind the paired-bound methods to a stub, with no Home Assistant import."""
    tree = ast.parse(SOURCE)
    wanted = {"_paired_bound", "_check_paired_constraint", "_friendly",
              "native_min_value", "native_max_value"}
    found = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name in wanted:
            found[node.name] = node
    missing = wanted - set(found)
    assert not missing, f"methods no longer present in number.py: {sorted(missing)}"

    module = types.ModuleType("_paired")
    module.__dict__["HomeAssistantError"] = _HomeAssistantError

    body = [found[name] for name in
            ("_paired_bound", "_check_paired_constraint", "_friendly",
             "native_min_value", "native_max_value")]
    # Decorators are re-applied explicitly on the stub below.
    for node in body:
        node.decorator_list = []
    src = ast.unparse(ast.Module(body=body, type_ignores=[]))
    src = src.replace("from .const import WRITABLE_REGISTERS",
                      "from growatt_under_test.const import WRITABLE_REGISTERS")
    exec(compile(src, "<paired>", "exec"), module.__dict__)
    return module


M = _load_methods()


class _Data:
    def __init__(self, **raw):
        self.unread_fields: set[str] = set()
        for name, value in raw.items():
            setattr(self, name, value)


class _Entity:
    """Enough of GrowattGenericNumber for the paired-bound logic."""

    def __init__(self, control_name, data=None):
        self._control_name = control_name
        self._control_config = CONST.WRITABLE_REGISTERS[control_name]
        self._attr_name = control_name.replace("_", " ").title()
        self._attr_native_min_value = STATIC_MIN
        self._attr_native_max_value = STATIC_MAX
        self.coordinator = types.SimpleNamespace(data=data)

    _paired_bound = M._paired_bound
    _check_paired_constraint = M._check_paired_constraint
    _friendly = staticmethod(M._friendly)
    min_value = property(M.native_min_value)
    max_value = property(M.native_max_value)


# Raw register values: scale 0.1, so 540 is 54.0 V.
FLOAT_54V = {"float_charge_voltage": 540}
BULK_564V = {"bulk_charge_voltage": 564}


def test_the_constraint_is_declared_on_both_controls():
    """Declared per control, not inferred. Only this pair is known to interact."""
    assert CONST.WRITABLE_REGISTERS["bulk_charge_voltage"]["not_below"] == "float_charge_voltage"
    assert CONST.WRITABLE_REGISTERS["float_charge_voltage"]["not_above"] == "bulk_charge_voltage"


def test_bulk_cannot_be_dragged_below_float():
    """THE fix. With float at 54.0 V the Bulk slider must not offer anything lower."""
    entity = _Entity("bulk_charge_voltage", _Data(**FLOAT_54V))

    assert entity.min_value == 54.0
    assert entity.max_value == STATIC_MAX


def test_float_cannot_be_dragged_above_bulk():
    """The other direction, which matters just as much - raising Float past Bulk produces
    the same invalid pair from the opposite side."""
    entity = _Entity("float_charge_voltage", _Data(**BULK_564V))

    assert entity.max_value == 56.4
    assert entity.min_value == STATIC_MIN


def test_a_service_call_below_the_floor_is_refused_with_a_reason():
    """The bounds stop the slider; they do not stop `number.set_value` from a script or the
    REST API, which is the path an automation takes."""
    entity = _Entity("bulk_charge_voltage", _Data(**FLOAT_54V))

    with pytest.raises(_HomeAssistantError) as raised:
        entity._check_paired_constraint(52.0)

    message = str(raised.value)
    assert "54.0" in message, "the error does not say what the limit currently is"
    assert "revert" in message.lower(), (
        "the error does not explain why - the user would otherwise read this as our refusal "
        "rather than the inverter's"
    )


def test_a_valid_value_is_not_refused():
    """Guard against over-correcting: equal values are legal, and above-float is normal."""
    entity = _Entity("bulk_charge_voltage", _Data(**FLOAT_54V))

    entity._check_paired_constraint(54.0)   # equal - allowed
    entity._check_paired_constraint(56.4)   # the default bulk voltage


def test_an_unread_partner_does_not_collapse_the_range():
    """The failure this guard exists for. An unread register keeps its 0.0 default, so a
    Float slider taking its maximum from an unread Bulk would collapse to 0 and become
    unusable - a worse bug than the one being fixed."""
    data = _Data(bulk_charge_voltage=0)
    data.unread_fields.add("bulk_charge_voltage")
    entity = _Entity("float_charge_voltage", data)

    assert entity.max_value == STATIC_MAX
    entity._check_paired_constraint(58.0)


def test_a_partner_value_outside_the_static_range_is_ignored():
    """A 0.0 default that was never marked unread would otherwise clamp the range to zero."""
    entity = _Entity("float_charge_voltage", _Data(bulk_charge_voltage=0))

    assert entity.max_value == STATIC_MAX


def test_no_coordinator_data_falls_back_to_the_static_range():
    """During setup `coordinator.data` is an empty placeholder."""
    entity = _Entity("bulk_charge_voltage", None)

    assert entity.min_value == STATIC_MIN
    assert entity.max_value == STATIC_MAX


def test_controls_without_a_declared_pair_are_untouched():
    """Only this pair is constrained. Every other number control must behave as before."""
    for name, config in CONST.WRITABLE_REGISTERS.items():
        if name in ("bulk_charge_voltage", "float_charge_voltage"):
            continue
        assert "not_below" not in config and "not_above" not in config, (
            f"{name} has gained a paired constraint with no evidence behind it"
        )
