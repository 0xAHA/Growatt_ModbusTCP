"""
WIT Series - Three-Phase Hybrid Inverters with Advanced Storage
Based on legacy Growatt Modbus Protocol
"""

# WIT 4000-15000TL3 (Three-phase hybrid with battery, 4-15kW residential)
WIT_4000_15000TL3 = {
    'name': 'WIT 4-15kW Hybrid',
    'description': 'Three-phase hybrid inverter with battery storage and UPS/EPS backup (4-15kW)',
    'notes': 'Uses 0-124, 125-249, 875-999, 8000-8124 and VPP (31000-31399) register ranges. Battery data mapped to 8000-8124 range; battery temperature seen at 31223 (VPP block). Features: UPS 10ms switching, time-of-use programming, VPP/demand management.',
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

        # Output Power
        35: {'name': 'ac_power_high', 'alias': 'output_power_high', 'scale': 1, 'unit': '', 'pair': 36},
        36: {'name': 'ac_power_low', 'alias': 'output_power_low', 'scale': 1, 'unit': '', 'pair': 35, 'combined_scale': 0.1, 'combined_unit': 'W'},

        # AC Grid Frequency
        37: {'name': 'ac_frequency', 'scale': 0.01, 'unit': 'Hz'},

        # Three-Phase AC Output - Phase R
        38: {'name': 'ac_voltage_r', 'alias': 'ac_voltage', 'scale': 0.1, 'unit': 'V', 'desc': 'Phase R voltage'},
        39: {'name': 'ac_current_r', 'alias': 'ac_current', 'scale': 0.1, 'unit': 'A', 'desc': 'Phase R current'},
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

        # Battery Range (8000-8124)
        8034: {'name': 'battery_voltage', 'scale': 0.1, 'unit': 'V'},
        8035: {'name': 'battery_current', 'scale': 0.1, 'unit': 'A', 'signed': True},
        8093: {'name': 'battery_soc', 'scale': 1, 'unit': '%'},
        8094: {'name': 'battery_soh', 'scale': 1, 'unit': '%'},

        # Battery temperature (VPP block observed on WIT)
        31223: {'name': 'battery_temp', 'scale': 0.1, 'unit': '°C', 'signed': True},

        # Power flow / consumption (8045-8086)
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

        8077: {'name': 'load_energy_today_high', 'scale': 1, 'unit': '', 'pair': 8078},
        8078: {'name': 'load_energy_today_low', 'scale': 1, 'unit': '', 'pair': 8077, 'combined_scale': 0.1, 'combined_unit': 'kWh'},

        8079: {'name': 'power_to_load_high', 'scale': 1, 'unit': '', 'pair': 8080},
        8080: {'name': 'power_to_load_low', 'scale': 1, 'unit': '', 'pair': 8079, 'combined_scale': 0.1, 'combined_unit': 'W'},

        8081: {'name': 'power_to_user_high', 'scale': 1, 'unit': '', 'pair': 8082},
        8082: {'name': 'power_to_user_low', 'scale': 1, 'unit': '', 'pair': 8081, 'combined_scale': 0.1, 'combined_unit': 'W'},

        8083: {'name': 'power_to_grid_high', 'scale': 1, 'unit': '', 'pair': 8084},
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

        # ============================================================================
        # EXTENDED RANGE 125-249: Advanced Grid Control
        # ============================================================================

        # Reactive Power Control
        137: {'name': 'reactive_power_high', 'scale': 1, 'unit': '', 'access': 'RW', 'pair': 138},
        138: {'name': 'reactive_power_low', 'scale': 1, 'unit': '', 'access': 'RW', 'pair': 137, 'combined_scale': 0.1, 'combined_unit': 'var'},
        139: {'name': 'reactive_priority_enable', 'scale': 1, 'unit': '', 'access': 'RW', 'desc': '0=Disable, 1=Enable'},
        140: {'name': 'reactive_power_ratio', 'scale': 0.1, 'unit': '', 'access': 'RW'},
        141: {'name': 'svg_night_enable', 'scale': 1, 'unit': '', 'access': 'RW', 'desc': '0=Disable, 1=Enable'},

        # Frequency/Voltage Derating
        142: {'name': 'underfreq_upload_point', 'scale': 0.01, 'unit': 'Hz', 'access': 'RW'},
        143: {'name': 'overfreq_derate_recover', 'scale': 0.01, 'unit': 'Hz', 'access': 'RW'},
        144: {'name': 'overfreq_derate_delay', 'scale': 0.05, 'unit': 's', 'access': 'RW', 'desc': '50ms steps, 0-30000'},
        148: {'name': 'hvolt_derate_high', 'scale': 0.1, 'unit': 'V', 'access': 'RW'},
        149: {'name': 'hvolt_derate_low', 'scale': 0.1, 'unit': 'V', 'access': 'RW'},

        # Grid Support Settings
        152: {'name': 'underfreq_load_start_set', 'scale': 0.01, 'unit': 'Hz', 'access': 'RW'},
        153: {'name': 'underfreq_load_end_set', 'scale': 0.01, 'unit': 'Hz', 'access': 'RW'},
        154: {'name': 'overfreq_load_start_set', 'scale': 0.01, 'unit': 'Hz', 'access': 'RW'},
        155: {'name': 'overfreq_load_end_set', 'scale': 0.01, 'unit': 'Hz', 'access': 'RW'},
        156: {'name': 'undervolt_load_start_set', 'scale': 0.1, 'unit': 'V', 'access': 'RW'},
        157: {'name': 'undervolt_load_end_set', 'scale': 0.1, 'unit': 'V', 'access': 'RW'},
        158: {'name': 'overvolt_load_start_set', 'scale': 0.1, 'unit': 'V', 'access': 'RW'},
        159: {'name': 'overvolt_load_end_set', 'scale': 0.1, 'unit': 'V', 'access': 'RW'},

        # Intelligent Control
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

        # Energy Adjustment
        229: {'name': 'energy_adjust', 'scale': 0.1, 'unit': '%', 'access': 'RW', 'valid_range': (1, 1000)},

        # Debug Settings (230-249)
        230: {'name': 'island_disable', 'scale': 1, 'unit': '', 'access': 'W', 'desc': '0=Enable, 1=Disable'},
        236: {'name': 'nonstd_vac_enable', 'scale': 1, 'unit': '', 'access': 'W', 'desc': '0=Disable, 1=Grade1, 2=Grade2'},

		# Grid Phase Sequence
        871: {'name': 'grid_phase_sequence', 'scale': 1, 'unit': '', 'access': 'RW', 'desc': '0=Positive, 1=Reverse'},
		
		# Parallel Enable
        874: {'name': 'parallel_enable', 'scale': 1, 'unit': '', 'access': 'RW', 'desc': '0=Disable, 1=Enable'},

        # ============================================================================
        # BUSINESS STORAGE RANGE 875-999: Advanced Battery/Storage Features
        # ============================================================================

        # Firmware Versions (ATS - Automatic Transfer Switch)
        875: {'name': 'ats_fw_build_5', 'scale': 1, 'unit': '', 'access': 'R', 'desc': 'ATS version (MB)'},
        876: {'name': 'ats_fw_build_4', 'scale': 1, 'unit': '', 'access': 'R', 'desc': 'ATS version (AA)'},
        877: {'name': 'ats_dsp1_fw_build', 'scale': 1, 'unit': '', 'access': 'R'},
        878: {'name': 'ats_dsp2_fw_build', 'scale': 1, 'unit': '', 'access': 'R'},

        # System Control
        879: {'name': 'product_set_enable', 'scale': 1, 'unit': '', 'access': 'RW', 'desc': '0=Disable, 1=Enable'},
        897: {'name': 'grid_reconnect_wait_time', 'scale': 1, 'unit': 's', 'access': 'RW', 'valid_range': (0, 65536), 'desc': 'Default 300s'},
        900: {'name': 'sts_enable', 'scale': 1, 'unit': '', 'access': 'RW', 'desc': '0=Disable, 1=Enable'},
        901: {'name': 'oil_engine_enable', 'scale': 1, 'unit': '', 'access': 'RW', 'desc': '0=Disable, 1=Enable'},

        # Operation Mode
        902: {'name': 'onoff_change_mode', 'scale': 1, 'unit': '', 'access': 'RW', 'desc': '0=-H, 1=-EP, 2=-UP',
              'values': {0: 'Hybrid (-H)', 1: 'Economy (-EP)', 2: 'UPS (-UP)'}},
        903: {'name': 'pcs_type', 'scale': 1, 'unit': '', 'access': 'RW',
              'values': {0: 'All-in-one storage', 1: 'Energy storage machine'}},

        # Battery Configuration
        904: {'name': 'battery_type', 'scale': 1, 'unit': '', 'access': 'RW',
              'values': {0: 'Direct attach', 1: 'DC-DC'}},
        905: {'name': 'ac_charge_power_rate', 'scale': 1, 'unit': '%', 'access': 'RW', 'valid_range': (0, 100)},
        906: {'name': 'battery_max_charge_voltage', 'scale': 0.1, 'unit': 'V', 'access': 'RW'},
        907: {'name': 'battery_eod_voltage', 'scale': 0.1, 'unit': 'V', 'access': 'RW', 'desc': 'End of discharge voltage'},
        910: {'name': 'battery_max_charge_current', 'scale': 0.1, 'unit': 'A', 'access': 'RW'},
        911: {'name': 'battery_max_discharge_current', 'scale': 0.1, 'unit': 'A', 'access': 'RW'},
        917: {'name': 'battery_capacity', 'scale': 1, 'unit': 'Ah', 'access': 'RW'},

        # Grid Connection Mode
        908: {'name': 'ongrid_phase_mode', 'scale': 1, 'unit': '', 'access': 'RW',
              'values': {0: '3P3W (3-phase 3-wire)', 1: '3P4W (3-phase 4-wire)'}},
        909: {'name': 'offgrid_phase_mode', 'scale': 1, 'unit': '', 'access': 'RW',
              'values': {0: '3P3W (3-phase 3-wire)', 1: '3P4W (3-phase 4-wire)'}},

        # Grid/Battery Switching
        912: {'name': 'ongrid_offgrid_mode', 'scale': 1, 'unit': '', 'access': 'RW',
              'values': {0: 'Auto', 1: 'Manual'}},
        913: {'name': 'ongrid_offgrid_set', 'scale': 1, 'unit': '', 'access': 'RW',
              'desc': 'Manual mode only', 'values': {0: 'On-grid', 1: 'Off-grid'}},
        914: {'name': 'offgrid_softstart_enable', 'scale': 1, 'unit': '', 'access': 'RW', 'desc': '0=Disable, 1=Enable'},
        915: {'name': 'offgrid_softstart_time', 'scale': 0.1, 'unit': 's', 'access': 'RW', 'valid_range': (2, 20)},

        # VPP/Power Dispatch
        918: {'name': 'vpp_enable', 'scale': 1, 'unit': '', 'access': 'RW', 'desc': '0=Disable, 1=Enable'},
        919: {'name': 'vpp_active_power_set', 'scale': 0.1, 'unit': 'kW', 'access': 'RW'},

        # Off-grid Settings
        936: {'name': 'offgrid_voltage', 'scale': 1, 'unit': '', 'access': 'RW',
              'values': {0: '220V', 1: '230V', 2: '240V', 3: '277V', 4: '127V'}},
        937: {'name': 'offgrid_frequency', 'scale': 1, 'unit': '', 'access': 'RW',
              'values': {0: '50Hz', 1: '60Hz'}},
        938: {'name': 'load_pv_inverter', 'scale': 1, 'unit': '', 'access': 'RW',
              'desc': 'PCS load port has inverter', 'values': {0: 'No', 1: 'Yes'}},
        939: {'name': 'dg_start_soc', 'scale': 1, 'unit': '%', 'access': 'RW', 'desc': 'SOC to start oil engine'},
        940: {'name': 'dg_stop_soc', 'scale': 1, 'unit': '%', 'access': 'RW', 'desc': 'SOC to stop oil engine'},

        # Demand Management
        944: {'name': 'demand_discharge_limit', 'scale': 1, 'unit': 'kW', 'access': 'RW'},
        945: {'name': 'demand_charge_limit', 'scale': 1, 'unit': 'kW', 'access': 'RW'},
        946: {'name': 'demand_manage_enable', 'scale': 1, 'unit': '', 'access': 'RW', 'desc': '0=Disable, 1=Enable'},
        947: {'name': 'power_unbalance_ctrl_enable', 'scale': 1, 'unit': '', 'access': 'RW', 'desc': '0=Disable, 1=Enable'},

        # Parallel Operation
        948: {'name': 'pcs_parallel_num', 'scale': 1, 'unit': '', 'access': 'RW'},
        973: {'name': 'parallel_enable', 'scale': 1, 'unit': '', 'access': 'RW', 'desc': '0=Disable, 1=Enable'},

        # AC Charge/Grid Control
        949: {'name': 'ac_charge_enable', 'scale': 1, 'unit': '', 'access': 'RW', 'desc': '0=Disable, 1=Enable'},
        950: {'name': 'offgrid_enable', 'scale': 1, 'unit': '', 'access': 'RW', 'desc': '0=Disable, 1=Enable'},

        # Battery SOC Limits
        951: {'name': 'battery_charge_stop_soc', 'scale': 1, 'unit': '%', 'access': 'RW', 'valid_range': (0, 100)},
        952: {'name': 'battery_discharge_stop_soc', 'scale': 1, 'unit': '%', 'access': 'RW', 'valid_range': (0, 100)},
        998: {'name': 'offgrid_discharge_stop_soc', 'scale': 1, 'unit': '%', 'access': 'RW', 'valid_range': (0, 100)},

        # Anti-backflow
        953: {'name': 'single_phase_antibackflow', 'scale': 1, 'unit': '', 'access': 'RW', 'desc': '0=Disable, 1=Enable'},

        # Time-of-Use Programming (6 time slots)
        954: {'name': 'time1_enable', 'scale': 1, 'unit': '', 'access': 'RW',
              'desc': 'Bit13-14: 0=Load first, 1=Battery first, 2=Grid first; Bit15: 0=Disable, 1=Enable'},
        955: {'name': 'time1_start', 'scale': 1, 'unit': '', 'access': 'RW', 'desc': 'Bit0-7: minutes, Bit8-12: hours'},
        956: {'name': 'time1_end', 'scale': 1, 'unit': '', 'access': 'RW', 'desc': 'Bit0-7: minutes, Bit8-12: hours'},
        957: {'name': 'time2_enable', 'scale': 1, 'unit': '', 'access': 'RW'},
        958: {'name': 'time2_start', 'scale': 1, 'unit': '', 'access': 'RW'},
        959: {'name': 'time2_end', 'scale': 1, 'unit': '', 'access': 'RW'},
        960: {'name': 'time3_enable', 'scale': 1, 'unit': '', 'access': 'RW'},
        961: {'name': 'time3_start', 'scale': 1, 'unit': '', 'access': 'RW'},
        962: {'name': 'time3_end', 'scale': 1, 'unit': '', 'access': 'RW'},
        963: {'name': 'time4_enable', 'scale': 1, 'unit': '', 'access': 'RW'},
        964: {'name': 'time4_start', 'scale': 1, 'unit': '', 'access': 'RW'},
        965: {'name': 'time4_end', 'scale': 1, 'unit': '', 'access': 'RW'},
        966: {'name': 'time5_enable', 'scale': 1, 'unit': '', 'access': 'RW'},
        967: {'name': 'time5_start', 'scale': 1, 'unit': '', 'access': 'RW'},
        968: {'name': 'time5_end', 'scale': 1, 'unit': '', 'access': 'RW'},
        969: {'name': 'time6_enable', 'scale': 1, 'unit': '', 'access': 'RW'},
        970: {'name': 'time6_start', 'scale': 1, 'unit': '', 'access': 'RW'},
        971: {'name': 'time6_end', 'scale': 1, 'unit': '', 'access': 'RW'},

        # BMS and Power Limits
        972: {'name': 'bms_enable', 'scale': 1, 'unit': '', 'access': 'RW', 'desc': '0=Disable, 1=Enable'},
        974: {'name': 'battery_charge_power_limit', 'scale': 0.1, 'unit': 'kW', 'access': 'RW'},
        975: {'name': 'battery_discharge_power_limit', 'scale': 0.1, 'unit': 'kW', 'access': 'RW'},
        976: {'name': 'ats_spec_power', 'scale': 0.01, 'unit': 'W', 'access': 'RW'},

        # System Configuration
        987: {'name': 'esp_const_nc_enable', 'scale': 1, 'unit': '', 'access': 'RW',
              'desc': 'Emergency stop config', 'values': {0: 'Valid low', 1: 'Valid high'}},

        # WIT/WIS Detection - CRITICAL for auto-detection!
        988: {'name': 'machine_type', 'scale': 1, 'unit': '', 'access': 'RW',
              'desc': 'Machine type identifier',
              'values': {0: 'WIT', 1: 'WIS'}},

        # WIS-specific Force Power Settings (990-995, only for WIS models)
        989: {'name': 'force_power_slow_change', 'scale': 1, 'unit': '', 'access': 'RW',
              'values': {0: 'Disable', 1: 'Enable'}},
        990: {'name': 'force_power_time1', 'scale': 1, 'unit': '%', 'access': 'RW', 'valid_range': (0, 100), 'desc': 'WIS only'},
        991: {'name': 'force_power_time2', 'scale': 1, 'unit': '%', 'access': 'RW', 'valid_range': (0, 100), 'desc': 'WIS only'},
        992: {'name': 'force_power_time3', 'scale': 1, 'unit': '%', 'access': 'RW', 'valid_range': (0, 100), 'desc': 'WIS only'},
        993: {'name': 'force_power_time4', 'scale': 1, 'unit': '%', 'access': 'RW', 'valid_range': (0, 100), 'desc': 'WIS only'},
        994: {'name': 'force_power_time5', 'scale': 1, 'unit': '%', 'access': 'RW', 'valid_range': (0, 100), 'desc': 'WIS only'},
        995: {'name': 'force_power_time6', 'scale': 1, 'unit': '%', 'access': 'RW', 'valid_range': (0, 100), 'desc': 'WIS only'},

        # Backup SOC
        996: {'name': 'backup_soc', 'scale': 1, 'unit': '%', 'access': 'RW', 'valid_range': (0, 100), 'desc': 'Default 50%'},
        997: {'name': 'backup_soc_enable', 'scale': 1, 'unit': '', 'access': 'RW',
              'desc': 'Backup SOC for demand management', 'values': {0: 'Disable', 1: 'Enable'}},
    }
}

# Export all WIT profiles
WIT_REGISTER_MAPS = {
    'WIT_4000_15000TL3': WIT_4000_15000TL3,
}
