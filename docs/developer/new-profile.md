# Creating a New Inverter Profile

Use this guide when you have an inverter model that the integration does not currently support and you want to contribute support for it. The process involves four things: writing the register map, registering the profile, wiring up auto-detection, and verifying sensor output.

---

## Is a new profile the right approach?

A new profile is needed when the register map is materially different from existing profiles — different address ranges, different register meanings, or a different protocol family altogether. If your model is close to an existing one (same family, different power rating), check whether the existing profile simply works and only minor adjustments are needed.

The supported families and their register characteristics:

| Family | Protocol | Register range | Notes |
| --- | --- | --- | --- |
| SPH (single-phase hybrid) | Legacy / VPP V2.01 | 0–124 + 1000–1124 + 31000+ | Most common hybrid |
| MIN (single-phase string) | V1.39 / VPP V2.01 | 0–124 / 3000–3124 + 31000+ | Grid-tied only |
| MIC (micro inverter) | Legacy V3.05 / V1.39 | 0–179 | Single MPPT |
| MOD / MID (three-phase) | V1.39 / VPP V2.01 | 3000–3417 + 31000+ | 3-phase hybrid / string |
| SPH-TL3 (three-phase hybrid) | VPP V2.01 | 1000–1124 + 31000+ | 3-phase SPH |
| SPF (off-grid) | SPF protocol | 0–124 | **Never read VPP registers — causes power reset** |
| SPE (off-grid, SPF variant) | SPF protocol | 0–99 | |
| WIT (commercial 3-phase) | VPP V2.02 | 3000–3417 + 31000+ | Proprietary VPP variant |
| SPA (AC-coupled storage) | VPP V2.01 | 2000–2124 + 1000–1124 | Battery-only, no PV |

**Critical safety rule for off-grid (SPF/SPE) profiles:** Reading VPP registers (30000+, 31000+) causes an immediate power reset on these inverters. Any new off-grid profile must set `'offgrid_protocol': True` in its definition — this flag prevents the coordinator from ever issuing VPP register reads.

---

## Step 1 — Map the registers

### Identify the protocol and register ranges

Check what protocol documentation covers your model:

- **VPP V2.01 / V2.02** — WIT, SPH, MIN, MOD, MID, TL-XH models (newer firmware)
  - See [VPP Protocol Reference](protocol-vpp.md)
  - Input registers start at 31000; holding registers start at 30000
- **V1.39** — Covers WIT, SPH, SPA, MIN, MOD, MID, MAX, MAC
  - See [V1.39 Protocol Reference](protocol-v139.md)
  - Legacy address ranges (0–249, 875–999, 1000–1249, 3000–3417)
- **SPF off-grid protocol** — SPF and SPE series
  - See [Off-Grid Protocol Reference](protocol-offgrid.md)
- **Protocol Database** — Register scan data contributed by users
  - See [Protocol Database](protocol-database.md)

### Scan your inverter

Use the diagnostic scanner to confirm which registers actually respond before writing the profile:

1. In Home Assistant, call the `growatt_modbus.scan_registers` service
2. Note which addresses return non-zero values at the expected scale
3. Cross-reference with the protocol documentation for your family

Do not define registers that return 0 or error on your hardware — the integration supports many models and a register that looks correct in spec may not be wired up in your firmware variant.

---

## Step 2 — Write the profile file

### Where to add it

If your model is a variant of an existing family, add it to the existing family file (`profiles/sph.py`, `profiles/min.py`, etc.). If it is a genuinely different family, create a new file.

### Profile dict structure

