# Supported Models and Sensor Availability

This document provides detailed information about supported Growatt inverter models and their sensor capabilities.

---

## 🔌 Supported Inverter Models

The integration supports **residential and small commercial** Growatt inverters (3-25kW range) with automatic model detection for VPP-capable inverters and manual selection for older models.

### Single-Phase Grid-Tied Inverters

| Inverter Series | Model Range | PV Strings | Battery | VPP Support | Tested | Notes |
|-----------------|-------------|------------|---------|-------------|--------|-------|
| **MIC 600-3300TL-X** | 600-3300TL-X | 1 | No | ❌ Legacy | ⚠️ Untested | Micro inverter, 0.6-3.3kW |
| **MIN 3000-6000TL-X** | 3000-6000TL-X | 2 | No | ✅ VPP + Legacy | ⚠️ Untested | Grid-tied, 3-6kW |
| **MIN 7000-10000TL-X** | 7000-10000TL-X | 3 | No | ✅ VPP + Legacy | ✅ **Tested** | Grid-tied, 7-10kW |

### Single-Phase Hybrid Inverters (with Battery)

| Inverter Series | Model Range | PV Strings | Battery | VPP Support | Tested | Notes |
|-----------------|-------------|------------|---------|-------------|--------|-------|
| **TL-XH 3000-10000** | TL-XH 3000-10000 | 3 | Yes | ✅ VPP + Legacy | ⚠️ Untested | Hybrid with battery, 3-10kW |
| **TL-XH US 3000-10000** | TL-XH US 3000-10000 | 3 | Yes | ✅ VPP + Legacy | ⚠️ Untested | US version hybrid, 3-10kW |
| **MIN TL-XH 3000-10000** | MIN 6000/10000 TL-XH | 2-3 | Yes | ✅ VPP | ✅ **Tested** | MIN hybrid with battery, DTC 5100, 3-6kW: 2 strings, 7-10kW: 3 strings, **Fixed v0.2.4** |
| **SPH 3000-6000** | SPH 3000-6000 | 2 | Yes | ✅ VPP + Legacy | ⚠️ Untested | Storage hybrid, 3-6kW |
| **SPH 7000-10000** | SPH 7000-10000 | 2 | Yes | ✅ VPP + Legacy | ⚠️ Untested | Storage hybrid, 7-10kW |

### Single-Phase Off-Grid Inverters

| Inverter Series | Model Range | PV Strings | Battery | VPP Support | Tested | Notes |
|-----------------|-------------|------------|---------|-------------|--------|-------|
| **SPF 3000-6000 ES PLUS** | SPF 3000-6000 ES PLUS | 2 | Yes | ❌ Off-Grid Protocol | ✅ **Tested** | Off-grid with battery, 3-6kW, **Fixed v0.2.4** |

### Three-Phase Inverters

| Inverter Series | Model Range | PV Strings | Battery | VPP Support | Tested | Notes |
|-----------------|-------------|------------|---------|-------------|--------|-------|
| **MID 15000-25000TL3-X** | 15000-25000TL3-X | 2 | No | ✅ VPP + Legacy | ⚠️ Untested | Grid-tied, 15-25kW |
| **MOD 6000-15000TL3-XH** | MOD 6000-15000TL3-XH | 3 | Yes | ✅ VPP + Legacy | ✅ **Tested** | Hybrid with battery, 6-15kW, **Fixed v0.2.4** |
| **SPH-TL3 3000-10000** | SPH-TL3 3000-10000 | 2 | Yes | ✅ VPP + Legacy | ⚠️ Untested | Three-phase hybrid, 3-10kW |
| **WIT 4000-15000TL3** | WIT 4000-15000TL3 | 2 | Yes | ✅ VPP v2.02 | ⚠️ Untested | Three-phase hybrid with advanced storage, 4-15kW, DTC 5603 |

**Legend:**
- ✅ **Tested** - Confirmed working with real hardware
- ⚠️ **Untested** - Profile created from official documentation, needs validation
- **✅ VPP** - Supports Growatt VPP Protocol (auto-detection via DTC available)
- **✅ VPP + Legacy** - Supports both VPP and legacy protocols (automatic fallback)
- **❌ Legacy** - Uses V1.39/V3.05 register maps only (manual selection required)
- **❌ Off-Grid Protocol** - Uses off-grid protocol (register range 0-124, no VPP support)

