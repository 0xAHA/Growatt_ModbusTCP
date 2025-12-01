#!/usr/bin/env python3
"""Test script to verify register values"""

import sys
sys.path.insert(0, '.')

from emulator.models import InverterModel
from emulator.simulator import InverterSimulator

# Create SPH TL3 simulator
model = InverterModel('sph_tl3_3000_10000')
sim = InverterSimulator(model, 502)

# Set up some test conditions
sim.solar_irradiance = 800
sim.house_load = 2000
sim.battery_override = 5000  # Force 5000W charging

# Update to calculate values
sim.update()

print("=" * 80)
print("REGISTER VALUE TEST - SPH TL3")
print("=" * 80)
print()

# Test battery charge power
print("Battery Charge Power Test:")
print(f"  Internal battery_power value: {sim.values['battery_power']:.1f}W")
print()

# Read registers
reg_1011 = sim.get_register_value('input', 1011)
reg_1012 = sim.get_register_value('input', 1012)
reg_1013 = sim.get_register_value('input', 1013)
reg_1014 = sim.get_register_value('input', 1014)

print(f"  Register 1011 (charge_power_high): {reg_1011} (0x{reg_1011:04X})")
print(f"  Register 1012 (charge_power_low):  {reg_1012} (0x{reg_1012:04X})")
print(f"  Register 1013 (battery_voltage):   {reg_1013} (0x{reg_1013:04X}) -> {reg_1013 * 0.1:.1f}V")
print(f"  Register 1014 (battery_soc):       {reg_1014} -> {reg_1014}%")
print()

# Reconstruct 32-bit value
if reg_1011 is not None and reg_1012 is not None:
    combined = (reg_1011 << 16) | reg_1012
    power_w = combined * 0.1
    print(f"  Combined 32-bit value: {combined} (0x{combined:08X})")
    print(f"  Scaled power: {power_w:.1f}W")
print()

# Test AC phase registers
print("AC Phase R Test:")
print(f"  Internal voltage: {sim.values['voltages']['ac_r']:.1f}V")
print(f"  Internal current: {sim.values['currents']['ac_r']:.1f}A")
print(f"  Internal power: {sim.values['ac_power'] / 3:.1f}W")
print()

reg_38 = sim.get_register_value('input', 38)
reg_39 = sim.get_register_value('input', 39)
reg_40 = sim.get_register_value('input', 40)
reg_41 = sim.get_register_value('input', 41)

print(f"  Register 38 (ac_voltage_r):     {reg_38} (0x{reg_38:04X}) -> {reg_38 * 0.1:.1f}V")
print(f"  Register 39 (ac_current_r):     {reg_39} (0x{reg_39:04X}) -> {reg_39 * 0.1:.1f}A")
print(f"  Register 40 (ac_power_r_high):  {reg_40} (0x{reg_40:04X})")
print(f"  Register 41 (ac_power_r_low):   {reg_41} (0x{reg_41:04X})")
print()

if reg_40 is not None and reg_41 is not None:
    combined = (reg_40 << 16) | reg_41
    power_w = combined * 0.1
    print(f"  Combined 32-bit value: {combined} (0x{combined:08X})")
    print(f"  Scaled power: {power_w:.1f}W")
print()

# Check register definitions
print("Register Definitions from Model:")
input_regs = model.get_input_registers()
print(f"  Register 1011: {input_regs.get(1011)}")
print(f"  Register 1012: {input_regs.get(1012)}")
print(f"  Register 1013: {input_regs.get(1013)}")
print()
print(f"  Register 38: {input_regs.get(38)}")
print(f"  Register 39: {input_regs.get(39)}")
print(f"  Register 40: {input_regs.get(40)}")
print(f"  Register 41: {input_regs.get(41)}")
