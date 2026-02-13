# Release Notes

# Release Notes - v0.4.7

## 🐛 Bug Fix: SPF AC Charge/Discharge Energy Sensors

**Fixed:**
- SPF AC Charge Energy Today/Total sensors showing 0.00 (should show same values as Battery Charge sensors)
- SPF AC Discharge Energy Today/Total sensors showing 0.00 (registers 64-67)

---

### What's Fixed in v0.4.7:

#### 1. 🔧 Fixed SPF AC Charge/Discharge Energy Sensors

**Root Cause:** SPF uses different register names than WIT for the same energy measurements, causing "AC Charge/Discharge Energy" sensors to show 0.00 even though the data exists.

**Register Name Differences:**
- **WIT:** Uses `ac_charge_energy_*` and `ac_discharge_energy_*` register names
- **SPF:** Uses `charge_energy_*` (56-59) and `ac_discharge_energy_*` (64-67) register names
- Same data, different naming convention

**Affected sensors (now fixed):**
- `ac_charge_energy_today` - Now populated from SPF's `charge_energy_today` (registers 56-57)
- `ac_charge_energy_total` - Now populated from SPF's `charge_energy_total` (registers 58-59)
- `ac_discharge_energy_today` - Now reads from registers 64-65
- `ac_discharge_energy_total` - Now reads from registers 66-67

**The Fix:**
1. **AC Charge Energy**: SPF now populates BOTH `charge_energy_*` AND `ac_charge_energy_*` fields from the same registers (56-59)
2. **AC Discharge Energy**: Added missing register reading code for registers 64-67
3. **WIT compatibility**: WIT-specific register names still work for WIT inverters

**Impact:**
- ✅ SPF users will now see actual values in ALL "AC Charge/Discharge Energy" sensors
- ✅ "AC Charge Energy" sensors will match "Battery Charge" sensors (same data source)
- ✅ "AC Discharge Energy" sensors will show battery → load energy flow
- ✅ Complete energy tracking for SPF 6000 ES Plus and similar models

**What You'll See After Upgrade (SPF users):**
- "Battery Charge Today" = 0.80 kWh ✅ (working before)
- "AC Charge Energy Today" = 0.80 kWh ✅ (NOW FIXED - was 0.00)
- "Battery Charge Total" = 446.90 kWh ✅ (working before)
- "AC Charge Energy Total" = 446.90 kWh ✅ (NOW FIXED - was 0.00)
- "AC Discharge Energy Today" = actual value ✅ (NOW FIXED - was 0.00)
- "AC Discharge Energy Total" = actual value ✅ (NOW FIXED - was 0.00)

**Note:** Both "Battery Charge" and "AC Charge Energy" sensors track the same thing (grid/generator charging your battery) and will show identical values. This is normal - they're just different sensor names for the same SPF register data.

---

### Files Changed:
- `custom_components/growatt_modbus/growatt_modbus.py` - Added AC charge/discharge energy register mapping for SPF
- `custom_components/growatt_modbus/manifest.json` - Version bump to 0.4.7
- `README.md` - Version badge updated to 0.4.7
- `RELEASENOTES.md` - Updated with v0.4.7 changes

---

# Release Notes - v0.4.6

## 🐛 Bug Fix: SPF AC Discharge Energy Sensors (Partial Fix)

**Fixed:**
- SPF AC Discharge Energy Today/Total sensors showing 0.00 (registers 64-67)

**Note:** v0.4.6 only fixed AC Discharge Energy. AC Charge Energy still showed 0.00 and was fully fixed in v0.4.7.

---

# Release Notes - v0.4.5

## 🔥 CRITICAL Bug Fix: Serial Connection File Descriptor Leak

**Fixed:**
- **CRITICAL:** Serial connection file descriptor leak causing permanent integration failure after overnight offline periods

---

### What's Fixed in v0.4.5:

