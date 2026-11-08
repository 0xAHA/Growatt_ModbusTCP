"""Deferred entity listeners must be removed at most once during reload."""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

COMPONENT = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"


@pytest.mark.parametrize(
    ("filename", "cleanup_name", "check_name", "deferred_name"),
    [
        ("select.py", "_remove_vpp_listener_once", "_async_check_deferred_vpp", "deferred_vpp"),
        ("sensor.py", "_remove_listener_once", "_async_check_deferred_sensors", "deferred"),
    ],
)
def test_deferred_listener_cleanup_is_idempotent(
    filename: str,
    cleanup_name: str,
    check_name: str,
    deferred_name: str,
) -> None:
    """Reload can invoke unload after the deferred callback already removed the listener."""
    source = (COMPONENT / filename).read_text(encoding="utf-8")
    tree = ast.parse(source)
    setup = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "async_setup_entry"
    )
    cleanup = next(
        node
        for node in ast.walk(setup)
        if isinstance(node, ast.FunctionDef) and node.name == cleanup_name
    )
    deferred_check = next(
        node
        for node in ast.walk(setup)
        if isinstance(node, ast.FunctionDef) and node.name == check_name
    )

    assert any(
        isinstance(node, ast.Nonlocal) and "listener_removed" in node.names
        for node in cleanup.body
    )
    assert any(
        isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "listener_removed"
            for target in node.targets
        )
        and isinstance(node.value, ast.Constant)
        and node.value.value is True
        for node in ast.walk(cleanup)
    )
    assert any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == cleanup_name.removesuffix("_once")
        for node in ast.walk(cleanup)
    )

    deferred_source = ast.get_source_segment(source, deferred_check)
    assert deferred_source is not None
    assert f"if not {deferred_name}:" in deferred_source
    assert f"{cleanup_name}()" in deferred_source

    setup_source = ast.get_source_segment(source, setup)
    assert setup_source is not None
    assert f"config_entry.async_on_unload({cleanup_name})" in setup_source
