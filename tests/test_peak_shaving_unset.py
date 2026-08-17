"""An unset peak-shaving limit must publish nothing, not a ceiling (#380).

Registers 3307, 3308 and 3311 hold a ceiling rather than zero when peak shaving has never
been configured. The read succeeds, so there is no error, no warning and no unavailable
entity — just a stable, typed, entirely wrong number. On a MID 25KTL3-XH the three raw
values were 30000, 30000 and 65535, which decode at x0.1 to 3000 kW, 3000 kW and 6553.5 kW
on a 25 kW inverter.

This was found before it reached a user, because the reporter was still on v1.5.5 and sent
raw registers rather than a dashboard. It is the same class of defect as #360, #370 and
#374: something that is not a real reading, published as a plausible one.

The tests drive the real read path with a scripted register block and assert what lands on
GrowattData, rather than checking that the source mentions a sentinel. A source-level check
would have passed against the shipped code in #374 while the defect was live.
"""
from __future__ import annotations

import importlib

import pytest

_gm = importlib.import_module("growatt_under_test.growatt_modbus")
_const = importlib.import_module("growatt_under_test.const")

GrowattModbus = _gm.GrowattModbus
GrowattData = _gm.GrowattData

# Measured on the MID 25KTL3-XH that has never had peak shaving configured (#380),
# and on a MOD 10KTL3-XH where it is configured to a real 7.5 kW limit.
MID_UNCONFIGURED = [30000, 30000, 0, 50, 65535, 100]
MOD_CONFIGURED = [75, 75, 0, 50, 75, 100]


def _client() -> GrowattModbus:
    """A client with no transport. Only the decode path is under test."""
    return GrowattModbus(connection_type="tcp", host="10.0.0.1", port=502,
                         register_map="MOD_6000_15000TL3_XH")


def _read(block) -> GrowattData:
    client = _client()
    client.read_holding_registers = lambda addr, count: list(block)
    data = GrowattData()
    client._read_peak_shaving(data)
    return data


@pytest.mark.parametrize("field", ["demand_import_limit", "demand_export_limit",
                                   "ac_charge_max_power"])
def test_unconfigured_limits_are_none_not_a_number(field):
    """The whole point: unavailable beats 3000 kW."""
    value = getattr(_read(MID_UNCONFIGURED), field)
    assert value is None, (
        f"{field} published {value!r} for an unconfigured system. A sensor showing a "
        f"number is indistinguishable from a real reading; None makes it unavailable."
    )


def test_configured_limits_still_decode():
    """A sentinel that also swallows real values would be a worse bug than the one
    being fixed."""
    data = _read(MOD_CONFIGURED)
    assert data.demand_import_limit == 7.5
    assert data.demand_export_limit == 7.5
    assert data.ac_charge_max_power == 7.5


def test_zero_is_a_real_value_and_survives():
    """0 kW is a legitimate limit and must not be confused with unset — which is exactly
    why the default had to become None rather than 0.0."""
    data = _read([0, 0, 0, 50, 0, 100])
    assert data.demand_import_limit == 0.0
    assert data.demand_export_limit == 0.0
    assert data.ac_charge_max_power == 0.0


def test_socs_are_untouched_by_the_sentinel_logic():
    """3310 and 3312 are deliberately excluded: an SOC has no absurd ceiling, so 50 %
    reads identically whether configured or defaulted. Guessing there would be worse
    than leaving it alone."""
    data = _read(MID_UNCONFIGURED)
    assert data.peak_shaving_reserve_soc == 50
    assert data.grid_charge_stopped_soc == 100


def test_defaults_are_none_before_any_read():
    """A failed or skipped read must not leave 0.0 behind either. GrowattData is
    constructed fresh each poll, so the default is what a non-responding block
    publishes."""
    data = GrowattData()
    assert data.demand_import_limit is None
    assert data.demand_export_limit is None
    assert data.ac_charge_max_power is None


def test_a_short_read_assigns_nothing():
    """Guards the length check. A truncated block must not decode whatever arrived."""
    client = _client()
    client.read_holding_registers = lambda addr, count: [75, 75]
    data = GrowattData()
    client._read_peak_shaving(data)
    assert data.demand_import_limit is None
    assert data.ac_charge_max_power is None


@pytest.mark.parametrize("raw", _const.PEAK_SHAVING_UNSET_RAW)
def test_each_declared_sentinel_actually_suppresses(raw):
    """Every value in the tuple must do something. A sentinel listed but not honoured is
    the kind of decorative declaration this project has shipped before."""
    assert GrowattModbus._peak_shaving_kw(raw) is None


def test_the_plausibility_ceiling_catches_unseen_encodings():
    """The sentinel list covers what has been observed. The ceiling is the backstop for
    an unset encoding from a model nobody has scanned yet."""
    limit = _const.PEAK_SHAVING_MAX_PLAUSIBLE_KW
    over = int((limit + 1) * 10)
    assert GrowattModbus._peak_shaving_kw(over) is None
    under = int((limit - 1) * 10)
    assert GrowattModbus._peak_shaving_kw(under) == pytest.approx(limit - 1)
