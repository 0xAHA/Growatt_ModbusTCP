# Growatt Inverter Emulator

A realistic Modbus TCP emulator for testing Growatt inverter integrations without physical hardware.

## Features

- **10 Inverter Models** - Supports all major Growatt series (MIC, MIN, TL-XH, MID, SPH, SPH-TL3, MOD)
- **VPP Protocol V2.01** - Full support for V2.01 register ranges (30000+, 31000+) with DTC codes
- **Legacy Protocol Support** - Also supports V1.39 and V3.05 register ranges for older models
- **Auto-Detection Ready** - Serves official DTC codes (Device Type Code) for automatic model identification
- **Realistic Simulation** - Day/night cycles, solar generation, battery charging/discharging
- **Live Terminal UI** - Real-time display of all inverter parameters including protocol info
- **Interactive Controls** - Adjust solar irradiance, cloud cover, house load, battery behavior, and time speed
- **Full Modbus TCP** - Implements complete register maps for each model
- **Battery Simulation** - Automatic charging from PV excess, discharging to cover loads
- **Grid Interaction** - Calculates import/export based on generation and consumption

## Installation

### Requirements

- Python 3.7 or higher
- pip package manager

### Install Dependencies

```bash
pip3 install -r requirements_emulator.txt
```

Or manually:

```bash
pip3 install pymodbus rich flask
```

## Usage

The emulator supports two interfaces: **Terminal UI** (command-line) and **Web UI** (browser-based).

### Web UI (Recommended)

Run the web-based interface for a visual dashboard with energy flow diagram:

```bash
python3 growatt_emulator_web.py
```

Then open your browser to: **http://localhost:5000**

