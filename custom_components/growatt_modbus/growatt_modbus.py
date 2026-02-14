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
    pv1_energy_today: float = 0.0     # kWh (WIT per-MPPT energy tracking - Issue #146)
    pv2_voltage: float = 0.0          # V
    pv2_current: float = 0.0          # A
    pv2_power: float = 0.0            # W
    pv2_energy_today: float = 0.0     # kWh (WIT per-MPPT energy tracking - Issue #146)
    pv3_voltage: float = 0.0          # V
    pv3_current: float = 0.0          # A
    pv3_power: float = 0.0            # W
    pv_total_power: float = 0.0       # W
    pv_energy_total: float = 0.0      # kWh (WIT total PV lifetime energy - Issue #146)
    
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
    system_output_power: float = 0.0  # W (total system output per inverter)
    
    # Energy & Status
    energy_today: float = 0.0         # kWh
    energy_total: float = 0.0         # kWh
    energy_to_user_today: float = 0.0 # kWh
    energy_to_user_total: float = 0.0 # kWh
    energy_to_grid_today: float = 0.0 # kWh
    energy_to_grid_total: float = 0.0 # kWh
    load_energy_today: float = 0.0    # kWh
    load_energy_total: float = 0.0    # kWh

    # SPF Off-Grid AC Input (from grid/generator)
    grid_voltage: float = 0.0         # V (AC input voltage)
    grid_frequency: float = 0.0       # Hz (AC input frequency)
    ac_input_power: float = 0.0       # W (AC input power)
    ac_apparent_power: float = 0.0    # VA (AC apparent power)
    load_percentage: float = 0.0      # % (Load percentage)

    # SPF Generator Sensors
    generator_power: float = 0.0      # W
    generator_voltage: float = 0.0    # V
    generator_discharge_today: float = 0.0  # kWh
    generator_discharge_total: float = 0.0  # kWh

    # SPF/WIT AC Charge/Discharge Energy (from grid/generator)
    ac_charge_energy_today: float = 0.0     # kWh
    ac_charge_energy_total: float = 0.0     # kWh (WIT/SPF)
    ac_discharge_energy_today: float = 0.0  # kWh
    ac_discharge_energy_total: float = 0.0  # kWh

    # SPF Operational Discharge Energy
    op_discharge_energy_today: float = 0.0  # kWh
    op_discharge_energy_total: float = 0.0  # kWh

    # WIT Extra/Parallel Inverter Sensors (multi-inverter systems)
    extra_power_to_grid: float = 0.0  # W
    extra_energy_today: float = 0.0   # kWh
    extra_energy_total: float = 0.0   # kWh

    # Temperatures
    inverter_temp: float = 0.0        # °C
    ipm_temp: float = 0.0             # °C
    boost_temp: float = 0.0           # °C
    dcdc_temp: float = 0.0            # °C (SPF off-grid)
    buck1_temp: float = 0.0           # °C (SPF off-grid MPPT1)
    buck2_temp: float = 0.0           # °C (SPF off-grid MPPT2)

    # Fan Speeds (SPF off-grid)
    mppt_fan_speed: float = 0.0       # %
    inverter_fan_speed: float = 0.0   # %

    # Battery (storage/hybrid models)
    battery_voltage: float = 0.0      # V
    battery_current: float = 0.0      # A (signed: +discharge, -charge)
    battery_soc: float = 0.0          # %
    battery_temp: float = 0.0         # °C
    battery_soh: float = 0.0          # % (State of Health - WIT)
    battery_voltage_bms: float = 0.0  # V (BMS voltage reading - WIT)
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

    # Control registers (writable holding registers)
    export_limit_mode: int = 0        # 0=Disabled, 1=RS485, 2=RS232, 3=CT
    export_limit_power: int = 0       # 0-1000 (0-100.0%)
    active_power_rate: int = 100      # 0-100 (max output power %)

    # SPH/SPM Battery Control registers (1000+ range)
    priority_mode: int = 0            # 0=Load First, 1=Battery First, 2=Grid First
    discharge_power_rate: int = 0     # 0-100 (battery discharge power %)
    discharge_stopped_soc: int = 0    # 0-100 (stop discharge at SOC %)
    charge_power_rate: int = 0        # 0-100 (battery charge power %)
    charge_stopped_soc: int = 0       # 0-100 (stop charge at SOC %)
    ac_charge_enable: int = 0         # 0=Disabled, 1=Enabled

    # WIT VPP Remote Control (30000+ range)
    control_authority: int = 0        # 0=Disabled, 1=Enabled (VPP master enable)
    remote_power_control_enable: int = 0  # 0=Disabled, 1=Enabled (timed override enable)
    remote_power_control_charging_time: int = 0  # 0-1440 minutes (duration)
    remote_charge_and_discharge_power: int = 0   # -100 to +100% (negative=discharge, positive=charge)

    time_period_1_enable: int = 0     # 0=Disabled, 1=Enabled
    time_period_1_start: int = 0      # HHMM format (e.g., 530 = 05:30)
    time_period_1_end: int = 0        # HHMM format
    time_period_2_enable: int = 0     # 0=Disabled, 1=Enabled
    time_period_2_start: int = 0      # HHMM format
    time_period_2_end: int = 0        # HHMM format
    time_period_3_enable: int = 0     # 0=Disabled, 1=Enabled
    time_period_3_start: int = 0      # HHMM format
    time_period_3_end: int = 0        # HHMM format

    # SPF Off-Grid Control registers
    output_config: int = 0            # 0=SBU, 1=SOL, 2=UTI, 3=SUB
    charge_config: int = 0            # 0=CSO, 1=SNU, 2=OSO
    ac_input_mode: int = 0            # 0=APL, 1=UPS, 2=GEN
    battery_type: int = 0             # 0=AGM, 1=FLD, 2=USE, 3=Lithium, 4=USE2
    ac_charge_current: int = 0        # 0-800 (0-80A with scale 0.1)
    gen_charge_current: int = 0       # 0-800 (0-80A with scale 0.1)
    bat_low_to_uti: int = 0           # Battery-dependent: Non-Lithium 200-640 (20-64V), Lithium 5-100 (0.5-10%)
    ac_to_bat_volt: int = 0           # Battery-dependent: Non-Lithium 200-640 (20-64V), Lithium 5-100 (0.5-10%)

    # Device Info
    firmware_version: str = ""
    serial_number: str = ""

