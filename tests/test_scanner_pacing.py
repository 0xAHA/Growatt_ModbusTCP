"""The register scanner must pace its reads (Issue #360).

`_read_registers_chunked` uses a raw pymodbus client rather than `GrowattModbus`, so
`_enforce_read_interval()` never runs and nothing throttles it. Without an explicit pause
the chunks go out as fast as the socket accepts them.

That produced a diagnostic tool that failed on exactly the systems most likely to need it:
a user whose entities were updating normally got two consecutive scans back almost empty,
because the scan was hammering a gateway the poller was carefully spacing. The scan looked
like a dead inverter on hardware that was working.

The delay is taken from the entry's own `modbus_delay`, which is already tuned to what
that gateway tolerates.

Parsed from source rather than executed: diagnostic.py imports Home Assistant service
plumbing that the HA-free suite cannot load.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

DIAGNOSTIC = (Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
              / "diagnostic.py")
SOURCE = DIAGNOSTIC.read_text(encoding="utf-8")


def _chunked_signature() -> ast.FunctionDef:
    for node in ast.walk(ast.parse(SOURCE)):
        if isinstance(node, ast.FunctionDef) and node.name == "_read_registers_chunked":
            return node
    raise AssertionError("_read_registers_chunked not found")


def test_chunked_reader_accepts_a_delay():
    args = [a.arg for a in _chunked_signature().args.args]
    assert "delay_s" in args, (
        "_read_registers_chunked has no delay_s parameter, so nothing can pace it"
    )


def test_chunked_reader_actually_sleeps():
    """A parameter that is accepted and ignored is worse than none — it reads as solved."""
    fn = _chunked_signature()
    body = ast.get_source_segment(SOURCE, fn) or ""
    assert "time.sleep" in body, "_read_registers_chunked never sleeps"
    assert "delay_s" in body.split("def ", 1)[1], "delay_s is unused in the body"


def test_first_chunk_is_not_delayed():
    """Pausing before the first read of every range would add latency for nothing —
    the previous range's own pause has already elapsed."""
    fn = _chunked_signature()
    body = ast.get_source_segment(SOURCE, fn) or ""
    assert "first_chunk" in body, (
        "no guard against sleeping before the first chunk"
    )


@pytest.mark.parametrize(
    "call",
    [c for c in re.findall(r"_read_registers_chunked\([^)]*\)", SOURCE)
     if "client, start: int" not in c],
    ids=lambda c: c[:48],
)
def test_every_call_site_passes_a_delay(call):
    """One unpaced call site is enough to upset a marginal gateway for the reads that
    follow it, so the parameter has to be threaded everywhere rather than to the big
    range scans alone."""
    assert "delay_s=" in call, f"unpaced call: {call[:80]}"


def test_pacing_defaults_to_the_poller_default():
    """With no coordinator to read from, the scan should still pace at the same 250 ms
    the integration uses by default rather than falling back to zero."""
    assert re.search(r"_scan_delay_ms\s*=\s*250", SOURCE), (
        "scan pacing does not default to 250 ms"
    )
    assert "modbus_delay" in SOURCE, (
        "scan pacing does not read the entry's configured modbus_delay"
    )
