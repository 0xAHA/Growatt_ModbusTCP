# Inverter Control Guide

This guide covers the battery and inverter control functionality available for each Growatt inverter model family. Not all models support the same controls — the method of control and available settings differ significantly between families.

---

## Control Architecture Overview

The integration exposes inverter control via standard Home Assistant **Select** and **Number** entities. Controls are automatically instantiated based on which holding registers are present in the active device profile — no manual configuration is required.

Two fundamentally different control models are used across the supported inverter families:

![Control Architecture](../images/control-architecture.svg)

All writes use **read-back verification** — after writing, the integration reads the register back to confirm the value stuck. If a ShineWiFi dongle overwrites the value on the next poll cycle, a persistent notification is shown in the HA UI.

### Persistent Holding Register Writes (SPH, SPF, MOD)

- **How it works:** Write a value to a Modbus holding register. The setting takes effect immediately and persists until changed again — it survives inverter restarts.
- **When to use:** Changing operating mode, charge/discharge limits, AC charge enable. Set once and forget.
- **Risk level:** Low. Standard Modbus write to a well-documented register.

### VPP Time-Limited Overrides (WIT)

- **How it works:** Write a command to VPP protocol registers (30xxx range) that activates a time-limited battery override. The inverter returns to its base TOU schedule when the duration expires or HA restarts.
- **When to use:** Temporary battery force-charge (e.g., cheap tariff window), temporary discharge control.
- **Risk level:** Medium. Requires understanding of the VPP protocol. Rate limiting and conflict detection are built in.
- **See also:** [WIT Control Guide](wit-guide.md) for detailed VPP documentation.

---

## SPH Hybrid Inverters

**Applies to:** SPH 3000-6000TL-BH, SPH 7000-10000TL3-BH, SPH/SPM 8000-10000TL3-BH-HU

**Control method:** Persistent holding register writes (1000+ range)

**Control entities:**

| Entity | Type | Register | Options / Range | Description |
|--------|------|----------|-----------------|-------------|
| Priority Mode | Select | 1044 | Load First (0), Battery First (1), Grid First (2) | Sets the primary power source priority |
| AC Charge Enable | Select | 1092 | Disabled (0), Enabled (1) | Allows/prevents charging from grid |
| Discharge Power Rate | Number | 1070 | 0–100 % | Maximum battery discharge power rate |
| Discharge Stop SOC | Number | 1071 | 0–100 % | SOC level at which discharge stops |
| Charge Power Rate | Number | 1090 | 0–100 % | Maximum battery charge power rate |
| Charge Stop SOC | Number | 1091 | 0–100 % | SOC level at which charging stops |
| System Enable | Select | 1008 | Disabled (0), Enabled (1) | System enable control (HU models only) |
| Time Period 1 Start | Number | 1100 | 0–2359 (HHMM) | Charge/discharge period 1 start time |
| Time Period 1 End | Number | 1101 | 0–2359 (HHMM) | Charge/discharge period 1 end time |
| Time Period 1 Enable | Select | 1102 | Disabled (0), Enabled (1) | Enable/disable period 1 |
| Time Period 2 Start | Number | 1103 | 0–2359 (HHMM) | Charge/discharge period 2 start time |
| Time Period 2 End | Number | 1104 | 0–2359 (HHMM) | Charge/discharge period 2 end time |
| Time Period 2 Enable | Select | 1105 | Disabled (0), Enabled (1) | Enable/disable period 2 |
| Time Period 3 Start | Number | 1106 | 0–2359 (HHMM) | Charge/discharge period 3 start time |
| Time Period 3 End | Number | 1107 | 0–2359 (HHMM) | Charge/discharge period 3 end time |
| Time Period 3 Enable | Select | 1108 | Disabled (0), Enabled (1) | Enable/disable period 3 |

**Notes:**
- All SPH variants share the same 1000+ register range — controls apply across 3–6kW, 7–10kW, and HU variants automatically.
- Time periods use HHMM format: `530` = 05:30, `2300` = 23:00.
- Controls are polled on every coordinator update and reflected in Home Assistant state without restart.

---

## SPF Off-Grid Inverters

**Applies to:** SPF 3000-6000 ES PLUS

