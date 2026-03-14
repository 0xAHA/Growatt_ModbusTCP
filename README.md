# Growatt Modbus Integration for Home Assistant ☀️

![HACS Badge](https://img.shields.io/badge/HACS-Custom-orange.svg)
![Version](https://img.shields.io/badge/Version-0.5.8-blue.svg)
[![GitHub Issues](https://img.shields.io/github/issues/0xAHA/Growatt_ModbusTCP.svg)](https://github.com/0xAHA/Growatt_ModbusTCP/issues)
[![GitHub Stars](https://img.shields.io/github/stars/0xAHA/Growatt_ModbusTCP.svg?style=social)](https://github.com/0xAHA/Growatt_ModbusTCP)

<a href="https://www.buymeacoffee.com/0xAHA" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>

A native Home Assistant integration for Growatt solar inverters using direct Modbus RTU/TCP communication. Get real-time data straight from your inverter without relying on cloud services! 🚀

**Smart Protocol Support:**

- **Auto-detection** - VPP Protocol V2.01 inverters detected automatically via Device Type Code (DTC)
- **Legacy support** - Automatic fallback to V1.39/V3.05 protocols with register probing
- **High success rate** - ~100% detection for V2.01 inverters, ~90% for legacy models

---

## 🌱 Early Adopter Notice

> **This integration is actively evolving with your help!**
>
> **How You Can Help:**
>
> - ✅ **Test and report** - Try the integration with your inverter model
> - 📊 **Share register scans** - Use the built-in Universal Scanner to help verify profiles
> - 🐛 **Report issues** - Found incorrect values? [Open an issue](https://github.com/0xAHA/Growatt_ModbusTCP/issues)
> - ⭐ **Star the repo** - Help others discover this integration
>
> **Current Status:**
>
> - Core functionality is stable and tested on multiple inverter models
> - New features and profiles added regularly based on community feedback
> - Active development with responsive issue resolution

---

## ✨ Features

- 🎯 **Auto-detection** - VPP 2.01 inverters detected automatically (no manual selection!)
- 📊 **Real-time monitoring** - Direct Modbus communication
- 🌙 **Night-time friendly** - Sensors stay available when inverter is offline
- ⚡ **Smart power flow** - Automatic calculation of export, import, and consumption
- 🔌 **Flexible connectivity** - TCP/WiFi adapters or USB/Serial connections
- 📈 **Energy dashboard ready** - Automatic HA Energy Dashboard integration
- 🌡️ **Complete diagnostics** - Temperatures, fault codes, derating status
- 💾 **No cloud dependency** - Local polling, your data stays yours
- 🔄 **Grid power auto-fix** - Automatic CT clamp orientation detection
- 🏠 **Residential focus** - Optimized profiles for home solar (0.6-25kW)
- 🔍 **Universal scanner** - One-click diagnostic tool with auto-detection
- 📱 **Device identification** - Automatic serial, firmware, model, protocol version

---

## 🔌 Supported Inverter Models

**Residential and small commercial** Growatt inverters (0.6-25kW):

**Single-Phase:**

- **Grid-Tied:** MIC 0.6-3.3kW, MIN 3-6kW, MIN 7-10kW ✅
- **Hybrid:** SPH 3-6kW, SPH 7-10kW, SPH/SPM 8-10kW HU, TL-XH 3-10kW, MIN TL-XH 3-10kW
- **Off-Grid:** SPF 3-6kW ES PLUS

**Three-Phase:**

- **Grid-Tied:** MID 15-25kW
- **Hybrid:** MOD 6-15kW, SPH-TL3 3-10kW, WIT 4-15kW

✅ = Tested with real hardware

📖 **[View detailed specifications, protocol support, and sensor availability →](docs/MODELS.md)**

> 💡 **VPP 2.01 inverters** auto-detect via DTC code. Legacy inverters use register probing or manual selection.

---

## 📊 Sensor Overview

**All Models:**

- PV strings (voltage, current, power per string)
- AC output (single or three-phase)
- Energy totals (today, lifetime)
- Grid power (export/import)
- System diagnostics (temps, status, faults)

**Hybrid Models Add:**

- Battery (voltage, current, power, SOC, temperature)
- BMS monitoring (SOH, cycle count, cell voltages) - *HU models*
- Power flow (to grid, to load, to user)
- Battery energy tracking (charge/discharge today/total)

**Model-Specific:**

- **1 PV string:** MIC
- **2 PV strings:** MIN 3-6kW, SPH 3-6kW/7-10kW, SPH-TL3, MID
- **3 PV strings:** MIN 7-10kW, SPH/SPM 8-10kW HU, TL-XH, MOD

📖 **[Complete sensor list by model →](docs/MODELS.md#-sensor-availability-by-model)**

---

## 🛠️ Hardware Setup

### Connection Options

**Option 1: TCP/WiFi Adapter (Recommended)**


| Adapter                    | Wiring             | Settings                        |
| ---------------------------- | -------------------- | --------------------------------- |
| **EW11**                   | RS485 A/B → D+/D- | TCP Server, 9600 baud, port 502 |
| **USR-W630**               | RS485 A/B → A/B   | Modbus TCP Gateway mode         |
| **USR-TCP232-410s**        | RS485 A/B → A/B   | TCP Server, 9600 baud, port 502 |
| **Waveshare RS485-to-ETH** | RS485 A/B → A/B   | 9600 8N1, port 502, Reset: off, Link: on, Index: off, RFC2217: on |

**Waveshare RS485-to-ETH Configuration Details:**

Access the Waveshare web interface and configure:
- **Baud Rate:** 9600
- **Data Bits:** 8
- **Parity:** None
- **Stop Bits:** 1
- **Port:** 502 (Modbus TCP standard)
- **Reset:** Off
- **Link:** On
- **Index:** Off
- **RFC2217 (Similar):** On

**Option 2: USB/Serial Adapter**

Direct USB connection via RS485-to-USB adapter (e.g., `/dev/ttyUSB0` or `COM3`)

### Inverter Wiring


| Connector          | Pins                 | → | Adapter            |
| -------------------- | ---------------------- | ---- | -------------------- |
| **16-pin DRM/COM** | Pin 3 (A), Pin 4 (B) | → | RS485-A/B or D+/D- |
| **4-pin COM**      | Pin 1 (A), Pin 2 (B) | → | RS485-A/B or D+/D- |
| **RJ45 (485-3)**   | Pin 5 (A), Pin 1 (B) | → | RS485-A/B or D+/D- |

> ⚠️ **Tip:** If data looks garbled, try swapping A and B connections. Adapter labeling varies.

---

## 📥 Installation

### Prerequisites

- Home Assistant 2023.1 or newer
- [HACS](https://hacs.xyz/) installed (for HACS installation method)
- RS485-to-TCP adapter or RS485-to-USB adapter configured and accessible
- Inverter connected to adapter via RS485 (A/B wiring)

### Method 1: HACS (Recommended)

[![HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=0xAHA&repository=Growatt_ModbusTCP&category=integration )

**Step 1: Add Custom Repository**

1. Open **HACS** in Home Assistant
2. Click the **⋮** menu (top right)
3. Select **Custom repositories**
4. Enter repository URL: `https://github.com/0xAHA/Growatt_ModbusTCP`
5. Select category: **Integration**
6. Click **Add**

**Step 2: Install Integration**

1. In HACS, search for **"Growatt Modbus Integration"**
2. Click on the integration
3. Click **Download**
4. Select the latest version
5. Click **Download** again to confirm

**Step 3: Restart Home Assistant**

1. Go to **Settings** → **System** → **Restart**
2. Click **Restart** and wait for restart to complete

**Step 4: Add Integration**

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration** (bottom right)
3. Search for **"Growatt Modbus"**
4. Follow the configuration wizard

### Method 2: Manual Installation

**Step 1: Download Integration**

1. Download the [latest release](https://github.com/0xAHA/Growatt_ModbusTCP/releases)
2. Extract the ZIP file

**Step 2: Copy Files**

1. Navigate to your Home Assistant `config` directory
2. If it doesn't exist, create a `custom_components` folder
3. Copy the `growatt_modbus` folder into `custom_components`
4. Final path should be: `config/custom_components/growatt_modbus/`

**Step 3: Verify Installation**

Check that these files exist:

```
config/
└── custom_components/
    └── growatt_modbus/
        ├── __init__.py
        ├── manifest.json
        ├── config_flow.py
        ├── sensor.py
        └── ... (other files)
```

**Step 4: Restart and Configure**

1. **Restart Home Assistant**
2. Go to **Settings** → **Devices & Services**
3. Click **+ Add Integration**
4. Search for **"Growatt Modbus"**
5. Follow the configuration wizard

### Verification

After installation, verify the integration appears:

1. Go to **Settings** → **Devices & Services**
2. Look for **Growatt Modbus** in the integrations list
3. If missing, check **Settings** → **System** → **Logs** for errors

### Updating

**HACS:**

- HACS will notify you of updates
- Click **Update** in HACS when available
- Restart Home Assistant after update

**Manual:**

- Download new release
- Replace files in `custom_components/growatt_modbus/`
- Restart Home Assistant

---

## ⚙️ Configuration

### Quick Setup

1. **Settings** → **Devices & Services** → **Add Integration**
2. Search **"Growatt Modbus"**
3. **Auto-detection runs automatically** (V2.01 inverters)
   - Accept detected model or override manually
4. Enter connection details:
   - **TCP:** Host (IP), Port (502), Slave ID (1)
   - **Serial:** Device path, Baudrate (9600), Slave ID (1)

### Manual Model Selection

If auto-detection fails or you have a legacy inverter:

**Single-Phase Grid-Tied:**

- MIC 600-3300TL-X (1 PV string)
- MIN 3000-6000TL-X (2 PV strings)
- MIN 7000-10000TL-X (3 PV strings)

**Single-Phase Hybrid:**

- SPH 3000-6000 (2 PV, battery)
- SPH 7000-10000 (2 PV, battery)
- SPH/SPM 8000-10000 HU (3 PV, battery, BMS)
- TL-XH 3000-10000 (3 PV, battery)
- MIN TL-XH 3000-10000 (2-3 PV, battery)

**Three-Phase:**

- MID 15000-25000TL3-X (grid-tied)
- MOD 6000-15000TL3-XH (hybrid)
- SPH-TL3 3000-10000 (hybrid)
- WIT 4000-15000TL3 (hybrid)

### Options

Access via **Configure** button:


| Option                 | Default   | Description                            |
| ------------------------ | ----------- | ---------------------------------------- |
| **Device Name**        | "Growatt" | Prefix for all sensor names            |
| **Scan Interval**      | 30s       | Polling frequency (5-300s)             |
| **Connection Timeout** | 10s       | Response timeout (1-60s)               |
| **Invert Grid Power**  | Auto      | Fix backwards CT clamp (auto-detected) |

---

## 🔄 Grid Power Direction

### Auto-Detection (Recommended)

The integration **automatically detects** grid power orientation during setup:

✅ **What happens:**

- Runs during initial setup when solar is producing
- Analyzes power flow direction
- Applies correct setting automatically
- Logs detection result

⚠️ **If setup happens at night:**

- Auto-detection skips (no solar)
- Uses default (usually correct)
- Run manual detection service after sunrise:

```yaml
service: growatt_modbus.detect_grid_orientation
```

### Why This Matters

Growatt inverters use **IEC 61850 standard** (export = positive), while Home Assistant's Power Flow card expects export = negative. The integration handles this conversion automatically.

**Symptoms of wrong setting:**

- Power Flow graph shows backwards arrows
- Export/import values swapped
- House consumption incorrect

**Fix:** Run detection service or toggle "Invert Grid Power" in options.

---

## 🔧 Universal Register Scanner

Test your connection and auto-detect your model **before** or **after** installation:

### How to Use

1. **Developer Tools** → **Services**
2. Search **"Growatt Modbus: Universal Register Scanner"**
3. Select connection type:
   - **TCP:** Enter host, port, slave ID
   - **Serial:** Enter device path, baudrate, slave ID
4. **Call Service**
5. Check notification for auto-detected model
6. Download CSV: `/config/growatt_register_scan_[timestamp].csv`

### What It Does

- Scans all register ranges (legacy + VPP 2.01)
- Auto-detects inverter model with confidence rating
- Shows sample values and detection reasoning
- Exports full register dump with entity values (if configured)
- No terminal/SSH needed!

### Manual Register Operations

For advanced troubleshooting and testing, you can read or write individual registers:

#### Read Register

Read a single input or holding register to inspect its value:

**Example: Read battery SOC (SPH models)**

```yaml
service: growatt_modbus.read_register
data:
  register_type: input
  register_address: 1086
  count: 1
target:
  device_id: YOUR_DEVICE_ID
```

**Example: Read priority mode (SPH holding register)**

```yaml
service: growatt_modbus.read_register
data:
  register_type: holding
  register_address: 1044
  count: 1
target:
  device_id: YOUR_DEVICE_ID
```

**Example: Read 32-bit register pair (battery power)**

```yaml
service: growatt_modbus.read_register
data:
  register_type: input
  register_address: 1009  # LOW word address
  count: 2                # Read both HIGH and LOW
target:
  device_id: YOUR_DEVICE_ID
```

**Returns:** Notification with register value(s) and interpretation

#### Write Register

Write a value to a holding register (control entities):

**Example: Set charge power rate to 50% (SPH models)**

```yaml
service: growatt_modbus.write_register
data:
  register_address: 1090
  value: 50
target:
  device_id: YOUR_DEVICE_ID
```

**Example: Enable AC charge (SPH models)**

```yaml
service: growatt_modbus.write_register
data:
  register_address: 1092
  value: 1  # 0=Disabled, 1=Enabled
target:
  device_id: YOUR_DEVICE_ID
```

**Example: Set time period (HHMM format)**

```yaml
service: growatt_modbus.write_register
data:
  register_address: 1100  # Period 1 start time
  value: 530              # 05:30 in HHMM format
target:
  device_id: YOUR_DEVICE_ID
```

**⚠️ Important Notes:**

- Only write to **holding registers** (writable controls)
- Check profile documentation for valid ranges
- Invalid values may be rejected by inverter
- Changes take effect immediately
- Use control entities (Number/Select) instead when available

---

## 📈 Energy Dashboard

Sensors are pre-configured for the Energy Dashboard:

**Solar Production:**

```
sensor.{name}_solar_total_power
```

**Grid Export/Import:**

```
sensor.{name}_grid_export_power
sensor.{name}_grid_import_power
```

**Home Consumption:**

```
sensor.{name}_house_consumption
```

**Battery (Hybrid models):**

```
sensor.{name}_battery_power
```

> 💡 **Tip:** If grid values appear backwards, run the grid orientation detection service!

---

## 🌙 Night-Time Behavior

When inverter powers down at night:

✅ Sensors remain **available** (not "unavailable")
✅ Last known values retained (typically 0W)
✅ `last_successful_update` attribute shows freshness
✅ DEBUG logs instead of errors
✅ Resumes automatically at sunrise

This prevents sensor unavailability cascades in automations!

---

## 🐛 Troubleshooting

### Connection Issues

**TCP connection fails:**

```bash
# Test network connectivity
ping 192.168.1.100

# Check Modbus port (Linux/Mac)
telnet 192.168.1.100 502
```

**Common fixes:**

- ✅ Check wiring (swap A/B if needed)
- ✅ Verify IP address and port 502
- ✅ Confirm slave ID (usually 1)
- ✅ Set baud rate to 9600
- ✅ Test during daytime (inverter powered on)

### Grid Power Backwards

- ✅ Run `growatt_modbus.detect_grid_orientation` service
- ✅ Or manually toggle **Invert Grid Power** in options

### Wrong Model Detected

- ✅ Delete integration
- ✅ Re-add with manual model selection
- ✅ Use register scanner to verify correct profile

### Sensors Show "Unavailable"

- ✅ Normal at night (first-time setup)
- ✅ Wait for sunrise
- ✅ Check logs for connection errors
- ✅ Verify TCP/Serial connectivity

### Enable Debug Logging

Add to `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.growatt_modbus: debug
```

---

## 🆕 What's New

See **[RELEASENOTES.md](RELEASENOTES.md)** for v0.2.2 details.

**Recent highlights:**

- SPH battery control entities for time-based charging automation
- SPF battery SOC controls expanded to 0-100% for Lithium batteries
- SPF off-grid status codes (fixes "Unknown" status display)
- SPF AC Apparent Power sensor now visible

📖 **[Full changelog →](https://github.com/0xAHA/Growatt_ModbusTCP/releases)**

---

## 🤝 Contributing

**Testing with Hardware:**

- Test with your inverter model
- Run Universal Scanner
- Report results via [GitHub Issues](https://github.com/0xAHA/Growatt_ModbusTCP/issues)
- Include model name, scanner output, and sensor screenshots

**Code Contributions:**

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Test with real hardware
4. Commit changes (`git commit -m 'Add feature'`)
5. Push and open Pull Request

**Most Needed:**

- Validation of untested profiles (SPH, TL-XH, MID, MOD)
- Register scans from different inverter models
- Bug reports with debug logs

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file.

---

## 🙏 Acknowledgments

- Based on [Growatt Modbus RTU Protocol](https://shop.frankensolar.ca/content/documentation/Growatt/AppNote_Growatt_WIT-Modbus-RTU-Protocol-II-V1.39-English-20240416_%28frankensolar%29.pdf)
- Built for the Home Assistant community
- Hardware validation: [@0xAHA](https://github.com/0xAHA) (MIN-10000TL-X), [@JoelSimmo](https://github.com/JoelSimmo) (MOD TL-XH)
- WIT support: [@jekmanis](https://github.com/jekmanis)

---

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/0xAHA/Growatt_ModbusTCP/issues)
- **Discussions:** [GitHub Discussions](https://github.com/0xAHA/Growatt_ModbusTCP/discussions)
- **Community:** [Home Assistant Forum](https://community.home-assistant.io/)

---

**Made with ☀️ and ☕ by [@0xAHA](https://github.com/0xAHA)**

*Turning photons into data, one Modbus packet at a time!* ⚡
