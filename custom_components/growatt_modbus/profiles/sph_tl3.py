# SPH-TL3 Series - Three-Phase Hybrid with Battery Storage
# Based on SPH-10000-TL3-BH-UP scan results
# Register scan date: 2025-10-28

SPH_TL3_3000_10000 = {
    'name': 'SPH-TL3 Series 3-10kW',
    'description': 'Three-phase hybrid inverter with battery storage (3-10kW)',
    'notes': 'Uses 0-124, 1000-1124 register ranges. Three-phase with battery management.',
    'input_registers': {
        # ============================================================================
        # BASE RANGE 0-124: PV, AC, and System Status
        # ============================================================================
        
        # System Status
        0: {'name': 'inverter_status', 'scale': 1, 'unit': '', 'desc': '0=Waiting, 1=Normal, 3=Fault, 5=Standby'},
        
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
        
        # AC Grid Frequency
        37: {'name': 'ac_frequency', 'scale': 0.01, 'unit': 'Hz'},

        # Three-Phase AC Output - Phase R
        38: {'name': 'ac_voltage_r', 'scale': 0.1, 'unit': 'V', 'desc': 'Phase R voltage'},
        39: {'name': 'ac_current_r', 'scale': 0.1, 'unit': 'A', 'desc': 'Phase R current'},
        40: {'name': 'ac_power_r_high', 'scale': 1, 'unit': '', 'pair': 41},
        41: {'name': 'ac_power_r_low', 'scale': 1, 'unit': '', 'pair': 40, 'combined_scale': 0.1, 'combined_unit': 'W'},

        # Three-Phase AC Output - Phase S
        42: {'name': 'ac_voltage_s', 'scale': 0.1, 'unit': 'V', 'desc': 'Phase S voltage'},
        43: {'name': 'ac_current_s', 'scale': 0.1, 'unit': 'A', 'desc': 'Phase S current'},
        44: {'name': 'ac_power_s_high', 'scale': 1, 'unit': '', 'pair': 45},
        45: {'name': 'ac_power_s_low', 'scale': 1, 'unit': '', 'pair': 44, 'combined_scale': 0.1, 'combined_unit': 'W'},

        # Three-Phase AC Output - Phase T
        46: {'name': 'ac_voltage_t', 'scale': 0.1, 'unit': 'V', 'desc': 'Phase T voltage'},
        47: {'name': 'ac_current_t', 'scale': 0.1, 'unit': 'A', 'desc': 'Phase T current'},
        48: {'name': 'ac_power_t_high', 'scale': 1, 'unit': '', 'pair': 49},
        49: {'name': 'ac_power_t_low', 'scale': 1, 'unit': '', 'pair': 48, 'combined_scale': 0.1, 'combined_unit': 'W'},
        
        # Energy
        53: {'name': 'energy_today_high', 'scale': 1, 'unit': '', 'desc': 'Today energy HIGH', 'pair': 54},
        54: {'name': 'energy_today_low', 'scale': 1, 'unit': '', 'desc': 'Today energy LOW', 'pair': 53, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        55: {'name': 'energy_total_high', 'scale': 1, 'unit': '', 'desc': 'Total energy HIGH', 'pair': 56},
        56: {'name': 'energy_total_low', 'scale': 1, 'unit': '', 'desc': 'Total energy LOW', 'pair': 55, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        
        # Temperatures
        93: {'name': 'inverter_temp', 'scale': 0.1, 'unit': '°C'},
        
        # Status
        105: {'name': 'fault_code', 'scale': 1, 'unit': ''},
        112: {'name': 'warning_code', 'scale': 1, 'unit': ''},
        
        # ============================================================================
        # STORAGE RANGE 1000-1124: Battery and Power Flow
        # ============================================================================
        
        # System Work Mode
        1000: {'name': 'system_work_mode', 'scale': 1, 'unit': '', 'desc': 'Work mode'},
        
        # Battery Discharge/Charge Power
        1009: {'name': 'discharge_power_high', 'scale': 1, 'unit': '', 'pair': 1010},
        1010: {'name': 'discharge_power_low', 'scale': 1, 'unit': '', 'pair': 1009, 'combined_scale': 0.1, 'combined_unit': 'W'},
        1011: {'name': 'charge_power_high', 'scale': 1, 'unit': '', 'pair': 1012},
        1012: {'name': 'charge_power_low', 'scale': 1, 'unit': '', 'pair': 1011, 'combined_scale': 0.1, 'combined_unit': 'W'},
        
        # Battery State
        1013: {'name': 'battery_voltage', 'scale': 0.1, 'unit': 'V'},
        1014: {'name': 'battery_soc', 'scale': 1, 'unit': '%'},
        1040: {'name': 'battery_temp', 'scale': 0.1, 'unit': '°C'},
        1041: {'name': 'battery_type', 'scale': 1, 'unit': ''},
        
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
        1008: {'name': 'system_enable', 'scale': 1, 'unit': '', 'access': 'RW'},
        1044: {'name': 'priority', 'scale': 1, 'unit': '', 'access': 'RW', 'desc': '0=Load, 1=Battery, 2=Grid'},
    }
}

# Export all SPH profiles
SPH_TL3_REGISTER_MAPS = {
    'SPH_TL3_3000_10000': SPH_TL3_3000_10000,
}