"""Every entity derives from GrowattEntity (Issue #362 follow-up).

`GrowattEntity` owns three things every entity needs to get right: the unique ID, the
sub-device it attaches to, and `has_entity_name`. Before this was enforced, 20 classes
carried their own copies, and they had drifted:

  - 16 set `has_entity_name = False` and baked the device name into `_attr_name`, so the
    integration shipped two naming conventions at once.
  - One had `has_entity_name = True` *and* the baked-in prefix, so WIT owners saw
    "Growatt Growatt TOU Period 1 Start".

The unique ID is the part that matters most: it is what Home Assistant matches an existing
entity on. Change it and the entity is orphaned — new one created, history gone, and
nothing in the logs to say so.

Parsed from source rather than imported: these modules need `homeassistant.components.*`,
which is only available in the `tests_ha/` environment.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

COMPONENT = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
PLATFORMS = ["sensor.py", "binary_sensor.py", "number.py", "select.py", "time.py"]


def _entity_classes(path: Path) -> list[tuple[str, list[str]]]:
    """Return (class_name, base_names) for classes that look like HA entities."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        bases = [b.id if isinstance(b, ast.Name)
                 else (b.attr if isinstance(b, ast.Attribute) else "")
                 for b in node.bases]
        if any(b.endswith("Entity") for b in bases):
            out.append((node.name, bases))
    return out


@pytest.mark.parametrize("filename", PLATFORMS)
def test_no_entity_derives_from_coordinatorentity_directly(filename):
    """Deriving straight from CoordinatorEntity means re-implementing unique_id and
    device_info, which is exactly how the two conventions diverged."""
    path = COMPONENT / filename
    if not path.exists():
        pytest.skip(f"{filename} not present")

    offenders = [name for name, bases in _entity_classes(path)
                 if "CoordinatorEntity" in bases]
    assert not offenders, (
        f"{filename}: these derive from CoordinatorEntity instead of GrowattEntity: "
        f"{offenders}"
    )


@pytest.mark.parametrize("filename", PLATFORMS)
def test_no_platform_sets_its_own_unique_id(filename):
    """The unique ID must come from GrowattEntity. A local assignment can silently use a
    different format and orphan every existing entity of that type."""
    path = COMPONENT / filename
    if not path.exists():
        pytest.skip(f"{filename} not present")

    hits = re.findall(r"^\s*self\._attr_unique_id\s*=.*$",
                      path.read_text(encoding="utf-8"), re.M)
    assert not hits, f"{filename}: unique_id set outside GrowattEntity:\n  " + "\n  ".join(hits)


@pytest.mark.parametrize("filename", PLATFORMS)
def test_no_platform_defines_its_own_device_info(filename):
    path = COMPONENT / filename
    if not path.exists():
        pytest.skip(f"{filename} not present")

    src = path.read_text(encoding="utf-8")
    assert "def device_info" not in src, (
        f"{filename}: defines device_info; GrowattEntity already provides it from the "
        f"device_type passed to __init__"
    )


@pytest.mark.parametrize("filename", PLATFORMS)
def test_entity_names_do_not_repeat_the_device_name(filename):
    """With has_entity_name = True, Home Assistant prefixes the device name itself.

    An entity name that also contains it renders twice — "Growatt Growatt Work Mode".
    That shipped for WIT TOU time entities until this was enforced.
    """
    path = COMPONENT / filename
    if not path.exists():
        pytest.skip(f"{filename} not present")

    bad = [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if re.search(r"_attr_name\s*=", line)
        and ("entry_name" in line
             or "data['name']" in line
             or 'data["name"]' in line
             or "config_entry.title" in line)
    ]
    assert not bad, (
        f"{filename}: entity name includes the device name, which Home Assistant adds "
        f"already:\n  " + "\n  ".join(bad)
    )
