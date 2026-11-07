"""TOU Priority / Enable skip a write that would change nothing (#491).

The time entities already compared a fresh read with what they were about to write; the
Priority and Enable selects did not, so re-selecting the current option re-wrote the pair.
Those registers' storage is not documented (the V1.39 range has no EEPROM note), so an
unnecessary write is worth avoiding.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

COMPONENT = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
SRC = (COMPONENT / "select.py").read_text(encoding="utf-8")


def _method(cls):
    tree = ast.parse(SRC)
    klass = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == cls)
    fn = next(n for n in klass.body if isinstance(n, ast.AsyncFunctionDef) and n.name == "async_select_option")
    return ast.get_source_segment(SRC, fn)


@pytest.mark.parametrize("cls", ["GrowattModTouPriority", "GrowattModTouEnable"])
def test_an_unchanged_value_is_not_written(cls):
    body = _method(cls)
    skip = body.index("if is_fresh and new_raw == current_raw:")
    assert skip < body.index("write_registers"), "the comparison must come before the write"
    assert "return" in body[skip:body.index("write_registers")]
