# Growatt Modbus Integration

![HACS Badge](https://img.shields.io/badge/HACS-Custom-orange.svg)
![Version](https://img.shields.io/badge/Version-0.7.8-blue.svg)
[![GitHub Issues](https://img.shields.io/github/issues/0xAHA/Growatt_ModbusTCP.svg)](https://github.com/0xAHA/Growatt_ModbusTCP/issues)

A native Home Assistant integration for Growatt solar inverters using **direct Modbus RTU/TCP communication**. Real-time data straight from your inverter — no cloud, no ShineWiFi, no dependency on Growatt's servers.

---

## How It Works

![System Topology](images/system-topology.svg)

The integration polls your inverter directly over Modbus — the same protocol the inverter uses natively. No cloud account is required and no data leaves your home network. A RS485-to-TCP (or RS485-to-USB) adapter bridges the inverter's serial port to your Home Assistant instance.

---

## Quick Navigation

<div class="grid cards" markdown>

-   **Hardware**

    Supported inverter models, hardware wiring, and auto-detection system

    [Supported Models](hardware/models.md) · [Auto-Detection](hardware/autodetection.md)

-   **Controls**

    Battery mode switching, TOU scheduling, and inverter-specific control guides

    [Entity Reference](controls/entity-reference.md) · [Battery & Scheduling](controls/battery-scheduling.md) · [WIT Guide](controls/wit-guide.md)

-   **Troubleshooting**

    Built-in diagnostic tools and DTC debugging guides

    [Diagnostic Service](troubleshooting/diagnostic-service.md) · [DTC Debugging](troubleshooting/dtc-debugging.md)

-   **Developer**

    Contributing sensors, protocol research, and internal architecture notes

    [Adding Sensors](developer/sensor-checklist.md) · [Protocol Database](developer/protocol-database.md)

</div>

---

## Device Structure

When you add the integration, it creates **up to five devices** in Home Assistant:

![Device Hierarchy](images/device-hierarchy.svg)

| Device | Always present? | Key entities |
|--------|-----------------|--------------|
| **Inverter** | Yes | Status, inverter temp, fault code, firmware version |
| **Solar** | Yes | `pv1_power`, `solar_total_power`, `energy_today`, `energy_total` |
| **Grid** | Yes | `grid_export_power`, `grid_import_power`, `energy_to_grid_today` |
| **Load** | Yes | `house_consumption`, `power_to_load`, `load_energy_today` |
| **Battery** | Hybrid models only | `battery_soc`, `battery_power`, `charge_energy_today` |

> The Battery device is automatically created for hybrid and off-grid profiles. It will not appear for grid-tied-only models (MIC, MIN TL-X, MID).

---

## Installation

Full setup instructions — including HACS install, manual install, and initial configuration — are in the [README on GitHub](https://github.com/0xAHA/Growatt_ModbusTCP#installation).

### Requirements

- Home Assistant 2024.1 or later
- A RS485-to-TCP adapter (e.g. Waveshare, USR-W610) **or** a RS485-to-USB cable
- Your inverter's Modbus slave ID (usually `1` — check the inverter display)

---

## Supported Models at a Glance

| Family | Type | Auto-detect |
|--------|------|-------------|
| SPH TL3-BH | Single-phase hybrid | DTC |
| MOD TL3-X | Three-phase hybrid | DTC |
| MIN TL-XH | Single-phase hybrid (small) | DTC |
| SPF ES | Off-grid | DTC |
| WIT TL3 | Three-phase commercial | DTC |
| MIC / MIN TL-X | Grid-tied | Register probe |
| MID TL3 | Three-phase grid-tied | Register probe |

See [Supported Models](hardware/models.md) for the full matrix including sensor availability.
