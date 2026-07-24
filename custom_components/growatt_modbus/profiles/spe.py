"""
SPE Series Profiles - Single-Phase Hybrid Solar Inverters (8-12kW)

The SPE 8000-12000 ES is a single-phase hybrid inverter with battery storage,
dual MPPT trackers, and grid-tied peak shaving capability. It supports parallel
operation for capacity expansion up to 108kW.

Key characteristics:
- 8-12kW capacity, single-phase hybrid
- Dual MPPT trackers (PV1 + PV2), max PV input 550VDC
- Two AC input terminals with integrated transfer switch
- Grid-tied with peak shaving capability
- Parallel operation support (up to 108kW)
- Dual outputs for smart load management

Register Layout Notes (from Issue #212 register scan analysis):
- Uses the same 0-97 base register range as SPF
- Register layout shares many SPF-compatible addresses but has key differences:
  * Regs 36/37: SPF uses these for ac_input_power; SPE produces garbage (429GW overflow)
    → These registers are excluded from this profile until the correct mapping is confirmed
  * Regs 64/65: SPF = AC discharge energy today; SPE = grid import energy today (confirmed 20.0 kWh)
  * Regs 66/67: SPF = AC discharge energy total; SPE = grid import energy total (confirmed 855.2 kWh)
  * Regs 85/86: SPF = op discharge energy today; SPE = load energy today (confirmed 21.3 kWh)
  * Regs 87/88: SPF = op discharge energy total; SPE = load energy total (confirmed 1028.3 kWh)
  * Regs 92-97: Generator registers — SPE has no generator input, all zero
- offgrid_protocol flag prevents reading VPP registers (30000+) which return garbage on this firmware

Grid-Tie Export Controls (confirmed via nicauswu field data, Issue #322):
- Holding regs 115-124 control grid-tied export behaviour (not present on SPF)
- Cross-referenced against Off-Grid Protocol V0.26 (docs/developer/protocol-offgrid.md)

DTC Identification:
- This device returned DTC 64541 (unknown, not in standard mapping) in the Issue #212 scan
- Auto-detection falls back to legacy range analysis for this device
- See auto_detection.py for manual profile override instructions

Battery Power Sign Convention:
Same as SPF — hardware reports inverted convention (positive=discharge, negative=charge).
Negative scale (-0.1) on registers 77/78 converts to standard HA convention.
"""

from .spf import SPF_3000_6000_ES_PLUS

# Build SPE input registers by modifying the SPF base
# All confirmed register mappings are validated against Issue #212 daytime scan
# cross-referenced with actual entity values from the XLSX file
_spe_input_regs = dict(SPF_3000_6000_ES_PLUS['input_registers'])

# ── Remove registers that are wrong or absent on SPE ──────────────────────────

# Regs 36/37: SPF maps these as ac_input_power_high/low but SPE produces 429GW overflow.
# The 32-bit value appears to be a signed grid power register that the coordinator
# interprets as unsigned, yielding 0xFFFFFFE4 → 4,294,966,436 × 0.1 = 429,496,643.6W.
# Excluded until the correct signed semantics are confirmed from a cleaner scan.
for _addr in (36, 37):
    _spe_input_regs.pop(_addr, None)

# Regs 92-97: Generator discharge energy, generator power, generator voltage.
# SPE has no generator input port — these registers are all zero and inapplicable.
for _addr in (92, 93, 94, 95, 96, 97):
    _spe_input_regs.pop(_addr, None)

# ── Add grid export energy registers (SPE grid-tied, not present in SPF) ─────
# Reg 44 = DTC (Device Type Code) per Off-Grid Protocol V0.26 — NOT overridden here.
# Reg 45 = Export to Grid Today — single 16-bit register (scale 0.1 kWh) per V0.26.
#   Nicauswu's implementation also reads this as a standalone register. Max 6553.5 kWh
#   is sufficient for daily totals.
# Regs 46/47 = Export to Grid Total — 32-bit pair, combined scale 0.1 kWh per V0.26.
_spe_input_regs.update({
    45: {
        'name': 'energy_to_grid_today', 'scale': 0.1, 'unit': 'kWh',
        'desc': 'Grid export energy today (single 16-bit register). Protocol V0.26 reg 45.',
    },
    46: {
        'name': 'energy_to_grid_total_high', 'scale': 1, 'unit': '', 'pair': 47,
        'desc': 'Grid export energy total (HIGH word). Protocol V0.26 reg 46.',
    },
    47: {
        'name': 'energy_to_grid_total_low', 'scale': 1, 'unit': '', 'pair': 46,
        'combined_scale': 0.1, 'combined_unit': 'kWh',
        'desc': 'Grid export energy total (LOW word). Protocol V0.26 reg 47.',
    },
})

# ── Remap energy registers: SPF names are semantically wrong for SPE ──────────

