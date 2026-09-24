"""Inverter on/off across every protocol family (#432).

Each family encodes remote on/off differently, and two of them pack a second setting into
the same register. The failure these tests exist for is not a crash - it is a write that
succeeds and quietly changes something else: a bare `0` on a TL3-S turns auto start off
along with the inverter, so after the next power cut it stays off until someone notices.

Behavioural where it can be (encoding, resolution against every real register map, the
read-modify-write against a fake client); source-level for the HA entity, which needs
homeassistant.components to import.
"""
from __future__ import annotations

import ast
import importlib
import json
from pathlib import Path

import pytest

pc = importlib.import_module("growatt_under_test.power_control")
REGISTER_MAPS = importlib.import_module("growatt_under_test.const").REGISTER_MAPS
COMPONENT = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"


# ---------------------------------------------------------------------------
# Which encoding each profile gets
# ---------------------------------------------------------------------------

LEGACY = {"TL3_S_3000_15000", "MIC_600_3300TL_X", "MIC_2500_5500MTL_S", "MIC_600_3300TL_X_V201"}
OFFGRID = {"SPF_3000_6000_ES_PLUS", "SPE_8000_12000_ES"}
VPP_ONLY = {"MIN_TL_XH2_3000_10000_V201"}


@pytest.mark.parametrize("name", sorted(REGISTER_MAPS))
def test_every_profile_with_an_onoff_register_gets_a_control(name):
    holding = REGISTER_MAPS[name].get("holding_registers", {})
    control = pc.resolve_power_control(REGISTER_MAPS[name])
    if 0 in holding or 30101 in holding:
        assert control is not None, f"{name} declares on/off but gets no switch"
    else:
        assert control is None


@pytest.mark.parametrize("name", sorted(REGISTER_MAPS))
def test_each_profile_gets_its_protocols_encoding(name):
    control = pc.resolve_power_control(REGISTER_MAPS[name])
    if control is None:
        return
    if name in LEGACY:
        expected = (0, pc.ENCODING_LEGACY_AUTOSTART)
    elif name in OFFGRID:
        expected = (0, pc.ENCODING_OFFGRID_OUTPUT)
    elif name in VPP_ONLY:
        expected = (30101, pc.ENCODING_VPP)
    else:
        expected = (0, pc.ENCODING_PLAIN)
    assert (control.register, control.encoding) == expected, (
        f"{name}: expected register {expected[0]} with {expected[1]} encoding, got "
        f"{control.register} with {control.encoding}"
    )


def test_v201_profiles_keep_holding_0_rather_than_30101():
    """Same hardware as their legacy siblings, and 30101 is unmeasured without control
    authority - which the switch must not grant as a side effect."""
    control = pc.resolve_power_control(REGISTER_MAPS["MOD_6000_15000TL3_XH"])
    assert control.register == 0
    for name in ("MIN_TL_XH_3000_10000_V201", "SPH_3000_6000_V201", "MIC_600_3300TL_X_V201"):
        assert pc.resolve_power_control(REGISTER_MAPS[name]).register == 0, name


# ---------------------------------------------------------------------------
# Encoding
# ---------------------------------------------------------------------------

LEG = pc.PowerControl(0, pc.ENCODING_LEGACY_AUTOSTART)
OFF = pc.PowerControl(0, pc.ENCODING_OFFGRID_OUTPUT)
PLAIN = pc.PowerControl(0, pc.ENCODING_PLAIN)
VPP = pc.PowerControl(30101, pc.ENCODING_VPP)


@pytest.mark.parametrize("current,on,expected", [
    (0x0101, False, 0x0100),  # the TL3-S's real reading (257): off keeps auto start
    (0x0100, True, 0x0101),
    (0x0001, False, 0x0000),  # auto start already off stays off
    (0x0000, True, 0x0001),
])
def test_legacy_keeps_the_auto_start_byte(current, on, expected):
    assert pc.encode(LEG, on, current) == expected


@pytest.mark.parametrize("current,on,expected", [
    (0x0000, False, 0x0100),  # documented: 0x0100 = output disabled
    (0x0100, True, 0x0000),   # documented: 0x0000 = output enabled
    (0x0001, False, 0x0101),  # standby byte preserved
    (0x0101, True, 0x0001),
])
def test_offgrid_toggles_only_the_ac_output_byte(current, on, expected):
    assert pc.encode(OFF, on, current) == expected


@pytest.mark.parametrize("control", [PLAIN, VPP])
def test_plain_and_vpp_write_only_1_and_0(control):
    """Never 2/3: on V1.39 those switch the battery DC converter, not the inverter."""
    assert pc.encode(control, True) == 1
    assert pc.encode(control, False) == 0


# ---------------------------------------------------------------------------
# The write itself
# ---------------------------------------------------------------------------

class _Client:
    def __init__(self, reg0=None):
        self.reg0 = reg0
        self.reads: list = []
        self.writes: list = []

    def read_holding_registers(self, start, count):
        self.reads.append((start, count))
        return None if self.reg0 is None else [self.reg0]

    def write_register(self, register, value):
        self.writes.append((register, value))
        return True


def test_legacy_write_reads_first_and_preserves_auto_start():
    client = _Client(reg0=0x0101)
    assert pc.set_power(client, LEG, False) == 0x0100
    assert client.reads == [(0, 1)]
    assert client.writes == [(0, 0x0100)]


@pytest.mark.parametrize("control", [LEG, OFF])
def test_a_failed_read_writes_nothing(control):
    """Guessing the other byte is the exact mistake the read exists to prevent."""
    client = _Client(reg0=None)
    with pytest.raises(pc.PowerControlError, match="nothing was written"):
        pc.set_power(client, control, False)
    assert client.writes == []


def test_plain_write_does_not_read():
    client = _Client(reg0=None)
    assert pc.set_power(client, PLAIN, True) == 1
    assert client.reads == []
    assert client.writes == [(0, 1)]


# ---------------------------------------------------------------------------
# The entity
# ---------------------------------------------------------------------------

def _class_attrs(source: str, class_name: str) -> dict[str, str]:
    tree = ast.parse(source)
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == class_name)
    return {
        t.id: ast.get_source_segment(source, s.value)
        for s in cls.body if isinstance(s, ast.Assign)
        for t in s.targets if isinstance(t, ast.Name)
    }


def test_the_switch_is_disabled_by_default():
    """So nobody turns an inverter off by accident - the explicit requirement."""
    attrs = _class_attrs((COMPONENT / "switch.py").read_text(encoding="utf-8"), "GrowattPowerSwitch")
    assert attrs.get("_attr_entity_registry_enabled_default") == "False"
    assert attrs.get("_attr_assumed_state") == "True"


def test_the_switch_platform_is_registered():
    assert "Platform.SWITCH" in (COMPONENT / "__init__.py").read_text(encoding="utf-8")


def test_both_switch_names_exist_in_both_string_files():
    for rel in ("strings.json", "translations/en.json"):
        switches = json.loads((COMPONENT / rel).read_text(encoding="utf-8"))["entity"]["switch"]
        assert switches["inverter_power"]["name"] == "Inverter Power", rel
        assert switches["ac_output"]["name"] == "AC Output", rel
