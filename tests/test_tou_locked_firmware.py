"""MOD/MID TOU controls are not offered on firmware that rejects them (#485).

Growatt firmware reporting VPP V2.05 (holding 30099 = 205) gives TOU weekday calendars and
Idle / Idle Charge modes. Writes to the legacy slots 3038-3059 are accepted and reverted
within seconds, and the new modes read back as the classic ones: a MOD 12KTL3-HU (#480) and
two MID TL3-XH on DN1.0 / DNBA0851 (#485). The controls looked like they worked and did
nothing.
"""
from __future__ import annotations

import importlib
from pathlib import Path

import pytest

_const = importlib.import_module("growatt_under_test.const")
COMPONENT = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
MOD = _const.REGISTER_MAPS["MOD_6000_15000TL3_XH"]


@pytest.mark.parametrize("raw, locked", [(205, True), (206, True), (204, False),
                                         (201, False), (None, False), ("205", False)])
def test_the_lock_follows_the_reported_version(raw, locked):
    assert _const.tou_legacy_writes_locked(MOD, raw) is locked


def test_only_maps_that_declare_it_are_affected():
    """Every other family keeps its TOU controls on any version until shown otherwise."""
    declaring = [n for n, m in _const.REGISTER_MAPS.items() if m.get("tou_locked_from_vpp")]
    assert declaring == ["MOD_6000_15000TL3_XH"]
    assert not _const.tou_legacy_writes_locked({}, 205)


def _src(name):
    return (COMPONENT / name).read_text(encoding="utf-8")


@pytest.mark.parametrize("module", ["select.py", "time.py"])
def test_setup_leaves_them_out_when_locked(module):
    src = _src(module)
    assert "if 3038 in holding_registers and coordinator.tou_legacy_locked:" in src


@pytest.mark.parametrize("module, count", [("select.py", 2), ("time.py", 1)])
def test_existing_entities_go_unavailable_and_refuse_writes(module, count):
    src = _src(module)
    assert src.count("return super().available and not self.coordinator.tou_legacy_locked") == count
    assert src.count("TOU_LOCKED_MESSAGE.format(") == count


def test_the_version_is_persisted_for_the_next_setup():
    src = _src("coordinator.py")
    assert 'self._vpp_protocol_raw = entry.data.get("vpp_protocol_raw")' in src
    assert '"vpp_protocol_raw": self._vpp_protocol_raw' in src


def test_registered_entities_are_cleared_at_setup():
    src = _src("__init__.py")
    assert "if coordinator.tou_legacy_locked:" in src
    assert 'f"{entry.entry_id}_mod_tou_{_period[\'period\']}_{_suffix}"' in src
