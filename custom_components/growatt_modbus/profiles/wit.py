"""
WIT Series - Three-Phase Hybrid Inverters with Advanced Storage
Based on legacy Growatt Modbus Protocol

WIT-specific notes:
- Input registers: 0–249, 8000–8086
- VPP / battery cluster data: 31200–31223 (HOLDING registers!)
"""

# WIT 4000–15000TL3 (3-phase hybrid, battery)
WIT_4000_15000TL3 = {
    "name": "WIT 4-15kW Hybrid",
    "description": "Three-phase hybrid inverter with battery and VPP",
    "notes": "WIT uses VPP holding registers for battery energy and control",

    # ==========================================================
    # INPUT REGISTERS (READ)
    # ==========================================================
    "input_registers": {
        # --- Status ---
        0: {"name": "inverter_status", "scale": 1},

        # --- PV total power (32-bit) ---
        1: {"name": "pv_total_power_high", "pair": 2},
        2: {"name": "pv_total_power_low", "pair": 1, "combined_scale": 0.1, "combined_unit": "W"},

        # --- AC output power (32-bit, signed) ---
        35: {"name": "ac_power_high", "pair": 36, "signed": True},
        36: {"name": "ac_power_low", "pair": 35, "signed": True,
             "combined_scale": 0.1, "combined_unit": "W"},

        # --- Frequency ---
        37: {"name": "ac_frequency", "scale": 0.01, "unit": "Hz"},

        # --- Temperatures ---
        93: {"name": "inverter_temp", "scale": 0.1, "unit": "°C", "signed": True},
        94: {"name": "ipm_temp", "scale": 0.1, "unit": "°C", "signed": True},
        95: {"name": "boost_temp", "scale": 0.1, "unit": "°C", "signed": True},

        # --- Battery basic block ---
        8034: {"name": "battery_voltage", "scale": 0.1, "unit": "V"},
        8035: {"name": "battery_current", "scale": 0.1, "unit": "A", "signed": True},
        8093: {"name": "battery_soc", "scale": 1, "unit": "%"},
        8094: {"name": "battery_soh", "scale": 1, "unit": "%"},
    },

    # ==========================================================
    # HOLDING REGISTERS (READ + WRITE)
    # ==========================================================
    "holding_registers": {

        # ------------------------------------------------------
        # ✅ WIT CONTROL – NÄMÄ TEKEE OHJAUKSEN TOIMIVAKSI
        # ------------------------------------------------------

        # Active power command (%)
        201: {
            "name": "active_power_rate",
            "scale": 1,
            "unit": "%",
            "access": "RW",
            "valid_range": (0, 100),
            "desc": "Active power command percent"
        },

        # Work mode
        202: {
            "name": "work_mode",
            "scale": 1,
            "access": "RW",
            "values": {
                0: "Standby",
                1: "Charge",
                2: "Discharge"
            },
            "desc": "Work mode control"
        },

        # Export limit (0 = zero export)
        203: {
            "name": "export_limit_w",
            "scale": 1,
            "unit": "W",
            "access": "RW",
            "valid_range": (0, 60000),
            "desc": "Export limit (0 = no export)"
        },

        # ------------------------------------------------------
        # 🔋 VPP BATTERY CLUSTER (READ-ONLY, BUT MUST BE HOLDING)
        # ------------------------------------------------------

        # Battery power (signed, 32-bit)
        31200: {"name": "battery_power_high", "pair": 31201},
        31201: {"name": "battery_power_low", "pair": 31200,
                "signed": True, "combined_scale": 1.0, "combined_unit": "W"},

        # Charge energy today
        31202: {"name": "charge_energy_today_high", "pair": 31203},
        31203: {"name": "charge_energy_today_low", "pair": 31202,
                 "combined_scale": 0.1, "combined_unit": "kWh"},

        # Charge energy total
        31204: {"name": "charge_energy_total_high", "pair": 31205},
        31205: {"name": "charge_energy_total_low", "pair": 31204,
                 "combined_scale": 0.1, "combined_unit": "kWh"},

        # Discharge energy today
        31206: {"name": "discharge_energy_today_high", "pair": 31207},
        31207: {"name": "discharge_energy_today_low", "pair": 31206,
                 "combined_scale": 0.1, "combined_unit": "kWh"},

        # Discharge energy total
        31208: {"name": "discharge_energy_total_high", "pair": 31209},
        31209: {"name": "discharge_energy_total_low", "pair": 31208,
                 "combined_scale": 0.1, "combined_unit": "kWh"},

        # Cluster state
        31214: {"name": "battery_voltage_vpp", "scale": 0.1, "unit": "V"},
        31215: {"name": "battery_current_vpp", "scale": 0.1, "unit": "A", "signed": True},
        31217: {"name": "battery_soc_vpp", "scale": 1, "unit": "%"},
        31222: {"name": "battery_temp_vpp", "scale": 0.1, "unit": "°C", "signed": True},
    }
}

# Export profile
WIT_REGISTER_MAPS = {
    "WIT_4000_15000TL3": WIT_4000_15000TL3
}
