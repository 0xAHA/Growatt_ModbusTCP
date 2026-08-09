# DTC Detection Debugging Guide

## What to Look For in Home Assistant Logs

After reducing log verbosity, the DTC detection process is now clearly visible with these markers:

### ✅ Success Path

```
INFO - Starting automatic inverter type detection
INFO - ✓ DTC Detection - Read DTC code: 5400 from holding register 30000
INFO - ✓ DTC Detection - Matched DTC code 5400 to profile 'mod_6000_15000tl3_xh'
INFO - ✓ Auto-detected from DTC code 5400: MOD 6000-15000TL3-XH
```

### ⚠️ Failure Indicators

**DTC Read Failed:**
```
INFO - Starting automatic inverter type detection
WARNING - Failed to read DTC code from register 30000: [error details]
INFO - DTC and model name detection failed, trying register-based detection...
```

**DTC Returns Zero:**
```
INFO - Starting automatic inverter type detection
WARNING - DTC code register 30000 returned 0 or invalid value: 0
INFO - DTC and model name detection failed, trying register-based detection...
```

**Unknown DTC Code:**
```
INFO - ✓ DTC Detection - Read DTC code: 9999 from holding register 30000
WARNING - ✗ DTC Detection - Unknown DTC code: 9999 (not in supported models)
INFO - DTC and model name detection failed, trying register-based detection...
```

## Valid DTC Codes

DTC codes are read from holding register 30000 (VPP models) or register 43 (legacy models). Each code maps to a specific profile.

Model names below follow Growatt VPP 2.03 protocol documentation, Table 3-1.

### Reading the Status column

The DTC is read from your inverter, so it identifies the **model** reliably. Whether the **profile** we point that model at is correct for it is a separate question:

| Status | Meaning |
|--------|---------|
| ✅ Confirmed | A real device reporting this DTC has been seen running this profile, and the confirmation is traceable to an issue or register scan. |
| ⚠️ Unconfirmed | The mapping comes from Growatt's model table only. It has never been checked against hardware. Sensors may be missing, or present but meaningless. |

An unconfirmed mapping is not necessarily wrong — most are probably fine. It means nobody has verified it. If your model shows ⚠️, a [register scan](diagnostic-service.md) attached to a GitHub issue is what turns it into ✅.

These statuses live in `DTC_REGISTRY` in `auto_detection.py`, which is the single source of truth; this page is checked against it by the test suite.

### Legacy Protocol (register 43, no VPP support)

