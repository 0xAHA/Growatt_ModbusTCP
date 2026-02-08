# Claude Development Guide - Growatt Modbus Integration

This document provides comprehensive guidelines for AI assistants (and developers) working on the Growatt Modbus Home Assistant integration.

---

## 🚨 START HERE - Adding/Updating Sensors 🚨

**BEFORE making ANY changes to sensors or registers:**

### 1. **Required Checklist** (Complete ALL 5 steps)
```
□ Step 1: Update profile file (profiles/*.py) - Add register definition
□ Step 2: Add sensor definition (sensor.py) - SENSOR_DEFINITIONS
□ Step 3: Assign device type (const.py) - SENSOR_DEVICE_MAP
□ Step 4: Add to sensor group (device_profiles.py) - BATTERY_SENSORS/GRID_SENSORS/etc
□ Step 5: Run validation script: python3 validate_sensors.py --sensor <name>
```

### 2. **Validation Tools**
```bash
# Validate a specific sensor
python3 validate_sensors.py --sensor battery_power

# Validate all sensors
python3 validate_sensors.py

# Validate entire profile
python3 validate_sensors.py --profile sph
```

### 3. **Quick Search Check**
```bash
# After making changes, verify sensor appears in all places:
grep -r "your_sensor_name" custom_components/growatt_modbus/
```

**If ANY step is skipped, the sensor WILL NOT work correctly!**

