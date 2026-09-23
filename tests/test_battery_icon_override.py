"""An explicit icon on a battery-percentage sensor breaks its dynamic fill level (#455).

Home Assistant computes a charge-level icon (mdi:battery, mdi:battery-60,
mdi:battery-outline, ...) automatically for any entity with `device_class: battery`, but
only when the entity has no icon of its own - an explicit `icon` always wins. `battery_soc`
carried `"icon": "mdi:battery"` alongside `device_class: SensorDeviceClass.BATTERY`, so the
icon was permanently the "full" glyph regardless of state; only its colour changed. The
Energy Dashboard's battery tile showed this as a battery that never seemed to discharge.

Reported by @AzraelsDisk, who isolated it precisely: an identical sensor with the `icon:`
line removed picked up the dynamic fill immediately.

Parsed from source: sensor.py imports Home Assistant sensor plumbing the HA-free suite
cannot load.
"""
from __future__ import annotations

import ast
from pathlib import Path

SENSOR_PY = (Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
             / "sensor.py")
SOURCE = SENSOR_PY.read_text(encoding="utf-8")


def _sensor_definitions() -> dict[str, ast.Dict]:
    """Map sensor key -> its definition dict AST node, without evaluating the module."""
    tree = ast.parse(SOURCE)
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "SENSOR_DEFINITIONS"
        ):
            definitions = node.value
            assert isinstance(definitions, ast.Dict)
            result = {}
            for key_node, value_node in zip(definitions.keys, definitions.values):
                # A bare `**something` spread has no key node (None) - not a named
                # sensor definition, so it is not something this test can check.
                if isinstance(key_node, ast.Constant) and isinstance(value_node, ast.Dict):
                    result[key_node.value] = value_node
            return result
    raise AssertionError("SENSOR_DEFINITIONS not found")


def _field_names(definition: ast.Dict) -> set[str]:
    return {
        key.value for key in definition.keys
        if isinstance(key, ast.Constant)
    }


def test_battery_soc_has_no_static_icon():
    definition = _sensor_definitions()["battery_soc"]
    assert "icon" not in _field_names(definition), (
        "battery_soc has an explicit icon, which overrides Home Assistant's dynamic "
        "charge-level icon for device_class BATTERY - the Energy Dashboard tile will "
        "show a permanently full battery regardless of state (#455)"
    )


def test_no_battery_percentage_sensor_carries_a_static_icon():
    """The general form of the same mistake: any sensor whose device_class is BATTERY
    (a state-of-charge percentage, by Home Assistant's own definition of that device
    class) must not set its own icon, or the same bug reappears under a new name."""
    offenders = []
    for key, definition in _sensor_definitions().items():
        fields = _field_names(definition)
        if "device_class" not in fields or "icon" not in fields:
            continue
        device_class_node = next(
            v for k, v in zip(definition.keys, definition.values)
            if isinstance(k, ast.Constant) and k.value == "device_class"
        )
        device_class_src = ast.unparse(device_class_node)
        if device_class_src == "SensorDeviceClass.BATTERY":
            offenders.append(key)

    assert offenders == [], (
        f"these sensors combine device_class BATTERY with an explicit icon, which "
        f"defeats Home Assistant's dynamic charge-level icon: {offenders} (#455)"
    )
