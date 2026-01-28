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
        93: {'name': 'inverter_temp', 'scale': 0.1, 'unit': '°C', 'signed': True},
        94: {'name': 'ipm_temp', 'scale': 0.1, 'unit': '°C', 'signed': True},
        95: {'name': 'boost_temp', 'scale': 0.1, 'unit': '°C', 'signed': True},

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
        
        # Battery - Discharge/Charge Energy (3000 range - PRIMARY for MOD XH)
        # Note: Order is discharge first, then charge (different from VPP which is charge first)
        3125: {'name': 'discharge_energy_today_high', 'scale': 1, 'unit': '', 'pair': 3126, 'desc': 'Battery discharge energy today (primary source for MOD XH)'},
        3126: {'name': 'discharge_energy_today_low', 'scale': 1, 'unit': '', 'pair': 3125, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        3127: {'name': 'discharge_energy_total_high', 'scale': 1, 'unit': '', 'pair': 3128, 'desc': 'Battery discharge energy total (primary source for MOD XH)'},
        3128: {'name': 'discharge_energy_total_low', 'scale': 1, 'unit': '', 'pair': 3127, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        3129: {'name': 'charge_energy_today_high', 'scale': 1, 'unit': '', 'pair': 3130, 'desc': 'Battery charge energy today (primary source for MOD XH)'},
        3130: {'name': 'charge_energy_today_low', 'scale': 1, 'unit': '', 'pair': 3129, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        3131: {'name': 'charge_energy_total_high', 'scale': 1, 'unit': '', 'pair': 3132, 'desc': 'Battery charge energy total (primary source for MOD XH)'},
        3132: {'name': 'charge_energy_total_low', 'scale': 1, 'unit': '', 'pair': 3131, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        
        # Battery State (3000 range - PRIMARY for MOD XH with ARK battery)
        # Note: VPP 31200+ range doesn't respond on MOD 10000TL3-XH, so 3000+ is primary
        3144: {'name': 'priority_mode', 'scale': 1, 'unit': '', 'desc': '0=Load, 1=Battery, 2=Grid'},
        3169: {'name': 'battery_voltage', 'scale': 0.01, 'unit': 'V', 'desc': 'Battery voltage (primary source for MOD XH)'},
        3170: {'name': 'battery_current', 'scale': 0.1, 'unit': 'A', 'signed': True, 'desc': 'Battery current (primary source for MOD XH)'},
        3171: {'name': 'battery_soc', 'scale': 1, 'unit': '%', 'desc': 'Battery SOC (primary source for MOD XH)'},
        3176: {'name': 'battery_temp', 'scale': 0.1, 'unit': '°C', 'signed': True, 'desc': 'Battery temperature (primary source for MOD XH)'},

        # Battery Power (3000 range - separate charge/discharge registers)
        # These follow the MIN TL-XH pattern for ARK battery systems
        3178: {'name': 'discharge_power_high', 'scale': 1, 'unit': '', 'pair': 3179, 'desc': 'Battery discharge power HIGH (unsigned)'},
        3179: {'name': 'discharge_power_low', 'scale': 1, 'unit': '', 'pair': 3178, 'combined_scale': 0.1, 'combined_unit': 'W', 'desc': 'Battery discharge power (unsigned, positive=discharging)'},
        3180: {'name': 'charge_power_high', 'scale': 1, 'unit': '', 'pair': 3181, 'desc': 'Battery charge power HIGH (unsigned)'},
        3181: {'name': 'charge_power_low', 'scale': 1, 'unit': '', 'pair': 3180, 'combined_scale': 0.1, 'combined_unit': 'W', 'desc': 'Battery charge power (unsigned, positive=charging)'},

        # === BATTERY INFORMATION 1 (31200-31299) - Official VPP Protocol V2.01 ===
        # This is the official battery data range for MOD series per Growatt VPP Protocol
        # Ref: GROWATT VPP COMMUNICATION PROTOCOL OF INVERTER V2.01 (2024.9.20)

        # Battery Power (signed: positive=charging, negative=discharging)
        31200: {'name': 'battery_power_high', 'scale': 1, 'unit': '', 'pair': 31201},
        31201: {'name': 'battery_power_low', 'scale': 1, 'unit': '', 'pair': 31200, 'combined_scale': 0.1, 'combined_unit': 'W', 'signed': True},

        # Battery Energy (VPP range - NOT responding on MOD 10000TL3-XH, kept for other MOD variants)
        # Renamed with _vpp suffix to avoid conflict with 3000+ range (primary source)
        # Note: VPP protocol lists charge first, then discharge (opposite of 3000+ range)
        31202: {'name': 'charge_energy_today_vpp_high', 'scale': 1, 'unit': '', 'pair': 31203},
        31203: {'name': 'charge_energy_today_vpp_low', 'scale': 1, 'unit': '', 'pair': 31202, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        31204: {'name': 'charge_energy_total_vpp_high', 'scale': 1, 'unit': '', 'pair': 31205},
        31205: {'name': 'charge_energy_total_vpp_low', 'scale': 1, 'unit': '', 'pair': 31204, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        31206: {'name': 'discharge_energy_today_vpp_high', 'scale': 1, 'unit': '', 'pair': 31207},
        31207: {'name': 'discharge_energy_today_vpp_low', 'scale': 1, 'unit': '', 'pair': 31206, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        31208: {'name': 'discharge_energy_total_vpp_high', 'scale': 1, 'unit': '', 'pair': 31209},
        31209: {'name': 'discharge_energy_total_vpp_low', 'scale': 1, 'unit': '', 'pair': 31208, 'combined_scale': 0.1, 'combined_unit': 'kWh'},

        # Battery Power Limits
        31210: {'name': 'battery_max_charge_power_high', 'scale': 1, 'unit': '', 'pair': 31211},
        31211: {'name': 'battery_max_charge_power_low', 'scale': 1, 'unit': '', 'pair': 31210, 'combined_scale': 0.1, 'combined_unit': 'W'},
        31212: {'name': 'battery_max_discharge_power_high', 'scale': 1, 'unit': '', 'pair': 31213},
        31213: {'name': 'battery_max_discharge_power_low', 'scale': 1, 'unit': '', 'pair': 31212, 'combined_scale': 0.1, 'combined_unit': 'W'},

        # Battery State (VPP range - NOT responding on MOD 10000TL3-XH, kept for other MOD variants)
        # Renamed with _vpp suffix to avoid conflict with 3000+ range (primary source)
        31214: {'name': 'battery_voltage_vpp', 'scale': 0.1, 'unit': 'V', 'signed': True, 'desc': 'Battery voltage (VPP range, may not respond on XH variants)'},
        31215: {'name': 'battery_current_vpp_high', 'scale': 1, 'unit': '', 'pair': 31216},
        31216: {'name': 'battery_current_vpp_low', 'scale': 1, 'unit': '', 'pair': 31215, 'combined_scale': 0.1, 'combined_unit': 'A', 'signed': True},
        31217: {'name': 'battery_soc_vpp', 'scale': 1, 'unit': '%', 'desc': 'Battery SOC (VPP range, may not respond on XH variants)'},
        31218: {'name': 'battery_soh', 'scale': 1, 'unit': '%'},

        # Battery Capacity
        31219: {'name': 'battery_fcc_high', 'scale': 1, 'unit': '', 'pair': 31220},
        31220: {'name': 'battery_fcc_low', 'scale': 1, 'unit': '', 'pair': 31219, 'combined_scale': 1, 'combined_unit': 'Ah'},

        # Battery Temperature (VPP range)
        31223: {'name': 'battery_temp_vpp', 'scale': 0.1, 'unit': '°C', 'signed': True, 'desc': 'Battery temp (VPP range, may not respond on XH variants)'},

        # Battery System Info
        31225: {'name': 'battery_cluster_sum', 'scale': 1, 'unit': ''},
        31226: {'name': 'battery_module_number', 'scale': 1, 'unit': ''},
        31227: {'name': 'battery_module_rated_voltage', 'scale': 0.1, 'unit': 'V'},
        31228: {'name': 'battery_module_rated_capacity', 'scale': 0.1, 'unit': 'Ah'},

        # === BATTERY CLUSTER 2 (31300-31399) - VPP Protocol V2.01 ===
        # Battery 2 Power (signed: positive=charging, negative=discharging)
        31300: {'name': 'battery2_power_high', 'scale': 1, 'unit': '', 'pair': 31301},
        31301: {'name': 'battery2_power', 'scale': 1, 'unit': '', 'pair': 31300, 'combined_scale': 0.1, 'combined_unit': 'W', 'signed': True},

        # Battery 2 Energy
        31302: {'name': 'battery2_charge_energy_today_high', 'scale': 1, 'unit': '', 'pair': 31303},
        31303: {'name': 'battery2_charge_energy_today_low', 'scale': 1, 'unit': '', 'pair': 31302, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        31304: {'name': 'battery2_charge_energy_total_high', 'scale': 1, 'unit': '', 'pair': 31305},
        31305: {'name': 'battery2_charge_energy_total_low', 'scale': 1, 'unit': '', 'pair': 31304, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        31306: {'name': 'battery2_discharge_energy_today_high', 'scale': 1, 'unit': '', 'pair': 31307},
        31307: {'name': 'battery2_discharge_energy_today_low', 'scale': 1, 'unit': '', 'pair': 31306, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        31308: {'name': 'battery2_discharge_energy_total_high', 'scale': 1, 'unit': '', 'pair': 31309},
        31309: {'name': 'battery2_discharge_energy_total_low', 'scale': 1, 'unit': '', 'pair': 31308, 'combined_scale': 0.1, 'combined_unit': 'kWh'},

        # Battery 2 State
        31314: {'name': 'battery2_voltage', 'scale': 0.1, 'unit': 'V', 'signed': True},
        31315: {'name': 'battery2_current_high', 'scale': 1, 'unit': '', 'pair': 31316},
        31316: {'name': 'battery2_current_low', 'scale': 1, 'unit': '', 'pair': 31315, 'combined_scale': 0.1, 'combined_unit': 'A', 'signed': True},
        31317: {'name': 'battery2_soc', 'scale': 1, 'unit': '%'},
        31318: {'name': 'battery2_soh', 'scale': 1, 'unit': '%'},
        31323: {'name': 'battery2_temp', 'scale': 0.1, 'unit': '°C', 'signed': True},

        # === V2.01 VPP ADDITIONAL REGISTERS ===
        # Grid/Meter Power (same as PtoGrid at 3043/3044)
        31112: {'name': 'meter_power_high', 'scale': 1, 'unit': '', 'pair': 31113, 'maps_to': 'power_to_grid', 'desc': 'Meter power (same as PtoGrid)'},
        31113: {'name': 'meter_power_low', 'scale': 1, 'unit': '', 'pair': 31112, 'combined_scale': 0.1, 'combined_unit': 'W', 'signed': True},

        # Load Power (same as PtoLoad at 3045/3046)
        31118: {'name': 'load_power_high_vpp', 'scale': 1, 'unit': '', 'pair': 31119, 'maps_to': 'power_to_load'},
        31119: {'name': 'load_power_low_vpp', 'scale': 1, 'unit': '', 'pair': 31118, 'combined_scale': 0.1, 'combined_unit': 'W'},

        # Status
        31000: {'name': 'equipment_status', 'scale': 1, 'unit': '', 'desc': 'Equipment running status'},
        31001: {'name': 'battery_working_status', 'scale': 1, 'unit': '', 'desc': '0=Idle, 1=Charge, 2=Discharge, 3=Fault, 4=Standby, 5=Shutdown'},
    },
    'holding_registers': {
        # Basic control
        0: {'name': 'on_off', 'scale': 1, 'unit': '', 'access': 'RW', 'desc': '0=Off, 1=On'},
        3: {'name': 'active_power_rate', 'scale': 1, 'unit': '%', 'access': 'RW', 'desc': 'Max output power %'},
        30: {'name': 'modbus_address', 'scale': 1, 'unit': '', 'access': 'RW', 'desc': 'Modbus address 1-254'},

        # Device identification
        30000: {'name': 'dtc_code', 'scale': 1, 'unit': '', 'access': 'RO', 'desc': 'Device Type Code: 5400 for MOD-XH/MID-XH', 'default': 5400},
        30099: {'name': 'protocol_version', 'scale': 1, 'unit': '', 'access': 'RO', 'desc': 'VPP Protocol version (201 = V2.01)', 'default': 201},

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

# MOD-6000-15000TL3-X (Three-phase grid-tied WITHOUT battery)
MOD_6000_15000TL3_X = {
    'name': 'MOD TL3-X Series (Grid-Tied)',
    'description': 'Modular three-phase grid-tied inverter without battery (6-15kW)',
    'notes': 'Uses 0-124 base range only. Grid-tied version without battery storage.',
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

        # PV String 3
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

        # Generic AC aliases (point to Phase R for compatibility)
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

        # Energy Today (32-bit)
        53: {'name': 'energy_today_high', 'scale': 1, 'unit': '', 'pair': 54},
        54: {'name': 'energy_today_low', 'scale': 1, 'unit': '', 'pair': 53, 'combined_scale': 0.1, 'combined_unit': 'kWh'},

        # Energy Total (32-bit)
        55: {'name': 'energy_total_high', 'scale': 1, 'unit': '', 'pair': 56},
        56: {'name': 'energy_total_low', 'scale': 1, 'unit': '', 'pair': 55, 'combined_scale': 0.1, 'combined_unit': 'kWh'},

        # Temperatures
        93: {'name': 'inverter_temp', 'scale': 0.1, 'unit': '°C', 'signed': True},
        94: {'name': 'ipm_temp', 'scale': 0.1, 'unit': '°C', 'signed': True},
        95: {'name': 'boost_temp', 'scale': 0.1, 'unit': '°C', 'signed': True},

        # Status
        100: {'name': 'power_factor', 'scale': 1, 'unit': ''},
        104: {'name': 'derating_mode', 'scale': 1, 'unit': ''},
        105: {'name': 'fault_code', 'scale': 1, 'unit': ''},
        112: {'name': 'warning_code', 'scale': 1, 'unit': ''},
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
    'MOD_6000_15000TL3_X': MOD_6000_15000TL3_X,
    'MOD_6000_15000TL3_XH': MOD_6000_15000TL3_XH,
}