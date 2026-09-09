"""Grid power must come from a meter or not be claimed at all (#228).

Grid Power, Grid Export Power and Grid Import Power are three views of one quantity, and
each derived it with its own byte-identical copy of the same logic. Two defects therefore
lived in all three at once.

**A negative reading was ignored.** `meter_power` is a single signed register. The MID
V2.01 profile negates it on combine, so an importing site arrives as a *negative*
`power_to_grid` - deliberately. Nothing tested for that, so the meter reading was thrown
away exactly when it said "importing".

**The estimate ran with nothing to estimate from.** Without a smart meter the directional
registers read 0, and on a grid-tied profile `charge_power` and `discharge_power` are not
mapped. `(solar + 0) - (0 + 0)` is `solar`, published as grid flow. @majliSK's portal
showed **240 W import** while Home Assistant showed **74 W export** - which was his PV
output wearing a grid label, and matched his Solar Total Power to the watt.

`mid.py` already documented that those registers read 0 without a meter and that the AC
power entities are what to use instead. The sensor was overriding its own profile's
documentation with a fabrication, which is why this is tested at the derivation rather
than at the profile.

**A meter reading of zero was thrown away too** (found on a WIT, 2026-09-08). Where a
meter IS fitted, 0/0 is what a balanced site reads - a battery covering the house exactly.
Both directional tests fail on it, so the estimate ran and published `(0 + discharge)` as
grid flow: 605.5 W of export byte-identical to the battery discharge, on an evening when
the portal showed no export at all. The Energy dashboard then computed home consumption as
`battery_out - grid_out` = 0. Believing the meter is gated on a profile flag, because on a
hybrid with no meter the same 0/0 means the opposite and the estimate is right there.

The helper is extracted with `ast` and executed: `sensor.py` imports Home Assistant, which
the tests/ suite does not have, but the function itself is pure and touches only `getattr`.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

COMPONENT = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"


def _load_helper():
    source = (COMPONENT / "sensor.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    fn = next(
        n for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef) and n.name == "_signed_grid_power"
    )
    namespace: dict = {}
    exec(compile(ast.parse(ast.get_source_segment(source, fn)), "<grid>", "exec"), namespace)
    return namespace["_signed_grid_power"]


signed_grid_power = _load_helper()


class _Data:
    """Only the attributes the derivation reads. Absent ones behave as a profile that
    does not map them, which is the grid-tied case."""

    def __init__(self, **values):
        for key, value in values.items():
            setattr(self, key, value)


def test_a_metered_import_is_not_discarded():
    """THE #228 regression. mid.py negates meter_power so import arrives negative; the old
    code tested only `> 0` twice and fell through to the estimate."""
    # -240 W: importing 240 W, as the profile delivers it.
    assert signed_grid_power(_Data(power_to_grid=-240.0)) == -240.0


def test_solar_alone_is_not_published_as_grid_power():
    """@majliSK's case exactly: 74 W of PV, no meter, no battery registers on a grid-tied
    profile. The old code returned 74.0 and labelled it export while he was importing."""
    result = signed_grid_power(_Data(power_to_grid=0, power_to_user=0, pv_total_power=74.0))

    assert result is None, (
        f"returned {result} — with nothing to balance solar against this is just the PV "
        f"reading, and publishing it claims a grid flow we cannot measure"
    )


def test_an_idle_site_still_reports_zero():
    """Guard against over-correcting into uselessness: no generation and no flow is a
    genuine zero, not an unknown."""
    assert signed_grid_power(_Data(power_to_grid=0, power_to_user=0, pv_total_power=0)) == 0.0


def test_the_estimate_still_runs_when_there_is_something_to_balance():
    """A hybrid with a load reading keeps the behaviour it had. 3000 W solar, 1200 W load,
    500 W charging leaves 1300 W going out."""
    result = signed_grid_power(_Data(
        power_to_grid=0, power_to_user=0,
        pv_total_power=3000.0, power_to_load=1200.0, charge_power=500.0, discharge_power=0.0,
    ))
    assert result == pytest.approx(1300.0)


def test_a_battery_alone_is_enough_to_balance_against():
    """Discharging with no load register mapped is still a real balance, not a fabrication."""
    result = signed_grid_power(_Data(
        power_to_grid=0, power_to_user=0, pv_total_power=0.0, discharge_power=800.0,
    ))
    assert result == pytest.approx(800.0)


@pytest.mark.parametrize(
    "values, expected",
    [
        ({"power_to_grid": 1500.0}, 1500.0),          # metered export
        ({"power_to_user": 900.0}, -900.0),           # metered import, legacy register
        ({"power_to_grid": 0, "power_to_user": 900.0}, -900.0),
    ],
)
def test_direct_register_readings_always_win(values, expected):
    """A real directional reading must never be second-guessed by the estimate."""
    assert signed_grid_power(_Data(**values)) == expected


def test_missing_attributes_do_not_raise():
    """Profiles map different subsets; the derivation sees whatever GrowattData carries."""
    assert signed_grid_power(_Data()) == 0.0


def test_none_valued_attributes_are_treated_as_absent():
    """Withheld readings arrive as None rather than 0 since #384, and `None > 0` raises."""
    assert signed_grid_power(_Data(power_to_grid=None, power_to_user=None,
                                   pv_total_power=None)) == 0.0


