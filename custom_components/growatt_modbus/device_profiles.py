"""Device profiles for Growatt inverters."""
from typing import Dict, Set

# ============================================================================
# SENSOR GROUPS
# ============================================================================

BASIC_PV_SENSORS: Set[str] = {
    "pv1_voltage", "pv1_current", "pv1_power",
    "pv2_voltage", "pv2_current", "pv2_power",
    "pv_total_power",
}

PV3_SENSORS: Set[str] = {
    "pv3_voltage", "pv3_current", "pv3_power",
}

BASIC_AC_SENSORS: Set[str] = {
    "ac_voltage", "ac_current", "ac_power", "ac_frequency",
}

GRID_SENSORS: Set[str] = {
    "grid_power", "grid_export_power", "grid_import_power",
}

POWER_FLOW_SENSORS: Set[str] = {
    "power_to_grid", "power_to_load", "power_to_user",
}

CONSUMPTION_SENSORS: Set[str] = {
    "self_consumption", "self_consumption_percentage", "house_consumption",
}

ENERGY_SENSORS: Set[str] = {
    "energy_today", "energy_total",
}

ENERGY_BREAKDOWN_SENSORS: Set[str] = {
    "grid_energy_today", "grid_energy_total",
    "energy_to_grid_today", "energy_to_grid_total",
    "grid_import_energy_today", "grid_import_energy_total",
    "load_energy_today", "load_energy_total",
}

BATTERY_SENSORS: Set[str] = {
    "battery_voltage", "battery_current", "battery_soc",
    "battery_temp", "battery_power",
    "battery_charge_power", "battery_discharge_power",
    "battery_charge_today", "battery_discharge_today",
    "battery_charge_total", "battery_discharge_total",
}

BMS_SENSORS: Set[str] = {
    "bms_status", "bms_error", "bms_warn_info",
    "bms_max_current", "bms_cycle_count", "bms_soh",
    "bms_constant_volt", "bms_max_cell_volt", "bms_min_cell_volt",
    "bms_module_num", "bms_battery_count",
    "bms_max_soc", "bms_min_soc",
}

TEMPERATURE_SENSORS: Set[str] = {
    "inverter_temp", "ipm_temp", "boost_temp",
}

STATUS_SENSORS: Set[str] = {
    "status", "last_update", "derating_mode", "fault_code", "warning_code",
}

THREE_PHASE_SENSORS: Set[str] = {
    "ac_voltage_r", "ac_voltage_s", "ac_voltage_t",  # Phase voltages
    "ac_voltage_rs", "ac_voltage_st", "ac_voltage_tr",  # Line-to-line voltages
    "ac_current_r", "ac_current_s", "ac_current_t",  # Phase currents
    "ac_power_r", "ac_power_s", "ac_power_t",  # Phase powers
    "ac_frequency",
}

SYSTEM_OUTPUT_SENSORS: Set[str] = {
    "system_output_power",
}

SPF_OFFGRID_SENSORS: Set[str] = {
    # Load monitoring
    "load_percentage",
    # AC apparent power (VA)
    "ac_apparent_power",
    # AC charge/discharge energy (from grid/generator)
    "ac_charge_energy_today", "ac_discharge_energy_today",
    # Fan speeds
    "mppt_fan_speed", "inverter_fan_speed",
    # Temperatures
    "dcdc_temp", "buck1_temp", "buck2_temp",
}


# ============================================================================
# INVERTER PROFILES
# ============================================================================

