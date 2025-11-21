# Auto-Detection System

The integration automatically detects your inverter model using the Growatt VPP Protocol V2.01 standard.

## 🎯 How It Works

Auto-detection follows a **4-step priority system**:

### Step 1: DTC Code Detection (Primary - V2.01 Inverters)
Reads the **Device Type Code** from register `30000` (VPP 2.01 Protocol).

✅ **Advantages:**
- Most reliable method
- Official Growatt identification
- Confirms V2.01 protocol support

❌ **Limitations:**
- Only available on V2.01-capable inverters
- Some models share DTC codes (refinement needed)

### Step 2: DTC Refinement (When Needed)
For models sharing the same DTC code, additional register checks differentiate them:

| Shared DTC | Models | Check Register | Decision Logic |
|------------|--------|----------------|----------------|
| **3502** | SPH 3-6kW<br>SPH 7-10kW | 31018 (V2.01 PV3)<br>11 (Legacy PV3) | Has PV3 → 7-10kW<br>No PV3 → 3-6kW |
| **5200** | MIC<br>MIN 3-6kW | 31010 (V2.01 MIN range)<br>3003 (Legacy MIN range) | Readable → MIN<br>Not readable → MIC |
| **5400** | MOD<br>MID | 31217 (V2.01 Battery SOC)<br>3169 (Legacy Battery voltage) | Readable → MOD<br>Not readable → MID |
| **5100** | TL-XH<br>TL-XH US | N/A | Both use same profile |

### Step 3: Model Name Detection
If DTC unavailable, reads model name string from holding registers and pattern-matches against known models.

### Step 4: Register Range Probing (Legacy Fallback)
If DTC and model name unavailable, probes different register ranges to identify the inverter series:

**Detection Patterns:**
- **MIN Series:** Tests register 3003 (PV1 voltage in 3000 range)
  - If readable → MIN detected
  - Tests register 3011 (PV3): Readable = 7-10kW, Not readable = 3-6kW
- **Hybrid Models:** Tests register 3169 (battery voltage)
  - If readable → Hybrid model (SPH/TL-XH/MOD)
  - Tests 3-phase registers: Determines MOD/SPH-TL3 vs single-phase hybrid
- **MID Series:** Tests 3-phase grid-tied registers (38, 42)
- **MIC Series:** Tests base range (0-124) without 3000 range

**Result:** Logs medium/low confidence detection - works for most legacy inverters!

---

## 📋 Official DTC Code Table

Based on **Growatt VPP Protocol V2.01 - Table 3-1**:

| Model Series | DTC Code | Protocol | Battery | Legacy Registers | Notes |
|--------------|----------|----------|---------|------------------|-------|
| **SPH 3000-6000TL BL** | 3502 | V2.01 | Yes | 0-124, 1000-1124 | Single-phase hybrid |
| **SPA 3000-6000TL BL** | 3735 | V2.01 | Yes | 0-124 | SPA variant of SPH |
| **SPH 4000-10000TL3 BH-UP** | 3601 | V2.01 | Yes | 0-124, 1000-1124 | Three-phase hybrid |
| **SPA 4000-10000TL3 BH-UP** | 3725 | V2.01 | Yes | 0-124 | SPA variant |
| **MIN 2500-6000TL-XH/XH(P)** | 5100 | V2.01 | No | 0-124 | Covers TL-XH series |
| **MIC/MIN 2500-6000TL-X/X2** | 5200 | V2.01 | No | 0-179 (MIC)<br>3000-3124 (MIN) | Shared code |
| **MIN 7000-10000TL-X/X2** | 5201 | V2.01 | No | 3000-3124 | Grid-tied, 3 PV strings |
| **MOD-XH / MID-XH** | 5400 | V2.01 | MOD: Yes<br>MID: No | 0-124, 3000+ (MOD)<br>0-124 (MID) | Shared code |
| **WIT 100KTL3-H** | 5601 | V2.01 | No | Uses MID profile | Large commercial |
| **WIS 215KTL3** | 5800 | V2.01 | No | Uses MID profile | Large commercial |

---

## 🔍 Detection Examples

### Example 1: MOD Inverter (V2.01)
```
1. Read register 30000 → DTC = 5400
2. DTC 5400 maps to MOD/MID (shared)
3. Check register 31217 (Battery SOC) → Readable
4. Result: MOD 6000-15000TL3-XH (V2.01) ✅
5. Protocol version: "Protocol 2.01" (from register 30099)
```

