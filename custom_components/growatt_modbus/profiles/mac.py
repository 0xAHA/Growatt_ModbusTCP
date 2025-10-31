"""MAC Series Inverter Profiles.

Covers MAC series commercial 3-phase inverters.
Mid-range commercial power ratings.
"""

from .helpers import (
    merge_register_maps,
    create_base_registers,
    create_three_phase_registers,
    create_diagnostic_registers,
    create_temperature_registers,
)

# MAC base registers
MAC_BASE_REGISTERS = merge_register_maps(
    create_base_registers(),
    create_three_phase_registers(),
    create_diagnostic_registers(),
    create_temperature_registers(),
    {
        "pv3_voltage": {"address": 11, "type": "holding", "scale": 0.1, "unit": "V"},
        "pv3_current": {"address": 12, "type": "holding", "scale": 0.1, "unit": "A"},
        "pv3_power": {"address": 13, "type": "holding", "scale": 0.1, "unit": "W"},
        "line_voltage_r_s": {"address": 50, "type": "holding", "scale": 0.1, "unit": "V"},
        "line_voltage_s_t": {"address": 51, "type": "holding", "scale": 0.1, "unit": "V"},
        "line_voltage_t_r": {"address": 52, "type": "holding", "scale": 0.1, "unit": "V"},
        "total_hours": {"address": 57, "type": "holding", "scale": 0.5, "unit": "h"},
    }
)

MAC_REGISTER_MAPS = {
    "MAC-30-50KTL3": {
        "name": "MAC 30-50K Series",
        "models": ["MAC-30KTL3", "MAC-36KTL3", "MAC-40KTL3", "MAC-50KTL3"],
        "phase": "three",
        "max_power": 50000,
        "registers": MAC_BASE_REGISTERS,
        "sensor_sets": ["basic", "three_phase", "diagnostic", "temperature", "pv3"],
    },
}
