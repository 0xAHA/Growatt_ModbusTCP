#!/usr/bin/env python3
"""
Growatt Register Scanner & Detective
Scans all available registers and outputs to CSV files

Usage: python growatt_scanner.py 192.168.1.100 502 1
"""

import sys
import csv
from datetime import datetime

try:
    from pymodbus.client import ModbusTcpClient
except ImportError:
    try:
        from pymodbus.client.sync import ModbusTcpClient
    except ImportError:
        print("Error: pymodbus not installed")
        print("Install with: pip install pymodbus")
        sys.exit(1)

def combine_32bit(high_word, low_word):
    """Combine two 16-bit words into a 32-bit value"""
    return (high_word << 16) | low_word

# Known/Documented Register Mappings (from JavaScript client)
KNOWN_REGISTERS = [
    # Format: (register, scaling, unit, description, notes)
    (0, 1, "", "Status", "0=Waiting, 1=Normal, 3=Fault"),
    (1, 0.1, "W", "Input Power HIGH", "32-bit with reg 2"),
    (2, 0.1, "W", "Input Power LOW", "Part of 32-bit value"),
    (3, 0.1, "V", "PV1 Voltage", "DC input from string 1"),
    (4, 0.1, "A", "PV1 Current", "DC current from string 1"),
    (5, 0.1, "W", "PV1 Power HIGH", "32-bit with reg 6"),
    (6, 0.1, "W", "PV1 Power LOW", "Part of 32-bit value"),
    (7, 0.1, "V", "PV2 Voltage", "DC input from string 2"),
    (8, 0.1, "A", "PV2 Current", "DC current from string 2"),
    (9, 0.1, "W", "PV2 Power HIGH", "32-bit with reg 10"),
    (10, 0.1, "W", "PV2 Power LOW", "Part of 32-bit value"),
    (35, 0.1, "W", "Output Power HIGH", "32-bit with reg 36"),
    (36, 0.1, "W", "Output Power LOW", "Part of 32-bit value"),
    (37, 0.01, "Hz", "Grid Frequency", "Should be ~50Hz for AU"),
    (38, 0.1, "V", "Grid Voltage", "Should be ~240V for AU"),
    (39, 0.1, "A", "Grid Current", "AC output current"),
    (40, 0.1, "VA", "Grid Output Power HIGH", "32-bit with reg 41"),
    (41, 0.1, "VA", "Grid Output Power LOW", "Part of 32-bit value"),
    (53, 0.1, "kWh", "Today Energy HIGH", "32-bit with reg 54"),
    (54, 0.1, "kWh", "Today Energy LOW", "Part of 32-bit value"),
    (55, 0.1, "kWh", "Total Energy HIGH", "32-bit with reg 56"),
    (56, 0.1, "kWh", "Total Energy LOW", "Part of 32-bit value"),
    (93, 0.1, "°C", "Inverter Temperature", "Internal temperature"),
    (94, 0.1, "°C", "IPM Temperature", "Power module temperature"),
]

