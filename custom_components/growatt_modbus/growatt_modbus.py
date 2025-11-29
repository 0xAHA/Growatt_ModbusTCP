#!/usr/bin/env python3
"""
Growatt MIN-10000 Modbus Reader
Home Assistant Integration Module

This module handles communication with Growatt MIN series inverters via RS485 Modbus.
Based on Growatt Modbus RTU Protocol V1.39 documentation.

REQUIREMENTS:
- Python 3.7+
- pymodbus (pip install pymodbus)
- pyserial (pip install pyserial) 

Hardware Setup:
- Connect RS485-to-USB/TCP converter to inverter SYS COM port pins 3&4
- Set converter to 9600 baud, 8N1, no flow control
"""

import time
import logging
from dataclasses import dataclass
from typing import Dict, Any, Optional, Tuple, Union
from homeassistant.config_entries import ConfigEntry

# Import register definitions
from .const import STATUS_CODES, combine_registers, REGISTER_MAPS

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pymodbus.client import ModbusTcpClient, ModbusSerialClient

try:
    # For RS485-to-USB connection
    import serial
    # Try new import style first (pymodbus 3.x+)
    try:
        from pymodbus.client import ModbusSerialClient as ModbusClient
    except ImportError:
        # Fall back to old import style (pymodbus 2.x)
        from pymodbus.client.sync import ModbusSerialClient as ModbusClient
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False

try:
    # For RS485-to-TCP connection (like EW11)
    # Try new import style first (pymodbus 3.x+)
    try:
        from pymodbus.client import ModbusTcpClient
    except ImportError:
        # Fall back to old import style (pymodbus 2.x)
        from pymodbus.client.sync import ModbusTcpClient
    TCP_AVAILABLE = True
except ImportError:
    TCP_AVAILABLE = False

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class GrowattData:
    """Container for Growatt inverter data"""
    # Solar Input
    pv1_voltage: float = 0.0          # V
    pv1_current: float = 0.0          # A  
    pv1_power: float = 0.0            # W
    pv2_voltage: float = 0.0          # V
    pv2_current: float = 0.0          # A
    pv2_power: float = 0.0            # W
    pv3_voltage: float = 0.0          # V
    pv3_current: float = 0.0          # A
    pv3_power: float = 0.0            # W
    pv_total_power: float = 0.0       # W
    
    # AC Output (generic - usually Phase R for 3-phase)
    ac_voltage: float = 0.0           # V
    ac_current: float = 0.0           # A
    ac_power: float = 0.0             # W
    ac_frequency: float = 0.0         # Hz

    # Three-Phase AC Output (individual phases)
    ac_voltage_r: float = 0.0         # V (Phase R/L1)
    ac_current_r: float = 0.0         # A (Phase R/L1)
    ac_power_r: float = 0.0           # W (Phase R/L1)
    ac_voltage_s: float = 0.0         # V (Phase S/L2)
    ac_current_s: float = 0.0         # A (Phase S/L2)
    ac_power_s: float = 0.0           # W (Phase S/L2)
    ac_voltage_t: float = 0.0         # V (Phase T/L3)
    ac_current_t: float = 0.0         # A (Phase T/L3)
    ac_power_t: float = 0.0           # W (Phase T/L3)

    # Line-to-Line Voltages (3-phase only)
    ac_voltage_rs: float = 0.0        # V
    ac_voltage_st: float = 0.0        # V
    ac_voltage_tr: float = 0.0        # V
    
    # Power Flow (storage/hybrid models)
    power_to_user: float = 0.0        # W
    power_to_grid: float = 0.0        # W (export)
    power_to_load: float = 0.0        # W
    
    # Energy & Status
    energy_today: float = 0.0         # kWh
    energy_total: float = 0.0         # kWh
    energy_to_user_today: float = 0.0 # kWh
    energy_to_user_total: float = 0.0 # kWh
    energy_to_grid_today: float = 0.0 # kWh
    energy_to_grid_total: float = 0.0 # kWh
    load_energy_today: float = 0.0    # kWh
    load_energy_total: float = 0.0    # kWh
    
    # Temperatures
    inverter_temp: float = 0.0        # °C
    ipm_temp: float = 0.0             # °C
    boost_temp: float = 0.0           # °C

    # Battery (storage/hybrid models)
    battery_voltage: float = 0.0      # V
    battery_current: float = 0.0      # A (signed: +discharge, -charge)
    battery_soc: float = 0.0          # %
    battery_temp: float = 0.0         # °C
    charge_power: float = 0.0         # W
    discharge_power: float = 0.0      # W
    charge_energy_today: float = 0.0  # kWh
    discharge_energy_today: float = 0.0  # kWh
    charge_energy_total: float = 0.0  # kWh
    discharge_energy_total: float = 0.0  # kWh
        
    # Diagnostics
    status: int = 0                   # Inverter status
    derating_mode: int = 0
    fault_code: int = 0
    warning_code: int = 0

    # Export Control (writable registers)
    export_limit_mode: int = 0        # 0=Disabled, 1=RS485, 2=RS232, 3=CT
    export_limit_power: int = 0       # 0-1000 (0-100.0%)

    # Device Info
    firmware_version: str = ""
    serial_number: str = ""

