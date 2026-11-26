# SPA Series - AC-Coupled Battery Storage (No PV MPPT Inputs)
# Based on SPA 3000TL BL + Ark 2.5L-A1 register scans (issue #249)
# Scan date: 2026-04 (day + night scans cross-verified)

from .sph_tl3 import SPH_TL3_3000_10000

SPA_3000_6000_TL_BL = {
    'name': 'SPA (AC Storage) 3-6kW',
    'description': 'AC-coupled battery storage inverter — no PV MPPT inputs (SPA 3000TL BL and similar)',
    'notes': (
        'Uses the 1000-1124 range, plus 2000-2124 (confirmed on a SPA3000TL-BL, #510). '
        'No solar DC inputs. '
        'Base range (0-124) and 3000+ range respond with zeros — not exceptions. '
        'Holding registers identical to SPH-TL3. '
        'Register layout differs from SPH-TL3 at shared addresses: '
        'reg 1021/1022 = grid import power on SPA (SPH-TL3 calls this power_to_load); '
        'reg 1037/1038 = load power (SPH-TL3 load power is at 1021/1022). '
        'AC voltage/frequency at 2038/2037, falling back to 1105/1113 only when the 2000 '
        'range is unread and the value is plausible. Battery current at reg 1088 (×0.01 A, signed).'
    ),
    'input_registers': {
        # ============================================================================
        # STORAGE RANGE 1000-1124 (the ONLY range with real data on SPA)
        # ============================================================================

        # System Work Mode
        1000: {'name': 'system_work_mode', 'scale': 1, 'unit': '', 'desc': 'Work mode'},

        # Battery Discharge/Charge Power
        # Confirmed: discharge=0 during AC-coupled solar export (battery idle);
        # non-zero only when battery actually provides/absorbs power.
        1009: {'name': 'discharge_power_high', 'scale': 1, 'unit': '', 'pair': 1010},
        1010: {'name': 'discharge_power_low', 'scale': 1, 'unit': '', 'pair': 1009,
               'combined_scale': 0.1, 'combined_unit': 'W'},
        1011: {'name': 'charge_power_high', 'scale': 1, 'unit': '', 'pair': 1012},
        1012: {'name': 'charge_power_low', 'scale': 1, 'unit': '', 'pair': 1011,
               'combined_scale': 0.1, 'combined_unit': 'W'},

        # Battery State
        1013: {'name': 'battery_voltage', 'scale': 0.1, 'unit': 'V'},
        1014: {'name': 'battery_soc', 'scale': 1, 'unit': '%'},
        1040: {'name': 'battery_temp', 'scale': 0.1, 'unit': '°C', 'signed': True},
        1041: {'name': 'battery_type', 'scale': 1, 'unit': ''},

        # BMS block (input registers) — documented in V1.39 as "BMS information 1082-1124".
        #
        # Added from the protocol rather than a scan: the same block is already
        # implemented identically in sph.py, and the Homey Growatt app reads these exact
        # addresses on this hardware. A user on #360 showed Battery Health 97%, cycle
        # count 225 and BMS status 129 in Homey while Home Assistant had none of them —
        # not a hardware limit, just registers we had never asked for.
        #
        # DELIBERATELY PARTIAL. The full block also defines SOC/voltage/current/temp at
        # 1086-1089, and those are NOT added here: this profile already carries them at
        # 1013/1014/1040/1088, field-verified by energy balance in #249. Adding the BMS
        # copies would duplicate register 1088 outright (silently overriding a verified
        # mapping, since a later dict key wins) and would give two registers the same
        # name, making _find_register_by_name() resolution order-dependent.
        1083: {'name': 'bms_status', 'scale': 1, 'unit': '', 'desc': 'Status from BMS'},
        1085: {'name': 'bms_error', 'scale': 1, 'unit': '', 'desc': 'Error information from BMS'},
        1095: {'name': 'bms_cycle_count', 'scale': 1, 'unit': '', 'desc': 'Cycle count from BMS'},
        1096: {'name': 'bms_soh', 'scale': 1, 'unit': '%', 'desc': 'SOH (State of Health) from BMS'},

        # Battery Current (BMS) — signed 16-bit, ×0.01 A
        # Positive = charging, negative = discharging (HA standard convention).
        # Confirmed: reg 1088 = 1400 during 760W charge (÷54.3V = 14.0A ✓);
        #            reg 1088 = 59686 (signed -5850) during 3050W discharge (÷52.5V = -58.1A ✓)
        1088: {'name': 'battery_current', 'scale': 0.01, 'unit': 'A', 'signed': True,
               'desc': 'BMS battery current; negative=discharging (confirmed #249 scan)'},

        # Power Flow
        # Note on register pairs: for this single-phase device the R-phase registers
        # (1015/1016 = PacToUser R, 1023/1024 = PacToGrid R) are identical to the
        # total registers (1021/1022 = PacToUser Total, 1029/1030 = PacToGrid Total).
        # We use the "Total" registers throughout for semantic correctness.
        #
        # SPA measures the grid connection point bidirectionally — power_to_user and
        # power_to_grid reflect all AC import/export through that point (battery +
        # any AC-coupled solar inverters on the same circuit), not just the battery.

        # Grid import: 1021(HIGH)/1022(LOW) = PacToUser Total.
        # Confirmed: energy balance bat_discharge + grid_import = load ✓ across all scans.
        # (SPH-TL3 names this same address pair 'power_to_load' — SPA semantics differ.)
        1021: {'name': 'power_to_user_high', 'scale': 1, 'unit': '', 'pair': 1022},
        1022: {'name': 'power_to_user_low', 'scale': 1, 'unit': '', 'pair': 1021,
               'combined_scale': 0.1, 'combined_unit': 'W'},

        # Grid export: 1029(HIGH)/1030(LOW) = PacToGrid Total.
        1029: {'name': 'power_to_grid_high', 'scale': 1, 'unit': '', 'pair': 1030},
        1030: {'name': 'power_to_grid_low', 'scale': 1, 'unit': '', 'pair': 1029,
               'combined_scale': 0.1, 'combined_unit': 'W', 'signed': True},

        # Load power: 1037(HIGH)/1038(LOW) = PacToLoad Total.
        # NOTE: SPH-TL3 maps power_to_load at 1021/1022 — those registers contain
        #       grid IMPORT on SPA. Load power on SPA is at 1037/1038.
        1037: {'name': 'power_to_load_high', 'scale': 1, 'unit': '', 'pair': 1038},
        1038: {'name': 'power_to_load_low', 'scale': 1, 'unit': '', 'pair': 1037,
               'combined_scale': 0.1, 'combined_unit': 'W'},

        # AC voltage / frequency FALLBACK only - the primary source is 2038/2037 below.
        #
        # #249 read 1105 = 21575 (215.75 V at x0.01) and 1113 = 4986-5000 (49.86-50.00 Hz),
        # and these were mapped as voltage and frequency. The protocol says otherwise: input
        # 1105 is BMS_BMSInfo and 1113 is uwMinVoltCellNo, in the BMS block where 1108/1109
        # are the max/min cell voltages. On a second SPA3000TL-BL (firmware RHAA081005,
        # #510) they read 256 and 3239 - 2.56 V and 32.39 Hz - while 2038/2037 gave 240.8 V
        # and 49.90 Hz at one discharge level and 241.9 V / 49.91 Hz at another.
        #
        # Kept, under names nothing resolves directly, so a firmware whose 2000 range does
        # not answer still gets #249's readings - but only when they are plausible mains
        # values (see _spa_ac_fallback in growatt_modbus.py).
        # NOTE: Not to be confused with holding reg 1105 (FC03) = time_period_2_enable.
        1105: {'name': 'ac_voltage_bms_block', 'scale': 0.01, 'unit': 'V',
               'desc': 'Fallback AC voltage (#249); protocol: BMS_BMSInfo'},
        1113: {'name': 'ac_frequency_bms_block', 'scale': 0.01, 'unit': 'Hz',
               'desc': 'Fallback AC frequency (#249); protocol: uwMinVoltCellNo'},

        # Energy Breakdown (all registers confirmed from day + night cross-scan analysis)
        1044: {'name': 'energy_to_user_today_high', 'scale': 1, 'unit': '', 'pair': 1045},
        1045: {'name': 'energy_to_user_today_low', 'scale': 1, 'unit': '', 'pair': 1044,
               'combined_scale': 0.1, 'combined_unit': 'kWh'},
        1046: {'name': 'energy_to_user_total_high', 'scale': 1, 'unit': '', 'pair': 1047},
        1047: {'name': 'energy_to_user_total_low', 'scale': 1, 'unit': '', 'pair': 1046,
               'combined_scale': 0.1, 'combined_unit': 'kWh'},
        1048: {'name': 'energy_to_grid_today_high', 'scale': 1, 'unit': '', 'pair': 1049},
        1049: {'name': 'energy_to_grid_today_low', 'scale': 1, 'unit': '', 'pair': 1048,
               'combined_scale': 0.1, 'combined_unit': 'kWh'},
        1050: {'name': 'energy_to_grid_total_high', 'scale': 1, 'unit': '', 'pair': 1051},
        1051: {'name': 'energy_to_grid_total_low', 'scale': 1, 'unit': '', 'pair': 1050,
               'combined_scale': 0.1, 'combined_unit': 'kWh'},
        1052: {'name': 'discharge_energy_today_high', 'scale': 1, 'unit': '', 'pair': 1053},
        1053: {'name': 'discharge_energy_today_low', 'scale': 1, 'unit': '', 'pair': 1052,
               'combined_scale': 0.1, 'combined_unit': 'kWh'},
        1054: {'name': 'discharge_energy_total_high', 'scale': 1, 'unit': '', 'pair': 1055},
        1055: {'name': 'discharge_energy_total_low', 'scale': 1, 'unit': '', 'pair': 1054,
               'combined_scale': 0.1, 'combined_unit': 'kWh'},
        1056: {'name': 'charge_energy_today_high', 'scale': 1, 'unit': '', 'pair': 1057},
        1057: {'name': 'charge_energy_today_low', 'scale': 1, 'unit': '', 'pair': 1056,
               'combined_scale': 0.1, 'combined_unit': 'kWh'},
        1058: {'name': 'charge_energy_total_high', 'scale': 1, 'unit': '', 'pair': 1059},
        1059: {'name': 'charge_energy_total_low', 'scale': 1, 'unit': '', 'pair': 1058,
               'combined_scale': 0.1, 'combined_unit': 'kWh'},
        1060: {'name': 'load_energy_today_high', 'scale': 1, 'unit': '', 'pair': 1061},
        1061: {'name': 'load_energy_today_low', 'scale': 1, 'unit': '', 'pair': 1060,
               'combined_scale': 0.1, 'combined_unit': 'kWh'},
        1062: {'name': 'load_energy_total_high', 'scale': 1, 'unit': '', 'pair': 1063},
        1063: {'name': 'load_energy_total_low', 'scale': 1, 'unit': '', 'pair': 1062,
               'combined_scale': 0.1, 'combined_unit': 'kWh'},

        # ============================================================================
        # SPA EXTENDED RANGE 2000-2124 — "thirteen group for Storage power's SPA"
        # ============================================================================
        #
        # UNVERIFIED ON HARDWARE. Scales and meanings are from the V1.39 protocol,
        # documented in docs/developer/protocol-v139.md under "Thirteenth group — SPA
        # storage (2000-2124)". Nobody has yet read these addresses on a device.
        #
        # These were mapped only after a user posted a photo of the same table on #360,
        # months after the range was already extracted into our own reference. The
        # information was checked in the whole time. Grep the reference before treating
        # a screenshot as a discovery.
        #
        # They are added because they fill gaps this profile has carried since it was
        # built: AC current and AC output power were explicitly recorded as "not
        # confirmed for SPA" in the model docs, and inverter status and AC energy had no
        # source at all. Every sensor below is already in this profile's sensor set and
        # simply had no register behind it.
        #
        # Scope note, and the reason this range is not in the SPA-TL3 profile: the
        # #360 reporter's three-phase SPA-TL3 answers nothing here, nor in 1000-1124.
        # This block describes single-phase SPA models only. A three-phase SPA uses the
        # SPH-TL3 layout instead — see spa_tl3_4000_10000_v201.
        #
        # Until v2.0.8 nothing requested this range: read_all_data had no window for
        # 2000-2999, so every field here was unread on every SPA. A SPA3000TL-BL scan
        # (#510) then showed it populated and matching the protocol.
        #
        # PARTIAL. The protocol documents roughly forty registers here; the ones below
        # are those with an existing sensor behind them. Still unmapped and available:
        # 2040/2041 (apparent power VA), 2057/2058 (work time total), 2097 (BatVolt_DSP),
        # 2098/2099 (P/N bus voltage), 2102-2111 (extra-inverter and system energy),
        # 2112-2115 (AC charge energy). Each needs a sensor definition, so they are left
        # until there is a device to verify against.
        2000: {'name': 'status', 'scale': 1, 'unit': '',
               'desc': 'Run state, hybrid work-mode codes: 0 in standby, 6 (Bat On-Grid) while discharging (#510)'},

        # Pac — AC output power. Distinct from the 1000-range flow registers above:
        # this is the inverter's own output, not the grid connection point.
        2035: {'name': 'ac_power_high', 'scale': 1, 'unit': '', 'pair': 2036},
        2036: {'name': 'ac_power_low', 'scale': 1, 'unit': '', 'pair': 2035,
               'combined_scale': 0.1, 'combined_unit': 'W', 'signed': True,
               'desc': 'AC output power (0.1 W; 634.0 / 1992.9 W discharging, #510). Sign while charging unconfirmed'},

        # Fac / Vac1 / Iac1. Protocol and #510 agree, at two operating points: 49.90 /
        # 49.91 Hz, 240.8 / 241.9 V, 2.6 / 8.1 A with Pac 634.0 / 1992.9 W.
        2037: {'name': 'ac_frequency', 'scale': 0.01, 'unit': 'Hz',
               'desc': 'AC frequency (Fac, 0.01 Hz; confirmed #510)'},
        2038: {'name': 'ac_voltage', 'scale': 0.1, 'unit': 'V',
               'desc': 'AC voltage (Vac1, 0.1 V; confirmed #510)'},
        2039: {'name': 'ac_current', 'scale': 0.1, 'unit': 'A',
               'desc': 'AC output current (Iac1, 0.1 A; confirmed #510)'},

        # Eac today / total — AC energy generated.
        #
        # Worth stating because it was an open question: an AC-coupled inverter with no
        # solar inputs does still meter the energy it puts out when discharging, and the
        # protocol gives it a home here. That is why ENERGY_SENSORS belongs on this
        # profile but not on SPA-TL3, which cannot reach these addresses.
        2053: {'name': 'energy_today_high', 'scale': 1, 'unit': '', 'pair': 2054},
        2054: {'name': 'energy_today_low', 'scale': 1, 'unit': '', 'pair': 2053,
               'combined_scale': 0.1, 'combined_unit': 'kWh',
               'desc': 'AC energy today (0.1 kWh; plausible on #510, not cross-checked)'},
        2055: {'name': 'energy_total_high', 'scale': 1, 'unit': '', 'pair': 2056},
        2056: {'name': 'energy_total_low', 'scale': 1, 'unit': '', 'pair': 2055,
               'combined_scale': 0.1, 'combined_unit': 'kWh',
               'desc': 'AC energy total (0.1 kWh; plausible on #510, not cross-checked)'},

        # Temperatures. This profile had none at all before — an SPA reported no
        # temperature of any kind, which read as "this hardware doesn't measure it"
        # rather than "we never asked".
        2093: {'name': 'inverter_temp', 'scale': 0.1, 'unit': '°C', 'signed': True,
               'desc': 'Inverter temperature (0.1 C; 23.1 C on #510)'},
        2094: {'name': 'ipm_temp', 'scale': 0.1, 'unit': '°C', 'signed': True,
               'desc': 'IPM temperature (0.1 C; 20.3 C on #510)'},
        2095: {'name': 'boost_temp', 'scale': 0.1, 'unit': '°C', 'signed': True,
               'desc': 'Boost temperature (0.1 C; 20.0 C on #510)'},
    },
    'holding_registers': {
        # Confirmed identical to SPH-TL3 from entity values in scan:
        # priority_mode, discharge_stopped_soc, charge_power_rate, time_period_1/2/3
        **SPH_TL3_3000_10000['holding_registers'],
    },
}

# Export all SPA profiles
SPA_REGISTER_MAPS = {
    'SPA_3000_6000_TL_BL': SPA_3000_6000_TL_BL,
}
