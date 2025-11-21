#!/usr/bin/env python3
"""
Growatt Inverter Emulator - Web UI
Flask-based web interface for the Growatt Modbus TCP emulator.
"""

import argparse
import logging
import sys
import os
import json
import importlib.util
from flask import Flask, render_template, jsonify, request
from datetime import datetime
import threading

# Add custom_components to path for emulator imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'custom_components'))

# Import device_profiles directly without triggering package __init__.py
# This avoids the homeassistant dependency required by the HA integration
spec = importlib.util.spec_from_file_location(
    "device_profiles",
    os.path.join(os.path.dirname(__file__), 'custom_components', 'growatt_modbus', 'device_profiles.py')
)
device_profiles = importlib.util.module_from_spec(spec)
spec.loader.exec_module(device_profiles)
INVERTER_PROFILES = device_profiles.INVERTER_PROFILES

from emulator.simulator import InverterSimulator
from emulator.modbus_server import ModbusEmulatorServer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
_LOGGER = logging.getLogger(__name__)

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Global simulator and server instances
simulator = None
modbus_server = None
selected_profile = None


@app.route('/')
def index():
    """Main dashboard page."""
    if simulator is None:
        return render_template('select_model.html',
                             profiles=INVERTER_PROFILES)

    # Get the base profile (without _v201 suffix)
    base_profile_key = selected_profile.replace('_v201', '') if selected_profile else None

    if not base_profile_key or base_profile_key not in INVERTER_PROFILES:
        _LOGGER.error(f"Invalid profile key: {selected_profile} (base: {base_profile_key})")
        return render_template('select_model.html',
                             profiles=INVERTER_PROFILES)

    profile = INVERTER_PROFILES[base_profile_key]
    return render_template('dashboard.html',
                         model_name=profile['name'],
                         profile_key=base_profile_key,
                         has_battery=profile.get('has_battery', False),
                         is_three_phase=profile.get('is_three_phase', False),
                         INVERTER_PROFILES=INVERTER_PROFILES)


