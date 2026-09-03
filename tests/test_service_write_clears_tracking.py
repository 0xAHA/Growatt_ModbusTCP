"""A service write must not leave an entity's write-check expecting the old value (#411).

Entity writes register an expected value with `coordinator.track_write()`, and a poll that
disagrees twice running raises **"Write reversion detected"**. The `write_register` and
`write_registers` services write the same registers without touching that bookkeeping.

So an automation that sets a time entity and then calls `write_registers` on the same slot
- two legitimate writes, seconds apart - left the tracker still expecting the entity's
value. It then reported the service's own value as a reversion, blaming the inverter or a
cloud dongle for a change the user had just made deliberately.

A reporter chased that through three separate issue reports over a week before finding the
duplicate write in his own automation. The warning was ours.

The fix is to forget the expectation rather than re-track it: `track_write()` keys its
expectation to a `GrowattData` attribute name, and these services take a raw address with
no such mapping, so there is nothing honest to re-track it against.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

COMPONENT = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
SOURCE = (COMPONENT / "diagnostic.py").read_text(encoding="utf-8")


def _service(name: str) -> str:
    """Source of one service handler, comments stripped.

    Comments are removed because both handlers explain the bug at length and name the
    very call they are being checked for.
    """
    tree = ast.parse(SOURCE)
    fn = next(
        n for n in ast.walk(tree)
        if isinstance(n, ast.AsyncFunctionDef) and n.name == name
    )
    body = ast.get_source_segment(SOURCE, fn)
    return "\n".join(
        line for line in body.splitlines() if not line.strip().startswith("#")
    )


@pytest.mark.parametrize("service", ["write_register", "write_registers"])
def test_a_service_write_clears_the_pending_check(service):
    """Without this, the tracker keeps comparing against a value the user has replaced."""
    body = _service(service)

    assert "_pending_write_checks.pop" in body, (
        f"{service} does not clear the write-check for the registers it writes, so a "
        f"later poll will report the value it just wrote as a reversion"
    )


def test_the_multi_register_service_clears_every_register_it_wrote():
    """write_registers is FC16 over a consecutive block. Clearing only the first address
    would leave the rest of the block still expecting stale values - and the reported case
    was a [start, end, enable] triple, where the stale expectation was on the second."""
    body = _service("write_registers")

    assert "range(len(values))" in body and "register + _offset" in body, (
        "only the base address is cleared; the remaining registers of the block keep "
        "their stale expectations"
    )


def test_the_tracking_it_clears_actually_exists():
    """Rule 4: absence of evidence needs the evidence to have been possible. If the
    coordinator stopped keeping this dict, the assertions above would pass while testing
    nothing at all."""
    coordinator = (COMPONENT / "coordinator.py").read_text(encoding="utf-8")

    assert "_pending_write_checks" in coordinator
    assert "def track_write" in coordinator
    assert "Write reversion detected" in coordinator, (
        "the warning these services were producing spuriously no longer exists - re-read "
        "this file's premise before trusting it"
    )
