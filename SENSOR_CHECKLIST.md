# ✅ SENSOR ADDITION CHECKLIST

## Use this checklist EVERY TIME you add or update a sensor

### Sensor Name: `__________________`

---

## Required Steps (ALL must be completed)

### ☐ Step 1: Add Register Definition
**File:** `custom_components/growatt_modbus/profiles/[PROFILE].py`

Add to `'input_registers':` or `'holding_registers':` dict:
```python
XX: {'name': 'your_sensor_name', 'scale': X.X, 'unit': 'X', 'desc': '...'},
```

**Notes:**
- For 32-bit values: define both `_high` and `_low` with `pair` attribute
- For negative values: add `'signed': True`
- Check similar sensors for correct scale factor

---

### ☐ Step 2: Add to GrowattData Dataclass
**File:** `custom_components/growatt_modbus/growatt_modbus.py` (~lines 60-180)

Add field to the `@dataclass` definition:
```python
@dataclass
class GrowattData:
    """Container for Growatt inverter data"""
    # ... existing fields ...

    your_sensor_name: float = 0.0  # Units (description)
```

**⚠️ CRITICAL:** Without this field, `hasattr(data, 'your_sensor_name')` returns False and the sensor won't appear!

**Type Guidelines:**
- `float = 0.0` - For sensor values (voltage, current, power, energy, temperature, etc.)
- `int = 0` - For status codes, counts, or control registers
- `str = ""` - For text fields (firmware version, serial number)

**Where to add:**
- Group with similar sensors (e.g., battery fields together, PV fields together)
- Add comments to section headers for clarity

---

### ☐ Step 3: Add Sensor Definition
**File:** `custom_components/growatt_modbus/sensor.py` (~lines 40-700)

Add to `SENSOR_DEFINITIONS` dict:
```python
"your_sensor_name": {
    "name": "Display Name",
    "icon": "mdi:icon-name",
    "device_class": SensorDeviceClass.XXX,
    "state_class": SensorStateClass.MEASUREMENT,
    "unit": UnitOfXXX.XXX,
    "attr": "your_sensor_name",  # Must match register name!
},
```

**Device Classes:** VOLTAGE, CURRENT, POWER, ENERGY, TEMPERATURE, BATTERY, FREQUENCY
**Icons:** Browse at https://materialdesignicons.com/

---

### ☐ Step 4: Assign Device Type
**File:** `custom_components/growatt_modbus/const.py` (~lines 416-488)

Add sensor name to appropriate device in `SENSOR_DEVICE_MAP`:
```python
SENSOR_DEVICE_MAP = {
    DEVICE_TYPE_SOLAR: {..., 'your_sensor_name', ...},    # PV inputs, solar production
    DEVICE_TYPE_GRID: {...},                                # Grid import/export
    DEVICE_TYPE_LOAD: {...},                                # Consumption, load
    DEVICE_TYPE_BATTERY: {...},                             # Battery storage
    DEVICE_TYPE_INVERTER: {...},                            # Status, temps, faults
}
```

---

### ☐ Step 5: Add to Sensor Group
**File:** `custom_components/growatt_modbus/device_profiles.py` (~lines 5-110)

Add to appropriate sensor group:
```python
BASIC_PV_SENSORS: Set[str] = {..., 'your_sensor_name', ...}
BATTERY_SENSORS: Set[str] = {..., 'your_sensor_name', ...}
GRID_SENSORS: Set[str] = {..., 'your_sensor_name', ...}
# ... etc
```

**Available Groups:**
`BASIC_PV_SENSORS` `PV3_SENSORS` `BASIC_AC_SENSORS` `GRID_SENSORS`
`BATTERY_SENSORS` `BMS_SENSORS` `ENERGY_SENSORS` `TEMPERATURE_SENSORS`
`STATUS_SENSORS` `THREE_PHASE_SENSORS` `SPF_OFFGRID_SENSORS`

---

### ☐ Step 6: Validate

Run validation script:
```bash
python3 validate_sensors.py --sensor your_sensor_name
```

Expected output:
```
✓ Found in profile register definitions
✓ Found in sensor.py SENSOR_DEFINITIONS
✓ Found in const.py SENSOR_DEVICE_MAP
✓ Found in sensor groups
```

If any ❌ appears, go back and fix that step!

---

### ☐ Step 7: Final Checks

```bash
# Verify sensor appears everywhere
grep -r "your_sensor_name" custom_components/growatt_modbus/

# Check for similar sensors (consistency)
grep -r "similar_sensor" custom_components/

# Syntax check
python3 -m py_compile custom_components/growatt_modbus/profiles/*.py
python3 -m py_compile custom_components/growatt_modbus/*.py
```

---

## Common Mistakes

❌ **Forgot Step 2 (Dataclass)** - Most common! Code tries to set value but field doesn't exist → `hasattr()` fails, sensor shows "condition not met"
❌ **Forgot Step 5** - Sensor defined but not in any group → Won't appear in profiles
❌ **Wrong device_class** - Shows wrong icon/unit in HA
❌ **attr doesn't match register name** - Sensor shows "unavailable"
❌ **Forgot 'signed': True** - Negative values show as huge positive numbers
❌ **Wrong scale factor** - Values too high/low by 10x or 100x

---

## Quick Reference

| What | Where | Why |
|------|-------|-----|
| Register address, scale, unit | `profiles/*.py` | How to read from Modbus |
| **Data field declaration** | **`growatt_modbus.py`** | **Storage for sensor value** |
| Display name, icon, device_class | `sensor.py` | How to show in Home Assistant |
| Device assignment | `const.py` | Which sub-device to group under |
| Sensor group membership | `device_profiles.py` | Which profiles include this sensor |

---

**After completing all steps, copy this checklist into your commit message or PR description!**

For detailed documentation, see [claude.md](claude.md)
