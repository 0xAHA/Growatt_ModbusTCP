#!/usr/bin/env python3
"""
Growatt Inverter Web Emulator

A web-based interface for the Growatt Modbus TCP emulator.
Provides a Home Assistant-inspired dashboard with energy flow visualization
and interactive controls.

Usage:
    python3 growatt_emulator_web.py [--port PORT] [--webport WEBPORT] [--model MODEL]

Examples:
    python3 growatt_emulator_web.py
    python3 growatt_emulator_web.py --port 5020 --webport 8080
    python3 growatt_emulator_web.py --model sph_3000_6000 --port 502 --webport 8080
"""

import sys
import os
import argparse
import logging
import json
import threading
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import models (safe - doesn't require pymodbus thanks to lazy imports in __init__.py)
from emulator.models import InverterModel, get_available_models, INVERTER_PROFILES

# These will be lazy-loaded when needed
InverterSimulator = None
ModbusEmulatorServer = None

def lazy_import_emulator_components():
    """Lazy import components that require pymodbus.

    This function is only called when actually starting an emulator,
    at which point pymodbus and other dependencies should be installed.
    """
    global InverterSimulator, ModbusEmulatorServer
    if InverterSimulator is None:
        try:
            from emulator.simulator import InverterSimulator as _InverterSimulator
            from emulator.modbus_server import ModbusEmulatorServer as _ModbusEmulatorServer

            InverterSimulator = _InverterSimulator
            ModbusEmulatorServer = _ModbusEmulatorServer

        except ImportError as e:
            raise ImportError(
                f"Failed to import emulator components: {e}\n\n"
                "Please install required dependencies:\n"
                "  pip install pymodbus>=3.0.0 rich>=13.0.0"
            )

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)
CORS(app)

# Global emulator instance
emulator = None
emulator_lock = threading.Lock()


def get_series_from_name(name: str) -> str:
    """Derive series from model name."""
    name_upper = name.upper()
    if 'MIC' in name_upper:
        return 'MIC'
    elif 'MIN' in name_upper:
        return 'MIN'
    elif 'TL-XH' in name_upper or 'TL XH' in name_upper:
        return 'TL-XH'
    elif 'MID' in name_upper:
        return 'MID'
    elif 'SPH-TL3' in name_upper or 'SPH TL3' in name_upper:
        return 'SPH-TL3'
    elif 'SPH' in name_upper:
        return 'SPH'
    elif 'MOD' in name_upper:
        return 'MOD'
    else:
        return 'Other'


