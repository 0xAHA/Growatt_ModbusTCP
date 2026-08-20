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
