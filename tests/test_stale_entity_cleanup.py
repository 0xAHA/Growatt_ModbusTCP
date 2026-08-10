"""Sensors dropped from a profile must be removed from the entity registry.

Removing a sensor from a profile's set stops it being created. It does not remove what
earlier versions already registered, so the entity stays in Home Assistant showing
`unavailable` — which reads as a broken sensor rather than one that was never meant to
exist, and is arguably worse than the wrong value it replaced.

This cleanup has now failed twice, each time differently:

  - v1.4.0 gated it on the inverter being reachable. `async_config_entry_first_refresh`
    seeds an empty `GrowattData()`, so the guard was never satisfied during setup and the
    block never ran at all (#362).
  - v1.5.3 dropped `dcdc_temp` from ~26 profiles, but the cleanup was a per-sensor block
    listing specific names, and the new removal never got one. The entities went
    unavailable instead of disappearing.

The fix for the second was a general rule: anything in SENSOR_DEFINITIONS that is not in
the profile's sensor set is stale, because sensor.py creates exactly the intersection of
those two and nothing else. These tests hold both properties.

Parsed from source: __init__.py imports Home Assistant, which the HA-free suite cannot
load.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

INIT = (Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
        / "__init__.py")
SOURCE = INIT.read_text(encoding="utf-8")


def _setup_entry_source() -> str:
    for node in ast.walk(ast.parse(SOURCE)):
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "async_setup_entry":
            return ast.get_source_segment(SOURCE, node) or ""
    raise AssertionError("async_setup_entry not found")


def test_cleanup_is_driven_by_the_profile_sensor_set():
    """A per-sensor list only cleans up the removals someone remembered to add to it."""
    body = _setup_entry_source()
    assert "get_sensors_for_profile" in body, (
        "stale-entity cleanup does not consult the profile's sensor set, so it can only "
        "remove sensors that were hard-coded into it by name"
    )
    assert re.search(r"for sensor_key in SENSOR_DEFINITIONS", body), (
        "cleanup does not iterate SENSOR_DEFINITIONS, so a dropped sensor with no "
        "dedicated block will linger in the registry as unavailable"
    )


def test_cleanup_actually_removes():
    body = _setup_entry_source()
    assert "async_remove" in body, "cleanup never calls async_remove"


def test_cleanup_is_not_gated_on_connectivity():
    """The v1.4.0 failure. Profile membership is static — it needs no inverter and no
    poll, and requiring one means the cleanup never runs during setup, which is the only
    time it matters.
    """
    body = _setup_entry_source()
    # Find the general cleanup block and check no connectivity guard wraps it.
    idx = body.find("for sensor_key in SENSOR_DEFINITIONS")
    assert idx != -1, "general cleanup block not found"
    window = body[max(0, idx - 900):idx]
    for guard in ("serial_number", "has_real_data", "last_update_success"):
        assert guard not in window, (
            f"stale-entity cleanup appears gated on {guard!r}. coordinator.data is an "
            f"empty placeholder during setup, so such a guard stops the cleanup running "
            f"at all — this is the v1.4.0 regression (#362)."
        )
