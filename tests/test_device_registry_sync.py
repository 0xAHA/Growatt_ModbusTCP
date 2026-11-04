"""Identified firmware and serial reach the device registry (#485).

The inverter device is pre-created at setup with no firmware or serial, and identification
runs on the first successful poll. When that poll came after the entities were registered,
nothing told the registry: a MID 25KTL3-XH's device page showed no firmware all session
while the diagnostics held DN1.0 / DNBA08510120.
"""
from __future__ import annotations

import ast
import importlib
from pathlib import Path

_const = importlib.import_module("growatt_under_test.const")
COMPONENT = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"

INFO = {"model": "MID 25KTL3-XH", "serial_number": "ABC123",
        "sw_version": "DN1.0 (DNBA08510120)", "hw_version": "Protocol 2.05"}


def test_a_blank_registry_entry_gets_everything_known():
    blank = dict.fromkeys(_const.DEVICE_REGISTRY_FIELDS)
    assert _const.device_registry_changes(blank, INFO) == INFO


def test_nothing_is_sent_when_the_registry_already_agrees():
    assert _const.device_registry_changes(dict(INFO), INFO) == {}


def test_an_unknown_field_never_blanks_a_known_one():
    known = dict(INFO)
    assert _const.device_registry_changes(known, {**INFO, "serial_number": None}) == {}


def _function(name):
    source = (COMPONENT / "coordinator.py").read_text(encoding="utf-8")
    fn = next(n for n in ast.walk(ast.parse(source))
              if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name)
    return ast.get_source_segment(source, fn)


def test_identification_marks_the_device_info_for_syncing():
    body = _function("_read_device_identification")
    assert "self._device_info_pending = True" in body


def test_the_poll_applies_it_on_the_event_loop():
    body = _function("_async_update_data")
    assert "self._async_sync_device_registry()" in body
    sync = _function("_async_sync_device_registry")
    assert "async_update_device(" in sync and "device_registry_changes(" in sync


def test_a_blank_23_27_falls_back_to_the_3000_range():
    """MID 25KTL3-XH: 23-27 all zero, serial at 3001-3005 (#485)."""
    body = _function("_read_device_identification")
    fallback = body.index("fallback = self._read_holding(3000, 15)")
    assert body.index("if not serial_found:") < fallback
