#!/usr/bin/env python3
"""
Growatt Inverter Emulator

A realistic Modbus TCP emulator for testing Growatt integrations.
Simulates all inverter models with realistic solar generation, battery behavior,
and grid interaction.

Usage:
    python3 growatt_emulator.py [--port PORT] [--model MODEL]

Examples:
    python3 growatt_emulator.py
    python3 growatt_emulator.py --port 5020
    python3 growatt_emulator.py --model sph_3000_6000 --port 502
"""

import sys
import os
import argparse
import time
import logging
from typing import Optional

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from emulator.models import InverterModel, get_available_models, INVERTER_PROFILES
from emulator.simulator import InverterSimulator
from emulator.modbus_server import ModbusEmulatorServer
from emulator.display import EmulatorDisplay
from emulator.controls import ControlHandler

# Configure logging
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GrowattEmulator:
    """Main emulator application."""

    def __init__(self, model_key: str, port: int = 502):
        """Initialize emulator.

        Args:
            model_key: Inverter model profile key
            port: Modbus TCP port
        """
        self.model_key = model_key
        self.port = port
        self.running = False

        # Create components
        self.model = InverterModel(model_key)
        self.simulator = InverterSimulator(self.model, port)
        self.modbus_server = ModbusEmulatorServer(self.simulator, port)
        self.display = EmulatorDisplay(self.simulator)
        self.controls = ControlHandler(self.simulator, display=self.display, on_quit=self.stop)

    def start(self) -> None:
        """Start the emulator."""
        try:
            print(f"\n🚀 Starting Growatt Emulator...")
            print(f"   Model: {self.model.name}")
            print(f"   Port: {self.port}")
            print(f"   Serial: {self.simulator.serial_number}")
            print(f"\n⏳ Initializing Modbus server...")

            # Start Modbus server
            self.modbus_server.start()
            time.sleep(1)  # Give server time to start

            if not self.modbus_server.is_running():
                raise RuntimeError("Failed to start Modbus server")

            print(f"✓ Modbus TCP server running on port {self.port}")
            print(f"✓ Ready for connections!")
            print(f"\n Press any control key to begin...\n")

            time.sleep(2)

            # Start display and controls
            self.running = True
            self.controls.start()

            # Run live display (blocking)
            with self.display.start_live_display() as live:
                while self.running:
                    live.update(self.display.render())
                    time.sleep(1.0)  # Update every second

        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupted by user")
        except Exception as e:
            print(f"\n\n❌ Error: {e}")
            logger.exception("Emulator error")
        finally:
            self.cleanup()

    def stop(self) -> None:
        """Stop the emulator."""
        self.running = False

    def cleanup(self) -> None:
        """Clean up resources."""
        print("\n\n🛑 Shutting down...")

        if hasattr(self, 'controls'):
            self.controls.stop()

        if hasattr(self, 'display'):
            self.display.stop_live_display()

        if hasattr(self, 'modbus_server'):
            self.modbus_server.stop()

        print("✓ Emulator stopped")