See [Register Update/Addition Process](#register-updateaddition-process) below for detailed instructions.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Register Update/Addition Process](#register-updateaddition-process)
3. [Profile Management](#profile-management)
4. [Critical Patterns & Conventions](#critical-patterns--conventions)
5. [Testing & Validation](#testing--validation)
6. [Common Issues & Solutions](#common-issues--solutions)

---

## Architecture Overview

### Project Structure

```
custom_components/growatt_modbus/
├── profiles/              # Register maps by inverter family
│   ├── sph.py            # SPH single-phase hybrid
│   ├── spf.py            # SPF off-grid
│   ├── mod.py            # MOD three-phase hybrid
│   ├── min.py            # MIN grid-tied
│   └── wit.py            # WIT commercial hybrid
├── device_profiles.py    # Profile registry & display names
├── const.py              # Device mappings, entity categories
├── sensor.py             # Sensor entity definitions
├── number.py             # Number entity definitions
├── select.py             # Select entity definitions
├── coordinator.py        # Data coordinator & device info
├── auto_detection.py     # Automatic profile detection
└── diagnostic.py         # Register scanning & diagnostics
```

### Device Hierarchy

The integration uses a **multi-device structure** where entities are logically grouped:

```
Inverter (parent device)
├── Solar Device       - PV inputs, AC output, solar energy
├── Grid Device        - Grid import/export, grid power flow
├── Load Device        - Consumption, load power, AC output voltage
└── Battery Device     - Battery storage, charge/discharge
```

**Why this matters:** When adding sensors, you MUST assign them to the correct device type or they'll appear in the wrong location in Home Assistant.

---

## Register Update/Addition Process

### ⚠️ CRITICAL CHECKLIST - Follow Every Time

When adding or updating a register in a profile, you MUST complete ALL these steps:

#### Step 1: Update Profile File (`profiles/*.py`)

**Location:** `custom_components/growatt_modbus/profiles/<profile>.py`

Add the register definition:

```python
'input_registers': {
    20: {'name': 'grid_voltage', 'scale': 0.1, 'unit': 'V', 'desc': 'AC input voltage'},
}
```

**Important considerations:**
- Choose the correct register name (see [Naming Conventions](#register-naming-conventions))
- Set correct `scale` factor
- For 32-bit values, define both `_high` and `_low` with `pair` attribute
- Mark signed values with `'signed': True`

#### Step 2: Add Sensor Definition (`sensor.py`)

**Location:** `custom_components/growatt_modbus/sensor.py`

Add to `SENSOR_DEFINITIONS` dictionary (~line 40-700):

```python
"grid_voltage": {
    "name": "Grid Voltage",
    "icon": "mdi:transmission-tower",
    "device_class": SensorDeviceClass.VOLTAGE,
    "state_class": SensorStateClass.MEASUREMENT,
    "unit": UnitOfElectricPotential.VOLT,
    "attr": "grid_voltage",  # Must match register name
},
```

**Required fields:**
- `name` - Display name in Home Assistant
- `icon` - MDI icon (browse at https://materialdesignicons.com/)
- `device_class` - HA device class (VOLTAGE, POWER, ENERGY, etc.)
- `state_class` - Usually `MEASUREMENT` for sensors
- `unit` - Unit constant from `homeassistant.const`
- `attr` - Data attribute name (must match register `name` in profile)

**Optional fields:**
- `condition` - Lambda function to conditionally create sensor
- `entity_category` - Set to `EntityCategory.DIAGNOSTIC` for technical sensors

#### Step 3: Assign Device Type (`const.py`)

**Location:** `custom_components/growatt_modbus/const.py` (~line 416-488)

Add the sensor key to the appropriate device's set in `SENSOR_DEVICE_MAP`:

```python
SENSOR_DEVICE_MAP = {
    DEVICE_TYPE_GRID: {
        'grid_power', 'grid_export_power',
        'grid_voltage',  # ← Add here
        ...
    },
}
```

**Device assignment guidelines:**
- `DEVICE_TYPE_SOLAR` - PV inputs, solar production, AC output current/power
- `DEVICE_TYPE_GRID` - Grid connection, import/export, grid voltage/frequency
- `DEVICE_TYPE_LOAD` - Consumption, load power, AC output voltage (for SPF)
- `DEVICE_TYPE_BATTERY` - Battery storage, SOC, charge/discharge
- `DEVICE_TYPE_INVERTER` - Status, faults, temperatures, system info

#### Step 4: Add to Sensor Group (`device_profiles.py`)

**Location:** `custom_components/growatt_modbus/device_profiles.py` (Lines 5-110)

Add the sensor key to the appropriate sensor group set:

```python
BATTERY_SENSORS: Set[str] = {
    "battery_voltage", "battery_current", "battery_soc",
    "battery_temp", "battery_power",
    "new_battery_sensor",  # ← Add here
    ...
}

GRID_SENSORS: Set[str] = {
    "grid_power", "grid_export_power",
    "grid_voltage",  # ← Or add here if it's a grid sensor
    ...
}
```

**Available sensor groups:**
- `BASIC_PV_SENSORS` - PV string sensors (voltage, current, power)
- `BASIC_AC_SENSORS` - AC output sensors
- `BATTERY_SENSORS` - Battery related sensors
- `GRID_SENSORS` - Grid import/export sensors
- `ENERGY_SENSORS` - Energy production sensors
- `TEMPERATURE_SENSORS` - Temperature sensors
- `STATUS_SENSORS` - Status and diagnostic sensors
- `THREE_PHASE_SENSORS` - Three-phase AC sensors
- `SPF_OFFGRID_SENSORS` - Off-grid specific sensors

**Why this matters:** Profiles in `INVERTER_PROFILES` compose these sensor groups (e.g., `sensors: BASIC_PV_SENSORS | BATTERY_SENSORS`). If the sensor isn't in the right group, it won't be included in any profile.

#### Step 5: Validate Across Project

**Run the validation script (REQUIRED):**
```bash
python3 validate_sensors.py --sensor your_sensor_name
```

This will automatically check:
- ✅ Register defined in profile
- ✅ Added to sensor.py SENSOR_DEFINITIONS
- ✅ Added to const.py SENSOR_DEVICE_MAP
- ✅ Added to profile 'sensors' set

**Additional manual checks:**

1. **Search for similar register names** to ensure consistency:
   ```bash
   grep -r "grid_voltage" custom_components/growatt_modbus/
   ```

2. **Verify no naming conflicts** in the profile:
   ```bash
   grep "'name': 'grid_voltage'" profiles/*.py
   ```

3. **Check if register needs special handling** in coordinator.py:
   - Signed value conversion?
   - Inversion (like battery power for SPF)?
   - Fallback logic (like battery voltage)?

4. **Update tests** (if applicable)

---

## Profile Management

### When to Create a New Profile

**Create a new profile when:**
- Inverter uses a different register range (e.g., 0-124 vs 3000-3124)
- Register addresses overlap but have different meanings
- Significantly different capabilities (e.g., battery vs no battery)

**Extend existing profile when:**
- Only adding optional sensors (e.g., PV3 for 3-string models)
- Different power ratings but same register map
- Minor firmware variations

### Profile Inheritance

Profiles can inherit from others using Python's `**` operator:

```python
SPH_8000_10000_HU = {
    'name': 'SPH/SPM 8000-10000TL-HU',
    'input_registers': {
        # Inherit base registers
        **SPH_7000_10000['input_registers'],

        # Add/override specific registers
        1086: {'name': 'bms_soc', 'scale': 1, 'unit': '%'},
    },
}
```

**Benefits:**
- Reduces code duplication
- Makes differences explicit
- Easier to maintain

**Risks:**
- Changes to base profile affect all children
- Must verify overrides don't break inheritance

### Protocol Versions

The integration supports two protocol families:

1. **Legacy Protocol** - Older models, 0-124 register range
2. **VPP V2.01** - Newer models, 31000+ registers, DTC codes

**Auto-detection logic:**
1. Try to read DTC code (register 30000)
2. If present, use DTC-to-profile mapping
3. If not, use legacy detection (PV voltage, range checks)

**When adding profiles:**
- Determine protocol version first
- Set `'offgrid_protocol': True` for SPF (prevents VPP register access)
- Use appropriate register ranges

---

## Critical Patterns & Conventions

### Register Naming Conventions

Register names are critical because they control fallback behavior:

#### Standard Names (Enable Fallback)
```python
'battery_voltage'          # Coordinator searches for this exact name
'battery_soc'              # Falls back through: soc → battery_soc
'battery_power_low'        # Falls back to: charge_power_low / discharge_power_low
```

#### Suffixed Names (Prevent Fallback)
```python
'battery_voltage_legacy'   # Coordinator won't find "battery_voltage"
'battery_soc_vpp'          # Coordinator won't find "battery_soc"
'battery_power_vpp_low'    # Coordinator won't find "battery_power_low"
```

**Use case for suffixes:**
When multiple register ranges have the same logical sensor but only one works:

```python
# MOD profile - VPP range doesn't respond, 3000+ range does
31200: {'name': 'battery_power_vpp_high', ...},  # Won't be found
31201: {'name': 'battery_power_vpp_low', ...},   # Won't be found
3178: {'name': 'battery_charge_power_high', ...}, # Will be found ✓
3179: {'name': 'battery_charge_power_low', ...},  # Will be found ✓
```

### 32-bit Paired Registers

Many registers are 32-bit values split across two 16-bit registers:

```python
77: {
    'name': 'battery_power_high',
    'scale': 1,
    'unit': '',
    'pair': 78,  # Points to low word
    'signed': True,
    'desc': 'Battery power (HIGH word)'
},
78: {
    'name': 'battery_power_low',
    'scale': 1,
    'unit': '',
    'pair': 77,  # Points to high word
    'combined_scale': 0.1,  # Scale after combining
    'combined_unit': 'W',   # Unit after combining
    'signed': True,
    'desc': 'Battery power (LOW word)'
},
```

**Key points:**
- Both registers must have `'pair'` pointing to each other
- The `_low` register typically has `combined_scale` and `combined_unit`
- Combined value = `(high << 16) | low`
- Apply `signed` conversion BEFORE scaling

### Sign Conventions

#### Standard Convention (VPP 2.01, Most Models)
```
Battery Power:
  Positive = Charging
  Negative = Discharging

Grid Power:
  Positive = Exporting to grid
  Negative = Importing from grid
```

#### SPF Exception (Off-Grid Inverters)
SPF uses **inverted convention** for battery power:
```
Battery Power (Hardware):
  Positive = Discharging  ❌
  Negative = Charging     ❌
```

**Solution:** Use negative scale to flip:
```python
78: {
    'name': 'battery_power_low',
    'combined_scale': -0.1,  # Negative scale inverts sign
    'signed': True,
}
```

**Why this matters:** Home Assistant and energy dashboards expect standard convention. SPF is the only exception.

### Device-Specific Scales

Some registers have different scales depending on the device:

```python
# SPF: Battery voltage uses 0.01 scale for precision
17: {'name': 'battery_voltage', 'scale': 0.01, 'unit': 'V'},

# SPH: Battery voltage uses 0.1 scale
13: {'name': 'battery_voltage', 'scale': 0.1, 'unit': 'V'},
```

**Always verify scale** by checking:
1. Official Modbus documentation
2. Actual register values vs expected values
3. Other similar models

---

## Testing & Validation

### Pre-Commit Validation

Before committing changes:

1. **Check syntax:**
   ```bash
   python3 -m py_compile custom_components/growatt_modbus/profiles/*.py
   python3 -m py_compile custom_components/growatt_modbus/*.py
   ```

2. **Search for register name** across project:
   ```bash
   grep -r "register_name" custom_components/
   ```

3. **Verify sensor appears in all required locations:**
   - Profile `'input_registers'` or `'holding_registers'`
   - Profile `'sensors'` set
   - `sensor.py` `SENSOR_DEFINITIONS`
   - `const.py` `SENSOR_DEVICE_MAP`

4. **Check for naming conflicts:**
   ```bash
   grep -E "^    [0-9]+:" profiles/sph.py | grep "register_address"
   ```

### Testing New Profiles

When adding a new profile:

1. **Test auto-detection** (if applicable):
   - Add DTC code to `auto_detection.py` DTC_MAP
   - Add refinement logic if needed (e.g., storage range check)
   - Test with diagnostic scanner

2. **Verify register readings:**
   - Use diagnostic service `growatt_modbus.read_register`
   - Check raw values match expected with correct scale
   - Verify 32-bit combined values

3. **Test with actual hardware** (if possible):
   - Use Universal Scanner diagnostic service
   - Verify all sensors appear
   - Check values are reasonable

4. **Document in release notes:**
   - Add profile to supported models list
   - Note any special considerations
   - Include known limitations

---

## Common Issues & Solutions

### Issue 1: Sensor Not Appearing

**Symptoms:** Register defined in profile, but sensor doesn't appear in HA

**Checklist:**
- ✅ Added to profile `'sensors'` set?
- ✅ Added to `sensor.py` `SENSOR_DEFINITIONS`?
- ✅ Added to `const.py` `SENSOR_DEVICE_MAP`?
- ✅ `attr` in sensor definition matches register `name`?
- ✅ Condition in sensor definition evaluates to true?

### Issue 2: Wrong Device Assignment

**Symptoms:** Sensor appears in wrong device (e.g., battery sensor in solar device)

**Solution:** Update `const.py` `SENSOR_DEVICE_MAP` to assign sensor to correct device type.

### Issue 3: Incorrect Values

**Symptoms:** Sensor shows wrong value (too high, too low, negative when should be positive)

**Common causes:**
1. **Wrong scale** - Check register documentation
2. **Missing signed flag** - Add `'signed': True` for signed registers
3. **Incorrect paired register** - Verify high/low word order
4. **Wrong combined_scale** - Check which register has combined_scale
5. **SPF sign inversion** - Use negative scale for battery_power

### Issue 4: Fallback Not Working

**Symptoms:** Sensor shows 0 or unavailable when fallback register has data

**Cause:** Register name includes suffix that blocks fallback

**Example:**
```python
# BAD - Won't fallback
31201: {'name': 'battery_power_vpp_low', ...},  # Coordinator looks for battery_power_low

# GOOD - Will fallback
31201: {'name': 'battery_power_low', ...},       # Coordinator finds it
```

**Solution:** Use standard names for registers that should participate in fallback, use suffixed names for registers that shouldn't.

### Issue 5: Profile Detection Fails

**Symptoms:** Auto-detection picks wrong profile

**Common causes:**
1. **DTC code not in mapping** - Add to `auto_detection.py`
2. **Refinement logic wrong** - Check range detection (storage, 3000+)
3. **Detection order wrong** - Storage range should be checked before PV3

**Solution:** Update `auto_detection.py` with correct logic:
```python
# CORRECT ORDER for SPH detection:
1. Check storage range (1000-1124) → SPH HU
2. Check PV3 voltage → SPH 7-10kW
3. No PV3 → SPH 3-6kW
```

### Issue 6: Breaking Existing Profiles

**Symptoms:** Update to one profile breaks others that inherit from it

**Prevention:**
1. **Check inheritance chains** before modifying base profiles
2. **Use overrides** instead of modifying shared definitions
3. **Test all child profiles** after base changes

**Solution:**
```python
# Don't modify base
BASE_PROFILE = {
    1044: {'name': 'priority_mode', 'scale': 1, ...}
}

# Override in child instead
CHILD_PROFILE = {
    **BASE_PROFILE,
    1044: {'name': 'priority', 'scale': 1, ...}  # Override
}
```

### Issue 7: MIC Micro Inverter Detection Failures

**Symptoms:** MIC 1000TL-X or other micro inverters (600W-3.3kW) detected as MIN 3000-6000TL-X or communication failures

**Common causes:**
1. **Wrong detection order** - Auto-detection checked MIN (3000+ range) before MIC (0-179 range)
2. **Serial/RTU converter misconfiguration** - Wrong timing or framing settings
3. **Model name not recognized** - Model string doesn't match patterns

**Solution 1: Verify correct profile selected**
- MIC uses 0-179 register range (legacy V3.05 protocol, 2013)
- MIN uses 3000+ register range (V1.39 protocol)
- These are completely different protocols - MIN profile won't work on MIC!

**Solution 2: Check serial/RTU converter settings (USR-DR164, etc.)**

For Modbus RTU over serial at 9600 baud:

```yaml
Required Settings:
- Baud Rate: 9600
- Data Bits: 8
- Parity: None
- Stop Bits: 1  ← NOT "CTSRTS" or "2"!
- Pack Interval: 50-100ms  ← NOT 20ms!

Common Mistakes:
❌ Stop Bit = "CTSRTS" → Hardware flow control not supported
❌ Pack Interval = 20ms → Too short for inverter processing
✅ Stop Bit = "1" → Standard Modbus framing
✅ Pack Interval = 50-100ms → Safe timing for 9600 baud
```

**Why timing matters for MIC:**
- Frame transmission at 9600 baud: ~10ms (8-10 bytes)
- MIC inverter processing time: 50-100ms (legacy protocol may be slower)
- Total round-trip: 100-150ms minimum
- Pack interval too short (20ms) cuts off inverter responses

**Frame timing calculation:**
```
At 9600 baud with 8N1:
- 1 bit time: 104 μs
- 1 byte (8+1+1): 1.04 ms
- Modbus read 1 register: ~8-10 bytes → 10ms transmission
- Inverter processing: 50-100ms
- Safe interval: 50-100ms between requests
```

**Solution 3: Manual profile selection**
If auto-detection fails, manually select correct profile:
- Navigate to: Settings → Devices & Services → Growatt Modbus → Configure
- Select: "MIC (0.6-3.3kW)" from dropdown
- Verify sensors: ~15-20 sensors (not 40+ like MIN)

**Expected MIC sensors:**
- PV1 voltage/current/power (single string only)
- AC voltage/current/power/frequency
- Energy today/total
- Inverter/IPM temperature
- Status/fault codes
- NO Grid sensors (MIC doesn't have grid monitoring)
- NO PV2/PV3 sensors (MIC is single string only)

**MIC model patterns recognized:**
```python
'MIC600', 'MIC750', 'MIC1000', 'MIC1500',
'MIC2000', 'MIC2500', 'MIC3000', 'MIC3300'
→ All map to: mic_600_3300tl_x
```

**Detection order (fixed in v0.2.7):**
```
1. Check OffGrid DTC (SPF prevention)
2. Check VPP DTC (register 30000)
3. Check model name
4. Check MIC range (0-179) ← NOW BEFORE MIN
5. Check MIN range (3000+)
6. Check SPH range (battery)
7. Check 3-phase (MOD/MID)
```

---

## Version Bumping Checklist

When preparing a release:

1. **Update version numbers:**
   - `manifest.json` - version field
   - `README.md` - version badges
   - `const.py` - VERSION constant (if exists)

2. **Update documentation:**
   - `RELEASENOTES.md` - Add new version section
   - Document all fixes and new features
   - Include upgrade notes if needed

3. **Commit with proper message:**
   ```
   Bump version to vX.Y.Z

   - Feature 1 description
   - Fix 1 description
   - Update 1 description
   ```

4. **Test before release:**
   - Verify import in Home Assistant
   - Check all changed sensors work
   - Test with at least one real device if possible

---

## Quick Reference: File Responsibilities

| File | Purpose | When to Update |
|------|---------|----------------|
| `profiles/*.py` | Register definitions | Adding/updating registers |
| `sensor.py` | Sensor entity definitions | Adding new sensors |
| `const.py` | Device assignments, categories | Assigning sensors to devices |
| `device_profiles.py` | Profile registry | Adding new profiles |
| `auto_detection.py` | Auto-detection logic | New DTC codes, refinement logic |
| `coordinator.py` | Data processing | Special handling, fallback logic |
| `diagnostic.py` | Scanner/diagnostics | Detection improvements |

---

## Final Notes

**Remember:** This is a multi-device integration with complex fallback logic. Changes in one area can affect others unexpectedly.

**When in doubt:**
1. Search the codebase for similar patterns
2. Check how existing registers are handled
3. Test with diagnostic tools before deploying
4. Document architectural decisions in commit messages

**For AI Assistants:**
- Follow this guide completely for every register update
- Double-check all 5 steps in the checklist
- Search for similar patterns before implementing
- Ask user to verify if uncertain about device assignments

---

*Last updated: 2026-01-29*
*Integration version: 0.2.7*
