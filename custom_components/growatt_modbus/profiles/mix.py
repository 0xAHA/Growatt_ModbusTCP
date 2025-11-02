# MIX Series - Legacy Storage Inverters
# Three-phase hybrid with battery storage
# Register ranges: 0-124 (base), 1000-1124 (storage/EMS)

MIX_3_6KTL3 = {
    'name': 'MIX 3-6KTL3',
    'description': 'Three-phase hybrid storage inverter (3-6kW) - Legacy model',
    'notes': 'Uses 0-124, 1000-1124 register ranges. Three-phase with battery and EMS control. Merged into SPH series in newer models.',
    'input_registers': {
        # ============================================================================
        # BASE RANGE 0-124: PV, AC, and System Status
        # ============================================================================
        
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
        
        # Battery (in base range for MIX)
        13: {'name': 'battery_voltage', 'scale': 0.01, 'unit': 'V', 'desc': 'Battery pack voltage'},
        14: {'name': 'battery_current', 'scale': 0.1, 'unit': 'A', 'desc': 'Battery current', 'signed': True},
        15: {'name': 'battery_power', 'scale': 1, 'unit': 'W', 'desc': 'Battery power', 'signed': True},
        17: {'name': 'battery_soc', 'scale': 1, 'unit': '%', 'desc': 'Battery state of charge'},
        18: {'name': 'battery_temp', 'scale': 0.1, 'unit': '°C', 'desc': 'Battery temperature'},
        
        # AC Grid Frequency
        37: {'name': 'ac_frequency', 'scale': 0.01, 'unit': 'Hz'},
        
        # Three-Phase Line-to-Line Voltages (MIX uses R-S, S-T, T-R)
        38: {'name': 'ac_voltage_r', 'scale': 0.1, 'unit': 'V', 'desc': 'Phase R voltage'},
        39: {'name': 'ac_current_r', 'scale': 0.1, 'unit': 'A', 'desc': 'Phase R current'},
        40: {'name': 'ac_power_high', 'scale': 1, 'unit': '', 'desc': 'AC power HIGH', 'pair': 41},
        41: {'name': 'ac_power_low', 'scale': 1, 'unit': '', 'desc': 'AC power LOW', 'pair': 40, 'combined_scale': 0.1, 'combined_unit': 'W'},
        42: {'name': 'ac_voltage_s', 'scale': 0.1, 'unit': 'V', 'desc': 'Phase S voltage'},
        43: {'name': 'ac_current_s', 'scale': 0.1, 'unit': 'A', 'desc': 'Phase S current'},
        44: {'name': 'ac_power_s', 'scale': 0.1, 'unit': 'W', 'desc': 'Phase S power'},
        46: {'name': 'ac_voltage_t', 'scale': 0.1, 'unit': 'V', 'desc': 'Phase T voltage'},
        47: {'name': 'ac_current_t', 'scale': 0.1, 'unit': 'A', 'desc': 'Phase T current'},
        48: {'name': 'ac_power_t', 'scale': 0.1, 'unit': 'W', 'desc': 'Phase T power'},
        
        # Line-to-Line Voltages
        50: {'name': 'line_voltage_rs', 'scale': 0.1, 'unit': 'V', 'desc': 'Line voltage R-S'},
        51: {'name': 'line_voltage_st', 'scale': 0.1, 'unit': 'V', 'desc': 'Line voltage S-T'},
        52: {'name': 'line_voltage_tr', 'scale': 0.1, 'unit': 'V', 'desc': 'Line voltage T-R'},
        
        # Energy
        53: {'name': 'energy_today_high', 'scale': 1, 'unit': '', 'desc': 'Today energy HIGH', 'pair': 54},
        54: {'name': 'energy_today_low', 'scale': 1, 'unit': '', 'desc': 'Today energy LOW', 'pair': 53, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        55: {'name': 'energy_total_high', 'scale': 1, 'unit': '', 'desc': 'Total energy HIGH', 'pair': 56},
        56: {'name': 'energy_total_low', 'scale': 1, 'unit': '', 'desc': 'Total energy LOW', 'pair': 55, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        57: {'name': 'time_total_high', 'scale': 1, 'unit': '', 'pair': 58},
        58: {'name': 'time_total_low', 'scale': 1, 'unit': '', 'pair': 57, 'combined_scale': 0.5, 'combined_unit': 'h'},
        
        # Backup Output (3-phase)
        59: {'name': 'backup_voltage_r', 'scale': 0.1, 'unit': 'V', 'desc': 'Backup R-phase voltage'},
        60: {'name': 'backup_current_r', 'scale': 0.1, 'unit': 'A', 'desc': 'Backup R-phase current'},
        61: {'name': 'backup_power_r', 'scale': 1, 'unit': 'W', 'desc': 'Backup R-phase power'},
        63: {'name': 'backup_voltage_s', 'scale': 0.1, 'unit': 'V', 'desc': 'Backup S-phase voltage'},
        64: {'name': 'load_power', 'scale': 1, 'unit': 'W', 'desc': 'Total load power'},
        67: {'name': 'backup_voltage_t', 'scale': 0.1, 'unit': 'V', 'desc': 'Backup T-phase voltage'},
        
        # Temperatures
        93: {'name': 'inverter_temp', 'scale': 0.1, 'unit': '°C'},
        94: {'name': 'ipm_temp', 'scale': 0.1, 'unit': '°C'},
        95: {'name': 'boost_temp', 'scale': 0.1, 'unit': '°C'},
        
        # Diagnostics
        104: {'name': 'derating_mode', 'scale': 1, 'unit': ''},
        105: {'name': 'fault_code', 'scale': 1, 'unit': ''},
        112: {'name': 'warning_code', 'scale': 1, 'unit': ''},
        
        # ============================================================================
        # STORAGE/EMS RANGE 1000-1124: Battery Management and Power Flow
        # ============================================================================
        
        # System Work Mode
        1000: {'name': 'system_work_mode', 'scale': 1, 'unit': '', 'desc': 'EMS work mode'},
        
        # Battery Power
        1009: {'name': 'discharge_power_high', 'scale': 1, 'unit': '', 'pair': 1010},
        1010: {'name': 'discharge_power_low', 'scale': 1, 'unit': '', 'pair': 1009, 'combined_scale': 0.1, 'combined_unit': 'W'},
        1011: {'name': 'charge_power_high', 'scale': 1, 'unit': '', 'pair': 1012},
        1012: {'name': 'charge_power_low', 'scale': 1, 'unit': '', 'pair': 1011, 'combined_scale': 0.1, 'combined_unit': 'W'},
        
        # Power Flow
        1015: {'name': 'power_to_user_high', 'scale': 1, 'unit': '', 'pair': 1016},
        1016: {'name': 'power_to_user_low', 'scale': 1, 'unit': '', 'pair': 1015, 'combined_scale': 0.1, 'combined_unit': 'W'},
        1021: {'name': 'power_to_load_high', 'scale': 1, 'unit': '', 'pair': 1022},
        1022: {'name': 'power_to_load_low', 'scale': 1, 'unit': '', 'pair': 1021, 'combined_scale': 0.1, 'combined_unit': 'W'},
        1029: {'name': 'power_to_grid_high', 'scale': 1, 'unit': '', 'pair': 1030},
        1030: {'name': 'power_to_grid_low', 'scale': 1, 'unit': '', 'pair': 1029, 'combined_scale': 0.1, 'combined_unit': 'W', 'signed': True},
        1037: {'name': 'self_consumption_power_high', 'scale': 1, 'unit': '', 'pair': 1038},
        1038: {'name': 'self_consumption_power_low', 'scale': 1, 'unit': '', 'pair': 1037, 'combined_scale': 0.1, 'combined_unit': 'W'},
        1039: {'name': 'self_consumption_percentage', 'scale': 1, 'unit': '%'},
        
        # Energy Breakdown
        1044: {'name': 'energy_to_user_today_high', 'scale': 1, 'unit': '', 'pair': 1045},
        1045: {'name': 'energy_to_user_today_low', 'scale': 1, 'unit': '', 'pair': 1044, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        1046: {'name': 'energy_to_user_total_high', 'scale': 1, 'unit': '', 'pair': 1047},
        1047: {'name': 'energy_to_user_total_low', 'scale': 1, 'unit': '', 'pair': 1046, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        1048: {'name': 'energy_to_grid_today_high', 'scale': 1, 'unit': '', 'pair': 1049},
        1049: {'name': 'energy_to_grid_today_low', 'scale': 1, 'unit': '', 'pair': 1048, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        1050: {'name': 'energy_to_grid_total_high', 'scale': 1, 'unit': '', 'pair': 1051},
        1051: {'name': 'energy_to_grid_total_low', 'scale': 1, 'unit': '', 'pair': 1050, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        1052: {'name': 'discharge_energy_today_high', 'scale': 1, 'unit': '', 'pair': 1053},
        1053: {'name': 'discharge_energy_today_low', 'scale': 1, 'unit': '', 'pair': 1052, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        1054: {'name': 'discharge_energy_total_high', 'scale': 1, 'unit': '', 'pair': 1055},
        1055: {'name': 'discharge_energy_total_low', 'scale': 1, 'unit': '', 'pair': 1054, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        1056: {'name': 'charge_energy_today_high', 'scale': 1, 'unit': '', 'pair': 1057},
        1057: {'name': 'charge_energy_today_low', 'scale': 1, 'unit': '', 'pair': 1056, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        1058: {'name': 'charge_energy_total_high', 'scale': 1, 'unit': '', 'pair': 1059},
        1059: {'name': 'charge_energy_total_low', 'scale': 1, 'unit': '', 'pair': 1058, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        1060: {'name': 'load_energy_today_high', 'scale': 1, 'unit': '', 'pair': 1061},
        1061: {'name': 'load_energy_today_low', 'scale': 1, 'unit': '', 'pair': 1060, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        1062: {'name': 'load_energy_total_high', 'scale': 1, 'unit': '', 'pair': 1063},
        1063: {'name': 'load_energy_total_low', 'scale': 1, 'unit': '', 'pair': 1062, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
    },
    'holding_registers': {
        0: {'name': 'on_off', 'scale': 1, 'unit': '', 'access': 'RW'},
        
        # EMS Control (1000-1124 range)
        1000: {'name': 'ems_mode', 'scale': 1, 'unit': '', 'access': 'RW', 'desc': 'EMS operating mode'},
        1001: {'name': 'battery_charge_start', 'scale': 1, 'unit': '', 'access': 'RW', 'desc': 'Charge start time'},
        1002: {'name': 'battery_charge_end', 'scale': 1, 'unit': '', 'access': 'RW', 'desc': 'Charge end time'},
        1003: {'name': 'battery_discharge_start', 'scale': 1, 'unit': '', 'access': 'RW', 'desc': 'Discharge start time'},
        1004: {'name': 'battery_discharge_end', 'scale': 1, 'unit': '', 'access': 'RW', 'desc': 'Discharge end time'},
        1005: {'name': 'battery_soc_target', 'scale': 1, 'unit': '%', 'access': 'RW', 'desc': 'Target SOC'},
        1008: {'name': 'system_enable', 'scale': 1, 'unit': '', 'access': 'RW'},
        1044: {'name': 'priority', 'scale': 1, 'unit': '', 'access': 'RW', 'desc': '0=Load, 1=Battery, 2=Grid'},
    }
}

# Export all MIX profiles
MIX_REGISTER_MAPS = {
    'MIX_SERIES': MIX_3_6KTL3,
}