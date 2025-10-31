"""MIX Series Hybrid Inverter Profiles.

Covers MIX series 3-phase hybrid inverters with battery storage.
Commercial-scale hybrid with backup and EMS functionality.
"""

from .helpers import (
    merge_register_maps,
    create_base_registers,
    create_three_phase_registers,
    create_diagnostic_registers,
    create_temperature_registers,
)

# MIX base registers
MIX_BASE_REGISTERS = merge_register_maps(
    create_base_registers(),
    create_three_phase_registers(),
    create_diagnostic_registers(),
    create_temperature_registers(),
    {
        "battery_voltage": {"address": 13, "type": "holding", "scale": 0.01, "unit": "V"},
        "battery_current": {"address": 14, "type": "holding", "scale": 0.1, "unit": "A"},
        "battery_power": {"address": 15, "type": "holding", "scale": 1, "unit": "W", "signed": True},
        "battery_soc": {"address": 17, "type": "holding", "unit": "%"},
        "battery_temp": {"address": 18, "type": "holding", "scale": 0.1, "unit": "°C"},
        "line_voltage_r_s": {"address": 50, "type": "holding", "scale": 0.1, "unit": "V"},
        "line_voltage_s_t": {"address": 51, "type": "holding", "scale": 0.1, "unit": "V"},
        "line_voltage_t_r": {"address": 52, "type": "holding", "scale": 0.1, "unit": "V"},
        "total_hours": {"address": 57, "type": "holding", "scale": 0.5, "unit": "h"},
        "backup_voltage_r": {"address": 59, "type": "holding", "scale": 0.1, "unit": "V"},
        "backup_voltage_s": {"address": 63, "type": "holding", "scale": 0.1, "unit": "V"},
        "backup_voltage_t": {"address": 67, "type": "holding", "scale": 0.1, "unit": "V"},
        "load_power": {"address": 64, "type": "holding", "scale": 1, "unit": "W"},
    }
)

# MIX with EMS control
MIX_EMS_REGISTERS = merge_register_maps(
    MIX_BASE_REGISTERS,
    {
        "ems_mode": {"address": 1000, "type": "holding", "writable": True},
        "battery_charge_start": {"address": 1001, "type": "holding", "writable": True},
        "battery_charge_end": {"address": 1002, "type": "holding", "writable": True},
        "battery_discharge_start": {"address": 1003, "type": "holding", "writable": True},
        "battery_discharge_end": {"address": 1004, "type": "holding", "writable": True},
        "battery_soc_target": {"address": 1005, "type": "holding", "writable": True},
    }
)

MIX_REGISTER_MAPS = {
    "MIX-3-6KTL3": {
        "name": "MIX 3-6K Hybrid",
        "models": ["MIX-3KTL3", "MIX-4KTL3", "MIX-5KTL3", "MIX-6KTL3"],
        "phase": "three",
        "max_power": 6000,
        "has_battery": True,
        "registers": MIX_EMS_REGISTERS,
        "sensor_sets": ["basic", "three_phase", "diagnostic", "temperature", "battery", "backup", "ems"],
    },
    "MIX-10-15KTL3": {
        "name": "MIX 10-15K Hybrid",
        "models": ["MIX-10KTL3", "MIX-15KTL3"],
        "phase": "three",
        "max_power": 15000,
        "has_battery": True,
        "registers": MIX_EMS_REGISTERS,
        "sensor_sets": ["basic", "three_phase", "diagnostic", "temperature", "battery", "backup", "ems"],
    },
}
