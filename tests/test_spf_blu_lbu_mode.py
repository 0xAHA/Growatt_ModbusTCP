"""SPF gains the BLU/LBU energy priority control on holding 116 (#437).

Growatt added the setting to the SPF 6000 ES Plus in firmware 100.08/101.07. The reporter
established the mapping by writing each value and reading the inverter's own screen back:
**0 = BLU, 1 = LBU**.

The register is not new to the protocol. The off-grid table calls it `uwLoadFirst` and
documents three orderings - 0 charge first, 1 load first, 2 feed first - which are the same
three the SPE profile already exposes as BLU / LBU / LUB (Battery-Load-Utility,
Load-Battery-Utility, Load-Utility-Battery). The naming differs between Growatt's own
documents; the register does not.

Two things this file pins, because both are easy to undo by tidying:

  * **SPF gets two options, not three.** The reporter's hardware shows exactly two on its
    screen and has no LUB. Widening `spe_output_priority`'s `only_profiles` to cover SPF
    would have been the smaller diff and would have offered a third mode this hardware does
    not implement - a control that writes a value the inverter has no meaning for.

  * **It is not called "Output Priority".** SPF already has `output_config` (SBU / SOL /
    UTI / SUB) under that name. A second control called something similar reads as the same
    setting, and these are different: one picks the output source, the other picks what PV
    energy serves first.
"""
from __future__ import annotations

import importlib

import pytest

_const = importlib.import_module("growatt_under_test.const")
_gm = importlib.import_module("growatt_under_test.growatt_modbus")

SPF_MAP = "SPF_3000_6000_ES_PLUS"
SPE_MAP = "SPE_8000_12000_ES"
CONTROL = "spf_blu_lbu_mode"


def _control():
    return _const.WRITABLE_REGISTERS[CONTROL]


def test_the_control_exists_on_register_116():
    control = _control()

    assert control["register"] == 116
    assert control["options"] == {0: "BLU", 1: "LBU"}


def test_only_two_options_are_offered():
    """THE point of a separate entry. The reporter's firmware has no LUB, so a third
    option would write a mode the hardware does not implement."""
    options = _control()["options"]

    assert len(options) == 2, f"SPF is being offered {len(options)} orderings, not two"
    assert 2 not in options, "LUB is offered on SPF, which has no such mode"
    assert _control()["valid_range"] == (0, 1)


def test_it_is_scoped_to_spf_and_nothing_else():
    """A control on a register another profile maps differently must not leak. 116 is
    `spe_output_priority` on SPE, with three values."""
    assert _control()["only_profiles"] == [SPF_MAP]

    spe = _const.WRITABLE_REGISTERS["spe_output_priority"]
    assert spe["only_profiles"] == [SPE_MAP]
    assert spe["register"] == 116
    assert len(spe["options"]) == 3, "the SPE control lost its third ordering"


def test_the_two_controls_do_not_both_apply_to_one_profile():
    """Register 116 carries a different option set per family, so exactly one control may
    claim it for any given register map."""
    claimants = {
        name: definition["only_profiles"]
        for name, definition in _const.WRITABLE_REGISTERS.items()
        if definition.get("register") == 116
    }
    assert claimants, "nothing maps register 116 any more"

    for profile in (SPF_MAP, SPE_MAP):
        applies = [name for name, profiles in claimants.items() if profile in profiles]
        assert len(applies) == 1, (
            f"{profile} would offer {len(applies)} controls on register 116: {applies}"
        )


def test_the_register_is_mapped_writable_in_the_spf_profile():
    """The read is gated on the register being in the profile's holding map, so without
    this entry the select would be write-only and show unknown."""
    holding = _const.REGISTER_MAPS[SPF_MAP]["holding_registers"]

    assert 116 in holding, "register 116 is not in the SPF holding map"
    assert holding[116]["name"] == CONTROL
    assert holding[116]["values"] == {0: "BLU", 1: "LBU"}
    assert not _const.is_read_only_register(holding[116]), (
        "the register is marked read-only, so no control would be created for it"
    )


def test_the_value_has_somewhere_to_land():
    """`current_option` reads the control name off GrowattData. Without a field the select
    reports unknown for ever, which is what the SPE control does today."""
    assert hasattr(_gm.GrowattData(), CONTROL)


def test_the_name_cannot_be_confused_with_output_config():
    """SPF's existing `output_config` is 'Output source priority'. These are different
    settings and must not read as the same one."""
    label = _control()["label"]

    assert "BLU" in label and "LBU" in label, f"label {label!r} does not name the modes"
    assert "output priority" not in label.lower(), (
        f"label {label!r} collides with SPF's existing Output Priority control"
    )


def test_no_other_profile_gained_the_register():
    """Gated on the profile because it is an off-grid register that only SPF maps -
    adding it to the shared holding ranges would make every other model pay for the read."""
    for name, register_map in _const.REGISTER_MAPS.items():
        if name == SPF_MAP:
            continue
        holding = register_map.get("holding_registers", {})
        if 116 in holding:
            assert name == SPE_MAP, (
                f"{name} maps register 116 as {holding[116].get('name')}, which now "
                f"collides with the SPF control"
            )


def test_the_read_is_gated_on_the_profile():
    """Source-level: the poll must not read 116 on a profile that does not map it."""
    source = _gm.__file__
    with open(source, encoding="utf-8") as handle:
        text = handle.read()

    assert "if 116 in holding_map:" in text, (
        "the BLU/LBU read is no longer gated on the profile mapping the register"
    )
