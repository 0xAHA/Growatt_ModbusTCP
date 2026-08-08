"""DTC registry integrity.

The registry maps a Device Type Code, read from the inverter, to a profile. Two facts
live in each entry and conflating them caused a real bug: the DTC identifies the *model*
reliably, but whether the *profile* suits that model is separate and, for most entries,
has never been checked against hardware.

#360 is what that looks like — an SPA model (no solar DC inputs at all) mapped to an SPH
profile, so the user got PV entities reading zero forever, while the scanner reported
"Very High" confidence and called DTC matching "the most reliable method".

These tests hold the line on three things:
  - every mapping points at a profile that actually exists
  - provenance is one of the two known values, so it can never be quietly mistyped
    into something that reads as confirmed
  - anything claiming CONFIRMED cites where the confirmation came from
"""
from __future__ import annotations

import importlib

import pytest

_ad = importlib.import_module("growatt_under_test.auto_detection")
_dp = importlib.import_module("growatt_under_test.device_profiles")

DTC_REGISTRY = _ad.DTC_REGISTRY
CONFIRMED = _ad.CONFIRMED
ASSUMED = _ad.ASSUMED
INVERTER_PROFILES = _dp.INVERTER_PROFILES


def test_registry_is_not_empty():
    assert len(DTC_REGISTRY) > 20


@pytest.mark.parametrize("dtc", sorted(DTC_REGISTRY))
def test_every_mapping_points_at_a_real_profile(dtc):
    """A typo here sends a whole model family to a profile that doesn't exist."""
    entry = DTC_REGISTRY[dtc]
    assert entry.profile in INVERTER_PROFILES, (
        f"DTC {dtc} ({entry.model}) maps to '{entry.profile}', "
        f"which is not in INVERTER_PROFILES"
    )


@pytest.mark.parametrize("dtc", sorted(DTC_REGISTRY))
def test_provenance_is_a_known_value(dtc):
    """Guards against a third value appearing that the scanner would treat as
    unconfirmed, or worse, that a truthiness check would treat as confirmed."""
    assert DTC_REGISTRY[dtc].provenance in (CONFIRMED, ASSUMED)


@pytest.mark.parametrize("dtc", sorted(DTC_REGISTRY))
def test_every_entry_states_its_evidence(dtc):
    """An empty evidence string is how 'we never checked' becomes invisible again."""
    assert DTC_REGISTRY[dtc].evidence.strip(), f"DTC {dtc} has no evidence text"


@pytest.mark.parametrize(
    "dtc", sorted(d for d, e in DTC_REGISTRY.items() if e.provenance == CONFIRMED)
)
def test_confirmed_entries_cite_a_source(dtc):
    """CONFIRMED means a real device was seen running this profile. That claim has to
    be traceable to an issue or a scan, otherwise it is just an assertion."""
    evidence = DTC_REGISTRY[dtc].evidence.lower()
    assert any(token in evidence for token in ("#", "scan", "hardware")), (
        f"DTC {dtc} is CONFIRMED but its evidence cites nothing checkable: "
        f"{DTC_REGISTRY[dtc].evidence!r}"
    )


@pytest.mark.parametrize("dtc", sorted(DTC_REGISTRY))
def test_model_name_is_present(dtc):
    assert DTC_REGISTRY[dtc].model.strip()


# ---------------------------------------------------------------------------
# Coverage of the official table
# ---------------------------------------------------------------------------

# Growatt VPP 2.03 protocol, Table 3-1 "DTC code description". Transcribed from the
# document rather than from our own code, so this fails if a family is dropped or was
# never added — the MAX/MAX-X block (5000, 5500, 5501, 5502) was missing entirely
# until this test was written.
TABLE_3_1 = {
    3501, 3502, 3503, 3504,          # SPH
    3701, 3735, 3715, 3716, 3725,    # SPA
    3601,                            # SPH TL3
    5100,                            # MIN-XH
    5400, 5401,                      # MOD-XH / MID-XH / HU
    5600, 5601, 5800, 5801,          # WIT / WIS
    5200, 5201,                      # MIC / MIN-X
    5001, 5002, 5003,                # MOD / MID / MAC-X
    5000, 5500, 5501, 5502,          # MAX / MAX-X
}


