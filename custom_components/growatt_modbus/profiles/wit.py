"""
WIT Series - Three-Phase Hybrid Inverters with Advanced Storage
Based on legacy Growatt Modbus Protocol

NOTE (WIT-specific):
- WIT uses base input ranges 0-249, optional 875-999, and battery block 8000-8124
- VPP / cluster data is in 31xxx range (typically HOLDING registers), e.g. 31200-31223
  -> These MUST be under holding_registers for most Modbus integrations, otherwise they won't be read.
"""

# WIT 4000-15000TL3 (Three-phase hybrid with battery, 4-15kW residential)
WIT_4000_15000TL3 = {
    'name': 'WIT 4-15kW Hybrid',
    'description': 'Three-phase hybrid inverter with battery storage and UPS/EPS backup (4-15kW)',
    'notes': (
        'Uses 0-124, 125-249, 875-999, 8000-8124 and VPP (31000-31399) register ranges. '
        'Battery data mapped to 8000-8124 range; battery temperature seen at 31222/31223 (VPP block). '
        'Features: UPS 10ms switching, time-of-use programming, VPP/demand management.'
    ),

    'input_registers': {
        # ============================================================================
        # BASE RANGE 0-124: PV, AC, and System Status (same as SPH-TL3)
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

        # Output Power (Total)
        35: {'name': 'ac_power_high', 'alias': 'output_power_high', 'scale': 1, 'unit': '', 'pair': 36, 'signed': True},
        36: {'name': 'ac_power_low', 'alias': 'output_power_low', 'scale': 1, 'unit': '', 'pair': 35, 'combined_scale': 0.1, 'combined_unit': 'W', 'signed': True},

        # AC Grid Frequency
        37: {'name': 'ac_frequency', 'scale': 0.01, 'unit': 'Hz'},

        # Three-Phase AC Output - Phase R
        38: {'name': 'ac_voltage_r', 'alias': 'ac_voltage', 'scale': 0.1, 'unit': 'V', 'desc': 'Phase R voltage'},
        39: {'name': 'ac_current_r', 'alias': 'ac_current', 'scale': 0.1, 'unit': 'A', 'desc': 'Phase R current'},
        40: {'name': 'ac_power_r_high', 'scale': 1, 'unit': '', 'pair': 41, 'signed': True},
        41: {'name': 'ac_power_r_low', 'scale': 1, 'unit': '', 'pair': 40, 'combined_scale': 0.1, 'combined_unit': 'W', 'signed': True},

        # Three-Phase AC Output - Phase S
        42: {'name': 'ac_voltage_s', 'scale': 0.1, 'unit': 'V', 'desc': 'Phase S voltage'},
        43: {'name': 'ac_current_s', 'scale': 0.1, 'unit': 'A', 'desc': 'Phase S current'},
        44: {'name': 'ac_power_s_high', 'scale': 1, 'unit': '', 'pair': 45, 'signed': True},
        45: {'name': 'ac_power_s_low', 'scale': 1, 'unit': '', 'pair': 44, 'combined_scale': 0.1, 'combined_unit': 'W', 'signed': True},

        # Three-Phase AC Output - Phase T
        46: {'name': 'ac_voltage_t', 'scale': 0.1, 'unit': 'V', 'desc': 'Phase T voltage'},
        47: {'name': 'ac_current_t', 'scale': 0.1, 'unit': 'A', 'desc': 'Phase T current'},
        48: {'name': 'ac_power_t_high', 'scale': 1, 'unit': '', 'pair': 49, 'signed': True},
        49: {'name': 'ac_power_t_low', 'scale': 1, 'unit': '', 'pair': 48, 'combined_scale': 0.1, 'combined_unit': 'W', 'signed': True},

        # Line-to-Line Voltages
        50: {'name': 'line_voltage_rs', 'scale': 0.1, 'unit': 'V', 'desc': 'Line voltage R-S'},
        51: {'name': 'line_voltage_st', 'scale': 0.1, 'unit': 'V', 'desc': 'Line voltage S-T'},
        52: {'name': 'line_voltage_tr', 'scale': 0.1, 'unit': 'V', 'desc': 'Line voltage T-R'},

        # Energy
        53: {'name': 'energy_today_high', 'scale': 1, 'unit': '', 'pair': 54},
        54: {'name': 'energy_today_low', 'scale': 1, 'unit': '', 'pair': 53, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
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

        # ============================================================================
        # EXTENDED RANGE 125-249: Grid Support and Advanced Features
        # ============================================================================

        # Inverter Type (ASCII string)
        125: {'name': 'inv_type_1', 'scale': 1, 'unit': '', 'desc': 'Inverter type character 1-2'},
        126: {'name': 'inv_type_2', 'scale': 1, 'unit': '', 'desc': 'Inverter type character 3-4'},
        127: {'name': 'inv_type_3', 'scale': 1, 'unit': '', 'desc': 'Inverter type character 5-6'},
        128: {'name': 'inv_type_4', 'scale': 1, 'unit': '', 'desc': 'Inverter type character 7-8'},

        # Reactive Power Control
        137: {'name': 'reactive_power_high', 'scale': 1, 'unit': '', 'pair': 138},
        138: {'name': 'reactive_power_low', 'scale': 1, 'unit': '', 'pair': 137, 'combined_scale': 0.1, 'combined_unit': 'var'},

        # Grid Support Features
        152: {'name': 'underfreq_load_start', 'scale': 0.01, 'unit': 'Hz', 'desc': 'Underfrequency load start point'},
        153: {'name': 'underfreq_load_end', 'scale': 0.01, 'unit': 'Hz', 'desc': 'Underfrequency load end point'},
        154: {'name': 'overfreq_load_start', 'scale': 0.01, 'unit': 'Hz', 'desc': 'Overfrequency load start point'},
        155: {'name': 'overfreq_load_end', 'scale': 0.01, 'unit': 'Hz', 'desc': 'Overfrequency load end point'},
        156: {'name': 'undervolt_load_start', 'scale': 0.1, 'unit': 'V', 'desc': 'Undervoltage load start point'},
        157: {'name': 'undervolt_load_end', 'scale': 0.1, 'unit': 'V', 'desc': 'Undervoltage load end point'},
        158: {'name': 'overvolt_load_start', 'scale': 0.1, 'unit': 'V', 'desc': 'Overvoltage load start point'},
        159: {'name': 'overvolt_load_end', 'scale': 0.1, 'unit': 'V', 'desc': 'Overvoltage load end point'},

        # Intelligent Control
        180: {'name': 'meter_link', 'scale': 1, 'unit': '', 'desc': '0=Missed, 1=Received'},
        181: {'name': 'optimizer_count', 'scale': 1, 'unit': '', 'desc': 'Number of optimizers connected (0-64)'},
        183: {'name': 'pv_string_scan', 'scale': 1, 'unit': '', 'desc': 'String scanning: 0=Not support, 8/16/32=Num strings'},
        184: {'name': 'bdc_parallel_num', 'scale': 1, 'unit': '', 'desc': 'Number of BDC units in parallel'},
        185: {'name': 'battery_pack_count', 'scale': 1, 'unit': '', 'desc': 'Total battery modules connected'},
        187: {'name': 'vpp_function_status', 'scale': 1, 'unit': '', 'desc': '0=Disabled, 1=Enabled'},
        188: {'name': 'datalog_server_status', 'scale': 1, 'unit': '', 'desc': '0=Connected, 1=Failed'},

        # ============================================================================
        # Battery Range (8000-8124)
        # ============================================================================
        8034: {'name': 'battery_voltage', 'scale': 0.1, 'unit': 'V'},
        8035: {'name': 'battery_current', 'scale': 0.1, 'unit': 'A', 'signed': True},
        8093: {'name': 'battery_soc', 'scale': 1, 'unit': '%'},
        8094: {'name': 'battery_soh', 'scale': 1, 'unit': '%'},

        # ============================================================================
        # Power flow / consumption (8045-8086)
        # ============================================================================
        8045: {'name': 'self_consumption_power_high', 'scale': 1, 'unit': '', 'pair': 8046},
        8046: {'name': 'self_consumption_power_low', 'scale': 1, 'unit': '', 'pair': 8045, 'combined_scale': 0.1, 'combined_unit': 'W'},

        8063: {'name': 'self_output_energy_today_high', 'scale': 1, 'unit': '', 'pair': 8064},
        8064: {'name': 'self_output_energy_today_low', 'scale': 1, 'unit': '', 'pair': 8063, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        8065: {'name': 'self_output_energy_total_high', 'scale': 1, 'unit': '', 'pair': 8066},
        8066: {'name': 'self_output_energy_total_low', 'scale': 1, 'unit': '', 'pair': 8065, 'combined_scale': 0.1, 'combined_unit': 'kWh'},

        8067: {'name': 'energy_to_user_today_high', 'scale': 1, 'unit': '', 'pair': 8068},
        8068: {'name': 'energy_to_user_today_low', 'scale': 1, 'unit': '', 'pair': 8067, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        8069: {'name': 'energy_to_user_total_high', 'scale': 1, 'unit': '', 'pair': 8070},
        8070: {'name': 'energy_to_user_total_low', 'scale': 1, 'unit': '', 'pair': 8069, 'combined_scale': 0.1, 'combined_unit': 'kWh'},

        8071: {'name': 'energy_to_grid_today_high', 'scale': 1, 'unit': '', 'pair': 8072},
        8072: {'name': 'energy_to_grid_today_low', 'scale': 1, 'unit': '', 'pair': 8071, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        8073: {'name': 'energy_to_grid_total_high', 'scale': 1, 'unit': '', 'pair': 8074},
        8074: {'name': 'energy_to_grid_total_low', 'scale': 1, 'unit': '', 'pair': 8073, 'combined_scale': 0.1, 'combined_unit': 'kWh'},

        # Load Energy
        8075: {'name': 'load_energy_today_high', 'scale': 1, 'unit': '', 'pair': 8076},
        8076: {'name': 'load_energy_today_low', 'scale': 1, 'unit': '', 'pair': 8075, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        8077: {'name': 'load_energy_total_high', 'scale': 1, 'unit': '', 'pair': 8078},
        8078: {'name': 'load_energy_total_low', 'scale': 1, 'unit': '', 'pair': 8077, 'combined_scale': 0.1, 'combined_unit': 'kWh'},

        # Power Flow
        8079: {'name': 'power_to_load_high', 'scale': 1, 'unit': '', 'pair': 8080, 'desc': 'Total load power (Ptoload)'},
        8080: {'name': 'power_to_load_low', 'scale': 1, 'unit': '', 'pair': 8079, 'combined_scale': 0.1, 'combined_unit': 'W'},

        8081: {'name': 'power_to_user_high', 'scale': 1, 'unit': '', 'pair': 8082, 'desc': 'Total forward power (grid import)'},
        8082: {'name': 'power_to_user_low', 'scale': 1, 'unit': '', 'pair': 8081, 'combined_scale': 0.1, 'combined_unit': 'W'},

        8083: {'name': 'power_to_grid_high', 'scale': 1, 'unit': '', 'pair': 8084, 'desc': 'Total reverse power (grid export)'},
        8084: {'name': 'power_to_grid_low', 'scale': 1, 'unit': '', 'pair': 8083, 'combined_scale': 0.1, 'combined_unit': 'W'},

        8085: {'name': 'system_output_power_high', 'scale': 1, 'unit': '', 'pair': 8086},
        8086: {'name': 'system_output_power_low', 'scale': 1, 'unit': '', 'pair': 8085, 'combined_scale': 0.1, 'combined_unit': 'W'},
    },

    'holding_registers': {
        # ============================================================================
        # BASE RANGE 0-124: Basic Configuration
        # ============================================================================

        0: {'name': 'on_off', 'scale': 1, 'unit': '', 'access': 'RW', 'desc': '0=Off, 1=On'},
        3: {'name': 'active_power_rate', 'scale': 1, 'unit': '%', 'access': 'RW'},

        # Device identification
        30000: {'name': 'dtc_code', 'scale': 1, 'unit': '', 'access': 'RO', 'desc': 'Device Type Code: 5603 for WIT 4-15kW', 'default': 5603},
        30099: {'name': 'protocol_version', 'scale': 1, 'unit': '', 'access': 'RO', 'desc': 'VPP Protocol version (202 = V2.02)', 'default': 202},

        # ============================================================================
        # VPP BATTERY RANGE (31200-31223): Battery Cluster Data (READ-ONLY)
        # IMPORTANT: moved from input_registers -> holding_registers so charge/discharge totals appear.
        # ============================================================================

        # NOTE:
        # VPP spec says 0.1W, but WIT field testing shows 1.0W scale for 31200/31201.
        31200: {'name': 'battery_power_high', 'scale': 1, 'unit': '', 'access': 'RO', 'pair': 31201},
        31201: {'name': 'battery_power_low', 'scale': 1, 'unit': '', 'access': 'RO', 'pair': 31200, 'combined_scale': 1.0, 'combined_unit': 'W', 'signed': True},

        # 66: Daily charge of battery
        31202: {'name': 'charge_energy_today_high', 'scale': 1, 'unit': '', 'access': 'RO', 'pair': 31203},
        31203: {'name': 'charge_energy_today_low', 'scale': 1, 'unit': '', 'access': 'RO', 'pair': 31202, 'combined_scale': 0.1, 'combined_unit': 'kWh'},

        # 67: Cumulative charge of battery
        31204: {'name': 'charge_energy_total_high', 'scale': 1, 'unit': '', 'access': 'RO', 'pair': 31205},
        31205: {'name': 'charge_energy_total_low', 'scale': 1, 'unit': '', 'access': 'RO', 'pair': 31204, 'combined_scale': 0.1, 'combined_unit': 'kWh'},

        # 68: Daily discharge capacity of battery
        31206: {'name': 'discharge_energy_today_high', 'scale': 1, 'unit': '', 'access': 'RO', 'pair': 31207},
        31207: {'name': 'discharge_energy_today_low', 'scale': 1, 'unit': '', 'access': 'RO', 'pair': 31206, 'combined_scale': 0.1, 'combined_unit': 'kWh'},

        # 69: Cumulative discharge of battery
        31208: {'name': 'discharge_energy_total_high', 'scale': 1, 'unit': '', 'access': 'RO', 'pair': 31209},
        31209: {'name': 'discharge_energy_total_low', 'scale': 1, 'unit': '', 'access': 'RO', 'pair': 31208, 'combined_scale': 0.1, 'combined_unit': 'kWh'},

        # 70/71: limits
        31210: {'name': 'max_charge_power_high', 'scale': 1, 'unit': '', 'access': 'RO', 'pair': 31211},
        31211: {'name': 'max_charge_power_low', 'scale': 1, 'unit': '', 'access': 'RO', 'pair': 31210, 'combined_scale': 0.1, 'combined_unit': 'W'},

        31212: {'name': 'max_discharge_power_high', 'scale': 1, 'unit': '', 'access': 'RO', 'pair': 31213},
        31213: {'name': 'max_discharge_power_low', 'scale': 1, 'unit': '', 'access': 'RO', 'pair': 31212, 'combined_scale': 0.1, 'combined_unit': 'W'},

        # Cluster state
        31214: {'name': 'battery_voltage_vpp', 'scale': 0.1, 'unit': 'V', 'access': 'RO', 'maps_to': 'battery_voltage', 'signed': True},
        31215: {'name': 'battery_current_vpp', 'scale': 0.1, 'unit': 'A', 'access': 'RO', 'maps_to': 'battery_current', 'signed': True},
        31217: {'name': 'battery_soc_vpp', 'scale': 1, 'unit': '%', 'access': 'RO', 'maps_to': 'battery_soc'},
        31222: {'name': 'battery_temp_vpp', 'scale': 0.1, 'unit': '°C', 'access': 'RO', 'maps_to': 'battery_temp', 'signed': True},
        31223: {'name': 'battery_temp_alt', 'scale': 0.1, 'unit': '°C', 'access': 'RO', 'signed': True, 'desc': 'Alternative battery temp register'},

        # ============================================================================
        # EXTENDED RANGE 125-249: Advanced Grid Control
        # ============================================================================

        137: {'name': 'reactive_power_high', 'scale': 1, 'unit': '', 'access': 'RW', 'pair': 138},
        138: {'name': 'reactive_power_low', 'scale': 1, 'unit': '', 'access': 'RW', 'pair': 137, 'combined_scale': 0.1, 'combined_unit': 'var'},
        139: {'name': 'reactive_priority_enable', 'scale': 1, 'unit': '', 'access': 'RW', 'desc': '0=Disable, 1=Enable'},
        140: {'name': 'reactive_power_ratio', 'scale': 0.1, 'unit': '', 'access': 'RW'},
        141: {'name': 'svg_night_enable', 'scale': 1, 'unit': '', 'access': 'RW', 'desc': '0=Disable, 1=Enable'},

        142: {'name': 'underfreq_upload_point', 'scale': 0.01, 'unit': 'Hz', 'access': 'RW'},
        143: {'name': 'overfreq_derate_recover', 'scale': 0.01, 'unit': 'Hz', 'access': 'RW'},
        144: {'name': 'overfreq_derate_delay', 'scale': 0.05, 'unit': 's', 'access': 'RW', 'desc': '50ms steps, 0-30000'},
        148: {'name': 'hvolt_derate_high', 'scale': 0.1, 'unit': 'V', 'access': 'RW'},
        149: {'name': 'hvolt_derate_low', 'scale': 0.1, 'unit': 'V', 'access': 'RW'},

        152: {'name': 'underfreq_load_start_set', 'scale': 0.01, 'unit': 'Hz', 'access': 'RW'},
        153: {'name': 'underfreq_load_end_set', 'scale': 0.01, 'unit': 'Hz', 'access': 'RW'},
        154: {'name': 'overfreq_load_start_set', 'scale': 0.01, 'unit': 'Hz', 'access': 'RW'},
        155: {'name': 'overfreq_load_end_set', 'scale': 0.01, 'unit': 'Hz', 'access': 'RW'},
        156: {'name': 'undervolt_load_start_set', 'scale': 0.1, 'unit': 'V', 'access': 'RW'},
        157: {'name': 'undervolt_load_end_set', 'scale': 0.1, 'unit': 'V', 'access': 'RW'},
        158: {'name': 'overvolt_load_start_set', 'scale': 0.1, 'unit': 'V', 'access': 'RW'},
        159: {'name': 'overvolt_load_end_set', 'scale': 0.1, 'unit': 'V', 'access': 'RW'},

        180: {'name': 'meter_link_set', 'scale': 1, 'unit': '', 'access': 'RW', 'desc': '0=Missed, 1=Received'},
        181: {'name': 'optimizer_count_set', 'scale': 1, 'unit': '', 'access': 'RW', 'valid_range': (0, 64)},

        # PID Control
        201: {'name': 'pid_working_mode', 'scale': 1, 'unit': '', 'access': 'W', 'desc': '0=Auto, 1=Continuous, 2=All night'},
        202: {'name': 'pid_on_off', 'scale': 1, 'unit': '', 'access': 'W', 'desc': '0=On, 1=Off'},
        203: {'name': 'pid_voltage_option', 'scale': 1, 'unit': 'V', 'access': 'W', 'valid_range': (300, 1000)},

        # Serial Number (209-223, 2 chars per register)
        209: {'name': 'serial_1_2', 'scale': 1, 'unit': '', 'access': 'R'},
        210: {'name': 'serial_3_4', 'scale': 1, 'unit': '', 'access': 'R'},
        211: {'name': 'serial_5_6', 'scale': 1, 'unit': '', 'access': 'R'},
        212: {'name': 'serial_7_8', 'scale': 1, 'unit': '', 'access': 'R'},
        213: {'name': 'serial_9_10', 'scale': 1, 'unit': '', 'access': 'R'},
        214: {'name': 'serial_11_12', 'scale': 1, 'unit': '', 'access': 'R'},
        215: {'name': 'serial_13_14', 'scale': 1, 'unit': '', 'access': 'R'},
        216: {'name': 'serial_15_16', 'scale': 1, 'unit': '', 'access': 'R'},
        217: {'name': 'serial_17_18', 'scale': 1, 'unit': '', 'access': 'R'},
        218: {'name': 'serial_19_20', 'scale': 1, 'unit': '', 'access': 'R'},

        229: {'name': 'energy_adjust', 'scale': 0.1, 'unit': '%', 'access': 'RW', 'valid_range': (1, 1000)},

        230: {'name': 'island_disable', 'scale': 1, 'unit': '', 'access': 'W', 'desc': '0=Enable, 1=Disable'},
        236: {'name': 'nonstd_vac_enable', 'scale': 1, 'unit': '', 'access': 'W', 'desc': '0=Disable, 1=Grade1, 2=Grade2'},

        871: {'name': 'grid_phase_sequence', 'scale': 1, 'unit': '', 'access': 'RW', 'desc': '0=Positive, 1=Reverse'},
        874: {'name': 'parallel_enable', 'scale': 1, 'unit': '', 'access': 'RW', 'desc': '0=Disable, 1=Enable'},

        # ============================================================================
        # BUSINESS STORAGE RANGE 875-999: Advanced Battery/Storage Features
        # ============================================================================

        875: {'name': 'ats_fw_build_5', 'scale': 1, 'unit': '', 'access': 'R', 'desc': 'ATS version (MB)'},
        876: {'name': 'ats_fw_build_4', 'scale': 1, 'unit': '', 'access': 'R', 'desc': 'ATS version (AA)'},
        877: {'name': 'ats_dsp1_fw_build', 'scale': 1, 'unit': '', 'access': 'R'},
        878: {'name': 'ats_dsp2_fw_build', 'scale': 1, 'unit': '', 'access': 'R'},

        879:
