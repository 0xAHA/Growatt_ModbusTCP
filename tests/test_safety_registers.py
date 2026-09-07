"""ISO / DCI / GFCI come from input 200-205, not 3087-3091 (#404).

Four scans showed the old block returning text rather than measurements. `22616` is
`0x5858` — ASCII **"XX"** — and three different quantities came back with the same value on
the same device. V1.39 documents holding 3087-3092 as Serial Number 1-6, so what was being
published as an insulation resistance of 2261.6 kOhm was serial-number characters.

**Input, not holding.** Holding 201/202/203 are PID working mode, PID on/off and PID output
voltage — write registers for an entirely different subsystem. Reading the wrong space here
would present a PID configuration value as a DC injection current.

The mapping is confirmed from outside this project: Growatt's own app shows `Gfci(mA)` and
`Iso(KOhm)` next to the values our scan reads from 205 and 200.

`pv_iso` is withheld when it reads the not-measured sentinel. Two unrelated inverters report
exactly 65530 (`0xFFFA`), and Growatt's app shows the same 65530 rather than a resistance —
so it is what the inverter sends. A falling insulation resistance is how water in a connector
gets found, so a fixed 65530 that looks like a healthy array is worse than no sensor at all.
"""
from __future__ import annotations

import ast
import importlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, "tests")

PROFILES = importlib.import_module("growatt_under_test.profiles").REGISTER_MAPS
COMPONENT = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"

# Every profile that carried the old block, including the ones that inherit it.
AFFECTED = [
    "MIN_7000_10000TL_X",
    "MIN_7000_10000TL_X_V201",
    "MOD_6000_15000TL3_XH",
    "MIN_TL_XH_3000_10000_V201",
]

SAFETY_NAMES = {"pv_iso", "dci_r", "dci_s", "dci_t", "gfci"}


@pytest.mark.parametrize("profile", AFFECTED)
def test_the_serial_number_block_is_gone(profile):
    """THE regression. 3087-3091 returned ASCII text on every scan we have."""
    registers = PROFILES[profile]["input_registers"]

    for address in (3087, 3088, 3089, 3090, 3091):
        if address in registers:
            assert registers[address]["name"] not in SAFETY_NAMES, (
                f"{profile} still reads a safety measurement from {address}, which returns "
                f"serial-number text"
            )


@pytest.mark.parametrize("profile", AFFECTED)
def test_iso_and_gfci_come_from_the_confirmed_addresses(profile):
    """200 and 205 are the two confirmed against Growatt's own app."""
    registers = PROFILES[profile]["input_registers"]

    assert registers[200]["name"] == "pv_iso"
    assert registers[200]["scale"] == 1
    assert registers[205]["name"] == "gfci"
    assert registers[205]["scale"] == 1


@pytest.mark.parametrize("profile", AFFECTED)
def test_dci_uses_the_documented_tenth_milliamp_scale(profile):
    """V1.39 documents R/S/T DCI in 0.1 mA. At scale 1 a 2823 reading would publish as
    2823 mA of DC injection, which would look like a serious fault."""
    registers = PROFILES[profile]["input_registers"]

    assert registers[201]["name"] == "dci_r"
    assert registers[201]["scale"] == 0.1


def test_three_phase_dci_is_only_on_the_three_phase_profile():
    """S and T phases do not exist on a single-phase MIN. Mapping them there would create
    two entities that can only ever read zero."""
    assert PROFILES["MOD_6000_15000TL3_XH"]["input_registers"][202]["name"] == "dci_s"
    assert PROFILES["MOD_6000_15000TL3_XH"]["input_registers"][203]["name"] == "dci_t"

    for profile in ("MIN_7000_10000TL_X", "MIN_TL_XH_3000_10000_V201"):
        registers = PROFILES[profile]["input_registers"]
        for address in (202, 203):
            assert registers.get(address, {}).get("name") not in {"dci_s", "dci_t"}, (
                f"{profile} is single-phase and should not map an S or T phase DCI"
            )


@pytest.mark.parametrize("profile", AFFECTED)
def test_the_pid_write_registers_are_not_confused_with_these(profile):
    """The overlap. Holding 201/202/203 are PID working mode, PID on/off and PID output
    voltage — writable controls for a different subsystem entirely."""
    holding = PROFILES[profile].get("holding_registers", {})

    for address in (200, 201, 202, 203, 205):
        if address in holding:
            assert holding[address]["name"] not in SAFETY_NAMES, (
                f"{profile} maps a safety measurement into the HOLDING space at {address}, "
                f"where the PID controls live"
            )


def test_the_not_measured_sentinel_is_withheld_rather_than_published():
    """The value two devices actually report. Published, it reads as a 65 MOhm array in
    perfect health — the opposite of what a safety sensor is for.

    Asserted against the shipped constant and the branch that uses it, rather than a
    hard-coded 65530, so changing the threshold moves this test with it.
    """
    source = (COMPONENT / "growatt_modbus.py").read_text(encoding="utf-8")
    tree = ast.parse(source)

    threshold = None
    for node in ast.walk(tree):
        if (isinstance(node, ast.Assign)
                and any(getattr(t, "attr", getattr(t, "id", None)) == "PV_ISO_NOT_MEASURED_MIN"
                        for t in node.targets)):
            threshold = node.value.value
    assert threshold is not None, "the sentinel threshold constant is gone"
    assert threshold <= 65530, (
        f"the threshold is {threshold}, so the observed 65530 sentinel would be published"
    )
    assert threshold > 41077, (
        f"the threshold is {threshold}, which would withhold the highest reading anyone has "
        f"seen behaving like a real measurement (41077 kOhm)"
    )

    assert "if _attr == 'pv_iso' and _v >= self.PV_ISO_NOT_MEASURED_MIN:" in source, (
        "nothing checks the sentinel"
    )
    assert "data.unread_fields.add(_attr)" in source, (
        "the sentinel is not withheld — it would reach the sensor as a number"
    )


def test_a_failed_read_is_withheld_too():
    """Unread is not zero. A DC injection current of 0.0 mA reads as a healthy inverter,
    which is exactly the wrong thing to show when the register did not answer."""
    source = (COMPONENT / "growatt_modbus.py").read_text(encoding="utf-8")

    assert "if _v is None:\n                    data.unread_fields.add(_attr)" in source, (
        "a register that did not answer leaves the previous value or a default in place"
    )
