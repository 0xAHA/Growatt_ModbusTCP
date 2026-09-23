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
    """With no entry to read from, the scan should still pace at the same 250 ms
    the integration uses by default rather than falling back to zero."""
    assert re.search(r"scan_delay_ms\s*=\s*250", SOURCE), (
        "scan pacing does not default to 250 ms"
    )
    assert "modbus_delay" in SOURCE, (
        "scan pacing does not read the entry's configured modbus_delay"
    )


# ---------------------------------------------------------------------------
# Scanning a disabled entry (#360)
# ---------------------------------------------------------------------------
#
# Pacing alone did not fix the reporter's scan, because the documented procedure and
# the code contradicted each other. The docs say to disable the integration first so
# the poller stops competing for the gateway. Disabling unloads the entry, which clears
# `runtime_data`, which is where the service looked for the connection details — so it
# aborted, and the only way to scan at all was to retype host and port by hand. That
# path silently substitutes defaults for slave_id, modbus_delay and block size, and a
# gateway tuned to 25-register reads at a long delay cannot serve 125-register reads at
# the default one. Every range then reports "no response" on hardware that polls fine.
#
# `entry.data` and `entry.options` are persisted and readable while disabled; only the
# coordinator (used to enrich the CSV with entity values) genuinely goes away.


def _service_handler_source() -> str:
    """The register-scan service handler, where the entry is resolved."""
    for node in ast.walk(ast.parse(SOURCE)):
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "export_register_dump":
            return ast.get_source_segment(SOURCE, node) or ""
    raise AssertionError("export_register_dump service handler not found")


def test_entry_details_do_not_require_a_loaded_coordinator():
    handler = _service_handler_source()
    assert "async_get_entry" in handler, (
        "the scan resolves connection details from the coordinator rather than the "
        "config entry, so it cannot scan a disabled entry — which is the state the "
        "documented procedure asks for"
    )


def test_a_missing_coordinator_does_not_abort_the_scan():
    """The coordinator only enriches the CSV. Losing it must cost profile and entity
    columns, never the scan itself."""
    handler = _service_handler_source()
    aborts = re.findall(
        r"if not coordinator[^\n]*\n\s*_LOGGER\.error[^\n]*\n\s*return", handler
    )
    assert not aborts, f"scan still aborts when no coordinator is loaded: {aborts}"


def test_pacing_and_block_size_come_from_the_entry_options():
    """Both are tuned per gateway. Reading one from the entry and leaving the other at
    a service default still sends 125-register requests to a link that cannot take them.
    """
    handler = _service_handler_source()
    assert re.search(r"entry\.options\.get\(\s*[\"']modbus_delay", handler), (
        "scan pacing is not read from the entry's options"
    )
    assert re.search(r"resolve_block_size\(\s*entry\.options", handler), (
        "scan block size ignores the entry's configured max_block_size"
    )


def test_an_explicit_block_size_still_wins():
    """The service exposes block_size so a user can force 1-register reads to isolate a
    fault. Inheriting the entry's value must not override what they typed."""
    handler = _service_handler_source()
    assert re.search(r"[\"']block_size[\"']\s+not in call\.data", handler), (
        "the entry's block size is applied unconditionally, overriding an explicit one"
    )


def test_the_serial_device_path_uses_the_real_key():
    """The config entry stores the serial path under CONF_DEVICE_PATH ("device_path"),
    the same key config_flow.py writes it under. Reading the bare literal "device"
    instead always misses, so a config_entry-selected serial scan connected to None
    regardless of which device was picked (#432, @JHPHendriks: "Cannot connect to
    None @ 9600 baud" - baudrate resolved correctly, only the device path did not,
    which is the signature of a wrong dict key rather than a real connection failure)."""
    handler = _service_handler_source()
    assert 'entry_data.get("device")' not in handler, (
        "reads the entry's serial device path under the literal key \"device\", which "
        "config_flow.py never writes - always resolves to None (#432)"
    )
    assert "CONF_DEVICE_PATH" in handler, (
        "the device path is not resolved from CONF_DEVICE_PATH, the key config_flow.py "
        "actually stores it under"
    )
