"""Controls must be backed by a register, and scoped to the models that have it.

`WRITABLE_REGISTERS` (const.py) defines a control; a profile's `holding_registers` decides
whether it is offered. Nothing checked the two against each other — the sensor side has
`test_sensor_integrity.py`, the control side had nothing — so a control could name a
register no profile maps, or a profile could offer one its hardware rejects, and neither
showed up until a user wrote to it.

#371 is what that costs. MOD TL3-XH mapped 1090 and 1092 while the entire holding block
1000-1124 is unimplemented on that firmware: both reject writes with exception 2. Users
were shown two grid-charge switches, one of which silently did nothing.
"""
from __future__ import annotations

import importlib
from pathlib import Path

import pytest

_const = importlib.import_module("growatt_under_test.const")
_dp = importlib.import_module("growatt_under_test.device_profiles")
_profiles = importlib.import_module("growatt_under_test.profiles")

WRITABLE_REGISTERS = _const.WRITABLE_REGISTERS
REGISTER_MAPS = _profiles.REGISTER_MAPS


def _holding(map_key: str) -> dict:
    return REGISTER_MAPS.get(map_key, {}).get("holding_registers", {})


@pytest.mark.parametrize("control_name", sorted(WRITABLE_REGISTERS))
def test_every_control_is_offered_by_at_least_one_profile(control_name):
    """A control no profile maps is dead weight: it can never be created, and it reads as
    a supported feature to anyone scanning const.py."""
    register = WRITABLE_REGISTERS[control_name].get("register")
    assert register is not None, f"{control_name} has no register"
    offering = [k for k in REGISTER_MAPS if register in _holding(k)]
    assert offering, (
        f"control '{control_name}' names register {register}, which no register map "
        f"defines as a holding register. Either a profile lost it, or the control should "
        f"go with it."
    )


# There is deliberately no test for the reverse direction — "every RW register in a
# profile must have a control". It was written and removed: `access: 'RW'` records what
# the hardware permits, not what we choose to expose, and 32 of 34 maps failed it on
# register 0 (on_off), 30 (modbus_address) and assorted VPP settings that nobody wants as
# a Home Assistant entity. An assertion that fires on correct code teaches people to
# silence it.


# ---------------------------------------------------------------------------
# MOD TL3-XH: the holding block 1000-1124 is unimplemented (#343, #362, #371)
# ---------------------------------------------------------------------------

MOD_XH_MAPS = ["MOD_6000_15000TL3_XH"]
DEAD_MOD_HOLDING = {
    1071: "discharge_stopped_soc  (use 3067)",
    1090: "charge_power_rate      (use 3047)",
    1091: "charge_stopped_soc     (use 3048)",
    1092: "ac_charge_enable       (use 3049)",
}


@pytest.mark.parametrize("map_key", MOD_XH_MAPS)
@pytest.mark.parametrize("addr", sorted(DEAD_MOD_HOLDING))
def test_mod_xh_does_not_map_the_dead_holding_block(map_key, addr):
    """Measured dead across three firmware lines. 1071/1091 accept writes and ignore them;
    1090/1092 reject with exception 2. A full holding sweep on DN1.0 read 0 of 125
    registers non-zero across 1000-1124 (#371)."""
    assert addr not in _holding(map_key), (
        f"{map_key} maps holding {addr} ({DEAD_MOD_HOLDING[addr]}). The whole 1000-1124 "
        f"block is unimplemented on this family; mapping it creates a control that cannot "
        f"work and shows no error when used."
    )


@pytest.mark.parametrize("map_key", MOD_XH_MAPS)
def test_mod_xh_still_offers_the_working_replacements(map_key):
    """Removing the dead registers is only safe because these exist. If one of these ever
    goes, the family loses the capability rather than gaining a correct control."""
    for addr, what in ((3047, "charge power rate"), (3048, "charge stop SOC"),
                       (3049, "allow grid charge"), (3067, "discharge stop SOC")):
        assert addr in _holding(map_key), f"{map_key} lost {addr} ({what})"


# ---------------------------------------------------------------------------
# MOD TL3-XH peak shaving (#372) and VPP state (#373)
# ---------------------------------------------------------------------------

UNDOCUMENTED_MOD_REGISTERS = {
    3307: "demand_import_limit",
    3308: "demand_export_limit",
    3310: "peak_shaving_reserve_soc",
    3311: "ac_charge_max_power",
    3312: "grid_charge_stopped_soc",
}


@pytest.mark.parametrize("addr,name", sorted(UNDOCUMENTED_MOD_REGISTERS.items()))
def test_peak_shaving_registers_are_mapped_with_their_provenance(addr, name):
    """These appear in no public protocol document — protocol-v139.md has no holding
    semantics above 3282. The only evidence is a portal round-trip on one machine, so each
    entry has to say so rather than reading like documented fact."""
    reg = _holding("MOD_6000_15000TL3_XH").get(addr)
    assert reg is not None, f"holding {addr} ({name}) is not mapped"
    assert reg["name"] == name
    assert "#372" in reg.get("desc", ""), (
        f"holding {addr} does not cite its evidence. It is undocumented by Growatt; "
        f"without the reference nobody can tell how it was established."
    )


def test_only_3312_is_writable_in_the_peak_shaving_cluster():
    """3312 is the one with a demonstrated need and a verified write. The rest are
    portal-managed settings — exposing writes we have not tested invites a bad value in a
    register with no public documentation."""
    holding = _holding("MOD_6000_15000TL3_XH")
    writable = sorted(
        a for a in UNDOCUMENTED_MOD_REGISTERS
        if str(holding[a].get("access", "")).upper() == "RW"
    )
    assert writable == [3312], f"expected only 3312 writable, got {writable}"


@pytest.mark.parametrize("addr", [30100, 30407, 30408, 30409, 30410, 30474])
def test_mod_vpp_registers_are_read_only(addr):
    """#373 established that this family supports remote power control, and also that the
    power value is a target rather than a cap: at 100% it climbed toward the setpoint and
    imported from the grid with allow_grid_charge off. Until that is guarded, these are
    exposed for visibility only."""
    reg = _holding("MOD_6000_15000TL3_XH").get(addr)
    assert reg is not None, f"holding {addr} is not mapped on MOD-XH"
    assert str(reg.get("access", "")).upper() in ("RO", "R"), (
        f"holding {addr} is writable on MOD-XH. Commanding VPP power on this family needs "
        f"a guard against importing from the grid to reach the setpoint (#373)."
    )


def test_the_wit_gate_still_confines_writable_vpp_controls():
    """`access: 'RO'` in the profile does not by itself stop a control being created —
    number.py and select.py key off WRITABLE_REGISTERS plus profile membership, not the
    access flag. What actually keeps MOD read-only is the WIT-only name check.

    So if that gate becomes a capability probe, MOD gains writable VPP controls the moment
    its hardware answers — including the power setpoint that #373 measured importing from
    the grid to reach its target. That is the change to make deliberately, with a guard,
    not to arrive at by refactoring.
    """
    src = (Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
           / "select.py").read_text(encoding="utf-8")
    assert "is_wit = str(register_map_name).upper() in" in src, (
        "the WIT gate in select.py has changed shape. If it is now a capability probe, "
        "MOD-XH will gain writable VPP controls — #373 defers those until commanding "
        "power is bounded against available PV."
    )
