"""
Growatt Inverter Emulator Package

A realistic Modbus TCP emulator for Growatt inverter models.
Simulates solar generation, battery storage, and grid interaction.
"""

__version__ = "0.1.0"

# Lazy imports - only import if the modules are directly requested
# This allows importing emulator.models without requiring pymodbus
__all__ = [
    'InverterSimulator',
    'ModbusEmulatorServer',
    'EmulatorDisplay',
    'ControlHandler',
]

def __getattr__(name):
    """Lazy import modules to avoid requiring pymodbus for everything."""
    if name == 'InverterSimulator':
        from .simulator import InverterSimulator
        return InverterSimulator
    elif name == 'ModbusEmulatorServer':
        from .modbus_server import ModbusEmulatorServer
        return ModbusEmulatorServer
    elif name == 'EmulatorDisplay':
        from .display import EmulatorDisplay
        return EmulatorDisplay
    elif name == 'ControlHandler':
        from .controls import ControlHandler
        return ControlHandler
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
