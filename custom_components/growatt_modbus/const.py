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
CONF_DEVICE_STRUCTURE_VERSION = "device_structure_version"

# Default Values
DEFAULT_PORT = 502
DEFAULT_SLAVE_ID = 1
DEFAULT_BAUDRATE = 9600

# Device Structure Version
# Version 1: Single device (legacy)
# Version 2: Multi-device (inverter, solar, grid, load, battery)
#            Controls are within their respective devices (inverter or battery)
CURRENT_DEVICE_STRUCTURE_VERSION = 2

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


# WRITABLE REGISTERS - Control Entities
WRITABLE_REGISTERS = {
    # Grid-Tied Inverter Controls
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
    },
    'active_power_rate': {
        'register': 3,
        'scale': 1,  # Direct percentage: 0-100
        'valid_range': (0, 100),  # 0% to 100%
        'unit': '%',
        'desc': 'Maximum output power limitation'
    },

    # SPF Off-Grid Inverter Controls
    'output_config': {
        'register': 1,
        'scale': 1,
        'valid_range': (0, 3),
        'options': {
            0: 'SBU (Battery First)',
            1: 'SOL (Solar First)',
            2: 'UTI (Utility First)',
            3: 'SUB (Solar & Utility First)'
        }
    },
    'charge_config': {
        'register': 2,
        'scale': 1,
        'valid_range': (0, 2),
        'options': {
            0: 'CSO (Solar First)',
            1: 'SNU (Solar & Utility)',
            2: 'OSO (Solar Only)'
        }
    },
    'ac_input_mode': {
        'register': 8,
        'scale': 1,
        'valid_range': (0, 2),
        'options': {
            0: 'APL (Appliance)',
            1: 'UPS',
            2: 'GEN (Generator)'
        }
    },
    'battery_type': {
        'register': 39,
        'scale': 1,
        'valid_range': (0, 4),
        'options': {
            0: 'AGM',
            1: 'Flooded (FLD)',
            2: 'User Defined',
            3: 'Lithium',
            4: 'User Defined 2'
        }
    },
    'ac_charge_current': {
        'register': 38,
        'scale': 1,
        'valid_range': (0, 400),
        'unit': 'A',
        'desc': 'AC charging current limit'
    },
    'gen_charge_current': {
        'register': 83,
        'scale': 1,
        'valid_range': (0, 400),
        'unit': 'A',
        'desc': 'Generator charging current limit'
    },
    # Battery-type-dependent registers (special handling required)
    'bat_low_to_uti': {
        'register': 37,
        'scale': 0.1,
        'valid_range': (5, 640),  # Full range: Lithium 0.5-10.0%, Non-Lithium 20.0-64.0V
        'unit': 'V/%',  # Unit depends on battery_type
        'desc': 'Battery low voltage/SOC switch to utility',
        'battery_dependent': True
    },
    'ac_to_bat_volt': {
        'register': 95,
        'scale': 0.1,
        'valid_range': (5, 640),  # Full range: Lithium 0.5-10.0%, Non-Lithium 20.0-64.0V
        'unit': 'V/%',  # Unit depends on battery_type
        'desc': 'AC to battery voltage/SOC switch point',
        'battery_dependent': True
    },
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
# DEVICE STRUCTURE - Multi-Device Organization
# ============================================================================

# Device Types
DEVICE_TYPE_INVERTER = "inverter"
DEVICE_TYPE_SOLAR = "solar"
DEVICE_TYPE_GRID = "grid"
DEVICE_TYPE_LOAD = "load"
DEVICE_TYPE_BATTERY = "battery"

# Sensor to Device Mapping
# Each sensor is assigned to a logical device for better organization
SENSOR_DEVICE_MAP = {
    # Inverter device - system health and status
    DEVICE_TYPE_INVERTER: {
        'status', 'last_update', 'fault_code', 'warning_code', 'derating_mode',
        'inverter_temp', 'ipm_temp', 'boost_temp',
        'battery_derating_mode',  # Battery-related status on inverter
    },

    # Solar device - PV production and AC output
    DEVICE_TYPE_SOLAR: {
        # PV inputs
        'pv1_voltage', 'pv1_current', 'pv1_power',
        'pv2_voltage', 'pv2_current', 'pv2_power',
        'pv3_voltage', 'pv3_current', 'pv3_power',
        'pv_total_power',
        # AC output (single phase)
        'ac_voltage', 'ac_current', 'ac_power', 'ac_frequency',
        # AC output (three phase)
        'ac_voltage_r', 'ac_voltage_s', 'ac_voltage_t',
        'ac_voltage_rs', 'ac_voltage_st', 'ac_voltage_tr',
        'ac_current_r', 'ac_current_s', 'ac_current_t',
        'ac_power_r', 'ac_power_s', 'ac_power_t',
        'system_output_power',
        # Solar production energy
        'energy_today', 'energy_total',
        # Self-consumption percentage (related to solar utilization)
        'self_consumption_percentage',
    },

    # Grid device - grid connection and import/export
    DEVICE_TYPE_GRID: {
        'grid_power', 'grid_export_power', 'grid_import_power',
        'grid_energy_today', 'grid_energy_total',
        'grid_import_energy_today', 'grid_import_energy_total',
        'energy_to_grid_today', 'energy_to_grid_total',
        'power_to_grid',
    },

    # Load device - consumption
    DEVICE_TYPE_LOAD: {
        'house_consumption', 'power_to_load', 'power_to_user',
        'load_energy_today', 'load_energy_total',
        'energy_to_user_today', 'energy_to_user_total',
        'self_consumption',
    },

    # Battery device - storage
    DEVICE_TYPE_BATTERY: {
        'battery_voltage', 'battery_current', 'battery_soc',
        'battery_temp', 'battery_power',
        'battery_charge_power', 'battery_discharge_power',
        'battery_charge_today', 'battery_discharge_today',
        'battery_charge_total', 'battery_discharge_total',
        'priority_mode',  # Battery priority mode
    },
}


