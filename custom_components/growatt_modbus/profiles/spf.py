"""
SPF Series Profiles - Off-grid Solar Inverters with Battery Storage

The SPF series are off-grid inverters designed for standalone solar systems.
Unlike grid-tied models, they have AC input (for grid/generator backup charging)
but no grid export capability.

Key Features:
- Off-grid operation with battery storage
- AC input for charging from grid/generator
- Load output for powering devices
- Battery charge/discharge management
- Detailed energy tracking for all power flows

Device Identification (Holding Registers):
- Firmware Version: Registers 9-11 (ASCII, 6 chars)
- Control Firmware Version: Registers 12-14 (ASCII, 6 chars)
- Serial Number: Registers 23-27 (ASCII, 10 chars, numbered 5→1)

IMPORTANT - Battery Power Sign Convention:
SPF uses INVERTED sign convention compared to VPP 2.01 standard:
- SPF Hardware: Positive = Discharge, Negative = Charge
- VPP 2.01:     Positive = Charge,    Negative = Discharge
This profile uses negative scale (-0.1) on registers 77-78 to convert SPF's
inverted convention to the standard convention used by Home Assistant and other models.

Battery Sensor Limitations:
- Battery Temperature: NOT AVAILABLE (SPF hardware does not provide battery temp sensor)
- Battery Current: Only measured during AC charging (shows 0 during PV charging or discharging)
- Battery Charge Energy: Only tracks AC charging (from grid/gen), NOT PV charging to battery
"""

