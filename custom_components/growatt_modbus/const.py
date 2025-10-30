#!/usr/bin/env python3
"""
Growatt Inverter Register Definitions and Integration Constants
Modbus register mappings for Growatt inverters
Based on official Growatt Protocol V1.39 (2024.04.16)

REQUIREMENTS:
- Python 3.7+

Usage:
    from const import REGISTER_MAPS, STATUS_CODES
    registers = REGISTER_MAPS['MIN_7000_10000TL_X']
"""

# Import register maps from profile package
# If running as standalone module, profiles must be importable
try:
    from .profiles import (
        REGISTER_MAPS,
        get_profile,
        get_available_profiles,
        get_profile_keys,
        list_profiles,
    )
except ImportError:
    # Fallback for standalone testing
    from profiles import (
        REGISTER_MAPS,
        get_profile,
        get_available_profiles,
        get_profile_keys,
        list_profiles,
    )

# ============================================================================
# HOME ASSISTANT INTEGRATION CONSTANTS
# ============================================================================

DOMAIN = "growatt_modbus"

# Configuration Constants
CONF_SLAVE_ID = "slave_id"
CONF_CONNECTION_TYPE = "connection_type"
CONF_DEVICE_PATH = "device_path"
CONF_BAUDRATE = "baudrate"
CONF_REGISTER_MAP = "register_map"
CONF_INVERTER_SERIES = "inverter_series"
CONF_INVERT_GRID_POWER = "invert_grid_power"  # For reversed CT clamps

# Default Values
DEFAULT_PORT = 502
DEFAULT_SLAVE_ID = 1
DEFAULT_BAUDRATE = 9600

# ============================================================================
# SENSOR TYPE CLASSIFICATIONS FOR OFFLINE BEHAVIOR
# ============================================================================

SENSOR_TYPES = {
    # Power sensors - should go to 0 when offline
    'power': [
        'pv1_power', 'pv2_power', 'pv3_power', 'pv_total_power',
        'ac_power', 'grid_power', 'grid_export_power', 'grid_import_power',
        'power_to_grid', 'power_to_load', 'power_to_user',
        'self_consumption', 'house_consumption',
        # Battery power sensors
        'battery_power', 'battery_charge_power', 'battery_discharge_power',
        # Three-phase power sensors
        'ac_power_r', 'ac_power_s', 'ac_power_t',
    ],
    
    # Daily total sensors - retain until midnight, then reset
    'daily_total': [
        'energy_today', 'energy_to_grid_today', 'grid_import_energy_today',
        'load_energy_today', 'energy_to_user_today', 'grid_energy_today',
        # Battery daily sensors
        'battery_charge_today', 'battery_discharge_today',
    ],
    
    # Lifetime total sensors - always retain last value
    'lifetime_total': [
        'energy_total', 'energy_to_grid_total', 'grid_import_energy_total',
        'load_energy_total', 'energy_to_user_total', 'grid_energy_total',
        # Battery lifetime sensors
        'battery_charge_total', 'battery_discharge_total',
    ],
    
    # Diagnostic sensors - go unavailable when offline
    'diagnostic': [
        'pv1_voltage', 'pv1_current', 'pv2_voltage', 'pv2_current',
        'pv3_voltage', 'pv3_current', 'ac_voltage', 'ac_current',
        'ac_frequency', 'inverter_temp', 'ipm_temp', 'boost_temp',
        'self_consumption_percentage',
        # Battery diagnostic sensors
        'battery_voltage', 'battery_current', 'battery_soc', 'battery_temp',
        # Three-phase diagnostic sensors
        'ac_voltage_r', 'ac_voltage_s', 'ac_voltage_t',
        'ac_current_r', 'ac_current_s', 'ac_current_t',
    ],
    
    # Status sensors - show "offline" when not responding
    'status': ['status', 'derating_mode', 'fault_code', 'warning_code', 
               'priority_mode', 'battery_derating_mode'],
}


# WRITABLE REGISTERS - Export Control
WRITABLE_REGISTERS = {
    'export_limit_mode': {
        'register': 122,
        'scale': 1,
        'valid_range': (0, 3),
        'options': {
            0: 'Disabled',
            1: 'RS485 External Meter',
            2: 'RS232 External Meter',
            3: 'CT Clamp Limit'
        }
    },
    'export_limit_power': {
        'register': 123,
        'scale': 0.1,  # Store as 0-1000, display as 0-100.0%
        'valid_range': (0, 1000),  # 0 = 0%, 1000 = 100%
        'unit': '%'
    }
}

