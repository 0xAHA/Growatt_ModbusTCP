# SPH 3000-6000 (Single-phase hybrid with battery)
SPH_3000_6000 = {
    'name': 'SPH Series 3-6kW',
    'description': 'Single-phase hybrid inverter with battery storage (3-6kW)',
    'notes': 'Uses 0-124 register range. 2 PV strings, battery management, backup output.',
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

        # Battery (registers 13-18 for battery in SPH models)
        13: {'name': 'battery_voltage', 'scale': 0.1, 'unit': 'V', 'desc': 'Battery pack voltage'},
        14: {'name': 'battery_current', 'scale': 0.1, 'unit': 'A', 'desc': 'Battery current (+ charging, - discharging)', 'signed': True},
        15: {'name': 'battery_power', 'scale': 1, 'unit': 'W', 'desc': 'Battery power (+ charging, - discharging)', 'signed': True},
        17: {'name': 'battery_soc', 'scale': 1, 'unit': '%', 'desc': 'Battery state of charge'},
        18: {'name': 'battery_temp', 'scale': 0.1, 'unit': '°C', 'desc': 'Battery temperature'},
        19: {'name': 'bms_type', 'scale': 1, 'unit': '', 'desc': 'BMS type identifier'},

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

        # Backup Output (registers 59-64 for backup/load in SPH models)
        59: {'name': 'backup_voltage', 'scale': 0.1, 'unit': 'V', 'desc': 'Backup output voltage'},
        60: {'name': 'backup_current', 'scale': 0.1, 'unit': 'A', 'desc': 'Backup output current'},
        61: {'name': 'backup_power', 'scale': 1, 'unit': 'W', 'desc': 'Backup output power'},
        62: {'name': 'backup_frequency', 'scale': 0.01, 'unit': 'Hz', 'desc': 'Backup output frequency'},
        64: {'name': 'load_power', 'scale': 1, 'unit': 'W', 'desc': 'Load consumption power'},

        # Temperatures
        93: {'name': 'inverter_temp', 'scale': 0.1, 'unit': '°C'},
        94: {'name': 'ipm_temp', 'scale': 0.1, 'unit': '°C'},
        95: {'name': 'boost_temp', 'scale': 0.1, 'unit': '°C'},

        # Diagnostics
        104: {'name': 'derating_mode', 'scale': 1, 'unit': ''},
        105: {'name': 'fault_code', 'scale': 1, 'unit': ''},
        112: {'name': 'warning_code', 'scale': 1, 'unit': ''},
    },
    'holding_registers': {
        0: {'name': 'on_off', 'scale': 1, 'unit': '', 'access': 'RW', 'desc': '0=Off, 1=On'},
        3: {'name': 'active_power_rate', 'scale': 1, 'unit': '%', 'access': 'RW'},
    }
}

# SPH 7000-10000 (Higher power version)
SPH_7000_10000 = {
    'name': 'SPH Seres 7-10KW',
    'description': 'Single-phase hybrid inverter with battery storage (7-10kW)',
    'notes': 'Uses 0-124 register range. Same registers as 3-6kW model, higher power rating.',
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

        # Battery
        13: {'name': 'battery_voltage', 'scale': 0.1, 'unit': 'V'},
        14: {'name': 'battery_current', 'scale': 0.1, 'unit': 'A', 'signed': True},
        15: {'name': 'battery_power', 'scale': 1, 'unit': 'W', 'signed': True},
        17: {'name': 'battery_soc', 'scale': 1, 'unit': '%'},
        18: {'name': 'battery_temp', 'scale': 0.1, 'unit': '°C'},
        19: {'name': 'bms_type', 'scale': 1, 'unit': ''},

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

        # Backup Output
        59: {'name': 'backup_voltage', 'scale': 0.1, 'unit': 'V'},
        60: {'name': 'backup_current', 'scale': 0.1, 'unit': 'A'},
        61: {'name': 'backup_power', 'scale': 1, 'unit': 'W'},
        62: {'name': 'backup_frequency', 'scale': 0.01, 'unit': 'Hz'},
        64: {'name': 'load_power', 'scale': 1, 'unit': 'W'},

        # Temperatures
        93: {'name': 'inverter_temp', 'scale': 0.1, 'unit': '°C'},
        94: {'name': 'ipm_temp', 'scale': 0.1, 'unit': '°C'},
        95: {'name': 'boost_temp', 'scale': 0.1, 'unit': '°C'},

        # Diagnostics
        104: {'name': 'derating_mode', 'scale': 1, 'unit': ''},
        105: {'name': 'fault_code', 'scale': 1, 'unit': ''},
        112: {'name': 'warning_code', 'scale': 1, 'unit': ''},
    },
    'holding_registers': {
        0: {'name': 'on_off', 'scale': 1, 'unit': '', 'access': 'RW'},
        3: {'name': 'active_power_rate', 'scale': 1, 'unit': '%', 'access': 'RW'},
    }
}

# Export all SPH profiles
SPH_REGISTER_MAPS = {
    'SPH_3000_6000': SPH_3000_6000,
    'SPH_7000_10000': SPH_7000_10000,
}