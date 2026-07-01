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

### What You CAN Do

✅ **Read** the current priority mode (register 30476) - shows TOU schedule default
✅ **Override** battery behavior temporarily using VPP remote control
✅ **Set** charge/discharge power and duration (30407-30409)
✅ **Monitor** all battery/inverter parameters

### What You CANNOT Do

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

> **EEPROM-safe:** Registers 30407, 30408, and 30409 are explicitly marked **"Not storage"** in the VPP V2.03 spec — they bypass non-volatile memory entirely. High-frequency writes (e.g., updating charge/discharge power every minute based on spot prices or live consumption) do not risk wearing out the inverter's flash memory. All other writable VPP registers ARE written to EEPROM and should not be written at high frequency.

#### Register 30407: Remote Power Control Enable
- 0 = Disabled
- 1 = Enabled (activates timed override)
- Resets to 0 on inverter reboot (built-in safety failsafe)

#### Register 30408: Charging Time (Duration)

- Range: 0–1440 minutes
- **0 = unlimited/continuous control** (no automatic timeout)
- 1–1440 = control active for this many minutes, then reverts
- Timer starts when register 30407 is set to 1

#### Register 30409: Charge/Discharge Power

- Range: -100 to +100 (signed integer, percentage of rated power)
- Negative values = Discharge battery / export to grid
- Positive values = Charge battery from grid/PV
- 0 = Suspend forced cycle (passthrough)

### Legacy VPP Registers (Registers 201-202)

#### Register 201: Active Power Rate
- Range: 0-100%
- Maximum power level for the operation

#### Register 202: Work Mode
- 0 = Standby
- 1 = Charge (from grid)
- 2 = Discharge (to grid)

---

## Timed vs Continuous Control

WIT remote control has two fundamentally different operating modes depending on register 30408:

| Mode | 30408 value | Behaviour |
| --- | --- | --- |
| **Timed** | 1–1440 min | Override active for exactly that many minutes, then inverter returns to base mode automatically |
| **Continuous** | 0 | Override stays active indefinitely — only cancelled by writing 30407=0 or an inverter reboot |

**Continuous mode (30408=0) is the right choice for:**

- Spot-price automations that adjust power in real time
- Energy management systems that control charge/discharge every minute
- Any scenario where you want HA to explicitly control the end of the session

**Timed mode (30408=1–1440) is the right choice for:**

- Simple time-bounded overrides ("charge for 2 hours")
- Set-and-forget operations that should self-cancel
- Cases where you want the inverter to recover on its own if HA goes offline

> **Safety note:** Register 30407 resets to 0 on inverter reboot or power cut. This is an intentional hardware failsafe — the inverter never stays in externally-commanded state across a restart. Design automations to re-enable remote control after an unexpected reboot if unattended operation is required.

---

## Write Order

Always write registers in this order to avoid momentary incorrect inverter state:

1. **30408** — set duration (or 0 for continuous)
2. **30409** — set charge/discharge power target
3. **30407** — enable remote control last

Enabling 30407 before setting 30409 puts the inverter under remote control with whatever power value was last in 30409 (which could be stale).

---

## Proper WIT Control Patterns

> **Entity names:** Replace `INVERTER` in all entity IDs with your integration entry name.
> Find it at **Settings → Devices & Services → Growatt Modbus** — it appears as the card title
> (e.g. if named "Growatt", IDs become `select.growatt_control_authority`, etc.).

### Pattern 1: Temporary Grid Charging (2-hour window)

```yaml
action:
  # 1. Set duration (BEFORE enabling)
  - action: number.set_value
    target:
      entity_id: number.INVERTER_remote_power_control_charging_time
    data:
      value: 120  # 2 hours

  # 2. Set charge power
  - action: number.set_value
    target:
      entity_id: number.INVERTER_remote_charge_and_discharge_power
    data:
      value: 50  # +50% = charge from grid at half rate

  # 3. Enable last
  - action: select.select_option
    target:
      entity_id: select.INVERTER_remote_power_control_enable
    data:
      option: Enabled
```

After 2 hours the inverter returns to base mode automatically (TOU schedule or self-consumption).

### Pattern 2: Peak Shaving / Grid Export (timed)

