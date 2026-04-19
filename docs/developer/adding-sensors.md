# Adding Sensors to an Existing Profile

Use this guide when you want to expose a register that is already present in the inverter's Modbus map but not yet appearing in Home Assistant — either because the register was never wired up, or because a firmware update added new data.

If your inverter model is not supported at all, see [Creating a New Profile](new-profile.md) first.

---

## Before you start

Check that the register actually responds on your hardware using the diagnostic scanner (`growatt_modbus.read_register` service or the Universal Register Scanner). Many registers listed in the protocol spec are model-specific or firmware-gated and return 0 or error on hardware that doesn't support them. Confirm a live non-zero reading before wiring up a sensor.

Also search the codebase to make sure the sensor doesn't already exist under a different name:

```bash
grep -r "your_register_name" custom_components/growatt_modbus/
```

---

## Six steps — all required

### Step 1 — Add the register definition

**File:** `custom_components/growatt_modbus/profiles/<family>.py`

Add an entry to `input_registers` or `holding_registers`:

```python
# Single 16-bit register
93: {'name': 'inverter_temp', 'scale': 0.1, 'unit': '°C', 'signed': True},

# 32-bit value — both words required, pointing at each other via 'pair'
1: {'name': 'pv_total_power_high', 'scale': 1, 'unit': '', 'pair': 2},
2: {'name': 'pv_total_power_low',  'scale': 1, 'unit': '', 'pair': 1,
    'combined_scale': 0.1, 'combined_unit': 'W'},
```

**Key fields:**

