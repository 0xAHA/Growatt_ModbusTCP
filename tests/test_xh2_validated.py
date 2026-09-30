"""MIN TL-XH2 findings from a MIN 3000TL-XH2 with an APX 5.0M-B3 (#461), and the battery
pack registers read on a MIN 4200TL-XH (#460).

The XH2 answers only the VPP ranges. Three things on its profile assumed otherwise:

* The Inverter Clock read holding 45-51, in the dead base range, so it stayed unavailable
  while 30104-30109 held the right time.
* Status came from 31000 - there is no register 0 to find - but was rendered with the
  grid-tied table. 31000 is the VPP working state, documented with the hybrid table, and
  the reporter's inverter read 6, which the grid-tied table has no entry for.
* The controls the reporter validated (30405, 30407-30410) were not mapped.

Each test here drives the real client over a register cache built from the reporter's
own values, rather than reading the source for the change.
"""
from __future__ import annotations

import importlib

_gm = importlib.import_module("growatt_under_test.growatt_modbus")
_const = importlib.import_module("growatt_under_test.const")
_profiles = importlib.import_module("growatt_under_test.profiles")

XH2 = "MIN_TL_XH2_3000_10000_V201"
MIN_TL_XH = "MIN_TL_XH_3000_10000_V201"

# Holding 30104-30109 as the reporter read them: 26 / 9 / 30 / 20 / 13 / 33.
XH2_CLOCK = {30104: 26, 30105: 9, 30106: 30, 30107: 20, 30108: 13, 30109: 33}

# Input 31000 read 6 in the reporter's scan: battery online, on-grid.
XH2_INPUT = {31000: 6}


def _client(map_key: str, inputs: dict, holding: dict):
    client = _gm.GrowattModbus(connection_type="serial", register_map=map_key)

    def read_input(start, count, log_errors=True):
        if start not in inputs:
            return None
        return [inputs.get(a, 0) for a in range(start, start + count)]

    def read_holding(start, count):
        if start not in holding:
            return None
        return [holding.get(a, 0) for a in range(start, start + count)]

    client.read_input_registers = read_input
    client.read_holding_registers = read_holding
    return client


# ---------------------------------------------------------------------------
# Clock
# ---------------------------------------------------------------------------

def test_xh2_reads_its_clock_from_the_vpp_block():
    client = _client(XH2, XH2_INPUT, XH2_CLOCK)

    when = client.read_inverter_time()

    assert when is not None, "XH2 clock unreadable - it is being read from the dead 45-51 range"
    assert (when.year, when.month, when.day, when.hour, when.minute, when.second) == (
        2026, 9, 30, 20, 13, 33
    )


def test_xh2_does_not_offer_a_clock_write_it_has_never_tested():
    """30104 reads back 26, not 2026, so the year form for a write is unknown."""
    assert _client(XH2, XH2_INPUT, XH2_CLOCK).is_clock_writable is False


def test_legacy_profiles_keep_the_v139_clock():
    client = _client("MIN_3000_6000TL_X", {}, {45: 2026, 46: 9, 47: 30, 48: 8, 49: 0, 50: 0, 51: 0})

    assert client.clock_register_start == 45
    assert client.is_clock_writable is True
    assert client.read_inverter_time() is not None


# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------

def test_xh2_status_comes_from_31000_and_uses_the_table_documented_for_it():
    data = _client(XH2, XH2_INPUT, {}).read_all_data()
    assert data is not None
    assert data.status == 6

    family = _const.PROFILE_STATUS_MAP.get(XH2, "grid_tied")
    table = _const.HYBRID_STATUS_CODES if family == "hybrid" else _const.STATUS_CODES
    assert 6 in table, "XH2 status 6 would render as 'Unknown (6)'"
    assert table[6]["name"] == "Bat On-Grid"


# ---------------------------------------------------------------------------
# Controls
# ---------------------------------------------------------------------------

def test_xh2_maps_the_controls_validated_on_hardware():
    holding = _profiles.REGISTER_MAPS[XH2]["holding_registers"]

    for address, name in {
        30405: "vpp_ongrid_discharge_soc",
        30407: "remote_power_control_enable",
        30408: "remote_power_control_charging_time",
        30409: "remote_charge_and_discharge_power",
        30410: "vpp_ac_charge_enable",
    }.items():
        assert holding[address]["name"] == name
        assert _const.WRITABLE_REGISTERS[name]["register"] == address


def test_xh2_leaves_out_the_charge_cutoff_that_reverted_itself():
    """30404: 100 -> 95 held six minutes, then read 100 again with nothing writing it."""
    assert 30404 not in _profiles.REGISTER_MAPS[XH2]["holding_registers"]


def test_set_battery_mode_prerequisites_are_present_on_xh2():
    """diagnostic.py refuses Set Battery Mode without 30100, 30407 and 30409."""
    holding = _profiles.REGISTER_MAPS[XH2]["holding_registers"]
    assert {30100, 30407, 30409} <= set(holding)


def test_ongrid_discharge_soc_is_read_into_its_field():
    data = _client(XH2, XH2_INPUT, {**XH2_CLOCK, 30405: 20}).read_all_data()
    assert data.vpp_ongrid_discharge_soc == 20
    assert "vpp_ongrid_discharge_soc" not in data.unread_fields


def test_a_missed_ongrid_discharge_soc_read_is_unknown_not_ten_percent():
    data = _client(XH2, XH2_INPUT, {}).read_all_data()
    assert "vpp_ongrid_discharge_soc" in data.unread_fields


# ---------------------------------------------------------------------------
# Battery pack description (MIN TL-XH, #460)
# ---------------------------------------------------------------------------

def test_min_tl_xh_decodes_the_battery_pack_registers():
    """Reporter's MIN 4200TL-XH with two APX modules: 1 / 2 / 512 / 1000."""
    inputs = {a: 0 for a in range(31200, 31229)}
    inputs.update({31225: 1, 31226: 2, 31227: 512, 31228: 1000})

    data = _client(MIN_TL_XH, inputs, {}).read_all_data()

    assert data is not None
    assert data.battery_cluster_sum == 1
    assert data.battery_module_number == 2
    assert round(data.battery_module_rated_voltage, 1) == 51.2
    assert round(data.battery_module_rated_capacity, 1) == 100.0
