# Fork Review: linksu79/Growatt_ModbusTCP

**Fork URL:** https://github.com/linksu79/Growatt_ModbusTCP
**Review Date:** 2026-02-05
**Reviewer:** Claude (via GitHub Issue Analysis)

## Executive Summary

This fork adds comprehensive **WIT VPP Remote Control** capabilities that are currently missing from the main repository. The changes are well-structured, follow Home Assistant best practices, and have been field-tested by the fork maintainer. The improvements are complementary to our v0.3.1 critical fix and address the "write" side of WIT battery control while v0.3.1 addresses the "read" side.

**Recommendation:** Integrate these changes with minor modifications for consistency.

---

## Key Improvements in Fork

### 1. VPP Remote Control Implementation (NEW FEATURE)

**Files Modified:**
- `const.py` - Register definitions
- `number.py` - Power rate slider entity
- `select.py` - Work mode selector entity

**Functionality Added:**
- **Work Mode Select** (register 202): Standby / Charge / Discharge
- **Active Power Rate Number** (register 201): 0-100% power command
- **Export Limit Number** (register 203): 0-20000W zero-export control

**Key Features:**
1. Work mode re-assertion before power rate writes (field-tested requirement)
2. 0.4s delay between register writes for ShineWiLan compatibility
3. Coordinator state tracking: `wit_last_work_mode`, `wit_last_power_rate`
4. Automatic power rate re-application when work mode changes
5. WIT-specific entity creation separate from generic auto-generation

### 2. Improved pymodbus Compatibility

**File:** `growatt_modbus.py`

**Changes:**
```python
# Old (single try):
result = self.client.write_register(address=register, value=value, device_id=self.slave_id)

# New (fallback chain):
try:
    result = self.client.write_register(address=register, value=value, unit=self.slave_id)
except TypeError:
    try:
        result = self.client.write_register(address=register, value=value, slave=self.slave_id)
    except TypeError:
        # ... more fallbacks
```

**Benefit:** Handles different pymodbus versions (3.0+, 2.x, legacy) gracefully

### 3. WIT Profile Refinements

**File:** `profiles/wit.py`

**Changes:**
1. Register 3: `active_power_rate` → `max_output_power_rate` (clarification)
2. Battery power scale: Already matches main repo (1.0)
3. Battery temp registers 31222-31224: Remapped based on field observations

---

## Detailed Analysis by File

### A. `const.py` - VPP Register Definitions

**Fork Approach:**
```python
'active_power_rate': {
    'register': 201,
    'scale': 1,
    'valid_range': (0, 100),
    'unit': '%',
    'desc': 'VPP remote active power command (percent) – requires work_mode'
},
'work_mode': {
    'register': 202,
    'scale': 1,
    'valid_range': (0, 2),
    'options': {
        0: 'Standby',
        1: 'Charge',
        2: 'Discharge'
    },
    'desc': 'VPP remote work mode / command'
},
'export_limit_w': {
    'register': 203,
    'scale': 1,
    'valid_range': (0, 20000),
    'unit': 'W',
    'desc': 'Export limit in watts (0 = zero export)'
},
```

**Main Repo Status:** These controls don't exist yet

**Recommendation:** ✅ Integrate with minor naming adjustments for consistency

---

### B. `number.py` - Active Power Rate Control

**Key Implementation Details:**

1. **WIT Detection:**
```python
is_wit = str(register_map_name).upper() == "WIT_4000_15000TL3"
if is_wit:
    if 203 in holding_registers:
        entities.append(GrowattWitExportLimitWNumber(coordinator, config_entry))
    if 201 in holding_registers:
        entities.append(GrowattWitActivePowerRateNumber(coordinator, config_entry))
    return  # Early return to prevent auto-generation conflicts
```

2. **Work Mode Re-Assertion Logic:**
```python
async def async_set_native_value(self, value: float) -> None:
    raw_value = int(max(0, min(int(value), 100)))

    # Re-assert last known work_mode if we have it
    last_mode = getattr(self.coordinator, "wit_last_work_mode", None)
    if last_mode is None:
        _LOGGER.warning("[WIT] work_mode not set yet. Set Work Mode first")
    else:
        _LOGGER.debug("[WIT] Re-asserting work_mode (202) = %s", last_mode)

    # If we have a non-standby mode, write it first
    if isinstance(last_mode, int) and last_mode in (1, 2):
        ok_mode = await self.hass.async_add_executor_job(
            self.coordinator.modbus_client.write_register,
            202,
            last_mode,
        )
        # ShineWiLan / WIT often benefits from a short delay between writes
        await asyncio.sleep(0.4)

    success = await self.hass.async_add_executor_job(
        self.coordinator.modbus_client.write_register,
        201,
        raw_value,
    )

    if success:
        setattr(self.coordinator, "wit_last_power_rate", raw_value)
```

**Analysis:**
- ✅ Field-tested approach (work mode must be asserted before power rate is effective)
- ✅ Proper state tracking in coordinator
- ✅ 0.4s delay matches empirical ShineWiLan requirements
- ✅ Graceful handling when work_mode not yet set

