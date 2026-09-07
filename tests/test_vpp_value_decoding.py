"""A control's option list and the profile's decode must agree (#373).

Two defects of the same shape, both shipped in v1.10.0 and both found by @KevlarD-67 reading
the release rather than running it.

**30410 decoded two values where the register has three.** `WRITABLE_REGISTERS` offers
Disabled / PV priority / AC priority, matching VPP 2.03 and `wit.py`; `mod.py` listed only
Disabled / Enabled. So the control could write a `2` that the sensor then rendered as unknown
- a control and a sensor for one register disagreeing about what it means.

**30407's labels were inverted against the evidence in their own comment.** The measurement
recorded three paragraphs above them has Growatt's scheduler moving 12.3 kWh through the
*roster* branch while 30407 read 0, yet 0 was labelled "Direct setpoint". Selecting
"Roster/TOU schedule" wrote the value that selects the other branch.

Neither is caught by anything else: a `values` dict is free-text as far as the loader is
concerned, and nothing compared it against `WRITABLE_REGISTERS` or against the protocol.
"""
from __future__ import annotations

import importlib
import sys

import pytest

sys.path.insert(0, "tests")

CONST = importlib.import_module("growatt_under_test.const")
PROFILES = importlib.import_module("growatt_under_test.profiles").REGISTER_MAPS

# Profiles carrying a VPP holding block with decode tables.
VPP_PROFILES = ["MOD_6000_15000TL3_XH", "WIT_4000_15000TL3"]


def _holding(profile: str, address: int) -> dict | None:
    return PROFILES[profile].get("holding_registers", {}).get(address)


def test_ac_charge_enable_decodes_all_three_documented_values():
    """THE regression. VPP 2.03 documents 0 = not enabled, 1 = AC charge with PV priority,
    2 = AC charge with AC priority. A profile that stops at 1 turns a live 2 into unknown."""
    for profile in VPP_PROFILES:
        register = _holding(profile, 30410)
        if register is None or "values" not in register:
            continue
        values = register["values"]
        assert set(values) == {0, 1, 2}, (
            f"{profile} decodes 30410 as {sorted(values)}; the register has three documented "
            f"values and the control offers three"
        )


def test_the_control_and_the_profile_agree_on_ac_charge_enable():
    """A control writing options the sensor cannot decode is the actual defect - the two
    tables are describing one register and must not drift apart."""
    offered = set(CONST.WRITABLE_REGISTERS["vpp_ac_charge_enable"]["options"])

    for profile in VPP_PROFILES:
        register = _holding(profile, 30410)
        if register is None or "values" not in register:
            continue
        assert set(register["values"]) == offered, (
            f"{profile} decodes {sorted(register['values'])} for 30410 while the control "
            f"offers {sorted(offered)}"
        )


def test_every_writable_option_can_be_decoded_by_the_profile():
    """The general form, so the next control to gain an option is caught rather than the
    next one to lose a decode."""
    mismatches = []
    for name, config in CONST.WRITABLE_REGISTERS.items():
        options = config.get("options")
        if not options:
            continue
        address = config["register"]
        for profile in VPP_PROFILES:
            register = _holding(profile, address)
            if register is None or "values" not in register:
                continue
            undecodable = set(options) - set(register["values"])
            if undecodable:
                mismatches.append(f"{profile} {name} ({address}): cannot decode {sorted(undecodable)}")

    assert not mismatches, (
        "controls offer values the profile cannot decode, so a live reading renders as "
        "unknown:\n  " + "\n  ".join(mismatches)
    )


def test_the_branch_selector_labels_match_the_measurement():
    """30407 is a branch selector, not an enable, and the labels must follow the evidence
    rather than the register's name.

    The measurement: Growatt's own scheduler put 12.30 kWh into a battery through the roster
    branch across two hours while 30407 stood at **0** the whole time (#349). So 0 is the
    roster branch.

    Corroborated from the other side by the WIT control path, which sets 30407 = 1 and then
    drives 30409 - the direct setpoint - and is reported working.
    """
    register = _holding("MOD_6000_15000TL3_XH", 30407)
    assert register is not None and "values" in register, "30407 has no decode table"

    values = register["values"]
    assert "Roster" in values[0], (
        f"30407 value 0 is labelled {values[0]!r}; the measurement has the roster branch "
        f"driving while this register read 0"
    )
    assert "Direct" in values[1], (
        f"30407 value 1 is labelled {values[1]!r}; 1 is the direct-setpoint branch"
    )


def test_the_branch_selector_is_not_described_as_an_enable():
    """The name says enable and the behaviour is a selector. Anyone testing this register to
    answer "is external power control active" gets the wrong answer - 30100 is the authority
    bit."""
    register = _holding("MOD_6000_15000TL3_XH", 30407)
    description = register["desc"].lower()

    assert "not a master" in description or "selects" in description, (
        "30407's description does not say it is a branch selector"
    )
    for label in register["values"].values():
        assert label.lower() not in ("enabled", "disabled"), (
            f"30407 still offers {label!r}, which reads as an on/off switch"
        )
