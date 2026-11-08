"""MIN TL-XH portal battery settings confirmed in issue #489."""
import importlib

import pytest

_const = importlib.import_module("growatt_under_test.const")
_gm = importlib.import_module("growatt_under_test.growatt_modbus")
_profiles = importlib.import_module("growatt_under_test.profiles")

GrowattData = _gm.GrowattData
GrowattModbus = _gm.GrowattModbus
MIN_PROFILE = "MIN_TL_XH_3000_10000_V201"


def _holding() -> dict[int, dict]:
    return _profiles.REGISTER_MAPS[MIN_PROFILE]["holding_registers"]


def _client() -> GrowattModbus:
    return GrowattModbus(
        connection_type="tcp",
        host="10.0.0.1",
        port=502,
        register_map=MIN_PROFILE,
    )


def test_all_four_portal_settings_are_rw_on_first_generation_min_tl_xh() -> None:
    """All four portal settings are exposed as writable MIN TL-XH controls."""
    expected = {
        3036: "grid_first_discharge_power_rate",
        3037: "off_grid_discharge_stopped_soc",
        3311: "ac_charge_max_power",
        3312: "grid_charge_stopped_soc",
    }

    for address, name in expected.items():
        register = _holding()[address]
        assert register["name"] == name
        assert register["access"] == "RW"
        assert _const.WRITABLE_REGISTERS[name]["register"] == address


def test_h30475_is_preserved_and_distinct_from_h3037() -> None:
    """The legacy VPP address remains separate from the newly mapped H3037."""
    holding = _holding()
    assert holding[30475]["name"] == "vpp_offgrid_discharge_soc"
    assert holding[3037]["name"] == "off_grid_discharge_stopped_soc"
    assert _const.WRITABLE_REGISTERS["vpp_offgrid_discharge_soc"]["register"] == 30475
    assert _const.WRITABLE_REGISTERS["off_grid_discharge_stopped_soc"]["register"] == 3037
    assert (
        _const.WRITABLE_REGISTERS["vpp_offgrid_discharge_soc"]["label"]
        != _const.WRITABLE_REGISTERS["off_grid_discharge_stopped_soc"]["label"]
    )


def test_h3311_is_read_write_only_on_min_not_mod() -> None:
    """H3311 is writable on MIN TL-XH but remains read-only on MOD-XH."""
    mod = _profiles.REGISTER_MAPS["MOD_6000_15000TL3_XH"]["holding_registers"][3311]
    assert mod["access"] == "RO"
    assert _holding()[3311]["access"] == "RW"
    assert _const.WRITABLE_REGISTERS["ac_charge_max_power"]["scale"] == pytest.approx(0.1)
    assert _const.WRITABLE_REGISTERS["ac_charge_max_power"]["read_scale"] == 1


def test_min_grid_charge_settings_are_read_individually() -> None:
    """MIN TL-XH reads H3311 and H3312 separately from the MOD peak-shaving block."""
    client = _client()
    reads: list[tuple[int, int]] = []
    values = {3311: [13], 3312: [85]}

    def read(address: int, count: int) -> list[int]:
        reads.append((address, count))
        return values[address]

    client.read_holding_registers = read
    data = GrowattData()
    client._read_min_tlxh_grid_charge_settings(data, _holding())

    assert reads == [(3311, 1), (3312, 1)]
    assert data.ac_charge_max_power == pytest.approx(1.3)
    assert data.grid_charge_stopped_soc == 85
    assert not data.unread_fields.intersection(
        {"ac_charge_max_power", "grid_charge_stopped_soc"}
    )


@pytest.mark.parametrize("address", [3311, 3312])
def test_failed_min_grid_charge_read_is_unavailable(address: int) -> None:
    """A failed MIN grid-charge read is marked unavailable rather than defaulted."""
    client = _client()
    client.read_holding_registers = lambda _address, _count: None
    data = GrowattData()
    client._read_min_tlxh_grid_charge_settings(data, _holding())

    field = {3311: "ac_charge_max_power", 3312: "grid_charge_stopped_soc"}[address]
    assert field in data.unread_fields


def test_min_path_does_not_request_the_mod_peak_shaving_block() -> None:
    """The MIN path never requests the six-register MOD/MID block."""
    client = _client()
    reads: list[tuple[int, int]] = []
    client.read_holding_registers = lambda address, count: reads.append((address, count)) or [13]
    client._read_min_tlxh_grid_charge_settings(GrowattData(), _holding())

    assert (3307, 6) not in reads
