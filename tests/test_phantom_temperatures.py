"""Temperature sensors must have a register behind them (#360, #362).

A sensor in a profile's sensor set is created unconditionally. Its `condition` cannot
save it when the attribute is a `GrowattData` field, because the field always exists with
a default — so a temperature with no register publishes 0.0 °C forever rather than going
unavailable. On a dashboard that is a battery or a power module sitting at freezing, which
reads as a measurement rather than as missing data.

This is the #362 battery_temp bug. It recurred immediately: a full scan of the #360 device
showed `ipm_temp` and `boost_temp` in the SPH-TL3 sensor set with nothing mapped to them,
and `dcdc_temp` too — three phantom temperatures on hardware that has been confirmed since
DTC 3601. Two were fixable by adding registers 94 and 95, which the device answers with
plausible values; the third has no register anywhere in that map and had to be removed
from the set.

Scoped to temperatures deliberately. The same check across every sensor produces mostly
false positives, because sensors such as `status`, `last_update`, `grid_import_power` and
`grid_export_power` are computed by the coordinator rather than read from an address. A
noisy test gets ignored, and this class is worth catching precisely.
"""
from __future__ import annotations

import importlib

import pytest

_dp = importlib.import_module("growatt_under_test.device_profiles")
_profiles = importlib.import_module("growatt_under_test.profiles")

INVERTER_PROFILES = _dp.INVERTER_PROFILES

TEMPERATURE_SENSORS = {
    "inverter_temp", "ipm_temp", "boost_temp", "dcdc_temp", "battery_temp",
}


def _register_names(profile_key: str) -> set[str]:
    """Every name a profile's register map can produce, including combined pairs."""
    rmap = _profiles.get_profile(INVERTER_PROFILES[profile_key]["register_map"])
    assert rmap is not None, (
        f"{profile_key} names register map "
        f"{INVERTER_PROFILES[profile_key]['register_map']!r}, which does not resolve"
    )
    names: set[str] = set()
    for space in ("input_registers", "holding_registers"):
        for reg in rmap.get(space, {}).values():
            name = reg["name"]
            names.add(name)
            for suffix in ("_high", "_low"):
                if name.endswith(suffix):
                    names.add(name[: -len(suffix)])
    return names


# Profiles with pre-existing phantom temperatures, recorded rather than hidden.
#
# These predate the dcdc_temp regression and are a different problem: the sensor is
# plausible for the hardware, but no register is mapped and there is no scan from one of
# these models to say whether the device reports it. Fixing them blind means either
# inventing an address or deleting a sensor that may work — both need a device.
#
# Listed explicitly so the count can only go down. A new profile with a phantom
# temperature fails; these six are known debt, and removing a name from this list when a
# scan settles it is the intended way to close them.
KNOWN_PHANTOM_TEMPERATURES = {
    "mic_2500_5500mtl_s": {"boost_temp"},
    "mic_600_3300tl_x": {"boost_temp"},
    "mic_600_3300tl_x_v201": {"boost_temp"},
    "spe_8000_12000_es": {"battery_temp", "boost_temp", "ipm_temp"},
    "spf_3000_6000_es_plus": {"battery_temp", "boost_temp", "ipm_temp"},
    "tl3_s_3000_15000": {"boost_temp", "ipm_temp"},
}


@pytest.mark.parametrize("profile_key", sorted(INVERTER_PROFILES))
def test_every_temperature_sensor_has_a_register(profile_key):
    declared = INVERTER_PROFILES[profile_key]["sensors"] & TEMPERATURE_SENSORS
    available = _register_names(profile_key)
    known = KNOWN_PHANTOM_TEMPERATURES.get(profile_key, set())
    phantom = sorted(declared - available - known)

    # A name that stops being phantom must leave the list, or the list quietly becomes
    # a place where fixed things are still described as broken.
    stale = sorted(known - (declared - available))
    assert not stale, (
        f"{profile_key} lists {stale} as known phantom temperatures, but they now have "
        f"registers. Remove them from KNOWN_PHANTOM_TEMPERATURES."
    )

    assert not phantom, (
        f"{profile_key} declares temperature sensors with no register to populate them: "
        f"{phantom}. They will be created and publish 0.0 °C. Either map the register, "
        f"or subtract the sensor from this profile's set — a hasattr() condition cannot "
        f"suppress it, because these are GrowattData fields with defaults."
    )
