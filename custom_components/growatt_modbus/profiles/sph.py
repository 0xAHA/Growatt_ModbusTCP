# SPH 3000-6000 (Single-phase hybrid with battery)
SPH_3000_6000 = {
    'name': 'SPH Series 3-6kW',
    'description': 'Single-phase hybrid inverter with battery storage (3-6kW)',
    'notes': 'Uses 0-124 register range. 2 PV strings, battery management, backup output.',
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

        # Battery (registers 13-18 for battery in SPH models)
        13: {'name': 'battery_voltage', 'scale': 0.1, 'unit': 'V', 'desc': 'Battery pack voltage'},
        14: {'name': 'battery_current', 'scale': 0.1, 'unit': 'A', 'desc': 'Battery current (+ charging, - discharging)', 'signed': True},
        15: {'name': 'battery_power', 'scale': 1, 'unit': 'W', 'desc': 'Battery power (+ charging, - discharging)', 'signed': True},
        17: {'name': 'battery_soc', 'scale': 1, 'unit': '%', 'desc': 'Battery state of charge'},
        18: {'name': 'battery_temp', 'scale': 0.1, 'unit': '°C', 'desc': 'Battery temperature'},
        19: {'name': 'bms_type', 'scale': 1, 'unit': '', 'desc': 'BMS type identifier'},

        # AC Output
        37: {'name': 'ac_frequency', 'scale': 0.01, 'unit': 'Hz'},
        38: {'name': 'ac_voltage', 'scale': 0.1, 'unit': 'V', 'desc': 'Grid voltage'},
        39: {'name': 'ac_current', 'scale': 0.1, 'unit': 'A'},
        40: {'name': 'ac_power_high', 'scale': 1, 'unit': '', 'pair': 41},
        41: {'name': 'ac_power_low', 'scale': 1, 'unit': '', 'pair': 40, 'combined_scale': 0.1, 'combined_unit': 'W'},

        # Energy
        53: {'name': 'energy_today_high', 'scale': 1, 'unit': '', 'pair': 54},
        54: {'name': 'energy_today_low', 'scale': 1, 'unit': '', 'pair': 53, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        55: {'name': 'energy_total_high', 'scale': 1, 'unit': '', 'pair': 56},
        56: {'name': 'energy_total_low', 'scale': 1, 'unit': '', 'pair': 55, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        57: {'name': 'time_total_high', 'scale': 1, 'unit': '', 'pair': 58},
        58: {'name': 'time_total_low', 'scale': 1, 'unit': '', 'pair': 57, 'combined_scale': 0.5, 'combined_unit': 'h'},

        # Backup Output (registers 59-64 for backup/load in SPH models)
        59: {'name': 'backup_voltage', 'scale': 0.1, 'unit': 'V', 'desc': 'Backup output voltage'},
        60: {'name': 'backup_current', 'scale': 0.1, 'unit': 'A', 'desc': 'Backup output current'},
        61: {'name': 'backup_power', 'scale': 1, 'unit': 'W', 'desc': 'Backup output power'},
        62: {'name': 'backup_frequency', 'scale': 0.01, 'unit': 'Hz', 'desc': 'Backup output frequency'},
        64: {'name': 'load_power', 'scale': 1, 'unit': 'W', 'desc': 'Load consumption power'},

        # Temperatures
        93: {'name': 'inverter_temp', 'scale': 0.1, 'unit': '°C'},
        94: {'name': 'ipm_temp', 'scale': 0.1, 'unit': '°C'},
        95: {'name': 'boost_temp', 'scale': 0.1, 'unit': '°C'},

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

# SPH 7000-10000 (Higher power version)
SPH_7000_10000 = {
    'name': 'SPH Seres 7-10KW',
    'description': 'Single-phase hybrid inverter with battery storage (7-10kW)',
    'notes': 'Uses 0-124 register range. Same registers as 3-6kW model, higher power rating.',
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

        # Battery
        13: {'name': 'battery_voltage', 'scale': 0.1, 'unit': 'V'},
        14: {'name': 'battery_current', 'scale': 0.1, 'unit': 'A', 'signed': True},
        15: {'name': 'battery_power', 'scale': 1, 'unit': 'W', 'signed': True},
        17: {'name': 'battery_soc', 'scale': 1, 'unit': '%'},
        18: {'name': 'battery_temp', 'scale': 0.1, 'unit': '°C'},
        19: {'name': 'bms_type', 'scale': 1, 'unit': ''},

        # AC Output
        37: {'name': 'ac_frequency', 'scale': 0.01, 'unit': 'Hz'},
        38: {'name': 'ac_voltage', 'scale': 0.1, 'unit': 'V'},
        39: {'name': 'ac_current', 'scale': 0.1, 'unit': 'A'},
        40: {'name': 'ac_power_high', 'scale': 1, 'unit': '', 'pair': 41},
        41: {'name': 'ac_power_low', 'scale': 1, 'unit': '', 'pair': 40, 'combined_scale': 0.1, 'combined_unit': 'W'},

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

        # Temperatures
        93: {'name': 'inverter_temp', 'scale': 0.1, 'unit': '°C'},
        94: {'name': 'ipm_temp', 'scale': 0.1, 'unit': '°C'},
        95: {'name': 'boost_temp', 'scale': 0.1, 'unit': '°C'},

        # Diagnostics
        104: {'name': 'derating_mode', 'scale': 1, 'unit': ''},
        105: {'name': 'fault_code', 'scale': 1, 'unit': ''},
        112: {'name': 'warning_code', 'scale': 1, 'unit': ''},
    },
    'holding_registers': {
        0: {'name': 'on_off', 'scale': 1, 'unit': '', 'access': 'RW'},
        3: {'name': 'active_power_rate', 'scale': 1, 'unit': '%', 'access': 'RW'},
    }
}

# SPH 3000-6000 V2.01 Protocol (V1.39 + VPP 2.01 registers)
# V2.01 adds 30000+ range on top of legacy registers for complete functionality
SPH_3000_6000_V201 = {
    'name': 'SPH Series 3-6kW (V2.01)',
    'description': 'Single-phase hybrid inverter with battery storage (3-6kW) and VPP Protocol V2.01',
    'notes': 'Combines legacy (0-124 range) with V2.01 (30000+ range). Overlapping values served at both addresses.',
    'input_registers': {
        # === Legacy REGISTERS (0-124 range) ===
        **SPH_3000_6000['input_registers'],

        # === V2.01 REGISTERS (31000+ range) ===
        # Status
        31000: {'name': 'equipment_status', 'scale': 1, 'unit': '', 'desc': 'Equipment running status'},
        31001: {'name': 'system_fault_word0', 'scale': 1, 'unit': '', 'desc': 'System fault word 0'},
        31002: {'name': 'system_fault_word1', 'scale': 1, 'unit': '', 'desc': 'System fault word 1'},
        31003: {'name': 'system_fault_word2', 'scale': 1, 'unit': '', 'desc': 'System fault word 2'},
        31004: {'name': 'grid_first_connected', 'scale': 1, 'unit': '', 'desc': 'Grid first connected status'},

        # PV Data (overlaps with 3-10)
        31010: {'name': 'pv1_voltage_vpp', 'scale': 0.1, 'unit': 'V', 'maps_to': 'pv1_voltage'},
        31011: {'name': 'pv1_current_vpp', 'scale': 0.1, 'unit': 'A', 'maps_to': 'pv1_current'},
        31012: {'name': 'pv1_power_high_vpp', 'scale': 1, 'unit': '', 'pair': 31013, 'maps_to': 'pv1_power'},
        31013: {'name': 'pv1_power_low_vpp', 'scale': 1, 'unit': '', 'pair': 31012, 'combined_scale': 0.1, 'combined_unit': 'W'},
        31014: {'name': 'pv2_voltage_vpp', 'scale': 0.1, 'unit': 'V', 'maps_to': 'pv2_voltage'},
        31015: {'name': 'pv2_current_vpp', 'scale': 0.1, 'unit': 'A', 'maps_to': 'pv2_current'},
        31016: {'name': 'pv2_power_high_vpp', 'scale': 1, 'unit': '', 'pair': 31017, 'maps_to': 'pv2_power'},
        31017: {'name': 'pv2_power_low_vpp', 'scale': 1, 'unit': '', 'pair': 31016, 'combined_scale': 0.1, 'combined_unit': 'W'},

        # Total PV Power
        31018: {'name': 'pv_total_power_high_vpp', 'scale': 1, 'unit': '', 'pair': 31019, 'maps_to': 'pv_total_power'},
        31019: {'name': 'pv_total_power_low_vpp', 'scale': 1, 'unit': '', 'pair': 31018, 'combined_scale': 0.1, 'combined_unit': 'W'},

        # AC Output (overlaps with 37-41)
        31100: {'name': 'ac_voltage_vpp', 'scale': 0.1, 'unit': 'V', 'maps_to': 'ac_voltage'},
        31101: {'name': 'ac_current_vpp', 'scale': 0.1, 'unit': 'A', 'maps_to': 'ac_current'},
        31102: {'name': 'ac_power_high_vpp', 'scale': 1, 'unit': '', 'pair': 31103, 'maps_to': 'ac_power'},
        31103: {'name': 'ac_power_low_vpp', 'scale': 1, 'unit': '', 'pair': 31102, 'combined_scale': 0.1, 'combined_unit': 'VA'},
        31104: {'name': 'ac_reactive_power_high', 'scale': 1, 'unit': '', 'pair': 31105},
        31105: {'name': 'ac_reactive_power_low', 'scale': 1, 'unit': '', 'pair': 31104, 'combined_scale': 0.1, 'combined_unit': 'var'},
        31106: {'name': 'ac_frequency_vpp', 'scale': 0.01, 'unit': 'Hz', 'maps_to': 'ac_frequency'},

        # Grid/Meter Power
        31112: {'name': 'meter_power_high', 'scale': 1, 'unit': '', 'pair': 31113, 'desc': 'Grid power (same as backup power)'},
        31113: {'name': 'meter_power_low', 'scale': 1, 'unit': '', 'pair': 31112, 'combined_scale': 0.1, 'combined_unit': 'W', 'signed': True},

        # Load Power
        31118: {'name': 'load_power_high_vpp', 'scale': 1, 'unit': '', 'pair': 31119, 'maps_to': 'load_power'},
        31119: {'name': 'load_power_low_vpp', 'scale': 1, 'unit': '', 'pair': 31118, 'combined_scale': 0.1, 'combined_unit': 'W'},

        # Energy Data
        31120: {'name': 'energy_today_high_vpp', 'scale': 1, 'unit': '', 'pair': 31121, 'maps_to': 'energy_today'},
        31121: {'name': 'energy_today_low_vpp', 'scale': 1, 'unit': '', 'pair': 31120, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        31122: {'name': 'energy_total_high_vpp', 'scale': 1, 'unit': '', 'pair': 31123, 'maps_to': 'energy_total'},
        31123: {'name': 'energy_total_low_vpp', 'scale': 1, 'unit': '', 'pair': 31122, 'combined_scale': 0.1, 'combined_unit': 'kWh'},

        # Temperatures
        31130: {'name': 'inverter_temp_vpp', 'scale': 0.1, 'unit': '°C', 'maps_to': 'inverter_temp'},
        31131: {'name': 'ipm_temp_vpp', 'scale': 0.1, 'unit': '°C', 'maps_to': 'ipm_temp'},
        31132: {'name': 'boost_temp_vpp', 'scale': 0.1, 'unit': '°C', 'maps_to': 'boost_temp'},

        # Battery Cluster 1 State (31200-31223)
        31200: {'name': 'battery_discharge_power_high', 'scale': 1, 'unit': '', 'pair': 31201},
        31201: {'name': 'battery_discharge_power_low', 'scale': 1, 'unit': '', 'pair': 31200, 'combined_scale': 0.1, 'combined_unit': 'W'},
        31202: {'name': 'battery_charge_power_high', 'scale': 1, 'unit': '', 'pair': 31203},
        31203: {'name': 'battery_charge_power_low', 'scale': 1, 'unit': '', 'pair': 31202, 'combined_scale': 0.1, 'combined_unit': 'W'},
        31214: {'name': 'battery_voltage_vpp', 'scale': 0.1, 'unit': 'V', 'maps_to': 'battery_voltage', 'signed': True},
        31215: {'name': 'battery_current_vpp', 'scale': 0.1, 'unit': 'A', 'maps_to': 'battery_current', 'signed': True},
        31217: {'name': 'battery_soc_vpp', 'scale': 1, 'unit': '%', 'maps_to': 'battery_soc'},
        31222: {'name': 'battery_temp_vpp', 'scale': 0.1, 'unit': '°C', 'maps_to': 'battery_temp'},

        # Battery Cluster 2 State (31300-31323) - Optional second battery
        31300: {'name': 'battery2_discharge_power_high', 'scale': 1, 'unit': '', 'pair': 31301},
        31301: {'name': 'battery2_discharge_power_low', 'scale': 1, 'unit': '', 'pair': 31300, 'combined_scale': 0.1, 'combined_unit': 'W'},
        31302: {'name': 'battery2_charge_power_high', 'scale': 1, 'unit': '', 'pair': 31303},
        31303: {'name': 'battery2_charge_power_low', 'scale': 1, 'unit': '', 'pair': 31302, 'combined_scale': 0.1, 'combined_unit': 'W'},
        31314: {'name': 'battery2_voltage', 'scale': 0.1, 'unit': 'V', 'desc': 'Battery 2 voltage (0 if not present)', 'signed': True},
        31315: {'name': 'battery2_current', 'scale': 0.1, 'unit': 'A', 'signed': True},
        31317: {'name': 'battery2_soc', 'scale': 1, 'unit': '%'},
        31322: {'name': 'battery2_temp', 'scale': 0.1, 'unit': '°C'},
    },
    'holding_registers': {
        # === Legacy REGISTERS ===
        **SPH_3000_6000['holding_registers'],

        # === V2.01 REGISTERS (30000+ range) ===
        # Device Identification
        30000: {'name': 'dtc_code', 'scale': 1, 'unit': '', 'access': 'RO', 'desc': 'Device Type Code: 1000 for SPH 3-6kW', 'default': 1000},
        30099: {'name': 'protocol_version', 'scale': 1, 'unit': '', 'access': 'RO', 'desc': 'VPP Protocol version (201 = V2.01)', 'default': 201},

        # Control Authority
        30100: {'name': 'control_authority', 'scale': 1, 'unit': '', 'access': 'RW', 'desc': '0=Disable, 1=Enable control'},
        30101: {'name': 'remote_onoff', 'scale': 1, 'unit': '', 'access': 'RW', 'desc': '0=Off, 1=On', 'maps_to': 'on_off'},

        # System Time
        30104: {'name': 'sys_year_vpp', 'scale': 1, 'unit': '', 'access': 'RW'},
        30105: {'name': 'sys_month_vpp', 'scale': 1, 'unit': '', 'access': 'RW'},
        30106: {'name': 'sys_day_vpp', 'scale': 1, 'unit': '', 'access': 'RW'},
        30107: {'name': 'sys_hour_vpp', 'scale': 1, 'unit': '', 'access': 'RW'},
        30108: {'name': 'sys_minute_vpp', 'scale': 1, 'unit': '', 'access': 'RW'},
        30109: {'name': 'sys_second_vpp', 'scale': 1, 'unit': '', 'access': 'RW'},

        # Active Power Control
        30114: {'name': 'active_power_rate_vpp', 'scale': 0.1, 'unit': '%', 'access': 'RW', 'maps_to': 'active_power_rate'},

        # Export Limitation
        30200: {'name': 'export_limit_enable', 'scale': 1, 'unit': '', 'access': 'RW', 'desc': '0=Disable, 1=Enable'},
        30201: {'name': 'export_limit_power_rate', 'scale': 0.1, 'unit': '%', 'access': 'RW'},
    }
}

# SPH 7000-10000 V2.01 Protocol
SPH_7000_10000_V201 = {
    'name': 'SPH Series 7-10kW (V2.01)',
    'description': 'Single-phase hybrid inverter with battery storage (7-10kW) and VPP Protocol V2.01',
    'notes': 'Combines legacy (0-124 range) with V2.01 (30000+ range). Overlapping values served at both addresses.',
    'input_registers': {
        # === Legacy REGISTERS (0-124 range) ===
        **SPH_7000_10000['input_registers'],

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

        # Total PV Power
        31018: {'name': 'pv_total_power_high_vpp', 'scale': 1, 'unit': '', 'pair': 31019, 'maps_to': 'pv_total_power'},
        31019: {'name': 'pv_total_power_low_vpp', 'scale': 1, 'unit': '', 'pair': 31018, 'combined_scale': 0.1, 'combined_unit': 'W'},

        # AC Output
        31100: {'name': 'ac_voltage_vpp', 'scale': 0.1, 'unit': 'V', 'maps_to': 'ac_voltage'},
        31101: {'name': 'ac_current_vpp', 'scale': 0.1, 'unit': 'A', 'maps_to': 'ac_current'},
        31102: {'name': 'ac_power_high_vpp', 'scale': 1, 'unit': '', 'pair': 31103, 'maps_to': 'ac_power'},
        31103: {'name': 'ac_power_low_vpp', 'scale': 1, 'unit': '', 'pair': 31102, 'combined_scale': 0.1, 'combined_unit': 'VA'},
        31104: {'name': 'ac_reactive_power_high', 'scale': 1, 'unit': '', 'pair': 31105},
        31105: {'name': 'ac_reactive_power_low', 'scale': 1, 'unit': '', 'pair': 31104, 'combined_scale': 0.1, 'combined_unit': 'var'},
        31106: {'name': 'ac_frequency_vpp', 'scale': 0.01, 'unit': 'Hz', 'maps_to': 'ac_frequency'},

        # Grid/Meter Power
        31112: {'name': 'meter_power_high', 'scale': 1, 'unit': '', 'pair': 31113},
        31113: {'name': 'meter_power_low', 'scale': 1, 'unit': '', 'pair': 31112, 'combined_scale': 0.1, 'combined_unit': 'W', 'signed': True},

        # Load Power
        31118: {'name': 'load_power_high_vpp', 'scale': 1, 'unit': '', 'pair': 31119, 'maps_to': 'load_power'},
        31119: {'name': 'load_power_low_vpp', 'scale': 1, 'unit': '', 'pair': 31118, 'combined_scale': 0.1, 'combined_unit': 'W'},

        # Energy Data
        31120: {'name': 'energy_today_high_vpp', 'scale': 1, 'unit': '', 'pair': 31121, 'maps_to': 'energy_today'},
        31121: {'name': 'energy_today_low_vpp', 'scale': 1, 'unit': '', 'pair': 31120, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        31122: {'name': 'energy_total_high_vpp', 'scale': 1, 'unit': '', 'pair': 31123, 'maps_to': 'energy_total'},
        31123: {'name': 'energy_total_low_vpp', 'scale': 1, 'unit': '', 'pair': 31122, 'combined_scale': 0.1, 'combined_unit': 'kWh'},

        # Temperatures
        31130: {'name': 'inverter_temp_vpp', 'scale': 0.1, 'unit': '°C', 'maps_to': 'inverter_temp'},
        31131: {'name': 'ipm_temp_vpp', 'scale': 0.1, 'unit': '°C', 'maps_to': 'ipm_temp'},
        31132: {'name': 'boost_temp_vpp', 'scale': 0.1, 'unit': '°C', 'maps_to': 'boost_temp'},

        # Battery Cluster 1 State
        31200: {'name': 'battery_discharge_power_high', 'scale': 1, 'unit': '', 'pair': 31201},
        31201: {'name': 'battery_discharge_power_low', 'scale': 1, 'unit': '', 'pair': 31200, 'combined_scale': 0.1, 'combined_unit': 'W'},
        31202: {'name': 'battery_charge_power_high', 'scale': 1, 'unit': '', 'pair': 31203},
        31203: {'name': 'battery_charge_power_low', 'scale': 1, 'unit': '', 'pair': 31202, 'combined_scale': 0.1, 'combined_unit': 'W'},
        31214: {'name': 'battery_voltage_vpp', 'scale': 0.1, 'unit': 'V', 'maps_to': 'battery_voltage', 'signed': True},
        31215: {'name': 'battery_current_vpp', 'scale': 0.1, 'unit': 'A', 'maps_to': 'battery_current', 'signed': True},
        31217: {'name': 'battery_soc_vpp', 'scale': 1, 'unit': '%', 'maps_to': 'battery_soc'},
        31222: {'name': 'battery_temp_vpp', 'scale': 0.1, 'unit': '°C', 'maps_to': 'battery_temp'},

        # Battery Cluster 2 State
        31300: {'name': 'battery2_discharge_power_high', 'scale': 1, 'unit': '', 'pair': 31301},
        31301: {'name': 'battery2_discharge_power_low', 'scale': 1, 'unit': '', 'pair': 31300, 'combined_scale': 0.1, 'combined_unit': 'W'},
        31302: {'name': 'battery2_charge_power_high', 'scale': 1, 'unit': '', 'pair': 31303},
        31303: {'name': 'battery2_charge_power_low', 'scale': 1, 'unit': '', 'pair': 31302, 'combined_scale': 0.1, 'combined_unit': 'W'},
        31314: {'name': 'battery2_voltage', 'scale': 0.1, 'unit': 'V', 'desc': 'Battery 2 voltage (0 if not present)', 'signed': True},
        31315: {'name': 'battery2_current', 'scale': 0.1, 'unit': 'A', 'signed': True},
        31317: {'name': 'battery2_soc', 'scale': 1, 'unit': '%'},
        31322: {'name': 'battery2_temp', 'scale': 0.1, 'unit': '°C'},
    },
    'holding_registers': {
        # === Legacy REGISTERS ===
        **SPH_7000_10000['holding_registers'],

        # === V2.01 REGISTERS (30000+ range) ===
        30000: {'name': 'dtc_code', 'scale': 1, 'unit': '', 'access': 'RO', 'desc': 'Device Type Code: 1001 for SPH 7-10kW', 'default': 1001},
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

# Export all SPH profiles
SPH_REGISTER_MAPS = {
    'SPH_3000_6000': SPH_3000_6000,
    'SPH_7000_10000': SPH_7000_10000,
    'SPH_3000_6000_V201': SPH_3000_6000_V201,
    'SPH_7000_10000_V201': SPH_7000_10000_V201,
}