@pytest.mark.parametrize("dtc", sorted(TABLE_3_1))
def test_official_table_code_is_mapped(dtc):
    assert dtc in DTC_REGISTRY, (
        f"DTC {dtc} appears in Growatt VPP 2.03 Table 3-1 but has no registry entry — "
        f"devices reporting it fall through to heuristic detection"
    )


# ---------------------------------------------------------------------------
# The lookup itself
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("dtc", sorted(DTC_REGISTRY))
def test_lookup_returns_the_registered_profile(dtc):
    assert _ad.detect_profile_from_dtc(dtc) == DTC_REGISTRY[dtc].profile


def test_unknown_dtc_returns_none():
    """Falling through to heuristic detection is correct for an unrecognised code."""
    assert _ad.detect_profile_from_dtc(999999) is None


# ---------------------------------------------------------------------------
# The documentation table
# ---------------------------------------------------------------------------
#
# docs/troubleshooting/dtc-debugging.md publishes this table for users. It was a third
# hand-maintained copy alongside auto_detection.py and diagnostic.py, and all three had
# drifted: nine codes were missing from one, 5600 disagreed outright between two, and
# the whole MAX/MAX-X family was absent from all of them.
#
# diagnostic.py now derives its copy from the registry. The docs page cannot, so it is
# checked here instead.

import re
from pathlib import Path

DOCS_PAGE = Path(__file__).parent.parent / "docs" / "troubleshooting" / "dtc-debugging.md"


def _documented_dtcs() -> set[int]:
    """DTC codes appearing in the leading column of a markdown table row."""
    text = DOCS_PAGE.read_text(encoding="utf-8")
    return {int(m) for m in re.findall(r"^\|\s*(\d{3,5})\s*\|", text, re.M)}


@pytest.mark.parametrize("dtc", sorted(DTC_REGISTRY))
def test_every_registry_entry_is_documented(dtc):
    assert dtc in _documented_dtcs(), (
        f"DTC {dtc} ({DTC_REGISTRY[dtc].model}) is in DTC_REGISTRY but missing from "
        f"{DOCS_PAGE.name} — users cannot see which profile their model resolves to"
    )


def test_docs_do_not_list_unknown_dtcs():
    """The reverse direction: a code removed from the registry but left in the docs
    tells users we support something we do not."""
    stale = _documented_dtcs() - set(DTC_REGISTRY)
    assert not stale, f"{DOCS_PAGE.name} documents DTCs with no registry entry: {sorted(stale)}"


def test_docs_flag_every_unconfirmed_mapping():
    """An ⚠️ in the docs is the user-facing half of `provenance`. If a mapping is
    ASSUMED in code it must not read as settled on the page."""
    text = DOCS_PAGE.read_text(encoding="utf-8")
    rows = {int(m.group(1)): m.group(0)
            for m in re.finditer(r"^\|\s*(\d{3,5})\s*\|.*$", text, re.M)}

    for dtc, entry in DTC_REGISTRY.items():
        row = rows.get(dtc)
        if row is None:
            continue  # covered by test_every_registry_entry_is_documented
        if entry.provenance == ASSUMED:
            assert "Unconfirmed" in row, f"DTC {dtc} is ASSUMED in code but not flagged in the docs"
        else:
            assert "Confirmed" in row, f"DTC {dtc} is CONFIRMED in code but not shown as such in the docs"


def test_spa_mappings_are_not_marked_confirmed():
    """Specific to #360, and the reason this file exists.

    Every SPA code currently points at an SPH profile, which carries PV sensor groups
    that SPA hardware cannot populate. Whatever else changes, none of these may claim
    to be a confirmed mapping while that is still true.
    """
    for dtc in (3701, 3715, 3716, 3725, 3735):
        assert DTC_REGISTRY[dtc].provenance == ASSUMED, (
            f"DTC {dtc} is an SPA model mapped to {DTC_REGISTRY[dtc].profile!r}; "
            f"it must not be marked CONFIRMED while SPA lacks a dedicated profile"
        )
