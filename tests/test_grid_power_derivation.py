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
