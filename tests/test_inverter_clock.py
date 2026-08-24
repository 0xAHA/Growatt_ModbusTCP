"""Setting the inverter's real-time clock (#393).

The inverter runs its own RTC and it drifts. That matters because time-of-use windows fire
against the *inverter's* clock, not Home Assistant's — a reporter's 13:00 export window
started two minutes late, and the drift was the reason.

Protocol V1.39 documents holding registers 45-51 as writable:

    45 Sys Year | 46 Sys Month | 47 Sys Day
    48 Sys Hour | 49 Sys Min   | 50 Sys Sec  | 51 Sys Weekly

Confirmed on hardware from two unrelated device classes before implementing:

* an SPH 3600 read 2026/8/22 14:08:19 with weekday 6, and 22 August 2026 was a Saturday —
  so the weekday field counts Monday as 1
* a GroHomeManager-X (DTC 82) on a different site read 2026/8/22 09:42:17 in the same
  registers

The year is the full four digits on both. The off-grid protocol uses the same addresses but
records "Year offset is 2000" and assigns register 51 to Chip Select, so writing this block
to an SPF would set the year wrong and clobber an unrelated register.
"""
from __future__ import annotations

import importlib
from datetime import datetime

import pytest

_gm = importlib.import_module("growatt_under_test.growatt_modbus")


class _FakeClock:
    """Records writes and serves a scripted clock reading.

    Both write paths are captured. The weekday (51) is always written on its own — never as
    part of the block — because not every model implements it and an FC16 spanning a missing
    address fails as a whole, taking the six good registers with it.
    """

    def __init__(self, registers=None):
        self.registers = registers
        self.written = None      # the FC16 block, if one was accepted
        self.singles = {}        # register -> value, for single writes

    def read_holding_registers(self, start, count):
        self.last_read = (start, count)
        if self.registers is None:
            return None
        return self.registers[:count]

    def write_registers(self, register, values):
        self.written = (register, list(values))
        return True

    def write_single(self, register, value):
        self.singles[register] = value
        return True


def _client(offgrid=False, registers=None):
    profile = "SPF_3000_6000_ES_PLUS" if offgrid else "SPH_3000_6000"
    client = _gm.GrowattModbus(connection_type="tcp", host="10.0.0.1", port=502,
                               register_map=profile)
    fake = _FakeClock(registers)
    client.read_holding_registers = fake.read_holding_registers
    client.write_registers = fake.write_registers
    client.write_single_register_any_fc = fake.write_single
    client._fake = fake
    return client


# --------------------------------------------------------------------------
# Reading
# --------------------------------------------------------------------------

def test_the_reporters_registers_decode_to_his_timestamp():
    """The exact values from the SPH scan, including the Saturday weekday."""
    client = _client(registers=[2026, 8, 22, 14, 8, 19, 6])
    assert client.read_inverter_time() == datetime(2026, 8, 22, 14, 8, 19)


def test_the_gro_home_manager_registers_decode_too():
    """A different device class on a different site, same layout."""
    client = _client(registers=[2026, 8, 22, 9, 42, 17, 6])
    assert client.read_inverter_time() == datetime(2026, 8, 22, 9, 42, 17)


def test_it_reads_the_documented_block():
    client = _client(registers=[2026, 8, 22, 14, 8, 19, 6])
    client.read_inverter_time()
    assert client._fake.last_read == (45, 7)


def test_an_unreadable_clock_returns_none_rather_than_raising():
    """A fresh or unconfigured inverter can hold zeroes here. The caller still needs to be
    able to set the clock, so this must not blow up."""
    assert _client(registers=[0, 0, 0, 0, 0, 0, 0]).read_inverter_time() is None
    assert _client(registers=None).read_inverter_time() is None
    assert _client(registers=[2026, 13, 40, 99, 99, 99, 9]).read_inverter_time() is None


def test_a_short_response_is_not_decoded():
    assert _client(registers=[2026, 8, 22]).read_inverter_time() is None


# --------------------------------------------------------------------------
# Writing
# --------------------------------------------------------------------------

