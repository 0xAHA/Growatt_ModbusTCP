"""SPH time-slot entities must be named after the slot the inverter actually uses (#386).

Protocol V1.39 and the Growatt app agree on what these registers are. The control names did
not, and a reporter had to determine the mapping by experiment - setting a slot in Home
Assistant and seeing which one moved in the app.

| Registers | Protocol V1.39 | Control name |
|---|---|---|
| 1080-1088 | Grid First 1 / 2 / 3 | grid_first_time_period_7/8/9 |
| 1100-1108 | Bat First 1 / 2 / 3  | time_period_1/2/3 |

The names are left alone deliberately. Renaming would change entity IDs and break existing
automations, which is too high a price for a labelling error - the same reasoning as #362,
where two SPH controls were relabelled rather than renamed. Only the display name is fixed.
"""
from __future__ import annotations

import importlib

import pytest

_const = importlib.import_module("growatt_under_test.const")
W = _const.WRITABLE_REGISTERS

# register -> what the protocol and the app both call it
EXPECTED = {
    1080: "Grid First Period 1 Start", 1081: "Grid First Period 1 End",
    1082: "Grid First Period 1 Enable",
    1083: "Grid First Period 2 Start", 1084: "Grid First Period 2 End",
    1085: "Grid First Period 2 Enable",
    1086: "Grid First Period 3 Start", 1087: "Grid First Period 3 End",
    1088: "Grid First Period 3 Enable",
    1100: "Battery First Period 1 Start", 1101: "Battery First Period 1 End",
    1102: "Battery First Period 1 Enable",
    1103: "Battery First Period 2 Start", 1104: "Battery First Period 2 End",
    1105: "Battery First Period 2 Enable",
    1106: "Battery First Period 3 Start", 1107: "Battery First Period 3 End",
    1108: "Battery First Period 3 Enable",
}

BY_REGISTER = {cfg["register"]: (name, cfg) for name, cfg in W.items() if "register" in cfg}


@pytest.mark.parametrize("register,label", sorted(EXPECTED.items()))
def test_the_slot_is_labelled_as_the_inverter_numbers_it(register, label):
    name, cfg = BY_REGISTER[register]
    assert cfg.get("label") == label, (
        f"register {register} ({name}) displays as {cfg.get('label') or name!r}, but the "
        f"protocol and the Growatt app both call it {label!r}"
    )


@pytest.mark.parametrize("register", sorted(EXPECTED))
def test_control_names_are_not_renamed(register):
    """The other half of the decision. Correcting the label must not become a rename -
    entity IDs derive from the control name and automations reference them."""
    name, _ = BY_REGISTER[register]
    if 1080 <= register <= 1088:
        assert name.startswith("grid_first_time_period_"), f"{register} was renamed to {name}"
    else:
        assert name.startswith("time_period_"), f"{register} was renamed to {name}"


def test_both_platforms_honour_the_label():
    """Start/end are time entities and enable is a select. A label read by one and not the
    other would leave every third entity still mislabelled."""
    from pathlib import Path
    base = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
    for platform in ("time.py", "select.py"):
        source = (base / platform).read_text(encoding="utf-8")
        assert "control_config.get('label')" in source, (
            f"{platform} ignores the label, so its entities keep the misleading name"
        )


def test_the_4_to_6_slots_are_left_alone():
    """Those registers are documented and correctly named; one firmware rejects writes to
    them. Other firmware may not, and a user can disable the entities - so they stay."""
    for n in (4, 5, 6):
        assert f"grid_first_time_period_{n}_start" in W
        assert f"batt_first_time_period_{n}_start" in W