# Regs 64/65: SPF labels these "AC discharge energy today" (battery-to-load via inverter).
# On SPE these registers track GRID IMPORT energy today.
# Confirmed: scan raw 200 × 0.1 = 20.0 kWh, actual grid import = 19.8 kWh ✓
_spe_input_regs.update({
    64: {
        'name': 'ac_discharge_energy_today_high', 'scale': 1, 'unit': '', 'pair': 65,
        'desc': 'Grid import energy today (HIGH word) [SPE: different semantics from SPF at same address]',
    },
    65: {
        'name': 'ac_discharge_energy_today_low', 'scale': 1, 'unit': '', 'pair': 64,
        'combined_scale': 0.1, 'combined_unit': 'kWh',
        'desc': 'Grid import energy today (LOW word). Confirmed ≈ 20.0 kWh (#212)',
    },
})

# Regs 66/67: SPF labels these "AC discharge energy total".
# On SPE these registers track GRID IMPORT energy total (lifetime).
# Confirmed: scan raw 8552 × 0.1 = 855.2 kWh, actual = 855.2 kWh ✓
_spe_input_regs.update({
    66: {
        'name': 'ac_discharge_energy_total_high', 'scale': 1, 'unit': '', 'pair': 67,
        'desc': 'Grid import energy total (HIGH word)',
    },
    67: {
        'name': 'ac_discharge_energy_total_low', 'scale': 1, 'unit': '', 'pair': 66,
        'combined_scale': 0.1, 'combined_unit': 'kWh',
        'desc': 'Grid import energy total (LOW word). Confirmed 855.2 kWh (#212)',
    },
})

# Regs 85/86: SPF labels these "operational discharge energy today".
# On SPE these registers track LOAD ENERGY consumed today (all sources: PV + grid + battery).
# Confirmed: scan raw 213 × 0.1 = 21.3 kWh, actual load today = 20.9 kWh ✓
_spe_input_regs.update({
    85: {
        'name': 'load_energy_today_high', 'scale': 1, 'unit': '', 'pair': 86,
        'desc': 'Load energy today (HIGH word)',
    },
    86: {
        'name': 'load_energy_today_low', 'scale': 1, 'unit': '', 'pair': 85,
        'combined_scale': 0.1, 'combined_unit': 'kWh',
        'desc': 'Load energy today (LOW word). Confirmed 21.3 kWh actual 20.9 kWh (#212)',
    },
})

# Regs 87/88: SPF labels these "operational discharge energy total".
# On SPE these registers track LOAD ENERGY consumed total (lifetime).
# Confirmed: scan raw 10283 × 0.1 = 1028.3 kWh, actual load total = 1027.9 kWh ✓
_spe_input_regs.update({
    87: {
        'name': 'load_energy_total_high', 'scale': 1, 'unit': '', 'pair': 88,
        'desc': 'Load energy total (HIGH word)',
    },
    88: {
        'name': 'load_energy_total_low', 'scale': 1, 'unit': '', 'pair': 87,
        'combined_scale': 0.1, 'combined_unit': 'kWh',
        'desc': 'Load energy total (LOW word). Confirmed 1028.3 kWh actual 1027.9 kWh (#212)',
    },
})

