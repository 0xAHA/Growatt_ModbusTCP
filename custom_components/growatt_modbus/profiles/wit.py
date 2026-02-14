"""
WIT Series - Three-Phase Hybrid Inverters with Advanced Storage
Based on VPP (Virtual Power Plant) Modbus Protocol

IMPORTANT CONTROL MODEL DIFFERENCES:
- WIT uses VPP protocol with time-limited overrides (NOT persistent mode control like SPH/SPF)
- Register 30476 (priority_mode) is READ-ONLY - shows TOU default, cannot be changed via Modbus
- For temporary control, use VPP remote control registers (30407-30409)
- See docs/WIT_CONTROL_GUIDE.md for detailed control patterns and best practices
"""

# WIT 4000-15000TL3 (Three-phase hybrid with battery, 4-15kW residential)
WIT_4000_15000TL3 = {
    'name': 'WIT 4-15kW Hybrid',
    'description': 'Three-phase hybrid inverter with battery storage and UPS/EPS backup (4-15kW)',
    'notes': 'Uses 0-124, 125-249, 875-999, 8000-8124 and VPP (31000-31399) register ranges. Battery data mapped to 8000-8124 range; battery temperature seen at 31223 (VPP block). Features: UPS 10ms switching, time-of-use programming, VPP/demand management. CONTROL MODEL: VPP protocol with time-limited overrides - register 30476 is READ-ONLY. Use registers 30407-30409 for temporary control.',
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

        # Battery Range (8000-8124)
        8034: {'name': 'battery_voltage', 'scale': 0.1, 'unit': 'V'},
        8035: {'name': 'battery_current', 'scale': 0.1, 'unit': 'A', 'signed': True},

        # AC charge energy (from grid to battery) - 32-bit pairs
        8057: {'name': 'ac_charge_energy_today_high', 'scale': 1, 'unit': '', 'pair': 8058},
        8058: {'name': 'ac_charge_energy_today_low', 'scale': 1, 'unit': '', 'pair': 8057, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        8059: {'name': 'ac_charge_energy_total_high', 'scale': 1, 'unit': '', 'pair': 8060},
        8060: {'name': 'ac_charge_energy_total_low', 'scale': 1, 'unit': '', 'pair': 8059, 'combined_scale': 0.1, 'combined_unit': 'kWh'},

        8093: {'name': 'battery_soc', 'scale': 1, 'unit': '%'},
        8094: {'name': 'battery_soh', 'scale': 1, 'unit': '%'},
        8095: {'name': 'battery_voltage_bms', 'scale': 0.1, 'unit': 'V', 'desc': 'BMS reported voltage (more accurate than 8034)'},

        # Extra/Parallel inverter output (for multi-inverter systems) - 32-bit pairs
        # These will be 0 for single inverter installations
        8102: {'name': 'extra_power_to_grid_high', 'scale': 1, 'unit': '', 'pair': 8103},
        8103: {'name': 'extra_power_to_grid_low', 'scale': 1, 'unit': '', 'pair': 8102, 'combined_scale': 0.1, 'combined_unit': 'kW'},
        8104: {'name': 'extra_energy_today_high', 'scale': 1, 'unit': '', 'pair': 8105},
        8105: {'name': 'extra_energy_today_low', 'scale': 1, 'unit': '', 'pair': 8104, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        8106: {'name': 'extra_energy_total_high', 'scale': 1, 'unit': '', 'pair': 8107},
        8107: {'name': 'extra_energy_total_low', 'scale': 1, 'unit': '', 'pair': 8106, 'combined_scale': 0.1, 'combined_unit': 'kWh'},

        # ============================================================================
        # VPP BATTERY RANGE (31200-31323): Battery Cluster Data
        # ============================================================================
        # Per VPP Protocol V2.02: Battery power and energy data

        # Battery Cluster 1 Power & Energy (31200-31213)
        # Per VPP Protocol V2.01/V2.02 Official Specification

        # 65: Charge/discharge power (INT32, signed: positive=charge, negative=discharge)
        # VPP spec: 0.1W scale (standard for most WIT inverters)
        # NOTE: Some rare WIT variants may use 1.0W scale - see v0.1.8 release notes for manual fix
        31200: {'name': 'battery_power_high', 'scale': 1, 'unit': '', 'pair': 31201},
        31201: {'name': 'battery_power_low', 'scale': 1, 'unit': '', 'pair': 31200, 'combined_scale': 0.1, 'combined_unit': 'W', 'signed': True},

        # 66: Daily charge of battery
        31202: {'name': 'charge_energy_today_high', 'scale': 1, 'unit': '', 'pair': 31203},
        31203: {'name': 'charge_energy_today_low', 'scale': 1, 'unit': '', 'pair': 31202, 'combined_scale': 0.1, 'combined_unit': 'kWh'},

        # 67: Cumulative charge of battery
        31204: {'name': 'charge_energy_total_high', 'scale': 1, 'unit': '', 'pair': 31205},
        31205: {'name': 'charge_energy_total_low', 'scale': 1, 'unit': '', 'pair': 31204, 'combined_scale': 0.1, 'combined_unit': 'kWh'},

        # 68: Daily discharge capacity of battery
        31206: {'name': 'discharge_energy_today_high', 'scale': 1, 'unit': '', 'pair': 31207},
        31207: {'name': 'discharge_energy_today_low', 'scale': 1, 'unit': '', 'pair': 31206, 'combined_scale': 0.1, 'combined_unit': 'kWh'},

        # 69: Cumulative discharge of battery
        31208: {'name': 'discharge_energy_total_high', 'scale': 1, 'unit': '', 'pair': 31209},
        31209: {'name': 'discharge_energy_total_low', 'scale': 1, 'unit': '', 'pair': 31208, 'combined_scale': 0.1, 'combined_unit': 'kWh'},

        # 70: Maximum allowable charging power of battery (this is a LIMIT, not actual power)
        31210: {'name': 'max_charge_power_high', 'scale': 1, 'unit': '', 'pair': 31211},
        31211: {'name': 'max_charge_power_low', 'scale': 1, 'unit': '', 'pair': 31210, 'combined_scale': 0.1, 'combined_unit': 'W'},

        # 71: Maximum allowable discharge power of battery (this is a LIMIT, not actual power)
        31212: {'name': 'max_discharge_power_high', 'scale': 1, 'unit': '', 'pair': 31213},
        31213: {'name': 'max_discharge_power_low', 'scale': 1, 'unit': '', 'pair': 31212, 'combined_scale': 0.1, 'combined_unit': 'W'},

        # Battery Cluster 1 State (31214-31223)
        31214: {'name': 'battery_voltage_vpp', 'scale': 0.1, 'unit': 'V', 'maps_to': 'battery_voltage', 'signed': True},
        31215: {'name': 'battery_current_vpp', 'scale': 0.1, 'unit': 'A', 'maps_to': 'battery_current', 'signed': True},
        31217: {'name': 'battery_soc_vpp', 'scale': 1, 'unit': '%', 'maps_to': 'battery_soc'},
        # Per VPP Protocol V2.03 - firmware variant differences observed:
        # Some WIT firmware: 31222=temp, 31223=alt_temp (e.g., linksu79's unit)
        # Other WIT firmware: 31222=max_power(?), 31223=temp (e.g., YEAa141299/ZDDa-0014)
        # We map 31223 as primary to support majority firmware, 31222 as alternative
        31222: {'name': 'battery_temp_vpp_alt', 'scale': 0.1, 'unit': '°C', 'signed': True, 'desc': 'Battery temp (some firmware variants)'},
        31223: {'name': 'battery_temp', 'scale': 0.1, 'unit': '°C', 'signed': True, 'maps_to': 'battery_temp', 'desc': 'Battery environmental temperature'},
        31224: {'name': 'battery_temp_max', 'scale': 0.1, 'unit': '°C', 'signed': True, 'desc': 'Maximum battery temperature'},

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

        # Load Energy (8075-8078)
        8075: {'name': 'load_energy_today_high', 'scale': 1, 'unit': '', 'pair': 8076},
        8076: {'name': 'load_energy_today_low', 'scale': 1, 'unit': '', 'pair': 8075, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        8077: {'name': 'load_energy_total_high', 'scale': 1, 'unit': '', 'pair': 8078},
        8078: {'name': 'load_energy_total_low', 'scale': 1, 'unit': '', 'pair': 8077, 'combined_scale': 0.1, 'combined_unit': 'kWh'},

        # Power Flow (8079-8084) - Per VPP spec terminology
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
        3: {'name': 'max_output_power_rate', 'scale': 1, 'unit': '%', 'access': 'RW'},

        # Device identification
        30000: {'name': 'dtc_code', 'scale': 1, 'unit': '', 'access': 'RO', 'desc': 'Device Type Code: 5603 for WIT 4-15kW', 'default': 5603},
        30099: {'name': 'protocol_version', 'scale': 1, 'unit': '', 'access': 'RO', 'desc': 'VPP Protocol version (202 = V2.02)', 'default': 202},

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
        # VPP REMOTE CONTROL (WIT SPECIFIC)
        # 201 = Active power rate (%)
        # 202 = Work mode / remote command (0 standby, 1 charge, 2 discharge)
        # 203 = Export limit (W), 0 = zero export
        201: {'name': 'active_power_rate', 'scale': 1, 'unit': '%', 'access': 'W', 'valid_range': (0, 100),
              'desc': 'VPP remote active power command (percent) – requires work_mode'},
        202: {'name': 'work_mode', 'scale': 1, 'unit': '', 'access': 'W',
              'values': {0: 'Standby', 1: 'Charge', 2: 'Discharge'},
              'desc': 'VPP remote work mode / command'},
        203: {'name': 'export_limit_w', 'scale': 1, 'unit': 'W', 'access': 'W', 'valid_range': (0, 20000),
              'desc': 'Export limit in watts (0 = zero export)'},
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

        # ============================================================================
        # TOU/OPERATING MODE CONTROL (30000+ range)
        # ============================================================================

        # VPP Remote Control Authority
        30100: {'name': 'control_authority', 'scale': 1, 'unit': '', 'access': 'RW',
                'desc': 'VPP master enable switch',
                'valid_range': (0, 1),
                'values': {
                    0: 'Disabled',
                    1: 'Enabled'
                }},

        # VPP Timed Charge/Discharge Override (temporary power control)
        30407: {'name': 'remote_power_control_enable', 'scale': 1, 'unit': '', 'access': 'RW',
                'desc': 'Enable timed charge/discharge power override',
                'valid_range': (0, 1),
                'values': {
                    0: 'Disabled',
                    1: 'Enabled'
                }},
        30408: {'name': 'remote_power_control_charging_time', 'scale': 1, 'unit': 'min', 'access': 'RW',
                'desc': 'Duration for remote power control (0-1440 minutes)',
                'valid_range': (0, 1440)},
        30409: {'name': 'remote_charge_and_discharge_power', 'scale': 1, 'unit': '%', 'access': 'RW',
                'desc': 'Remote charge/discharge power (-100% to +100%, negative=discharge, positive=charge)',
                'valid_range': (-100, 100),
                'signed': True},

        # Operating Mode Selection (READ-ONLY - shows default mode when no TOU period is active)
        # NOTE: WIT inverters do NOT support external mode control via Modbus.
        # This register shows the current TOU default mode but cannot be changed via Modbus.
        # For temporary overrides, use VPP remote control registers (30407-30409) instead.
        # See docs/WIT_CONTROL_GUIDE.md for details.
        30476: {'name': 'priority_mode', 'scale': 1, 'unit': '', 'access': 'R',
                'desc': 'System operating mode (READ-ONLY: TOU default / outside configured periods)',
                'valid_range': (0, 2),
                'values': {
                    0: 'Load First',
                    1: 'Battery First',
                    2: 'Grid First'
                }},

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