class WebGrowattEmulator:
    """Web-based emulator application."""

    def __init__(self, model_key: str, port: int = 502):
        """Initialize emulator.

        Args:
            model_key: Inverter model profile key
            port: Modbus TCP port
        """
        # Lazy import components that require pymodbus
        lazy_import_emulator_components()

        self.model_key = model_key
        self.port = port
        self.running = False

        # Create components
        self.model = InverterModel(model_key)
        self.simulator = InverterSimulator(self.model, port)
        self.modbus_server = ModbusEmulatorServer(self.simulator, port)

        # Update thread
        self.update_thread = None

    def start(self) -> None:
        """Start the emulator."""
        try:
            logger.info(f"Starting Growatt Web Emulator...")
            logger.info(f"  Model: {self.model.name}")
            logger.info(f"  Port: {self.port}")
            logger.info(f"  Serial: {self.simulator.serial_number}")

            # Start Modbus server
            self.modbus_server.start()

            if not self.modbus_server.is_running():
                raise RuntimeError("Failed to start Modbus server")

            logger.info(f"✓ Modbus TCP server running on port {self.port}")

            # Start background update thread
            self.running = True
            self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
            self.update_thread.start()

            logger.info("✓ Emulator started successfully")

        except Exception as e:
            logger.error(f"Failed to start emulator: {e}")
            raise

    def _update_loop(self):
        """Background update loop."""
        import time
        while self.running:
            try:
                self.simulator.update()
                time.sleep(1.0)  # Update every second
            except Exception as e:
                logger.error(f"Update error: {e}")

    def stop(self) -> None:
        """Stop the emulator."""
        logger.info("Stopping emulator...")
        self.running = False

        if self.update_thread:
            self.update_thread.join(timeout=2.0)

        if hasattr(self, 'modbus_server'):
            self.modbus_server.stop()

        logger.info("✓ Emulator stopped")

    def get_status(self) -> dict:
        """Get current emulator status.

        Returns:
            Dictionary with all current values and state
        """
        sim = self.simulator
        sim_time = sim.get_simulation_time()

        # Get current power values
        values = sim.values

        # Build status response
        status = {
            'running': self.running,  # Top-level for easy access
            'model': {
                'key': self.model_key,
                'name': self.model.name,
                'series': get_series_from_name(self.model.name),
                'has_battery': self.model.has_battery,
                'has_pv3': self.model.has_pv3,
                'phases': self.model.phases,
                'max_power_kw': self.model.max_power_kw,
            },
            'runtime': {
                'running': self.running,
                'paused': sim.paused,
                'time': sim_time.strftime('%Y-%m-%d %H:%M:%S'),
                'time_multiplier': sim.time_multiplier,
            },
            'serial': sim.serial_number,
            'firmware': sim.firmware_version,
            'modbus': {
                'port': self.port,
                'running': self.modbus_server.is_running(),
            },
            'power': {
                'pv1': values.get('pv_power', {}).get('pv1', 0),
                'pv2': values.get('pv_power', {}).get('pv2', 0),
                'pv3': values.get('pv_power', {}).get('pv3', 0) if self.model.has_pv3 else None,
                'pv_total': values.get('pv_power', {}).get('total', 0),
                'battery': values.get('battery_power', 0) if self.model.has_battery else None,
                'grid': values.get('grid_power', {}).get('grid', 0),
                'load': sim.house_load,
                'inverter_output': values.get('ac_power', 0),
            },
            'battery': {
                'soc': sim.battery_soc if self.model.has_battery else None,
                'voltage': values.get('voltages', {}).get('battery', 0) if self.model.has_battery else None,
                'current': values.get('currents', {}).get('battery', 0) if self.model.has_battery else None,
                'temperature': values.get('temperatures', {}).get('battery', 25) if self.model.has_battery else None,
                'capacity_kwh': sim.battery_capacity_kwh if self.model.has_battery else None,
            } if self.model.has_battery else None,
            'energy': {
                'today': sim.energy_today,
                'total': sim.energy_total,
                'battery_charge_today': sim.battery_charge_today if self.model.has_battery else None,
                'battery_discharge_today': sim.battery_discharge_today if self.model.has_battery else None,
                'grid_import_today': sim.grid_import_energy_today,
                'grid_export_today': sim.energy_to_grid_today,
                'load_today': sim.load_energy_today,
            },
            'controls': {
                'solar_irradiance': sim.solar_irradiance,
                'cloud_cover': sim.cloud_cover,
                'house_load': sim.house_load,
                'battery_override': sim.battery_override,
            },
            'inverter': {
                'temperature': values.get('temperatures', {}).get('inverter', 25),
                'frequency': 50.0,  # Hardcoded like in simulator
                'grid_voltage': values.get('voltages', {}).get('ac', 240) if not self.model.is_three_phase else values.get('voltages', {}).get('ac_r', 230),
            },
        }

        return status

    def set_control(self, param: str, value: float) -> bool:
        """Set a control parameter.

        Args:
            param: Parameter name
            value: New value

        Returns:
            True if successful
        """
        sim = self.simulator

        if param == 'solar_irradiance':
            sim.solar_irradiance = max(0, min(1000, value))
        elif param == 'cloud_cover':
            sim.cloud_cover = max(0, min(1, value))
        elif param == 'house_load':
            sim.house_load = max(0, value)
        elif param == 'battery_override':
            if value == 0:
                sim.battery_override = None
            else:
                sim.battery_override = value
        elif param == 'time_multiplier':
            sim.time_multiplier = max(0.1, min(100, value))
        elif param == 'paused':
            sim.paused = bool(value)
        else:
            return False

        return True


@app.route('/')
def index():
    """Render main dashboard."""
    return render_template('select_model.html')


@app.route('/dashboard')
def dashboard():
    """Render emulator dashboard."""
    global emulator
    if not emulator:
        return "Emulator not started", 503
    return render_template('dashboard.html')