**Control method:** Persistent holding register writes (0–97 range)

**Control entities:**

| Entity | Type | Register | Options / Range | Description |
|--------|------|----------|-----------------|-------------|
| Output Priority | Select | 1 | SBU (0), SOL (1), UTI (2), SUB (3) | Output source priority |
| Charge Priority | Select | 2 | CSO (0), SNU (1), OSO (2) | Battery charge source priority |
| AC Input Mode | Select | 8 | APL (0), UPS (1), GEN (2) | AC input mode (appliance / UPS / generator) |
| Battery Type | Select | 39 | AGM (0), FLD (1), User (2), Lithium (3), User 2 (4) | Battery chemistry (⚠️ set with caution) |
| Max Charge Current | Number | 34 | 10–100 A | **Total** charging current, solar + utility combined (LCD Program 02) |
| Bulk Charge Voltage | Number | 35 | 48.0–58.4 V | C.V. charging voltage (LCD Program 19). Disabled by default |
| Float Charge Voltage | Number | 36 | 48.0–58.4 V | Floating charging voltage (LCD Program 20). Disabled by default |
| AC Charge Current | Number | 38 | 0–80 A | Max charging current from AC/grid (LCD Program 11) |
| Generator Charge Current | Number | 83 | 0–80 A | Max charging current from generator |
| Battery to Utility SOC | Number | 37 | 0–100 % (Lithium) / 20–64 V (Lead-acid) | SOC/voltage to switch from battery to utility |
| Utility to Battery SOC | Number | 95 | 0–100 % (Lithium) / 20–64 V (Lead-acid) | SOC/voltage to switch back from utility to battery |

**Output Priority options:**
- `SBU` — Solar → Battery → Utility (battery-first, self-consumption focused)
- `SOL` — Solar → Utility → Battery (solar-first, grid backup)
- `UTI` — Utility → Solar → Battery (grid-first, battery preserved)
- `SUB` — Solar & Utility → Battery (combined source charging)

**Charge Priority options:**
- `CSO` — Solar first, grid only when solar insufficient
- `SNU` — Solar and grid simultaneously
- `OSO` — Solar only, no grid charging

**Max Charge Current vs AC Charge Current.** Max Charge Current (34) is the *total* across
both chargers — solar plus utility. AC Charge Current (38) limits only the utility side. If
you set the total below the AC limit, the inverter applies the total to the utility charger
as well, so 34 can quietly override 38.

**Bulk and Float Charge Voltage are disabled by default, and only work on a self-defined
battery type.** These are the only controls in this integration where a wrong value affects
hardware rather than a reading: the inverter rejects anything outside 48.0-58.4 V, but an
in-range value that is wrong for your battery chemistry will be accepted and applied. They
are created disabled so enabling them is a deliberate step - **Settings > Devices & Services
> Growatt Modbus > entities**, then enable the one you want.