Features:
- 🌐 Browser-based interface (no terminal needed)
- 📊 Live energy flow diagram (like Home Assistant's energy dashboard)
- 🎛️ Interactive sliders for simulation controls
- 📝 Real-time register display
- 📈 Live sensor values and graphs
- 🔄 Auto-refresh (1 second updates)

**Custom web port:**
```bash
python3 growatt_emulator_web.py --web-port 8080
```

### Terminal UI (Classic)

Run the emulator with interactive terminal UI:

```bash
python3 growatt_emulator.py
```

### Specify Model and Port

```bash
python3 growatt_emulator.py --model sph_3000_6000 --port 5020
```

### List Available Models

```bash
python3 growatt_emulator.py --list-models
```

### Available Models

When running interactively, you can choose between **V2.01** (with DTC auto-detection) or **Legacy** protocol for each model.

| Model Key | Name | Type | Battery | Phases | PV Strings | Power | DTC Code |
|-----------|------|------|---------|--------|------------|-------|----------|
| `mic_600_3300tl_x` | MIC 600-3300TL-X | Micro | No | 1 | 1 | 3.3kW | 5200* |
| `min_3000_6000_tl_x` | MIN 3000-6000TL-X | String | No | 1 | 2 | 6.0kW | 5200* |
| `min_7000_10000_tl_x` | MIN 7000-10000TL-X | String | No | 1 | 3 | 10.0kW | 5201 |
| `tl_xh_3000_10000` | TL-XH 3000-10000 | Hybrid | Yes | 1 | 3 | 10.0kW | 5100 |
| `tl_xh_us_3000_10000` | TL-XH US 3000-10000 | Hybrid (US) | Yes | 1 | 3 | 10.0kW | 5100 |
| `mid_15000_25000tl3_x` | MID 15000-25000TL3-X | Commercial | No | 3 | 2 | 25.0kW | 5400* |
| `sph_3000_6000` | SPH 3000-6000 | Hybrid Storage | Yes | 1 | 2 | 6.0kW | 3502* |
| `sph_7000_10000` | SPH 7000-10000 | Hybrid Storage | Yes | 1 | 2 | 10.0kW | 3502* |
| `sph_tl3_3000_10000` | SPH-TL3 3000-10000 | Hybrid 3-Phase | Yes | 3 | 2 | 10.0kW | 3601 |
| `mod_6000_15000tl3_xh` | MOD 6000-15000TL3-XH | Modular Hybrid | Yes | 3 | 3 | 15.0kW | 5400* |

**\* DTC codes marked with asterisk are shared** - Additional register checks differentiate exact model during auto-detection.

**Protocol Versions:**
- **V2.01 Mode:** Serves register 30099 with value 201 (protocol version), register 30000 with DTC code
- **Legacy Mode:** V2.01 registers not readable (simulates older inverter firmware)

## Keyboard Controls

While the emulator is running, you can use these keys:

- **[I]** - Adjust solar irradiance (0-1000 W/m²)
- **[C]** - Adjust cloud cover (0-100%)
- **[L]** - Adjust house load (Watts)
- **[T]** - Adjust time speed multiplier (0.1-100x)
- **[B]** - Battery control (Auto/Manual charge/discharge) - Only for models with battery
- **[R]** - Reset daily energy totals
- **[Q]** - Quit emulator

## Display Panels

The terminal UI shows:

1. **Header** - Model name, time, status, port, protocol version
2. **Protocol Info** - DTC code (register 30000), Protocol version (register 30099)
3. **PV Generation** - Voltage, current, and power for each string
4. **AC Output** - Voltage, current, frequency, power
5. **Battery** (if equipped) - SOC, voltage, current, charging status
6. **Grid & Load** - Import/export status, house consumption
7. **Energy Totals** - Today and lifetime energy statistics
8. **Temperatures** - Inverter, IPM, and boost converter temps

**Protocol Info Display:**
- **V2.01 Mode:** Shows "DTC: 5201 | Protocol: 2.01"
- **Legacy Mode:** Shows "DTC: Not Available | Protocol: Legacy"

## Connecting to the Emulator

### From Home Assistant

Add a Modbus TCP integration pointing to:
- Host: `localhost` (or IP of machine running emulator)
- Port: `502` (or custom port specified)

### From Python

```python
from pymodbus.client import ModbusTcpClient

client = ModbusTcpClient('localhost', port=502)
client.connect()

# Read input registers (e.g., PV1 voltage at register 3)
result = client.read_input_registers(3, 1, slave=1)
if not result.isError():
    pv1_voltage = result.registers[0] * 0.1  # Apply scale
    print(f"PV1 Voltage: {pv1_voltage}V")

client.close()
```

## Simulation Details

### Solar Generation

- Follows realistic day/night cycle (sunrise ~6:00, sunset ~18:00)
- Peak generation at solar noon (~13:00)
- Affected by:
  - Time of day (sine wave sun elevation)
  - Solar irradiance setting (0-1000 W/m²)
  - Cloud cover (0-100%)
  - Random variations to simulate real conditions

### Battery Behavior

For models with batteries:

- **Auto Mode** (default):
  - Charges from excess PV generation
  - Discharges to cover shortfall when PV < load
  - Stops charging above 95% SOC
  - Stops discharging below 10% SOC
  - Trickle charge/discharge near limits

- **Manual Mode**:
  - Force specific charge/discharge rate
  - Override automatic behavior for testing

### Grid Interaction

- **Export**: When PV generation exceeds house load
- **Import**: When PV generation cannot meet house load
- Properly accounts for battery charging/discharging

### Temperature Simulation

- Ambient: 25°C
- Rises with inverter load (up to +30°C at full power)
- IPM runs ~5°C hotter than inverter
- Boost converter ~3°C hotter than inverter

## Port Selection

- **Port 502** (default Modbus): Requires sudo/root on Linux
- **Port >= 1024**: No special privileges required

Example with custom port:
```bash
python3 growatt_emulator.py --model sph_3000_6000 --port 5020
```

## Testing Your Integration

1. Start the emulator with your target model (choose V2.01 or Legacy when prompted)
2. Connect your integration (Home Assistant, script, etc.)
3. **Test Auto-Detection (V2.01 Mode):**
   - Run Universal Register Scanner service
   - Verify DTC code is read correctly from register 30000
   - Confirm protocol version shows "2.01" from register 30099
   - Check that model is auto-detected with "HIGH" confidence
   - Verify integration setup doesn't require manual selection
4. **Test Legacy Mode:**
   - Restart emulator and select Legacy protocol
   - Verify DTC register (30000) returns error/not readable
   - Confirm manual model selection is required during setup
   - Check that protocol version shows "Legacy" in device info
5. Use keyboard controls to simulate different conditions:
   - High sun: `[I]` → 1000 W/m²
   - Cloudy day: `[C]` → 70%
   - Heavy load: `[L]` → 5000W
   - Fast time: `[T]` → 10x (see full day in minutes)
6. Verify your integration correctly:
   - Reads all sensor values
   - Handles zero values at night
   - Processes battery data (if applicable)
   - Calculates derived values correctly
   - Updates energy totals

## Troubleshooting

### Permission Denied on Port 502

Use a higher port or run with sudo:
```bash
sudo python3 growatt_emulator.py --model sph_3000_6000
# OR
python3 growatt_emulator.py --model sph_3000_6000 --port 5020
```

### Module Not Found Errors

Install dependencies:
```bash
pip3 install pymodbus rich
```

### Terminal Display Issues

The emulator uses the `rich` library for terminal UI. Ensure your terminal supports:
- ANSI colors
- Unicode characters
- Terminal size at least 80x24

## Architecture

```
emulator/
├── __init__.py         - Package initialization
├── models.py           - Inverter model definitions
├── simulator.py        - Simulation engine (solar, battery, grid)
├── modbus_server.py    - Modbus TCP server
├── display.py          - Terminal UI with rich
└── controls.py         - Keyboard input handler

growatt_emulator.py     - Main entry point
```

## Development

### Adding New Models

1. Add profile to `custom_components/growatt_modbus/device_profiles.py`
2. Add register map to appropriate profile file in `custom_components/growatt_modbus/profiles/`
3. Emulator will automatically detect and support the new model

### Extending Simulation

Edit `emulator/simulator.py` to:
- Add new calculated values
- Modify generation curves
- Implement different battery algorithms
- Add weather effects

## License

This emulator is part of the Growatt ModbusTCP integration project.
See the main LICENSE file for details.
