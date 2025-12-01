#!/usr/bin/env python3
"""
Test DTC code reading from MOD emulator
"""

import sys
sys.path.insert(0, '.')

from emulator.models import InverterModel
from emulator.simulator import InverterSimulator

print("Testing MOD Emulator DTC Code\n" + "=" * 60)

# Create MOD model
model_key = 'mod_6000_15000tl3_xh'
print(f"Loading model: {model_key}")

model = InverterModel(model_key)
print(f"✓ Model loaded: {model.name}")

# Create simulator
sim = InverterSimulator(model, port=5020)
sim.update()
print(f"✓ Simulator created")

# Check holding register 30000 (DTC code)
print(f"\nTesting DTC Code Register (holding 30000):")

# Get register definition
holding_regs = model.get_holding_registers()
if 30000 in holding_regs:
    reg_def = holding_regs[30000]
    print(f"  Register definition:")
    print(f"    name: {reg_def['name']}")
    print(f"    default: {reg_def.get('default', 'NOT SET')}")
    print(f"    desc: {reg_def.get('desc', '')}")

    # Read value from simulator
    value = sim.get_register_value('holding', 30000)
    print(f"\n  Simulated value: {value}")

    if value == 5400:
        print(f"  ✓ CORRECT! DTC code 5400 for MOD series")
    else:
        print(f"  ✗ WRONG! Expected 5400, got {value}")
else:
    print(f"  ✗ Register 30000 not found in holding registers!")

# Also check protocol version (30099)
print(f"\nTesting Protocol Version Register (holding 30099):")
if 30099 in holding_regs:
    reg_def = holding_regs[30099]
    value = sim.get_register_value('holding', 30099)
    print(f"  Value: {value}")
    print(f"  Expected: 201 (V2.01)")
    if value == 201:
        print(f"  ✓ CORRECT!")
    else:
        print(f"  ✗ WRONG!")

print("\n" + "=" * 60)
