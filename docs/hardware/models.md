# Supported Models and Sensor Availability

---

## How Auto-Detection Works

When you add the integration, it attempts to identify your inverter automatically before asking you to choose a profile.

![Auto-Detection Flow](../images/auto-detection-flow.svg)

**Key points:**

- VPP-capable inverters (DTC present) are identified with high confidence
- Legacy inverters (no DTC) use model name probing — works for MIN, MIC, SPH families
- If auto-detection picks the wrong profile, delete and re-add the integration with manual selection
- The Universal Register Scanner (Developer Tools → Services) shows the detection reasoning in its output

---

## Supported Models

### Single-Phase Grid-Tied

| Model | Range | PV Strings | VPP Support | Auto-detect | Tested | Notes |
|-------|-------|-----------|-------------|-------------|--------|-------|
| **MIC 600-3300TL-X** | 0.6–3.3 kW | 1 | Legacy only | Model name | ✅ | Micro inverter |
| **MIN 3000-6000TL-X** | 3–6 kW | 2 | VPP + Legacy | Model name | ✅ | |
| **MIN 7000-10000TL-X** | 7–10 kW | 3 | VPP + Legacy | Model name | ✅ | |

### Single-Phase Hybrid (with Battery)

| Model | Range | PV Strings | VPP Support | Auto-detect | Tested | Notes |
|-------|-------|-----------|-------------|-------------|--------|-------|
| **MIN TL-XH 3000-10000** | 3–10 kW | 2–3 | VPP | DTC 5100 | ✅ | 3–6kW: 2 strings; 7–10kW: 3 strings |
| **SPA 3000-6000TL BL** | 3–6 kW | None | Legacy only | Auto | ✅ | AC-coupled storage only — no PV DC inputs |
| **SPE 8000-12000 ES** | 8–12 kW | 2 | VPP-like | Model name | ✅ | Peak shaving, parallel operation |
| **SPH 3000-6000** | 3–6 kW | 2 | VPP + Legacy | Model name | ✅ | |
| **SPH 7000-10000** | 7–10 kW | 2 | VPP + Legacy | Model name | ✅ | |
| **SPH/SPM 8000-10000 HU** | 8–10 kW | 3 | VPP + Legacy | DTC | ⚠️ | BMS monitoring (SOH, cell voltages) |

### Single-Phase Off-Grid

| Model | Range | PV Strings | VPP Support | Auto-detect | Tested | Notes |
|-------|-------|-----------|-------------|-------------|--------|-------|
| **SPF 3000-6000 ES PLUS** | 3–6 kW | 2 | Off-grid protocol | Manual | ✅ | No grid export; grid = AC input only |

### Three-Phase

| Model | Range | PV Strings | Battery | VPP Support | Auto-detect | Tested | Notes |
|-------|-------|-----------|---------|-------------|-------------|--------|-------|
| **MID 15000-25000TL3-X** | 15–25 kW | 2 | No | VPP + Legacy | Model name | ⚠️ | Grid-tied |
| **MOD 6000-15000TL3-XH** | 6–15 kW | 3 | Yes | VPP + Legacy | DTC 5400 | ✅ | Battery monitoring only (control pending) |
| **SPH-TL3 3000-10000** | 3–10 kW | 2 | Yes | VPP + Legacy | DTC | ✅ | Tested: SPH 8000TL3 BH-UP |
| **WIT 4000-15000TL3** | 4–15 kW | 2 | Yes | VPP v2.02 | DTC 5603 | ✅ | Advanced VPP control |

**Legend:** ✅ Tested with real hardware · ⚠️ Profile from documentation, community validation welcome

> **VPP Protocol:** Growatt's Virtual Power Plant Protocol (registers 30000+) enables advanced monitoring and control, and allows automatic model identification via Device Type Code. Models with "VPP + Legacy" fall back to the legacy register range (0–3999) if VPP registers don't respond.

> **Off-Grid Protocol:** SPF inverters use registers 0–97 only. VPP registers are never attempted for these models.

> **Help us test!** If you have an untested model, run the Universal Register Scanner and open an issue with the CSV output.

---

## Sensor Availability by Model

