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

        # Three-Phase AC Output - Phase R (with generic aliases for compatibility)
        38: {'name': 'ac_voltage_r', 'scale': 0.1, 'unit': 'V', 'desc': 'Phase R voltage', 'alias': 'ac_voltage'},
        39: {'name': 'ac_current_r', 'scale': 0.1, 'unit': 'A', 'desc': 'Phase R current', 'alias': 'ac_current'},
        40: {'name': 'ac_power_r_high', 'scale': 1, 'unit': '', 'pair': 41, 'alias': 'ac_power_high'},
        41: {'name': 'ac_power_r_low', 'scale': 1, 'unit': '', 'pair': 40, 'combined_scale': 0.1, 'combined_unit': 'W', 'alias': 'ac_power_low'},

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

# SPH-TL3 V2.01 Protocol (legacy + VPP 2.01 registers)
SPH_TL3_3000_10000_V201 = {
    'name': 'SPH-TL3 Series 3-10kW (V2.01)',
    'description': 'Three-phase hybrid inverter with battery storage (3-10kW) and VPP Protocol V2.01',
    'notes': 'Combines legacy (0-124, 1000-1124 range) with V2.01 (30000+ range). Overlapping values served at both addresses.',
    'input_registers': {
        # === Legacy REGISTERS (0-124, 1000-1124 ranges) ===
        **SPH_TL3_3000_10000['input_registers'],

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

        # Three-Phase AC Output
        31100: {'name': 'ac_voltage_r_vpp', 'scale': 0.1, 'unit': 'V', 'maps_to': 'ac_voltage_r'},
        31101: {'name': 'ac_voltage_s_vpp', 'scale': 0.1, 'unit': 'V', 'maps_to': 'ac_voltage_s'},
        31102: {'name': 'ac_voltage_t_vpp', 'scale': 0.1, 'unit': 'V', 'maps_to': 'ac_voltage_t'},
        31103: {'name': 'ac_frequency_vpp', 'scale': 0.01, 'unit': 'Hz', 'maps_to': 'ac_frequency'},

        # Grid/Meter Power (maps to power_to_grid at 1029/1030)
        31112: {'name': 'meter_power_high', 'scale': 1, 'unit': '', 'pair': 31113, 'maps_to': 'power_to_grid'},
        31113: {'name': 'meter_power_low', 'scale': 1, 'unit': '', 'pair': 31112, 'combined_scale': 0.1, 'combined_unit': 'W', 'signed': True},

        # Load Power (maps to power_to_load at 1021/1022)
        31118: {'name': 'load_power_high_vpp', 'scale': 1, 'unit': '', 'pair': 31119, 'maps_to': 'power_to_load'},
        31119: {'name': 'load_power_low_vpp', 'scale': 1, 'unit': '', 'pair': 31118, 'combined_scale': 0.1, 'combined_unit': 'W'},

        # Energy Data
        31120: {'name': 'energy_today_high_vpp', 'scale': 1, 'unit': '', 'pair': 31121, 'maps_to': 'energy_today'},
        31121: {'name': 'energy_today_low_vpp', 'scale': 1, 'unit': '', 'pair': 31120, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        31122: {'name': 'energy_total_high_vpp', 'scale': 1, 'unit': '', 'pair': 31123, 'maps_to': 'energy_total'},
        31123: {'name': 'energy_total_low_vpp', 'scale': 1, 'unit': '', 'pair': 31122, 'combined_scale': 0.1, 'combined_unit': 'kWh'},

        # Temperatures
        31130: {'name': 'inverter_temp_vpp', 'scale': 0.1, 'unit': '°C', 'maps_to': 'inverter_temp'},

        # Battery Cluster 1 State (31200-31223)
        31200: {'name': 'battery_discharge_power_high', 'scale': 1, 'unit': '', 'pair': 31201, 'maps_to': 'discharge_power'},
        31201: {'name': 'battery_discharge_power_low', 'scale': 1, 'unit': '', 'pair': 31200, 'combined_scale': 0.1, 'combined_unit': 'W'},
        31202: {'name': 'battery_charge_power_high', 'scale': 1, 'unit': '', 'pair': 31203, 'maps_to': 'charge_power'},
        31203: {'name': 'battery_charge_power_low', 'scale': 1, 'unit': '', 'pair': 31202, 'combined_scale': 0.1, 'combined_unit': 'W'},
        31214: {'name': 'battery_voltage_vpp', 'scale': 0.1, 'unit': 'V', 'maps_to': 'battery_voltage', 'signed': True},
        31217: {'name': 'battery_soc_vpp', 'scale': 1, 'unit': '%', 'maps_to': 'battery_soc'},
        31222: {'name': 'battery_temp_vpp', 'scale': 0.1, 'unit': '°C', 'maps_to': 'battery_temp'},

        # Battery Cluster 2 State (31300-31323)
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
        **SPH_TL3_3000_10000['holding_registers'],

        # === V2.01 REGISTERS (30000+ range) ===
        30000: {'name': 'dtc_code', 'scale': 1, 'unit': '', 'access': 'RO', 'desc': 'Device Type Code: 2000 for SPH-TL3', 'default': 2000},
        30099: {'name': 'protocol_version', 'scale': 1, 'unit': '', 'access': 'RO', 'desc': 'VPP Protocol version (201 = V2.01)', 'default': 201},
        30100: {'name': 'control_authority', 'scale': 1, 'unit': '', 'access': 'RW'},
        30101: {'name': 'remote_onoff', 'scale': 1, 'unit': '', 'access': 'RW', 'maps_to': 'on_off'},
        30104: {'name': 'sys_year_vpp', 'scale': 1, 'unit': '', 'access': 'RW'},
        30105: {'name': 'sys_month_vpp', 'scale': 1, 'unit': '', 'access': 'RW'},
        30106: {'name': 'sys_day_vpp', 'scale': 1, 'unit': '', 'access': 'RW'},
        30107: {'name': 'sys_hour_vpp', 'scale': 1, 'unit': '', 'access': 'RW'},
        30108: {'name': 'sys_minute_vpp', 'scale': 1, 'unit': '', 'access': 'RW'},
        30109: {'name': 'sys_second_vpp', 'scale': 1, 'unit': '', 'access': 'RW'},
        30200: {'name': 'export_limit_enable', 'scale': 1, 'unit': '', 'access': 'RW'},
        30201: {'name': 'export_limit_power_rate', 'scale': 0.1, 'unit': '%', 'access': 'RW'},
    }
}

# Export all SPH profiles
SPH_TL3_REGISTER_MAPS = {
    'SPH_TL3_3000_10000': SPH_TL3_3000_10000,
    'SPH_TL3_3000_10000_V201': SPH_TL3_3000_10000_V201,
}