**Recommendation:** ✅ Integrate as-is (proven field logic)

---

### C. `select.py` - Work Mode Control

**Key Implementation:**

1. **Work Mode Select Entity:**
```python
class GrowattWitWorkModeSelect(CoordinatorEntity, SelectEntity):
    """WIT VPP: Work mode / remote command (holding register 202)."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:battery-clock"
    _attr_options = ["Standby", "Charge", "Discharge"]
```

2. **Power Rate Re-Application Logic:**
```python
async def async_select_option(self, option: str) -> None:
    value_map = {"Standby": 0, "Charge": 1, "Discharge": 2}
    value = value_map.get(option)

    # ... write work_mode to register 202 ...

    if success:
        setattr(self.coordinator, "wit_last_work_mode", int(value))

        # If we have a previously set power rate (>0), re-apply it after
        # setting work_mode. This matches field-tested manual sequences.
        last_power = getattr(self.coordinator, "wit_last_power_rate", None)
        if isinstance(last_power, int) and last_power > 0 and value in (1, 2):
            await asyncio.sleep(0.4)
            await self.hass.async_add_executor_job(
                self.coordinator.modbus_client.write_register,
                201,
                last_power,
            )
```

**Analysis:**
- ✅ Bidirectional coordination: number.py re-asserts work_mode, select.py re-applies power_rate
- ✅ Matches field-tested manual control sequences
- ✅ Proper state management
- ⚠️ Early return removes WIT from generic auto-generation (intentional design)

**Recommendation:** ✅ Integrate as-is

---

### D. `growatt_modbus.py` - Write Compatibility

**Changes:**

```python
# Multi-fallback approach for different pymodbus versions
result = None
try:
    result = self.client.write_register(address=register, value=value, unit=self.slave_id)
except TypeError:
    try:
        result = self.client.write_register(address=register, value=value, slave=self.slave_id)
    except TypeError:
        try:
            result = self.client.write_register(address=register, value=value, device_id=self.slave_id)
        except TypeError:
            result = self.client.write_register(register, value)

if result is None:
    logger.error('[WRITE] No response from write_register call')
    return False

if hasattr(result, 'isError') and callable(getattr(result, 'isError')) and result.isError():
    logger.error(f"[WRITE] Inverter responded with error: {result}")
    return False
```

**Analysis:**
- ✅ Handles pymodbus 3.x (`unit=`), 2.x (`slave=`), and legacy versions
- ✅ Better error handling for different response types
- ⚠️ Main repo currently only supports `device_id=` parameter

**Recommendation:** ✅ Integrate (improves compatibility)

---

### E. `profiles/wit.py` - Profile Refinements

**Changes:**

1. **Register 3 Rename:**
```python
# Old:
3: {'name': 'active_power_rate', 'scale': 1, 'unit': '%', 'access': 'RW'},

# New:
3: {'name': 'max_output_power_rate', 'scale': 1, 'unit': '%', 'access': 'RW'},
```

2. **Battery Power Scale (31200-31201):**
```python
# Fork has: combined_scale: 1.0
# Main repo also has: 1.0 (fixed in v0.1.3)
```
✅ Already aligned

3. **Battery Temp/SOH Registers (31222-31224):**
```python
# Old (main repo):
31222: {'name': 'battery_soh_vpp', 'scale': 1, 'unit': '%'},
31223: {'name': 'battery_temp', 'scale': 0.1, 'unit': '°C'},
31224: {'name': 'battery_temp_max', 'scale': 0.1, 'unit': '°C'},

# New (fork):
31222: {'name': 'battery_temp_vpp', 'scale': 0.1, 'unit': '°C', 'maps_to': 'battery_temp'},
31223: {'name': 'battery_temp_alt', 'scale': 0.1, 'unit': '°C'},
# 31224 removed
```

**Analysis:**
- ⚠️ Fork user observed different register mapping than VPP spec
- ⚠️ Needs validation with user register scans before adopting
- ⚠️ Could be variant-specific

**Recommendation:** ⏸️ Hold pending user validation

---

## Compatibility with v0.3.1 Critical Fix

### Our v0.3.1 Fix (Read-Side)
- Prevents permanent skipping of WIT 31200-31224 battery range
- Ensures battery power/SOC registers keep being attempted
- Critical for battery monitoring

### Fork's VPP Control (Write-Side)
- Adds work mode and power rate control entities
- Implements register write sequencing
- Critical for battery control

**Result:** ✅ **Fully complementary** - v0.3.1 fixes reads, fork adds writes

---

## Integration Recommendations

### Phase 1: Core VPP Control (IMMEDIATE)

**Files to integrate:**
1. ✅ `const.py` - Add VPP register definitions
2. ✅ `number.py` - Add `GrowattWitActivePowerRateNumber`, `GrowattWitExportLimitWNumber`
3. ✅ `select.py` - Add `GrowattWitWorkModeSelect`
4. ✅ `growatt_modbus.py` - Add pymodbus version fallbacks

