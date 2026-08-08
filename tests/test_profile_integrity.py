"""Profile registry integrity.

Two failures here have reached users, both the same shape: a profile that exists and
can be selected by auto-detection, but that the options flow cannot render.

  v1.1.6  #360  The SPA profile had a full register map but no PROFILE_DISPLAY_NAMES
                entry, so it never appeared in the dropdown — nobody could select it.
                I spent three comments telling a user to pick it.

  v1.1.9  #361  Four TL-XH profiles had the same gap. Auto-detection assigns
                tl_xh_3000_10000_v201 for DTC 5100, and with no display entry the
                options form pre-selected an invalid value, so validation rejected
                the whole form — locking the user out of every setting, not just the
                profile.

v1.1.9 added an import-time warning for this. These tests make it a failure instead,
because a warning in the log is not something anyone reads before shipping.
"""
from __future__ import annotations

import importlib

import pytest

_dp = importlib.import_module("growatt_under_test.device_profiles")
_const = importlib.import_module("growatt_under_test.const")

INVERTER_PROFILES = _dp.INVERTER_PROFILES
PROFILE_DISPLAY_NAMES = _dp.PROFILE_DISPLAY_NAMES
REGISTER_MAPS = _const.REGISTER_MAPS


def _reachable_profile_ids() -> set[str]:
    """Profile ids reachable from the dropdown, via 'base' or 'v201'."""
    ids: set[str] = set()
    for info in PROFILE_DISPLAY_NAMES.values():
        ids.add(info["base"])
        ids.add(info["v201"])
    return ids


def test_every_profile_is_selectable_from_the_dropdown():
    """Regression guard for #360 and #361.

    A profile with no display-name entry cannot be rendered by the options flow:
    get_display_name_for_profile() falls through to the profile's technical `name`,
    which is not a valid dropdown key, so vol.In() rejects the default.
    """
    orphans = sorted(set(INVERTER_PROFILES) - _reachable_profile_ids())
    assert not orphans, (
        "Profiles with no PROFILE_DISPLAY_NAMES entry — selectable by auto-detection "
        f"but unrenderable in the options flow: {orphans}"
    )


def test_dropdown_entries_all_point_at_real_profiles():
    """The inverse: a display entry naming a profile that does not exist."""
    dangling = sorted(_reachable_profile_ids() - set(INVERTER_PROFILES))
    assert not dangling, f"Dropdown entries pointing at missing profiles: {dangling}"


@pytest.mark.parametrize("profile_id", sorted(INVERTER_PROFILES))
def test_profile_register_map_resolves(profile_id):
    """Every profile's register_map must exist in REGISTER_MAPS."""
    map_key = INVERTER_PROFILES[profile_id]["register_map"]
    assert map_key in REGISTER_MAPS, (
        f"{profile_id} references register map '{map_key}', which does not exist"
    )


@pytest.mark.parametrize("profile_id", sorted(INVERTER_PROFILES))
def test_profile_has_required_fields(profile_id):
    profile = INVERTER_PROFILES[profile_id]
    for field in ("name", "description", "register_map", "sensors"):
        assert field in profile, f"{profile_id} is missing '{field}'"
    assert profile["sensors"], f"{profile_id} declares no sensors"


# ---------------------------------------------------------------------------
# Known gaps
#
# Pre-existing issues, recorded so they cannot grow silently. Each was found by the
# tests below when they were written; none is fixed here, because changing which
# register feeds a sensor alters what users see and needs a field report first —
# the exact mistake that caused the v1.1.3 SPH regression.
# ---------------------------------------------------------------------------

KNOWN_ASYMMETRIC_PAIRS: dict[str, set[int]] = {
    # 31222 'battery_temp_vpp_high' declares pair=31223, but 31223 is a standalone
    # scaled 'battery_temp' rather than a low word, so it does not reciprocate.
    # Harmless in practice — battery_temp resolves to 31223 and decodes correctly on
    # its own — but the declaration is misleading. 31222 should either drop its
    # 'pair' or 31223 should become a proper low word.
    "MID_15000_25000TL3_X_V201": {31222},
}

