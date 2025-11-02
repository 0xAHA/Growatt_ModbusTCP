#!/usr/bin/env python3
"""
Standalone script to read Growatt firmware info.
Compatible with pymodbus 3.x
"""

# Try different import paths for different pymodbus versions
try:
    from pymodbus.client import ModbusTcpClient
except ImportError:
    try:
        from pymodbus.client.tcp import ModbusTcpClient
    except ImportError:
        from pymodbus.client.sync import ModbusTcpClient

HOST = "192.168.1.60"
PORT = 502
DEVICE_ID = 1

def registers_to_ascii(registers):
    """Convert list of 16-bit registers to ASCII string."""
    ascii_bytes = []
    for reg in registers:
        high_byte = (reg >> 8) & 0xFF
        low_byte = reg & 0xFF
        ascii_bytes.extend([high_byte, low_byte])
    
    return bytes(ascii_bytes).decode('ascii', errors='ignore').strip('\x00').strip()


def read_and_display(client, start, count, name):
    """Read registers and display as ASCII."""
    try:
        # Try new pymodbus 3.x style first
        if hasattr(client, 'read_holding_registers'):
            result = client.read_holding_registers(address=start, count=count, slave=DEVICE_ID)
        else:
            result = client.read_holding_registers(start, count, unit=DEVICE_ID)
        
        if hasattr(result, 'isError') and result.isError():
            print(f"❌ {name}: Read error")
            return None
        
        if not hasattr(result, 'registers'):
            print(f"❌ {name}: No registers in response")
            return None
            
        ascii_value = registers_to_ascii(result.registers)
        raw_values = " ".join([f"{r:04X}" for r in result.registers])
        
        print(f"✅ {name}:")
        print(f"   Registers {start}-{start+count-1}: {raw_values}")
        print(f"   ASCII: '{ascii_value}'")
        print()
        
        return ascii_value
        
    except Exception as e:
        print(f"❌ {name}: {e}")
        print()
        return None


def main():
    print("=" * 80)
    print("Growatt Inverter Firmware & Identification Reader")
    print(f"Host: {HOST}:{PORT}, Device ID: {DEVICE_ID}")
    print("=" * 80)
    print()
    
    # Connect
    client = ModbusTcpClient(HOST, port=PORT)
    
    if not client.connect():
        print(f"❌ Failed to connect to {HOST}:{PORT}")
        return
    
    print(f"✅ Connected to {HOST}:{PORT}")
    print()
    print("-" * 80)
    
    # Firmware Version (registers 9-11)
    print("\n📦 FIRMWARE VERSION (Main)")
    fw_version = read_and_display(client, 9, 3, "Firmware Version")
    
    # Firmware Version 2 (registers 12-14)
    print("\n📦 FIRMWARE VERSION 2 (Control)")
    fw_version2 = read_and_display(client, 12, 3, "Control Firmware Version")
    
    # Serial Number (registers 23-27)
    print("\n🔢 SERIAL NUMBER (Original)")
    serial = read_and_display(client, 23, 5, "Serial Number")
    
    # Manufacturer Info (registers 34-41)
    print("\n🏭 MANUFACTURER INFO")
    mfr_info = read_and_display(client, 34, 8, "Manufacturer Info")
    
    # FW Build Number (registers 82-87)
    print("\n🔨 FIRMWARE BUILD INFO")
    fw_build = read_and_display(client, 82, 6, "FW Build Number")
    
    # Inverter Type (registers 125-132)
    print("\n📋 INVERTER TYPE")
    inv_type = read_and_display(client, 125, 8, "Inverter Type")
    
    # New Serial Number (registers 215-223)
    print("\n🔢 SERIAL NUMBER (Extended)")
    new_serial = read_and_display(client, 215, 9, "New Serial Number")
    
    # Summary
    print("-" * 80)
    print("\n📊 SUMMARY")
    print("-" * 80)
    if fw_version:
        print(f"Firmware Version:        {fw_version}")
    if fw_version2:
        print(f"Control FW Version:      {fw_version2}")
    if serial:
        print(f"Serial Number:           {serial}")
    if new_serial:
        print(f"Extended Serial:         {new_serial}")
    if mfr_info:
        print(f"Manufacturer:            {mfr_info}")
    if inv_type:
        print(f"Inverter Type:           {inv_type}")
    if fw_build:
        print(f"Build Number:            {fw_build}")
    print()
    
    client.close()
    print("✅ Connection closed")


if __name__ == "__main__":
    main()