@app.route('/api/models')
def api_models():
    """Get available models."""
    try:
        models = get_available_models()
        model_list = []

        for key, model in models.items():
            # Skip V2.01 profiles for now (can add protocol selection later)
            if '_v201' in key:
                continue

            profile = INVERTER_PROFILES[key]
            series = get_series_from_name(profile['name'])

            model_list.append({
                'key': key,
                'name': profile['name'],
                'series': series,
                'has_battery': profile['has_battery'],
                'has_pv3': profile['has_pv3'],
                'phases': profile['phases'],
                'max_power_kw': profile['max_power_kw'],
            })

        # Sort by series then name
        model_list.sort(key=lambda x: (x['series'], x['name']))

        return jsonify({'models': model_list})
    except Exception as e:
        logger.error(f"Error loading models: {e}")
        return jsonify({'error': str(e), 'models': []}), 500


@app.route('/api/start', methods=['POST'])
def api_start():
    """Start emulator with selected model."""
    global emulator

    data = request.json
    model_key = data.get('model')
    port = data.get('port', 502)

    if not model_key:
        return jsonify({'error': 'Model not specified'}), 400

    # Validate model
    models = get_available_models()
    if model_key not in models:
        return jsonify({'error': f'Unknown model: {model_key}'}), 400

    # Stop existing emulator if running
    with emulator_lock:
        if emulator:
            emulator.stop()

        try:
            # Create and start new emulator
            emulator = WebGrowattEmulator(model_key, port)
            emulator.start()
            return jsonify({'success': True, 'status': emulator.get_status()})
        except Exception as e:
            logger.error(f"Failed to start emulator: {e}")
            emulator = None
            return jsonify({'error': str(e)}), 500


@app.route('/api/stop', methods=['POST'])
def api_stop():
    """Stop the emulator."""
    global emulator

    with emulator_lock:
        if emulator:
            emulator.stop()
            emulator = None
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Emulator not running'}), 400


@app.route('/api/status')
def api_status():
    """Get current emulator status."""
    global emulator

    if not emulator:
        return jsonify({'running': False}), 200

    try:
        status = emulator.get_status()
        return jsonify(status)
    except Exception as e:
        logger.error(f"Status error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/control', methods=['POST'])
def api_control():
    """Set control parameter."""
    global emulator

    if not emulator:
        return jsonify({'error': 'Emulator not running'}), 400

    data = request.json
    param = data.get('param')
    value = data.get('value')

    if not param or value is None:
        return jsonify({'error': 'Missing param or value'}), 400

    try:
        success = emulator.set_control(param, value)
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'error': f'Unknown parameter: {param}'}), 400
    except Exception as e:
        logger.error(f"Control error: {e}")
        return jsonify({'error': str(e)}), 500


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Growatt Inverter Web Emulator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        '--model',
        type=str,
        help='Pre-select inverter model (optional)'
    )

    parser.add_argument(
        '--port',
        type=int,
        default=502,
        help='Modbus TCP port (default: 502)'
    )

    parser.add_argument(
        '--webport',
        type=int,
        default=8080,
        help='Web interface port (default: 8080)'
    )

    parser.add_argument(
        '--host',
        type=str,
        default='0.0.0.0',
        help='Web interface host (default: 0.0.0.0)'
    )

    args = parser.parse_args()

    # Auto-start emulator if model specified
    if args.model:
        global emulator
        try:
            emulator = WebGrowattEmulator(args.model, args.port)
            emulator.start()
        except Exception as e:
            logger.error(f"Failed to auto-start emulator: {e}")
            sys.exit(1)

    # Start Flask web server
    print("\n" + "=" * 80)
    print(" " * 20 + "GROWATT INVERTER WEB EMULATOR")
    print("=" * 80)
    print(f"\n🌐 Web interface: http://{args.host}:{args.webport}")
    if emulator:
        print(f"📡 Modbus TCP: port {args.port}")
        print(f"🔧 Model: {emulator.model.name}")
    else:
        print(f"📡 Modbus TCP: port {args.port} (will start when model selected)")
    print("\n" + "=" * 80 + "\n")

    try:
        app.run(host=args.host, port=args.webport, debug=False)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    finally:
        if emulator:
            emulator.stop()


if __name__ == "__main__":
    main()
