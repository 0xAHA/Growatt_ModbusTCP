"""
VPP Protocol V2.01 Shared Register Blocks

Register definitions that are identical across multiple VPP V2.01 inverter
profiles.  Profiles import and unpack these dicts with ** then override
individual registers as needed.

Grep index — all register keys defined here:
  VPP_V201_STATUS:            31000–31004
  VPP_V201_PV2_INPUT:         31010–31017  (PV string 1 and 2)
  VPP_V201_PV2_TOTAL:         31018–31019  (total PV power, 2-string profiles)
  VPP_V201_PV3_AND_TOTAL:     31018–31023  (PV string 3 + total, 3-string profiles)
  VPP_V201_ENERGY_1P:         31120–31123  (single-phase energy today/total)
  VPP_V201_TEMPERATURE_1P:    31130–31132  (single-phase temperatures)
  VPP_V201_BATTERY2:          31300–31303, 31314–31322  (battery cluster 2)
  VPP_V201_HOLDING_1P:        30099–30109, 30114, 30200–30201

Usage guide
-----------
2-string profiles:
    **VPP_V201_STATUS, **VPP_V201_PV2_INPUT, **VPP_V201_PV2_TOTAL, ...

3-string profiles:
    **VPP_V201_STATUS, **VPP_V201_PV2_INPUT, **VPP_V201_PV3_AND_TOTAL, ...
    (VPP_V201_PV3_AND_TOTAL occupies the same 31018–31019 addresses as
    VPP_V201_PV2_TOTAL; they must not both be unpacked.)

Profiles NOT using these blocks
--------------------------------
AC output block (31100–31119): varies between families.
  - Single-phase: SPH omits maps_to on meter_power; MIN/TL-XH map to power_to_grid.
  - Three-phase:  SPH-TL3/MID use different register names for phase voltages.
Battery cluster 1 (31200–31222): SPH and TL-XH interpret registers 31202–31209
  differently (SPH: 31202=charge today, 31204=charge total, 31206=discharge today,
  31208=discharge total; TL-XH: charge/discharge power).  Left inline in each
  profile to make the difference explicit.
"""

# ---------------------------------------------------------------------------
# Status — identical across all V2.01 profiles
# ---------------------------------------------------------------------------

VPP_V201_STATUS = {
    31000: {'name': 'equipment_status',   'scale': 1, 'unit': '', 'desc': 'Equipment running status'},
    31001: {'name': 'system_fault_word0', 'scale': 1, 'unit': '', 'desc': 'System fault word 0'},
    31002: {'name': 'system_fault_word1', 'scale': 1, 'unit': '', 'desc': 'System fault word 1'},
    31003: {'name': 'system_fault_word2', 'scale': 1, 'unit': '', 'desc': 'System fault word 2'},
    31004: {'name': 'grid_first_connected', 'scale': 1, 'unit': '', 'desc': 'Grid first connected status'},
}

# ---------------------------------------------------------------------------
# PV strings 1 and 2 — identical across all V2.01 profiles with PV inputs
# ---------------------------------------------------------------------------

VPP_V201_PV2_INPUT = {
    31010: {'name': 'pv1_voltage_vpp',    'scale': 0.1, 'unit': 'V',  'maps_to': 'pv1_voltage'},
    31011: {'name': 'pv1_current_vpp',    'scale': 0.1, 'unit': 'A',  'maps_to': 'pv1_current'},
    31012: {'name': 'pv1_power_high_vpp', 'scale': 1,   'unit': '',   'pair': 31013, 'maps_to': 'pv1_power'},
    31013: {'name': 'pv1_power_low_vpp',  'scale': 1,   'unit': '',   'pair': 31012,
            'combined_scale': 0.1, 'combined_unit': 'W'},
    31014: {'name': 'pv2_voltage_vpp',    'scale': 0.1, 'unit': 'V',  'maps_to': 'pv2_voltage'},
    31015: {'name': 'pv2_current_vpp',    'scale': 0.1, 'unit': 'A',  'maps_to': 'pv2_current'},
    31016: {'name': 'pv2_power_high_vpp', 'scale': 1,   'unit': '',   'pair': 31017, 'maps_to': 'pv2_power'},
    31017: {'name': 'pv2_power_low_vpp',  'scale': 1,   'unit': '',   'pair': 31016,
            'combined_scale': 0.1, 'combined_unit': 'W'},
}