```python
MY_NEW_MODEL = {
    'name': 'MyBrand 5000TL-X',
    'description': 'Single-phase hybrid inverter (5kW), 2 PV strings',
    'notes': 'Uses 0-124 legacy range. Confirmed on firmware v1.23.',

    'input_registers': {
        # Single 16-bit register
        0:  {'name': 'inverter_status', 'scale': 1,   'unit': '',   'desc': '0=Waiting, 1=Normal, 3=Fault'},
        3:  {'name': 'pv1_voltage',     'scale': 0.1, 'unit': 'V'},
        4:  {'name': 'pv1_current',     'scale': 0.1, 'unit': 'A'},

        # 32-bit paired registers — both words required
        5:  {'name': 'pv1_power_high',  'scale': 1,   'unit': '',   'pair': 6},
        6:  {'name': 'pv1_power_low',   'scale': 1,   'unit': '',   'pair': 5,
             'combined_scale': 0.1, 'combined_unit': 'W'},

        # Signed register (negative values possible)
        14: {'name': 'battery_current', 'scale': 0.1, 'unit': 'A',  'signed': True,
             'desc': '+ charging, - discharging'},

        # VPP shared registers (unpack from vpp_v201.py if applicable)
        **VPP_V201_STATUS,
        **VPP_V201_PV2_INPUT,
    },

    'holding_registers': {
        # Writable registers — only include confirmed writable registers
        1044: {'name': 'priority_mode', 'scale': 1, 'unit': '',
               'desc': '0=Load First, 1=Battery First, 2=Grid First'},
    },
}
```

### Using VPP shared blocks

If your model supports VPP V2.01 registers (31000+ range) and is a standard single-phase or three-phase variant, import and unpack the shared blocks from `profiles/vpp_v201.py` rather than duplicating them:

```python
from .vpp_v201 import (
    VPP_V201_STATUS,
    VPP_V201_PV2_INPUT,
    VPP_V201_PV2_TOTAL,
    VPP_V201_ENERGY_1P,
    VPP_V201_TEMPERATURE_1P,
    VPP_V201_BATTERY2,
    VPP_V201_HOLDING_1P,
)
```

Then unpack with `**VPP_V201_STATUS` etc. inside your `input_registers` or `holding_registers` dict. Only use blocks whose registers you have confirmed responding on your hardware — do not speculatively include blocks.

### Register naming conventions

Names drive fallback behaviour in the coordinator. Use the canonical names that the coordinator knows about:

```
battery_voltage     battery_current     battery_soc
pv1_voltage         pv1_current         pv1_power_low
inverter_status     inverter_temp       fault_code
energy_today_low    energy_total_low    ac_voltage
```

If your model has a register at an unusual address that shadows a canonical name from another range, suffix it with `_vpp` or `_legacy` to prevent the coordinator from mistakenly treating it as the primary source:

```python
# Falls back correctly — coordinator finds 'battery_power_low'
3179: {'name': 'battery_power_low', ...},

# Blocked from fallback — coordinator won't find 'battery_power_vpp_low'
31201: {'name': 'battery_power_vpp_low', ...},
```

### Off-grid flag

Off-grid models (SPF, SPE) must include this at the profile dict level:

```python
MY_SPF_MODEL = {
    'name': 'SPF 5000ES',
    'offgrid_protocol': True,   # REQUIRED — prevents VPP register access
    'input_registers': { ... },
    'holding_registers': { ... },
}
```

---

## Step 3 — Register the profile

### Add to INVERTER_PROFILES

**File:** `custom_components/growatt_modbus/device_profiles.py`

Add an entry to `INVERTER_PROFILES`. The key becomes the profile identifier used throughout the codebase:

```python
INVERTER_PROFILES = {
    ...
    "my_new_model_5000tl_x": {
        "name": "MyBrand 5000TL-X",
        "description": "Single-phase hybrid inverter (5kW)",
        "register_map": "MY_NEW_MODEL",      # Must match the dict name in profiles/
        "phases": 1,                          # 1 or 3
        "has_pv3": False,                     # Third PV string
        "has_battery": True,                  # Battery storage
        "max_power_kw": 5.0,
        "protocol_version": "v2.01",          # or "v1.39", "legacy", "offgrid"
        "sensors": HYBRID_1P_SENSORS,         # Sensor set — see below
    },
    ...
}
```

### Choosing a sensor set

Use the smallest composite group that covers the model's capabilities:

| Inverter type | `sensors` value |
| --- | --- |
| Single-phase hybrid (battery) | `HYBRID_1P_SENSORS` |
| Three-phase hybrid (battery) | `HYBRID_3P_SENSORS` |
| Single-phase grid-tied (no battery) | `GRID_TIED_1P_SENSORS` |
| Off-grid | `HYBRID_1P_SENSORS \| SPF_OFFGRID_SENSORS` |
| Minimal (add groups individually) | `BASIC_PV_SENSORS \| BASIC_AC_SENSORS \| ENERGY_SENSORS \| ...` |