Both correspond to LCD Programs 19 and 20, which the manual marks as settable only when
Program 5 (battery type) is a self-defined option. The entities are therefore unavailable on
AGM, Flooded and Lithium. The integration reads your existing values and never writes a
default - a value changes only when you move the control
([#384](https://github.com/0xAHA/Growatt_ModbusTCP/issues/384)).

**Max Charge Current is unavailable when Battery Type is Lithium.** The inverter does not
allow it to be set in that mode — the BMS takes over charge current control — so the entity
is withheld rather than offered and ignored. Range and behaviour are confirmed on an
SPF 6000ES Plus; smaller units in this family accept a lower maximum, and a value above
what your model allows will be rejected by the inverter and the entity will revert
([#376](https://github.com/0xAHA/Growatt_ModbusTCP/issues/376)).

**Notes:**
- SPF is an off-grid inverter — there is no grid export. The grid is treated as an AC input source for charging/backup.
- `battery_type` (register 39) controls charging voltage thresholds. Changing this incorrectly can damage batteries. Verify your battery chemistry before writing.
- `bat_low_to_uti` and `ac_to_bat_volt` operate in different units depending on battery type: percentage (0–100%) for Lithium, voltage (20.0–64.0V) for lead-acid types.

---

## WIT Commercial Hybrid Inverters

**Applies to:** WIT 4000-15000TL3-X

**Control method:** VPP time-limited protocol (30xxx registers + legacy 2xx registers)

**Control entities:**

| Entity | Type | Register | Options / Range | Description |
|--------|------|----------|-----------------|-------------|
| Work Mode | Select | 202 | Standby (0), Charge (1), Discharge (2) | Remote battery command mode |
| Active Power Rate | Number | 201 | 0–100 % | Power level for charge/discharge command |
| Export Limit | Number | 203 | 0–20000 W | Export limit in watts (0 = zero export) |
| Control Authority | Select | 30100 | Disabled (0), Enabled (1) | VPP master enable switch |
| VPP Export Limit Enable | Select | 30200 | Disabled (0), Enabled (1) | Enable VPP export limitation |
| VPP Export Limit Rate | Number | 30201 | -100–+100 % | Export power rate (positive=export, 0=zero export) |
| Remote Power Control | Select | 30407 | Disabled (0), Enabled (1) | Enable timed charge/discharge override |
| Remote Control Duration | Number | 30408 | 0–1440 min | Duration for remote power control override |
| Remote Charge/Discharge Power | Number | 30409 | -100–+100 % | Power level (negative=discharge, positive=charge) |

**Important notes:**
- WIT uses a **time-limited override** model. Commands via registers 30407–30409 expire after the configured duration or when HA restarts. The inverter then returns to its TOU schedule default.
- Register 30476 (`priority_mode`) on WIT is **read-only** — it shows the base TOU mode but cannot be written via Modbus. Use the inverter display or Growatt app to change the base mode.
- Rate limiting is built in to prevent command flooding.
- Conflict detection prevents simultaneous charge + discharge commands.

See [WIT Control Guide](wit-guide.md) for full protocol documentation.

---

## MOD Three-Phase Hybrid Inverters

**Applies to:** MOD 6000-15000TL3-XH and MID 11000-30000TL3-XH (VPP V2.01, DTC 5400)

**Control method:** Persistent writes to the 3000-range GEN4 registers.

### Controls

| Entity | Type | Register | Options / Range | Description |
|--------|------|----------|-----------------|-------------|
| Allow Grid Charge | Select | 3049 | Disabled (0), Enabled (1) | Permits charging from the grid. Must be Enabled for time-of-use writes to persist |
| Charge Power Rate | Number | 3047 | 1–100 % | Battery charge power limit |
| Charge Stopped SOC | Number | 3048 | 0–100 % | SOC at which charging stops, from any source |
| Discharge Power Rate | Number | 3036 | 0–100 % | Battery discharge power limit |
| Discharge Stopped SOC | Number | 3067 | 1–100 % | SOC at which discharging stops |
| Grid Charge Stopped SOC | Number | 3312 | 0–100 % | SOC at which charging **from the grid** stops. See below |
| Time Period 1–9 Priority | Select | 3038–3058 | Load / Battery / Grid First | Priority for each time-of-use slot |
| Time Period 1–9 Enable | Select | 3038–3058 | Disabled, Enabled | Enable each slot |
| Time Period 1–9 Start / End | Time | 3038–3059 | 00:00–23:59 | Slot start and end times |

!!! warning "Two charge-stop settings, and they are not the same"
    **Charge Stopped SOC** (3048) applies to charging from any source. **Grid Charge
    Stopped SOC** (3312) applies only to charging from the grid, and the lower of the two
    wins.

    This catches people out. On one system 3312 sat at 55 % while 3048 was 100 %, silently
    capping grid charging for two days ([#372](https://github.com/0xAHA/Growatt_ModbusTCP/issues/372)).
    Growatt exposes 3312 in neither the ShinePhone app nor the web portal, so if grid
    charging stops short of your configured limit, check this entity.

!!! info "Registers 1090 and 1092 are not available on this hardware"
    Earlier versions offered **Charge Power Rate (1090)** and **AC Charge Enable (1092)**
    on MOD. The entire holding block 1000–1124 is unimplemented on this family — a full
    sweep read zero across all 125 registers, and writes are rejected outright with Modbus
    exception 2 ([#371](https://github.com/0xAHA/Growatt_ModbusTCP/issues/371)).

    Both were removed. Use **Charge Power Rate (3047)** and **Allow Grid Charge (3049)**
    instead; both are confirmed working. If you had automations pointing at the old
    entities, they will have been removed on upgrade.

### Peak shaving and demand management (read-only)

These are configured in the Growatt web portal and shown here for visibility. They are
diagnostic entities, and appear in no public Growatt protocol document — the mappings were
established by changing each value in the portal and reading the register back
([#372](https://github.com/0xAHA/Growatt_ModbusTCP/issues/372)).

| Entity | Register | Description |
|--------|----------|-------------|
| Import Limit | 3307 | Demand-management import ceiling (kW) |
| Export Limit | 3308 | Demand-management export ceiling (kW) |
| Peak Shaving Reserve SOC | 3310 | Charge held back for peak shaving (%) |
| AC Charge Max Power | 3311 | Ceiling on grid charging power (kW) |

**These also apply to MID.** The MID 11-30KTL3-XH profile loads the same register map, so
the entities appear there too — the profile name does not tell you which family a register
cluster reaches.

**The three kW limits are unavailable until peak shaving has been configured.** When the
feature has never been set up, those registers hold a ceiling rather than a zero — 30000 or
65535, which would render as 3000 kW and 6553.5 kW. The integration publishes nothing
instead, so an unavailable entity here means "not configured in the portal", not a
communication problem
([#380](https://github.com/0xAHA/Growatt_ModbusTCP/issues/380)).

Reserve SOC is the exception and is always shown. An SOC has no implausible ceiling to
give it away — 50 % reads identically whether you set it or the factory did — so there is
no way to tell configured from unset, and guessing would be worse than showing the value.

### VPP remote power control (read-only)

MOD TL3-XH **does** support VPP remote power control — this was measured on hardware
([#373](https://github.com/0xAHA/Growatt_ModbusTCP/issues/373)) — but the controls are not
exposed for writing yet. The state is available as disabled-by-default diagnostic entities:
VPP Control Authority (30100), VPP Remote Power Control (30407), VPP Commanded Power
(30409) and VPP Last Setpoint (30474).

!!! danger "Why writing is not exposed"
    **The commanded power is a target, not a limit.** At 100 % with insufficient solar, the
    inverter climbed toward the setpoint and drew 912 W from the grid — while Allow Grid
    Charge was Disabled. At lower percentages only downward limiting is visible, which
    makes it look like a cap.

    **The duration expires but the registers do not clear.** After a 2-minute command the
    power constraint released at ~128 s while all three registers stayed set for the full
    observation. You cannot tell from these values whether control is currently active.

    Writable controls need a guard against commanding more power than solar can supply.
    Until that exists, exposing them would let an automation import from the grid while the
    user believes grid charging is switched off.

**Battery monitoring sensors available:**

| Sensor | Register | Description |
|--------|----------|-------------|
| Battery SOC | 3171 | State of charge (%) |
| Battery SOH | 1096 | State of health (%) |
| Battery Voltage | 3169 | Battery voltage (×0.01 V) |
| Battery Current | 3170 | Battery current (×0.1 A) |
| DC-DC Temperature | 3176 | Battery-side DC-DC stage temperature (×0.1 °C). Not the pack temperature — see [#362](https://github.com/0xAHA/Growatt_ModbusTCP/issues/362) |
| Battery Charge Power | 3178/3179 | Charge power (×0.1 W) |
| Battery Discharge Power | 3180/3181 | Discharge power (×0.1 W) |
| Battery Charge Today | 3129/3130 | Energy charged today (kWh) |
| Battery Discharge Today | 3125/3126 | Energy discharged today (kWh) |
| Battery Charge Total | 3131/3132 | Lifetime charge energy (kWh) |
| Battery Discharge Total | 3127/3128 | Lifetime discharge energy (kWh) |
| AC Charge Energy Today | 3133/3134 | Grid→battery energy today (kWh) |
| AC Charge Energy Total | 3135/3136 | Grid→battery lifetime energy (kWh) |

---

## MIN / MIN TL-XH Grid-Tied Inverters

**Applies to:** MIN 3000-6000TL-X, MIN 7000-10000TL-X, MIN TL-XH 3000-10000 V2.01

**Control:** No battery control available. These are grid-tied inverters without battery management registers.

**Available controls:** None beyond the universal `on_off` (register 0) and `active_power_rate` (register 3) which are present on all models but not exposed as control entities by default.

---

## MIC Micro Inverters

**Applies to:** MIC 600-3300TL-X

**Control:** None. MIC is a grid-tied micro inverter with no battery or control registers beyond basic inverter status.

---

## Summary Table

| Model Family | Battery Control | Control Method | Select Entities | Number Entities |
|---|---|---|---|---|
| **SPH** (3–10kW) | Yes | Persistent writes | Priority Mode, AC Charge Enable, Time Period Enables (×3), System Enable (HU) | Discharge Rate, Discharge Stop SOC, Charge Rate, Charge Stop SOC, Time Period Start/End (×3) |
| **SPF** ES PLUS | Yes | Persistent writes | Output Priority, Charge Priority, AC Input Mode, Battery Type | Max Charge Current, AC Charge Current, Gen Charge Current, Battery→Utility SOC, Utility→Battery SOC |
| **WIT** (4–15kW) | Yes (timed) | VPP overrides | Work Mode, Control Authority, VPP Export Limit Enable, Remote Power Control | Active Power Rate, Export Limit, VPP Export Rate, Remote Duration, Remote Power |
| **MOD / MID** TL3-XH | Yes | Persistent writes | Allow Grid Charge, Time Period Priority/Enable (×9) | Charge Rate, Charge Stop SOC, Grid Charge Stop SOC, Discharge Rate, Discharge Stop SOC, Time Period Start/End (×9) |
| **MIN / TL-XH** | No | — | — | — |
| **MIC** | No | — | — | — |

---

## Adding Control Entities to Automations

All control entities follow standard Home Assistant naming. Examples:

```yaml
# Force battery to charge at 80% power for 60 minutes (WIT)
- service: number.set_value
  target:
    entity_id: number.growatt_remote_charge_and_discharge_power
  data:
    value: 80
- service: number.set_value
  target:
    entity_id: number.growatt_remote_power_control_charging_time
  data:
    value: 60
- service: select.select_option
  target:
    entity_id: select.growatt_remote_power_control
  data:
    option: "Enabled"

# Set SPH to Battery First mode (SPH)
- service: select.select_option
  target:
    entity_id: select.growatt_priority_mode
  data:
    option: "Battery First"

# Enable AC charging on SPH
- service: select.select_option
  target:
    entity_id: select.growatt_ac_charge_enable
  data:
    option: "Enabled"
```

---

## Energy Dashboard Setup

The integration pre-configures all energy sensors with the correct `state_class` and `device_class` for the HA Energy Dashboard. Recommended sensor mapping:

| Dashboard slot | Sensor |
| --- | --- |
| Solar production | `sensor.{name}_energy_total` |
| Return to grid | `sensor.{name}_energy_to_grid_today` *(use total variant)* |
| Grid consumption | `sensor.{name}_energy_to_user_today` *(use total variant)* |
| Individual consumption | `sensor.{name}_load_energy_today` *(use total variant)* |
| Battery in | `sensor.{name}_charge_energy_today` *(use total variant)* |
| Battery out | `sensor.{name}_discharge_energy_today` *(use total variant)* |

> If `Grid Export Power` and `Grid Import Power` appear swapped after upgrading to v0.9.1b1, disable **Invert Grid Power** in the integration options (Settings → Devices & Services → Growatt Modbus → Configure) — it was incorrectly enabled by the setup wizard's auto-detection in previous versions. Most users should have this option off. If the signed `Grid Power` sensor shows the wrong sign independently, run the `detect_grid_orientation` service.

---

## Contributing

If you have a MOD inverter with APX battery (Issue #131) and can provide holding register scans from the 1000–1124 range, please share your findings in the issue. This will enable battery control for the MOD family.

For other model-specific control questions, [open an issue](https://github.com/0xAHA/Growatt_ModbusTCP/issues) with your model, DTC code, and a register scan from the diagnostic tool.
