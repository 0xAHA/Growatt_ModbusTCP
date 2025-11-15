"""
Modbus TCP Server for Inverter Emulation

Serves simulated register values via Modbus TCP protocol.
"""

import logging
import threading
from typing import Optional
from pymodbus.server import StartTcpServer
from pymodbus.datastore import ModbusServerContext, ModbusDeviceContext
from pymodbus.datastore import ModbusSparseDataBlock

logger = logging.getLogger(__name__)


class GrowattDataBlock(ModbusSparseDataBlock):
    """
    Custom Modbus data block for pymodbus 3.x.

    Directly fetches values from the simulator on each read request,
    avoiding internal storage issues and addressing offsets.
    """

    def __init__(self, simulator, register_type: str):
        """Initialize custom data block.

        Args:
            simulator: InverterSimulator instance
            register_type: 'input' or 'holding'
        """
        # Initialize sparse block with empty values
        # This allows arbitrary address ranges
        super().__init__({0: 0})
        self.simulator = simulator
        self.register_type = register_type
        logger.info(f"GrowattDataBlock initialized: type={register_type}")

    def getValues(self, address, count=1):
        """Get register values from simulator.

        This method IS called by pymodbus 3.x (unlike async_getValues).

        IMPORTANT: pymodbus 3.x passes address+1 to this method when using
        ModbusSparseDataBlock. To compensate, we subtract 1 from the address.

        Args:
            address: Starting register address (will be actual_address + 1)
            count: Number of registers to read

        Returns:
            List of register values
        """
        values = []
        for i in range(count):
            # Compensate for pymodbus 3.x adding 1 to addresses
            addr = (address - 1) + i
            value = self.simulator.get_register_value(self.register_type, addr)
            if value is None:
                value = 0  # Default for unmapped registers
            values.append(value)

        # Debug logging for key registers (can be disabled in production)
        # if address >= 38 and address <= 50:
        #     logger.debug(f"getValues({self.register_type}, address={address}, count={count}) compensated to {address-1}-{address-1+count-1} -> {values}")
        # elif address >= 1010 and address <= 1064:
        #     logger.debug(f"getValues({self.register_type}, address={address}, count={count}) compensated to {address-1}-{address-1+count-1} -> {values}")

        return values

    def setValues(self, address, values):
        """Set register values (for holding registers).

        Args:
            address: Starting register address
            values: List of values to write
        """
        logger.info(f"Write to {self.register_type} register {address}: {values}")
        # For now, we don't support writes to the simulator
        # Could implement control later
        # Don't call super() - we don't want internal storage

    def validate(self, address, count=1):
        """Validate the request.

        Args:
            address: Starting address
            count: Number of registers

        Returns:
            True if valid (we support all addresses)
        """
        # Accept all addresses - simulator will return 0 for unmapped ones
        return True


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

        # Create custom data blocks that fetch directly from simulator
        input_block = GrowattDataBlock(simulator, 'input')
        holding_block = GrowattDataBlock(simulator, 'holding')

        # Create empty blocks for discrete inputs and coils (not used)
        discrete_block = GrowattDataBlock(simulator, 'discrete')
        coil_block = GrowattDataBlock(simulator, 'coil')

        # Create device context with our custom blocks
        device_context = ModbusDeviceContext(
            di=discrete_block,   # Discrete Inputs
            co=coil_block,       # Coils
            hr=holding_block,    # Holding Registers
            ir=input_block       # Input Registers
        )

        # Create server context
        self.server_context = ModbusServerContext(
            devices={slave_id: device_context},
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
            # Values are fetched directly from simulator on each read,
            # no need to update internal storage
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
