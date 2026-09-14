"""Off-grid holding register 3 is a schedule hour, not a power rate (#444).

V1.39 gives holding 3 as the active power rate, and `max_output_power_rate` is correct for
every grid-tied family. The off-grid protocol table gives the same address to something
else entirely:

    3 | UtiOutStart    | Uti Time             | W | bit0~bit7
    4 | UtiOutEnd      | Uti Output End Time  | W | bit0~bit7
    5 | UtiChargeStart | Uti Time             | W | bit0~bit7
    6 | UtiChargeEnd   | Uti Charge End Time  | W | bit0~bit7

Hours, 0-23. ShinePhone shows them as the output and charging period times, LCD programs 50
and 49. So on an SPF the "Max Output Power Rate" entity read **0 %** while the inverter was
delivering full output - and it is **writable**, so anyone setting the limit to 100 would
have written **hour 100** into the inverter's output schedule.

Reported by @eugeniodb, who checked the whole SPF control set against the app and the SPF
3500/5000 ES manual v4.0. His raw dump reads `3: 0, 4: 0, 5: 0, 6: 0` - the factory default
of 0000, not a failed read, which is what distinguishes this from a register that simply is
not answering.

This is the register-overlap trap the project warns about, with the twist that the two
meanings live in different *protocols* rather than different spaces: same address, same
holding space, different document.
"""
from __future__ import annotations

import importlib

import pytest

_const = importlib.import_module("growatt_under_test.const")

OFFGRID_MAPS = ("SPF_3000_6000_ES_PLUS", "SPE_8000_12000_ES")


def test_the_power_rate_control_is_withheld_from_offgrid_profiles():
    """THE regression. A writable percentage pointed at a schedule hour."""
    control = _const.WRITABLE_REGISTERS["max_output_power_rate"]

    assert control["register"] == 3
    excluded = control.get("not_profiles") or []
    for map_name in OFFGRID_MAPS:
        assert map_name in excluded, (
            f"{map_name} is still offered Max Output Power Rate on register 3, which on the "
            f"off-grid protocol is the utility output start hour - writing 100 there sets "
            f"hour 100 in the inverter's schedule"
        )


def test_grid_tied_profiles_keep_the_control():
    """Guard against over-correcting: register 3 really is the active power rate on V1.39,
    and this control works for everyone else."""
    excluded = set(_const.WRITABLE_REGISTERS["max_output_power_rate"].get("not_profiles") or [])

    grid_tied = [
        name for name in _const.REGISTER_MAPS
        if not _const.REGISTER_MAPS[name].get("offgrid_protocol")
    ]
    assert grid_tied, "no grid-tied maps found"
    assert not (set(grid_tied) & excluded), (
        f"a grid-tied profile has been excluded from the power rate control: "
        f"{sorted(set(grid_tied) & excluded)}"
    )


@pytest.mark.parametrize("map_name", OFFGRID_MAPS)
def test_the_offgrid_profiles_name_register_3_for_what_it_is(map_name):
    """Renamed rather than deleted, so the next person reading the profile sees a schedule
    hour instead of rediscovering it."""
    info = _const.REGISTER_MAPS[map_name]["holding_registers"].get(3)

    assert info is not None, f"{map_name} dropped register 3 entirely"
    assert "power_rate" not in info["name"], (
        f"{map_name} still calls register 3 {info['name']!r}, which is the grid-tied meaning"
    )
    assert info["name"] == "uti_out_start"
    assert info.get("unit") == "h", "the unit should say hours, not percent"


@pytest.mark.parametrize("map_name", OFFGRID_MAPS)
def test_no_control_targets_register_3_on_offgrid(map_name):
    """The general property. Any control on register 3 that reaches an off-grid profile
    has the same problem, whatever it is called."""
    offenders = []
    for name, control in _const.WRITABLE_REGISTERS.items():
        if control.get("register") != 3:
            continue
        only = control.get("only_profiles")
        if only and map_name not in only:
            continue
        if map_name in (control.get("not_profiles") or []):
            continue
        offenders.append(name)

    assert not offenders, (
        f"{map_name} would offer {offenders} on register 3, which is a schedule hour on "
        f"this protocol"
    )
