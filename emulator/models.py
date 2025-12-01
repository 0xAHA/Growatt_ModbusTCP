"""
Inverter Model Definitions

Defines characteristics and capabilities for each Growatt inverter model.
"""

from typing import Dict, Any
import sys
import os
import importlib.util

# Direct import of device_profiles and const modules to avoid HA dependencies
def _import_module_from_path(module_name, file_path):
    """Import a module from a file path without importing package __init__."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

# Get base path
base_path = os.path.join(os.path.dirname(__file__), '..', 'custom_components', 'growatt_modbus')

# Import profiles module directly
profiles_init_path = os.path.join(base_path, 'profiles', '__init__.py')
profiles = _import_module_from_path('emulator._temp_profiles', profiles_init_path)
REGISTER_MAPS = profiles.REGISTER_MAPS

# Import device_profiles directly
device_profiles_path = os.path.join(base_path, 'device_profiles.py')
device_profiles = _import_module_from_path('emulator._temp_device_profiles', device_profiles_path)
INVERTER_PROFILES = device_profiles.INVERTER_PROFILES


class InverterModel:
    """Represents a specific inverter model with its capabilities."""

    def __init__(self, profile_key: str):
        """Initialize inverter model from profile.

        Args:
            profile_key: Profile key from INVERTER_PROFILES (e.g., 'sph_3000_6000')
        """
        if profile_key not in INVERTER_PROFILES:
            raise ValueError(f"Unknown profile: {profile_key}")

        self.profile_key = profile_key
        self.profile = INVERTER_PROFILES[profile_key]
        self.register_map_key = self.profile['register_map']

        if self.register_map_key not in REGISTER_MAPS:
            raise ValueError(f"Register map not found: {self.register_map_key}")

        self.register_map = REGISTER_MAPS[self.register_map_key]

        # Extract capabilities
        self.name = self.profile['name']
        self.description = self.profile['description']
        self.phases = self.profile['phases']
        self.has_pv3 = self.profile['has_pv3']
        self.has_battery = self.profile['has_battery']
        self.max_power_kw = self.profile['max_power_kw']
        self.sensors = self.profile['sensors']

        # Calculate derived properties
        self.num_pv_strings = 3 if self.has_pv3 else 2
        self.is_three_phase = self.phases == 3

    def get_input_registers(self) -> Dict[int, Dict[str, Any]]:
        """Get input register definitions."""
        return self.register_map.get('input_registers', {})

    def get_holding_registers(self) -> Dict[int, Dict[str, Any]]:
        """Get holding register definitions."""
        return self.register_map.get('holding_registers', {})

    def __str__(self) -> str:
        return f"{self.name} - {self.description}"

    def __repr__(self) -> str:
        return f"InverterModel('{self.profile_key}')"


def get_available_models() -> Dict[str, str]:
    """Get available inverter models for selection.

    Returns:
        Dict mapping profile_key to display name
    """
    return {
        key: f"{profile['name']} - {profile['description']}"
        for key, profile in INVERTER_PROFILES.items()
    }


def list_models() -> None:
    """Print available models to console."""
    models = get_available_models()
    print("\nAvailable Growatt Inverter Models:")
    print("=" * 70)
    for i, (key, description) in enumerate(models.items(), 1):
        profile = INVERTER_PROFILES[key]
        battery = "Battery" if profile['has_battery'] else "No Battery"
        phase = f"{profile['phases']}-Phase"
        pv = f"{3 if profile['has_pv3'] else 2} PV Strings"
        power = f"{profile['max_power_kw']}kW"

        print(f"{i:2}. {key:25} - {profile['name']:30} [{phase}, {pv}, {battery}, {power}]")
    print("=" * 70)


if __name__ == "__main__":
    # Test the model loader
    list_models()

    print("\n\nTesting SPH-6000 model:")
    print("-" * 70)
    model = InverterModel('sph_3000_6000')
    print(f"Name: {model.name}")
    print(f"Max Power: {model.max_power_kw}kW")
    print(f"Has Battery: {model.has_battery}")
    print(f"PV Strings: {model.num_pv_strings}")
    print(f"Input Registers: {len(model.get_input_registers())}")
    print(f"Holding Registers: {len(model.get_holding_registers())}")
