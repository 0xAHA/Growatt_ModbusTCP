"""The set_tou_period action: one whole legacy TOU period in one write, or none (#491).

The Start, End, Priority and Enable entities each write the period's register pair, so an
automation changing a whole period cost up to four writes to registers that may be
EEPROM-backed. The action builds the pair once and writes it once - and not at all when
the inverter already holds it.
"""
import ast
import importlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, "tests")

tou = importlib.import_module("growatt_under_test.tou_packing")
const = importlib.import_module("growatt_under_test.const")

COMPONENT = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"

# Period enabled, Battery priority, 01:00 - 05:59
ENABLED_BATTERY_0100 = 0x8000 | (1 << 13) | (1 << 8) | 0
END_0559 = (5 << 8) | 59


def test_everything_given_builds_the_documented_words():
    start, end, changed = tou.plan_period(
        [0, 0], start=(1, 0), end=(5, 59), priority="battery", enabled=True
    )
    assert (start, end) == (ENABLED_BATTERY_0100, END_0559)
    assert changed


def test_the_same_request_twice_writes_nothing():
    _, _, changed = tou.plan_period(
        [ENABLED_BATTERY_0100, END_0559],
        start=(1, 0), end=(5, 59), priority="battery", enabled=True,
    )
    assert not changed


@pytest.mark.parametrize("kwargs,expected_start,expected_end", [
    ({"enabled": False}, ENABLED_BATTERY_0100 & ~0x8000, END_0559),
    ({"priority": "grid"}, (ENABLED_BATTERY_0100 & ~0x6000) | (2 << 13), END_0559),
    ({"start": (2, 30)}, 0x8000 | (1 << 13) | (2 << 8) | 30, END_0559),
    ({"end": (23, 59)}, ENABLED_BATTERY_0100, (23 << 8) | 59),
])
def test_fields_left_out_keep_what_the_inverter_holds(kwargs, expected_start, expected_end):
    start, end, changed = tou.plan_period([ENABLED_BATTERY_0100, END_0559], **kwargs)
    assert (start, end) == (expected_start, expected_end)
    assert changed


def test_load_priority_clears_the_priority_bits():
    start, _, _ = tou.plan_period([ENABLED_BATTERY_0100, END_0559], priority="load")
    assert start & 0x6000 == 0
    assert start & 0x8000  # enable untouched


def test_a_change_to_only_the_end_word_is_still_a_change():
    _, _, changed = tou.plan_period([ENABLED_BATTERY_0100, END_0559], end=(6, 0))
    assert changed


# --------------------------------------------------------------------- the handler
def _handler_source() -> str:
    source = (COMPONENT / "diagnostic.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    func = next(
        n for n in ast.walk(tree)
        if isinstance(n, ast.AsyncFunctionDef) and n.name == "set_tou_period"
    )
    return ast.get_source_segment(source, func)


def test_nothing_is_written_when_unchanged_or_unreadable():
    body = _handler_source()
    write_at = body.index("client.write_registers")
    # A failed read raises before any write: no rebuilding from a stale copy (#475).
    assert body.index("Nothing was written") < write_at
    # An unchanged period returns before the write.
    assert body.index("if not changed:") < write_at
    assert "tou_plan_period(" in body


def test_refused_on_firmware_that_rejects_legacy_tou():
    body = _handler_source()
    assert "tou_legacy_locked" in body
    assert body.index("tou_legacy_locked") < body.index("client.write_registers")


def test_the_action_is_registered_and_documented():
    source = (COMPONENT / "diagnostic.py").read_text(encoding="utf-8")
    assert 'SERVICE_SET_TOU_PERIOD = "set_tou_period"' in source
    services = (COMPONENT / "services.yaml").read_text(encoding="utf-8")
    assert "\nset_tou_period:" in services


def test_every_period_the_action_accepts_exists():
    assert sorted(p["period"] for p in const.MOD_TOU_PERIODS) == list(range(1, 10))


def test_a_call_with_nothing_to_set_is_rejected():
    import voluptuous as vol
    if not getattr(vol, "__file__", None):
        pytest.skip("voluptuous is the conftest stub here; the real one runs in CI")
    diagnostic = importlib.import_module("growatt_under_test.diagnostic")
    with pytest.raises(vol.Invalid):
        diagnostic._require_a_tou_field({"device_id": "x", "period": 1})
    assert diagnostic._require_a_tou_field({"device_id": "x", "period": 1, "enabled": False})
