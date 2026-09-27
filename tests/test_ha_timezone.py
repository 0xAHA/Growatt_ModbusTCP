"""Inverter-clock arithmetic must use Home Assistant's time zone, not the host's (#458).

The RTC holds wall-clock time with no zone, and the clock sync writes it from
`dt_util.now()` - Home Assistant's configured zone. Anything that compares against it or
schedules by it has to use the same zone. `datetime.now()` is the host process's zone, which
on Docker without a TZ variable or in a dev container is UTC:

- the drift check reported a false drift of the whole UTC offset straight after a correct
  sync (found by @l4m4re in a dev container, with a fix);
- both Hold paths computed their TOU window in host time while the inverter runs it on its
  own clock, so on such a host the window landed hours off.

Parsed from source: these modules need Home Assistant to import.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

COMPONENT = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"


def _function(filename: str, name: str) -> str:
    source = (COMPONENT / filename).read_text(encoding="utf-8")
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return ast.get_source_segment(source, node)
    raise AssertionError(f"{name} not found in {filename}")


@pytest.mark.parametrize("filename,function", [
    ("coordinator.py", "_check_inverter_clock"),   # drift check
    ("select.py", "_apply_mode"),                  # Mode (VPP) Hold window
    ("diagnostic.py", "set_battery_mode"),         # Set Battery Mode action Hold window
])
def test_clock_arithmetic_uses_home_assistants_zone(filename, function):
    body = _function(filename, function)
    assert "dt_util.now()" in body, f"{function} does not take the time from Home Assistant"
    assert "datetime.now()" not in body and "dt.now()" not in body.replace("dt_util.now()", ""), (
        f"{function} still reads the host clock, which is UTC on many Docker hosts (#458)"
    )


@pytest.mark.parametrize("filename", sorted(p.name for p in COMPONENT.glob("*.py")))
def test_dt_util_is_always_imported_where_it_is_used(filename):
    """diagnostic.py imports dt_util per function, not at module level. A new use in a
    function without its own import is a NameError that only shows at runtime - on the one
    code path that needed it."""
    source = (COMPONENT / filename).read_text(encoding="utf-8")
    tree = ast.parse(source)

    def binds_dt_util(function) -> bool:
        """An import in this function's own body - not in a sibling nested function, which
        does not put the name in scope here."""
        stack = list(function.body)
        while stack:
            n = stack.pop()
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
                continue
            if isinstance(n, (ast.Import, ast.ImportFrom)) and any(
                (a.asname or a.name) == "dt_util" for a in n.names
            ):
                return True
            stack.extend(ast.iter_child_nodes(n))
        return False

    module_level = any(
        isinstance(n, (ast.Import, ast.ImportFrom))
        and any((a.asname or a.name) == "dt_util" for a in n.names)
        for n in tree.body
    )
    if module_level:
        return

    offenders = []

    def visit(node, enclosing_functions):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            enclosing_functions = enclosing_functions + [node]
        if isinstance(node, ast.Name) and node.id == "dt_util":
            if not any(binds_dt_util(f) for f in enclosing_functions):
                offenders.append(getattr(node, "lineno", "?"))
        for child in ast.iter_child_nodes(node):
            visit(child, enclosing_functions)

    visit(tree, [])
    assert not offenders, f"{filename}: dt_util used without an import in scope at lines {offenders}"
