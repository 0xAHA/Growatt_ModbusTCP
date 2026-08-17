"""SPF max total charge current, holding 34 (#376).

Two things this control has to get right, and both come from the reporter's own testing
rather than from the protocol document:

1. The range is **10-100 A**, from the SPF 6000ES Plus LCD manual (Program 02), not the
   0~400 in the family-wide off-grid protocol. The floor of 10 is the part that matters:
   this panel scrolls to 999 and then silently discards an out-of-range save, so a slider
   offering 0-9 would look accepted and change nothing.

2. It cannot be set at all when battery type is Lithium — "(If LI is selected in Program 5,
   this program can't be set up)". On hardware that discards rejected saves silently, a
   control offered in that state would appear to work. It is withheld instead.

The availability rule is tested through `control_is_blocked` rather than the entity, because
the entity needs Home Assistant and that suite only runs on Linux CI. The property is a
two-line call into this function, and a source check holds them together.
"""
from __future__ import annotations

import importlib
from dataclasses import dataclass
from pathlib import Path

import pytest

_const = importlib.import_module("growatt_under_test.const")
_profiles = importlib.import_module("growatt_under_test.profiles")
_gm = importlib.import_module("growatt_under_test.growatt_modbus")

SPF = _profiles.get_profile("SPF_3000_6000_ES_PLUS")
ENTRY = _const.WRITABLE_REGISTERS["max_charge_current"]

LITHIUM = 3  # register 39 value


@dataclass
class _Data:
    battery_type: int = 0


def test_register_34_is_mapped_and_writable():
    reg = SPF["holding_registers"][34]
    assert reg["name"] == "max_charge_current"
    assert reg["access"] == "RW"
    assert reg["scale"] == 1, "raw 50 reads as 50 A on hardware — no scale factor"


def test_the_range_is_the_manual_not_the_protocol_document():
    """0~400 is the whole off-grid family. 10-100 is this model."""
    assert ENTRY["valid_range"] == (10, 100)
    assert SPF["holding_registers"][34]["valid_range"] == (10, 100)


def test_the_floor_is_ten_not_zero():
    """Called out separately because it is the easy thing to get wrong, and because an
    out-of-range value is discarded silently by this hardware rather than refused."""
    assert ENTRY["valid_range"][0] == 10, (
        "a floor of 0 would offer 0-9 A, which this inverter accepts in the UI and then "
        "discards without telling anyone"
    )


def test_it_is_withheld_on_a_lithium_battery():
    assert _const.control_is_blocked(ENTRY, _Data(battery_type=LITHIUM)) is True


@pytest.mark.parametrize("battery_type", [0, 1, 2, 4])
def test_it_is_offered_on_every_non_lithium_battery(battery_type):
    """AGM, Flooded, User and User 2 all allow Program 02. The reporter's own unit is on
    User, which is why the control could be tested at all."""
    assert _const.control_is_blocked(ENTRY, _Data(battery_type=battery_type)) is False


def test_controls_without_a_condition_are_never_blocked():
    """The mechanism must not affect the other 500-odd controls."""
    assert _const.control_is_blocked(_const.WRITABLE_REGISTERS["ac_charge_current"], _Data()) is False


def test_no_data_yet_does_not_hide_the_control():
    """coordinator.data is an empty placeholder during setup. An entity that vanished at
    startup would be worse than one that briefly accepts a write."""
    assert _const.control_is_blocked(ENTRY, None) is False


def test_the_number_entity_actually_consults_the_rule():
    """Guards the join between the tested function and the untested property. Without this
    the rule could be correct and never called — which is exactly how #374 shipped."""
    source = (Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
              / "number.py").read_text(encoding="utf-8")
    assert "def available" in source, "GrowattGenericNumber no longer overrides available"
    assert "control_is_blocked(self._control_config, self.coordinator.data)" in source, (
        "the availability property does not consult control_is_blocked, so a control with "
        "an unavailable_when condition would still be offered"
    )


def test_the_read_block_covers_register_34():
    """34 is not contiguous with 37-39. Reading 37 for 3 would never see it."""
    source = (Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
              / "growatt_modbus.py").read_text(encoding="utf-8")
    assert "self.read_holding_registers(34, 6)" in source, (
        "the SPF battery-config block does not start at 34, so max_charge_current is "
        "never populated"
    )


def test_max_charge_current_reaches_the_data_container():
    """A field missing from GrowattData is the most common way a control silently fails."""
    assert hasattr(_gm.GrowattData(), "max_charge_current")