**About VPP Protocol:**
- **VPP** = Virtual Power Plant Protocol - Growatt's modern communication protocol for grid-interactive inverters
- Uses extended register ranges (30000+, 31000+) for enhanced monitoring and control
- Supports automatic model detection via Device Type Code (DTC)
- Protocol versions include V2.01 (201), V2.02 (202), and future versions
- Models with "VPP + Legacy" support both register ranges for maximum compatibility

> 💡 **Help us test!** If you have a model marked as untested and can confirm it works, please open an issue or PR!

> 🏭 **Commercial/Industrial Models:** Large commercial inverters (MAC, MAX, WIT 30-150kW) have been removed to maintain focus on residential systems. If you need these profiles, see legacy v0.0.3 release.

---

## 📊 Sensor Availability by Model

Different inverter models create different sensors based on their hardware capabilities:

| Sensor | MIC | MIN 3-6k | MIN 7-10k | MIN TL-XH | TL-XH | SPH 3-6k | SPH 7-10k | SPF | SPH-TL3 | MID | MOD | WIT |
|--------|:---:|:--------:|:---------:|:---------:|:-----:|:--------:|:---------:|:---:|:-------:|:---:|:---:|:---:|
| **Solar Input (PV Strings)** | | | | | | | | | | | | |
| PV1 Voltage/Current/Power | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| PV2 Voltage/Current/Power | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| PV3 Voltage/Current/Power | ❌ | ❌ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| Solar Total Power | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **AC Output (Single-Phase)** | | | | | | | | | | | | |
| AC Voltage | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| AC Current | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| AC Power (Active Power) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| AC Apparent Power | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| AC Frequency | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **AC Output (Three-Phase)** | | | | | | | | | | | | |
| AC Phase R/S/T Voltage | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| AC Phase R/S/T Current | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| AC Phase R/S/T Power | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| AC Total Power | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| **Power Flow (Calculated)** | | | | | | | | | | | | |
| Grid Export Power | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Grid Import Power | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Self Consumption | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| House Consumption | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Power Flow (From Registers)** | | | | | | | | | | | | |
| Power to Grid | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ |
| Power to Load | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ |
| Power to User | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ |
| **Battery (Hybrid Only)** | | | | | | | | | | | | |
| Battery Voltage/Current/Power | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ |
| Battery SOC | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ |
| Battery Temperature | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ |
| **Energy Totals** | | | | | | | | | | | | |
| Energy Today/Total | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Energy to Grid Today/Total | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Load Energy Today/Total | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **System & Diagnostics** | | | | | | | | | | | | |
| Inverter Temperature | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| IPM Temperature | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Boost Temperature | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Status/Derating/Faults | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

**Legend:**
- ✅ Available for this model
- ❌ Not available (hardware limitation)

---

## 📝 Notes on Power Flow

### Grid-Tied Models (MIN, MIC, MID)
- No battery or direct load measurement
- **Power flow calculated** from solar production vs AC output
- Formulas:
  ```
  Grid Power = AC Output - Solar Production
    Positive = Exporting to grid
    Negative = Importing from grid

  Self Consumption = min(Solar Production, House Consumption)
  House Consumption = Solar Production - Grid Export + Grid Import
  ```

### Hybrid Models (TL-XH, SPH, MOD)
- Battery and load measured directly from registers
- Both **calculated** and **register-based** power flow available
- Register-based sensors preferred for accuracy (when available)
- Battery power sign convention:
  - **Positive** = Charging
  - **Negative** = Discharging

---

## 🔄 Invert Grid Power Option

All models support the **Invert Grid Power** configuration option to correct backwards CT clamp installations:

**When to use:**
- Your "Grid Import" shows power when exporting to grid
- Your "Grid Export" shows power when importing from grid
- Grid power values are the opposite of what they should be

**What it does:**
- Automatically flips the sign of grid power measurements
- Swaps Grid Import ⬌ Grid Export sensor values
- Applies to both power (W) and energy (kWh) sensors
- No need for template sensors or workarounds!

**How to enable:**
1. Go to **Growatt Modbus** integration → **Configure**
2. Toggle **Invert Grid Power** to ON
3. Changes apply on next update (within scan interval)

