# Growatt Web Emulator

A web-based interface for the Growatt Modbus TCP emulator with Home Assistant-inspired dashboard.

## Features

- **Home Assistant-style UI**: Clean, modern interface inspired by HA's energy dashboard
- **Energy Flow Visualization**: Real-time diagram showing Solar → Battery/Grid/Home power flow
- **Protocol Selection**: Choose between V2.01 VPP protocol or Legacy protocol
- **Interactive Controls**: Adjust solar irradiance, cloud cover, house load, and time speed
- **Live Updates**: Real-time value updates every second
- **Compact Layout**: Diagram on left, controls and info tiles on right

## Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements_emulator.txt

# Or install minimal dependencies for web UI only
pip install Flask flask-cors
```

### Running the Web Emulator

```bash
# Start web interface (Flask server)
python3 growatt_emulator_web.py --webport 8080

# Or specify a default model
python3 growatt_emulator_web.py --model min_3000_6000_tl_x --port 5020 --webport 8080
```

Then open your browser to: `http://localhost:8080`

## Usage

1. **Select Model**: Choose an inverter model from the dropdown
2. **Choose Protocol** (if available): V2.01 VPP or Legacy
3. **Set Port**: Default is 502 (use 5020 or higher to avoid needing sudo)
4. **Start Emulator**: Click "Start Emulator" button
5. **Dashboard**: View real-time energy flow and control settings

### Available Models

The web emulator supports all inverter models with automatic protocol selection:

**Models with V2.01 Support:**
- MIN Series (3-6kW, 7-10kW)
- MIC Series (600-3300W)
- MID Series (15-25kW)
- SPH Series (3-6kW, 7-10kW)
- SPH-TL3 Series (3-10kW)
- TL-XH Series (3-10kW, US variants)

**Legacy Only:**
- MOD Series (6-15kW)

## Protocol Selection

### V2.01 VPP Protocol (Recommended)
- Modern protocol with DTC (Device Type Code) support
- Registers: 30000-31132 range + legacy 3000+ range
- Full VPP/smart grid functionality
- Serves BOTH legacy and new registers

### Legacy Protocol
- Traditional 3000+ register range only
- Maximum compatibility with older systems
- No DTC or VPP features

## Controls

### Solar Irradiance (0-1000 W/m²)
- **Night** (0): No solar generation
- **Dawn** (300): Low generation
- **Day** (800): Normal operation
- **Peak** (1000): Maximum output

### Cloud Cover (0-100%)
- **Clear** (0): No clouds
- **Partly** (30): Some clouds
- **Cloudy** (70): Mostly cloudy
- **Overcast** (100): Heavy clouds

### House Load (0-10000 W)
- Simulates home power consumption
- Affects grid import/export

### Time Speed (0.1x - 100x)
- Speed up time for testing
- 1x = real-time
- 60x = 1 minute per second
- 300x = 5 minutes per second

## Testing

### Test Register Loading

```bash
python3 test_emulator_registers.py
```

This verifies:
- Model loading from profiles
- Register map loading
- Simulator value generation
- Register serving via Modbus

### Test with Home Assistant

1. Start the web emulator with MIN or SPH series
2. Choose V2.01 protocol for best compatibility
3. Configure Home Assistant Growatt integration:
   - Host: `localhost` (or your IP)
   - Port: `502` (or your chosen port)
   - Model: Auto-detect or match your selection
4. Reload integration to detect emulator

## Architecture

### Components

1. **growatt_emulator_web.py**: Flask web server and API
2. **templates/select_model.html**: Model selection page
3. **templates/dashboard.html**: Dashboard with energy flow
4. **emulator/**: Core emulator package
   - `models.py`: Inverter model definitions
   - `simulator.py`: Physics simulation engine
   - `modbus_server.py`: Modbus TCP server
   - `display.py`: Terminal UI (for CLI mode)
   - `controls.py`: Keyboard controls (for CLI mode)

### API Endpoints

- `GET /`: Model selection page
- `GET /dashboard`: Dashboard page
- `GET /api/models`: List available models
- `POST /api/start`: Start emulator with model
- `POST /api/stop`: Stop running emulator
- `GET /api/status`: Get current emulator status
- `POST /api/control`: Update control parameters

### Status API Response

```json
{
  "running": true,
  "model": {
    "key": "min_3000_6000_tl_x",
    "name": "MIN Series 3000-6000TL-X",
    "series": "MIN",
    "has_battery": false,
    "phases": 1,
    "max_power_kw": 6.0
  },
  "runtime": {
    "running": true,
    "paused": false,
    "time": "2025-11-21 14:23:45",
    "time_multiplier": 1.0
  },
  "power": {
    "pv1": 2500,
    "pv2": 2500,
    "pv_total": 5000,
    "grid": 3000,
    "load": 2000,
    "battery": null
  },
  "energy": {
    "today": 12.5,
    "total": 1234.5,
    "grid_import_today": 2.3,
    "grid_export_today": 8.7,
    "load_today": 15.2
  },
  "inverter": {
    "temperature": 45,
    "frequency": 50.0,
    "grid_voltage": 240
  }
}
```

## Troubleshooting

### Models Not Loading
- Check browser console for errors
- Verify Flask server is running
- Test with: `curl http://localhost:8080/api/models`

### Emulator Won't Start
- Check if pymodbus is installed: `pip show pymodbus`
- Verify port is available: `sudo lsof -i :502`
- Try a different port (>= 1024)

### Home Assistant Can't Connect
- Ensure Modbus TCP port is accessible
- Check firewall rules
- Verify emulator is running: check web dashboard
- Use protocol that matches HA integration expectations

### Dashboard Shows Zeros
- Check browser console for JavaScript errors
- Verify emulator is updating: watch terminal logs
- Refresh the page
- Check `/api/status` endpoint directly

## Development

### Adding New Models

1. Add profile to `custom_components/growatt_modbus/device_profiles.py`
2. Create register map in `custom_components/growatt_modbus/profiles/`
3. Test with `python3 test_emulator_registers.py`
4. Restart web emulator

### Debugging

Enable debug logging in `growatt_emulator_web.py`:

```python
logging.basicConfig(level=logging.DEBUG)
```

Check browser console for JavaScript errors.

## License

Same as main project (MIT)