### Example 2: MIN 7-10kW (V2.01)
```
1. Read register 30000 → DTC = 5201
2. DTC 5201 maps to MIN 7-10kW (unique code)
3. No refinement needed
4. Result: MIN Series 7-10kW (V2.01) ✅
5. Protocol version: "Protocol 2.01"
```

### Example 3: Legacy MIN (Register Probing)
```
1. Read register 30000 → Not readable (No DTC)
2. Try model name detection → Not readable
3. Start register probing:
   - Test register 3003 → Readable (MIN series confirmed)
   - Test register 3011 → Readable (PV3 present = 7-10kW)
4. Result: MIN Series 7-10kW (Legacy) ✅
5. Protocol version: "Protocol Legacy"
6. Confidence: Medium (register probing)
```

### Example 4: Manual Selection Required (Rare)
```
1. Read register 30000 → Not readable (No DTC)
2. Try model name detection → Not readable
3. Register probing → Inconclusive
4. Manual selection required → User selects from legacy profile list
5. Result: Selected model ✅
6. Protocol version: "Protocol Legacy"
```

---

## ⚙️ Configuration Flow

### Auto-Detection Success
```
Connect → Read DTC → Identify Model → Show Confirmation
                                         ↓
                            "Detected: MOD 6000-15000TL3-XH (V2.01)"
                                         ↓
                            [✅ Accept] or [🔧 Choose Different]
```

### Auto-Detection Fallback (Legacy)
```
Connect → Read DTC → Failed → Try Model Name → Failed
                                         ↓
                              Register Probing
                                         ↓
                       ┌─────────────────┴─────────────────┐
                       ↓                                   ↓
                  Success (Medium confidence)         Failed (Rare)
                       ↓                                   ↓
         Show Confirmation Screen              Show Manual Selection
"Detected: MIN 7-10kW (Legacy)"         "Please select your model"
         ↓                                         ↓
[✅ Accept] or [🔧 Choose Different]     [Select from legacy profiles]
```

The manual selection list **only shows legacy profiles** because:
- If V2.01 was supported, auto-detection would have succeeded
- DTC register (30000) not readable = Legacy protocol only

---

## 🛠️ Troubleshooting Auto-Detection

### "Auto-detection failed"
**Causes:**
- Inverter uses legacy protocol (no DTC register)
- Communication issues
- Incorrect Modbus settings

**Solution:**
1. Manually select your inverter series from the list
2. Legacy profile will be used automatically
3. Check logs for specific error details

### "Wrong model detected"
**Causes:**
- Shared DTC code with failed refinement
- Non-standard firmware

**Solution:**
1. In integration options, change inverter series manually
2. Report issue with logs to help improve detection

### Protocol Version Shows "Legacy" but Should Be V2.01
**Cause:**
- Register 30099 not implemented in firmware
- Read error

**Note:**
- Protocol version is informational only
- Integration will still work correctly
- V2.01 registers are included in profile regardless

---

## 📊 Detection Statistics

After successful detection, check **Device Info** in Home Assistant:

| Field | Example | Source |
|-------|---------|--------|
| **Model** | MOD-15000TL3-XH | Register 125-132 (parsed) |
| **Serial Number** | AB12345678 | Register 23-27 or 3000-3015 |
| **Firmware Version** | 2.01 | Register 9-11 |
| **Hardware Version** | Protocol 2.01 | Register 30099 (VPP version) |

---

## 🔬 For Developers

### Adding New DTC Codes

Edit `/custom_components/growatt_modbus/auto_detection.py`:

```python
dtc_map = {
    # Add new code
    XXXX: 'profile_key_v201',  # Description
}
```

### Testing Auto-Detection

Use the emulator with specific DTC codes:
```bash
python3 growatt_emulator.py
# Select model with V2.01 profile
# DTC code will be served from profile default
```

Check logs:
```
✓ Auto-detected from DTC code 5400: MOD 6000-15000TL3-XH (V2.01)
Detected V2.01 battery SOC register (31217) - MOD series
Detected protocol version: Protocol 2.01 (register 30099 = 201)
```

---

[← Back to README](../README.md)
