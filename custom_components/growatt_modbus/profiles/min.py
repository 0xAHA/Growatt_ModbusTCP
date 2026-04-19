from .vpp_v201 import (
    VPP_V201_STATUS, VPP_V201_PV2_INPUT, VPP_V201_PV2_TOTAL,
    VPP_V201_PV3_AND_TOTAL, VPP_V201_ENERGY_1P, VPP_V201_TEMPERATURE_1P,
    VPP_V201_HOLDING_1P,
)

# MIN-3000-6000TL-X (2 PV strings, 3-6kW)
MIN_3000_6000TL_X = {
    'name': 'MIN Series 3-6kW',
    'description': '2 PV string single-phase inverter (3-6kW)',
    'notes': 'Uses 3000-3124 register range. No PV3 string.',
    'input_registers': {
        # System Status
        3000: {'name': 'inverter_status', 'scale': 1, 'unit': '', 'desc': '0=Waiting, 1=Normal, 3=Fault'},
        
        # PV Total Power (32-bit)
        3001: {'name': 'pv_total_power_high', 'scale': 1, 'unit': '', 'desc': 'Total PV power HIGH word', 'pair': 3002},
        3002: {'name': 'pv_total_power_low', 'scale': 1, 'unit': '', 'desc': 'Total PV power LOW word', 'pair': 3001, 'combined_scale': 0.1, 'combined_unit': 'W'},
        
        # PV String 1
        3003: {'name': 'pv1_voltage', 'scale': 0.1, 'unit': 'V', 'desc': 'PV1 DC voltage'},
        3004: {'name': 'pv1_current', 'scale': 0.1, 'unit': 'A', 'desc': 'PV1 DC current'},
        3005: {'name': 'pv1_power_high', 'scale': 1, 'unit': '', 'desc': 'PV1 power HIGH word', 'pair': 3006},
        3006: {'name': 'pv1_power_low', 'scale': 1, 'unit': '', 'desc': 'PV1 power LOW word', 'pair': 3005, 'combined_scale': 0.1, 'combined_unit': 'W'},
        
        # PV String 2
        3007: {'name': 'pv2_voltage', 'scale': 0.1, 'unit': 'V', 'desc': 'PV2 DC voltage'},
        3008: {'name': 'pv2_current', 'scale': 0.1, 'unit': 'A', 'desc': 'PV2 DC current'},
        3009: {'name': 'pv2_power_high', 'scale': 1, 'unit': '', 'desc': 'PV2 power HIGH word', 'pair': 3010},
        3010: {'name': 'pv2_power_low', 'scale': 1, 'unit': '', 'desc': 'PV2 power LOW word', 'pair': 3009, 'combined_scale': 0.1, 'combined_unit': 'W'},
        
        # AC Output
        3025: {'name': 'ac_frequency', 'scale': 0.01, 'unit': 'Hz', 'desc': 'AC frequency'},
        3026: {'name': 'ac_voltage', 'scale': 0.1, 'unit': 'V', 'desc': 'AC voltage'},
        3027: {'name': 'ac_current', 'scale': 0.1, 'unit': 'A', 'desc': 'AC current'},
        3028: {'name': 'ac_power_high', 'scale': 1, 'unit': '', 'desc': 'AC power HIGH', 'pair': 3029},
        3029: {'name': 'ac_power_low', 'scale': 1, 'unit': '', 'desc': 'AC power LOW', 'pair': 3028, 'combined_scale': 0.1, 'combined_unit': 'VA'},
        
        # Power Flow (signed for import/export)
        3041: {'name': 'power_to_user_high', 'scale': 1, 'unit': '', 'desc': 'Forward power HIGH', 'pair': 3042},
        3042: {'name': 'power_to_user_low', 'scale': 1, 'unit': '', 'desc': 'Forward power LOW', 'pair': 3041, 'combined_scale': 0.1, 'combined_unit': 'W'},
        3043: {'name': 'power_to_grid_high', 'scale': 1, 'unit': '', 'desc': 'Grid power HIGH (signed)', 'pair': 3044},
        3044: {'name': 'power_to_grid_low', 'scale': 1, 'unit': '', 'desc': 'Grid power LOW (signed)', 'pair': 3043, 'combined_scale': 0.1, 'combined_unit': 'W', 'signed': True},
        3045: {'name': 'power_to_load_high', 'scale': 1, 'unit': '', 'desc': 'Load power HIGH', 'pair': 3046},
        3046: {'name': 'power_to_load_low', 'scale': 1, 'unit': '', 'desc': 'Load power LOW', 'pair': 3045, 'combined_scale': 0.1, 'combined_unit': 'W'},
        
        # Energy Today (32-bit)
        3049: {'name': 'energy_today_high', 'scale': 1, 'unit': '', 'desc': 'Today energy HIGH', 'pair': 3050},
        3050: {'name': 'energy_today_low', 'scale': 1, 'unit': '', 'desc': 'Today energy LOW', 'pair': 3049, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        
        # Energy Total (32-bit)
        # 3051/3052 = Eac_total: total AC energy output from inverter (solar generation for
        # pure grid-tied MIN). Read directly — not overridden by coordinator (#255 fix).
        3051: {'name': 'energy_total_high', 'scale': 1, 'unit': '', 'desc': 'Total AC energy HIGH (Eac_total)', 'pair': 3052},
        3052: {'name': 'energy_total_low', 'scale': 1, 'unit': '', 'desc': 'Total AC energy LOW (Eac_total)', 'pair': 3051, 'combined_scale': 0.1, 'combined_unit': 'kWh'},

        # PV DC energy (Epv_total / Epv1 / Epv2 — #253)
        # 3053/3054 = Epv_total: total DC energy captured from PV panels (slightly higher than
        # Eac_total due to inverter conversion losses ~2-7%). Exposed as a SEPARATE entity
        # "PV Energy Total" — NOT used to replace energy_total (#255). Per-MPPT totals at
        # 3057/3058 (PV1) and 3061/3062 (PV2) are also exposed as separate entities.
        3053: {'name': 'pv_energy_total_high', 'scale': 1, 'unit': '', 'pair': 3054, 'desc': 'Total PV DC energy HIGH (Epv_total — solar only, unaffected by battery discharge)'},
        3054: {'name': 'pv_energy_total_low', 'scale': 1, 'unit': '', 'pair': 3053, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'Total PV DC energy LOW'},
        3055: {'name': 'pv1_energy_today_high', 'scale': 1, 'unit': '', 'pair': 3056, 'desc': 'PV1 DC energy today HIGH'},
        3056: {'name': 'pv1_energy_today_low', 'scale': 1, 'unit': '', 'pair': 3055, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        3057: {'name': 'pv1_energy_total_high', 'scale': 1, 'unit': '', 'pair': 3058, 'desc': 'PV1 DC energy total HIGH'},
        3058: {'name': 'pv1_energy_total_low', 'scale': 1, 'unit': '', 'pair': 3057, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        3059: {'name': 'pv2_energy_today_high', 'scale': 1, 'unit': '', 'pair': 3060, 'desc': 'PV2 DC energy today HIGH'},
        3060: {'name': 'pv2_energy_today_low', 'scale': 1, 'unit': '', 'pair': 3059, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        3061: {'name': 'pv2_energy_total_high', 'scale': 1, 'unit': '', 'pair': 3062, 'desc': 'PV2 DC energy total HIGH'},
        3062: {'name': 'pv2_energy_total_low', 'scale': 1, 'unit': '', 'pair': 3061, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        3063: {'name': 'pv3_energy_today_high', 'scale': 1, 'unit': '', 'pair': 3064, 'desc': 'PV3 DC energy today HIGH'},
        3064: {'name': 'pv3_energy_today_low', 'scale': 1, 'unit': '', 'pair': 3063, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        3065: {'name': 'pv3_energy_total_high', 'scale': 1, 'unit': '', 'pair': 3066, 'desc': 'PV3 DC energy total HIGH'},
        3066: {'name': 'pv3_energy_total_low', 'scale': 1, 'unit': '', 'pair': 3065, 'combined_scale': 0.1, 'combined_unit': 'kWh'},

        # Energy Breakdown
        3067: {'name': 'energy_to_user_today_high', 'scale': 1, 'unit': '', 'pair': 3068},
        3068: {'name': 'energy_to_user_today_low', 'scale': 1, 'unit': '', 'pair': 3067, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        3071: {'name': 'energy_to_grid_today_high', 'scale': 1, 'unit': '', 'pair': 3072},
        3072: {'name': 'energy_to_grid_today_low', 'scale': 1, 'unit': '', 'pair': 3071, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        3075: {'name': 'load_energy_today_high', 'scale': 1, 'unit': '', 'pair': 3076},
        3076: {'name': 'load_energy_today_low', 'scale': 1, 'unit': '', 'pair': 3075, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        
        # Diagnostics
        3086: {'name': 'derating_mode', 'scale': 1, 'unit': '', 'desc': 'Derating status'},
        3092: {'name': 'bus_voltage', 'scale': 0.1, 'unit': 'V', 'desc': 'DC bus voltage'},
        
        # Temperatures
        3093: {'name': 'inverter_temp', 'scale': 0.1, 'unit': '°C', 'desc': 'Inverter temperature', 'signed': True},
        3094: {'name': 'ipm_temp', 'scale': 0.1, 'unit': '°C', 'desc': 'IPM temperature', 'signed': True},
        3095: {'name': 'boost_temp', 'scale': 0.1, 'unit': '°C', 'desc': 'Boost temperature', 'signed': True},
        
        # Fault Codes
        3105: {'name': 'fault_code', 'scale': 1, 'unit': '', 'desc': 'Main fault code'},
        3106: {'name': 'warning_code', 'scale': 1, 'unit': '', 'desc': 'Main warning code'},
    },
    'holding_registers': {
        0: {'name': 'on_off', 'scale': 1, 'unit': '', 'access': 'RW', 'desc': '0=Off, 1=On'},
        3: {'name': 'active_power_rate', 'scale': 1, 'unit': '%', 'access': 'RW', 'desc': 'Max output power %'},
        30: {'name': 'modbus_address', 'scale': 1, 'unit': '', 'access': 'RW', 'desc': 'Modbus address 1-254'},

        # Safety/compliance diagnostic registers (read-only, Issue #282)
        235: {'name': 'ntognd_detect',     'scale': 1, 'unit': '', 'access': 'R', 'desc': '0=Disable, 1=Enable — NToGND detection'},
        236: {'name': 'nonstd_vac_enable', 'scale': 1, 'unit': '', 'access': 'R', 'desc': '0=Disable, 1=Grade1, 2=Grade2 — non-standard VAC'},
        237: {'name': 'enable_spec_set',   'scale': 1, 'unit': '', 'access': 'R', 'desc': 'Regional spec bitmask (Bit0=Hungary)'},
        238: {'name': 'fast_mppt_enable',  'scale': 1, 'unit': '', 'access': 'R', 'desc': '0-2 — fast MPPT (Reserved)'},
    }
}

# MIN-7000-10000TL-X (3 PV strings, 7-10kW)
MIN_7000_10000TL_X = {
    'name': 'MIN Series 7-10kW',
    'description': '3 PV string single-phase inverter (7-10kW)',
    'notes': 'Uses 3000-3124 register range. Includes PV3 string. Tested with real hardware.',
    'input_registers': {
        # System Status
        3000: {'name': 'inverter_status', 'scale': 1, 'unit': '', 'desc': '0=Waiting, 1=Normal, 3=Fault'},
        
        # PV Total Power (32-bit)
        3001: {'name': 'pv_total_power_high', 'scale': 1, 'unit': '', 'desc': 'Total PV power HIGH word', 'pair': 3002},
        3002: {'name': 'pv_total_power_low', 'scale': 1, 'unit': '', 'desc': 'Total PV power LOW word', 'pair': 3001, 'combined_scale': 0.1, 'combined_unit': 'W'},
        
        # PV String 1
        3003: {'name': 'pv1_voltage', 'scale': 0.1, 'unit': 'V', 'desc': 'PV1 DC voltage'},
        3004: {'name': 'pv1_current', 'scale': 0.1, 'unit': 'A', 'desc': 'PV1 DC current'},
        3005: {'name': 'pv1_power_high', 'scale': 1, 'unit': '', 'desc': 'PV1 power HIGH word', 'pair': 3006},
        3006: {'name': 'pv1_power_low', 'scale': 1, 'unit': '', 'desc': 'PV1 power LOW word', 'pair': 3005, 'combined_scale': 0.1, 'combined_unit': 'W'},
        
        # PV String 2
        3007: {'name': 'pv2_voltage', 'scale': 0.1, 'unit': 'V', 'desc': 'PV2 DC voltage'},
        3008: {'name': 'pv2_current', 'scale': 0.1, 'unit': 'A', 'desc': 'PV2 DC current'},
        3009: {'name': 'pv2_power_high', 'scale': 1, 'unit': '', 'desc': 'PV2 power HIGH word', 'pair': 3010},
        3010: {'name': 'pv2_power_low', 'scale': 1, 'unit': '', 'desc': 'PV2 power LOW word', 'pair': 3009, 'combined_scale': 0.1, 'combined_unit': 'W'},
        
        # PV String 3
        3011: {'name': 'pv3_voltage', 'scale': 0.1, 'unit': 'V', 'desc': 'PV3 DC voltage'},
        3012: {'name': 'pv3_current', 'scale': 0.1, 'unit': 'A', 'desc': 'PV3 DC current'},
        3013: {'name': 'pv3_power_high', 'scale': 1, 'unit': '', 'desc': 'PV3 power HIGH word', 'pair': 3014},
        3014: {'name': 'pv3_power_low', 'scale': 1, 'unit': '', 'desc': 'PV3 power LOW word', 'pair': 3013, 'combined_scale': 0.1, 'combined_unit': 'W'},
        
        # System Output Power (32-bit)
        3019: {'name': 'system_output_power_high', 'scale': 1, 'unit': '', 'desc': 'System output power HIGH', 'pair': 3020},
        3020: {'name': 'system_output_power_low', 'scale': 1, 'unit': '', 'desc': 'System output power LOW', 'pair': 3019, 'combined_scale': 0.1, 'combined_unit': 'W'},
        
        # Reactive Power (32-bit)
        3021: {'name': 'reactive_power_high', 'scale': 1, 'unit': '', 'desc': 'Reactive power HIGH', 'pair': 3022},
        3022: {'name': 'reactive_power_low', 'scale': 1, 'unit': '', 'desc': 'Reactive power LOW', 'pair': 3021, 'combined_scale': 0.1, 'combined_unit': 'var'},
        
        # Output Power (32-bit)
        3023: {'name': 'output_power_high', 'scale': 1, 'unit': '', 'desc': 'Output power HIGH', 'pair': 3024},
        3024: {'name': 'output_power_low', 'scale': 1, 'unit': '', 'desc': 'Output power LOW', 'pair': 3023, 'combined_scale': 0.1, 'combined_unit': 'W'},
        
        # AC Output
        3025: {'name': 'ac_frequency', 'scale': 0.01, 'unit': 'Hz', 'desc': 'Inverter AC output frequency'},
        3026: {'name': 'ac_voltage', 'scale': 0.1, 'unit': 'V', 'desc': 'Inverter AC output voltage'},
        3027: {'name': 'ac_current', 'scale': 0.1, 'unit': 'A', 'desc': 'Inverter AC output current'},
        3028: {'name': 'ac_power_high', 'scale': 1, 'unit': '', 'desc': 'AC power HIGH', 'pair': 3029},
        3029: {'name': 'ac_power_low', 'scale': 1, 'unit': '', 'desc': 'AC power LOW', 'pair': 3028, 'combined_scale': 0.1, 'combined_unit': 'VA'},
        
        # Power Flow (signed for import/export)
        3041: {'name': 'power_to_user_high', 'scale': 1, 'unit': '', 'desc': 'Forward power HIGH', 'pair': 3042},
        3042: {'name': 'power_to_user_low', 'scale': 1, 'unit': '', 'desc': 'Forward power LOW', 'pair': 3041, 'combined_scale': 0.1, 'combined_unit': 'W'},
        3043: {'name': 'power_to_grid_high', 'scale': 1, 'unit': '', 'desc': 'Grid power HIGH (signed: +export, -import)', 'pair': 3044},
        3044: {'name': 'power_to_grid_low', 'scale': 1, 'unit': '', 'desc': 'Grid power LOW (signed: +export, -import)', 'pair': 3043, 'combined_scale': 0.1, 'combined_unit': 'W', 'signed': True},
        3045: {'name': 'power_to_load_high', 'scale': 1, 'unit': '', 'desc': 'Load power HIGH', 'pair': 3046},
        3046: {'name': 'power_to_load_low', 'scale': 1, 'unit': '', 'desc': 'Load power LOW', 'pair': 3045, 'combined_scale': 0.1, 'combined_unit': 'W'},
        
        # Operating Time (32-bit)
        3047: {'name': 'time_total_high', 'scale': 1, 'unit': '', 'desc': 'Total time HIGH', 'pair': 3048},
        3048: {'name': 'time_total_low', 'scale': 1, 'unit': '', 'desc': 'Total time LOW', 'pair': 3047, 'combined_scale': 0.5, 'combined_unit': 's'},
        
        # Energy Today (32-bit)
        3049: {'name': 'energy_today_high', 'scale': 1, 'unit': '', 'desc': 'Today energy HIGH', 'pair': 3050},
        3050: {'name': 'energy_today_low', 'scale': 1, 'unit': '', 'desc': 'Today energy LOW', 'pair': 3049, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        
        # Energy Total (32-bit)
        # 3051/3052 = Eac_total: total AC energy output from inverter. Read directly.
        3051: {'name': 'energy_total_high', 'scale': 1, 'unit': '', 'desc': 'Total AC energy HIGH (Eac_total)', 'pair': 3052},
        3052: {'name': 'energy_total_low', 'scale': 1, 'unit': '', 'desc': 'Total AC energy LOW (Eac_total)', 'pair': 3051, 'combined_scale': 0.1, 'combined_unit': 'kWh'},

        # PV DC energy (Epv_total / Epv1 / Epv2 — #253)
        # 3053/3054 = Epv_total: total DC energy from panels. Exposed as separate entity
        # "PV Energy Total" — NOT used to replace energy_total.
        3053: {'name': 'pv_energy_total_high', 'scale': 1, 'unit': '', 'pair': 3054, 'desc': 'Total PV DC energy HIGH (Epv_total — solar only)'},
        3054: {'name': 'pv_energy_total_low', 'scale': 1, 'unit': '', 'pair': 3053, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'Total PV DC energy LOW'},
        3055: {'name': 'pv1_energy_today_high', 'scale': 1, 'unit': '', 'pair': 3056, 'desc': 'PV1 DC energy today HIGH'},
        3056: {'name': 'pv1_energy_today_low', 'scale': 1, 'unit': '', 'pair': 3055, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        3057: {'name': 'pv1_energy_total_high', 'scale': 1, 'unit': '', 'pair': 3058, 'desc': 'PV1 DC energy total HIGH'},
        3058: {'name': 'pv1_energy_total_low', 'scale': 1, 'unit': '', 'pair': 3057, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        3059: {'name': 'pv2_energy_today_high', 'scale': 1, 'unit': '', 'pair': 3060, 'desc': 'PV2 DC energy today HIGH'},
        3060: {'name': 'pv2_energy_today_low', 'scale': 1, 'unit': '', 'pair': 3059, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        3061: {'name': 'pv2_energy_total_high', 'scale': 1, 'unit': '', 'pair': 3062, 'desc': 'PV2 DC energy total HIGH'},
        3062: {'name': 'pv2_energy_total_low', 'scale': 1, 'unit': '', 'pair': 3061, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        3063: {'name': 'pv3_energy_today_high', 'scale': 1, 'unit': '', 'pair': 3064, 'desc': 'PV3 DC energy today HIGH'},
        3064: {'name': 'pv3_energy_today_low', 'scale': 1, 'unit': '', 'pair': 3063, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        3065: {'name': 'pv3_energy_total_high', 'scale': 1, 'unit': '', 'pair': 3066, 'desc': 'PV3 DC energy total HIGH'},
        3066: {'name': 'pv3_energy_total_low', 'scale': 1, 'unit': '', 'pair': 3065, 'combined_scale': 0.1, 'combined_unit': 'kWh'},

        # Energy Breakdown (32-bit pairs)
        3067: {'name': 'energy_to_user_today_high', 'scale': 1, 'unit': '', 'pair': 3068},
        3068: {'name': 'energy_to_user_today_low', 'scale': 1, 'unit': '', 'pair': 3067, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        3069: {'name': 'energy_to_user_total_high', 'scale': 1, 'unit': '', 'pair': 3070},
        3070: {'name': 'energy_to_user_total_low', 'scale': 1, 'unit': '', 'pair': 3069, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        3071: {'name': 'energy_to_grid_today_high', 'scale': 1, 'unit': '', 'pair': 3072},
        3072: {'name': 'energy_to_grid_today_low', 'scale': 1, 'unit': '', 'pair': 3071, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        3073: {'name': 'energy_to_grid_total_high', 'scale': 1, 'unit': '', 'pair': 3074},
        3074: {'name': 'energy_to_grid_total_low', 'scale': 1, 'unit': '', 'pair': 3073, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        3075: {'name': 'load_energy_today_high', 'scale': 1, 'unit': '', 'pair': 3076},
        3076: {'name': 'load_energy_today_low', 'scale': 1, 'unit': '', 'pair': 3075, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        3077: {'name': 'load_energy_total_high', 'scale': 1, 'unit': '', 'pair': 3078},
        3078: {'name': 'load_energy_total_low', 'scale': 1, 'unit': '', 'pair': 3077, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        
        # Diagnostics
        3086: {'name': 'derating_mode', 'scale': 1, 'unit': '', 'desc': 'Derating status'},
        3087: {'name': 'pv_iso', 'scale': 1, 'unit': 'kΩ', 'desc': 'PV isolation resistance'},
        3088: {'name': 'dci_r', 'scale': 0.1, 'unit': 'mA', 'desc': 'DC injection R phase'},
        3091: {'name': 'gfci', 'scale': 1, 'unit': 'mA', 'desc': 'Ground fault current'},
        3092: {'name': 'bus_voltage', 'scale': 0.1, 'unit': 'V', 'desc': 'DC bus voltage'},
        
        # Temperatures
        3093: {'name': 'inverter_temp', 'scale': 0.1, 'unit': '°C', 'desc': 'Inverter temperature', 'signed': True},
        3094: {'name': 'ipm_temp', 'scale': 0.1, 'unit': '°C', 'desc': 'IPM temperature', 'signed': True},
        3095: {'name': 'boost_temp', 'scale': 0.1, 'unit': '°C', 'desc': 'Boost temperature', 'signed': True},
        3097: {'name': 'comms_board_temp', 'scale': 0.1, 'unit': '°C', 'desc': 'Comms board temperature', 'signed': True},

        # Fault Codes
        3105: {'name': 'fault_code', 'scale': 1, 'unit': '', 'desc': 'Main fault code'},
        3106: {'name': 'warning_code', 'scale': 1, 'unit': '', 'desc': 'Main warning code'},
        3107: {'name': 'fault_subcode', 'scale': 1, 'unit': '', 'desc': 'Fault subcode'},
        3108: {'name': 'warning_subcode', 'scale': 1, 'unit': '', 'desc': 'Warning subcode'},
    },
    'holding_registers': {
        0: {'name': 'on_off', 'scale': 1, 'unit': '', 'access': 'RW', 'desc': '0=Off, 1=On'},
        3: {'name': 'active_power_rate', 'scale': 1, 'unit': '%', 'access': 'RW', 'desc': 'Max output power %'},
        15: {'name': 'lcd_language', 'scale': 1, 'unit': '', 'access': 'RW'},
        22: {'name': 'baud_rate', 'scale': 1, 'unit': '', 'access': 'RW', 'desc': '0=9600, 1=38400'},
        30: {'name': 'modbus_address', 'scale': 1, 'unit': '', 'access': 'RW', 'desc': 'Modbus address 1-254'},
        45: {'name': 'sys_year', 'scale': 1, 'unit': '', 'access': 'RW'},
        46: {'name': 'sys_month', 'scale': 1, 'unit': '', 'access': 'RW'},
        47: {'name': 'sys_day', 'scale': 1, 'unit': '', 'access': 'RW'},
        48: {'name': 'sys_hour', 'scale': 1, 'unit': '', 'access': 'RW'},
        49: {'name': 'sys_min', 'scale': 1, 'unit': '', 'access': 'RW'},
        50: {'name': 'sys_sec', 'scale': 1, 'unit': '', 'access': 'RW'},

        # Safety/compliance diagnostic registers (read-only, Issue #282)
        235: {'name': 'ntognd_detect',     'scale': 1, 'unit': '', 'access': 'R', 'desc': '0=Disable, 1=Enable — NToGND detection'},
        236: {'name': 'nonstd_vac_enable', 'scale': 1, 'unit': '', 'access': 'R', 'desc': '0=Disable, 1=Grade1, 2=Grade2 — non-standard VAC'},
        237: {'name': 'enable_spec_set',   'scale': 1, 'unit': '', 'access': 'R', 'desc': 'Regional spec bitmask (Bit0=Hungary)'},
        238: {'name': 'fast_mppt_enable',  'scale': 1, 'unit': '', 'access': 'R', 'desc': '0-2 — fast MPPT (Reserved)'},
    }
}

# MIN Series Base Range (0-124) - Legacy/Alternative addressing
MIN_SERIES_BASE_RANGE = {
    'name': 'MIN Series Base Range (0-124)',
    'description': 'Alternative register addressing starting at 0 instead of 3000',
    'notes': 'Contains same data as 3000 range. Use for devices that expect base 0 addressing.',
    'input_registers': {
        0: {'name': 'inverter_status', 'scale': 1, 'unit': '', 'desc': '0=Waiting, 1=Normal, 3=Fault'},
        1: {'name': 'input_power_high', 'scale': 1, 'unit': '', 'pair': 2},
        2: {'name': 'input_power_low', 'scale': 1, 'unit': '', 'pair': 1, 'combined_scale': 0.1, 'combined_unit': 'W'},
        3: {'name': 'pv1_voltage', 'scale': 0.1, 'unit': 'V'},
        4: {'name': 'pv1_current', 'scale': 0.1, 'unit': 'A'},
        5: {'name': 'pv1_power_high', 'scale': 1, 'unit': '', 'pair': 6},
        6: {'name': 'pv1_power_low', 'scale': 1, 'unit': '', 'pair': 5, 'combined_scale': 0.1, 'combined_unit': 'W'},
        7: {'name': 'pv2_voltage', 'scale': 0.1, 'unit': 'V'},
        8: {'name': 'pv2_current', 'scale': 0.1, 'unit': 'A'},
        9: {'name': 'pv2_power_high', 'scale': 1, 'unit': '', 'pair': 10},
        10: {'name': 'pv2_power_low', 'scale': 1, 'unit': '', 'pair': 9, 'combined_scale': 0.1, 'combined_unit': 'W'},
        11: {'name': 'pv3_voltage', 'scale': 0.1, 'unit': 'V'},
        12: {'name': 'pv3_current', 'scale': 0.1, 'unit': 'A'},
        13: {'name': 'pv3_power_high', 'scale': 1, 'unit': '', 'pair': 14},
        14: {'name': 'pv3_power_low', 'scale': 1, 'unit': '', 'pair': 13, 'combined_scale': 0.1, 'combined_unit': 'W'},
        35: {'name': 'output_power_high', 'scale': 1, 'unit': '', 'pair': 36},
        36: {'name': 'output_power_low', 'scale': 1, 'unit': '', 'pair': 35, 'combined_scale': 0.1, 'combined_unit': 'W'},
        37: {'name': 'grid_frequency', 'scale': 0.01, 'unit': 'Hz'},
        38: {'name': 'grid_voltage', 'scale': 0.1, 'unit': 'V'},
        39: {'name': 'grid_current', 'scale': 0.1, 'unit': 'A'},
        40: {'name': 'grid_power_high', 'scale': 1, 'unit': '', 'pair': 41},
        41: {'name': 'grid_power_low', 'scale': 1, 'unit': '', 'pair': 40, 'combined_scale': 0.1, 'combined_unit': 'VA'},
        53: {'name': 'energy_today_high', 'scale': 1, 'unit': '', 'pair': 54},
        54: {'name': 'energy_today_low', 'scale': 1, 'unit': '', 'pair': 53, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        55: {'name': 'energy_total_high', 'scale': 1, 'unit': '', 'pair': 56},
        56: {'name': 'energy_total_low', 'scale': 1, 'unit': '', 'pair': 55, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        57: {'name': 'time_total_high', 'scale': 1, 'unit': '', 'pair': 58},
        58: {'name': 'time_total_low', 'scale': 1, 'unit': '', 'pair': 57, 'combined_scale': 0.5, 'combined_unit': 's'},
        93: {'name': 'inverter_temp', 'scale': 0.1, 'unit': '°C', 'signed': True},
        94: {'name': 'ipm_temp', 'scale': 0.1, 'unit': '°C', 'signed': True},
        95: {'name': 'boost_temp', 'scale': 0.1, 'unit': '°C', 'signed': True},
        98: {'name': 'p_bus_voltage', 'scale': 0.1, 'unit': 'V'},
        99: {'name': 'n_bus_voltage', 'scale': 0.1, 'unit': 'V'},
        100: {'name': 'power_factor', 'scale': 1, 'unit': '', 'desc': '0-10000=underexcited, 10001-20000=overexcited'},
        104: {'name': 'derating_mode', 'scale': 1, 'unit': ''},
        105: {'name': 'fault_code', 'scale': 1, 'unit': ''},
        107: {'name': 'fault_subcode', 'scale': 1, 'unit': ''},
        110: {'name': 'warning_high', 'scale': 1, 'unit': ''},
        111: {'name': 'warning_subcode', 'scale': 1, 'unit': ''},
        112: {'name': 'warning_code', 'scale': 1, 'unit': ''},
    },
    'holding_registers': {
        0: {'name': 'on_off', 'scale': 1, 'unit': '', 'access': 'RW'},
        3: {'name': 'active_power_rate', 'scale': 1, 'unit': '%', 'access': 'RW'},
        15: {'name': 'lcd_language', 'scale': 1, 'unit': '', 'access': 'RW'},
        22: {'name': 'baud_rate', 'scale': 1, 'unit': '', 'access': 'RW'},
        30: {'name': 'modbus_address', 'scale': 1, 'unit': '', 'access': 'RW'},
        45: {'name': 'sys_year', 'scale': 1, 'unit': '', 'access': 'RW'},
        46: {'name': 'sys_month', 'scale': 1, 'unit': '', 'access': 'RW'},
        47: {'name': 'sys_day', 'scale': 1, 'unit': '', 'access': 'RW'},
        48: {'name': 'sys_hour', 'scale': 1, 'unit': '', 'access': 'RW'},
        49: {'name': 'sys_min', 'scale': 1, 'unit': '', 'access': 'RW'},
        50: {'name': 'sys_sec', 'scale': 1, 'unit': '', 'access': 'RW'},
    }
}

# MIN-3000-6000TL-X V2.01 Protocol (V1.39 + VPP 2.01 registers)
# V2.01 adds 30000+ range on top of V1.39 for complete functionality
MIN_3000_6000TL_X_V201 = {
    'name': 'MIN Series 3-6kW (V2.01)',
    'description': '2 PV string single-phase inverter with VPP Protocol V2.01',
    'notes': 'Combines V1.39 (3000+ range) with V2.01 (30000+ range). Overlapping values served at both addresses.',
    'input_registers': {
        # === V1.39 REGISTERS (3000+ range) ===
        **MIN_3000_6000TL_X['input_registers'],

        # === V2.01 REGISTERS (31000+ range) ===
        **VPP_V201_STATUS,
        **VPP_V201_PV2_INPUT,   # PV1/PV2 (overlaps with 3003-3010, same values served)
        **VPP_V201_PV2_TOTAL,

        # AC Output (overlaps with 3025-3029) — MIN/TL-XH: meter_power maps to power_to_grid;
        # load_power maps to power_to_load (differs from SPH naming).
        31100: {'name': 'ac_voltage_vpp',   'scale': 0.1,  'unit': 'V',  'maps_to': 'ac_voltage'},
        31101: {'name': 'ac_current_vpp',   'scale': 0.1,  'unit': 'A',  'maps_to': 'ac_current'},
        31102: {'name': 'ac_power_high_vpp','scale': 1,    'unit': '',   'pair': 31103, 'maps_to': 'ac_power'},
        31103: {'name': 'ac_power_low_vpp', 'scale': 1,    'unit': '',   'pair': 31102, 'combined_scale': 0.1, 'combined_unit': 'VA'},
        31104: {'name': 'ac_reactive_power_high', 'scale': 1, 'unit': '', 'pair': 31105},
        31105: {'name': 'ac_reactive_power_low',  'scale': 1, 'unit': '', 'pair': 31104, 'combined_scale': 0.1, 'combined_unit': 'var'},
        31106: {'name': 'ac_frequency_vpp', 'scale': 0.01, 'unit': 'Hz', 'maps_to': 'ac_frequency'},

        # Grid/Meter Power (same as PtoGrid - 3043/3044)
        31112: {'name': 'meter_power_high', 'scale': 1, 'unit': '', 'pair': 31113, 'maps_to': 'power_to_grid'},
        31113: {'name': 'meter_power_low',  'scale': 1, 'unit': '', 'pair': 31112, 'combined_scale': 0.1, 'combined_unit': 'W', 'signed': True},

        # Load Power (same as PtoLoad - 3045/3046)
        31118: {'name': 'load_power_high_vpp', 'scale': 1, 'unit': '', 'pair': 31119, 'maps_to': 'power_to_load'},
        31119: {'name': 'load_power_low_vpp',  'scale': 1, 'unit': '', 'pair': 31118, 'combined_scale': 0.1, 'combined_unit': 'W'},

        **VPP_V201_ENERGY_1P,
        **VPP_V201_TEMPERATURE_1P,
    },
    'holding_registers': {
        # === V1.39 REGISTERS ===
        **MIN_3000_6000TL_X['holding_registers'],

        # === V2.01 REGISTERS (30000+ range) ===
        30000: {'name': 'dtc_code', 'scale': 1, 'unit': '', 'access': 'RO', 'desc': 'Device Type Code: 5200 for MIN 3-6kW', 'default': 5200},
        **VPP_V201_HOLDING_1P,
        # Communication settings (MIN-specific, overlap with V1.39)
        30112: {'name': 'modbus_address_vpp', 'scale': 1, 'unit': '', 'access': 'RW', 'maps_to': 'modbus_address'},
        30113: {'name': 'baud_rate_vpp',      'scale': 1, 'unit': '', 'access': 'RW', 'maps_to': 'baud_rate'},
        # Export super-mode (MIN-specific)
        30202: {'name': 'export_limit_super_mode', 'scale': 1, 'unit': '', 'access': 'RW'},
    }
}

# MIN-7000-10000TL-X V2.01 Protocol (V1.39 + VPP 2.01 registers)
MIN_7000_10000TL_X_V201 = {
    'name': 'MIN Series 7-10kW (V2.01)',
    'description': '3 PV string single-phase inverter with VPP Protocol V2.01',
    'notes': 'Combines V1.39 (3000+ range) with V2.01 (30000+ range). Includes PV3 string.',
    'input_registers': {
        # === V1.39 REGISTERS (3000+ range) ===
        **MIN_7000_10000TL_X['input_registers'],

        # === V2.01 REGISTERS (31000+ range) ===
        **VPP_V201_STATUS,
        **VPP_V201_PV2_INPUT,
        **VPP_V201_PV3_AND_TOTAL,   # PV3 + total (31018-31023)

        # AC Output — same MIN/TL-XH layout as MIN_3000_6000TL_X_V201
        31100: {'name': 'ac_voltage_vpp',   'scale': 0.1,  'unit': 'V',  'maps_to': 'ac_voltage'},
        31101: {'name': 'ac_current_vpp',   'scale': 0.1,  'unit': 'A',  'maps_to': 'ac_current'},
        31102: {'name': 'ac_power_high_vpp','scale': 1,    'unit': '',   'pair': 31103, 'maps_to': 'ac_power'},
        31103: {'name': 'ac_power_low_vpp', 'scale': 1,    'unit': '',   'pair': 31102, 'combined_scale': 0.1, 'combined_unit': 'VA'},
        31104: {'name': 'ac_reactive_power_high', 'scale': 1, 'unit': '', 'pair': 31105},
        31105: {'name': 'ac_reactive_power_low',  'scale': 1, 'unit': '', 'pair': 31104, 'combined_scale': 0.1, 'combined_unit': 'var'},
        31106: {'name': 'ac_frequency_vpp', 'scale': 0.01, 'unit': 'Hz', 'maps_to': 'ac_frequency'},

        # Grid/Meter Power
        31112: {'name': 'meter_power_high', 'scale': 1, 'unit': '', 'pair': 31113, 'maps_to': 'power_to_grid'},
        31113: {'name': 'meter_power_low',  'scale': 1, 'unit': '', 'pair': 31112, 'combined_scale': 0.1, 'combined_unit': 'W', 'signed': True},

        # Load Power
        31118: {'name': 'load_power_high_vpp', 'scale': 1, 'unit': '', 'pair': 31119, 'maps_to': 'power_to_load'},
        31119: {'name': 'load_power_low_vpp',  'scale': 1, 'unit': '', 'pair': 31118, 'combined_scale': 0.1, 'combined_unit': 'W'},

        **VPP_V201_ENERGY_1P,
        **VPP_V201_TEMPERATURE_1P,
    },
    'holding_registers': {
        # === V1.39 REGISTERS ===
        **MIN_7000_10000TL_X['holding_registers'],

        # === V2.01 REGISTERS (30000+ range) ===
        30000: {'name': 'dtc_code', 'scale': 1, 'unit': '', 'access': 'RO', 'desc': 'Device Type Code: 5201 for MIN 7-10kW', 'default': 5201},
        **VPP_V201_HOLDING_1P,
        # Communication settings (MIN-specific, overlap with V1.39)
        30112: {'name': 'modbus_address_vpp', 'scale': 1, 'unit': '', 'access': 'RW', 'maps_to': 'modbus_address'},
        30113: {'name': 'baud_rate_vpp',      'scale': 1, 'unit': '', 'access': 'RW', 'maps_to': 'baud_rate'},
        # Export super-mode (MIN-specific)
        30202: {'name': 'export_limit_super_mode', 'scale': 1, 'unit': '', 'access': 'RW'},
    }
}

# Export all MIN profiles
MIN_REGISTER_MAPS = {
    'MIN_3000_6000TL_X': MIN_3000_6000TL_X,
    'MIN_7000_10000TL_X': MIN_7000_10000TL_X,
    'MIN_3000_6000TL_X_V201': MIN_3000_6000TL_X_V201,
    'MIN_7000_10000TL_X_V201': MIN_7000_10000TL_X_V201,
    'MIN_SERIES_BASE_RANGE': MIN_SERIES_BASE_RANGE,
}