# Sensor offline behavior mapping
SENSOR_OFFLINE_BEHAVIOR = {
    'power': 0,              # Power sensors go to 0W
    'daily_total': 'retain', # Daily totals retain until midnight
    'lifetime_total': 'retain', # Lifetime totals always retain
    'diagnostic': None,      # Diagnostic sensors go unavailable
    'status': 'offline',     # Status shows "offline"
}


def get_sensor_type(sensor_key: str) -> str:
    """Get the sensor type for a given sensor key."""
    for sensor_type, sensors in SENSOR_TYPES.items():
        if sensor_key in sensors:
            return sensor_type
    return 'diagnostic'  # Default to diagnostic if not found


# ============================================================================
# STATUS CODE MAPPINGS
# ============================================================================

STATUS_CODES = {
    0: {'name': 'Waiting', 'desc': 'Waiting for sufficient PV power or grid conditions'},
    1: {'name': 'Normal', 'desc': 'Operating normally'},
    3: {'name': 'Fault', 'desc': 'Fault condition detected'},
    5: {'name': 'Standby', 'desc': 'Inverter in standby mode'},
}


def get_status_name(status_code: int) -> dict:
    """Get human-readable status name and description."""
    return STATUS_CODES.get(
        status_code, 
        {'name': f'Unknown ({status_code})', 'desc': 'Unknown status code'}
    )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def combine_registers(high: int, low: int) -> int:
    """Combine two 16-bit registers into 32-bit value.
    
    Args:
        high: High word (upper 16 bits)
        low: Low word (lower 16 bits)
        
    Returns:
        Combined 32-bit unsigned integer
    """
    return (high << 16) | low


def scale_value(raw_value: float, scale: float) -> float:
    """Apply scaling factor to raw register value.
    
    Args:
        raw_value: Raw value from register
        scale: Scaling factor (e.g., 0.1 for 1 decimal place)
        
    Returns:
        Scaled value
    """
    return raw_value * scale


def get_register_info(register_map_name: str, register_type: str, address: int) -> dict | None:
    """Get information about a specific register.
    
    Args:
        register_map_name: Profile key (e.g., 'MIN_7000_10000TL_X')
        register_type: 'input' or 'holding'
        address: Register address
        
    Returns:
        Register info dict or None if not found
    """
    if register_map_name not in REGISTER_MAPS:
        return None
    
    register_map = REGISTER_MAPS[register_map_name]
    registers = register_map.get(f'{register_type}_registers', {})
    
    return registers.get(address, None)


# ============================================================================
# TESTING / STANDALONE EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("Growatt Register Maps (Protocol V1.39)")
    print("=" * 60)
    print()
    list_profiles()
    
    print("\n" + "=" * 60)
    print("\nExample: Reading MIN-7000-10000TL-X PV1 Power")
    print("-" * 60)
    
    # Example: Combining 32-bit power register
    profile = get_profile('MIN_7000_10000TL_X')
    if profile:
        pv1_high_addr = 3005
        pv1_low_addr = 3006
        
        pv1_high_info = profile['input_registers'].get(pv1_high_addr)
        pv1_low_info = profile['input_registers'].get(pv1_low_addr)
        
        print(f"Register {pv1_high_addr}: {pv1_high_info['name']}")
        print(f"Register {pv1_low_addr}: {pv1_low_info['name']}")
        print(f"Pair: {pv1_low_info.get('pair')} (should be {pv1_high_addr})")
        print(f"Combined scale: {pv1_low_info.get('combined_scale')}")
        print(f"Combined unit: {pv1_low_info.get('combined_unit')}")
        
        # Example values
        example_high = 0
        example_low = 12450
        combined = combine_registers(example_high, example_low)
        scaled = scale_value(combined, 0.1)
        
        print(f"\nExample reading:")
        print(f"  HIGH word: {example_high}")
        print(f"  LOW word: {example_low}")
        print(f"  Combined: {combined}")
        print(f"  Scaled: {scaled}W")
