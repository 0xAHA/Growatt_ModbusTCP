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

| DTC Code | Model Series | Profile |
|----------|-------------|---------|
| 3502 | SPH 3000-6000TL BL | sph_3000_6000 |
| 3601 | SPH 4000-10000TL3 BH-UP | sph_tl3_3000_10000 |
| 5100 | MIN 2500-6000TL-XH | min_3000_6000_tl_x |
| 5200 | MIC/MIN 2500-6000TL-X | min_3000_6000_tl_x |
| 5201 | MIN 7000-10000TL-X | min_7000_10000_tl_x |
| 5400 | MOD-XH/MID-XH | mod_6000_15000tl3_xh |

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
