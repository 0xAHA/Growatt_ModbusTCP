# TL-XH Series - Single-Phase Hybrid Inverters with Battery Storage
# Uses similar register layout to SPH series

from .vpp_v201 import (
    VPP_V201_STATUS, VPP_V201_PV2_INPUT, VPP_V201_PV3_AND_TOTAL,
    VPP_V201_ENERGY_1P, VPP_V201_TEMPERATURE_1P,
    VPP_V201_BATTERY2, VPP_V201_HOLDING_1P,
)

# TL-XH 3000-10000 (Single-phase hybrid with battery, 3-10kW)
TL_XH_3000_10000 = {
    'name': 'TL-XH 3000-10000',
    'description': 'Single-phase hybrid inverter with battery (3-10kW)',
    'notes': 'Uses 0-124 register range. 3 PV strings, battery management, backup output.',
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

        # PV String 3
        11: {'name': 'pv3_voltage', 'scale': 0.1, 'unit': 'V'},
        12: {'name': 'pv3_current', 'scale': 0.1, 'unit': 'A'},
        13: {'name': 'pv3_power_high', 'scale': 1, 'unit': '', 'pair': 14},
        14: {'name': 'pv3_power_low', 'scale': 1, 'unit': '', 'pair': 13, 'combined_scale': 0.1, 'combined_unit': 'W'},

        # Battery
        17: {'name': 'battery_voltage', 'scale': 0.1, 'unit': 'V'},
        18: {'name': 'battery_current', 'scale': 0.1, 'unit': 'A', 'signed': True},
        19: {'name': 'battery_power', 'scale': 1, 'unit': 'W', 'signed': True},
        21: {'name': 'battery_soc', 'scale': 1, 'unit': '%'},
        22: {'name': 'battery_temp', 'scale': 0.1, 'unit': '°C', 'signed': True},

        # AC Output
        37: {'name': 'ac_frequency', 'scale': 0.01, 'unit': 'Hz'},
        38: {'name': 'ac_voltage', 'scale': 0.1, 'unit': 'V'},
        39: {'name': 'ac_current', 'scale': 0.1, 'unit': 'A'},
        40: {'name': 'ac_power_high', 'scale': 1, 'unit': '', 'pair': 41},
        41: {'name': 'ac_power_low', 'scale': 1, 'unit': '', 'pair': 40, 'combined_scale': 0.1, 'combined_unit': 'W'},

        # Power Flow
        45: {'name': 'power_to_grid_high', 'scale': 1, 'unit': '', 'pair': 46},
        46: {'name': 'power_to_grid_low', 'scale': 1, 'unit': '', 'pair': 45, 'combined_scale': 0.1, 'combined_unit': 'W', 'signed': True},
        47: {'name': 'power_to_load_high', 'scale': 1, 'unit': '', 'pair': 48},
        48: {'name': 'power_to_load_low', 'scale': 1, 'unit': '', 'pair': 47, 'combined_scale': 0.1, 'combined_unit': 'W'},

        # Energy
        53: {'name': 'energy_today_high', 'scale': 1, 'unit': '', 'pair': 54},
        54: {'name': 'energy_today_low', 'scale': 1, 'unit': '', 'pair': 53, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        55: {'name': 'energy_total_high', 'scale': 1, 'unit': '', 'pair': 56},
        56: {'name': 'energy_total_low', 'scale': 1, 'unit': '', 'pair': 55, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        57: {'name': 'time_total_high', 'scale': 1, 'unit': '', 'pair': 58},

        # PV energy total — raw DC-side generation, unaffected by battery cycling (#243)
        # Protocol V1.39 regs 91-92: Epv_total H/L (0.1 kWh)
        # Use this for HA energy dashboard; energy_total (reg 55/56) is a net calculated value
        91: {'name': 'pv_energy_total_high', 'scale': 1, 'unit': '', 'pair': 92, 'desc': 'PV energy total lifetime HIGH'},
        92: {'name': 'pv_energy_total_low', 'scale': 1, 'unit': '', 'pair': 91, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'PV energy total lifetime LOW'},
        58: {'name': 'time_total_low', 'scale': 1, 'unit': '', 'pair': 57, 'combined_scale': 0.5, 'combined_unit': 'h'},

        # Per-string DC energy (today and lifetime totals) — confirmed via scan #224
        59: {'name': 'pv1_energy_today_high', 'scale': 1, 'unit': '', 'pair': 60, 'desc': 'PV1 DC energy today HIGH'},
        60: {'name': 'pv1_energy_today_low', 'scale': 1, 'unit': '', 'pair': 59, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'PV1 DC energy today LOW'},
        61: {'name': 'pv1_energy_total_high', 'scale': 1, 'unit': '', 'pair': 62, 'desc': 'PV1 DC energy total HIGH'},
        62: {'name': 'pv1_energy_total_low', 'scale': 1, 'unit': '', 'pair': 61, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'PV1 DC energy total LOW'},
        63: {'name': 'pv2_energy_today_high', 'scale': 1, 'unit': '', 'pair': 64, 'desc': 'PV2 DC energy today HIGH'},
        64: {'name': 'pv2_energy_today_low', 'scale': 1, 'unit': '', 'pair': 63, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'PV2 DC energy today LOW'},
        65: {'name': 'pv2_energy_total_high', 'scale': 1, 'unit': '', 'pair': 66, 'desc': 'PV2 DC energy total HIGH'},
        66: {'name': 'pv2_energy_total_low', 'scale': 1, 'unit': '', 'pair': 65, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'PV2 DC energy total LOW'},

        # Energy Breakdown
        69: {'name': 'energy_to_grid_today_high', 'scale': 1, 'unit': '', 'pair': 70},
        70: {'name': 'energy_to_grid_today_low', 'scale': 1, 'unit': '', 'pair': 69, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        71: {'name': 'energy_to_grid_total_high', 'scale': 1, 'unit': '', 'pair': 72},
        72: {'name': 'energy_to_grid_total_low', 'scale': 1, 'unit': '', 'pair': 71, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        77: {'name': 'load_energy_today_high', 'scale': 1, 'unit': '', 'pair': 78},
        78: {'name': 'load_energy_today_low', 'scale': 1, 'unit': '', 'pair': 77, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        79: {'name': 'load_energy_total_high', 'scale': 1, 'unit': '', 'pair': 80},
        80: {'name': 'load_energy_total_low', 'scale': 1, 'unit': '', 'pair': 79, 'combined_scale': 0.1, 'combined_unit': 'kWh'},

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
        0: {'name': 'on_off', 'scale': 1, 'unit': '', 'access': 'RW', 'desc': '0=Off, 1=On'},
        3: {'name': 'active_power_rate', 'scale': 1, 'unit': '%', 'access': 'RW'},

        # Safety/compliance diagnostic registers (read-only, Issue #282)
        235: {'name': 'ntognd_detect',     'scale': 1, 'unit': '', 'access': 'R', 'desc': '0=Disable, 1=Enable — NToGND detection'},
        236: {'name': 'nonstd_vac_enable', 'scale': 1, 'unit': '', 'access': 'R', 'desc': '0=Disable, 1=Grade1, 2=Grade2 — non-standard VAC'},
        237: {'name': 'enable_spec_set',   'scale': 1, 'unit': '', 'access': 'R', 'desc': 'Regional spec bitmask (Bit0=Hungary)'},
        238: {'name': 'fast_mppt_enable',  'scale': 1, 'unit': '', 'access': 'R', 'desc': '0-2 — fast MPPT (Reserved)'},

        3000: {'name': 'export_limit_failed_power_rate', 'scale': 0.1, 'unit': '%', 'access': 'RW',
               'desc': 'Fallback output power rate applied when export limitation control fails'},
    }
}

# TL-XH US 3000-10000 (US version, same registers)
TL_XH_US_3000_10000 = {
    'name': 'TL-XH US 3000-10000',
    'description': 'US single-phase hybrid inverter with battery (3-10kW)',
    'notes': 'Uses 0-124 register range. Same as TL-XH but for US market.',
    'input_registers': TL_XH_3000_10000['input_registers'].copy(),
    'holding_registers': TL_XH_3000_10000['holding_registers'].copy(),
}

# TL-XH V2.01 Protocol (legacy + VPP 2.01 registers)
TL_XH_3000_10000_V201 = {
    'name': 'TL-XH 3000-10000 (V2.01)',
    'description': 'Single-phase hybrid inverter with battery (3-10kW) and VPP Protocol V2.01',
    'notes': 'Combines legacy (0-124 range) with V2.01 (30000+ range). Overlapping values served at both addresses.',
    'input_registers': {
        # === Legacy REGISTERS (0-124 range) ===
        **TL_XH_3000_10000['input_registers'],

        # === V2.01 REGISTERS (31000+ range) ===

        # Status — VPP_V201_STATUS (31000–31004)
        **VPP_V201_STATUS,

        # PV strings 1 and 2 — VPP_V201_PV2_INPUT (31010–31017)
        **VPP_V201_PV2_INPUT,

        # PV string 3 + total PV power — VPP_V201_PV3_AND_TOTAL (31018–31023)
        # TL-XH is a 3-string profile at VPP level.
        **VPP_V201_PV3_AND_TOTAL,

        # AC Output (31100–31119) — TL-XH specific: no reactive power (31104–31105);
        # meter_power maps to power_to_grid; load_power maps to power_to_load.
        # SPH omits maps_to on meter_power; MIN/TL-XH both map to power_to_grid.
        31100: {'name': 'ac_voltage_vpp',      'scale': 0.1,  'unit': 'V',  'maps_to': 'ac_voltage'},
        31101: {'name': 'ac_current_vpp',      'scale': 0.1,  'unit': 'A',  'maps_to': 'ac_current'},
        31102: {'name': 'ac_power_high_vpp',   'scale': 1,    'unit': '',   'pair': 31103, 'maps_to': 'ac_power'},
        31103: {'name': 'ac_power_low_vpp',    'scale': 1,    'unit': '',   'pair': 31102,
                'combined_scale': 0.1, 'combined_unit': 'VA'},
        31106: {'name': 'ac_frequency_vpp',    'scale': 0.01, 'unit': 'Hz', 'maps_to': 'ac_frequency'},
        31112: {'name': 'meter_power_high',    'scale': 1,    'unit': '',   'pair': 31113,
                'maps_to': 'power_to_grid'},
        31113: {'name': 'meter_power_low',     'scale': 1,    'unit': '',   'pair': 31112,
                'combined_scale': 0.1, 'combined_unit': 'W', 'signed': True},
        31118: {'name': 'load_power_high_vpp', 'scale': 1,    'unit': '',   'pair': 31119,
                'maps_to': 'power_to_load'},
        31119: {'name': 'load_power_low_vpp',  'scale': 1,    'unit': '',   'pair': 31118,
                'combined_scale': 0.1, 'combined_unit': 'W'},

        # Energy today / total — VPP_V201_ENERGY_1P (31120–31123)
        **VPP_V201_ENERGY_1P,

        # Temperatures — VPP_V201_TEMPERATURE_1P (31130–31132)
        **VPP_V201_TEMPERATURE_1P,

        # Battery Cluster 1 (31200–31222) — TL-XH specific power layout.
        # Unlike SPH (energy counters at 31202–31209), TL-XH uses charge/discharge power here.
        # Left inline to make the family difference explicit.
        31200: {'name': 'battery_power_high', 'scale': 1, 'unit': '', 'pair': 31201},
        31201: {'name': 'battery_power_low',  'scale': 1, 'unit': '', 'pair': 31200,
                'combined_scale': 0.1, 'combined_unit': 'W', 'signed': True},
        31202: {'name': 'charge_energy_today_high', 'scale': 1, 'unit': '', 'pair': 31203,
                'desc': 'Battery charge energy today HIGH'},
        31203: {'name': 'charge_energy_today_low',  'scale': 1, 'unit': '', 'pair': 31202,
                'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'Battery charge energy today'},
        31204: {'name': 'charge_power_high', 'scale': 1, 'unit': '', 'pair': 31205,
                'desc': 'Battery charge power HIGH'},
        31205: {'name': 'charge_power_low',  'scale': 1, 'unit': '', 'pair': 31204,
                'combined_scale': 0.1, 'combined_unit': 'W', 'signed': True,
                'desc': 'Battery charge power (signed: positive=charging, negative=discharging)'},
        31206: {'name': 'discharge_energy_today_high', 'scale': 1, 'unit': '', 'pair': 31207,
                'desc': 'Battery discharge energy today HIGH'},
        31207: {'name': 'discharge_energy_today_low',  'scale': 1, 'unit': '', 'pair': 31206,
                'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'Battery discharge energy today'},
        31208: {'name': 'discharge_power_high', 'scale': 1, 'unit': '', 'pair': 31209,
                'desc': 'Battery discharge power HIGH'},
        31209: {'name': 'discharge_power_low',  'scale': 1, 'unit': '', 'pair': 31208,
                'combined_scale': 0.1, 'combined_unit': 'W', 'signed': True,
                'desc': 'Battery discharge power (signed: positive=discharging, negative=charging)'},
        31214: {'name': 'battery_voltage_vpp', 'scale': 0.1, 'unit': 'V',  'maps_to': 'battery_voltage', 'signed': True},
        31215: {'name': 'battery_current_vpp', 'scale': 0.1, 'unit': 'A',  'maps_to': 'battery_current', 'signed': True},
        31217: {'name': 'battery_soc_vpp',     'scale': 1,   'unit': '%',  'maps_to': 'battery_soc'},
        31222: {'name': 'battery_temp_vpp',    'scale': 0.1, 'unit': '°C', 'maps_to': 'battery_temp', 'signed': True},

        # Battery Cluster 2 — VPP_V201_BATTERY2 (31300–31303, 31314–31322)
        **VPP_V201_BATTERY2,
    },
    'holding_registers': {
        # === Legacy REGISTERS ===
        **TL_XH_3000_10000['holding_registers'],

        # === V2.01 REGISTERS (30000+ range) ===
        30000: {'name': 'dtc_code', 'scale': 1, 'unit': '', 'access': 'RO',
                'desc': 'Device Type Code: 4000 for TL-XH', 'default': 5100},

        # Shared holding block — VPP_V201_HOLDING_1P (30099–30109, 30114, 30200–30201)
        **VPP_V201_HOLDING_1P,
    }
}

# TL-XH US V2.01 Protocol
TL_XH_US_3000_10000_V201 = {
    'name': 'TL-XH US 3000-10000 (V2.01)',
    'description': 'US single-phase hybrid inverter with battery (3-10kW) and VPP Protocol V2.01',
    'notes': 'Combines legacy (0-124 range) with V2.01 (30000+ range). US market version.',
    'input_registers': TL_XH_3000_10000_V201['input_registers'].copy(),
    'holding_registers': TL_XH_3000_10000_V201['holding_registers'].copy(),
}
# Update DTC code for US version
TL_XH_US_3000_10000_V201['holding_registers'][30000] = {
    'name': 'dtc_code', 'scale': 1, 'unit': '', 'access': 'RO',
    'desc': 'Device Type Code: 4001 for TL-XH US', 'default': 5100
}

# MIN TL-XH Hybrid - Uses MIN 3000+ range + VPP 31200+ battery range
# This is for MIN 6000 TL-XH models that use MIN series register layout with battery support
MIN_TL_XH_3000_10000_V201 = {
    'name': 'MIN TL-XH 3000-10000 (V2.01)',
    'description': 'MIN series TL-XH hybrid with battery (3-10kW) using 3000+ and 31000+ ranges',
    'notes': 'Uses MIN 3000+ range for base sensors and VPP 31200+ range for battery. 3-6kW models have 2 PV strings, 7-10kW models have 3 PV strings. Found in MIN 6000/10000 TL-XH models with DTC 5100.',
    'input_registers': {
        # === MIN SERIES BASE RANGE (3000+) ===
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

        # PV String 3 (7-10kW models only)
        3011: {'name': 'pv3_voltage', 'scale': 0.1, 'unit': 'V', 'desc': 'PV3 DC voltage'},
        3012: {'name': 'pv3_current', 'scale': 0.1, 'unit': 'A', 'desc': 'PV3 DC current'},
        3013: {'name': 'pv3_power_high', 'scale': 1, 'unit': '', 'desc': 'PV3 power HIGH word', 'pair': 3014},
        3014: {'name': 'pv3_power_low', 'scale': 1, 'unit': '', 'desc': 'PV3 power LOW word', 'pair': 3013, 'combined_scale': 0.1, 'combined_unit': 'W'},

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

        # Energy Total (32-bit) — Eac: total AC output energy (includes battery discharge on hybrids)
        3051: {'name': 'energy_total_high', 'scale': 1, 'unit': '', 'desc': 'Total energy HIGH', 'pair': 3052},
        3052: {'name': 'energy_total_low', 'scale': 1, 'unit': '', 'desc': 'Total energy LOW', 'pair': 3051, 'combined_scale': 0.1, 'combined_unit': 'kWh'},

        # PV Energy Total (32-bit) — Epv: pure DC solar input energy (unaffected by battery discharge)
        # Primary source: 3053/3054 (matches MIN grid-tied 3000-range layout).
        # Some hardware variants return 0 here and report valid data at legacy regs 91/92 instead.
        # growatt_modbus.py falls back to pv_energy_total_legacy_low (reg 92) when this reads 0.
        3053: {'name': 'pv_energy_total_high', 'scale': 1, 'unit': '', 'pair': 3054, 'desc': 'Total PV DC energy HIGH (Epv_total — solar only, unaffected by battery discharge)'},
        3054: {'name': 'pv_energy_total_low', 'scale': 1, 'unit': '', 'pair': 3053, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'Total PV DC energy LOW'},

        # PV Energy Total legacy fallback (32-bit) — reg 91/92 (same layout as TL-XH 0-124 range)
        # Used by growatt_modbus.py when 3053/3054 returns 0 (firmware variant difference).
        91: {'name': 'pv_energy_total_legacy_high', 'scale': 1, 'unit': '', 'pair': 92, 'desc': 'PV energy total legacy HIGH (fallback when 3053/3054 = 0)'},
        92: {'name': 'pv_energy_total_legacy_low', 'scale': 1, 'unit': '', 'pair': 91, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'PV energy total legacy LOW (fallback when 3053/3054 = 0)'},

        # Energy Breakdown
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
        3092: {'name': 'bus_voltage', 'scale': 0.1, 'unit': 'V', 'desc': 'DC bus voltage'},

        # Temperatures
        3093: {'name': 'inverter_temp', 'scale': 0.1, 'unit': '°C', 'desc': 'Inverter temperature', 'signed': True},
        3094: {'name': 'ipm_temp', 'scale': 0.1, 'unit': '°C', 'desc': 'IPM temperature', 'signed': True},
        97: {'name': 'boost_temp', 'scale': 0.1, 'unit': '°C', 'desc': 'Boost temperature (at register 97, not 3095)', 'signed': True},

        # Fault Codes
        3105: {'name': 'fault_code', 'scale': 1, 'unit': '', 'desc': 'Main fault code'},
        3106: {'name': 'warning_code', 'scale': 1, 'unit': '', 'desc': 'Main warning code'},

        # Battery Extended Diagnostics
        3136: {'name': 'battery_bms_temp', 'scale': 0.1, 'unit': '°C', 'signed': True, 'desc': 'Battery BMS/module temperature'},

        # === BATTERY STATE REGISTERS (3169-3176) - PRIMARY for MIN TL-XH ===
        # MIN TL-XH uses 3000+ range for battery state (not VPP 31200+ range)
        # Similar to MOD series layout
        3169: {'name': 'battery_voltage', 'scale': 0.01, 'unit': 'V', 'desc': 'Battery voltage (primary source for MIN TL-XH)'},
        3170: {'name': 'battery_current', 'scale': 0.1, 'unit': 'A', 'signed': True, 'desc': 'Battery current (primary source for MIN TL-XH)'},
        3171: {'name': 'battery_soc', 'scale': 1, 'unit': '%', 'desc': 'Battery SOC (primary source for MIN TL-XH)'},
        3176: {'name': 'battery_temp', 'scale': 0.1, 'unit': '°C', 'signed': True, 'desc': 'Battery temperature (primary source for MIN TL-XH)'},

        # === BATTERY ENERGY REGISTERS (3125-3136) ===
        # Battery energy today/total in fallback 3000 range (same layout as MOD series)
        # These are fallback registers when VPP 31200+ is not available
        3125: {'name': 'discharge_energy_today_high', 'scale': 1, 'unit': '', 'pair': 3126, 'desc': 'Battery discharge energy today HIGH (fallback range)'},
        3126: {'name': 'discharge_energy_today_low', 'scale': 1, 'unit': '', 'pair': 3125, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'Battery discharge energy today (fallback range)'},
        3127: {'name': 'discharge_energy_total_high', 'scale': 1, 'unit': '', 'pair': 3128, 'desc': 'Battery discharge energy total HIGH (confirmed: 481.5 kWh)'},
        3128: {'name': 'discharge_energy_total_low', 'scale': 1, 'unit': '', 'pair': 3127, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'Battery discharge energy total'},
        3129: {'name': 'charge_energy_today_high', 'scale': 1, 'unit': '', 'pair': 3130, 'desc': 'Battery charge energy today HIGH (fallback range)'},
        3130: {'name': 'charge_energy_today_low', 'scale': 1, 'unit': '', 'pair': 3129, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'Battery charge energy today (fallback range)'},
        3131: {'name': 'charge_energy_total_high', 'scale': 1, 'unit': '', 'pair': 3132, 'desc': 'Battery charge energy total HIGH (confirmed: 528.9 kWh)'},
        3132: {'name': 'charge_energy_total_low', 'scale': 1, 'unit': '', 'pair': 3131, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'Battery charge energy total'},
        3133: {'name': 'ac_charge_energy_today_high', 'scale': 1, 'unit': '', 'pair': 3134, 'desc': 'AC (grid→battery) charge energy today HIGH'},
        3134: {'name': 'ac_charge_energy_today_low', 'scale': 1, 'unit': '', 'pair': 3133, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'AC (grid→battery) charge energy today'},
        3135: {'name': 'ac_charge_energy_total_high', 'scale': 1, 'unit': '', 'pair': 3136, 'desc': 'AC (grid→battery) charge energy total HIGH (confirmed: 37.4 kWh)'},
        3136: {'name': 'ac_charge_energy_total_low', 'scale': 1, 'unit': '', 'pair': 3135, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'AC (grid→battery) charge energy total'},

        # === BATTERY POWER REGISTERS (3178-3181) ===
        # Some TL-XH models provide unsigned battery power in addition to VPP 31200+ signed power
        # These are fallback registers when VPP 31200+ is not available
        3178: {'name': 'discharge_power_high', 'scale': 1, 'unit': '', 'pair': 3179, 'desc': 'Battery discharge power HIGH (unsigned)'},
        3179: {'name': 'discharge_power_low', 'scale': 1, 'unit': '', 'pair': 3178, 'combined_scale': 0.1, 'combined_unit': 'W', 'desc': 'Battery discharge power (unsigned, positive=discharge)'},
        3180: {'name': 'charge_power_high', 'scale': 1, 'unit': '', 'pair': 3181, 'desc': 'Battery charge power HIGH (unsigned)'},
        3181: {'name': 'charge_power_low', 'scale': 1, 'unit': '', 'pair': 3180, 'combined_scale': 0.1, 'combined_unit': 'W', 'desc': 'Battery charge power (unsigned, positive=charge)'},

        # === VPP V2.01 BATTERY RANGE (31000+) ===

        # Status — VPP_V201_STATUS (31000–31004)
        **VPP_V201_STATUS,

        # Battery Cluster 1 State
        # Per VPP Protocol V2.01: 31200-31201 is signed battery power (positive=charge, negative=discharge)
        31200: {'name': 'battery_power_high', 'scale': 1, 'unit': '', 'pair': 31201},
        31201: {'name': 'battery_power_low',  'scale': 1, 'unit': '', 'pair': 31200, 'combined_scale': 0.1, 'combined_unit': 'W', 'signed': True},
        # VPP V2.01 Battery Energy and Power registers (validated from real-world register scans)
        31202: {'name': 'charge_energy_today_high', 'scale': 1, 'unit': '', 'pair': 31203, 'desc': 'Battery charge energy today HIGH'},
        31203: {'name': 'charge_energy_today_low',  'scale': 1, 'unit': '', 'pair': 31202, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'Battery charge energy today'},
        31204: {'name': 'charge_power_high', 'scale': 1, 'unit': '', 'pair': 31205, 'desc': 'Battery charge power HIGH'},
        31205: {'name': 'charge_power_low',  'scale': 1, 'unit': '', 'pair': 31204, 'combined_scale': 0.1, 'combined_unit': 'W', 'signed': True, 'desc': 'Battery charge power (signed: positive=charging, negative=discharging)'},
        31206: {'name': 'discharge_energy_today_high', 'scale': 1, 'unit': '', 'pair': 31207, 'desc': 'Battery discharge energy today HIGH'},
        31207: {'name': 'discharge_energy_today_low',  'scale': 1, 'unit': '', 'pair': 31206, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'Battery discharge energy today'},
        31208: {'name': 'discharge_power_high', 'scale': 1, 'unit': '', 'pair': 31209, 'desc': 'Battery discharge power HIGH'},
        31209: {'name': 'discharge_power_low',  'scale': 1, 'unit': '', 'pair': 31208, 'combined_scale': 0.1, 'combined_unit': 'W', 'signed': True, 'desc': 'Battery discharge power (signed: positive=discharging, negative=charging)'},
        31214: {'name': 'battery_voltage_vpp', 'scale': 0.1, 'unit': 'V',  'signed': True, 'desc': 'Battery voltage (VPP range - not used on MIN TL-XH, use 3169 instead)'},
        31215: {'name': 'battery_current_vpp', 'scale': 0.1, 'unit': 'A',  'signed': True, 'desc': 'Battery current (VPP range - not used on MIN TL-XH, use 3170 instead)'},
        31217: {'name': 'battery_soc_vpp',     'scale': 1,   'unit': '%',  'desc': 'Battery SOC (VPP range - not used on MIN TL-XH, use 3171 instead)'},
        31222: {'name': 'battery_temp_vpp',    'scale': 0.1, 'unit': '°C', 'signed': True, 'desc': 'Battery temp (VPP range - not used on MIN TL-XH, use 3176 instead)'},

        # Battery power (calculated from charge/discharge)
        31220: {'name': 'battery_power', 'scale': 1, 'unit': 'W', 'desc': 'Battery power (positive=discharge, negative=charge)', 'signed': True},

        # Battery Cluster 2 — VPP_V201_BATTERY2 (31300–31303, 31314–31322)
        **VPP_V201_BATTERY2,
    },
    'holding_registers': {
        0: {'name': 'on_off', 'scale': 1, 'unit': '', 'access': 'RW', 'desc': '0=Off, 1=On'},
        3: {'name': 'active_power_rate', 'scale': 1, 'unit': '%', 'access': 'RW', 'desc': 'Max output power %'},
        30: {'name': 'modbus_address', 'scale': 1, 'unit': '', 'access': 'RW', 'desc': 'Modbus address 1-254'},

        # VPP V2.01 registers
        # protocol_version default=0: MIN TL-XH may report 0 (not 201) depending on firmware.
        # Left inline rather than using VPP_V201_HOLDING_1P to preserve this override.
        30000: {'name': 'dtc_code',          'scale': 1,   'unit': '', 'access': 'RO', 'desc': 'Device Type Code: 5100 for MIN TL-XH', 'default': 5100},
        30099: {'name': 'protocol_version',  'scale': 1,   'unit': '', 'access': 'RO', 'desc': 'VPP Protocol version (may be 0 or 201)', 'default': 0},
        30100: {'name': 'control_authority', 'scale': 1,   'unit': '', 'access': 'RW'},
        30101: {'name': 'remote_onoff',      'scale': 1,   'unit': '', 'access': 'RW', 'maps_to': 'on_off'},
        30114: {'name': 'active_power_rate_vpp', 'scale': 0.1, 'unit': '%', 'access': 'RW', 'maps_to': 'active_power_rate'},
        30200: {'name': 'export_limit_enable',     'scale': 1,   'unit': '', 'access': 'RW'},
        30201: {'name': 'export_limit_power_rate', 'scale': 0.1, 'unit': '%', 'access': 'RW'},

        # Safety/compliance diagnostic registers (read-only, Issue #282)
        235: {'name': 'ntognd_detect',     'scale': 1, 'unit': '', 'access': 'R', 'desc': '0=Disable, 1=Enable — NToGND detection'},
        236: {'name': 'nonstd_vac_enable', 'scale': 1, 'unit': '', 'access': 'R', 'desc': '0=Disable, 1=Grade1, 2=Grade2 — non-standard VAC'},
        237: {'name': 'enable_spec_set',   'scale': 1, 'unit': '', 'access': 'R', 'desc': 'Regional spec bitmask (Bit0=Hungary)'},
        238: {'name': 'fast_mppt_enable',  'scale': 1, 'unit': '', 'access': 'R', 'desc': '0-2 — fast MPPT (Reserved)'},
    }
}

# Export all TL-XH profiles
TL_XH_REGISTER_MAPS = {
    'TL_XH_3000_10000': TL_XH_3000_10000,
    'TL_XH_US_3000_10000': TL_XH_US_3000_10000,
    'TL_XH_3000_10000_V201': TL_XH_3000_10000_V201,
    'TL_XH_US_3000_10000_V201': TL_XH_US_3000_10000_V201,
    'MIN_TL_XH_3000_10000_V201': MIN_TL_XH_3000_10000_V201,
}
