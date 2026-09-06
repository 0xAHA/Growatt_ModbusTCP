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


# The five that are now writable, and the two that must never be.
VPP_WRITABLE = [30100, 30407, 30408, 30409, 30410]
VPP_READ_ONLY = [30474, 30476]


@pytest.mark.parametrize("addr", VPP_WRITABLE + VPP_READ_ONLY)
def test_the_vpp_registers_are_mapped_at_all(addr):
    """Rule 4. Every assertion below is about what a mapping says; none of them mean
    anything if the register has quietly stopped being mapped."""
    assert _holding("MOD_6000_15000TL3_XH").get(addr) is not None, (
        f"holding {addr} is not mapped on MOD-XH"
    )


@pytest.mark.parametrize("addr", VPP_READ_ONLY)
def test_the_mirror_and_the_reserve_stay_read_only(addr):
    """30474 mirrors the last commanded setpoint - 102 register changes in the
    30410-30477 range on one day, every one of them on 30474, each mirroring 30409. A
    write is accepted and ignored: the echo returns the written value while the read-back
    keeps the old one. Offered as a control it could only lie about what it is doing.

    30476 is `Reserve` in the V2.01 table and the default-mode selector in the V2.03
    3.3.3 diagram. Visible as a sensor, not offered as a control, because nobody has
    measured what writing it does (#373).
    """
    reg = _holding("MOD_6000_15000TL3_XH")[addr]
    assert _const.is_read_only_register(reg), (
        f"holding {addr} is writable on MOD-XH; it is a mirror or an unmeasured reserve"
    )


@pytest.mark.parametrize("addr", VPP_WRITABLE)
def test_the_vpp_controls_are_writable(addr):
    """These were read-only while commanding VPP power was unguarded (#374). A field
    measurement on #373 established what the controls actually do, and they are now
    offered - disabled by default, which is the test below."""
    reg = _holding("MOD_6000_15000TL3_XH")[addr]
    assert not _const.is_read_only_register(reg), (
        f"holding {addr} is read-only again on MOD-XH"
    )


@pytest.mark.parametrize("addr", VPP_WRITABLE)
def test_every_exposed_vpp_control_is_disabled_by_default(addr):
    """THE safety property, and the reason these could be exposed at all.

    A standing control_authority does not compete with the RTU scheduler - it removes it
    from circuit. Per V2.03 3.3.3, with authority held and an empty scheduler block the
    inverter enters the VPP model and 3047, 3049 and the Battery First slot all stop
    applying together. Measured: 84 minutes at 30100=1 bought 0.04 kWh against a plan of
    3.53; released, 51 minutes bought 4.33 kWh and took SoC 37 -> 65 %.

    It fails silently. No error, no entity going unavailable, nothing in a log - the
    reporter took 84 minutes to notice while watching at 1 Hz. A control whose failure
    mode is a night of cheap-rate charging that never happened must not arrive switched
    on by somebody merely updating.
    """
    names = {n for n, cfg in WRITABLE_REGISTERS.items() if cfg.get("register") == addr}
    assert names, f"no control is defined for register {addr}"
    for name in names:
        assert WRITABLE_REGISTERS[name].get("disabled_by_default") is True, (
            f"{name} (register {addr}) would be created enabled. It can silently stop grid "
            f"charging; it has to be opt-in."
        )


def test_control_authority_says_what_enabling_it_does():
    """Nine words that would have saved 84 minutes. If the description is ever trimmed,
    the control becomes a toggle whose consequence is invisible until the bill arrives."""
    desc = _holding("MOD_6000_15000TL3_XH")[30100].get("desc", "").lower()
    assert "tou schedule out of circuit" in desc, (
        "control_authority no longer warns that enabling it takes the TOU schedule out of "
        "circuit"
    )


def test_both_platforms_honour_disabled_by_default():
    """Three of the five are selects and two are numbers. number.py has had this since
    #384; select.py had not, so without it the pair would have shipped half disabled -
    and control_authority, the one that matters most, is a select.
    """
    from pathlib import Path
    component = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
    for platform in ("number.py", "select.py"):
        source = (component / platform).read_text(encoding="utf-8")
        assert "disabled_by_default" in source, (
            f"{platform} ignores disabled_by_default, so controls marked opt-in arrive "
            f"switched on"
        )


