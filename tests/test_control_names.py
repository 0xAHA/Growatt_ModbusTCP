"""Display names for writable controls (#407).

Names came from three places and the last of them was `key.replace('_',' ').title()`, which
lowercases every acronym: "Ac Charge Enable", "Charge Stopped Soc", "Vpp Export Limit
Enable". It also surfaced raw register abbreviations - "Bat Low To Uti" is the battery-to-
utility switchover voltage, and is the register from #402 where someone left his inverter on
a threshold he never chose.

Names now live in WRITABLE_REGISTERS['label'], which select.py and time.py already read, so
a control's name no longer depends on which platform happens to create it.
"""
import ast
import importlib
import io
import re
import sys

import pytest

sys.path.insert(0, "tests")

_const = importlib.import_module("growatt_under_test.const")
WRITABLE = _const.WRITABLE_REGISTERS

_src = io.open("custom_components/growatt_modbus/number.py", encoding="utf-8").read()
_OVERRIDES = ast.literal_eval(
    "{" + re.search(r"friendly_overrides\s*=\s*\{(.*?)\n        \}", _src, re.S).group(1) + "}"
)

# Acronyms that title-casing destroys. Not exhaustive of English, just of this domain.
_ACRONYMS = re.compile(
    r"\b(Ac|Dc|Soc|Soh|Pv|Bms|Vpp|Spe|Spf|Sph|Uti|Eps|Ct|Tou|Iso|Gfci|Dci|Mppt)\b"
)


def display_name(key: str) -> str:
    """Mirror the resolution order in number.py: label, then override, then title-case."""
    cfg = WRITABLE[key]
    return cfg.get("label") or _OVERRIDES.get(key) or key.replace("_", " ").title()


def test_no_control_name_has_a_mangled_acronym():
    bad = {k: display_name(k) for k in WRITABLE if _ACRONYMS.search(display_name(k))}
    assert not bad, f"title-casing has lowercased an acronym: {bad}"


def test_the_ac_charge_block_reads_as_one_block():
    """Three controls that operate together were sorted apart with nothing connecting them.
    The prefix names the register block - 1090, 1091 and 1092 are adjacent - not an
    operating mode, which is what made the prefixes removed in #362 misleading."""
    for key in ("charge_power_rate", "charge_stopped_soc", "ac_charge_enable"):
        assert display_name(key).startswith("AC Charge"), (
            f"{key} is {display_name(key)!r}, which does not group with its block"
        )


def test_the_charge_stop_soc_names_no_longer_collide():
    """1091 and 3048 differed only by the capitalisation of "Soc". No profile maps both, so
    nobody saw them side by side - but it was ambiguous everywhere they were written down."""
    assert display_name("charge_stopped_soc") != display_name("batt_first_charge_stopped_soc")


@pytest.mark.parametrize("key", ["bat_low_to_uti", "ac_to_bat_volt"])
def test_the_cryptic_register_abbreviations_are_gone(key):
    """"Bat Low To Uti" tells a user nothing about what they are setting, and this is the
    control from #402 where a slider drag left an inverter on the wrong threshold."""
    name = display_name(key)
    # Whole words only - "Utility" legitimately begins with the mangled token "Uti".
    assert not re.search(r"(Uti|Bat|Volt)", name), f"{key} still reads as {name!r}"
    assert "Voltage" in name, f"{key} should say what it is: {name!r}"


def test_number_entities_read_the_shared_label():
    """select.py and time.py already used WRITABLE_REGISTERS['label']. If number.py stops
    consulting it, the same control gets two different names depending on its platform."""
    body = _src[_src.index("class GrowattGenericNumber"):]
    body = body[:body.index("\nclass ")]
    assert "control_config.get('label')" in body, (
        "number.py no longer prefers the shared label"
    )


def test_the_discharge_collision_is_still_recorded_as_unresolved():
    """1071 and 3067 still share a name. That is deliberate: #362 measured what 3067 does,
    but nobody has established what 1071 governs, and it is one of the two registers on
    record as accepting writes and silently ignoring them. A name asserting a scope we have
    not measured would be a guess dressed as documentation.

    This test exists so the day someone tests 1071, the decision is revisited rather than
    forgotten."""
    assert display_name("discharge_stopped_soc") == display_name(
        "grid_first_discharge_stopped_soc"
    ), "1071 has been given a distinguishing name - if that rests on a measurement, update #407"
