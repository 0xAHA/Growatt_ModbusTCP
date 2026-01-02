# Release Notes - v0.1.0

## Multi-Device Architecture & Automatic Grid Orientation Detection

This release brings major improvements to device organization and automatic grid power configuration, along with important bug fixes.

---

## ✨ New Features

### 🏗️ Multi-Device Architecture

Sensors are now organized into **logical devices** for better organization:

- **Inverter** (parent device)
  - System health, status, fault codes
  - Temperatures (inverter, IPM, boost)
  - Connectivity sensor

- **Solar**
  - PV inputs (voltage, current, power per string)
  - AC output (single-phase/three-phase)
  - Energy production totals
  - Self-consumption percentage

- **Grid**
  - Grid power (bidirectional)
  - Import/export power
  - Grid energy totals

- **Load**
  - House consumption
  - Power to load
  - Load energy totals

- **Battery** (conditional - only if battery detected)
  - Battery voltage, current, power, SOC
  - Battery temperature
  - Charge/discharge power and energy
  - Priority mode

**Entity Categories:**
- Main sensors shown prominently
- Diagnostic sensors in separate tab (voltages, currents, temperatures)
- Config entities (controls) hidden by default

**Migration:**
- ✅ **Fully automatic** - Existing installations upgrade seamlessly
- ✅ **Entity IDs preserved** - All dashboards and automations continue working
- ✅ **No manual action required** - Migration happens on integration reload

---

### 🎯 Automatic Grid Orientation Detection

The integration now **automatically detects** the correct grid power sign convention!

**During Initial Setup:**
- Automatically detects if your inverter follows IEC 61850 or HA convention
- Applies correct "Invert Grid Power" setting automatically
- Shows notification with detection result
- Falls back gracefully if solar isn't producing

**Detection Service:**
```yaml
service: growatt_modbus.detect_grid_orientation
```

**Features:**
- Analyzes current power flow to determine convention
- Works with just **100W export** (down from 500W - much more practical!)
- Shows persistent notification with:
  - Detection result and reasoning
  - Current measurements
  - Recommended setting
  - Step-by-step configuration instructions

**Documentation:**
- Comprehensive README section explaining IEC 61850 vs HA conventions
- Why the difference exists
- What sensors are affected
- When to enable/disable inversion

---

### 🌅 Stale Daily Totals Debouncing

Fixes issue where inverters report yesterday's totals when waking up in the morning.

**Problem:**
- Inverters keep previous day totals in volatile memory
- When powering on at sunrise, briefly report yesterday's values
- Causes false spikes in energy dashboards

**Solution:**
- Detects when inverter comes online on new day
- 15-minute debounce window filters stale readings
- Resets daily totals to 0 when stale data detected
- Automatic recovery after window expires

---

### ⚙️ Default Options on Setup

Integration now sets proper defaults during initial setup:

- **Scan interval:** 60 seconds (previously unset, fell back to 30s)
- **Offline scan interval:** 300 seconds (5 minutes)
- **Timeout:** 10 seconds
- **Invert grid power:** Auto-detected or False

No more need to manually configure polling rate!

---

## 🐛 Bug Fixes

### Critical: Grid Export/Import Sensors

**Fixed a critical bug** in `grid_export_power` and `grid_import_power` sensors when "Invert Grid Power" is enabled.

**The Problem:**
- Export sensor used `max(0, grid_power)` - wrong after inversion
- Import sensor used `max(0, -grid_power)` - wrong after inversion
- After inversion: negative = export, positive = import
- Logic was backwards, showing swapped values

**The Fix:**
- Export sensor now correctly uses `max(0, -grid_power)` after inversion
- Import sensor now correctly uses `max(0, grid_power)` after inversion
- Export/import sensors now show correct unsigned values regardless of inversion setting

### Critical: Battery Discharge Power Sign Convention

**Fixed a critical bug** in TL-XH/SPH VPP 2.01 profiles where battery discharge power was misinterpreted as unsigned.

**The Problem:**
- Register 31200-31201 returns **signed** battery power per VPP Protocol V2.01 spec
- Positive = charging, Negative = discharging
- Profile was missing `'signed': True` flag on register 31201
- Code interpreted -1238W discharge as 4294954916W (huge positive value!)
- Affected all TL-XH, SPH, SPH-TL3 users with VPP 2.01 inverters

**The Fix:**
- Added `'signed': True` flag to register 31201 in all affected profiles
- Renamed `battery_discharge_power` → `battery_power` (matches VPP spec)
- Battery power now correctly shows negative when discharging
- Updated profiles: TL_XH, MIN_TL_XH, SPH_3000_6000, SPH_7000_10000, SPH_TL3

