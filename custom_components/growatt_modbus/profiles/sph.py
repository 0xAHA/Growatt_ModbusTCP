from .vpp_v201 import (
    VPP_V201_STATUS, VPP_V201_PV2_INPUT, VPP_V201_PV2_TOTAL,
    VPP_V201_PV3_AND_TOTAL, VPP_V201_ENERGY_1P, VPP_V201_TEMPERATURE_1P,
    VPP_V201_BATTERY2, VPP_V201_HOLDING_1P,
)

# SPH 3000-6000 (Single-phase hybrid with battery)
SPH_3000_6000 = {
    'name': 'SPH Series 3-6kW',
    'description': 'Single-phase hybrid inverter with battery storage (3-6kW)',
    'notes': 'Uses 0-124 register range. 2 PV strings, battery management, backup output.',
    'use_mppt_energy_today': True,  # Reg 53/54 = system AC output incl. battery discharge; use per-MPPT DC sum instead
    'input_registers': {
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

        # Per V1.39: regs 13-22 are PV3-PV5 channel registers (voltage, current, power H/L).
        # Standard SPH 3-6kW has only 2 MPPT strings — PV3+ registers return 0 or are unused.
        # Battery data is in the storage range (1000+) — see below.
        17: {'name': 'ppv4_power_high', 'scale': 1, 'unit': '', 'pair': 18, 'desc': 'PV4 power HIGH word (0 if no PV4 string)'},
        18: {'name': 'ppv4_power_low', 'scale': 1, 'unit': '', 'pair': 17, 'combined_scale': 0.1, 'combined_unit': 'W', 'desc': 'PV4 power LOW word (0 if no PV4 string)'},

        # Battery — storage range (V1.39 correct registers — Issue #283)
        1009: {'name': 'discharge_power_high', 'scale': 1, 'unit': '', 'pair': 1010},
        1010: {'name': 'discharge_power_low', 'scale': 1, 'unit': '', 'pair': 1009, 'combined_scale': 0.1, 'combined_unit': 'W'},
        1011: {'name': 'charge_power_high', 'scale': 1, 'unit': '', 'pair': 1012},
        1012: {'name': 'charge_power_low', 'scale': 1, 'unit': '', 'pair': 1011, 'combined_scale': 0.1, 'combined_unit': 'W'},
        1013: {'name': 'battery_voltage', 'scale': 0.1, 'unit': 'V', 'desc': 'Battery voltage (Vbat)'},
        1014: {'name': 'battery_soc', 'scale': 1, 'unit': '%', 'desc': 'Battery state of charge'},
        1040: {'name': 'battery_temp', 'scale': 0.1, 'unit': '°C', 'signed': True, 'desc': 'Battery temperature'},

        # AC Output
        37: {'name': 'ac_frequency', 'scale': 0.01, 'unit': 'Hz'},
        38: {'name': 'ac_voltage', 'scale': 0.1, 'unit': 'V', 'desc': 'Grid voltage'},
        39: {'name': 'ac_current', 'scale': 0.1, 'unit': 'A'},
        40: {'name': 'ac_power_high', 'scale': 1, 'unit': '', 'pair': 41},
        41: {'name': 'ac_power_low', 'scale': 1, 'unit': '', 'pair': 40, 'combined_scale': 0.1, 'combined_unit': 'W'},

        # Energy
        53: {'name': 'energy_today_high', 'scale': 1, 'unit': '', 'pair': 54},
        54: {'name': 'energy_today_low', 'scale': 1, 'unit': '', 'pair': 53, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        55: {'name': 'energy_total_high', 'scale': 1, 'unit': '', 'pair': 56},
        56: {'name': 'energy_total_low', 'scale': 1, 'unit': '', 'pair': 55, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        57: {'name': 'time_total_high', 'scale': 1, 'unit': '', 'pair': 58},
        58: {'name': 'time_total_low', 'scale': 1, 'unit': '', 'pair': 57, 'combined_scale': 0.5, 'combined_unit': 'h'},

        # Per-string DC energy (today and lifetime totals) — confirmed via scan #131
        59: {'name': 'pv1_energy_today_high', 'scale': 1, 'unit': '', 'pair': 60, 'desc': 'PV1 DC energy today HIGH'},
        60: {'name': 'pv1_energy_today_low', 'scale': 1, 'unit': '', 'pair': 59, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'PV1 DC energy today LOW'},
        61: {'name': 'pv1_energy_total_high', 'scale': 1, 'unit': '', 'pair': 62, 'desc': 'PV1 DC energy total HIGH'},
        62: {'name': 'pv1_energy_total_low', 'scale': 1, 'unit': '', 'pair': 61, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'PV1 DC energy total LOW'},
        63: {'name': 'pv2_energy_today_high', 'scale': 1, 'unit': '', 'pair': 64, 'desc': 'PV2 DC energy today HIGH'},
        64: {'name': 'pv2_energy_today_low', 'scale': 1, 'unit': '', 'pair': 63, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'PV2 DC energy today LOW'},
        65: {'name': 'pv2_energy_total_high', 'scale': 1, 'unit': '', 'pair': 66, 'desc': 'PV2 DC energy total HIGH'},
        66: {'name': 'pv2_energy_total_low', 'scale': 1, 'unit': '', 'pair': 65, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'PV2 DC energy total LOW'},

        # PV energy total — raw DC-side generation, unaffected by battery cycling (#243)
        # Protocol V1.39 regs 91-92: Epv_total H/L (0.1 kWh)
        # Use this for HA energy dashboard; energy_total (reg 55/56) is a net calculated value
        91: {'name': 'pv_energy_total_high', 'scale': 1, 'unit': '', 'pair': 92, 'desc': 'PV energy total lifetime HIGH'},
        92: {'name': 'pv_energy_total_low', 'scale': 1, 'unit': '', 'pair': 91, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'PV energy total lifetime LOW'},

        # Temperatures
        93: {'name': 'inverter_temp', 'scale': 0.1, 'unit': '°C', 'signed': True},
        94: {'name': 'ipm_temp', 'scale': 0.1, 'unit': '°C', 'signed': True},
        95: {'name': 'boost_temp', 'scale': 0.1, 'unit': '°C', 'signed': True},

        # Diagnostics
        104: {'name': 'derating_mode', 'scale': 1, 'unit': ''},
        105: {'name': 'fault_code', 'scale': 1, 'unit': ''},
        112: {'name': 'warning_code', 'scale': 1, 'unit': ''},

        # Battery AC Charge Energy (SPH 3-6kW V201 with newer firmware)
        115: {'name': 'ac_charge_energy_total', 'scale': 0.1, 'unit': 'kWh', 'desc': 'Total energy charged from AC/grid to battery'},
    },
    'holding_registers': {
        # Basic Control
        0: {'name': 'on_off', 'scale': 1, 'unit': '', 'access': 'RW', 'desc': '0=Off, 1=On'},
        3: {'name': 'active_power_rate', 'scale': 1, 'unit': '%', 'access': 'RW'},

        # Export Limit Control
        122: {'name': 'export_limit_mode', 'scale': 1, 'unit': '', 'access': 'RW',
              'desc': 'Export limit mode: 0=Disabled, 1=RS485'},
        123: {'name': 'export_limit_power', 'scale': 0.1, 'unit': '%', 'access': 'RW',
              'desc': 'Export limit power percentage (0-100%)'},

        # Load First Battery Minimum SOC
        # Not in official Growatt Modbus protocol documentation.
        # Source: https://www.photovoltaikforum.com/thread/192228-growatt-sph-modbus-rtu-rj45-pinout-und-register-beschreibung/?postID=3017838#post3017838
        # Also confirmed by homeassistant-solax-modbus plugin_growatt.py (register 608, GEN3/SPH).
        608: {'name': 'load_first_battery_minimum_soc', 'scale': 1, 'unit': '%', 'access': 'RW',
              'valid_range': (10, 100),
              'desc': 'Minimum battery SOC in Load First mode — inverter stops discharging below this level (10-100%)'},

        # Battery Management Control (1000+ range)
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
               'desc': 'Period 1 end time (hex-packed: hours*256+minutes, e.g. 22:00 = 0x1600 = 5632)'},
        1102: {'name': 'time_period_1_enable', 'scale': 1, 'unit': '', 'access': 'RW',
               'desc': 'Enable time period 1',
               'values': {
                   0: 'Disabled',
                   1: 'Enabled'
               }},

        # Time Period 2 Control
        1103: {'name': 'time_period_2_start', 'scale': 1, 'unit': '', 'access': 'RW',
               'valid_range': (0, 2359),
               'desc': 'Period 2 start time (hex-packed: hours*256+minutes)'},
        1104: {'name': 'time_period_2_end', 'scale': 1, 'unit': '', 'access': 'RW',
               'valid_range': (0, 2359),
               'desc': 'Period 2 end time (hex-packed: hours*256+minutes)'},
        1105: {'name': 'time_period_2_enable', 'scale': 1, 'unit': '', 'access': 'RW',
               'desc': 'Enable time period 2',
               'values': {
                   0: 'Disabled',
                   1: 'Enabled'
               }},

        # Time Period 3 Control
        1106: {'name': 'time_period_3_start', 'scale': 1, 'unit': '', 'access': 'RW',
               'valid_range': (0, 2359),
               'desc': 'Period 3 start time (hex-packed: hours*256+minutes)'},
        1107: {'name': 'time_period_3_end', 'scale': 1, 'unit': '', 'access': 'RW',
               'valid_range': (0, 2359),
               'desc': 'Period 3 end time (hex-packed: hours*256+minutes)'},
        1108: {'name': 'time_period_3_enable', 'scale': 1, 'unit': '', 'access': 'RW',
               'desc': 'Enable time period 3',
               'values': {
                   0: 'Disabled',
                   1: 'Enabled'
               }},

        # Battery First extended time slots 4-6 (GEN3, registers 1017-1025)
        1017: {'name': 'batt_first_time_period_4_start',  'scale': 1, 'unit': '', 'access': 'RW', 'valid_range': (0, 5947), 'desc': 'Battery First period 4 start (hex-packed)'},
        1018: {'name': 'batt_first_time_period_4_end',    'scale': 1, 'unit': '', 'access': 'RW', 'valid_range': (0, 5947), 'desc': 'Battery First period 4 end (hex-packed)'},
        1019: {'name': 'batt_first_time_period_4_enable', 'scale': 1, 'unit': '', 'access': 'RW', 'values': {0: 'Disabled', 1: 'Enabled'}, 'desc': 'Enable Battery First period 4'},
        1020: {'name': 'batt_first_time_period_5_start',  'scale': 1, 'unit': '', 'access': 'RW', 'valid_range': (0, 5947), 'desc': 'Battery First period 5 start (hex-packed)'},
        1021: {'name': 'batt_first_time_period_5_end',    'scale': 1, 'unit': '', 'access': 'RW', 'valid_range': (0, 5947), 'desc': 'Battery First period 5 end (hex-packed)'},
        1022: {'name': 'batt_first_time_period_5_enable', 'scale': 1, 'unit': '', 'access': 'RW', 'values': {0: 'Disabled', 1: 'Enabled'}, 'desc': 'Enable Battery First period 5'},
        1023: {'name': 'batt_first_time_period_6_start',  'scale': 1, 'unit': '', 'access': 'RW', 'valid_range': (0, 5947), 'desc': 'Battery First period 6 start (hex-packed)'},
        1024: {'name': 'batt_first_time_period_6_end',    'scale': 1, 'unit': '', 'access': 'RW', 'valid_range': (0, 5947), 'desc': 'Battery First period 6 end (hex-packed)'},
        1025: {'name': 'batt_first_time_period_6_enable', 'scale': 1, 'unit': '', 'access': 'RW', 'values': {0: 'Disabled', 1: 'Enabled'}, 'desc': 'Enable Battery First period 6'},

        # Grid First extended time slots 4-6 (GEN3, registers 1026-1034)
        1026: {'name': 'grid_first_time_period_4_start',  'scale': 1, 'unit': '', 'access': 'RW', 'valid_range': (0, 5947), 'desc': 'Grid First period 4 start (hex-packed)'},
        1027: {'name': 'grid_first_time_period_4_end',    'scale': 1, 'unit': '', 'access': 'RW', 'valid_range': (0, 5947), 'desc': 'Grid First period 4 end (hex-packed)'},
        1028: {'name': 'grid_first_time_period_4_enable', 'scale': 1, 'unit': '', 'access': 'RW', 'values': {0: 'Disabled', 1: 'Enabled'}, 'desc': 'Enable Grid First period 4'},
        1029: {'name': 'grid_first_time_period_5_start',  'scale': 1, 'unit': '', 'access': 'RW', 'valid_range': (0, 5947), 'desc': 'Grid First period 5 start (hex-packed)'},
        1030: {'name': 'grid_first_time_period_5_end',    'scale': 1, 'unit': '', 'access': 'RW', 'valid_range': (0, 5947), 'desc': 'Grid First period 5 end (hex-packed)'},
        1031: {'name': 'grid_first_time_period_5_enable', 'scale': 1, 'unit': '', 'access': 'RW', 'values': {0: 'Disabled', 1: 'Enabled'}, 'desc': 'Enable Grid First period 5'},
        1032: {'name': 'grid_first_time_period_6_start',  'scale': 1, 'unit': '', 'access': 'RW', 'valid_range': (0, 5947), 'desc': 'Grid First period 6 start (hex-packed)'},
        1033: {'name': 'grid_first_time_period_6_end',    'scale': 1, 'unit': '', 'access': 'RW', 'valid_range': (0, 5947), 'desc': 'Grid First period 6 end (hex-packed)'},
        1034: {'name': 'grid_first_time_period_6_enable', 'scale': 1, 'unit': '', 'access': 'RW', 'values': {0: 'Disabled', 1: 'Enabled'}, 'desc': 'Enable Grid First period 6'},

        # Grid First extended time slots 7-9 (GEN3, registers 1080-1088)
        1080: {'name': 'grid_first_time_period_7_start',  'scale': 1, 'unit': '', 'access': 'RW', 'valid_range': (0, 5947), 'desc': 'Grid First period 7 start (hex-packed)'},
        1081: {'name': 'grid_first_time_period_7_end',    'scale': 1, 'unit': '', 'access': 'RW', 'valid_range': (0, 5947), 'desc': 'Grid First period 7 end (hex-packed)'},
        1082: {'name': 'grid_first_time_period_7_enable', 'scale': 1, 'unit': '', 'access': 'RW', 'values': {0: 'Disabled', 1: 'Enabled'}, 'desc': 'Enable Grid First period 7'},
        1083: {'name': 'grid_first_time_period_8_start',  'scale': 1, 'unit': '', 'access': 'RW', 'valid_range': (0, 5947), 'desc': 'Grid First period 8 start (hex-packed)'},
        1084: {'name': 'grid_first_time_period_8_end',    'scale': 1, 'unit': '', 'access': 'RW', 'valid_range': (0, 5947), 'desc': 'Grid First period 8 end (hex-packed)'},
        1085: {'name': 'grid_first_time_period_8_enable', 'scale': 1, 'unit': '', 'access': 'RW', 'values': {0: 'Disabled', 1: 'Enabled'}, 'desc': 'Enable Grid First period 8'},
        1086: {'name': 'grid_first_time_period_9_start',  'scale': 1, 'unit': '', 'access': 'RW', 'valid_range': (0, 5947), 'desc': 'Grid First period 9 start (hex-packed)'},
        1087: {'name': 'grid_first_time_period_9_end',    'scale': 1, 'unit': '', 'access': 'RW', 'valid_range': (0, 5947), 'desc': 'Grid First period 9 end (hex-packed)'},
        1088: {'name': 'grid_first_time_period_9_enable', 'scale': 1, 'unit': '', 'access': 'RW', 'values': {0: 'Disabled', 1: 'Enabled'}, 'desc': 'Enable Grid First period 9'},

        # Safety/compliance diagnostic registers (read-only, Issue #282)
        235: {'name': 'ntognd_detect',     'scale': 1, 'unit': '', 'access': 'R', 'desc': '0=Disable, 1=Enable — NToGND detection'},
        236: {'name': 'nonstd_vac_enable', 'scale': 1, 'unit': '', 'access': 'R', 'desc': '0=Disable, 1=Grade1, 2=Grade2 — non-standard VAC'},
        237: {'name': 'enable_spec_set',   'scale': 1, 'unit': '', 'access': 'R', 'desc': 'Regional spec bitmask (Bit0=Hungary)'},
        238: {'name': 'fast_mppt_enable',  'scale': 1, 'unit': '', 'access': 'R', 'desc': '0-2 — fast MPPT (Reserved)'},
    }
}

# SPH 7000-10000 (Higher power version)
SPH_7000_10000 = {
    'name': 'SPH Seres 7-10KW',
    'description': 'Single-phase hybrid inverter with battery storage (7-10kW)',
    'notes': 'Uses 0-124 register range. Same registers as 3-6kW model, higher power rating.',
    'use_mppt_energy_today': True,  # Reg 53/54 = system AC output incl. battery discharge; use per-MPPT DC sum instead
    'input_registers': {
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

        # Per V1.39: regs 13-22 are PV3-PV5 channel registers (voltage, current, power H/L).
        # Standard SPH 7-10kW has 2 MPPT strings — PV3+ registers return 0 or are unused.
        # Battery data is in the storage range (1000+) — see below.
        17: {'name': 'ppv4_power_high', 'scale': 1, 'unit': '', 'pair': 18, 'desc': 'PV4 power HIGH word (0 if no PV4 string)'},
        18: {'name': 'ppv4_power_low', 'scale': 1, 'unit': '', 'pair': 17, 'combined_scale': 0.1, 'combined_unit': 'W', 'desc': 'PV4 power LOW word (0 if no PV4 string)'},

        # Battery — storage range (V1.39 correct registers — Issue #283)
        1009: {'name': 'discharge_power_high', 'scale': 1, 'unit': '', 'pair': 1010},
        1010: {'name': 'discharge_power_low', 'scale': 1, 'unit': '', 'pair': 1009, 'combined_scale': 0.1, 'combined_unit': 'W'},
        1011: {'name': 'charge_power_high', 'scale': 1, 'unit': '', 'pair': 1012},
        1012: {'name': 'charge_power_low', 'scale': 1, 'unit': '', 'pair': 1011, 'combined_scale': 0.1, 'combined_unit': 'W'},
        1013: {'name': 'battery_voltage', 'scale': 0.1, 'unit': 'V', 'desc': 'Battery voltage (Vbat)'},
        1014: {'name': 'battery_soc', 'scale': 1, 'unit': '%', 'desc': 'Battery state of charge'},
        1040: {'name': 'battery_temp', 'scale': 0.1, 'unit': '°C', 'signed': True, 'desc': 'Battery temperature'},

        # AC Output
        37: {'name': 'ac_frequency', 'scale': 0.01, 'unit': 'Hz'},
        38: {'name': 'ac_voltage', 'scale': 0.1, 'unit': 'V'},
        39: {'name': 'ac_current', 'scale': 0.1, 'unit': 'A'},
        40: {'name': 'ac_power_high', 'scale': 1, 'unit': '', 'pair': 41},
        41: {'name': 'ac_power_low', 'scale': 1, 'unit': '', 'pair': 40, 'combined_scale': 0.1, 'combined_unit': 'W'},

        # Energy
        53: {'name': 'energy_today_high', 'scale': 1, 'unit': '', 'pair': 54},
        54: {'name': 'energy_today_low', 'scale': 1, 'unit': '', 'pair': 53, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        55: {'name': 'energy_total_high', 'scale': 1, 'unit': '', 'pair': 56},
        56: {'name': 'energy_total_low', 'scale': 1, 'unit': '', 'pair': 55, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        57: {'name': 'time_total_high', 'scale': 1, 'unit': '', 'pair': 58},
        58: {'name': 'time_total_low', 'scale': 1, 'unit': '', 'pair': 57, 'combined_scale': 0.5, 'combined_unit': 'h'},

        # Per-string DC energy (today and lifetime totals) — confirmed via scan #131
        59: {'name': 'pv1_energy_today_high', 'scale': 1, 'unit': '', 'pair': 60, 'desc': 'PV1 DC energy today HIGH'},
        60: {'name': 'pv1_energy_today_low', 'scale': 1, 'unit': '', 'pair': 59, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'PV1 DC energy today LOW'},
        61: {'name': 'pv1_energy_total_high', 'scale': 1, 'unit': '', 'pair': 62, 'desc': 'PV1 DC energy total HIGH'},
        62: {'name': 'pv1_energy_total_low', 'scale': 1, 'unit': '', 'pair': 61, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'PV1 DC energy total LOW'},
        63: {'name': 'pv2_energy_today_high', 'scale': 1, 'unit': '', 'pair': 64, 'desc': 'PV2 DC energy today HIGH'},
        64: {'name': 'pv2_energy_today_low', 'scale': 1, 'unit': '', 'pair': 63, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'PV2 DC energy today LOW'},
        65: {'name': 'pv2_energy_total_high', 'scale': 1, 'unit': '', 'pair': 66, 'desc': 'PV2 DC energy total HIGH'},
        66: {'name': 'pv2_energy_total_low', 'scale': 1, 'unit': '', 'pair': 65, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'PV2 DC energy total LOW'},

        # Temperatures
        93: {'name': 'inverter_temp', 'scale': 0.1, 'unit': '°C', 'signed': True},
        94: {'name': 'ipm_temp', 'scale': 0.1, 'unit': '°C', 'signed': True},
        95: {'name': 'boost_temp', 'scale': 0.1, 'unit': '°C', 'signed': True},

        # Diagnostics
        104: {'name': 'derating_mode', 'scale': 1, 'unit': ''},
        105: {'name': 'fault_code', 'scale': 1, 'unit': ''},
        112: {'name': 'warning_code', 'scale': 1, 'unit': ''},
    },
    'holding_registers': {
        # Basic Control
        0: {'name': 'on_off', 'scale': 1, 'unit': '', 'access': 'RW', 'desc': '0=Off, 1=On'},
        3: {'name': 'active_power_rate', 'scale': 1, 'unit': '%', 'access': 'RW'},

        # Export Limit Control
        122: {'name': 'export_limit_mode', 'scale': 1, 'unit': '', 'access': 'RW',
              'desc': 'Export limit mode: 0=Disabled, 1=RS485'},
        123: {'name': 'export_limit_power', 'scale': 0.1, 'unit': '%', 'access': 'RW',
              'desc': 'Export limit power percentage (0-100%)'},

        # Load First Battery Minimum SOC
        # Not in official Growatt Modbus protocol documentation.
        # Source: https://www.photovoltaikforum.com/thread/192228-growatt-sph-modbus-rtu-rj45-pinout-und-register-beschreibung/?postID=3017838#post3017838
        # Also confirmed by homeassistant-solax-modbus plugin_growatt.py (register 608, GEN3/SPH).
        608: {'name': 'load_first_battery_minimum_soc', 'scale': 1, 'unit': '%', 'access': 'RW',
              'valid_range': (10, 100),
              'desc': 'Minimum battery SOC in Load First mode — inverter stops discharging below this level (10-100%)'},

        # Battery Management Control (1000+ range)
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
               'desc': 'Period 1 end time (hex-packed: hours*256+minutes, e.g. 22:00 = 0x1600 = 5632)'},
        1102: {'name': 'time_period_1_enable', 'scale': 1, 'unit': '', 'access': 'RW',
               'desc': 'Enable time period 1',
               'values': {
                   0: 'Disabled',
                   1: 'Enabled'
               }},

        # Time Period 2 Control
        1103: {'name': 'time_period_2_start', 'scale': 1, 'unit': '', 'access': 'RW',
               'valid_range': (0, 2359),
               'desc': 'Period 2 start time (hex-packed: hours*256+minutes)'},
        1104: {'name': 'time_period_2_end', 'scale': 1, 'unit': '', 'access': 'RW',
               'valid_range': (0, 2359),
               'desc': 'Period 2 end time (hex-packed: hours*256+minutes)'},
        1105: {'name': 'time_period_2_enable', 'scale': 1, 'unit': '', 'access': 'RW',
               'desc': 'Enable time period 2',
               'values': {
                   0: 'Disabled',
                   1: 'Enabled'
               }},

        # Time Period 3 Control
        1106: {'name': 'time_period_3_start', 'scale': 1, 'unit': '', 'access': 'RW',
               'valid_range': (0, 2359),
               'desc': 'Period 3 start time (hex-packed: hours*256+minutes)'},
        1107: {'name': 'time_period_3_end', 'scale': 1, 'unit': '', 'access': 'RW',
               'valid_range': (0, 2359),
               'desc': 'Period 3 end time (hex-packed: hours*256+minutes)'},
        1108: {'name': 'time_period_3_enable', 'scale': 1, 'unit': '', 'access': 'RW',
               'desc': 'Enable time period 3',
               'values': {
                   0: 'Disabled',
                   1: 'Enabled'
               }},

        # Battery First extended time slots 4-6 (GEN3, registers 1017-1025)
        1017: {'name': 'batt_first_time_period_4_start',  'scale': 1, 'unit': '', 'access': 'RW', 'valid_range': (0, 5947), 'desc': 'Battery First period 4 start (hex-packed)'},
        1018: {'name': 'batt_first_time_period_4_end',    'scale': 1, 'unit': '', 'access': 'RW', 'valid_range': (0, 5947), 'desc': 'Battery First period 4 end (hex-packed)'},
        1019: {'name': 'batt_first_time_period_4_enable', 'scale': 1, 'unit': '', 'access': 'RW', 'values': {0: 'Disabled', 1: 'Enabled'}, 'desc': 'Enable Battery First period 4'},
        1020: {'name': 'batt_first_time_period_5_start',  'scale': 1, 'unit': '', 'access': 'RW', 'valid_range': (0, 5947), 'desc': 'Battery First period 5 start (hex-packed)'},
        1021: {'name': 'batt_first_time_period_5_end',    'scale': 1, 'unit': '', 'access': 'RW', 'valid_range': (0, 5947), 'desc': 'Battery First period 5 end (hex-packed)'},
        1022: {'name': 'batt_first_time_period_5_enable', 'scale': 1, 'unit': '', 'access': 'RW', 'values': {0: 'Disabled', 1: 'Enabled'}, 'desc': 'Enable Battery First period 5'},
        1023: {'name': 'batt_first_time_period_6_start',  'scale': 1, 'unit': '', 'access': 'RW', 'valid_range': (0, 5947), 'desc': 'Battery First period 6 start (hex-packed)'},
        1024: {'name': 'batt_first_time_period_6_end',    'scale': 1, 'unit': '', 'access': 'RW', 'valid_range': (0, 5947), 'desc': 'Battery First period 6 end (hex-packed)'},
        1025: {'name': 'batt_first_time_period_6_enable', 'scale': 1, 'unit': '', 'access': 'RW', 'values': {0: 'Disabled', 1: 'Enabled'}, 'desc': 'Enable Battery First period 6'},

        # Grid First extended time slots 4-6 (GEN3, registers 1026-1034)
        1026: {'name': 'grid_first_time_period_4_start',  'scale': 1, 'unit': '', 'access': 'RW', 'valid_range': (0, 5947), 'desc': 'Grid First period 4 start (hex-packed)'},
        1027: {'name': 'grid_first_time_period_4_end',    'scale': 1, 'unit': '', 'access': 'RW', 'valid_range': (0, 5947), 'desc': 'Grid First period 4 end (hex-packed)'},
        1028: {'name': 'grid_first_time_period_4_enable', 'scale': 1, 'unit': '', 'access': 'RW', 'values': {0: 'Disabled', 1: 'Enabled'}, 'desc': 'Enable Grid First period 4'},
        1029: {'name': 'grid_first_time_period_5_start',  'scale': 1, 'unit': '', 'access': 'RW', 'valid_range': (0, 5947), 'desc': 'Grid First period 5 start (hex-packed)'},
        1030: {'name': 'grid_first_time_period_5_end',    'scale': 1, 'unit': '', 'access': 'RW', 'valid_range': (0, 5947), 'desc': 'Grid First period 5 end (hex-packed)'},
        1031: {'name': 'grid_first_time_period_5_enable', 'scale': 1, 'unit': '', 'access': 'RW', 'values': {0: 'Disabled', 1: 'Enabled'}, 'desc': 'Enable Grid First period 5'},
        1032: {'name': 'grid_first_time_period_6_start',  'scale': 1, 'unit': '', 'access': 'RW', 'valid_range': (0, 5947), 'desc': 'Grid First period 6 start (hex-packed)'},
        1033: {'name': 'grid_first_time_period_6_end',    'scale': 1, 'unit': '', 'access': 'RW', 'valid_range': (0, 5947), 'desc': 'Grid First period 6 end (hex-packed)'},
        1034: {'name': 'grid_first_time_period_6_enable', 'scale': 1, 'unit': '', 'access': 'RW', 'values': {0: 'Disabled', 1: 'Enabled'}, 'desc': 'Enable Grid First period 6'},

        # Grid First extended time slots 7-9 (GEN3, registers 1080-1088)
        1080: {'name': 'grid_first_time_period_7_start',  'scale': 1, 'unit': '', 'access': 'RW', 'valid_range': (0, 5947), 'desc': 'Grid First period 7 start (hex-packed)'},
        1081: {'name': 'grid_first_time_period_7_end',    'scale': 1, 'unit': '', 'access': 'RW', 'valid_range': (0, 5947), 'desc': 'Grid First period 7 end (hex-packed)'},
        1082: {'name': 'grid_first_time_period_7_enable', 'scale': 1, 'unit': '', 'access': 'RW', 'values': {0: 'Disabled', 1: 'Enabled'}, 'desc': 'Enable Grid First period 7'},
        1083: {'name': 'grid_first_time_period_8_start',  'scale': 1, 'unit': '', 'access': 'RW', 'valid_range': (0, 5947), 'desc': 'Grid First period 8 start (hex-packed)'},
        1084: {'name': 'grid_first_time_period_8_end',    'scale': 1, 'unit': '', 'access': 'RW', 'valid_range': (0, 5947), 'desc': 'Grid First period 8 end (hex-packed)'},
        1085: {'name': 'grid_first_time_period_8_enable', 'scale': 1, 'unit': '', 'access': 'RW', 'values': {0: 'Disabled', 1: 'Enabled'}, 'desc': 'Enable Grid First period 8'},
        1086: {'name': 'grid_first_time_period_9_start',  'scale': 1, 'unit': '', 'access': 'RW', 'valid_range': (0, 5947), 'desc': 'Grid First period 9 start (hex-packed)'},
        1087: {'name': 'grid_first_time_period_9_end',    'scale': 1, 'unit': '', 'access': 'RW', 'valid_range': (0, 5947), 'desc': 'Grid First period 9 end (hex-packed)'},
        1088: {'name': 'grid_first_time_period_9_enable', 'scale': 1, 'unit': '', 'access': 'RW', 'values': {0: 'Disabled', 1: 'Enabled'}, 'desc': 'Enable Grid First period 9'},

        # Safety/compliance diagnostic registers (read-only, Issue #282)
        235: {'name': 'ntognd_detect',     'scale': 1, 'unit': '', 'access': 'R', 'desc': '0=Disable, 1=Enable — NToGND detection'},
        236: {'name': 'nonstd_vac_enable', 'scale': 1, 'unit': '', 'access': 'R', 'desc': '0=Disable, 1=Grade1, 2=Grade2 — non-standard VAC'},
        237: {'name': 'enable_spec_set',   'scale': 1, 'unit': '', 'access': 'R', 'desc': 'Regional spec bitmask (Bit0=Hungary)'},
        238: {'name': 'fast_mppt_enable',  'scale': 1, 'unit': '', 'access': 'R', 'desc': '0-2 — fast MPPT (Reserved)'},
    }
}

# SPH/SPM 8000-10000 HU (High-power models with 3 MPPTs and storage range)
SPH_8000_10000_HU = {
    'name': 'SPH/SPM 8000-10000TL-HU',
    'description': 'Single-phase hybrid inverter with battery storage and 3 MPPT inputs (8-10kW). Models: SPH/SPM 8000-10000TL-HU.',
    'notes': 'Uses 0-124 and 1000-1124 register ranges. Single-phase with 3 PV strings, detailed power flow and energy tracking.',
    'use_mppt_energy_today': True,  # Reg 53/54 = system AC output incl. battery discharge; use per-MPPT DC sum instead
    'input_registers': {
        # === BASE RANGE (0-124) - Same as SPH_7000_10000 ===
        **SPH_7000_10000['input_registers'],

        # PV String 3 (3rd MPPT on HU models)
        # Per V1.39: regs 13-14 = Ppv3 H/L (PV3 power). Base profile leaves these undefined for
        # standard 2-string models; HU defines them explicitly for its 3rd MPPT string.
        11: {'name': 'pv3_voltage', 'scale': 0.1, 'unit': 'V', 'desc': 'PV3 voltage (0 if not connected)'},
        12: {'name': 'pv3_current', 'scale': 0.1, 'unit': 'A', 'desc': 'PV3 current (0 if not connected)'},
        13: {'name': 'pv3_power_high', 'scale': 1, 'unit': '', 'pair': 14, 'desc': 'PV3 power HIGH (0 if not connected)'},
        14: {'name': 'pv3_power_low', 'scale': 1, 'unit': '', 'pair': 13, 'combined_scale': 0.1, 'combined_unit': 'W', 'desc': 'PV3 power LOW (0 if not connected)'},

        # Per V1.39: reg 15 = Vpv4 (PV4 voltage); reg 19 = Vpv5 (PV5 voltage). Named to avoid spurious
        # sensor creation — HU battery data comes from BMS registers (1086-1089), not base 1013/1040.
        15: {'name': 'battery_power_calc', 'scale': 1, 'unit': 'W', 'signed': True, 'desc': 'Calculated battery power (use with caution, BMS data more accurate)'},
        19: {'name': 'bms_type_legacy', 'scale': 1, 'unit': '', 'desc': 'Legacy BMS type (use BMS info at 1082+)'},

        # === STORAGE RANGE (1000-1124) - Power Flow and Energy Breakdown ===

        # System Work Mode
        1000: {'name': 'system_work_mode', 'scale': 1, 'unit': '', 'desc': 'Work mode'},

        # Battery Discharge/Charge Power
        1009: {'name': 'discharge_power_high', 'scale': 1, 'unit': '', 'pair': 1010},
        1010: {'name': 'discharge_power_low', 'scale': 1, 'unit': '', 'pair': 1009, 'combined_scale': 0.1, 'combined_unit': 'W'},
        1011: {'name': 'charge_power_high', 'scale': 1, 'unit': '', 'pair': 1012},
        1012: {'name': 'charge_power_low', 'scale': 1, 'unit': '', 'pair': 1011, 'combined_scale': 0.1, 'combined_unit': 'W'},

        # Power Flow - Critical for grid import/export tracking
        1015: {'name': 'power_to_user_high', 'scale': 1, 'unit': '', 'pair': 1016, 'desc': 'Power to user (grid import when positive)'},
        1016: {'name': 'power_to_user_low', 'scale': 1, 'unit': '', 'pair': 1015, 'combined_scale': 0.1, 'combined_unit': 'W'},
        1021: {'name': 'power_to_load_high', 'scale': 1, 'unit': '', 'pair': 1022, 'desc': 'Total load power consumption'},
        1022: {'name': 'power_to_load_low', 'scale': 1, 'unit': '', 'pair': 1021, 'combined_scale': 0.1, 'combined_unit': 'W'},
        1029: {'name': 'power_to_grid_high', 'scale': 1, 'unit': '', 'pair': 1030, 'desc': 'Power to grid (negative=export, positive=import)'},
        1030: {'name': 'power_to_grid_low', 'scale': 1, 'unit': '', 'pair': 1029, 'combined_scale': 0.1, 'combined_unit': 'W', 'signed': True},
        1037: {'name': 'self_consumption_power_high', 'scale': 1, 'unit': '', 'pair': 1038},
        1038: {'name': 'self_consumption_power_low', 'scale': 1, 'unit': '', 'pair': 1037, 'combined_scale': 0.1, 'combined_unit': 'W'},
        1039: {'name': 'self_consumption_percentage', 'scale': 1, 'unit': '%'},

        # Energy Breakdown - Hardware registers for grid import/export
        1044: {'name': 'energy_to_user_today_high', 'scale': 1, 'unit': '', 'pair': 1045, 'desc': 'Grid import energy today'},
        1045: {'name': 'energy_to_user_today_low', 'scale': 1, 'unit': '', 'pair': 1044, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        1046: {'name': 'energy_to_user_total_high', 'scale': 1, 'unit': '', 'pair': 1047, 'desc': 'Grid import energy total'},
        1047: {'name': 'energy_to_user_total_low', 'scale': 1, 'unit': '', 'pair': 1046, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        1048: {'name': 'energy_to_grid_today_high', 'scale': 1, 'unit': '', 'pair': 1049, 'desc': 'Grid export energy today'},
        1049: {'name': 'energy_to_grid_today_low', 'scale': 1, 'unit': '', 'pair': 1048, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        1050: {'name': 'energy_to_grid_total_high', 'scale': 1, 'unit': '', 'pair': 1051, 'desc': 'Grid export energy total'},
        1051: {'name': 'energy_to_grid_total_low', 'scale': 1, 'unit': '', 'pair': 1050, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        1052: {'name': 'battery_discharge_today_high', 'scale': 1, 'unit': '', 'pair': 1053, 'desc': 'Battery discharge energy today HIGH'},
        1053: {'name': 'battery_discharge_today_low', 'scale': 1, 'unit': '', 'pair': 1052, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        1054: {'name': 'battery_discharge_total_high', 'scale': 1, 'unit': '', 'pair': 1055, 'desc': 'Battery discharge energy total HIGH'},
        1055: {'name': 'battery_discharge_total_low', 'scale': 1, 'unit': '', 'pair': 1054, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        1056: {'name': 'battery_charge_today_high', 'scale': 1, 'unit': '', 'pair': 1057, 'desc': 'Battery charge energy today HIGH'},
        1057: {'name': 'battery_charge_today_low', 'scale': 1, 'unit': '', 'pair': 1056, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        1058: {'name': 'battery_charge_total_high', 'scale': 1, 'unit': '', 'pair': 1059, 'desc': 'Battery charge energy total HIGH'},
        1059: {'name': 'battery_charge_total_low', 'scale': 1, 'unit': '', 'pair': 1058, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        1060: {'name': 'load_energy_today_high', 'scale': 1, 'unit': '', 'pair': 1061},
        1061: {'name': 'load_energy_today_low', 'scale': 1, 'unit': '', 'pair': 1060, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        1062: {'name': 'load_energy_total_high', 'scale': 1, 'unit': '', 'pair': 1063},
        1063: {'name': 'load_energy_total_low', 'scale': 1, 'unit': '', 'pair': 1062, 'combined_scale': 0.1, 'combined_unit': 'kWh'},

        # BMS Information (1082-1124) - Battery Management System data
        # Per Growatt Modbus RTU Protocol V1.24 specification
        1082: {'name': 'bms_status_old', 'scale': 1, 'unit': '', 'desc': 'Status Old from BMS'},
        1083: {'name': 'bms_status', 'scale': 1, 'unit': '', 'desc': 'Status from BMS'},
        1084: {'name': 'bms_error_old', 'scale': 1, 'unit': '', 'desc': 'Error info Old from BMS'},
        1085: {'name': 'bms_error', 'scale': 1, 'unit': '', 'desc': 'Error information from BMS'},
        1086: {'name': 'battery_soc', 'scale': 1, 'unit': '%', 'desc': 'SOC from BMS (actual battery state of charge)'},
        1087: {'name': 'battery_voltage', 'scale': 0.1, 'unit': 'V', 'desc': 'Battery voltage from BMS'},
        1088: {'name': 'battery_current', 'scale': 0.1, 'unit': 'A', 'desc': 'Battery current from BMS', 'signed': True},
        1089: {'name': 'battery_temp', 'scale': 0.1, 'unit': '°C', 'desc': 'Battery temperature from BMS', 'signed': True},
        1090: {'name': 'bms_max_current', 'scale': 0.1, 'unit': 'A', 'desc': 'Max charge/discharge current from BMS'},
        1091: {'name': 'bms_gauge_rm', 'scale': 1, 'unit': '', 'desc': 'Gauge RM from BMS'},
        1092: {'name': 'bms_gauge_fcc', 'scale': 1, 'unit': '', 'desc': 'Gauge FCC from BMS'},
        1093: {'name': 'bms_fw_version', 'scale': 1, 'unit': '', 'desc': 'BMS firmware version'},
        1094: {'name': 'bms_delta_volt', 'scale': 0.001, 'unit': 'V', 'desc': 'Delta V from BMS'},
        1095: {'name': 'bms_cycle_count', 'scale': 1, 'unit': '', 'desc': 'Cycle Count from BMS'},
        1096: {'name': 'bms_soh', 'scale': 1, 'unit': '%', 'desc': 'SOH (State of Health) from BMS'},
        1097: {'name': 'bms_constant_volt', 'scale': 0.1, 'unit': 'V', 'desc': 'CV voltage (float/absorption) from BMS'},
        1098: {'name': 'bms_warn_info_old', 'scale': 1, 'unit': '', 'desc': 'Warning info old from BMS'},
        1099: {'name': 'bms_warn_info', 'scale': 1, 'unit': '', 'desc': 'Warning info from BMS'},
        1108: {'name': 'bms_max_cell_volt', 'scale': 0.001, 'unit': 'V', 'desc': 'Maximum single battery voltage'},
        1109: {'name': 'bms_min_cell_volt', 'scale': 0.001, 'unit': 'V', 'desc': 'Lowest single battery voltage'},
        1110: {'name': 'bms_module_num', 'scale': 1, 'unit': '', 'desc': 'Battery parallel number'},
        1111: {'name': 'bms_battery_count', 'scale': 1, 'unit': '', 'desc': 'Number of batteries'},
        1119: {'name': 'bms_max_soc', 'scale': 1, 'unit': '%', 'desc': 'Parallel maximum SOC'},
        1120: {'name': 'bms_min_soc', 'scale': 1, 'unit': '%', 'desc': 'Parallel minimum SOC'},
    },
    'holding_registers': {
        # SPH HU uses different register architecture than SPH 7-10kW
        # Battery management registers (1044, 1070-1071, 1090-1092, 1100-1108) return Modbus exceptions
        # These settings must be configured via Growatt ShinePhone app or inverter LCD
        # 1000+ range has INPUT registers (BMS data) but NOT corresponding HOLDING registers

        # Basic Control (0-10 range)
        0: {'name': 'on_off', 'scale': 1, 'unit': '', 'access': 'RW', 'desc': '0=Off, 1=On'},
        3: {'name': 'active_power_rate', 'scale': 1, 'unit': '%', 'access': 'RW'},

        # HU-specific control (1000+ range)
        1008: {'name': 'system_enable', 'scale': 1, 'unit': '', 'access': 'RW',
               'desc': 'System enable control',
               'values': {
                   0: 'Disabled',
                   1: 'Enabled'
               }},
    }
}

# SPH 3000-6000 V2.01 Protocol (V1.39 + VPP 2.01 registers)
# V2.01 adds 30000+ range on top of legacy registers for complete functionality
SPH_3000_6000_V201 = {
    'name': 'SPH Series 3-6kW (V2.01)',
    'description': 'Single-phase hybrid inverter with battery storage (3-6kW) and VPP Protocol V2.01',
    'notes': 'Combines legacy (0-124 range) with V2.01 (30000+ range). Overlapping values served at both addresses.',
    'use_mppt_energy_today': True,  # Reg 53/54 = system AC output incl. battery discharge; use per-MPPT DC sum instead
    'input_registers': {
        # === Legacy REGISTERS (0-124 range) ===
        **SPH_3000_6000['input_registers'],

        # === STORAGE RANGE REGISTERS (1000-1124) ===
        # Power Flow (storage range — Modbus RTU V1.20, issue #207)
        # 1021: PactouserTotal  = AC power to user total (grid import)
        # 1029: Pactogrid total = AC power to grid total (grid export)
        # 1037: PLocalLoad total = INV power to local load total
        1021: {'name': 'power_to_user_high', 'scale': 1, 'unit': '', 'pair': 1022, 'desc': 'AC power to user total H (PactouserTotal)'},
        1022: {'name': 'power_to_user_low', 'scale': 1, 'unit': '', 'pair': 1021, 'combined_scale': 0.1, 'combined_unit': 'W'},
        1029: {'name': 'power_to_grid_high', 'scale': 1, 'unit': '', 'pair': 1030, 'desc': 'AC power to grid total H (Pactogrid total)'},
        1030: {'name': 'power_to_grid_low', 'scale': 1, 'unit': '', 'pair': 1029, 'combined_scale': 0.1, 'combined_unit': 'W', 'signed': True},
        1037: {'name': 'power_to_load_high', 'scale': 1, 'unit': '', 'pair': 1038, 'desc': 'INV power to local load total H (PLocalLoad total)'},
        1038: {'name': 'power_to_load_low', 'scale': 1, 'unit': '', 'pair': 1037, 'combined_scale': 0.1, 'combined_unit': 'W'},

        # Grid Energy — import and export (storage range)
        1044: {'name': 'energy_to_user_today_high', 'scale': 1, 'unit': '', 'pair': 1045, 'desc': 'Energy to user today H (Etouser_today)'},
        1045: {'name': 'energy_to_user_today_low', 'scale': 1, 'unit': '', 'pair': 1044, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        1046: {'name': 'energy_to_user_total_high', 'scale': 1, 'unit': '', 'pair': 1047, 'desc': 'Energy to user total H'},
        1047: {'name': 'energy_to_user_total_low', 'scale': 1, 'unit': '', 'pair': 1046, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        1048: {'name': 'energy_to_grid_today_high', 'scale': 1, 'unit': '', 'pair': 1049},
        1049: {'name': 'energy_to_grid_today_low', 'scale': 1, 'unit': '', 'pair': 1048, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        1050: {'name': 'energy_to_grid_total_high', 'scale': 1, 'unit': '', 'pair': 1051},
        1051: {'name': 'energy_to_grid_total_low', 'scale': 1, 'unit': '', 'pair': 1050, 'combined_scale': 0.1, 'combined_unit': 'kWh'},

        # Grid Energy (from grid / import)
        1052: {'name': 'grid_import_energy_today_high', 'scale': 1, 'unit': '', 'pair': 1053},
        1053: {'name': 'grid_import_energy_today_low', 'scale': 1, 'unit': '', 'pair': 1052, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        1054: {'name': 'grid_import_energy_total_high', 'scale': 1, 'unit': '', 'pair': 1055},
        1055: {'name': 'grid_import_energy_total_low', 'scale': 1, 'unit': '', 'pair': 1054, 'combined_scale': 0.1, 'combined_unit': 'kWh'},

        # Load Energy
        1060: {'name': 'load_energy_today_high', 'scale': 1, 'unit': '', 'pair': 1061},
        1061: {'name': 'load_energy_today_low', 'scale': 1, 'unit': '', 'pair': 1060, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        1062: {'name': 'load_energy_total_high', 'scale': 1, 'unit': '', 'pair': 1063},
        1063: {'name': 'load_energy_total_low', 'scale': 1, 'unit': '', 'pair': 1062, 'combined_scale': 0.1, 'combined_unit': 'kWh'},

        # === MIN/MOD RANGE REGISTERS (3000-3124) ===
        # Grid Energy (to grid / export)
        3071: {'name': 'energy_to_grid_today_high_mod', 'scale': 1, 'unit': '', 'pair': 3072, 'maps_to': 'energy_to_grid_today'},
        3072: {'name': 'energy_to_grid_today_low_mod', 'scale': 1, 'unit': '', 'pair': 3071, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        3073: {'name': 'energy_to_grid_total_high_mod', 'scale': 1, 'unit': '', 'pair': 3074, 'maps_to': 'energy_to_grid_total'},
        3074: {'name': 'energy_to_grid_total_low_mod', 'scale': 1, 'unit': '', 'pair': 3073, 'combined_scale': 0.1, 'combined_unit': 'kWh'},

        # Load Energy
        3075: {'name': 'load_energy_today_high_mod', 'scale': 1, 'unit': '', 'pair': 3076, 'maps_to': 'load_energy_today'},
        3076: {'name': 'load_energy_today_low_mod', 'scale': 1, 'unit': '', 'pair': 3075, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        3077: {'name': 'load_energy_total_high_mod', 'scale': 1, 'unit': '', 'pair': 3078, 'maps_to': 'load_energy_total'},
        3078: {'name': 'load_energy_total_low_mod', 'scale': 1, 'unit': '', 'pair': 3077, 'combined_scale': 0.1, 'combined_unit': 'kWh'},

        # === V2.01 REGISTERS (31000+ range) ===
        **VPP_V201_STATUS,
        **VPP_V201_PV2_INPUT,
        **VPP_V201_PV2_TOTAL,

        # AC Output (overlaps with 37-41) — SPH-specific: includes reactive power;
        # meter_power has no maps_to (SPH gets power_to_grid from legacy 1000+ range).
        31100: {'name': 'ac_voltage_vpp', 'scale': 0.1, 'unit': 'V', 'maps_to': 'ac_voltage'},
        31101: {'name': 'ac_current_vpp', 'scale': 0.1, 'unit': 'A', 'maps_to': 'ac_current'},
        31102: {'name': 'ac_power_high_vpp', 'scale': 1, 'unit': '', 'pair': 31103, 'maps_to': 'ac_power'},
        31103: {'name': 'ac_power_low_vpp', 'scale': 1, 'unit': '', 'pair': 31102, 'combined_scale': 0.1, 'combined_unit': 'VA'},
        31104: {'name': 'ac_reactive_power_high', 'scale': 1, 'unit': '', 'pair': 31105},
        31105: {'name': 'ac_reactive_power_low', 'scale': 1, 'unit': '', 'pair': 31104, 'combined_scale': 0.1, 'combined_unit': 'var'},
        31106: {'name': 'ac_frequency_vpp', 'scale': 0.01, 'unit': 'Hz', 'maps_to': 'ac_frequency'},

        # Grid/Meter Power — no maps_to: SPH reads power_to_grid from 1000+ legacy range.
        31112: {'name': 'meter_power_high', 'scale': 1, 'unit': '', 'pair': 31113, 'desc': 'Grid power (same as backup power)'},
        31113: {'name': 'meter_power_low', 'scale': 1, 'unit': '', 'pair': 31112, 'combined_scale': 0.1, 'combined_unit': 'W', 'signed': True},

        # Load Power — maps_to 'load_power' (SPH name; MIN/TL-XH use 'power_to_load').
        31118: {'name': 'load_power_high_vpp', 'scale': 1, 'unit': '', 'pair': 31119, 'maps_to': 'load_power'},
        31119: {'name': 'load_power_low_vpp', 'scale': 1, 'unit': '', 'pair': 31118, 'combined_scale': 0.1, 'combined_unit': 'W'},

        **VPP_V201_ENERGY_1P,
        **VPP_V201_TEMPERATURE_1P,

        # Battery Cluster 1 State (31200–31222) — SPH-specific register layout.
        # Registers 31202–31209 are energy counters here (discharge today, charge total,
        # charge today, discharge total); TL-XH interprets them as charge/discharge power.
        # Per VPP Protocol V2.01: 31200–31201 is signed battery power
        # (positive = charge, negative = discharge).
        31200: {'name': 'battery_power_high', 'scale': 1, 'unit': '', 'pair': 31201},
        31201: {'name': 'battery_power_low', 'scale': 1, 'unit': '', 'pair': 31200, 'combined_scale': 0.1, 'combined_unit': 'W', 'signed': True},

        # Battery Energy (VPP registers - validated against scan data)
        31202: {'name': 'battery_discharge_today_high', 'scale': 1, 'unit': '', 'pair': 31203, 'desc': 'Battery discharge energy today HIGH'},
        31203: {'name': 'battery_discharge_today_low', 'scale': 1, 'unit': '', 'pair': 31202, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        31204: {'name': 'battery_charge_total_high', 'scale': 1, 'unit': '', 'pair': 31205, 'desc': 'Battery charge energy total HIGH'},
        31205: {'name': 'battery_charge_total_low', 'scale': 1, 'unit': '', 'pair': 31204, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        31206: {'name': 'battery_charge_today_high', 'scale': 1, 'unit': '', 'pair': 31207, 'desc': 'Battery charge energy today HIGH'},
        31207: {'name': 'battery_charge_today_low', 'scale': 1, 'unit': '', 'pair': 31206, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        31208: {'name': 'battery_discharge_total_high', 'scale': 1, 'unit': '', 'pair': 31209, 'desc': 'Battery discharge energy total HIGH'},
        31209: {'name': 'battery_discharge_total_low', 'scale': 1, 'unit': '', 'pair': 31208, 'combined_scale': 0.1, 'combined_unit': 'kWh'},

        31214: {'name': 'battery_voltage_vpp', 'scale': 0.1, 'unit': 'V', 'maps_to': 'battery_voltage', 'signed': True},
        31215: {'name': 'battery_current_vpp', 'scale': 0.1, 'unit': 'A', 'maps_to': 'battery_current', 'signed': True},
        31217: {'name': 'battery_soc_vpp', 'scale': 1, 'unit': '%', 'maps_to': 'battery_soc'},
        31218: {'name': 'battery_soh', 'scale': 1, 'unit': '%', 'desc': 'Battery state of health'},
        # Note: Registers 31220-31221 appear to contain incorrect data when paired as 32-bit
        # AC charge energy total is available in register 115 (legacy range) instead
        31222: {'name': 'battery_temp_vpp', 'scale': 0.1, 'unit': '°C', 'maps_to': 'battery_temp', 'signed': True},

        # Battery Cluster 2 State (31300-31323) - Optional second battery
        **VPP_V201_BATTERY2,
    },
    'holding_registers': {
        # === Legacy REGISTERS ===
        **SPH_3000_6000['holding_registers'],

        # === V2.01 REGISTERS (30000+ range) ===
        30000: {'name': 'dtc_code', 'scale': 1, 'unit': '', 'access': 'RO', 'desc': 'Device Type Code: 1000 for SPH 3-6kW', 'default': 3502},
        **VPP_V201_HOLDING_1P,
    }
}

# SPH 7000-10000 V2.01 Protocol
SPH_7000_10000_V201 = {
    'name': 'SPH Series 7-10kW (V2.01)',
    'description': 'Single-phase hybrid inverter with battery storage (7-10kW) and VPP Protocol V2.01',
    'notes': 'Combines legacy (0-124 range) with V2.01 (30000+ range). Overlapping values served at both addresses.',
    'use_mppt_energy_today': True,  # Reg 53/54 = system AC output incl. battery discharge; use per-MPPT DC sum instead
    'input_registers': {
        # === Legacy REGISTERS (0-124 range) ===
        **SPH_7000_10000['input_registers'],

        # === STORAGE RANGE REGISTERS (1000-1124) ===
        # Power Flow (storage range — Modbus RTU V1.20, issue #207)
        # 1021: PactouserTotal  = AC power to user total (grid import)
        # 1029: Pactogrid total = AC power to grid total (grid export)
        # 1037: PLocalLoad total = INV power to local load total
        1021: {'name': 'power_to_user_high', 'scale': 1, 'unit': '', 'pair': 1022, 'desc': 'AC power to user total H (PactouserTotal)'},
        1022: {'name': 'power_to_user_low', 'scale': 1, 'unit': '', 'pair': 1021, 'combined_scale': 0.1, 'combined_unit': 'W'},
        1029: {'name': 'power_to_grid_high', 'scale': 1, 'unit': '', 'pair': 1030, 'desc': 'AC power to grid total H (Pactogrid total)'},
        1030: {'name': 'power_to_grid_low', 'scale': 1, 'unit': '', 'pair': 1029, 'combined_scale': 0.1, 'combined_unit': 'W', 'signed': True},
        1037: {'name': 'power_to_load_high', 'scale': 1, 'unit': '', 'pair': 1038, 'desc': 'INV power to local load total H (PLocalLoad total)'},
        1038: {'name': 'power_to_load_low', 'scale': 1, 'unit': '', 'pair': 1037, 'combined_scale': 0.1, 'combined_unit': 'W'},

        # Grid Energy — import and export (storage range)
        1044: {'name': 'energy_to_user_today_high', 'scale': 1, 'unit': '', 'pair': 1045, 'desc': 'Energy to user today H (Etouser_today)'},
        1045: {'name': 'energy_to_user_today_low', 'scale': 1, 'unit': '', 'pair': 1044, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        1046: {'name': 'energy_to_user_total_high', 'scale': 1, 'unit': '', 'pair': 1047, 'desc': 'Energy to user total H'},
        1047: {'name': 'energy_to_user_total_low', 'scale': 1, 'unit': '', 'pair': 1046, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        1048: {'name': 'energy_to_grid_today_high', 'scale': 1, 'unit': '', 'pair': 1049},
        1049: {'name': 'energy_to_grid_today_low', 'scale': 1, 'unit': '', 'pair': 1048, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        1050: {'name': 'energy_to_grid_total_high', 'scale': 1, 'unit': '', 'pair': 1051},
        1051: {'name': 'energy_to_grid_total_low', 'scale': 1, 'unit': '', 'pair': 1050, 'combined_scale': 0.1, 'combined_unit': 'kWh'},

        # Grid Energy (from grid / import)
        1052: {'name': 'grid_import_energy_today_high', 'scale': 1, 'unit': '', 'pair': 1053},
        1053: {'name': 'grid_import_energy_today_low', 'scale': 1, 'unit': '', 'pair': 1052, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        1054: {'name': 'grid_import_energy_total_high', 'scale': 1, 'unit': '', 'pair': 1055},
        1055: {'name': 'grid_import_energy_total_low', 'scale': 1, 'unit': '', 'pair': 1054, 'combined_scale': 0.1, 'combined_unit': 'kWh'},

        # Load Energy
        1060: {'name': 'load_energy_today_high', 'scale': 1, 'unit': '', 'pair': 1061},
        1061: {'name': 'load_energy_today_low', 'scale': 1, 'unit': '', 'pair': 1060, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        1062: {'name': 'load_energy_total_high', 'scale': 1, 'unit': '', 'pair': 1063},
        1063: {'name': 'load_energy_total_low', 'scale': 1, 'unit': '', 'pair': 1062, 'combined_scale': 0.1, 'combined_unit': 'kWh'},

        # === MIN/MOD RANGE REGISTERS (3000-3124) ===
        # Grid Energy (to grid / export)
        3071: {'name': 'energy_to_grid_today_high_mod', 'scale': 1, 'unit': '', 'pair': 3072, 'maps_to': 'energy_to_grid_today'},
        3072: {'name': 'energy_to_grid_today_low_mod', 'scale': 1, 'unit': '', 'pair': 3071, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        3073: {'name': 'energy_to_grid_total_high_mod', 'scale': 1, 'unit': '', 'pair': 3074, 'maps_to': 'energy_to_grid_total'},
        3074: {'name': 'energy_to_grid_total_low_mod', 'scale': 1, 'unit': '', 'pair': 3073, 'combined_scale': 0.1, 'combined_unit': 'kWh'},

        # Load Energy
        3075: {'name': 'load_energy_today_high_mod', 'scale': 1, 'unit': '', 'pair': 3076, 'maps_to': 'load_energy_today'},
        3076: {'name': 'load_energy_today_low_mod', 'scale': 1, 'unit': '', 'pair': 3075, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        3077: {'name': 'load_energy_total_high_mod', 'scale': 1, 'unit': '', 'pair': 3078, 'maps_to': 'load_energy_total'},
        3078: {'name': 'load_energy_total_low_mod', 'scale': 1, 'unit': '', 'pair': 3077, 'combined_scale': 0.1, 'combined_unit': 'kWh'},

        # === V2.01 REGISTERS (31000+ range) ===
        **VPP_V201_STATUS,
        **VPP_V201_PV2_INPUT,
        **VPP_V201_PV2_TOTAL,

        # AC Output — SPH-specific (see SPH_3000_6000_V201 for rationale)
        31100: {'name': 'ac_voltage_vpp', 'scale': 0.1, 'unit': 'V', 'maps_to': 'ac_voltage'},
        31101: {'name': 'ac_current_vpp', 'scale': 0.1, 'unit': 'A', 'maps_to': 'ac_current'},
        31102: {'name': 'ac_power_high_vpp', 'scale': 1, 'unit': '', 'pair': 31103, 'maps_to': 'ac_power'},
        31103: {'name': 'ac_power_low_vpp', 'scale': 1, 'unit': '', 'pair': 31102, 'combined_scale': 0.1, 'combined_unit': 'VA'},
        31104: {'name': 'ac_reactive_power_high', 'scale': 1, 'unit': '', 'pair': 31105},
        31105: {'name': 'ac_reactive_power_low', 'scale': 1, 'unit': '', 'pair': 31104, 'combined_scale': 0.1, 'combined_unit': 'var'},
        31106: {'name': 'ac_frequency_vpp', 'scale': 0.01, 'unit': 'Hz', 'maps_to': 'ac_frequency'},

        # Grid/Meter Power — no maps_to on meter_power (SPH gets power_to_grid from 1000+ range)
        31112: {'name': 'meter_power_high', 'scale': 1, 'unit': '', 'pair': 31113},
        31113: {'name': 'meter_power_low', 'scale': 1, 'unit': '', 'pair': 31112, 'combined_scale': 0.1, 'combined_unit': 'W', 'signed': True},

        # Load Power
        31118: {'name': 'load_power_high_vpp', 'scale': 1, 'unit': '', 'pair': 31119, 'maps_to': 'load_power'},
        31119: {'name': 'load_power_low_vpp', 'scale': 1, 'unit': '', 'pair': 31118, 'combined_scale': 0.1, 'combined_unit': 'W'},

        **VPP_V201_ENERGY_1P,
        **VPP_V201_TEMPERATURE_1P,

        # Battery Cluster 1 State — SPH energy-counter layout (see SPH_3000_6000_V201)
        31200: {'name': 'battery_power_high', 'scale': 1, 'unit': '', 'pair': 31201},
        31201: {'name': 'battery_power_low', 'scale': 1, 'unit': '', 'pair': 31200, 'combined_scale': 0.1, 'combined_unit': 'W', 'signed': True},
        31202: {'name': 'battery_discharge_today_high', 'scale': 1, 'unit': '', 'pair': 31203, 'desc': 'Battery discharge energy today HIGH'},
        31203: {'name': 'battery_discharge_today_low', 'scale': 1, 'unit': '', 'pair': 31202, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        31204: {'name': 'battery_charge_total_high', 'scale': 1, 'unit': '', 'pair': 31205, 'desc': 'Battery charge energy total HIGH'},
        31205: {'name': 'battery_charge_total_low', 'scale': 1, 'unit': '', 'pair': 31204, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        31206: {'name': 'battery_charge_today_high', 'scale': 1, 'unit': '', 'pair': 31207, 'desc': 'Battery charge energy today HIGH'},
        31207: {'name': 'battery_charge_today_low', 'scale': 1, 'unit': '', 'pair': 31206, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        31208: {'name': 'battery_discharge_total_high', 'scale': 1, 'unit': '', 'pair': 31209, 'desc': 'Battery discharge energy total HIGH'},
        31209: {'name': 'battery_discharge_total_low', 'scale': 1, 'unit': '', 'pair': 31208, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        31214: {'name': 'battery_voltage_vpp', 'scale': 0.1, 'unit': 'V', 'maps_to': 'battery_voltage', 'signed': True},
        31215: {'name': 'battery_current_vpp', 'scale': 0.1, 'unit': 'A', 'maps_to': 'battery_current', 'signed': True},
        31217: {'name': 'battery_soc_vpp', 'scale': 1, 'unit': '%', 'maps_to': 'battery_soc'},
        31218: {'name': 'battery_soh', 'scale': 1, 'unit': '%', 'desc': 'Battery state of health'},
        # Note: Registers 31220-31221 appear to contain incorrect data when paired as 32-bit
        # AC charge energy total is available in register 115 (legacy range) instead
        31222: {'name': 'battery_temp_vpp', 'scale': 0.1, 'unit': '°C', 'maps_to': 'battery_temp', 'signed': True},

        # Battery AC Charge Energy (SPH 7-10kW V201 with newer firmware)
        115: {'name': 'ac_charge_energy_total', 'scale': 0.1, 'unit': 'kWh', 'desc': 'Total energy charged from AC/grid to battery'},

        # Battery Cluster 2 State
        **VPP_V201_BATTERY2,
    },
    'holding_registers': {
        # === Legacy REGISTERS ===
        **SPH_7000_10000['holding_registers'],

        # === V2.01 REGISTERS (30000+ range) ===
        30000: {'name': 'dtc_code', 'scale': 1, 'unit': '', 'access': 'RO', 'desc': 'Device Type Code: 1001 for SPH 7-10kW', 'default': 3502},
        **VPP_V201_HOLDING_1P,
    }
}

# Export all SPH profiles
SPH_REGISTER_MAPS = {
    'SPH_3000_6000': SPH_3000_6000,
    'SPH_7000_10000': SPH_7000_10000,
    'SPH_8000_10000_HU': SPH_8000_10000_HU,
    'SPH_3000_6000_V201': SPH_3000_6000_V201,
    'SPH_7000_10000_V201': SPH_7000_10000_V201,
}