**Testing Required:**
- Verify work_mode → power_rate write sequence
- Confirm 0.4s delay is necessary
- Test with different pymodbus versions (3.0+, 2.x)
- Validate export_limit functionality

### Phase 2: Profile Refinements (VALIDATE FIRST)

**Files to consider:**
1. ⏸️ `profiles/wit.py` - Register 3 rename (minor, low priority)
2. ⏸️ `profiles/wit.py` - Battery temp/SOH remapping (needs validation)

**Validation needed:**
- Request register scans from multiple WIT users
- Check if 31222 is temp or SOH across variants
- Determine if this is variant-specific or universal

---

## Code Quality Assessment

**Strengths:**
- ✅ Follows Home Assistant entity patterns correctly
- ✅ Proper use of `CoordinatorEntity` base class
- ✅ WIT-specific logic isolated (doesn't affect other profiles)
- ✅ Comprehensive logging with `[WIT]` prefixes
- ✅ Field-tested with real hardware

**Minor Issues:**
- ⚠️ Uses broad `except Exception` in some places (could be more specific)
- ⚠️ Magic number `0.4` for delay (could be constant with explanation)

**Verdict:** Production-ready with minor polish opportunities

---

## Comparison with Main Repo Conventions

| Aspect | Fork Approach | Main Repo Convention | Recommendation |
|--------|---------------|----------------------|----------------|
| Entity naming | `GrowattWit*` prefix | `Growatt*` prefix with profile detection | Use fork's explicit naming |
| WIT detection | `is_wit = "WIT_4000_15000TL3"` | Profile name in register map | Keep fork's approach (clearer) |
| State tracking | Coordinator attributes | Coordinator data object | Fork's approach OK (simpler) |
| Delay handling | Hardcoded `0.4s` | No existing pattern | Add as configurable constant |
| Error logging | `[WIT]` prefix | Standard logging | Keep prefix (useful) |

---

## Risk Assessment

**Low Risk:**
- VPP control additions don't affect existing functionality
- WIT-specific code paths have early returns (isolated)
- Pymodbus fallbacks are backwards compatible

**Medium Risk:**
- Battery temp/SOH register remapping (needs validation)
- Register 3 rename (could confuse existing automations)

**Mitigation:**
- Phase integration (core control first, profile changes later)
- Comprehensive changelog and migration notes
- Request user testing before release

---

## Recommended Integration Plan

### Step 1: Prepare Branch
```bash
git checkout -b feat/wit-vpp-control
```

### Step 2: Integrate Core VPP Control
1. Add VPP registers to `const.py`
2. Add WIT number entities to `number.py`
3. Add WIT work mode select to `select.py`
4. Add pymodbus compatibility to `growatt_modbus.py`
5. Update `RELEASENOTES.md` with comprehensive feature description

### Step 3: Testing Checklist
- [ ] WIT user can set work mode (Standby/Charge/Discharge)
- [ ] WIT user can adjust power rate (0-100%)
- [ ] Work mode changes automatically re-apply last power rate
- [ ] Power rate changes automatically re-assert work mode
- [ ] 0.4s delay between writes is respected
- [ ] Export limit control works (if applicable)
- [ ] No impact on non-WIT profiles
- [ ] Works with pymodbus 3.0+ and 2.x

### Step 4: Documentation Updates
- [ ] Update README with WIT VPP control instructions
- [ ] Add example automations for battery management
- [ ] Document work_mode + power_rate relationship
- [ ] Explain zero-export configuration

### Step 5: Release as v0.4.0
- Feature release (new VPP control capabilities)
- Builds on v0.3.1 critical fix
- Target: WIT users with Home Battery Systems

---

## User Feedback from Fork

**From fork maintainer:**
- Work mode MUST be set before power rate is effective (field-tested)
- 0.4s delay between writes required for ShineWiLan reliability
- Power rate should be re-applied when work mode changes (automation use case)
- Export limit useful for zero-export configurations

**From fork users:**
- VPP control working reliably in production
- No reported issues with the implementation

---

## Conclusion

The linksu79 fork provides **production-ready WIT VPP remote control** that fills a critical gap in the main repository. The code quality is high, the approach is field-tested, and the changes are complementary to our v0.3.1 fix.

**Primary Recommendation:**
✅ **Integrate Phase 1 (Core VPP Control) into main repo as v0.4.0**

**Secondary Recommendation:**
⏸️ **Defer Phase 2 (Profile Refinements) pending user validation**

This integration will give WIT users complete battery control capabilities:
- v0.3.1: Reliable battery monitoring (read)
- v0.4.0: VPP remote control (write)

Together, these enable full Home Battery System integration with Home Assistant.

---

## Questions for Fork Maintainer (Optional)

1. Have you observed the 0.4s delay requirement on all WIT inverters or specific variants?
2. What happens if power_rate is set without work_mode? (Does it fail silently or error?)
3. Have you tested export_limit functionality? (Register 203)
4. Battery temp register remapping (31222): Was this observed on all WIT units?

---

**End of Fork Review**
