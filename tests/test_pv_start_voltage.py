"""PV Startup Voltage control on the MIC MIN-range profile (holding 17).

Holding 17 is "Vpv start - Input start voltage, 0.1 V" in protocol V1.39 and V3.14. On a
MIC 2000TL-X with a single high-voltage panel, the 50.0 V factory default let the inverter
connect at dawn before the panel could carry the load; it dropped out, recovered and
reconnected for minutes on end. Raising holding 17 to 65.0 V stopped it.

The control is scoped to MIC_2500_6000TL_X_MIN_RANGE, the profile the register was
confirmed on. These tests drive a real poll of that profile.
"""
from __future__ import annotations

import importlib

_gm = importlib.import_module("growatt_under_test.growatt_modbus")
_const = importlib.import_module("growatt_under_test.const")
_profiles = importlib.import_module("growatt_under_test.profiles")

MAP = "MIC_2500_6000TL_X_MIN_RANGE"

# Field reading from the MIC 2000TL-X after the change: 650 = 65.0 V.
HOLDING = {17: 650}


def _holding(map_key: str) -> dict:
    return _profiles.REGISTER_MAPS[map_key].get("holding_registers", {})


def _poll(holding_reader):
    client = _gm.GrowattModbus(connection_type="tcp", host="10.0.0.1", port=502,
                               slave_id=1, register_map=MAP)
    client.read_input_registers = lambda start, count, log_errors=True: [0] * count
    client.read_holding_registers = holding_reader
    return client.read_all_data()


def _reads(values: dict):
    return lambda start, count: [values.get(a, 0) for a in range(start, start + count)]


def test_holding_17_is_mapped_rw_on_the_mic_min_range_profile():
    reg = _holding(MAP).get(17)
    assert reg is not None, f"{MAP} does not map holding 17"
    assert reg["name"] == "pv_start_voltage"
    assert not _const.is_read_only_register(reg), "holding 17 must be RW to be a control"


def test_the_control_is_created_for_the_mic_min_range_profile_only():
    from tests.test_control_registers import _controls_created_for

    offering = sorted(k for k in _profiles.REGISTER_MAPS
                      if "pv_start_voltage" in _controls_created_for(k))
    assert offering == [MAP]


def test_another_profile_mapping_holding_17_gets_no_control(monkeypatch):
    """Today only the MIC map has holding 17, so the profile alone limits the control.
    `only_profiles` is what keeps it limited once another family maps 17 for reading:
    a MIN 10000TL-X and a MIC 2500-5500MTL-S both read 1000 (100.0 V) there, and the
    control is not verified on either."""
    from tests.test_control_registers import _controls_created_for

    other = next(k for k in sorted(_profiles.REGISTER_MAPS)
                 if k != MAP and 17 not in _holding(k))
    patched = dict(_profiles.REGISTER_MAPS[other])
    patched["holding_registers"] = {**_holding(other), 17: dict(_holding(MAP)[17])}
    monkeypatch.setitem(_profiles.REGISTER_MAPS, other, patched)

    assert "pv_start_voltage" not in _controls_created_for(other)


def test_a_read_of_650_publishes_65_volts():
    data = _poll(_reads(HOLDING))
    assert "pv_start_voltage" not in data.unread_fields
    scale = _const.WRITABLE_REGISTERS["pv_start_voltage"]["scale"]
    assert round(data.pv_start_voltage * scale, 1) == 65.0


def test_a_failed_read_marks_the_field_unread():
    """A failed read must show as unknown, not as a 0 V start voltage."""
    def reader(start, count):
        if (start, count) == (17, 1):
            return None
        return [0] * count

    data = _poll(reader)
    assert "pv_start_voltage" in data.unread_fields


def test_a_raised_exception_marks_the_field_unread():
    def reader(start, count):
        if (start, count) == (17, 1):
            raise OSError("timeout")
        return [0] * count

    data = _poll(reader)
    assert "pv_start_voltage" in data.unread_fields


def test_the_range_holds_every_factory_start_voltage():
    """Home Assistant shows a number as unavailable when its value is outside the range.
    The factory start voltage is 50 V on MIC 600-2000TL-X and 80 V on MIC 2500-3300TL-X
    (datasheet), and holding 17 read 100 V on a MIN 10000TL-X and a MIC 2500-5500MTL-S.
    A range fitted to one panel's Voc (72 V) hid all but the first."""
    lo, hi = _const.WRITABLE_REGISTERS["pv_start_voltage"]["valid_range"]
    for raw in (500, 800, 1000):
        assert lo <= raw <= hi, f"factory start voltage {raw * 0.1:.1f} V is out of range"
