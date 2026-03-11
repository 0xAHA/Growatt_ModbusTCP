# Release Notes

<a href="https://www.buymeacoffee.com/0xAHA" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>

---

# Release Notes - v0.5.2

## 🔧 Critical Bug Fix - Integration Initialization Failure (Issue #188)

This release fixes a critical bug where the integration fails to initialize on inverters that don't support extended register ranges added in v0.5.0.

### What Was Fixed:

**Problem:** After upgrading to v0.5.*, some users reported:
- Integration stuck in "Initializing" state with constant retrying
- Error in logs: `ExceptionResponse(dev_id=1, function_code=132, exception_code=4)`
- Error message: `Modbus error reading input registers 3000-3078`
- Downgrading to v0.4.8 resolves the issue

**Root Cause:**
- In v0.5.0, registers 3071-3078 were added to SPH V2.01 profiles for load energy and grid export energy metrics
- These registers are in the MIN/MOD range (3000-3124) which not all inverters support
- When reading the 3000 range, inverters without these registers return Modbus exception code 4 (Slave Device Failure)
- The code treated this as a **fatal error** and aborted initialization by returning `None`
- This was inconsistent with how other register ranges (storage 1000-1124, business 875-999) handle failures

**The Fix:**

Changed 3000 range register read failure handling from fatal to graceful degradation:

1. **Non-Fatal Error Handling:**
   - Changed from `logger.error()` + `return None` to `logger.warning()` + continue
   - Matches the pattern used for storage and business register ranges
   - Allows initialization to complete even if extended registers aren't available

2. **Graceful Degradation:**
   - Inverters **with** extended registers: Get full data including load energy metrics
   - Inverters **without** extended registers: Work normally with core functionality
   - No user intervention required - automatic compatibility

**Impact:**
- ✅ Integration initializes successfully on all inverter models
- ✅ Fixes "stuck in Initializing" issue reported in #188
- ✅ Backward compatible with inverters lacking extended register support
- ✅ Forward compatible - still provides enhanced data when registers are available
- ✅ No configuration changes needed

### 📋 Action Required:

**For users experiencing initialization failures:**

1. **Update to v0.5.2**
2. **Restart Home Assistant**
3. **Verify integration initializes successfully:**
   - Integration should complete initialization within 30 seconds
   - No more "Initializing" stuck state
   - All supported sensors should appear and update normally

**No configuration changes needed** - fix is automatic after upgrade.

### Technical Details:

**Files Changed:**
- `custom_components/growatt_modbus/growatt_modbus.py:824-825`

**What Changed:**
- Modified `_read_registers()` method to handle 3000 range read failures gracefully
- Changed error handling from fatal (return None) to warning (continue)
- Inverters report Modbus exception code 4 when unsupported registers are requested
- Integration now continues with available data instead of aborting

**Affected Models:**
- All inverter models that don't support registers 3071-3078 (load energy, grid export in MIN/MOD range)
- Primarily affects inverters without VPP V2.01 protocol extended register support
- Fixes compatibility regression introduced in v0.5.0

## 🚀 Enhancement - MIC Auto-Detection Fix for Waveshare Adapters (Issue #187)

This release fixes auto-detection timeouts for MIC micro inverters when using Waveshare RS485-to-ETH adapters.

### What Was Fixed:

**Problem:** MIC 3000TLX users with Waveshare RS485-ETH adapters reported:
- Integration hangs at "off-grid inverter warning" screen during setup
- Setup takes ~10 minutes instead of completing immediately
- Logs show: `No response received after 3 retries` when reading register 30000
- Integration eventually times out and fails to initialize

**Root Cause:**
- MIC micro inverters use **legacy V3.05 protocol** (registers 0-179 only)
- Auto-detection was attempting to read VPP 2.01 register 30000 before checking legacy registers
- MIC doesn't support register 30000, causing long timeout with Waveshare adapters
- Legacy register detection (which includes MIC) only ran AFTER the VPP timeout

**The Fix:**

Added **early legacy register detection** before attempting VPP register reads:

1. **Quick Legacy Check (Step 1.5):**
   - Try reading register 3 (PV1 voltage) - exists in most legacy protocols
   - If register 3 responds, check if register 3003 is absent
   - Register 3 present + register 3003 absent = MIC series (0-179 range only)

2. **Skip VPP Detection:**
   - Once MIC is detected via legacy registers, skip reading register 30000
   - Prevents long timeout on unsupported VPP registers
   - Detection completes in <1 second instead of ~10 minutes

3. **Detection Order Updated:**
   - Step 1: OffGrid DTC (registers 34/43) - SPF detection
   - **Step 1.5: Legacy register check (NEW) - MIC detection**
   - Step 2: VPP DTC (register 30000) - V2.01 inverters
   - Step 3: Model name read
   - Step 4: Register probing (fallback)

**Impact:**
- ✅ MIC inverters detected immediately via legacy registers
- ✅ No timeout on unsupported VPP register 30000
- ✅ Setup completes in <1 second instead of ~10 minutes
- ✅ Works with all RS485-to-TCP adapters including Waveshare
- ✅ No impact on other inverter models

### 📋 Waveshare RS485-to-ETH Configuration

