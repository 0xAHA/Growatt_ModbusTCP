# Release Notes

<a href="https://www.buymeacoffee.com/0xAHA" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>

> This page shows recent highlights. The [full changelog](https://github.com/0xAHA/Growatt_ModbusTCP/blob/main/RELEASENOTES.md) on GitHub contains every version with complete details.

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
