"""A withheld battery reading must reach the sensors as unknown, not as 0 W (#434).

v2.0.4-b12 added withholding: when a poll's voltage x current contradicts the battery power
scale about to be applied, the read path marks `battery_power`, `charge_power` and
`discharge_power` unread and leaves the fields at 0.0. Battery Charge Power and Battery
Discharge Power went unknown, as intended.

**Battery Power published 0.** It is a *calculated* sensor - rebuilt from charge and
discharge power rather than read from a field - and calculated sensors return from
native_value before the generic "was this read?" check. It saw 0 and 0 and fell through to
a literal `raw_value = 0`. A WIT reporter's history showed exactly that at two polls:

    08:41:31  battery_current -10.3 A   battery_power 0
    08:48:00  battery_current -10.4 A   battery_power 0

Zero is worse than the tenth-of-the-truth the withholding replaced, because zero is what an
idle battery genuinely reads. The same hole was open on the older path too: a battery block
that failed to read (#384) zeroed the same fields and Battery Power published 0 there as
well.

Two other calculated consumers of charge and discharge power had the same exposure:

  * House Consumption balanced solar + discharge - charge + import - export on whatever the
    fields held, so a withheld battery was reported as a house running on solar alone.
  * Grid Power's zero-balance guard read "no load, no battery flow" as an idle site and
    answered 0.0 at night, while the battery was carrying the house.

**Why this file drives the real read path.** The test that shipped with b12 read the source
of growatt_modbus.py and confirmed the withholding branch marked the fields unread. It did,
and the test passed - throughout a bug that lived one module further on, in a consumer the
test never ran. So here the WIT client decodes a register cache, and the GrowattData it
produces is handed to the sensor helpers themselves, extracted with `ast` because sensor.py
imports Home Assistant and this suite does not.
"""
from __future__ import annotations

import ast
import importlib
from pathlib import Path

import pytest

_gm = importlib.import_module("growatt_under_test.growatt_modbus")

COMPONENT = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
WIT_MAP = "WIT_4000_15000TL3"

_HELPERS = ("_signed_battery_power", "_house_consumption", "_signed_grid_power")


def _load_helpers() -> dict:
    """The three sensor helpers, executed from the real source."""
    source = (COMPONENT / "sensor.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    namespace: dict = {}
    for name in _HELPERS:
        fn = next(
            (n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == name),
            None,
        )
        assert fn is not None, f"sensor.py no longer defines {name}"
        exec(compile(ast.parse(ast.get_source_segment(source, fn)), f"<{name}>", "exec"),
             namespace)
    return namespace


_H = _load_helpers()
signed_battery_power = _H["_signed_battery_power"]
house_consumption = _H["_house_consumption"]
signed_grid_power = _H["_signed_grid_power"]


def _u32(watts: int) -> tuple[int, int]:
    """A signed 32-bit reading as the (high, low) words the inverter sends."""
    raw = watts & 0xFFFFFFFF
    return raw >> 16, raw & 0xFFFF


def _wit_poll(power_register_watts: int, volts_x10: int = 523, amps_x10: int = 103) -> dict:
    """A WIT battery block. Defaults are the reporter's 08:41 poll: 52.3 V, 10.3 A
    discharging, with the power register in whole watts rather than the documented tenths.
    31215 and 3170 read zero, as they do on his hardware - only 8035 carries current."""
    high, low = _u32(power_register_watts)
    return {
        8034: volts_x10,
        8035: amps_x10,
        31215: 0,
        3170: 0,
        8093: 60,
        31200: high,
        31201: low,
    }


def _read(cache: dict):
    client = _gm.GrowattModbus(connection_type="tcp", host="10.0.0.1", port=502,
                              register_map=WIT_MAP)
    client._register_cache = dict(cache)
    data = _gm.GrowattData()
    client._read_battery_data(data)
    return client, data


# ---------------------------------------------------------------------------
# The chain, end to end
# ---------------------------------------------------------------------------

def test_the_read_path_withholds_the_disputed_poll():
    """Precondition for everything below: this cache really does trigger the withholding.
    If it stops doing so, the sensor assertions would pass for the wrong reason."""
    # 52.3 V x 10.3 A = 539 W. The register says 539 - right at 1.0, a tenth at 0.1.
    client, data = _read(_wit_poll(-539))
    assert client._battery_power_scale_disputed is True, (
        "the fixture no longer produces a disputed scale, so these tests prove nothing"
    )
    assert {"charge_power", "discharge_power"} <= data.unread_fields


def test_battery_power_is_unknown_not_zero():
    """THE regression. The reporter's history showed `0` here."""
    _client, data = _read(_wit_poll(-539))
    result = signed_battery_power(data)
    assert result is None, (
        f"Battery Power published {result!r} for a withheld reading - an idle-looking "
        f"number where the battery was discharging 539 W"
    )


def test_house_consumption_is_unknown_not_solar_alone():
    _client, data = _read(_wit_poll(-539))
    data.pv_total_power = 1200.0   # read, and non-zero
    result = house_consumption(data)
    assert result is None, (
        f"House Consumption published {result!r} - the balance ran with the battery terms "
        f"zeroed, so the load the battery was carrying vanished from it"
    )


def test_grid_power_does_not_call_a_withheld_battery_an_idle_site():
    """At night: no solar, no meter flow, no load register. With the battery withheld the
    zero-balance guard used to answer 0.0 - a site at rest - while 539 W left the battery."""
    _client, data = _read(_wit_poll(-539))
    data.pv_total_power = 0.0
    data.power_to_grid = 0.0
    data.power_to_user = 0.0
    data.power_to_load = 0.0
    assert signed_grid_power(data) != 0.0


# ---------------------------------------------------------------------------
# What must not change
# ---------------------------------------------------------------------------

def test_a_battery_that_was_read_still_reports():
    """The documented scale agreeing with voltage x current is no dispute. 52.3 V x 10.3 A
    is 539 W, and at the documented 0.1 that is a register of 5390."""
    client, data = _read(_wit_poll(-5390))
    assert client._battery_power_scale_disputed is False
    assert "discharge_power" not in data.unread_fields
    assert signed_battery_power(data) == pytest.approx(-539.0)


def test_an_idle_battery_still_reads_zero():
    """A genuine zero is a measurement and must keep being published. No current, no power:
    detection has nothing to act on, so nothing is withheld."""
    _client, data = _read(_wit_poll(0, amps_x10=0))
    assert not ({"charge_power", "discharge_power"} & data.unread_fields)
    assert signed_battery_power(data) == 0.0


def test_a_working_load_register_is_still_believed():
    """The balance is only the fallback. A load register that was read and is non-zero
    answers on its own, whatever state the battery terms are in."""

    class _D:
        unread_fields = {"charge_power", "discharge_power"}
        power_to_load = 850.0

    assert house_consumption(_D()) == pytest.approx(850.0)


def test_a_grid_tied_site_at_rest_is_still_zero():
    """#228's guard over-correcting into uselessness was the thing to avoid. A profile that
    never maps battery registers has them at their defaults and NOT unread - nothing was
    withheld - so an idle site with no generation is still a genuine 0."""

    class _D:
        unread_fields: set = set()
        power_to_grid = 0.0
        power_to_user = 0.0
        pv_total_power = 0.0

    assert signed_grid_power(_D()) == 0.0


def test_charge_and_discharge_both_read_keep_their_sign():
    class _D:
        unread_fields: set = set()
        charge_power = 1234.5
        discharge_power = 0.0

    assert signed_battery_power(_D()) == pytest.approx(1234.5)
