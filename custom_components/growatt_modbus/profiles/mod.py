# MOD-6000-15000TL3-XH (Three-phase hybrid with battery, 6-15kW)
MOD_6000_15000TL3_XH = {
    'name': 'MOD TL3-XH Series',
    'description': 'Modular three-phase hybrid inverter with battery (6-15kW)',
    'notes': 'Uses 0-124 base range + 3000+ battery range. Validated with real hardware 2025-10-26.',
    'input_registers': {
        # === BASE RANGE (0-124) - Inverter Data ===
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
        
        # PV String 3 (optional - often unused)
        11: {'name': 'pv3_voltage', 'scale': 0.1, 'unit': 'V'},
        12: {'name': 'pv3_current', 'scale': 0.1, 'unit': 'A'},
        13: {'name': 'pv3_power_high', 'scale': 1, 'unit': '', 'pair': 14},
        14: {'name': 'pv3_power_low', 'scale': 1, 'unit': '', 'pair': 13, 'combined_scale': 0.1, 'combined_unit': 'W'},
        
        # Output Power Total (32-bit)
        35: {'name': 'output_power_high', 'scale': 1, 'unit': '', 'pair': 36},
        36: {'name': 'output_power_low', 'scale': 1, 'unit': '', 'pair': 35, 'combined_scale': 0.1, 'combined_unit': 'W'},
        
        # === AC OUTPUT - THREE PHASE ===
        # Grid Frequency (shared across all phases)
        37: {'name': 'ac_frequency', 'scale': 0.01, 'unit': 'Hz', 'desc': 'AC output frequency'},

        # Generic AC aliases (point to Phase R for compatibility with generic code)
        # These allow the standard ac_voltage/current/power fields to work
        38: {'name': 'ac_voltage_r', 'scale': 0.1, 'unit': 'V', 'desc': 'Phase R AC voltage', 'alias': 'ac_voltage'},
        39: {'name': 'ac_current_r', 'scale': 0.1, 'unit': 'A', 'desc': 'Phase R AC current', 'alias': 'ac_current'},
        40: {'name': 'ac_power_r_high', 'scale': 1, 'unit': '', 'pair': 41, 'alias': 'ac_power_high'},
        41: {'name': 'ac_power_r_low', 'scale': 1, 'unit': '', 'pair': 40, 'combined_scale': 0.1, 'combined_unit': 'VA', 'alias': 'ac_power_low'},
        
        # Phase S (L2) - AC Output
        42: {'name': 'ac_voltage_s', 'scale': 0.1, 'unit': 'V', 'desc': 'Phase S AC voltage'},
        43: {'name': 'ac_current_s', 'scale': 0.1, 'unit': 'A', 'desc': 'Phase S AC current'},
        44: {'name': 'ac_power_s_high', 'scale': 1, 'unit': '', 'pair': 45},
        45: {'name': 'ac_power_s_low', 'scale': 1, 'unit': '', 'pair': 44, 'combined_scale': 0.1, 'combined_unit': 'VA'},
        
        # Phase T (L3) - AC Output
        46: {'name': 'ac_voltage_t', 'scale': 0.1, 'unit': 'V', 'desc': 'Phase T AC voltage'},
        47: {'name': 'ac_current_t', 'scale': 0.1, 'unit': 'A', 'desc': 'Phase T AC current'},
        48: {'name': 'ac_power_t_high', 'scale': 1, 'unit': '', 'pair': 49},
        49: {'name': 'ac_power_t_low', 'scale': 1, 'unit': '', 'pair': 48, 'combined_scale': 0.1, 'combined_unit': 'VA'},
        
        # Line-to-Line Voltages (three-phase only)
        50: {'name': 'line_voltage_rs', 'scale': 0.1, 'unit': 'V', 'desc': 'Line voltage R-S'},
        51: {'name': 'line_voltage_st', 'scale': 0.1, 'unit': 'V', 'desc': 'Line voltage S-T'},
        52: {'name': 'line_voltage_tr', 'scale': 0.1, 'unit': 'V', 'desc': 'Line voltage T-R'},
        
        # Energy Today (32-bit) - VALIDATED: 8.1kWh
        53: {'name': 'energy_today_high', 'scale': 1, 'unit': '', 'pair': 54},
        54: {'name': 'energy_today_low', 'scale': 1, 'unit': '', 'pair': 53, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        
        # Energy Total (32-bit)
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
        
        # === BATTERY RANGE (3000+) - Battery & Power Flow ===
        # System Status
        3000: {'name': 'battery_status', 'scale': 1, 'unit': '', 'desc': 'Battery system status'},
        
        # Power Flow (32-bit pairs, signed for import/export)
        3041: {'name': 'power_to_user_high', 'scale': 1, 'unit': '', 'pair': 3042},
        3042: {'name': 'power_to_user_low', 'scale': 1, 'unit': '', 'pair': 3041, 'combined_scale': 0.1, 'combined_unit': 'W'},
        3043: {'name': 'power_to_grid_high', 'scale': 1, 'unit': '', 'pair': 3044},
        3044: {'name': 'power_to_grid_low', 'scale': 1, 'unit': '', 'pair': 3043, 'combined_scale': 0.1, 'combined_unit': 'W', 'signed': True},
        3045: {'name': 'power_to_load_high', 'scale': 1, 'unit': '', 'pair': 3046},
        3046: {'name': 'power_to_load_low', 'scale': 1, 'unit': '', 'pair': 3045, 'combined_scale': 0.1, 'combined_unit': 'W'},
        
        # Energy Breakdown
        3067: {'name': 'energy_to_user_today_high', 'scale': 1, 'unit': '', 'pair': 3068},
        3068: {'name': 'energy_to_user_today_low', 'scale': 1, 'unit': '', 'pair': 3067, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        3071: {'name': 'energy_to_grid_today_high', 'scale': 1, 'unit': '', 'pair': 3072},
        3072: {'name': 'energy_to_grid_today_low', 'scale': 1, 'unit': '', 'pair': 3071, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        3073: {'name': 'energy_to_grid_total_high', 'scale': 1, 'unit': '', 'pair': 3074},
        3074: {'name': 'energy_to_grid_total_low', 'scale': 1, 'unit': '', 'pair': 3073, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        3075: {'name': 'load_energy_today_high', 'scale': 1, 'unit': '', 'pair': 3076},
        3076: {'name': 'load_energy_today_low', 'scale': 1, 'unit': '', 'pair': 3075, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        3077: {'name': 'load_energy_total_high', 'scale': 1, 'unit': '', 'pair': 3078},
        3078: {'name': 'load_energy_total_low', 'scale': 1, 'unit': '', 'pair': 3077, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        
        # Battery Diagnostics
        3086: {'name': 'battery_derating_mode', 'scale': 1, 'unit': ''},
        
        # Battery - Discharge/Charge Energy
        3125: {'name': 'battery_discharge_today_high', 'scale': 1, 'unit': '', 'pair': 3126},
        3126: {'name': 'battery_discharge_today_low', 'scale': 1, 'unit': '', 'pair': 3125, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        3127: {'name': 'battery_discharge_total_high', 'scale': 1, 'unit': '', 'pair': 3128},
        3128: {'name': 'battery_discharge_total_low', 'scale': 1, 'unit': '', 'pair': 3127, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        3129: {'name': 'battery_charge_today_high', 'scale': 1, 'unit': '', 'pair': 3130},
        3130: {'name': 'battery_charge_today_low', 'scale': 1, 'unit': '', 'pair': 3129, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        3131: {'name': 'battery_charge_total_high', 'scale': 1, 'unit': '', 'pair': 3132},
        3132: {'name': 'battery_charge_total_low', 'scale': 1, 'unit': '', 'pair': 3131, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        
        # Battery State
        3144: {'name': 'priority_mode', 'scale': 1, 'unit': '', 'desc': '0=Load, 1=Battery, 2=Grid'},
        3169: {'name': 'battery_voltage', 'scale': 0.01, 'unit': 'V'},
        3170: {'name': 'battery_current', 'scale': 0.1, 'unit': 'A', 'signed': True},
        3171: {'name': 'battery_soc', 'scale': 1, 'unit': '%'},
        3176: {'name': 'battery_temp', 'scale': 0.1, 'unit': '°C'},

        # NOTE: Registers 3178-3180 don't exist on some MOD hardware
        # If your inverter doesn't have these, battery power will be calculated from V×I
        # Battery Power (32-bit) - OPTIONAL, may not exist on all MOD hardware
        3178: {'name': 'discharge_power_high', 'scale': 1, 'unit': '', 'pair': 3179},
        3179: {'name': 'discharge_power_low', 'scale': 1, 'unit': '', 'pair': 3178, 'combined_scale': 0.1, 'combined_unit': 'W'},
        3180: {'name': 'charge_power_high', 'scale': 1, 'unit': '', 'pair': 3181},
        3181: {'name': 'charge_power_low', 'scale': 1, 'unit': '', 'pair': 3180, 'combined_scale': 0.1, 'combined_unit': 'W'},
    },
    'holding_registers': {
        # Basic control
        0: {'name': 'on_off', 'scale': 1, 'unit': '', 'access': 'RW', 'desc': '0=Off, 1=On'},
        3: {'name': 'active_power_rate', 'scale': 1, 'unit': '%', 'access': 'RW', 'desc': 'Max output power %'},
        30: {'name': 'modbus_address', 'scale': 1, 'unit': '', 'access': 'RW', 'desc': 'Modbus address 1-254'},
        
        # Export Control Registers
        122: {
            'name': 'export_limit_mode',
            'scale': 1,
            'unit': '',
            'access': 'RW',
            'desc': 'Export limit control mode',
            'valid_range': (0, 3),
            'values': {
                0: 'Export limit disabled',
                1: 'Enable 485 (external meter) limitation',
                2: 'Enable 232 (external meter) limitation',
                3: 'CT export limit'
            }
        },
        123: {
            'name': 'export_limit_power',
            'scale': 0.1,
            'unit': '%',
            'access': 'RW',
            'desc': 'Export limit power percentage',
            'valid_range': (0, 1000),
            'note': '0=0%, 1000=100.0%'
        },
    }
}

# Export all MOD profiles
MOD_REGISTER_MAPS = {
    'MOD_6000_15000TL3_XH': MOD_6000_15000TL3_XH,
}