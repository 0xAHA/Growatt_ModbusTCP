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

# Export all MIC profiles
MIC_REGISTER_MAPS = {
    'MIC_600_3300TL_X': MIC_600_3300TL_X,
}