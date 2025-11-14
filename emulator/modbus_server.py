"""
Modbus TCP Server for Inverter Emulation

Serves simulated register values via Modbus TCP protocol.
"""

import logging
import threading
from typing import Optional
from pymodbus.server import StartTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusServerContext
from pymodbus.datastore.context import ModbusDeviceContext

logger = logging.getLogger(__name__)


class DynamicModbusDataBlock(ModbusSequentialDataBlock):
    """Dynamic data block that fetches values from simulator."""

    def __init__(self, simulator, register_type: str, address_range: tuple):
        """Initialize dynamic data block.

        Args:
            simulator: InverterSimulator instance
            register_type: 'input' or 'holding'
            address_range: (start, count) tuple
        """
        self.simulator = simulator
        self.register_type = register_type

        # Initialize with zeros
        initial_values = [0] * address_range[1]
        super().__init__(address_range[0], initial_values)

    def getValues(self, address, count=1):
        """Get register values from simulator.

        Args:
            address: Starting register address
            count: Number of registers to read

        Returns:
            List of register values
        """
        values = []
        for i in range(count):
            addr = address + i
            value = self.simulator.get_register_value(self.register_type, addr)
            if value is None:
                value = 0  # Default for unmapped registers
            values.append(value)
        return values

    def setValues(self, address, values):
        """Set register values (for holding registers).

        Args:
            address: Starting register address
            values: List of values to write
        """
        # For now, we don't support writes, but could implement control later
        logger.info(f"Write to {self.register_type} register {address}: {values}")
        # Call parent to maintain internal state
        super().setValues(address, values)


class ModbusEmulatorServer:
    """Modbus TCP server for inverter emulation."""

    def __init__(self, simulator, port: int = 502, slave_id: int = 1):
        """Initialize Modbus server.

        Args:
            simulator: InverterSimulator instance
            port: TCP port to listen on
            slave_id: Modbus slave ID
        """
        self.simulator = simulator
        self.port = port
        self.slave_id = slave_id
        self.server_thread = None
        self.running = False

        # Determine register ranges from model
        input_regs = simulator.model.get_input_registers()
        holding_regs = simulator.model.get_holding_registers()

        # Calculate ranges (Modbus addressing starts at 0)
        if input_regs:
            input_min = min(input_regs.keys())
            input_max = max(input_regs.keys())
            input_range = (0, input_max + 10)  # Add some buffer
        else:
            input_range = (0, 100)

        if holding_regs:
            holding_min = min(holding_regs.keys())
            holding_max = max(holding_regs.keys())
            holding_range = (0, holding_max + 10)
        else:
            holding_range = (0, 100)

        # Create dynamic data blocks
        input_block = DynamicModbusDataBlock(simulator, 'input', input_range)
        holding_block = DynamicModbusDataBlock(simulator, 'holding', holding_range)

        # Discrete and coil blocks (not used, but required)
        discrete_block = ModbusSequentialDataBlock(0, [0] * 100)
        coil_block = ModbusSequentialDataBlock(0, [0] * 100)

        # Create device context
        self.device_context = ModbusDeviceContext(
            di=discrete_block,  # Discrete Inputs
            co=coil_block,      # Coils
            hr=holding_block,   # Holding Registers
            ir=input_block      # Input Registers
        )

        # Create server context
        self.server_context = ModbusServerContext(
            devices={slave_id: self.device_context},
            single=False
        )

    def start(self) -> None:
        """Start the Modbus server in a background thread."""
        if self.running:
            logger.warning("Server already running")
            return

        self.running = True
        self.server_thread = threading.Thread(target=self._run_server, daemon=True)
        self.server_thread.start()
        logger.info(f"Modbus server started on port {self.port}")

    def _run_server(self) -> None:
        """Run the Modbus server (blocking)."""
        try:
            # Update simulator periodically (every 2 seconds)
            def update_callback():
                """Callback to update simulator values."""
                if self.running:
                    self.simulator.update()
                    threading.Timer(2.0, update_callback).start()

            # Start update timer
            update_callback()

            # Start Modbus server
            StartTcpServer(
                context=self.server_context,
                address=("0.0.0.0", self.port)
            )
        except Exception as e:
            logger.error(f"Server error: {e}")
            self.running = False

    def stop(self) -> None:
        """Stop the Modbus server."""
        self.running = False
        if self.server_thread:
            self.server_thread.join(timeout=2.0)
        logger.info("Modbus server stopped")

    def is_running(self) -> bool:
        """Check if server is running."""
        return self.running
