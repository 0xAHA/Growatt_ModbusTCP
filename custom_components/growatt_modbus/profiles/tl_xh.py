# TL-XH Series - Single-Phase Hybrid Inverters with Battery Storage
# Uses similar register layout to SPH series

# TL-XH 3000-10000 (Single-phase hybrid with battery, 3-10kW)
TL_XH_3000_10000 = {
    'name': 'TL-XH 3000-10000',
    'description': 'Single-phase hybrid inverter with battery (3-10kW)',
    'notes': 'Uses 0-124 register range. 3 PV strings, battery management, backup output.',
    'input_registers': {
        # System Status
        0: {'name': 'inverter_status', 'scale': 1, 'unit': '', 'desc': '0=Waiting, 1=Normal, 3=Fault'},

        # PV Total Power (32-bit)
        1: {'name': 'pv_total_power_high', 'scale': 1, 'unit': '', 'pair': 2},
        2: {'name': 'pv_total_power_low', 'scale': 1, 'unit': '', 'pair': 1, 'combined_scale': 0.1, 'combined_unit': 'W'},

        # PV String 1
        3: {'name': 'pv1_voltage', 'scale': 0.1, 'unit': 'V'},
        4: {'name': 'pv1_current', 'scale': 0.1, 'unit': 'A'},
        5: {'name': 'pv1_power_high', 'scale': 1, 'unit': '', 'pair': 6},
        6: {'name': 'pv1_power_low', 'scale': 1, 'unit': '', 'pair': 5, 'combined_scale': 0.1, 'combined_unit': 'W'},

        # PV String 2
        7: {'name': 'pv2_voltage', 'scale': 0.1, 'unit': 'V'},
        8: {'name': 'pv2_current', 'scale': 0.1, 'unit': 'A'},
        9: {'name': 'pv2_power_high', 'scale': 1, 'unit': '', 'pair': 10},
        10: {'name': 'pv2_power_low', 'scale': 1, 'unit': '', 'pair': 9, 'combined_scale': 0.1, 'combined_unit': 'W'},

        # PV String 3
        11: {'name': 'pv3_voltage', 'scale': 0.1, 'unit': 'V'},
        12: {'name': 'pv3_current', 'scale': 0.1, 'unit': 'A'},
        13: {'name': 'pv3_power_high', 'scale': 1, 'unit': '', 'pair': 14},
        14: {'name': 'pv3_power_low', 'scale': 1, 'unit': '', 'pair': 13, 'combined_scale': 0.1, 'combined_unit': 'W'},

        # Battery
        17: {'name': 'battery_voltage', 'scale': 0.1, 'unit': 'V'},
        18: {'name': 'battery_current', 'scale': 0.1, 'unit': 'A', 'signed': True},
        19: {'name': 'battery_power', 'scale': 1, 'unit': 'W', 'signed': True},
        21: {'name': 'battery_soc', 'scale': 1, 'unit': '%'},
        22: {'name': 'battery_temp', 'scale': 0.1, 'unit': '°C', 'signed': True},

        # AC Output
        37: {'name': 'ac_frequency', 'scale': 0.01, 'unit': 'Hz'},
        38: {'name': 'ac_voltage', 'scale': 0.1, 'unit': 'V'},
        39: {'name': 'ac_current', 'scale': 0.1, 'unit': 'A'},
        40: {'name': 'ac_power_high', 'scale': 1, 'unit': '', 'pair': 41},
        41: {'name': 'ac_power_low', 'scale': 1, 'unit': '', 'pair': 40, 'combined_scale': 0.1, 'combined_unit': 'W'},

        # Power Flow
        45: {'name': 'power_to_grid_high', 'scale': 1, 'unit': '', 'pair': 46},
        46: {'name': 'power_to_grid_low', 'scale': 1, 'unit': '', 'pair': 45, 'combined_scale': 0.1, 'combined_unit': 'W', 'signed': True},
        47: {'name': 'power_to_load_high', 'scale': 1, 'unit': '', 'pair': 48},
        48: {'name': 'power_to_load_low', 'scale': 1, 'unit': '', 'pair': 47, 'combined_scale': 0.1, 'combined_unit': 'W'},

        # Energy
        53: {'name': 'energy_today_high', 'scale': 1, 'unit': '', 'pair': 54},
        54: {'name': 'energy_today_low', 'scale': 1, 'unit': '', 'pair': 53, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        55: {'name': 'energy_total_high', 'scale': 1, 'unit': '', 'pair': 56},
        56: {'name': 'energy_total_low', 'scale': 1, 'unit': '', 'pair': 55, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        57: {'name': 'time_total_high', 'scale': 1, 'unit': '', 'pair': 58},
        58: {'name': 'time_total_low', 'scale': 1, 'unit': '', 'pair': 57, 'combined_scale': 0.5, 'combined_unit': 'h'},

        # Backup Output
        59: {'name': 'backup_voltage', 'scale': 0.1, 'unit': 'V'},
        60: {'name': 'backup_current', 'scale': 0.1, 'unit': 'A'},
        61: {'name': 'backup_power', 'scale': 1, 'unit': 'W'},
        62: {'name': 'backup_frequency', 'scale': 0.01, 'unit': 'Hz'},
        64: {'name': 'load_power', 'scale': 1, 'unit': 'W'},

        # Energy Breakdown
        69: {'name': 'energy_to_grid_today_high', 'scale': 1, 'unit': '', 'pair': 70},
        70: {'name': 'energy_to_grid_today_low', 'scale': 1, 'unit': '', 'pair': 69, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        71: {'name': 'energy_to_grid_total_high', 'scale': 1, 'unit': '', 'pair': 72},
        72: {'name': 'energy_to_grid_total_low', 'scale': 1, 'unit': '', 'pair': 71, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        77: {'name': 'load_energy_today_high', 'scale': 1, 'unit': '', 'pair': 78},
        78: {'name': 'load_energy_today_low', 'scale': 1, 'unit': '', 'pair': 77, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        79: {'name': 'load_energy_total_high', 'scale': 1, 'unit': '', 'pair': 80},
        80: {'name': 'load_energy_total_low', 'scale': 1, 'unit': '', 'pair': 79, 'combined_scale': 0.1, 'combined_unit': 'kWh'},

        # Temperatures
        93: {'name': 'inverter_temp', 'scale': 0.1, 'unit': '°C', 'signed': True},
        94: {'name': 'ipm_temp', 'scale': 0.1, 'unit': '°C', 'signed': True},
        95: {'name': 'boost_temp', 'scale': 0.1, 'unit': '°C', 'signed': True},

        # Diagnostics
        104: {'name': 'derating_mode', 'scale': 1, 'unit': ''},
        105: {'name': 'fault_code', 'scale': 1, 'unit': ''},
        112: {'name': 'warning_code', 'scale': 1, 'unit': ''},
    },
    'holding_registers': {
        0: {'name': 'on_off', 'scale': 1, 'unit': '', 'access': 'RW', 'desc': '0=Off, 1=On'},
        3: {'name': 'active_power_rate', 'scale': 1, 'unit': '%', 'access': 'RW'},
    }
}

# TL-XH US 3000-10000 (US version, same registers)
TL_XH_US_3000_10000 = {
    'name': 'TL-XH US 3000-10000',
    'description': 'US single-phase hybrid inverter with battery (3-10kW)',
    'notes': 'Uses 0-124 register range. Same as TL-XH but for US market.',
    'input_registers': TL_XH_3000_10000['input_registers'].copy(),
    'holding_registers': TL_XH_3000_10000['holding_registers'].copy(),
}

# TL-XH V2.01 Protocol (legacy + VPP 2.01 registers)
TL_XH_3000_10000_V201 = {
    'name': 'TL-XH 3000-10000 (V2.01)',
    'description': 'Single-phase hybrid inverter with battery (3-10kW) and VPP Protocol V2.01',
    'notes': 'Combines legacy (0-124 range) with V2.01 (30000+ range). Overlapping values served at both addresses.',
    'input_registers': {
        # === Legacy REGISTERS (0-124 range) ===
        **TL_XH_3000_10000['input_registers'],

        # === V2.01 REGISTERS (31000+ range) ===
        # Status
        31000: {'name': 'equipment_status', 'scale': 1, 'unit': '', 'desc': 'Equipment running status'},
        31001: {'name': 'system_fault_word0', 'scale': 1, 'unit': '', 'desc': 'System fault word 0'},
        31002: {'name': 'system_fault_word1', 'scale': 1, 'unit': '', 'desc': 'System fault word 1'},
        31003: {'name': 'system_fault_word2', 'scale': 1, 'unit': '', 'desc': 'System fault word 2'},
        31004: {'name': 'grid_first_connected', 'scale': 1, 'unit': '', 'desc': 'Grid first connected status'},

        # PV Data
        31010: {'name': 'pv1_voltage_vpp', 'scale': 0.1, 'unit': 'V', 'maps_to': 'pv1_voltage'},
        31011: {'name': 'pv1_current_vpp', 'scale': 0.1, 'unit': 'A', 'maps_to': 'pv1_current'},
        31012: {'name': 'pv1_power_high_vpp', 'scale': 1, 'unit': '', 'pair': 31013, 'maps_to': 'pv1_power'},
        31013: {'name': 'pv1_power_low_vpp', 'scale': 1, 'unit': '', 'pair': 31012, 'combined_scale': 0.1, 'combined_unit': 'W'},
        31014: {'name': 'pv2_voltage_vpp', 'scale': 0.1, 'unit': 'V', 'maps_to': 'pv2_voltage'},
        31015: {'name': 'pv2_current_vpp', 'scale': 0.1, 'unit': 'A', 'maps_to': 'pv2_current'},
        31016: {'name': 'pv2_power_high_vpp', 'scale': 1, 'unit': '', 'pair': 31017, 'maps_to': 'pv2_power'},
        31017: {'name': 'pv2_power_low_vpp', 'scale': 1, 'unit': '', 'pair': 31016, 'combined_scale': 0.1, 'combined_unit': 'W'},
        31018: {'name': 'pv3_voltage_vpp', 'scale': 0.1, 'unit': 'V', 'maps_to': 'pv3_voltage'},
        31019: {'name': 'pv3_current_vpp', 'scale': 0.1, 'unit': 'A', 'maps_to': 'pv3_current'},
        31020: {'name': 'pv3_power_high_vpp', 'scale': 1, 'unit': '', 'pair': 31021, 'maps_to': 'pv3_power'},
        31021: {'name': 'pv3_power_low_vpp', 'scale': 1, 'unit': '', 'pair': 31020, 'combined_scale': 0.1, 'combined_unit': 'W'},

        # Total PV Power
        31022: {'name': 'pv_total_power_high_vpp', 'scale': 1, 'unit': '', 'pair': 31023, 'maps_to': 'pv_total_power'},
        31023: {'name': 'pv_total_power_low_vpp', 'scale': 1, 'unit': '', 'pair': 31022, 'combined_scale': 0.1, 'combined_unit': 'W'},

        # AC Output
        31100: {'name': 'ac_voltage_vpp', 'scale': 0.1, 'unit': 'V', 'maps_to': 'ac_voltage'},
        31101: {'name': 'ac_current_vpp', 'scale': 0.1, 'unit': 'A', 'maps_to': 'ac_current'},
        31102: {'name': 'ac_power_high_vpp', 'scale': 1, 'unit': '', 'pair': 31103, 'maps_to': 'ac_power'},
        31103: {'name': 'ac_power_low_vpp', 'scale': 1, 'unit': '', 'pair': 31102, 'combined_scale': 0.1, 'combined_unit': 'VA'},
        31106: {'name': 'ac_frequency_vpp', 'scale': 0.01, 'unit': 'Hz', 'maps_to': 'ac_frequency'},

        # Grid/Meter Power
        31112: {'name': 'meter_power_high', 'scale': 1, 'unit': '', 'pair': 31113, 'maps_to': 'power_to_grid'},
        31113: {'name': 'meter_power_low', 'scale': 1, 'unit': '', 'pair': 31112, 'combined_scale': 0.1, 'combined_unit': 'W', 'signed': True},

        # Load Power
        31118: {'name': 'load_power_high_vpp', 'scale': 1, 'unit': '', 'pair': 31119, 'maps_to': 'power_to_load'},
        31119: {'name': 'load_power_low_vpp', 'scale': 1, 'unit': '', 'pair': 31118, 'combined_scale': 0.1, 'combined_unit': 'W'},

        # Energy Data
        31120: {'name': 'energy_today_high_vpp', 'scale': 1, 'unit': '', 'pair': 31121, 'maps_to': 'energy_today'},
        31121: {'name': 'energy_today_low_vpp', 'scale': 1, 'unit': '', 'pair': 31120, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        31122: {'name': 'energy_total_high_vpp', 'scale': 1, 'unit': '', 'pair': 31123, 'maps_to': 'energy_total'},
        31123: {'name': 'energy_total_low_vpp', 'scale': 1, 'unit': '', 'pair': 31122, 'combined_scale': 0.1, 'combined_unit': 'kWh'},

        # Temperatures
        31130: {'name': 'inverter_temp_vpp', 'scale': 0.1, 'unit': '°C', 'maps_to': 'inverter_temp', 'signed': True},
        31131: {'name': 'ipm_temp_vpp', 'scale': 0.1, 'unit': '°C', 'maps_to': 'ipm_temp', 'signed': True},
        31132: {'name': 'boost_temp_vpp', 'scale': 0.1, 'unit': '°C', 'maps_to': 'boost_temp', 'signed': True},

        # Battery Cluster 1 State
        31200: {'name': 'battery_discharge_power_high', 'scale': 1, 'unit': '', 'pair': 31201},
        31201: {'name': 'battery_discharge_power_low', 'scale': 1, 'unit': '', 'pair': 31200, 'combined_scale': 0.1, 'combined_unit': 'W'},
        31202: {'name': 'battery_charge_power_high', 'scale': 1, 'unit': '', 'pair': 31203},
        31203: {'name': 'battery_charge_power_low', 'scale': 1, 'unit': '', 'pair': 31202, 'combined_scale': 0.1, 'combined_unit': 'W'},
        31214: {'name': 'battery_voltage_vpp', 'scale': 0.1, 'unit': 'V', 'maps_to': 'battery_voltage', 'signed': True},
        31215: {'name': 'battery_current_vpp', 'scale': 0.1, 'unit': 'A', 'maps_to': 'battery_current', 'signed': True},
        31217: {'name': 'battery_soc_vpp', 'scale': 1, 'unit': '%', 'maps_to': 'battery_soc'},
        31222: {'name': 'battery_temp_vpp', 'scale': 0.1, 'unit': '°C', 'maps_to': 'battery_temp', 'signed': True},

        # Battery Cluster 2 State
        31300: {'name': 'battery2_discharge_power_high', 'scale': 1, 'unit': '', 'pair': 31301},
        31301: {'name': 'battery2_discharge_power_low', 'scale': 1, 'unit': '', 'pair': 31300, 'combined_scale': 0.1, 'combined_unit': 'W'},
        31302: {'name': 'battery2_charge_power_high', 'scale': 1, 'unit': '', 'pair': 31303},
        31303: {'name': 'battery2_charge_power_low', 'scale': 1, 'unit': '', 'pair': 31302, 'combined_scale': 0.1, 'combined_unit': 'W'},
        31314: {'name': 'battery2_voltage', 'scale': 0.1, 'unit': 'V', 'desc': 'Battery 2 voltage (0 if not present)', 'signed': True},
        31315: {'name': 'battery2_current', 'scale': 0.1, 'unit': 'A', 'signed': True},
        31317: {'name': 'battery2_soc', 'scale': 1, 'unit': '%'},
        31322: {'name': 'battery2_temp', 'scale': 0.1, 'unit': '°C', 'signed': True},
    },
    'holding_registers': {
        # === Legacy REGISTERS ===
        **TL_XH_3000_10000['holding_registers'],

        # === V2.01 REGISTERS (30000+ range) ===
        30000: {'name': 'dtc_code', 'scale': 1, 'unit': '', 'access': 'RO', 'desc': 'Device Type Code: 4000 for TL-XH', 'default': 5100},
        30099: {'name': 'protocol_version', 'scale': 1, 'unit': '', 'access': 'RO', 'desc': 'VPP Protocol version (201 = V2.01)', 'default': 201},
        30100: {'name': 'control_authority', 'scale': 1, 'unit': '', 'access': 'RW'},
        30101: {'name': 'remote_onoff', 'scale': 1, 'unit': '', 'access': 'RW', 'maps_to': 'on_off'},
        30104: {'name': 'sys_year_vpp', 'scale': 1, 'unit': '', 'access': 'RW'},
        30105: {'name': 'sys_month_vpp', 'scale': 1, 'unit': '', 'access': 'RW'},
        30106: {'name': 'sys_day_vpp', 'scale': 1, 'unit': '', 'access': 'RW'},
        30107: {'name': 'sys_hour_vpp', 'scale': 1, 'unit': '', 'access': 'RW'},
        30108: {'name': 'sys_minute_vpp', 'scale': 1, 'unit': '', 'access': 'RW'},
        30109: {'name': 'sys_second_vpp', 'scale': 1, 'unit': '', 'access': 'RW'},
        30114: {'name': 'active_power_rate_vpp', 'scale': 0.1, 'unit': '%', 'access': 'RW', 'maps_to': 'active_power_rate'},
        30200: {'name': 'export_limit_enable', 'scale': 1, 'unit': '', 'access': 'RW'},
        30201: {'name': 'export_limit_power_rate', 'scale': 0.1, 'unit': '%', 'access': 'RW'},
    }
}

# TL-XH US V2.01 Protocol
TL_XH_US_3000_10000_V201 = {
    'name': 'TL-XH US 3000-10000 (V2.01)',
    'description': 'US single-phase hybrid inverter with battery (3-10kW) and VPP Protocol V2.01',
    'notes': 'Combines legacy (0-124 range) with V2.01 (30000+ range). US market version.',
    'input_registers': TL_XH_3000_10000_V201['input_registers'].copy(),
    'holding_registers': TL_XH_3000_10000_V201['holding_registers'].copy(),
}
# Update DTC code for US version
TL_XH_US_3000_10000_V201['holding_registers'][30000] = {
    'name': 'dtc_code', 'scale': 1, 'unit': '', 'access': 'RO',
    'desc': 'Device Type Code: 4001 for TL-XH US', 'default': 5100
}

# Export all TL-XH profiles
TL_XH_REGISTER_MAPS = {
    'TL_XH_3000_10000': TL_XH_3000_10000,
    'TL_XH_US_3000_10000': TL_XH_US_3000_10000,
    'TL_XH_3000_10000_V201': TL_XH_3000_10000_V201,
    'TL_XH_US_3000_10000_V201': TL_XH_US_3000_10000_V201,
}