def guess_parameter_type(raw_value, scaled_values, reg_index, all_data):
    """Make intelligent guesses about what a register might represent"""
    guesses = []
    
    # Status indicators (typically 0-5)
    if 0 <= raw_value <= 5:
        guesses.append(("High", "Status Code", "0=Wait, 1=Normal, 3=Fault, etc"))
    
    # For each scaling factor, check against known patterns
    for scale_factor, scaled_value in scaled_values.items():
        
        # Grid/AC Voltage (typically 220-260V in AU)
        if 200 <= scaled_value <= 280 and scale_factor == 0.1:
            guesses.append(("High", f"Grid/AC Voltage", f"{scaled_value:.1f}V"))
        elif 90 <= scaled_value <= 150 and scale_factor == 0.1:
            guesses.append(("Medium", f"Grid/AC Voltage (US)", f"{scaled_value:.1f}V"))
        
        # PV/DC Voltage (typically 200-600V)
        if 150 <= scaled_value <= 650 and scale_factor == 0.1:
            guesses.append(("Medium", f"PV/DC Voltage", f"{scaled_value:.1f}V"))
        
        # Current (typically 0-50A)
        if 0 <= scaled_value <= 60 and scale_factor == 0.1 and raw_value > 0:
            guesses.append(("Medium", f"Current", f"{scaled_value:.1f}A"))
        
        # Frequency (should be around 50Hz AU or 60Hz US)
        if 45 <= scaled_value <= 65 and scale_factor == 0.01:
            guesses.append(("High", f"Grid Frequency", f"{scaled_value:.2f}Hz"))
        
        # Power readings (0-12000W for 10kW inverter)
        if 0 < scaled_value <= 15000 and scale_factor == 0.1:
            guesses.append(("Low", f"Power Output", f"{scaled_value:.0f}W"))
        
        # Temperature (typically 0-100°C)
        if 0 <= scaled_value <= 120 and scale_factor == 0.1 and raw_value > 0:
            guesses.append(("Medium", f"Temperature", f"{scaled_value:.1f}°C"))
        
        # Energy readings (kWh - could be large)
        if scaled_value > 10 and scale_factor == 0.1:
            guesses.append(("Low", f"Energy", f"{scaled_value:.1f}kWh"))
    
    # Check 32-bit combinations with next register ONLY if it looks like a HIGH/LOW pair
    # Don't automatically assume adjacent registers are paired
    if reg_index < len(all_data) - 1:
        next_value = all_data[reg_index + 1]

        # Only suggest 32-bit combination if current value is suspiciously small
        # (likely HIGH word of a 32-bit pair) or if both are non-zero
        # This prevents false pairings like SOC (8093=0) + SOH (8094=100)
        if raw_value > 0 or (raw_value == 0 and next_value == 0):
            combined = combine_32bit(raw_value, next_value)

            # Large power readings (32-bit) - only suggest if combined value makes sense
            if 0 < combined < 150000:
                combined_scaled = combined / 10.0
                if 0 < combined_scaled <= 15000:
                    guesses.append(("Low", f"Possible 32-bit Power (if paired with reg+1)", f"{combined_scaled:.0f}W"))

            # Energy totals (can be very large)
            if combined > 100 and combined < 10000000:
                energy_kwh = combined / 10.0
                if energy_kwh < 100000:
                    guesses.append(("Low", f"Possible 32-bit Energy (if paired with reg+1)", f"{energy_kwh:.1f}kWh"))
    
    # Raw value patterns
    if raw_value == 0:
        guesses.append(("Low", "Zero/Inactive/Unused", ""))
    elif raw_value == 65535:
        guesses.append(("Medium", "Max Value/Error/N/A", ""))
    
    return guesses

def read_known_registers(client, slave_id):
    """Read all the known/documented registers and return their current values"""
    
    print("\nReading known/documented registers...")
    
    known_data = []
    
    # Read the base range that contains all known registers (0-124)
    try:
        try:
            response = client.read_input_registers(address=0, count=125, device_id=slave_id)
        except TypeError:
            response = client.read_input_registers(0, 125, slave=slave_id)
        
        if hasattr(response, 'registers') and len(response.registers) >= 95:
            data = response.registers
            
            for reg_num, scaling, unit, description, notes in KNOWN_REGISTERS:
                if reg_num < len(data):
                    raw_value = data[reg_num]
                    
                    # Handle 32-bit values
                    if "HIGH" in description and reg_num + 1 < len(data):
                        combined = combine_32bit(raw_value, data[reg_num + 1])
                        scaled_value = combined * scaling
                        status = "OK-32bit"
                    else:
                        scaled_value = raw_value * scaling
                        status = "OK"
                    
                    known_data.append({
                        'Register': reg_num,
                        'Alt_Register': reg_num + 3000,  # Common offset
                        'Raw_Value': raw_value,
                        'Scaled_Value': f"{scaled_value:.2f}",
                        'Scaling': scaling,
                        'Unit': unit,
                        'Description': description,
                        'Notes': notes,
                        'Status': status
                    })
            
            print(f"Read {len(known_data)} known registers successfully")
        else:
            print("Could not read base register range")
            
    except Exception as e:
        print(f"Error reading known registers: {e}")
    
    return known_data

def scan_register_range(client, start_addr, count, slave_id):
    """Scan a range of registers and analyze them"""
    
    scan_data = []
    
    try:
        try:
            response = client.read_input_registers(address=start_addr, count=count, device_id=slave_id)
        except TypeError:
            response = client.read_input_registers(start_addr, count, slave=slave_id)
        
        if not hasattr(response, 'registers') or len(response.registers) == 0:
            return None
        
        data = response.registers
        
        for i, raw_value in enumerate(data):
            reg_addr = start_addr + i
            
            # Calculate common scaling factors
            scaled_values = {
                1: raw_value,
                0.1: raw_value / 10.0,
                0.01: raw_value / 100.0,
                0.001: raw_value / 1000.0
            }
            
            # Get guesses for this register
            guesses = guess_parameter_type(raw_value, scaled_values, i, data)
            
            # Get best guess
            if guesses:
                best_guess = sorted(guesses, key=lambda x: {"High": 3, "Medium": 2, "Low": 1}[x[0]], reverse=True)[0]
                confidence = best_guess[0]
                guess_type = best_guess[1]
                guess_value = best_guess[2]
            else:
                confidence = ""
                guess_type = ""
                guess_value = ""
            
            scan_data.append({
                'Register': reg_addr,
                'Raw_Value': raw_value,
                'Div_10': f"{scaled_values[0.1]:.1f}",
                'Div_100': f"{scaled_values[0.01]:.2f}",
                'Div_1000': f"{scaled_values[0.001]:.3f}",
                'Confidence': confidence,
                'Likely_Type': guess_type,
                'Calculated_Value': guess_value,
            })
        
        return scan_data
        
    except Exception as e:
        print(f"❌ Error reading range {start_addr}-{start_addr + count - 1}: {e}")
        return None