**Bonus: Added Legacy Battery Power Registers (3178-3181)**

For TL-XH models that provide both register sets, added optional legacy registers:

- **`battery_discharge_power`** (3178-3179) - Unsigned discharge power (always positive)
- **`battery_charge_power`** (3180-3181) - Unsigned charge power (always positive)
- **`battery_power`** (31200-31201) - Signed VPP power (negative=discharge, positive=charge)

**Benefits:**
- Users can compare both values to validate correct operation
- Legacy registers easier to understand (always positive)
- Users can disable entities they don't need
- Provides redundancy and fallback options

---

## ⚠️ Breaking Changes / Action Required

### IMPORTANT: Verify Grid Power Settings

After updating to v0.1.0, **verify your grid power configuration** using the detection service:

**Step 1: Run Detection Service**

During daytime when solar is producing (> 1000W) and exporting (> 100W):

```yaml
service: growatt_modbus.detect_grid_orientation
```

**Step 2: Review Recommendation**

The service will analyze your setup and show a notification with:
- Your current power flow measurements
- Detected grid power convention (IEC 61850 or HA format)
- Whether "Invert Grid Power" should be ON or OFF
- Current vs recommended setting

**Step 3: Update if Needed**

If the recommendation differs from your current setting:

1. Go to **Settings** → **Devices & Services** → **Growatt Modbus**
2. Click **Configure** on your integration
3. Toggle **Invert Grid Power** to match recommendation
4. Click **Submit** and reload integration

**Why This is Needed:**

Previous versions had a bug in export/import sensors when inversion was enabled. The bug is now fixed, but you should verify your current setting is correct to ensure accurate power flow visualization.

**What's NOT Affected:**
- ✅ Entity IDs unchanged - All dashboards continue working
- ✅ Energy totals always correct (never affected by inversion)
- ✅ Automations continue working
- ✅ Only instantaneous grid power sensors affected

---

## 📦 Commits Since v0.0.8

Full list of changes:

- `c0e0949` - Clean up battery power entity naming - remove _legacy and _low suffixes
- `0913ecd` - Add legacy battery power registers (3178-3181) to MIN TL-XH profile
- `c985a23` - Fix battery discharge power sign convention for TL-XH/SPH VPP 2.01 profiles
- `635d5c1` - Prepare release v0.0.9
- `a7f5a78` - Add persistent notification for grid orientation detection results during setup
- `e0b559c` - Reduce grid orientation detection export threshold from 500W to 100W
- `8a76782` - Add automatic grid orientation detection during initial setup
- `03ad84f` - Fix grid export/import sensors and add automatic orientation detection
- `68e42e5` - Debounce stale daily totals when inverter wakes up in the morning
- `ed4ec0e` - Set default options during initial setup with 60-second scan interval
- `8dd8f82` - Move controls into respective devices instead of separate Controls device
- `79438e7` - Implement multi-device architecture with automatic migration

---

## 📚 Documentation Updates

- Added comprehensive grid power sign convention section to README
- Documented IEC 61850 vs Home Assistant conventions
- Added usage instructions for detection service
- Updated "What's New" section for v0.1.0
- Added battery power entity documentation
- Updated RELEASENOTES.md with battery power bug fix details

---

## 🙏 Acknowledgments

Thank you to all users who reported issues and provided feedback! Special thanks for:
- Grid power sign convention feedback
- Battery discharge power sign convention bug report
- Morning energy spike reports
- Device organization suggestions

---

## 🔗 Links

- **Full Changelog:** https://github.com/0xAHA/Growatt_ModbusTCP/compare/v0.0.8...v0.1.0
- **Issues:** https://github.com/0xAHA/Growatt_ModbusTCP/issues
- **Documentation:** https://github.com/0xAHA/Growatt_ModbusTCP/blob/main/README.md

---

## Installation / Update

### HACS (Custom Repository)

1. Go to HACS → Integrations
2. Click "Growatt Modbus"
3. Click "Update" (or "Download" for new installations)
4. Restart Home Assistant
5. **Run detection service** to verify grid power settings (existing users)

### Manual Installation

1. Download `growatt_modbus.zip` from release assets
2. Extract to `custom_components/growatt_modbus/`
3. Restart Home Assistant
4. **Run detection service** to verify grid power settings (existing users)

---

**Enjoy the new multi-device organization and automatic grid orientation detection!** 🎉