INVERTER_PROFILES = {
    
    # ========================================================================
    # MIC SERIES - Single Phase Micro Inverters
    # ========================================================================
    "mic_600_3300tl_x": {
        "name": "MIC 600-3300TL-X",
        "description": "Micro inverter (0.6-3.3kW)",
        "register_map": "MIC_600_3300TL_X",
        "phases": 1,
        "has_pv3": False,
        "has_battery": False,
        "max_power_kw": 3.3,
        "sensors": (
            BASIC_PV_SENSORS |
            BASIC_AC_SENSORS |
            ENERGY_SENSORS |
            TEMPERATURE_SENSORS |
            STATUS_SENSORS
        ),
    },

    # MIC V2.01 VPP Protocol
    "mic_600_3300tl_x_v201": {
        "name": "MIC 600-3300TL-X",
        "description": "Micro inverter (0.6-3.3kW) with VPP Protocol V2.01",
        "register_map": "MIC_600_3300TL_X_V201",
        "phases": 1,
        "has_pv3": False,
        "has_battery": False,
        "max_power_kw": 3.3,
        "protocol_version": "v2.01",
        "sensors": (
            BASIC_PV_SENSORS |
            BASIC_AC_SENSORS |
            ENERGY_SENSORS |
            TEMPERATURE_SENSORS |
            STATUS_SENSORS
        ),
    },

    # ========================================================================
    # MIN SERIES - Single Phase String Inverters
    # ========================================================================
    
    "min_3000_6000_tl_x": {
        "name": "MIN Series 3000-6000TL-X",
        "description": "2 PV string single-phase inverter (3-6kW)",
        "register_map": "MIN_3000_6000TL_X",
        "phases": 1,
        "has_pv3": False,
        "has_battery": False,
        "max_power_kw": 6.0,
        "protocol_version": "v1.39",
        "sensors": (
            BASIC_PV_SENSORS |
            BASIC_AC_SENSORS |
            GRID_SENSORS |
            POWER_FLOW_SENSORS |
            CONSUMPTION_SENSORS |
            ENERGY_SENSORS |
            ENERGY_BREAKDOWN_SENSORS |
            TEMPERATURE_SENSORS |
            STATUS_SENSORS
        ),
    },
    
    "min_7000_10000_tl_x": {
        "name": "MIN Series 7000-10000TL-X",
        "description": "3 PV string single-phase inverter (7-10kW)",
        "register_map": "MIN_7000_10000TL_X",
        "phases": 1,
        "has_pv3": True,
        "has_battery": False,
        "max_power_kw": 10.0,
        "protocol_version": "v1.39",
        "sensors": (
            BASIC_PV_SENSORS |
            PV3_SENSORS |
            BASIC_AC_SENSORS |
            SYSTEM_OUTPUT_SENSORS |
            GRID_SENSORS |
            POWER_FLOW_SENSORS |
            CONSUMPTION_SENSORS |
            ENERGY_SENSORS |
            ENERGY_BREAKDOWN_SENSORS |
            TEMPERATURE_SENSORS |
            STATUS_SENSORS
        ),
    },

    # MIN Series VPP Protocol V2.01 (adds 30000 range for DTC)
    "min_3000_6000_tl_x_v201": {
        "name": "MIN Series 3-6kW",
        "description": "2 PV string inverter with VPP Protocol V2.01",
        "register_map": "MIN_3000_6000TL_X_V201",
        "phases": 1,
        "has_pv3": False,
        "has_battery": False,
        "max_power_kw": 6.0,
        "protocol_version": "v2.01",
        "sensors": (
            BASIC_PV_SENSORS |
            BASIC_AC_SENSORS |
            GRID_SENSORS |
            POWER_FLOW_SENSORS |
            CONSUMPTION_SENSORS |
            ENERGY_SENSORS |
            ENERGY_BREAKDOWN_SENSORS |
            TEMPERATURE_SENSORS |
            STATUS_SENSORS
        ),
    },

    "min_7000_10000_tl_x_v201": {
        "name": "MIN Series 7-10kW",
        "description": "3 PV string inverter with VPP Protocol V2.01",
        "register_map": "MIN_7000_10000TL_X_V201",
        "phases": 1,
        "has_pv3": True,
        "has_battery": False,
        "max_power_kw": 10.0,
        "protocol_version": "v2.01",
        "sensors": (
            BASIC_PV_SENSORS |
            PV3_SENSORS |
            BASIC_AC_SENSORS |
            SYSTEM_OUTPUT_SENSORS |
            GRID_SENSORS |
            POWER_FLOW_SENSORS |
            CONSUMPTION_SENSORS |
            ENERGY_SENSORS |
            ENERGY_BREAKDOWN_SENSORS |
            TEMPERATURE_SENSORS |
            STATUS_SENSORS
        ),
    },

    # ========================================================================
    # TL-XH SERIES - Single Phase Hybrid (with battery)
    # ========================================================================
    
    "tl_xh_3000_10000": {
        "name": "TL-XH 3000-10000",
        "description": "Hybrid single-phase inverter with battery (3-10kW)",
        "register_map": "TL_XH_3000_10000",
        "phases": 1,
        "has_pv3": True,
        "has_battery": True,
        "max_power_kw": 10.0,
        "sensors": (
            BASIC_PV_SENSORS |
            PV3_SENSORS |
            BASIC_AC_SENSORS |
            GRID_SENSORS |
            POWER_FLOW_SENSORS |
            CONSUMPTION_SENSORS |
            ENERGY_SENSORS |
            ENERGY_BREAKDOWN_SENSORS |
            BATTERY_SENSORS |
            TEMPERATURE_SENSORS |
            STATUS_SENSORS
        ),
    },
    
    "tl_xh_us_3000_10000": {
        "name": "TL-XH US 3000-10000",
        "description": "US hybrid single-phase inverter with battery (3-10kW)",
        "register_map": "TL_XH_US_3000_10000",
        "phases": 1,
        "has_pv3": True,
        "has_battery": True,
        "max_power_kw": 10.0,
        "sensors": (
            BASIC_PV_SENSORS |
            PV3_SENSORS |
            BASIC_AC_SENSORS |
            GRID_SENSORS |
            POWER_FLOW_SENSORS |
            CONSUMPTION_SENSORS |
            ENERGY_SENSORS |
            ENERGY_BREAKDOWN_SENSORS |
            BATTERY_SENSORS |
            TEMPERATURE_SENSORS |
            STATUS_SENSORS
        ),
    },

    # TL-XH V2.01 VPP Protocol
    "tl_xh_3000_10000_v201": {
        "name": "TL-XH 3000-10000",
        "description": "Hybrid single-phase inverter with battery (3-10kW) and VPP Protocol V2.01",
        "register_map": "TL_XH_3000_10000_V201",
        "phases": 1,
        "has_pv3": True,
        "has_battery": True,
        "max_power_kw": 10.0,
        "protocol_version": "v2.01",
        "sensors": (
            BASIC_PV_SENSORS |
            PV3_SENSORS |
            BASIC_AC_SENSORS |
            GRID_SENSORS |
            POWER_FLOW_SENSORS |
            CONSUMPTION_SENSORS |
            ENERGY_SENSORS |
            ENERGY_BREAKDOWN_SENSORS |
            BATTERY_SENSORS |
            TEMPERATURE_SENSORS |
            STATUS_SENSORS
        ),
    },

    "tl_xh_us_3000_10000_v201": {
        "name": "TL-XH US 3000-10000",
        "description": "US hybrid single-phase inverter with battery (3-10kW) and VPP Protocol V2.01",
        "register_map": "TL_XH_US_3000_10000_V201",
        "phases": 1,
        "has_pv3": True,
        "has_battery": True,
        "max_power_kw": 10.0,
        "protocol_version": "v2.01",
        "sensors": (
            BASIC_PV_SENSORS |
            PV3_SENSORS |
            BASIC_AC_SENSORS |
            GRID_SENSORS |
            POWER_FLOW_SENSORS |
            CONSUMPTION_SENSORS |
            ENERGY_SENSORS |
            ENERGY_BREAKDOWN_SENSORS |
            BATTERY_SENSORS |
            TEMPERATURE_SENSORS |
            STATUS_SENSORS
        ),
    },

    # MIN TL-XH Hybrid - Uses MIN 3000+ range with VPP battery
    "min_tl_xh_3000_10000_v201": {
        "name": "MIN TL-XH 3000-10000",
        "description": "MIN series TL-XH hybrid with battery (3-10kW) using 3000+ and 31000+ ranges",
        "register_map": "MIN_TL_XH_3000_10000_V201",
        "phases": 1,
        "has_pv3": True,  # 3-6kW: 2 strings, 7-10kW: 3 strings
        "has_battery": True,
        "max_power_kw": 10.0,
        "protocol_version": "v2.01",
        "sensors": (
            BASIC_PV_SENSORS |
            PV3_SENSORS |
            BASIC_AC_SENSORS |
            GRID_SENSORS |
            POWER_FLOW_SENSORS |
            CONSUMPTION_SENSORS |
            ENERGY_SENSORS |
            ENERGY_BREAKDOWN_SENSORS |
            BATTERY_SENSORS |
            TEMPERATURE_SENSORS |
            STATUS_SENSORS
        ),
    },

    # ========================================================================
    # MID SERIES - Three Phase String Inverters
    # ========================================================================
    
    "mid_15000_25000tl3_x": {
        "name": "MID Series 15000-25000TL3-X",
        "description": "Three-phase commercial inverter (15-25kW)",
        "register_map": "MID_15000_25000TL3_X",
        "phases": 3,
        "has_pv3": False,
        "has_battery": False,
        "max_power_kw": 25.0,
        "sensors": (
            BASIC_PV_SENSORS |
            THREE_PHASE_SENSORS |
            ENERGY_SENSORS |
            TEMPERATURE_SENSORS |
            STATUS_SENSORS
        ),
    },

    # MID V2.01 VPP Protocol
    "mid_15000_25000tl3_x_v201": {
        "name": "MID Series 15-25kW",
        "description": "Three-phase commercial inverter (15-25kW) with VPP Protocol V2.01",
        "register_map": "MID_15000_25000TL3_X_V201",
        "phases": 3,
        "has_pv3": False,
        "has_battery": False,
        "max_power_kw": 25.0,
        "protocol_version": "v2.01",
        "sensors": (
            BASIC_PV_SENSORS |
            THREE_PHASE_SENSORS |
            ENERGY_SENSORS |
            TEMPERATURE_SENSORS |
            STATUS_SENSORS
        ),
    },

    # ========================================================================
    # SPH SERIES - Hybrid Storage (Single Phase with Battery)
    # ========================================================================
    
    "sph_3000_6000": {
        "name": "SPH Series 3000-6000",
        "description": "Single-phase hybrid inverter with battery storage (3-6kW)",
        "register_map": "SPH_3000_6000",
        "phases": 1,
        "has_pv3": False,
        "has_battery": True,
        "max_power_kw": 6.0,
        "sensors": (
            BASIC_PV_SENSORS |
            BASIC_AC_SENSORS |
            GRID_SENSORS |
            POWER_FLOW_SENSORS |
            CONSUMPTION_SENSORS |
            ENERGY_SENSORS |
            ENERGY_BREAKDOWN_SENSORS |
            BATTERY_SENSORS |
            TEMPERATURE_SENSORS |
            STATUS_SENSORS
        ),
    },
    
    "sph_7000_10000": {
        "name": "SPH Series 7000-10000",
        "description": "Single-phase hybrid inverter with battery storage (7-10kW)",
        "register_map": "SPH_7000_10000",
        "phases": 1,
        "has_pv3": True,  # 7-10kW models have 3 PV strings (registers 11-14)
        "has_battery": True,
        "max_power_kw": 10.0,
        "sensors": (
            BASIC_PV_SENSORS |
            PV3_SENSORS |  # 7-10kW models have 3 PV strings
            BASIC_AC_SENSORS |
            GRID_SENSORS |
            POWER_FLOW_SENSORS |
            CONSUMPTION_SENSORS |
            ENERGY_SENSORS |
            ENERGY_BREAKDOWN_SENSORS |
            BATTERY_SENSORS |
            TEMPERATURE_SENSORS |
            STATUS_SENSORS
        ),
    },

    "sph_8000_10000_hu": {
        "name": "SPH/SPM 8000-10000TL-HU",
        "description": "Single-phase hybrid inverter with battery and 3 MPPT inputs (8-10kW)",
        "register_map": "SPH_8000_10000_HU",
        "phases": 1,
        "has_pv3": True,
        "has_battery": True,
        "max_power_kw": 10.0,
        "sensors": (
            BASIC_PV_SENSORS |
            PV3_SENSORS |
            BASIC_AC_SENSORS |
            GRID_SENSORS |
            POWER_FLOW_SENSORS |
            CONSUMPTION_SENSORS |
            ENERGY_SENSORS |
            ENERGY_BREAKDOWN_SENSORS |
            BATTERY_SENSORS |
            BMS_SENSORS |
            TEMPERATURE_SENSORS |
            STATUS_SENSORS
        ),
    },

    # SPH V2.01 VPP Protocol
    "sph_3000_6000_v201": {
        "name": "SPH Series 3-6kW",
        "description": "Single-phase hybrid inverter with battery (3-6kW) and VPP Protocol V2.01",
        "register_map": "SPH_3000_6000_V201",
        "phases": 1,
        "has_pv3": False,
        "has_battery": True,
        "max_power_kw": 6.0,
        "protocol_version": "v2.01",
        "sensors": (
            BASIC_PV_SENSORS |
            BASIC_AC_SENSORS |
            GRID_SENSORS |
            POWER_FLOW_SENSORS |
            CONSUMPTION_SENSORS |
            ENERGY_SENSORS |
            ENERGY_BREAKDOWN_SENSORS |
            BATTERY_SENSORS |
            TEMPERATURE_SENSORS |
            STATUS_SENSORS
        ),
    },

    "sph_7000_10000_v201": {
        "name": "SPH Series 7-10kW",
        "description": "Single-phase hybrid inverter with battery (7-10kW) and VPP Protocol V2.01",
        "register_map": "SPH_7000_10000_V201",
        "phases": 1,
        "has_pv3": True,  # 7-10kW models have 3 PV strings (registers 11-14)
        "has_battery": True,
        "max_power_kw": 10.0,
        "protocol_version": "v2.01",
        "sensors": (
            BASIC_PV_SENSORS |
            PV3_SENSORS |  # 7-10kW models have 3 PV strings
            BASIC_AC_SENSORS |
            GRID_SENSORS |
            POWER_FLOW_SENSORS |
            CONSUMPTION_SENSORS |
            ENERGY_SENSORS |
            ENERGY_BREAKDOWN_SENSORS |
            BATTERY_SENSORS |
            TEMPERATURE_SENSORS |
            STATUS_SENSORS
        ),
    },

    # ========================================================================
    # SPH TL3 SERIES - Hybrid Storage (Three Phase with Battery)
    # ========================================================================
    
    "sph_tl3_3000_10000": {
        "name": "SPH-TL3 Series 3000-10000",
        "description": "Hybrid 3-phase inverter with battery storage (3-10kW)",
        "register_map": "SPH_TL3_3000_10000",
        "phases": 3,
        "has_pv3": False,
        "has_battery": True,
        "max_power_kw": 10.0,
        "sensors": (
            BASIC_PV_SENSORS |
            THREE_PHASE_SENSORS |
            GRID_SENSORS |
            POWER_FLOW_SENSORS |
            CONSUMPTION_SENSORS |
            ENERGY_SENSORS |
            ENERGY_BREAKDOWN_SENSORS |
            BATTERY_SENSORS |
            TEMPERATURE_SENSORS |
            STATUS_SENSORS
        ),
    },

    # SPH-TL3 V2.01 VPP Protocol
    "sph_tl3_3000_10000_v201": {
        "name": "SPH-TL3 Series 3-10kW",
        "description": "Hybrid 3-phase inverter with battery (3-10kW) and VPP Protocol V2.01",
        "register_map": "SPH_TL3_3000_10000_V201",
        "phases": 3,
        "has_pv3": False,
        "has_battery": True,
        "max_power_kw": 10.0,
        "protocol_version": "v2.01",
        "sensors": (
            BASIC_PV_SENSORS |
            THREE_PHASE_SENSORS |
            GRID_SENSORS |
            POWER_FLOW_SENSORS |
            CONSUMPTION_SENSORS |
            ENERGY_SENSORS |
            ENERGY_BREAKDOWN_SENSORS |
            BATTERY_SENSORS |
            TEMPERATURE_SENSORS |
            STATUS_SENSORS
        ),
    },

    # ========================================================================
    # SPF SERIES - Off-Grid Storage (Battery with AC Input/Output)
    # ========================================================================

    "spf_3000_6000_es_plus": {
        "name": "SPF 3000-6000 ES PLUS",
        "description": "Off-grid inverter with battery storage and AC charging (3-6kW)",
        "register_map": "SPF_3000_6000_ES_PLUS",
        "phases": 1,
        "has_pv3": False,
        "has_battery": True,
        "max_power_kw": 6.0,
        "sensors": (
            BASIC_PV_SENSORS |
            BASIC_AC_SENSORS |
            ENERGY_SENSORS |
            ENERGY_BREAKDOWN_SENSORS |
            BATTERY_SENSORS |
            TEMPERATURE_SENSORS |
            STATUS_SENSORS |
            SPF_OFFGRID_SENSORS
        ),
    },

    # ========================================================================
    # MOD SERIES - Modular Three Phase Hybrid
    # ========================================================================

    "mod_6000_15000tl3_x": {
        "name": "MOD 6000-15000TL3-X (Grid-Tied)",
        "description": "Modular three-phase grid-tied inverter without battery (6-15kW)",
        "register_map": "MOD_6000_15000TL3_X",
        "phases": 3,
        "has_pv3": True,
        "has_battery": False,
        "max_power_kw": 15.0,
        "sensors": (
            BASIC_PV_SENSORS |
            PV3_SENSORS |
            THREE_PHASE_SENSORS |
            ENERGY_SENSORS |
            TEMPERATURE_SENSORS |
            STATUS_SENSORS
        ),
    },

    "mod_6000_15000tl3_xh": {
        "name": "MOD 6000-15000TL3-XH (Hybrid)",
        "description": "Modular three-phase hybrid inverter with battery (6-15kW)",
        "register_map": "MOD_6000_15000TL3_XH",
        "phases": 3,
        "has_pv3": True,
        "has_battery": True,
        "max_power_kw": 15.0,
        "sensors": (
            BASIC_PV_SENSORS |
            PV3_SENSORS |
            THREE_PHASE_SENSORS |
            GRID_SENSORS |
            POWER_FLOW_SENSORS |
            CONSUMPTION_SENSORS |
            ENERGY_SENSORS |
            ENERGY_BREAKDOWN_SENSORS |
            BATTERY_SENSORS |
            TEMPERATURE_SENSORS |
            STATUS_SENSORS
        ),
    },

    "mod_6000_15000tl3_xh_v201": {
        "name": "MOD 6000-15000TL3-XH",
        "description": "Modular three-phase hybrid with VPP Protocol V2.01 (6-15kW)",
        "register_map": "MOD_6000_15000TL3_XH",  # Same map, already includes V2.01 registers
        "protocol_version": "v2.01",
        "phases": 3,
        "has_pv3": True,
        "has_battery": True,
        "max_power_kw": 15.0,
        "sensors": (
            BASIC_PV_SENSORS |
            PV3_SENSORS |
            THREE_PHASE_SENSORS |
            GRID_SENSORS |
            POWER_FLOW_SENSORS |
            CONSUMPTION_SENSORS |
            ENERGY_SENSORS |
            ENERGY_BREAKDOWN_SENSORS |
            BATTERY_SENSORS |
            TEMPERATURE_SENSORS |
            STATUS_SENSORS
        ),
    },

    # ========================================================================
    # WIT SERIES - Three-Phase Hybrid with Advanced Storage
    # ========================================================================

    "wit_4000_15000tl3": {
        "name": "WIT 4-15kW Hybrid",
        "description": "Three-phase hybrid inverter with battery and UPS backup (4-15kW)",
        "register_map": "WIT_4000_15000TL3",
        "phases": 3,
        "has_pv3": False,  # Standard 2 PV strings
        "has_battery": True,
        "max_power_kw": 15.0,
        "protocol_version": "v2.02",  # VPP Protocol V2.02 (register 30099 = 202)
        "dtc_code": 5603,  # Device Type Code from register 30000
        "sensors": (
            BASIC_PV_SENSORS |
            BASIC_AC_SENSORS |
            THREE_PHASE_SENSORS |
            SYSTEM_OUTPUT_SENSORS |
            GRID_SENSORS |
            POWER_FLOW_SENSORS |
            CONSUMPTION_SENSORS |
            ENERGY_SENSORS |
            ENERGY_BREAKDOWN_SENSORS |
            BATTERY_SENSORS |
            TEMPERATURE_SENSORS |
            STATUS_SENSORS
        ),
    },
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

# User-friendly profile names (hides protocol versions and technical details)
PROFILE_DISPLAY_NAMES = {
    # Single-Phase Grid-Tied
    "MIC (0.6-3.3kW)": {
        "base": "mic_600_3300tl_x",
        "v201": "mic_600_3300tl_x_v201",
        "description": "Micro inverter, 1 PV string",
    },
    "MIN (3-6kW)": {
        "base": "min_3000_6000_tl_x",
        "v201": "min_3000_6000_tl_x_v201",
        "description": "Grid-tied, 2 PV strings",
    },
    "MIN (7-10kW)": {
        "base": "min_7000_10000_tl_x",
        "v201": "min_7000_10000_tl_x_v201",
        "description": "Grid-tied, 3 PV strings",
    },

    # Single-Phase Hybrid
    "SPH (3-6kW)": {
        "base": "sph_3000_6000",
        "v201": "sph_3000_6000_v201",
        "description": "Hybrid with battery, 2 PV strings",
    },
    "SPH (7-10kW)": {
        "base": "sph_7000_10000",
        "v201": "sph_7000_10000_v201",
        "description": "Hybrid with battery, 3 PV strings",
    },
    "SPH/SPM HU (8-10kW)": {
        "base": "sph_8000_10000_hu",
        "v201": "sph_8000_10000_hu",  # HU only has one profile
        "description": "Hybrid with BMS monitoring, 3 PV strings",
    },
    "MIN TL-XH (3-10kW)": {
        "base": "min_tl_xh_3000_10000_v201",  # Only V2.01 available
        "v201": "min_tl_xh_3000_10000_v201",
        "description": "MIN hybrid with battery, DTC 5100",
    },

    # Three-Phase Grid-Tied
    "MID (15-25kW)": {
        "base": "mid_15000_25000tl3_x",
        "v201": "mid_15000_25000tl3_x_v201",
        "description": "Three-phase grid-tied",
    },

    # Three-Phase Hybrid
    "MOD Grid-Tied (6-15kW)": {
        "base": "mod_6000_15000tl3_x",
        "v201": "mod_6000_15000tl3_x",  # Only one variant
        "description": "Three-phase grid-tied (no battery)",
    },
    "MOD Hybrid (6-15kW)": {
        "base": "mod_6000_15000tl3_xh",
        "v201": "mod_6000_15000tl3_xh_v201",
        "description": "Three-phase hybrid with battery",
    },
    "SPH-TL3 (3-10kW)": {
        "base": "sph_tl3_3000_10000",
        "v201": "sph_tl3_3000_10000_v201",
        "description": "Three-phase hybrid with battery",
    },
    "WIT (4-15kW)": {
        "base": "wit_4000_15000tl3",
        "v201": "wit_4000_15000tl3",  # Only one variant
        "description": "Three-phase hybrid with advanced storage",
    },

    # Off-Grid
    "SPF (3-6kW)": {
        "base": "spf_3000_6000_es_plus",
        "v201": "spf_3000_6000_es_plus",  # Only one variant
        "description": "Off-grid with battery",
    },
}


def get_profile(series: str):
    """Get inverter profile by series name."""
    return INVERTER_PROFILES.get(series, INVERTER_PROFILES["min_7000_10000_tl_x"])


def get_available_profiles(legacy_only: bool = False, friendly_names: bool = True) -> Dict[str, str]:
    """Get dict of available profiles for UI selection.

    Args:
        legacy_only: If True, exclude V2.01 profiles (for manual selection after failed auto-detection)
        friendly_names: If True, return user-friendly names. If False, return technical profile IDs.

    Returns:
        Dict mapping display name to profile ID (if friendly_names=True)
        or profile ID to display name (if friendly_names=False)
    """
    if friendly_names:
        # Return user-friendly names in alphabetical order
        profiles = {}
        for display_name in sorted(PROFILE_DISPLAY_NAMES.keys()):
            profile_info = PROFILE_DISPLAY_NAMES[display_name]
            # Use base profile for legacy-only, otherwise use v201 as default
            if legacy_only:
                profile_id = profile_info["base"]
            else:
                # Prefer v201 if available and different from base
                profile_id = profile_info["v201"]

            profiles[display_name] = profile_id

        return profiles
    else:
        # Return old format (technical profile IDs)
        profiles = {}
        for series, profile in INVERTER_PROFILES.items():
            # Filter out V2.01 profiles if legacy_only is True
            if legacy_only and '_v201' in series:
                continue
            profiles[series] = profile["name"]
        return profiles


def resolve_profile_selection(display_name: str, supports_v201: bool = True) -> str:
    """Resolve user-friendly profile selection to actual profile ID.

    Args:
        display_name: User-friendly profile name
        supports_v201: Whether inverter supports VPP V2.01 protocol

    Returns:
        Actual profile ID to use
    """
    if display_name in PROFILE_DISPLAY_NAMES:
        profile_info = PROFILE_DISPLAY_NAMES[display_name]
        if supports_v201:
            return profile_info["v201"]
        else:
            return profile_info["base"]

    # Fallback: if it's already a profile ID, return as-is
    if display_name in INVERTER_PROFILES:
        return display_name

    # Default fallback
    return "min_7000_10000_tl_x"


def get_display_name_for_profile(profile_id: str) -> str:
    """Get user-friendly display name for a profile ID.

    Args:
        profile_id: Technical profile ID

    Returns:
        User-friendly display name from profile's 'name' field
    """
    # Use the profile's 'name' field directly (e.g., "SPH/SPM 8000-10000TL-HU")
    profile = INVERTER_PROFILES.get(profile_id)
    if profile:
        return profile["name"]

    # Fallback: return the profile_id as-is if not found
    return profile_id


def get_sensors_for_profile(series: str) -> Set[str]:
    """Get available sensors for a profile."""
    profile = get_profile(series)
    return profile.get("sensors", set())
