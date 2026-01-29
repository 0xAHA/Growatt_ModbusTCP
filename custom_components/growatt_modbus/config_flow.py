"""Config flow for Growatt Modbus integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
import serial
import serial.tools.list_ports

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_INVERTER_SERIES,
    CONF_SLAVE_ID,
    CONF_REGISTER_MAP,
    CONF_CONNECTION_TYPE,
    CONF_DEVICE_PATH,
    CONF_BAUDRATE,
    CONF_INVERT_BATTERY_POWER,
    DEFAULT_PORT,
    DEFAULT_SLAVE_ID,
    DEFAULT_BAUDRATE,
    DOMAIN,
)
from .device_profiles import (
    get_available_profiles,
    get_profile,
    resolve_profile_selection,
    get_display_name_for_profile,
)
from .growatt_modbus import GrowattModbus
from .auto_detection import async_determine_inverter_type

_LOGGER = logging.getLogger(__name__)


def _detect_grid_orientation(client: GrowattModbus) -> tuple[bool, str]:
    """
    Detect if grid power needs inversion for Home Assistant compatibility.

    Returns:
        tuple: (invert_needed, detection_message)
            - invert_needed: True if inversion should be enabled
            - detection_message: Human-readable explanation of detection result
    """
    try:
        # Read current data from inverter
        data = client.read_all_data()
        if not data:
            return False, "⚠️ Could not read data - using default (no inversion)"

        pv_power = getattr(data, "pv_total_power", 0)
        consumption = getattr(data, "house_consumption", 0) or getattr(data, "power_to_load", 0)
        raw_grid_power = getattr(data, "power_to_grid", 0)

        # Check if conditions are good for detection
        if pv_power < 1000:
            return False, f"⚠️ Solar production too low ({pv_power:.0f}W) - using default (no inversion). Run detection service later."

        expected_export = pv_power - consumption
        if expected_export < 100:
            return False, f"⚠️ Not exporting enough ({expected_export:.0f}W) - using default (no inversion). Run detection service later."

        # Analyze grid power sign
        # IEC 61850: positive = export, negative = import
        # HA: negative = export, positive = import

        if raw_grid_power > 100:
            # Positive while exporting = IEC standard → need inversion for HA
            return True, f"✅ Auto-detected: IEC 61850 standard (exporting {raw_grid_power:.0f}W shows as positive) - inversion enabled"
        elif raw_grid_power < -100:
            # Negative while exporting = already HA format → no inversion
            return False, f"✅ Auto-detected: Already HA format (exporting shows as negative) - no inversion needed"
        else:
            # Too close to zero
            return False, f"⚠️ Grid power near zero ({raw_grid_power:.0f}W) - using default (no inversion). Run detection service later."

    except Exception as e:
        _LOGGER.debug(f"Grid orientation detection failed: {e}")
        return False, f"⚠️ Detection failed - using default (no inversion). Run detection service later."


class GrowattModbusConfigFlow(config_entries.ConfigFlow, domain=DOMAIN): # type: ignore[call-arg]
    """Handle a config flow for Growatt Modbus."""

    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self._discovered_data = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step - choose connection type."""
        errors = {}

        if user_input is not None:
            # Store the name and connection type
            self._discovered_data = {
                CONF_NAME: user_input[CONF_NAME],
                CONF_CONNECTION_TYPE: user_input[CONF_CONNECTION_TYPE],
            }

            # Route to appropriate connection step
            if user_input[CONF_CONNECTION_TYPE] == "tcp":
                return await self.async_step_tcp()
            else:  # serial
                return await self.async_step_serial()

        # Build the initial form schema
        schema = vol.Schema({
            vol.Required(CONF_NAME, default="Growatt"): str,
            vol.Required(CONF_CONNECTION_TYPE, default="tcp"): vol.In({
                "tcp": "TCP/Ethernet (RS485-to-TCP adapter)",
                "serial": "USB/Serial (RS485-to-USB adapter)",
            }),
        })

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "info": "Choose how to connect to your Growatt inverter"
            }
        )

    async def async_step_tcp(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle TCP connection configuration."""
        errors = {}

        if user_input is not None:
            try:
                # Test basic connection first
                _LOGGER.info(f"Testing TCP connection to {user_input[CONF_HOST]}:{user_input[CONF_PORT]}")

                # Create temporary client for auto-detection
                client = GrowattModbus(
                    connection_type="tcp",
                    host=user_input[CONF_HOST],
                    port=user_input[CONF_PORT],
                    slave_id=user_input.get(CONF_SLAVE_ID, DEFAULT_SLAVE_ID),
                    register_map="MIN_7000_10000TL_X"  # Temporary for connection
                )

                # Try to connect
                if not await self.hass.async_add_executor_job(client.connect):
                    _LOGGER.error("Failed to connect to inverter")
                    errors["base"] = "cannot_connect"
                else:
                    _LOGGER.info("✓ Connected successfully")

                    # Disconnect immediately - we'll reconnect in offgrid_check if needed
                    await self.hass.async_add_executor_job(client.disconnect)

                    # Store connection details and proceed to OffGrid safety check
                    self._discovered_data.update({
                        CONF_HOST: user_input[CONF_HOST],
                        CONF_PORT: user_input[CONF_PORT],
                        CONF_SLAVE_ID: user_input[CONF_SLAVE_ID],
                    })

                    # CRITICAL: Check if user has OffGrid inverter BEFORE autodetection
                    # This prevents SPF power resets from reading VPP registers
                    return await self.async_step_offgrid_check()

            except Exception as err:
                _LOGGER.exception("Unexpected error during TCP setup")
                errors["base"] = "unknown"

        # Build the TCP form schema
        schema = vol.Schema({
            vol.Required(CONF_HOST): str,
            vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
            vol.Required(CONF_SLAVE_ID, default=DEFAULT_SLAVE_ID): int,
        })

        return self.async_show_form(
            step_id="tcp",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "info": "Enter TCP connection details for your RS485-to-TCP adapter (EW11, USR-W630, etc.)"
            }
        )

    async def async_step_serial(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle serial connection configuration with USB device selection."""
        errors = {}

        if user_input is not None:
            try:
                device_path = user_input.get(CONF_DEVICE_PATH)

                # If manual entry was selected, use the manual path
                if user_input.get("manual_path"):
                    device_path = user_input["manual_path"]
                    _LOGGER.info(f"Using manually entered device path: {device_path}")

                if not device_path or device_path == "manual":
                    errors["base"] = "no_device"
                    _LOGGER.warning("No device path provided")
                else:
                    # Log the connection attempt with all parameters
                    baudrate = user_input.get(CONF_BAUDRATE, DEFAULT_BAUDRATE)
                    slave_id = user_input.get(CONF_SLAVE_ID, DEFAULT_SLAVE_ID)
                    _LOGGER.info(
                        f"Testing serial connection: device={device_path}, "
                        f"baudrate={baudrate}, slave_id={slave_id}"
                    )

                    # Create temporary client for auto-detection
                    client = GrowattModbus(
                        connection_type="serial",
                        device=device_path,
                        baudrate=baudrate,
                        slave_id=slave_id,
                        register_map="MIN_7000_10000TL_X"  # Temporary for connection
                    )

                    # Try to connect
                    if not await self.hass.async_add_executor_job(client.connect):
                        _LOGGER.error(
                            f"Failed to connect to inverter via serial port {device_path}. "
                            f"Please check: (1) Device is plugged in, (2) Correct port selected, "
                            f"(3) RS485 wiring (A/B pins), (4) Inverter is powered on, "
                            f"(5) Baudrate matches inverter setting ({baudrate})"
                        )
                        errors["base"] = "cannot_connect"
                    else:
                        _LOGGER.info("✓ Connected successfully")

                        # Disconnect immediately - we'll reconnect in offgrid_check if needed
                        await self.hass.async_add_executor_job(client.disconnect)

                        # Store connection details and proceed to OffGrid safety check
                        self._discovered_data.update({
                            CONF_DEVICE_PATH: device_path,
                            CONF_BAUDRATE: user_input[CONF_BAUDRATE],
                            CONF_SLAVE_ID: user_input[CONF_SLAVE_ID],
                        })

                        # CRITICAL: Check if user has OffGrid inverter BEFORE autodetection
                        # This prevents SPF power resets from reading VPP registers
                        return await self.async_step_offgrid_check()

            except serial.SerialException as err:
                _LOGGER.error(
                    f"Serial port error: {err}. "
                    f"This may indicate: (1) Port in use by another application, "
                    f"(2) Insufficient permissions to access {device_path}, "
                    f"(3) Device disconnected during configuration"
                )
                errors["base"] = "cannot_connect"
            except Exception as err:
                _LOGGER.exception(f"Unexpected error during serial setup: {err}")
                errors["base"] = "unknown"

        # Get list of available serial ports
        ports = await self.hass.async_add_executor_job(serial.tools.list_ports.comports)

        # Log discovered USB devices for debugging
        _LOGGER.info("Scanning for USB serial devices...")
        if ports:
            _LOGGER.info(f"Found {len(ports)} serial device(s):")
            for port in ports:
                _LOGGER.info(
                    f"  - {port.device}: {port.description} "
                    f"(VID:PID={port.vid:04X}:{port.pid:04X} SN={port.serial_number or 'N/A'})"
                    if port.vid and port.pid
                    else f"  - {port.device}: {port.description}"
                )
        else:
            _LOGGER.warning("No serial devices found on system")

        # Build port options with descriptions
        port_options = {}
        for port in ports:
            # Create friendly description
            desc = port.device
            if port.description and port.description != "n/a":
                desc = f"{port.device} - {port.description}"
            port_options[port.device] = desc

        # Add manual entry option
        port_options["manual"] = "⌨️  Enter path manually"

        # Default to first port or manual if no ports found
        default_port = next(iter(port_options.keys())) if port_options else "manual"

        if not ports:
            _LOGGER.info("Defaulting to manual entry (no devices detected)")

        # Build the serial form schema
        schema = vol.Schema({
            vol.Required(CONF_DEVICE_PATH, default=default_port): vol.In(port_options),
            vol.Optional("manual_path"): str,
            vol.Required(CONF_BAUDRATE, default=DEFAULT_BAUDRATE): vol.In({
                9600: "9600 (Default)",
                19200: "19200",
                38400: "38400",
                115200: "115200",
            }),
            vol.Required(CONF_SLAVE_ID, default=DEFAULT_SLAVE_ID): int,
        })

        return self.async_show_form(
            step_id="serial",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "info": "Select your USB-to-RS485 adapter or enter the path manually"
            }
        )

    async def async_step_offgrid_check(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """
        CRITICAL SAFETY CHECK: Ask user if they have an Off-Grid (SPF) inverter.

        Off-Grid inverters (SPF series) experience PHYSICAL POWER RESETS if VPP
        registers (30000+, 31000+) are accessed during autodetection.

        This step prevents power cuts by redirecting SPF users to manual selection.
        """
        errors = {}

        if user_input is not None:
            if user_input.get("has_offgrid"):
                # User has Off-Grid inverter - redirect to manual selection (safe!)
                _LOGGER.info("⚠️ User confirmed Off-Grid inverter - redirecting to manual selection to prevent power reset")
                self._discovered_data["is_offgrid"] = True
                return await self.async_step_manual()
            else:
                # User does NOT have Off-Grid inverter - safe to proceed with autodetection
                _LOGGER.info("✓ User confirmed NOT Off-Grid inverter - proceeding with autodetection")

                connection_type = self._discovered_data[CONF_CONNECTION_TYPE]

                # Reconnect and attempt autodetection
                try:
                    # Create temporary client for auto-detection
                    if connection_type == "tcp":
                        client = GrowattModbus(
                            connection_type="tcp",
                            host=self._discovered_data[CONF_HOST],
                            port=self._discovered_data[CONF_PORT],
                            slave_id=self._discovered_data[CONF_SLAVE_ID],
                            register_map="MIN_7000_10000TL_X"  # Temporary for connection
                        )
                    else:  # serial
                        client = GrowattModbus(
                            connection_type="serial",
                            device=self._discovered_data[CONF_DEVICE_PATH],
                            baudrate=self._discovered_data[CONF_BAUDRATE],
                            slave_id=self._discovered_data[CONF_SLAVE_ID],
                            register_map="MIN_7000_10000TL_X"  # Temporary for connection
                        )

                    # Connect
                    if not await self.hass.async_add_executor_job(client.connect):
                        _LOGGER.error("Failed to reconnect for autodetection")
                        self._discovered_data["auto_detection_failed"] = True
                        return await self.async_step_manual()

                    _LOGGER.info("✓ Reconnected, attempting auto-detection...")

                    # Attempt auto-detection (SAFE - user confirmed not SPF)
                    profile_key, profile = await async_determine_inverter_type(
                        self.hass,
                        client,
                        self._discovered_data[CONF_SLAVE_ID]
                    )

                    # Disconnect
                    await self.hass.async_add_executor_job(client.disconnect)

                    if profile_key and profile:
                        # Auto-detection successful!
                        _LOGGER.info(f"✓ Auto-detected: {profile['name']}")

                        # Store discovered info for confirmation step
                        self._discovered_data.update({
                            CONF_INVERTER_SERIES: profile_key,
                            CONF_REGISTER_MAP: profile["register_map"],
                            "detected_profile": profile,
                            "auto_detected": True,
                        })

                        # Show confirmation step
                        return await self.async_step_confirm()
                    else:
                        # Auto-detection failed, go to manual selection
                        _LOGGER.warning("Auto-detection failed, falling back to manual selection")
                        self._discovered_data.update({
                            "auto_detection_failed": True,
                            "dtc_result": "Not readable (inverter uses legacy protocol)"
                        })
                        return await self.async_step_manual()

                except Exception as err:
                    _LOGGER.exception("Error during autodetection")
                    self._discovered_data["auto_detection_failed"] = True
                    return await self.async_step_manual()

        # Show the OffGrid safety check form
        schema = vol.Schema({
            vol.Required("has_offgrid", default=False): bool,
        })

        return self.async_show_form(
            step_id="offgrid_check",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "info": (
                    "⚠️ CRITICAL SAFETY CHECK\n\n"
                    "Do you have an Off-Grid inverter (SPF series)?\n\n"
                    "Off-Grid inverters will experience a POWER RESET if auto-detection is attempted.\n\n"
                    "• If YES: You will manually select your model (safe)\n"
                    "• If NO: Automatic detection will proceed (safe for grid-tied models)\n\n"
                    "Examples of Off-Grid models: SPF 3000-6000 ES PLUS"
                )
            }
        )

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm auto-detected inverter model."""
        errors = {}

        if user_input is not None:
            if user_input.get("action") == "accept":
                # User accepted auto-detection
                connection_type = self._discovered_data[CONF_CONNECTION_TYPE]

                # Build config data based on connection type
                config_data = {
                    CONF_NAME: self._discovered_data[CONF_NAME],
                    CONF_CONNECTION_TYPE: connection_type,
                    CONF_SLAVE_ID: self._discovered_data[CONF_SLAVE_ID],
                    CONF_INVERTER_SERIES: self._discovered_data[CONF_INVERTER_SERIES],
                    CONF_REGISTER_MAP: self._discovered_data[CONF_REGISTER_MAP],
                    "register_map": self._discovered_data[CONF_REGISTER_MAP],
                }

                # Add connection-specific parameters
                if connection_type == "tcp":
                    config_data[CONF_HOST] = self._discovered_data[CONF_HOST]
                    config_data[CONF_PORT] = self._discovered_data[CONF_PORT]
                    unique_id = f"{config_data[CONF_HOST]}_{config_data[CONF_SLAVE_ID]}"
                else:  # serial
                    config_data[CONF_DEVICE_PATH] = self._discovered_data[CONF_DEVICE_PATH]
                    config_data[CONF_BAUDRATE] = self._discovered_data[CONF_BAUDRATE]
                    unique_id = f"{config_data[CONF_DEVICE_PATH]}_{config_data[CONF_SLAVE_ID]}"

                # Set unique ID
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                profile_name = self._discovered_data["detected_profile"]["name"]

                # Attempt grid orientation detection
                invert_grid_power = False
                detection_msg = "⚠️ Using default (no inversion)"

                try:
                    # Create temporary client for grid orientation detection
                    if connection_type == "tcp":
                        detection_client = GrowattModbus(
                            connection_type="tcp",
                            host=config_data[CONF_HOST],
                            port=config_data[CONF_PORT],
                            slave_id=config_data[CONF_SLAVE_ID],
                            register_map=config_data[CONF_REGISTER_MAP]
                        )
                    else:  # serial
                        detection_client = GrowattModbus(
                            connection_type="serial",
                            device=config_data[CONF_DEVICE_PATH],
                            baudrate=config_data[CONF_BAUDRATE],
                            slave_id=config_data[CONF_SLAVE_ID],
                            register_map=config_data[CONF_REGISTER_MAP]
                        )

                    # Try to connect and detect
                    if await self.hass.async_add_executor_job(detection_client.connect):
                        invert_grid_power, detection_msg = await self.hass.async_add_executor_job(
                            _detect_grid_orientation, detection_client
                        )
                        await self.hass.async_add_executor_job(detection_client.disconnect)
                        _LOGGER.info(f"Grid orientation detection: {detection_msg}")
                    else:
                        _LOGGER.debug("Could not connect for grid orientation detection")
                except Exception as e:
                    _LOGGER.debug(f"Grid orientation detection error: {e}")

                # Set default options
                default_options = {
                    "scan_interval": 60,  # 60 seconds default polling
                    "offline_scan_interval": 300,  # 5 minutes when offline
                    "timeout": 10,  # 10 seconds connection timeout
                    "invert_grid_power": invert_grid_power,  # Auto-detected or default
                }

                # Create notification about grid orientation detection
                if "✅" in detection_msg:
                    # Successful detection
                    notification_message = (
                        f"**Grid Orientation Detection**\n\n"
                        f"{detection_msg}\n\n"
                        f"**Setting applied:** Invert Grid Power = {'ON' if invert_grid_power else 'OFF'}\n\n"
                        f"You can verify this anytime using the service:\n"
                        f"`growatt_modbus.detect_grid_orientation`"
                    )
                else:
                    # Detection skipped or failed
                    notification_message = (
                        f"**Grid Orientation Detection**\n\n"
                        f"{detection_msg}\n\n"
                        f"**Default setting applied:** Invert Grid Power = OFF\n\n"
                        f"To detect the correct setting, run this service when solar is producing:\n"
                        f"`growatt_modbus.detect_grid_orientation`"
                    )

                await self.hass.services.async_call(
                    "persistent_notification",
                    "create",
                    {
                        "title": "Growatt Modbus Setup Complete",
                        "message": notification_message,
                        "notification_id": f"growatt_setup_{config_data.get(CONF_HOST, 'device')}",
                    },
                )

                return self.async_create_entry(
                    title=f"{config_data[CONF_NAME]} ({profile_name})",
                    data=config_data,
                    options=default_options,
                )
            else:
                # User wants manual selection
                return await self.async_step_manual()

        # Show confirmation form with detected profile info
        detected_profile = self._discovered_data.get("detected_profile", {})
        profile_name = detected_profile.get("name", "Unknown")
        profile_key = self._discovered_data.get(CONF_INVERTER_SERIES, "unknown")

        # Use a selector dropdown instead of checkbox
        schema = vol.Schema({
            vol.Required("action", default="accept"): vol.In({
                "accept": f"✅ Use detected profile: {profile_name}",
                "manual": "🔧 Choose different profile manually"
            }),
        })

        return self.async_show_form(
            step_id="confirm",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "info": f"Auto-detection complete!\n\nDetected: {profile_name}\nProfile key: {profile_key}"
            }
        )

    async def async_step_manual(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manual inverter model selection fallback."""
        errors = {}

        if user_input is not None:
            try:
                # User selected a friendly name - resolve to actual profile ID
                display_name = user_input.get(CONF_INVERTER_SERIES, "MIN (7-10kW)")

                # Determine V2.01 support based on auto-detection results
                # Default to legacy (False) unless v2.01 was explicitly detected
                # This prevents incorrectly selecting v2.01 profiles when DTC register isn't readable
                supports_v201 = self._discovered_data.get("auto_detected", False) and not self._discovered_data.get("auto_detection_failed", False)

                # Resolve friendly name to actual profile ID
                series = resolve_profile_selection(display_name, supports_v201=supports_v201)

                _LOGGER.info(f"User selected '{display_name}', resolved to profile '{series}' (V2.01: {supports_v201})")

                profile = get_profile(series)

                if not profile:
                    errors["base"] = "invalid_profile"
                    _LOGGER.error(f"Invalid profile: {series}")
                else:
                    connection_type = self._discovered_data[CONF_CONNECTION_TYPE]

                    # Build config data with connection-agnostic fields
                    config_data = {
                        CONF_NAME: self._discovered_data[CONF_NAME],
                        CONF_CONNECTION_TYPE: connection_type,
                        CONF_SLAVE_ID: self._discovered_data[CONF_SLAVE_ID],
                        CONF_INVERTER_SERIES: series,
                        CONF_REGISTER_MAP: series,
                        "register_map": profile["register_map"],
                    }

                    # Add connection-specific parameters
                    if connection_type == "tcp":
                        config_data[CONF_HOST] = self._discovered_data[CONF_HOST]
                        config_data[CONF_PORT] = self._discovered_data[CONF_PORT]
                        unique_id = f"{config_data[CONF_HOST]}_{config_data[CONF_SLAVE_ID]}"
                    else:  # serial
                        config_data[CONF_DEVICE_PATH] = self._discovered_data[CONF_DEVICE_PATH]
                        config_data[CONF_BAUDRATE] = self._discovered_data[CONF_BAUDRATE]
                        unique_id = f"{config_data[CONF_DEVICE_PATH]}_{config_data[CONF_SLAVE_ID]}"

                    # Set unique ID
                    await self.async_set_unique_id(unique_id)
                    self._abort_if_unique_id_configured()

                    # Attempt grid orientation detection
                    invert_grid_power = False
                    detection_msg = "⚠️ Using default (no inversion)"

                    try:
                        # Create temporary client for grid orientation detection
                        if connection_type == "tcp":
                            detection_client = GrowattModbus(
                                connection_type="tcp",
                                host=config_data[CONF_HOST],
                                port=config_data[CONF_PORT],
                                slave_id=config_data[CONF_SLAVE_ID],
                                register_map=config_data["register_map"]
                            )
                        else:  # serial
                            detection_client = GrowattModbus(
                                connection_type="serial",
                                device=config_data[CONF_DEVICE_PATH],
                                baudrate=config_data[CONF_BAUDRATE],
                                slave_id=config_data[CONF_SLAVE_ID],
                                register_map=config_data["register_map"]
                            )

                        # Try to connect and detect
                        if await self.hass.async_add_executor_job(detection_client.connect):
                            invert_grid_power, detection_msg = await self.hass.async_add_executor_job(
                                _detect_grid_orientation, detection_client
                            )
                            await self.hass.async_add_executor_job(detection_client.disconnect)
                            _LOGGER.info(f"Grid orientation detection: {detection_msg}")
                        else:
                            _LOGGER.debug("Could not connect for grid orientation detection")
                    except Exception as e:
                        _LOGGER.debug(f"Grid orientation detection error: {e}")

                    # Set default options
                    default_options = {
                        "scan_interval": 60,  # 60 seconds default polling
                        "offline_scan_interval": 300,  # 5 minutes when offline
                        "timeout": 10,  # 10 seconds connection timeout
                        "invert_grid_power": invert_grid_power,  # Auto-detected or default
                    }

                    # Create notification about grid orientation detection
                    if "✅" in detection_msg:
                        # Successful detection
                        notification_message = (
                            f"**Grid Orientation Detection**\n\n"
                            f"{detection_msg}\n\n"
                            f"**Setting applied:** Invert Grid Power = {'ON' if invert_grid_power else 'OFF'}\n\n"
                            f"You can verify this anytime using the service:\n"
                            f"`growatt_modbus.detect_grid_orientation`"
                        )
                    else:
                        # Detection skipped or failed
                        notification_message = (
                            f"**Grid Orientation Detection**\n\n"
                            f"{detection_msg}\n\n"
                            f"**Default setting applied:** Invert Grid Power = OFF\n\n"
                            f"To detect the correct setting, run this service when solar is producing:\n"
                            f"`growatt_modbus.detect_grid_orientation`"
                        )

                    await self.hass.services.async_call(
                        "persistent_notification",
                        "create",
                        {
                            "title": "Growatt Modbus Setup Complete",
                            "message": notification_message,
                            "notification_id": f"growatt_setup_{config_data.get(CONF_HOST, config_data.get(CONF_DEVICE_PATH, 'device'))}",
                        },
                    )

                    return self.async_create_entry(
                        title=f"{config_data[CONF_NAME]} ({profile['name']})",
                        data=config_data,
                        options=default_options,
                    )

            except Exception as err:
                _LOGGER.exception("Unexpected error during manual selection")
                errors["base"] = "unknown"
        
        # Build manual selection schema with user-friendly names
        # friendly_names=True returns display names that hide protocol versions
        available_profiles = get_available_profiles(legacy_only=False, friendly_names=True)

        schema = vol.Schema({
            vol.Required(
                CONF_INVERTER_SERIES,
                default="MIN (7-10kW)"
            ): vol.In(available_profiles),
        })

        # Prepare description based on whether auto-detection was attempted
        if self._discovered_data and self._discovered_data.get("auto_detection_failed"):
            dtc_result = self._discovered_data.get("dtc_result", "Unknown")
            info_text = (
                f"⚠️ Auto-Detection Results:\n"
                f"• DTC Code (register 30000): {dtc_result}\n"
                f"• Result: V2.01 protocol not supported\n\n"
                f"Please select your inverter model below.\n"
                f"Legacy protocol will be used automatically."
            )
        else:
            info_text = (
                "Please select your inverter model below.\n"
                "Protocol version will be detected automatically."
            )

        return self.async_show_form(
            step_id="manual",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "info": info_text
            }
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get options flow."""
        return GrowattModbusOptionsFlow()


class GrowattModbusOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Growatt Modbus."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle options flow."""
        errors = {}

        if user_input is not None:
            # Update options
            new_options = {**user_input}
            
            # If profile changed, update config data too
            new_data = dict(self.config_entry.data)
            changed = False
            
            if "device_name" in user_input and user_input["device_name"] != new_data.get(CONF_NAME):
                new_data[CONF_NAME] = user_input["device_name"]
                changed = True
            
            if CONF_INVERTER_SERIES in user_input:
                # Resolve friendly display name to actual profile ID
                selected_display_name = user_input[CONF_INVERTER_SERIES]
                current_series = new_data.get(CONF_INVERTER_SERIES, "min_7000_10000_tl_x")

                # Detect V2.01 support from current profile
                # If currently using a v201 profile, hardware supports it
                # Otherwise, default to legacy for safety
                supports_v201 = '_v201' in current_series.lower()

                # Resolve to actual profile ID
                new_series = resolve_profile_selection(selected_display_name, supports_v201=supports_v201)

                _LOGGER.info(f"Options: selected '{selected_display_name}', resolved to '{new_series}' (current: '{current_series}')")

                profile = get_profile(new_series)
                if profile:
                    new_data[CONF_INVERTER_SERIES] = new_series
                    new_data[CONF_REGISTER_MAP] = new_series
                    new_data["register_map"] = profile["register_map"]
                    changed = True
                    _LOGGER.info(f"Profile changed to: {profile['name']}")
            
            if changed:
                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    data=new_data,
                    options=new_options,
                    title=new_data[CONF_NAME],
                )
            else:
                # Just update options
                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    options=new_options,
                )
            
            # Reload the integration to apply changes
            await self.hass.config_entries.async_reload(self.config_entry.entry_id)
            
            return self.async_create_entry(title="", data=new_options)

        # Build options schema with current values
        current_name = self.config_entry.data.get(CONF_NAME, "Growatt")
        current_series = self.config_entry.data.get(CONF_INVERTER_SERIES, "min_7000_10000_tl_x")
        current_scan_interval = self.config_entry.options.get("scan_interval", 60)  # Default 60 seconds
        current_offline_scan_interval = self.config_entry.options.get("offline_scan_interval", 300)
        current_timeout = self.config_entry.options.get("timeout", 10)
        current_invert_grid = self.config_entry.options.get("invert_grid_power", False)
        current_invert_battery = self.config_entry.options.get("invert_battery_power", False)

        # Get user-friendly profiles
        available_profiles = get_available_profiles(legacy_only=False, friendly_names=True)

        # Convert current profile ID to display name for default
        current_display_name = get_display_name_for_profile(current_series)

        options_schema = vol.Schema({
            vol.Required(
                "device_name",
                default=current_name
            ): str,
            vol.Required(
                CONF_INVERTER_SERIES,
                default=current_display_name
            ): vol.In(list(available_profiles.keys())),
            vol.Required(
                "scan_interval",
                default=current_scan_interval
            ): vol.All(vol.Coerce(int), vol.Range(min=5, max=300)),
            vol.Required(
                "offline_scan_interval",
                default=current_offline_scan_interval
            ): vol.All(vol.Coerce(int), vol.Range(min=60, max=3600)),
            vol.Required(
                "timeout",
                default=current_timeout
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=60)),
            vol.Required(
                "invert_grid_power",
                default=current_invert_grid
            ): bool,
            vol.Required(
                "invert_battery_power",
                default=current_invert_battery
            ): bool,
        })

        return self.async_show_form(
            step_id="init",
            data_schema=options_schema,
            errors=errors,
            description_placeholders={
                "info": "Update integration settings and inverter profile"
            }
        )
    
