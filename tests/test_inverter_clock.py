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
        self.order = []          # registers in the order they were written

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
        self.order.append(register)
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
#
# Method taken from a published, working ESP32 implementation for an SPH5000
# (cosminpop.uk, Feb 2026), corroborated by an ESPHome forum finding three years earlier
# and by two failures on this tracker.
#
# The load-bearing fact: **the year is written as year-2000 and read back as four digits.**
# Write 26, read 2026. Neither protocol document records that for the V1.39 range, and an
# earlier version of this method detected the format by reading the register — which can
# only ever see the four-digit form, so it always wrote the value the inverter rejects.
# --------------------------------------------------------------------------

def test_the_year_is_written_as_an_offset_from_2000():
    """The whole point. `create_write_single_command(ctl, 45, time.year - 2000)`."""
    client = _client(registers=[2026, 8, 22, 14, 8, 19, 6])
    client.write_inverter_time(datetime(2026, 8, 25, 9, 30, 5))
    assert client._fake.singles[45] == 26, "the four-digit year is what the inverter refuses"


def test_all_six_fields_are_written_individually_in_order():
    """The reference writes one register per field rather than a block, year first."""
    client = _client(registers=[2026, 8, 22, 14, 8, 19, 6])
    client.write_inverter_time(datetime(2026, 8, 25, 9, 30, 5))

    assert client._fake.order == [45, 46, 47, 48, 49, 50]
    assert client._fake.singles == {45: 26, 46: 8, 47: 25, 48: 9, 49: 30, 50: 5}


def test_no_block_write_is_attempted():
    """A MIN TL-X and an SPH both refused FC 0x10 across this range. The reference uses
    single writes, and the RTC block is documented there as accepting them even where other
    settings registers do not."""
    client = _client(registers=[2026, 8, 22, 14, 8, 19, 6])
    client.write_registers = lambda register, values: pytest.fail(
        f"a block write to {register} was attempted"
    )
    assert client.write_inverter_time(datetime(2026, 8, 25, 9, 30, 5)) is True


def test_the_writes_are_paced():
    """The reference spaces them; these registers are committed one at a time."""
    client = _client(registers=[2026, 8, 22, 14, 8, 19, 6])
    assert client.CLOCK_WRITE_INTERVAL > 0

    sleeps = []
    import growatt_under_test.growatt_modbus as gm
    original = gm.time.sleep
    gm.time.sleep = lambda s: sleeps.append(s)
    try:
        client.write_inverter_time(datetime(2026, 8, 25, 9, 30, 5))
    finally:
        gm.time.sleep = original

    # Five gaps between six writes, and none before the first.
    assert len(sleeps) == 5
    assert all(s == client.CLOCK_WRITE_INTERVAL for s in sleeps)


def test_a_refused_year_leaves_the_clock_untouched():
    """The year goes first precisely so this is possible. A MIN TL-X reset its RTC to the
    year 2000 when five fields landed and the year did not."""
    client = _client(registers=[2026, 8, 22, 14, 8, 19, 6])
    client.write_single_register_any_fc = lambda r, v: r != 45

    with pytest.raises(_gm.ModbusWriteError) as excinfo:
        client.write_inverter_time(datetime(2026, 8, 25, 9, 30, 5))

    assert client._fake.singles == {}, "fields were written after the year was refused"
    assert "Nothing else was written" in str(excinfo.value)


def test_a_later_field_refused_is_reported_as_a_partial_write():
    """If the year lands and something after it does not, the clock really is part-updated
    and the user must be told rather than left to notice."""
    client = _client(registers=[2026, 8, 22, 14, 8, 19, 6])
    real = client._fake.write_single
    client.write_single_register_any_fc = lambda r, v: False if r == 48 else real(r, v)

    with pytest.raises(_gm.ModbusWriteError) as excinfo:
        client.write_inverter_time(datetime(2026, 8, 25, 9, 30, 5))

    message = str(excinfo.value)
    assert "part-updated" in message
    assert "hour" in message, "the failing field is not named"


def test_verification_compares_against_the_four_digit_year():
    """The register reads back 2026 having been written 26. Comparing the written value
    against the read value would report a mismatch on every successful sync."""
    client = _client(registers=[2026, 8, 25, 9, 30, 5, 2])
    caplog_free = client.write_inverter_time(datetime(2026, 8, 25, 9, 30, 5))
    assert caplog_free is True  # no exception, and the read-back agrees


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


def test_the_undocumented_year_encoding_stays_documented():
    """The year register takes two digits and reports four. That is in neither protocol
    document and it is the reason three earlier builds failed, so the explanation has to
    survive somewhere a maintainer will find it.

    It now lives in the docs rather than being repeated in the service picker: the action
    is confirmed working on a MIN TL-X, so the encoding is implementation detail rather
    than a caveat every user needs at the point of use. What the UI description must still
    carry is the scope limit, because that one changes what the action will do (#393)."""
    from pathlib import Path
    import yaml

    root = Path(__file__).parent.parent
    component = root / "custom_components" / "growatt_modbus"

    docs = (root / "docs" / "controls" / "actions.md").read_text(encoding="utf-8")
    assert "two-digit year" in docs, "the docs no longer explain the year encoding"
    assert "MIN TL-X" in docs, "the docs do not name the model it is confirmed on"
    assert "issues/393" in docs, "the docs do not say where to report other models"

    services = yaml.safe_load((component / "services.yaml").read_text(encoding="utf-8"))
    description = services["sync_inverter_time"]["description"]
    assert "SPF/SPE" in description, (
        "the UI description does not state that off-grid models are excluded"
    )


def test_routine_spf_sign_corrections_are_not_logged_as_warnings():
    """Status 12 corrections fire many times a day on an off-grid inverter in normal
    operation. At warning level they land in Home Assistant's error log looking like a
    fault, and a reporter raised them twice as "this error" while chasing something
    unrelated. The code's own comment says the hardware sign is *expected* to be unreliable
    in that state, so the correction working is not news (#384)."""
    from pathlib import Path

    source = (Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
              / "growatt_modbus.py").read_text(encoding="utf-8")

    block = source[source.index("if status == 12:"):]
    block = block[:block.index("return battery_power")]
    assert "logger.warning" not in block, (
        "a routine status-12 sign correction is still logged at warning level"
    )
    assert block.count("logger.debug") == 2, "both correction branches should log at debug"
