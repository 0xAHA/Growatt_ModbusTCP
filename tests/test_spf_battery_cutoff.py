"""SPF holding register 82 - battery undervoltage cut-off (#444).

An SPF 5000 ES owner mapped 24 ShinePhone settings against his inverter and found this
one reachable only from the front panel or the vendor app. His readings, live, on
Lithium (register 39 = 3):

    34: 120   37: 350   38: 0     39: 3
    82: 100   94: 420   95: 850

37, 82 and 95 at scale 0.1 give 35 %, 10 % and 85 %, which is exactly what the app shows
for "Battery to grid operational point", "Battery undervoltage cut-off point" and "Grid
to battery operational point".

The same file also covers the generator charge current sentinel from the same report:
register 83 answers 65535 on that model because it has no generator charge setting.
"""

from __future__ import annotations

import ast
import importlib
from pathlib import Path

import pytest

_const = importlib.import_module("growatt_under_test.const")
_gm = importlib.import_module("growatt_under_test.growatt_modbus")

COMPONENT = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
SPF_MAP = "SPF_3000_6000_ES_PLUS"


def _profile():
    return _const.REGISTER_MAPS[SPF_MAP]


def _control():
    return _const.WRITABLE_REGISTERS["bat_low_cutoff"]


# ---------------------------------------------------------------------------
# The register
# ---------------------------------------------------------------------------

def test_register_82_is_mapped_on_spf():
    reg = _profile()["holding_registers"][82]
    assert reg["name"] == "bat_low_cutoff"
    assert reg["access"] == "RW"


def test_the_scale_reproduces_the_reported_readings():
    """100 -> 10 %, and the two neighbours it was cross-checked against."""
    holding = _profile()["holding_registers"]
    assert holding[82]["scale"] * 100 == pytest.approx(10.0)
    assert holding[37]["scale"] * 350 == pytest.approx(35.0)
    assert holding[95]["scale"] * 850 == pytest.approx(85.0)


def test_it_follows_battery_type_like_its_two_neighbours():
    """Only the Lithium half is confirmed. 37 and 95 already switch between volts and
    percent on register 39, and 82 is assumed to do the same rather than being pinned to
    a percentage that a lead-acid system may not use."""
    holding = _profile()["holding_registers"]
    for address in (37, 82, 95):
        assert holding[address].get("battery_dependent") is True, address
        assert holding[address]["unit"] == "V/%", address


def test_the_control_matches_the_register():
    control = _control()
    reg = _profile()["holding_registers"][82]
    assert control["register"] == 82
    assert control["scale"] == reg["scale"]
    assert control["valid_range"] == reg["valid_range"]
    assert control["battery_dependent"] is True


def test_the_label_does_not_claim_a_unit():
    """number.py switches this entity between % and V at runtime, so a label saying
    either is wrong for half the owners - the same reasoning as bat_low_to_uti."""
    label = _control()["label"]
    assert "Voltage" not in label
    assert "SOC" not in label


def test_it_lands_on_the_battery_device():
    assert _const.get_device_type_for_control("bat_low_cutoff") == _const.DEVICE_TYPE_BATTERY


# ---------------------------------------------------------------------------
# Register 83's not-supported sentinel
# ---------------------------------------------------------------------------

def test_gen_charge_current_sentinel_threshold_clears_the_profile_ceiling():
    """65535 is 0xFFFF, not a current. The profile's own ceiling is 80 A, so nothing
    legitimate comes near the threshold."""
    threshold = _gm.GrowattModbus.GEN_CHARGE_CURRENT_NOT_SUPPORTED
    assert threshold == 65530
    assert 65535 >= threshold
    assert _profile()["holding_registers"][83]["valid_range"][1] < threshold


def test_number_entities_report_unknown_for_an_unread_control():
    """Adding the field to unread_fields is only half the job: native_value reads the
    dataclass, which still holds 0, so without the check the entity publishes 0 A - a
    plausible-looking charge limit rather than an absent one."""
    source = (COMPONENT / "number.py").read_text(encoding="utf-8")
    tree = ast.parse(source)

    found = False
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "native_value":
            segment = ast.get_source_segment(source, node) or ""
            if "unread_fields" in segment:
                found = True
                break

    assert found, "no native_value consults unread_fields, so a withheld control shows 0"


def test_the_read_takes_82_and_83_in_one_block():
    """They are adjacent; two single reads would cost an extra round trip on a gateway
    that is already the reason block sizes are configurable."""
    source = (COMPONENT / "growatt_modbus.py").read_text(encoding="utf-8")
    assert "read_holding_registers(82, 2)" in source
    assert "read_holding_registers(83, 1)" not in source, (
        "register 83 is still read on its own as well as in the 82-83 block"
    )
