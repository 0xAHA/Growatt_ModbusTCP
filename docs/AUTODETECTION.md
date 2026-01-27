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
| **5100** | TL-XH (standard)<br>MIN TL-XH (hybrid) | 3003 (MIN range)<br>31217 (Battery SOC in VPP range) | Has 3000+ range + battery → MIN TL-XH<br>No 3000+ range → Standard TL-XH |
| **5200** | MIC<br>MIN 3-6kW | 31010 (V2.01 MIN range)<br>3003 (Legacy MIN range) | Readable → MIN<br>Not readable → MIC |
| **5400** | MOD<br>MID | 31217 (V2.01 Battery SOC)<br>3169 (Legacy Battery voltage) | Readable → MOD<br>Not readable → MID |

### Step 3: Model Name Detection
If DTC unavailable, reads model name string from holding registers and pattern-matches against known models.

### Step 4: Register Range Probing (Legacy Fallback)
If DTC and model name unavailable, probes different register ranges to identify the inverter series:

**Detection Patterns:**
- **MIN Series:** Tests register 3003 (PV1 voltage in 3000 range)
  - If readable → MIN detected
  - Tests register 31217 (Battery SOC in VPP range): Readable = MIN TL-XH hybrid
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
| **SPH 3000-6000TL BL (legacy)** | 3501 | Legacy | Yes | 0-124, 1000-1124 | Pre-UP model, reg 30099 = 0 |
| **SPH 3000-6000TL BL -UP** | 3502 | V2.01 | Yes | 0-124, 1000-1124, 30000+, 31000+ | Upgraded model, reg 30099 = 201 |
| **SPF 3000-6000 ES PLUS** | 3400-3403 | V2.01 | Yes | 0-124, 31200+ | Off-grid with battery |
| **SPA 3000-6000TL BL** | 3735 | V2.01 | Yes | 0-124 | SPA variant of SPH |
| **SPH 4000-10000TL3 BH-UP** | 3601 | V2.01 | Yes | 0-124, 1000-1124 | Three-phase hybrid |
| **SPA 4000-10000TL3 BH-UP** | 3725 | V2.01 | Yes | 0-124 | SPA variant |
| **TL-XH 3000-10000** | 5100 | V2.01 | Yes | 0-124, 31200+ | Standard TL-XH (0-124 range) |
| **MIN TL-XH 3000-10000** | 5100 | V2.01 | Yes | 3000-3124, 31200+ | MIN series TL-XH (3000+ range) |
| **MIC/MIN 2500-6000TL-X/X2** | 5200 | V2.01 | No | 0-179 (MIC)<br>3000-3124 (MIN) | Shared code |
| **MIN 7000-10000TL-X/X2** | 5201 | V2.01 | No | 3000-3124 | Grid-tied, 3 PV strings |
| **MOD-XH / MID-XH** | 5400 | V2.01 | MOD: Yes<br>MID: No | 0-124, 3000+ (MOD)<br>0-124 (MID) | Shared code |
| **WIT 4000-15000TL3** | 5603 | V2.02 | Yes | 0-124, 8000+, 31000+ | Three-phase hybrid with advanced storage |
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

### Example 4: SPH Legacy Model (DTC with Protocol Check)
```
1. Read register 30000 → DTC = 3501
2. DTC 3501 maps to SPH 3000-6000TL BL
3. Check register 30099 (Protocol Version) → Returns 0
4. Protocol version 0 = Legacy protocol only
5. Convert profile: sph_3000_6000_v201 → sph_3000_6000 (legacy)
6. Result: SPH Series 3-6kW (Legacy) ✅
7. Battery controls use legacy registers (0-124 range)
```

**Why Protocol Check Matters:**
- DTC 3501 = Pre-UP model (legacy firmware)
- DTC 3502 = -UP model (V2.01 firmware)
- Both use register 30000, but only -UP supports V2.01 protocol
- Register 30099 confirms actual protocol support

### Example 5: Manual Selection Required (Rare)
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