class GrowattModbus:
    """Growatt MIN series Modbus client"""
    
    def __init__(self, connection_type='tcp', host='192.168.1.100', port=502, 
             device='/dev/ttyUSB0', baudrate=9600, slave_id=1, 
             register_map='MIN_7000_10000TL_X', timeout=10):
        """
        Initialize Modbus connection
        
        Args:
            connection_type: 'tcp' for RS485-to-TCP converter, 'serial' for RS485-to-USB
            host: IP address for TCP connection
            port: Port for TCP connection
            device: Serial device path for USB connection
            baudrate: Serial baud rate (usually 9600)
            slave_id: Modbus slave ID (usually 1)
            register_map: Which register mapping to use (see const.py)
            timeout: Connection timeout in seconds (default: 10)
        """
        self.connection_type = connection_type
        self.slave_id = slave_id
        self.client: Optional[Union['ModbusTcpClient', 'ModbusSerialClient']] = None
        self.last_read_time = 0
        self.min_read_interval = 1.0  # 1 second minimum between reads
        self._timeout = timeout

        # Store connection details for logging
        self.host = host
        self.port = port
        self.device = device

        # Load register map
        if register_map not in REGISTER_MAPS:
            raise ValueError(f"Unknown register map: {register_map}. Available: {list(REGISTER_MAPS.keys())}")

        self.register_map = REGISTER_MAPS[register_map]
        self.register_map_name = register_map

        # Build connection identifier for logs
        if connection_type == 'tcp':
            self.connection_id = f"{host}:{port}"
        else:
            self.connection_id = f"{device}"

        logger.info(f"Initializing {self.register_map['name']} profile for {self.connection_id}")
        
        # Cache for raw register data
        self._register_cache = {}
        
        if connection_type == 'tcp':
            if not TCP_AVAILABLE:
                raise ImportError("pymodbus not available for TCP connection")
            
            # Handle different pymodbus versions for TCP client
            try:
                # New style (pymodbus 3.x+) - supports timeout parameter
                self.client = ModbusTcpClient(host=host, port=port, timeout=self._timeout)
            except TypeError:
                # Old style (pymodbus 2.x) - timeout must be set after creation
                self.client = ModbusTcpClient(host, port)
                # Set timeout on the client object if supported
                if hasattr(self.client, 'timeout'):
                    self.client.timeout = self._timeout
            
            logger.info(f"Connecting to Growatt via TCP: {host}:{port} (timeout: {self._timeout}s)")
            
        elif connection_type == 'serial':
            if not SERIAL_AVAILABLE:
                raise ImportError("pymodbus and/or pyserial not available for serial connection")
            
            # Handle different pymodbus versions
            try:
                # New style (pymodbus 3.x+)
                self.client = ModbusClient(
                    port=device,
                    baudrate=baudrate,
                    timeout=self._timeout,  # Use configured timeout, not hardcoded 3
                    parity='N',
                    stopbits=1,
                    bytesize=8
                )
            except TypeError:
                # Old style (pymodbus 2.x)
                self.client = ModbusClient(
                    method='rtu',
                    port=device,
                    baudrate=baudrate,
                    timeout=self._timeout,  # Use configured timeout
                    parity='N',
                    stopbits=1,
                    bytesize=8
                )
            logger.info(f"Connecting to Growatt via Serial: {device} @ {baudrate} baud (timeout: {self._timeout}s)")
        else:
            raise ValueError("connection_type must be 'tcp' or 'serial'")
    
    def connect(self) -> bool:
        """Establish connection to inverter"""
        try:
            result = self.client.connect()
            if result:
                logger.info(f"[{self.register_map['name']}@{self.connection_id}] Successfully connected")
            else:
                logger.error(f"[{self.register_map['name']}@{self.connection_id}] Failed to connect")
            return result
        except Exception as e:
            logger.error(f"[{self.register_map['name']}@{self.connection_id}] Connection error: {e}")
            return False
    
    def disconnect(self):
        """Close connection"""
        if self.client:
            self.client.close()
            logger.info(f"[{self.register_map['name']}@{self.connection_id}] Disconnected")
    
    def _enforce_read_interval(self):
        """Ensure minimum time between reads per Growatt spec"""
        current_time = time.time()
        time_since_last = current_time - self.last_read_time
        if time_since_last < self.min_read_interval:
            sleep_time = self.min_read_interval - time_since_last
            logger.debug(f"Sleeping {sleep_time:.2f}s to respect read interval")
            time.sleep(sleep_time)
        self.last_read_time = time.time()
    
    def read_input_registers(self, start_address: int, count: int) -> Optional[list]:
        """Read input registers with error handling"""
        self._enforce_read_interval()
        
        try:
            # Try keyword arguments with different parameter names for pymodbus versions
            try:
                # Newer pymodbus uses device_id
                response = self.client.read_input_registers(
                    address=start_address, 
                    count=count, 
                    device_id=self.slave_id
                )
            except TypeError:
                # Try with 'slave' parameter
                try:
                    response = self.client.read_input_registers(
                        address=start_address, 
                        count=count, 
                        slave=self.slave_id
                    )
                except TypeError:
                    # Try with 'unit' parameter (pymodbus 2.5.x)
                    try:
                        response = self.client.read_input_registers(
                            start_address, 
                            count, 
                            unit=self.slave_id
                        )
                    except TypeError:
                        # Simplest - just address and count
                        response = self.client.read_input_registers(
                            start_address, 
                            count
                        )
            
            # Handle different pymodbus versions for error checking
            if hasattr(response, 'isError'):
                if response.isError():
                    logger.warning(f"Modbus error reading input registers {start_address}-{start_address+count-1}: {response}")
                    return None
            elif hasattr(response, 'is_error') and callable(response.is_error):
                if response.is_error():
                    logger.warning(f"Modbus error reading input registers {start_address}-{start_address+count-1}: {response}")
                    return None

            if hasattr(response, 'registers'):
                logger.debug(f"Successfully read {len(response.registers)} registers from {start_address}")
                return response.registers

            logger.warning(f"Unknown response type: {type(response)}, response: {response}")
            return None
            
        except Exception as e:
            logger.debug(f"Exception reading input registers: {e}")
            return None
    
    def read_holding_registers(self, start_address: int, count: int) -> Optional[list]:
        """Read holding registers with error handling"""
        self._enforce_read_interval()
        
        try:
            # Try keyword arguments (pymodbus 3.x+)
            try:
                response = self.client.read_holding_registers(
                    address=start_address, 
                    count=count, 
                    slave=self.slave_id
                )
            except TypeError:
                # Try with 'unit' parameter (pymodbus 2.5.x)
                try:
                    response = self.client.read_holding_registers(
                        start_address, 
                        count, 
                        unit=self.slave_id
                    )
                except TypeError:
                    # Simplest - just address and count (some versions handle slave differently)
                    response = self.client.read_holding_registers(
                        start_address, 
                        count
                    )
            
            # Handle different pymodbus versions for error checking
            if hasattr(response, 'isError'):
                if response.isError():
                    logger.debug(f"Modbus error reading holding registers {start_address}-{start_address+count-1}")
                    return None
            elif hasattr(response, 'is_error') and callable(response.is_error):
                if response.is_error():
                    logger.debug(f"Modbus error reading holding registers {start_address}-{start_address+count-1}")
                    return None
            
            if hasattr(response, 'registers'):
                return response.registers
            
            logger.debug(f"Unknown response type: {type(response)}")
            return None
            
        except Exception as e:
            logger.debug(f"Exception reading holding registers: {e}")
            return None

    def _get_register_value(self, address: int) -> Optional[float]:
        """
        Get scaled value from register, handling 32-bit pairs automatically
        """
        reg_info = self.register_map['input_registers'].get(address)
        if not reg_info:
            return None
        
        raw_value = self._register_cache.get(address)
        if raw_value is None:
            return None
        
        # Check if this is part of a 32-bit pair
        pair_addr = reg_info.get('pair')
        if pair_addr is not None:
            # This register is part of a pair
            # Determine if we're HIGH or LOW word
            pair_info = self.register_map['input_registers'].get(pair_addr)
            if not pair_info:
                # Fallback to single register
                scale = reg_info.get('scale', 1)
                return raw_value * scale
            
            # Check which register is HIGH and which is LOW
            if address < pair_addr:
                # Current address is HIGH, pair is LOW
                high_value = raw_value
                low_value = self._register_cache.get(pair_addr, 0)
                combined_scale = pair_info.get('combined_scale', 1)
            else:
                # Current address is LOW, pair is HIGH
                low_value = raw_value
                high_value = self._register_cache.get(pair_addr, 0)
                combined_scale = reg_info.get('combined_scale', 1)
            
            # Combine 32-bit value
            combined = (high_value << 16) | low_value
            
            # Handle signed values if specified
            if reg_info.get('signed') or pair_info.get('signed'):
                if combined > 0x7FFFFFFF:  # If sign bit is set
                    combined = combined - 0x100000000
            
            return combined * combined_scale
        
        else:
            # Single register, apply its scale
            scale = reg_info.get('scale', 1)
            return raw_value * scale

    def read_all_data(self) -> Optional[GrowattData]:
        """Read all relevant data from inverter"""
        data = GrowattData()
        
        # Determine register range based on map
        input_regs = self.register_map['input_registers']
        
        # Find min and max addresses to read
        addresses = list(input_regs.keys())
        if not addresses:
            logger.error("No input registers defined in map")
            return None
        
        min_addr = min(addresses)
        max_addr = max(addresses)
        
        # Clear cache
        self._register_cache = {}
        
        # Determine which ranges we need to read
        # Check if we have registers in different ranges
        has_base_range = any(0 <= addr < 1000 for addr in addresses)
        has_storage_range = any(1000 <= addr < 2000 for addr in addresses)
        has_3000_range = any(3000 <= addr < 4000 for addr in addresses)
        has_31000_range = any(31000 <= addr < 32000 for addr in addresses)
        
        # Read base range (0-124) if needed - SPH models
        if has_base_range:
            logger.debug("Reading base range (0-124)")
            registers = self.read_input_registers(0, 125)
            if registers is None:
                logger.error("Failed to read base input register block")
                return None
            
            # Populate cache
            for i, value in enumerate(registers):
                self._register_cache[i] = value
        
        # Read storage range (1000-1124) if needed - SPH/hybrid models with battery
        if has_storage_range:
            logger.debug("Reading storage range (1000-1124)")
            registers = self.read_input_registers(1000, 125)
            if registers is None:
                logger.warning("Failed to read storage register block (battery data may be unavailable)")
                # Don't return None - continue with what we have
            else:
                # Populate cache
                for i, value in enumerate(registers):
                    self._register_cache[1000 + i] = value
        
        # Read 3000 range if needed - MIN/MOD models
        if has_3000_range:
            addrs_3000 = sorted([addr for addr in addresses if 3000 <= addr < 4000])
            max_3000_addr = max(addrs_3000)
            count_3000 = (max_3000_addr - 3000) + 1

            # Check if we need to split the read (max 125 registers per read)
            if count_3000 > 125:
                # Split into contiguous blocks
                logger.debug(f"Splitting 3000 range into blocks (total range: 3000-{max_3000_addr}, {count_3000} registers)")

                blocks = []
                current_block = [addrs_3000[0]]
                for addr in addrs_3000[1:]:
                    if addr - current_block[-1] <= 10:  # Group if gap is small
                        current_block.append(addr)
                    else:
                        blocks.append(current_block)
                        current_block = [addr]
                blocks.append(current_block)

                # Read each block separately
                for block in blocks:
                    min_addr_block = min(block)
                    max_addr_block = max(block)
                    count_block = (max_addr_block - min_addr_block) + 1

                    # Further split if block still exceeds 125 registers
                    if count_block > 125:
                        # Read in 125-register chunks
                        for chunk_start in range(min_addr_block, max_addr_block + 1, 125):
                            chunk_count = min(125, max_addr_block - chunk_start + 1)
                            logger.debug(f"Reading 3000 sub-chunk ({chunk_start}-{chunk_start+chunk_count-1}, {chunk_count} registers)")
                            registers = self.read_input_registers(chunk_start, chunk_count)
                            if registers is None:
                                logger.warning(f"Failed to read 3000 chunk ({chunk_start}-{chunk_start+chunk_count-1})")
                            else:
                                for i, value in enumerate(registers):
                                    self._register_cache[chunk_start + i] = value
                    else:
                        logger.debug(f"Reading 3000 sub-range ({min_addr_block}-{max_addr_block}, {count_block} registers)")
                        registers = self.read_input_registers(min_addr_block, count_block)
                        if registers is None:
                            logger.warning(f"Failed to read 3000 block ({min_addr_block}-{max_addr_block})")
                        else:
                            for i, value in enumerate(registers):
                                addr = min_addr_block + i
                                self._register_cache[addr] = value
                                # Log load_energy registers specifically
                                if addr in [3075, 3076, 3077, 3078]:
                                    logger.debug(f"[{self.register_map['name']}@{self.connection_id}] Cached 3000 range: reg {addr} = {value}")
            else:
                # Single read is sufficient
                logger.debug(f"Reading 3000 range (3000-{max_3000_addr}, {count_3000} registers)")
                registers = self.read_input_registers(3000, count_3000)
                if registers is None:
                    logger.error("Failed to read main input register block")
                    return None

                # Populate cache
                for i, value in enumerate(registers):
                    self._register_cache[3000 + i] = value

        # Read 31000 range if needed - MOD extended battery/BMS range
        if has_31000_range:
            # Split into contiguous blocks to avoid reading large gaps
            # (e.g., 31126-31127 and 31200-31209 are separate blocks with a 73-register gap)
            addrs_31000 = sorted([addr for addr in addresses if 31000 <= addr < 32000])

            # Group into contiguous blocks (max gap of 10 registers)
            blocks = []
            current_block = [addrs_31000[0]]
            for addr in addrs_31000[1:]:
                if addr - current_block[-1] <= 10:
                    current_block.append(addr)
                else:
                    blocks.append(current_block)
                    current_block = [addr]
            blocks.append(current_block)

            # Read each block separately
            for block in blocks:
                min_addr_block = min(block)
                max_addr_block = max(block)
                count_block = (max_addr_block - min_addr_block) + 1
                logger.debug(f"Reading 31000 sub-range ({min_addr_block}-{max_addr_block}, {count_block} registers)")
                registers = self.read_input_registers(min_addr_block, count_block)
                if registers is None:
                    logger.warning(f"Failed to read extended battery register block ({min_addr_block}-{max_addr_block})")
                    # Don't return None - continue with what we have
                else:
                    # Populate cache
                    for i, value in enumerate(registers):
                        self._register_cache[min_addr_block + i] = value

        # Now extract values using the register map
        try:
            # Status
            data.status = int(self._get_register_value(min_addr) or 0)
            
            # PV String 1
            pv1_voltage_addr = self._find_register_by_name('pv1_voltage')
            pv1_current_addr = self._find_register_by_name('pv1_current')
            pv1_power_low_addr = self._find_register_by_name('pv1_power_low')
            
            if pv1_voltage_addr:
                data.pv1_voltage = self._get_register_value(pv1_voltage_addr) or 0.0
            if pv1_current_addr:
                data.pv1_current = self._get_register_value(pv1_current_addr) or 0.0
            if pv1_power_low_addr:
                data.pv1_power = self._get_register_value(pv1_power_low_addr) or 0.0
            
            # PV String 2
            pv2_voltage_addr = self._find_register_by_name('pv2_voltage')
            pv2_current_addr = self._find_register_by_name('pv2_current')
            pv2_power_low_addr = self._find_register_by_name('pv2_power_low')
            
            if pv2_voltage_addr:
                data.pv2_voltage = self._get_register_value(pv2_voltage_addr) or 0.0
            if pv2_current_addr:
                data.pv2_current = self._get_register_value(pv2_current_addr) or 0.0
            if pv2_power_low_addr:
                data.pv2_power = self._get_register_value(pv2_power_low_addr) or 0.0
            
            # PV String 3 (if available)
            pv3_voltage_addr = self._find_register_by_name('pv3_voltage')
            pv3_current_addr = self._find_register_by_name('pv3_current')
            pv3_power_low_addr = self._find_register_by_name('pv3_power_low')
            
            if pv3_voltage_addr:
                data.pv3_voltage = self._get_register_value(pv3_voltage_addr) or 0.0
            if pv3_current_addr:
                data.pv3_current = self._get_register_value(pv3_current_addr) or 0.0
            if pv3_power_low_addr:
                data.pv3_power = self._get_register_value(pv3_power_low_addr) or 0.0
            
            # Total PV Power
            pv_total_addr = self._find_register_by_name('pv_total_power_low')
            if pv_total_addr:
                data.pv_total_power = self._get_register_value(pv_total_addr) or 0.0
            else:
                # Calculate from strings if not available
                data.pv_total_power = data.pv1_power + data.pv2_power + data.pv3_power
            
            # AC Output (generic - will use Phase R via alias for 3-phase)
            ac_voltage_addr = self._find_register_by_name('ac_voltage')
            ac_current_addr = self._find_register_by_name('ac_current')
            ac_power_addr = self._find_register_by_name('ac_power_low')
            ac_freq_addr = self._find_register_by_name('ac_frequency')

            if ac_voltage_addr:
                data.ac_voltage = self._get_register_value(ac_voltage_addr) or 0.0
            if ac_current_addr:
                data.ac_current = self._get_register_value(ac_current_addr) or 0.0
            if ac_power_addr:
                data.ac_power = self._get_register_value(ac_power_addr) or 0.0
            if ac_freq_addr:
                data.ac_frequency = self._get_register_value(ac_freq_addr) or 0.0

            # Three-Phase AC Output (individual phases)
            # Phase R
            ac_voltage_r_addr = self._find_register_by_name('ac_voltage_r')
            ac_current_r_addr = self._find_register_by_name('ac_current_r')
            ac_power_r_addr = self._find_register_by_name('ac_power_r_low')
            if ac_voltage_r_addr:
                data.ac_voltage_r = self._get_register_value(ac_voltage_r_addr) or 0.0
            if ac_current_r_addr:
                data.ac_current_r = self._get_register_value(ac_current_r_addr) or 0.0
            if ac_power_r_addr:
                data.ac_power_r = self._get_register_value(ac_power_r_addr) or 0.0

            # Phase S
            ac_voltage_s_addr = self._find_register_by_name('ac_voltage_s')
            ac_current_s_addr = self._find_register_by_name('ac_current_s')
            ac_power_s_addr = self._find_register_by_name('ac_power_s_low')
            if ac_voltage_s_addr:
                data.ac_voltage_s = self._get_register_value(ac_voltage_s_addr) or 0.0
            if ac_current_s_addr:
                data.ac_current_s = self._get_register_value(ac_current_s_addr) or 0.0
            if ac_power_s_addr:
                data.ac_power_s = self._get_register_value(ac_power_s_addr) or 0.0

            # Phase T
            ac_voltage_t_addr = self._find_register_by_name('ac_voltage_t')
            ac_current_t_addr = self._find_register_by_name('ac_current_t')
            ac_power_t_addr = self._find_register_by_name('ac_power_t_low')
            if ac_voltage_t_addr:
                data.ac_voltage_t = self._get_register_value(ac_voltage_t_addr) or 0.0
            if ac_current_t_addr:
                data.ac_current_t = self._get_register_value(ac_current_t_addr) or 0.0
            if ac_power_t_addr:
                data.ac_power_t = self._get_register_value(ac_power_t_addr) or 0.0

            # Line-to-Line Voltages
            ac_voltage_rs_addr = self._find_register_by_name('line_voltage_rs')
            ac_voltage_st_addr = self._find_register_by_name('line_voltage_st')
            ac_voltage_tr_addr = self._find_register_by_name('line_voltage_tr')
            if ac_voltage_rs_addr:
                data.ac_voltage_rs = self._get_register_value(ac_voltage_rs_addr) or 0.0
            if ac_voltage_st_addr:
                data.ac_voltage_st = self._get_register_value(ac_voltage_st_addr) or 0.0
            if ac_voltage_tr_addr:
                data.ac_voltage_tr = self._get_register_value(ac_voltage_tr_addr) or 0.0
            
            # Power Flow (if available - storage/hybrid models)
            power_to_user_addr = self._find_register_by_name('power_to_user_low')
            power_to_grid_addr = self._find_register_by_name('power_to_grid_low')
            power_to_load_addr = self._find_register_by_name('power_to_load_low')
            
            if power_to_user_addr:
                data.power_to_user = self._get_register_value(power_to_user_addr) or 0.0
            if power_to_grid_addr:
                data.power_to_grid = self._get_register_value(power_to_grid_addr) or 0.0
            if power_to_load_addr:
                data.power_to_load = self._get_register_value(power_to_load_addr) or 0.0
            
            # Energy Today
            energy_today_addr = self._find_register_by_name('energy_today_low')
            if energy_today_addr:
                data.energy_today = self._get_register_value(energy_today_addr) or 0.0
                logger.debug(f"[{self.register_map['name']}@{self.connection_id}] Energy today from reg {energy_today_addr}: {data.energy_today} kWh (cache: {self._register_cache.get(energy_today_addr)})")
            
            # Energy Total
            energy_total_addr = self._find_register_by_name('energy_total_low')
            if energy_total_addr:
                data.energy_total = self._get_register_value(energy_total_addr) or 0.0
            
            # Energy Breakdown (if available)
            self._read_energy_breakdown(data)
            
            # Battery Data (if available - storage/hybrid models)
            self._read_battery_data(data)
            
            # Temperatures
            inverter_temp_addr = self._find_register_by_name('inverter_temp')
            ipm_temp_addr = self._find_register_by_name('ipm_temp')
            boost_temp_addr = self._find_register_by_name('boost_temp')
            
            if inverter_temp_addr:
                data.inverter_temp = self._get_register_value(inverter_temp_addr) or 0.0
            if ipm_temp_addr:
                data.ipm_temp = self._get_register_value(ipm_temp_addr) or 0.0
            if boost_temp_addr:
                data.boost_temp = self._get_register_value(boost_temp_addr) or 0.0
            
            # Diagnostics
            derating_addr = self._find_register_by_name('derating_mode')
            fault_addr = self._find_register_by_name('fault_code')
            warning_addr = self._find_register_by_name('warning_code')
            
            if derating_addr:
                data.derating_mode = int(self._get_register_value(derating_addr) or 0)
            if fault_addr:
                data.fault_code = int(self._get_register_value(fault_addr) or 0)
            if warning_addr:
                data.warning_code = int(self._get_register_value(warning_addr) or 0)
            
            logger.debug(f"Read data: PV={data.pv_total_power}W, AC={data.ac_power}W, Battery={getattr(data, 'battery_soc', 'N/A')}%, Temp={data.inverter_temp}°C")
            
        except Exception as e:
            logger.error(f"Error parsing register data: {e}", exc_info=True)
            return None
        
        # Read device info from holding registers
        self._read_device_info(data)
        
        return data
    
    def write_register(self, register: int, value: int) -> bool:
        """
        Write a single holding register.
        
        Args:
            register: Register address (relative to base address 0)
            value: Value to write (already scaled as integer)
        
        Returns:
            bool: True if write successful, False otherwise
        """
        try:
            # Check if client exists and is connected
            if not self.client or not hasattr(self.client, 'is_socket_open') or not self.client.is_socket_open():
                logger.error("Cannot write register - not connected")
                return False
            
            # Write to holding register (function code 6)
            result = self.client.write_register(
                address=register,
                value=value,
                device_id=self.slave_id
            )
            
            if result.isError():
                logger.error(f"Failed to write register {register}: {result}")
                return False
            
            logger.info(f"Successfully wrote value {value} to register {register}")
            return True
            
        except Exception as e:
            logger.error(f"Exception writing register {register}: {e}")
            return False


    def _find_register_by_name(self, name: str) -> Optional[int]:
        """Find register address by its name or alias"""
        input_regs = self.register_map['input_registers']
        for addr, reg_info in input_regs.items():
            # Check exact name match
            if reg_info['name'] == name:
                return addr
            # Check alias match (for 3-phase compatibility)
            if reg_info.get('alias') == name:
                return addr
        return None
    
    def _read_energy_breakdown(self, data: GrowattData) -> None:
        """Read detailed energy breakdown (storage/hybrid models)"""
        try:
            # Energy to user
            addr = self._find_register_by_name('energy_to_user_today_low')
            if addr:
                data.energy_to_user_today = self._get_register_value(addr) or 0.0
            
            addr = self._find_register_by_name('energy_to_user_total_low')
            if addr:
                data.energy_to_user_total = self._get_register_value(addr) or 0.0
            
            # Energy to grid
            addr = self._find_register_by_name('energy_to_grid_today_low')
            if addr:
                data.energy_to_grid_today = self._get_register_value(addr) or 0.0
            
            addr = self._find_register_by_name('energy_to_grid_total_low')
            if addr:
                data.energy_to_grid_total = self._get_register_value(addr) or 0.0
            
            # Load energy
            addr = self._find_register_by_name('load_energy_today_low')
            if addr:
                data.load_energy_today = self._get_register_value(addr) or 0.0
                logger.debug(f"[{self.register_map['name']}@{self.connection_id}] Load energy today from reg {addr}: {data.load_energy_today} kWh (cache: {self._register_cache.get(addr)})")
            else:
                logger.warning(f"[{self.register_map['name']}@{self.connection_id}] load_energy_today_low register not found")

            addr = self._find_register_by_name('load_energy_total_low')
            if addr:
                data.load_energy_total = self._get_register_value(addr) or 0.0
                logger.debug(f"[{self.register_map['name']}@{self.connection_id}] Load energy total from reg {addr}: {data.load_energy_total} kWh (cache: {self._register_cache.get(addr)})")
                
        except Exception as e:
            logger.debug(f"Energy breakdown not available: {e}")
    
    def _read_battery_data(self, data: GrowattData) -> None:
        """Read battery data (storage/hybrid models)"""
        try:
            # Battery voltage
            addr = self._find_register_by_name('battery_voltage')
            if addr:
                data.battery_voltage = self._get_register_value(addr) or 0.0
                logger.debug(f"Battery voltage from reg {addr}: {data.battery_voltage}V")

            # Battery current (signed: positive=discharge, negative=charge)
            # Try VPP protocol first (31216 - low register of 32-bit pair)
            addr = self._find_register_by_name('battery_current_low')
            if not addr:
                # Fallback to legacy register (3170)
                addr = self._find_register_by_name('battery_current_legacy')
            if addr:
                data.battery_current = self._get_register_value(addr) or 0.0
                logger.debug(f"Battery current from reg {addr}: {data.battery_current}A")

            # Battery SOC
            addr = self._find_register_by_name('battery_soc')
            if addr:
                data.battery_soc = self._get_register_value(addr) or 0.0
                logger.debug(f"Battery SOC from reg {addr}: {data.battery_soc}%")

            # Battery temperature
            addr = self._find_register_by_name('battery_temp')
            if addr:
                data.battery_temp = self._get_register_value(addr) or 0.0
                logger.debug(f"Battery temp from reg {addr}: {data.battery_temp}°C")

            # Battery power (signed: positive=charging, negative=discharging)
            # Try new signed battery_power register first (MOD series @ 31126)
            addr = self._find_register_by_name('battery_power_low')
            if addr:
                raw_low = self._register_cache.get(addr, 0)
                pair_addr = self._find_register_by_name('battery_power_high')
                raw_high = self._register_cache.get(pair_addr, 0) if pair_addr else 0
                battery_power = self._get_register_value(addr) or 0.0
                logger.debug(f"Battery power (signed): HIGH={raw_high} (reg {pair_addr}), LOW={raw_low} (reg {addr}) → {battery_power}W")

                # Split into charge/discharge based on sign
                if battery_power > 0:
                    data.charge_power = battery_power
                    data.discharge_power = 0.0
                    logger.debug(f"  → Charging: {data.charge_power}W")
                elif battery_power < 0:
                    data.charge_power = 0.0
                    data.discharge_power = abs(battery_power)
                    logger.debug(f"  → Discharging: {data.discharge_power}W")
                else:
                    data.charge_power = 0.0
                    data.discharge_power = 0.0
            else:
                # Fallback: Try old separate charge/discharge registers (SPH series)
                addr = self._find_register_by_name('charge_power_low')
                if addr:
                    raw_low = self._register_cache.get(addr, 0)
                    pair_addr = self._find_register_by_name('charge_power_high')
                    raw_high = self._register_cache.get(pair_addr, 0) if pair_addr else 0
                    data.charge_power = self._get_register_value(addr) or 0.0
                    logger.debug(f"Charge power: HIGH={raw_high} (reg {pair_addr}), LOW={raw_low} (reg {addr}) → {data.charge_power}W")
                elif data.battery_voltage > 0 and data.battery_current < 0:
                    # Fallback: Calculate from V×I when charging (negative current)
                    data.charge_power = data.battery_voltage * abs(data.battery_current)
                    logger.debug(f"Charge power (calculated): {data.battery_voltage}V × {abs(data.battery_current)}A = {data.charge_power}W")

                addr = self._find_register_by_name('discharge_power_low')
                if addr:
                    raw_low = self._register_cache.get(addr, 0)
                    pair_addr = self._find_register_by_name('discharge_power_high')
                    raw_high = self._register_cache.get(pair_addr, 0) if pair_addr else 0
                    data.discharge_power = self._get_register_value(addr) or 0.0
                    logger.debug(f"Discharge power: HIGH={raw_high} (reg {pair_addr}), LOW={raw_low} (reg {addr}) → {data.discharge_power}W")
                elif data.battery_voltage > 0 and data.battery_current > 0:
                    # Fallback: Calculate from V×I when discharging (positive current)
                    data.discharge_power = data.battery_voltage * data.battery_current
                    logger.debug(f"Discharge power (calculated): {data.battery_voltage}V × {data.battery_current}A = {data.discharge_power}W")
            
            # Charge energy today
            addr = self._find_register_by_name('charge_energy_today_low')
            if addr:
                raw_low = self._register_cache.get(addr, 0)
                pair_addr = self._find_register_by_name('charge_energy_today_high')
                raw_high = self._register_cache.get(pair_addr, 0) if pair_addr else 0
                data.charge_energy_today = self._get_register_value(addr) or 0.0
                logger.debug(f"Charge energy today: HIGH={raw_high} (reg {pair_addr}), LOW={raw_low} (reg {addr}) → {data.charge_energy_today} kWh")
            
            # Discharge energy today
            addr = self._find_register_by_name('discharge_energy_today_low')
            if addr:
                raw_low = self._register_cache.get(addr, 0)
                pair_addr = self._find_register_by_name('discharge_energy_today_high')
                raw_high = self._register_cache.get(pair_addr, 0) if pair_addr else 0
                data.discharge_energy_today = self._get_register_value(addr) or 0.0
                logger.debug(f"Discharge energy today: HIGH={raw_high} (reg {pair_addr}), LOW={raw_low} (reg {addr}) → {data.discharge_energy_today} kWh")
            
            # Charge energy total
            addr = self._find_register_by_name('charge_energy_total_low')
            if addr:
                raw_low = self._register_cache.get(addr, 0)
                pair_addr = self._find_register_by_name('charge_energy_total_high')
                raw_high = self._register_cache.get(pair_addr, 0) if pair_addr else 0
                data.charge_energy_total = self._get_register_value(addr) or 0.0
                logger.debug(f"Charge energy total: HIGH={raw_high} (reg {pair_addr}), LOW={raw_low} (reg {addr}) → {data.charge_energy_total} kWh")
            
            # Discharge energy total
            addr = self._find_register_by_name('discharge_energy_total_low')
            if addr:
                raw_low = self._register_cache.get(addr, 0)
                pair_addr = self._find_register_by_name('discharge_energy_total_high')
                raw_high = self._register_cache.get(pair_addr, 0) if pair_addr else 0
                data.discharge_energy_total = self._get_register_value(addr) or 0.0
                logger.debug(f"Discharge energy total: HIGH={raw_high} (reg {pair_addr}), LOW={raw_low} (reg {addr}) → {data.discharge_energy_total} kWh")

            if data.battery_voltage > 0:
                logger.debug(f"Battery summary: {data.battery_voltage}V, {data.battery_current}A, {data.battery_soc}%, {data.battery_temp}°C, Charge={data.charge_power}W, Discharge={data.discharge_power}W")
            
        except Exception as e:
            logger.debug(f"Battery data not available: {e}")

    def _read_device_info(self, data: GrowattData) -> None:
        """Read device info from holding registers"""
        holding_regs = self.read_holding_registers(0, 20)
        if holding_regs is None:
            logger.debug("Could not read holding registers for device info")
            return

        try:
            holding_map = self.register_map.get('holding_registers', {})

            # Firmware version at register 3
            if len(holding_regs) > 3 and 3 in holding_map:
                fw_version = holding_regs[3]
                data.firmware_version = f"{fw_version >> 8}.{fw_version & 0xFF}"

            # Serial number from registers 9-13
            if len(holding_regs) > 13:
                serial_parts = []
                for i in range(9, 14):  # registers 9-13
                    if i < len(holding_regs):
                        reg_val = holding_regs[i]
                        # Convert 16-bit register to 2 ASCII characters
                        if reg_val > 0:
                            char1 = (reg_val >> 8) & 0xFF
                            char2 = reg_val & 0xFF
                            if char1 > 0 and 32 <= char1 <= 126:  # Printable ASCII
                                serial_parts.append(chr(char1))
                            if char2 > 0 and 32 <= char2 <= 126:
                                serial_parts.append(chr(char2))
                data.serial_number = ''.join(serial_parts).rstrip('\x00')

        except Exception as e:
            logger.warning(f"Error reading device info: {e}")

        # Read export control registers (122-123) if they exist in the profile
        if 122 in holding_map or 123 in holding_map:
            try:
                export_regs = self.read_holding_registers(122, 2)
                if export_regs is not None and len(export_regs) >= 2:
                    if 122 in holding_map:
                        data.export_limit_mode = export_regs[0]
                    if 123 in holding_map:
                        data.export_limit_power = export_regs[1]
                    logger.debug(f"Read export control: mode={data.export_limit_mode}, power={data.export_limit_power}")
            except Exception as e:
                logger.debug(f"Could not read export control registers: {e}")

    def get_status_text(self, status_code: int) -> str:
        """Convert status code to human readable text"""
        status_info = STATUS_CODES.get(status_code, {'name': f'Unknown ({status_code})', 'desc': 'Unknown status code'})
        return status_info['name']