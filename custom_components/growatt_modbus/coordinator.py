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
from homeassistant.helpers.storage import Store

from .const import (
    DOMAIN,
    CONF_SLAVE_ID,
    CONF_REGISTER_MAP,
    CONF_CONNECTION_TYPE,
    CONF_DEVICE_PATH,
    CONF_BAUDRATE,
    CONF_INVERT_BATTERY_POWER,
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
        self._just_came_online_time = None  # Timestamp when inverter came online (for debouncing)
        # True once the inverter has responded at least once in this HA session.
        # Used to distinguish a cold-start recovery (preserve storage-loaded daily retention)
        # from a normal overnight recovery (clear retention to trigger stale-value debounce).
        self._ever_had_real_data = False

        # Adaptive polling for offline inverters
        self._consecutive_failures = 0
        self._failure_threshold = 5  # After 5 failures, slow down polling
        scan_interval = entry.options.get("scan_interval", 60)  # Default 60 seconds
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

        # Energy total retention — prevents total_increasing spikes from dormant-inverter zeros
        self._retained_lifetime_totals: dict[str, float] = {}
        self._retained_daily_totals: dict[str, float] = {}
        _store_key = f"{DOMAIN}.{entry.entry_id}_energy_totals"
        self._energy_store: Store = Store(hass, version=1, key=_store_key)

        # Cloud override detection: tracks recently written register values
        # Format: {register_address: (expected_value, write_timestamp, control_name)}
        self._pending_write_checks: dict[int, tuple[int, float, str]] = {}
        self._cloud_override_notified: bool = False  # Only notify once per session

        # WIT: saves register 122 (export_limit_mode) before disabling control authority (30100=0).
        # Disabling 30100 transiently resets reg 122 to 0; on older firmware it may not auto-restore.
        self._saved_export_limit_mode_wit: int = 0

    @property
    def has_real_data(self) -> bool:
        """True once the inverter has responded with real data at least once this session.

        Platforms use this in deferred-entity listeners to know when coordinator.data
        contains live hardware values rather than the empty GrowattData() placeholder
        that is seeded by async_config_entry_first_refresh. (Issue #262)
        """
        return self._ever_had_real_data

    @property
    def modbus_client(self):
        """Expose the modbus client for write operations."""
        return self._client

    def track_write(self, register: int, expected_value: int, control_name: str) -> None:
        """Track a recently written register value for deferred cloud override detection.

        Called by entity write methods after a successful write. On the next poll cycle,
        _check_for_cloud_overrides() compares the tracked value against the fresh data.
        """
        import time as _time
        self._pending_write_checks[register] = (expected_value, _time.time(), control_name)

    async def _check_for_cloud_overrides(self, data) -> None:
        """Check if any recently written register values have been overridden by the cloud."""
        if not self._pending_write_checks:
            return

        import time as _time
        current_time = _time.time()
        to_remove = []
        overridden_controls = []

        for register, (expected_value, write_time, control_name) in self._pending_write_checks.items():
            age = current_time - write_time

            # Expire entries older than 120 seconds (roughly 2 poll cycles)
            if age > 120:
                to_remove.append(register)
                continue

            # Get current value from the freshly polled data
            current_value = getattr(data, control_name, None)
            if current_value is None:
                continue

            if int(current_value) == expected_value:
                # Write stuck — remove from tracking
                to_remove.append(register)
            else:
                # Value reverted — cloud override detected
                overridden_controls.append((control_name, expected_value, int(current_value), age))
                to_remove.append(register)

        # Clean up tracked entries
        for reg in to_remove:
            self._pending_write_checks.pop(reg, None)

        # Report overrides
        if overridden_controls:
            for control_name, expected, actual, age in overridden_controls:
                _LOGGER.warning(
                    "Write reversion detected: '%s' was set to %d but reverted to %d "
                    "after %.0f seconds. Possible causes: ShineWiFi/cloud dongle overriding "
                    "local writes; inverter firmware rejecting the value; or a prerequisite "
                    "setting not enabled (e.g. Allow Grid Charge for MOD TOU).",
                    control_name, expected, actual, age,
                )

            # Send persistent notification (once per session to avoid spam)
            if not self._cloud_override_notified:
                self._cloud_override_notified = True
                affected = ", ".join(
                    c[0].replace('_', ' ').title() for c in overridden_controls
                )
                try:
                    await self.hass.services.async_call(
                        "persistent_notification",
                        "create",
                        {
                            "title": "Growatt: Write Reversion Detected",
                            "message": (
                                f"Local Modbus writes to **{affected}** were reverted shortly after being set.\n\n"
                                f"**Common causes:**\n"
                                f"- **ShineWiFi / ShineLink dongle** connected: the Growatt cloud server "
                                f"may be restoring its own settings. Disconnect the dongle or disable "
                                f"remote control in the ShinePhone/Growatt app.\n"
                                f"- **Inverter firmware rejecting the value**: check that any prerequisite "
                                f"settings are enabled (e.g. *Allow Grid Charge* must be Enabled before "
                                f"MOD TOU schedules will persist).\n"
                                f"- **Register read-only on this firmware**: the register may not be "
                                f"writable on your specific model or firmware version — check the logs "
                                f"for details and open an issue if the register should be writable."
                            ),
                            "notification_id": "growatt_cloud_override",
                        },
                    )
                except Exception as err:
                    _LOGGER.debug("Could not create persistent notification: %s", err)

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

            # Get invert battery power option (separate from grid power inversion)
            invert_battery_power = self.entry.options.get(CONF_INVERT_BATTERY_POWER, False)

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
                    timeout=timeout,
                    invert_battery_power=invert_battery_power
                )
                _LOGGER.debug("Initialized TCP Growatt client at %s:%s (invert_battery_power=%s)",
                             self.config[CONF_HOST], self.config[CONF_PORT], invert_battery_power)
            else:  # serial
                self._client = GrowattModbus(
                    connection_type="serial",
                    device=self.config[CONF_DEVICE_PATH],
                    baudrate=self.config[CONF_BAUDRATE],
                    slave_id=self.config[CONF_SLAVE_ID],
                    register_map=register_map,
                    timeout=timeout,
                    invert_battery_power=invert_battery_power
                )
                _LOGGER.debug("Initialized Serial Growatt client at %s @ %s baud (invert_battery_power=%s)",
                             self.config[CONF_DEVICE_PATH], self.config[CONF_BAUDRATE], invert_battery_power)

            _LOGGER.debug("Using register map: %s", register_map)

            # Startup summary — INFO so it appears without debug logging enabled.
            # Answers the most common support question ("why is my sensor missing?")
            # without needing the diagnostic scanner.
            profile = REGISTER_MAPS.get(register_map, {})
            input_addrs = sorted(profile.get('input_registers', {}).keys())
            profile_name = profile.get('name', register_map)
            range_summary = self._summarise_register_ranges(input_addrs)

            if connection_type == "tcp":
                conn_summary = f"TCP {self.config[CONF_HOST]}:{self.config[CONF_PORT]}"
            else:
                conn_summary = f"Serial {self.config[CONF_DEVICE_PATH]}@{self.config[CONF_BAUDRATE]}"

            _LOGGER.info(
                "Growatt Modbus starting — profile: %s (%s) | connection: %s | "
                "scan interval: %ds | polling %d input registers across %s",
                profile_name,
                register_map,
                conn_summary,
                int(self._normal_update_interval.total_seconds()),
                len(input_addrs),
                range_summary,
            )

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

        # Reset cloud override notification flag so it can fire again tomorrow
        self._cloud_override_notified = False

        # Clear daily total retention so new day starts fresh
        self._retained_daily_totals = {}

        # Persist cleared daily totals (lifetime totals carry over)
        await self._async_save_energy_totals()

        _LOGGER.debug("Previous day totals stored: %s", self._previous_day_totals)

        # If inverter is offline, zero out the daily totals now
        if not self._inverter_online and self.data is not None:
            _LOGGER.debug("Inverter offline at midnight - resetting daily totals to 0")
            # Create modified data with zeroed daily totals
            self.data.energy_today = 0
            self.data.energy_to_grid_today = 0
            self.data.load_energy_today = 0
            self.data.energy_to_user_today = 0
            self.data.charge_energy_today = 0
            self.data.discharge_energy_today = 0
            self.data.ac_charge_energy_today = 0
            self.data.ac_discharge_energy_today = 0
            self.data.op_discharge_energy_today = 0

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
        
        if offline_behavior is None:
            # Sensor goes unavailable (power, diagnostic, energy totals)
            return None
        elif offline_behavior == 'retain':
            # Retain last value
            return raw_value
        elif offline_behavior == 'offline':
            # Status sensors show offline
            return 'offline'
        
        return raw_value

    @property
    def is_online(self) -> bool:
        """Return whether the inverter is currently online."""
        return self._inverter_online

    def _protect_energy_totals(self, data) -> None:
        """Prevent total_increasing sensors from dropping to 0 on dormant inverters.

        Some inverters respond to Modbus at night but return 0 for all registers.
        A lifetime total dropping from e.g. 5000 kWh to 0 causes HA's
        total_increasing to record a phantom counter reset, spiking the
        energy dashboard.

        Retention is internal — when the inverter is truly offline,
        available=False on the sensor entity handles it instead.
        """
        from .const import LIFETIME_TOTAL_ATTRS, DAILY_TOTAL_ATTRS

        _updated = False

        # Lifetime totals: only block drops to exactly 0
        for attr in LIFETIME_TOTAL_ATTRS:
            value = getattr(data, attr, 0)
            retained = self._retained_lifetime_totals.get(attr)

            if value > 0:
                # Real value — update retention if changed
                if self._retained_lifetime_totals.get(attr) != value:
                    self._retained_lifetime_totals[attr] = value
                    _updated = True
            elif retained is not None and retained > 0:
                # Value dropped to 0 but we had a real value — dormant inverter
                _LOGGER.debug(
                    "Retaining %s=%.2f (hardware reported 0, likely dormant)",
                    attr, retained
                )
                setattr(data, attr, retained)

        # Daily totals: same logic, but retention clears at midnight.
        # Spike guard: the inverter writes 32-bit register pairs (high word, then low
        # word) separately.  During the midnight daily-counter reset, the two words
        # can be read in an inconsistent state, producing a transient garbage value
        # (e.g. 79 kWh when the real value should be near 0).  Any daily-counter jump
        # larger than _SPIKE_THRESHOLD_KWH in a single poll is rejected as a glitch.
        _SPIKE_THRESHOLD_KWH = 20.0  # safe upper bound for any poll interval / system size

        for attr in DAILY_TOTAL_ATTRS:
            value = getattr(data, attr, 0)
            retained = self._retained_daily_totals.get(attr)

            if value > 0:
                # Spike guard — reject implausible jumps
                _spike = False
                if retained is None:
                    # First reading after midnight clear (or inverter just came online).
                    # A legitimate morning start reading should be near 0.
                    if value > _SPIKE_THRESHOLD_KWH:
                        _spike = True
                elif value - retained > _SPIKE_THRESHOLD_KWH:
                    # Value jumped far more than any real system can accumulate in one poll.
                    _spike = True

                if _spike:
                    _LOGGER.warning(
                        "Daily total spike rejected for %s: %.2f kWh "
                        "(retained=%.2f kWh, threshold=%.1f kWh) — "
                        "likely register glitch during startup or midnight reset",
                        attr, value,
                        retained if retained is not None else 0.0,
                        _SPIKE_THRESHOLD_KWH,
                    )
                    # Leave retention unchanged — do not persist the garbage value.
                    # The next legitimate reading (near 0 after the inverter settles)
                    # will be accepted normally.
                else:
                    if self._retained_daily_totals.get(attr) != value:
                        self._retained_daily_totals[attr] = value
                        _updated = True
            elif retained is not None and retained > 0:
                _LOGGER.debug(
                    "Retaining %s=%.2f (hardware reported 0, likely dormant)",
                    attr, retained
                )
                setattr(data, attr, retained)

        # Persist updated retention values (only when something changed, to avoid unnecessary I/O)
        if _updated:
            self.hass.async_create_task(self._async_save_energy_totals())

    async def _async_update_data(self) -> GrowattData:
        """Fetch data from the Growatt inverter."""
        if self._client is None:
            raise UpdateFailed("Growatt client not initialized")

        try:
            # Run the blocking operations in executor
            data = await self.hass.async_add_executor_job(self._fetch_data)

            if data is None:
                # Inverter not responding (probably night time or powered off)
                was_online = self._inverter_online
                self._inverter_online = False
                self._consecutive_failures += 1

                # Log once on first transition (log-when-unavailable rule)
                if was_online:
                    _LOGGER.info(
                        "Inverter unavailable — entities will show unavailable until the inverter responds"
                    )

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

                if self.data is None:
                    # First startup with inverter offline — create empty placeholder so the
                    # integration loads successfully. Regular polling will connect when the
                    # inverter comes back online. Sensors will show unavailable until then.
                    # (Issue #255: previously raised UpdateFailed → ConfigEntryNotReady which
                    # could require manual reload if HA exhausted its retry budget.)
                    _LOGGER.warning(
                        "Inverter unreachable at startup — integration loading with empty state. "
                        "Sensors will be unavailable until the inverter responds."
                    )
                    from .growatt_modbus import GrowattData
                    self.data = GrowattData()

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
                    self.data.charge_energy_today = 0
                    self.data.discharge_energy_today = 0
                    self.data.ac_charge_energy_today = 0
                    self.data.ac_discharge_energy_today = 0
                    self.data.op_discharge_energy_today = 0
                    self._current_date = current_date
                    # Clear daily retention for new day
                    self._retained_daily_totals = {}

                # Return existing data (sensors will apply offline behavior via get_sensor_value)
                return self.data

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

            # Check for date transition and stale daily total debouncing (Issue #225)
            current_date = datetime.now().date()
            current_time = datetime.now()

            if was_offline:
                # Inverter came back online after being offline.
                if current_date > self._current_date:
                    self._current_date = current_date

                if self._ever_had_real_data:
                    # Normal overnight/transient recovery: HA has been running continuously so
                    # _previous_day_totals holds the actual yesterday total. Clear daily retention
                    # so the stale-value debounce can detect and reset values that the inverter
                    # hasn't cleared yet. _protect_energy_totals would otherwise preserve them
                    # and block the hardware's own midnight reset (Issue #225).
                    _LOGGER.info("Inverter back online - enabling daily total debouncing to detect stale values")
                    self._retained_daily_totals = {}
                    self._just_came_online_time = current_time
                else:
                    # Cold-start recovery: integration just loaded (HA restart or config entry
                    # reload). _previous_day_totals is always empty here because it is never
                    # persisted — only populated at midnight during a live session. Stale
                    # detection cannot work without a real yesterday reference and produces only
                    # false-positives (e.g. small legitimate morning values < 0.1 kWh, or large
                    # mid-day values on big systems exceeding the 2 kWh/h rate heuristic).
                    # Storage-loaded retention in _retained_daily_totals already protects against
                    # inverter glitches returning 0, so stale detection is both redundant and
                    # harmful here.
                    _LOGGER.debug(
                        "Cold-start recovery — preserving storage-loaded daily retention (%d values), "
                        "skipping stale-value debounce (no yesterday totals available)",
                        len(self._retained_daily_totals)
                    )
                    # Do NOT set _just_came_online_time — leaves debounce window disabled.

                self._ever_had_real_data = True

            # Debounce stale daily totals for a window after wake-up
            # Many inverters report yesterday's values from volatile memory before resetting
            debounce_window = timedelta(minutes=15)  # 15-minute debounce window

            if self._just_came_online_time and (current_time - self._just_came_online_time) < debounce_window:
                # Within debounce window - check if daily totals look stale
                tolerance = 0.1  # 0.1 kWh tolerance for floating point comparison
                energy_today = getattr(data, 'energy_today', 0)
                yesterday_energy = self._previous_day_totals.get('energy_today', 0)

                # Stale data detection: matches yesterday's final value OR is suspiciously high for early morning
                hours_since_midnight = (current_time.hour * 60 + current_time.minute) / 60
                max_expected_early = hours_since_midnight * 2.0  # Assume max 2 kWh/hour in early morning

                is_stale = (abs(energy_today - yesterday_energy) < tolerance and energy_today > 0) or \
                          (energy_today > max_expected_early and energy_today > 1.0)

                if is_stale:
                    _LOGGER.warning(
                        "Detected stale daily total in debounce window (%.1f min since wake-up): "
                        "energy_today=%.2f kWh (yesterday: %.2f kWh, max expected: %.2f kWh) - resetting to 0",
                        (current_time - self._just_came_online_time).total_seconds() / 60,
                        energy_today, yesterday_energy, max_expected_early
                    )
                    # Reset stale daily totals to zero
                    data.energy_today = 0
                    data.energy_to_grid_today = 0
                    data.load_energy_today = 0
                    data.energy_to_user_today = 0
                    data.charge_energy_today = 0
                    data.discharge_energy_today = 0
                    data.grid_energy_today = 0
                    data.grid_import_energy_today = 0
                    # Clear retention so _protect_energy_totals doesn't undo this reset
                    self._retained_daily_totals = {}
                else:
                    _LOGGER.debug(
                        "Daily totals look valid: energy_today=%.2f kWh (yesterday: %.2f kWh, hours since midnight: %.1f)",
                        energy_today, yesterday_energy, hours_since_midnight
                    )
            elif self._just_came_online_time:
                # Debounce window expired
                _LOGGER.debug("Debounce window expired - normal operation resumed")
                self._just_came_online_time = None

            # Check for cloud overrides on recently written registers
            await self._check_for_cloud_overrides(data)

            # Protect energy totals from dormant-inverter zeros
            self._protect_energy_totals(data)

            return data

        except Exception as err:
            was_online = self._inverter_online
            self._inverter_online = False
            self._consecutive_failures += 1

            # Log once on first transition (log-when-unavailable rule); subsequent failures at debug
            if was_online:
                _LOGGER.info(
                    "Inverter unavailable (error: %s) — entities will show unavailable until the inverter responds", err
                )
            else:
                _LOGGER.debug("Error fetching data from Growatt inverter: %s", err)

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
            # First startup with an exception — create placeholder instead of failing setup.
            # Without this, CancelledError (bootstrap timeout) or ConfigEntryNotReady would
            # prevent the integration loading until the inverter comes online. (Issue #255)
            _LOGGER.info(
                "Inverter unreachable at startup — integration loading with empty state. "
                "Sensors will be unavailable until the inverter responds."
            )
            self.data = GrowattData()
            return self.data

    def _fetch_data(self) -> GrowattData | None:
        """Fetch data from the inverter (runs in executor)."""
        max_retries = 3
        retry_delay = 3  # seconds - increased from 2

        for attempt in range(max_retries):
            try:
                # Ensure clean state before connecting - always disconnect first
                # This prevents file descriptor leaks from failed connection attempts
                try:
                    self._client.disconnect()
                except Exception as err:
                    _LOGGER.debug("Disconnect before connect raised exception (safe to ignore): %s", err)

                if not self._client.connect():
                    _LOGGER.warning(
                        "Failed to connect to Growatt inverter (attempt %d/%d)",
                        attempt + 1, max_retries
                    )
                    # CRITICAL: Always disconnect after failed connect to release serial port/socket
                    try:
                        self._client.disconnect()
                    except Exception as err:
                        _LOGGER.debug("Disconnect after failed connect raised exception: %s", err)

                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)  # constant delay, not exponential
                        continue
                    _LOGGER.debug("All connection attempts failed")
                    return None

                data = self._client.read_all_data()
                if data is not None:  # Success!
                    # Lazily read device identification on the first successful connection.
                    # Previously called during async_config_entry_first_refresh, but that
                    # blocked the HA bootstrap executor and triggered a CancelledError on
                    # slow/offline inverters. Called here while the connection is still open.
                    if not self._serial_number:
                        self._read_device_identification()
                    self._client.disconnect()
                    return data

                # Read failed - disconnect before retrying to avoid stale connections
                _LOGGER.warning("Read returned None (attempt %d/%d)", attempt + 1, max_retries)
                try:
                    self._client.disconnect()
                except Exception as err:
                    _LOGGER.debug("Disconnect after failed read raised exception: %s", err)

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
                    except Exception as disconnect_err:
                        _LOGGER.debug("Disconnect after exception raised error: %s", disconnect_err)

                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    _LOGGER.debug("All fetch attempts failed after %d retries", max_retries)
                    return None

        # Final disconnect if we get here
        try:
            self._client.disconnect()
        except Exception as err:
            _LOGGER.debug("Final disconnect raised exception: %s", err)
        return None

    async def async_config_entry_first_refresh(self) -> None:
        """Load integration immediately without blocking on inverter connectivity.

        The default DataUpdateCoordinator implementation calls _async_update_data()
        which runs _fetch_data() in an executor — up to 3 TCP retries, each waiting
        for a connection timeout. During HA's bootstrap stage 2 this can exceed the
        global task timeout (CancelledError) and cancel integration setup entirely.

        Instead: restore persisted energy totals (fast, local storage only), set an
        empty GrowattData placeholder, and let the regular poll schedule handle the
        first real inverter read. All sensors show unavailable until then.

        Device identification (serial, firmware, model) is read lazily on the first
        successful poll inside _fetch_data when _serial_number is still empty.
        """
        # Restore persisted energy totals (local storage only — never blocks on network)
        await self._async_load_energy_totals()

        # Seed coordinator state so HA considers the entry loaded
        self.data = GrowattData()
        self.last_update_success = True

        # Schedule an immediate background poll so sensors populate right away
        # instead of waiting a full scan interval.  This runs after setup returns
        # so it cannot block HA's bootstrap stage-2 task timeout (Issue #262).
        self.hass.async_create_task(
            self.async_refresh(),
            name="growatt_modbus_initial_refresh",
        )
        _LOGGER.debug("Growatt Modbus: integration setup complete — immediate background poll scheduled.")
    
    async def _async_load_energy_totals(self) -> None:
        """Load persisted energy totals from HA storage."""
        try:
            stored = await self._energy_store.async_load()
            if stored is None:
                _LOGGER.debug("No persisted energy totals found (first run or storage cleared)")
                return
            # Lifetime totals: always restore (monotone increasing, never legitimately 0)
            for attr, value in stored.get("lifetime_totals", {}).items():
                if isinstance(value, (int, float)) and value > 0:
                    self._retained_lifetime_totals[attr] = float(value)
            # Daily totals: only restore if saved today
            today_str = datetime.now().date().isoformat()
            if stored.get("daily_totals_date") == today_str:
                for attr, value in stored.get("daily_totals", {}).items():
                    if isinstance(value, (int, float)) and value > 0:
                        self._retained_daily_totals[attr] = float(value)
            _LOGGER.debug(
                "Restored %d lifetime totals, %d daily totals from storage",
                len(self._retained_lifetime_totals), len(self._retained_daily_totals),
            )
        except Exception as err:
            _LOGGER.warning("Failed to load persisted energy totals (non-fatal): %s", err)

    async def _async_save_energy_totals(self) -> None:
        """Save energy retention dicts to HA storage."""
        try:
            await self._energy_store.async_save({
                "lifetime_totals": dict(self._retained_lifetime_totals),
                "daily_totals": dict(self._retained_daily_totals),
                "daily_totals_date": datetime.now().date().isoformat(),
            })
        except Exception as err:
            _LOGGER.debug("Failed to save energy totals: %s", err)

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

            # Read Protocol version (register 30099 for VPP, 73 for offgrid)
            # If readable, shows actual protocol version (e.g., 2.01, 2.02, etc.)
            if not profile.get("offgrid_protocol", False):
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
            else:
                # OffGrid profile selected
                try:
                    result = self._client.client.read_holding_registers(address=73, count=1, device_id=self._slave_id)
                    if not result.isError() and len(result.registers) > 0:
                        version_value = result.registers[0]
                        if version_value > 0:
                            # Format as version string (e.g., 201 -> "Protocol 2.01", 202 -> "Protocol 2.02")
                            major = version_value // 100
                            minor = version_value % 100
                            self._protocol_version = f"Modbus {major}.{minor:02d}"
                            _LOGGER.info(f"Detected protocol version: {self._protocol_version} (register 73 = {version_value})")
                        else:
                            self._protocol_version = "OffGrid Modbus"
                            _LOGGER.info("Protocol version register returned 0, using OffGrid Modbus")
                    else:
                        # Register not available - likely legacy protocol
                        self._protocol_version = "OffGrid Modbus"
                        _LOGGER.debug("Could not read register 73, assuming OffGrid Modbus")
                except Exception as e:
                    _LOGGER.debug(f"Could not read protocol version (73): {e}")
                    self._protocol_version = "OffGrid Modbus"

            # Consolidated identification summary — replaces scattered debug lines
            # with one INFO-level line visible in the default HA log.
            _LOGGER.info(
                "Inverter identified — model: %s | serial: %s | firmware: %s | %s",
                self._model_name or "unknown",
                self._serial_number or "unknown",
                self._firmware_version or "unknown",
                self._protocol_version or "unknown",
            )

        except Exception as e:
            _LOGGER.error(f"Error reading device identification: {e}")

    @staticmethod
    def _summarise_register_ranges(addresses: list) -> str:
        """Compact string of polled register ranges, e.g. '0–124, 1000–1124, 31000–31199'.

        Addresses within 100 of each other are merged into one range.
        Used in the startup log so support questions can be answered without
        running the diagnostic scanner.
        """
        if not addresses:
            return "none"
        sorted_addrs = sorted(addresses)
        ranges = []
        start = prev = sorted_addrs[0]
        for addr in sorted_addrs[1:]:
            if addr - prev > 100:
                ranges.append(f"{start}–{prev}" if start != prev else str(start))
                start = addr
            prev = addr
        ranges.append(f"{start}–{prev}" if start != prev else str(start))
        return ", ".join(ranges)

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