# ---------------------------------------------------------------------------
# No control may exist for a register its profile marks read-only (#374)
# ---------------------------------------------------------------------------
#
# This replaces two tests that passed while the defect shipped, which is worth recording
# because both were the wrong shape rather than merely incomplete:
#
#   test_mod_vpp_registers_are_read_only    asserted the `access` flag was 'RO'. It was.
#                                           Nothing read the flag, so the assertion was
#                                           true and meaningless.
#   test_the_wit_gate_still_confines_...    asserted the WIT gate still had its shape. It
#                                           did. But the gate only returns *inside* the
#                                           WIT branch — non-WIT profiles fall through to
#                                           the generic loop it was believed to confine.
#
# Both tested a declaration, or a mechanism believed to enforce it, rather than the
# outcome. v1.6.0 created five writable VPP controls on MOD with both passing, including a
# -100..+100% power slider on the register measured importing from the grid to reach its
# setpoint. The tests below assert the outcome instead.


PLATFORMS = ("number.py", "select.py")


def test_both_control_platforms_consult_the_read_only_flag():
    """The load-bearing test. Everything below models the loops; this checks the loops.

    `_controls_created_for` applies the read-only filter itself, so on its own it would
    pass whatever number.py and select.py actually do — a model of the code agreeing with
    itself. That is the shape of mistake that let v1.6.0 ship: a test asserting a
    declaration rather than an outcome.
    """
    component = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
    for platform in PLATFORMS:
        src = (component / platform).read_text(encoding="utf-8")
        assert "is_read_only_register" in src, (
            f"{platform} never consults the read-only flag, so a profile marking a "
            f"register RO does not stop the control being created — which is exactly "
            f"what shipped in v1.6.0 (#374)"
        )


def _controls_created_for(map_key: str) -> set[str]:
    """Control names the generic loops would create for a profile.

    Mirrors the filters in number.py/select.py: profile membership, the read-only flag,
    only_profiles/not_profiles. Bespoke classes and the live-confirmation skips are not
    modelled — they can only ever remove entities from this set, never add one, so a
    control absent here cannot appear in Home Assistant.

    This is a model, not the code. Pair it with
    test_both_control_platforms_consult_the_read_only_flag, which checks the real thing.
    """
    holding = _holding(map_key)
    created = set()
    for name, cfg in WRITABLE_REGISTERS.items():
        addr = cfg.get("register")
        if addr not in holding:
            continue
        if _const.is_read_only_register(holding.get(addr)):
            continue
        only = cfg.get("only_profiles")
        if only and map_key not in only:
            continue
        not_p = cfg.get("not_profiles")
        if not_p and map_key in not_p:
            continue
        created.add(name)
    return created


@pytest.mark.parametrize("map_key", sorted(REGISTER_MAPS))
def test_no_control_is_created_for_a_read_only_register(map_key):
    """The general rule. A profile marking a register read-only is a statement that the
    hardware will not accept a write, and the only way to honour it is not to offer the
    control."""
    holding = _holding(map_key)
    offending = sorted(
        name for name in _controls_created_for(map_key)
        if _const.is_read_only_register(holding.get(WRITABLE_REGISTERS[name]["register"]))
    )
    assert not offending, f"{map_key} would create controls for read-only registers: {offending}"


@pytest.mark.parametrize("addr", VPP_READ_ONLY)
def test_mod_creates_no_vpp_control(addr):
    """The specific case, stated as the user-visible outcome rather than a flag.

    Each of these had a control in v1.6.0: two selects, two numbers, and control_authority
    arriving 8 seconds later through the deferred-registration path.
    """
    created = _controls_created_for("MOD_6000_15000TL3_XH")
    named = {
        name for name, cfg in WRITABLE_REGISTERS.items() if cfg.get("register") == addr
    }
    leaked = sorted(named & created)
    assert not leaked, (
        f"MOD-XH would create {leaked} for register {addr}, which is a mirror or an "
        f"unmeasured reserve rather than a control."
    )


def test_the_deferred_path_honours_read_only_too():
    """Gating only the setup loop fixes four of the five.

    control_authority is skipped at setup for want of live data, then added by the
    deferred listener once the first poll confirms 30100 answers — which is exactly what
    the reported log shows happening 8 seconds in. The two paths have to agree.
    """
    src = (Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
           / "select.py").read_text(encoding="utf-8")
    deferred = src[src.index("deferred_vpp: list"):src.index("if deferred_vpp:")]
    assert "is_read_only_register" in deferred, (
        "the deferred VPP registration path does not check the read-only flag, so a "
        "control withheld at setup will be added a few seconds later anyway"
    )


def test_mod_still_creates_the_controls_it_should():
    """The counterweight. It would be easy to fix #374 by withholding too much."""
    created = _controls_created_for("MOD_6000_15000TL3_XH")
    for expected in ("batt_first_charge_power_rate", "batt_first_charge_stopped_soc",
                     "grid_first_discharge_stopped_soc", "grid_charge_stopped_soc"):
        assert expected in created, f"MOD-XH lost the {expected} control"
