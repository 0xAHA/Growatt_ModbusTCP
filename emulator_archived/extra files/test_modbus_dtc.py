#!/usr/bin/env python3
"""
Test Modbus DTC code reading from emulator

This script simulates what Home Assistant does to read the DTC code.
Use this to verify the emulator is serving the DTC correctly.
"""

import sys
from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException

def test_dtc_read(host='localhost', port=502, device_id=1):
    """
    Test reading DTC code from holding register 30000.

    Args:
        host: Emulator host
        port: Modbus TCP port
        device_id: Modbus device ID (usually 1)
    """
    print(f"\n{'=' * 70}")
    print(f"Testing Modbus DTC Read")
    print(f"{'=' * 70}")
    print(f"Target: {host}:{port}")
    print(f"Device ID: {device_id}")
    print()

    # Create client
    print(f"Connecting to emulator...")
    client = ModbusTcpClient(host=host, port=port, timeout=5)

    if not client.connect():
        print(f"✗ Failed to connect to {host}:{port}")
        print(f"\nMake sure the emulator is running:")
        print(f"  python3 growatt_emulator_web.py --port {port} --webport 8080")
        return False

    print(f"✓ Connected successfully")
    print()

    try:
        # Test 1: Read holding register 30000 (DTC code)
        print(f"Test 1: Reading DTC Code (holding register 30000)...")
        result = client.read_holding_registers(30000, 1, slave=device_id)

        if result.isError():
            print(f"✗ Error reading register 30000: {result}")
            return False

        dtc_code = result.registers[0]
        print(f"  Value: {dtc_code}")

        # Check if it's a valid DTC code
        dtc_map = {
            3502: 'SPH 3000-6000TL BL',
            3601: 'SPH 4000-10000TL3 BH-UP',
            5100: 'MIN 2500-6000TL-XH',
            5200: 'MIC/MIN 2500-6000TL-X',
            5201: 'MIN 7000-10000TL-X',
            5400: 'MOD-XH/MID-XH',
        }

        if dtc_code in dtc_map:
            print(f"  ✓ Valid DTC code: {dtc_map[dtc_code]}")
        elif dtc_code == 0:
            print(f"  ✗ DTC code is 0 - emulator may not be configured correctly")
        else:
            print(f"  ? Unknown DTC code: {dtc_code}")

        print()

        # Test 2: Read protocol version (holding register 30099)
        print(f"Test 2: Reading Protocol Version (holding register 30099)...")
        result = client.read_holding_registers(30099, 1, slave=device_id)

        if result.isError():
            print(f"✗ Error reading register 30099: {result}")
        else:
            protocol_version = result.registers[0]
            print(f"  Value: {protocol_version}")
            if protocol_version == 201:
                print(f"  ✓ V2.01 VPP Protocol")
            else:
                print(f"  ? Protocol version: {protocol_version}")

        print()

        # Test 3: Read some input registers to verify basic functionality
        print(f"Test 3: Reading Status Register (input register 0)...")
        result = client.read_input_registers(0, 1, slave=device_id)

        if result.isError():
            print(f"✗ Error reading register 0: {result}")
        else:
            status = result.registers[0]
            status_map = {0: 'Waiting', 1: 'Normal', 3: 'Fault'}
            print(f"  Value: {status} ({status_map.get(status, 'Unknown')})")
            print(f"  ✓ Input registers working")

        print()
        print(f"{'=' * 70}")
        print(f"Summary:")
        print(f"  DTC Code: {dtc_code}")
        print(f"  Expected by HA: holding register 30000")
        print(f"  Modbus function: read_holding_registers (0x03)")

        if dtc_code > 0 and dtc_code in dtc_map:
            print(f"\n✓ Emulator is correctly serving DTC code {dtc_code}")
            print(f"\nIf HA still can't detect it, check:")
            print(f"  1. HA is connecting to correct host:port")
            print(f"  2. Device ID in HA matches ({device_id})")
            print(f"  3. Check HA logs for Modbus errors")
            print(f"  4. Verify HA integration is reading holding registers")
        else:
            print(f"\n✗ DTC code issue detected")
            print(f"  Check emulator model and profile")

        print(f"{'=' * 70}\n")

        return True

    except ModbusException as e:
        print(f"✗ Modbus exception: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        client.close()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Test Modbus DTC code reading')
    parser.add_argument('--host', default='localhost', help='Emulator host (default: localhost)')
    parser.add_argument('--port', type=int, default=502, help='Modbus TCP port (default: 502)')
    parser.add_argument('--device-id', type=int, default=1, help='Modbus device ID (default: 1)')

    args = parser.parse_args()

    test_dtc_read(args.host, args.port, args.device_id)
