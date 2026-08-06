"""Status code table selection.

`PROFILE_STATUS_MAP` decides which table decodes `data.status`. Getting it wrong
produces a plausible-looking but incorrect label, which is the hardest kind of bug to
notice — it took four separate user reports to sort out.

  v1.0.4  #348  MOD5000TL3-X (grid-tied) was on the hybrid table, so a normal
                inverter (value 1) displayed as "Self-Test".

  v1.1.3  #348  Same fix applied to MOD-XH, WIT and TL-XH — all confirmed against
                ShinePhone by their owners. SPH and SPH-TL3 were moved in the same
                change with NO field confirmation, reasoned from profile `desc`
                strings that turned out to be unchecked boilerplate.

  v1.1.7  #363  darimar's SPH-4600 reported "Unknown (6)" — the standard table has no
                entry for 6 at all. SPH and SPH-TL3 restored to the hybrid table.

The rule these tests pin: a family belongs on the hybrid table only when its status
register genuinely carries hybrid-range values, and that must come from a field
report, not from a `desc` string.
"""
from __future__ import annotations

import importlib

import pytest

_const = importlib.import_module("growatt_under_test.const")

STATUS_CODES = _const.STATUS_CODES
HYBRID_STATUS_CODES = _const.HYBRID_STATUS_CODES
SPF_STATUS_CODES = _const.SPF_STATUS_CODES
PROFILE_STATUS_MAP = _const.PROFILE_STATUS_MAP


def _table_for(map_key: str) -> dict:
    """Mirror the selection in sensor.py's status rendering."""
    family = PROFILE_STATUS_MAP.get(map_key, "grid_tied")
    if family == "hybrid":
        return HYBRID_STATUS_CODES
    if family == "spf":
        return SPF_STATUS_CODES
    return STATUS_CODES


# --------------------------------------------------------------------------
# The regressions
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "map_key",
    [
        "SPH_3000_6000",
        "SPH_7000_10000",
        "SPH_8000_10000_HU",
        "SPH_3000_6000_V201",
        "SPH_7000_10000_V201",
        "SPH_TL3_3000_10000",
        "SPH_TL3_3000_10000_V201",
    ],
)
def test_sph_family_can_decode_value_6(map_key):
    """Regression guard for Issue #363.

    darimar's SPH-4600 reports status 6 (Bat On-Grid). The standard table has no
    entry for 6, so moving SPH off the hybrid table rendered "Unknown (6)".
    """
    table = _table_for(map_key)
    assert 6 in table, f"{map_key} cannot decode status 6 — the #363 regression"
    assert table[6]["name"] == "Bat On-Grid"


@pytest.mark.parametrize(
    ("map_key", "expected"),
    [
        # Field-confirmed against ShinePhone by their owners — must stay standard.
        ("MOD_6000_15000TL3_X", "Normal"),    # GreenThumb91, v1.0.4
        ("MOD_6000_15000TL3_XH", "Normal"),   # Husplace, v1.1.3
        ("WIT_4000_15000TL3", "Normal"),      # Fyntiker, v1.1.3
        ("TL_XH_3000_10000", "Normal"),       # uspino2 (MIN TL-XH), v1.1.2
        ("MIN_TL_XH_3000_10000_V201", "Normal"),
    ],
)
def test_confirmed_standard_families_decode_1_as_normal(map_key, expected):
    """Regression guard for Issue #348.

    These families report 1 = Normal. On the hybrid table 1 is "Self-Test", which is
    what users saw during normal operation.
    """
    assert _table_for(map_key)[1]["name"] == expected


# --------------------------------------------------------------------------
# The documented exceptions
# --------------------------------------------------------------------------

def test_spa_uses_hybrid_because_it_has_no_inverter_status_register():
    """SPA defines no `inverter_status`, so the lookup falls through to min_addr —
    register 1000 (`system_work_mode`), which genuinely is the hybrid register.
    """
    assert PROFILE_STATUS_MAP.get("SPA_3000_6000_TL_BL") == "hybrid"


@pytest.mark.parametrize("map_key", ["SPF_3000_6000_ES_PLUS", "SPE_8000_12000_ES"])
def test_offgrid_families_use_spf_table(map_key):
    """SPE inherits SPF's input_registers wholesale, so its reg 0 carries SPF
    semantics — it was on the hybrid table until v1.1.3, showing PV Charge as
    "PV On-Grid" and Discharge as "Reserved".
    """
    assert PROFILE_STATUS_MAP.get(map_key) == "spf"
    assert _table_for(map_key) is SPF_STATUS_CODES


# --------------------------------------------------------------------------
# Table integrity
# --------------------------------------------------------------------------

def test_standard_table_covers_the_states_profiles_document():
    """WIT and SPH-TL3 document 5=Standby on register 0; it was added in v1.1.3 so
    they would not render "Unknown (5)" after moving off the hybrid table.
    """
    for code in (0, 1, 3, 5):
        assert code in STATUS_CODES


def test_every_status_entry_has_a_name():
    for table in (STATUS_CODES, HYBRID_STATUS_CODES, SPF_STATUS_CODES):
        for code, entry in table.items():
            assert "name" in entry, f"status {code} has no name"
            assert entry["name"], f"status {code} has an empty name"


def test_profile_status_map_only_references_known_families():
    assert set(PROFILE_STATUS_MAP.values()) <= {"hybrid", "spf"}
