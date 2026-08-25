"""Every sensor has translated name text.

Sensor names come from `entity.sensor.<key>.name` in strings.json rather than from
`sensor_def['name']`, so the 22 shipped languages can translate them.

The failure mode if a key is missing is bad and quiet: Home Assistant does **not** fall
back to anything readable — the entity ends up with no name of its own, showing just the
device name. It still exists, still has a value, still works. It simply has no label.

This has to live in `tests_ha/` because it imports `sensor.py`, which needs
`homeassistant.components.sensor`. The HA-free suite cannot see SENSOR_DEFINITIONS at all,
which is exactly why the English text was generated in CI rather than by parsing source.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from custom_components.growatt_modbus.sensor import SENSOR_DEFINITIONS

COMPONENT = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"

# Sensors that have their own entity class instead of a SENSOR_DEFINITIONS entry, because
# they do not read a GrowattData field. They still need translated names, so they are not
# orphans - but SENSOR_DEFINITIONS will never list them.
STANDALONE_SENSORS = {
    # Reads the RTC registers directly via GrowattInverterClockSensor (#393)
    "inverter_clock",
}


def _entity_names(filename: str) -> dict[str, str]:
    data = json.loads((COMPONENT / filename).read_text(encoding="utf-8"))
    return {k: v.get("name") for k, v in data.get("entity", {}).get("sensor", {}).items()}


@pytest.mark.parametrize("filename", ["strings.json", "translations/en.json"])
def test_every_sensor_has_translated_text(filename):
    missing = sorted(set(SENSOR_DEFINITIONS) - set(_entity_names(filename)))
    assert not missing, (
        f"{filename} has no entity.sensor entry for {len(missing)} sensor(s), which "
        f"leaves them unnamed in the UI: {missing[:15]}"
    )


@pytest.mark.parametrize("filename", ["strings.json", "translations/en.json"])
def test_no_orphaned_translation_entries(filename):
    """Text for a sensor that no longer exists is dead weight and misleads translators."""
    orphans = sorted(
        set(_entity_names(filename)) - set(SENSOR_DEFINITIONS) - STANDALONE_SENSORS
    )
    assert not orphans, f"{filename} names sensors that do not exist: {orphans}"


def test_english_text_matches_the_original_definitions():
    """The migration must not have changed what English users see.

    The strings were generated from `sensor_def['name']`, so any divergence means either
    a definition changed without the translation following, or the generation was wrong.
    """
    names = _entity_names("strings.json")
    differences = {
        key: (definition["name"], names.get(key))
        for key, definition in SENSOR_DEFINITIONS.items()
        if definition.get("name") and names.get(key) != definition["name"]
    }
    assert not differences, (
        "English entity names differ from SENSOR_DEFINITIONS:\n  "
        + "\n  ".join(f"{k}: definition={v[0]!r} translation={v[1]!r}"
                      for k, v in list(differences.items())[:15])
    )


def test_strings_and_english_translation_agree():
    assert _entity_names("strings.json") == _entity_names("translations/en.json")