# ---------------------------------------------------------------------------
# Total PV power — 2-string profiles (occupies 31018–31019)
# Use this XOR VPP_V201_PV3_AND_TOTAL (they share addresses 31018–31019).
# ---------------------------------------------------------------------------

VPP_V201_PV2_TOTAL = {
    31018: {'name': 'pv_total_power_high_vpp', 'scale': 1, 'unit': '', 'pair': 31019,
            'maps_to': 'pv_total_power'},
    31019: {'name': 'pv_total_power_low_vpp',  'scale': 1, 'unit': '', 'pair': 31018,
            'combined_scale': 0.1, 'combined_unit': 'W'},
}

# ---------------------------------------------------------------------------
# PV string 3 + total PV power — 3-string profiles (occupies 31018–31023)
# Replaces VPP_V201_PV2_TOTAL; PV3 reuses 31018–31019 and total shifts to
# 31022–31023.
# ---------------------------------------------------------------------------

VPP_V201_PV3_AND_TOTAL = {
    31018: {'name': 'pv3_voltage_vpp',         'scale': 0.1, 'unit': 'V',  'maps_to': 'pv3_voltage'},
    31019: {'name': 'pv3_current_vpp',         'scale': 0.1, 'unit': 'A',  'maps_to': 'pv3_current'},
    31020: {'name': 'pv3_power_high_vpp',      'scale': 1,   'unit': '',   'pair': 31021,
            'maps_to': 'pv3_power'},
    31021: {'name': 'pv3_power_low_vpp',       'scale': 1,   'unit': '',   'pair': 31020,
            'combined_scale': 0.1, 'combined_unit': 'W'},
    31022: {'name': 'pv_total_power_high_vpp', 'scale': 1,   'unit': '',   'pair': 31023,
            'maps_to': 'pv_total_power'},
    31023: {'name': 'pv_total_power_low_vpp',  'scale': 1,   'unit': '',   'pair': 31022,
            'combined_scale': 0.1, 'combined_unit': 'W'},
}

# ---------------------------------------------------------------------------
# Energy today / total — single-phase V2.01 profiles (SPH, MIN, TL-XH)
# NOT used by SPH-TL3 or MID: those profiles map different quantities to
# 31120–31123 (grid-energy counters, not inverter output energy).
# ---------------------------------------------------------------------------

VPP_V201_ENERGY_1P = {
    31120: {'name': 'energy_today_high_vpp', 'scale': 1, 'unit': '', 'pair': 31121,
            'maps_to': 'energy_today'},
    31121: {'name': 'energy_today_low_vpp',  'scale': 1, 'unit': '', 'pair': 31120,
            'combined_scale': 0.1, 'combined_unit': 'kWh'},
    31122: {'name': 'energy_total_high_vpp', 'scale': 1, 'unit': '', 'pair': 31123,
            'maps_to': 'energy_total'},
    31123: {'name': 'energy_total_low_vpp',  'scale': 1, 'unit': '', 'pair': 31122,
            'combined_scale': 0.1, 'combined_unit': 'kWh'},
}

# ---------------------------------------------------------------------------
# Temperatures — single-phase V2.01 profiles (SPH, MIN, TL-XH)
# NOT used by SPH-TL3 (has only 31130) or MID (different temp layout).
# ---------------------------------------------------------------------------