For users with Waveshare RS485-to-ETH adapters, use these settings:

**Connection Parameters:**
- **Baud Rate:** 9600
- **Data Bits:** 8
- **Parity:** None
- **Stop Bits:** 1
- **Port:** 502 (Modbus TCP standard)
- **Reset:** Off
- **Link:** On
- **Index:** Off
- **RFC2217 (Similar):** On

These settings are now documented in the README for reference.

### Technical Details:

**Files Changed:**
- `custom_components/growatt_modbus/auto_detection.py:923-945`
- `README.md:118-131` (added Waveshare configuration guide)

**Detection Logic:**
```python
# Before: VPP DTC read first → timeout on MIC
1. OffGrid DTC → VPP DTC → Model name → Register probing

# After: Legacy check before VPP → instant MIC detection
1. OffGrid DTC → Legacy check (MIC) → VPP DTC → Model name → Register probing
```

**Affected Models:**
- MIC 600-3300TL-X series (all micro inverters using 0-179 register range)
- Any legacy inverter using V3.05 protocol without VPP 2.01 support
- Particularly affects users with Waveshare RS485-to-ETH adapters

---

# Release Notes - v0.5.1

## 🔧 Bug Fixes - SPH Battery & Grid Energy Sensors

This release fixes critical sensor issues for SPH inverters including battery sensor inaccuracies and grid energy calculation errors.

### What Was Fixed:

