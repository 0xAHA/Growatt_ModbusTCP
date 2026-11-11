"""The manifest's integration categories.

Home Assistant introduced integration categories in October 2026:
https://contributors.home-assistant.io/core/integrations/categories/

The HACS action fails the build on an unknown category, and hassfest only
warns, so a typo would surface as a HACS validation failure rather than a
test failure. This pins the value to the published list.
"""

import json
from pathlib import Path

MANIFEST = (
    Path(__file__).resolve().parent.parent
    / "custom_components"
    / "growatt_modbus"
    / "manifest.json"
)

# The energy category and its subcategories, as published by Home Assistant.
KNOWN_ENERGY_CATEGORIES = {
    "energy",
    "energy.backup_power",
    "energy.energy_prices",
    "energy.ev_charging",
    "energy.meters_monitoring",
    "energy.solar_batteries",
}


def _manifest():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_categories_present_and_within_limits():
    categories = _manifest().get("categories")
    assert isinstance(categories, list)
    assert 1 <= len(categories) <= 3
    assert len(set(categories)) == len(categories)


def test_primary_category_is_solar_batteries():
    # Growatt inverters are solar inverters, most of them hybrids with a
    # home battery: Energy > Solar panels and home batteries.
    assert _manifest()["categories"][0] == "energy.solar_batteries"


def test_categories_are_known_values():
    for category in _manifest()["categories"]:
        assert category in KNOWN_ENERGY_CATEGORIES, category
