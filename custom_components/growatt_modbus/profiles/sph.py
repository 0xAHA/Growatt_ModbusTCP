"""SPH Series Hybrid Inverter Profiles.

Covers SPH series single-phase hybrid inverters with battery storage.
Includes battery management, EMS control, and backup functionality.
"""

from .helpers import (
    merge_register_maps,
    create_base_registers,
    create_diagnostic_registers,
    create_temperature_registers,
)

# SPH base registers
SPH_BASE_REGISTERS = merge_register_maps(
    create_base_registers(),
    create_diagnostic_registers(),
    create_temperature_registers(),
    {
        "grid_voltage": {"address": 38, "type": "holding", "scale": 0.1, "unit": "V"},
        "output_current": {"address": 39, "type": "holding", "scale": 0.1, "unit": "A"},
        "battery_voltage": {"address": 13, "type": "holding", "scale": "dynamic", "unit": "V"},
        "battery_current": {"address": 14, "type": "holding", "scale": 0.1, "unit": "A"},
        "battery_power": {"address": 15, "type": "holding", "scale": 1, "unit": "W", "signed": True},
        "battery_soc": {"address": 17, "type": "holding", "unit": "%"},
        "battery_temp": {"address": 18, "type": "holding", "scale": 0.1, "unit": "°C"},
        "bms_type": {"address": 19, "type": "holding"},
        "total_hours": {"address": 57, "type": "holding", "scale": 0.5, "unit": "h"},
        "backup_voltage": {"address": 59, "type": "holding", "scale": 0.1, "unit": "V"},
        "backup_current": {"address": 60, "type": "holding", "scale": 0.1, "unit": "A"},
        "backup_power": {"address": 61, "type": "holding", "scale": 1, "unit": "W"},
        "backup_frequency": {"address": 62, "type": "holding", "scale": 0.01, "unit": "Hz"},
        "load_power": {"address": 64, "type": "holding", "scale": 1, "unit": "W"},
    }
)

# SPH with EMS control
SPH_EMS_REGISTERS = merge_register_maps(
    SPH_BASE_REGISTERS,
    {
        "ems_mode": {"address": 1000, "type": "holding", "writable": True},
        "battery_charge_start": {"address": 1001, "type": "holding", "writable": True},
        "battery_charge_end": {"address": 1002, "type": "holding", "writable": True},
        "battery_discharge_start": {"address": 1003, "type": "holding", "writable": True},
        "battery_discharge_end": {"address": 1004, "type": "holding", "writable": True},
        "battery_soc_target": {"address": 1005, "type": "holding", "writable": True},
    }
)

SPH_REGISTER_MAPS = {
    "SPH-3000-6000": {
        "name": "SPH 3-6K Hybrid",
        "models": ["SPH-3000", "SPH-3600", "SPH-4000", "SPH-4600", "SPH-5000", "SPH-6000"],
        "phase": "single",
        "max_power": 6000,
        "has_battery": True,
        "registers": SPH_EMS_REGISTERS,
        "sensor_sets": ["basic", "diagnostic", "temperature", "battery", "backup", "ems"],
    },
    "SPH-7000-10000": {
        "name": "SPH 7-10K Hybrid",
        "models": ["SPH-7000", "SPH-8000", "SPH-10000"],
        "phase": "single",
        "max_power": 10000,
        "has_battery": True,
        "registers": SPH_EMS_REGISTERS,
        "sensor_sets": ["basic", "diagnostic", "temperature", "battery", "backup", "ems"],
    },
}