# ---------------------------------------------------------------------------
# A meter that read zero has told us something (found on a WIT)
# ---------------------------------------------------------------------------

def test_a_metered_site_in_balance_reports_zero_not_an_estimate():
    """The reference WIT at 20:00 on 2026-09-08: PV down, the battery covering the
    house, both meter registers reading a truthful 0.0 and `power_to_load` reading 0.0
    with it. Before this the estimate ran anyway and published 605.5 W of export that
    did not exist - the battery discharge wearing a grid label."""
    state = _Data(power_to_grid=0.0, power_to_user=0.0, power_to_load=0.0,
                  discharge_power=605.5, charge_power=0.0, pv_total_power=0.0,
                  grid_flow_from_meter_only=True)

    assert signed_grid_power(state) == 0.0


def test_the_fabrication_followed_the_battery_sign_either_way():
    """The same site under either polarity setting. One of these published 605 W of
    import and the other 605 W of export, from a meter reading zero in both - and the
    export is what a discharge experiment checks to decide whether a limit held."""
    discharging = _Data(power_to_grid=0.0, power_to_user=0.0, power_to_load=0.0,
                        discharge_power=605.5, charge_power=0.0,
                        pv_total_power=0.0, grid_flow_from_meter_only=True)
    charging = _Data(power_to_grid=0.0, power_to_user=0.0, power_to_load=0.0,
                     discharge_power=0.0, charge_power=605.5,
                     pv_total_power=0.0, grid_flow_from_meter_only=True)

    assert signed_grid_power(discharging) == 0.0
    assert signed_grid_power(charging) == 0.0


def test_a_real_meter_reading_still_wins_on_a_meter_only_profile():
    """Believing a zero must not mean ignoring a number. The same WIT at 04:00 and at
    midday, importing and exporting through the same registers."""
    importing = _Data(power_to_grid=0.0, power_to_user=259.0, power_to_load=0.0,
                      discharge_power=0.0, charge_power=0.0, pv_total_power=0.0,
                      grid_flow_from_meter_only=True)
    exporting = _Data(power_to_grid=793.0, power_to_user=0.0, power_to_load=0.0,
                      discharge_power=0.0, charge_power=0.0, pv_total_power=3500.0,
                      grid_flow_from_meter_only=True)

    assert signed_grid_power(importing) == -259.0
    assert signed_grid_power(exporting) == 793.0


def test_the_meterless_grid_tied_case_is_still_unknown():
    """#228 must survive: no battery registers mapped and no meter, so a zero reading is
    the absence of a meter rather than a balanced site. Order keeps both answers right."""
    state = _Data(power_to_grid=0.0, power_to_user=0.0, power_to_load=0.0,
                  charge_power=0.0, discharge_power=0.0, pv_total_power=74.0)

    assert signed_grid_power(state) is None


def test_a_meterless_hybrid_still_gets_its_estimate():
    """The counterpart to the WIT case, and the reason the flag exists. Same registers,
    opposite meaning: nothing is reporting, so the balance is the best answer there."""
    state = _Data(power_to_grid=0.0, power_to_user=0.0, pv_total_power=0.0,
                  discharge_power=800.0)

    assert signed_grid_power(state) == pytest.approx(800.0)


def test_a_meter_that_could_not_be_read_is_not_a_zero():
    """Unread beats the value left behind: the estimate must run rather than a stale or
    defaulted 0 being believed as a balanced site."""
    state = _Data(power_to_grid=0.0, power_to_user=0.0,
                  unread_fields={"power_to_grid", "power_to_user"},
                  power_to_load=1000.0, charge_power=500.0,
                  discharge_power=0.0, pv_total_power=3000.0)

    assert signed_grid_power(state) == pytest.approx(1500.0)


def test_an_unread_export_still_believes_a_real_import():
    state = _Data(power_to_grid=0.0, power_to_user=428.1,
                  unread_fields={"power_to_grid"})

    assert signed_grid_power(state) == -428.1


def test_an_estimate_missing_one_of_its_own_inputs_is_unknown():
    """Fixing "unread became zero" at the meter and leaving it in the estimate would
    produce the same class of fabrication one line lower."""
    state = _Data(power_to_grid=0.0, power_to_user=0.0,
                  unread_fields={"power_to_grid", "power_to_user", "power_to_load"},
                  power_to_load=0.0, charge_power=0.0, discharge_power=450.0,
                  pv_total_power=0.0)

    assert signed_grid_power(state) is None


