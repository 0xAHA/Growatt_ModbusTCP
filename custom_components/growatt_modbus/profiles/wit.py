"""WIT Series Inverter Profiles.

Covers WIT series compact single and 3-phase inverters.
Lightweight design for residential and small commercial applications.
"""

from .helpers import (
    merge_register_maps,
    create_base_registers,
    create_three_phase_registers,
    create_diagnostic_registers,
    create_temperature_registers,
)

# WIT single phase
WIT_SINGLE_BASE = merge_register_maps(
    create_base_registers(),
    create_diagnostic_registers(),
    create_temperature_registers(),
    {
        "grid_voltage": {"address": 38, "type": "holding", "scale": 0.1, "unit": "V"},
        "output_current": {"address": 39, "type": "holding", "scale": 0.1, "unit": "A"},
        "total_hours": {"address": 57, "type": "holding", "scale": 0.5, "unit": "h"},
    }
)

# WIT three phase
WIT_THREE_PHASE_BASE = merge_register_maps(
    create_base_registers(),
    create_three_phase_registers(),
    create_diagnostic_registers(),
    create_temperature_registers(),
    {
        "total_hours": {"address": 57, "type": "holding", "scale": 0.5, "unit": "h"},
    }
)

WIT_REGISTER_MAPS = {
    "WIT-3000-6000": {
        "name": "WIT 3-6K Single Phase",
        "models": ["WIT-3000", "WIT-4000", "WIT-5000", "WIT-6000"],
        "phase": "single",
        "max_power": 6000,
        "registers": WIT_SINGLE_BASE,
        "sensor_sets": ["basic", "diagnostic", "temperature"],
    },
    "WIT-TL3-SERIES": {
        "name": "WIT TL3 Three Phase",
        "models": ["WIT-3KTL3", "WIT-4KTL3", "WIT-5KTL3", "WIT-6KTL3"],
        "phase": "three",
        "max_power": 6000,
        "registers": WIT_THREE_PHASE_BASE,
        "sensor_sets": ["basic", "three_phase", "diagnostic", "temperature"],
    },
}
