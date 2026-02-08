#!/usr/bin/env python3
"""
Validation script to ensure sensors are properly defined across all required files.

Usage:
    python3 validate_sensors.py
    python3 validate_sensors.py --sensor battery_power
    python3 validate_sensors.py --profile sph
"""

import sys
import re
from pathlib import Path
from typing import Dict, Set, List, Tuple

# Add custom_components to path
sys.path.insert(0, str(Path(__file__).parent / "custom_components" / "growatt_modbus"))

def extract_sensors_from_profile_files() -> Dict[str, Set[str]]:
    """Extract all sensor names from profile files."""
    profiles_dir = Path(__file__).parent / "custom_components" / "growatt_modbus" / "profiles"
    profile_sensors = {}

    for profile_file in profiles_dir.glob("*.py"):
        if profile_file.name == "__init__.py":
            continue

        content = profile_file.read_text()

        # Find register definitions: number: {'name': 'sensor_name', ...}
        # Pattern: whitespace + number + colon + dict with 'name'
        pattern = r"^\s+\d+:\s*\{[^}]*'name':\s*'([^']+)'[^}]*\}"
        matches = re.findall(pattern, content, re.MULTILINE)

        # Exclude _high for 32-bit registers (we only check the _low)
        actual_sensors = set()
        for name in matches:
            # Skip _high registers (they pair with _low)
            if name.endswith('_high'):
                continue
            # Keep everything else including _low
            actual_sensors.add(name)

        profile_sensors[profile_file.stem] = actual_sensors

    return profile_sensors

def extract_sensors_from_sensor_definitions() -> Set[str]:
    """Extract all sensor keys from sensor.py SENSOR_DEFINITIONS."""
    sensor_file = Path(__file__).parent / "custom_components" / "growatt_modbus" / "sensor.py"
    content = sensor_file.read_text()

    # Find SENSOR_DEFINITIONS block
    match = re.search(r'SENSOR_DEFINITIONS\s*=\s*\{(.*?)\n\}', content, re.DOTALL)
    if not match:
        return set()

    definitions_block = match.group(1)

    # Extract all keys (sensor names in quotes)
    sensor_keys = set(re.findall(r'"([^"]+)":\s*\{', definitions_block))

    return sensor_keys

def extract_sensors_from_device_map() -> Set[str]:
    """Extract all sensor keys from const.py SENSOR_DEVICE_MAP."""
    const_file = Path(__file__).parent / "custom_components" / "growatt_modbus" / "const.py"
    content = const_file.read_text()

    # Find SENSOR_DEVICE_MAP block
    match = re.search(r'SENSOR_DEVICE_MAP\s*=\s*\{(.*?)\n\}', content, re.DOTALL)
    if not match:
        return set()

    device_map_block = match.group(1)

    # Extract all sensor names in quotes or single quotes
    sensor_keys = set(re.findall(r'''['"]([^'"]+)['"]''', device_map_block))

    # Remove device type keys
    device_types = {'solar', 'grid', 'load', 'battery', 'inverter'}
    sensor_keys = {s for s in sensor_keys if s not in device_types}

    return sensor_keys

def extract_sensor_groups() -> Dict[str, Set[str]]:
    """Extract sensor group sets from device_profiles.py."""
    device_profiles_file = Path(__file__).parent / "custom_components" / "growatt_modbus" / "device_profiles.py"
    content = device_profiles_file.read_text()

    sensor_groups = {}

    # Find all sensor group definitions (e.g., BATTERY_SENSORS: Set[str] = { ... })
    # Pattern: GROUP_NAME: Set[str] = { ... }
    pattern = r'([A-Z_]+_SENSORS):\s*Set\[str\]\s*=\s*\{([^}]+)\}'
    matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)

    for group_name, sensors_block in matches:
        # Extract quoted sensor names
        sensors = set(re.findall(r'''['"]([^'"]+)['"]''', sensors_block))
        sensor_groups[group_name] = sensors

    return sensor_groups

