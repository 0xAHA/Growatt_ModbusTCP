# SPA Series - AC-Coupled Battery Storage (No PV MPPT Inputs)
# Based on SPA 3000TL BL + Ark 2.5L-A1 register scans (issue #249)
# Scan date: 2026-04 (day + night scans cross-verified)

from .sph_tl3 import SPH_TL3_3000_10000

SPA_3000_6000_TL_BL = {
    'name': 'SPA (AC Storage) 3-6kW',
    'description': 'AC-coupled battery storage inverter — no PV MPPT inputs (SPA 3000TL BL and similar)',
    'notes': (
        'Uses the 1000-1124 range, plus 2000-2124 per the protocol (unverified). '
        'No solar DC inputs. '
        'Base range (0-124) and 3000+ range respond with zeros — not exceptions. '
        'Holding registers identical to SPH-TL3. '
        'Register layout differs from SPH-TL3 at shared addresses: '
        'reg 1021/1022 = grid import power on SPA (SPH-TL3 calls this power_to_load); '
        'reg 1037/1038 = load power (SPH-TL3 load power is at 1021/1022). '
        'Grid frequency at reg 1113 (×0.01 Hz). Battery current at reg 1088 (×0.01 A, signed).'
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

        # AC Grid Voltage
        # Reg 1105 (input FC04) = ~21575 raw → ×0.01 = 215.75V on UK 230V grid.
        # Constant between day/night scans — consistent with mains voltage.
        # NOTE: Not to be confused with holding reg 1105 (FC03) = time_period_2_enable.
        1105: {'name': 'ac_voltage', 'scale': 0.01, 'unit': 'V',
               'desc': 'Grid/AC voltage (×0.01; confirmed ~216V on 230V grid)'},

        # Grid Frequency
        # Confirmed: 4986 × 0.01 = 49.86 Hz, 5000 = 50.00 Hz, varies realistically (#249).
        1113: {'name': 'ac_frequency', 'scale': 0.01, 'unit': 'Hz',
               'desc': 'Grid frequency (×0.01 Hz; confirmed 49.86-50.00 Hz range #249)'},

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
        # UNVERIFIED ON HARDWARE. Transcribed from the Growatt protocol table posted on
        # #360, which is the only description of this range we have. Scales and meanings
        # are the document's; nobody has yet read these addresses on a device.
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
        # If you own a single-phase SPA, a scan of 2000-2124 would confirm or refute all
        # of this in one pass; the scanner has covered the range since v1.4.0.
        2000: {'name': 'status', 'scale': 1, 'unit': '',
               'desc': 'Inverter run state (0=waiting, 1=normal, 3=fault) — spec, unverified'},

        # Pac — AC output power. Distinct from the 1000-range flow registers above:
        # this is the inverter's own output, not the grid connection point.
        2035: {'name': 'ac_power_high', 'scale': 1, 'unit': '', 'pair': 2036},
        2036: {'name': 'ac_power_low', 'scale': 1, 'unit': '', 'pair': 2035,
               'combined_scale': 0.1, 'combined_unit': 'W',
               'desc': 'AC output power (spec 0.1W, unverified)'},

        # Iac1 — AC output current. Fills a gap the model matrix flagged as unconfirmed.
        #
        # Vac1 (2038, 0.1V) and Fac (2037, 0.01Hz) are deliberately NOT mapped: this
        # profile already has ac_voltage at 1105 and ac_frequency at 1113, both verified
        # against real readings in #249. A second register with the same name would make
        # _find_register_by_name() resolution order-dependent, and the verified one must
        # win. Document-derived values do not get to displace measured ones.
        2039: {'name': 'ac_current', 'scale': 0.1, 'unit': 'A',
               'desc': 'AC output current (spec 0.1A, unverified)'},

        # Eac today / total — AC energy generated.
        #
        # Worth stating because it was an open question: an AC-coupled inverter with no
        # solar inputs does still meter the energy it puts out when discharging, and the
        # protocol gives it a home here. That is why ENERGY_SENSORS belongs on this
        # profile but not on SPA-TL3, which cannot reach these addresses.
        2053: {'name': 'energy_today_high', 'scale': 1, 'unit': '', 'pair': 2054},
        2054: {'name': 'energy_today_low', 'scale': 1, 'unit': '', 'pair': 2053,
               'combined_scale': 0.1, 'combined_unit': 'kWh',
               'desc': 'AC energy today (spec 0.1kWh, unverified)'},
        2055: {'name': 'energy_total_high', 'scale': 1, 'unit': '', 'pair': 2056},
        2056: {'name': 'energy_total_low', 'scale': 1, 'unit': '', 'pair': 2055,
               'combined_scale': 0.1, 'combined_unit': 'kWh',
               'desc': 'AC energy total (spec 0.1kWh, unverified)'},
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
