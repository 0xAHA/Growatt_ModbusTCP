# TOU Register Reversion — Investigation Findings

## Problem

TOU (Time-of-Use) schedule writes on Growatt GEN4 MOD-series inverters revert after being set.
Initially suspected to be cloud service interference (ShineWiFi dongle), but the
`wills106/homeassistant-solax-modbus` integration successfully manages TOU on the same hardware
via its dedicated Growatt plugin (`plugin_growatt.py`). Comparing their approach to ours reveals
three concrete gaps.

---

## Source of Truth

All findings below come directly from:
**`wills106/homeassistant-solax-modbus` → `custom_components/solax_modbus/plugin_growatt.py`**

This repo supports multiple inverter brands including a complete Growatt plugin with working TOU.
The plugin classifies inverters by generation (`GEN3`, `GEN4`) and type (`HYBRID`, `AC`, `SPF`).

---

## Finding 1 — Missing Prerequisite Gate: "Allow Grid Charge" (Register 3049)

**This is the most likely root cause of register reversion.**

The Solax Modbus Growatt plugin defines register **3049** as a mandatory control for
`HYBRID | AC | GEN4` models:

```python
GrowattModbusSelectEntityDescription(
    name="Allow Grid Charge",
    key="charger_switch",
    register=3049,
    option_dict={0: "Disabled", 1: "Enabled"},
    allowedtypes=HYBRID | AC | GEN4,
)
```

This register must be set to **Enabled (1)** before TOU time slot registers (3038–3059) will
persist. When it is disabled, the inverter firmware silently ignores TOU writes, or re-applies
its own defaults after each write.

**Register 3049 does not appear anywhere in our current codebase.**

### Manual verification

To confirm this is the root cause before writing any code:

```bash
# Enable Allow Grid Charge
mbpoll -a 1 -r 3049 -t 4 <inverter-ip> 1

# Write TOU Period 1: 06:00 start (enabled, Battery First)
# bit15=1 (enable) + bit13=1 (Battery First) + 0x0600 (06:00) = 0xA600 = 42496
mbpoll -a 1 -r 3038 -t 4 <inverter-ip> 42496
mbpoll -a 1 -r 3039 -t 4 <inverter-ip> 0x2200   # 22:00 end

# Read back after 60 seconds
mbpoll -a 1 -r 3038 -t 4:hex <inverter-ip>
```

If the values persist, register 3049 is confirmed as the prerequisite gate.

---

## Finding 2 — GEN4 Supports 9 TOU Time Slots, Not 4

The Solax Modbus plugin exposes **9 "Time N Update" buttons** for GEN4 models:

| Slot | Start reg | End reg | Notes |
|------|-----------|---------|-------|
| 1 | 3038 | 3039 | |
| 2 | 3040 | 3041 | |
| 3 | 3042 | 3043 | |
| 4 | 3044 | 3045 | |
| 5 | **3050** | 3051 | Jumps — 3046–3049 are EMS/grid-charge regs |
| 6 | 3052 | 3053 | |
| 7 | 3054 | 3055 | |
| 8 | 3056 | 3057 | |
| 9 | 3058 | 3059 | |

**The gap between slots 4 and 5 is intentional.** Registers 3046–3049 are EMS and grid-charge
controls, not TOU slots:

- `3047` = EMS Discharging Rate
- `3048` = EMS Charging Stop SOC
- `3049` = Allow Grid Charge (the prerequisite gate above)

Our `MOD_TOU_PERIODS` in `const.py` only defines 4 periods (3038–3045).
Slots 5–9 at **3050–3059 are entirely missing**.

---

## Finding 3 — Atomic Two-Register Writes

The Solax plugin never writes a TOU start register alone. It always writes start + end as a
single **FC16 (write multiple registers)** transaction. This prevents the inverter from ever
seeing a partial update where start has changed but end has not.

The pattern they use:

1. Each time field (begin, end, mode, enabled) is stored locally in HA memory only —
   it does **not** write to the inverter immediately (`write_method=WRITE_DATA_LOCAL`).
2. The user presses a "Time N Update" button, which fires a single atomic write of both
   registers via `WRITE_MULTI_MODBUS`.

The value function for each slot:
```python
def value_function_time_1_update(initval, descr, datadict):
    time_begin = datadict.get("time_1_begin", "00:00")
    time_end   = datadict.get("time_1_end",   "00:00")
    enabled    = datadict.get("time_1_enabled", "Disabled")
    mode       = datadict.get("time_1_mode",   "Load First")
    return [
        (REGISTER_U16, encode_time_begin(time_begin, enabled, mode)),
        (REGISTER_U16, time_to_int(time_end)),
    ]

def encode_time_begin(begin_str, enabled, mode) -> int:
    value = hours * 256 + minutes   # packed time — same format as our mod.py
    if enabled == "Enabled":        value += 32768  # bit15
    if mode == "Battery First":     value += 8192   # bit13
    elif mode == "Grid First":      value += 16384  # bit14
    return value
```

The encoding is **identical** to what `profiles/mod.py` already documents for bits 13–15 of
start registers. Our `time.py` (`GrowattModTouTime.async_set_value`, lines 206–240) writes
each register independently via `write_register_verified`, creating a window where the inverter
sees an inconsistent state.

---

## Finding 4 — GEN3 (SPH) Uses a Different Register Set

For `HYBRID | GEN3` models (e.g., SPH TL-HUB series), the Solax plugin exposes additional
time slot registers not currently in our `sph.py`:

| Range | Purpose |
|-------|---------|
| 1017–1025 | Battery First Time slots 4–6 (begin/end/enable triples) |
| 1026–1034 | Grid First Time slots 4–6 |
| 1080–1088 | Grid First Time slots 7–9 |
| 1092 | AC Charge Enable (already in our `sph.py`) |
| 1100–1108 | AC Charge Time slots 1–3 (already in our `sph.py`) |

GEN3 uses **separate enable registers** (e.g., 1019, 1022, 1025) rather than the bit-packed
format used by GEN4. Reversion on GEN3 is more likely cloud interference than a missing
prerequisite — there is no equivalent of register 3049 for GEN3.

---

## Summary of Required Changes

| # | File | Change | Priority |
|---|------|--------|----------|
| 1 | `profiles/mod.py` | Add register 3049 (`allow_grid_charge`) | **Critical** |
| 2 | `const.py` | Add `allow_grid_charge` to `WRITABLE_REGISTERS` | **Critical** |
| 3 | `select.py` | Expose register 3049 as a select entity for MOD GEN4 | **Critical** |
| 4 | `profiles/mod.py` | Add TOU slots 5–9 (registers 3050–3059) | High |
| 5 | `const.py` | Extend `MOD_TOU_PERIODS` from 4 to 9 entries | High |
| 6 | `time.py` | Write start+end as atomic FC16 pair (lines 206–240) | Medium |
| 7 | `profiles/sph.py` | Add Battery First / Grid First time registers (1017–1034, 1080–1088) | Low |

Items 1–3 should be implemented and field-tested first (manual mbpoll verification recommended
before writing HA code). Items 4–7 can follow once the root cause is confirmed.