def validate_sensor(sensor_name: str) -> List[str]:
    """Validate a specific sensor across all files."""
    issues = []

    # Check profiles
    profile_sensors = extract_sensors_from_profile_files()
    found_in_profiles = [p for p, sensors in profile_sensors.items() if sensor_name in sensors or sensor_name + '_low' in sensors]

    if not found_in_profiles:
        issues.append(f"❌ NOT found in any profile register definitions")
    else:
        issues.append(f"✓ Found in profile register definitions: {', '.join(found_in_profiles)}")

    # Check sensor.py
    sensor_definitions = extract_sensors_from_sensor_definitions()
    if sensor_name not in sensor_definitions:
        # Check if it's a _low register (those shouldn't be in sensor definitions)
        if not sensor_name.endswith('_low'):
            issues.append(f"❌ NOT found in sensor.py SENSOR_DEFINITIONS")
    else:
        issues.append(f"✓ Found in sensor.py SENSOR_DEFINITIONS")

    # Check const.py device map
    device_map_sensors = extract_sensors_from_device_map()
    if sensor_name not in device_map_sensors:
        if not sensor_name.endswith('_low'):
            issues.append(f"❌ NOT found in const.py SENSOR_DEVICE_MAP")
    else:
        issues.append(f"✓ Found in const.py SENSOR_DEVICE_MAP")

    # Check sensor groups in device_profiles.py
    sensor_groups = extract_sensor_groups()
    found_in_groups = [group for group, sensors in sensor_groups.items() if sensor_name in sensors]

    if found_in_profiles and not found_in_groups:
        issues.append(f"❌ Found in register definitions but NOT in any sensor group in device_profiles.py")
    elif found_in_groups:
        issues.append(f"✓ Found in sensor groups: {', '.join(found_in_groups)}")

    return issues

def validate_all() -> Tuple[List[str], List[str]]:
    """Validate all sensors across all files."""
    profile_sensors = extract_sensors_from_profile_files()
    sensor_definitions = extract_sensors_from_sensor_definitions()
    device_map_sensors = extract_sensors_from_device_map()
    sensor_groups = extract_sensor_groups()

    # Get all sensor names from groups (flattened)
    all_group_sensors = set()
    for sensors in sensor_groups.values():
        all_group_sensors.update(sensors)

    # Get all unique sensor names (excluding _low suffix for combined registers)
    all_sensors = set()
    for sensors in profile_sensors.values():
        # Remove _low suffix for validation
        all_sensors.update(s.replace('_low', '') if s.endswith('_low') else s for s in sensors)

    issues = []
    warnings = []

    # Check each sensor
    for sensor in sorted(all_sensors):
        # Skip internal/technical registers
        if sensor.endswith('_high') or sensor.endswith('_vpp') or sensor.endswith('_legacy'):
            continue

        problems = []

        # Check if in sensor.py
        if sensor not in sensor_definitions:
            problems.append("missing from sensor.py")

        # Check if in const.py device map
        if sensor not in device_map_sensors:
            problems.append("missing from const.py device map")

        # Check if in any sensor group
        if sensor not in all_group_sensors:
            problems.append("missing from device_profiles.py sensor groups")

        if problems:
            issues.append(f"❌ {sensor}: {', '.join(problems)}")

    # Check for sensors in definitions but not in profiles
    for sensor in sorted(sensor_definitions):
        found_in_profiles = any(sensor in sensors or sensor + '_low' in sensors
                               for sensors in profile_sensors.values())
        if not found_in_profiles:
            warnings.append(f"⚠️  {sensor}: defined in sensor.py but not in any profile")

    return issues, warnings

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Validate sensor definitions across all files")
    parser.add_argument("--sensor", help="Validate a specific sensor")
    parser.add_argument("--profile", help="Check a specific profile file")

    args = parser.parse_args()

    print("=" * 80)
    print("SENSOR VALIDATION")
    print("=" * 80)

    if args.sensor:
        print(f"\nValidating sensor: {args.sensor}")
        print("-" * 80)
        issues = validate_sensor(args.sensor)
        for issue in issues:
            print(issue)

    elif args.profile:
        print(f"\nValidating profile: {args.profile}")
        print("-" * 80)
        profile_sensors = extract_sensors_from_profile_files()
        if args.profile in profile_sensors:
            for sensor in sorted(profile_sensors[args.profile]):
                print(f"\nSensor: {sensor}")
                issues = validate_sensor(sensor)
                for issue in issues:
                    print(f"  {issue}")
        else:
            print(f"❌ Profile '{args.profile}' not found")

    else:
        print("\nValidating all sensors...")
        print("-" * 80)
        issues, warnings = validate_all()

        if issues:
            print("\n🔴 ISSUES FOUND:")
            for issue in issues:
                print(issue)
        else:
            print("\n✅ No issues found!")

        if warnings:
            print("\n⚠️  WARNINGS:")
            for warning in warnings:
                print(warning)

        print("\n" + "=" * 80)
        print(f"Summary: {len(issues)} issues, {len(warnings)} warnings")

        if issues:
            sys.exit(1)

    print("=" * 80)

if __name__ == "__main__":
    main()