class GrowattModbus:
    """Growatt MIN series Modbus client"""
    
    def __init__(self, connection_type='tcp', host='192.168.1.100', port=502,
             device='/dev/ttyUSB0', baudrate=9600, slave_id=1,
             register_map='MIN_7000_10000TL_X', timeout=10, invert_battery_power=False):
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
            invert_battery_power: Invert battery power sign for inverters with opposite convention (default: False)
        """
        self.connection_type = connection_type
        self.slave_id = slave_id
        self.client: Optional[Union['ModbusTcpClient', 'ModbusSerialClient']] = None
        self.last_read_time = 0
        self.min_read_interval = 0.25  # 250ms minimum between reads (reduced from 1s, safe for serial and TCP)
        self._timeout = timeout
        self._invert_battery_power = invert_battery_power

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

        # Track failed optional register ranges to avoid repeated warnings
        # Format: set of (start_addr, count) tuples
        self._failed_optional_ranges = set()

        # WIT control rate limiting (v0.4.6) - track last write time per register
        # Prevents oscillation and unstable control behavior
        self._wit_control_last_write = {}  # {register: timestamp}
        self._wit_control_rate_limit_seconds = 30  # 30 second cooldown
        # WIT control registers that require rate limiting
        self._wit_control_registers = {
            201,    # active_power_rate (Legacy VPP)
            202,    # work_mode (Legacy VPP)
            203,    # export_limit_w
            30100,  # control_authority (VPP master enable)
            30407,  # remote_power_control_enable
            30408,  # remote_power_control_charging_time
            30409,  # remote_charge_and_discharge_power
        }

        # Adaptive polling: automatic backoff on errors
        self._consecutive_read_failures = 0
        self._read_failure_threshold = 5  # Back off after 5 consecutive failures
        self._default_min_read_interval = 0.25  # Fast polling default
        self._fallback_min_read_interval = 1.0  # Safe fallback on errors
        self._backed_off = False  # Track if we've backed off

        # Battery power scale auto-detection (WIT profile specific)
        self._battery_power_scale_override = None  # None = use profile default, 0.1 or 1.0 = detected scale
        self._battery_power_scale_samples = []  # Store validation samples
        self._battery_power_scale_validated = False  # Set to True once detection is complete

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
            # Check if already connected (prevents double-open and file descriptor leaks)
            if hasattr(self.client, 'is_socket_open'):
                try:
                    if self.client.is_socket_open():
                        logger.debug(f"[{self.register_map['name']}@{self.connection_id}] Already connected")
                        return True
                except Exception as e:
                    logger.debug(f"[{self.register_map['name']}@{self.connection_id}] is_socket_open() check failed: {e}")
                    # Continue to connect attempt below

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
        """Close connection and release resources (critical for preventing file descriptor leaks)"""
        if self.client:
            try:
                self.client.close()
                logger.debug(f"[{self.register_map['name']}@{self.connection_id}] Disconnected successfully")
            except Exception as e:
                # Log disconnect errors - these can indicate resource leaks
                logger.warning(f"[{self.register_map['name']}@{self.connection_id}] Error during disconnect: {e}")
                # Re-raise if it's a critical error (file descriptor issues)
                if "Too many open files" in str(e) or "errno 24" in str(e):
                    logger.error(f"[{self.register_map['name']}@{self.connection_id}] CRITICAL: File descriptor leak detected!")
                    raise
    
    def _track_read_success(self):
        """Track successful read and restore fast polling if we had backed off"""
        if self._consecutive_read_failures > 0:
            self._consecutive_read_failures = 0
            if self._backed_off:
                logger.info(
                    "[%s@%s] Communication restored - resuming fast polling (%.0fms intervals)",
                    self.register_map['name'],
                    self.connection_id,
                    self._default_min_read_interval * 1000
                )
                self.min_read_interval = self._default_min_read_interval
                self._backed_off = False

    def _track_read_failure(self):
        """Track read failure and back off to safe polling if threshold exceeded"""
        self._consecutive_read_failures += 1

        if not self._backed_off and self._consecutive_read_failures >= self._read_failure_threshold:
            logger.warning(
                "[%s@%s] %d consecutive read failures detected - backing off to safe polling interval (%.0fs) to prevent communication errors. "
                "This may indicate serial connection issues, low baudrate, or device processing limitations.",
                self.register_map['name'],
                self.connection_id,
                self._consecutive_read_failures,
                self._fallback_min_read_interval
            )
            self.min_read_interval = self._fallback_min_read_interval
            self._backed_off = True

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
                    self._track_read_failure()
                    return None
            elif hasattr(response, 'is_error') and callable(response.is_error):
                if response.is_error():
                    logger.warning(f"Modbus error reading input registers {start_address}-{start_address+count-1}: {response}")
                    self._track_read_failure()
                    return None

            if hasattr(response, 'registers'):
                logger.debug(f"Successfully read {len(response.registers)} registers from {start_address}")
                self._track_read_success()
                return response.registers

            logger.warning(f"Unknown response type: {type(response)}, response: {response}")
            self._track_read_failure()
            return None

        except Exception as e:
            logger.debug(f"Exception reading input registers: {e}")
            self._track_read_failure()
            return None
    
    def read_holding_registers(self, start_address: int, count: int) -> Optional[list]:
        """Read holding registers with error handling (no unit/slave, no positional count)."""
        self._enforce_read_interval()
        try:
            response = self.client.read_holding_registers(address=start_address, count=count)
            if hasattr(response, "isError") and callable(response.isError) and response.isError():
                logger.debug("Modbus error reading holding registers %d-%d: %r", start_address, start_address + count - 1, response)
                self._track_read_failure()
                return None
            if hasattr(response, "registers"):
                self._track_read_success()
                return response.registers
            logger.debug("Unexpected response type from read_holding_registers(%d, %d): %r", start_address, count, response)
            self._track_read_failure()
            return None
        except Exception as e:
            logger.debug("Exception reading holding registers %d-%d: %s", start_address, start_address + count - 1, e)
            self._track_read_failure()
            return None

    def _detect_battery_power_scale(self, voltage: float, current: float, power_register_value: int) -> Optional[float]:
        """
        Auto-detect correct battery power scale using V×I validation.

        WIT inverters have firmware variants - some use 0.1W scale (VPP spec), some use 1.0W.
        This method validates which scale is correct by comparing V×I with register reading.

        Args:
            voltage: Battery voltage in volts
            current: Battery current in amps (absolute value)
            power_register_value: Raw 32-bit power register value

        Returns:
            Detected scale (0.1 or 1.0), or None if detection uncertain
        """
        # Skip detection if already validated
        if self._battery_power_scale_validated:
            return self._battery_power_scale_override

        # Calculate expected power from V×I
        expected_power = abs(voltage * current)

        # Skip detection if power is too small (avoid noise/measurement errors)
        if expected_power < 50:  # Less than 50W
            return None

        # Test both possible scales
        power_with_0_1_scale = abs(power_register_value) * 0.1
        power_with_1_0_scale = abs(power_register_value) * 1.0

        # Calculate relative errors
        error_0_1 = abs(power_with_0_1_scale - expected_power) / expected_power if expected_power > 0 else 1.0
        error_1_0 = abs(power_with_1_0_scale - expected_power) / expected_power if expected_power > 0 else 1.0

        # Determine which scale is better (allow 20% tolerance for measurement variation)
        detected_scale = None
        if error_0_1 < 0.20 and error_0_1 < error_1_0:
            detected_scale = 0.1
        elif error_1_0 < 0.20 and error_1_0 < error_0_1:
            detected_scale = 1.0

        # Store sample for validation
        if detected_scale is not None:
            self._battery_power_scale_samples.append(detected_scale)

            # Validate after collecting 3 consistent samples
            if len(self._battery_power_scale_samples) >= 3:
                # Check if samples are consistent
                if all(s == detected_scale for s in self._battery_power_scale_samples[-3:]):
                    self._battery_power_scale_override = detected_scale
                    self._battery_power_scale_validated = True
                    logger.info(
                        f"WIT Battery Power Scale Auto-Detected: {detected_scale}W "
                        f"(V={voltage:.1f}V, I={current:.1f}A, Expected={expected_power:.0f}W, "
                        f"With 0.1={power_with_0_1_scale:.0f}W, With 1.0={power_with_1_0_scale:.0f}W)"
                    )
                    return detected_scale

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

            # WIT Battery Power Scale Override (auto-detected if needed)
            reg_name = reg_info.get('name') or pair_info.get('name')
            if reg_name in ('battery_power_low', 'battery_power') and self._battery_power_scale_override is not None:
                # Use detected scale instead of profile default
                combined_scale = self._battery_power_scale_override
                logger.debug(f"Applying detected battery power scale override: {combined_scale}W")

            return combined * combined_scale
        
        else:
            # Single register, apply its scale
            scale = reg_info.get('scale', 1)

            # Handle signed 16-bit values if specified
            if reg_info.get('signed'):
                if raw_value > 0x7FFF:  # If sign bit is set in 16-bit value
                    raw_value = raw_value - 0x10000  # Convert to negative

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

        logger.debug(f"[{self.register_map['name']}] Register range: {min_addr}-{max_addr} ({len(addresses)} registers defined)")

        # Clear cache
        self._register_cache = {}

        # Determine which ranges we need to read
        # Check if we have registers in different ranges
        has_base_range = any(0 <= addr < 1000 for addr in addresses)
        has_storage_range = any(1000 <= addr < 2000 for addr in addresses)
        has_3000_range = any(3000 <= addr < 4000 for addr in addresses)
        has_875_range = any(875 <= addr < 1000 for addr in addresses)
        has_8000_range = any(8000 <= addr < 8200 for addr in addresses)
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

        # Read business storage range (875-999) if needed - WIT/WIS models
        if has_875_range:
            addrs_875 = sorted([addr for addr in addresses if 875 <= addr < 1000])
            min_addr_875 = min(addrs_875)
            max_addr_875 = max(addrs_875)
            count_875 = (max_addr_875 - min_addr_875) + 1

            logger.debug(f"Reading 875 range ({min_addr_875}-{max_addr_875}, {count_875} registers)")
            if count_875 > 125:
                for chunk_start in range(min_addr_875, max_addr_875 + 1, 125):
                    chunk_count = min(125, max_addr_875 - chunk_start + 1)
                    registers = self.read_input_registers(chunk_start, chunk_count)
                    if registers is None:
                        logger.warning(f"Failed to read 875 block ({chunk_start}-{chunk_start+chunk_count-1})")
                    else:
                        for i, value in enumerate(registers):
                            self._register_cache[chunk_start + i] = value
            else:
                registers = self.read_input_registers(min_addr_875, count_875)
                if registers is None:
                    logger.warning("Failed to read business storage register block (875-999)")
                else:
                    for i, value in enumerate(registers):
                        self._register_cache[min_addr_875 + i] = value
        
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

        # Read 8000 range if needed - WIT/WIS battery/storage data
        if has_8000_range:
            addrs_8000 = sorted([addr for addr in addresses if 8000 <= addr < 8200])
            min_addr_8000 = min(addrs_8000)
            max_addr_8000 = max(addrs_8000)
            count_8000 = (max_addr_8000 - min_addr_8000) + 1

            is_wit_profile = 'WIT' in self.register_map['name']
            logger.debug(f"Reading 8000 range ({min_addr_8000}-{max_addr_8000}, {count_8000} registers)")
            if count_8000 > 125:
                for chunk_start in range(min_addr_8000, max_addr_8000 + 1, 125):
                    chunk_count = min(125, max_addr_8000 - chunk_start + 1)
                    registers = self.read_input_registers(chunk_start, chunk_count)
                    if registers is None:
                        log_level = "warning" if is_wit_profile else "debug"
                        logger.warning(f"Failed to read 8000 block ({chunk_start}-{chunk_start+chunk_count-1}) - will retry next poll")
                    else:
                        for i, value in enumerate(registers):
                            self._register_cache[chunk_start + i] = value
            else:
                registers = self.read_input_registers(min_addr_8000, count_8000)
                if registers is None:
                    logger.warning(f"Failed to read 8000 register block ({min_addr_8000}-{max_addr_8000}) - will retry next poll")
                else:
                    for i, value in enumerate(registers):
                        self._register_cache[min_addr_8000 + i] = value

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

                # Determine if this range is truly optional or critical
                # WIT profiles: 31200-31223 range contains CRITICAL battery data (no fallback)
                # MIN profiles: 31000+ ranges are optional VPP duplicates of 3000-range data
                is_wit_critical_range = (
                    'WIT' in self.register_map['name'] and
                    31200 <= min_addr_block <= 31224
                )

                # Check if this range already failed - skip silently if optional
                range_key = (min_addr_block, count_block)
                if not is_wit_critical_range and range_key in self._failed_optional_ranges:
                    logger.debug(f"Skipping known-failed optional VPP range ({min_addr_block}-{max_addr_block})")
                    continue

                logger.debug(f"Reading 31000 sub-range ({min_addr_block}-{max_addr_block}, {count_block} registers)")
                registers = self.read_input_registers(min_addr_block, count_block)
                if registers is None:
                    # Only mark as permanently failed if it's truly optional
                    if not is_wit_critical_range:
                        self._failed_optional_ranges.add(range_key)
                        logger.debug(f"Optional VPP range not supported ({min_addr_block}-{max_addr_block}) - will use 3000-range data instead")
                    else:
                        # Critical WIT battery range - keep trying, log warning
                        logger.warning(f"Failed to read critical WIT battery range ({min_addr_block}-{max_addr_block}) - will retry next poll")
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

            # PV Energy (WIT per-MPPT tracking - Issue #146)
            # These registers track DC input from solar panels only (not total system output)
            pv1_energy_today_addr = self._find_register_by_name('pv1_energy_today_low')
            if pv1_energy_today_addr:
                data.pv1_energy_today = self._get_register_value(pv1_energy_today_addr) or 0.0
                logger.debug(f"[{self.register_map['name']}] PV1 energy today from reg {pv1_energy_today_addr}: {data.pv1_energy_today} kWh")

            pv2_energy_today_addr = self._find_register_by_name('pv2_energy_today_low')
            if pv2_energy_today_addr:
                data.pv2_energy_today = self._get_register_value(pv2_energy_today_addr) or 0.0
                logger.debug(f"[{self.register_map['name']}] PV2 energy today from reg {pv2_energy_today_addr}: {data.pv2_energy_today} kWh")

            pv_energy_total_addr = self._find_register_by_name('pv_energy_total_low')
            if pv_energy_total_addr:
                data.pv_energy_total = self._get_register_value(pv_energy_total_addr) or 0.0
                logger.debug(f"[{self.register_map['name']}] PV energy total from reg {pv_energy_total_addr}: {data.pv_energy_total} kWh")

            # AC Output (generic - will use Phase R via alias for 3-phase)
            ac_voltage_addr = self._find_register_by_name('ac_voltage')
            ac_current_addr = self._find_register_by_name('ac_current')
            ac_power_addr = self._find_register_by_name('ac_power_low')
            if not ac_power_addr:
                # SPF off-grid models use 'load_power_low' instead
                ac_power_addr = self._find_register_by_name('load_power_low')
            ac_freq_addr = self._find_register_by_name('ac_frequency')

            if ac_voltage_addr:
                data.ac_voltage = self._get_register_value(ac_voltage_addr) or 0.0
            if ac_current_addr:
                data.ac_current = self._get_register_value(ac_current_addr) or 0.0
            if ac_power_addr:
                data.ac_power = self._get_register_value(ac_power_addr) or 0.0
                logger.debug(f"AC Power from reg {ac_power_addr}: {data.ac_power}W")
            if ac_freq_addr:
                data.ac_frequency = self._get_register_value(ac_freq_addr) or 0.0

            # AC Apparent Power (SPF Off-Grid, some other models)
            ac_apparent_power_addr = self._find_register_by_name('ac_apparent_power_low')
            if ac_apparent_power_addr:
                data.ac_apparent_power = self._get_register_value(ac_apparent_power_addr) or 0.0
                logger.debug(f"AC Apparent Power from reg {ac_apparent_power_addr}: {data.ac_apparent_power} VA")

            # Load Percentage (SPF Off-Grid)
            load_percentage_addr = self._find_register_by_name('load_percentage')
            if load_percentage_addr:
                data.load_percentage = self._get_register_value(load_percentage_addr) or 0.0
                logger.debug(f"Load Percentage from reg {load_percentage_addr}: {data.load_percentage}%")

            # Grid/AC Input (SPF Off-Grid, other models)
            grid_voltage_addr = self._find_register_by_name('grid_voltage')
            grid_frequency_addr = self._find_register_by_name('grid_frequency')
            ac_input_power_low_addr = self._find_register_by_name('ac_input_power_low')
            if grid_voltage_addr:
                data.grid_voltage = self._get_register_value(grid_voltage_addr) or 0.0
                logger.debug(f"Grid voltage from reg {grid_voltage_addr}: {data.grid_voltage} V (raw cache: {self._register_cache.get(grid_voltage_addr)})")
            else:
                logger.debug("Grid voltage register not found in profile")
            if grid_frequency_addr:
                data.grid_frequency = self._get_register_value(grid_frequency_addr) or 0.0
                logger.debug(f"Grid frequency from reg {grid_frequency_addr}: {data.grid_frequency} Hz (raw cache: {self._register_cache.get(grid_frequency_addr)})")
            else:
                logger.debug("Grid frequency register not found in profile")
            if ac_input_power_low_addr:
                data.ac_input_power = self._get_register_value(ac_input_power_low_addr) or 0.0
                logger.debug(f"AC input power from reg {ac_input_power_low_addr}: {data.ac_input_power} W")
            else:
                logger.debug("AC input power register not found in profile")

            # Generator Sensors (SPF Off-Grid with generator input)
            generator_power_addr = self._find_register_by_name('generator_power')
            generator_voltage_addr = self._find_register_by_name('generator_voltage')
            generator_discharge_today_low_addr = self._find_register_by_name('generator_discharge_today_low')
            generator_discharge_total_low_addr = self._find_register_by_name('generator_discharge_total_low')
            if generator_power_addr:
                data.generator_power = self._get_register_value(generator_power_addr) or 0.0
                logger.debug(f"Generator power from reg {generator_power_addr}: {data.generator_power} W (raw cache: {self._register_cache.get(generator_power_addr)})")
            else:
                logger.debug("Generator power register not found in profile")
            if generator_voltage_addr:
                data.generator_voltage = self._get_register_value(generator_voltage_addr) or 0.0
                logger.debug(f"Generator voltage from reg {generator_voltage_addr}: {data.generator_voltage} V (raw cache: {self._register_cache.get(generator_voltage_addr)})")
            else:
                logger.debug("Generator voltage register not found in profile")
            if generator_discharge_today_low_addr:
                data.generator_discharge_today = self._get_register_value(generator_discharge_today_low_addr) or 0.0
                logger.debug(f"Generator discharge today from reg {generator_discharge_today_low_addr}: {data.generator_discharge_today} kWh")
            else:
                logger.debug("Generator discharge today register not found in profile")
            if generator_discharge_total_low_addr:
                data.generator_discharge_total = self._get_register_value(generator_discharge_total_low_addr) or 0.0
                logger.debug(f"Generator discharge total from reg {generator_discharge_total_low_addr}: {data.generator_discharge_total} kWh")
            else:
                logger.debug("Generator discharge total register not found in profile")

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
            
            # System output power (total per inverter)
            system_output_addr = self._find_register_by_name('system_output_power_low')
            if system_output_addr:
                data.system_output_power = self._get_register_value(system_output_addr) or 0.0

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
            # For WIT with per-MPPT tracking: use sum of PV1+PV2 energy for accurate solar production
            # Registers 53-54 show total system AC output (PV+battery), not PV-only (Issue #146)
            if data.pv1_energy_today > 0 or data.pv2_energy_today > 0:
                # WIT with per-MPPT energy: sum PV inputs for true solar production
                data.energy_today = data.pv1_energy_today + data.pv2_energy_today
                logger.debug(f"[{self.register_map['name']}@{self.connection_id}] Energy today calculated from PV MPPTs: PV1={data.pv1_energy_today} + PV2={data.pv2_energy_today} = {data.energy_today} kWh")
            else:
                # Fallback to total system output for other inverters
                energy_today_addr = self._find_register_by_name('energy_today_low')
                if energy_today_addr:
                    data.energy_today = self._get_register_value(energy_today_addr) or 0.0
                    logger.debug(f"[{self.register_map['name']}@{self.connection_id}] Energy today from reg {energy_today_addr}: {data.energy_today} kWh (cache: {self._register_cache.get(energy_today_addr)})")

            # Energy Total
            # For WIT: use total PV energy register if available (accurate DC input lifetime energy)
            if data.pv_energy_total > 0:
                # WIT with PV total energy register
                data.energy_total = data.pv_energy_total
                logger.debug(f"[{self.register_map['name']}@{self.connection_id}] Energy total from PV lifetime register: {data.energy_total} kWh")
            else:
                # Fallback to total system output for other inverters
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

            # SPF Off-Grid additional temperatures
            dcdc_temp_addr = self._find_register_by_name('dcdc_temp')
            buck1_temp_addr = self._find_register_by_name('buck1_temp')
            buck2_temp_addr = self._find_register_by_name('buck2_temp')

            if dcdc_temp_addr:
                data.dcdc_temp = self._get_register_value(dcdc_temp_addr) or 0.0
            if buck1_temp_addr:
                data.buck1_temp = self._get_register_value(buck1_temp_addr) or 0.0
            if buck2_temp_addr:
                data.buck2_temp = self._get_register_value(buck2_temp_addr) or 0.0

            # SPF Off-Grid fan speeds
            mppt_fan_speed_addr = self._find_register_by_name('mppt_fan_speed')
            inverter_fan_speed_addr = self._find_register_by_name('inverter_fan_speed')

            if mppt_fan_speed_addr:
                data.mppt_fan_speed = self._get_register_value(mppt_fan_speed_addr) or 0.0
            if inverter_fan_speed_addr:
                data.inverter_fan_speed = self._get_register_value(inverter_fan_speed_addr) or 0.0

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
            logger.debug(f"[WRITE] Request to write register {register} with value {value}")

            # WIT control rate limiting (v0.4.6) - prevent oscillation
            if register in self._wit_control_registers:
                import time
                current_time = time.time()
                last_write_time = self._wit_control_last_write.get(register, 0)
                time_since_last_write = current_time - last_write_time

                if time_since_last_write < self._wit_control_rate_limit_seconds:
                    remaining = self._wit_control_rate_limit_seconds - time_since_last_write
                    logger.warning(
                        f"[WIT CTRL] Rate limit: Register {register} write blocked. "
                        f"Must wait {remaining:.1f}s more (30s cooldown between WIT control writes). "
                        f"See docs/WIT_CONTROL_GUIDE.md for details."
                    )
                    return False

                # Update last write time
                self._wit_control_last_write[register] = current_time
                logger.debug(f"[WIT CTRL] Rate limit check passed for register {register}")

            if not self.client:
                logger.error("[WRITE] Cannot write register - client not initialized")
                return False

            # ---- Connection / socket check and reconnection ----------------------
            # Check if socket is open, attempt reconnect if not
            socket_is_open = False

            if hasattr(self.client, 'is_socket_open'):
                try:
                    socket_is_open = self.client.is_socket_open()
                    logger.debug(f"[WRITE] is_socket_open() returned: {socket_is_open}")

                    if not socket_is_open:
                        logger.warning("[WRITE] Socket not open, attempting reconnect...")
                        if not self.connect():
                            logger.error("[WRITE] Reconnect failed - not connected")
                            return False
                        logger.info("[WRITE] Reconnect successful, proceeding with write")
                        socket_is_open = True

                except Exception as e:
                    logger.warning(f"[WRITE] is_socket_open() threw exception: {e}")
                    logger.warning("[WRITE] Attempting reconnect due to error...")
                    if not self.connect():
                        logger.error("[WRITE] Reconnect failed after exception")
                        return False
                    logger.info("[WRITE] Reconnect successful after exception")
                    socket_is_open = True
            else:
                # Client doesn't support is_socket_open(), try to reconnect to be safe
                logger.debug("[WRITE] Client has no is_socket_open(), attempting reconnect...")
                if not self.connect():
                    logger.error("[WRITE] Reconnect failed - cannot determine socket state")
                    return False
                logger.info("[WRITE] Reconnect successful (no is_socket_open available)")
                socket_is_open = True
            # -----------------------------------------------------------------------

            # ---- Perform actual write ---------------------------------------------
            logger.debug(f"[WRITE] Sending write_register({register}, {value}) to inverter")

            # Try different keyword arguments for pymodbus version compatibility
            result = None
            try:
                # Preferred for ModbusTcpClient / recent pymodbus
                result = self.client.write_register(address=register, value=value, unit=self.slave_id)
            except TypeError:
                try:
                    # Some versions use 'slave'
                    result = self.client.write_register(address=register, value=value, slave=self.slave_id)
                except TypeError:
                    try:
                        # Older/newer variants may accept 'device_id'
                        result = self.client.write_register(address=register, value=value, device_id=self.slave_id)
                    except TypeError:
                        # Fallback: positional args only
                        result = self.client.write_register(register, value)

            # Handle different pymodbus error APIs
            if result is None:
                logger.error('[WRITE] No response from write_register call')
                return False

            if hasattr(result, 'isError') and callable(getattr(result, 'isError')) and result.isError():
                logger.error(f"[WRITE] Inverter responded with error: {result}")
                return False

            logger.info(f"[WRITE] Successfully wrote value {value} → register {register}")

            # Check for WIT control conflicts after successful write (v0.4.6)
            if register in self._wit_control_registers:
                self._check_wit_control_conflicts(register, value)

            return True
            # -----------------------------------------------------------------------

        except Exception as e:
            logger.error(f"[WRITE] Exception writing register {register}: {e}")
            return False

    def _check_wit_control_conflicts(self, register: int, value: int) -> None:
        """
        Check for potential WIT control conflicts (v0.4.6 - Issue #143).

        Detects situations that may cause unstable control behavior:
        - Multiple VPP remote control registers active simultaneously
        - Conflicting control commands within short time windows
        - Potential TOU vs remote control conflicts

        Args:
            register: The register that was just written
            value: The value that was written
        """
        try:
            # Check for multiple active VPP remote controls
            active_controls = []

            # Check if remote power control is being enabled
            if register == 30407 and value == 1:
                active_controls.append("Remote Power Control (30407)")

                # Check if control authority is also enabled
                control_authority = self._register_cache.get(30100, 0)
                if control_authority == 1:
                    active_controls.append("Control Authority (30100)")

            # Check for legacy VPP controls being active
            if register == 202:  # work_mode
                if value > 0:  # 1=charge, 2=discharge
                    active_controls.append(f"Legacy Work Mode (202={value})")

            # Warn if multiple control mechanisms are active
            if len(active_controls) > 1:
                logger.warning(
                    f"[WIT CTRL] Multiple control mechanisms active simultaneously: {', '.join(active_controls)}. "
                    f"This may cause conflicts. See docs/WIT_CONTROL_GUIDE.md for recommended patterns."
                )

            # Detect potential TOU conflicts when enabling remote control
            if register == 30407 and value == 1:
                # Check if any TOU periods are enabled (registers 954, 957, 960, 963, 966, 969)
                tou_enabled_registers = [954, 957, 960, 963, 966, 969]
                tou_periods_active = False

                for tou_reg in tou_enabled_registers:
                    if tou_reg in self._register_cache:
                        # Bit 15 indicates if period is enabled
                        tou_value = self._register_cache[tou_reg]
                        if tou_value & 0x8000:  # Check bit 15
                            tou_periods_active = True
                            break

                if tou_periods_active:
                    logger.warning(
                        f"[WIT CTRL] Remote power control enabled while TOU periods are configured. "
                        f"TOU schedule may override remote commands during scheduled periods. "
                        f"Consider disabling TOU via inverter panel if full remote control is needed."
                    )

        except Exception as e:
            # Don't fail the write if conflict detection has issues
            logger.debug(f"[WIT CTRL] Conflict detection error (non-critical): {e}")

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
                logger.debug(f"[{self.register_map['name']}@{self.connection_id}] load_energy_today_low register not found (expected for off-grid models like SPF)")

            addr = self._find_register_by_name('load_energy_total_low')
            if addr:
                data.load_energy_total = self._get_register_value(addr) or 0.0
                logger.debug(f"[{self.register_map['name']}@{self.connection_id}] Load energy total from reg {addr}: {data.load_energy_total} kWh (cache: {self._register_cache.get(addr)})")

            # Operational discharge energy (SPF off-grid models)
            addr = self._find_register_by_name('op_discharge_energy_today_low')
            if addr:
                data.op_discharge_energy_today = self._get_register_value(addr) or 0.0
                logger.debug(f"[{self.register_map['name']}@{self.connection_id}] Operational discharge energy today from reg {addr}: {data.op_discharge_energy_today} kWh (cache: {self._register_cache.get(addr)})")

            addr = self._find_register_by_name('op_discharge_energy_total_low')
            if addr:
                data.op_discharge_energy_total = self._get_register_value(addr) or 0.0
                logger.debug(f"[{self.register_map['name']}@{self.connection_id}] Operational discharge energy total from reg {addr}: {data.op_discharge_energy_total} kWh (cache: {self._register_cache.get(addr)})")

            # AC Discharge Energy (SPF off-grid models - battery to load via inverter)
            addr = self._find_register_by_name('ac_discharge_energy_today_low')
            if addr:
                data.ac_discharge_energy_today = self._get_register_value(addr) or 0.0
                logger.debug(f"[{self.register_map['name']}@{self.connection_id}] AC discharge energy today from reg {addr}: {data.ac_discharge_energy_today} kWh (cache: {self._register_cache.get(addr)})")

            addr = self._find_register_by_name('ac_discharge_energy_total_low')
            if addr:
                data.ac_discharge_energy_total = self._get_register_value(addr) or 0.0
                logger.debug(f"[{self.register_map['name']}@{self.connection_id}] AC discharge energy total from reg {addr}: {data.ac_discharge_energy_total} kWh (cache: {self._register_cache.get(addr)})")

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
                # Fallback to single-register name (used by legacy/WIT maps)
                addr = self._find_register_by_name('battery_current')
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

            # Battery State of Health (WIT)
            addr = self._find_register_by_name('battery_soh')
            if addr:
                data.battery_soh = self._get_register_value(addr) or 0.0
                logger.debug(f"Battery SOH from reg {addr}: {data.battery_soh}%")

            # Battery Voltage BMS (WIT - more accurate than standard battery_voltage)
            addr = self._find_register_by_name('battery_voltage_bms')
            if addr:
                data.battery_voltage_bms = self._get_register_value(addr) or 0.0
                logger.debug(f"Battery voltage BMS from reg {addr}: {data.battery_voltage_bms}V")

            # Battery power (signed: positive=charging, negative=discharging)
            # Try new signed battery_power register first (MOD series @ 31126)
            addr = self._find_register_by_name('battery_power_low')
            if addr:
                raw_low = self._register_cache.get(addr, 0)
                pair_addr = self._find_register_by_name('battery_power_high')
                raw_high = self._register_cache.get(pair_addr, 0) if pair_addr else 0

                # WIT Battery Power Scale Auto-Detection (before applying scale)
                # Combine raw 32-bit value for detection
                combined_raw = (raw_high << 16) | raw_low
                if combined_raw > 0x7FFFFFFF:  # Handle signed
                    combined_raw = combined_raw - 0x100000000

                # Attempt scale detection if we have V and I data
                if data.battery_voltage > 0 and data.battery_current != 0:
                    detected_scale = self._detect_battery_power_scale(
                        data.battery_voltage,
                        abs(data.battery_current),
                        abs(combined_raw)
                    )

                battery_power = self._get_register_value(addr) or 0.0
                logger.debug(f"Battery power (signed): HIGH={raw_high} (reg {pair_addr}), LOW={raw_low} (reg {addr}) → {battery_power}W")

                # Apply inversion if configured (for inverters with opposite sign convention)
                if self._invert_battery_power:
                    battery_power = -battery_power
                    logger.debug(f"  → Inverted battery power: {battery_power}W (invert_battery_power=True)")

                # Split into charge/discharge based on sign
                # Convention: positive=charging, negative=discharging
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
                # These registers are absolute values, but may be swapped for opposite convention inverters
                addr = self._find_register_by_name('charge_power_low')
                if addr:
                    raw_low = self._register_cache.get(addr, 0)
                    pair_addr = self._find_register_by_name('charge_power_high')
                    raw_high = self._register_cache.get(pair_addr, 0) if pair_addr else 0
                    raw_charge_power = self._get_register_value(addr) or 0.0
                    logger.debug(f"Charge power (raw): HIGH={raw_high} (reg {pair_addr}), LOW={raw_low} (reg {addr}) → {raw_charge_power}W")

                    # Apply swapping if battery power is inverted (opposite convention)
                    if self._invert_battery_power:
                        # Opposite convention: "charge" register contains discharge, "discharge" contains charge
                        data.discharge_power = raw_charge_power
                        logger.debug(f"  → Swapped charge→discharge: {data.discharge_power}W (invert_battery_power=True)")
                    else:
                        data.charge_power = raw_charge_power
                elif data.battery_voltage > 0 and data.battery_current < 0:
                    # Fallback: Calculate from V×I when charging (negative current)
                    data.charge_power = data.battery_voltage * abs(data.battery_current)
                    logger.debug(f"Charge power (calculated): {data.battery_voltage}V × {abs(data.battery_current)}A = {data.charge_power}W")

                addr = self._find_register_by_name('discharge_power_low')
                if addr:
                    raw_low = self._register_cache.get(addr, 0)
                    pair_addr = self._find_register_by_name('discharge_power_high')
                    raw_high = self._register_cache.get(pair_addr, 0) if pair_addr else 0
                    raw_discharge_power = self._get_register_value(addr) or 0.0
                    logger.debug(f"Discharge power (raw): HIGH={raw_high} (reg {pair_addr}), LOW={raw_low} (reg {addr}) → {raw_discharge_power}W")

                    # Apply swapping if battery power is inverted (opposite convention)
                    if self._invert_battery_power:
                        # Opposite convention: "discharge" register contains charge, "charge" contains discharge
                        data.charge_power = raw_discharge_power
                        logger.debug(f"  → Swapped discharge→charge: {data.charge_power}W (invert_battery_power=True)")
                    else:
                        data.discharge_power = raw_discharge_power
                elif data.battery_voltage > 0 and data.battery_current > 0:
                    # Fallback: Calculate from V×I when discharging (positive current)
                    data.discharge_power = data.battery_voltage * data.battery_current
                    logger.debug(f"Discharge power (calculated): {data.battery_voltage}V × {data.battery_current}A = {data.discharge_power}W")
            
            # Charge energy today
            # Try both naming conventions: "charge_energy_today" and "battery_charge_today"
            addr = self._find_register_by_name('charge_energy_today_low')
            if not addr:
                addr = self._find_register_by_name('battery_charge_today_low')
            if addr:
                raw_low = self._register_cache.get(addr, 0)
                pair_addr = self._find_register_by_name('charge_energy_today_high')
                if not pair_addr:
                    pair_addr = self._find_register_by_name('battery_charge_today_high')
                raw_high = self._register_cache.get(pair_addr, 0) if pair_addr else 0
                data.charge_energy_today = self._get_register_value(addr) or 0.0
                # SPF uses charge_energy_* registers for AC charging - populate both fields
                data.ac_charge_energy_today = data.charge_energy_today
                logger.debug(f"Charge energy today: HIGH={raw_high} (reg {pair_addr}), LOW={raw_low} (reg {addr}) → {data.charge_energy_today} kWh (also populating ac_charge_energy_today for SPF)")

            # Discharge energy today
            # Try both naming conventions: "discharge_energy_today" and "battery_discharge_today"
            addr = self._find_register_by_name('discharge_energy_today_low')
            if not addr:
                addr = self._find_register_by_name('battery_discharge_today_low')
            if addr:
                raw_low = self._register_cache.get(addr, 0)
                pair_addr = self._find_register_by_name('discharge_energy_today_high')
                if not pair_addr:
                    pair_addr = self._find_register_by_name('battery_discharge_today_high')
                raw_high = self._register_cache.get(pair_addr, 0) if pair_addr else 0
                data.discharge_energy_today = self._get_register_value(addr) or 0.0
                logger.debug(f"Discharge energy today: HIGH={raw_high} (reg {pair_addr}), LOW={raw_low} (reg {addr}) → {data.discharge_energy_today} kWh")

            # Charge energy total
            # Try both naming conventions: "charge_energy_total" and "battery_charge_total"
            addr = self._find_register_by_name('charge_energy_total_low')
            if not addr:
                addr = self._find_register_by_name('battery_charge_total_low')
            if addr:
                raw_low = self._register_cache.get(addr, 0)
                pair_addr = self._find_register_by_name('charge_energy_total_high')
                if not pair_addr:
                    pair_addr = self._find_register_by_name('battery_charge_total_high')
                raw_high = self._register_cache.get(pair_addr, 0) if pair_addr else 0
                data.charge_energy_total = self._get_register_value(addr) or 0.0
                # SPF uses charge_energy_* registers for AC charging - populate both fields
                data.ac_charge_energy_total = data.charge_energy_total
                logger.debug(f"Charge energy total: HIGH={raw_high} (reg {pair_addr}), LOW={raw_low} (reg {addr}) → {data.charge_energy_total} kWh (also populating ac_charge_energy_total for SPF)")

            # Discharge energy total
            # Try both naming conventions: "discharge_energy_total" and "battery_discharge_total"
            addr = self._find_register_by_name('discharge_energy_total_low')
            if not addr:
                addr = self._find_register_by_name('battery_discharge_total_low')
            if addr:
                raw_low = self._register_cache.get(addr, 0)
                pair_addr = self._find_register_by_name('discharge_energy_total_high')
                if not pair_addr:
                    pair_addr = self._find_register_by_name('battery_discharge_total_high')
                raw_high = self._register_cache.get(pair_addr, 0) if pair_addr else 0
                data.discharge_energy_total = self._get_register_value(addr) or 0.0
                logger.debug(f"Discharge energy total: HIGH={raw_high} (reg {pair_addr}), LOW={raw_low} (reg {addr}) → {data.discharge_energy_total} kWh")

            # AC Charge Energy Today (WIT-specific - SPF populates this from charge_energy_today above)
            addr = self._find_register_by_name('ac_charge_energy_today_low')
            if addr:
                raw_low = self._register_cache.get(addr, 0)
                pair_addr = self._find_register_by_name('ac_charge_energy_today_high')
                raw_high = self._register_cache.get(pair_addr, 0) if pair_addr else 0
                data.ac_charge_energy_today = self._get_register_value(addr) or 0.0
                logger.debug(f"AC charge energy today: HIGH={raw_high} (reg {pair_addr}), LOW={raw_low} (reg {addr}) → {data.ac_charge_energy_today} kWh")

            # AC Charge Energy Total (WIT-specific - SPF populates this from charge_energy_total above)
            addr = self._find_register_by_name('ac_charge_energy_total_low')
            if addr:
                raw_low = self._register_cache.get(addr, 0)
                pair_addr = self._find_register_by_name('ac_charge_energy_total_high')
                raw_high = self._register_cache.get(pair_addr, 0) if pair_addr else 0
                data.ac_charge_energy_total = self._get_register_value(addr) or 0.0
                logger.debug(f"AC charge energy total: HIGH={raw_high} (reg {pair_addr}), LOW={raw_low} (reg {addr}) → {data.ac_charge_energy_total} kWh")

            if data.battery_voltage > 0:
                logger.debug(f"Battery summary: {data.battery_voltage}V, {data.battery_current}A, {data.battery_soc}%, {data.battery_temp}°C, Charge={data.charge_power}W, Discharge={data.discharge_power}W")

            # BMS Information (SPH HU and other models with BMS monitoring)
            # Registers 1082-1120 contain detailed battery management system data
            bms_attrs = [
                ('bms_status_old', 'BMS Status Old'),
                ('bms_status', 'BMS Status'),
                ('bms_error_old', 'BMS Error Old'),
                ('bms_error', 'BMS Error'),
                ('bms_max_current', 'BMS Max Current'),
                ('bms_gauge_rm', 'BMS Gauge RM'),
                ('bms_gauge_fcc', 'BMS Gauge FCC'),
                ('bms_fw_version', 'BMS FW Version'),
                ('bms_delta_volt', 'BMS Delta Volt'),
                ('bms_cycle_count', 'BMS Cycle Count'),
                ('bms_soh', 'Battery State of Health'),
                ('bms_constant_volt', 'BMS Constant Voltage'),
                ('bms_warn_info_old', 'BMS Warning Old'),
                ('bms_warn_info', 'BMS Warning'),
                ('bms_max_cell_volt', 'BMS Max Cell Voltage'),
                ('bms_min_cell_volt', 'BMS Min Cell Voltage'),
                ('bms_module_num', 'BMS Module Count'),
                ('bms_battery_count', 'BMS Battery Count'),
                ('bms_max_soc', 'BMS Max SOC'),
                ('bms_min_soc', 'BMS Min SOC'),
            ]

            bms_found = False
            for attr_name, friendly_name in bms_attrs:
                addr = self._find_register_by_name(attr_name)
                if addr:
                    value = self._get_register_value(addr)
                    if value is not None:
                        setattr(data, attr_name, value)
                        if not bms_found:
                            logger.debug(f"BMS data available - reading BMS attributes")
                            bms_found = True
                        logger.debug(f"  {friendly_name} from reg {addr}: {value}")

        except Exception as e:
            logger.debug(f"Battery data not available: {e}")

    def _read_device_info(self, data: GrowattData) -> None:
        """Read device info from holding registers"""

        # Get holding register map once so we can use it even if 0–19 read fails
        holding_map = self.register_map.get("holding_registers", {})

        # --- Device info (0–19) ---
        holding_regs = self.read_holding_registers(0, 20)
        if holding_regs is None:
            logger.debug("Could not read holding registers 0–19 for device info")
        else:
            try:
                # Firmware version at register 3
                if len(holding_regs) > 3 and 3 in holding_map:
                    fw_version = holding_regs[3]
                    data.firmware_version = f"{fw_version >> 8}.{fw_version & 0xFF}"

                # Serial number from registers 9-13
                if len(holding_regs) > 13:
                    serial_parts = []
                    for i in range(9, 14):
                        if i < len(holding_regs):
                            reg_val = holding_regs[i]
                            # Convert 16-bit register to 2 ASCII characters
                            if reg_val > 0:
                                char1 = (reg_val >> 8) & 0xFF
                                char2 = reg_val & 0xFF
                                if char1 > 0 and 32 <= char1 <= 126:
                                    serial_parts.append(chr(char1))
                                if char2 > 0 and 32 <= char2 <= 126:
                                    serial_parts.append(chr(char2))
                    data.serial_number = ''.join(serial_parts).rstrip('\x00')
            except Exception as e:
                logger.warning(f"Error reading device info: {e}")

        # --- Export control (122–123) --- ALWAYS ATTEMPTED
        if 122 in holding_map or 123 in holding_map:
            try:
                export_regs = self.read_holding_registers(122, 2)
                logger.debug("[EXPORT CTRL] Raw export_regs from 122–123: %r", export_regs)

                if export_regs is not None and len(export_regs) >= 2:
                    if 122 in holding_map:
                        data.export_limit_mode = int(export_regs[0])
                    if 123 in holding_map:
                        data.export_limit_power = int(export_regs[1])

                    logger.debug("[EXPORT CTRL] Read export control: mode=%s, power=%s",
                               data.export_limit_mode, data.export_limit_power)
            except Exception as e:
                logger.debug(f"Could not read export control registers: {e}")

        # --- Active Power Rate (3) --- Read if present in profile
        if 3 in holding_map:
            try:
                power_rate_regs = self.read_holding_registers(3, 1)
                logger.debug("[POWER CTRL] Raw active_power_rate from reg 3: %r", power_rate_regs)

                if power_rate_regs is not None and len(power_rate_regs) >= 1:
                    data.active_power_rate = int(power_rate_regs[0])
                    data.max_output_power_rate = data.active_power_rate  # Alias for number entity
                    logger.debug("[POWER CTRL] Read active_power_rate: %s%%", data.active_power_rate)
            except Exception as e:
                logger.debug(f"Could not read active_power_rate register: {e}")

        # --- SPF Off-Grid Controls --- Read if present in profile
        # Read registers 1, 2, 8 (output config, charge config, AC input mode)
        if any(reg in holding_map for reg in [1, 2, 8]):
            try:
                spf_ctrl_regs = self.read_holding_registers(1, 8)
                logger.debug("[SPF CTRL] Raw SPF control regs 1-8: %r", spf_ctrl_regs)

                if spf_ctrl_regs is not None and len(spf_ctrl_regs) >= 8:
                    if 1 in holding_map:
                        data.output_config = int(spf_ctrl_regs[0])
                    if 2 in holding_map:
                        data.charge_config = int(spf_ctrl_regs[1])
                    if 8 in holding_map:
                        data.ac_input_mode = int(spf_ctrl_regs[7])
                    logger.debug("[SPF CTRL] output_config=%s, charge_config=%s, ac_input_mode=%s",
                               data.output_config, data.charge_config, data.ac_input_mode)
            except Exception as e:
                logger.debug(f"Could not read SPF control registers 1-8: {e}")

        # Read battery configuration registers (37-39)
        if any(reg in holding_map for reg in [37, 38, 39]):
            try:
                battery_ctrl_regs = self.read_holding_registers(37, 3)
                logger.debug("[SPF CTRL] Raw battery ctrl regs 37-39: %r", battery_ctrl_regs)

                if battery_ctrl_regs is not None and len(battery_ctrl_regs) >= 3:
                    if 37 in holding_map:
                        data.bat_low_to_uti = int(battery_ctrl_regs[0])
                    if 38 in holding_map:
                        data.ac_charge_current = int(battery_ctrl_regs[1])
                    if 39 in holding_map:
                        data.battery_type = int(battery_ctrl_regs[2])
                    logger.debug("[SPF CTRL] bat_low_to_uti=%s, ac_charge_current=%s, battery_type=%s",
                               data.bat_low_to_uti, data.ac_charge_current, data.battery_type)
            except Exception as e:
                logger.debug(f"Could not read battery control registers 37-39: {e}")

        # Read generator charge current (83) and AC to battery voltage (95)
        if 83 in holding_map:
            try:
                gen_charge_regs = self.read_holding_registers(83, 1)
                logger.debug("[SPF CTRL] Raw gen_charge_current from reg 83: %r", gen_charge_regs)

                if gen_charge_regs is not None and len(gen_charge_regs) >= 1:
                    data.gen_charge_current = int(gen_charge_regs[0])
                    logger.debug("[SPF CTRL] gen_charge_current=%s A", data.gen_charge_current)
            except Exception as e:
                logger.debug(f"Could not read gen_charge_current register: {e}")

        if 95 in holding_map:
            try:
                ac_to_bat_regs = self.read_holding_registers(95, 1)
                logger.debug("[SPF CTRL] Raw ac_to_bat_volt from reg 95: %r", ac_to_bat_regs)

                if ac_to_bat_regs is not None and len(ac_to_bat_regs) >= 1:
                    data.ac_to_bat_volt = int(ac_to_bat_regs[0])
                    logger.debug("[SPF CTRL] ac_to_bat_volt=%s", data.ac_to_bat_volt)
            except Exception as e:
                logger.debug(f"Could not read ac_to_bat_volt register: {e}")

        # --- SPH/SPM Battery Control registers (1000+ range) ---
        # Priority Mode (1044 for SPH/SPH-TL3, 30476 for WIT)
        priority_addr = 1044 if 1044 in holding_map else (30476 if 30476 in holding_map else None)
        if priority_addr:
            try:
                priority_regs = self.read_holding_registers(priority_addr, 1)
                if priority_regs is not None and len(priority_regs) >= 1:
                    data.priority_mode = int(priority_regs[0])
                    profile_name = "WIT" if priority_addr == 30476 else "SPH"
                    logger.debug("[%s CTRL] priority_mode=%s", profile_name, data.priority_mode)
            except Exception as e:
                logger.debug(f"Could not read priority_mode register {priority_addr}: {e}")

        # Discharge Control (1070-1071)
        if any(reg in holding_map for reg in [1070, 1071]):
            try:
                discharge_regs = self.read_holding_registers(1070, 2)
                if discharge_regs is not None and len(discharge_regs) >= 2:
                    if 1070 in holding_map:
                        data.discharge_power_rate = int(discharge_regs[0])
                    if 1071 in holding_map:
                        data.discharge_stopped_soc = int(discharge_regs[1])
                    logger.debug("[SPH CTRL] discharge_power_rate=%s%%, discharge_stopped_soc=%s%%",
                               data.discharge_power_rate, data.discharge_stopped_soc)
            except Exception as e:
                logger.debug(f"Could not read discharge control registers: {e}")

        # Charge Control (1090-1092)
        if any(reg in holding_map for reg in [1090, 1091, 1092]):
            try:
                charge_regs = self.read_holding_registers(1090, 3)
                if charge_regs is not None and len(charge_regs) >= 3:
                    if 1090 in holding_map:
                        data.charge_power_rate = int(charge_regs[0])
                    if 1091 in holding_map:
                        data.charge_stopped_soc = int(charge_regs[1])
                    if 1092 in holding_map:
                        data.ac_charge_enable = int(charge_regs[2])
                    logger.debug("[SPH CTRL] charge_power_rate=%s%%, charge_stopped_soc=%s%%, ac_charge_enable=%s",
                               data.charge_power_rate, data.charge_stopped_soc, data.ac_charge_enable)
            except Exception as e:
                logger.debug(f"Could not read charge control registers: {e}")

        # Time Period Controls (1100-1108)
        if any(reg in holding_map for reg in range(1100, 1109)):
            try:
                time_period_regs = self.read_holding_registers(1100, 9)
                if time_period_regs is not None and len(time_period_regs) >= 9:
                    if 1100 in holding_map:
                        data.time_period_1_start = int(time_period_regs[0])
                    if 1101 in holding_map:
                        data.time_period_1_end = int(time_period_regs[1])
                    if 1102 in holding_map:
                        data.time_period_1_enable = int(time_period_regs[2])
                    if 1103 in holding_map:
                        data.time_period_2_start = int(time_period_regs[3])
                    if 1104 in holding_map:
                        data.time_period_2_end = int(time_period_regs[4])
                    if 1105 in holding_map:
                        data.time_period_2_enable = int(time_period_regs[5])
                    if 1106 in holding_map:
                        data.time_period_3_start = int(time_period_regs[6])
                    if 1107 in holding_map:
                        data.time_period_3_end = int(time_period_regs[7])
                    if 1108 in holding_map:
                        data.time_period_3_enable = int(time_period_regs[8])
                    logger.debug("[SPH CTRL] time_period_1: %s-%s (enabled=%s), time_period_2: %s-%s (enabled=%s), time_period_3: %s-%s (enabled=%s)",
                               data.time_period_1_start, data.time_period_1_end, data.time_period_1_enable,
                               data.time_period_2_start, data.time_period_2_end, data.time_period_2_enable,
                               data.time_period_3_start, data.time_period_3_end, data.time_period_3_enable)
            except Exception as e:
                logger.debug(f"Could not read time period control registers: {e}")

        # --- WIT VPP Remote Control registers (30000+ range) ---
        # Control Authority (30100)
        if 30100 in holding_map:
            try:
                vpp_ctrl_regs = self.read_holding_registers(30100, 1)
                if vpp_ctrl_regs is not None and len(vpp_ctrl_regs) >= 1:
                    data.control_authority = int(vpp_ctrl_regs[0])
                    logger.debug("[WIT VPP] control_authority=%s", data.control_authority)
            except Exception as e:
                logger.debug(f"Could not read VPP control_authority register 30100: {e}")

        # Remote Power Control (30407-30409)
        if any(reg in holding_map for reg in [30407, 30408, 30409]):
            try:
                vpp_power_regs = self.read_holding_registers(30407, 3)
                if vpp_power_regs is not None and len(vpp_power_regs) >= 3:
                    if 30407 in holding_map:
                        data.remote_power_control_enable = int(vpp_power_regs[0])
                    if 30408 in holding_map:
                        data.remote_power_control_charging_time = int(vpp_power_regs[1])
                    if 30409 in holding_map:
                        # Register 30409 is signed (-100 to +100)
                        raw_val = vpp_power_regs[2]
                        if raw_val > 32767:  # Handle signed 16-bit
                            raw_val = raw_val - 65536
                        data.remote_charge_and_discharge_power = int(raw_val)
                    logger.debug("[WIT VPP] remote_power_control_enable=%s, charging_time=%s min, charge_discharge_power=%s%%",
                               data.remote_power_control_enable, data.remote_power_control_charging_time, data.remote_charge_and_discharge_power)
            except Exception as e:
                logger.debug(f"Could not read VPP remote power control registers 30407-30409: {e}")

    def get_status_text(self, status_code: int) -> str:
        """Convert status code to human readable text"""
        status_info = STATUS_CODES.get(status_code, {'name': f'Unknown ({status_code})', 'desc': 'Unknown status code'})
        return status_info['name']