```yaml
action:
  - action: number.set_value
    target:
      entity_id: number.INVERTER_remote_power_control_charging_time
    data:
      value: 180  # 3 hours

  - action: number.set_value
    target:
      entity_id: number.INVERTER_remote_charge_and_discharge_power
    data:
      value: -80  # -80% = discharge battery / export to grid

  - action: select.select_option
    target:
      entity_id: select.INVERTER_remote_power_control_enable
    data:
      option: Enabled
```

### Pattern 3: Simple Cancel

```yaml
action:
  - action: select.select_option
    target:
      entity_id: select.INVERTER_remote_power_control_enable
    data:
      option: Disabled
```

Inverter returns to base mode immediately. Use this for timed sessions. For continuous sessions (30408=0) use [Pattern 5](#pattern-5-proper-termination-sequence-continuous-sessions) instead.

### Pattern 4: Continuous Control Session (30408=0)

Use this when HA will explicitly manage the entire session — spot-price automation, dynamic load following, or any case where you want HA to control the end state.

```yaml
# --- START continuous session ---
action:
  # Duration = 0 means unlimited (no auto-expiry)
  - action: number.set_value
    target:
      entity_id: number.INVERTER_remote_power_control_charging_time
    data:
      value: 0

  # Initial power target
  - action: number.set_value
    target:
      entity_id: number.INVERTER_remote_charge_and_discharge_power
    data:
      value: -50  # -50% discharge

  - action: select.select_option
    target:
      entity_id: select.INVERTER_remote_power_control_enable
    data:
      option: Enabled
```

Once the session is active, **only update 30409** to change power. You do NOT need to re-touch 30407 or 30408:

```yaml
# --- MID-SESSION power update (every minute, spot price changed) ---
action:
  - action: number.set_value
    target:
      entity_id: number.INVERTER_remote_charge_and_discharge_power
    data:
      value: "{{ new_power_target | int }}"
  # remote_power_control_enable and charging_time are unchanged — session stays active
```

End a continuous session with [Pattern 5](#pattern-5-proper-termination-sequence-continuous-sessions).

### Pattern 5: Proper Termination Sequence (Continuous Sessions)

Simply disabling 30407 (`remote_power_control_enable`) is not sufficient for clean termination of a continuous session — the inverter may not immediately release forced battery state, causing stray power flows. The correct sequence is to revoke `control_authority` first, then disable remote control.

A 35-second delay between the two steps is required to prevent Modbus command collisions while the inverter processes the state change.

```yaml
# Triggered when: export session is done (SOC target reached, price changed, etc.)
action:
  - if:
      - condition: state
        entity_id: select.INVERTER_control_authority
        state: Enabled
    then:
      # Optional: set a helper to signal that a handover is in progress
      - action: input_boolean.turn_on
        target:
          entity_id: input_boolean.wit_session_active

      # 1. Revoke grid control authority — forces inverter back to local self-consumption mode
      - action: select.select_option
        target:
          entity_id: select.INVERTER_control_authority
        data:
          option: Disabled

      # 2. Wait for inverter to process the state change
      - delay: "00:00:35"

      # 3. Disable remote power control (register 30407 → 0)
      - action: select.select_option
        target:
          entity_id: select.INVERTER_remote_power_control_enable
        data:
          option: Disabled

      # Clear helper flag
      - action: input_boolean.turn_off
        target:
          entity_id: input_boolean.wit_session_active
```

> **Why two steps?** `control_authority` (register 30100) is the master VPP compliance switch. Disabling it immediately drops the inverter out of externally-commanded state and resumes local battery self-consumption logic — even before 30407 is cleared. Disabling 30407 afterwards cleanly resets the remote control registers. Skipping step 1 and only clearing 30407 can leave the inverter in a brief intermediate state with undefined battery behaviour. Credit: [@Wojak129](https://github.com/Wojak129) — confirmed on WIT 15KTL3 hardware.

### Pattern 6: Dynamic Spot-Price Automation

Full example — continuously adjusts charge/discharge every minute based on electricity price, with correct session start and termination. Registers 30407/30408/30409 are marked "Not storage" (EEPROM-safe) — per-minute writes carry no risk of flash wear.

```yaml
automation:
  - alias: "WIT Spot Price Battery Control"
    trigger:
      - platform: time_pattern
        minutes: "/1"  # Every minute
    condition:
      # Only run when control authority is enabled
      - condition: state
        entity_id: select.INVERTER_control_authority
        state: Enabled
    action:
      - variables:
          price: "{{ states('sensor.electricity_price') | float(0) }}"
          soc: "{{ states('sensor.INVERTER_battery_soc') | int(0) }}"

      - choose:
          # High price: discharge battery if SOC > cutoff
          - conditions:
              - condition: template
                value_template: "{{ price > 0.25 and soc > 20 }}"
            sequence:
              - action: number.set_value
                target:
                  entity_id: number.INVERTER_remote_charge_and_discharge_power
                data:
                  value: -80  # Discharge at 80%

          # Low price: charge battery if SOC < 95%
          - conditions:
              - condition: template
                value_template: "{{ price < 0.10 and soc < 95 }}"
            sequence:
              - action: number.set_value
                target:
                  entity_id: number.INVERTER_remote_charge_and_discharge_power
                data:
                  value: 80  # Charge at 80%

          # Mid price: hold (minimal positive value keeps register active without forcing charge)
          default:
            - action: number.set_value
              target:
                entity_id: number.INVERTER_remote_charge_and_discharge_power
              data:
                value: 1

      # Re-enable remote control if inverter rebooted (30407 resets to 0 on power cut)
      - action: select.select_option
        target:
          entity_id: select.INVERTER_remote_power_control_enable
        data:
          option: Enabled
```

To end the session call [Pattern 5](#pattern-5-proper-termination-sequence-continuous-sessions).

### Pattern 7: Checking SOC Cutoffs Before Commanding

The inverter enforces its own SOC limits (registers 30404/30405). Your automation can mirror these:

```yaml
variables:
  soc: "{{ states('sensor.INVERTER_battery_soc') | int(0) }}"
  charge_cutoff: "{{ states('number.INVERTER_vpp_charge_cutoff_soc') | int(100) }}"
  discharge_cutoff: "{{ states('number.INVERTER_vpp_discharge_cutoff_soc') | int(20) }}"
condition:
  - condition: template
    value_template: >
      {{ (power_target > 0 and soc < charge_cutoff) or
         (power_target < 0 and soc > discharge_cutoff) }}
```

---

## Export Limitation (VPP Registers 30200–30208)

WIT inverters support VPP export limitation, which is **percentage-based only** — there is no watts-based register in the VPP protocol.

| Register | Name | Notes |
| --- | --- | --- |
| 30200 | Export Limitation Enable | 0=disabled, 1=single machine enable |
| 30201 | Export Limitation power Rate | 0–100%, positive=export allowed, 0=no export |
| 30202 | Failure power Rate | If EMS comms fail (see 30203/30204), export drops to this % — default 0% |
| 30203 | EMS Failure Time | Seconds before failure rate applies (default 30s) |
| 30204 | EMS Failure Enable | Must also be enabled for failure rate to activate |
| 30206 | Change slope | Ramp rate: default 27 × 0.01%Pn/s |
| 30208 | Protection mode | **Not used by WIT/WIS** (per VPP V2.03 spec Note 2) |

> **Important:** The 5000W value often visible at legacy register 203 is a **grid compliance cap** set by the Growatt commissioning tool at installation — it acts as a hard ceiling below VPP control. VPP register 30201 at 100% combined with a 5000W legacy cap means actual export is limited to 5000W. This legacy cap is not writable via VPP Modbus and requires the Growatt service tool to change.

---

## VPP Standby Hazard

When `control_authority` (register 30100) is enabled but `remote_power_control` (register 30407) is **not** enabled, the inverter enters a standby state where local battery logic is suspended and load is drawn from the grid.

**Safe state combinations:**

| control_authority (30100) | remote_power_control (30407) | Result |
| --- | --- | --- |
| 0 | 0 | Normal local control (no VPP) |
| 1 | 1 | VPP active — battery follows register 30409 |
| **1** | **0** | **⚠️ VPP standby — inverter draws from grid, battery suspended** |

Always ensure remote power control is enabled when control authority is on, or disable both together.

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

- [WIT Profile Documentation](https://github.com/0xAHA/Growatt_ModbusTCP/blob/main/custom_components/growatt_modbus/profiles/wit.py)
- [Supported Models](../hardware/models.md)
- [VPP Protocol Overview](../developer/protocol-database.md)

---

**Version**: 0.9.8
**Last Updated**: 2026-06-30