#### 1. 🔥 CRITICAL: Fixed Serial Connection File Descriptor Leak

**Root Cause:** When using USB-RS485 adapters (serial connection), failed connection attempts during offline periods (e.g., overnight when inverter is powered down) were not properly releasing the serial port file descriptor. Over hours of offline polling, hundreds of leaked file descriptors would accumulate until the system exhausted its limit.

**Symptoms:**
- Integration works fine initially
- Inverter goes offline (night time, powered down)
- After several hours, integration stops working completely
- Error in logs: `OSError: [Errno 24] No file descriptors available`
- Integration never recovers even when inverter comes back online
- **Inverter is actually online** (proven by Growatt cloud connectivity)
- Only fix is restarting Home Assistant

**Technical Details:**
The coordinator's `_fetch_data()` method had three critical flaws:
1. **No cleanup on failed connection** - When `connect()` failed, `disconnect()` was never called to release the serial port
2. **No cleanup before retry** - Each retry attempt would call `connect()` without first calling `disconnect()`, potentially creating multiple open file descriptors
3. **Silent exception handling** - Bare `except: pass` blocks hid disconnect failures

**Scenario Example:**
- Inverter offline 5pm-5am (12 hours)
- Offline polling every 300s = ~144 poll attempts
- Each attempt tries 3 connection retries = ~432 connection attempts
- Each leaked file descriptor accumulates
- At 5:12am when inverter wakes: errno 24 "No file descriptors available"
- Integration permanently broken until HA restart

**The Fix:**
1. **Always disconnect before connect** - Ensures clean state, prevents double-open
2. **Always disconnect after failed connect** - Releases file descriptors even on failure
3. **Proper error logging** - Replace bare `except: pass` with debug logging
4. **Connection state checking** - Skip `connect()` if already connected (prevents double-open)

**Files Changed:**
- `coordinator.py:482-537` - Added disconnect calls before/after every connect attempt
- `growatt_modbus.py:330-350` - Added `is_socket_open()` check to prevent double-connect
- `growatt_modbus.py:351-364` - Enhanced disconnect error logging with critical error detection

**Impact:**
- ✅ **ALL Serial/USB-RS485 users (ALL inverter models):** Integration now properly recovers from overnight offline periods
- ✅ **TCP users:** Not affected by the bug, but benefits from cleaner connection management
- ✅ **All inverter series (MIN/MID/MAX/MOD/SPH/SPF/WIT/MIX/SPA):** No more permanent failures when using serial connections
- ✅ **Logging:** Better visibility into connection lifecycle and resource leak issues

**Migration Notes:**
- No action required - fix is automatic
- If you experienced this issue, upgrade to v0.4.5 and restart Home Assistant once
- Monitor logs after upgrade - should see `Disconnected successfully` debug messages
- If you see `CRITICAL: File descriptor leak detected!` in logs after upgrade, please report the issue

---

### Files Changed:
- `custom_components/growatt_modbus/coordinator.py` - Fixed file descriptor leak in _fetch_data()
- `custom_components/growatt_modbus/growatt_modbus.py` - Enhanced connect/disconnect with leak prevention
- `custom_components/growatt_modbus/manifest.json` - Version bump to 0.4.5
- `RELEASENOTES.md` - Updated with v0.4.5 changes

---

# Release Notes - v0.4.4

## 🐛 Critical Bug Fixes: SPF Grid Sensors + Missing WIT Battery Sensors

