# Actions Reference

The integration registers nine actions (Home Assistant used to call these "services"). They
appear in **Developer Tools → Actions**, search for `growatt_modbus`, and every one of them
can be used in an automation or script.

Most take a `device_id`. The easiest way to get one is to build the call in Developer Tools
with the UI picker, then switch to YAML mode with the toggle at the top right — Home
Assistant fills in the ID for you.

| Action | What it does |
|---|---|
| [`sync_inverter_time`](#sync-the-inverter-clock) | Set the inverter's clock from Home Assistant |
| [`read_register`](#read-a-register) | Read one register |
| [`get_register_data`](#read-a-block-of-registers) | Read a block of registers |
| [`write_register`](#write-a-register) | Write one register |
| [`write_registers`](#write-several-registers-at-once) | Write consecutive registers atomically |
| [`export_register_dump`](#scan-every-register) | Full register scan to CSV |
| [`detect_grid_orientation`](#detect-grid-ct-orientation) | Work out the grid CT sign convention |
| [`set_battery_mode`](#set-battery-mode-vpp) | VPP charge/discharge/hold (WIT, MOD) |
| [`sync_tou_schedule`](#write-a-time-of-use-schedule) | Push a full TOU schedule to the inverter |

---

## Sync the inverter clock

The inverter keeps its own real-time clock, and it drifts. Time period schedules run against
**the inverter's clock, not Home Assistant's** — so a window set for 13:00 starts whenever
the drifted clock reaches 13:00. One reported SPH was two minutes out.

```yaml
action: growatt_modbus.sync_inverter_time
data:
  device_id: 1a2b3c4d5e6f7890abcdef1234567890
```

There is also an **Inverter Clock Sync** button and an **Inverter Clock** sensor on the
inverter device, both disabled by default — see
[Entity Reference](entity-reference.md#keeping-the-inverters-clock-accurate). The button is
the same write with no options; the action is what you want for anything scheduled, because
of `min_drift_seconds` and the response below.

It returns what it found, so you can see the drift it corrected:

```yaml
written: true
inverter_time: "2026-08-25T09:28:03"
home_assistant_time: "2026-08-25T09:30:11"
drift_seconds: 128.0
```

### Scheduled

```yaml
automation:
  - alias: "Growatt — weekly clock sync"
    triggers:
      - trigger: time
        at: "03:30:00"
    conditions:
      - condition: time
        weekday: sun
    actions:
      - action: growatt_modbus.sync_inverter_time
        data:
          device_id: 1a2b3c4d5e6f7890abcdef1234567890
          min_drift_seconds: 30
```

`min_drift_seconds` skips the write when the inverter is already close enough. Leave it at
`0` for a manual one-off; set it for anything scheduled, so a run that finds nothing to fix
costs nothing. These are holding registers and most likely have a finite write endurance —
see [#392](https://github.com/0xAHA/Growatt_ModbusTCP/issues/392).

**Weekly is plenty** for a clock drifting a couple of minutes a month. Hourly buys nothing
and spends writes.

### Does the Growatt cloud not do this for you?

No. Tested over two nights on a cloud-connected SPH with a ShineWiFi dongle attached
([#393](https://github.com/0xAHA/Growatt_ModbusTCP/issues/393)): the clock was deliberately
left five minutes slow and was **still five to six minutes slow the next morning**, twice.

The same test answered a more useful question in passing. Time period changes made locally
over Modbus **appeared correctly in the app and were not reverted** overnight. So the portal
reflects what is on the inverter rather than pushing its own copy back down — your local
schedule changes are safe from it.

### How accurate can it get?

About half a second, and no better — the registers hold whole seconds, so the write lands on
a second boundary whatever you do.

Measured on an SPH after the write-latency compensation was added in v1.8.9: **0.38 s, 1.01 s
and 1.13 s** residual immediately after a sync, against 1.4-3.3 s before it. What is left is
the quantisation, not the integration.

That is far below anything a schedule cares about. Time periods run to the minute.

### Acting on the drift

Because the action returns a value, you can react to it:

```yaml
actions:
  - action: growatt_modbus.sync_inverter_time
    data:
      device_id: 1a2b3c4d5e6f7890abcdef1234567890
    response_variable: clock
  - if:
      - condition: template
        value_template: "{{ clock.drift_seconds | abs > 300 }}"
    then:
      - action: notify.persistent_notification
        data:
          message: >-
            Growatt clock was {{ clock.drift_seconds | round }} s out.
            Schedules may have been firing at the wrong time.
```

### How the year is written

Worth knowing, because it is in neither protocol document and it is what made three earlier
builds fail.

**Register 45 takes a two-digit year and reports back four.** Write `26`, read `2026`. Send
the full year and the inverter rejects the write outright. This was established from a
published ESP32 implementation for an SPH5000 and an ESPHome forum finding, after both a MIN
TL-X and an SPH refused everything else that was tried.

**Confirmed on a MIN TL-X.** The write was accepted, and a subsequent reload of the
integration no longer raised the clock drift notification that had appeared on the restart
before it. That is the only model confirmed so far; if you run the action on anything else,
[#393](https://github.com/0xAHA/Growatt_ModbusTCP/issues/393) is the place to say so.

Two consequences for how the action behaves:

- Each field is written **individually**, not as a block. Both models above refused a
  multi-register write across this range, and the reference implementation notes that while
  settings registers on that hardware generally require FC `0x10`, the RTC block at 45-50 is
  an exception and does accept single writes.
- The **year is written first**. It is the field that fails when something is wrong, so a
  refusal leaves your clock untouched rather than half-set. An earlier build wrote it last,
  five fields landed, and the inverter reset its clock to the year 2000 rather than keep a
  date it considered inconsistent.

The action reads the clock back afterwards and logs a warning if it does not match.

!!! warning "Not available on SPF/SPE"

    The off-grid protocol uses the same addresses but stores the year as an offset from 2000
    and gives register 51 to Chip Select rather than the weekday. Writing the standard layout
    would set the year wrongly and overwrite an unrelated register, so the action refuses
    rather than guessing.

    If you have an off-grid model and can post a register scan covering holding 45-51, that
    is all that is needed to add support.

---

## Read a register

```yaml
action: growatt_modbus.read_register
data:
  device_id: 1a2b3c4d5e6f7890abcdef1234567890
  register: 1044
  register_type: holding   # or input (default)
```

!!! note "Input and holding are different registers"

    The same address means different things in each space. Holding 43 is the device type
    code; input 43 is phase 2 current. Always set `register_type` deliberately.

## Read a block of registers

```yaml
action: growatt_modbus.get_register_data
data:
  device_id: 1a2b3c4d5e6f7890abcdef1234567890
  register_type: input
  start_address: 0
  count: 50
```

## Write a register

```yaml
action: growatt_modbus.write_register
data:
  device_id: 1a2b3c4d5e6f7890abcdef1234567890
  register: 1044
  value: 2
```

## Write several registers at once

Consecutive registers in a single Modbus transaction. Use this where the inverter expects a
group to change together — time period start and end, for instance — so it never sees a
half-applied state.

```yaml
action: growatt_modbus.write_registers
data:
  device_id: 1a2b3c4d5e6f7890abcdef1234567890
  register: 1080
  values: [1320, 1439, 1]
```

## Scan every register

Writes a CSV covering every range the integration knows about, with the reason each read
failed as well as the values that succeeded. This is what to attach when raising an issue —
see [Diagnostic Service](../troubleshooting/diagnostic-service.md).

```yaml
action: growatt_modbus.export_register_dump
data:
  connection_type: tcp
  host: 192.168.1.50
  port: 502
  slave_id: 1
  notify: true
```

If your gateway cannot serve large blocks — LoRa bridges especially — add `block_size: 1`.
Since v1.7.1 the scanner detects that and drops to single reads on its own, but setting it
explicitly is faster.

## Detect grid CT orientation

```yaml
action: growatt_modbus.detect_grid_orientation
data:
  device_id: 1a2b3c4d5e6f7890abcdef1234567890
```

## Set battery mode (VPP)

WIT and MOD models with VPP support. See the [WIT Inverter Guide](wit-guide.md).

```yaml
action: growatt_modbus.set_battery_mode
data:
  device_id: 1a2b3c4d5e6f7890abcdef1234567890
  mode: charge        # charge | discharge | hold
  power_percent: 50
```

## Write a time-of-use schedule

Pushes a whole schedule so the inverter follows it even if Home Assistant is offline. Up to
20 periods, and **they must not overlap or touch** — end at `XX:59`, start the next at
`XX:00`. See [Battery & Scheduling](battery-scheduling.md).

```yaml
action: growatt_modbus.sync_tou_schedule
data:
  device_id: 1a2b3c4d5e6f7890abcdef1234567890
  default_mode: 0
  periods:
    - {start: 0,    end: 119,  power: 100}
    - {start: 120,  end: 1019, power: 1}
    - {start: 1020, end: 1259, power: -100}
```
