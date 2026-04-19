from .vpp_v201 import (
    VPP_V201_STATUS, VPP_V201_PV2_INPUT, VPP_V201_PV2_TOTAL,
    VPP_V201_TEMPERATURE_1P, VPP_V201_HOLDING_1P,
)

# MID-15000-25000TL3-X (Three-phase, 15-25kW)
MID_15000_25000TL3_X = {
    'name': 'MID-TL3-X Series',
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

        # Power flow — confirmed responding in issue #240 scan
        3041: {'name': 'power_to_user_high', 'scale': 1, 'unit': '', 'pair': 3042, 'desc': 'Grid import power (HIGH word)'},
        3042: {'name': 'power_to_user_low', 'scale': 1, 'unit': '', 'pair': 3041, 'combined_scale': 0.1, 'combined_unit': 'W', 'desc': 'Grid import power (LOW word)'},
        3043: {'name': 'power_to_grid_high', 'scale': 1, 'unit': '', 'pair': 3044, 'desc': 'Grid export power (HIGH word)'},
        3044: {'name': 'power_to_grid_low', 'scale': 1, 'unit': '', 'pair': 3043, 'combined_scale': 0.1, 'combined_unit': 'W', 'signed': True, 'desc': 'Grid export power (LOW word, signed)'},
        3045: {'name': 'power_to_load_high', 'scale': 1, 'unit': '', 'pair': 3046, 'desc': 'Load power (HIGH word)'},
        3046: {'name': 'power_to_load_low', 'scale': 1, 'unit': '', 'pair': 3045, 'combined_scale': 0.1, 'combined_unit': 'W', 'desc': 'Load power (LOW word)'},

        # Grid energy counters — confirmed responding in issue #240 scan
        3067: {'name': 'energy_to_user_today_high', 'scale': 1, 'unit': '', 'pair': 3068, 'desc': 'Grid import energy today (HIGH word)'},
        3068: {'name': 'energy_to_user_today_low', 'scale': 1, 'unit': '', 'pair': 3067, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'Grid import energy today (LOW word)'},
        3069: {'name': 'energy_to_user_total_high', 'scale': 1, 'unit': '', 'pair': 3070, 'desc': 'Grid import energy total (HIGH word)'},
        3070: {'name': 'energy_to_user_total_low', 'scale': 1, 'unit': '', 'pair': 3069, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'Grid import energy total (LOW word)'},
        3071: {'name': 'energy_to_grid_today_high', 'scale': 1, 'unit': '', 'pair': 3072, 'desc': 'Grid export energy today (HIGH word)'},
        3072: {'name': 'energy_to_grid_today_low', 'scale': 1, 'unit': '', 'pair': 3071, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'Grid export energy today (LOW word)'},
        3073: {'name': 'energy_to_grid_total_high', 'scale': 1, 'unit': '', 'pair': 3074, 'desc': 'Grid export energy total (HIGH word)'},
        3074: {'name': 'energy_to_grid_total_low', 'scale': 1, 'unit': '', 'pair': 3073, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'Grid export energy total (LOW word)'},
        3075: {'name': 'load_energy_today_high', 'scale': 1, 'unit': '', 'pair': 3076, 'desc': 'Load energy today (HIGH word)'},
        3076: {'name': 'load_energy_today_low', 'scale': 1, 'unit': '', 'pair': 3075, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'Load energy today (LOW word)'},
        3077: {'name': 'load_energy_total_high', 'scale': 1, 'unit': '', 'pair': 3078, 'desc': 'Load energy total (HIGH word)'},
        3078: {'name': 'load_energy_total_low', 'scale': 1, 'unit': '', 'pair': 3077, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'Load energy total (LOW word)'},

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
        0: {'name': 'on_off', 'scale': 1, 'unit': '', 'access': 'RW'},
        3: {'name': 'active_power_rate', 'scale': 1, 'unit': '%', 'access': 'RW'},
        30: {'name': 'modbus_address', 'scale': 1, 'unit': '', 'access': 'RW'},

        # Safety/compliance diagnostic registers (read-only, Issue #282)
        235: {'name': 'ntognd_detect',     'scale': 1, 'unit': '', 'access': 'R', 'desc': '0=Disable, 1=Enable — NToGND detection'},
        236: {'name': 'nonstd_vac_enable', 'scale': 1, 'unit': '', 'access': 'R', 'desc': '0=Disable, 1=Grade1, 2=Grade2 — non-standard VAC'},
        237: {'name': 'enable_spec_set',   'scale': 1, 'unit': '', 'access': 'R', 'desc': 'Regional spec bitmask (Bit0=Hungary)'},
        238: {'name': 'fast_mppt_enable',  'scale': 1, 'unit': '', 'access': 'R', 'desc': '0-2 — fast MPPT (Reserved)'},
    }
}

