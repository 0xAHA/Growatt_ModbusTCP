"""MID Series Inverter Profiles.

Three-phase commercial inverters (15-25kW).
Based on Growatt Protocol V1.39 (2024.04.16)

Register Structure:
- Uses 0-124 address range (base 0 series)
- Three-phase AC output (R, S, T phases)
- 32-bit values stored as HIGH/LOW word pairs
"""

# MID-15000-25000TL3-X (Three-phase, 15-25kW)
MID_15000_25000TL3_X = {
    'name': 'MID-15000-25000TL3-X',
    'description': 'Three-phase commercial inverter (15-25kW)',
    'notes': 'Uses 0-124, 125-249 register range. Three-phase output.',
    'input_registers': {
        # System Status
        0: {'name': 'inverter_status', 'scale': 1, 'unit': '', 'desc': '0=Waiting, 1=Normal, 3=Fault'},
        
        # PV Totals
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
        
        # Output Power
        35: {'name': 'output_power_high', 'scale': 1, 'unit': '', 'pair': 36},
        36: {'name': 'output_power_low', 'scale': 1, 'unit': '', 'pair': 35, 'combined_scale': 0.1, 'combined_unit': 'W'},
        
        # Grid Frequency
        37: {'name': 'grid_frequency', 'scale': 0.01, 'unit': 'Hz'},
        
        # Phase R (L1)
        38: {'name': 'grid_voltage_r', 'scale': 0.1, 'unit': 'V', 'desc': 'Phase R voltage'},
        39: {'name': 'grid_current_r', 'scale': 0.1, 'unit': 'A', 'desc': 'Phase R current'},
        40: {'name': 'grid_power_r_high', 'scale': 1, 'unit': '', 'pair': 41},
        41: {'name': 'grid_power_r_low', 'scale': 1, 'unit': '', 'pair': 40, 'combined_scale': 0.1, 'combined_unit': 'VA'},
        
        # Phase S (L2)
        42: {'name': 'grid_voltage_s', 'scale': 0.1, 'unit': 'V', 'desc': 'Phase S voltage'},
        43: {'name': 'grid_current_s', 'scale': 0.1, 'unit': 'A', 'desc': 'Phase S current'},
        44: {'name': 'grid_power_s_high', 'scale': 1, 'unit': '', 'pair': 45},
        45: {'name': 'grid_power_s_low', 'scale': 1, 'unit': '', 'pair': 44, 'combined_scale': 0.1, 'combined_unit': 'VA'},
        
        # Phase T (L3)
        46: {'name': 'grid_voltage_t', 'scale': 0.1, 'unit': 'V', 'desc': 'Phase T voltage'},
        47: {'name': 'grid_current_t', 'scale': 0.1, 'unit': 'A', 'desc': 'Phase T current'},
        48: {'name': 'grid_power_t_high', 'scale': 1, 'unit': '', 'pair': 49},
        49: {'name': 'grid_power_t_low', 'scale': 1, 'unit': '', 'pair': 48, 'combined_scale': 0.1, 'combined_unit': 'VA'},
        
        # Line voltages
        50: {'name': 'grid_voltage_rs', 'scale': 0.1, 'unit': 'V', 'desc': 'Line voltage R-S'},
        51: {'name': 'grid_voltage_st', 'scale': 0.1, 'unit': 'V', 'desc': 'Line voltage S-T'},
        52: {'name': 'grid_voltage_tr', 'scale': 0.1, 'unit': 'V', 'desc': 'Line voltage T-R'},
        
        # Energy
        53: {'name': 'energy_today_high', 'scale': 1, 'unit': '', 'pair': 54},
        54: {'name': 'energy_today_low', 'scale': 1, 'unit': '', 'pair': 53, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        55: {'name': 'energy_total_high', 'scale': 1, 'unit': '', 'pair': 56},
        56: {'name': 'energy_total_low', 'scale': 1, 'unit': '', 'pair': 55, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        
        # Temperatures
        93: {'name': 'inverter_temp', 'scale': 0.1, 'unit': '°C'},
        94: {'name': 'ipm_temp', 'scale': 0.1, 'unit': '°C'},
        95: {'name': 'boost_temp', 'scale': 0.1, 'unit': '°C'},
        
        # Status
        100: {'name': 'power_factor', 'scale': 1, 'unit': ''},
        104: {'name': 'derating_mode', 'scale': 1, 'unit': ''},
        105: {'name': 'fault_code', 'scale': 1, 'unit': ''},
        112: {'name': 'warning_code', 'scale': 1, 'unit': ''},
    },
    'holding_registers': {
        0: {'name': 'on_off', 'scale': 1, 'unit': '', 'access': 'RW'},
        3: {'name': 'active_power_rate', 'scale': 1, 'unit': '%', 'access': 'RW'},
        30: {'name': 'modbus_address', 'scale': 1, 'unit': '', 'access': 'RW'},
    }
}

# Export all MID profiles
MID_REGISTER_MAPS = {
    'MID_15000_25000TL3_X': MID_15000_25000TL3_X,
}
