"""Helper functions for building Growatt inverter profile register maps.

These helpers reduce repetition across profiles by providing common register sets.
"""

from typing import Dict, Any


def merge_register_maps(*maps: Dict[str, Any]) -> Dict[str, Any]:
    """Merge multiple register maps into one.

    Args:
        *maps: Variable number of register map dictionaries

    Returns:
        Combined dictionary with all registers
    """
    result = {}
    for map_dict in maps:
        result.update(map_dict)
    return result


def create_base_registers() -> Dict[str, Any]:
    """Create common base registers found in all inverters.

    Returns:
        Dictionary of basic PV input and AC output registers
    """
    return {
        "status": {"address": 0, "type": "holding", "scale": 1, "unit": ""},
        "pv1_voltage": {"address": 3, "type": "holding", "scale": 0.1, "unit": "V"},
        "pv1_current": {"address": 4, "type": "holding", "scale": 0.1, "unit": "A"},
        "pv1_power": {"address": 5, "type": "holding", "scale": 0.1, "unit": "W"},
        "pv2_voltage": {"address": 7, "type": "holding", "scale": 0.1, "unit": "V"},
        "pv2_current": {"address": 8, "type": "holding", "scale": 0.1, "unit": "A"},
        "pv2_power": {"address": 9, "type": "holding", "scale": 0.1, "unit": "W"},
        "ac_voltage": {"address": 38, "type": "holding", "scale": 0.1, "unit": "V"},
        "ac_current": {"address": 39, "type": "holding", "scale": 0.1, "unit": "A"},
        "ac_power": {"address": 40, "type": "holding", "scale": 0.1, "unit": "W"},
        "ac_frequency": {"address": 37, "type": "holding", "scale": 0.01, "unit": "Hz"},
        "energy_today": {"address": 53, "type": "holding", "scale": 0.1, "unit": "kWh"},
        "energy_total": {"address": 55, "type": "holding", "scale": 0.1, "unit": "kWh"},
    }


def create_diagnostic_registers() -> Dict[str, Any]:
    """Create common diagnostic registers for fault/warning codes.

    Returns:
        Dictionary of diagnostic registers
    """
    return {
        "fault_code": {"address": 105, "type": "holding", "scale": 1, "unit": ""},
        "warning_code": {"address": 112, "type": "holding", "scale": 1, "unit": ""},
        "derating_mode": {"address": 104, "type": "holding", "scale": 1, "unit": ""},
    }


def create_temperature_registers() -> Dict[str, Any]:
    """Create common temperature sensor registers.

    Returns:
        Dictionary of temperature registers
    """
    return {
        "inverter_temp": {"address": 93, "type": "holding", "scale": 0.1, "unit": "°C"},
        "ipm_temp": {"address": 94, "type": "holding", "scale": 0.1, "unit": "°C"},
        "boost_temp": {"address": 95, "type": "holding", "scale": 0.1, "unit": "°C"},
    }


def create_pv3_registers() -> Dict[str, Any]:
    """Create PV3 string registers for 3-string inverters.

    Returns:
        Dictionary of PV3 registers
    """
    return {
        "pv3_voltage": {"address": 11, "type": "holding", "scale": 0.1, "unit": "V"},
        "pv3_current": {"address": 12, "type": "holding", "scale": 0.1, "unit": "A"},
        "pv3_power": {"address": 13, "type": "holding", "scale": 0.1, "unit": "W"},
    }


def create_battery_registers() -> Dict[str, Any]:
    """Create battery storage registers for hybrid inverters.

    Returns:
        Dictionary of battery registers
    """
    return {
        "battery_voltage": {"address": 13, "type": "holding", "scale": 0.1, "unit": "V"},
        "battery_current": {"address": 14, "type": "holding", "scale": 0.1, "unit": "A"},
        "battery_power": {"address": 15, "type": "holding", "scale": 1, "unit": "W", "signed": True},
        "battery_soc": {"address": 17, "type": "holding", "unit": "%"},
        "battery_temp": {"address": 18, "type": "holding", "scale": 0.1, "unit": "°C"},
    }


def create_three_phase_registers() -> Dict[str, Any]:
    """Create three-phase AC registers.

    Returns:
        Dictionary of 3-phase AC registers
    """
    return {
        "ac_voltage_r": {"address": 38, "type": "holding", "scale": 0.1, "unit": "V"},
        "ac_voltage_s": {"address": 42, "type": "holding", "scale": 0.1, "unit": "V"},
        "ac_voltage_t": {"address": 46, "type": "holding", "scale": 0.1, "unit": "V"},
        "ac_current_r": {"address": 39, "type": "holding", "scale": 0.1, "unit": "A"},
        "ac_current_s": {"address": 43, "type": "holding", "scale": 0.1, "unit": "A"},
        "ac_current_t": {"address": 47, "type": "holding", "scale": 0.1, "unit": "A"},
        "ac_power_r": {"address": 40, "type": "holding", "scale": 0.1, "unit": "W"},
        "ac_power_s": {"address": 44, "type": "holding", "scale": 0.1, "unit": "W"},
        "ac_power_t": {"address": 48, "type": "holding", "scale": 0.1, "unit": "W"},
    }


__all__ = [
    "merge_register_maps",
    "create_base_registers",
    "create_diagnostic_registers",
    "create_temperature_registers",
    "create_pv3_registers",
    "create_battery_registers",
    "create_three_phase_registers",
]