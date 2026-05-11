# TL3-S Series - Three-Phase Grid-Tied String Inverters (Legacy Protocol)
# 3-phase grid-tied string inverters, 3-15kW
# Register range: 0-179 (legacy protocol, same base as MIC)
# DTC 2049 at holding register 43

TL3_S_3000_15000 = {
    'name': 'TL3-S 3000-15000',
    'description': 'Three-phase grid-tied string inverter (3-15kW), legacy protocol',
    'notes': (
        'Legacy 0-179 register range. Two MPPT inputs: PV1 (regs 3-6), PV2 voltage/current only (regs 7-8). '
        'Regs 9-10 are firmware version bytes (ASCII "DH"/"1.") not PV2 power — pv2_power stays 0, use pv_total_power. '
        'AC output total at reg 12 (standalone 16-bit, named ac_power_low). '
        'Per-phase output at regs 16-25 (R/S/T power confirmed by sum crosscheck: 1823+1837+1805=5465W ≈ 5458W total ✓). '
        'Phase T voltage/current location unclear (regs 26/27 show 0/10 which do not match expected ~420V/7.5A). '
        'Energy at regs 53 and 55 as standalone 16-bit (×0.1 kWh). '
        'Temperature at reg 32 (38.7°C confirmed). DTC 2049 at holding reg 43. Firmware DH1.0. '
        'No VPP support (holding reg 30000 returns Illegal Function). '
        'Regs 35-39 are all zero (MID-style AC layout does NOT apply to this model).'
    ),
    'input_registers': {
        # System Status
        0: {'name': 'inverter_status', 'scale': 1, 'unit': '', 'desc': '0=Waiting, 1=Normal, 3=Fault'},

        # PV Total Power (32-bit) — confirmed: HIGH=0, LOW=60163 → 6016.3W
        1: {'name': 'pv_total_power_high', 'scale': 1, 'unit': '', 'pair': 2},
        2: {'name': 'pv_total_power_low', 'scale': 1, 'unit': '', 'pair': 1, 'combined_scale': 0.1, 'combined_unit': 'W'},

        # PV String 1 — confirmed: 510.3V / 5.8A / 2959.7W
        3: {'name': 'pv1_voltage', 'scale': 0.1, 'unit': 'V'},
        4: {'name': 'pv1_current', 'scale': 0.1, 'unit': 'A'},
        5: {'name': 'pv1_power_high', 'scale': 1, 'unit': '', 'pair': 6},
        6: {'name': 'pv1_power_low', 'scale': 1, 'unit': '', 'pair': 5, 'combined_scale': 0.1, 'combined_unit': 'W'},

        # PV String 2 — voltage/current confirmed: 527.0V / 5.8A
        # Regs 9-10 contain firmware version bytes ('DH' = 0x4448 = 17480, '1.' = 0x312E = 12590)
        # and must NOT be mapped as pv2_power. pv2_power is computed from pv_total_power - pv1_power.
        7: {'name': 'pv2_voltage', 'scale': 0.1, 'unit': 'V'},
        8: {'name': 'pv2_current', 'scale': 0.1, 'unit': 'A'},

        # AC Output — Total
        # Reg 12: standalone 16-bit AC active power (named ac_power_low so coordinator finds it).
        #   Scan: 54581 × 0.1 = 5458.1W; crosscheck: sum of phase powers 1823+1837+1805=5465W ✓
        # Reg 11 = 12320 is firmware version byte '0 ' (0x3020), not reactive power.
        # Regs 35-39 (MID-style AC layout) are ALL ZERO for this model.
        12: {'name': 'ac_power_low', 'scale': 0.1, 'unit': 'W', 'desc': 'Total AC active output power (standalone 16-bit)'},
        13: {'name': 'ac_frequency', 'scale': 0.01, 'unit': 'Hz'},
        14: {'name': 'ac_voltage', 'scale': 0.1, 'unit': 'V', 'desc': 'Line-to-line voltage (avg)'},
        15: {'name': 'ac_current', 'scale': 0.1, 'unit': 'A'},

        # Per-Phase AC Output — confirmed from scan, 4-register groups per phase (32-bit power + V + I)
        # Sum crosscheck: 1823.1 + 1837.4 + 1805.0 = 5465.5W ≈ 5458.1W total ✓

        # Phase R — confirmed: 1823.1W / 425.2V / 7.5A
        16: {'name': 'ac_power_r_high', 'scale': 1, 'unit': '', 'pair': 17},
        17: {'name': 'ac_power_r_low', 'scale': 1, 'unit': '', 'pair': 16, 'combined_scale': 0.1, 'combined_unit': 'W'},
        18: {'name': 'ac_voltage_r', 'scale': 0.1, 'unit': 'V'},
        19: {'name': 'ac_current_r', 'scale': 0.1, 'unit': 'A'},

        # Phase S — confirmed: 1837.4W / 420.7V / 7.5A
        20: {'name': 'ac_power_s_high', 'scale': 1, 'unit': '', 'pair': 21},
        21: {'name': 'ac_power_s_low', 'scale': 1, 'unit': '', 'pair': 20, 'combined_scale': 0.1, 'combined_unit': 'W'},
        22: {'name': 'ac_voltage_s', 'scale': 0.1, 'unit': 'V'},
        23: {'name': 'ac_current_s', 'scale': 0.1, 'unit': 'A'},

        # Phase T — power confirmed: 1805.0W (regs 24-25 pair)
        # Voltage/current not mapped: regs 26/27 show 0 and 10 which don't match expected ~420V/7.5A.
        24: {'name': 'ac_power_t_high', 'scale': 1, 'unit': '', 'pair': 25},
        25: {'name': 'ac_power_t_low', 'scale': 1, 'unit': '', 'pair': 24, 'combined_scale': 0.1, 'combined_unit': 'W'},

        # Temperature — confirmed: reg 32 = 387 × 0.1 = 38.7°C
        32: {'name': 'inverter_temp', 'scale': 0.1, 'unit': '°C', 'signed': True},

        # Energy — standalone 16-bit (NOT 32-bit pairs)
        # Reg 53: 54 × 0.1 = 5.4 kWh today ✓ | Reg 55: 61329 × 0.1 = 6132.9 kWh total ✓
        53: {'name': 'energy_today_low', 'scale': 0.1, 'unit': 'kWh', 'desc': 'AC energy today (standalone 16-bit)'},
        55: {'name': 'energy_total_low', 'scale': 0.1, 'unit': 'kWh', 'desc': 'AC energy total (standalone 16-bit)'},

        # Diagnostics
        105: {'name': 'fault_code', 'scale': 1, 'unit': ''},
        112: {'name': 'warning_code', 'scale': 1, 'unit': ''},
    },
    'holding_registers': {
        0: {'name': 'on_off', 'scale': 1, 'unit': '', 'access': 'RW', 'desc': '0=Off, 1=On'},
        3: {'name': 'active_power_rate', 'scale': 1, 'unit': '%', 'access': 'RW', 'desc': 'Max output active power percent (0-100)'},
        30: {'name': 'com_address', 'scale': 1, 'unit': '', 'access': 'RW', 'desc': 'Modbus communication address'},
    },
}

TL3S_REGISTER_MAPS = {
    'TL3_S_3000_15000': TL3_S_3000_15000,
}