KNOWN_DUPLICATE_NAMES: dict[str, set[str]] = {
    # Dual-range profile: the same logical values exist in both the 3000 range and
    # the VPP 31200 range. _find_register_by_name returns the first match and the
    # 3000 block is spread first, so the 3000 registers win and the VPP copies are
    # dead. Intentional in effect, but implicit — and it is precisely why TL-XH2
    # needed its own profile rather than reusing this one (#361).
    "MIN_TL_XH_3000_10000_V201": {
        "charge_energy_today_high", "charge_energy_today_low",
        "charge_power_high", "charge_power_low",
        "discharge_energy_today_high", "discharge_energy_today_low",
        "discharge_power_high", "discharge_power_low",
    },
    # R-phase (1015/1016) and Total (1021/1022) PacToUser. Identical on a
    # single-phase unit, so which one wins does not change the value.
    "SPH_3000_6000_V201": {"power_to_user_high", "power_to_user_low"},
    "SPH_7000_10000_V201": {"power_to_user_high", "power_to_user_low"},
    # NEEDS INVESTIGATION, not merely accepted:
    # 1086-1089 are the BMS values ("actual battery state of charge" per their own
    # desc) and are the reason the HU profile exists. But the profile spreads
    # SPH_7000_10000's registers first, so 1013/1014/1040 shadow them and the BMS
    # readings are unreachable via _find_register_by_name.
    # Fixing this changes what SOC/voltage/temperature an SPH HU owner sees, so it
    # wants a field report before being touched.
    "SPH_8000_10000_HU": {"battery_soc", "battery_voltage", "battery_temp"},
}


@pytest.mark.parametrize("map_key", sorted(REGISTER_MAPS))
def test_register_map_pairs_are_symmetric(map_key):
    """A 32-bit pair must reference back.

    A one-way `pair` silently decodes as a single register, producing a value wrong
    by a factor of 65536 or simply truncated — plausible enough to go unnoticed,
    which is how the TL-XH2 AC power bug survived a release.
    """
    regs = REGISTER_MAPS[map_key].get("input_registers", {})
    allowed = KNOWN_ASYMMETRIC_PAIRS.get(map_key, set())
    problems: list[str] = []
    for addr, info in regs.items():
        partner = info.get("pair")
        if partner is None or addr in allowed:
            continue
        if partner not in regs:
            problems.append(f"{addr} pairs with {partner}, which is not defined")
        elif regs[partner].get("pair") != addr:
            problems.append(
                f"{addr} pairs with {partner}, but {partner} pairs with "
                f"{regs[partner].get('pair')}"
            )
    assert not problems, f"{map_key}: asymmetric pairs: {problems}"


@pytest.mark.parametrize("map_key", sorted(REGISTER_MAPS))
def test_register_names_are_unique_within_a_map(map_key):
    """Duplicate names make _find_register_by_name() order-dependent.

    Whichever register appears first in insertion order wins and the other becomes
    unreachable — silently, and dependent on the order profile blocks are spread.
    """
    regs = REGISTER_MAPS[map_key].get("input_registers", {})
    allowed = KNOWN_DUPLICATE_NAMES.get(map_key, set())
    seen: dict[str, int] = {}
    duplicates: list[str] = []
    for addr, info in regs.items():
        name = info.get("name")
        if not name:
            continue
        if name in seen and name not in allowed:
            duplicates.append(f"{name} at {seen[name]} and {addr}")
        seen.setdefault(name, addr)
    assert not duplicates, f"{map_key}: duplicate register names: {duplicates}"


def test_no_profile_defines_the_same_register_address_twice():
    """Duplicate dict keys are invisible once the module is imported.

    Python keeps the last value and discards the earlier one silently — no error, no
    warning, and nothing left in the loaded map to inspect. So this has to read the
    source, not REGISTER_MAPS: by the time the dict exists the evidence is gone.

    tl_xh.py carried `3136: battery_bms_temp` alongside `3136: ac_charge_energy_total_low`
    for a long time. The energy pair won, so the temperature mapping never existed at
    runtime — no sensor, no dataclass field, nothing to notice. mod.py had already
    recorded the same address as a "corrected from wrong battery_bms_temp mapping", but
    the stale line survived here where it could not be seen.
    """
    import ast
    from collections import Counter
    from pathlib import Path

    profiles_dir = Path(_dp.__file__).parent / "profiles"
    problems: list[str] = []

    for path in sorted(profiles_dir.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Dict):
                continue
            addresses = [
                k.value for k in node.keys
                if isinstance(k, ast.Constant) and isinstance(k.value, int)
            ]
            for addr, count in Counter(addresses).items():
                if count > 1:
                    problems.append(
                        f"{path.name} line {node.lineno}: register {addr} defined "
                        f"{count} times — all but the last are silently discarded"
                    )

    assert not problems, "duplicate register addresses:\n  " + "\n  ".join(problems)


def test_known_gap_allowlists_do_not_grow_stale():
    """Every allowlisted map must still exist, so the lists cannot rot unnoticed."""
    for map_key in {**KNOWN_ASYMMETRIC_PAIRS, **KNOWN_DUPLICATE_NAMES}:
        assert map_key in REGISTER_MAPS, (
            f"'{map_key}' is allowlisted but no longer exists — remove the entry"
        )
