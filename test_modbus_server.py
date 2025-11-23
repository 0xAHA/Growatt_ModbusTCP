#!/usr/bin/env python3
"""Test Modbus server to verify it's serving the correct values"""

import sys
import time
import logging
sys.path.insert(0, '.')

# Enable logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

from pymodbus.client import ModbusTcpClient
from emulator.models import InverterModel
from emulator.simulator import InverterSimulator
from emulator.modbus_server import ModbusEmulatorServer

# Create SPH TL3 emulator
model = InverterModel('sph_tl3_3000_10000')
sim = InverterSimulator(model, 5020)
sim.solar_irradiance = 800
sim.house_load = 2000
sim.battery_override = 5000  # Force 5000W charging
sim.update()

# Start Modbus server
server = ModbusEmulatorServer(sim, port=5020, slave_id=1)
server.start()
time.sleep(2)  # Give server time to start

print("=" * 80)
print("MODBUS SERVER TEST - SPH TL3")
print("=" * 80)
print()

# Connect as a Modbus client
client = ModbusTcpClient('localhost', port=5020)
if not client.connect():
    print("Failed to connect to Modbus server")
    server.stop()
    sys.exit(1)

print("Connected to Modbus server on port 5020")
print()

try:
    # Test battery charge power registers (1011-1012)
    print("Reading battery charge power (input registers 1011-1012):")
    result = client.read_input_registers(1011, count=2, device_id=1)
    if not result.isError():
        print(f"  Register 1011 (charge_power_high): {result.registers[0]} (0x{result.registers[0]:04X})")
        print(f"  Register 1012 (charge_power_low):  {result.registers[1]} (0x{result.registers[1]:04X})")
        combined = (result.registers[0] << 16) | result.registers[1]
        power_w = combined * 0.1
        print(f"  Combined: {combined} (0x{combined:08X}) -> {power_w:.1f}W")
    else:
        print(f"  Error: {result}")
    print()

    # Test battery voltage and SOC (1013-1014)
    print("Reading battery voltage/SOC (input registers 1013-1014):")
    result = client.read_input_registers(1013, count=2, device_id=1)
    if not result.isError():
        print(f"  Register 1013 (battery_voltage): {result.registers[0]} (0x{result.registers[0]:04X}) -> {result.registers[0] * 0.1:.1f}V")
        print(f"  Register 1014 (battery_soc):     {result.registers[1]} -> {result.registers[1]}%")
    else:
        print(f"  Error: {result}")
    print()

    # Test AC phase R registers (38-41)
    print("Reading AC Phase R (input registers 38-41):")
    result = client.read_input_registers(38, count=4, device_id=1)
    if not result.isError():
        print(f"  Register 38 (ac_voltage_r):    {result.registers[0]} (0x{result.registers[0]:04X}) -> {result.registers[0] * 0.1:.1f}V")
        print(f"  Register 39 (ac_current_r):    {result.registers[1]} (0x{result.registers[1]:04X}) -> {result.registers[1] * 0.1:.1f}A")
        print(f"  Register 40 (ac_power_r_high): {result.registers[2]} (0x{result.registers[2]:04X})")
        print(f"  Register 41 (ac_power_r_low):  {result.registers[3]} (0x{result.registers[3]:04X})")
        combined = (result.registers[2] << 16) | result.registers[3]
        power_w = combined * 0.1
        print(f"  Combined power: {combined} (0x{combined:08X}) -> {power_w:.1f}W")
    else:
        print(f"  Error: {result}")
    print()

    # Test with offset addressing (like HA might be doing)
    print("Testing if HA is using different addressing:")
    print("  Trying to read register 1010-1011 instead of 1011-1012:")
    result = client.read_input_registers(1010, count=2, device_id=1)
    if not result.isError():
        print(f"    Register 1010: {result.registers[0]} (0x{result.registers[0]:04X})")
        print(f"    Register 1011: {result.registers[1]} (0x{result.registers[1]:04X})")
        combined = (result.registers[0] << 16) | result.registers[1]
        print(f"    Combined: {combined} (0x{combined:08X})")
    print()

    print("  Trying to read register 1012-1013 instead of 1011-1012:")
    result = client.read_input_registers(1012, count=2, device_id=1)
    if not result.isError():
        print(f"    Register 1012: {result.registers[0]} (0x{result.registers[0]:04X})")
        print(f"    Register 1013: {result.registers[1]} (0x{result.registers[1]:04X})")
        combined = (result.registers[0] << 16) | result.registers[1]
        print(f"    Combined: {combined} (0x{combined:08X})")
    print()

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

finally:
    client.close()
    server.stop()
    print("Test complete")
