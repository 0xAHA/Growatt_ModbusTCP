"""TL-XH Series Inverter Profiles.

Covers TL-XH single-phase and 3-phase models.
Similar to MIN series but with high-voltage PV inputs.
"""

from .helpers import (
    merge_register_maps,
    create_base_registers,
    create_three_phase_registers,
    create_diagnostic_registers,
    create_temperature_registers,
)

# TL-XH Single Phase
TL_XH_SINGLE_BASE = merge_register_maps(
    create_base_registers(),
    create_diagnostic_registers(),
    create_temperature_registers(),
    {
        "grid_voltage": {"address": 38, "type": "holding", "scale": 0.1, "unit": "V"},
        "output_current": {"address": 39, "type": "holding", "scale": 0.1, "unit": "A"},
        "total_hours": {"address": 57, "type": "holding", "scale": 0.5, "unit": "h"},
    }
)

# TL-XH Three Phase
TL_XH_THREE_PHASE_BASE = merge_register_maps(
    create_base_registers(),
    create_three_phase_registers(),
    create_diagnostic_registers(),
    create_temperature_registers(),
    {
        "total_hours": {"address": 57, "type": "holding", "scale": 0.5, "unit": "h"},
    }
)

TL_XH_REGISTER_MAPS = {
    "TL-XH-3000-10000": {
        "name": "TL-XH Single Phase 3-10K",
        "models": ["TL-XH-3000", "TL-XH-4000", "TL-XH-5000", "TL-XH-6000", "TL-XH-8000", "TL-XH-10000"],
        "phase": "single",
        "max_power": 10000,
        "registers": TL_XH_SINGLE_BASE,
        "sensor_sets": ["basic", "diagnostic", "temperature"],
    },
    "TL-XH-US-3000-10000": {
        "name": "TL-XH US Single Phase 3-10K",
        "models": ["TL-XH-US-3000", "TL-XH-US-4000", "TL-XH-US-5000", "TL-XH-US-6000", "TL-XH-US-8000", "TL-XH-US-10000"],
        "phase": "single",
        "max_power": 10000,
        "registers": TL_XH_SINGLE_BASE,
        "sensor_sets": ["basic", "diagnostic", "temperature"],
    },
    "TL-XH-15-25KTL3": {
        "name": "TL-XH Three Phase 15-25K",
        "models": ["TL-XH-15KTL3", "TL-XH-20KTL3", "TL-XH-25KTL3"],
        "phase": "three",
        "max_power": 25000,
        "registers": TL_XH_THREE_PHASE_BASE,
        "sensor_sets": ["basic", "three_phase", "diagnostic", "temperature"],
    },
}
