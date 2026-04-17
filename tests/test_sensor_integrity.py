"""Sensor integrity tests.

These tests verify that the sensor configuration is internally consistent
across sensor.py, const.py, and device_profiles.py — without importing any
Home Assistant modules.

Checks performed:
  1. Every sensor in SENSOR_DEFINITIONS is assigned to a device in SENSOR_DEVICE_MAP.
  2. Every sensor in a *_SENSORS group constant is defined in SENSOR_DEFINITIONS.
  3. SENSOR_DEVICE_MAP does not grow its undefined-sensor count beyond the
     explicitly tracked known-gap allowlist (KNOWN_MAP_WITHOUT_DEF).
"""
import re
from pathlib import Path

COMPONENT_DIR = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"

# Keys present in SENSOR_DEVICE_MAP that have no SENSOR_DEFINITIONS entry.
# These represent pre-existing technical debt tracked here so that new orphaned
# entries cannot be added silently.  Each item should have a comment explaining
# why it exists and what should eventually be done with it.
KNOWN_MAP_WITHOUT_DEF: frozenset = frozenset({
    # MOD profile diagnostic status — no sensor definition added yet
    "battery_derating_mode",
    # SPH HU detailed BMS registers — processed by coordinator but not yet
    # exposed in sensor.py or included in any sensor group
    "bms_delta_volt",
    "bms_fw_version",
    "bms_gauge_fcc",
    "bms_gauge_rm",
    # Grid import energy from hardware bidirectional meter (SPH/MIN/MID/MOD
    # profiles).  Actively populated by coordinator and used as source data
    # for computed grid_import_energy_* sensors.  No standalone sensor
    # definition yet — device assignment is pre-reserved.
    "energy_to_user_today",
    "energy_to_user_total",
    # Control/mode register (RW) — read back by coordinator; no sensor
    # definition yet; present in SPH, MOD, SPH-TL3, WIT profiles
    "priority_mode",
})


# ---------------------------------------------------------------------------
# Source-file parsers (no HA imports required)
# ---------------------------------------------------------------------------

def _read(filename: str) -> str:
    return (COMPONENT_DIR / filename).read_text(encoding="utf-8")


def _extract_sensor_definitions(src: str) -> set:
    """Return keys from the SENSOR_DEFINITIONS dict in sensor.py."""
    return set(re.findall(r'^\s{4}"([a-z][a-z0-9_]+)":\s*\{', src, re.MULTILINE))


def _extract_device_map_keys(src: str) -> set:
    """Return all sensor keys present inside SENSOR_DEVICE_MAP in const.py."""
    m = re.search(r"SENSOR_DEVICE_MAP\s*=\s*\{(.+?)^\}", src, re.DOTALL | re.MULTILINE)
    if not m:
        return set()
    return set(re.findall(r"'([a-z][a-z0-9_]+)'", m.group(1)))


def _extract_group_members(src: str) -> set:
    """Return all sensor keys that appear inside *_SENSORS group constants."""
    groups = re.findall(
        r"^[A-Z_]+_SENSORS\s*:\s*Set\[str\]\s*=\s*\{([^}]+)\}",
        src,
        re.MULTILINE | re.DOTALL,
    )
    members: set = set()
    for body in groups:
        members |= set(re.findall(r'"([a-z][a-z0-9_]+)"', body))
    return members


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_all_defined_sensors_assigned_to_device() -> None:
    """Every key in SENSOR_DEFINITIONS must appear in SENSOR_DEVICE_MAP.

    If a sensor is defined but not assigned to a device, it will end up
    attached to the wrong device (or no device) in Home Assistant.
    """
    defined = _extract_sensor_definitions(_read("sensor.py"))
    in_map = _extract_device_map_keys(_read("const.py"))

    missing = defined - in_map
    assert not missing, (
        f"Sensors in SENSOR_DEFINITIONS but missing from SENSOR_DEVICE_MAP "
        f"({len(missing)}): {sorted(missing)}"
    )


def test_all_group_sensors_have_definitions() -> None:
    """Every sensor key in a *_SENSORS group constant must exist in SENSOR_DEFINITIONS.

    If a sensor is added to a group but never defined, no entity is ever created
    for profiles that include that group.
    """
    defined = _extract_sensor_definitions(_read("sensor.py"))
    group_members = _extract_group_members(_read("device_profiles.py"))

    missing = group_members - defined
    assert not missing, (
        f"Sensors in group constants but missing from SENSOR_DEFINITIONS "
        f"({len(missing)}): {sorted(missing)}"
    )


def test_device_map_has_no_unknown_undefined_sensors() -> None:
    """SENSOR_DEVICE_MAP must not gain new undefined-sensor entries.

    Keys in SENSOR_DEVICE_MAP that have no SENSOR_DEFINITIONS entry are
    dead weight — assigned to a device but never rendered as entities.
    Pre-existing gaps are listed in KNOWN_MAP_WITHOUT_DEF above.
    Any entry beyond that set causes this test to fail.

    Also fails if KNOWN_MAP_WITHOUT_DEF contains stale entries (i.e., gaps
    that were fixed but the allowlist was not pruned).
    """
    defined = _extract_sensor_definitions(_read("sensor.py"))
    in_map = _extract_device_map_keys(_read("const.py"))

    gaps = in_map - defined
    unexpected = gaps - KNOWN_MAP_WITHOUT_DEF
    assert not unexpected, (
        f"New undefined sensors in SENSOR_DEVICE_MAP ({len(unexpected)}): "
        f"{sorted(unexpected)}.  Either add a SENSOR_DEFINITIONS entry in "
        f"sensor.py, or add to KNOWN_MAP_WITHOUT_DEF with an explanatory comment."
    )

    stale = KNOWN_MAP_WITHOUT_DEF - gaps
    assert not stale, (
        f"KNOWN_MAP_WITHOUT_DEF has stale entries that are now defined "
        f"({len(stale)}): {sorted(stale)}.  Remove them from the allowlist."
    )
