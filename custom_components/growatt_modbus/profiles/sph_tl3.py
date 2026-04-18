# SPH-TL3 Series - Three-Phase Hybrid with Battery Storage
# Based on SPH-10000-TL3-BH-UP scan results
# Register scan date: 2025-10-28

from .vpp_v201 import (
    VPP_V201_STATUS, VPP_V201_PV2_INPUT, VPP_V201_PV2_TOTAL,
    VPP_V201_TEMPERATURE_1P, VPP_V201_BATTERY2, VPP_V201_HOLDING_1P,
)

SPH_TL3_3000_10000 = {
    'name': 'SPH-TL3 Series 3-10kW',
    'description': 'Three-phase hybrid inverter with battery storage (3-10kW)',
    'notes': 'Uses 0-124, 1000-1124 register ranges. Three-phase with battery management.',
    'use_mppt_energy_today': True,  # Reg 53/54 = system AC output incl. battery discharge; use per-MPPT DC sum instead
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

        # PV String 3 (optional - present on models with 3 MPPT inputs)
        11: {'name': 'pv3_voltage', 'scale': 0.1, 'unit': 'V'},
        12: {'name': 'pv3_current', 'scale': 0.1, 'unit': 'A'},
        13: {'name': 'pv3_power_high', 'scale': 1, 'unit': '', 'pair': 14},
        14: {'name': 'pv3_power_low', 'scale': 1, 'unit': '', 'pair': 13, 'combined_scale': 0.1, 'combined_unit': 'W'},

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
        # NOTE: Registers 53-54 show total AC output energy (what went to grid/loads)
        # For true total PV production on hybrid inverters, use PV1+PV2 energy (59-60, 63-64)
        53: {'name': 'energy_today_high', 'scale': 1, 'unit': '', 'desc': 'Total AC output today HIGH (PV+Battery discharge, NOT PV-only)', 'pair': 54},
        54: {'name': 'energy_today_low', 'scale': 1, 'unit': '', 'desc': 'Total AC output today LOW', 'pair': 53, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        55: {'name': 'energy_total_high', 'scale': 1, 'unit': '', 'desc': 'Total AC output lifetime HIGH', 'pair': 56},
        56: {'name': 'energy_total_low', 'scale': 1, 'unit': '', 'desc': 'Total AC output lifetime LOW', 'pair': 55, 'combined_scale': 0.1, 'combined_unit': 'kWh'},

        # Per-MPPT PV Energy (true solar production, excludes DC battery charging)
        59: {'name': 'pv1_energy_today_high', 'scale': 1, 'unit': '', 'pair': 60, 'desc': 'PV1 DC energy today HIGH (true solar production from string 1)'},
        60: {'name': 'pv1_energy_today_low', 'scale': 1, 'unit': '', 'pair': 59, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'PV1 DC energy today LOW'},
        61: {'name': 'pv1_energy_total_high', 'scale': 1, 'unit': '', 'pair': 62, 'desc': 'PV1 DC energy total HIGH'},
        62: {'name': 'pv1_energy_total_low', 'scale': 1, 'unit': '', 'pair': 61, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'PV1 DC energy total LOW'},
        63: {'name': 'pv2_energy_today_high', 'scale': 1, 'unit': '', 'pair': 64, 'desc': 'PV2 DC energy today HIGH (true solar production from string 2)'},
        64: {'name': 'pv2_energy_today_low', 'scale': 1, 'unit': '', 'pair': 63, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'PV2 DC energy today LOW'},
        65: {'name': 'pv2_energy_total_high', 'scale': 1, 'unit': '', 'pair': 66, 'desc': 'PV2 DC energy total HIGH'},
        66: {'name': 'pv2_energy_total_low', 'scale': 1, 'unit': '', 'pair': 65, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'PV2 DC energy total LOW'},

        # PV String 3 Energy (for 3-MPPT models like SPH 10000TL3 — Issue #211)
        67: {'name': 'pv3_energy_today_high', 'scale': 1, 'unit': '', 'pair': 68, 'desc': 'PV3 DC energy today HIGH (Epv3_today H — V1.24 reg 67)'},
        68: {'name': 'pv3_energy_today_low', 'scale': 1, 'unit': '', 'pair': 67, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'PV3 DC energy today LOW'},

        # Total PV Energy (lifetime sum of all DC input from solar panels)
        91: {'name': 'pv_energy_total_high', 'scale': 1, 'unit': '', 'pair': 92, 'desc': 'Total PV energy lifetime HIGH (DC input from all MPPTs)'},
        92: {'name': 'pv_energy_total_low', 'scale': 1, 'unit': '', 'pair': 91, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'Total PV energy lifetime LOW'},

        # Temperatures
        93: {'name': 'inverter_temp', 'scale': 0.1, 'unit': '°C', 'signed': True},

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
        1040: {'name': 'battery_temp', 'scale': 0.1, 'unit': '°C', 'signed': True},
        1041: {'name': 'battery_type', 'scale': 1, 'unit': ''},
        
        # Power Flow
        # Per Growatt Modbus Protocol II V1.24:
        # 1021: PactouserTotal  = AC power to user total (grid import, positive = importing)
        # 1029: Pactogrid total = AC power to grid total (grid export, positive = exporting)
        # 1037: PLocalLoad total = INV power to local load total
        1015: {'name': 'power_to_user_high', 'scale': 1, 'unit': '', 'pair': 1016, 'desc': 'Power imported from grid HIGH (legacy register)'},
        1016: {'name': 'power_to_user_low', 'scale': 1, 'unit': '', 'pair': 1015, 'combined_scale': 0.1, 'combined_unit': 'W'},
        1021: {'name': 'power_to_user_total_high', 'scale': 1, 'unit': '', 'pair': 1022, 'desc': 'AC power to user total H (PactouserTotal = grid import)', 'maps_to': 'power_to_user'},
        1022: {'name': 'power_to_user_total_low', 'scale': 1, 'unit': '', 'pair': 1021, 'combined_scale': 0.1, 'combined_unit': 'W'},
        1029: {'name': 'power_to_grid_high', 'scale': 1, 'unit': '', 'pair': 1030, 'desc': 'AC power to grid total H (Pactogrid total)'},
        1030: {'name': 'power_to_grid_low', 'scale': 1, 'unit': '', 'pair': 1029, 'combined_scale': 0.1, 'combined_unit': 'W', 'signed': True},
        1037: {'name': 'power_to_load_high', 'scale': 1, 'unit': '', 'pair': 1038, 'desc': 'INV power to local load total H (PLocalLoad total)'},
        1038: {'name': 'power_to_load_low', 'scale': 1, 'unit': '', 'pair': 1037, 'combined_scale': 0.1, 'combined_unit': 'W'},
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
        0: {'name': 'on_off', 'scale': 1, 'unit': '', 'access': 'RW', 'desc': '0=Off, 1=On'},
        1008: {'name': 'system_enable', 'scale': 1, 'unit': '', 'access': 'RW'},

        # Max Output Power Rate
        3: {'name': 'max_output_power_rate', 'scale': 1, 'unit': '%', 'access': 'RW',
            'valid_range': (0, 100),
            'desc': 'Maximum output power limitation (0-100%)'},

        # Export Limit Control
        122: {'name': 'export_limit_mode', 'scale': 1, 'unit': '', 'access': 'RW',
              'desc': 'Export limit mode: 0=Disabled, 1=RS485'},
        123: {'name': 'export_limit_power', 'scale': 0.1, 'unit': '%', 'access': 'RW',
              'desc': 'Export limit power percentage (0-100%)'},

        # Load First Battery Minimum SOC
        608: {'name': 'load_first_battery_minimum_soc', 'scale': 1, 'unit': '%', 'access': 'RW',
              'valid_range': (10, 100),
              'desc': 'Minimum battery SOC in Load First mode — inverter stops discharging below this level (10-100%)'},

        # Battery Management Control
        1044: {'name': 'priority_mode', 'scale': 1, 'unit': '', 'access': 'RW',
               'desc': 'Priority mode selection',
               'valid_range': (0, 2),
               'values': {
                   0: 'Load First',
                   1: 'Battery First',
                   2: 'Grid First'
               }},

        # Discharge Control
        1070: {'name': 'discharge_power_rate', 'scale': 1, 'unit': '%', 'access': 'RW',
               'valid_range': (0, 100),
               'desc': 'Battery discharge power rate limit (0-100%)'},
        1071: {'name': 'discharge_stopped_soc', 'scale': 1, 'unit': '%', 'access': 'RW',
               'valid_range': (0, 100),
               'desc': 'SOC level to stop battery discharge (0-100%)'},

        # Charge Control
        1090: {'name': 'charge_power_rate', 'scale': 1, 'unit': '%', 'access': 'RW',
               'valid_range': (0, 100),
               'desc': 'Battery charge power rate limit (0-100%)'},
        1091: {'name': 'charge_stopped_soc', 'scale': 1, 'unit': '%', 'access': 'RW',
               'valid_range': (0, 100),
               'desc': 'SOC level to stop battery charge (0-100%)'},
        1092: {'name': 'ac_charge_enable', 'scale': 1, 'unit': '', 'access': 'RW',
               'desc': 'Enable charging from AC (grid/backup)',
               'values': {
                   0: 'Disabled',
                   1: 'Enabled'
               }},

        # Time Period 1 Control (for time-based charging/discharging)
        1100: {'name': 'time_period_1_start', 'scale': 1, 'unit': '', 'access': 'RW',
               'valid_range': (0, 2359),
               'desc': 'Period 1 start time (hex-packed: hours*256+minutes, e.g. 06:00 = 0x0600 = 1536)'},
        1101: {'name': 'time_period_1_end', 'scale': 1, 'unit': '', 'access': 'RW',
               'valid_range': (0, 2359),
               'desc': 'Period 1 end time (hex-packed: hours*256+minutes)'},
        1102: {'name': 'time_period_1_enable', 'scale': 1, 'unit': '', 'access': 'RW',
               'desc': 'Enable time period 1',
               'values': {0: 'Disabled', 1: 'Enabled'}},

        # Time Period 2 Control
        1103: {'name': 'time_period_2_start', 'scale': 1, 'unit': '', 'access': 'RW',
               'valid_range': (0, 2359),
               'desc': 'Period 2 start time (hex-packed: hours*256+minutes)'},
        1104: {'name': 'time_period_2_end', 'scale': 1, 'unit': '', 'access': 'RW',
               'valid_range': (0, 2359),
               'desc': 'Period 2 end time (hex-packed: hours*256+minutes)'},
        1105: {'name': 'time_period_2_enable', 'scale': 1, 'unit': '', 'access': 'RW',
               'desc': 'Enable time period 2',
               'values': {0: 'Disabled', 1: 'Enabled'}},

        # Time Period 3 Control
        1106: {'name': 'time_period_3_start', 'scale': 1, 'unit': '', 'access': 'RW',
               'valid_range': (0, 2359),
               'desc': 'Period 3 start time (hex-packed: hours*256+minutes)'},
        1107: {'name': 'time_period_3_end', 'scale': 1, 'unit': '', 'access': 'RW',
               'valid_range': (0, 2359),
               'desc': 'Period 3 end time (hex-packed: hours*256+minutes)'},
        1108: {'name': 'time_period_3_enable', 'scale': 1, 'unit': '', 'access': 'RW',
               'desc': 'Enable time period 3',
               'values': {0: 'Disabled', 1: 'Enabled'}},

        # -----------------------------------------------------------------------
        # Battery First mode scheduling windows — slots 4–6 (registers 1017–1025)
        # These control WHEN the inverter applies Battery First priority.
        # Register naming confirmed via SPH_3000-6000TL-HUB manual:
        #   1021 = "Bat First Stop Time 5", 1022 = "BatFirst on/off Switch 5"
        # Note: these are HOLDING registers; input registers 1021/1022/1029/1030
        # (power_to_user_total / power_to_grid) are in a separate address space.
        # -----------------------------------------------------------------------
        1017: {'name': 'batt_first_time_period_4_start', 'scale': 1, 'unit': '', 'access': 'RW',
               'desc': 'Battery First slot 4 start (hex-packed: hours*256+minutes, e.g. 06:00 = 1536)'},
        1018: {'name': 'batt_first_time_period_4_end', 'scale': 1, 'unit': '', 'access': 'RW',
               'desc': 'Battery First slot 4 end (hex-packed: hours*256+minutes)'},
        1019: {'name': 'batt_first_time_period_4_enable', 'scale': 1, 'unit': '', 'access': 'RW',
               'values': {0: 'Disabled', 1: 'Enabled'},
               'desc': 'Enable Battery First slot 4'},
        1020: {'name': 'batt_first_time_period_5_start', 'scale': 1, 'unit': '', 'access': 'RW',
               'desc': 'Battery First slot 5 start (hex-packed: hours*256+minutes)'},
        1021: {'name': 'batt_first_time_period_5_end', 'scale': 1, 'unit': '', 'access': 'RW',
               'desc': 'Battery First slot 5 end (hex-packed: hours*256+minutes)'},
        1022: {'name': 'batt_first_time_period_5_enable', 'scale': 1, 'unit': '', 'access': 'RW',
               'values': {0: 'Disabled', 1: 'Enabled'},
               'desc': 'Enable Battery First slot 5'},
        1023: {'name': 'batt_first_time_period_6_start', 'scale': 1, 'unit': '', 'access': 'RW',
               'desc': 'Battery First slot 6 start (hex-packed: hours*256+minutes)'},
        1024: {'name': 'batt_first_time_period_6_end', 'scale': 1, 'unit': '', 'access': 'RW',
               'desc': 'Battery First slot 6 end (hex-packed: hours*256+minutes)'},
        1025: {'name': 'batt_first_time_period_6_enable', 'scale': 1, 'unit': '', 'access': 'RW',
               'values': {0: 'Disabled', 1: 'Enabled'},
               'desc': 'Enable Battery First slot 6'},

        # -----------------------------------------------------------------------
        # Grid First mode scheduling windows — slots 4–6 (registers 1026–1034)
        # 1029 = "Grid First Start Time 5", 1030 = "Grid First Stop Time 5" (confirmed via manual)
        # -----------------------------------------------------------------------
        1026: {'name': 'grid_first_time_period_4_start', 'scale': 1, 'unit': '', 'access': 'RW',
               'desc': 'Grid First slot 4 start (hex-packed: hours*256+minutes)'},
        1027: {'name': 'grid_first_time_period_4_end', 'scale': 1, 'unit': '', 'access': 'RW',
               'desc': 'Grid First slot 4 end (hex-packed: hours*256+minutes)'},
        1028: {'name': 'grid_first_time_period_4_enable', 'scale': 1, 'unit': '', 'access': 'RW',
               'values': {0: 'Disabled', 1: 'Enabled'},
               'desc': 'Enable Grid First slot 4'},
        1029: {'name': 'grid_first_time_period_5_start', 'scale': 1, 'unit': '', 'access': 'RW',
               'desc': 'Grid First slot 5 start (hex-packed: hours*256+minutes)'},
        1030: {'name': 'grid_first_time_period_5_end', 'scale': 1, 'unit': '', 'access': 'RW',
               'desc': 'Grid First slot 5 end (hex-packed: hours*256+minutes)'},
        1031: {'name': 'grid_first_time_period_5_enable', 'scale': 1, 'unit': '', 'access': 'RW',
               'values': {0: 'Disabled', 1: 'Enabled'},
               'desc': 'Enable Grid First slot 5'},
        1032: {'name': 'grid_first_time_period_6_start', 'scale': 1, 'unit': '', 'access': 'RW',
               'desc': 'Grid First slot 6 start (hex-packed: hours*256+minutes)'},
        1033: {'name': 'grid_first_time_period_6_end', 'scale': 1, 'unit': '', 'access': 'RW',
               'desc': 'Grid First slot 6 end (hex-packed: hours*256+minutes)'},
        1034: {'name': 'grid_first_time_period_6_enable', 'scale': 1, 'unit': '', 'access': 'RW',
               'values': {0: 'Disabled', 1: 'Enabled'},
               'desc': 'Enable Grid First slot 6'},

        # -----------------------------------------------------------------------
        # Grid First mode scheduling windows — slots 7–9 (registers 1080–1088)
        # -----------------------------------------------------------------------
        1080: {'name': 'grid_first_time_period_7_start', 'scale': 1, 'unit': '', 'access': 'RW',
               'desc': 'Grid First slot 7 start (hex-packed: hours*256+minutes)'},
        1081: {'name': 'grid_first_time_period_7_end', 'scale': 1, 'unit': '', 'access': 'RW',
               'desc': 'Grid First slot 7 end (hex-packed: hours*256+minutes)'},
        1082: {'name': 'grid_first_time_period_7_enable', 'scale': 1, 'unit': '', 'access': 'RW',
               'values': {0: 'Disabled', 1: 'Enabled'},
               'desc': 'Enable Grid First slot 7'},
        1083: {'name': 'grid_first_time_period_8_start', 'scale': 1, 'unit': '', 'access': 'RW',
               'desc': 'Grid First slot 8 start (hex-packed: hours*256+minutes)'},
        1084: {'name': 'grid_first_time_period_8_end', 'scale': 1, 'unit': '', 'access': 'RW',
               'desc': 'Grid First slot 8 end (hex-packed: hours*256+minutes)'},
        1085: {'name': 'grid_first_time_period_8_enable', 'scale': 1, 'unit': '', 'access': 'RW',
               'values': {0: 'Disabled', 1: 'Enabled'},
               'desc': 'Enable Grid First slot 8'},
        1086: {'name': 'grid_first_time_period_9_start', 'scale': 1, 'unit': '', 'access': 'RW',
               'desc': 'Grid First slot 9 start (hex-packed: hours*256+minutes)'},
        1087: {'name': 'grid_first_time_period_9_end', 'scale': 1, 'unit': '', 'access': 'RW',
               'desc': 'Grid First slot 9 end (hex-packed: hours*256+minutes)'},
        1088: {'name': 'grid_first_time_period_9_enable', 'scale': 1, 'unit': '', 'access': 'RW',
               'values': {0: 'Disabled', 1: 'Enabled'},
               'desc': 'Enable Grid First slot 9'},
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

        # Status — VPP_V201_STATUS (31000–31004)
        **VPP_V201_STATUS,

        # PV strings 1 and 2 — VPP_V201_PV2_INPUT (31010–31017)
        **VPP_V201_PV2_INPUT,

        # Total PV power — VPP_V201_PV2_TOTAL (31018–31019)
        # SPH-TL3 is a 2-string profile at VPP level.
        **VPP_V201_PV2_TOTAL,

        # Three-Phase AC Output
        31100: {'name': 'ac_voltage_r_vpp', 'scale': 0.1, 'unit': 'V', 'maps_to': 'ac_voltage_r'},
        31101: {'name': 'ac_voltage_s_vpp', 'scale': 0.1, 'unit': 'V', 'maps_to': 'ac_voltage_s'},
        31102: {'name': 'ac_voltage_t_vpp', 'scale': 0.1, 'unit': 'V', 'maps_to': 'ac_voltage_t'},
        31103: {'name': 'ac_frequency_vpp', 'scale': 0.01, 'unit': 'Hz', 'maps_to': 'ac_frequency'},

        # Grid/Meter Power (maps to power_to_grid at 1029/1030)
        31112: {'name': 'meter_power_high', 'scale': 1, 'unit': '', 'pair': 31113, 'maps_to': 'power_to_grid'},
        31113: {'name': 'meter_power_low', 'scale': 1, 'unit': '', 'pair': 31112, 'combined_scale': 0.1, 'combined_unit': 'W', 'signed': True},

        # Energy Data (VPP range — per Growatt VPP V2.01 register table)
        # Row 60: Power to user daily  → energy consumed by load today (0.1 kWh)
        # Row 61: Total power to user  → lifetime energy consumed by load (0.1 kWh)
        # Row 62: Power to grid daily  → energy exported to grid today (0.1 kWh)
        # Row 63: Total power to grid  → lifetime energy exported to grid (0.1 kWh)
        # These duplicate the legacy 1044–1051 registers; legacy values are used by coordinator
        # (found first in dict iteration). VPP copies kept for reference/future fallback.
        31118: {'name': 'energy_to_user_today_vpp_high', 'scale': 1, 'unit': '', 'pair': 31119, 'desc': 'Power to user daily HIGH (VPP, 0.1 kWh)'},
        31119: {'name': 'energy_to_user_today_vpp_low', 'scale': 1, 'unit': '', 'pair': 31118, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'Power to user daily LOW'},
        31120: {'name': 'energy_to_user_total_vpp_high', 'scale': 1, 'unit': '', 'pair': 31121, 'desc': 'Total power to user HIGH (VPP, 0.1 kWh)'},
        31121: {'name': 'energy_to_user_total_vpp_low', 'scale': 1, 'unit': '', 'pair': 31120, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'Total power to user LOW'},
        31122: {'name': 'energy_to_grid_today_vpp_high', 'scale': 1, 'unit': '', 'pair': 31123, 'desc': 'Power to grid daily HIGH (VPP, 0.1 kWh)'},
        31123: {'name': 'energy_to_grid_today_vpp_low', 'scale': 1, 'unit': '', 'pair': 31122, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'Power to grid daily LOW'},
        31124: {'name': 'energy_to_grid_total_vpp_high', 'scale': 1, 'unit': '', 'pair': 31125, 'desc': 'Total power to grid HIGH (VPP, 0.1 kWh)'},
        31125: {'name': 'energy_to_grid_total_vpp_low', 'scale': 1, 'unit': '', 'pair': 31124, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'Total power to grid LOW'},

        # Temperatures — VPP_V201_TEMPERATURE_1P (31130–31132)
        # Confirmed responding on SPH-TL3 in scans 251_1 and 251_2.
        **VPP_V201_TEMPERATURE_1P,

        # Battery Cluster 1 State (31200-31223)
        # Per VPP Protocol V2.01: 31200-31201 is signed battery power (positive=charge, negative=discharge)
        31200: {'name': 'battery_power_high', 'scale': 1, 'unit': '', 'pair': 31201},
        31201: {'name': 'battery_power_low', 'scale': 1, 'unit': '', 'pair': 31200, 'combined_scale': 0.1, 'combined_unit': 'W', 'signed': True},
        # Note: 31202-31203 might be charge energy per VPP spec, but keeping as charge power for now (needs validation)
        31202: {'name': 'battery_charge_power_high', 'scale': 1, 'unit': '', 'pair': 31203, 'maps_to': 'charge_power'},
        31203: {'name': 'battery_charge_power_low', 'scale': 1, 'unit': '', 'pair': 31202, 'combined_scale': 0.1, 'combined_unit': 'W'},
        31214: {'name': 'battery_voltage_vpp', 'scale': 0.1, 'unit': 'V', 'maps_to': 'battery_voltage', 'signed': True},
        31217: {'name': 'battery_soc_vpp', 'scale': 1, 'unit': '%', 'maps_to': 'battery_soc'},
        31218: {'name': 'battery_soh', 'scale': 1, 'unit': '%', 'desc': 'Battery state of health'},
        31222: {'name': 'battery_temp_vpp', 'scale': 0.1, 'unit': '°C', 'maps_to': 'battery_temp', 'signed': True},

        # Battery Cluster 2 — VPP_V201_BATTERY2 (31300–31303, 31314–31322)
        **VPP_V201_BATTERY2,
    },
    'holding_registers': {
        # === Legacy REGISTERS ===
        **SPH_TL3_3000_10000['holding_registers'],

        # === V2.01 REGISTERS (30000+ range) ===
        30000: {'name': 'dtc_code', 'scale': 1, 'unit': '', 'access': 'RO',
                'desc': 'Device Type Code: 2000 for SPH-TL3', 'default': 3601},

        # Shared holding block — VPP_V201_HOLDING_1P (30099–30109, 30114, 30200–30201)
        # Confirmed: all registers including 30114 respond Read OK on SPH-TL3 (scans 251_1, 251_2).
        **VPP_V201_HOLDING_1P,
    }
}

# Export all SPH profiles
SPH_TL3_REGISTER_MAPS = {
    'SPH_TL3_3000_10000': SPH_TL3_3000_10000,
    'SPH_TL3_3000_10000_V201': SPH_TL3_3000_10000_V201,
}