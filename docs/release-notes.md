# Release Notes

<a href="https://www.buymeacoffee.com/0xAHA" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>

> This page shows recent highlights. The [full changelog](https://github.com/0xAHA/Growatt_ModbusTCP/blob/main/RELEASENOTES.md) on GitHub contains every version with complete details.

---

## v0.9.1b3

- **Fix: MIC 2500-5500MTL-S entities all unavailable (Issue #304):** The inverter rejects any Modbus read of more than one register at a time (ExceptionResponse, Illegal Function). Fixed by adding per-profile `max_block_size` support to the coordinator. Profiles that set `max_block_size: 1` now use sparse read mode — only the specific register addresses defined in the profile are read, skipping all gaps between them. All other profiles continue using the original 125-register block reads unchanged.

---

## v0.9.1b2

- **New profile: Growatt 3000-15000TL3-S (Issue #299):** Added support for the TL3-S three-phase grid-tied string inverter (3–15 kW, legacy protocol). Register layout confirmed from a full device scan — PV inputs, per-phase AC output (R/S/T confirmed by sum crosscheck), temperature, and energy. Auto-detected via DTC 2049. No VPP support.

- **Fix: `house_consumption` mirrors solar on SPM/SPH HU variants (Issue #303):** The HU variant does not populate `power_to_load` or `power_to_user`, causing the fallback to collapse to `load = solar`. Fixed with a full energy balance: `load = solar + discharge − charge + import − export`. Correctly computes real house load on HU models with active battery and grid.

- **New profile: MIC 2500-5500MTL-S (Issue #304):** Added support for the MIC 2500–5500MTL-S single-phase dual-string grid-tied inverter family (legacy V3.05 protocol). Inherits the MIC 600–3300TL-X register map with a confirmed second PV string. Auto-detected via DTC 210. Note: this inverter rejects multi-register Modbus block reads — use `block_size=1` with the Universal Scanner.

---

## v0.9.1b1

We apologise for this one. The `Grid Export Power` and `Grid Import Power` sensors have had their values swapped since they were introduced — every user has been seeing export labelled as import and vice versa. The bug was in the formula that splits the signed grid power value into its two always-positive halves. The signed `Grid Power` sensor and all daily energy sensors were unaffected. We only caught it because a user noticed it on a hybrid inverter where both directions are active (Issue #302). Grid-tied string inverter users (MIN, MID, MIC) were also affected but less obviously — those inverters only export during the day, so `Grid Export Power` silently read zero while `Grid Import Power` carried the export value. Both are now correct.

> ⚠️ **BREAKING CHANGE — affects all users.** After upgrading, `Grid Export Power` and `Grid Import Power` will read the opposite value to before. Swap any automations, dashboard cards, or energy dashboard slots that reference either sensor. Users with **Invert Grid Power** enabled should also disable it (Settings → Devices & Services → Growatt Modbus → Configure) — it was incorrectly set by auto-detection in previous versions.

- **Breaking fix: `grid_export_power` and `grid_import_power` swapped on all profiles (Issue #302):** The two always-positive derived power sensors had their formulas inverted in all previous versions. On hybrid profiles (SPH, MOD, WIT) the symptom was visible: during grid import, `grid_export_power` showed the import magnitude while `grid_import_power` read zero. On grid-tied string inverters (MIN, MIC, MID), `grid_export_power` silently read zero and `grid_import_power` showed the export value under the wrong name. The signed `grid_power` sensor and the daily energy sensors (`Energy to Grid Today`, `Grid Import Energy Today`) were unaffected.

- **Fix: `invert_grid_power` auto-detection was enabling inversion for the wrong case:** The setup wizard's grid orientation detection returned the wrong result — it enabled inversion when it detected positive = export (the correct convention) and disabled it when it detected negative = export (the case that actually needs correction). Existing users with the flag incorrectly enabled should disable it via Configure.

---

## v0.9.0

- **Fix: Universal Scanner DTC registers showing as zero on fresh TCP connection:** The DTC identification registers (holding 30000 and holding 43) frequently returned 0 in scan output even though `read_register` always worked. The scanner opens a new raw TCP connection that displaces the coordinator's session; the inverter returns 0 until it settles. Fixed with a post-connect warmup delay and end-of-scan settled re-reads — by the time the full range scan completes the inverter's Modbus state is stable. Also fixes garbled firmware version (holding 9-11) from the same cause.

- **Fix: VPP battery charge/discharge today swapped on SPH V2.01 profiles (Issue #300):** `battery_charge_today` and `battery_discharge_today` from VPP registers 31202 and 31206 were labelled the wrong way round on `sph_3000_6000_v201` and `sph_7000_10000_v201`. VPP Protocol V2.01 specifies 31202 as daily charge and 31206 as daily discharge. The legacy storage-range registers (1052/1053 and 1056/1057) were always correct; only the VPP-sourced entities were affected.

- **Feature: Universal Scanner now includes holding register scan (0-124 and 1000-1124):** The `export_register_dump` scanner now reads holding registers (FC03) for the base range (0-124) and control range (1000-1124). These contain writable controls including `ac_charge_enable` (H1092), TOU time period slots (H1100-H1108), charge/discharge power rates, and scheduling windows. Holding register rows appear in the CSV with an H-prefix and a Suggested Match column populated from the active profile's register definitions.

---

## v0.8.9

- **Fix: WIT all entities unavailable after upgrading to v0.8.8 (Issue #295):** Two related bugs in the v0.8.8 register scan sizing affected WIT inverters. First, the base range check included WIT's 875-range registers, causing a ~999-register read that exceeded the Modbus limit. Second, WIT's base range extends to address 188, which also exceeds 125. Both fixed: 875-999 is now excluded from the base range check, and base ranges over 125 registers are now read in chunks. WIT/WIS models only.

- **Feature: Universal Scanner configurable block size:** The `export_register_dump` service now has a **Block Size** field (125, 25, or 1 register per request; default 125). Use 25 or 1 for inverters that reject large block reads — older RS485 models and some TL3-S units return Illegal Function on 125-register requests. Smaller blocks scan every register individually at the cost of scan time.

- **Feature: Universal Scanner always reports both DTC registers:** The notification and CSV now always show both VPP DTC (holding 30000) and legacy DTC (holding 43), making it easier to diagnose unknown or dual-protocol inverters.

---

## v0.8.8

- **Feature: Configurable inter-request Modbus delay (Issue #294):** A new **Modbus Request Delay** field (50–1000 ms, default 250 ms) is available in Options (Settings → Devices & Services → Growatt Modbus → Configure). Users seeing `transaction_id` mismatch errors or inverter fault log entries caused by Modbus traffic should increase this to 500–1000 ms. Takes effect immediately without restart.

- **Fix: Profile-driven input register block sizing:** The base (0–N) and storage (1000–N) input register reads now request only as many registers as the active profile actually defines, rather than always reading 125. Reduces Modbus payload size and poll time.

- **Fix: VPP holding register retry throttling:** VPP-range holding registers (30100, 30200–30201, 30407–30410) that return no response on the first read of a session are skipped for the rest of that session, preventing repeated unanswered requests from causing transaction-ID mismatches. Retried on the next HA restart.

- **Fix: `priority_mode` sensor displays mode name instead of raw integer:** Shows "Load First", "Battery First", or "Grid First" instead of 0 / 1 / 2.

- **Feature: `Export Limit Fallback Power Rate` writable number control (holding register 3000):** Available on MIN TL-X, MIN TL-XH, MIC 600–3300TL-X, and TL-XH 3000–10000 profiles (and all V2.01 variants). Reads and writes the fallback output power cap (0–100%) the inverter applies when export limitation control fails. Appears under the Grid device as a configuration entity.

---

## v0.8.7

- **Fix: `priority_mode` (register 1044) demoted to read-only sensor (Issue #293):** V1.39 protocol specifies holding register 1044 as read-only. SPH 3–6kW, SPH 7–10kW, and SPH-TL3 profiles incorrectly exposed it as a writable select entity. It is now a read-only diagnostic sensor under the Battery device. WIT (register 30476) and MOD (input register 3144) were already read-only and are unchanged.

- **Feature: SPH V2.01 remote power control registers (Issue #286):** Registers 30407–30410 are now exposed on `sph_3000_6000_v201` and `sph_7000_10000_v201` as writable entities: `remote_power_control_enable` (on/off), `remote_power_control_charging_time` (0–1440 min), `remote_charge_and_discharge_power` (−100 to +100%), and `vpp_ac_charge_enable` (disabled/PV priority/AC priority). Enables time-limited charge/discharge overrides and AC charging mode control from HA automations.

- **Feature: Battery voltage range option in integration settings:** A new **Battery Voltage Range** dropdown is available in Options (Settings → Devices & Services → Growatt Modbus → Configure): *Auto-detect* (default), *Standard battery (under 600 V)*, or *High-voltage battery (600–950 V, e.g. ARK)*. Use the High-voltage option when VPP register 31214 does not respond and register 3169 is reading ~10× too low due to a 16-bit overflow.

- **Feature: MID TL3-X V2.01 PV3 string sensors:** `pv3_voltage`, `pv3_current`, and `pv3_power` are now available on the `mid_15000_25000tl3_x_v201` profile via VPP registers 31018–31021.

- **Fix: MOD TL3-XH battery voltage 10× too high on standard battery systems (Issue #287):** v0.8.0 changed register 3169 scale to 0.1 to fix high-voltage ARK battery readings (600–950 V). This broke units with standard 200–300 V batteries, producing readings 10× too high (e.g. 2500 V instead of 250 V). Register 3169 reverted to 0.01 V/unit. VPP register 31214 is now a higher-priority candidate in the voltage selection logic — when it responds it correctly covers both battery voltage ranges. The plausibility ceiling is raised from 800 V to 1100 V so HV readings are not discarded.

---

## v0.8.5

- **Fix: MOD TL3-X and TL3-XH `ac_power` reported Phase R only:** Both profiles had the total-power alias on the Phase R register instead of the three-phase total register (35/36). `ac_power` now correctly reflects full three-phase output.

- **Fix: Midnight ENERGY_GUARD retained previous-day small daily totals until morning:** Daily totals under the 20 kWh spike threshold (e.g. `charge_energy_today`) were accepted into retention from the pre-reset inverter poll, then held as stale values until sunrise caused a backward step and HA recorder warnings. A 10-minute midnight grace window now suppresses all non-zero daily totals until the inverter has reset its own counters.

- **Feature: Inverter clock drift notification:** On first connection each session the coordinator compares the inverter's system time registers to HA time. If drift exceeds 5 minutes a persistent HA notification is raised, explaining the impact on daily energy counters and how to fix it.

- **Breaking change: MID TL3-X grid export/import source corrected (Issue #242):** `grid_export_power` and `grid_import_power` on MID grid-tied models (DTC 5001/5002 — MID 15–50KTL3-X, MID 20–30KTL3-X2) now read from VPP Meter Power (31112/31113) rather than Active Power (31100/31101). Active Power is the inverter's own AC output; Meter Power is the actual metered grid exchange. With a connected Growatt smart meter, export/import values will now be correct. Without a smart meter, these entities will read 0 — use `ac_power` / `solar_total_power` for inverter output monitoring. Hybrid models (SPH, MOD-XH, WIT) are unaffected.

- **Fix: Daily energy totals drop to 0 and show backward steps after mid-day inverter reconnect (Issue #284):** When the inverter briefly goes offline mid-day and comes back online, ENERGY_GUARD retention was unconditionally cleared, leaving daily counters unprotected against the transient 0-reads that occur while the inverter repopulates its registers. Sensors dropped to 0 then recovered to a value slightly below the pre-offline reading, causing `total_increasing` recorder warnings in HA. Fixed by only clearing retention on morning wakeups (before 10:00) where stale-value detection is needed. Mid-day wakeups now preserve retention. The morning stale-detection path (Issue #225) is unaffected.

- **Fix: DTC 5001 misdetected as MIC (Issue #242):** MID 17–25KTL3-X and related grid-tied MID/MOD-X models were falling through to MIC micro-inverter detection because DTC 5001 was not in the detection map. All missing DTC codes from Growatt VPP 2.03 Table 3-1 have been added: 5001/5002/5003 (MID/MOD/MAC-X grid-tied), 5600/5801 (large commercial WIT/WIS), 3503/3504 (SPH HU/HUB), 3701/3715/3716 (SPA AU/AUB/BL).

- **Fix: Lifetime energy totals show brief backward step after HA restart (Issue #285):** `energy_total` and other lifetime counters are now written to HA storage immediately after each poll where their retained value changes, rather than via a background task that could be lost if HA restarted between polls. Eliminates the transient `total_increasing` backward-step warning seen on restart.

---

## v0.8.4

- **Debug: `[ENERGY_GUARD]` diagnostic logging for energy counter protection (Issue #228):** Searchable log entries now trace every accept/retain/spike-reject decision in the daily energy protection logic, plus the wake-up retention-clear event and stale-value debounce window. Helps diagnose inverters (e.g. MOD12-KTL3-HU) that accumulate overnight import values which then drop to zero at morning startup. Enable with `custom_components.growatt_modbus: debug` and search logs for `ENERGY_GUARD`.

---

## v0.8.3

- **Fix (Issue #283): SPH 3–6kW and 7–10kW battery registers corrected:** Input registers 13–19 in the 0–124 range were mislabelled as battery registers. Per V1.39 protocol they are PV3–PV5 channel registers. Battery data moved to the correct storage-range registers: discharge power (1009–1010), charge power (1011–1012), battery voltage (1013), SOC (1014), battery temperature (1040). Fixes wrong `battery_power`, `battery_soc`, and `battery_voltage` readings on SPH 3600 TL-UP and similar models.

---

## v0.8.2

- **Fix: Critical `set_battery_mode` service was non-functional (F-001/F-002):** The VPP write logic had been spliced into `get_register_data`, leaving `set_battery_mode` as a registered no-op. `sync_tou_schedule` had an orphaned `_read()` closure referencing undefined variables — a latent NameError on the success path. All three function bodies restructured.
- **Fix: `services.yaml` field mismatches (F-006/F-007):** Removed three phantom services never registered in Python. Fixed `set_battery_mode`, `write_registers`, and `sync_tou_schedule` field definitions — each now matches the Python schema exactly.
- **Fix: Holding register reads omitted slave ID (F-003):** `read_holding_registers()` now passes `slave_id` with a pymodbus compatibility fallback. Five `auto_detection.py` raw client calls switched to the wrapper.
- **Fix: WIT cooldown timestamp now set after successful write (F-005):** Previously a failed write would block subsequent writes for the full 30-second cooldown unnecessarily.
- **Fix: Binary sensor `is_on` uses `coordinator.is_online` (F-018), duplicate coordinator property removed (F-021), explicit `disconnect()` on entry unload added (F-022).**
- **Docs: `battery-scheduling.md` `read_register` examples corrected** — wrong field names (`register_address`, `count`) replaced with the actual schema field (`register`).
- **Feat (Issue #282): WIT registers 235–238 exposed as read-only diagnostic sensors** — `ntognd_detect`, `nonstd_vac_enable`, `enable_spec_set`, `fast_mppt_enable` visible on the Inverter device. **Intentionally read-only:** these registers control safety-critical grid-protection behaviour; incorrect writes risk grid-code violations or hardware damage. All four are disabled by default and require explicit opt-in.
- **Fix (Issue #131): `grid_first_discharge_power_rate` range corrected to 1–100%** — register 3036 on MOD TL3-XH is a percentage value; values above 100 cause an unknown inverter error. Number entity clamped accordingly.

---

## v0.8.1

- **Fix (Issue #228):** Daily energy spike at inverter startup eliminated. The midnight 32-bit register reset briefly produced garbage readings (e.g. 79 kWh) that were stored as the day's retained total. A 20 kWh/poll spike guard now rejects these with a WARNING log entry.

---

## v0.8.0

- **Fix (Issue #228):** MOD TL3-XH battery voltage scale corrected from `0.01` to `0.1`. Hardware operates at 600–950 V — the previous scale overflows a 16-bit register above 655 V, producing readings ~10× too low (e.g. 73 V instead of 733 V).
- **Feat (Issue #131):** MOD TL3-XH — two new battery mode power rate controls: `grid_first_discharge_power_rate` (register 3036, 1–255) and `batt_first_charge_power_rate` (register 3047, 1–100%). Appear as number entities under the Battery device.
- **Refactor:** VPP V2.01 shared register block extraction (Phase 3) — new `vpp_v201.py` shared block library used across SPH, MIN, TL-XH, SPH-TL3, and MID V2.01 profiles. Also fixed two previously missing SPH-TL3 registers: `ipm_temp_vpp` (31131), `boost_temp_vpp` (31132), and `active_power_rate_vpp` (30114) — all confirmed responding in hardware scans.

---

## v0.7.9

- **Feat:** Documentation migrated to GitHub Pages at [0xaha.github.io/Growatt_ModbusTCP](https://0xaha.github.io/Growatt_ModbusTCP/). README slimmed to installation essentials with a link to the full docs.
- **Feat:** Register read and disconnect log messages promoted from DEBUG to INFO — successful polls are now visible without enabling debug logging.
- **Refactor:** Template-generated sensor definitions — PV string (1/2/3) and three-phase R/S/T sensor groups replaced with helper functions, reducing `sensor.py` by ~100 lines. CI test updated to parse grep-index comments for statically-analysing generated keys.
- **Refactor:** Profile key alias mechanism — `PROFILE_ALIASES` dict in `device_profiles.py` maps retired profile keys to canonical replacements. First alias: `mod_6000_15000tl3_xh_v201` → `mod_6000_15000tl3_xh` (identical register map and sensors). Config entries are silently updated on startup.

---

## v0.7.8

- **Feat:** INFO-level startup logging — single log line summarising active profile, connection, scan interval, and polled register ranges without needing debug mode.
- **Feat:** CI sensor integrity tests (pytest) — three automated tests verify sensor definitions, device map assignments, and sensor group consistency on every push.
- **Fix:** `ac_voltage_rs/st/tr` three-phase line-to-line voltage sensors were wired end-to-end but missing from `SENSOR_DEFINITIONS`; added as diagnostic sensors.
- **Fix:** V2.01 profile incorrectly assigned to non-VPP inverters — introduced `vpp_protocol_confirmed` flag; automatic migration downgrades affected entries on startup with a one-time WARNING log.
- **Chore:** Removed orphaned `SENSOR_DEVICE_MAP` entries for legacy BMS register variants.

---

## v0.7.7

- **Refactor:** Composite sensor group constants — introduced `GRID_TIED_1P_SENSORS`, `HYBRID_1P_SENSORS`, `HYBRID_3P_SENSORS` to eliminate 17 verbatim-repeated sensor union blocks across profiles. Net: −201 lines in `device_profiles.py`. No runtime behaviour change.

---

## v0.7.6

- **Refactor:** Extracted `SPE_OFFGRID_SENSORS` constant for the `spe_8000_12000_es` profile, with comments documenting deviations from `SPF_OFFGRID_SENSORS`. No runtime behaviour change.

---

## v0.7.5

- **Fix:** SPH-TL3 power flow corrections — `grid_import_power` and `grid_export_power` sign handling normalised to match other hybrid profiles.

---

## v0.7.4

- **Feat:** Per-string energy sensors (`pv1_energy_today`, `pv2_energy_today`) added for profiles that expose them via registers.
- **Fix:** Register mapping corrections for several SPH and MOD profiles.

---

## v0.7.3

- **Feat:** SPH-TL3 TOU scheduling controls — time period entities for battery charge/discharge scheduling.
- **Feat:** Translations for 20 languages.

---

[View the full release history on GitHub →](https://github.com/0xAHA/Growatt_ModbusTCP/blob/main/RELEASENOTES.md)
