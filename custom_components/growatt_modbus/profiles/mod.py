from .vpp_v201 import VPP_V201_BATTERY3, VPP_V201_BATTERY4

# MOD-6000-15000TL3-XH (Three-phase hybrid with battery, 6-15kW)
MOD_6000_15000TL3_XH = {
    'name': 'MOD TL3-XH Series',
    'description': 'Modular three-phase hybrid inverter with battery (6-15kW)',
    'notes': 'Uses 0-124 base range + 3000+ battery range. Validated with real hardware 2025-10-26.',
    'use_mppt_energy_today': True,  # Reg 53/54 = system AC output incl. battery discharge; use per-MPPT DC sum instead
    'input_registers': {
        # === BASE RANGE (0-124) - Inverter Data ===
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
        
        # PV String 3 (optional - often unused)
        11: {'name': 'pv3_voltage', 'scale': 0.1, 'unit': 'V'},
        12: {'name': 'pv3_current', 'scale': 0.1, 'unit': 'A'},
        13: {'name': 'pv3_power_high', 'scale': 1, 'unit': '', 'pair': 14},
        14: {'name': 'pv3_power_low', 'scale': 1, 'unit': '', 'pair': 13, 'combined_scale': 0.1, 'combined_unit': 'W'},
        
        # Output Power Total (32-bit) — true three-phase inverter output total.
        # Aliased to ac_power so the generic ac_power sensor reflects the correct total.
        # Do NOT alias ac_power_r (reg 40/41) — that is Phase R only, not total.
        35: {'name': 'output_power_high', 'scale': 1, 'unit': '', 'pair': 36, 'alias': 'ac_power_high'},
        36: {'name': 'output_power_low', 'scale': 1, 'unit': '', 'pair': 35, 'combined_scale': 0.1, 'combined_unit': 'W', 'alias': 'ac_power_low'},

        # === AC OUTPUT - THREE PHASE ===
        # Grid Frequency (shared across all phases)
        37: {'name': 'ac_frequency', 'scale': 0.01, 'unit': 'Hz', 'desc': 'AC output frequency'},

        # Phase R (L1) — ac_voltage/ac_current aliased for generic code; ac_power NOT aliased here
        # (ac_power comes from output_power reg 35/36 which holds the true three-phase total)
        38: {'name': 'ac_voltage_r', 'scale': 0.1, 'unit': 'V', 'desc': 'Phase R AC voltage', 'alias': 'ac_voltage'},
        39: {'name': 'ac_current_r', 'scale': 0.1, 'unit': 'A', 'desc': 'Phase R AC current', 'alias': 'ac_current'},
        40: {'name': 'ac_power_r_high', 'scale': 1, 'unit': '', 'pair': 41},
        41: {'name': 'ac_power_r_low', 'scale': 1, 'unit': '', 'pair': 40, 'combined_scale': 0.1, 'combined_unit': 'VA'},

        # Phase S (L2) - AC Output
        42: {'name': 'ac_voltage_s', 'scale': 0.1, 'unit': 'V', 'desc': 'Phase S AC voltage'},
        43: {'name': 'ac_current_s', 'scale': 0.1, 'unit': 'A', 'desc': 'Phase S AC current'},
        44: {'name': 'ac_power_s_high', 'scale': 1, 'unit': '', 'pair': 45},
        45: {'name': 'ac_power_s_low', 'scale': 1, 'unit': '', 'pair': 44, 'combined_scale': 0.1, 'combined_unit': 'VA'},
        
        # Phase T (L3) - AC Output
        46: {'name': 'ac_voltage_t', 'scale': 0.1, 'unit': 'V', 'desc': 'Phase T AC voltage'},
        47: {'name': 'ac_current_t', 'scale': 0.1, 'unit': 'A', 'desc': 'Phase T AC current'},
        48: {'name': 'ac_power_t_high', 'scale': 1, 'unit': '', 'pair': 49},
        49: {'name': 'ac_power_t_low', 'scale': 1, 'unit': '', 'pair': 48, 'combined_scale': 0.1, 'combined_unit': 'VA'},
        
        # Line-to-Line Voltages (three-phase only)
        50: {'name': 'line_voltage_rs', 'scale': 0.1, 'unit': 'V', 'desc': 'Line voltage R-S'},
        51: {'name': 'line_voltage_st', 'scale': 0.1, 'unit': 'V', 'desc': 'Line voltage S-T'},
        52: {'name': 'line_voltage_tr', 'scale': 0.1, 'unit': 'V', 'desc': 'Line voltage T-R'},
        
        # Energy Today (32-bit) - VALIDATED: 8.1kWh
        53: {'name': 'energy_today_high', 'scale': 1, 'unit': '', 'pair': 54},
        54: {'name': 'energy_today_low', 'scale': 1, 'unit': '', 'pair': 53, 'combined_scale': 0.1, 'combined_unit': 'kWh'},

        # Energy Total (32-bit)
        55: {'name': 'energy_total_high', 'scale': 1, 'unit': '', 'pair': 56},
        56: {'name': 'energy_total_low', 'scale': 1, 'unit': '', 'pair': 55, 'combined_scale': 0.1, 'combined_unit': 'kWh'},

        # PV String Energy (per MPPT, daily and lifetime) — confirmed in scan #228
        59: {'name': 'pv1_energy_today_high', 'scale': 1, 'unit': '', 'pair': 60, 'desc': 'PV1 energy today HIGH'},
        60: {'name': 'pv1_energy_today_low', 'scale': 1, 'unit': '', 'pair': 59, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        61: {'name': 'pv1_energy_total_high', 'scale': 1, 'unit': '', 'pair': 62, 'desc': 'PV1 DC energy total HIGH'},
        62: {'name': 'pv1_energy_total_low', 'scale': 1, 'unit': '', 'pair': 61, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'PV1 DC energy total LOW'},
        63: {'name': 'pv2_energy_today_high', 'scale': 1, 'unit': '', 'pair': 64, 'desc': 'PV2 energy today HIGH'},
        64: {'name': 'pv2_energy_today_low', 'scale': 1, 'unit': '', 'pair': 63, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        65: {'name': 'pv2_energy_total_high', 'scale': 1, 'unit': '', 'pair': 66, 'desc': 'PV2 DC energy total HIGH'},
        66: {'name': 'pv2_energy_total_low', 'scale': 1, 'unit': '', 'pair': 65, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'PV2 DC energy total LOW'},

        # PV3 energy — the map previously jumped from 66 straight to 91, so a third string
        # was invisible to every per-string figure while its power sensors worked fine.
        #
        # The daily consequence is the one that reached users: use_mppt_energy_today sums
        # the per-string counters, so a three-string system under-reported daily solar by a
        # whole string. On a MID 25KTL3-XH that was 17.6 kWh against the portal's 29.5.
        #
        # Confirmed by prediction, then measurement (#381). PV3 lifetime was derived from
        # registers already mapped — 91/92 (all strings, 3611.9) minus PV1 (1268.4) minus
        # PV2 (801.1) = 1542.4 — which predicted a raw 15424 at 69/70 before anyone read it.
        # The scan returned exactly 15424, and 67/68 returned 119, giving 11.9 kWh for the
        # day. PV1 9.4 + PV2 8.2 + PV3 11.9 = 29.5, matching the portal's daily solar figure
        # to the decimal.
        #
        # Independently re-confirmed on a second MID 25KTL3-XH (#399). That reporter had
        # decoded 59-70 himself into template sensors before v1.6.3 shipped, and read both
        # at the same moment after retiring the workaround:
        #
        #     PV1 1451.3 = 1451.3   PV2 929.4 = 929.4   PV3 1792.3 = 1792.3
        #
        # Exact on all three. Two independent decodes of the same addresses agreeing to the
        # decimal is as strong as this gets short of a manufacturer statement - the pairing,
        # the word order and the 0.1 scale are all settled.
        67: {'name': 'pv3_energy_today_high', 'scale': 1, 'unit': '', 'pair': 68, 'desc': 'PV3 DC energy today HIGH (Epv3_today)'},
        68: {'name': 'pv3_energy_today_low', 'scale': 1, 'unit': '', 'pair': 67, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'PV3 DC energy today LOW'},
        69: {'name': 'pv3_energy_total_high', 'scale': 1, 'unit': '', 'pair': 70, 'desc': 'PV3 DC energy total HIGH (Epv3_total)'},
        70: {'name': 'pv3_energy_total_low', 'scale': 1, 'unit': '', 'pair': 69, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'PV3 DC energy total LOW'},

        # PV Total energy lifetime
        91: {'name': 'pv_energy_total_high', 'scale': 1, 'unit': '', 'pair': 92, 'desc': 'PV energy total lifetime HIGH'},
        92: {'name': 'pv_energy_total_low', 'scale': 1, 'unit': '', 'pair': 91, 'combined_scale': 0.1, 'combined_unit': 'kWh'},

        # Temperatures
        93: {'name': 'inverter_temp', 'scale': 0.1, 'unit': '°C', 'signed': True},
        94: {'name': 'ipm_temp', 'scale': 0.1, 'unit': '°C', 'signed': True},
        95: {'name': 'boost_temp', 'scale': 0.1, 'unit': '°C', 'signed': True},
        96: {'name': 'temp_sensor_1', 'scale': 0.1, 'unit': '°C', 'signed': True, 'desc': 'Additional temperature sensor 1 (possibly BMS/battery related)'},
        97: {'name': 'temp_sensor_2', 'scale': 0.1, 'unit': '°C', 'signed': True, 'desc': 'Additional temperature sensor 2 (appears to match Growatt server Boost Temp)'},

        # Status
        100: {'name': 'power_factor', 'scale': 1, 'unit': ''},
        104: {'name': 'derating_mode', 'scale': 1, 'unit': ''},
        105: {'name': 'fault_code', 'scale': 1, 'unit': ''},
        112: {'name': 'warning_code', 'scale': 1, 'unit': ''},

        # === BATTERY RANGE (3000+) - Battery & Power Flow ===
        # System Status
        3000: {'name': 'battery_status', 'scale': 1, 'unit': '', 'desc': 'Battery system status'},
        
        # Power Flow (32-bit pairs, signed for import/export)
        3041: {'name': 'power_to_user_high', 'scale': 1, 'unit': '', 'pair': 3042},
        3042: {'name': 'power_to_user_low', 'scale': 1, 'unit': '', 'pair': 3041, 'combined_scale': 0.1, 'combined_unit': 'W'},
        3043: {'name': 'power_to_grid_high', 'scale': 1, 'unit': '', 'pair': 3044},
        3044: {'name': 'power_to_grid_low', 'scale': 1, 'unit': '', 'pair': 3043, 'combined_scale': 0.1, 'combined_unit': 'W', 'signed': True},
        3045: {'name': 'power_to_load_high', 'scale': 1, 'unit': '', 'pair': 3046},
        3046: {'name': 'power_to_load_low', 'scale': 1, 'unit': '', 'pair': 3045, 'combined_scale': 0.1, 'combined_unit': 'W'},
        
        # Energy Breakdown
        3067: {'name': 'energy_to_user_today_high', 'scale': 1, 'unit': '', 'pair': 3068},
        3068: {'name': 'energy_to_user_today_low', 'scale': 1, 'unit': '', 'pair': 3067, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        3069: {'name': 'energy_to_user_total_high', 'scale': 1, 'unit': '', 'pair': 3070, 'desc': 'Grid import energy total (HIGH word)'},
        3070: {'name': 'energy_to_user_total_low', 'scale': 1, 'unit': '', 'pair': 3069, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'Grid import energy total (LOW word)'},
        3071: {'name': 'energy_to_grid_today_high', 'scale': 1, 'unit': '', 'pair': 3072},
        3072: {'name': 'energy_to_grid_today_low', 'scale': 1, 'unit': '', 'pair': 3071, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        3073: {'name': 'energy_to_grid_total_high', 'scale': 1, 'unit': '', 'pair': 3074},
        3074: {'name': 'energy_to_grid_total_low', 'scale': 1, 'unit': '', 'pair': 3073, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        3075: {'name': 'load_energy_today_high', 'scale': 1, 'unit': '', 'pair': 3076},
        3076: {'name': 'load_energy_today_low', 'scale': 1, 'unit': '', 'pair': 3075, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        3077: {'name': 'load_energy_total_high', 'scale': 1, 'unit': '', 'pair': 3078},
        3078: {'name': 'load_energy_total_low', 'scale': 1, 'unit': '', 'pair': 3077, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        
        # Battery Diagnostics
        3086: {'name': 'battery_derating_mode', 'scale': 1, 'unit': ''},
        3087: {'name': 'pv_iso', 'scale': 1, 'unit': 'kΩ', 'desc': 'PV insulation resistance'},
        3088: {'name': 'dci_r', 'scale': 0.1, 'unit': 'mA', 'desc': 'DC injection current (R-phase)'},
        3089: {'name': 'dci_s', 'scale': 0.1, 'unit': 'mA', 'desc': 'DC injection current (S-phase)'},
        3090: {'name': 'dci_t', 'scale': 0.1, 'unit': 'mA', 'desc': 'DC injection current (T-phase)'},
        3091: {'name': 'gfci', 'scale': 1, 'unit': 'mA', 'desc': 'Residual/leakage current (GFCI)'},

        # Battery - Discharge/Charge Energy (3000 range - PRIMARY for MOD XH)
        # Note: Order is discharge first, then charge (different from VPP which is charge first)
        3125: {'name': 'discharge_energy_today_high', 'scale': 1, 'unit': '', 'pair': 3126, 'desc': 'Battery discharge energy today (primary source for MOD XH)'},
        3126: {'name': 'discharge_energy_today_low', 'scale': 1, 'unit': '', 'pair': 3125, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        3127: {'name': 'discharge_energy_total_high', 'scale': 1, 'unit': '', 'pair': 3128, 'desc': 'Battery discharge energy total (primary source for MOD XH)'},
        3128: {'name': 'discharge_energy_total_low', 'scale': 1, 'unit': '', 'pair': 3127, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        3129: {'name': 'charge_energy_today_high', 'scale': 1, 'unit': '', 'pair': 3130, 'desc': 'Battery charge energy today (primary source for MOD XH)'},
        3130: {'name': 'charge_energy_today_low', 'scale': 1, 'unit': '', 'pair': 3129, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        3131: {'name': 'charge_energy_total_high', 'scale': 1, 'unit': '', 'pair': 3132, 'desc': 'Battery charge energy total (primary source for MOD XH)'},
        3132: {'name': 'charge_energy_total_low', 'scale': 1, 'unit': '', 'pair': 3131, 'combined_scale': 0.1, 'combined_unit': 'kWh'},

        # AC Charge Energy (grid→battery) - confirmed via hardware scan (MOD 10000TL3-XH, Feb 2026)
        # Register 3133/3134: AC charge today = 4.0 kWh at scan time
        # Register 3135/3136: AC charge total = 530.5 kWh at scan time (corrected from wrong battery_bms_temp mapping)
        3133: {'name': 'ac_charge_energy_today_high', 'scale': 1, 'unit': '', 'pair': 3134, 'desc': 'AC charge energy today HIGH (grid→battery)'},
        3134: {'name': 'ac_charge_energy_today_low', 'scale': 1, 'unit': '', 'pair': 3133, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'AC charge energy today (grid→battery)'},
        3135: {'name': 'ac_charge_energy_total_high', 'scale': 1, 'unit': '', 'pair': 3136, 'desc': 'AC charge energy total HIGH (grid→battery lifetime)'},
        3136: {'name': 'ac_charge_energy_total_low', 'scale': 1, 'unit': '', 'pair': 3135, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'AC charge energy total (grid→battery lifetime)'},

        # Battery State (3000 range - PRIMARY for MOD XH with ARK battery)
        # Note: VPP 31200+ range doesn't respond on MOD 10000TL3-XH, so 3000+ is primary
        3144: {'name': 'priority_mode', 'scale': 1, 'unit': '', 'desc': '0=Load, 1=Battery, 2=Grid'},
        3169: {'name': 'battery_voltage', 'scale': 0.01, 'unit': 'V', 'desc': 'Battery voltage (0.01V/unit; use VPP 31214 as primary — it overrides this via max-value selection)'},
        3170: {'name': 'battery_current', 'scale': 0.1, 'unit': 'A', 'signed': True, 'desc': 'Battery current (primary source for MOD XH)'},
        3171: {'name': 'battery_soc', 'scale': 1, 'unit': '%', 'desc': 'Battery SOC (primary source for MOD XH)'},
        # 3176 is NOT a battery temperature. It is Bdc1Temp1 — the bidirectional DC-DC
        # converter, i.e. the battery-side power stage inside the inverter (#362).
        #
        # Confirmed by reading ShineApp and Home Assistant in the same minute, at an
        # operating point where 3176 and reg 93 were 16 °C apart:
        #
        #     App 13:22                 HA 13:21
        #     Bdc1Temp1   51.9   <--    reg 3176   51.9
        #     Temp2       68.0   <--    reg 93     68.0
        #     BmsTemp1Bat  0.0
        #
        # That explains what looked like a bug: the reported ~52 °C on battery cabinets
        # that are cool to the touch, and the register sitting flat through an evening
        # while reg 93 shed six degrees — the DC-DC stage was idle while the AC side
        # was still cooling.
        #
        # Getting here took two wrong turns worth remembering. It was first reported as
        # a duplicate of reg 93 after both read raw 545 in one scan; a paired reading at
        # a different operating point refuted that. Through the morning ramp the two
        # track within ~1.5 °C and the sign of the difference flips, so a single daytime
        # sample cannot separate them. Two registers agreeing at one moment proves
        # nothing; two diverging at any moment proves they are independent.
        #
        # There is nothing to remap battery temperature TO. On the reporting system
        # (APX HV pack, MID 25KTL3-XH) BmsTemp1Bat reads 0.0 while BmsStatus=4,
        # BmsSoc=100 and BmsVbat=428.7 V — the BMS is communicating and simply does not
        # publish a cell temperature. So MOD/MID has no battery temperature over Modbus,
        # and inventing one from a nearby plausible register is exactly the trap this
        # comment exists to prevent. (Bdc1Temp2 = 39.4 °C also exists; its address is
        # unknown and deliberately not guessed.)
        3176: {'name': 'dcdc_temp', 'scale': 0.1, 'unit': '°C', 'signed': True,
               'desc': 'Bdc1Temp1 — bidirectional DC-DC converter temperature, NOT battery '
                       'temperature (confirmed against ShineApp, #362)'},

        # Battery Power (3000 range - separate charge/discharge registers)
        # These follow the MIN TL-XH pattern for ARK battery systems
        3178: {'name': 'discharge_power_high', 'scale': 1, 'unit': '', 'pair': 3179, 'desc': 'Battery discharge power HIGH (unsigned)'},
        3179: {'name': 'discharge_power_low', 'scale': 1, 'unit': '', 'pair': 3178, 'combined_scale': 0.1, 'combined_unit': 'W', 'desc': 'Battery discharge power (unsigned, positive=discharging)'},
        3180: {'name': 'charge_power_high', 'scale': 1, 'unit': '', 'pair': 3181, 'desc': 'Battery charge power HIGH (unsigned)'},
        3181: {'name': 'charge_power_low', 'scale': 1, 'unit': '', 'pair': 3180, 'combined_scale': 0.1, 'combined_unit': 'W', 'desc': 'Battery charge power (unsigned, positive=charging)'},

        # === BACKUP BOX (Growatt ARK transfer switch, RS485 at regs 3281-3342) ===
        # Confirmed active on MOD 10KTL3-XH-BP via ledermueller scan (Issue #336):
        # reg 3282=1 (On-Grid), 3286=33°C, 3287=2340 (234.0V), 3297/3298=10898 (1089.8W), 3320=1 (connected)
        # Same register layout as TL-XH profile.
        3281: {'name': 'box_bypass_status', 'scale': 1,   'unit': '',   'desc': '0=Off, 1=On'},
        3282: {'name': 'box_work_mode',     'scale': 1,   'unit': '',   'desc': '0=Offgrid, 1=Ongrid, 2=Generator'},
        3284: {'name': 'box_error_code',    'scale': 1,   'unit': '',   'desc': 'Error code (700-800 range)'},
        3285: {'name': 'box_warning_code',  'scale': 1,   'unit': '',   'desc': 'Warning code (700-800 range)'},
        3286: {'name': 'box_temperature',   'scale': 1,   'unit': '°C', 'signed': True, 'desc': 'NTC temperature, Int8, -40 to 100°C'},
        3287: {'name': 'box_grid_voltage',  'scale': 0.1, 'unit': 'V',  'desc': 'Grid voltage'},
        # box_grid_power has been observed constant at zero on a MOD 10KTL3-XH (DN1.0):
        # 4430 consecutive samples over two nights, never once non-zero, including samples
        # where the house meter showed real grid flow of up to 2064 W (#373).
        #
        # NOT removed on that evidence. The box's other sensors work on the same unit
        # (temperature, grid voltage, work mode, bypass status all report), so this is not
        # a dead block — and this register is the *box's* view of the grid, which may
        # legitimately read zero in whichever mode that unit sits in on-grid. What would
        # settle it is box_work_mode (3282) during a sample with known grid flow; nobody
        # has captured that pairing yet.
        #
        # USE power_to_user (3041/3042) FOR GRID IMPORT ON THIS MODEL, not this register.
        #
        # An earlier version of this note claimed a grid-bounded limit ("never command
        # anything that causes import") was not buildable from this inverter's own
        # registers. That was too strong, and the reporter said so rather than let it
        # stand: across 637 samples during EV charging, power_to_user was non-zero in
        # 632 of 632, with a median difference of -4 W against a P1 meter and 98% of
        # samples within 200 W. For sustained import it tracks the grid closely.
        #
        # The limitation is real but narrower than stated. power_to_user also read 0.0
        # through eight transient events, including a confirmed 2.2 kW load running for
        # ten seconds while the inverter's own discharge register moved by 2.2 kW to meet
        # it. So it is trustworthy for sustained flow and blind to transients on roughly
        # that timescale — which is the normal profile of a kettle, an espresso machine or
        # a boiler, so any design using it should expect to miss those.
        #
        # For a clamp that exists to stop a *command* causing continuous import, that gap
        # is acceptable and should be stated rather than discovered. PV power (1/2, 5/6,
        # 9/10) and battery power (3178-3181) are also validated on this model.
        3289: {'name': 'box_grid_power_high', 'scale': 1, 'unit': '', 'pair': 3290, 'signed': True, 'desc': 'Grid power HIGH (Int32, positive=import). Reads 0 on at least one DN1.0 unit — see note above'},
        3290: {'name': 'box_grid_power_low',  'scale': 1, 'unit': '', 'pair': 3289, 'combined_scale': 0.1, 'combined_unit': 'W', 'signed': True, 'desc': 'Grid power LOW'},
        3297: {'name': 'box_load_power_high', 'scale': 1, 'unit': '', 'pair': 3298, 'desc': 'Load power HIGH (Uint32)'},
        3298: {'name': 'box_load_power_low',  'scale': 1, 'unit': '', 'pair': 3297, 'combined_scale': 0.1, 'combined_unit': 'W', 'desc': 'Load power LOW'},
        3320: {'name': 'box_connect_flag',  'scale': 1,   'unit': '',   'desc': '0=Abnormal/absent, 1=Normal/connected'},
        3342: {'name': 'box_relay_status',  'scale': 1,   'unit': '',   'desc': '0=Not supported/comm error, 1=Open, 2=Close'},

        # === BATTERY INFORMATION 1 (31200-31299) - Official VPP Protocol V2.01 ===
        # This is the official battery data range for MOD series per Growatt VPP Protocol
        # Ref: GROWATT VPP COMMUNICATION PROTOCOL OF INVERTER V2.01 (2024.9.20)

        # Battery Power (VPP range - NOT responding on MOD 10000TL3-XH, kept for other MOD variants)
        # Renamed with _vpp suffix to avoid conflict with 3000+ range (primary source)
        # Signed: positive=charging, negative=discharging
        31200: {'name': 'battery_power_high', 'scale': 1, 'unit': '', 'pair': 31201, 'desc': 'Battery power HIGH (VPP range — confirmed responding on MOD XH)'},
        31201: {'name': 'battery_power_low', 'scale': 1, 'unit': '', 'pair': 31200, 'combined_scale': 0.1, 'combined_unit': 'W', 'signed': True, 'desc': 'Battery power signed (VPP range — confirmed responding on MOD XH, positive=charging)'},

        # Battery Energy (VPP range - NOT responding on MOD 10000TL3-XH, kept for other MOD variants)
        # Renamed with _vpp suffix to avoid conflict with 3000+ range (primary source)
        # Note: VPP protocol lists charge first, then discharge (opposite of 3000+ range)
        31202: {'name': 'charge_energy_today_vpp_high', 'scale': 1, 'unit': '', 'pair': 31203},
        31203: {'name': 'charge_energy_today_vpp_low', 'scale': 1, 'unit': '', 'pair': 31202, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        31204: {'name': 'charge_energy_total_vpp_high', 'scale': 1, 'unit': '', 'pair': 31205},
        31205: {'name': 'charge_energy_total_vpp_low', 'scale': 1, 'unit': '', 'pair': 31204, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        31206: {'name': 'discharge_energy_today_vpp_high', 'scale': 1, 'unit': '', 'pair': 31207},
        31207: {'name': 'discharge_energy_today_vpp_low', 'scale': 1, 'unit': '', 'pair': 31206, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        31208: {'name': 'discharge_energy_total_vpp_high', 'scale': 1, 'unit': '', 'pair': 31209},
        31209: {'name': 'discharge_energy_total_vpp_low', 'scale': 1, 'unit': '', 'pair': 31208, 'combined_scale': 0.1, 'combined_unit': 'kWh'},

        # Battery Power Limits
        31210: {'name': 'battery_max_charge_power_high', 'scale': 1, 'unit': '', 'pair': 31211},
        31211: {'name': 'battery_max_charge_power_low', 'scale': 1, 'unit': '', 'pair': 31210, 'combined_scale': 0.1, 'combined_unit': 'W'},
        31212: {'name': 'battery_max_discharge_power_high', 'scale': 1, 'unit': '', 'pair': 31213},
        31213: {'name': 'battery_max_discharge_power_low', 'scale': 1, 'unit': '', 'pair': 31212, 'combined_scale': 0.1, 'combined_unit': 'W'},

        # Battery State (VPP range - NOT responding on MOD 10000TL3-XH, kept for other MOD variants)
        # Renamed with _vpp suffix to avoid conflict with 3000+ range (primary source)
        31214: {'name': 'battery_voltage_vpp', 'scale': 0.1, 'unit': 'V', 'signed': True, 'maps_to': 'battery_voltage', 'desc': 'Battery voltage VPP (0.1V/unit; maps_to battery_voltage so it wins over 3169 in max-value selection)'},
        31215: {'name': 'battery_current_vpp_high', 'scale': 1, 'unit': '', 'pair': 31216},
        31216: {'name': 'battery_current_vpp_low', 'scale': 1, 'unit': '', 'pair': 31215, 'combined_scale': 0.1, 'combined_unit': 'A', 'signed': True},
        31217: {'name': 'battery_soc_vpp', 'scale': 1, 'unit': '%', 'desc': 'Battery SOC (VPP range, may not respond on XH variants)'},
        31218: {'name': 'battery_soh', 'scale': 1, 'unit': '%'},

        # Battery Capacity
        31219: {'name': 'battery_fcc_high', 'scale': 1, 'unit': '', 'pair': 31220},
        31220: {'name': 'battery_fcc_low', 'scale': 1, 'unit': '', 'pair': 31219, 'combined_scale': 1, 'combined_unit': 'Ah'},

        # Battery Temperature (VPP range)
        31223: {'name': 'battery_temp_vpp', 'scale': 0.1, 'unit': '°C', 'signed': True, 'desc': 'Battery temp (VPP range, may not respond on XH variants)'},

        # Battery System Info
        31225: {'name': 'battery_cluster_sum', 'scale': 1, 'unit': ''},
        31226: {'name': 'battery_module_number', 'scale': 1, 'unit': ''},
        31227: {'name': 'battery_module_rated_voltage', 'scale': 0.1, 'unit': 'V'},
        31228: {'name': 'battery_module_rated_capacity', 'scale': 0.1, 'unit': 'Ah'},

        # === BATTERY CLUSTER 2 (31300-31399) - VPP Protocol V2.01 ===
        # Battery 2 Power (signed: positive=charging, negative=discharging)
        31300: {'name': 'battery2_power_high', 'scale': 1, 'unit': '', 'pair': 31301},
        31301: {'name': 'battery2_power', 'scale': 1, 'unit': '', 'pair': 31300, 'combined_scale': 0.1, 'combined_unit': 'W', 'signed': True},

        # Battery 2 Energy
        31302: {'name': 'battery2_charge_energy_today_high', 'scale': 1, 'unit': '', 'pair': 31303},
        31303: {'name': 'battery2_charge_energy_today_low', 'scale': 1, 'unit': '', 'pair': 31302, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        31304: {'name': 'battery2_charge_energy_total_high', 'scale': 1, 'unit': '', 'pair': 31305},
        31305: {'name': 'battery2_charge_energy_total_low', 'scale': 1, 'unit': '', 'pair': 31304, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        31306: {'name': 'battery2_discharge_energy_today_high', 'scale': 1, 'unit': '', 'pair': 31307},
        31307: {'name': 'battery2_discharge_energy_today_low', 'scale': 1, 'unit': '', 'pair': 31306, 'combined_scale': 0.1, 'combined_unit': 'kWh'},
        31308: {'name': 'battery2_discharge_energy_total_high', 'scale': 1, 'unit': '', 'pair': 31309},
        31309: {'name': 'battery2_discharge_energy_total_low', 'scale': 1, 'unit': '', 'pair': 31308, 'combined_scale': 0.1, 'combined_unit': 'kWh'},

        # Battery 2 State
        31314: {'name': 'battery2_voltage', 'scale': 0.1, 'unit': 'V', 'signed': True,
                'desc': 'Battery 2 voltage (0 = not connected)'},
        31315: {'name': 'battery2_current_high', 'scale': 1, 'unit': '', 'pair': 31316},
        31316: {'name': 'battery2_current_low', 'scale': 1, 'unit': '', 'pair': 31315, 'combined_scale': 0.1, 'combined_unit': 'A', 'signed': True},
        31317: {'name': 'battery2_soc', 'scale': 1, 'unit': '%'},
        31318: {'name': 'battery2_soh', 'scale': 1, 'unit': '%'},
        31323: {'name': 'battery2_temp', 'scale': 0.1, 'unit': '°C', 'signed': True},

        # Battery clusters 3 and 4 (VPP V2.03 spec, gate: batteryN_voltage > 0)
        **VPP_V201_BATTERY3,
        **VPP_V201_BATTERY4,

        # === V2.01 VPP ADDITIONAL REGISTERS (31100+ range) ===
        # Per VPP 2.01 protocol spec (same layout as MID — confirmed on MID via #245 scan):

        # Active power (INT32 signed, 0.1W) — spec item 45
        # Positive = export to grid, Negative = import from grid.
        # Register 3043/3044 (power_to_grid_high/low) returns 0 on some firmware when the VPP
        # range is active; 31100/31101 carries the authoritative signed active power value.
        # maps_to power_to_grid_low so coordinator sees grid export (positive=export).
        31100: {'name': 'ac_active_power_high', 'scale': 1, 'unit': '', 'pair': 31101,
                'desc': 'Active power HIGH (INT32 signed, positive=export)'},
        31101: {'name': 'ac_active_power_low', 'scale': 1, 'unit': '', 'pair': 31100,
                'combined_scale': 0.1, 'combined_unit': 'W', 'signed': True,
                'maps_to': 'power_to_grid_low',
                'desc': 'Active power LOW — maps_to power_to_grid (positive=export per VPP 2.01 item 45)'},

        # Meter power (INT32 signed, 0.1W) — spec item 55
        # NOTE: sign convention OPPOSITE to active power — positive = IMPORT from grid.
        # maps_to power_to_user_low so coordinator sees grid import directly.
        31112: {'name': 'meter_power_high', 'scale': 1, 'unit': '', 'pair': 31113,
                'desc': 'Meter power HIGH (INT32, positive=import)'},
        31113: {'name': 'meter_power_low', 'scale': 1, 'unit': '', 'pair': 31112,
                'combined_scale': 0.1, 'combined_unit': 'W', 'signed': True,
                'maps_to': 'power_to_user_low',
                'desc': 'Meter power LOW — maps_to power_to_user (positive=import per VPP 2.01 item 55)'},

        # === VPP 2.01 GRID ENERGY COUNTERS (31118-31125) — spec items 60-63 ===
        # Per VPP 2.01 spec (same layout as MID — confirmed #245).
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

        # Status
        31000: {'name': 'equipment_status', 'scale': 1, 'unit': '', 'desc': 'Equipment running status'},
        31001: {'name': 'battery_working_status', 'scale': 1, 'unit': '', 'desc': '0=Idle, 1=Charge, 2=Discharge, 3=Fault, 4=Standby, 5=Shutdown'},
    },
    'holding_registers': {
        # Basic control
        0: {'name': 'on_off', 'scale': 1, 'unit': '', 'access': 'RW', 'desc': '0=Off, 1=On'},
        3: {'name': 'active_power_rate', 'scale': 1, 'unit': '%', 'access': 'RW', 'desc': 'Max output power %'},
        30: {'name': 'modbus_address', 'scale': 1, 'unit': '', 'access': 'RW', 'desc': 'Modbus address 1-254'},

        # THE WHOLE HOLDING BLOCK 1000-1124 IS UNIMPLEMENTED ON THIS FAMILY.
        #
        # Nothing from that range is mapped here, and nothing should be added. Four
        # registers were mapped at various points and all four are gone:
        #
        #   1071  discharge_stopped_soc   removed — writes accepted, silently ignored
        #   1090  charge_power_rate       removed — writes REJECTED, exception 2
        #   1091  charge_stopped_soc      removed — writes accepted, silently ignored
        #   1092  ac_charge_enable        removed — writes REJECTED, exception 2
        #
        # Evidence, across three firmware lines:
        #
        #   #343  @Rohde2026 and @TimOsth, MOD DO1.0 — read back zeros; 3048/3067 work
        #   #362  @as-wallpen, MID 25KTL3-XH DN1.0 — 0 on every poll despite months of
        #         writes, while 3067 was proven by direct before/after measurement
        #   #371  @KevlarD-67, MOD 10KTL3-XH DN1.0 — a full holding sweep read 0 of 125
        #         registers non-zero across 1000-1124, and A/B writes 19 seconds apart on
        #         one connection gave: FC6 1092 -> exception 2, FC6 3049 -> echoed and
        #         read back. Same for 1090 against 3047.
        #
        # Note the two failure modes differ, which matters for how each is detected. A
        # silently ignored write only shows up on read-back — which is why 1071/1091
        # survived a scan reporting "all Read OK", a register answering 0 being Read OK.
        # An exception 2 surfaces immediately as a Modbus error, so 1090/1092 were never
        # ambiguous once anyone wrote to them; they were simply never written to in a
        # test. Neither has ever had evidence *for* it.
        #
        # 1090/1092 were the worse pair to leave in place: they created a second grid
        # charge switch and a second charge-rate control alongside the working ones, with
        # no error surfaced when a user reached for the wrong one.
        #
        # Use instead, all confirmed working on this hardware:
        #   3047  batt_first_charge_power_rate      (replaces 1090)
        #   3048  batt_first_charge_stopped_soc     (replaces 1091)
        #   3049  allow_grid_charge                 (replaces 1092)
        #   3067  grid_first_discharge_stopped_soc  (replaces 1071)

        # Device identification
        30000: {'name': 'dtc_code', 'scale': 1, 'unit': '', 'access': 'RO', 'desc': 'Device Type Code: 5400 for MOD-XH/MID-XH', 'default': 5400},
        30099: {'name': 'protocol_version', 'scale': 1, 'unit': '', 'access': 'RO', 'desc': 'VPP Protocol version (201 = V2.01)', 'default': 201},

        # Export Control Registers
        122: {
            'name': 'export_limit_mode',
            'scale': 1,
            'unit': '',
            'access': 'RW',
            'desc': 'Export limit control mode',
            'valid_range': (0, 3),
            'values': {
                0: 'Export limit disabled',
                1: 'Enable 485 (external meter) limitation',
                2: 'Enable 232 (external meter) limitation',
                3: 'CT export limit'
            }
        },
        123: {
            'name': 'export_limit_power',
            'scale': 0.1,
            'unit': '%',
            'access': 'RW',
            'desc': 'Export limit power percentage',
            'valid_range': (0, 1000),
            'note': '0=0%, 1000=100.0%'
        },

        # Power rate limits for Grid First and Battery First modes
        # Scan #228 confirmed: 3036=100 (Read OK, GridFirstDischargePowerRate), 3047=80 (Read OK, BatFirstPowerRate)
        3036: {'name': 'grid_first_discharge_power_rate', 'scale': 1, 'unit': '%', 'access': 'RW',
               'valid_range': (1, 100), 'desc': 'Discharge power rate when Grid First mode (1-100%)'},

        # TOU (Time-of-Use) schedule (FC04 holding, registers 3038-3045)
        # Start registers: bit15=enable, bit13-14=priority(0=Load,1=Battery,2=Grid), bit8-12=hour, bit0-7=minute
        # End registers: bit8-12=hour, bit0-7=minute (same hex-packed as SPH time periods)
        3038: {'name': 'mod_tou_1_start', 'scale': 1, 'unit': '', 'access': 'RW',
               'desc': 'TOU Period 1 start: bit15=enable, bit13-14=priority(0=Load,1=Batt,2=Grid), bit8-12=hour, bit0-7=min'},
        3039: {'name': 'mod_tou_1_end',   'scale': 1, 'unit': '', 'access': 'RW',
               'desc': 'TOU Period 1 end: bit8-12=hour, bit0-7=min'},
        3040: {'name': 'mod_tou_2_start', 'scale': 1, 'unit': '', 'access': 'RW',
               'desc': 'TOU Period 2 start: bit15=enable, bit13-14=priority, bit8-12=hour, bit0-7=min'},
        3041: {'name': 'mod_tou_2_end',   'scale': 1, 'unit': '', 'access': 'RW',
               'desc': 'TOU Period 2 end: bit8-12=hour, bit0-7=min'},
        3042: {'name': 'mod_tou_3_start', 'scale': 1, 'unit': '', 'access': 'RW',
               'desc': 'TOU Period 3 start: bit15=enable, bit13-14=priority, bit8-12=hour, bit0-7=min'},
        3043: {'name': 'mod_tou_3_end',   'scale': 1, 'unit': '', 'access': 'RW',
               'desc': 'TOU Period 3 end: bit8-12=hour, bit0-7=min'},
        3044: {'name': 'mod_tou_4_start', 'scale': 1, 'unit': '', 'access': 'RW',
               'desc': 'TOU Period 4 start: bit15=enable, bit13-14=priority, bit8-12=hour, bit0-7=min'},
        3045: {'name': 'mod_tou_4_end',   'scale': 1, 'unit': '', 'access': 'RW',
               'desc': 'TOU Period 4 end: bit8-12=hour, bit0-7=min'},

        # EMS / grid-charge controls (3046-3049) — NOT TOU slots
        3047: {'name': 'batt_first_charge_power_rate', 'scale': 1, 'unit': '%', 'access': 'RW',
               'valid_range': (1, 100), 'desc': 'Charge power rate when Battery First mode (1-100%)'},
        3048: {'name': 'batt_first_charge_stopped_soc', 'scale': 1, 'unit': '%', 'access': 'RW',
               'valid_range': (0, 100), 'desc': 'SOC to stop charging - Battery First mode (DO1.0+ firmware; replaces reg 1091 which is dead on this firmware)'},
        3049: {'name': 'allow_grid_charge', 'scale': 1, 'unit': '', 'access': 'RW',
               'desc': 'Allow Grid Charge — must be Enabled (1) for TOU writes to persist (GEN4)'},

        # TOU slots 5-9 (3050-3059; gap at 3046-3049 is intentional — EMS/grid-charge regs)
        3050: {'name': 'mod_tou_5_start', 'scale': 1, 'unit': '', 'access': 'RW',
               'desc': 'TOU Period 5 start: bit15=enable, bit13-14=priority, bit8-12=hour, bit0-7=min'},
        3051: {'name': 'mod_tou_5_end',   'scale': 1, 'unit': '', 'access': 'RW',
               'desc': 'TOU Period 5 end: bit8-12=hour, bit0-7=min'},
        3052: {'name': 'mod_tou_6_start', 'scale': 1, 'unit': '', 'access': 'RW',
               'desc': 'TOU Period 6 start: bit15=enable, bit13-14=priority, bit8-12=hour, bit0-7=min'},
        3053: {'name': 'mod_tou_6_end',   'scale': 1, 'unit': '', 'access': 'RW',
               'desc': 'TOU Period 6 end: bit8-12=hour, bit0-7=min'},
        3054: {'name': 'mod_tou_7_start', 'scale': 1, 'unit': '', 'access': 'RW',
               'desc': 'TOU Period 7 start: bit15=enable, bit13-14=priority, bit8-12=hour, bit0-7=min'},
        3055: {'name': 'mod_tou_7_end',   'scale': 1, 'unit': '', 'access': 'RW',
               'desc': 'TOU Period 7 end: bit8-12=hour, bit0-7=min'},
        3056: {'name': 'mod_tou_8_start', 'scale': 1, 'unit': '', 'access': 'RW',
               'desc': 'TOU Period 8 start: bit15=enable, bit13-14=priority, bit8-12=hour, bit0-7=min'},
        3057: {'name': 'mod_tou_8_end',   'scale': 1, 'unit': '', 'access': 'RW',
               'desc': 'TOU Period 8 end: bit8-12=hour, bit0-7=min'},
        3058: {'name': 'mod_tou_9_start', 'scale': 1, 'unit': '', 'access': 'RW',
               'desc': 'TOU Period 9 start: bit15=enable, bit13-14=priority, bit8-12=hour, bit0-7=min'},
        3059: {'name': 'mod_tou_9_end',   'scale': 1, 'unit': '', 'access': 'RW',
               'desc': 'TOU Period 9 end: bit8-12=hour, bit0-7=min'},

        # Discharge SOC floor. Replaces the dead register 1071 (see the note above).
        #
        # Named "grid_first" after the Growatt documentation, but that understates it.
        # @as-wallpen demonstrated on DN1.0 (#362) that it governs on-grid discharge in
        # self-consumption operation too, with every TOU period disabled and all
        # priorities set to Load Priority: raising it above the current SOC made the
        # inverter actively *charge* to reach it, and lowering it resumed discharge,
        # ~2 minutes each way. So it is the discharge floor generally, not a
        # mode-specific setting — which also means there is no separate on-grid
        # register still to be found.
        3067: {'name': 'grid_first_discharge_stopped_soc', 'scale': 1, 'unit': '%', 'access': 'RW',
               'valid_range': (1, 100),
               'desc': 'SOC to stop discharging. Applies in Load/self-consumption operation as '
                       'well as Grid First (#362); firmware may enforce a higher floor than 1'},

        # ====================================================================
        # Peak shaving / demand management (3307-3312)
        # ====================================================================
        #
        # NOT IN ANY PUBLIC PROTOCOL DOCUMENT. docs/developer/protocol-v139.md carries no
        # holding-register semantics above 3282 — the table jumps from there to 5400 —
        # and Modbus RTU Protocol II V1.24 declares the TL-XH ranges up to 3374 but its
        # tables stop around 3280. Consistent with Growatt's own statement that peak
        # shaving on the MOD 3-10KTL3-XH needs a firmware upgrade obtained from them.
        #
        # Every mapping below was established by @KevlarD-67 (#372) on a MOD 10KTL3-XH
        # (DN1.0) by changing the value in the Growatt web portal and reading the register
        # back over Modbus, with peak shaving disabled throughout so the changes were
        # inert, and all values restored afterwards. Correlation on value alone would not
        # have been enough — 100 occurs in 6 cloud settings and 17 registers — so only the
        # observed diffs are treated as confirmed.
        #
        # 3309, 3313 and 3314 are deliberately NOT mapped. 3314 in particular reads 10,
        # which coincides with two other discharge-stop SOCs, and is settable nowhere, so
        # it could not be confirmed in either direction.
        # Direction established by changing ONE portal field (#372).
        #
        # The first measurement moved a limit and saw both 3307 and 3308 go 75->70 together,
        # which pins the cluster to uw_demand_mgt_* but says nothing about which is which -
        # both registers carried the same evidence line and neither was distinguishable.
        # Two values moving together cannot separate them; only a divergence can.
        #
        # Settled by changing Import Limit alone, 7.5 -> 7.0 kW, with Export Limit untouched:
        # 3307 followed 51 seconds later, 3308 did not move at all. That also established
        # something not previously known - the portal writes these two fields independently,
        # rather than driving both from one control.
        #
        # Read-only routes were tried first and cannot settle it: the cloud API reports 7.5
        # for both uw_demand_mgt_downstrm_power_limit and uw_demand_mgt_revse_power_limit,
        # and seven days of recorder history had the two sensors never once diverging.
        3307: {'name': 'demand_import_limit', 'scale': 0.1, 'unit': 'kW', 'access': 'RO',
               'desc': 'Import limit (uw_demand_mgt_downstrm_power_limit). Confirmed by an '
                       'isolated portal change 7.5->7.0 kW that moved this register and not '
                       '3308 (#372); not in any public protocol document'},
        3308: {'name': 'demand_export_limit', 'scale': 0.1, 'unit': 'kW', 'access': 'RO',
               'desc': 'Export limit (uw_demand_mgt_revse_power_limit). Confirmed by exclusion '
                       'in the same test: unchanged while 3307 followed an isolated Import '
                       'Limit change (#372); not in any public protocol document'},
        3310: {'name': 'peak_shaving_reserve_soc', 'scale': 1, 'unit': '%', 'access': 'RO',
               'desc': 'Reserved SOC for peak shaving (ub_peak_shaving_backup_soc). Portal '
                       '50->45 read back 50->45 (#372); not in any public protocol document'},
        3311: {'name': 'ac_charge_max_power', 'scale': 0.1, 'unit': 'kW', 'access': 'RO',
               'desc': 'AC charging max power limit (uw_ac_charging_max_power_limit). Identified '
                       'by elimination, write verified (#372); not in any public protocol document'},

        # A configured cluster does not mean peak shaving is running. On the unit these
        # mappings came from, Peak Shaving Enable reads Disable while all five registers
        # hold plausible configured values (75/75/50/75/100) - so these sensors report what
        # the feature *would* use, not what it is currently doing (#372).
        #
        # Note that is the inverse of #380, where an unconfigured system left the three kW
        # limits at a ceiling and they had to be suppressed. Configured-looking values and
        # an active feature are independent facts here.

        # Grid-charge stop SOC — the one writable register in this cluster.
        #
        # Distinct from 3048 (batt_first_charge_stopped_soc, the general charge stop): this
        # one caps charging *from the grid* specifically. On the reporter's system it sat at
        # 55 while the general stop was 100 and silently capped grid charging for two days,
        # costing a full charge cycle before the cause was found.
        #
        # Writable here because Modbus is the only way to reach it. It is not exposed in the
        # ShinePhone app, the portal settings page, "Advanced Setting", or among the 39 types
        # returned by tlx_enabled_settings. Confirmed in reverse (#372): FC6 3312=85 was
        # echoed and read back, the Growatt cloud reported 85 about 12 minutes later, and it
        # was then restored to 100 and verified.
        3312: {'name': 'grid_charge_stopped_soc', 'scale': 1, 'unit': '%', 'access': 'RW',
               'valid_range': (0, 100),
               'desc': 'SOC to stop charging from the grid (ub_ac_charging_stop_soc). Separate '
                       'from 3048, which is the general charge stop. Confirmed by write plus '
                       'cloud read-back (#372); not in any public protocol document'},

        # ====================================================================
        # VPP remote power control (30100, 30407-30410, 30474) — READ ONLY
        # ====================================================================
        #
        # Mapped read-only on purpose. @KevlarD-67 demonstrated on hardware (#373) that
        # this family does support remote power control — the WIT-only gate in select.py
        # excludes it — but also that commanding it is not safe to expose yet:
        #
        #   1. THE POWER COMMAND IS A TARGET, NOT A LIMIT, AND IT OVERRIDES 3049.
        #      At 30409=100 with insufficient PV the inverter climbed toward the commanded
        #      power and drew from the grid while allow_grid_charge was 0. At 5/10/20%
        #      only downward limiting is visible, which makes it look like a cap.
        #      The 912 W often quoted for this is one sample five seconds in, from a run
        #      an abort threshold stopped while charge power was still climbing
        #      (2592 -> 4767 W in those five seconds) — a lower bound, not a typical value.
        #   2. The duration is not reliable in either direction. At 30408=2 the constraint
        #      released at ~128 s; at 30408=5 it had NOT released at 390 s and only did so
        #      when 30407/30100 were written back to 0 by hand. In both runs 30407, 30409
        #      and 30100 stayed set throughout. So active state cannot be inferred from
        #      these values, and an implementation must clear them itself rather than
        #      treating the timer as a safety net.
        #   3. 30407 alone does nothing — 30100 (control authority) must also be set. That
        #      is presumably why the capability was assumed absent on this family.
        #
        # The charge transfer function fits a line over three points (77.6 W per percentage
        # point) and then does not: a repeat of the 20% point produced 0 W rather than
        # ~1466 W, with lower PV surplus and higher SoC. Which variable matters is untested.
        # A clamp that assumes commanded power is delivered will meet that case.
        #
        # Exposing the values makes the state visible and lets anyone verify the capability
        # on their own hardware. Writable controls need a guard against commanding more than
        # PV can supply, and that design is still open on #373.
        #
        # No new read code is needed: growatt_modbus.py already probes anchors 30100 and
        # 30407 behind `if <addr> in holding_map`, so adding them here activates the
        # existing path, including the 300 s failure retry from #370.
        30100: {'name': 'control_authority', 'scale': 1, 'unit': '', 'access': 'RO',
                'desc': 'VPP master enable. Read-only here — remote power control does nothing '
                        'without it, and commanding power is not yet guarded (#373)'},
        30407: {'name': 'remote_power_control_enable', 'scale': 1, 'unit': '', 'access': 'RO',
                'desc': 'Remote power control enable. Does nothing unless 30100 is also set (#373)'},
        30408: {'name': 'remote_power_control_charging_time', 'scale': 1, 'unit': 'min', 'access': 'RO',
                'desc': 'Remote control duration. Expires without clearing 30407/30409/30100 (#373)'},
        30409: {'name': 'remote_charge_and_discharge_power', 'scale': 1, 'unit': '%', 'access': 'RO',
                'signed': True,
                'desc': 'Commanded power, -100 to +100%. A TARGET, not a limit: it will import from '
                        'the grid to reach it even with allow_grid_charge off (#373)'},
        30410: {'name': 'vpp_ac_charge_enable', 'scale': 1, 'unit': '', 'access': 'RO',
                'desc': 'VPP AC charge enable'},

        # Mirrors the last commanded setpoint. Retains it after remote control is disabled —
        # confirmed ten hours on, still reading -33 (raw 65503) with 30100/30407/30409 all
        # zero, which also confirms the two's complement decode. A direct write is accepted
        # and ignored: the echo returns the written value, the read-back keeps the old one.
        # That combination is what makes it right as a sensor and wrong as a control.
        #
        # An earlier report that it returns to 100 on its own has not reproduced and is not
        # relied on here (#373).
        30474: {'name': 'vpp_last_setpoint', 'scale': 1, 'unit': '%', 'access': 'RO',
                'signed': True,
                'desc': 'Mirror of the last commanded VPP power setpoint. Write-ignored (#373)'},

        # Safety/compliance diagnostic registers (read-only, Issue #282)
        235: {'name': 'ntognd_detect',     'scale': 1, 'unit': '', 'access': 'R', 'desc': '0=Disable, 1=Enable — NToGND detection'},
        236: {'name': 'nonstd_vac_enable', 'scale': 1, 'unit': '', 'access': 'R', 'desc': '0=Disable, 1=Grade1, 2=Grade2 — non-standard VAC'},
        237: {'name': 'enable_spec_set',   'scale': 1, 'unit': '', 'access': 'R', 'desc': 'Regional spec bitmask (Bit0=Hungary)'},
        238: {'name': 'fast_mppt_enable',  'scale': 1, 'unit': '', 'access': 'R', 'desc': '0-2 — fast MPPT (Reserved)'},
    }
}

# MOD-6000-15000TL3-X (Three-phase grid-tied WITHOUT battery)
MOD_6000_15000TL3_X = {
    'name': 'MOD TL3-X Series (Grid-Tied)',
    'description': 'Modular three-phase grid-tied inverter without battery (6-15kW)',
    'notes': 'Uses 0-124 base range only. Grid-tied version without battery storage.',
    'input_registers': {
        # === BASE RANGE (0-124) - Inverter Data ===
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

        # Output Power Total (32-bit) — true three-phase inverter output total.
        # Aliased to ac_power so the generic ac_power sensor reflects the correct total.
        # Do NOT alias ac_power_r (reg 40/41) — that is Phase R only, not total.
        35: {'name': 'output_power_high', 'scale': 1, 'unit': '', 'pair': 36, 'alias': 'ac_power_high'},
        36: {'name': 'output_power_low', 'scale': 1, 'unit': '', 'pair': 35, 'combined_scale': 0.1, 'combined_unit': 'W', 'alias': 'ac_power_low'},

        # === AC OUTPUT - THREE PHASE ===
        # Grid Frequency (shared across all phases)
        37: {'name': 'ac_frequency', 'scale': 0.01, 'unit': 'Hz', 'desc': 'AC output frequency'},

        # Phase R (L1) — ac_voltage/ac_current aliased for generic code; ac_power NOT aliased here
        # (ac_power comes from output_power reg 35/36 which holds the true three-phase total)
        38: {'name': 'ac_voltage_r', 'scale': 0.1, 'unit': 'V', 'desc': 'Phase R AC voltage', 'alias': 'ac_voltage'},
        39: {'name': 'ac_current_r', 'scale': 0.1, 'unit': 'A', 'desc': 'Phase R AC current', 'alias': 'ac_current'},
        40: {'name': 'ac_power_r_high', 'scale': 1, 'unit': '', 'pair': 41},
        41: {'name': 'ac_power_r_low', 'scale': 1, 'unit': '', 'pair': 40, 'combined_scale': 0.1, 'combined_unit': 'VA'},

        # Phase S (L2) - AC Output
        42: {'name': 'ac_voltage_s', 'scale': 0.1, 'unit': 'V', 'desc': 'Phase S AC voltage'},
        43: {'name': 'ac_current_s', 'scale': 0.1, 'unit': 'A', 'desc': 'Phase S AC current'},
        44: {'name': 'ac_power_s_high', 'scale': 1, 'unit': '', 'pair': 45},
        45: {'name': 'ac_power_s_low', 'scale': 1, 'unit': '', 'pair': 44, 'combined_scale': 0.1, 'combined_unit': 'VA'},

        # Phase T (L3) - AC Output
        46: {'name': 'ac_voltage_t', 'scale': 0.1, 'unit': 'V', 'desc': 'Phase T AC voltage'},
        47: {'name': 'ac_current_t', 'scale': 0.1, 'unit': 'A', 'desc': 'Phase T AC current'},
        48: {'name': 'ac_power_t_high', 'scale': 1, 'unit': '', 'pair': 49},
        49: {'name': 'ac_power_t_low', 'scale': 1, 'unit': '', 'pair': 48, 'combined_scale': 0.1, 'combined_unit': 'VA'},

        # Line-to-Line Voltages (three-phase only)
        50: {'name': 'line_voltage_rs', 'scale': 0.1, 'unit': 'V', 'desc': 'Line voltage R-S'},
        51: {'name': 'line_voltage_st', 'scale': 0.1, 'unit': 'V', 'desc': 'Line voltage S-T'},
        52: {'name': 'line_voltage_tr', 'scale': 0.1, 'unit': 'V', 'desc': 'Line voltage T-R'},

        # Energy Today (32-bit)
        53: {'name': 'energy_today_high', 'scale': 1, 'unit': '', 'pair': 54},
        54: {'name': 'energy_today_low', 'scale': 1, 'unit': '', 'pair': 53, 'combined_scale': 0.1, 'combined_unit': 'kWh'},

        # Energy Total (32-bit)
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
    },
    'holding_registers': {
        # Basic control
        0: {'name': 'on_off', 'scale': 1, 'unit': '', 'access': 'RW', 'desc': '0=Off, 1=On'},
        3: {'name': 'active_power_rate', 'scale': 1, 'unit': '%', 'access': 'RW', 'desc': 'Max output power %'},
        30: {'name': 'modbus_address', 'scale': 1, 'unit': '', 'access': 'RW', 'desc': 'Modbus address 1-254'},

        # Export Control Registers
        122: {
            'name': 'export_limit_mode',
            'scale': 1,
            'unit': '',
            'access': 'RW',
            'desc': 'Export limit control mode',
            'valid_range': (0, 3),
            'values': {
                0: 'Export limit disabled',
                1: 'Enable 485 (external meter) limitation',
                2: 'Enable 232 (external meter) limitation',
                3: 'CT export limit'
            }
        },
        123: {
            'name': 'export_limit_power',
            'scale': 0.1,
            'unit': '%',
            'access': 'RW',
            'desc': 'Export limit power percentage',
            'valid_range': (0, 1000),
            'note': '0=0%, 1000=100.0%'
        },

        # Safety/compliance diagnostic registers (read-only, Issue #282)
        235: {'name': 'ntognd_detect',     'scale': 1, 'unit': '', 'access': 'R', 'desc': '0=Disable, 1=Enable — NToGND detection'},
        236: {'name': 'nonstd_vac_enable', 'scale': 1, 'unit': '', 'access': 'R', 'desc': '0=Disable, 1=Grade1, 2=Grade2 — non-standard VAC'},
        237: {'name': 'enable_spec_set',   'scale': 1, 'unit': '', 'access': 'R', 'desc': 'Regional spec bitmask (Bit0=Hungary)'},
        238: {'name': 'fast_mppt_enable',  'scale': 1, 'unit': '', 'access': 'R', 'desc': '0-2 — fast MPPT (Reserved)'},
    }
}

# Export all MOD profiles
MOD_REGISTER_MAPS = {
    'MOD_6000_15000TL3_X': MOD_6000_15000TL3_X,
    'MOD_6000_15000TL3_XH': MOD_6000_15000TL3_XH,
}