def save_to_csv(known_data, all_scan_data, host):
    """Save results to CSV files"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    host_safe = host.replace(".", "_")
    
    # Save known registers
    known_filename = f"growatt_known_registers_{host_safe}_{timestamp}.csv"
    with open(known_filename, 'w', newline='', encoding='utf-8-sig') as f:
        if known_data:
            writer = csv.DictWriter(f, fieldnames=known_data[0].keys())
            writer.writeheader()
            writer.writerows(known_data)
    
    print(f"Saved known registers to: {known_filename}")
    
    # Save full scan results
    scan_filename = f"growatt_full_scan_{host_safe}_{timestamp}.csv"
    with open(scan_filename, 'w', newline='', encoding='utf-8-sig') as f:
        if all_scan_data:
            writer = csv.DictWriter(f, fieldnames=all_scan_data[0].keys())
            writer.writeheader()
            writer.writerows(all_scan_data)
    
    print(f"Saved full scan to: {scan_filename}")
    
    # Save interesting registers only (high/medium confidence, non-zero)
    interesting_data = [
        row for row in all_scan_data 
        if row['Confidence'] in ['High', 'Medium'] and row['Raw_Value'] not in [0, 65535]
    ]
    
    if interesting_data:
        interesting_filename = f"growatt_interesting_{host_safe}_{timestamp}.csv"
        with open(interesting_filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=interesting_data[0].keys())
            writer.writeheader()
            writer.writerows(interesting_data)
        
        print(f"Saved interesting registers to: {interesting_filename}")
        print(f"   ({len(interesting_data)} registers with High/Medium confidence)")

def scan_all_ranges(host, port, slave_id):
    """Scan multiple common register ranges"""
    
    print(f"Starting comprehensive register scan on {host}:{port} slave {slave_id}")
    print("This will take a minute or two...\n")
    
    try:
        client = ModbusTcpClient(host=host, port=port)
    except TypeError:
        client = ModbusTcpClient(host, port)
    
    if not client.connect():
        print(f"Failed to connect to {host}:{port}")
        return
    
    print("Connected successfully!")
    
    # First, read known registers
    known_data = read_known_registers(client, slave_id)
    
    # Then scan all ranges
    all_scan_data = []
    
    ranges = [
        (0, 125, "Base Registers (0-124)"),
        (3000, 125, "Input Registers (3000-3124)"),
        (3500, 50, "Extended Registers (3500-3549)"),
        (4000, 50, "High Registers (4000-4049)"),
    ]
    
    for start_addr, count, range_name in ranges:
        print(f"\nScanning {range_name}...")
        result = scan_register_range(client, start_addr, count, slave_id)
        if result:
            all_scan_data.extend(result)
            print(f"   Read {len(result)} registers")
        
        import time
        time.sleep(0.5)
    
    client.close()
    
    # Save everything to CSV
    print(f"\n{'='*80}")
    print("SAVING RESULTS TO CSV FILES")
    print(f"{'='*80}\n")
    
    save_to_csv(known_data, all_scan_data, host)
    
    # Print summary to console
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"Known/Documented Registers: {len(known_data)}")
    print(f"Total Registers Scanned: {len(all_scan_data)}")
    
    high_conf = len([r for r in all_scan_data if r['Confidence'] == 'High'])
    med_conf = len([r for r in all_scan_data if r['Confidence'] == 'Medium'])
    
    print(f"High Confidence Matches: {high_conf}")
    print(f"Medium Confidence Matches: {med_conf}")
    
    print("\nNEXT STEPS:")
    print("1. Open the 'known_registers' CSV to see documented values")
    print("2. Open the 'interesting' CSV to see high-confidence discoveries")
    print("3. Open the 'full_scan' CSV to see everything")
    print("4. Validate the interesting registers and update your const.py")

def main():
    if len(sys.argv) != 4:
        print("Usage: python growatt_scanner.py <host> <port> <slave_id>")
        print("Example: python growatt_scanner.py 192.168.1.100 502 1")
        return
    
    host = sys.argv[1]
    port = int(sys.argv[2])
    slave_id = int(sys.argv[3])
    
    scan_all_ranges(host, port, slave_id)

if __name__ == "__main__":
    main()