**Fixed:**
1. SPF Grid device sensors (generator, grid voltage/frequency) showing zero values (Issue #145)
2. WIT battery sensors (SOH, BMS voltage, AC charge total) missing from v0.4.3 fix

---

### What's Fixed in v0.4.4:

#### 1. 🔧 Added Missing Generator Register Reading Code

**Root Cause:** Generator sensors (registers 92-97) were added to the SPF profile in v0.4.3, which made the sensors *appear* in Home Assistant, but the code to actually *read* these registers into the `GrowattData` object was never added. This caused all generator sensors to permanently show zero values.

**Affected sensors (now fixed):**
- `generator_power` (register 96) - Current generator power output
- `generator_voltage` (register 97) - Current generator voltage
- `generator_discharge_today` (registers 92-93) - Generator energy today
- `generator_discharge_total` (registers 94-95) - Generator lifetime energy

**The Fix:** Added register reading code in `read_all_data()` following the same pattern as other SPF sensors like `grid_voltage` and `ac_input_power`.

**Impact:**
- ✅ SPF 6000 ES Plus generator sensors now show correct values
- ✅ Grid device for SPF models now fully functional
- ✅ Other Grid sensors (`grid_voltage`, `grid_frequency`, `ac_input_power`) continue to work

#### 2. 📊 Enhanced Debug Logging for Troubleshooting

**Added comprehensive diagnostic logging:**
- Shows full register range being read (e.g., "Register range: 0-97")
- Logs when registers are not found in profile
- Shows raw cache values alongside scaled values
- Helps diagnose sensor value issues

**Example debug output:**
```
[SPF 3000-6000 ES PLUS] Register range: 0-97 (42 registers defined)
Reading base range (0-124)
Grid voltage from reg 20: 230.5 V (raw cache: 2305)
Generator power from reg 96: 1250 W (raw cache: 1250)
```

**Impact:**
- ✅ Easier troubleshooting for users and developers
- ✅ Clear visibility into which registers are being read
- ✅ Raw hardware values visible for validation

#### 3. 📝 Updated SPF Profile Documentation

**Updated register range note:**
- Changed from "Uses 0-88 register range" to "Uses 0-97 register range"
- Reflects addition of generator sensors at registers 92-97

#### 4. 🔧 Fixed Missing WIT Battery Sensors (Incomplete v0.4.3 Fix)

**Root Cause:** v0.4.3 claimed to fix missing dataclass fields but only added 3 WIT sensors (`extra_power_to_grid`, `extra_energy_today`, `extra_energy_total`). It **missed** 3 other WIT battery sensors that had the same issue.

**Missing WIT sensors (now fixed in v0.4.4):**
- `battery_soh` (register 8094) - Battery State of Health percentage
- `battery_voltage_bms` (register 8095) - BMS-reported voltage (more accurate than standard reading)
- `ac_charge_energy_total` (registers 8059-8060) - Total AC charge energy from grid

**The Complete Fix:**
1. Added missing dataclass fields to `GrowattData`
2. Added register reading code in `_read_battery_data()`
3. Updated comment to clarify `ac_charge_energy_today` is for both WIT and SPF

**Impact:**
- ✅ WIT users can now see Battery State of Health (SOH)
- ✅ WIT users can now see accurate BMS voltage reading
- ✅ WIT users can now see total AC charge energy counter
- ✅ Completes the v0.4.3 fix that was only partially implemented

**Note:** These sensors were defined in the profile and sensor.py since earlier releases, but v0.4.3's dataclass fix was incomplete.

---

### Migration Notes:

**No action required** - This is a bug fix release. Simply upgrade and the Grid device sensors will start showing correct values.

**For SPF users:**
- Generator sensors will now show actual values instead of zero
- If you previously dismissed Grid device sensors as "broken," they should now work
- Enable debug logging (see below) if you want to verify register reads

**For WIT users:**
- Battery SOH (State of Health) sensor will now appear and show correct values
- Battery Voltage BMS sensor will now appear (more accurate than standard voltage)
- AC Charge Energy Total sensor will now appear
- These sensors should have been working in v0.4.3 but were missed

**Debug logging setup** (optional, for troubleshooting):
```yaml
logger:
  default: info
  logs:
    custom_components.growatt_modbus: debug
```

---

### Files Changed:
- `custom_components/growatt_modbus/growatt_modbus.py` - Added SPF generator + WIT battery register reading code + enhanced debug logging + 3 missing dataclass fields
- `custom_components/growatt_modbus/profiles/spf.py` - Updated register range documentation
- `custom_components/growatt_modbus/manifest.json` - Version bump to 0.4.4
- `RELEASENOTES.md` - Updated with v0.4.4 changes

---

### Technical Details:

**Why did this happen?**

v0.4.3 fixed the missing dataclass fields, which made the generator sensors *appear* in Home Assistant. However, there were still 3 missing pieces:

1. ✅ Register definitions in profile - PRESENT (added in earlier release for Issue #145)
2. ✅ GrowattData dataclass fields - FIXED in v0.4.3
3. ✅ Sensor definitions in sensor.py - PRESENT
4. ❌ **Register reading code** - MISSING until v0.4.4

**The chain of events:**
1. Registers can be read via `read_register` service → Hardware works ✅
2. Sensors appear in entity list → Dataclass fields exist ✅
3. But sensors show zero → No code to read registers into data object ❌

This is a classic case of partial implementation where the infrastructure existed but the actual data pipeline connection was missing.

---

### Known Issues:
- None - All SPF Grid device sensors should now show correct values

---

# Release Notes - v0.4.3

## 🐛 Critical Bug Fix: Missing Dataclass Fields

**Fixed:** SPF generator sensors and WIT extra_energy sensors not appearing despite being properly configured.

---

### What's Fixed in v0.4.3:

#### 1. 🔧 Added Missing GrowattData Dataclass Fields

**Root Cause:** 28 sensor fields were missing from the `GrowattData` dataclass, causing `hasattr()` checks to fail and sensors to show "condition not met" in logs.

**SPF Off-Grid sensors added (14 fields):**
- `grid_voltage`, `grid_frequency` - AC input voltage/frequency monitoring
- `ac_input_power`, `ac_apparent_power` - AC input power monitoring
- `load_percentage` - Load percentage monitoring
- `generator_power`, `generator_voltage` - Generator monitoring
- `generator_discharge_today`, `generator_discharge_total` - Generator energy counters
- `ac_charge_energy_today`, `ac_discharge_energy_today`, `ac_discharge_energy_total` - AC charge/discharge energy
- `op_discharge_energy_today`, `op_discharge_energy_total` - Operational discharge energy

**WIT sensors added (3 fields):**
- `extra_power_to_grid` - Parallel inverter power export
- `extra_energy_today`, `extra_energy_total` - Parallel inverter energy counters

**Impact:**
- ✅ SPF 6000 ES Plus generator entities now appear correctly
- ✅ WIT extra_energy sensors now work (no longer show "not in profile")
- ✅ All SPF AC input monitoring sensors now functional

#### 2. 📚 Documentation Improvements

**Added:**
- Comprehensive MODELS.md documentation listing all supported models
- Protocol version documentation (VPP vs Legacy)
- Testing status for each model series

**Impact:**
- ✅ Clear visibility into which models are supported
- ✅ Protocol compatibility information
- ✅ Community testing status

---

### Migration Notes:

**No action required** - Simply upgrade and the missing sensors will appear.

**For SPF users:**
- Generator power, voltage, and energy sensors will now appear
- Grid/AC input sensors will now be available
- Check your Grid device in Home Assistant - all entities should be present

**For WIT users:**
- Extra power to grid sensor will now appear
- Extra energy today/total sensors will now be available

---

### Files Changed:
- `custom_components/growatt_modbus/growatt_modbus.py` - Added 28 missing dataclass fields
- `docs/MODELS.md` - Comprehensive supported models documentation
- `custom_components/growatt_modbus/manifest.json` - Version bump to 0.4.3

---

### Known Issues:
- SPF generator sensors appear but show zero values - **FIXED in v0.4.4**
- WIT battery_soh, battery_voltage_bms, ac_charge_energy_total still missing - **FIXED in v0.4.4**