# SPF 3000-6000 ES PLUS (Off-grid inverter with battery)
SPF_3000_6000_ES_PLUS = {
    'name': 'SPF 3000-6000 ES PLUS',
    'description': 'Off-grid solar inverter with battery storage and AC charging (3-6kW)',
    'notes': 'Uses 0-97 register range. Off-grid system with AC input, battery, and load output. No grid export.',
    'offgrid_protocol': True,
    'input_registers': {
        # System Status
        0: {'name': 'inverter_status', 'scale': 1, 'unit': '', 'desc': '0=Standby, 1=No Use, 2=Discharge, 3=Fault, 4=Flash, 5=PV Charge, 6=AC Charge, 7=Combine Charge, 8=Combine Charge+Bypass, 9=PV Charge+Bypass, 10=AC Charge+Bypass, 11=Bypass, 12=PV Charge+Discharge'},

        # PV String 1
        1: {'name': 'pv1_voltage', 'scale': 0.1, 'unit': 'V', 'desc': 'PV string 1 voltage'},
        7: {'name': 'pv1_current', 'scale': 0.1, 'unit': 'A', 'desc': 'PV string 1 current'},
        3: {'name': 'pv1_power_high', 'scale': 1, 'unit': '', 'pair': 4, 'desc': 'PV1 charge power (HIGH word)'},
        4: {'name': 'pv1_power_low', 'scale': 1, 'unit': '', 'pair': 3, 'combined_scale': 0.1, 'combined_unit': 'W', 'desc': 'PV1 charge power (LOW word)'},

        # PV String 2
        2: {'name': 'pv2_voltage', 'scale': 0.1, 'unit': 'V', 'desc': 'PV string 2 voltage'},
        8: {'name': 'pv2_current', 'scale': 0.1, 'unit': 'A', 'desc': 'PV string 2 current'},
        5: {'name': 'pv2_power_high', 'scale': 1, 'unit': '', 'pair': 6, 'desc': 'PV2 charge power (HIGH word)'},
        6: {'name': 'pv2_power_low', 'scale': 1, 'unit': '', 'pair': 5, 'combined_scale': 0.1, 'combined_unit': 'W', 'desc': 'PV2 charge power (LOW word)'},

        # AC Output Power (active power to loads)
        9: {'name': 'load_power_high', 'scale': 1, 'unit': '', 'pair': 10, 'desc': 'AC output active power (HIGH word)'},
        10: {'name': 'load_power_low', 'scale': 1, 'unit': '', 'pair': 9, 'combined_scale': 0.1, 'combined_unit': 'W', 'desc': 'AC output active power (LOW word)'},

        # AC Output Apparent Power (to loads)
        11: {'name': 'ac_apparent_power_high', 'scale': 1, 'unit': '', 'pair': 12, 'desc': 'AC output apparent power (HIGH word)'},
        12: {'name': 'ac_apparent_power_low', 'scale': 1, 'unit': '', 'pair': 11, 'combined_scale': 0.1, 'combined_unit': 'VA', 'desc': 'AC output apparent power (LOW word)'},

        # AC Charge Power (from grid/generator to battery)
        13: {'name': 'ac_charge_power_high', 'scale': 1, 'unit': '', 'pair': 14, 'desc': 'AC charge power (HIGH word)'},
        14: {'name': 'ac_charge_power_low', 'scale': 1, 'unit': '', 'pair': 13, 'combined_scale': 0.1, 'combined_unit': 'W', 'desc': 'AC charge power (LOW word)'},

        # Battery
        17: {'name': 'battery_voltage', 'scale': 0.01, 'unit': 'V', 'desc': 'Battery voltage (note: 0.01 scale for precision)'},
        18: {'name': 'battery_soc', 'scale': 1, 'unit': '%', 'desc': 'Battery state of charge'},
        # SPF uses INVERTED sign convention vs VPP 2.01: positive=discharge, negative=charge
        # Using negative scale (-0.1) to flip sign so coordinator interprets correctly
        77: {'name': 'battery_power_high', 'scale': 1, 'unit': '', 'pair': 78, 'signed': True, 'desc': 'Battery power (HIGH word, signed)'},
        78: {'name': 'battery_power_low', 'scale': 1, 'unit': '', 'pair': 77, 'combined_scale': -0.1, 'combined_unit': 'W', 'signed': True, 'desc': 'Battery power (LOW word, SPF: +discharge/-charge, inverted to standard convention)'},

        # Grid Input (AC input from grid/generator)
        20: {'name': 'grid_voltage', 'scale': 0.1, 'unit': 'V', 'desc': 'AC input voltage (grid/generator)'},
        21: {'name': 'grid_frequency', 'scale': 0.01, 'unit': 'Hz', 'desc': 'AC input frequency'},
        36: {'name': 'ac_input_power_high', 'scale': 1, 'unit': '', 'pair': 37, 'desc': 'AC input power (HIGH word)'},
        37: {'name': 'ac_input_power_low', 'scale': 1, 'unit': '', 'pair': 36, 'combined_scale': 0.1, 'combined_unit': 'W', 'desc': 'AC input power (LOW word)'},

        # AC Output (to load)
        22: {'name': 'ac_voltage', 'scale': 0.1, 'unit': 'V', 'desc': 'AC output voltage'},
        23: {'name': 'ac_frequency', 'scale': 0.01, 'unit': 'Hz', 'desc': 'AC output frequency'},
        24: {'name': 'output_dc_voltage', 'scale': 0.1, 'unit': 'V', 'desc': 'Output DC voltage (battery voltage to inverter)'},

        # Temperatures
        25: {'name': 'inverter_temp', 'scale': 0.1, 'unit': '°C', 'desc': 'Inverter temperature', 'signed': True},
        26: {'name': 'dcdc_temp', 'scale': 0.1, 'unit': '°C', 'desc': 'DC-DC converter temperature', 'signed': True},

        # Load Percentage
        27: {'name': 'load_percentage', 'scale': 0.1, 'unit': '%', 'desc': 'Load percentage of rated capacity'},

        # Work Time Total (inverter operating hours)
        30: {'name': 'time_total_high', 'scale': 1, 'unit': '', 'pair': 31, 'desc': 'Total work time (HIGH word)'},
        31: {'name': 'time_total_low', 'scale': 1, 'unit': '', 'pair': 30, 'combined_scale': 0.5, 'combined_unit': 's', 'desc': 'Total work time (LOW word, in seconds)'},

        # Buck Converter Temperatures (MPPT temperatures)
        32: {'name': 'buck1_temp', 'scale': 0.1, 'unit': '°C', 'desc': 'Buck1 temperature (PV1 MPPT)', 'signed': True},
        33: {'name': 'buck2_temp', 'scale': 0.1, 'unit': '°C', 'desc': 'Buck2 temperature (PV2 MPPT)', 'signed': True},

        # AC Output Current
        34: {'name': 'ac_current', 'scale': 0.1, 'unit': 'A', 'desc': 'AC output current (to loads)'},
        35: {'name': 'inverter_current', 'scale': 0.1, 'unit': 'A', 'desc': 'Inverter output current'},

        # Fault & Warning Codes
        40: {'name': 'fault_bit', 'scale': 1, 'unit': '', 'desc': 'Fault bit field'},
        41: {'name': 'warning_bit', 'scale': 1, 'unit': '', 'desc': 'Warning bit field'},
        42: {'name': 'fault_code', 'scale': 1, 'unit': '', 'desc': 'Fault value/code'},
        43: {'name': 'warning_code', 'scale': 1, 'unit': '', 'desc': 'Warning value/code'},

        # === Energy Counters (all 32-bit pairs) ===

        # Solar Energy
        48: {'name': 'energy_today_high', 'scale': 1, 'unit': '', 'pair': 49, 'desc': 'Solar energy today (HIGH word)'},
        49: {'name': 'energy_today_low', 'scale': 1, 'unit': '', 'pair': 48, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'Solar energy today (LOW word)'},
        50: {'name': 'energy_total_high', 'scale': 1, 'unit': '', 'pair': 51, 'desc': 'Solar energy total (HIGH word)'},
        51: {'name': 'energy_total_low', 'scale': 1, 'unit': '', 'pair': 50, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'Solar energy total (LOW word)'},

        # Battery Charge Energy (from grid/generator via AC charging)
        # Note: SPF only measures AC charging energy (from grid/gen), not PV charging to battery
        # Named charge_energy_* (not ac_charge_energy_*) for battery_charge sensor compatibility
        56: {'name': 'charge_energy_today_high', 'scale': 1, 'unit': '', 'pair': 57, 'desc': 'Battery charge energy today (HIGH word) - AC charge only on SPF'},
        57: {'name': 'charge_energy_today_low', 'scale': 1, 'unit': '', 'pair': 56, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'Battery charge energy today (LOW word) - AC charge only on SPF'},
        58: {'name': 'charge_energy_total_high', 'scale': 1, 'unit': '', 'pair': 59, 'desc': 'Battery charge energy total (HIGH word) - AC charge only on SPF'},
        59: {'name': 'charge_energy_total_low', 'scale': 1, 'unit': '', 'pair': 58, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'Battery charge energy total (LOW word) - AC charge only on SPF'},

        # Battery Discharge Energy
        60: {'name': 'discharge_energy_today_high', 'scale': 1, 'unit': '', 'pair': 61, 'desc': 'Battery discharge energy today (HIGH word)'},
        61: {'name': 'discharge_energy_today_low', 'scale': 1, 'unit': '', 'pair': 60, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'Battery discharge energy today (LOW word)'},
        62: {'name': 'discharge_energy_total_high', 'scale': 1, 'unit': '', 'pair': 63, 'desc': 'Battery discharge energy total (HIGH word)'},
        63: {'name': 'discharge_energy_total_low', 'scale': 1, 'unit': '', 'pair': 62, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'Battery discharge energy total (LOW word)'},

        # AC Discharge Energy (from battery to load via inverter)
        64: {'name': 'ac_discharge_energy_today_high', 'scale': 1, 'unit': '', 'pair': 65, 'desc': 'AC discharge energy today (HIGH word)'},
        65: {'name': 'ac_discharge_energy_today_low', 'scale': 1, 'unit': '', 'pair': 64, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'AC discharge energy today (LOW word)'},
        66: {'name': 'ac_discharge_energy_total_high', 'scale': 1, 'unit': '', 'pair': 67, 'desc': 'AC discharge energy total (HIGH word)'},
        67: {'name': 'ac_discharge_energy_total_low', 'scale': 1, 'unit': '', 'pair': 66, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'AC discharge energy total (LOW word)'},

        # Battery Current (only measured during AC charging on SPF)
        # Note: SPF hardware limitation - no general battery current sensor
        # Named battery_current (not ac_charge_battery_current) for battery_current sensor compatibility
        68: {'name': 'battery_current', 'scale': 0.1, 'unit': 'A', 'desc': 'Battery current (SPF: only shows current during AC charging, 0 otherwise)'},
        69: {'name': 'ac_discharge_power_high', 'scale': 1, 'unit': '', 'pair': 70, 'desc': 'AC discharge power (HIGH word)'},
        70: {'name': 'ac_discharge_power_low', 'scale': 1, 'unit': '', 'pair': 69, 'combined_scale': 0.1, 'combined_unit': 'W', 'desc': 'AC discharge power (LOW word)'},

        # Fan Speeds
        81: {'name': 'mppt_fan_speed', 'scale': 1, 'unit': '%', 'desc': 'MPPT fan speed percentage'},
        82: {'name': 'inverter_fan_speed', 'scale': 1, 'unit': '%', 'desc': 'Inverter fan speed percentage'},

        # Operational Discharge Energy (Equipment Operation Discharge)
        85: {'name': 'op_discharge_energy_today_high', 'scale': 1, 'unit': '', 'pair': 86, 'desc': 'Operational discharge energy today (HIGH word)'},
        86: {'name': 'op_discharge_energy_today_low', 'scale': 1, 'unit': '', 'pair': 85, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'Operational discharge energy today (LOW word)'},
        87: {'name': 'op_discharge_energy_total_high', 'scale': 1, 'unit': '', 'pair': 88, 'desc': 'Operational discharge energy total (HIGH word)'},
        88: {'name': 'op_discharge_energy_total_low', 'scale': 1, 'unit': '', 'pair': 87, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'Operational discharge energy total (LOW word)'},

        # Generator Energy (from grid/generator input) - Issue #145
        # For SPF 6000 ES Plus and similar models with generator input
        92: {'name': 'generator_discharge_today_high', 'scale': 1, 'unit': '', 'pair': 93, 'desc': 'Generator discharge energy today (HIGH word)'},
        93: {'name': 'generator_discharge_today_low', 'scale': 1, 'unit': '', 'pair': 92, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'Generator discharge energy today (LOW word)'},
        94: {'name': 'generator_discharge_total_high', 'scale': 1, 'unit': '', 'pair': 95, 'desc': 'Generator discharge energy total (HIGH word)'},
        95: {'name': 'generator_discharge_total_low', 'scale': 1, 'unit': '', 'pair': 94, 'combined_scale': 0.1, 'combined_unit': 'kWh', 'desc': 'Generator discharge energy total (LOW word)'},

        # Generator Power and Voltage (16-bit single registers)
        96: {'name': 'generator_power', 'scale': 1, 'unit': 'W', 'desc': 'Current generator power output'},
        97: {'name': 'generator_voltage', 'scale': 0.1, 'unit': 'V', 'desc': 'Current generator voltage'},
    },
    'holding_registers': {
        # System Control
        0: {'name': 'on_off', 'scale': 1, 'unit': '', 'access': 'RW', 'desc': '0=Off, 1=On'},
        3: {'name': 'active_power_rate', 'scale': 1, 'unit': '%', 'access': 'RW', 'desc': 'Active power rate control'},

        # Output Priority Configuration
        1: {'name': 'output_config', 'scale': 1, 'unit': '', 'access': 'RW',
            'desc': 'Output source priority',
            'values': {
                0: 'SBU (Battery First)',
                1: 'SOL (Solar First)',
                2: 'UTI (Utility First)',
                3: 'SUB (Solar & Utility First)'
            }},

        # Charge Priority Configuration
        2: {'name': 'charge_config', 'scale': 1, 'unit': '', 'access': 'RW',
            'desc': 'Charge source priority',
            'values': {
                0: 'CSO (Solar First)',
                1: 'SNU (Solar & Utility)',
                2: 'OSO (Solar Only)'
            }},

        # AC Input Mode
        8: {'name': 'ac_input_mode', 'scale': 1, 'unit': '', 'access': 'RW',
            'desc': 'AC input mode selection',
            'values': {
                0: 'APL (Appliance)',
                1: 'UPS',
                2: 'GEN (Generator)'
            }},

        # === DEVICE IDENTIFICATION ===

        # Firmware Version (ASCII, 2 chars per register = 6 chars total)
        9: {'name': 'firmware_version_high', 'scale': 1, 'unit': '', 'access': 'RO', 'desc': 'Firmware version HIGH (ASCII)'},
        10: {'name': 'firmware_version_medium', 'scale': 1, 'unit': '', 'access': 'RO', 'desc': 'Firmware version MEDIUM (ASCII)'},
        11: {'name': 'firmware_version_low', 'scale': 1, 'unit': '', 'access': 'RO', 'desc': 'Firmware version LOW (ASCII)'},

        # Control Firmware Version (ASCII, 2 chars per register = 6 chars total)
        12: {'name': 'control_firmware_version_high', 'scale': 1, 'unit': '', 'access': 'RO', 'desc': 'Control firmware version HIGH (ASCII)'},
        13: {'name': 'control_firmware_version_medium', 'scale': 1, 'unit': '', 'access': 'RO', 'desc': 'Control firmware version MEDIUM (ASCII)'},
        14: {'name': 'control_firmware_version_low', 'scale': 1, 'unit': '', 'access': 'RO', 'desc': 'Control firmware version LOW (ASCII)'},

        # Serial Number (ASCII, 2 chars per register = 10 chars total)
        # Note: Numbered 5 to 1 (register 23 = serial_5, register 27 = serial_1)
        23: {'name': 'serial_number_5', 'scale': 1, 'unit': '', 'access': 'RO', 'desc': 'Serial number chars 1-2 (ASCII)'},
        24: {'name': 'serial_number_4', 'scale': 1, 'unit': '', 'access': 'RO', 'desc': 'Serial number chars 3-4 (ASCII)'},
        25: {'name': 'serial_number_3', 'scale': 1, 'unit': '', 'access': 'RO', 'desc': 'Serial number chars 5-6 (ASCII)'},
        26: {'name': 'serial_number_2', 'scale': 1, 'unit': '', 'access': 'RO', 'desc': 'Serial number chars 7-8 (ASCII)'},
        27: {'name': 'serial_number_1', 'scale': 1, 'unit': '', 'access': 'RO', 'desc': 'Serial number chars 9-10 (ASCII)'},

        # Battery Low Voltage/SOC Switch to Utility (Battery to Grid)
        # BATTERY TYPE DEPENDENT (see register 39)
        # Non-Lithium (AGM/FLD/USE/USE2): 200-640 = 20.0V - 64.0V (scale 0.1V)
        # Lithium: 0-1000 = 0% - 100% (scale 0.1%)
        37: {'name': 'bat_low_to_uti', 'scale': 0.1, 'unit': 'V/%', 'access': 'RW',
             'valid_range': (0, 1000),
             'desc': 'Battery to Grid: SOC level to switch from battery to utility. Non-Lithium: 20.0-64.0V, Lithium: 0-100%',
             'battery_dependent': True},

        # AC Charge Current
        38: {'name': 'ac_charge_current', 'scale': 1, 'unit': 'A', 'access': 'RW',
             'valid_range': (0, 80),
             'desc': 'AC charging current limit (SPF 6000 hardware max: 80A, stored directly)'},

        # Battery Type
        39: {'name': 'battery_type', 'scale': 1, 'unit': '', 'access': 'RW',
             'desc': 'Battery type selection (can only be set in standby state)',
             'values': {
                 0: 'AGM',
                 1: 'Flooded (FLD)',
                 2: 'User Defined',
                 3: 'Lithium',
                 4: 'User Defined 2'
             }},

        # NOTE: Device Type Code (DTC) is at INPUT register 44, not holding registers
        # DTC is used during auto-detection only (034xx for SPF 3-6K ES PLUS series)
        # Holding register 43 may contain DTC as fallback on some firmware versions

        # Generator Charge Current
        83: {'name': 'gen_charge_current', 'scale': 1, 'unit': 'A', 'access': 'RW',
             'valid_range': (0, 80),
             'desc': 'Generator charging current limit (SPF 6000 hardware max: 80A, stored directly)'},

        # AC to Battery Voltage/SOC Switch Point (Grid to Battery)
        # BATTERY TYPE DEPENDENT (see register 39)
        # Non-Lithium (AGM/FLD/USE/USE2): 200-640 = 20.0V - 64.0V (scale 0.1V)
        # Lithium: 0-1000 = 0% - 100% (scale 0.1%)
        95: {'name': 'ac_to_bat_volt', 'scale': 0.1, 'unit': 'V/%', 'access': 'RW',
             'valid_range': (0, 1000),
             'desc': 'Grid to Battery: SOC level to switch back from utility to battery mode. Non-Lithium: 20.0-64.0V, Lithium: 0-100%',
             'battery_dependent': True},
    }
}

# Export register maps for import by __init__.py
SPF_REGISTER_MAPS = {
    'SPF_3000_6000_ES_PLUS': SPF_3000_6000_ES_PLUS,
}
