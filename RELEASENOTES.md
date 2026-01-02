# Release Notes - v0.1.1

## WIT Battery Sensors & Control Device Organization

This release addresses **GitHub Issue #75** - WIT inverters showing minimal battery sensors. WIT users now get the complete VPP battery monitoring suite with power and energy tracking. Additionally, control entities are now properly organized under their logical devices.

---

## ✨ New Features

### WIT Profile: Complete VPP Battery Sensor Suite (Issue #75)

**Added complete VPP V2.02 battery power and energy registers** to WIT 4-15kW profile.

**The Problem:**
- WIT profile only had basic battery registers (voltage, current, SOC, SOH, temperature)
- Missing VPP battery power registers (31200-31205)
- Missing battery energy registers (31206-31213)
- Battery power was calculated from V×I instead of using dedicated registers
- Battery energy sensors (charge/discharge today/total) didn't exist
- **Users reported only 4 battery sensors visible instead of full battery monitoring suite**

**The Fix:**
- Added VPP battery power registers:
  - 31200-31201: `battery_power` (signed, positive=charge, negative=discharge)
  - 31202-31203: `charge_power` (unsigned charge power)
  - 31204-31205: `discharge_power` (unsigned discharge power)
- Added VPP battery energy registers:
  - 31206-31207: `charge_energy_today`
  - 31208-31209: `charge_energy_total`
  - 31210-31211: `discharge_energy_today`
  - 31212-31213: `discharge_energy_total`
- Added VPP battery state registers for redundancy:
  - 31214: `battery_voltage_vpp` (maps to 8034)
  - 31215: `battery_current_vpp` (maps to 8035)
  - 31217: `battery_soc_vpp` (maps to 8093)
  - 31222: `battery_temp_vpp` (maps to battery_temp)

**Benefits:**
- Battery power now read from dedicated inverter registers (more accurate than V×I calculation)
- Battery charge/discharge energy tracking now available
- Complete battery monitoring suite with all expected sensors
- Consistent with other VPP-enabled profiles (SPH, TL-XH, MOD)
- **Resolves:** GitHub Issue #75

**Validated:** Register mapping confirmed against real WIT inverter VPP 2.02 register dump

---

### Control Entity Device Organization

**Controls now appear under their logical device** instead of a separate Controls device.

**Implementation:**
- Added `get_device_type_for_control()` function to automatically map controls to devices
- Battery controls → Battery device (Configuration section)
  - Examples: `battery_charge_stop_soc`, `battery_discharge_stop_soc`, `bms_enable`, `battery_charge_power_limit`, `ac_charge_power_rate`
- Grid controls → Grid device (Configuration section)
  - Examples: `export_limit_mode`, `export_limit_power`, `vpp_enable`, `ongrid_offgrid_mode`, `phase_mode`
- Solar/PV controls → Solar device (Configuration section)
  - Examples: `pid_working_mode`, `optimizer_count_set`
- Load controls → Load device (Configuration section)
  - Examples: `demand_discharge_limit`, `demand_charge_limit`
- System controls → Inverter device (Configuration section)
  - Examples: `active_power_rate`, `time programming`, `operation_mode`

**All controls:**
- Hidden by default (EntityCategory.CONFIG)
- Appear when expanding the **Configuration** section of their device
- No separate Controls device cluttering the UI

---

### Active Power Rate Control (Register 3)

**Added Active Power Rate control** for inverter output power limiting.

**Details:**
- Register: 3 (holding register)
- Type: Number entity (slider)
- Range: 0-100%
- Function: Limits maximum inverter output power
- Device: Inverter device → Configuration section
- Availability: MIN series (all models), and other profiles with register 3

**Tested on:** MIN-10000TL-X hardware

---

## 🔧 Enhancements

- **Control device mapping infrastructure** - Future controls will automatically be assigned to correct devices
- **Device-based organization** - All controls now properly categorized under their functional device
- **Validated WIT VPP registers** - Register dump analysis confirms correct mapping for VPP V2.02 protocol

---

## 📝 Technical Details

### WIT Profile Currently Implemented Controls

The WIT profile has extensive control registers defined in `holding_registers`, but only the following are currently exposed as entities:

**Currently Available:**
- None specific to WIT (infrastructure is in place for future implementation)

**Available on models with these registers:**
- `export_limit_mode` (122) - Available on: SPH, MOD, TL-XH, some MIN V2.01
- `export_limit_power` (123) - Available on: SPH, MOD, TL-XH, some MIN V2.01
- `active_power_rate` (3) - Available on: MIN series, and other profiles with register 3

### WIT Future Control Potential

The WIT profile defines 70+ holding registers with `'access': 'RW'` that could be exposed as controls:

**Battery Controls (would appear in Battery device):**
- Battery type, charge/discharge voltage/current limits, capacity
- Battery SOC limits (charge/discharge stop SOC)
- BMS enable/disable
- Battery charge/discharge power limits
- AC charge power rate

**Grid Controls (would appear in Grid device):**
- On-grid/off-grid phase mode
- On-grid/off-grid switching mode
- VPP enable & active power settings
- AC charge enable
- Off-grid voltage/frequency settings
- Anti-backflow configuration

**System Controls (would appear in Inverter device):**
- Operation mode (Hybrid/Economy/UPS)
- Time-of-use programming (6 time slots)
- Demand management
- Parallel operation settings

**Note:** These controls are **not yet implemented** but the infrastructure is in place to add them in future releases.

---

## 🐛 Bug Fixes

None - This is a feature and enhancement release.

---

## 📦 Commits

- Add VPP battery power and energy registers to WIT profile
- Update v0.1.0 documentation for WIT battery sensors enhancement
- Add control entity device mapping to organize controls by device type
- Add Active Power Rate control for MIN series testing

---

## 🙏 Acknowledgments

Special thanks to WIT users who reported Issue #75 and provided register dump data for validation.

---

## 📖 Migration Notes

**No breaking changes** - This is a drop-in upgrade.

**After Upgrading:**
1. WIT users will see new battery sensors appear automatically
2. Controls will move from separate device to their logical device's Configuration section
3. Entity IDs remain unchanged
4. No manual configuration required

---

## 🔗 Related Issues

- Closes: #75 - WIT showing minimal battery sensors

---