# MID-15000-25000TL3-X V2.01 Protocol (legacy + VPP 2.01 registers)
MID_15000_25000TL3_X_V201 = {
    'name': 'MID-TL3-X Series (V2.01)',
    'description': 'Three-phase commercial inverter (15-25kW) with VPP Protocol V2.01',
    'notes': 'Combines legacy (0-124 range) with V2.01 (30000+ range). Overlapping values served at both addresses.',
    'input_registers': {
        # === Legacy REGISTERS (0-124 range) ===
        **MID_15000_25000TL3_X['input_registers'],

        # === V2.01 REGISTERS (31000+ range) ===

        # Status — VPP_V201_STATUS (31000–31004)
        **VPP_V201_STATUS,

        # PV strings 1 and 2 — VPP_V201_PV2_INPUT (31010–31017)
        **VPP_V201_PV2_INPUT,

        # Total PV power — VPP_V201_PV2_TOTAL (31018–31019)
        # MID is a 2-string profile at VPP level.
        **VPP_V201_PV2_TOTAL,

        # === VPP 2.01 GRID POWER REGISTERS (31100-31113) ===
        # Per VPP 2.01 protocol spec (confirmed against issue #245 scan data):

        # Active power (INT32 signed, 0.1W) — spec item 45
        # Positive = export to grid, Negative = import from grid
        # maps_to power_to_grid_low so coordinator uses this for grid export fallback.
        # Confirmed: -32876 raw = -3287.6W → 328.9W import during #245 battery-charging scan.
        31100: {'name': 'ac_active_power_high', 'scale': 1, 'unit': '', 'pair': 31101,
                'desc': 'Active power HIGH (INT32 signed, positive=export)'},
        31101: {'name': 'ac_active_power_low', 'scale': 1, 'unit': '', 'pair': 31100,
                'combined_scale': 0.1, 'combined_unit': 'W', 'signed': True,
                'maps_to': 'power_to_grid_low',
                'desc': 'Active power LOW — maps_to power_to_grid (positive=export per VPP 2.01 item 45)'},

        # Reactive power (INT32 signed, 0.1VA) — spec item 46
        31102: {'name': 'ac_reactive_power_high', 'scale': 1, 'unit': '', 'pair': 31103,
                'desc': 'Reactive power HIGH (INT32)'},
        31103: {'name': 'ac_reactive_power_low', 'scale': 1, 'unit': '', 'pair': 31102,
                'combined_scale': 0.1, 'combined_unit': 'VA', 'signed': True,
                'desc': 'Reactive power LOW (VPP 2.01 item 46)'},

        # Register 31104 = Reserve (1 reg, skip) — spec item 47

        # Grid frequency (UINT16, 0.01 Hz) — spec item 48
        31105: {'name': 'ac_frequency_vpp', 'scale': 0.01, 'unit': 'Hz', 'maps_to': 'grid_frequency',
                'desc': 'Grid frequency (VPP 2.01 item 48, 0.01Hz)'},

        # Line voltages (UINT16, 0.1V) — spec items 49-51
        # Coordinator looks for register names 'line_voltage_rs/st/tr' to populate ac_voltage_rs/st/tr.
        31106: {'name': 'line_voltage_rs', 'scale': 0.1, 'unit': 'V',
                'desc': 'AB line voltage (VPP 2.01 item 49)'},
        31107: {'name': 'line_voltage_st', 'scale': 0.1, 'unit': 'V',
                'desc': 'BC line voltage (VPP 2.01 item 50)'},
        31108: {'name': 'line_voltage_tr', 'scale': 0.1, 'unit': 'V',
                'desc': 'CA line voltage (VPP 2.01 item 51)'},

        # Grid phase currents (INT16 signed, 0.1A) — spec items 52-54
        # Coordinator looks for register names 'ac_current_r/s/t' to populate those sensors.
        31109: {'name': 'ac_current_r', 'scale': 0.1, 'unit': 'A', 'signed': True,
                'desc': 'Phase A current (VPP 2.01 item 52)'},
        31110: {'name': 'ac_current_s', 'scale': 0.1, 'unit': 'A', 'signed': True,
                'desc': 'Phase B current (VPP 2.01 item 53)'},
        31111: {'name': 'ac_current_t', 'scale': 0.1, 'unit': 'A', 'signed': True,
                'desc': 'Phase C current (VPP 2.01 item 54)'},

        # Meter power (INT32 signed, 0.1W) — spec item 55
        # NOTE: sign convention is OPPOSITE to active power — positive = IMPORT from grid.
        # maps_to power_to_user_low so coordinator uses this for grid import.
        31112: {'name': 'meter_power_high', 'scale': 1, 'unit': '', 'pair': 31113,
                'desc': 'Meter power HIGH (INT32, positive=import)'},
        31113: {'name': 'meter_power_low', 'scale': 1, 'unit': '', 'pair': 31112,
                'combined_scale': 0.1, 'combined_unit': 'W', 'signed': True,
                'maps_to': 'power_to_user_low',
                'desc': 'Meter power LOW — maps_to power_to_user (positive=import per VPP 2.01 item 55)'},

        # === VPP 2.01 GRID ENERGY COUNTERS (31118-31125) — spec items 60-63 ===
        # NOTE: registers 31114-31117 (spec items 56-59) are unknown/not mapped.
        # NOTE: 31119=94 in #240 scan = 9.4 kWh energy_to_user_today (was mis-labelled as 9.4W load power).
        # These are VPP fallbacks — 3000-range (3067-3074) takes priority per coordinator ordering.

        # Item 60: Power to user daily (UINT32, 0.1kWh) — grid import energy today
        31118: {'name': 'energy_to_user_today_vpp_high', 'scale': 1, 'unit': '', 'pair': 31119,
                'desc': 'Grid import energy today HIGH (VPP 2.01 item 60)'},
        31119: {'name': 'energy_to_user_today_vpp_low', 'scale': 1, 'unit': '', 'pair': 31118,
                'combined_scale': 0.1, 'combined_unit': 'kWh',
                'maps_to': 'energy_to_user_today_low',
                'desc': 'Grid import energy today LOW (VPP 2.01 item 60)'},

        # Item 61: Total power to user (UINT32, 0.1kWh) — grid import energy total
        31120: {'name': 'energy_to_user_total_vpp_high', 'scale': 1, 'unit': '', 'pair': 31121,
                'desc': 'Grid import energy total HIGH (VPP 2.01 item 61)'},
        31121: {'name': 'energy_to_user_total_vpp_low', 'scale': 1, 'unit': '', 'pair': 31120,
                'combined_scale': 0.1, 'combined_unit': 'kWh',
                'maps_to': 'energy_to_user_total_low',
                'desc': 'Grid import energy total LOW (VPP 2.01 item 61)'},

        # Item 62: Power to grid daily (UINT32, 0.1kWh) — grid export energy today
        31122: {'name': 'energy_to_grid_today_vpp_high', 'scale': 1, 'unit': '', 'pair': 31123,
                'desc': 'Grid export energy today HIGH (VPP 2.01 item 62)'},
        31123: {'name': 'energy_to_grid_today_vpp_low', 'scale': 1, 'unit': '', 'pair': 31122,
                'combined_scale': 0.1, 'combined_unit': 'kWh',
                'maps_to': 'energy_to_grid_today_low',
                'desc': 'Grid export energy today LOW (VPP 2.01 item 62)'},

        # Item 63: Total power to grid (UINT32, 0.1kWh) — grid export energy total
        31124: {'name': 'energy_to_grid_total_vpp_high', 'scale': 1, 'unit': '', 'pair': 31125,
                'desc': 'Grid export energy total HIGH (VPP 2.01 item 63)'},
        31125: {'name': 'energy_to_grid_total_vpp_low', 'scale': 1, 'unit': '', 'pair': 31124,
                'combined_scale': 0.1, 'combined_unit': 'kWh',
                'maps_to': 'energy_to_grid_total_low',
                'desc': 'Grid export energy total LOW (VPP 2.01 item 63)'},

        # Temperatures — VPP_V201_TEMPERATURE_1P (31130–31132)
        **VPP_V201_TEMPERATURE_1P,

        # === BATTERY (VPP 31200+ range) — confirmed responding in issue #240 scan ===
        # Named without _vpp suffix so coordinator's fallback lookup finds them directly
        # (no competing 3000-range battery registers on MID)
        31200: {'name': 'battery_power_high', 'scale': 1, 'unit': '', 'pair': 31201, 'desc': 'Battery power HIGH'},
        31201: {'name': 'battery_power_low', 'scale': 1, 'unit': '', 'pair': 31200, 'combined_scale': 0.1, 'combined_unit': 'W', 'signed': True, 'desc': 'Battery power (signed, positive=charging)'},

        # Battery charge/discharge energy (VPP)
        31202: {'name': 'charge_energy_today_vpp_high', 'scale': 1, 'unit': '', 'pair': 31203},
        31203: {'name': 'charge_energy_today_vpp_low', 'scale': 1, 'unit': '', 'pair': 31202, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        31204: {'name': 'charge_energy_total_vpp_high', 'scale': 1, 'unit': '', 'pair': 31205},
        31205: {'name': 'charge_energy_total_vpp_low', 'scale': 1, 'unit': '', 'pair': 31204, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        31206: {'name': 'discharge_energy_today_vpp_high', 'scale': 1, 'unit': '', 'pair': 31207},
        31207: {'name': 'discharge_energy_today_vpp_low', 'scale': 1, 'unit': '', 'pair': 31206, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        31208: {'name': 'discharge_energy_total_vpp_high', 'scale': 1, 'unit': '', 'pair': 31209},
        31209: {'name': 'discharge_energy_total_vpp_low', 'scale': 1, 'unit': '', 'pair': 31208, 'combined_scale': 0.1, 'combined_unit': 'kWh'},

        # Battery state — confirmed responding in issue #240 scan
        # 31214=4048 → 404.8V, 31215/31216=0/148 → 14.8A, 31217=33 → 33% SOC
        31214: {'name': 'battery_voltage', 'scale': 0.1, 'unit': 'V', 'desc': 'Battery voltage (VPP)'},
        31215: {'name': 'battery_current_vpp_high', 'scale': 1, 'unit': '', 'pair': 31216},
        31216: {'name': 'battery_current_vpp_low', 'scale': 1, 'unit': '', 'pair': 31215, 'combined_scale': 0.1, 'combined_unit': 'A', 'signed': True, 'maps_to': 'battery_current'},
        31217: {'name': 'battery_soc', 'scale': 1, 'unit': '%', 'desc': 'Battery SOC (VPP)'},
        31218: {'name': 'battery_soh', 'scale': 1, 'unit': '%', 'desc': 'Battery state of health'},
        # 31222/31223=0/415 → 41.5°C battery temp
        31222: {'name': 'battery_temp_vpp_high', 'scale': 1, 'unit': '', 'pair': 31223},
        31223: {'name': 'battery_temp', 'scale': 0.1, 'unit': '°C', 'signed': True, 'desc': 'Battery temperature (VPP)'},
    },
    'holding_registers': {
        # === Legacy REGISTERS ===
        **MID_15000_25000TL3_X['holding_registers'],

        # === V2.01 REGISTERS (30000+ range) ===
        30000: {'name': 'dtc_code', 'scale': 1, 'unit': '', 'access': 'RO',
                'desc': 'Device Type Code: 3000 for MID', 'default': 5400},

        # Shared holding block — VPP_V201_HOLDING_1P (30099–30109, 30114, 30200–30201)
        **VPP_V201_HOLDING_1P,

        # MID-specific: Modbus address via VPP (between 30109 and 30114 in address space)
        30112: {'name': 'modbus_address_vpp', 'scale': 1, 'unit': '', 'access': 'RW',
                'maps_to': 'modbus_address'},
    }
}

# Export all MID profiles
MID_REGISTER_MAPS = {
    'MID_15000_25000TL3_X': MID_15000_25000TL3_X,
    'MID_15000_25000TL3_X_V201': MID_15000_25000TL3_X_V201,
}
