"""No function may re-import a name the module already imports (#479).

A function that imports a name anywhere in its body makes that name local for the whole
function. Any use of the module-level binding earlier in the function, or on a path where
the local import never runs, then raises UnboundLocalError instead.

It shipped in v2.0.6-b6: native_value in sensor.py imported PROFILE_STATUS_MAP locally in its
status branch, and the Grid Connection Status branch above it, added for #474, used the
module-level name. On an SPH without register 31000 that sensor raised on every poll - 1,029
times in 17 hours on one install. The same shape was latent in the coordinator: a local
import of GrowattData in one branch left the startup-failure path, which builds the same
placeholder, to raise instead of loading with empty state.

Nothing else catches it: the code imports, the tests that read source pass, and it only
fails on the path that hits the name first.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

COMPONENT = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
FILES = sorted(p for p in COMPONENT.rglob("*.py") if "__pycache__" not in p.parts)


def _imported(nodes) -> set[str]:
    names = set()
    for node in nodes:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                names.add(alias.asname or alias.name.split(".")[0])
    return names


@pytest.mark.parametrize("path", FILES, ids=lambda p: str(p.relative_to(COMPONENT)))
def test_no_function_shadows_a_module_level_import(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    module_level = _imported(tree.body)
    clashes = []
    for fn in ast.walk(tree):
        if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            shadowed = _imported(ast.walk(fn)) & module_level
            clashes += [f"{fn.name} (line {fn.lineno}): {name}" for name in sorted(shadowed)]
    assert not clashes, (
        "re-imported inside a function, which makes the name local for the whole function: "
        + "; ".join(clashes)
    )
