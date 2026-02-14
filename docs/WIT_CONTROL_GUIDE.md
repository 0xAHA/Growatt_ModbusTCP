# WIT Inverter Control Guide

## Understanding WIT Control Architecture

WIT (Wireless Inverter Technology) series inverters (4000-15000TL3) use a fundamentally different control model compared to SPH/SPF hybrid inverters. Understanding this difference is critical for stable battery management.

---

## Critical Difference: VPP Protocol vs Legacy Protocol

### SPH/SPF/MOD Models (Legacy Protocol)
- **Direct mode control**: Can set priority mode (Load First/Battery First/Grid First) via Modbus
- **Persistent settings**: Mode changes remain active until changed again
- **Simple control**: Write to register, mode changes immediately
- **Register range**: 1000+ (holding registers)

### WIT Models (VPP Protocol)
- **Time-limited overrides**: Control commands are temporary (duration-based)
- **Read-only base mode**: Register 30476 (priority_mode) shows TOU schedule default, cannot be changed via Modbus
- **VPP remote control**: Registers 201-202 and 30407-30409 for temporary overrides
- **Register range**: 30000+ (VPP protocol range)

---

## WIT Control Model Explained

### What You CAN Do:
✅ **Read** the current priority mode (register 30476) - shows TOU schedule default
✅ **Override** battery behavior temporarily using VPP remote control
✅ **Set** charge/discharge power and duration (30407-30409)
✅ **Monitor** all battery/inverter parameters

### What You CANNOT Do:
❌ **Change** the base priority mode via Modbus (register 30476 is read-only)
❌ **Permanently set** battery mode externally
❌ **Disable** TOU schedule via Modbus
❌ **Use** SPH-style persistent mode control

---

## Register 30476: Priority Mode (READ-ONLY)

**Common Misconception**: This register can be written to change WIT operating mode.

**Reality**: On WIT inverters, register 30476 is **read-only** and shows:
- The **default mode** used outside configured TOU periods
- What mode the inverter will return to when remote overrides expire
- Current TOU period mode if a schedule is active

**Values**:
- 0 = Load First (default)
- 1 = Battery First
- 2 = Grid First

**To change this value**: Must be configured via inverter display panel or manufacturer app, NOT Modbus.

---

## VPP Remote Control Registers (Proper WIT Control)

### Control Authority (Register 30100)
**Purpose**: Master enable/disable for VPP remote control
**Values**: 0 = Disabled, 1 = Enabled
**Note**: Must be enabled before using remote power control

### Remote Power Control (Registers 30407-30409)

#### Register 30407: Remote Power Control Enable
- 0 = Disabled
- 1 = Enabled (activates timed override)

#### Register 30408: Charging Time (Duration)
- Range: 0-1440 minutes (0-24 hours)
- How long the override remains active
- Timer starts when register 30407 is set to 1

#### Register 30409: Charge/Discharge Power
- Range: -100 to +100 (signed integer)
- Negative values = Discharge battery to grid
- Positive values = Charge battery from grid
- 0 = No charge/discharge (passthrough)

### Legacy VPP Registers (Registers 201-202)

#### Register 201: Active Power Rate
- Range: 0-100%
- Maximum power level for the operation

#### Register 202: Work Mode
- 0 = Standby
- 1 = Charge (from grid)
- 2 = Discharge (to grid)

---

## Proper WIT Control Patterns

### Pattern 1: Temporary Grid Charging (2-hour window)

1. Enable control authority (if not already enabled)
2. Set charging time: 120 minutes (register 30408)
3. Set charge power: +50 (50% charge, register 30409)
4. Enable remote control: 1 (register 30407)
5. After 2 hours, inverter automatically returns to base mode

### Pattern 2: Peak Shaving (discharge during high rates)

1. Set discharge power: -80 (80% discharge, register 30409)
2. Set duration: 180 minutes (3 hours, register 30408)
3. Enable remote control: 1 (register 30407)
4. Inverter discharges battery for 3 hours, then returns to normal

### Pattern 3: Cancel Active Override

1. Set remote control enable: 0 (register 30407)
2. Inverter immediately returns to base mode (TOU schedule or priority_mode default)

---

## Common Problems and Solutions

### Problem: Power Oscillation / Looping Behavior

**Symptoms**: Battery rapidly switches between charging and discharging

**Causes**:
1. Home Assistant automation writing to WIT controls too frequently
2. Multiple automations conflicting (TOU + manual control)
3. No rate limiting on control changes
4. Trying to write to read-only register 30476

**Solutions**:
- ✅ Use v0.4.6+ which includes 30s rate limiting
- ✅ Consolidate control logic into single automation
- ✅ Use time-based overrides with appropriate durations
- ✅ Don't write to register 30476 (it's read-only on WIT)

### Problem: Control Changes Don't Persist

**Symptoms**: Battery mode changes but reverts quickly

**Cause**: This is expected WIT behavior - overrides are time-limited

**Solution**:
- ✅ Set appropriate duration in register 30408
- ✅ Don't expect permanent mode changes like SPH inverters
- ✅ Use longer durations for extended operations

### Problem: Conflicts Between TOU and Remote Control

**Symptoms**: Inverter doesn't follow remote commands during certain times

**Cause**: TOU schedule periods override remote control