def get_device_type_for_sensor(sensor_key: str) -> str:
    """Get the device type that a sensor belongs to.

    Args:
        sensor_key: The sensor key (e.g., 'pv1_power', 'battery_soc')

    Returns:
        Device type string (e.g., DEVICE_TYPE_SOLAR, DEVICE_TYPE_BATTERY)
    """
    for device_type, sensors in SENSOR_DEVICE_MAP.items():
        if sensor_key in sensors:
            return device_type
    # Default to inverter for unknown sensors
    return DEVICE_TYPE_INVERTER


# ============================================================================
# CONTROL ENTITY DEVICE MAPPING
# ============================================================================

# Map control entity names to their parent device
# Controls (number/select entities) are created from holding registers with 'access': 'RW'
# They appear as CONFIG entities (hidden by default) under the appropriate device

def get_device_type_for_control(control_name: str) -> str:
    """Get the device type that a control entity belongs to.

    Args:
        control_name: The control register name (e.g., 'battery_charge_stop_soc', 'vpp_enable')

    Returns:
        Device type string (e.g., DEVICE_TYPE_BATTERY, DEVICE_TYPE_GRID)
    """
    # Battery controls → Battery device
    if any(keyword in control_name for keyword in [
        'battery', 'bms', 'soc', 'charge_power', 'discharge_power',
        'ac_charge_power_rate', 'eod_voltage',
        # SPF off-grid battery controls
        'charge_config', 'charge_current', 'bat_low', 'ac_to_bat'
    ]):
        return DEVICE_TYPE_BATTERY

    # Grid controls → Grid device
    if any(keyword in control_name for keyword in [
        'grid', 'ongrid', 'offgrid', 'vpp', 'export', 'import',
        'phase_mode', 'phase_sequence', 'antibackflow',
        # SPF off-grid AC input controls
        'ac_input_mode'
    ]):
        return DEVICE_TYPE_GRID

    # Load/demand controls → Load device
    if any(keyword in control_name for keyword in [
        'demand', 'load_pv'
    ]):
        return DEVICE_TYPE_LOAD

    # PV/solar controls → Solar device
    if any(keyword in control_name for keyword in [
        'pv_', 'optimizer', 'pid'
    ]):
        return DEVICE_TYPE_SOLAR

    # Everything else → Inverter device (default)
    # Includes: time programming, system settings, operation mode, output priority, etc.
    return DEVICE_TYPE_INVERTER


# ============================================================================
# ENTITY CATEGORIES
# ============================================================================

# Entity category assignments for better UI organization
# - None (default): Main sensors shown prominently
# - "diagnostic": Technical details shown in separate diagnostic tab
# - "config": Configuration entities (hidden by default)

ENTITY_CATEGORY_MAP = {
    # Diagnostic entities - voltages, currents, temperatures, technical details
    'diagnostic': {
        # PV diagnostic
        'pv1_voltage', 'pv1_current',
        'pv2_voltage', 'pv2_current',
        'pv3_voltage', 'pv3_current',
        # AC diagnostic
        'ac_voltage', 'ac_current', 'ac_frequency',
        'ac_voltage_r', 'ac_voltage_s', 'ac_voltage_t',
        'ac_voltage_rs', 'ac_voltage_st', 'ac_voltage_tr',
        'ac_current_r', 'ac_current_s', 'ac_current_t',
        # Battery diagnostic
        'battery_voltage', 'battery_current', 'battery_temp',
        # Temperatures
        'inverter_temp', 'ipm_temp', 'boost_temp',
        # Status codes
        'fault_code', 'warning_code', 'derating_mode', 'battery_derating_mode',
    },

    # Config entities - all control entities
    # Note: These are handled in number.py and select.py
    'config': set(),
}


def get_entity_category(sensor_key: str) -> str | None:
    """Get the entity category for a sensor.

    Args:
        sensor_key: The sensor key

    Returns:
        Entity category string ('diagnostic', 'config') or None for main sensors
    """
    for category, sensors in ENTITY_CATEGORY_MAP.items():
        if sensor_key in sensors:
            return category
    return None


# ============================================================================
# STATUS CODE MAPPINGS
# ============================================================================

STATUS_CODES = {
    0: {'name': 'Waiting', 'desc': 'Waiting for sufficient PV power or grid conditions'},
    1: {'name': 'Normal', 'desc': 'Operating normally'},
    3: {'name': 'Fault', 'desc': 'Fault condition detected'},
    5: {'name': 'Standby', 'desc': 'Inverter in standby mode'},
}


DERATING_CODES = {
    0: "No derating",
    1: "Bus voltage high derating",
    2: "Aging fixed power derating",
    3: "Grid voltage high derating",
    4: "Over-frequency reduce derating",
    5: "Single DC source mode derating",
    6: "Inverter module over-temperature derating",
    7: "User activated setting to limit output derating",
    8: "Load speed process derating",
    9: "Over back by time derating",
    10: "Internal environment over-temperature derating",
    11: "External environment over-temperature derating",
    12: "Wire impedance derating",
    13: "Parallel inverter export limit derating",
    14: "Single inverter export limit derating",
    15: "Load first mode derating",
    16: "CT installation issue derating",
    17: "Zero current mode derating",
    18: "Boost module over-temperature derating",
    19: "Zero power mode derating",
    20: "Under-frequency increase derating",
    21: "Bus bar current limit derating",
}


def get_derating_name(derating_code: int) -> str:
    """Get human-readable derating mode name."""
    return DERATING_CODES.get(derating_code, f"Unknown ({derating_code})")


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
