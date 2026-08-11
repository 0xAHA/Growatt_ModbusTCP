"""Storage-range power flow must not swap grid import with house load (#369).

V1.39 lays the storage range out as four 8-register blocks — R phase, S phase, T phase,
Total — so within the Total block:

    1021  PactouserTotal    AC power to user total      grid import
    1029  Pactogrid total   AC power to grid total      grid export
    1037  PLocalLoad total  INV power to local load     house load

Three legacy SPH profiles had 1021 as `power_to_load` and 1037 as `self_consumption_power`
— a name no sensor group uses. Load Power therefore reported grid import, and the real
load was read and thrown away. `self_consumption` is derived from `power_to_load`, so it
was computed from the wrong quantity too.

The symptom hid well. On a single-phase inverter R phase and Total are the same
measurement, so 1015 and a mis-mapped 1021 return identical numbers, and grid import is a
plausible-looking value to see on a dashboard labelled Load Power. It shows up as Load
Power sitting at zero whenever the house is running on solar or battery.

Confirmed on an SPH 5000 (#369) by charting the two entities together: identical across a
sunny morning, down to a shared 29 W baseline.
"""
from __future__ import annotations

import importlib

import pytest

_profiles = importlib.import_module("growatt_under_test.profiles")

# Every profile that maps the storage-range Total block.
STORAGE_PROFILES = [
    "SPH_3000_6000", "SPH_7000_10000", "SPH_8000_10000_HU",
    "SPH_3000_6000_V201", "SPH_7000_10000_V201",
    "SPH_TL3_3000_10000", "SPH_TL3_3000_10000_V201",
    "SPA_3000_6000_TL_BL",
]

# address -> the sensor name it must resolve to, per the protocol
EXPECTED = {1021: "power_to_user", 1029: "power_to_grid", 1037: "power_to_load"}


def _name_at(profile_key: str, addr: int) -> str | None:
    prof = _profiles.get_profile(profile_key)
    if prof is None:
        pytest.skip(f"{profile_key} not present")
    reg = prof.get("input_registers", {}).get(addr)
    if reg is None:
        return None
    name = reg["name"]
    for suffix in ("_high", "_low"):
        if name.endswith(suffix):
            name = name[: -len(suffix)]
    return name


@pytest.mark.parametrize("profile_key", STORAGE_PROFILES)
def test_1037_is_house_load(profile_key):
    """The register that was being discarded. This is the one that matters — it is the
    only source of real load power on these profiles."""
    name = _name_at(profile_key, 1037)
    if name is None:
        pytest.skip(f"{profile_key} does not map 1037")
    assert name == "power_to_load", (
        f"{profile_key} maps 1037 as {name!r}. Per V1.39 it is PLocalLoad total — house "
        f"load. Mapping it to anything else means Load Power comes from somewhere it "
        f"shouldn't, and the real load is read and thrown away (#369)."
    )


@pytest.mark.parametrize("profile_key", STORAGE_PROFILES)
def test_1021_is_never_house_load(profile_key):
    """1021 is grid import. It may carry a suffixed name to avoid colliding with 1015,
    but it must never be `power_to_load` — that is the exact defect #369 fixed."""
    name = _name_at(profile_key, 1021)
    if name is None:
        pytest.skip(f"{profile_key} does not map 1021")
    assert name != "power_to_load", (
        f"{profile_key} maps 1021 as house load. Per V1.39 it is PactouserTotal — grid "
        f"import. On a single-phase unit this is indistinguishable from 1015 at a "
        f"glance, which is why it survived so long (#369)."
    )
    assert name.startswith("power_to_user"), (
        f"{profile_key} maps 1021 as {name!r}; expected a power_to_user variant"
    )


# Duplicate names that exist and have not been resolved, recorded rather than hidden.
#
# SPH_8000_10000_HU carries the battery block (1013/1014/1040) and the BMS block
# (1086-1089) under the same names. They are not guaranteed to be the same measurement —
# one is the inverter's view, the other the BMS's — so choosing between them needs a
# device to compare against, which we do not have. The SPA profile hit this and
# deliberately mapped only the four BMS registers that could not collide; this profile
# predates that reasoning.
#
# Listed explicitly so the count can only go down, and so this is a decision rather than
# an oversight.
KNOWN_DUPLICATE_NAMES = {
    "SPH_8000_10000_HU": {"battery_soc", "battery_voltage", "battery_temp"},
}


@pytest.mark.parametrize("profile_key", STORAGE_PROFILES)
def test_no_duplicate_names_in_the_storage_range(profile_key):
    """1015 and 1021 are the same measurement on single-phase hardware, so both wanting
    the name `power_to_user` is tempting. Two registers sharing a name makes
    _find_register_by_name() resolution order-dependent — it returns whichever the dict
    yields first, which is not a property anyone should be relying on."""
    prof = _profiles.get_profile(profile_key)
    if prof is None:
        pytest.skip(f"{profile_key} not present")
    known = KNOWN_DUPLICATE_NAMES.get(profile_key, set())
    seen: dict[str, int] = {}
    dupes = []
    for addr, reg in prof.get("input_registers", {}).items():
        if not 1000 <= addr < 1125:
            continue
        name = reg["name"]
        prev = seen.get(name)
        if prev is not None and name not in known:
            dupes.append((name, prev, addr))
        seen[name] = addr
    assert not dupes, (
        f"{profile_key} has duplicate register names in the storage range: {dupes}. "
        f"Give one of them a suffixed name so lookups are deterministic."
    )