SPE_8000_12000_ES = {
    'name': 'SPE 8000-12000 ES',
    'description': 'Single-phase hybrid inverter with battery storage (8-12kW)',
    'notes': (
        'Uses SPF-compatible 0-97 register range with key remapping. '
        'Reg 45 = grid export energy today (single 16-bit, 0.1 kWh). '
        'Regs 46/47 = grid export energy total (32-bit pair). '
        'Regs 64/65 = grid import energy (not AC discharge), '
        'Regs 85-88 = load energy today/total (not operational discharge). '
        'Regs 36/37 (ac_input_power) excluded — produces 429GW overflow. '
        'No generator input. '
        'Grid-tie controls at holding regs 115-124 (confirmed via Issue #322, Protocol V0.26).'
    ),
    # NOTE: offgrid_protocol refers to the REGISTER LAYOUT (SPF-style 0-97),
    # not the inverter's grid capability. The SPE supports grid-tied operation
    # with peak shaving. This flag prevents reading VPP registers (30000+)
    # which return garbage data on this device firmware.
    'offgrid_protocol': True,
    'input_registers': _spe_input_regs,
    'holding_registers': {
        # Holding registers inherited from SPF — confirmed consistent with
        # entity values seen in Issue #212 scan (charge_current, battery_type,
        # ac_input_mode, output_config, charge_config all reading correctly).
        **SPF_3000_6000_ES_PLUS['holding_registers'],

        # ── SPE grid-tie export controls ──────────────────────────────────────
        # All confirmed via nicauswu field data (Issue #322).
        # Cross-referenced against Off-Grid Protocol V0.26 holding register table.
        # Ranges and names from V0.26 unless noted.

        # 115: uwFeedEn — grid feed enable
        115: {'name': 'spe_grid_export_enable', 'scale': 1, 'unit': '', 'access': 'RW',
              'desc': 'Grid export enable (uwFeedEn): 0=Disabled, 1=Enabled',
              'values': {0: 'Disabled', 1: 'Enabled'}},

        # 116: uwLoadFirst — output priority in SUB mode (LCD acronyms confirmed via Issue #322)
        # BLU=Battery-Load-Utility, LBU=Load-Battery-Utility, LUB=Load-Utility-Battery
        116: {'name': 'spe_output_priority', 'scale': 1, 'unit': '', 'access': 'RW',
              'desc': 'PV Energy Priority in SUB Mode (uwLoadFirst): 0=BLU, 1=LBU, 2=LUB',
              'values': {0: 'BLU', 1: 'LBU', 2: 'LUB'}},

        # 117: uwFeedRange — grid compliance region (firmware-determined, read-only on most units)
        # nicauswu reports value 7 (South Africa Alt) — write attempts rejected by firmware
        117: {'name': 'spe_feed_range', 'scale': 1, 'unit': '', 'access': 'R',
              'desc': 'Grid compliance region (uwFeedRange): 0=Asia, 1=Europe, 2=S.America, 3=S.Africa, 7=S.Africa (Alt). Firmware-determined; writes may be rejected.',
              'values': {0: 'Asia', 1: 'Europe', 2: 'South America', 3: 'South Africa', 7: 'South Africa (Alt)'}},

        # 118: uwBatFeedEn — battery-to-grid export enable
        118: {'name': 'spe_battery_export_enable', 'scale': 1, 'unit': '', 'access': 'RW',
              'desc': 'Battery-to-grid export enable (uwBatFeedEn): 0=Disabled, 1=Enabled',
              'values': {0: 'Disabled', 1: 'Enabled'}},

        # 119: uwFeedPow — feed power limit (0-120 raw = 0-12.0 kW)
        119: {'name': 'spe_export_limit_power', 'scale': 0.1, 'unit': 'kW', 'access': 'RW',
              'valid_range': (0, 120),
              'desc': 'Grid export power limit (uwFeedPow): 0-12 kW (raw 0-120, scale 0.1)'},

        # 120: uwBatFeedCurr — max battery current for grid export
        # Protocol V0.26 states 0-400 A; nicauswu confirmed hardware cap at 280 A on SPE 12000ES
        120: {'name': 'spe_battery_export_max_current', 'scale': 1, 'unit': 'A', 'access': 'RW',
              'valid_range': (0, 280),
              'desc': 'Max battery current for grid export (uwBatFeedCurr): 0-280 A (hardware cap confirmed on SPE 12000ES)'},

        # 121: uwBatFeedVLoss — battery voltage at which export stops (420-540, units: 0.1V = 42-54V)
        121: {'name': 'spe_bat_feed_vloss', 'scale': 0.1, 'unit': 'V', 'access': 'RW',
              'valid_range': (420, 540),
              'desc': 'Battery voltage loss point to stop export (uwBatFeedVLoss): 42-54V (raw 420-540)'},

        # 122: uwBatFeedVBack — battery voltage at which export resumes (440-560, units: 0.1V = 44-56V)
        122: {'name': 'spe_bat_feed_vback', 'scale': 0.1, 'unit': 'V', 'access': 'RW',
              'valid_range': (440, 560),
              'desc': 'Battery voltage back point to resume export (uwBatFeedVBack): 44-56V (raw 440-560)'},

        # 123: uwBatFeedSocLoss — minimum SOC to allow export (5-90 %)
        # NOTE: SPH reg 123 = export_limit_power (%). WRITABLE_REGISTERS carries
        # not_profiles=['SPE_8000_12000_ES'] on that entry to prevent cross-contamination.
        # Protocol V0.26 valid range is 5-90 (not 0-100 as nicauswu had).
        123: {'name': 'spe_export_min_soc', 'scale': 1, 'unit': '%', 'access': 'RW',
              'valid_range': (5, 90),
              'desc': 'Min battery SOC to allow export (uwBatFeedSocLoss): 5-90% (Protocol V0.26)'},

        # 124: uwBatFeedSocBack — SOC hysteresis to re-enable export (15-100 %)
        124: {'name': 'spe_export_back_soc', 'scale': 1, 'unit': '%', 'access': 'RW',
              'valid_range': (15, 100),
              'desc': 'SOC back point to resume export (uwBatFeedSocBack): 15-100% (Protocol V0.26)'},
    },
}

# Export register maps for import by __init__.py
SPE_REGISTER_MAPS = {
    'SPE_8000_12000_ES': SPE_8000_12000_ES,
}
