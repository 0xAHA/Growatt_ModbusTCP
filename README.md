# Growatt Modbus Integration for Home Assistant ☀️

![HACS Badge](https://img.shields.io/badge/HACS-Custom-orange.svg)
![Version](https://img.shields.io/badge/Version-0.1.9-blue.svg)
[![GitHub Issues](https://img.shields.io/github/issues/0xAHA/Growatt_ModbusTCP.svg)](https://github.com/0xAHA/Growatt_ModbusTCP/issues)
[![GitHub Stars](https://img.shields.io/github/stars/0xAHA/Growatt_ModbusTCP.svg?style=social)](https://github.com/0xAHA/Growatt_ModbusTCP)

A native Home Assistant integration for Growatt solar inverters using direct Modbus RTU/TCP communication. Get real-time data straight from your inverter without relying on cloud services! 🚀

**Protocol Support:**

- **Primary:** Growatt VPP Protocol V2.01 with automatic model detection via Device Type Code (DTC)
- **Fallback:** Legacy protocols (V1.39, V3.05) with manual model selection for older inverters
- **Smart Detection:** Automatically uses best available protocol based on inverter capabilities

---

## 🌱 Early Adopter Notice - Help Us Grow!

> **This integration is actively evolving with your help!**
>
> We're building something great together, and your real-world testing is invaluable. This integration supports many Growatt inverter models, but some profiles are based on official documentation and haven't been verified with actual hardware yet.
>
> **How You Can Help:**
>
> - ✅ **Test and report** - Try the integration with your inverter and let us know how it works
> - 📊 **Share register scans** - Use the built-in Universal Scanner to help us verify or improve profiles
> - 🐛 **Report issues** - Found incorrect values or missing sensors? [Open an issue](https://github.com/0xAHA/Growatt_ModbusTCP/issues) with your inverter model
> - 💡 **Share feedback** - Your experience helps us prioritize features and fixes
> - ⭐ **Star the repo** - Show support and help others discover this integration
>
> **Current Status:**
> - Core functionality is stable and tested on multiple inverter models
> - New features and profiles added regularly based on community feedback
> - Active development with responsive issue resolution
>
> Together we're building the most comprehensive local Growatt integration for Home Assistant. Thank you for being part of this journey! 🙏

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
**Single-Phase Hybrid:** SPH 3-6kW, SPH 7-10kW, TL-XH 3-10kW, TL-XH US 3-10kW, MIN TL-XH 3-10kW ✅
**Single-Phase Off-Grid:** SPF 3-6kW ES PLUS ✅
**Three-Phase Hybrid:** MID 15-25kW, MOD 6-15kW, SPH-TL3 3-10kW, WIT 4-15kW ✅

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

The integration uses a **4-step auto-detection** process:

**VPP 2.01 Inverters** (newer models):

1. Reads Device Type Code (DTC) from register 30000
2. Identifies exact model (e.g., "MOD 6000-15000TL3-XH")
3. Shows confirmation screen - accept or manually override
4. Protocol version displayed as "Protocol 2.01"

**Legacy Inverters** (older models without V2.01):

1. DTC not available → tries model name detection
2. Model name not available → probes register ranges
3. **Register probing identifies most legacy inverters automatically!**
4. Only requires manual selection if all detection methods fail (rare)
5. Protocol version displayed as "Protocol Legacy"

**Detection Success Rate:**

- ✅ V2.01 inverters: ~100% (DTC code)
- ✅ Legacy inverters: ~90% (register probing)
- ⚠️ Manual selection: ~10% (unusual/old models)

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

### 🔄 Grid Power Sign Convention & Inversion

#### Understanding Grid Power Signs

Your Growatt inverter and Home Assistant use **different sign conventions** for grid power:


| Convention             | Export (to grid) | Import (from grid) | Used By                                              |
| ------------------------ | ------------------ | -------------------- | ------------------------------------------------------ |
| **IEC 61850 Standard** | ✅ Positive (+)  | ⛔ Negative (-)    | Growatt inverters, industrial systems, energy meters |
| **Home Assistant**     | ⛔ Negative (-)  | ✅ Positive (+)    | HA Power Flow visualization                          |

**Why the difference?**

- **IEC 61850** measures current flow direction at grid connection (export = current flowing TO grid = positive)
- **Home Assistant** uses consumer perspective (import = power coming FROM grid = positive, like "spending money")

**Example:**

- You're generating 6 kW solar, consuming 1 kW, exporting 5 kW
- **Inverter reports:** `grid_power = +5000 W` (positive = export, IEC standard ✓)
- **HA expects:** `grid_power = -5000 W` (negative = export, for visualization)

This is why the **Invert Grid Power** setting exists!

#### ✨ Automatic Detection During Setup

**NEW!** The integration now **automatically detects** the correct grid orientation during initial setup:

- When you add the integration, it reads current power flow
- If solar is producing (> 1000 W) and exporting (> 100 W), it automatically detects your inverter's convention
- The correct setting is applied automatically - no manual configuration needed!
- Detection result is logged: check Home Assistant logs for confirmation

**What you'll see in logs:**

```
✅ Auto-detected: IEC 61850 standard (exporting 5000W shows as positive) - inversion enabled
```

or

```
⚠️ Solar production too low (200W) - using default (no inversion). Run detection service later.
```

**If setup happens at night or indoors:**

- Detection can't run (no solar production)
- Default setting is used (no inversion)
- Use the manual detection service below once solar is producing

#### Manual Detection Service 🎯

**Already installed?** Use the detection service to verify or update your configuration:

```yaml
service: growatt_modbus.detect_grid_orientation
```

**Requirements:**

- Solar must be producing > 1000 W
- Must be exporting > 100 W to grid
- Run during daytime with good sun

The service will:

1. Analyze your current power flow
2. Detect which convention your inverter uses
3. Compare with your current setting
4. Recommend whether to enable/disable inversion
5. Display results as a persistent notification

#### Manual Configuration

**When to enable Invert Grid Power:**

✅ **Enable if:** Your inverter follows IEC 61850 (most Growatt inverters do)

- Grid power shows **positive** when exporting
- Power Flow graph shows incorrect direction
- Consumption calculation is wrong (too high/too low)

❌ **Disable if:** Your readings are already in HA format

- Grid power shows **negative** when exporting
- Power Flow graph is correct
- Or if the auto-detection recommends it

**How to configure:**

1. Go to **Settings** → **Devices & Services**
2. Find **Growatt Modbus** → **Configure**
3. Toggle **Invert Grid Power** based on auto-detection result
4. **Save** and reload the integration

**What it affects:**

- ✅ `sensor.grid_power` (signed W)
- ✅ `sensor.grid_export_power` (unsigned W)
- ✅ `sensor.grid_import_power` (unsigned W)
- ✅ Home Assistant Power Flow visualization
- ✅ Consumption calculation accuracy
- ❌ Does NOT affect energy totals (`_total` sensors) - they're always correct

> 💡 **Note:** This setting is for visualization compatibility, not because anything is "wrong" with your inverter. Most Growatt inverters correctly follow the IEC 61850 industrial standard, while Home Assistant uses a consumer-friendly convention for its UI.

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

## 🆕 What's New in v0.1.9

**Register Read Service & USB/Serial Diagnostics:**

**✨ New Features:**

- **Register Read Service** - Profile-aware register inspector for debugging and validation

  - New `growatt_modbus.read_register` service for instant register inspection
  - **Automatic paired register detection** - reads and combines 32-bit values automatically
  - Shows raw value, profile info (name, scale, unit), and computed values
  - Displays current entity value from Home Assistant for comparison
  - **Use Cases:**
    - Validate profile mappings during development
    - Troubleshoot incorrect sensor values
    - Verify scale factors and signed interpretations
    - Inspect any register without full scans
  - **Example:** Read battery power register (31201) to see raw value, paired register (31200), 32-bit combination, scale (×0.1), and final computed value (523.4 W)
  - Works with any configured device (TCP or Serial) - no connection re-entry needed

- **USB/Serial Support & Auto-Detection for Register Scanner**

  - `export_register_dump` service now supports USB RS485 adapters
  - **Auto-detects coordinator** by matching connection parameters (no device selection needed!)
  - **Entity values automatically included** when scanning a configured device
  - Removed confusing sub-device selector (Inverter/Solar/Grid/Load/Battery)
  - Select connection type: TCP (Ethernet) or Serial (USB)
  - Example: Scan `192.168.1.60:502` automatically includes entity values if you have a device configured at that address

**🔧 Enhancements:**

- Register read service provides detailed output in persistent notifications
- Automatic handling of signed/unsigned interpretations
- Paired register calculations shown step-by-step for transparency
- Service UI includes register type selector (Input/Holding)
- Cleaner, more intuitive register scanner UI

**Developer Tools → Services:**
```yaml
# Read any register
service: growatt_modbus.read_register
data:
  device_id: <select_your_device>
  register: 3  # e.g., PV1 voltage
  register_type: input

# Register scan via USB
service: growatt_modbus.export_register_dump
data:
  connection_type: serial
  device: "/dev/ttyUSB0"
  baudrate: 9600
  slave_id: 1
```

---

<details>
<summary>📋 Previous Release: v0.1.1</summary>

## 🆕 What's New in v0.1.1

**WIT Battery Sensors & Control Device Organization (Issue #75):**

**✨ New Features:**

- **WIT Profile Battery Sensors** - Complete VPP battery monitoring suite

  - **NEW:** VPP battery power registers (31200-31205)
    - Battery Power (signed: positive=charge, negative=discharge)
    - Charge Power & Discharge Power (unsigned separate values)
    - More accurate readings from dedicated hardware registers vs V×I calculation
  - **NEW:** Battery energy tracking (31206-31213)
    - Charge Energy Today / Total
    - Discharge Energy Today / Total
  - **NEW:** VPP battery state registers for redundancy
  - **Result:** WIT users now get **full battery monitoring suite** instead of just 4 basic sensors
  - **Fixes:** GitHub Issue #75 - WIT showing minimal battery sensors
- **Control Entity Device Organization**

  - Controls now appear under their **logical device** instead of separate Controls device
  - Battery controls → Battery device (Configuration section)
  - Grid controls → Grid device (Configuration section)
  - Solar controls → Solar device (Configuration section)
  - System controls → Inverter device (Configuration section)
  - All controls have EntityCategory.CONFIG (hidden by default, expand Configuration to view)
  - **NEW:** Active Power Rate control (register 3) - limits max inverter output 0-100%
    - Available on: MIN series, and other profiles with register 3
    - Appears in Inverter device Configuration section

**🔧 Enhancements:**

- Added device mapping infrastructure for future control entity auto-generation
- Control entities automatically assigned to correct device based on function
- Tested and validated on MIN-10000TL-X hardware

</details>

---

<details>
<summary>📋 Previous Release: v0.1.0</summary>

## 🆕 What's New in v0.1.0

**Multi-Device Architecture & Automatic Grid Orientation Detection:**

**✨ New Features:**

- **Multi-Device Organization** - Sensors now organized into logical devices

  - **Inverter** (parent) - System health, status, temperatures, connectivity
  - **Solar** - PV inputs, AC output, energy production
  - **Grid** - Grid connection, import/export, grid energy
  - **Load** - Consumption monitoring
  - **Battery** (conditional) - Battery storage metrics
  - Entities categorized as Main/Diagnostic/Config for cleaner UI
  - **Automatic migration** from single device - no manual action needed!
  - Entity IDs preserved - dashboards and automations continue working
- **Automatic Grid Orientation Detection** - Eliminates manual configuration

  - **Auto-detection during setup** - Correct setting applied automatically when adding integration
  - **Detection service** - `growatt_modbus.detect_grid_orientation` for verification anytime
  - Analyzes power flow to determine if inverter follows IEC 61850 or HA convention
  - Works with just 100W export (previously 500W) - much more practical
  - Shows persistent notification with detection results and applied setting
  - Comprehensive README documentation explaining IEC vs HA sign conventions
- **Stale Daily Totals Debouncing** - Fixes morning energy spikes

  - Detects when inverter wakes up with yesterday's totals in volatile memory
  - 15-minute debounce window filters stale readings
  - Prevents false spikes in energy dashboards
- **Default Options on Setup** - Proper defaults from first installation

  - 60-second scan interval set automatically
  - No need to manually configure polling rate

**🐛 Bug Fixes:**

- **Fixed Grid Export/Import Sensors** - Critical fix when inversion enabled

  - Export sensor now correctly shows `max(0, -grid_power)` after inversion
  - Import sensor now correctly shows `max(0, grid_power)` after inversion
  - Previously showed swapped values when "Invert Grid Power" was ON
- **Fixed Grid Import Energy Calculation** - Critical fix for all inverters with inversion enabled

  - Import energy now correctly calculated for inverters without hardware import registers
  - Affects: MIN, MOD, SPH-TL3, TL-XH, WIT profiles
  - Previously showed incorrect import energy when "Invert Grid Power" was ON
  - Import energy now always calculated as: `Load - Solar + Export`
  - Example: Load 11.8 kWh - Solar 34.1 kWh + Export 25.4 kWh = Import 3.1 kWh ✅
  - Previously incorrectly showed import = export (25.4 kWh = 25.4 kWh) ❌
- **Fixed Battery Discharge Power Sign Convention** - Critical fix for TL-XH/SPH VPP 2.01 profiles

  - Register 31200-31201 now correctly marked as **signed** battery power
  - Per VPP Protocol V2.01 spec: positive=charge, negative=discharge
  - Previously misinterpreted as unsigned, causing discharge to show as huge positive values
  - Affects all TL-XH, SPH, SPH-TL3 users with VPP 2.01 inverters
  - **NEW:** Added legacy battery power registers (3178-3181) for TL-XH models
    - `battery_discharge_power` - Unsigned discharge power (always positive)
    - `battery_charge_power` - Unsigned charge power (always positive)
    - `battery_power` - Signed VPP power (negative=discharge, positive=charge)
    - Users can disable entities they don't need
- **Enhanced WIT Battery Sensors** - Added complete VPP battery power and energy registers

  - **NEW:** VPP battery power registers (31200-31205)
    - `battery_power` - Signed power (positive=charge, negative=discharge)
    - `charge_power` and `discharge_power` - Unsigned power values
    - Battery power now read from dedicated registers instead of V×I calculation
  - **NEW:** Battery energy tracking (31206-31213)
    - `charge_energy_today` / `charge_energy_total`
    - `discharge_energy_today` / `discharge_energy_total`
  - **NEW:** VPP battery state registers for redundancy
    - Voltage, current, SOC, temperature from VPP range
  - WIT users now get full battery monitoring suite instead of just 4 basic sensors
  - More accurate power measurements from hardware registers vs calculated values

**⚠️ Breaking Changes:**

**IMPORTANT:** After updating, **verify your grid power settings:**

1. Run the detection service during daytime with solar producing:

   ```yaml
   service: growatt_modbus.detect_grid_orientation
   ```
2. The service will analyze your setup and recommend whether to enable/disable "Invert Grid Power"
3. If recommendation differs from current setting, update it:

   - Go to **Settings** → **Devices & Services** → **Growatt Modbus** → **Configure**
   - Toggle **Invert Grid Power** based on recommendation
   - Save and reload integration

**Why this is needed:**

- Previous versions had a bug in export/import sensors when inversion was enabled
- The bug is now fixed, but you should verify your current setting is correct
- Auto-detection makes this easy - just run the service!

**Entity IDs unchanged** - Your dashboards and automations continue working

</details>

---

<details>
<summary>📋 Previous Release: v0.0.8</summary>

## 🆕 What's New in v0.0.8

**MIN TL-XH Support & Modbus Write Service:**

**✨ New Features:**

- **MIN TL-XH Hybrid Detection** - Added support for MIN 6000 TL-XH inverters with unique register layout

  - Created `MIN_TL_XH_3000_10000_V201` profile combining MIN 3000+ range with VPP 31200+ battery registers
  - Enhanced DTC 5100 detection to differentiate MIN variant from standard TL-XH
  - Fixes missing sensors: `power_to_user`, `power_to_load`, `load_energy`, grid energy breakdown, and battery data
  - Users with MIN TL-XH now get complete sensor coverage without manual intervention
- **Modbus Write Service** - Advanced inverter control via Home Assistant services

  - New `growatt_modbus.write_register` service for writing to holding registers
  - Exposes existing write functionality for user automations and scripts
  - Allows control of on/off, power limits, export limits, and other writable parameters
  - Full device selector integration for Developer Tools and automations
  - Auto-refresh UI after successful writes
- **USB RS485 Adapter Support**

  - Now supports using a USB RS485/Modbus adapter, and not just Modbus TCP

**🐛 Bug Fixes:**

- **Fixed Options Flow** - Resolved `AttributeError` and `TypeError` when accessing integration options
  - Fixed compatibility with newer Home Assistant versions
  - Options flow now loads correctly for all users

**Breaking Changes:** None - Fully backward compatible with existing setups

</details>

---

<details>
<summary>📋 Previous Release: v0.0.7</summary>

## 🆕 What's New in v0.0.7

**MOD Series Enhancements & Bug Fixes:**

**🐛 Bug Fixes:**

- **Fixed MOD export control** - Export limit mode and power controls (registers 122-123) now work correctly on MOD units
  - Root cause: Coordinator wasn't reading holding registers 122-123
  - Added `export_limit_mode` and `export_limit_power` fields to data model
  - Number and Select entities now properly populate and function

**✨ Enhancements:**

- **New MOD-6000-15000TL3-X Profile** - Added dedicated grid-tied MOD profile (no battery)

  - Distinguishes MOD-XH (hybrid with battery) from MOD-X (grid-tied)
  - Only creates appropriate entities based on hardware (no battery sensors on grid-tied units)
  - Includes export control registers (122-123) for both variants
- **Enhanced Auto-Detection** - Automatically differentiates MOD variants:

  - **DTC** detection for WIT 4-15K models
  - **DTC 5400** detection now checks battery SOC (31217) or voltage (3169) with non-zero value
  - Battery present → MOD-XH hybrid (`mod_6000_15000tl3_xh_v201`)
  - 3000 range but no battery → MOD-X grid-tied (`mod_6000_15000tl3_x`)
  - 0-124 range only → MID series (`mid_15000_25000tl3_x_v201`)
  - Updated register probing and scan-based detection with same logic
- **Expanded VPP Register Scanning** - Universal scanner now covers full VPP Protocol V2.01 range:

  - 31000-31099: Equipment status, PV data, fault words
  - 31100-31199: AC output, meter/grid power (31112/31113), load power (31118/31119), energy, temperatures
  - 31200-31299: Battery cluster 1 data
  - 31300-31399: Battery cluster 2 data (optional)

**Breaking Changes:** None - Fully backward compatible with existing setups

---

<details>
<summary>📋 Previous Release: v0.0.7-beta3</summary>

**VPP Protocol V2.01 Support** - Major update adding support for Growatt's advanced VPP Protocol V2.01:

- **🎯 Auto-Detection via DTC Codes** - Automatic model identification using Device Type Code (register 30000) for V2.01 inverters
- **📡 Dual Protocol Support** - V2.01 profiles include both advanced (30000+, 31000+) and legacy registers for maximum compatibility
- **🔍 4-Step Detection** - DTC code → Model name → Register probing → Manual selection (only if all fail)
- **📊 Protocol Version Display** - Shows "Protocol 2.01" or "Protocol Legacy" in device info (from register 30099)
- **⚙️ Legacy Register Probing** - ~90% of legacy inverters still auto-detected using register range probing
- **📖 Comprehensive Documentation** - New detailed guides for auto-detection, model specs, and sensor availability
- **🔧 Improved Config Flow** - Shows auto-detection results when manual selection is required

**Official DTC Codes Implemented:**

- SPH series: 3502, 3601, 3725, 3735
- MIN/TL-XH/MIC series: 5100, 5200, 5201
- MOD/MID series: 5400
- Commercial series: 5601, 5800

**Breaking Changes:** None - Fully backward compatible with existing setups

</details>

📖 **Full changelog:** See [GitHub Releases](https://github.com/0xAHA/Growatt_ModbusTCP/releases)

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

- Scans all register ranges automatically:
  - Legacy ranges: 0-124, 125-249, 1000-1124, 3000-3249
  - VPP V2.01 ranges: 31000-31099, 31100-31199, 31200-31299, 31300-31399
- Auto-detects your inverter model (MIN, SPH, MOD-XH, MOD-X, MID, etc.)
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
- MOD TL-XH validation by [@JoelSimmo](https://github.com/JoelSimmo)
- WIT 4-15K support added by [@jekmanis](https://github.com/jekmanishttps://)

---

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/0xAHA/Growatt_ModbusTCP/issues)
- **Discussions:** [GitHub Discussions](https://github.com/0xAHA/Growatt_ModbusTCP/discussions)
- **Home Assistant Community:** [Community Forum](https://community.home-assistant.io/)

---

**Made with ☀️ and ☕ by [@0xAHA](https://github.com/0xAHA)**

*Turning photons into data, one Modbus packet at a time!* ⚡
