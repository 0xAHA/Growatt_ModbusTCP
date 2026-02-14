# Release Notes

# Release Notes - v0.4.6

## 🐛 Bug Fixes + 🎯 WIT Control Stability Improvements

**Fixed (Issue #163):**
- SPF AC Charge Energy Today/Total sensors showing 0.00 (should show same values as Battery Charge sensors)
- SPF AC Discharge Energy Today/Total sensors showing 0.00 (registers 64-67)
- Noisy WARNING log message for SPF users: "load_energy_today_low register not found"

**Improved (Issue #143):**
- WIT control stability - prevent oscillation and unstable battery behavior
- WIT control model clarified - VPP protocol vs Legacy protocol differences
- Rate limiting added to prevent rapid control changes
- Control conflict detection for TOU vs remote control scenarios

---

### What's Fixed in v0.4.6:

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

#### 2. 🔇 Reduced Log Noise for Off-Grid Inverters

**Issue:** SPF users (and other off-grid models) saw constant WARNING messages in Home Assistant logs:

    [SPF 3000-6000 ES PLUS@/dev/ttyACM0] load_energy_today_low register not found

**Root Cause:** The `load_energy_today` register is specific to **grid-tied inverters** (SPH/MIN/MID/MAX) that track energy consumed from grid by loads. **Off-grid inverters** like SPF don't have this register because they use different energy tracking:
- `ac_discharge_energy_*` - Battery → loads via inverter
- `op_discharge_energy_*` - Operational discharge energy

The code was logging this as a WARNING even though it's expected and harmless for off-grid models.

**The Fix:** Changed log level from WARNING to DEBUG with clarifying message: "register not found (expected for off-grid models like SPF)"

**Impact:**
- ✅ SPF users will no longer see noisy warnings in logs
- ✅ Debug logging still available if needed for troubleshooting
- ✅ No functional changes - purely cosmetic log improvement

#### 3. 🎯 WIT Control Stability Improvements (Issue #143)

**Problem:** WIT users experiencing power oscillation, charge/discharge looping, and unstable control behavior when using battery management features.

**Root Cause:** WIT inverters use **VPP (Virtual Power Plant) protocol** with fundamentally different control model:
- **WIT**: Time-limited overrides (NOT persistent mode changes like SPH/SPF)
- Register 30476 (`priority_mode`) is **READ-ONLY** on WIT - shows TOU default, cannot be changed via Modbus
- Proper control requires VPP remote registers (30407-30409) with duration-based commands
- Rapid control changes cause oscillation and conflicts with TOU schedules

**The Fixes:**

1. **Register 30476 Marked Read-Only**
   - WIT profile now correctly marks `priority_mode` (30476) as `'access': 'R'`
   - Prevents users from trying to write to read-only register
   - Description updated to clarify VPP control model
   - Users guided to use proper VPP remote control instead

2. **30-Second Rate Limiting**
   - All WIT control writes now have 30-second cooldown
   - Prevents rapid automation loops that cause oscillation
   - Applies to registers: 201, 202, 203, 30100, 30407, 30408, 30409
   - Warning logged if write blocked: "Rate limit: WIT control writes must be 30s apart"
   - Gives inverter time to respond and stabilize

3. **Control Conflict Detection**
   - Detects multiple VPP remote controls active simultaneously
   - Warns when TOU schedule conflicts with remote control
   - Logs warnings to Home Assistant logs
   - Helps users identify problematic automation patterns

4. **Comprehensive WIT Control Guide**
   - New documentation: `docs/WIT_CONTROL_GUIDE.md`
   - Explains VPP vs Legacy protocol differences
   - Shows proper WIT control patterns with examples
   - Documents why register 30476 is read-only
   - Provides automation templates for stable control
   - Troubleshooting guide for common issues

**Impact:**
- ✅ WIT users can now implement stable battery control
- ✅ Oscillation and looping behavior prevented
- ✅ Clear guidance on proper VPP remote control usage
- ✅ Automatic conflict detection helps debug issues
- ✅ Rate limiting prevents automation mistakes

**WIT Control Registers (Rate Limited):**
- 201: Active Power Rate (Legacy VPP)
- 202: Work Mode (Legacy VPP)
- 203: Export Limit (W)
- 30100: Control Authority (VPP master enable)
- 30407: Remote Power Control Enable
- 30408: Remote Charging Time (duration in minutes)
- 30409: Remote Charge/Discharge Power (-100% to +100%)

**For WIT Users:**
- **Read the guide**: See `docs/WIT_CONTROL_GUIDE.md` for proper control patterns
- **Use VPP remote control**: Don't try to write to register 30476
- **Set durations**: All overrides should specify time duration (register 30408)
- **Wait 30s between changes**: Rate limiting is intentional to prevent oscillation
- **Check for conflicts**: Monitor logs for TOU vs remote control warnings

---

### Migration Notes:

**No action required** - This is a bug fix and improvement release. Simply upgrade and:
- SPF AC Charge/Discharge Energy sensors will show correct values
- Log warnings for missing load_energy_today register will disappear
- WIT control writes will have automatic rate limiting

**For SPF users:**
- All four AC Charge/Discharge Energy sensors will now work
- "AC Charge Energy" sensors will show identical values to "Battery Charge" sensors (expected behavior)
- Log noise from missing grid-tied registers eliminated

**For WIT users:**
- **IMPORTANT:** Read `docs/WIT_CONTROL_GUIDE.md` if you use battery control features
- Control writes now have 30s cooldown (prevents oscillation - this is intentional)
- Register 30476 (priority_mode) is now correctly marked read-only
- If you have automations that write to WIT controls rapidly, they may need adjustment
- Check logs for rate limit warnings and control conflict warnings

**Debug logging setup** (optional, for troubleshooting):
```yaml
logger:
  default: info
  logs:
    custom_components.growatt_modbus: debug
```

---

### Files Changed:
- `custom_components/growatt_modbus/growatt_modbus.py` - Added AC charge/discharge energy register mapping for SPF + reduced log noise + WIT rate limiting + conflict detection
- `custom_components/growatt_modbus/profiles/wit.py` - Marked priority_mode as read-only + added VPP control model documentation
- `docs/WIT_CONTROL_GUIDE.md` - NEW: Comprehensive WIT control guide with examples and troubleshooting
- `custom_components/growatt_modbus/manifest.json` - Version bump to 0.4.6
- `README.md` - Version badge updated to 0.4.6
- `RELEASENOTES.md` - Updated with v0.4.6 changes

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
