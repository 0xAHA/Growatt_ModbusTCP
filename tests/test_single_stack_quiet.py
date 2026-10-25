"""A single battery stack is not a fault (#483).

An SPH 8000TL3 BH-UP with one battery logged "Optional VPP range (31300-31323) failed -
battery sensors may be temporarily unavailable" every session. 31300-31599 are battery
stacks 2-4: with one stack they do not answer, by design. That case now logs at debug;
other optional ranges still warn once.
"""
from __future__ import annotations

import importlib
import logging

_gm = importlib.import_module("growatt_under_test.growatt_modbus")

MAP = "SPH_TL3_3000_10000_V201"


def _poll(dead_from: int, dead_to: int):
    client = _gm.GrowattModbus(connection_type="tcp", host="10.0.0.1", port=502,
                               slave_id=1, register_map=MAP)

    def read(start, count, log_errors=True):
        if dead_from <= start < dead_to:
            return None
        return [0] * count
    client.read_input_registers = read
    client.read_holding_registers = lambda start, count: [0] * count
    client.read_all_data()


def _optional_warnings(caplog):
    return [r for r in caplog.records
            if r.levelno >= logging.WARNING and "Optional VPP range" in r.getMessage()]


def test_a_missing_second_stack_does_not_warn(caplog):
    caplog.set_level(logging.DEBUG)
    _poll(31300, 31600)
    assert not _optional_warnings(caplog)
    assert any("expected with a single battery stack" in r.getMessage() for r in caplog.records)


def test_other_optional_ranges_still_warn(caplog):
    """The quieting is scoped to stacks 2-4; stack 1 failing is still worth a warning."""
    caplog.set_level(logging.DEBUG)
    _poll(31200, 31300)
    assert _optional_warnings(caplog)