VPP_V201_TEMPERATURE_1P = {
    31130: {'name': 'inverter_temp_vpp', 'scale': 0.1, 'unit': '°C',
            'maps_to': 'inverter_temp', 'signed': True},
    31131: {'name': 'ipm_temp_vpp',     'scale': 0.1, 'unit': '°C',
            'maps_to': 'ipm_temp',      'signed': True},
    31132: {'name': 'boost_temp_vpp',   'scale': 0.1, 'unit': '°C',
            'maps_to': 'boost_temp',    'signed': True},
}

# ---------------------------------------------------------------------------
# Battery cluster 2 — all hybrid V2.01 profiles (SPH, TL-XH, SPH-TL3)
# Verified identical across all three families.
# ---------------------------------------------------------------------------

VPP_V201_BATTERY2 = {
    31300: {'name': 'battery2_power_high',        'scale': 1,   'unit': '', 'pair': 31301},
    31301: {'name': 'battery2_power',             'scale': 1,   'unit': '', 'pair': 31300,
            'combined_scale': 0.1, 'combined_unit': 'W', 'signed': True},
    31302: {'name': 'battery2_charge_power_high', 'scale': 1,   'unit': '', 'pair': 31303},
    31303: {'name': 'battery2_charge_power_low',  'scale': 1,   'unit': '', 'pair': 31302,
            'combined_scale': 0.1, 'combined_unit': 'W'},
    31314: {'name': 'battery2_voltage',  'scale': 0.1, 'unit': 'V',
            'desc': 'Battery 2 voltage (0 if not present)', 'signed': True},
    31315: {'name': 'battery2_current',  'scale': 0.1, 'unit': 'A', 'signed': True},
    31317: {'name': 'battery2_soc',      'scale': 1,   'unit': '%'},
    31322: {'name': 'battery2_temp',     'scale': 0.1, 'unit': '°C', 'signed': True},
}

# ---------------------------------------------------------------------------
# Holding registers — single-phase V2.01 profiles (SPH, MIN, TL-XH)
# Excludes 30000 (DTC code): each profile provides its own 'default' value.
# NOT used by SPH-TL3 (lacks 30114) or MID (different layout).
# ---------------------------------------------------------------------------

VPP_V201_HOLDING_1P = {
    30099: {'name': 'protocol_version',      'scale': 1,   'unit': '', 'access': 'RO',
            'desc': 'VPP Protocol version (201 = V2.01)', 'default': 201},
    30100: {'name': 'control_authority',     'scale': 1,   'unit': '', 'access': 'RW',
            'desc': '0=Disable, 1=Enable control'},
    30101: {'name': 'remote_onoff',          'scale': 1,   'unit': '', 'access': 'RW',
            'desc': '0=Off, 1=On', 'maps_to': 'on_off'},
    30104: {'name': 'sys_year_vpp',          'scale': 1,   'unit': '', 'access': 'RW'},
    30105: {'name': 'sys_month_vpp',         'scale': 1,   'unit': '', 'access': 'RW'},
    30106: {'name': 'sys_day_vpp',           'scale': 1,   'unit': '', 'access': 'RW'},
    30107: {'name': 'sys_hour_vpp',          'scale': 1,   'unit': '', 'access': 'RW'},
    30108: {'name': 'sys_minute_vpp',        'scale': 1,   'unit': '', 'access': 'RW'},
    30109: {'name': 'sys_second_vpp',        'scale': 1,   'unit': '', 'access': 'RW'},
    30114: {'name': 'active_power_rate_vpp', 'scale': 0.1, 'unit': '%', 'access': 'RW',
            'maps_to': 'active_power_rate'},
    30200: {'name': 'export_limit_enable',       'scale': 1,   'unit': '', 'access': 'RW',
            'desc': '0=Disable, 1=Enable'},
    30201: {'name': 'export_limit_power_rate',   'scale': 0.1, 'unit': '%', 'access': 'RW'},
}
