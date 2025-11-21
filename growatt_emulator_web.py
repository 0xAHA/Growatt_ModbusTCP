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
import time
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
from emulator.models import InverterModel

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

    # Debug logging
    _LOGGER.info(f"Profile lookup: key={profile_key}, type={type(profile).__name__}")
    if isinstance(profile, dict):
        _LOGGER.info(f"  Profile name: {profile.get('name', 'N/A')}")
        _LOGGER.info(f"  Has battery: {profile.get('has_battery', 'N/A')}")

    # Determine which register map to use
    if protocol_version == 'v201' and f"{profile_key}_v201" in INVERTER_PROFILES:
        actual_profile_key = f"{profile_key}_v201"
    else:
        # Use legacy profile
        actual_profile_key = profile_key
        if actual_profile_key.endswith('_v201'):
            # Remove _v201 suffix for legacy
            actual_profile_key = actual_profile_key.replace('_v201', '')

    _LOGGER.info(f"Creating simulator with profile: {actual_profile_key}")

    try:
        # Create model and simulator
        model = InverterModel(actual_profile_key)
        simulator = InverterSimulator(model, port=port)
        _LOGGER.info("Simulator created successfully")

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

    # Get values from simulator
    vals = simulator.values
    sim_time = simulator.get_simulation_time()

    # Get the base profile (without _v201 suffix)
    base_profile_key = selected_profile.replace('_v201', '') if selected_profile else None
    profile = INVERTER_PROFILES.get(base_profile_key, {})

    # Build response
    response = {
        'timestamp': datetime.now().isoformat(),
        'model': profile.get('name', 'Unknown'),
        'profile_key': selected_profile,
        'status': vals.get('status', 0),
        'time': sim_time.strftime('%H:%M'),
        'time_hour': sim_time.hour + sim_time.minute / 60.0,

        # Model capabilities
        'capabilities': {
            'has_battery': profile.get('has_battery', False),
            'has_pv3': profile.get('pv3_supported', False),
            'is_three_phase': profile.get('is_three_phase', False),
            'protocol_version': 'v201' if simulator.model.profile_key.endswith('_v201') else 'legacy',
        },

        # Solar generation
        'solar': {
            'pv1_voltage': vals['voltages'].get('pv1', 0),
            'pv1_current': vals['currents'].get('pv1', 0),
            'pv1_power': vals['pv_power'].get('pv1', 0),
            'pv2_voltage': vals['voltages'].get('pv2', 0),
            'pv2_current': vals['currents'].get('pv2', 0),
            'pv2_power': vals['pv_power'].get('pv2', 0),
            'pv3_voltage': vals['voltages'].get('pv3', 0) if profile.get('pv3_supported') else None,
            'pv3_current': vals['currents'].get('pv3', 0) if profile.get('pv3_supported') else None,
            'pv3_power': vals['pv_power'].get('pv3', 0) if profile.get('pv3_supported') else None,
            'total_power': vals['pv_power'].get('total', 0),
        },

        # AC output
        'ac': {
            'voltage': vals['voltages'].get('ac', 0),
            'current': vals['currents'].get('ac', 0),
            'power': vals.get('ac_power', 0),
            'frequency': 50.0,
        },

        # Power flow
        'grid': {
            'power': vals.get('grid_power', 0),
            'export': max(0, vals.get('grid_power', 0)),
            'import': max(0, -vals.get('grid_power', 0)),
        },

        'load': {
            'power': simulator.house_load,
        },

        # Battery (if equipped)
        'battery': None,

        # Energy totals
        'energy': {
            'today': simulator.energy_today,
            'total': simulator.energy_total,
            'to_grid_today': simulator.energy_to_grid_today,
            'load_today': simulator.load_energy_today,
        },

        # Temperatures
        'temperatures': {
            'inverter': vals['temperatures'].get('inverter', 25),
            'ipm': vals['temperatures'].get('ipm', 30),
            'boost': vals['temperatures'].get('boost', 28),
        },

        # Simulation controls
        'controls': {
            'irradiance': simulator.solar_irradiance,
            'cloud_cover': simulator.cloud_cover * 100,  # Convert to percentage
            'time_speed': simulator.time_multiplier,
        }
    }

    # Add battery if equipped
    if profile.get('has_battery', False):
        response['battery'] = {
            'voltage': vals['voltages'].get('battery', 0),
            'current': vals['currents'].get('battery', 0),
            'power': vals.get('battery_power', 0),
            'soc': simulator.battery_soc,
            'temp': 30.0,
            'charging': vals.get('battery_power', 0) > 0,
        }

    return jsonify(response)


@app.route('/api/registers')
def get_registers():
    """Get key register values."""
    if simulator is None:
        return jsonify({'error': 'Emulator not started'}), 400

    # Get input registers from model
    input_registers = simulator.model.get_input_registers()

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
        if addr in input_registers:
            reg_info = input_registers[addr]
            value = simulator.get_register_value('input', addr)

            if value is not None:
                registers[addr] = {
                    'address': addr,
                    'name': reg_info.get('name', f'Register {addr}'),
                    'value': value,
                    'scaled_value': value * reg_info.get('scale', 1),
                    'unit': reg_info.get('unit', ''),
                    'description': reg_info.get('desc', ''),
                    'access': 'RO',
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

    # Update cloud cover (convert from percentage to 0-1)
    if 'cloud_cover' in data:
        cloud = float(data['cloud_cover']) / 100.0
        simulator.set_cloud_cover(max(0, min(1, cloud)))

    # Update house load
    if 'house_load' in data:
        load = float(data['house_load'])
        simulator.set_house_load(max(0, load))

    # Update time speed
    if 'time_speed' in data:
        speed = float(data['time_speed'])
        simulator.set_time_multiplier(max(0.1, min(100, speed)))

    # Set time of day (0-24 hours)
    if 'time_of_day' in data:
        hour = float(data['time_of_day'])
        # Set the simulation_time to the specified hour
        new_time = datetime.now().replace(
            hour=int(hour),
            minute=int((hour % 1) * 60),
            second=0,
            microsecond=0
        )
        simulator.simulation_time = new_time
        simulator.start_time = time.time()  # Reset start time

    # Reset energy totals (if method exists)
    if data.get('reset_energy') and hasattr(simulator, 'reset_energy_totals'):
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

        # Get port
        port = data.get('port', 5020)

        # Create new model and simulator with new profile
        selected_profile = profile_key
        model = InverterModel(actual_profile_key)
        simulator = InverterSimulator(model, port=port)

        # Restart Modbus server with same port
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