def test_the_clock_is_written_as_one_atomic_block():
    """Writing the registers one at a time could straddle a minute boundary and set a time
    that never existed."""
    client = _client(registers=[2026, 8, 22, 14, 8, 19, 6])
    client.write_inverter_time(datetime(2026, 8, 25, 9, 30, 5))

    register, values = client._fake.written
    assert register == 45
    assert values == [2026, 8, 25, 9, 30, 5], "the block must cover 45-50 only"
    # The weekday goes separately so a model without register 51 still gets its clock.
    assert client._fake.singles == {51: 2}  # 25 Aug 2026 is a Tuesday → 2


@pytest.mark.parametrize(
    "when,weekday",
    [
        (datetime(2026, 8, 24), 1),  # Monday
        (datetime(2026, 8, 22), 6),  # Saturday — matches the reporter's scan
        (datetime(2026, 8, 23), 7),  # Sunday
    ],
)
def test_the_weekday_field_counts_monday_as_one(when, weekday):
    client = _client(registers=[2026, 8, 22, 14, 8, 19, 6])
    client.write_inverter_time(when)
    assert client._fake.singles[51] == weekday


def test_a_refused_block_falls_back_to_single_registers():
    """Reported on the maintainer's own inverter: FC 0x10 across 45-51 came back as an error
    even though the registers are writable. Without a fallback the action failed outright."""
    client = _client(registers=[2026, 8, 22, 14, 8, 19, 6])
    singles = {}

    def refuse_block(register, values):
        raise _gm.ModbusWriteError(register, values, "refused")

    client.write_registers = refuse_block
    client.write_single_register_any_fc = lambda r, v: singles.setdefault(r, v) is v

    assert client.write_inverter_time(datetime(2026, 8, 25, 9, 30, 5)) is True
    assert singles == {45: 2026, 46: 8, 47: 25, 48: 9, 49: 30, 50: 5, 51: 2}


def test_a_refused_weekday_does_not_fail_the_sync():
    """The weekday is derivable and schedules do not use it. Losing it must not cost the
    user a clock that would otherwise have been set."""
    client = _client(registers=[2026, 8, 22, 14, 8, 19, 6])
    written = {}

    def refuse_block(register, values):
        raise _gm.ModbusWriteError(register, values, "refused")

    def single(register, value):
        if register == 51:
            return False  # weekday refused
        written[register] = value
        return True

    client.write_registers = refuse_block
    client.write_single_register_any_fc = single

    assert client.write_inverter_time(datetime(2026, 8, 25, 9, 30, 5)) is True
    assert set(written) == {45, 46, 47, 48, 49, 50}


def test_a_clock_register_refused_both_ways_raises():
    """If the date itself will not take, the caller must hear about it rather than believe
    the clock was set."""
    client = _client(registers=[2026, 8, 22, 14, 8, 19, 6])

    def refuse_block(register, values):
        raise _gm.ModbusWriteError(register, values, "refused")

    client.write_registers = refuse_block
    client.write_single_register_any_fc = lambda r, v: False

    with pytest.raises(_gm.ModbusWriteError) as excinfo:
        client.write_inverter_time(datetime(2026, 8, 25, 9, 30, 5))
    # The message must name the registers, so the log says which one the model refuses.
    assert "45" in str(excinfo.value)


def test_a_two_digit_year_is_decoded_as_this_century():
    """Some models store the year as an offset from 2000. Without this a "26" decodes as the
    year 26 AD and the reported drift is two millennia."""
    client = _client(registers=[26, 8, 22, 14, 8, 19, 6])
    assert client.read_inverter_time() == datetime(2026, 8, 22, 14, 8, 19)


def test_the_year_format_is_taken_from_the_register_not_guessed():
    """A MIN TL-X refused 2026 and its year register afterwards read 2000, having read 2026
    before — so a rejected write is not necessarily a write that did nothing. Probing with a
    value the firmware may clamp can leave the clock worse than it started, so the encoding
    is read rather than tried (#393)."""
    client = _client(registers=[26, 8, 22, 14, 8, 19, 6])   # two-digit model
    client.write_inverter_time(datetime(2026, 8, 25, 9, 30, 5))
    assert client._fake.written[1][0] == 26, "a two-digit model was sent a four-digit year"