**Solution**:
- ✅ Check TOU schedule configuration on inverter
- ✅ Schedule remote overrides outside TOU periods
- ✅ Or disable TOU schedule entirely (via inverter panel)

---

## Rate Limiting (v0.4.6+)

To prevent oscillation and instability, v0.4.6 introduces **30-second rate limiting** on WIT control writes:

**How it works**:
- Integration tracks last write time for each WIT control register
- If you try to write within 30 seconds of previous write, request is blocked
- Warning logged: "Rate limit: WIT control writes must be 30s apart"

**Impact**:
- ✅ Prevents rapid automation loops
- ✅ Gives inverter time to respond to commands
- ✅ Reduces Modbus traffic and errors
- ⚠️ May delay rapid manual control changes (intentional)

**Bypass**: Wait 30 seconds between control changes (this is good practice anyway)

---

## Control Conflict Detection (v0.4.6+)

The integration now detects potential control conflicts:

**Checks**:
1. Multiple VPP remote control registers active simultaneously
2. TOU periods configured while remote control is active
3. Rapid control changes (rate limiting violations)

**Actions**:
- Warning logged to Home Assistant logs
- User notified via persistent notification (if enabled)
- No automatic remediation (user must resolve)

---

## Migration from SPH/SPF Control Logic

If you're used to SPH/SPF inverters and moving to WIT, here are key changes:

### SPH/SPF Approach (doesn't work on WIT):
```yaml
# DON'T DO THIS ON WIT
automation:
  - alias: "Set Battery First Mode"
    action:
      - service: number.set_value
        target:
          entity_id: select.growatt_priority_mode
        data:
          option: "Battery First"  # Won't persist on WIT!
```

### WIT Approach (correct):
```yaml
# DO THIS ON WIT
automation:
  - alias: "Discharge Battery for 3 Hours"
    action:
      # Set duration
      - service: number.set_value
        target:
          entity_id: number.growatt_remote_charging_time
        data:
          value: 180  # 3 hours

      # Set discharge power
      - service: number.set_value
        target:
          entity_id: number.growatt_remote_charge_discharge_power
        data:
          value: -80  # 80% discharge

      # Enable remote control
      - service: switch.turn_on
        target:
          entity_id: switch.growatt_remote_power_control
```

---

## Recommended WIT Control Setup

### 1. Enable VPP Control Authority (One-time setup)
```yaml
service: switch.turn_on
target:
  entity_id: switch.growatt_control_authority
```

### 2. Create Helper Input Numbers (for automation logic)
```yaml
# configuration.yaml
input_number:
  battery_override_duration:
    name: Battery Override Duration
    min: 0
    max: 1440
    step: 30
    unit_of_measurement: "min"

  battery_override_power:
    name: Battery Override Power
    min: -100
    max: 100
    step: 10
    unit_of_measurement: "%"
```

### 3. Create Automation Template
```yaml
automation:
  - alias: "WIT Battery Override"
    trigger:
      - platform: state
        entity_id: input_boolean.battery_override_active
        to: 'on'
    action:
      # Set duration from helper
      - service: number.set_value
        target:
          entity_id: number.growatt_remote_charging_time
        data:
          value: "{{ states('input_number.battery_override_duration') | int }}"

      # Set power from helper
      - service: number.set_value
        target:
          entity_id: number.growatt_remote_charge_discharge_power
        data:
          value: "{{ states('input_number.battery_override_power') | int }}"

      # Wait for rate limit (v0.4.6+)
      - delay:
          seconds: 2

      # Enable override
      - service: switch.turn_on
        target:
          entity_id: switch.growatt_remote_power_control
```

---

## Troubleshooting

### Enable Debug Logging
```yaml
# configuration.yaml
logger:
  default: info
  logs:
    custom_components.growatt_modbus: debug
```

### Check for Rate Limit Warnings
Look for: `[WIT CTRL] Rate limit: WIT control writes must be 30s apart`

### Verify Control Authority Status
Check entity: `switch.growatt_control_authority` (must be ON)

### Monitor Active Overrides
- `switch.growatt_remote_power_control` (shows if override active)
- `number.growatt_remote_charging_time` (shows remaining duration)
- `number.growatt_remote_charge_discharge_power` (shows current power setting)

---

## Summary

**Key Takeaways**:
1. WIT uses VPP protocol - time-limited overrides, not persistent mode changes
2. Register 30476 (priority_mode) is **read-only** on WIT
3. Use registers 30407-30409 for proper WIT control
4. Rate limiting (30s) prevents oscillation (v0.4.6+)
5. TOU schedule and remote control can conflict
6. Design automations for time-based operations, not permanent modes

**Best Practices**:
- ✅ Set appropriate duration for all overrides
- ✅ Wait 30+ seconds between control changes
- ✅ Use single automation for battery control (avoid conflicts)
- ✅ Monitor logs for rate limit warnings
- ✅ Test control changes during non-TOU periods first

---

## Further Reading

- [WIT Profile Documentation](../custom_components/growatt_modbus/profiles/wit.py)
- [Supported Models](MODELS.md)
- [VPP Protocol Overview](PROTOCOL_DATABASE_PROPOSAL.md)

---

**Version**: 0.4.6
**Last Updated**: 2026-02-14
