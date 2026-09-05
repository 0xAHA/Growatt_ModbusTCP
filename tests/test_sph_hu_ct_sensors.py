"""SPH-HU split-phase CT sensors (#418).

The HU-US power-flow block uses V1.39 R/S as the two 120 V legs. The whole-service
resolution from #419 stays authoritative; these tests only ensure the useful per-leg
measurements are surfaced without changing that netting behavior.
"""
from __future__ import annotations

import ast
import importlib
from pathlib import Path

import pytest

COMPONENT = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
SOURCE = (COMPONENT / "growatt_modbus.py").read_text(encoding="utf-8")
PROFILES = importlib.import_module("growatt_under_test.profiles").REGISTER_MAPS


CT_REGISTERS = {
    "ct_grid_import_l1": 1016,
    "ct_grid_import_l2": 1018,
    "ct_grid_export_l1": 1024,
    "ct_grid_export_l2": 1026,
    "inverter_to_load_l1": 1032,
    "inverter_to_load_l2": 1034,
}


def test_hu_maps_the_six_split_phase_leg_measurements():
    regs = PROFILES["SPH_8000_10000_HU"]["input_registers"]
    for sensor, low_addr in CT_REGISTERS.items():
        high_addr = low_addr - 1
        assert regs[high_addr]["name"] == f"{sensor}_high"
        assert regs[low_addr]["name"] == f"{sensor}_low"
        assert regs[low_addr]["combined_scale"] == 0.1
        assert regs[low_addr]["combined_unit"] == "W"


def test_hu_import_aliases_keep_419_phase_sum_fallback_working():
    regs = PROFILES["SPH_8000_10000_HU"]["input_registers"]
    assert regs[1016]["alias"] == "power_to_user_r_low"
    assert regs[1018]["alias"] == "power_to_user_s_low"
    assert regs[1019]["name"] == "power_to_user_t_high"
    assert regs[1020]["name"] == "power_to_user_t_low"


def test_whole_service_total_registers_are_unchanged():
    regs = PROFILES["SPH_8000_10000_HU"]["input_registers"]
    assert regs[1021]["name"] == "power_to_user_high"
    assert regs[1022]["name"] == "power_to_user_low"
    assert regs[1029]["name"] == "power_to_grid_high"
    assert regs[1030]["name"] == "power_to_grid_low"
    assert regs[1037]["name"] == "power_to_load_high"
    assert regs[1038]["name"] == "power_to_load_low"


def test_near_full_capture_local_load_legs_sum_to_total():
    # 2026-09-05 SPH-10000-US UL2.21 raw scan: 1032=1160, 1034=450, 1038=1610.
    # All are 32-bit low words with a zero high word and x0.1 W scale.
    l1 = 1160 * 0.1
    l2 = 450 * 0.1
    total = 1610 * 0.1
    assert l1 == pytest.approx(116.0)
    assert l2 == pytest.approx(45.0)
    assert l1 + l2 == pytest.approx(total)


def test_growatt_data_declares_every_ct_sensor_field():
    tree = ast.parse(SOURCE)
    growatt_data = next(
        n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "GrowattData"
    )
    fields = {
        n.target.id
        for n in growatt_data.body
        if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name)
    }
    assert set(CT_REGISTERS) <= fields
