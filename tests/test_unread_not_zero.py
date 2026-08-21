"""A register that could not be read must not be published as zero (#384).

The register cache is emptied at the start of every poll. When a block read failed its
addresses were simply absent, `_get_register_value` returned None, and the decode did
`or 0.0` - turning "I did not read this" into "the value is zero". The next poll recovered,
producing a one-sample vertical drop.

A reporter's solar graph showed exactly that: PV power falling to 0 W and returning to
~1450 W within one poll, with voltage and current dropping alongside it because all three
live in the same block. Nothing errored, because from Home Assistant's side the poll
succeeded.

Zero is not a neutral placeholder here. It is a plausible measurement that goes into
long-term statistics and cannot afterwards be told apart from a real one. An unknown state
leaves a gap, which is unambiguous about what happened.

This is the fifth appearance of the same root cause - see #360, #370, #374 and the residual
noted on #364.
"""
from __future__ import annotations

import importlib

import pytest

_gm = importlib.import_module("growatt_under_test.growatt_modbus")

PV_FIELDS = [f"pv{n}_{k}" for n in (1, 2, 3, 4) for k in ("voltage", "current", "power")]


def _client(cache):
    c = _gm.GrowattModbus(connection_type="tcp", host="10.0.0.1", port=502,
                          register_map="SPF_3000_6000_ES_PLUS")
    c._register_cache = dict(cache)
    return c


def test_a_fresh_container_has_nothing_unread():
    assert _gm.GrowattData().unread_fields == set()


def test_each_container_gets_its_own_set():
    """A mutable default shared across instances would leak one poll's failures into the
    next, which is a worse bug than the one being fixed."""
    a, b = _gm.GrowattData(), _gm.GrowattData()
    a.unread_fields.add("pv1_power")
    assert b.unread_fields == set()


def test_a_missing_register_is_recorded_not_zeroed():
    """The core of it. The field keeps a usable number - several are summed - and the fact
    that it was not read is recorded separately."""
    client = _client({})           # empty cache: the block read failed
    data = _gm.GrowattData()
    addr = client._find_register_by_name('pv1_voltage')
    assert addr, "the test profile has no pv1_voltage register"

    client._set_from_register(data, 'pv1_voltage', addr)
    assert 'pv1_voltage' in data.unread_fields
    assert isinstance(data.pv1_voltage, float), (
        "the field must stay numeric - pv_total_power sums these and None would raise"
    )


def test_a_real_reading_is_assigned_and_not_flagged():
    client = _client({})
    addr = client._find_register_by_name('pv1_voltage')
    client._register_cache = {addr: 2500}
    data = _gm.GrowattData()
    client._set_from_register(data, 'pv1_voltage', addr)
    assert data.pv1_voltage > 0
    assert 'pv1_voltage' not in data.unread_fields


def test_a_genuine_zero_is_still_published():
    """The distinction the old code could not make: an inverter reporting 0 W at night is a
    measurement and must keep being recorded."""
    client = _client({})
    addr = client._find_register_by_name('pv1_voltage')
    client._register_cache = {addr: 0}
    data = _gm.GrowattData()
    client._set_from_register(data, 'pv1_voltage', addr)
    assert data.pv1_voltage == 0.0
    assert 'pv1_voltage' not in data.unread_fields, (
        "a real zero was mistaken for a failed read - the opposite error"
    )


def test_the_pv_decode_no_longer_coerces_to_zero():
    """Guards the conversion itself. The helper existing is not enough if the call sites
    still use `or 0.0`."""
    from pathlib import Path
    source = (Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
              / "growatt_modbus.py").read_text(encoding="utf-8")
    for field in PV_FIELDS:
        assert f"data.{field} = self._get_register_value" not in source, (
            f"{field} still coerces a failed read to 0.0"
        )
        assert f"_set_from_register(data, '{field}'" in source, (
            f"{field} does not go through the unread-aware helper"
        )


def test_the_sensor_reports_unknown_for_an_unread_field():
    """The join between the recording and the entity. Without this the set is collected and
    never consulted, which is the decorative-declaration failure this project has shipped."""
    from pathlib import Path
    source = (Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
              / "sensor.py").read_text(encoding="utf-8")
    assert 'if attr in getattr(data, "unread_fields", ())' in source
    assert source.index('if attr in getattr(data, "unread_fields", ())') < \
           source.index('value = getattr(data, attr, None)'), (
        "the unread check runs after the value is read, so it cannot suppress it"
    )


# --------------------------------------------------------------------------
# Derived fields inherit the read state of their inputs
#
# The first fix covered the twelve fields decoded straight from a register and stopped
# there. Two PV fields are *computed* from those twelve, and both kept publishing a
# confident zero after it: an unread input keeps its 0.0 default, so the arithmetic
# succeeds and produces a number that looks like a measurement.
#
# pv_total_power is the one that matters, because it is what the Solar device's headline
# power sensor and every energy-flow card read.
# --------------------------------------------------------------------------

def _decode_source() -> str:
    from pathlib import Path
    return (Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
            / "growatt_modbus.py").read_text(encoding="utf-8")


def test_the_total_no_longer_coerces_a_failed_read_to_zero():
    """The register branch: profiles that map pv_total_power_low read it directly, and it
    was still going through `or 0.0` after the #384 fix."""
    source = _decode_source()
    assert "data.pv_total_power = self._get_register_value" not in source, (
        "pv_total_power still coerces a failed read to 0.0"
    )
    assert "_set_from_register(data, 'pv_total_power'" in source, (
        "pv_total_power does not go through the unread-aware helper"
    )


def test_the_summed_total_is_not_published_when_a_string_was_unread():
    """The sum branch, which is what SPF and most profiles use — they have no
    pv_total_power register at all, so the total is pv1+pv2+pv3+pv4. Unread strings sit at
    0.0, so the sum is 0.0 and indistinguishable from a genuine night-time reading."""
    source = _decode_source()
    guard = "elif any(f'pv{_pv}_power' in data.unread_fields for _pv in (1, 2, 3, 4)):"
    assert guard in source, (
        "the summed total does not check whether its inputs were read"
    )
    assert source.index(guard) < source.index(
        "data.pv_total_power = data.pv1_power + data.pv2_power"
    ), "the guard runs after the sum, so it cannot suppress it"


def test_a_derived_string_power_is_not_published_when_its_inputs_were_unread():
    """The #361 path: profiles reporting only per-string voltage and current get power as
    V*I. If either input was unread the product is 0.0, which reintroduces exactly the
    defect #384 fixed for the strings that do have a power register."""
    source = _decode_source()
    assert "data.unread_fields.add(f'pv{_pv}_power')" in source, (
        "derived per-string power does not inherit the unread state of V and I"
    )


def test_an_unread_total_reaches_home_assistant_as_unavailable():
    """The join. Recording it in the set is only useful if the sensor consults the set —
    and pv_total_power is read through the same generic path as the twelve fields already
    covered, so this pins that it is not special-cased around the gate."""
    data = _gm.GrowattData()
    data.pv1_power = 0.0
    data.unread_fields.add("pv_total_power")

    attr = "pv_total_power"
    assert attr in getattr(data, "unread_fields", ()), (
        "the sensor gate would read the 0.0 default and publish it as a measurement"
    )