def test_a_meter_only_profile_never_falls_back_to_the_estimate():
    """On the WIT the estimate cannot work: `power_to_load` is mapped and reads 0 while
    the house draws hundreds of watts. An unanswered meter there is unknown, not an
    invitation to calculate."""
    state = _Data(power_to_grid=0.0, power_to_user=0.0,
                  unread_fields={"power_to_grid", "power_to_user"},
                  power_to_load=0.0, charge_power=0.0, discharge_power=800.0,
                  pv_total_power=0.0, grid_flow_from_meter_only=True)

    assert signed_grid_power(state) is None


# ---------------------------------------------------------------------------
# ... and only while the inverter says something is measuring (MeterLink, holding 180)
# ---------------------------------------------------------------------------

def test_a_wit_that_is_not_receiving_its_meter_reports_unknown():
    """V1.39 register 180 MeterLink reads 0 = Missed: nothing is being received from the
    grid-side source. The same 0/0 then means the opposite of a balanced site, and the
    estimate is no better here, so the honest answer is unknown.

    This is the meterless case the manual describes - "Zero export to GRID", inverter
    output restricted to the LOAD port, no meter required - answered by measurement
    rather than by assuming how these sites are usually wired."""
    state = _Data(power_to_grid=0.0, power_to_user=0.0, power_to_load=0.0,
                  discharge_power=605.5, charge_power=0.0, pv_total_power=0.0,
                  grid_flow_from_meter_only=True, meter_link=0)

    assert signed_grid_power(state) is None


def test_a_received_meter_link_believes_the_zero():
    """1 = Received, which is what the reference WIT reads while its meter is live."""
    state = _Data(power_to_grid=0.0, power_to_user=0.0, power_to_load=0.0,
                  discharge_power=605.5, charge_power=0.0, pv_total_power=0.0,
                  grid_flow_from_meter_only=True, meter_link=1)

    assert signed_grid_power(state) == 0.0


def test_a_meter_link_we_never_established_keeps_the_profile_rule():
    """Not mapped, or one dropped holding read. A single failed read must not turn into
    "this site has no meter", so the profile-level answer stands."""
    absent = _Data(power_to_grid=0.0, power_to_user=0.0, power_to_load=0.0,
                   discharge_power=605.5, charge_power=0.0, pv_total_power=0.0,
                   grid_flow_from_meter_only=True)
    unread = _Data(power_to_grid=0.0, power_to_user=0.0, power_to_load=0.0,
                   discharge_power=605.5, charge_power=0.0, pv_total_power=0.0,
                   grid_flow_from_meter_only=True, meter_link=None)

    assert signed_grid_power(absent) == 0.0
    assert signed_grid_power(unread) == 0.0


def test_the_meter_link_gate_cannot_manufacture_a_reading():
    """It only ever narrows. With a real directional reading present, MeterLink is not
    consulted at all - a live register outranks a flag about registers."""
    state = _Data(power_to_grid=793.0, power_to_user=0.0, power_to_load=0.0,
                  discharge_power=0.0, charge_power=0.0, pv_total_power=3500.0,
                  grid_flow_from_meter_only=True, meter_link=0)

    assert signed_grid_power(state) == 793.0


def test_the_wit_profiles_map_the_register_the_read_path_looks_up():
    """The read path finds MeterLink by NAME in the holding map, so a rename or a lost
    mapping would silently disable the gate and take every meterless WIT back to a
    confident zero. The input mirror at 180 is deliberately not used: it read 0 on a unit
    whose holding 180 read 1 in the same second."""
    import importlib
    import sys

    sys.path.insert(0, "tests")
    maps = importlib.import_module("growatt_under_test.profiles").REGISTER_MAPS

    for name, profile in maps.items():
        if not profile.get("grid_flow_from_meter_only"):
            continue
        holding = profile.get("holding_registers", {})
        named = [addr for addr, info in holding.items()
                 if info.get("name") == "meter_link_set"]
        assert named == [180], f"{name}: expected MeterLink at holding 180, got {named}"


def test_the_wit_profiles_declare_what_the_derivation_relies_on():
    """The flag and the behaviour must not drift apart: it is the only thing that makes a
    zero meter believable, and it is asserted where the profiles live rather than assumed
    in the sensor. Nothing else claims it, because nothing else has the hardware
    evidence - 428 W of import read from 8081-8084 while power_to_load read 0.0."""
    import importlib
    import sys

    sys.path.insert(0, "tests")
    maps = importlib.import_module("growatt_under_test.profiles").REGISTER_MAPS

    wit = {name: m for name, m in maps.items() if name.startswith("WIT_")}
    assert wit, "no WIT profiles found"
    for name, profile in wit.items():
        assert profile.get("grid_flow_from_meter_only") is True, name

    others = [name for name, m in maps.items()
              if not name.startswith("WIT_") and m.get("grid_flow_from_meter_only")]
    assert not others, others