def select_model_interactive() -> str:
    """Interactive model selection menu.

    Returns:
        Selected model key
    """
    models = get_available_models()
    model_list = list(models.keys())

    print("\n" + "=" * 80)
    print(" " * 25 + "GROWATT INVERTER EMULATOR")
    print("=" * 80)
    print("\nAvailable Inverter Models:\n")

    # Group by series for better display
    series_groups = {
        'MIC': [],
        'MIN': [],
        'TL-XH': [],
        'MID': [],
        'SPH': [],
        'SPH-TL3': [],
        'MOD': [],
    }

    for key in model_list:
        profile = INVERTER_PROFILES[key]
        name = profile['name']

        # Determine series
        if 'MIC' in name:
            series_groups['MIC'].append(key)
        elif 'MIN' in name:
            series_groups['MIN'].append(key)
        elif 'TL-XH' in name:
            series_groups['TL-XH'].append(key)
        elif 'MID' in name:
            series_groups['MID'].append(key)
        elif 'SPH-TL3' in name:
            series_groups['SPH-TL3'].append(key)
        elif 'SPH' in name:
            series_groups['SPH'].append(key)
        elif 'MOD' in name:
            series_groups['MOD'].append(key)

    index = 1
    key_map = {}

    for series, keys in series_groups.items():
        if not keys:
            continue

        print(f"\n  {series} Series:")
        print("  " + "-" * 70)

        for key in keys:
            profile = INVERTER_PROFILES[key]
            battery = "🔋" if profile['has_battery'] else "  "
            phase = f"{profile['phases']}P"
            pv = f"{3 if profile['has_pv3'] else 2}PV"
            power = f"{profile['max_power_kw']:4.1f}kW"

            print(f"  [{index:2}] {battery} {profile['name']:35} ({phase}, {pv}, {power})")
            key_map[index] = key
            index += 1

    print("\n" + "=" * 80)
    print("\nSelect a model by number: ", end='', flush=True)

    try:
        choice = int(input().strip())
        if choice in key_map:
            return key_map[choice]
        else:
            print(f"❌ Invalid choice: {choice}")
            sys.exit(1)
    except (ValueError, EOFError, KeyboardInterrupt):
        print("\n❌ Invalid input")
        sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Growatt Inverter Modbus TCP Emulator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Interactive model selection
  %(prog)s --model sph_3000_6000              # Specify model directly
  %(prog)s --port 5020                        # Use custom port
  %(prog)s --model min_7000_10000_tl_x --port 502

Available Models:
  mic_600_3300tl_x         - MIC Series Micro Inverter
  min_3000_6000_tl_x       - MIN Series 3-6kW (no battery)
  min_7000_10000_tl_x      - MIN Series 7-10kW (no battery)
  tl_xh_3000_10000         - TL-XH Hybrid 3-10kW (with battery)
  tl_xh_us_3000_10000      - TL-XH US Hybrid 3-10kW (with battery)
  mid_15000_25000tl3_x     - MID Series 15-25kW 3-Phase
  sph_3000_6000            - SPH Hybrid 3-6kW (with battery)
  sph_7000_10000           - SPH Hybrid 7-10kW (with battery)
  sph_tl3_3000_10000       - SPH-TL3 3-Phase Hybrid (with battery)
  mod_6000_15000tl3_xh     - MOD Modular 3-Phase Hybrid (with battery)
        """
    )

    parser.add_argument(
        '--model',
        type=str,
        help='Inverter model key (e.g., sph_3000_6000)'
    )

    parser.add_argument(
        '--port',
        type=int,
        default=502,
        help='Modbus TCP port (default: 502)'
    )

    parser.add_argument(
        '--list-models',
        action='store_true',
        help='List available models and exit'
    )

    args = parser.parse_args()

    # List models
    if args.list_models:
        from emulator.models import list_models
        list_models()
        sys.exit(0)

    # Select model
    if args.model:
        model_key = args.model
        # Validate model
        models = get_available_models()
        if model_key not in models:
            print(f"❌ Unknown model: {model_key}")
            print(f"\nUse --list-models to see available models")
            sys.exit(1)
    else:
        # Interactive selection
        model_key = select_model_interactive()

    # Check port permissions (Unix/Linux only)
    if args.port < 1024 and hasattr(os, 'geteuid') and os.geteuid() != 0:
        print(f"\n⚠️  Warning: Port {args.port} requires root privileges on Linux/Unix")
        print(f"   Consider using a port >= 1024 or running with sudo")
        print(f"\n   Example: python3 {sys.argv[0]} --model {model_key} --port 5020\n")

        response = input("Continue anyway? [y/N]: ").strip().lower()
        if response != 'y':
            sys.exit(0)
    elif args.port < 1024 and not hasattr(os, 'geteuid'):
        # Windows - just warn
        print(f"\n⚠️  Note: Using port {args.port}")
        print(f"   If you get permission errors, try a port >= 1024")
        print(f"   Example: python {sys.argv[0]} --model {model_key} --port 5020\n")

    # Create and start emulator
    try:
        emulator = GrowattEmulator(model_key, args.port)
        emulator.start()
    except PermissionError:
        print(f"\n❌ Permission denied: Cannot bind to port {args.port}")
        print(f"   Try using a port >= 1024 or run with sudo")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Failed to start emulator: {e}")
        logger.exception("Startup error")
        sys.exit(1)


if __name__ == "__main__":
    main()
