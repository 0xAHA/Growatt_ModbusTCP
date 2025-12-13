"""Config flow for Growatt Modbus integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
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
    DEFAULT_PORT,
    DEFAULT_SLAVE_ID,
    DEFAULT_BAUDRATE,
    DOMAIN,
)
from .device_profiles import get_available_profiles, get_profile
from .growatt_modbus import GrowattModbus
from .auto_detection import async_determine_inverter_type

_LOGGER = logging.getLogger(__name__)


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
                    _LOGGER.info("✓ Connected successfully, attempting auto-detection...")

                    # Attempt auto-detection
                    profile_key, profile = await async_determine_inverter_type(
                        self.hass,
                        client,
                        user_input.get(CONF_SLAVE_ID, DEFAULT_SLAVE_ID)
                    )

                    # Disconnect temporary client
                    await self.hass.async_add_executor_job(client.disconnect)

                    if profile_key and profile:
                        # Auto-detection successful!
                        _LOGGER.info(f"✓ Auto-detected: {profile['name']}")

                        # Store discovered info for confirmation step
                        self._discovered_data.update({
                            CONF_HOST: user_input[CONF_HOST],
                            CONF_PORT: user_input[CONF_PORT],
                            CONF_SLAVE_ID: user_input[CONF_SLAVE_ID],
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
                            CONF_HOST: user_input[CONF_HOST],
                            CONF_PORT: user_input[CONF_PORT],
                            CONF_SLAVE_ID: user_input[CONF_SLAVE_ID],
                            "auto_detection_failed": True,
                            "dtc_result": "Not readable (inverter uses legacy protocol)"
                        })
                        return await self.async_step_manual()

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

                if not device_path:
                    errors["base"] = "no_device"
                else:
                    # Test basic connection first
                    _LOGGER.info(f"Testing serial connection to {device_path}")

                    # Create temporary client for auto-detection
                    client = GrowattModbus(
                        connection_type="serial",
                        device=device_path,
                        baudrate=user_input.get(CONF_BAUDRATE, DEFAULT_BAUDRATE),
                        slave_id=user_input.get(CONF_SLAVE_ID, DEFAULT_SLAVE_ID),
                        register_map="MIN_7000_10000TL_X"  # Temporary for connection
                    )

                    # Try to connect
                    if not await self.hass.async_add_executor_job(client.connect):
                        _LOGGER.error("Failed to connect to inverter")
                        errors["base"] = "cannot_connect"
                    else:
                        _LOGGER.info("✓ Connected successfully, attempting auto-detection...")

                        # Attempt auto-detection
                        profile_key, profile = await async_determine_inverter_type(
                            self.hass,
                            client,
                            user_input.get(CONF_SLAVE_ID, DEFAULT_SLAVE_ID)
                        )

                        # Disconnect temporary client
                        await self.hass.async_add_executor_job(client.disconnect)

                        if profile_key and profile:
                            # Auto-detection successful!
                            _LOGGER.info(f"✓ Auto-detected: {profile['name']}")

                            # Store discovered info for confirmation step
                            self._discovered_data.update({
                                CONF_DEVICE_PATH: device_path,
                                CONF_BAUDRATE: user_input[CONF_BAUDRATE],
                                CONF_SLAVE_ID: user_input[CONF_SLAVE_ID],
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
                                CONF_DEVICE_PATH: device_path,
                                CONF_BAUDRATE: user_input[CONF_BAUDRATE],
                                CONF_SLAVE_ID: user_input[CONF_SLAVE_ID],
                                "auto_detection_failed": True,
                                "dtc_result": "Not readable (inverter uses legacy protocol)"
                            })
                            return await self.async_step_manual()

            except Exception as err:
                _LOGGER.exception("Unexpected error during serial setup")
                errors["base"] = "unknown"

        # Get list of available serial ports
        ports = await self.hass.async_add_executor_job(serial.tools.list_ports.comports)

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
                return self.async_create_entry(
                    title=f"{config_data[CONF_NAME]} ({profile_name})",
                    data=config_data,
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
                series = user_input.get(CONF_INVERTER_SERIES, "min_7000_10000_tl_x")
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

                    return self.async_create_entry(
                        title=f"{config_data[CONF_NAME]} ({profile['name']})",
                        data=config_data,
                    )

            except Exception as err:
                _LOGGER.exception("Unexpected error during manual selection")
                errors["base"] = "unknown"
        
        # Build manual selection schema
        # Only show legacy profiles (V2.01 profiles excluded)
        # If auto-detection failed, the inverter doesn't support register 30000+ (V2.01)
        available_profiles = get_available_profiles(legacy_only=True)

        schema = vol.Schema({
            vol.Required(
                CONF_INVERTER_SERIES,
                default="min_7000_10000_tl_x"
            ): vol.In(available_profiles),
        })

        # Prepare description based on whether auto-detection was attempted
        if self._discovered_data and self._discovered_data.get("auto_detection_failed"):
            dtc_result = self._discovered_data.get("dtc_result", "Unknown")
            info_text = (
                f"⚠️ Auto-Detection Results:\n"
                f"• DTC Code (register 30000): {dtc_result}\n"
                f"• Conclusion: V2.01 protocol not supported\n\n"
                f"Please manually select your inverter series below.\n"
                f"Legacy protocol will be used automatically."
            )
        else:
            info_text = "Please select your inverter series. Legacy protocol will be used."

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
        return GrowattModbusOptionsFlow(config_entry)


class GrowattModbusOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Growatt Modbus."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

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
                profile = get_profile(user_input[CONF_INVERTER_SERIES])
                if profile:
                    new_data[CONF_INVERTER_SERIES] = user_input[CONF_INVERTER_SERIES]
                    new_data[CONF_REGISTER_MAP] = user_input[CONF_INVERTER_SERIES]
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
        current_scan_interval = self.config_entry.options.get("scan_interval", 30)
        current_offline_scan_interval = self.config_entry.options.get("offline_scan_interval", 300)
        current_timeout = self.config_entry.options.get("timeout", 10)
        current_invert = self.config_entry.options.get("invert_grid_power", False)

        available_profiles = get_available_profiles()

        options_schema = vol.Schema({
            vol.Required(
                "device_name",
                default=current_name
            ): str,
            vol.Required(
                CONF_INVERTER_SERIES,
                default=current_series
            ): vol.In(available_profiles),
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
                default=current_invert
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
    
