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
    get_sensor_type,
    SENSOR_OFFLINE_BEHAVIOR,
)

from .const import REGISTER_MAPS

from .growatt_modbus import GrowattModbus, GrowattData

_LOGGER = logging.getLogger(__name__)

def test_connection(config: dict) -> dict:
    """Test the connection to the Growatt inverter (TCP only)."""
    try:
        # Migrate old register map names
        register_map = config.get(CONF_REGISTER_MAP, 'MIN_7000_10000TL_X')
        
        # Ensure register map exists
        if register_map not in REGISTER_MAPS:
            register_map = 'MIN_7000_10000TL_X'
        
        # Create the TCP modbus client (TCP-only)
        client = GrowattModbus(
            connection_type="tcp",
            host=config[CONF_HOST],
            port=config[CONF_PORT],
            slave_id=config[CONF_SLAVE_ID],
            register_map=register_map,
            timeout=self.entry.options.get("timeout", 10)
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
        
        # Handle register map key (might be dict or string due to old bug)
        raw_register_map = entry.data.get(CONF_REGISTER_MAP, 'MIN_7000_10000TL_X')
        
        if isinstance(raw_register_map, dict):
            # Config stored entire dict instead of key name - use fallback
            _LOGGER.warning("Config contains register map dict instead of name, using fallback")
            self._register_map_key = "MIN_7000_10000TL_X"  # Your inverter model as fallback
            
            # Update config entry to store string key instead of dict
            new_data = {**entry.data, CONF_REGISTER_MAP: self._register_map_key}
            hass.config_entries.async_update_entry(entry, data=new_data)
            _LOGGER.info(f"Fixed config entry to store register map key: {self._register_map_key}")
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
        
        # Get update interval from options (default 30 seconds)
        scan_interval = entry.options.get("scan_interval", 30)
        
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.data[CONF_NAME]}",
            update_interval=timedelta(seconds=scan_interval),
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
                    _LOGGER.info("Identified register map as: %s", map_name)
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
        """Initialize the Growatt Modbus client (TCP-only)."""
        try:
            register_map = self._get_register_map()
            
            # Get timeout from options (default 10 seconds)
            timeout = self.entry.options.get("timeout", 10)
            
            # TCP-only connection
            self._client = GrowattModbus(
                connection_type="tcp",
                host=self.config[CONF_HOST],
                port=self.config[CONF_PORT],
                slave_id=self.config[CONF_SLAVE_ID],
                register_map=register_map,
                timeout=timeout  # Pass timeout
            )
                
            _LOGGER.info("Initialized Growatt client with register map: %s", register_map)
            
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
        _LOGGER.info("Midnight callback registered for daily total resets")

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
            _LOGGER.info("Inverter offline at midnight - resetting daily totals to 0")
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
                
                if self.data is not None:
                    _LOGGER.debug("Inverter offline - applying smart offline behavior")
                    
                    # Check if we crossed midnight while offline
                    current_date = datetime.now().date()
                    if current_date > self._current_date:
                        _LOGGER.info("Date changed while inverter offline - resetting daily totals")
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
            
            # Update successful - record timestamp (timezone-aware)
            from datetime import timezone as tz
            self.last_successful_update = datetime.now()
            self.last_update_success_time = datetime.now(tz.utc)
            self._last_successful_read = datetime.now()
            
            # Check for date transition (inverter came back online on new day)
            current_date = datetime.now().date()
            if was_offline and current_date > self._current_date:
                _LOGGER.info("Inverter back online after date change - daily totals already reset by inverter")
                self._current_date = current_date
                # Inverter's daily totals are already at new day values (small amounts from morning production)
            
            return data
            
        except Exception as err:
            _LOGGER.error("Error fetching data from Growatt inverter: %s", err)
            self._inverter_online = False
            
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
                
                # Read failed but connection was ok - retry without disconnecting
                _LOGGER.warning("Read returned None (attempt %d/%d)", attempt + 1, max_retries)
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
            await super().async_config_entry_first_refresh()
        except UpdateFailed as err:
            _LOGGER.error("Initial setup failed: %s", err)
            raise

    @property
    def device_info(self):
        profile = REGISTER_MAPS[self._register_map_key] # ✅ Use stored key
        return {
            "identifiers": {(DOMAIN, self._slave_id)},
            "name": "Growatt Inverter",
            "manufacturer": "Growatt",
            "model": profile["name"],
        }

    @property
    def modbus_client(self):
        """Expose the modbus client for write operations."""
        return self._client