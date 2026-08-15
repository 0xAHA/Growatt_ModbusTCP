<a href="https://www.buymeacoffee.com/0xAHA" target="_blank"><img src="docs/images/qr-code-buymeacoffee.png" alt="Buy Me A Coffee QR code" width="130" align="right"></a>

# Growatt Modbus Integration for Home Assistant ☀️

![HACS Badge](https://img.shields.io/badge/HACS-Custom-orange.svg)
[![Version](https://img.shields.io/github/v/release/0xAHA/Growatt_ModbusTCP?label=Version&color=blue)](https://github.com/0xAHA/Growatt_ModbusTCP/releases/latest)
[![Installations](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fanalytics.home-assistant.io%2Fcustom_integrations.json&query=%24.growatt_modbus.total&label=Installations&color=41BDF5&logo=home-assistant&logoColor=white&cacheSeconds=21600)](https://analytics.home-assistant.io/#integrations)
[![GitHub Issues](https://img.shields.io/github/issues/0xAHA/Growatt_ModbusTCP.svg)](https://github.com/0xAHA/Growatt_ModbusTCP/issues)
[![GitHub Stars](https://img.shields.io/github/stars/0xAHA/Growatt_ModbusTCP.svg?style=social)](https://github.com/0xAHA/Growatt_ModbusTCP)

<a href="https://www.buymeacoffee.com/0xAHA" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>

A native Home Assistant integration for Growatt solar inverters using **direct Modbus RTU/TCP communication**. Real-time data straight from your inverter — no cloud, no ShineWiFi, no dependency on Growatt's servers.

## 📖 [Full documentation → https://0xaha.github.io/Growatt_ModbusTCP/](https://0xaha.github.io/Growatt_ModbusTCP/)

The documentation site covers supported models, sensor reference, inverter controls, energy dashboard setup, troubleshooting, and developer guides.

---

## Installation

### HACS (Recommended)

[![Install via HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=0xAHA&repository=Growatt_ModbusTCP&category=integration)

1. Open **HACS** → **⋮ menu** → **Custom repositories**
2. Add URL `https://github.com/0xAHA/Growatt_ModbusTCP`, category: **Integration**
3. Search **"Growatt Modbus"** in HACS → **Download**
4. **Restart Home Assistant**
5. **Settings** → **Devices & Services** → **Add Integration** → search **"Growatt Modbus"**

### Manual

1. Download the [latest release](https://github.com/0xAHA/Growatt_ModbusTCP/releases) and extract
2. Copy `growatt_modbus/` into `config/custom_components/`
3. Restart Home Assistant and add via **Settings** → **Devices & Services**

---

## Setup

The setup wizard runs auto-detection automatically for VPP-capable inverters. For legacy models, select the profile manually based on your inverter's power range.

| Parameter | TCP | Serial |
| --- | --- | --- |
| Host / Device | IP address (e.g. `192.168.1.100`) | Path (e.g. `/dev/ttyUSB0`) |
| Port / Baudrate | `502` | `9600` |
| Slave ID | `1` (usually) | `1` (usually) |

---

## Documentation

| Page | What it covers |
| --- | --- |
| [Supported Models](https://0xaha.github.io/Growatt_ModbusTCP/hardware/models/) | Which profile matches your inverter |
| [Auto-Detection](https://0xaha.github.io/Growatt_ModbusTCP/hardware/autodetection/) | How the profile is chosen, and how to override it |
| [Entity Reference](https://0xaha.github.io/Growatt_ModbusTCP/controls/entity-reference/) | Every sensor and control, and what it means |
| [Battery & Scheduling](https://0xaha.github.io/Growatt_ModbusTCP/controls/battery-scheduling/) | Charge/discharge limits and time-of-use periods |
| [RS485 Gateways](https://0xaha.github.io/Growatt_ModbusTCP/troubleshooting/rs485-gateways/) | Which adapters work, and diagnosing one that doesn't |
| [DTC Debugging](https://0xaha.github.io/Growatt_ModbusTCP/troubleshooting/dtc-debugging/) | Device type codes and profile mappings |
| [Raising an Issue](https://0xaha.github.io/Growatt_ModbusTCP/troubleshooting/raising-an-issue/) | What to include so it can actually be diagnosed |
| [Protocol Reference](https://0xaha.github.io/Growatt_ModbusTCP/developer/protocol-vpp/) | Register maps for V1.39, VPP and off-grid |

---

## Support

- **Issues & bug reports:** [GitHub Issues](https://github.com/0xAHA/Growatt_ModbusTCP/issues)
- **Community:** [Home Assistant Forum](https://community.home-assistant.io/)

---

## License

MIT License — see [LICENSE](LICENSE)

---

## Thanks

This integration is built almost entirely on evidence from people's own hardware. Register
maps get confirmed because someone ran a scan at two different times of day; wrong mappings
get found because someone noticed a battery reading 0.0 °C and said so; whole model
families get supported because someone asked Growatt for a protocol document and shared it.

Several of the most useful reports were people **correcting their own earlier findings**
after measuring properly — which is what stopped working registers being "fixed" into
broken ones.

Contributions are credited where they're used: in the
[release notes](https://github.com/0xAHA/Growatt_ModbusTCP/releases), in the issue each one
came from, and in comments beside the registers they established. That keeps the credit
attached to the thing it explains, rather than in a list that goes stale and quietly
excludes whoever was added last.

If you have an inverter model or gateway that isn't well covered,
[a register scan](https://0xaha.github.io/Growatt_ModbusTCP/troubleshooting/diagnostic-service/)
is the single most useful thing you can contribute.

---

**Made with ☀️ and ☕ by [@0xAHA](https://github.com/0xAHA)**
