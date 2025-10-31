# Growatt Modbus Integration for Home Assistant ☀️

![HACS Badge](https://img.shields.io/badge/HACS-Custom-orange.svg)
![Version](https://img.shields.io/badge/Version-0.0.4b2-blue.svg)
[![GitHub Issues](https://img.shields.io/github/issues/0xAHA/Growatt_ModbusTCP.svg)](https://github.com/0xAHA/Growatt_ModbusTCP/issues)
[![GitHub Stars](https://img.shields.io/github/stars/0xAHA/Growatt_ModbusTCP.svg?style=social)](https://github.com/0xAHA/Growatt_ModbusTCP)

A native Home Assistant integration for Growatt solar inverters using direct Modbus RTU/TCP communication. Get real-time data straight from your inverter without relying on cloud services! 🚀

Based on the official **[Growatt Modbus RTU Protocol V1.39](https://shop.frankensolar.ca/content/documentation/Growatt/AppNote_Growatt_WIT-Modbus-RTU-Protocol-II-V1.39-English-20240416_%28frankensolar%29.pdf)** (2024.04.16) documentation.

---

## ✨ Features

- 📊 **Real-time monitoring** - Direct Modbus communication with your inverter
- 🌙 **Night-time friendly** - Sensors stay available when inverter is offline (no sun)
- ⚡ **Smart power flow** - Automatic calculation of export, import, and self-consumption
- 🔌 **TCP connection** - WiFi/Ethernet adapters for reliable communication
- 📈 **Energy dashboard ready** - Automatic integration with HA Energy Dashboard
- 🎯 **Official registers** - Uses verified Growatt protocol documentation
- 🌡️ **Complete diagnostics** - Temperatures, fault codes, derating status
- 💾 **No cloud dependency** - Local polling, your data stays yours
- 🔄 **Grid power inversion** - Fix backwards CT clamp installations with one click
- 🎛️ **Multi-model support** - 14 profiles covering MIN, MID, MAX, SPH, MOD, TL-XH, MAC, MIX, SPA, and WIT series

---

## 🔌 Supported Inverter Models

The integration supports **14 different Growatt inverter profiles** with dedicated register maps:

### Single-Phase Grid-Tied Inverters


| Inverter Series        | Model Range    | PV Strings | Tested        | Notes             |
| ------------------------ | ---------------- | ------------ | --------------- | ------------------- |
| **MIN 3000-6000TL-X**  | 3000-6000TL-X  | 2          | ⚠️ Untested | Grid-tied, 3-6kW  |
| **MIN 7000-10000TL-X** | 7000-10000TL-X | 3          | ✅**Tested**  | Grid-tied, 7-10kW |

### Single-Phase Hybrid Inverters (with Battery)


| Inverter Series         | Model Range         | PV Strings | Tested        | Notes                            |
| ------------------------- | --------------------- | ------------ | --------------- | ---------------------------------- |
| **TL-XH 3000-10000**    | TL-XH 3000-10000    | 3          | ⚠️ Untested | Hybrid with battery, 3-10kW      |
| **TL-XH US 3000-10000** | TL-XH US 3000-10000 | 3          | ⚠️ Untested | US version hybrid, 3-10kW        |
| **SPH 3000-10000**      | SPH 3000-10000      | 2          | ⚠️ Untested | Storage hybrid, 3-10kW           |
| **MIX Series**          | Various             | 2          | ⚠️ Untested | Legacy storage (merged into SPH) |
| **SPA Series**          | Various             | -          | ⚠️ Untested | AC-coupled storage               |

### Three-Phase Grid-Tied Inverters


| Inverter Series           | Model Range           | PV Strings | Tested        | Notes                       |
| --------------------------- | ----------------------- | ------------ | --------------- | ----------------------------- |
| **MID 15000-25000TL3-X**  | 15000-25000TL3-X      | 2          | ⚠️ Untested | Commercial, 15-25kW         |
| **MAC 20000-40000TL3-X**  | MAC 20000-40000TL3-X  | 2          | ⚠️ Untested | Compact commercial, 20-40kW |
| **MAX 50000-125000TL3-X** | MAX 50000-125000TL3-X | 3          | ⚠️ Untested | Industrial, 50-125kW        |
| **MAX 1500V Series**      | MAX 1500V             | 3+         | ⚠️ Untested | High-voltage, up to 150kW   |
| **MAX-X LV Series**       | MAX-X LV              | 3+         | ⚠️ Untested | Low-voltage, up to 125kW    |

### Three-Phase Hybrid Inverters (with Battery)


| Inverter Series          | Model Range          | PV Strings | Tested        | Notes                        |
| -------------------------- | ---------------------- | ------------ | --------------- | ------------------------------ |
| **MOD 6000-15000TL3-XH** | MOD 6000-15000TL3-XH | 3          | ⚠️ Untested | Modular hybrid, 6-15kW       |
| **WIT TL3 Series**       | WIT TL3              | 3+         | ⚠️ Untested | Business storage, up to 50kW |

**Legend:**

- ✅ **Tested** - Confirmed working with real hardware
- ⚠️ **Untested** - Profile created from official documentation, needs validation

> 💡 **Help us test!** If you have a model marked as untested and can confirm it works, please open an issue or PR to update the documentation!

---

## 📊 Sensor Availability by Model

Different inverter models create different sensors based on their capabilities:


| Sensor                          | MIN 3-6k | MIN 7-10k | TL-XH | MID/MAC | MAX | SPH | MOD/WIT |
| --------------------------------- | :--------: | :---------: | :-----: | :-------: | :---: | :---: | :-------: |
| **Solar Input**                 |          |          |      |        |    |    |        |
| PV1 Voltage/Current/Power       |    ✅    |    ✅    |  ✅  |   ✅   | ✅ | ✅ |   ✅   |
| PV2 Voltage/Current/Power       |    ✅    |    ✅    |  ✅  |   ✅   | ✅ | ✅ |   ✅   |
| PV3 Voltage/Current/Power       |    ❌    |    ✅    |  ✅  |   ❌   | ✅ | ❌ |   ✅   |
| Solar Total Power               |    ✅    |    ✅    |  ✅  |   ✅   | ✅ | ✅ |   ✅   |
| **AC Output (Single-Phase)**    |          |          |      |        |    |    |        |
| AC Voltage/Current/Power        |    ✅    |    ✅    |  ✅  |   ❌   | ❌ | ✅ |   ❌   |
| AC Frequency                    |    ✅    |    ✅    |  ✅  |   ❌   | ❌ | ✅ |   ❌   |
| **AC Output (Three-Phase)**     |          |          |      |        |    |    |        |
| AC Phase R/S/T Voltage          |    ❌    |    ❌    |  ❌  |   ✅   | ✅ | ❌ |   ✅   |
| AC Phase R/S/T Current          |    ❌    |    ❌    |  ❌  |   ✅   | ✅ | ❌ |   ✅   |
| AC Phase R/S/T Power            |    ❌    |    ❌    |  ❌  |   ✅   | ✅ | ❌ |   ✅   |
| AC Total Power                  |    ❌    |    ❌    |  ❌  |   ✅   | ✅ | ❌ |   ✅   |
| **Grid Power (Calculated)**     |          |          |      |        |    |    |        |
| Grid Export Power               |    ✅    |    ✅    |  ✅  |   ✅   | ✅ | ✅ |   ✅   |
| Grid Import Power               |    ✅    |    ✅    |  ✅  |   ✅   | ✅ | ✅ |   ✅   |
| Self Consumption                |    ✅    |    ✅    |  ✅  |   ✅   | ✅ | ✅ |   ✅   |
| House Consumption               |    ✅    |    ✅    |  ✅  |   ✅   | ✅ | ✅ |   ✅   |
| **Grid Power (From Registers)** |          |          |      |        |    |    |        |
| Power to Grid                   |    ❌    |    ❌    |  ✅  |   ❌   | ❌ | ✅ |   ✅   |
| Power to Load                   |    ❌    |    ❌    |  ✅  |   ❌   | ❌ | ✅ |   ✅   |
| Power to User                   |    ❌    |    ❌    |  ✅  |   ❌   | ❌ | ✅ |   ✅   |
| **Battery (Hybrid Only)**       |          |          |      |        |    |    |        |
| Battery Voltage/Current/Power   |    ❌    |    ❌    |  ✅  |   ❌   | ❌ | ✅ |   ✅   |
| Battery SOC                     |    ❌    |    ❌    |  ✅  |   ❌   | ❌ | ✅ |   ✅   |
| Battery Temperature             |    ❌    |    ❌    |  ✅  |   ❌   | ❌ | ✅ |   ✅   |
| **Energy Totals**               |          |          |      |        |    |    |        |
| Energy Today/Total              |    ✅    |    ✅    |  ✅  |   ✅   | ✅ | ✅ |   ✅   |
| Energy to Grid Today/Total      |    ✅    |    ✅    |  ✅  |   ✅   | ✅ | ✅ |   ✅   |
| Load Energy Today/Total         |    ✅    |    ✅    |  ✅  |   ✅   | ✅ | ✅ |   ✅   |
| **System & Diagnostics**        |          |          |      |        |    |    |        |
| Inverter Temperature            |    ✅    |    ✅    |  ✅  |   ✅   | ✅ | ✅ |   ✅   |
| IPM Temperature                 |    ✅    |    ✅    |  ✅  |   ✅   | ✅ | ✅ |   ✅   |
| Boost Temperature               |    ✅    |    ✅    |  ✅  |   ✅   | ✅ | ✅ |   ✅   |
| Status/Derating/Faults          |    ✅    |    ✅    |  ✅  |   ✅   | ✅ | ✅ |   ✅   |

**Legend:**

- ✅ Available for this model
- ❌ Not available (hardware limitation)

> 📝 **Note:** Hybrid models (TL-XH, SPH, MOD, WIT) have power flow measured directly from registers. Grid-tied models (MIN, MID, MAC, MAX) calculate power flow from solar production vs AC output.

---

## 🛠️ Hardware Setup

### Inverter Connection

Growatt inverters have a **SYS/COM port** on the bottom. It is likely that your inverter install ran a small cable only connecting the 2 pins to the smart meter. There should be space to put another cable through the gland to connect the RS485 adapter. You need to connect to **pins 3 & 4**. Conveniently, the terminals are just small screw terminals so no special tool/pins are required.

### Connection Hardware

Use an RS485-to-TCP/WiFi adapter:


| Adapter                    | Connection                 | Settings                        |
| ---------------------------- | ---------------------------- | --------------------------------- |
| **EW11**                   | RS485 A/B to adapter D+/D- | TCP Server, 9600 baud, port 502 |
| **USR-W630**               | RS485 A/B to adapter A/B   | Modbus TCP Gateway mode         |
| **USR-TCP232-410s**        | RS485 A/B to adapter A/B   | TCP Server, 9600 baud, port 502 |
| **Waveshare RS485-to-ETH** | RS485 A/B to adapter A/B   | Modbus TCP mode, 9600 baud      |

**Wiring:**

```
Growatt COM Pin 3 (A) ──────► Adapter RS485-A (or D+)
Growatt COM Pin 4 (B) ──────► Adapter RS485-B (or D-)
```

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
3. Select your **Inverter Series** from the dropdown
4. Enter your TCP connection details

### Inverter Series Selection

Choose the profile that matches your inverter model:

#### Single-Phase Grid-Tied


| Selection              | When to Use                              |
| ------------------------ | ------------------------------------------ |
| **MIN 3000-6000TL-X**  | 2 PV string models (3-6kW single-phase)  |
| **MIN 7000-10000TL-X** | 3 PV string models (7-10kW single-phase) |

#### Single-Phase Hybrid (with Battery)


| Selection               | When to Use                              |
| ------------------------- | ------------------------------------------ |
| **TL-XH 3000-10000**    | 3 PV string hybrid with battery (3-10kW) |
| **TL-XH US 3000-10000** | US version 3 PV string hybrid (3-10kW)   |
| **SPH 3000-10000**      | 2 PV string storage hybrid (3-10kW)      |
| **MIX Series**          | Legacy storage system                    |
| **SPA Series**          | AC-coupled storage system                |

#### Three-Phase Grid-Tied


| Selection                 | When to Use                           |
| --------------------------- | --------------------------------------- |
| **MID 15000-25000TL3-X**  | Commercial 3-phase (15-25kW)          |
| **MAC 20000-40000TL3-X**  | Compact commercial 3-phase (20-40kW)  |
| **MAX 50000-125000TL3-X** | Industrial 3-phase (50-125kW)         |
| **MAX 1500V Series**      | High-voltage commercial (up to 150kW) |
| **MAX-X LV Series**       | Low-voltage commercial (up to 125kW)  |

#### Three-Phase Hybrid (with Battery)


| Selection                | When to Use                           |
| -------------------------- | --------------------------------------- |
| **MOD 6000-15000TL3-XH** | Modular 3-phase hybrid (6-15kW)       |
| **WIT TL3 Series**       | Business storage 3-phase (up to 50kW) |

### TCP Connection Settings

- **Host**: IP address of your RS485-TCP adapter (e.g., `192.168.1.100`)
- **Port**: `502` (standard Modbus TCP port)
- **Slave ID**: `1` (check inverter display if unsure)

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

**Attributes:**

- `firmware_version` - Inverter firmware
- `serial_number` - Inverter serial number
- `last_successful_update` - Last time inverter responded

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

**Attributes:**

- `solar_production` - Current solar generation
- `grid_export` - Power exported to grid
- `house_load` - Current house consumption
- `self_consumption_percentage` - % of solar self-consumed

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
├── const.py                 # Register definitions for all 14 models (V1.39)
├── coordinator.py           # Data coordinator with night-time handling
├── device_profiles.py       # Inverter profile definitions
├── growatt_modbus.py        # Modbus communication (pymodbus 2.x & 3.x)
├── manifest.json            # Integration metadata
├── sensor.py                # Sensor platform with model-specific sensors
├── strings.json             # UI translations
└── translations/
    └── en.json              # English translations
```

### Device Information

All device metadata (firmware version, serial number, inverter series) is available in the **Device Info** section of the integration rather than as sensor attributes. This keeps sensor entities clean and follows Home Assistant best practices.

To view device information:

1. Go to **Settings** → **Devices & Services** → **Growatt Modbus**
2. Click on your inverter device
3. View firmware, serial number, and other metadata in the device info card

---

## 🆕 What's New in v0.0.3

- 🎛️ **Expanded Model Support** - Now supports 14 inverter profiles (up from 6)
- 🔋 **Fixed SPH Register Map** - SPH models now include complete PV, AC, and battery sensors
- ⚡ **New Hybrid Series** - Added TL-XH, TL-XH US profiles for single-phase hybrid inverters
- 🏭 **More Commercial Models** - Added MAC, MAX 1500V, MAX-X LV, WIT TL3 series
- 💾 **Legacy Storage** - Added MIX and SPA series profiles
- 📊 **Profile-Based Sensors** - Optimized sensor creation based on inverter capabilities
- 🐛 **Bug Fixes** - Resolved config flow loading issues and type hint errors

### v0.0.2 Features (Previously Released)

- 🔄 **Invert Grid Power Option** - Fix backwards CT clamp installations via UI toggle
- 📊 **Model-Specific Sensors** - Only relevant sensors created based on inverter capabilities
- ⚡ **Three-Phase Support** - Full support for MID, MAX, and MOD models
- 🎨 **Enhanced Configuration UI** - Better inverter series selection with descriptions

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

### 🔧 Built-In Diagnostic Service

**NEW!** Test your connection using our built-in service - no Terminal needed!

1. **Install** the integration files (don't need to configure yet)
2. **Restart** Home Assistant
3. Go to **Developer Tools** → **Services**
4. Search for **"Growatt Modbus: Run Diagnostic Test"**
5. Fill in your connection details
6. Click **"Call Service"**
7. Check the notification for results!

See [DIAGNOSTIC_SERVICE.md](DIAGNOSTIC_SERVICE.md) for full instructions.

**Alternatively:** Use our [standalone Python script](DIAGNOSTIC_TOOL.md) if you prefer command-line testing.

### Help Us Test More Models! 🧪

We need community members with different inverter models to validate the untested profiles. Currently only **MIN 7000-10000TL-X** is tested with real hardware!

**Profiles needing validation:**

- All single-phase grid-tied (MIN 3-6k)
- All hybrid models (TL-XH, SPH, MIX, SPA)
- All three-phase models (MID, MAC, MAX variants, MOD, WIT)

If you successfully test any of these, please report back via GitHub Issues!

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Based on [Growatt Modbus RTU Protocol V1.39](https://shop.frankensolar.ca/content/documentation/Growatt/AppNote_Growatt_WIT-Modbus-RTU-Protocol-II-V1.39-English-20240416_%28frankensolar%29.pdf) (2024.04.16)
- Built for the Home Assistant community
- Tested by solar enthusiasts worldwide (soon, hopefully) 🌍
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
