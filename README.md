# Growatt Modbus Integration for Home Assistant ☀️

![HACS Badge](https://img.shields.io/badge/HACS-Custom-orange.svg)
![Version](https://img.shields.io/badge/Version-0.9.4-blue.svg)
[![GitHub Issues](https://img.shields.io/github/issues/0xAHA/Growatt_ModbusTCP.svg)](https://github.com/0xAHA/Growatt_ModbusTCP/issues)
[![GitHub Stars](https://img.shields.io/github/stars/0xAHA/Growatt_ModbusTCP.svg?style=social)](https://github.com/0xAHA/Growatt_ModbusTCP)

<a href="https://www.buymeacoffee.com/0xAHA" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>

<details>
<summary>☕ Scan to support</summary>
<br>
<img src="docs/images/qr-code-buymeacoffee.png" alt="Buy Me A Coffee QR code" width="160">
</details>

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

## Support

- **Issues & bug reports:** [GitHub Issues](https://github.com/0xAHA/Growatt_ModbusTCP/issues)
- **Community:** [Home Assistant Forum](https://community.home-assistant.io/)

---

## License

MIT License — see [LICENSE](LICENSE)

---

**Made with ☀️ and ☕ by [@0xAHA](https://github.com/0xAHA)**