| DTC Code | Model Series | Profile | Status |
|----------|-------------|---------|--------|
| 210 | MIC 2500-5500MTL-S | mic_2500_5500mtl_s | ✅ Confirmed (#304) |
| 2049 | TL3-S 3000-15000 | tl3_s_3000_15000 | ✅ Confirmed (#299) |

### SPF Series — Off-Grid (register 43)

> ⚠️ Off-grid inverters will **reset** if VPP registers (30000+, 31000+) are accessed. The integration skips those ranges automatically when an SPF DTC is detected.

| DTC Code | Model Series | Profile | Status |
|----------|-------------|---------|--------|
| 3400 | SPF 3000-6000 ES PLUS | spf_3000_6000_es_plus | ⚠️ Unconfirmed |
| 3401 | SPF 3000-6000 ES PLUS (variant) | spf_3000_6000_es_plus | ⚠️ Unconfirmed |
| 3402 | SPF 3000-6000 ES PLUS (variant) | spf_3000_6000_es_plus | ⚠️ Unconfirmed |
| 3403 | SPF 3000-6000 ES PLUS (variant) | spf_3000_6000_es_plus | ⚠️ Unconfirmed |

### SPH / SPA Series — Single-Phase Hybrid

> **SPA owners, please read.** SPA models are AC-coupled battery storage with **no solar DC inputs**. Every SPA code below currently maps to an **SPH** profile, which includes PV sensors — so you will see PV entities that read zero permanently. They are not faulty; your inverter has no MPPT inputs for them to measure. A dedicated SPA profile is in progress ([#360](https://github.com/0xAHA/Growatt_ModbusTCP/issues/360)).

| DTC Code | Model Series | Profile | Status |
|----------|-------------|---------|--------|
| 3501 | SPH 3000-6000TL BL | sph_3000_6000_v201 | ⚠️ Unconfirmed |
| 3502 | SPH 3000-6000TL BL-UP | sph_3000_6000_v201 | ✅ Confirmed (#337) |
| 3503 | SPH 3000-6000TL HU | sph_3000_6000_v201 | ⚠️ Unconfirmed |
| 3504 | SPH 3000-6000TL HUB | sph_3000_6000_v201 | ✅ Confirmed (#286) |
| 3601 | SPH 4-10KTL3 BH-UP | sph_tl3_3000_10000_v201 | ✅ Confirmed (#210) |
| 3701 | SPA 1000-3000TL BL | sph_3000_6000_v201 | ⚠️ Unconfirmed — SPH profile on SPA hardware |
| 3715 | SPA 3000-6000TL AU | sph_3000_6000_v201 | ⚠️ Unconfirmed — SPH profile on SPA hardware |
| 3716 | SPA 3000-6000TL AUB | sph_3000_6000_v201 | ⚠️ Unconfirmed — SPH profile on SPA hardware |
| 3725 | SPA 4-10KTL3 BH-UP | sph_tl3_3000_10000_v201 | ⚠️ Unconfirmed — SPH profile on SPA hardware |
| 3735 | SPA 3000TL BL-UP | sph_3000_6000_v201 | ⚠️ Unconfirmed — SPH profile on SPA hardware |
| 21303 | SPH/SPM 8000-10000TL-HU | sph_8000_10000_hu | ✅ Confirmed (scan #303) |

### SPE Series — Single-Phase Hybrid (SPF protocol, 8-12 kW)

| DTC Code | Model Series | Profile | Status |
|----------|-------------|---------|--------|
| 64541 | SPE 8000-12000 ES | spe_8000_12000_es | ✅ Confirmed (scan #212) |

### MIN / MIC Series — Single-Phase Grid-Tied / Hybrid

| DTC Code | Model Series | Profile | Status |
|----------|-------------|---------|--------|
| 5100 | MIN 2500-6000TL-XH/XH2/XHE/XA | tl_xh_3000_10000_v201 | ✅ Confirmed (#71) |
| 5200 | MIC 600-3300TL-X/X2/X2(Pro); MIN 2500-6000TL-X/X2/X2(Pro)/X2(Pro.E) | min_3000_6000_tl_x_v201 | ⚠️ Unconfirmed — refined at runtime by per-MPPT energy check |
| 5201 | MIN 7-10KTL-X/X2/X2(E) | min_7000_10000_tl_x_v201 | ✅ Confirmed (MIN 10000TL-X, DTC from legacy holding 43) |

### MOD / MID / MAC Series — Three-Phase Hybrid / Grid-Tied

| DTC Code | Model Series | Profile | Status |
|----------|-------------|---------|--------|
| 5400 | MOD 3-10KTL3-XH/BP; MID 11-30KTL3-XH; MID 8-15KTL3-XHL/JP | mod_6000_15000tl3_xh_v201 | ✅ Confirmed (#313, #362) |
| 5401 | MOD 3-15KTL3-HU; MID 33-50KTL3-HU | mod_6000_15000tl3_xh_v201 | ✅ Confirmed (scan #228) |
| 5001 | MID 17-25KTL3-X; MID 20-30KTL3-X2; MID 25-30KTL3-X2 Pro/X2 Pro.E; MID 33-50KTL3-X2/X2 Pro/X2 Pro.E; MID 30-40KTL3-X; MID 33-36KTL3-X(Pro.E); MID 3-33KTL3-X3 | mid_15000_25000tl3_x_v201 | ✅ Confirmed (#242) |
| 5002 | MOD 3-15KTL3-X; MOD 3-15KTL3-X2(Pro); MOD 12-20KTL3-X2; MOD 12-20KTL3-X2(E); MOD 3-33KTL3-X3 | mid_15000_25000tl3_x_v201 | ⚠️ Unconfirmed |
| 5003 | MAC 30-70KTL3-X; MAC 15-36KTL3-XL; MAC 50-70KTL3-X2; MAC 30-36KTL3-XL2 | mid_15000_25000tl3_x_v201 | ⚠️ Unconfirmed — no dedicated MAC profile |

### MAX / MAX-X Series — Large Commercial Grid-Tied

> No MAX device has been seen by this integration. These map to the MID profile as the closest available — per Table 3-1, MAX/MAX-X do not use battery or energy-storage registers, so they belong with the grid-tied group above. **All four are unverified guesses.** If you own one, a register scan would be genuinely valuable.

| DTC Code | Model Series | Profile | Status |
|----------|-------------|---------|--------|
| 5000 | MAX 50-100KTL3 LV/MV | mid_15000_25000tl3_x_v201 | ⚠️ Unconfirmed — no MAX profile exists |
| 5500 | MAX 175-253KTL3-X HV | mid_15000_25000tl3_x_v201 | ⚠️ Unconfirmed — no MAX profile exists |
| 5501 | MAX 80-150KTL3-X LV/MV; MAX 100-150KYL3-X2 LV/MV | mid_15000_25000tl3_x_v201 | ⚠️ Unconfirmed — no MAX profile exists |
| 5502 | MAX 320-350KTL3-X | mid_15000_25000tl3_x_v201 | ⚠️ Unconfirmed — no MAX profile exists |

### WIT / WIS Series — Three-Phase Commercial Hybrid

| DTC Code | Model Series | Profile | Status |
|----------|-------------|---------|--------|
| 5601 | WIT 29.9-50K-XHU | wit_29900_50000tl3_xhu | ✅ Confirmed (scan #338) |
| 5600 | WIS 100K-AM; WIT 50-100K-H/HE/HU/A/AE/AU (incl. -US); WIT 28-55K-H/HE/HU/A/AE/AU-US L2 | wit_29900_50000tl3_xhu | ⚠️ Unconfirmed — interim; VPP 31200+ not available on 100K-HU ([#349](https://github.com/0xAHA/Growatt_ModbusTCP/issues/349)) |
| 5603 | WIT 4-15kW | wit_4000_15000tl3 | ✅ Confirmed (#335) |
| 5800 | WIS 210K | mid_15000_25000tl3_x_v201 | ⚠️ Unconfirmed — uses MID profile |
| 5801 | WIS 215K-AM | mid_15000_25000tl3_x_v201 | ⚠️ Unconfirmed — uses MID profile |

## How to View Logs in Home Assistant

### Method 1: Via UI
1. Go to Settings → System → Logs
2. Search for "DTC Detection"
3. Look for ✓ or ✗ markers

### Method 2: Via Log File
```bash
# View live logs
tail -f /config/home-assistant.log | grep "DTC"

# Search recent logs
grep "DTC Detection" /config/home-assistant.log | tail -20

# Full detection sequence
grep -A 5 "Starting automatic inverter type detection" /config/home-assistant.log | tail -30
```

## Common Issues and Solutions

### Issue 1: DTC Read Fails Immediately

**Symptom:**
```
WARNING - Failed to read DTC code from register 30000: [ModbusIOException]
```

**Possible Causes:**
- Emulator not running or not accessible
- Wrong host/port in HA configuration
- Firewall blocking connection
- Modbus device ID mismatch

**Debug Steps:**
```bash
# Test from HA machine
python3 test_modbus_dtc.py --host <emulator-ip> --port 502

# Check network connectivity
ping <emulator-ip>
telnet <emulator-ip> 502
```

### Issue 2: DTC Returns Zero

**Symptom:**
```
WARNING - DTC code register 30000 returned 0 or invalid value: 0
```

**Possible Causes:**
- Emulator profile doesn't define DTC default value
- Register 30000 not implemented in holding registers
- Reading from wrong register type (input vs holding)

**Debug Steps:**
1. Check emulator is serving register 30000:
   ```bash
   python3 test_dtc_code.py
   ```
2. Verify it's a HOLDING register (not input)
3. Check MOD profile has `default: 5400` for register 30000

### Issue 3: Connection Works in Modbus Poll but Not HA

**Symptom:**
- Modbus Poll can read DTC code 5400
- HA logs show "Failed to read DTC code"

**Possible Causes:**
- Device ID mismatch (HA using different ID than Modbus Poll)
- Timeout too short in HA
- Register address offset issue

**Debug Steps:**
1. Check device ID in both tools:
   - Modbus Poll: usually shown in connection settings
   - HA: check config entry or use device_id=1
2. Increase timeout in HA config
3. Verify register address is exactly 30000 (not 30001 or 29999)

### Issue 4: Unknown DTC Code

**Symptom:**
```
WARNING - ✗ DTC Detection - Unknown DTC code: 5400 (not in supported models)
```

**Possible Causes:**
- Integration doesn't have 5400 mapped to a profile
- Old version of integration

**Solution:**
Check `auto_detection.py` has this mapping:
```python
dtc_map = {
    ...
    5400: 'mod_6000_15000tl3_xh',  # MOD-XH\MID-XH
    ...
}
```

## Testing DTC Detection

### Test 1: Verify Emulator Serves DTC
```bash
python3 test_dtc_code.py
```

Expected output:
```
✓ Model loaded: MOD 6000-15000TL3-XH
✓ Simulated value: 5400
✓ CORRECT! DTC code 5400 for MOD series
```

### Test 2: Test Modbus Connection
```bash
python3 test_modbus_dtc.py --host localhost --port 502
```

Expected output:
```
✓ Connected successfully
✓ Valid DTC code: MOD-XH/MID-XH
Value: 5400
```

### Test 3: Watch HA Logs Live
```bash
# In one terminal - watch logs
tail -f /config/home-assistant.log | grep -E "DTC|auto.*detect"

# In another terminal - reload integration
# (via HA UI: Settings → Integrations → Growatt → Reload)
```

## What Changed

### Before (Verbose):
```
INFO - Fixed config entry to store register map key: MOD_6000_15000TL3_XH
INFO - Identified register map as: MOD_6000_15000TL3_XH
INFO - Initialized Growatt client with register map: MOD_6000_15000TL3_XH
INFO - Midnight callback registered for daily total resets
INFO - Read serial number: GRW12345678
INFO - Read firmware version: 1.39
INFO - Read inverter type: MOD-15000TL3-XH
INFO - Read protocol version: VPP 2.01
INFO - Detected 3-phase hybrid - SPH TL3 or MOD series
INFO - Detected 31200 range (VPP Protocol) - MOD series
```

### After (Clean):
```
INFO - Starting automatic inverter type detection
INFO - ✓ DTC Detection - Read DTC code: 5400 from holding register 30000
INFO - ✓ DTC Detection - Matched DTC code 5400 to profile 'mod_6000_15000tl3_xh'
INFO - ✓ Auto-detected from DTC code 5400: MOD 6000-15000TL3-XH
INFO - Midnight reset triggered - storing previous day totals
```

Routine operations are now at DEBUG level - enable debug logging if needed:
```yaml
logger:
  default: info
  logs:
    custom_components.growatt_modbus: debug
```
