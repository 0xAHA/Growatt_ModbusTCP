"""Child devices link to the parent across Home Assistant versions (#416).

`DeviceInfo["via_device"]` took an identifier tuple. It is deprecated because identifiers
are only unique *per config entry* and therefore no longer name a single device. The
replacement is `via_device_id` - an already-resolved device id, obtained with
`async_get_device_id_by_identifier()`, a helper added alongside the deprecation in HA
2026.8. The old form logs a warning now and raises from HA 2027.8.

See https://developers.home-assistant.io/blog/2026/08/24/device-registry-follow-up-changes/

The constraint that shapes the implementation: **this integration declares no minimum Home
Assistant version**, in neither `hacs.json` nor `manifest.json`. HACS will therefore offer
its releases to any HA. Calling the new helper unconditionally raises `AttributeError` on
anything older, and since every child DeviceInfo is built through this one path, that would
leave solar, grid, load and battery devices uncreated - a much worse outcome than a
deprecation line in a log.

So the code feature-detects. These tests pin both branches, because the failure they guard
against is invisible on a modern development machine: the new path is the one that gets
exercised, and the fallback is the one that matters to users who have not upgraded.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

REPO = Path(__file__).parent.parent
COMPONENT = REPO / "custom_components" / "growatt_modbus"
SOURCE = (COMPONENT / "coordinator.py").read_text(encoding="utf-8")


def _helper_node() -> ast.FunctionDef:
    tree = ast.parse(SOURCE)
    return next(
        n for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef) and n.name == "_via_parent_inverter"
    )


def _helper_source() -> str:
    """Executable statements only - docstring and comments removed.

    Both are stripped because the helper explains the deprecation at length and quotes the
    very identifiers under test: an earlier version of this file asserted `"via_device"` in
    the source and was satisfied by the docstring's own `DeviceInfo["via_device"]`, and
    another tripped over the word "raises" in prose. A check that its own explanation can
    satisfy is not a check.
    """
    fn = _helper_node()
    statements = fn.body
    if (
        statements
        and isinstance(statements[0], ast.Expr)
        and isinstance(statements[0].value, ast.Constant)
        and isinstance(statements[0].value.value, str)
    ):
        statements = statements[1:]
    return "\n".join(ast.unparse(node) for node in statements)


def test_no_minimum_home_assistant_version_is_declared():
    """Rule 4, and the premise of everything below. If a floor is ever declared at 2026.8
    or later, the fallback branch becomes dead code and this file should be revisited
    rather than continuing to demand it."""
    hacs = json.loads((REPO / "hacs.json").read_text(encoding="utf-8"))
    manifest = json.loads((COMPONENT / "manifest.json").read_text(encoding="utf-8"))

    assert "homeassistant" not in hacs and "homeassistant" not in manifest, (
        "a minimum HA version is now declared - if it is >= 2026.8, drop the via_device "
        "fallback and simplify _via_parent_inverter"
    )


def test_the_new_helper_is_feature_detected_not_assumed():
    """THE regression. Calling async_get_device_id_by_identifier unconditionally breaks
    every child device on HA older than 2026.8."""
    body = _helper_source()

    assert "getattr(" in body and "async_get_device_id_by_identifier" in body, (
        "the new device-id helper is not feature-detected; on older Home Assistant this "
        "raises AttributeError and no child devices are created at all"
    )


def _returned_dict_keys() -> set[str]:
    """Every constant key in a dict the helper returns.

    Read off the syntax tree rather than the text: ast.unparse normalises quoting, so a
    text search for a double-quoted key silently stops matching.
    """
    keys: set[str] = set()
    for node in ast.walk(_helper_node()):
        if isinstance(node, ast.Dict):
            for key in node.keys:
                if isinstance(key, ast.Constant) and isinstance(key.value, str):
                    keys.add(key.value)
    return keys


def test_the_deprecated_form_survives_as_the_fallback():
    """Older HA has no other way to express the parent link."""
    keys = _returned_dict_keys()

    assert "via_device" in keys, (
        "the identifier-tuple fallback has been removed - users on HA before 2026.8 would "
        "lose the parent link, or the devices entirely"
    )
    assert "via_device_id" in keys, "the modern form is not used on versions that have it"


def test_every_child_device_goes_through_the_one_resolution_point():
    """Five child devices are built here. A sixth added later must not reintroduce a
    hardcoded via_device, or it alone keeps warning after the rest are migrated."""
    assert SOURCE.count("**via_device,") == 5, (
        "child DeviceInfo dicts no longer all splat the resolved link"
    )
    assert '"via_device": via_device,' not in SOURCE, (
        "a child device still hardcodes the deprecated identifier form"
    )


def test_a_failed_lookup_does_not_take_the_devices_down():
    """The parent is pre-created before platforms are forwarded, so a miss should not
    happen - but losing a parent link is recoverable and raising during setup is not."""
    body = _helper_source()

    assert "return {}" in body, (
        "an unresolved parent has no safe branch; setup should degrade to an unparented "
        "device rather than fail"
    )
    # Checked on the syntax tree, not the text: the docstring legitimately contains the
    # word "raises" when describing HA 2027.8.
    raises = [n for n in ast.walk(_helper_node()) if isinstance(n, ast.Raise)]
    assert not raises, "the resolution path raises, which would abort device setup"