| Field | Required | Notes |
| --- | --- | --- |
| `name` | Yes | Snake-case string. Must match the `GrowattData` field name exactly. |
| `scale` | Yes | Multiplier for the raw 16-bit value. Check the protocol spec carefully — scale errors produce values 10× or 100× off. |
| `unit` | Yes | Human-readable string (`'V'`, `'W'`, `'kWh'`, `'%'`, `''` for dimensionless). |
| `signed` | No | `True` for registers that hold signed (two's complement) values — e.g. battery current, temperature. Omitting this causes large negative readings to appear as huge positive numbers. |
| `pair` | No | Address of the other word in a 32-bit pair. Both words must have `pair` set. |
| `combined_scale` | No | Applied after combining high/low words into a 32-bit integer. Usually on the `_low` register. Can be negative to invert sign (SPF battery convention). |
| `combined_unit` | No | Unit string for the combined value. |
| `desc` | No | Free text — useful for scan evidence references. |

**VPP shared blocks:** If the register address is in the 30000–31999 range and the same register exists identically across multiple families, check `profiles/vpp_v201.py` first. If it already defines the register, your profile gets it automatically via the `**VPP_V201_*` unpacking — no duplicate definition needed.

---

### Step 2 — Add a field to GrowattData

**File:** `custom_components/growatt_modbus/growatt_modbus.py`

Add a field to the `@dataclass GrowattData` class:

```python
@dataclass
class GrowattData:
    # ... existing fields ...

    inverter_temp: float = 0.0       # °C — inverter heat sink temperature
    battery_soc:   float = 0.0       # % — state of charge
    fault_code:    int   = 0         # raw fault register value
    serial_number: str   = ""        # firmware version string
```

**This step is the most commonly forgotten.** Without the field, `hasattr(data, 'your_sensor_name')` returns `False` and any condition on that sensor silently fails — the sensor never appears in HA.

Type guidelines:
- `float = 0.0` — voltages, currents, power, energy, temperature, percentages
- `int = 0` — status codes, counts, mode selectors, raw bitfields
- `str = ""` — text fields such as firmware version or serial number

Group the new field with similar fields (battery fields together, PV fields together) rather than appending at the end.

---

### Step 3 — Add a sensor definition

**File:** `custom_components/growatt_modbus/sensor.py`

**First check whether a template helper already covers your sensor.** The file contains `_pv_string_sensors(n)` and `_phase_sensors(n)` that generate uniform entries for PV strings and three-phase AC sensors automatically. If you are adding `pv4_voltage`, `pv4_current`, `pv4_power` — they are generated, not hand-written. Search for the grep index comment at the top of the file.

For everything else, add an entry to `SENSOR_DEFINITIONS`:

```python
"battery_soc": {
    "name": "Battery State of Charge",
    "icon": "mdi:battery",
    "device_class": SensorDeviceClass.BATTERY,
    "state_class": SensorStateClass.MEASUREMENT,
    "unit": PERCENTAGE,
    "attr": "battery_soc",          # Must match GrowattData field name exactly
},
```

Optional fields:

```python
"bms_max_cell_volt": {
    ...
    "entity_category": EntityCategory.DIAGNOSTIC,   # Hides from main UI
    "condition": lambda data: data.bms_max_cell_volt > 0,  # Suppress if register absent
},
```

Common device classes and their canonical units:

| Measurement | `device_class` | `unit` |
| --- | --- | --- |
| Voltage | `SensorDeviceClass.VOLTAGE` | `UnitOfElectricPotential.VOLT` |
| Current | `SensorDeviceClass.CURRENT` | `UnitOfElectricCurrent.AMPERE` |
| Power | `SensorDeviceClass.POWER` | `UnitOfPower.WATT` |
| Energy | `SensorDeviceClass.ENERGY` | `UnitOfEnergy.KILO_WATT_HOUR` |
| Temperature | `SensorDeviceClass.TEMPERATURE` | `UnitOfTemperature.CELSIUS` |
| Frequency | `SensorDeviceClass.FREQUENCY` | `UnitOfFrequency.HERTZ` |
| Battery % | `SensorDeviceClass.BATTERY` | `PERCENTAGE` |

---

### Step 4 — Assign to a device

**File:** `custom_components/growatt_modbus/const.py`

Add the sensor key to the correct set in `SENSOR_DEVICE_MAP`:

```python
SENSOR_DEVICE_MAP = {
    DEVICE_TYPE_SOLAR:    { ..., "pv3_voltage", ... },
    DEVICE_TYPE_GRID:     { ..., "grid_export_power", ... },
    DEVICE_TYPE_LOAD:     { ..., "house_consumption", ... },
    DEVICE_TYPE_BATTERY:  { ..., "battery_soc", ... },
    DEVICE_TYPE_INVERTER: { ..., "inverter_temp", ... },
}
```

Assignment guidelines:

| Device | What belongs here |
| --- | --- |
| `DEVICE_TYPE_SOLAR` | PV string voltage/current/power, AC output, solar energy totals |
| `DEVICE_TYPE_GRID` | Grid import/export power, grid voltage/frequency |
| `DEVICE_TYPE_LOAD` | House consumption, load power |
| `DEVICE_TYPE_BATTERY` | Battery voltage/current/SOC/temperature/power, BMS data |
| `DEVICE_TYPE_INVERTER` | Status, fault codes, temperatures, diagnostics |

---

### Step 5 — Add to a sensor group

**File:** `custom_components/growatt_modbus/device_profiles.py`

Profiles compose their sensor set from sensor group constants. Add the sensor key to the appropriate group:

```python
BATTERY_SENSORS: Set[str] = {
    "battery_voltage", "battery_current", "battery_soc",
    "battery_temp", "battery_power",
    "your_new_sensor",   # ← add here
    ...
}
```

Available sensor groups:

| Group | Contents |
| --- | --- |
| `BASIC_PV_SENSORS` | PV1/PV2 voltage, current, power; total PV power |
| `PV3_SENSORS` | PV3 voltage, current, power, energy |
| `BASIC_AC_SENSORS` | Single-phase AC voltage, current, power, frequency |
| `THREE_PHASE_SENSORS` | R/S/T phase voltages, currents, powers; line voltages |
| `GRID_SENSORS` | `grid_power`, `grid_export_power`, `grid_import_power` |
| `POWER_FLOW_SENSORS` | `power_to_grid`, `power_to_load`, `power_to_user` |
| `CONSUMPTION_SENSORS` | `house_consumption`, `self_consumption` |
| `ENERGY_SENSORS` | `energy_today`, `energy_total` |
| `ENERGY_BREAKDOWN_SENSORS` | Grid/load energy today and total |
| `PV_DC_ENERGY_SENSORS` | `pv_energy_total`, per-string energy today |
| `PV_MPPT_TOTAL_SENSORS` | `pv1_energy_total`, `pv2_energy_total` (lifetime, per-MPPT) |
| `BATTERY_SENSORS` | SOC, voltage, current, power, charge/discharge energy |
| `BMS_SENSORS` | BMS status, error codes, cell voltage extremes |
| `TEMPERATURE_SENSORS` | `inverter_temp`, `ipm_temp`, `boost_temp` |
| `STATUS_SENSORS` | `status`, `fault_code`, `warning_code`, `derating_mode` |
| `SPF_OFFGRID_SENSORS` | Off-grid specific (load %, AC input, generator, fans) |
| `SPE_OFFGRID_SENSORS` | SPE 8000–12000 ES subset of SPF sensors |
| `WIT_EXTRA_SENSORS` | WIT multi-inverter extra output sensors |

The composite groups (`HYBRID_1P_SENSORS`, `HYBRID_3P_SENSORS`, `GRID_TIED_1P_SENSORS`) are unions of the above — if you add to any base group, the composites automatically include the new sensor.

**If no existing group fits**, add the sensor to an existing group with a comment, or — only if genuinely a new category — define a new group and add it to the relevant composite.

---

### Step 6 — Validate and syntax-check

```bash
# Validate the specific sensor across all files
python validate_sensors.py --sensor your_sensor_name

# Syntax-check the files you touched
python -m py_compile custom_components/growatt_modbus/profiles/*.py
python -m py_compile custom_components/growatt_modbus/growatt_modbus.py
python -m py_compile custom_components/growatt_modbus/sensor.py
python -m py_compile custom_components/growatt_modbus/const.py

# Confirm the sensor name appears in all expected places
grep -r "your_sensor_name" custom_components/growatt_modbus/
```

The validator checks:
- Register defined in at least one profile
- Key present in `SENSOR_DEFINITIONS`
- Key present in `SENSOR_DEVICE_MAP`
- Key present in at least one sensor group

---

## Common mistakes

| Symptom | Likely cause |
| --- | --- |
| Sensor never appears in HA | Forgot Step 2 — `GrowattData` field missing |
| Sensor appears but always unavailable | `attr` in `SENSOR_DEFINITIONS` doesn't match register `name` or `GrowattData` field name |
| Sensor appears in wrong device | Wrong assignment in `SENSOR_DEVICE_MAP` (Step 4) |
| Sensor defined but not in any profile | Forgot Step 5 — not added to any sensor group |
| Values 10× too high or too low | Wrong `scale` or `combined_scale` in register definition |
| Large positive value instead of negative | Missing `'signed': True` on the register |
| 32-bit value wrong | `pair` pointing to wrong address, or `combined_scale` on the wrong word |

---

## Quick reference

| What you're changing | File |
| --- | --- |
| Register address, scale, unit, sign | `profiles/<family>.py` |
| **Data field** (required — most often forgotten) | **`growatt_modbus.py`** |
| Display name, icon, device class, unit | `sensor.py` — `SENSOR_DEFINITIONS` |
| Which sub-device the sensor appears under | `const.py` — `SENSOR_DEVICE_MAP` |
| Which profiles include the sensor | `device_profiles.py` — sensor group constants |
