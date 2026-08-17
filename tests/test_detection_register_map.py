"""A detected profile must report the register map it actually resolves to (#379).

The DTC branch is the primary detection path. It set `profile_key` and returned without
assigning `register_map`, so the field kept its "UNKNOWN" default while every heuristic
fallback filled it in — populated on the paths that matter least, blank on the one used
most.

Nothing failed. The scan generated, the integration ran on the right profile, and only the
report was wrong. That matters because those scans are what we ask people to attach when we
are trying to confirm a mapping, and on #377 the UNKNOWN sat directly above an UNCONFIRMED
warning, which made the whole detection block read as far more broken than it was.

Asserting merely "not UNKNOWN" would pass on a typo, so these check the name resolves to a
register map that exists.
"""
from __future__ import annotations

import importlib

import pytest

_dp = importlib.import_module("growatt_under_test.device_profiles")
_profiles = importlib.import_module("growatt_under_test.profiles")

INVERTER_PROFILES = _dp.INVERTER_PROFILES


def test_a_dtc_detection_reports_a_register_map():
    """The #377 case: DTC 3501 resolved sph_3000_6000 and reported UNKNOWN."""
    detection = {"profile_key": "sph_3000_6000", "register_map": "UNKNOWN"}
    _dp.fill_register_map(detection)
    assert detection["register_map"] != "UNKNOWN", (
        "a DTC-detected profile still reports UNKNOWN for its register map"
    )
    assert detection["register_map"] == "SPH_3000_6000"


def test_the_reported_map_actually_exists():
    """A name that resolves to nothing is no better than UNKNOWN — it is worse, because
    it looks like an answer."""
    detection = {"profile_key": "sph_3000_6000", "register_map": "UNKNOWN"}
    _dp.fill_register_map(detection)
    assert _profiles.get_profile(detection["register_map"]) is not None


@pytest.mark.parametrize("profile_key", sorted(INVERTER_PROFILES))
def test_every_profile_can_resolve_a_real_register_map(profile_key):
    """Whatever detection settles on, the report must be able to name its map. This also
    catches a profile whose register_map points at something that no longer exists."""
    detection = {"profile_key": profile_key, "register_map": "UNKNOWN"}
    _dp.fill_register_map(detection)

    assert detection["register_map"] != "UNKNOWN", (
        f"{profile_key} cannot resolve a register map name"
    )
    assert _profiles.get_profile(detection["register_map"]) is not None, (
        f"{profile_key} reports register map {detection['register_map']!r}, "
        f"which does not resolve to a real map"
    )


def test_an_explicit_choice_is_not_overwritten():
    """The heuristic branches assign deliberately — PV3 probing picks between maps that
    share a profile key. Recomputing from the profile key would undo that."""
    detection = {"profile_key": "sph_3000_6000", "register_map": "SPH_8000_10000_HU"}
    _dp.fill_register_map(detection)
    assert detection["register_map"] == "SPH_8000_10000_HU"


def test_an_unresolvable_profile_key_stays_unknown():
    """Better an honest UNKNOWN than a confident wrong name."""
    detection = {"profile_key": "no_such_profile", "register_map": "UNKNOWN"}
    _dp.fill_register_map(detection)
    assert detection["register_map"] == "UNKNOWN"


def test_it_runs_before_the_dtc_early_return():
    """The DTC path returns early. A resolver called only at the end of the function would
    fix every path except the one the bug was reported on.

    Read from source rather than imported: diagnostic.py pulls in voluptuous and the Home
    Assistant helpers, which this suite deliberately does not have.
    """
    from pathlib import Path

    source = (Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
              / "diagnostic.py").read_text(encoding="utf-8")
    marker = 'if detection.get("dtc_code") and detection.get("profile_key"):'
    assert marker in source, "the DTC early return has moved or been rewritten"
    after = source[source.index(marker):source.index(marker) + 200]
    assert "fill_register_map(detection)" in after, (
        "the DTC early return is not preceded by the register map resolver, so the "
        "primary detection path still reports UNKNOWN"
    )
