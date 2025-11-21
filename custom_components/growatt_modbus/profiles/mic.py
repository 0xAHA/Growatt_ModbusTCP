# MIC Series - Micro Inverters (V3.05 Protocol)
# Single-phase micro inverters, 600W-3300W
# Register range: 0-179 (compact legacy protocol)
# Protocol version: V3.05 (2013)

MIC_600_3300TL_X = {
    'name': 'MIC 600-3300TL-X',
    'description': 'Single-phase micro inverter (0.6-3.3kW) - Legacy V3.05 protocol',
    'notes': 'Uses legacy 0-179 register range. Single PV string only. Simple monitoring features. Protocol V3.05 from 2013.',
    'input_registers': {
        # ============================================================================
        # RANGE 0-179: Complete register map for MIC series
        # ============================================================================
        
        # System Status
        0: {'name': 'inverter_status', 'scale': 1, 'unit': '', 'desc': '0=Waiting, 1=Normal, 3=Fault'},
        
        # PV Input Total Power (32-bit)
        1: {'name': 'pv_total_power_high', 'scale': 1, 'unit': '', 'pair': 2},
        2: {'name': 'pv_total_power_low', 'scale': 1, 'unit': '', 'pair': 1, 'combined_scale': 0.1, 'combined_unit': 'W'},
        
        # PV String 1 (Only string for MIC series)
        3: {'name': 'pv1_voltage', 'scale': 0.1, 'unit': 'V'},
        4: {'name': 'pv1_current', 'scale': 0.1, 'unit': 'A'},
        5: {'name': 'pv1_power_high', 'scale': 1, 'unit': '', 'pair': 6},
        6: {'name': 'pv1_power_low', 'scale': 1, 'unit': '', 'pair': 5, 'combined_scale': 0.1, 'combined_unit': 'W'},
        
        # AC Output Total Power (32-bit)
        11: {'name': 'ac_power_high', 'scale': 1, 'unit': '', 'pair': 12},
        12: {'name': 'ac_power_low', 'scale': 1, 'unit': '', 'pair': 11, 'combined_scale': 0.1, 'combined_unit': 'W'},
        
        # AC Output
        13: {'name': 'ac_frequency', 'scale': 0.01, 'unit': 'Hz'},
        14: {'name': 'ac_voltage', 'scale': 0.1, 'unit': 'V'},
        15: {'name': 'ac_current', 'scale': 0.1, 'unit': 'A'},
        16: {'name': 'ac_power_single_high', 'scale': 1, 'unit': '', 'pair': 17},
        17: {'name': 'ac_power_single_low', 'scale': 1, 'unit': '', 'pair': 16, 'combined_scale': 0.1, 'combined_unit': 'VA'},
        
        # Energy
        26: {'name': 'energy_today_high', 'scale': 1, 'unit': '', 'desc': 'Today energy HIGH', 'pair': 27},
        27: {'name': 'energy_today_low', 'scale': 1, 'unit': '', 'desc': 'Today energy LOW', 'pair': 26, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        28: {'name': 'energy_total_high', 'scale': 1, 'unit': '', 'desc': 'Total energy HIGH', 'pair': 29},
        29: {'name': 'energy_total_low', 'scale': 1, 'unit': '', 'desc': 'Total energy LOW', 'pair': 28, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        30: {'name': 'time_total_high', 'scale': 1, 'unit': '', 'pair': 31},
        31: {'name': 'time_total_low', 'scale': 1, 'unit': '', 'pair': 30, 'combined_scale': 0.5, 'combined_unit': 'h'},
        
        # Temperatures
        32: {'name': 'inverter_temp', 'scale': 0.1, 'unit': '°C'},
        41: {'name': 'ipm_temp', 'scale': 0.1, 'unit': '°C', 'desc': 'Internal power module temperature'},
        
        # Diagnostics
        40: {'name': 'fault_code', 'scale': 1, 'unit': ''},
        64: {'name': 'warning_code', 'scale': 1, 'unit': ''},
        
        # Grid Fault Records (90-114 for fault history)
        90: {'name': 'grid_fault_1_code', 'scale': 1, 'unit': ''},
        91: {'name': 'grid_fault_1_date', 'scale': 1, 'unit': '', 'desc': 'Year/Month (year offset 2000)'},
        92: {'name': 'grid_fault_1_time', 'scale': 1, 'unit': '', 'desc': 'Day/Hour'},
        93: {'name': 'grid_fault_1_time_ms', 'scale': 1, 'unit': '', 'desc': 'Min/Sec'},
        94: {'name': 'grid_fault_1_value', 'scale': 1, 'unit': '', 'desc': '0.1V for voltage faults, 0.01Hz for frequency'},
        
        # Auto test diagnostics (135-144)
        135: {'name': 'auto_test_process', 'scale': 1, 'unit': ''},
        136: {'name': 'auto_test_result', 'scale': 1, 'unit': ''},
        137: {'name': 'test_step_stop', 'scale': 1, 'unit': ''},
        138: {'name': 'reserved_0', 'scale': 1, 'unit': ''},
        139: {'name': 'safety_voltage_limit', 'scale': 0.1, 'unit': 'V'},
        140: {'name': 'safety_time_limit', 'scale': 1, 'unit': 'ms'},
        141: {'name': 'real_value', 'scale': 0.1, 'unit': 'V'},
        142: {'name': 'test_value', 'scale': 0.1, 'unit': 'V'},
        143: {'name': 'test_treat_value', 'scale': 0.1, 'unit': 'V'},
        144: {'name': 'test_treat_time', 'scale': 1, 'unit': 'ms'},
    },
    'holding_registers': {
        0: {'name': 'on_off', 'scale': 1, 'unit': '', 'access': 'RW', 'desc': 'Low byte: on/off (1/0), High byte: auto start (1/0)'},
        2: {'name': 'pf_cmd_memory', 'scale': 1, 'unit': '', 'access': 'RW', 'desc': 'Power factor memory state (0/1)'},
        3: {'name': 'active_power_rate', 'scale': 1, 'unit': '%', 'access': 'RW', 'desc': 'Max output active power percent (0-100)'},
        4: {'name': 'reactive_power_rate', 'scale': 1, 'unit': '%', 'access': 'RW', 'desc': 'Max output reactive power percent (0-100)'},
        5: {'name': 'power_factor', 'scale': 1, 'unit': '', 'access': 'RW', 'desc': 'Power factor x10000 (0-20000)'},
        30: {'name': 'com_address', 'scale': 1, 'unit': '', 'access': 'RW', 'desc': 'Modbus communication address'},
    }
}

# MIC V2.01 Protocol (V3.05 + VPP 2.01 registers)
MIC_600_3300TL_X_V201 = {
    'name': 'MIC 600-3300TL-X (V2.01)',
    'description': 'Single-phase micro inverter (0.6-3.3kW) with VPP Protocol V2.01',
    'notes': 'Combines V3.05 (0-179 range) with V2.01 (30000+ range). Overlapping values served at both addresses.',
    'input_registers': {
        # === V3.05 REGISTERS (0-179 range) ===
        **MIC_600_3300TL_X['input_registers'],

        # === V2.01 REGISTERS (31000+ range) ===
        # Status
        31000: {'name': 'equipment_status', 'scale': 1, 'unit': '', 'desc': 'Equipment running status'},
        31001: {'name': 'system_fault_word0', 'scale': 1, 'unit': '', 'desc': 'System fault word 0'},
        31002: {'name': 'system_fault_word1', 'scale': 1, 'unit': '', 'desc': 'System fault word 1'},
        31003: {'name': 'system_fault_word2', 'scale': 1, 'unit': '', 'desc': 'System fault word 2'},
        31004: {'name': 'grid_first_connected', 'scale': 1, 'unit': '', 'desc': 'Grid first connected status'},

        # PV Data (single PV string for MIC)
        31010: {'name': 'pv1_voltage_vpp', 'scale': 0.1, 'unit': 'V', 'maps_to': 'pv1_voltage'},
        31011: {'name': 'pv1_current_vpp', 'scale': 0.1, 'unit': 'A', 'maps_to': 'pv1_current'},
        31012: {'name': 'pv1_power_high_vpp', 'scale': 1, 'unit': '', 'pair': 31013, 'maps_to': 'pv1_power'},
        31013: {'name': 'pv1_power_low_vpp', 'scale': 1, 'unit': '', 'pair': 31012, 'combined_scale': 0.1, 'combined_unit': 'W'},

        # Total PV Power
        31018: {'name': 'pv_total_power_high_vpp', 'scale': 1, 'unit': '', 'pair': 31019, 'maps_to': 'pv_total_power'},
        31019: {'name': 'pv_total_power_low_vpp', 'scale': 1, 'unit': '', 'pair': 31018, 'combined_scale': 0.1, 'combined_unit': 'W'},

        # AC Output
        31100: {'name': 'ac_voltage_vpp', 'scale': 0.1, 'unit': 'V', 'maps_to': 'ac_voltage'},
        31101: {'name': 'ac_current_vpp', 'scale': 0.1, 'unit': 'A', 'maps_to': 'ac_current'},
        31102: {'name': 'ac_power_high_vpp', 'scale': 1, 'unit': '', 'pair': 31103, 'maps_to': 'ac_power'},
        31103: {'name': 'ac_power_low_vpp', 'scale': 1, 'unit': '', 'pair': 31102, 'combined_scale': 0.1, 'combined_unit': 'VA'},
        31106: {'name': 'ac_frequency_vpp', 'scale': 0.01, 'unit': 'Hz', 'maps_to': 'ac_frequency'},

        # Energy Data
        31120: {'name': 'energy_today_high_vpp', 'scale': 1, 'unit': '', 'pair': 31121, 'maps_to': 'energy_today'},
        31121: {'name': 'energy_today_low_vpp', 'scale': 1, 'unit': '', 'pair': 31120, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        31122: {'name': 'energy_total_high_vpp', 'scale': 1, 'unit': '', 'pair': 31123, 'maps_to': 'energy_total'},
        31123: {'name': 'energy_total_low_vpp', 'scale': 1, 'unit': '', 'pair': 31122, 'combined_scale': 0.1, 'combined_unit': 'kWh'},

        # Temperatures
        31130: {'name': 'inverter_temp_vpp', 'scale': 0.1, 'unit': '°C', 'maps_to': 'inverter_temp'},
        31131: {'name': 'ipm_temp_vpp', 'scale': 0.1, 'unit': '°C', 'maps_to': 'ipm_temp'},
    },
    'holding_registers': {
        # === V3.05 REGISTERS ===
        **MIC_600_3300TL_X['holding_registers'],

        # === V2.01 REGISTERS (30000+ range) ===
        30000: {'name': 'dtc_code', 'scale': 1, 'unit': '', 'access': 'RO', 'desc': 'Device Type Code: 6000 for MIC', 'default': 6000},
        30099: {'name': 'protocol_version', 'scale': 1, 'unit': '', 'access': 'RO', 'desc': 'VPP Protocol version (201 = V2.01)', 'default': 201},
        30100: {'name': 'control_authority', 'scale': 1, 'unit': '', 'access': 'RW'},
        30101: {'name': 'remote_onoff', 'scale': 1, 'unit': '', 'access': 'RW', 'maps_to': 'on_off'},
        30104: {'name': 'sys_year_vpp', 'scale': 1, 'unit': '', 'access': 'RW'},
        30105: {'name': 'sys_month_vpp', 'scale': 1, 'unit': '', 'access': 'RW'},
        30106: {'name': 'sys_day_vpp', 'scale': 1, 'unit': '', 'access': 'RW'},
        30107: {'name': 'sys_hour_vpp', 'scale': 1, 'unit': '', 'access': 'RW'},
        30108: {'name': 'sys_minute_vpp', 'scale': 1, 'unit': '', 'access': 'RW'},
        30109: {'name': 'sys_second_vpp', 'scale': 1, 'unit': '', 'access': 'RW'},
        30112: {'name': 'com_address_vpp', 'scale': 1, 'unit': '', 'access': 'RW', 'maps_to': 'com_address'},
        30114: {'name': 'active_power_rate_vpp', 'scale': 0.1, 'unit': '%', 'access': 'RW', 'maps_to': 'active_power_rate'},
    }
}

# Export all MIC profiles
MIC_REGISTER_MAPS = {
    'MIC_600_3300TL_X': MIC_600_3300TL_X,
    'MIC_600_3300TL_X_V201': MIC_600_3300TL_X_V201,
}