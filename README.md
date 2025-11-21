# Growatt Modbus Integration for Home Assistant ☀️

![HACS Badge](https://img.shields.io/badge/HACS-Custom-orange.svg)
![Version](https://img.shields.io/badge/Version-0.0.7b2-blue.svg)
[![GitHub Issues](https://img.shields.io/github/issues/0xAHA/Growatt_ModbusTCP.svg)](https://github.com/0xAHA/Growatt_ModbusTCP/issues)
[![GitHub Stars](https://img.shields.io/github/stars/0xAHA/Growatt_ModbusTCP.svg?style=social)](https://github.com/0xAHA/Growatt_ModbusTCP)

A native Home Assistant integration for Growatt solar inverters using direct Modbus RTU/TCP communication. Get real-time data straight from your inverter without relying on cloud services! 🚀

**Protocol Support:**
- **Primary:** Growatt VPP Protocol V2.01 with automatic model detection via Device Type Code (DTC)
- **Fallback:** Legacy protocols (V1.39, V3.05) with manual model selection for older inverters
- **Smart Detection:** Automatically uses best available protocol based on inverter capabilities

---

## ✨ Features

- 🎯 **Auto-detection** - VPP 2.01 inverters detected automatically via DTC code (no manual selection needed!)
- 📊 **Real-time monitoring** - Direct Modbus communication with your inverter
- 🌙 **Night-time friendly** - Sensors stay available when inverter is offline (no sun)
- ⚡ **Smart power flow** - Automatic calculation of export, import, and self-consumption
- 🔌 **TCP connection** - WiFi/Ethernet adapters for reliable communication
- 📈 **Energy dashboard ready** - Automatic integration with HA Energy Dashboard
- 🌡️ **Complete diagnostics** - Temperatures, fault codes, derating status
- 💾 **No cloud dependency** - Local polling, your data stays yours
- 🔄 **Grid power inversion** - Fix backwards CT clamp installations with one click
- 🏠 **Residential focus** - Optimized profiles for home solar systems (3-25kW)
- 🔍 **Universal scanner** - One-click diagnostic tool auto-detects your inverter model
- 📱 **Device identification** - Automatic serial number, firmware version, exact model, and protocol version

---

## 🔌 Supported Inverter Models

The integration supports **residential and small commercial** Growatt inverters (3-25kW range):

**Single-Phase Grid-Tied:** MIC (0.6-3.3kW), MIN 3-6kW, MIN 7-10kW ✅
**Single-Phase Hybrid:** SPH 3-6kW, SPH 7-10kW, TL-XH 3-10kW, TL-XH US 3-10kW
**Three-Phase:** MID 15-25kW, MOD 6-15kW, SPH-TL3 3-10kW

✅ = Tested with real hardware | Most models created from official documentation (validation needed)

📖 **[View detailed model specifications, protocol support, and sensor availability →](docs/MODELS.md)**

> 💡 **VPP 2.01 inverters** are auto-detected via DTC code. Legacy inverters require manual selection.

---

## 📊 What Sensors Will I Get?

Sensors created depend on your inverter's hardware capabilities:

**All Models:**
- Solar PV strings (voltage, current, power per string)
- AC output (single-phase or three-phase depending on model)
- Energy totals (today, lifetime)
- Grid power (export/import, calculated or from registers)
- System diagnostics (temperatures, status, faults)

**Hybrid Models Only** (TL-XH, SPH, SPH-TL3, MOD):
- Battery voltage, current, power, SOC, temperature
- Direct power flow measurements (to grid, to load, to user)

**Model-Specific Details:**
- **1 PV string:** MIC only
- **2 PV strings:** MIN 3-6kW, SPH 3-6kW/7-10kW, SPH-TL3, MID
- **3 PV strings:** MIN 7-10kW, TL-XH, MOD

📖 **[View complete sensor availability table by model →](docs/MODELS.md#-sensor-availability-by-model)**

---

## 🛠️ Hardware Setup

### Inverter Connection

Growatt inverters have a **SYS/COM port** on the bottom. For units with a 4 or 16pin COM port, it is likely that your inverter installer ran a small cable only connecting the 2 pins to the smart meter. There should be space to put another cable through the gland to connect the RS485 adapter. Conveniently, the terminals are just small screw terminals so no special tool/pins are required. Hybrid and 3-phase models will likely have an RJ45 connection. See below for further wiring examples.

### Connection Hardware

Use an RS485-to-TCP/WiFi adapter:


| Adapter                    | Connection                 | Settings                        |
| ---------------------------- | ---------------------------- | --------------------------------- |
| **EW11**                   | RS485 A/B to adapter D+/D- | TCP Server, 9600 baud, port 502 |
| **USR-W630**               | RS485 A/B to adapter A/B   | Modbus TCP Gateway mode         |
| **USR-TCP232-410s**        | RS485 A/B to adapter A/B   | TCP Server, 9600 baud, port 502 |
| **Waveshare RS485-to-ETH** | RS485 A/B to adapter A/B   | Modbus TCP mode, 9600 baud      |

**Wiring:**


| Connector Type     | Pin   | Function   | → | Adapter Connection |
| -------------------- | ------- | ------------ | ---- | -------------------- |
| **16-pin DRM/COM** | Pin 3 | A (RS485+) | → | RS485-A (or D+)    |
|                    | Pin 4 | B (RS485-) | → | RS485-B (or D-)    |
| **4-pin COM**      | Pin 1 | A (RS485+) | → | RS485-A (or D+)    |
|                    | Pin 2 | B (RS485-) | → | RS485-B (or D-)    |
| **RJ45 (485-3)**   | Pin 1 | B (RS485-) | → | RS485-B (or D-)    |
|                    | Pin 2 | GND        | → | GND (optional)*    |
|                    | Pin 5 | A (RS485+) | → | RS485-A (or D+)    |

*GND connection may not be required depending on your RS485 adapter

> ⚠️ **Note:** If data looks garbled, try swapping A and B connections. Some adapters label differently.

### Inverter Settings (optional)

1. Access inverter menu (usually hold OK button for 3 seconds)
2. Navigate to **Communication** settings
3. Set **Modbus Address**: `1` (default)
4. Set **Baud Rate**: `9600` (default)
5. Save and exit

---

## 📥 Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to **Integrations**
3. Click the **⋮** menu (top right) → **Custom repositories**
4. Add repository: `https://github.com/0xAHA/Growatt_ModbusTCP`
5. Category: **Integration**
6. Click **Add**
7. Find "Growatt Modbus Integration" and click **Download**
8. Restart Home Assistant
9. Go to **Settings** → **Devices & Services** → **Add Integration**
10. Search for "Growatt Modbus"

### Manual Installation

1. Download the latest release from [GitHub](https://github.com/0xAHA/Growatt_ModbusTCP/releases)
2. Extract to `custom_components/growatt_modbus/` in your HA config directory
3. Restart Home Assistant
4. Go to **Settings** → **Devices & Services** → **Add Integration**
5. Search for "Growatt Modbus"

---

## ⚙️ Configuration

### Initial Setup

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration** → Search for **Growatt Modbus**
3. Select your **Inverter Series** from the dropdown (alphabetically sorted)
4. Enter your TCP connection details

### Inverter Series Selection

Choose the profile that matches your inverter model:

#### Single-Phase Grid-Tied


| Selection              | When to Use                                 |
| ------------------------ | --------------------------------------------- |
| **MIC 600-3300TL-X**   | 1 PV string models (0.6-3.3kW single-phase) |
| **MIN 3000-6000TL-X**  | 2 PV string models (3-6kW single-phase)     |
| **MIN 7000-10000TL-X** | 3 PV string models (7-10kW single-phase)    |

#### Single-Phase Hybrid (with Battery)


| Selection               | When to Use                              |
| ------------------------- | ------------------------------------------ |
| **SPH 3000-6000**       | 2 PV string storage hybrid (3-6kW)       |
| **SPH 7000-10000**      | 2 PV string storage hybrid (7-10kW)      |
| **TL-XH 3000-10000**    | 3 PV string hybrid with battery (3-10kW) |
| **TL-XH US 3000-10000** | US version 3 PV string hybrid (3-10kW)   |

#### Three-Phase


| Selection                | When to Use                          |
| -------------------------- | -------------------------------------- |
| **MID 15000-25000TL3-X** | Grid-tied 3-phase (15-25kW)          |
| **MOD 6000-15000TL3-XH** | Hybrid 3-phase with battery (6-15kW) |
| **SPH-TL3 3000-10000**   | Hybrid 3-phase with battery (3-10kW) |

### TCP Connection Settings

- **Host**: IP address of your RS485-TCP adapter (e.g., `192.168.1.100`)
- **Port**: `502` (standard Modbus TCP port)
- **Slave ID**: `1` (check inverter display if unsure)

---

## 🎯 Auto-Detection

**VPP 2.01 Inverters** (newer models) are automatically detected:
1. Integration reads Device Type Code (DTC) from register 30000
2. Identifies your exact model (e.g., "MOD 6000-15000TL3-XH")
3. Shows confirmation screen - accept or manually override
4. Protocol version displayed in device info (e.g., "Protocol 2.01")

**Legacy Inverters** (older models without V2.01 support):
1. Auto-detection fails (DTC not available)
2. Manual model selection required
3. Choose based on PV strings, phase, and battery capability
4. Legacy protocol used automatically

📖 **[Learn how auto-detection works, DTC codes, and troubleshooting →](docs/AUTODETECTION.md)**

---

## 🔧 Configuration Options

Access via **Settings** → **Devices & Services** → **Growatt Modbus** → **Configure**:


| Option                 | Default    | Range  | Description                                     |
| ------------------------ | ------------ | -------- | ------------------------------------------------- |
| **Device Name**        | "Growatt"  | -      | Friendly name (appears before all sensor names) |
| **Scan Interval**      | 30 seconds | 5-300s | How often to poll inverter                      |
| **Connection Timeout** | 10 seconds | 1-60s  | How long to wait for responses                  |
| **Invert Grid Power**  | OFF        | ON/OFF | **Reverse import/export if CT clamp backwards** |

### 🔄 Invert Grid Power

Got your CT clamp installed backwards? No problem! Just enable this option:

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

> 💡 **Tip:** 30 seconds scan interval is recommended. Faster polling provides minimal benefit and may stress the inverter.

---

## 📊 Available Sensors

### Solar Input (PV Strings)


| Entity ID                         | Name              | Unit | Description                             |
| ----------------------------------- | ------------------- | ------ | ----------------------------------------- |
| `sensor.{name}_pv1_voltage`       | PV1 Voltage       | V    | String 1 DC voltage                     |
| `sensor.{name}_pv1_current`       | PV1 Current       | A    | String 1 DC current                     |
| `sensor.{name}_pv1_power`         | PV1 Power         | W    | String 1 power output                   |
| `sensor.{name}_pv2_voltage`       | PV2 Voltage       | V    | String 2 DC voltage                     |
| `sensor.{name}_pv2_current`       | PV2 Current       | A    | String 2 DC current                     |
| `sensor.{name}_pv2_power`         | PV2 Power         | W    | String 2 power output                   |
| `sensor.{name}_pv3_voltage`       | PV3 Voltage       | V    | String 3 DC voltage (selected models)   |
| `sensor.{name}_pv3_current`       | PV3 Current       | A    | String 3 DC current (selected models)   |
| `sensor.{name}_pv3_power`         | PV3 Power         | W    | String 3 power output (selected models) |
| `sensor.{name}_solar_total_power` | Solar Total Power | W    | Combined PV power                       |

### AC Output (Single-Phase Models)


| Entity ID                    | Name         | Unit | Description       |
| ------------------------------ | -------------- | ------ | ------------------- |
| `sensor.{name}_ac_voltage`   | AC Voltage   | V    | Grid voltage      |
| `sensor.{name}_ac_current`   | AC Current   | A    | AC output current |
| `sensor.{name}_ac_power`     | AC Power     | W    | AC output power   |
| `sensor.{name}_ac_frequency` | AC Frequency | Hz   | Grid frequency    |

### AC Output (Three-Phase Models)


| Entity ID                      | Name               | Unit | Description         |
| -------------------------------- | -------------------- | ------ | --------------------- |
| `sensor.{name}_ac_voltage_r`   | AC Voltage Phase R | V    | Phase R voltage     |
| `sensor.{name}_ac_voltage_s`   | AC Voltage Phase S | V    | Phase S voltage     |
| `sensor.{name}_ac_voltage_t`   | AC Voltage Phase T | V    | Phase T voltage     |
| `sensor.{name}_ac_current_r`   | AC Current Phase R | A    | Phase R current     |
| `sensor.{name}_ac_current_s`   | AC Current Phase S | A    | Phase S current     |
| `sensor.{name}_ac_current_t`   | AC Current Phase T | A    | Phase T current     |
| `sensor.{name}_ac_power_r`     | AC Power Phase R   | W    | Phase R power       |
| `sensor.{name}_ac_power_s`     | AC Power Phase S   | W    | Phase S power       |
| `sensor.{name}_ac_power_t`     | AC Power Phase T   | W    | Phase T power       |
| `sensor.{name}_ac_power_total` | AC Total Power     | W    | Total 3-phase power |
| `sensor.{name}_ac_frequency`   | AC Frequency       | Hz   | Grid frequency      |

### Power Flow - Calculated (Grid-Tied Models)


| Entity ID                         | Name              | Unit | Description                               |
| ----------------------------------- | ------------------- | ------ | ------------------------------------------- |
| `sensor.{name}_grid_power`        | Grid Power        | W    | **Signed** grid power (+export / -import) |
| `sensor.{name}_grid_export_power` | Grid Export Power | W    | Power sent to grid (positive only)        |
| `sensor.{name}_grid_import_power` | Grid Import Power | W    | Power drawn from grid (positive only)     |
| `sensor.{name}_self_consumption`  | Self Consumption  | W    | Solar power used directly                 |
| `sensor.{name}_house_consumption` | House Consumption | W    | Total house load                          |

> 🔄 **Affected by "Invert Grid Power" option** - Enable if values are backwards!

**Grid Power Signs:**

- **Positive** (+1500W) = Exporting to grid
- **Negative** (-1200W) = Importing from grid
- **Zero** (0W) = No grid interaction (perfect self-consumption)

### Power Flow - From Registers (Hybrid Models)


| Entity ID                     | Name          | Unit | Description                   |
| ------------------------------- | --------------- | ------ | ------------------------------- |
| `sensor.{name}_power_to_grid` | Power to Grid | W    | Export power (from registers) |
| `sensor.{name}_power_to_load` | Power to Load | W    | Power to house load           |
| `sensor.{name}_power_to_user` | Power to User | W    | Forward power                 |

### Battery (Hybrid Models Only)


| Entity ID                       | Name                | Unit | Description                               |
| --------------------------------- | --------------------- | ------ | ------------------------------------------- |
| `sensor.{name}_battery_voltage` | Battery Voltage     | V    | Battery pack voltage                      |
| `sensor.{name}_battery_current` | Battery Current     | A    | Battery charge/discharge current          |
| `sensor.{name}_battery_power`   | Battery Power       | W    | Battery power (+ charging, - discharging) |
| `sensor.{name}_battery_soc`     | Battery SOC         | %    | State of charge                           |
| `sensor.{name}_battery_temp`    | Battery Temperature | °C  | Battery temperature                       |

### Energy


| Entity ID                            | Name                 | Unit | Description          |
| -------------------------------------- | ---------------------- | ------ | ---------------------- |
| `sensor.{name}_energy_today`         | Energy Today         | kWh  | Today's production   |
| `sensor.{name}_energy_total`         | Energy Total         | kWh  | Lifetime production  |
| `sensor.{name}_energy_to_grid_today` | Energy to Grid Today | kWh  | Today's export       |
| `sensor.{name}_energy_to_grid_total` | Energy to Grid Total | kWh  | Lifetime export      |
| `sensor.{name}_load_energy_today`    | Load Energy Today    | kWh  | Today's consumption  |
| `sensor.{name}_load_energy_total`    | Load Energy Total    | kWh  | Lifetime consumption |

> 🔄 **Grid energy sensors affected by "Invert Grid Power" option**

### System & Diagnostics


| Entity ID                     | Name                 | Unit | Description              |
| ------------------------------- | ---------------------- | ------ | -------------------------- |
| `sensor.{name}_inverter_temp` | Inverter Temperature | °C  | Internal temperature     |
| `sensor.{name}_ipm_temp`      | IPM Temperature      | °C  | Power module temp        |
| `sensor.{name}_boost_temp`    | Boost Temperature    | °C  | Boost converter temp     |
| `sensor.{name}_status`        | Status               | -    | Operating status         |
| `sensor.{name}_derating_mode` | Derating Mode        | -    | Power reduction status   |
| `sensor.{name}_fault_code`    | Fault Code           | -    | Current fault (if any)   |
| `sensor.{name}_warning_code`  | Warning Code         | -    | Current warning (if any) |

**Status Values:**

- `Waiting` - Waiting for sufficient PV power or grid
- `Normal` - Operating normally
- `Fault` - Fault condition detected

---

## 📈 Energy Dashboard Integration

Sensors are automatically configured for the Energy Dashboard:

1. Go to **Settings** → **Dashboards** → **Energy**
2. Click **Add Consumption** or **Add Solar Production**

### Recommended Configuration

**Solar Production:**

```
sensor.{name}_solar_total_power
```

**Grid Export:**

```
sensor.{name}_grid_export_power
```

**Grid Import:**

```
sensor.{name}_grid_import_power
```

**Home Consumption:**

```
sensor.{name}_house_consumption
```

**Battery Charge (Hybrid models):**

```
sensor.{name}_battery_power  (when positive)
```

**Battery Discharge (Hybrid models):**

```
sensor.{name}_battery_power  (when negative)
```

> 💡 **Tip:** If your grid values are backwards, enable **Invert Grid Power** in the integration options!

---

## 🌙 Night-Time Behavior

When the inverter powers down (no sun), the integration handles it gracefully:

- ✅ Sensors remain **available** (not "unavailable")
- ✅ Last known values retained (typically 0W)
- ✅ `last_successful_update` attribute shows when data was last fresh
- ✅ Logs show DEBUG messages instead of errors
- ✅ Resumes automatically when sun returns

This prevents sensor unavailability cascades in your automations and dashboards!

---

## 🐛 Troubleshooting

### Connection Issues

**TCP Connection:**

```bash
# Test if adapter is reachable
ping 192.168.1.100

# Check if Modbus port is open (Linux/Mac)
telnet 192.168.1.100 502
```

### Common Problems

#### "Failed to connect to inverter"

- ✅ Check wiring (A and B may need swapping)
- ✅ Verify IP address and port
- ✅ Confirm inverter Modbus address (usually 1)
- ✅ Ensure baud rate is 9600
- ✅ Check if inverter has power (try during daytime)
- ✅ Verify network connectivity to TCP adapter

#### Grid power values are backwards

- ✅ Enable **Invert Grid Power** option
- ✅ Go to integration Configure menu
- ✅ Toggle the option ON
- ✅ Wait for next update (within scan interval)

#### Wrong inverter series selected

- ✅ Delete the integration
- ✅ Re-add and select correct series
- ✅ Sensor names may change based on capabilities

#### Power values look wrong

- ✅ Compare readings with inverter display
- ✅ Check sensor attributes for calculation method
- ✅ Verify correct inverter series selected
- ✅ Enable DEBUG logging and check logs

#### Sensors show "Unavailable"

- ✅ Check if this is during night time (expected if first-time setup)
- ✅ Wait for sunrise and inverter to power on
- ✅ Check logs for connection errors
- ✅ Verify TCP network connection

### Enable Debug Logging

Add to `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.growatt_modbus: debug
```

---

## 📁 File Structure

```
custom_components/growatt_modbus/
├── __init__.py              # Integration setup
├── binary_sensor.py         # Binary sensors (inverter connectivity)
├── config_flow.py           # Configuration UI with inverter series selection
├── const.py                 # Register definitions for all models (V1.39)
├── coordinator.py           # Data coordinator with device identification
├── device_profiles.py       # Inverter profile definitions
├── diagnostic.py            # Universal register scanner service
├── growatt_modbus.py        # Modbus communication (pymodbus 2.x & 3.x)
├── manifest.json            # Integration metadata
├── sensor.py                # Sensor platform with model-specific sensors
├── services.yaml            # Service definitions
├── strings.json             # UI translations
├── translations/
│   └── en.json              # English translations
└── profiles/
    ├── mic.py               # MIC series register maps
    ├── min.py               # MIN series register maps
    ├── mid.py               # MID series register maps
    ├── mod.py               # MOD series register maps
    ├── sph.py               # SPH series register maps
    ├── sph_tl3.py           # SPH-TL3 series register maps
    └── tl_xh.py             # TL-XH series register maps
```

### Device Information

The integration automatically reads and displays:

- **Serial Number** - Unique inverter identifier
- **Firmware Version** - Software version running on inverter
- **Model Name** - Auto-detected exact model (e.g., "MIN-10000TL-X" instead of "MIN Series 7-10kW")

View in **Settings** → **Devices & Services** → **Growatt Modbus** → Click your inverter device

---

## 🆕 What's New in v0.0.6

- **📱 Bug Fixes**
  - Fix MIC sensors not being created.
  - Fix SPH TL3 auto detection failing
  - Fix SPH TL3 3-phase voltages not being created

## 🆕 What's New in v0.0.5

- **📱 Added model support** - Added profile for MIC micro inverter

## 🆕 What's New in v0.0.4

### 🎯 Major Improvements

- **🔍 Universal Register Scanner** - One-click diagnostic tool that:

  - Auto-scans all register ranges (no need to pick series)
  - Auto-detects inverter model with confidence rating
  - Exports complete CSV with detection analysis
  - Replaces old `run_diagnostic` and `scan_registers` services
- **📱 Device Identification** - Automatically reads and displays:

  - Serial number (from registers 23-27 or 3000-3015)
  - Firmware version (from registers 9-11)
  - Smart model names (parses inverter type register to show "MIN-10000TL-X" instead of "MIN Series")
- **🔧 SPH Profile Split** - Fixed SPH series detection:

  - Split into **SPH 3-6kW**, **SPH 7-10kW**, and **SPH-TL3 3-10kW**
  - Resolved "Unknown register map 'SPH_3000_10000'" errors
  - Proper 3-phase detection for SPH TL3 models
- **🏠 Residential Focus** - Removed commercial/industrial models:

  - Deleted MAX (50-150kW), MAC (30-50kW), MIX (legacy), WIT (commercial), SPA (uncommon)
  - Cleaner UI with only relevant residential options (3-25kW range)
  - Faster auto-detection with fewer patterns
- **🔤 Alphabetically Sorted** - Device model dropdown now in alphabetical order
- **🎯 Better Pattern Matching** - Checks longest patterns first to avoid "SPH10000TL3" → "SPH10000" mismatches

### 🐛 Bug Fixes

- Fixed device_info property to use stored register_map_key correctly
- Improved pattern matching in auto-detection (longest first)
- Resolved INVERTER_PROFILES vs REGISTER_MAPS confusion in coordinator

### 📝 Files Changed

- `coordinator.py` - Device identification, improved device_info
- `device_profiles.py` - SPH split, removed commercial models, alphabetical sort
- `auto_detection.py` - Better pattern matching, removed commercial patterns
- `diagnostic.py` - Universal scanner replaces old services
- `services.yaml` - Universal scanner service only
- `strings.json` - Updated model options, removed commercial
- `profiles/` - Removed mac.py, mix.py, wit.py, spa.py

---

## 🔧 Built-In Diagnostic Service

Test your connection using the built-in **Universal Register Scanner**:

1. **Install** the integration files (don't need to configure yet)
2. **Restart** Home Assistant
3. Go to **Developer Tools** → **Services**
4. Search for **"Growatt Modbus: Universal Register Scanner"**
5. Fill in connection details:
   - Host: `192.168.1.100`
   - Port: `502`
   - Slave ID: `1`
6. Click **"Call Service"**
7. Check notification for auto-detected model!
8. Download CSV from `/config/growatt_register_scan_YYYYMMDD_HHMMSS.csv`

**What the scanner does:**

- Scans all register ranges automatically (0-124, 125-249, 1000-1124, 3000-3249)
- Auto-detects your inverter model (MIN, SPH, MOD, etc.)
- Shows confidence rating (High/Medium/Low)
- Provides reasoning for detection
- Exports full register dump to CSV with detection analysis

**No need to:**

- Pick your inverter series in advance
- Run multiple scans for different models
- Use terminal/command line tools

---

## 🤝 Contributing

Contributions welcome! Here's how:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Test thoroughly with real hardware
4. Commit changes (`git commit -m 'Add amazing feature'`)
5. Push to branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

### Testing Checklist

- ✅ Tested with actual Growatt hardware
- ✅ Verified TCP connection
- ✅ Checked night-time behavior (inverter offline)
- ✅ Confirmed Energy Dashboard integration
- ✅ Validated all sensors appear correctly for your model
- ✅ Tested options configuration changes
- ✅ Reviewed logs for errors/warnings
- ✅ Ran Universal Scanner and confirmed detection

### Help Us Test More Models! 🧪

We need community members with different inverter models to validate the untested profiles. Currently only **MIN 7000-10000TL-X** is tested with real hardware!

**Profiles needing validation:**

- MIN 3-6kW (single-phase grid-tied)
- All SPH models (3-6kW, 7-10kW single-phase hybrid)
- SPH-TL3 (3-phase hybrid)
- TL-XH & TL-XH US (hybrid with battery)
- MID 15-25kW (3-phase grid-tied)
- MOD 6-15kW (3-phase hybrid)

If you successfully test any of these, please report back via GitHub Issues with:

- Model name from inverter display
- Universal Scanner detection results
- Screenshot of working sensors

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Based on [Growatt Modbus RTU Protocol V1.39](https://shop.frankensolar.ca/content/documentation/Growatt/AppNote_Growatt_WIT-Modbus-RTU-Protocol-II-V1.39-English-20240416_%28frankensolar%29.pdf) (2024.04.16)
- Built for the Home Assistant community
- Tested by solar enthusiasts worldwide 🌍
- Special thanks to all hardware testers and contributors
- MIN-10000TL-X validation by [@0xAHA](https://github.com/0xAHA)

---

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/0xAHA/Growatt_ModbusTCP/issues)
- **Discussions:** [GitHub Discussions](https://github.com/0xAHA/Growatt_ModbusTCP/discussions)
- **Home Assistant Community:** [Community Forum](https://community.home-assistant.io/)

---

**Made with ☀️ and ☕ by [@0xAHA](https://github.com/0xAHA)**

*Turning photons into data, one Modbus packet at a time!* ⚡
