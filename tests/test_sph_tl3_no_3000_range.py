"""SPH-TL3 does not implement the 3000 input range, and the poll no longer asks for it (#467).

The profile mapped one register there, 3119 (Dry Contact State). To fetch it, every poll
requested input 3000-3119, and the inverter answered Illegal Function: an SPH 8000TL3
BH-UP on #467, and the whole 3000-3124 range is silent in a DTC 3601 scan on #210, 3119
included. The block-level message said it would retry quietly. But the per-request warning
inside read_input_registers fired on every retry, so the log carried a warning every five
minutes indefinitely.

Two fixes, tested here:
  * 3119 is gone from the SPH-TL3 map, along with the sensor it fed on every profile that
    uses the map, so the range is never requested.
  * Any optional 3000 block (one the profile has other data sources besides) now retries
    without the per-request warning. A primary block still warns: there, a failure means
    the poll has nothing.
"""
from __future__ import annotations

import importlib

_gm = importlib.import_module("growatt_under_test.growatt_modbus")
_dp = importlib.import_module("growatt_under_test.device_profiles")
_profiles = importlib.import_module("growatt_under_test.profiles")

SPH_TL3_MAPS = ("SPH_TL3_3000_10000", "SPH_TL3_3000_10000_V201")
SPH_TL3_PROFILES = ("sph_tl3_3000_10000", "sph_tl3_3000_10000_v201", "spa_tl3_4000_10000_v201")


def _recording_client(register_map: str, refuse_3000: bool):
    client = _gm.GrowattModbus(connection_type="tcp", host="10.0.0.1", port=502,
                               slave_id=1, register_map=register_map)
    calls: list[tuple[int, int, bool]] = []

    def read_input_registers(start, count, log_errors=True):
        calls.append((start, count, log_errors))
        if refuse_3000 and 3000 <= start < 4000:
            return None  # Illegal Function reaches this layer as None
        return [1] * count

    client.read_input_registers = read_input_registers
    client.read_holding_registers = lambda start, count: [0] * count
    return client, calls


def test_sph_tl3_maps_nothing_in_the_3000_input_range():
    for name in SPH_TL3_MAPS:
        inputs = _profiles.REGISTER_MAPS[name]["input_registers"]
        assert not [a for a in inputs if 3000 <= a < 4000], name


def test_an_sph_tl3_poll_never_requests_the_3000_range():
    client, calls = _recording_client("SPH_TL3_3000_10000_V201", refuse_3000=True)
    client.read_all_data()
    assert not [c for c in calls if 3000 <= c[0] < 4000], calls


def test_dry_contact_state_is_not_offered_on_the_maps_without_it():
    for key in SPH_TL3_PROFILES:
        assert "dry_contact_state" not in _dp.INVERTER_PROFILES[key]["sensors"], key


def test_an_optional_3000_block_retries_without_the_per_request_warning():
    """MIN TL-XH V2.01 also has VPP data, so its 3000 block is optional."""
    client, calls = _recording_client("MIN_TL_XH_3000_10000_V201", refuse_3000=True)
    client.read_all_data()
    block = [c for c in calls if 3000 <= c[0] < 4000]
    assert block, "the 3000 block should still be attempted"
    assert all(log_errors is False for _, _, log_errors in block)


def test_a_primary_3000_block_still_warns():
    """MIN TL-X reads nothing else: a failure there is a failed poll and should be seen."""
    client, calls = _recording_client("MIN_3000_6000TL_X", refuse_3000=True)
    client.read_all_data()
    block = [c for c in calls if 3000 <= c[0] < 4000]
    assert block and all(log_errors is True for _, _, log_errors in block)