@app.route('/api/start', methods=['POST'])
def start_emulator():
    """Start the emulator with selected model."""
    global simulator, modbus_server, selected_profile

    data = request.json
    profile_key = data.get('profile_key')
    protocol_version = data.get('protocol_version', 'v201')  # 'v201' or 'legacy'
    port = int(data.get('port', 5020))

    if profile_key not in INVERTER_PROFILES:
        return jsonify({'error': 'Invalid profile'}), 400

    selected_profile = profile_key
    profile = INVERTER_PROFILES[profile_key]

    # Determine which register map to use
    if protocol_version == 'v201' and f"{profile_key}_v201" in INVERTER_PROFILES:
        actual_profile_key = f"{profile_key}_v201"
    else:
        # Use legacy profile
        actual_profile_key = profile_key
        if actual_profile_key.endswith('_v201'):
            # Remove _v201 suffix for legacy
            actual_profile_key = actual_profile_key.replace('_v201', '')

    try:
        # Create simulator
        simulator = InverterSimulator(actual_profile_key)

        # Start Modbus server
        modbus_server = ModbusEmulatorServer(
            simulator=simulator,
            port=port
        )
        modbus_server.start()

        _LOGGER.info(f"Started emulator: {profile['name']} on port {port}")
        _LOGGER.info(f"Protocol: {protocol_version.upper()}, Profile: {actual_profile_key}")

        return jsonify({
            'success': True,
            'model': profile['name'],
            'port': port,
            'protocol': protocol_version
        })

    except Exception as e:
        _LOGGER.error(f"Failed to start emulator: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/status')
def get_status():
    """Get current inverter status and values."""
    if simulator is None:
        return jsonify({'error': 'Emulator not started'}), 400

    state = simulator.get_state()

    # Get the base profile (without _v201 suffix)
    base_profile_key = selected_profile.replace('_v201', '') if selected_profile else None
    profile = INVERTER_PROFILES.get(base_profile_key, {})

    # Build response
    response = {
        'timestamp': datetime.now().isoformat(),
        'model': profile['name'],
        'profile_key': selected_profile,
        'status': state.get('status', 'Unknown'),
        'time': state.get('simulated_time', '00:00'),
        'time_hour': state.get('hour', 12),  # Current hour (0-24)

        # Model capabilities
        'capabilities': {
            'has_battery': profile.get('has_battery', False),
            'has_pv3': profile.get('pv3_supported', False),
            'is_three_phase': profile.get('is_three_phase', False),
            'protocol_version': 'v201' if simulator.profile_key.endswith('_v201') else 'legacy',
        },

        # Solar generation
        'solar': {
            'pv1_voltage': state.get('pv1_voltage', 0),
            'pv1_current': state.get('pv1_current', 0),
            'pv1_power': state.get('pv1_power', 0),
            'pv2_voltage': state.get('pv2_voltage', 0),
            'pv2_current': state.get('pv2_current', 0),
            'pv2_power': state.get('pv2_power', 0),
            'pv3_voltage': state.get('pv3_voltage', 0) if profile.get('pv3_supported') else None,
            'pv3_current': state.get('pv3_current', 0) if profile.get('pv3_supported') else None,
            'pv3_power': state.get('pv3_power', 0) if profile.get('pv3_supported') else None,
            'total_power': state.get('solar_power', 0),
        },

        # AC output
        'ac': {
            'voltage': state.get('ac_voltage', 0),
            'current': state.get('ac_current', 0),
            'power': state.get('ac_power', 0),
            'frequency': state.get('ac_frequency', 50.0),
        },

        # Power flow
        'grid': {
            'power': state.get('grid_power', 0),
            'export': max(0, state.get('grid_power', 0)),
            'import': max(0, -state.get('grid_power', 0)),
        },

        'load': {
            'power': state.get('house_load', 0),
        },

        # Battery (if equipped)
        'battery': None,

        # Energy totals
        'energy': {
            'today': state.get('energy_today', 0),
            'total': state.get('energy_total', 0),
            'to_grid_today': state.get('energy_to_grid_today', 0),
            'load_today': state.get('load_energy_today', 0),
        },

        # Temperatures
        'temperatures': {
            'inverter': state.get('inverter_temp', 25),
            'ipm': state.get('ipm_temp', 30),
            'boost': state.get('boost_temp', 28),
        },

        # Simulation controls
        'controls': {
            'irradiance': state.get('irradiance', 1000),
            'cloud_cover': state.get('cloud_cover', 0),
            'time_speed': state.get('time_speed', 1.0),
        }
    }

    # Add battery if equipped
    if profile.get('has_battery', False):
        response['battery'] = {
            'voltage': state.get('battery_voltage', 0),
            'current': state.get('battery_current', 0),
            'power': state.get('battery_power', 0),
            'soc': state.get('battery_soc', 0),
            'temp': state.get('battery_temp', 25),
            'charging': state.get('battery_power', 0) > 0,
        }

    return jsonify(response)


@app.route('/api/registers')
def get_registers():
    """Get key register values."""
    if simulator is None:
        return jsonify({'error': 'Emulator not started'}), 400

    # Get register map using already-loaded device_profiles module
    profile = device_profiles.get_profile(simulator.profile_key)

    if not profile:
        return jsonify({'error': 'Profile not found'}), 400

    register_map = profile.get('register_map', {})

    # Get current register values
    registers = {}

    # Sample key registers
    key_registers = [
        0,      # Status
        30000,  # DTC (if V2.01)
        30099,  # Protocol version (if V2.01)
        3000,   # Status (3000 range)
        3003,   # PV1 Voltage
        3004,   # PV1 Current
        3007,   # PV2 Voltage
        3008,   # PV2 Current
        3011,   # PV3 Voltage (if applicable)
        3026,   # AC Voltage
        3169,   # Battery Voltage (if applicable)
        3183,   # Battery SOC (if applicable)
    ]

    for addr in key_registers:
        if addr in register_map:
            reg_info = register_map[addr]
            value = simulator.get_register_value(addr)

            registers[addr] = {
                'address': addr,
                'name': reg_info.get('name', f'Register {addr}'),
                'value': value,
                'scaled_value': value * reg_info.get('scale', 1),
                'unit': reg_info.get('unit', ''),
                'description': reg_info.get('desc', ''),
                'access': reg_info.get('access', 'RO'),
            }

    return jsonify(registers)


@app.route('/api/control', methods=['POST'])
def control_simulator():
    """Update simulator controls."""
    if simulator is None:
        return jsonify({'error': 'Emulator not started'}), 400

    data = request.json

    # Update irradiance
    if 'irradiance' in data:
        irradiance = float(data['irradiance'])
        simulator.set_irradiance(max(0, min(1000, irradiance)))

    # Update cloud cover
    if 'cloud_cover' in data:
        cloud = float(data['cloud_cover'])
        simulator.set_cloud_cover(max(0, min(100, cloud)))

    # Update house load
    if 'house_load' in data:
        load = float(data['house_load'])
        simulator.set_house_load(max(0, load))

    # Update time speed
    if 'time_speed' in data:
        speed = float(data['time_speed'])
        simulator.set_time_speed(max(0.1, min(100, speed)))

    # Set time of day (0-24 hours)
    if 'time_of_day' in data:
        hour = float(data['time_of_day'])
        simulator.set_time_of_day(max(0, min(24, hour)))

    # Reset energy totals
    if data.get('reset_energy'):
        simulator.reset_energy_totals()

    return jsonify({'success': True})


@app.route('/api/switch_model', methods=['POST'])
def switch_model():
    """Switch to a different model without restarting."""
    global simulator, modbus_server, selected_profile

    if simulator is None:
        return jsonify({'error': 'Emulator not started'}), 400

    data = request.json
    profile_key = data.get('profile_key')
    protocol_version = data.get('protocol_version', 'v201')

    if profile_key not in INVERTER_PROFILES:
        return jsonify({'error': 'Invalid profile'}), 400

    try:
        # Determine which register map to use
        if protocol_version == 'v201' and f"{profile_key}_v201" in INVERTER_PROFILES:
            actual_profile_key = f"{profile_key}_v201"
        else:
            actual_profile_key = profile_key
            if actual_profile_key.endswith('_v201'):
                actual_profile_key = actual_profile_key.replace('_v201', '')

        # Stop current Modbus server
        if modbus_server:
            modbus_server.stop()
            modbus_server = None

        # Create new simulator with new profile
        selected_profile = profile_key
        simulator = InverterSimulator(actual_profile_key)

        # Restart Modbus server with same port
        port = data.get('port', 5020)
        modbus_server = ModbusEmulatorServer(
            simulator=simulator,
            port=port
        )
        modbus_server.start()

        profile = INVERTER_PROFILES[profile_key]
        _LOGGER.info(f"Switched to: {profile['name']} ({protocol_version.upper()})")

        return jsonify({
            'success': True,
            'model': profile['name'],
            'protocol': protocol_version
        })

    except Exception as e:
        _LOGGER.error(f"Failed to switch model: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/stop', methods=['POST'])
def stop_emulator():
    """Stop the emulator."""
    global simulator, modbus_server, selected_profile

    if modbus_server:
        modbus_server.stop()
        modbus_server = None

    simulator = None
    selected_profile = None

    return jsonify({'success': True})


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Growatt Inverter Emulator - Web UI'
    )
    parser.add_argument(
        '--web-port',
        type=int,
        default=5000,
        help='Web server port (default: 5000)'
    )
    parser.add_argument(
        '--host',
        default='0.0.0.0',
        help='Web server host (default: 0.0.0.0)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode'
    )

    args = parser.parse_args()

    print(f"""
╔══════════════════════════════════════════════════════════╗
║  Growatt Inverter Emulator - Web UI                     ║
╚══════════════════════════════════════════════════════════╝

🌐 Web Interface: http://localhost:{args.web_port}
📡 Modbus TCP: Configure port in web interface

Starting web server...
""")

    try:
        app.run(
            host=args.host,
            port=args.web_port,
            debug=args.debug
        )
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        if modbus_server:
            modbus_server.stop()


if __name__ == '__main__':
    main()