| Sensor | MIC | MIN 3-6k | MIN 7-10k | MIN TL-XH | SPA | SPH 3-6k | SPH 7-10k | SPF | SPH-TL3 | MID | MOD | WIT |
| -------- | :---: | :--------: | :---------: | :---------: | :---: | :--------: | :---------: | :---: | :-------: | :---: | :---: | :---: |
| **Solar Input** | | | | | | | | | | | | |
| PV1 Voltage/Current/Power | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| PV2 Voltage/Current/Power | ❌ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| PV3 Voltage/Current/Power | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| Solar Total Power | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **AC Output (Single-Phase)** | | | | | | | | | | | | |
| AC Voltage / Current / Power | ✅ | ✅ | ✅ | ✅ | ⚠️† | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| AC Apparent Power | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| AC Frequency | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **AC Output (Three-Phase)** | | | | | | | | | | | | |
| Phase R/S/T Voltage / Current / Power | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| AC Total Power | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| **Power Flow** | | | | | | | | | | | | |
| Grid Export / Import Power | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| House Consumption (calculated) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Self Consumption | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Power to Grid / Load / User (registers) | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ |
| **Battery (Hybrid/Off-Grid)** | | | | | | | | | | | | |
| Battery Voltage / Current / Power | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ |
| Battery SOC | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ |
| Battery Temperature | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ |
| BMS SOH / Cell Voltages | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅* | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Energy Totals** | | | | | | | | | | | | |
| Energy Today / Total (PV) | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Energy to Grid Today / Total | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Load Energy Today / Total | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Charge / Discharge Energy Today / Total | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ |
| AC Charge Energy Today / Total | ❌ | ❌ | ❌ | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ |
| **System & Diagnostics** | | | | | | | | | | | | |
| Inverter / IPM Temperature | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Boost Temperature | ❌ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Status / Derating / Fault Codes | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

*HU variants only (SPH/SPM 8000-10000TL3-BH-HU)
†AC voltage only (reg 1105, scale ×0.01); AC current/power and frequency not confirmed for SPA

---

## Power Flow Notes

### Grid-Tied Models (MIC, MIN TL-X, MID)

No battery and no direct load measurement register. Power flow values are **calculated**:

```text
house_consumption  = solar_total_power - grid_export_power + grid_import_power
self_consumption   = min(solar_total_power, house_consumption)
grid_export_power  = max(0,  power_to_grid)
grid_import_power  = max(0, -power_to_grid)
```

### Hybrid Models (SPH, TL-XH, MOD, WIT)

Both calculated and register-based values are available. Register-based sensors (`power_to_load`, `power_to_user`, `power_to_grid`) are read directly from the inverter and are generally more accurate.

**Battery power sign convention (all models):**

- **Positive** = Battery is charging
- **Negative** = Battery is discharging

> SPF off-grid inverters have hardware that reports the opposite polarity. The integration inverts this automatically — you always see the standard convention regardless of model.

---

## Invert Grid Power

All models support an **Invert Grid Power** option to correct backwards CT clamp installations. When enabled, grid import and export values are swapped, and the sign of all grid power/energy sensors is flipped.

**When to enable:** If the Power Flow card shows export when you are actually importing, or vice versa.

**How to enable:** Integration → **Configure** → toggle **Invert Grid Power**.

---

## Manual Model Selection Guide

If auto-detection fails (or you want to override), choose based on:

1. **Phase:** Single-phase or three-phase grid connection?
2. **Battery:** Do you have battery storage connected?
3. **PV strings:** How many separate solar array strings are connected?
4. **Power range:** Inverter nameplate rating

### Single-Phase Grid-Tied Models

| Select this | PV Strings | Power | When |
|-------------|-----------|-------|------|
| MIC 600-3300TL-X | 1 | 0.6–3.3 kW | Micro inverter, single string |
| MIN 3000-6000TL-X | 2 | 3–6 kW | Standard residential |
| MIN 7000-10000TL-X | 3 | 7–10 kW | Larger residential |

### Single-Phase Hybrid Models

| Select this | PV Strings | Power | When |
|-------------|-----------|-------|------|
| MIN TL-XH 3000-10000 | 2–3 | 3–10 kW | Battery hybrid (3–6kW: 2 strings, 7–10kW: 3 strings) |
| SPA 3000-6000TL BL | None | 3–6 kW | AC-coupled battery storage only (no PV inputs) |
| SPE 8000-12000 ES | 2 | 8–12 kW | Battery hybrid, peak shaving |
| SPF 3000-6000 ES PLUS | 2 | 3–6 kW | Off-grid with battery |
| SPH 3000-6000 | 2 | 3–6 kW | Battery hybrid |
| SPH 7000-10000 | 2 | 7–10 kW | Battery hybrid |
| SPH/SPM 8000-10000 HU | 3 | 8–10 kW | Battery hybrid with BMS monitoring |

### Three-Phase Models

| Select this | PV Strings | Battery | Power | When |
|-------------|-----------|---------|-------|------|
| MID 15000-25000TL3-X | 2 | No | 15–25 kW | Grid-tied only |
| MOD 6000-15000TL3-XH | 3 | Yes | 6–15 kW | Hybrid with battery |
| SPH-TL3 3000-10000 | 2 | Yes | 3–10 kW | Hybrid with battery |
| WIT 4000-15000TL3 | 2 | Yes | 4–15 kW | Hybrid, advanced VPP control |

---

## Device Information

The integration reads and displays identifying information about your inverter at startup:

| Field | Example | Notes |
|-------|---------|-------|
| Model Name | MIN-10000TL-X | From registers 125–132 |
| Serial Number | AB12345678 | From registers 23–27 or 3000–3015 |
| Firmware Version | 2.01 | |
| Protocol Version | VPP V2.01 | VPP models only |

---

*For control entity details, see [CONTROL.md](../controls/entity-reference.md)*
