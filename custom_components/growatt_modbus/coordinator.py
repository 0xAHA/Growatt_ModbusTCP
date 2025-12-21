"""Data update coordinator for Growatt Modbus Integration."""
import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.event import async_track_time_change

from .const import (
    DOMAIN,
    CONF_SLAVE_ID,
    CONF_REGISTER_MAP,
    CONF_CONNECTION_TYPE,
    CONF_DEVICE_PATH,
    CONF_BAUDRATE,
    CONF_DEVICE_STRUCTURE_VERSION,
    CURRENT_DEVICE_STRUCTURE_VERSION,
    get_sensor_type,
    SENSOR_OFFLINE_BEHAVIOR,
    DEVICE_TYPE_INVERTER,
    DEVICE_TYPE_SOLAR,
    DEVICE_TYPE_GRID,
    DEVICE_TYPE_LOAD,
    DEVICE_TYPE_BATTERY,
)

from .const import REGISTER_MAPS

from .growatt_modbus import GrowattModbus, GrowattData

_LOGGER = logging.getLogger(__name__)

def test_connection(config: dict) -> dict:
    """Test the connection to the Growatt inverter (TCP or Serial)."""
    try:
        # Migrate old register map names
        register_map = config.get(CONF_REGISTER_MAP, 'MIN_7000_10000TL_X')

        # Ensure register map exists
        if register_map not in REGISTER_MAPS:
            register_map = 'MIN_7000_10000TL_X'

        # Get connection type (default to tcp for backward compatibility)
        connection_type = config.get(CONF_CONNECTION_TYPE, "tcp")

        # Create the modbus client based on connection type
        if connection_type == "tcp":
            client = GrowattModbus(
                connection_type="tcp",
                host=config[CONF_HOST],
                port=config[CONF_PORT],
                slave_id=config[CONF_SLAVE_ID],
                register_map=register_map,
                timeout=config.get("timeout", 10)
            )
        else:  # serial
            client = GrowattModbus(
                connection_type="serial",
                device=config[CONF_DEVICE_PATH],
                baudrate=config[CONF_BAUDRATE],
                slave_id=config[CONF_SLAVE_ID],
                register_map=register_map,
                timeout=config.get("timeout", 10)
            )

        # Test connection
        if client.connect():
            # Try to read some basic data
            data = client.read_all_data()
            client.disconnect()

            if data is not None:
                return {
                    "success": True,
                    "serial_number": data.serial_number,
                    "firmware_version": data.firmware_version,
                    "register_map": register_map
                }
            else:
                return {"success": False, "error": "Could not read data from inverter"}
        else:
            return {"success": False, "error": "Could not connect to inverter"}

    except Exception as err:
        _LOGGER.exception("Connection test failed")
        return {"success": False, "error": str(err)}