If your model has PV3, add `\| PV3_SENSORS`. If it has BMS data, add `\| BMS_SENSORS`. The composite groups are defined in `device_profiles.py` — read the comments to understand what each includes.

### Import the register dict

At the top of `device_profiles.py`, import your new dict:

```python
from .profiles.my_file import MY_NEW_MODEL
```

Then add the register map to the lookup that the coordinator uses to resolve `"register_map"` strings:

```python
REGISTER_MAPS = {
    ...
    "MY_NEW_MODEL": MY_NEW_MODEL,
    ...
}
```

---

## Step 4 — Wire up auto-detection

### DTC code (preferred — VPP models)

If your model supports VPP V2.01 and has a DTC code in holding register 30000, add it to `dtc_map` in `auto_detection.py`:

```python
dtc_map = {
    ...
    5999: 'my_new_model_5000tl_x',   # MyBrand 5000TL-X
    ...
}
```

Get the DTC code by reading register 30000 from your inverter using the diagnostic service. If the DTC code returns 0 or errors, your model either doesn't support VPP or uses a different detection method.

### Model name matching (fallback)

If DTC detection isn't available (legacy protocol models), add a model name pattern to `detect_profile_from_model_name()` in `auto_detection.py`:

```python
patterns = {
    ...
    "MYBRAND5000TLX": "my_new_model_5000tl_x",
    "MYBRAND5000TL":  "my_new_model_5000tl_x",
    ...
}
```

The function normalises the model string (uppercase, strips spaces and hyphens) before matching. Add the normalised form of what your inverter actually returns.

### Off-grid detection

Off-grid (SPF/SPE) models are detected before VPP detection runs to prevent VPP register access. Add to the off-grid DTC section in `auto_detection.py`:

```python
dtc_map = {
    ...
    3499: 'my_spf_model',    # SPF variant — uses off-grid protocol
    ...
}
```

The caller ensures off-grid models are detected via their own DTC registers (not register 30000).

### Manual selection fallback

Even if auto-detection doesn't work, users can manually select a profile during setup. As long as `INVERTER_PROFILES` has the entry, it will appear in the manual selection list. This is acceptable for rare or prototype models.

---

## Step 5 — Add sensors for new registers

Any register you define in the profile that doesn't have a matching `GrowattData` field and `SENSOR_DEFINITIONS` entry won't appear in Home Assistant. Follow the [Adding Sensors](adding-sensors.md) guide for each new register name you introduced.

The sensor side is identical whether you're adding to an existing profile or a new one.

---

## Step 6 — Validate and syntax-check

```bash
# Syntax-check everything you touched
python -m py_compile custom_components/growatt_modbus/profiles/*.py
python -m py_compile custom_components/growatt_modbus/device_profiles.py
python -m py_compile custom_components/growatt_modbus/auto_detection.py

# Validate all sensors the new profile references
python validate_sensors.py --profile my_new_model_5000tl_x
```

The profile validator checks that every sensor key in the profile's `sensors` set has a `SENSOR_DEFINITIONS` entry and a `SENSOR_DEVICE_MAP` assignment.

---

## Checklist summary

```
□ Register map dict written in profiles/<family>.py
□ VPP shared blocks used where applicable (not duplicated)
□ offgrid_protocol: True set for SPF/SPE models
□ Profile entry added to INVERTER_PROFILES in device_profiles.py
□ Register map imported and added to REGISTER_MAPS lookup
□ DTC code added to dtc_map in auto_detection.py (VPP models)
    OR model name pattern added to detect_profile_from_model_name() (legacy)
□ GrowattData fields added for all new register names (Step 2 of Adding Sensors)
□ SENSOR_DEFINITIONS entries added for all new sensors (Step 3)
□ SENSOR_DEVICE_MAP assignments added (Step 4)
□ Sensor group memberships added (Step 5)
□ Syntax check passes on all modified files
□ validate_sensors.py --profile passes
□ At least one confirmed hardware scan attached to the PR
```

---

## PR guidance

When opening a pull request for a new profile:

- Attach the register scan output that confirms which registers respond on your hardware. Reference the issue number if one exists.
- Note the firmware version the scan was performed on.
- If you have access to only a subset of the model's registers (e.g., no battery), say so — partial profiles are accepted provided they don't silently break anything.
- If DTC detection was not possible, explain why and confirm that manual selection works.
