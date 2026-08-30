"""Write verification must not amplify writes (#402).

The old loop wrote, waited 0.5 s, read back, and on a mismatch **wrote again** - up to
three times. On an inverter that commits slowly the read-back returns the previous value,
which looks identical to a reversion, so a single user action became three EEPROM writes.

A reporter dragging a slider on an SPF 6000 hit both halves of this at once: the slider
issued a write per step, and each of those was tripled. He aimed for 48.0 V and the
inverter ended on 49.6 V, confirmed on its LCD.

The write is now issued once and the register polled until it settles.
"""
import importlib
import sys

import pytest

sys.path.insert(0, "tests")

_gm = importlib.import_module("growatt_under_test.growatt_modbus")


class _Recorder:
    """Counts writes and serves a scripted sequence of read-backs."""

    def __init__(self, reads):
        self.writes = []
        self._reads = list(reads)
        self.read_count = 0

    def write_register(self, register, value):
        self.writes.append((register, value))
        return True

    def read_holding_registers(self, register, count):
        self.read_count += 1
        if not self._reads:
            return [0]
        value = self._reads.pop(0)
        return None if value is None else [value]


def _client(reads):
    client = _gm.GrowattModbus.__new__(_gm.GrowattModbus)
    rec = _Recorder(reads)
    client.write_register = rec.write_register
    client.read_holding_registers = rec.read_holding_registers
    client._rec = rec
    return client


@pytest.fixture(autouse=True)
def _no_sleeping(monkeypatch):
    monkeypatch.setattr(_gm.time, "sleep", lambda _s: None)


def test_a_slow_commit_is_not_treated_as_a_reversion():
    """The reporter's exact shape: the register still shows the old value on the first
    read and the new one shortly after. That is a slow commit, not a rejection."""
    client = _client([490, 480])          # old value, then the value we wrote
    ok, verified = client.write_register_verified(37, 480)

    assert (ok, verified) == (True, True)
    assert len(client._rec.writes) == 1, (
        f"expected one write, got {len(client._rec.writes)}: {client._rec.writes}"
    )


def test_only_one_write_is_ever_issued_even_when_it_never_settles():
    """The write was acknowledged at the Modbus level. Re-writing is speculative and
    spends an EEPROM cycle to learn nothing - a genuine rejection refuses them all."""
    client = _client([490, 490, 490])     # never takes
    ok, verified = client.write_register_verified(37, 480)

    assert (ok, verified) == (True, False)
    assert len(client._rec.writes) == 1, "the write was re-issued on a failed verify"


def test_an_immediate_match_costs_one_read():
    client = _client([480])
    assert client.write_register_verified(37, 480) == (True, True)
    assert client._rec.read_count == 1
    assert len(client._rec.writes) == 1


def test_a_read_error_does_not_fail_the_write():
    """The write succeeded; an unverifiable read-back is not evidence against it."""
    client = _client([None])
    assert client.write_register_verified(37, 480) == (True, True)
    assert len(client._rec.writes) == 1


def test_values_are_compared_as_16_bit():
    """Negative setpoints are written as two's complement and read back unsigned."""
    client = _client([65526])             # -10 as unsigned
    assert client.write_register_verified(3049, -10) == (True, True)


def test_a_failed_write_still_raises():
    """A Modbus-level failure is a real error and must not be swallowed by the new
    read-until-settled path."""
    client = _client([480])

    def _boom(register, value):
        raise _gm.ModbusWriteError(register, [value], "refused")

    client.write_register = _boom
    with pytest.raises(_gm.ModbusWriteError):
        client.write_register_verified(37, 480)


def test_every_writable_number_uses_a_box_not_a_slider():
    """Home Assistant's number row fires its write on the DOM `change` event: once on blur
    or Enter for a box, but once per step while dragging a slider. Every control on that
    platform is a persistent holding register, so a drag wrote every value it passed
    through - and left one reporter's inverter on a threshold he never selected (#402)."""
    import ast
    from pathlib import Path

    source = (Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
              / "number.py").read_text(encoding="utf-8")
    tree = ast.parse(source)

    sliders = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        for stmt in node.body:
            if not isinstance(stmt, ast.Assign):
                continue
            for target in stmt.targets:
                if getattr(target, "id", None) != "_attr_mode":
                    continue
                if "SLIDER" in (ast.get_source_segment(source, stmt.value) or ""):
                    sliders.append(node.name)

    assert not sliders, f"these write persistent registers from a slider: {sliders}"