def test_a_four_digit_model_is_never_sent_two_digits():
    """The dangerous direction. Writing 26 to a model expecting 2026 would set the year to
    the first century, and on at least one model the firmware clamps rather than refusing."""
    client = _client(registers=[2026, 8, 22, 14, 8, 19, 6])
    client.write_inverter_time(datetime(2026, 8, 25, 9, 30, 5))
    assert client._fake.written[1][0] == 2026


def test_a_partial_write_is_reported_as_such():
    """The single-register fallback cannot be atomic. If some fields landed and one did not,
    the user needs to know the clock is part-updated rather than untouched."""
    client = _client(registers=[2026, 8, 22, 14, 8, 19, 6])

    def refuse_block(register, values):
        raise _gm.ModbusWriteError(register, values, "refused")

    client.write_registers = refuse_block
    # Everything except the year succeeds, and the two-digit retry fails too.
    client.write_single_register_any_fc = lambda r, v: r != 45

    with pytest.raises(_gm.ModbusWriteError) as excinfo:
        client.write_inverter_time(datetime(2026, 8, 25, 9, 30, 5))

    message = str(excinfo.value)
    assert "[45]" in message, "the refused register is not named"
    assert "46" in message, "the registers that did land are not reported"


def test_the_block_write_is_still_preferred():
    """The fallback must not become the normal path — an atomic write is what stops the
    clock briefly holding a mix of old and new fields."""
    client = _client(registers=[2026, 8, 22, 14, 8, 19, 6])

    def single(register, value):
        # 51 is expected here — it is always written on its own. Any of 45-50 arriving
        # individually means the block path was abandoned when it had worked.
        if register != 51:
            pytest.fail(
                f"register {register} was written individually even though the block "
                f"write succeeded"
            )
        return True

    client.write_single_register_any_fc = single
    assert client.write_inverter_time(datetime(2026, 8, 25, 9, 30, 5)) is True
    assert client._fake.written[0] == 45


def test_the_year_is_written_in_full():
    """The off-grid protocol offsets the year from 2000; V1.39 does not, and both scans read
    a full four-digit year."""
    client = _client(registers=[2026, 8, 22, 14, 8, 19, 6])
    client.write_inverter_time(datetime(2026, 8, 25, 9, 30, 5))
    assert client._fake.written[1][0] == 2026


# --------------------------------------------------------------------------
# Off-grid is excluded, deliberately
# --------------------------------------------------------------------------

def test_off_grid_profiles_report_no_clock_support():
    assert _client(offgrid=True).is_clock_supported is False
    assert _client(offgrid=False).is_clock_supported is True


def test_off_grid_reads_return_none():
    client = _client(offgrid=True, registers=[26, 8, 22, 14, 8, 19, 1])
    assert client.read_inverter_time() is None


def test_off_grid_writes_are_refused_rather_than_guessed():
    """Writing the V1.39 layout to an SPF would set the year to 2026 where the firmware
    expects 26, and overwrite Chip Select at register 51."""
    client = _client(offgrid=True)
    with pytest.raises(_gm.ModbusWriteError):
        client.write_inverter_time(datetime(2026, 8, 25, 9, 30, 5))
    assert client._fake.written is None, "an off-grid inverter was written to anyway"


# --------------------------------------------------------------------------
# Service wiring
# --------------------------------------------------------------------------

def test_the_service_is_registered_and_documented():
    from pathlib import Path
    import yaml

    component = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
    source = (component / "diagnostic.py").read_text(encoding="utf-8")
    assert 'SERVICE_SYNC_INVERTER_TIME = "sync_inverter_time"' in source
    assert "async def sync_inverter_time(call: ServiceCall)" in source
    assert "supports_response=SupportsResponse.OPTIONAL" in source

    services = yaml.safe_load((component / "services.yaml").read_text(encoding="utf-8"))
    assert "sync_inverter_time" in services, "the service is not exposed in the UI"
    assert set(services["sync_inverter_time"]["fields"]) == {"device_id", "min_drift_seconds"}
