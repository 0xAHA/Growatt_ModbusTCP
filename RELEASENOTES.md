# Release Notes - v0.1.2

## Critical WIT Battery Register Fixes

This release fixes critical battery sensor issues on WIT 8K HU and other WIT inverters. Battery power was stuck at 2-3W, and battery energy values were incorrect or showing astronomical values. This was caused by incorrect register mapping that didn't match the official VPP 2.01 protocol specification.

---

## 🐛 Critical Bug Fixes

### WIT Battery Power Stuck at 2-3W

**Fixed battery power register naming mismatch** that prevented battery power from being read correctly.

**The Problem:**
- Battery power sensor stuck at 2-3W regardless of actual charging/discharging
- Worked correctly in v0.1.0, broke in v0.1.1
- Register 31201 was named `battery_power` instead of `battery_power_low`
- Coordinator specifically searches for `battery_power_low` (line 944 of growatt_modbus.py)
- Naming mismatch caused coordinator to skip battery power reading logic
- Fell through to fallback logic that tried to read separate charge_power_low/discharge_power_low registers (which didn't exist after v0.1.1 register changes)
- Battery power defaulted to near-zero

**The Fix:**
- Renamed register 31201 from `battery_power` to `battery_power_low`
- Matches naming convention used in MOD profile and coordinator expectations
- Coordinator now properly:
  1. Finds `battery_power_low` register at 31201
  2. Reads signed INT32 value from 31200-31201 pair
  3. Splits into `charge_power` (positive values) and `discharge_power` (negative values)
  4. Battery power sensor displays correctly with realistic charging/discharging values

**Impact:** Battery power sensor now shows accurate real-time charging/discharging power.

---

### WIT Battery Energy Registers Corrected per VPP 2.01 Specification

**Comprehensive remapping of battery energy and power registers** based on official VPP 2.01 protocol documentation.

**The Problem:**
- Registers 31202-31213 were incorrectly mapped in v0.1.1
- Users reported astronomical battery charge energy values (2895.2 kWh, 7238.0 kWh)
- Discharge energy showed incorrect values (7545.60 kWh instead of expected 15.7 kWh)
- Some charge/discharge values appeared swapped
- Root cause: Register mapping didn't match official VPP 2.01 specification

**Analysis of Official VPP 2.01 Protocol Documentation:**

According to official VPP 2.01 specification:
- **31202-31203:** Daily charge of battery (charge_energy_today)
- **31204-31205:** Cumulative charge of battery (charge_energy_total)
- **31206-31207:** Daily discharge capacity of battery (discharge_energy_today)
- **31208-31209:** Cumulative discharge of battery (discharge_energy_total)
- **31210-31211:** Maximum allowable charging POWER of battery (power limit, NOT energy!)
- **31212-31213:** Maximum allowable discharge POWER of battery (power limit, NOT energy!)

**Previous Incorrect Mapping (v0.1.1):**
```python
31202-31203: charge_power          # ❌ WRONG - actually charge_energy_today
31204-31205: discharge_power       # ❌ WRONG - actually charge_energy_total
31206-31207: discharge_energy_today # ✅ CORRECT
31208-31209: discharge_energy_total # ✅ CORRECT
31210-31211: charge_energy_today   # ❌ WRONG - actually max_charge_power limit
31212-31213: charge_energy_total   # ❌ WRONG - actually max_discharge_power limit
```

**Corrected Mapping (v0.1.2) per VPP 2.01:**
```python
# Battery Energy Registers
31202-31203: charge_energy_today    # ✅ Daily charge of battery
31204-31205: charge_energy_total    # ✅ Cumulative charge of battery
31206-31207: discharge_energy_today # ✅ Daily discharge capacity of battery
31208-31209: discharge_energy_total # ✅ Cumulative discharge of battery

# Battery Power Limit Registers (BMS-controlled maximums)
31210-31211: max_charge_power       # ✅ Maximum allowable charging power (LIMIT)
31212-31213: max_discharge_power    # ✅ Maximum allowable discharge power (LIMIT)
```

**Why Users Saw Astronomical Values:**

The "energy" values of 2895.2 kWh and 7238.0 kWh were actually **maximum power limits** (2895.2W, 7238.0W) from registers 31210-31213. These are BMS-configured power capacity limits, not energy counters. When incorrectly labeled as energy, they appeared as absurdly high kWh values.

**Validation:**

Register mapping validated against:
- Official VPP 2.01 protocol specification document
- Real WIT 8K HU inverter register scan CSV data
- Growatt OSS dashboard comparison (values now match correctly)

**Impact:**
- ✅ Battery charge energy (today/total) now reads from correct registers 31202-31205
- ✅ Battery discharge energy (today/total) confirmed correct at 31206-31209
- ✅ Battery energy values now match Growatt OSS dashboard
- ✅ No more astronomical kWh values
- ✅ New sensors: max_charge_power and max_discharge_power (BMS limits)

---

## 🔧 Register Changes Summary

**WIT Profile VPP Battery Registers (31200-31213):**

| Register | v0.1.1 (Incorrect) | v0.1.2 (Corrected per VPP 2.01) |
|----------|-------------------|----------------------------------|
| 31200-31201 | `battery_power` | `battery_power_low` (signed INT32) |
| 31202-31203 | `charge_power` | `charge_energy_today` |
| 31204-31205 | `discharge_power` | `charge_energy_total` |
| 31206-31207 | `discharge_energy_today` | `discharge_energy_today` (✓ unchanged) |
| 31208-31209 | `discharge_energy_total` | `discharge_energy_total` (✓ unchanged) |
| 31210-31211 | `charge_energy_today` | `max_charge_power` (BMS limit) |
| 31212-31213 | `charge_energy_total` | `max_discharge_power` (BMS limit) |

---

## ✅ Resolved Issues

**For WIT 8K HU and other WIT inverters:**
- ✅ Battery power sensor no longer stuck at 2-3W
- ✅ Battery charge energy shows correct values from dedicated registers
- ✅ Battery discharge energy values match Growatt OSS dashboard
- ✅ No more astronomical energy values (2895 kWh, 7238 kWh)
- ✅ Charge/discharge power correctly derived from signed battery_power register
- ✅ VPP 2.01 protocol compliance verified

---

## 📝 Technical Notes

**Register Naming Convention:**
- 32-bit registers use `_high` and `_low` suffixes
- Low register contains the combined value after pairing
- Coordinator searches for `_low` suffix when reading combined registers
- **All profiles must use consistent `_low` naming for coordinator compatibility**

**VPP Protocol Compliance:**
- WIT profile now fully compliant with VPP Protocol V2.01 specification
- Register comments include VPP specification item numbers (65-71)
- Future updates will reference official VPP documentation for validation

---

## 🙏 Credits

Special thanks to the WIT 8K HU user who:
- Reported detailed battery sensor issues with screenshots
- Provided original register scan CSV data from VPP profile contributor
- Compared integration values against Growatt OSS dashboard
- Helped validate fixes against real hardware

---

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
