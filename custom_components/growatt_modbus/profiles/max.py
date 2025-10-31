"""MAX Series Inverter Profiles.

Covers MAX series high-power 3-phase commercial inverters.
Includes 1500V high-voltage string capability.
"""

from .helpers import (
    merge_register_maps,
    create_base_registers,
    create_three_phase_registers,
    create_diagnostic_registers,
    create_temperature_registers,
)

# MAX base registers
MAX_BASE_REGISTERS = merge_register_maps(
    create_base_registers(),
    create_three_phase_registers(),
    create_diagnostic_registers(),
    create_temperature_registers(),
    {
        "pv3_voltage": {"address": 11, "type": "holding", "scale": 0.1, "unit": "V"},
        "pv3_current": {"address": 12, "type": "holding", "scale": 0.1, "unit": "A"},
        "pv3_power": {"address": 13, "type": "holding", "scale": 0.1, "unit": "W"},
        "pv4_voltage": {"address": 15, "type": "holding", "scale": 0.1, "unit": "V"},
        "pv4_current": {"address": 16, "type": "holding", "scale": 0.1, "unit": "A"},
        "pv4_power": {"address": 17, "type": "holding", "scale": 0.1, "unit": "W"},
        "line_voltage_r_s": {"address": 50, "type": "holding", "scale": 0.1, "unit": "V"},
        "line_voltage_s_t": {"address": 51, "type": "holding", "scale": 0.1, "unit": "V"},
        "line_voltage_t_r": {"address": 52, "type": "holding", "scale": 0.1, "unit": "V"},
        "total_hours": {"address": 57, "type": "holding", "scale": 0.5, "unit": "h"},
    }
)

MAX_REGISTER_MAPS = {
    "MAX-50-100KTL3-LV": {
        "name": "MAX 50-100K LV",
        "models": ["MAX-50KTL3-LV", "MAX-60KTL3-LV", "MAX-75KTL3-LV", "MAX-80KTL3-LV", "MAX-100KTL3-LV"],
        "phase": "three",
        "max_power": 100000,
        "voltage": "low",
        "registers": MAX_BASE_REGISTERS,
        "sensor_sets": ["basic", "three_phase", "diagnostic", "temperature", "pv3", "pv4"],
    },
    "MAX-100-125KTL3-X-LV": {
        "name": "MAX 100-125K X LV",
        "models": ["MAX-100KTL3-X-LV", "MAX-110KTL3-X-LV", "MAX-120KTL3-X-LV", "MAX-125KTL3-X-LV"],
        "phase": "three",
        "max_power": 125000,
        "voltage": "low",
        "registers": MAX_BASE_REGISTERS,
        "sensor_sets": ["basic", "three_phase", "diagnostic", "temperature", "pv3", "pv4"],
    },
    "MAX-1500V-SERIES": {
        "name": "MAX 1500V High Voltage",
        "models": ["MAX-50KTL3-HV", "MAX-60KTL3-HV", "MAX-75KTL3-HV", "MAX-80KTL3-HV", "MAX-100KTL3-HV"],
        "phase": "three",
        "max_power": 100000,
        "voltage": "1500V",
        "registers": MAX_BASE_REGISTERS,
        "sensor_sets": ["basic", "three_phase", "diagnostic", "temperature", "pv3", "pv4"],
    },
}
