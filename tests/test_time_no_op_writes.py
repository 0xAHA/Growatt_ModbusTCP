"""Time entities skip writes that would change nothing (#392).

TOU slot registers are believed to be held in non-volatile memory with finite write
endurance. Believed, not known — Growatt marks a handful of VPP registers "Not storage"
and documents nothing about the rest, so the rest are treated conservatively.

A reporter building a price-driven controller that recomputes nine TOU slots daily asked
what the write budget was. Most of those slots will be unchanged on most days, and there is
no reason to spend a write cycle proving it. `number.py` has skipped no-op writes since
v1.6.6; the time entities did not, and a TOU scheduler writes through the time entities.

The interesting half is when it must NOT skip:

* On the cached fallback, where values may be a scan interval old. A skipped write that
  should have happened is worse than a redundant one — the same reasoning that makes these
  methods re-read sibling registers rather than trust coordinator.data at all.
* On the WIT TOU entity, whose "current value" is a command cache written only after a
  successful write and never read back from the inverter. Comparing against what we last
  commanded would skip a write that was correcting an external change.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

SOURCE_PATH = (Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
               / "time.py")
SOURCE = SOURCE_PATH.read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)


def _method(class_name: str, method_name: str) -> ast.FunctionDef:
    for node in TREE.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if child.name == method_name:
                        return child
    raise AssertionError(f"{class_name}.{method_name} not found")


def _source_of(node) -> str:
    return ast.get_source_segment(SOURCE, node) or ""


# --------------------------------------------------------------------------
# The guard exists where a fresh read is available
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "class_name",
    ["GrowattGenericTime", "GrowattModTouTime"],
)
def test_the_guard_is_present(class_name):
    body = _source_of(_method(class_name, "async_set_value"))
    assert "values_are_fresh" in body, (
        f"{class_name} writes unconditionally — a daily recompute burns a write cycle per "
        f"slot even when nothing changed"
    )
    assert "new_start == current_start" in body and "new_end == current_end" in body, (
        f"{class_name} does not compare both halves of the pair before skipping"
    )


@pytest.mark.parametrize(
    "class_name",
    ["GrowattGenericTime", "GrowattModTouTime"],
)
def test_the_guard_returns_before_writing(class_name):
    """A guard that logs but falls through would be decoration."""
    body = _source_of(_method(class_name, "async_set_value"))
    guard = body.index("values_are_fresh and")
    write = body.index("write_registers")
    assert guard < write, f"{class_name} evaluates the guard after the write"
    assert "return" in body[guard:write], (
        f"{class_name} does not return from the guard, so the write happens anyway"
    )


# --------------------------------------------------------------------------
# ...and only where it is safe
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "class_name",
    ["GrowattGenericTime", "GrowattModTouTime"],
)
def test_the_cached_fallback_still_writes(class_name):
    """`values_are_fresh` must be set False on the fallback branch. Skipping on stale data
    could drop a write the user asked for."""
    body = _source_of(_method(class_name, "async_set_value"))
    assert "values_are_fresh = False" in body, (
        f"{class_name} never marks the cached fallback as stale, so the guard would trust "
        f"values up to a scan interval old"
    )
    assert body.index("values_are_fresh = True") < body.index("values_are_fresh = False"), (
        "the fresh-read branch must be the one that sets True"
    )


def test_the_wit_entity_is_deliberately_not_guarded():
    """GrowattWitVppTouTime compares against coordinator.wit_vpp_tou_p*_{start,end}, which
    is set only after a successful write and never populated from a read. Guarding on it
    would skip a write intended to correct a change made by the Growatt cloud or app."""
    body = _source_of(_method("GrowattWitVppTouTime", "async_set_value"))
    assert "values_are_fresh" not in body, (
        "the WIT TOU entity is guarded against a command cache, not against inverter "
        "state — it can skip a correcting write"
    )


def test_the_wit_value_is_never_populated_from_a_register_read():
    """Pins the reason above.

    coordinator.py is where register values are decoded onto the coordinator. It does not
    mention the WIT TOU start/end attributes at all, which is what makes them a command
    cache rather than inverter state. If a read-back is ever added there, this fails and
    GrowattWitVppTouTime becomes eligible for the same guard as the other two.
    """
    coordinator = (SOURCE_PATH.parent / "coordinator.py").read_text(encoding="utf-8")
    assert "wit_vpp_tou_p" not in coordinator, (
        "coordinator.py now references the WIT TOU period attributes. If it populates "
        "them from a register read they are no longer a command cache, and the no-op "
        "write guard can be extended to GrowattWitVppTouTime."
    )