class GrowattModbusCoordinator(DataUpdateCoordinator[GrowattData]):
    """Growatt Modbus data update coordinator."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.entry = entry
        self.config = entry.data
        self.hass = hass

        self._slave_id = entry.data[CONF_SLAVE_ID]
        
        # Device identification (populated during first refresh)
        self._serial_number = None
        self._firmware_version = None
        self._inverter_type = None
        self._model_name = None
        self._protocol_version = None  # VPP Protocol version (from register 30099)

        # Handle register map key (might be dict or string due to old bug)
        raw_register_map = entry.data.get(CONF_REGISTER_MAP, 'MIN_7000_10000TL_X')
        
        if isinstance(raw_register_map, dict):
            # Config stored entire dict instead of key name - use fallback
            _LOGGER.warning("Config contains register map dict instead of name, using fallback")
            self._register_map_key = "MIN_7000_10000TL_X"  # Your inverter model as fallback
            
            # Update config entry to store string key instead of dict
            new_data = {**entry.data, CONF_REGISTER_MAP: self._register_map_key}
            hass.config_entries.async_update_entry(entry, data=new_data)
            _LOGGER.debug(f"Fixed config entry to store register map key: {self._register_map_key}")
        else:
            # Normal case - it's a string key, use it directly
            self._register_map_key = raw_register_map
        
        # Verify the key exists in REGISTER_MAPS
        if self._register_map_key not in REGISTER_MAPS:
            _LOGGER.error(f"Unknown register map '{self._register_map_key}', available: {list(REGISTER_MAPS.keys())}")
            # Try fallback
            self._register_map_key = "MIN_7000_10000TL_X"
            _LOGGER.warning(f"Using fallback register map: {self._register_map_key}")

        self.last_successful_update = None
        self.last_update_success_time = None  # For timezone-aware timestamp sensor
        
        # Offline state management
        self._last_successful_read = None
        self._previous_day_totals = {}
        self._current_date = datetime.now().date()
        self._inverter_online = False

        # Adaptive polling for offline inverters
        self._consecutive_failures = 0
        self._failure_threshold = 5  # After 5 failures, slow down polling
        scan_interval = entry.options.get("scan_interval", 30)
        self._normal_update_interval = timedelta(seconds=scan_interval)
        self._offline_update_interval = timedelta(seconds=entry.options.get("offline_scan_interval", 300))  # 5 min default

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.data[CONF_NAME]}",
            update_interval=self._normal_update_interval,
        )
        
        # Initialize the Growatt client
        self._client = None
        self._initialize_client()
        
        # Set up midnight callback for daily total resets
        self._setup_midnight_callback()
    @property
    def modbus_client(self):
        """Expose the modbus client for write operations."""
        return self._client

    def _get_register_map(self) -> str:
        """Get register map with migration support."""
        register_map = self.config.get(CONF_REGISTER_MAP, 'MIN_7000_10000TL_X')
        
        # BUGFIX: Handle case where config stored the dict instead of the string name
        if isinstance(register_map, dict):
            _LOGGER.warning("Config contains register map dict instead of name, attempting to identify...")
            # Try to find which register map this is by comparing
            for map_name, map_data in REGISTER_MAPS.items():
                if map_data == register_map or map_data.get('name') == register_map.get('name'):
                    _LOGGER.debug("Identified register map as: %s", map_name)
                    register_map = map_name
                    break
            else:
                # Could not identify, use default
                _LOGGER.error("Could not identify register map dict, falling back to MIN_7000_10000TL_X")
                register_map = 'MIN_7000_10000TL_X'
        
        # Ensure we have a string at this point
        if not isinstance(register_map, str):
            _LOGGER.error("register_map is not a string (%s), using default", type(register_map))
            register_map = 'MIN_7000_10000TL_X'
        
        # Validate register map exists
        if register_map not in REGISTER_MAPS:
            _LOGGER.warning(
                "Unknown register map '%s', falling back to MIN_7000_10000TL_X",
                register_map
            )
            register_map = 'MIN_7000_10000TL_X'
        
        return register_map

    def _initialize_client(self):
        """Initialize the Growatt Modbus client (TCP or Serial)."""
        try:
            register_map = self._get_register_map()

            # Get timeout from options (default 10 seconds)
            timeout = self.entry.options.get("timeout", 10)

            # Get connection type (default to tcp for backward compatibility)
            connection_type = self.config.get(CONF_CONNECTION_TYPE, "tcp")

            # Create client based on connection type
            if connection_type == "tcp":
                self._client = GrowattModbus(
                    connection_type="tcp",
                    host=self.config[CONF_HOST],
                    port=self.config[CONF_PORT],
                    slave_id=self.config[CONF_SLAVE_ID],
                    register_map=register_map,
                    timeout=timeout
                )
                _LOGGER.debug("Initialized TCP Growatt client at %s:%s",
                             self.config[CONF_HOST], self.config[CONF_PORT])
            else:  # serial
                self._client = GrowattModbus(
                    connection_type="serial",
                    device=self.config[CONF_DEVICE_PATH],
                    baudrate=self.config[CONF_BAUDRATE],
                    slave_id=self.config[CONF_SLAVE_ID],
                    register_map=register_map,
                    timeout=timeout
                )
                _LOGGER.debug("Initialized Serial Growatt client at %s @ %s baud",
                             self.config[CONF_DEVICE_PATH], self.config[CONF_BAUDRATE])

            _LOGGER.debug("Using register map: %s", register_map)

        except Exception as err:
            _LOGGER.error("Failed to initialize Growatt client: %s", err)
            self._client = None

    def _setup_midnight_callback(self):
        """Set up callback to run at midnight for daily total resets."""
        async_track_time_change(
            self.hass,
            self._handle_midnight_reset,
            hour=0,
            minute=0,
            second=0
        )
        _LOGGER.debug("Midnight callback registered for daily total resets")

    async def _handle_midnight_reset(self, now=None):
        """Handle midnight reset of daily totals."""
        _LOGGER.info("Midnight reset triggered - storing previous day totals")
        
        if self.data is None:
            _LOGGER.debug("No data available for midnight reset")
            return
        
        # Store today's daily totals as "yesterday" before they reset
        self._previous_day_totals = {
            'energy_today': getattr(self.data, 'energy_today', 0),
            'energy_to_grid_today': getattr(self.data, 'energy_to_grid_today', 0),
            'load_energy_today': getattr(self.data, 'load_energy_today', 0),
            'energy_to_user_today': getattr(self.data, 'energy_to_user_today', 0),
        }
        
        # Update current date
        self._current_date = datetime.now().date()
        
        _LOGGER.debug("Previous day totals stored: %s", self._previous_day_totals)
        
        # If inverter is offline, zero out the daily totals now
        if not self._inverter_online and self.data is not None:
            _LOGGER.debug("Inverter offline at midnight - resetting daily totals to 0")
            # Create modified data with zeroed daily totals
            self.data.energy_today = 0
            self.data.energy_to_grid_today = 0
            self.data.load_energy_today = 0
            self.data.energy_to_user_today = 0
            
            # Trigger update to notify sensors
            self.async_set_updated_data(self.data)

    @property
    def device_name(self) -> str:
        """Return the device name."""
        return self.config[CONF_NAME]

    def get_sensor_value(self, sensor_key: str, raw_value: Any) -> Any:
        """
        Get sensor value with smart offline behavior.
        
        Args:
            sensor_key: The sensor identifier
            raw_value: The raw value from the data
            
        Returns:
            The value to use, considering online/offline state
        """
        if self._inverter_online:
            # Inverter is online, use raw value
            return raw_value
        
        # Inverter is offline - apply offline behavior
        sensor_type = get_sensor_type(sensor_key)
        offline_behavior = SENSOR_OFFLINE_BEHAVIOR.get(sensor_type)
        
        if offline_behavior == 0:
            # Power sensors go to 0
            return 0
        elif offline_behavior == 'retain':
            # Daily and lifetime totals retain last value
            return raw_value
        elif offline_behavior == None:
            # Diagnostic sensors go unavailable
            return None
        elif offline_behavior == 'offline':
            # Status sensors show offline
            return 'offline'
        
        return raw_value

    @property
    def is_online(self) -> bool:
        """Return whether the inverter is currently online."""
        return self._inverter_online

    async def _async_update_data(self) -> GrowattData:
        """Fetch data from the Growatt inverter."""
        if self._client is None:
            raise UpdateFailed("Growatt client not initialized")

        try:
            # Run the blocking operations in executor
            data = await self.hass.async_add_executor_job(self._fetch_data)

            if data is None:
                # Inverter not responding (probably night time or powered off)
                self._inverter_online = False
                self._consecutive_failures += 1

                # Adaptive polling: slow down after repeated failures
                if self._consecutive_failures == self._failure_threshold:
                    _LOGGER.info(
                        "Inverter offline for %d consecutive polls - reducing poll frequency to %s",
                        self._failure_threshold,
                        self._offline_update_interval
                    )
                    self.update_interval = self._offline_update_interval
                elif self._consecutive_failures > self._failure_threshold:
                    # Already in slow mode, just log occasionally
                    if self._consecutive_failures % 10 == 0:  # Log every 10th failure
                        _LOGGER.debug(
                            "Inverter still offline (%d consecutive failures) - continuing slow polling",
                            self._consecutive_failures
                        )

                if self.data is not None:
                    _LOGGER.debug("Inverter offline - applying smart offline behavior")

                    # Check if we crossed midnight while offline
                    current_date = datetime.now().date()
                    if current_date > self._current_date:
                        _LOGGER.debug("Date changed while inverter offline - resetting daily totals")
                        # Reset daily totals to 0
                        self.data.energy_today = 0
                        self.data.energy_to_grid_today = 0
                        self.data.load_energy_today = 0
                        self.data.energy_to_user_today = 0
                        self._current_date = current_date

                    # Return existing data (sensors will apply offline behavior via get_sensor_value)
                    return self.data
                else:
                    # First connection attempt failed
                    raise UpdateFailed("Failed to read data from inverter")

            # Inverter is responding!
            was_offline = not self._inverter_online
            self._inverter_online = True

            # Reset failure counter and restore normal polling if we were in slow mode
            if self._consecutive_failures >= self._failure_threshold:
                _LOGGER.info(
                    "Inverter back online after %d failures - restoring normal poll frequency to %s",
                    self._consecutive_failures,
                    self._normal_update_interval
                )
                self.update_interval = self._normal_update_interval
            self._consecutive_failures = 0

            # Update successful - record timestamp (timezone-aware)
            from datetime import timezone as tz
            self.last_successful_update = datetime.now()
            self.last_update_success_time = datetime.now(tz.utc)
            self._last_successful_read = datetime.now()

            # Check for date transition (inverter came back online on new day)
            current_date = datetime.now().date()
            if was_offline and current_date > self._current_date:
                _LOGGER.debug("Inverter back online after date change - daily totals already reset by inverter")
                self._current_date = current_date
                # Inverter's daily totals are already at new day values (small amounts from morning production)

            return data

        except Exception as err:
            _LOGGER.error("Error fetching data from Growatt inverter: %s", err)
            self._inverter_online = False
            self._consecutive_failures += 1

            # Adaptive polling: slow down after repeated failures
            if self._consecutive_failures == self._failure_threshold:
                _LOGGER.info(
                    "Inverter errors for %d consecutive polls - reducing poll frequency to %s",
                    self._failure_threshold,
                    self._offline_update_interval
                )
                self.update_interval = self._offline_update_interval

            # Keep last data if available
            if self.data is not None:
                _LOGGER.debug("Error fetching data, keeping last known data with offline behavior")
                return self.data
            raise UpdateFailed(f"Error communicating with inverter: {err}")

    def _fetch_data(self) -> GrowattData | None:
        """Fetch data from the inverter (runs in executor)."""
        max_retries = 3
        retry_delay = 3  # seconds - increased from 2
        
        for attempt in range(max_retries):
            try:
                if not self._client.connect():
                    _LOGGER.warning(
                        "Failed to connect to Growatt inverter (attempt %d/%d)", 
                        attempt + 1, max_retries
                    )
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)  # constant delay, not exponential
                        continue
                    _LOGGER.error("All connection attempts failed")
                    return None
                    
                data = self._client.read_all_data()
                if data is not None:  # Success!
                    self._client.disconnect()
                    return data

                # Read failed - disconnect before retrying to avoid stale connections
                _LOGGER.warning("Read returned None (attempt %d/%d)", attempt + 1, max_retries)
                try:
                    self._client.disconnect()
                except:
                    pass
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                    
            except Exception as err:
                _LOGGER.warning(
                    "Error during data fetch (attempt %d/%d): %s", 
                    attempt + 1, max_retries, err
                )
                if self._client:
                    try:
                        self._client.disconnect()
                    except:
                        pass
                
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    _LOGGER.error("All fetch attempts failed after %d retries", max_retries)
                    return None
        
        # Final disconnect if we get here
        try:
            self._client.disconnect()
        except:
            pass
        return None

    async def async_config_entry_first_refresh(self) -> None:
        """Perform first refresh and handle setup errors."""
        try:
            # Read device identification before first data refresh
            await self.hass.async_add_executor_job(self._read_device_identification)
            
            await super().async_config_entry_first_refresh()
        except UpdateFailed as err:
            _LOGGER.error("Initial setup failed: %s", err)
            raise
    
    def _read_device_identification(self):
        """Read device identification info (serial, firmware, inverter type)."""
        try:
            if not self._client:
                _LOGGER.warning("Cannot read device ID - client not initialized")
                return
            
            profile_key = self._register_map_key
            profile = REGISTER_MAPS.get(profile_key, {})
            
            # Determine which serial number registers to use
            # TL-X and TL-XH models use 3000-3015, others use 23-27
            is_tl_x_model = 'tl_x' in profile_key or 'tl_xh' in profile_key
            
            # Read serial number
            try:
                if is_tl_x_model:
                    # TL-X/TL-XH: registers 3000-3015 (30 characters)
                    result = self._client.client.read_holding_registers(address=3000, count=15, device_id=self._slave_id)
                else:
                    # Standard: registers 23-27 (10 characters)
                    result = self._client.client.read_holding_registers(address=23, count=5, device_id=self._slave_id)
                
                if not result.isError():
                    self._serial_number = self._registers_to_ascii(result.registers)
                    _LOGGER.debug(f"Read serial number: {self._serial_number}")
            except Exception as e:
                _LOGGER.debug(f"Could not read serial number: {e}")
            
            # Read firmware version (registers 9-11)
            try:
                result = self._client.client.read_holding_registers(address=9, count=3, device_id=self._slave_id)
                if not result.isError():
                    self._firmware_version = self._registers_to_ascii(result.registers)
                    _LOGGER.debug(f"Read firmware version: {self._firmware_version}")
            except Exception as e:
                _LOGGER.debug(f"Could not read firmware version: {e}")
            
            # Read inverter type (registers 125-132)
            try:
                result = self._client.client.read_holding_registers(address=125, count=8, device_id=self._slave_id)
                if not result.isError():
                    self._inverter_type = self._registers_to_ascii(result.registers)
                    _LOGGER.debug(f"Read inverter type: {self._inverter_type}")

                    # Parse model name from inverter type
                    self._model_name = self._parse_model_name(self._inverter_type, profile)
            except Exception as e:
                _LOGGER.debug(f"Could not read inverter type: {e}")
                # Fallback to profile name
                self._model_name = profile.get("name", "Unknown Model")

            # Read Protocol version (register 30099)
            # If readable, shows actual protocol version (e.g., 2.01, 2.02, etc.)
            try:
                result = self._client.client.read_holding_registers(address=30099, count=1, device_id=self._slave_id)
                if not result.isError() and len(result.registers) > 0:
                    version_value = result.registers[0]
                    if version_value > 0:
                        # Format as version string (e.g., 201 -> "Protocol 2.01", 202 -> "Protocol 2.02")
                        major = version_value // 100
                        minor = version_value % 100
                        self._protocol_version = f"Protocol {major}.{minor:02d}"
                        _LOGGER.info(f"Detected protocol version: {self._protocol_version} (register 30099 = {version_value})")
                    else:
                        self._protocol_version = "Protocol Legacy"
                        _LOGGER.info("Protocol version register returned 0, using Protocol Legacy")
                else:
                    # Register not available - likely legacy protocol
                    self._protocol_version = "Protocol Legacy"
                    _LOGGER.debug("Could not read register 30099, assuming Protocol Legacy")
            except Exception as e:
                _LOGGER.debug(f"Could not read protocol version (30099): {e}")
                self._protocol_version = "Protocol Legacy"

        except Exception as e:
            _LOGGER.error(f"Error reading device identification: {e}")

    def _registers_to_ascii(self, registers):
        """Convert list of 16-bit registers to ASCII string."""
        ascii_bytes = []
        for reg in registers:
            high_byte = (reg >> 8) & 0xFF
            low_byte = reg & 0xFF
            ascii_bytes.extend([high_byte, low_byte])
        
        return bytes(ascii_bytes).decode('ascii', errors='ignore').strip('\x00').strip()

    def _parse_model_name(self, inverter_type: str, profile: dict) -> str:
        """
        Parse inverter type string to create proper model name.
        
        Examples:
        - "PV  10000" + MIN profile → "MIN-10000TL-X"
        - "PV  6000" + SPH profile → "SPH-6000"
        """
        if not inverter_type:
            return profile.get("name", "Unknown Model")
        
        # Extract capacity (power rating) from inverter type
        import re
        capacity_match = re.search(r'(\d+)', inverter_type)
        
        if not capacity_match:
            return profile.get("name", "Unknown Model")
        
        capacity = capacity_match.group(1)
        profile_name = profile.get("name", "")
        
        # Build model name based on series
        if "MIN" in profile_name:
            return f"MIN-{capacity}TL-X"
        elif "SPH-TL3" in profile_name:
            return f"SPH-TL3-{capacity}"
        elif "SPH" in profile_name:
            return f"SPH-{capacity}"
        elif "MID" in profile_name:
            return f"MID-{capacity}TL3-X"
        elif "MAX" in profile_name:
            return f"MAX-{capacity}TL3-X"
        elif "MOD" in profile_name:
            return f"MOD-{capacity}TL3-XH"
        elif "MAC" in profile_name:
            return f"MAC-{capacity}TL3-X"
        elif "TL-XH" in profile_name:
            if "US" in profile_name:
                return f"TL-XH-US-{capacity}"
            return f"TL-XH-{capacity}"
        elif "MIX" in profile_name:
            return f"MIX-{capacity}"
        elif "SPA" in profile_name:
            return f"SPA-{capacity}"
        elif "WIT" in profile_name:
            return f"WIT-TL3-{capacity}"
        else:
            return f"Growatt-{capacity}W"

    @property
    def device_info(self):
        """Return device information for Home Assistant (legacy compatibility).

        This property is maintained for backwards compatibility.
        New code should use get_device_info(device_type) instead.
        """
        return self.get_device_info(DEVICE_TYPE_INVERTER)

    def get_device_info(self, device_type: str) -> dict:
        """Get device info for a specific device type.

        Args:
            device_type: One of DEVICE_TYPE_INVERTER, DEVICE_TYPE_SOLAR, etc.

        Returns:
            Device info dictionary for Home Assistant device registry
        """
        profile = REGISTER_MAPS[self._register_map_key]
        base_name = self.config[CONF_NAME]
        entry_id = self.entry.entry_id

        # Use parsed model name if available, otherwise fall back to profile name
        model = self._model_name if self._model_name else profile.get("name", "Unknown Model")

        # Main inverter device (parent)
        if device_type == DEVICE_TYPE_INVERTER:
            device_info = {
                "identifiers": {(DOMAIN, f"{entry_id}_inverter")},
                "name": base_name,
                "manufacturer": "Growatt",
                "model": model,
            }

            # Add serial number if available
            if self._serial_number:
                device_info["serial_number"] = self._serial_number

            # Add firmware version if available
            if self._firmware_version:
                device_info["sw_version"] = self._firmware_version

            # Add protocol version (VPP 2.01 or Legacy)
            if self._protocol_version:
                device_info["hw_version"] = self._protocol_version

            return device_info

        # All other devices reference the inverter as parent
        via_device = (DOMAIN, f"{entry_id}_inverter")

        if device_type == DEVICE_TYPE_SOLAR:
            return {
                "identifiers": {(DOMAIN, f"{entry_id}_solar")},
                "name": f"{base_name} Solar",
                "manufacturer": "Growatt",
                "model": "Solar Production",
                "via_device": via_device,
            }

        elif device_type == DEVICE_TYPE_GRID:
            return {
                "identifiers": {(DOMAIN, f"{entry_id}_grid")},
                "name": f"{base_name} Grid",
                "manufacturer": "Growatt",
                "model": "Grid Connection",
                "via_device": via_device,
            }

        elif device_type == DEVICE_TYPE_LOAD:
            return {
                "identifiers": {(DOMAIN, f"{entry_id}_load")},
                "name": f"{base_name} Load",
                "manufacturer": "Growatt",
                "model": "Load Management",
                "via_device": via_device,
            }

        elif device_type == DEVICE_TYPE_BATTERY:
            return {
                "identifiers": {(DOMAIN, f"{entry_id}_battery")},
                "name": f"{base_name} Battery",
                "manufacturer": "Growatt",
                "model": "Battery Storage",
                "via_device": via_device,
            }

        # Default to inverter for unknown device types
        return self.get_device_info(DEVICE_TYPE_INVERTER)

    @property
    def modbus_client(self):
        """Expose the modbus client for write operations."""
        return self._client