**Problem:** SPH 3-6kW V2.01 users reporting incorrect battery sensor values (Issue #185):
- Battery SOC showing 0% instead of actual value (e.g., 31%)
- AC Charge Energy Total showing garbage value (70,516,736 kWh)
- Battery charge/discharge energy sensors showing incorrect or missing values

**Root Cause:**
- Register 17 (inherited from base profile) returns 0 for SOC on V2.01 inverters
- Correct SOC value is available in register 1086 (BMS register) but wasn't configured
- Battery energy registers in VPP range (31202-31209) were incorrectly mapped
- AC Charge Energy Total used wrong 32-bit register pairing (31220-31221)

**The Fix:**

1. **Added Correct Battery SOC Register:**
   - Added register 1086 for `battery_soc` in SPH 3-6kW V2.01 profile
   - Overrides inherited register 17 which returns 0
   - Provides accurate SOC value directly from BMS

2. **Fixed Battery Energy Register Mappings:**
   - Changed registers 31202-31203 from power to discharge_today energy
   - Added registers 31204-31205 for battery_charge_total
   - Added registers 31206-31207 for battery_charge_today
   - Added registers 31208-31209 for battery_discharge_total
   - All battery energy tracking now accurate

3. **Fixed AC Charge Energy Total:**
   - Removed incorrect 32-bit pairing of registers 31220-31221
   - Added register 115 for `ac_charge_energy_total`
   - Prevents garbage value of 70,516,736 kWh

**Impact:**
- ✅ Battery SOC now shows correct value (e.g., 31% instead of 0%)
- ✅ AC Charge Energy Total shows realistic value (e.g., 7.8 kWh instead of 70M kWh)
- ✅ Battery charge/discharge energy sensors now accurate
- ✅ Complete battery monitoring for SPH 3-6kW V2.01 users

---

## 🔧 Bug Fix - SPH-TL3 Grid Import Energy Calculation (Issue #183)

This release fixes incorrect grid import energy values for SPH-TL3 inverters where the energy sensor would show decreasing values or incorrect totals.

### What Was Fixed:

**Problem:** SPH-TL3 users reporting incorrect grid import energy:
- Grid import energy showing values that decrease when solar production starts
- Calculated values significantly different from actual grid consumption
- Energy meters not reflecting true grid import

**Root Cause:**
- SPH-TL3 has hardware registers for grid import energy (energy_to_user_today at 1044-1045 and energy_to_user_total at 1046-1047)
- Code was checking for energy_from_grid_today/total which don't exist on SPH-TL3
- This caused fallback to calculation: `import = load - solar + export`
- Calculation was **incorrect for hybrid inverters** because `solar` (energy_today) includes both PV generation AND battery discharge
- When solar production increased, calculated import energy would decrease (mathematically incorrect)

**The Fix:**

Modified sensor.py to check for energy_to_user_today/total registers and use them directly when available:

1. **Added Hardware Register Support:**
   - Check for registers 1044-1045 (`energy_to_user_today`) for daily grid import
   - Check for registers 1046-1047 (`energy_to_user_total`) for total grid import
   - Use hardware meter readings directly instead of calculation

2. **Improved CT Clamp Handling:**
   - Normal orientation + hardware register: use energy_to_user directly
   - CT clamp backwards + hardware register: use energy_to_grid (swapped)
   - No hardware register available: fall back to calculation (MIN series, etc.)

3. **Accurate Grid Import Tracking:**
   - Values now come directly from hardware meter
   - No dependency on PV production or battery discharge calculations
   - Grid import energy never decreases incorrectly

**Impact:**
- ✅ SPH-TL3 grid import energy now accurate from hardware registers
- ✅ Values stable and don't decrease when solar production starts
- ✅ Proper handling of CT clamp orientation (normal vs backwards)
- ✅ Fallback calculation still works for inverters without hardware registers
- ✅ Fixes issue #183

### 📋 Action Required for SPH Users:

**For SPH 3-6kW V2.01 inverters:**

1. **Update to v0.5.1**
2. **Restart Home Assistant**
3. **Verify sensors show correct values:**
   - Battery SOC should show actual percentage (not 0%)
   - AC Charge Energy Total should be realistic (not millions of kWh)
   - Battery energy today/total sensors should update properly

**For SPH-TL3 inverters:**

1. **Update to v0.5.1**
2. **Restart Home Assistant**
3. **Verify grid import energy:**
   - Grid import energy should be stable and accurate
   - Values should not decrease when solar production increases
   - Energy readings should match your actual grid consumption

**No configuration changes needed** - fixes are automatic after upgrade.

### Technical Details:

**Files Changed:**
- `custom_components/growatt_modbus/profiles/sph.py` (SPH 3-6kW battery sensors)
- `custom_components/growatt_modbus/sensor.py` (SPH-TL3 grid energy calculation)

**SPH 3-6kW Battery Fix - Registers Added/Modified:**
- 1086: `battery_soc` (overrides register 17)
- 115: `ac_charge_energy_total` (replaces incorrect 31220-31221 pair)
- 31202-31203: `battery_discharge_today` (was incorrectly mapped as power)
- 31204-31205: `battery_charge_total` (newly added)
- 31206-31207: `battery_charge_today` (newly added)
- 31208-31209: `battery_discharge_total` (newly added)

**SPH-TL3 Grid Energy Fix - Registers Used:**
- 1044-1045: `energy_to_user_today` (daily grid import from hardware meter)
- 1046-1047: `energy_to_user_total` (total grid import from hardware meter)
- Fallback calculation for inverters without hardware registers (MIN series, etc.)

**Affected Models:**
- **Battery sensor fix:** SPH 3000-6000 (V2.01 protocol only)
- **Grid energy fix:** SPH-TL3 (all versions with hardware meter registers)
- Does not affect SPH 7-10kW or other SPH models

---

## ⚠️ Known Issue - MIC-1000TL-X Profile Selection (Issue #130)

Some MIC-1000TL-X inverters (firmware "PV 1000") may show zero values for AC power, energy today, energy total, AC current, and AC frequency when using the "MIC 600-3300TL-X (V2.01)" profile.

### Problem:

MIC-1000TL-X inverters can have **two different register layouts**:

1. **Standard layout** (0-179 range): AC data at registers 11-12, 26-27
2. **Hybrid MIN layout** (0-124 + 3000-3124 range): AC data at registers 3028-3029, 3049-3050

If you selected "MIC 600-3300TL-X (V2.01)" but your inverter uses the hybrid MIN layout, the integration will read the wrong registers and show zeros.

### Solution:

1. Go to **Settings → Devices & Services → Integrations**
2. Find your **Growatt Modbus** integration
3. Click **Configure**
4. Change **Inverter Series** to: **MIC 1000-6000TL-X (MIN range)**
5. Click **Submit**
6. Restart Home Assistant

After restart, all sensors should show correct values.

### How to Identify if You Need This:

- **Inverter model:** MIC-1000TL-X (or similar MIC models 1-3.3kW)
- **Firmware:** "PV 1000" or similar
- **Symptoms:** AC power = 0, Energy today = 0, but PV power shows correct values
- **Profile needed:** MIC 1000-6000TL-X (MIN range)

**Note:** The profile name says "1000-6000" but works for all MIC inverters (including MIC-1000TL-X) that use the hybrid MIN register layout. The auto-detection should select this automatically, but if you manually selected a profile, you may need to change it.

---

# Release Notes - v0.5.0

## 🔧 Critical Bug Fix - Diagnostic DTC Detection

This release fixes a critical bug in the diagnostic scanner that caused incorrect profile suggestions for VPP 2.01 inverters.

### What Was Fixed:

**Problem:** Diagnostic scanner incorrectly overriding DTC-based detection with register-based detection:
- DTC code would correctly identify inverter model (e.g., DTC 3501 = SPH 3-6kW)
- Register-based detection would then override with wrong model (e.g., SPH 8-10kW HU)
- Users ended up with wrong profile selection, causing missing or incorrect sensors

**Root Cause:**
- Diagnostic scanner performed DTC detection first
- Then continued to register-based detection logic
- Register-based detection would override correct DTC mapping
- Example: SPH 3-6kW V2.01 has storage range (1000+) which triggered HU detection

**The Fix:**
- Added early exit after successful DTC detection
- Register-based detection now only runs if DTC detection fails
- DTC detection takes priority as most reliable method

**Impact:**
- ✅ DTC 3501 (SPH 3-6kW) now correctly suggests `sph_3000_6000_v201` instead of `sph_8000_10000_hu`
- ✅ All VPP 2.01 inverters with valid DTC codes get correct profile suggestions
- ✅ Battery sensors work correctly with proper profile

### 📋 Action Required for Existing Users:

If you previously ran the diagnostic scanner and it suggested the **wrong profile**, you need to update your configuration:

**Symptoms of wrong profile:**
- Missing battery sensors
- Incorrect power readings
- Diagnostic showed different model than what you selected

**How to Fix:**

1. **Update to v0.5.0**
2. **Re-run diagnostic scanner** (it will now show correct profile)
3. **Update your integration configuration:**
   - Go to: **Settings → Devices & Services → Integrations**
   - Find **Growatt Modbus** integration
   - Click **Configure**
   - Change **Inverter Series** to match diagnostic suggestion
   - Click **Submit**
4. **Restart Home Assistant**

**Common Corrections:**
- DTC 3501/3502: Change from `SPH 8-10kW HU` → `SPH 3-6kW (V2.01)`
- DTC 3501/3502: Change from `SPH 7-10kW` → `SPH 3-6kW (V2.01)`

### Technical Details:

**File Changed:** `diagnostic.py`

**Code Added:**
```python
# If DTC detected model, skip other detection logic
if detection["confidence"] == "Very High":
    return detection
```

This ensures DTC-based detection (confidence = "Very High") takes priority and prevents register-based detection from overriding the correct profile.

**Affected DTC Codes:**
- 3501, 3502, 3735 (SPH/SPA 3-6kW)
- 3601, 3725 (SPH/SPA TL3)
- 5100 (TL-XH)
- 5200, 5201 (MIN/MIC)
- 5400 (MOD-XH/MID-XH)
- 5603, 5601, 5800 (WIT/WIS)

---

# Release Notes - v0.4.9

## 🔧 Bug Fixes + ✨ New Features + 🎯 WIT/SPH Enhancements

This release combines all improvements from beta versions (v0.4.9b1-b4) plus additional bug fixes.

**Fixed:**
- Battery power sign inversion for VPP protocol registers (1013-1014 swapped)
- Missing energy and battery registers in SPH V2.01 profiles (Issue #176)
- Multiple inverters on same IP rejected with "already configured" (Issue #179)
- SPH TL3 Energy Today showing AC output instead of PV production (Issue #172)

**Added:**
- Multi-register write support for advanced Modbus operations
- WIT VPP battery control entities and services (PR #171)
- WIT VPP export limitation controls (30200/30201 registers, PR #175)
- WIT VPP V2.03 register definitions (TOU schedule, SOC limits, system time)
- Grid power sensor improvement using power_to_user register (PR #170)
- Register scan now includes holding registers in CSV output
- New `get_register_data` service for programmatic register reads

---

## What's New in v0.4.9:

### 1. 🔋 Fixed Battery Power Sign for VPP Protocol Registers

**Problem:** VPP protocol inverters (WIT, SPH V2.01) showing inverted battery power signs:
- Battery charging (power should be positive) showed negative values
- Battery discharging (power should be negative) showed positive values
- Caused confusion in energy monitoring and automation

**Root Cause:**
- VPP protocol stores battery power in registers 1013-1014 in **swapped order**
- Register 1013: Low word (W)
- Register 1014: High word (kW)
- Integration was reading them as 1014+1013 (reversed), causing sign inversion

**The Fix:**
- Registers 1013-1014 now read in correct order for VPP protocol profiles
- Battery power signs now match physical behavior:
  - **Positive = Charging** (power going INTO battery)
  - **Negative = Discharging** (power coming OUT of battery)
- Affects: WIT, SPH V2.01, and other VPP protocol inverters

**Impact:**
- ✅ Battery power values now show correct sign
- ✅ Automation triggers work as expected
- ✅ Energy flow visualization accurate

### 2. 🔋 Added Missing Registers to SPH V2.01 Profiles (Issue #176)

**Added to SPH V2.01:**
- Battery registers: SOC, voltage, current, power, temperature, discharge limits
- Energy registers: Battery charge/discharge energy (today & total)
- Complete battery monitoring for SPH inverters using VPP protocol

**Impact:**
- ✅ SPH V2.01 users now have full battery monitoring
- ✅ Battery charge/discharge energy tracking available
- ✅ Complete parity with SPH TL3 legacy profile features

### 3. 🔧 Fixed Unique ID Collision for Multiple Inverters (Issue #179)

**Problem:** Multiple inverters on same IP (different ports) could not be configured:
- Common with Modbus proxy/gateway setups
- Second inverter rejected: "This inverter is already configured"

**Root Cause:**
- TCP unique ID format was: `{host}_{slave_id}` (ignored port number)
- Multiple inverters on same IP with different ports generated identical unique IDs

**The Fix:**
- Changed TCP unique ID format to: `{host}:{port}_{slave_id}`
- Example: `192.168.168.4:5021_1` vs `192.168.168.4:5022_1`

**Impact:**
- ✅ Multiple inverters on same IP with different ports now supported
- ✅ Modbus proxy/gateway setups work correctly
- ✅ Still prevents true duplicates (same IP+port+slave_id)

### 4. 🔧 Fixed SPH TL3 Energy Today (Issue #172)

**Problem:** SPH TL3 "Energy Today" showing AC output instead of true PV production:
- DC-coupled battery charging excluded from total
- Reported values significantly lower than actual solar production

**The Fix:**
- Added per-MPPT PV energy registers (59-60, 63-64, 91-92) to SPH TL3 profile
- Energy Today now calculated as: **PV1 + PV2** (true solar production)
- Same fix previously applied to WIT profile in v0.4.7

**Impact:**
- ✅ Energy Today shows accurate total PV production
- ✅ Values include DC-coupled battery charging
- ✅ Consistent with WIT behavior

### 5. ✨ Multi-Register Write Support (PR #168)

**Added:** Ability to write multiple registers in a single Modbus transaction
- New `write_multiple_registers` method in GrowattModbus class
- Improved error reporting with detailed Modbus exception handling
- Atomic multi-register writes for complex settings

**Use Cases:**
- Setting TOU schedules (multiple time/power registers)
- Batch configuration updates
- Advanced inverter programming

### 6. 🎯 WIT VPP Battery Control Enhancements (PR #171)

**Added:**
- WIT VPP battery control entities (charge/discharge power, duration)
- Service handlers for programmatic battery control
- Remote control enable/disable functionality
- Integration with VPP protocol time-limited overrides

**New Entities:**
- Remote Power Control Enable (register 30407)
- Remote Charging Time (register 30408, duration in minutes)
- Remote Charge/Discharge Power (register 30409, -100% to +100%)

### 7. 🎯 WIT VPP Export Limitation (PR #175)

**Added:**
- VPP export limitation control registers (30200/30201)
- Enable/disable export limiting
- Set maximum export power to grid

**Use Cases:**
- Comply with grid connection agreements
- Prevent export during peak pricing
- Dynamic export control based on conditions

### 8. 📊 WIT VPP V2.03 Register Additions (PR #169)

**Added:**
- TOU (Time of Use) schedule registers
- SOC (State of Charge) limit registers
- System time registers
- Enhanced VPP protocol support

### 9. 🔌 Grid Power Sensor Improvement (PR #170)

**Changed:** Grid power calculation now uses `power_to_user` register
- More accurate grid import/export measurements
- Better handling of CT clamp configurations
- Improved power flow calculations

### 10. 🛠️ Enhanced Services and Diagnostics

**Added:**
- `get_register_data` service for programmatic register reads
- Holding registers now included in register scan CSV output
- Better integration with automation and scripts

---

## Migration Notes:

**No action required** - This is a bug fix and enhancement release.

**For VPP Protocol Users (WIT, SPH V2.01):**
- Battery power signs will flip after upgrade (this is the fix - values are now correct)
- **Positive = Charging**, **Negative = Discharging**
- Update any automations that relied on the incorrect sign behavior

**For SPH TL3 Users:**
- Energy Today values will increase (now showing true PV production)
- Dashboard graphs may show a step change (expected - previous values were too low)

**For SPH V2.01 Users:**
- Battery sensors will now appear after upgrade
- Full battery monitoring now available

**For Multi-Inverter Setups (Issue #179):**
- If you couldn't add a second inverter on same IP, try adding it again after upgrade
- Both inverters will now configure successfully

**For WIT Users:**
- New battery control and export limitation features available
- See PR documentation for usage examples
- Rate limiting (30s cooldown) applies to control writes

---

## Files Changed:

Core functionality:
- `custom_components/growatt_modbus/growatt_modbus.py` - Battery power sign fix, multi-register write support, enhanced services
- `custom_components/growatt_modbus/config_flow.py` - Updated TCP unique_id format
- `custom_components/growatt_modbus/services.yaml` - Added get_register_data service
- `custom_components/growatt_modbus/select.py` - VPP export limitation
- `custom_components/growatt_modbus/diagnostic.py` - Enhanced register scanning

Profile updates:
- `custom_components/growatt_modbus/profiles/sph_tl3.py` - Added per-MPPT energy registers
- `custom_components/growatt_modbus/profiles/sph_v201.py` - Added battery and energy registers
- `custom_components/growatt_modbus/profiles/wit.py` - VPP control registers, export limitation

Version bump:
- `custom_components/growatt_modbus/manifest.json` - Version 0.4.9
- `README.md` - Version badge updated to 0.4.9
- `RELEASENOTES.md` - Updated with v0.4.9 changes

---

# Release Notes - v0.4.9b4 (Pre-Release)

## 🔧 Bug Fix - Multiple Inverters on Same IP

**Fixed (Issue #179):**
- Multiple inverters on the same IP address (different ports) could not be configured
- Integration rejected second inverter with "This inverter is already configured"
- Common scenario with Modbus proxies/gateways exposing multiple inverters

---

### What's Fixed in v0.4.9b4:

#### 🔧 Fixed Unique ID Collision for Same-IP Multi-Inverter Setups (Issue #179)

**Problem:** Users with multiple inverters behind a Modbus proxy or gateway (same IP, different ports) could only configure one inverter. The second would fail with "This inverter is already configured."

**Root Cause:**
- TCP unique ID format was: `{host}_{slave_id}`
- Ignored the port number completely
- Multiple inverters on same IP with different ports generated identical unique IDs

**User Case (Issue #179):**
- Setup: 2 inverters → Waveshare → evcc → ModbusProxy
- SPH 10k TL3 BH-UP: `192.168.168.4:5021` (slave 1)
- MOD 10k TL3-XH: `192.168.168.4:5022` (slave 1)
- Both generated unique_id: `192.168.168.4_1` ❌ **COLLISION!**
- Only first inverter could be added

**The Fix:**

Changed TCP unique ID format to include port number:
- **Old format:** `{host}_{slave_id}` (e.g., `192.168.168.4_1`)
- **New format:** `{host}:{port}_{slave_id}` (e.g., `192.168.168.4:5021_1`)

**Impact:**
- ✅ Multiple inverters on same IP with different ports now supported
- ✅ Common Modbus proxy/gateway setups now work correctly
- ✅ Still prevents true duplicates (same IP+port+slave_id)
- ✅ Serial connections unchanged

**Example - Now Works:**
```
Configuration:
  SPH 10k TL3:  192.168.168.4:5021 slave_id=1 → unique_id: 192.168.168.4:5021_1 ✅
  MOD 10k TL3:  192.168.168.4:5022 slave_id=1 → unique_id: 192.168.168.4:5022_1 ✅

Still Blocks Duplicates:
  First:   192.168.168.4:502 slave_id=1 → unique_id: 192.168.168.4:502_1 ✅ (allowed)
  Second:  192.168.168.4:502 slave_id=1 → unique_id: 192.168.168.4:502_1 ❌ (blocked - true duplicate)
```

---

### Migration Notes:

**No action required for existing single-inverter setups** - unique IDs will update automatically.

**For Multi-Inverter Setups (Issue #179):**
- If you previously couldn't add a second inverter on the same IP:
  1. Upgrade to v0.4.9b4
  2. Try adding the second inverter again
  3. Both inverters will now configure successfully

**Technical Note:**
- Existing integrations will get new unique IDs on next restart
- Home Assistant handles unique ID changes automatically
- No need to remove/re-add existing integrations

---

### Files Changed:
- `custom_components/growatt_modbus/config_flow.py` - Updated TCP unique_id format to include port
- `custom_components/growatt_modbus/manifest.json` - Version bump to 0.4.9b4
- `README.md` - Version badge updated to 0.4.9b4
- `RELEASENOTES.md` - Updated with v0.4.9b4 changes

---

# Release Notes - v0.4.9b3 (Pre-Release)

## 🔧 Bug Fix - SPH TL3 Energy Today Incorrect Values

**Fixed (Issue #172):**
- SPH TL3 "Energy Today" sensor showing AC output energy instead of true PV solar production
- On hybrid inverters with batteries, DC-coupled battery charging was excluded from the total

---

### What's Fixed in v0.4.9b3:

#### 🔧 Fixed SPH TL3 Energy Today Calculation (Issue #172)

**Problem:** SPH TL3 users reported "Energy Today" showing significantly lower values than actual solar production. For example, a user producing ~8.1 kWh saw only 1.5-2.6 kWh reported.

**Root Cause:**
- Registers 53-54 (`energy_today`) on SPH TL3 measure **total AC output energy** (what goes to grid/loads)
- On hybrid inverters with batteries, energy that goes directly from PV to battery via DC coupling **bypasses the AC side** and is NOT counted in registers 53-54
- This means the "Energy Today" sensor was underreporting by the amount of DC-coupled battery charging

**User Case:**
- SPH TL3 inverter with battery
- Register 54 = 15 → 1.5 kWh (AC output only)
- Registers 60 (PV1) + 64 (PV2) = actual total PV production (~8.1 kWh)
- Difference = energy going directly to battery via DC coupling

**The Fix:**

1. **Added Per-MPPT PV Energy Registers to SPH TL3 Profile:**
   - 59-60: `pv1_energy_today` (PV string 1 DC energy production)
   - 63-64: `pv2_energy_today` (PV string 2 DC energy production)
   - 91-92: `pv_energy_total` (lifetime total PV energy from all MPPTs)

2. **Automatic Calculation:**
   - Existing code already sums PV1 + PV2 when per-MPPT registers are available
   - `energy_today` now calculated as: **PV1 + PV2** (true solar production)
   - Same approach already working correctly for WIT profile (Issue #146 fix in v0.4.7)

**Impact:**
- Energy Today now shows accurate total PV production (DC input from solar panels)
- Values include energy going to battery via DC coupling (previously excluded)
- Energy Total (lifetime) now uses PV energy total register for accuracy
- Other inverter profiles unaffected (backwards compatible)

**Example - Before vs After:**
```
Before (v0.4.9b1):
  Energy Today: 1.5 kWh  (AC output only, missing DC battery charging)

After (v0.4.9b3):
  Energy Today: 8.1 kWh  (PV1 + PV2 = true solar production)
```

---

### Migration Notes:

**No action required** - Fix is automatic after upgrade.

**For SPH TL3 Users:**
- "Energy Today" will now show higher (correct) values that include DC battery charging
- Dashboard energy graphs may show a one-time step change after upgrade - this is expected
- Previous values excluded DC-coupled battery charging (incorrect), new values are PV-only production (correct)

---

### Files Changed:
- `custom_components/growatt_modbus/profiles/sph_tl3.py` - Added per-MPPT PV energy registers (59-60, 63-64, 91-92)
- `custom_components/growatt_modbus/manifest.json` - Version bump to 0.4.9b3
- `README.md` - Version badge updated to 0.4.9b3
- `RELEASENOTES.md` - Updated with v0.4.9b3 changes

---

# Release Notes - v0.4.8

## 🔧 Bug Fix - MIC-1000TL-X Auto-Detection

**Fixed (Issue #130):**
- MIC-1000TL-X inverters incorrectly auto-detected as MIN series
- Manual MIC profile selection showed incorrect/missing values

---

### What's Fixed in v0.4.8:

#### 🔍 Improved MIC vs MIN Detection (Issue #130)

**Problem:**
- DTC code 5200 is shared by both MIC and MIN inverter series
- Previous logic tested for 3000+ register range to distinguish models
- Some MIC-1000TL-X inverters use MIN register layout (hybrid design) but are physically MIC hardware
- This caused incorrect auto-detection and wrong sensor values

**Root Cause:**
- MIC-1000TL-X (2500-6000W range) can use either:
  - Standard MIC layout: 0-179 registers only
  - Hybrid layout: 0-124 + 3000-3124 (MIN addressing) BUT with MIC features
- Previous detection tested register 3003 (MIN PV1 voltage)
- If found → assumed MIN series ❌
- If not found → assumed MIC series ✅

**User Case:**
- MIC-1000TL-X with firmware "PV 1000"
- Has data in BOTH 0-124 AND 3000-3124 ranges (hybrid layout)
- Previous detection saw 3000+ range → incorrectly selected MIN profile
- MIN profile missing MIC-specific per-MPPT energy registers (59-62)
- Result: Wrong/missing sensor values

**The Fix:**

1. **Hardware-Level Detection:**
   - MIC inverters have per-MPPT energy tracking capability (registers 59-62)
   - MIN inverters do NOT have these registers (not a firmware feature - hardware difference)
   - Now test registers 59-62 FIRST before checking register range

2. **New Detection Logic for DTC 5200:**
   ```
   Step 1: Read registers 59-62 (PV1/PV2 per-MPPT energy)

   Step 2: Validate if values are plausible energy data:
           - MIC hardware: registers contain valid energy values (high word 0-100)
           - MIN hardware: registers return garbage/system values (e.g., 5200 = DTC code)
           - Check: high word < 100 (rejects invalid data like DTC codes)

   Step 3: If valid energy data found in registers 59-62:
           → MIC hardware detected
           → Check if uses MIN layout (3000+ range)
           → If yes: Use new MIC_2500_6000TL_X_MIN_RANGE profile
           → If no: Use standard MIC_600_3300TL_X_V201 profile

   Step 4: If registers 59-62 empty or invalid:
           → MIN hardware (no per-MPPT capability or garbage data)
           → Use MIN_3000_6000TL_X_V201 profile
   ```

3. **New MIC Profile Created:**
   - Profile: `MIC_2500_6000TL_X_MIN_RANGE`
   - Supports hybrid MIC inverters using MIN register addressing
   - Combines:
     - MIN 0-124 register range (basic data)
     - MIN 3000-3124 register range (AC power, energy)
     - MIC per-MPPT registers 59-62 (PV1/PV2 energy tracking)
   - Provides complete sensor coverage for these hybrid models

**Impact:**
- ✅ MIC-1000TL-X correctly auto-detected regardless of register layout
- ✅ All sensors show correct values
- ✅ Per-MPPT energy tracking available for MIC users
- ✅ MIN detection unaffected (backwards compatible)
- ✅ Reliable hardware-level differentiation (not just register addressing)

**Example - Before vs After:**
```
Before (v0.4.7):
  Auto-Detection: MIN 3000-6000TL-X ❌ (wrong - saw 3000+ range)
  AC Power: 1127 W ✅ (worked from 3000+ range)
  Energy Today: 0.1 kWh ❌ (wrong - MIN profile missing PV1/PV2 registers)
  PV1 Energy: Not available ❌ (MIN profile doesn't define register 59-60)

After (v0.4.8):
  Auto-Detection: MIC 2500-6000TL-X (MIN range) ✅ (correct - saw registers 59-62)
  AC Power: 1127 W ✅ (from 3000+ range)
  Energy Today: 0.1 kWh ✅ (correct - using per-MPPT registers)
  PV1 Energy: 0.1 kWh ✅ (now available from register 59-60)
  PV2 Energy: 44927.0 kWh ✅ (now available from register 61-62)
```

---

### Technical Details:

**Register Scan Analysis:**
```
MIC-1000TL-X Hybrid Layout (verified):
  Register 11-12: 0 (MIC AC power location - empty)
  Register 35-36: 1127 (output power - populated)
  Register 59-60: 1/1 (PV1 energy - VALID energy data ✅)
  Register 61-62: 44927/0 (PV2 energy - VALID energy data ✅)
  Register 3028-3029: 1127 (MIN AC power location - populated)
  Register 3049-3052: energy values (MIN location - populated)

MIN 3000-6000TL-X (verified):
  Register 59: 5200 (garbage/DTC code - INVALID for energy ❌)
  Register 59-62: Returns system values, not energy data
  → Detection rejects high word >= 100 as garbage
```

**Validation Logic:**
- Energy registers use 32-bit pairs (high word, low word)
- Valid daily energy: 0-50 kWh → high word typically 0-1
- Valid lifetime energy: 10,000 kWh → high word ~1-2
- **Threshold: high word must be < 100 to be valid energy**
- MIN garbage values (5200, DTC codes, etc.) correctly rejected

**Key Insight:** Registers 59-62 differentiate MIC/MIN at hardware level. MIN may respond to these registers but returns garbage/system values, not energy data.

---

### Migration Notes:

**No action required** - Auto-detection improvement only.

**For Affected MIC-1000TL-X Users (Issue #130):**
- If previously manually selected MIN profile as workaround:
  1. Remove integration
  2. Re-add integration with auto-detection
  3. Inverter will now correctly detect as MIC
  4. All sensors (including per-MPPT energy) will appear

**Detection Changes:**
- MIC inverters with hybrid layout now correctly identified
- All existing MIC and MIN inverters unaffected
- More robust detection using hardware capabilities instead of register addressing

---

# Release Notes - v0.4.7

## 🐛 Bug Fix + 📊 Diagnostic Enhancement

**Fixed (Issue #146):**
- WIT "Energy Today" sensor showing incorrect values (total system output instead of PV-only production)
- WIT "Energy Total" sensor not reflecting actual solar panel production

**Enhanced:**
- Register scan now includes firmware version in metadata output

---

### What's Fixed in v0.4.7:

#### 1. 🔧 Fixed WIT PV Energy Calculation (Issue #146)

**Problem:** WIT users reported "Energy Today" sensor increasing at night when no solar production occurring.

**Root Cause:**
- Registers 53-56 (energy_today/total) track **total system AC output** (PV + battery discharge combined)
- Not suitable for tracking solar production on hybrid inverters with batteries
- Values increase whenever battery powers loads, even at night

**User Report:**
- Register 56 showed 6.2 kWh (wrong - total system output)
- Register 60 (PV1): 4.8 kWh ✅
- Register 64 (PV2): 2.7 kWh ✅
- **Actual PV production: 4.8 + 2.7 = 7.5 kWh** ✅

**The Fix:**
1. **Added Missing Registers to WIT Profile:**
   - 59-60: PV1 Energy Today (per-MPPT tracking)
   - 63-64: PV2 Energy Today (per-MPPT tracking)
   - 91-92: PV Energy Total (lifetime DC input from all MPPTs)

2. **Added Dataclass Fields:**
   - `pv1_energy_today` - PV1 MPPT daily production
   - `pv2_energy_today` - PV2 MPPT daily production
   - `pv_energy_total` - Lifetime PV production

3. **Changed Energy Calculation for WIT:**
   - `energy_today` now calculated as: **PV1 + PV2** (true solar production)
   - `energy_total` now uses register 92 (total PV lifetime energy)
   - Fallback to original registers for non-WIT inverters (backwards compatible)

**Impact:**
- ✅ WIT "Energy Today" now shows accurate solar production (not total system output)
- ✅ Values only increase during daylight when panels are producing
- ✅ Correctly tracks DC input from solar panels only
- ✅ Other inverter series unaffected (backwards compatible)

**Example - Before vs After:**
```
Before (v0.4.6):
  Energy Today: 6.2 kWh  ❌ (total system including battery)

After (v0.4.7):
  Energy Today: 7.5 kWh  ✅ (PV1 4.8 + PV2 2.7 = actual solar)
```

#### 2. 📊 Register Scan Enhancement

**Added:** Firmware version now included in register scan metadata output.

**How it Works:**
- Reads holding registers 9-11 (firmware version, ASCII encoded)
- Decodes to human-readable version string
- Displays in both CSV metadata and notification message

**Example Output:**
```
DETECTION ANALYSIS
Detected Model: WIT 4-15kW Hybrid
Confidence: Very High
DTC Code: 10046
Protocol Version: V2.01
Firmware: GH1.0     <-- NEW
Suggested Profile: WIT_4000_15000TL3
```

**Impact:**
- ✅ Easier troubleshooting - firmware version visible in scans
- ✅ Helps identify firmware-specific behaviors
- ✅ No additional user action required - automatic extraction

---

### Migration Notes:

**No action required** - This is a bug fix and enhancement release.

**For WIT Users:**
- "Energy Today" and "Energy Total" sensors will now show correct PV production values
- **IMPORTANT:** Values may differ from v0.4.6 - this is expected and correct
- Previous values included battery discharge (wrong), new values are PV-only (correct)
- Dashboard energy graphs may show a one-time step change after upgrade

**For All Users:**
- Next register scan will include firmware version automatically
- No changes needed to existing scans

---

### Files Changed:
- `custom_components/growatt_modbus/profiles/wit.py` - Added PV energy registers (59-60, 63-64, 91-92) with descriptions
- `custom_components/growatt_modbus/growatt_modbus.py` - Added PV energy dataclass fields + reading code + smart calculation logic
- `custom_components/growatt_modbus/diagnostic.py` - Added firmware version reading and display
- `custom_components/growatt_modbus/manifest.json` - Version bump to 0.4.7
- `README.md` - Version badge updated to 0.4.7
- `RELEASENOTES.md` - Updated with v0.4.7 changes

---

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
