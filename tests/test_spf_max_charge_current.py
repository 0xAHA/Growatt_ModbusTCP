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


# ---------------------------------------------------------------------------
# Bulk and float charging voltage, holding 35 and 36 (#384)
#
# Different in kind from every other control here: a wrong in-range value charges a battery
# bank incorrectly rather than producing a visible mistake. Created disabled by default so
# operating them is deliberate.
#
# The range is unusually well evidenced - the reporter photographed the SPF 6000ES Plus and
# SPF 3000-5000 ES manuals side by side, and Programs 19/20 are identical in both, so unlike
# max_charge_current these do not vary across the family.
# ---------------------------------------------------------------------------

VOLTAGE_CONTROLS = ["bulk_charge_voltage", "float_charge_voltage"]
USER_DEFINED = (2, 4)  # register 39: 2 = User Defined, 4 = User Defined 2


@pytest.mark.parametrize("name", VOLTAGE_CONTROLS)
def test_the_voltage_controls_are_mapped_and_writable(name):
    addr = {"bulk_charge_voltage": 35, "float_charge_voltage": 36}[name]
    reg = SPF["holding_registers"][addr]
    assert reg["name"] == name
    assert reg["access"] == "RW"
    assert reg["scale"] == 0.1, "555 raw must read as 55.5 V"


@pytest.mark.parametrize("name", VOLTAGE_CONTROLS)
def test_the_slider_spans_the_manual_range(name):
    """valid_range is in raw units; the entity multiplies by scale. 480-584 x 0.1 is the
    48.0-58.4 V both manuals give."""
    cfg = _const.WRITABLE_REGISTERS[name]
    lo, hi = cfg["valid_range"]
    assert lo * cfg["scale"] == pytest.approx(48.0)
    assert hi * cfg["scale"] == pytest.approx(58.4)


@pytest.mark.parametrize("name", VOLTAGE_CONTROLS)
def test_they_are_created_disabled(name):
    """The decision that separates these from every other control in the integration."""
    assert _const.WRITABLE_REGISTERS[name].get("disabled_by_default") is True


@pytest.mark.parametrize("name", VOLTAGE_CONTROLS)
@pytest.mark.parametrize("battery_type", USER_DEFINED)
def test_available_on_a_self_defined_battery(name, battery_type):
    """"If self-defined is selected in program 5, this program can be set up"."""
    cfg = _const.WRITABLE_REGISTERS[name]
    assert _const.control_is_blocked(cfg, _Data(battery_type=battery_type)) is False


@pytest.mark.parametrize("name", VOLTAGE_CONTROLS)
@pytest.mark.parametrize("battery_type", [0, 1, 3])  # AGM, Flooded, Lithium
def test_withheld_on_every_preset_battery_type(name, battery_type):
    """The inverse of max_charge_current, which is blocked only on Lithium. Offering these
    on a preset chemistry would present a slider the inverter will not honour."""
    cfg = _const.WRITABLE_REGISTERS[name]
    assert _const.control_is_blocked(cfg, _Data(battery_type=battery_type)) is True


def test_the_two_availability_forms_do_not_interfere():
    """max_charge_current uses unavailable_when, the voltages use available_when. A control
    with neither must stay available - that is the other 500-odd controls."""
    assert _const.control_is_blocked(_const.WRITABLE_REGISTERS["ac_charge_current"],
                                     _Data(battery_type=3)) is False
    assert _const.control_is_blocked(ENTRY, _Data(battery_type=2)) is False


@pytest.mark.parametrize("name", VOLTAGE_CONTROLS)
def test_the_data_container_carries_the_field(name):
    """native_value reads getattr(data, control_name), so the names must match exactly."""
    assert hasattr(_gm.GrowattData(), name)


def test_the_number_platform_honours_disabled_by_default():
    """Without this the flag is decoration and the controls appear enabled."""
    source = (Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
              / "number.py").read_text(encoding="utf-8")
    assert "control_config.get('disabled_by_default')" in source
    assert "_attr_entity_registry_enabled_default = False" in source


def test_the_block_read_covers_35_and_36():
    """34-39 is read as one block; 35 and 36 are indices 1 and 2."""
    source = (Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
              / "growatt_modbus.py").read_text(encoding="utf-8")
    assert "data.bulk_charge_voltage = int(battery_ctrl_regs[1])" in source
    assert "data.float_charge_voltage = int(battery_ctrl_regs[2])" in source


# ---------------------------------------------------------------------------
# EEPROM write avoidance (#384)
#
# These registers live in EEPROM, which has finite write endurance. Nothing in the
# integration writes on its own - a write happens only when a user or an automation sets a
# value - but an automation re-applying the same value on a schedule would burn a cycle every
# run for no effect. Raised by a reporter whose contact repairs inverters and saw four
# SPF6000ES units with failed EEPROMs in a year.
# ---------------------------------------------------------------------------

def test_nothing_writes_outside_an_explicit_set():
    """The reassuring half of the answer: polling never writes. If this ever changes, the
    EEPROM guarantee given to users on #384 is void."""
    for name in ("coordinator.py", "__init__.py"):
        source = (Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
                  / name).read_text(encoding="utf-8")
        assert "write_register(" not in source, f"{name} performs a Modbus write"
        assert "write_registers(" not in source, f"{name} performs a Modbus write"


def test_setting_the_current_value_does_not_write():
    """A redundant write costs an EEPROM cycle and cannot change anything."""
    source = (Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
              / "number.py").read_text(encoding="utf-8")
    guard = source[source.index("async def async_set_native_value"):]
    guard = guard[:guard.index("write_register_verified")]
    assert "int(current_raw) == raw_value" in guard, (
        "a write is issued even when the register already holds the requested value"
    )
    assert "return" in guard


def test_the_guard_needs_a_current_reading():
    """A skipped write that should have happened is worse than a redundant one, so an
    unread register must fall through to the write."""
    source = (Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
              / "number.py").read_text(encoding="utf-8")
    assert "current_raw is not None and" in source, (
        "the no-op guard fires without a known current value"
    )