---

## 🔍 Model Selection Guide

### During Setup (Auto-Detection)

For **VPP-capable** inverters, auto-detection reads the Device Type Code (DTC) from register 30000:
- Automatically identifies your model
- Shows confirmation screen with detected model
- Option to accept or manually override

See [AUTODETECTION.md](AUTODETECTION.md) for details on how auto-detection works.

### Manual Selection Required

For **legacy protocol** inverters (no VPP support):
- Auto-detection fails (DTC register not readable)
- Manual model selection required
- Choose based on:
  - **PV strings:** How many solar panel strings you have connected (1, 2, or 3)
  - **Phase:** Single-phase or three-phase grid connection
  - **Battery:** Hybrid models if you have battery storage

### Selection Reference Tables

#### Single-Phase Grid-Tied
| Selection | PV Strings | Power Range | When to Use |
|-----------|------------|-------------|-------------|
| **MIC 600-3300TL-X** | 1 | 0.6-3.3kW | Micro inverter, 1 PV string |
| **MIN 3000-6000TL-X** | 2 | 3-6kW | Standard residential, 2 PV strings |
| **MIN 7000-10000TL-X** | 3 | 7-10kW | Larger residential, 3 PV strings |

#### Single-Phase Hybrid
| Selection | PV Strings | Power Range | When to Use |
|-----------|------------|-------------|-------------|
| **SPH 3000-6000** | 2 | 3-6kW | Storage hybrid, 2 PV strings |
| **SPH 7000-10000** | 2 | 7-10kW | Storage hybrid, 2 PV strings |
| **TL-XH 3000-10000** | 3 | 3-10kW | Hybrid with battery, 3 PV strings |
| **TL-XH US 3000-10000** | 3 | 3-10kW | US version hybrid, 3 PV strings |

#### Three-Phase
| Selection | PV Strings | Power Range | Battery | When to Use |
|-----------|------------|-------------|---------|-------------|
| **MID 15000-25000TL3-X** | 2 | 15-25kW | No | Grid-tied, 3-phase |
| **MOD 6000-15000TL3-XH** | 3 | 6-15kW | Yes | Hybrid, 3-phase with battery |
| **SPH-TL3 3000-10000** | 2 | 3-10kW | Yes | Hybrid, 3-phase with battery |

---

## 📱 Device Information

The integration automatically reads and displays device information (when available):

| Field | Example | Register Source | Availability |
|-------|---------|----------------|--------------|
| **Model Name** | MIN-10000TL-X | 125-132 (parsed) | VPP + Legacy |
| **Serial Number** | AB12345678 | 23-27 or 3000-3015 | VPP + Legacy |
| **Firmware Version** | 2.01 | 9-11 | VPP + Legacy |
| **Hardware Version** | VPP Protocol V2.01 | 30099 (protocol version) | VPP only |

**Hardware Version Display:**
- **"VPP Protocol V2.01"** - Supports VPP register ranges (register 30099 = 201)
- **"VPP Protocol V2.02"** - Supports VPP v2.02 (register 30099 = 202)
- **"Legacy Protocol"** - Legacy register ranges only (register 30099 not readable or = 0)

View in **Settings** → **Devices & Services** → **Growatt Modbus** → Click your inverter device

---

## 🧪 Testing Status

### Tested Models (Confirmed Working)

The following models have been validated with real hardware:
- ✅ **MIN 7000-10000TL-X** - Grid-tied, 3 PV strings
- ✅ **MIN TL-XH (MIN-4600TL-XH)** - Hybrid with ARK battery (v0.2.4)
- ✅ **MOD 10000TL3-XH** - Three-phase hybrid with ARK battery (v0.2.4)
- ✅ **SPF 6000 ES PLUS** - Off-grid with battery (v0.2.4)

### Community Testing Needed

Many models still need validation with real hardware. We need community members to test!

**If you successfully test a model**, please report via GitHub Issues with:
- Model name from inverter display
- Universal Scanner detection results (if VPP-capable)
- Screenshot of working sensors
- Any issues or missing sensors

Your contribution helps improve the integration for everyone! 🙏

---

[← Back to README](../README.md) | [Auto-Detection Details →](AUTODETECTION.md)
