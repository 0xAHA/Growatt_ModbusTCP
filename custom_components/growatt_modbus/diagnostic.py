"""Diagnostic service for Growatt Modbus Integration."""
import logging
import csv
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Tuple, Optional

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import device_registry as dr
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN

# Import register maps for "Suggested Match" column
try:
    from .growatt_register_map import (
        INPUT_REGISTERS_BASE,
        INPUT_REGISTERS_STORAGE,
        HOLDING_REGISTERS,
    )
    REGISTER_MAPS_AVAILABLE = True
except ImportError:
    REGISTER_MAPS_AVAILABLE = False
    INPUT_REGISTERS_BASE = {}
    INPUT_REGISTERS_STORAGE = {}
    HOLDING_REGISTERS = {}

_LOGGER = logging.getLogger(__name__)

def _get_integration_version() -> str:
    """Get integration version from manifest.json."""
    try:
        manifest_path = os.path.join(os.path.dirname(__file__), "manifest.json")
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
            return manifest.get("version", "unknown")
    except Exception as e:
        _LOGGER.warning(f"Could not read integration version: {e}")
        return "unknown"

# Service names
SERVICE_EXPORT_DUMP = "export_register_dump"
SERVICE_WRITE_REGISTER = "write_register"
SERVICE_DETECT_GRID_ORIENTATION = "detect_grid_orientation"
SERVICE_READ_REGISTER = "read_register"

# Universal scan ranges - covers all Grid-Tied Growatt series
# Split into chunks of max 125 registers to respect Modbus limits
UNIVERSAL_SCAN_RANGES = [
    {"name": "Base Range 0-124", "start": 0, "count": 125},
    {"name": "Extended Range 125-249", "start": 125, "count": 125},
    {"name": "Storage Range 1000-1124", "start": 1000, "count": 125},
    {"name": "MIN/MOD Range 3000-3124", "start": 3000, "count": 125},
    {"name": "MOD Extended 3125-3249", "start": 3125, "count": 125},
    {"name": "WIT/WIS Battery Range 8000-8124", "start": 8000, "count": 125},
    # VPP Protocol V2.01 ranges (31000+)
    {"name": "VPP Status/PV: 31000-31099", "start": 31000, "count": 100},  # Equipment status, PV data, faults
    {"name": "VPP AC/Grid/Load: 31100-31199", "start": 31100, "count": 100},  # AC output, meter/grid power (31112), load power (31118), energy, temps
    {"name": "VPP Battery 1: 31200-31299", "start": 31200, "count": 100},  # Battery cluster 1 data
    {"name": "VPP Battery 2: 31300-31399", "start": 31300, "count": 100},  # Battery cluster 2 data (optional)
]

# OffGrid scan ranges - SAFE for SPF series (prevents power resets!)
# CRITICAL: OffGrid inverters RESET if VPP registers (30000+, 31000+) are accessed
# Limits based on OffGrid Modbus Protocol documentation
OFFGRID_SCAN_RANGES = [
    {"name": "OffGrid Base Range 0-82", "start": 0, "count": 83},  # SPF primary range
    {"name": "OffGrid Extended 83-165", "start": 83, "count": 83},  # Additional safe range
    {"name": "OffGrid Upper 166-248", "start": 166, "count": 83},  # Extended range
    {"name": "OffGrid Final 249-290", "start": 249, "count": 42},  # Up to input register limit (290)
]

# Service schema
SERVICE_EXPORT_DUMP_SCHEMA = vol.Schema(
    {
        # Connection type selection
        vol.Optional("connection_type", default="tcp"): vol.In(["tcp", "serial"]),

        # TCP parameters (required if connection_type=tcp)
        vol.Optional("host"): cv.string,
        vol.Optional("port", default=502): cv.port,

        # Serial parameters (required if connection_type=serial)
        vol.Optional("device"): cv.string,  # e.g., /dev/ttyUSB0, COM3
        vol.Optional("baudrate", default=9600): vol.In([4800, 9600, 19200, 38400, 57600, 115200]),

        # Common parameters
        vol.Optional("slave_id", default=1): vol.All(vol.Coerce(int), vol.Range(min=1, max=247)),
        vol.Optional("notify", default=True): cv.boolean,
        vol.Optional("offgrid_mode", default=False): cv.boolean,  # CRITICAL: Enable for SPF to prevent power reset
        vol.Optional("device_id"): cv.string,  # Optional: Include entity values from this device's coordinator
    }
)

SERVICE_WRITE_REGISTER_SCHEMA = vol.Schema(
    {
        vol.Required("device_id"): cv.string,
        vol.Required("register"): vol.All(vol.Coerce(int), vol.Range(min=0, max=65535)),
        vol.Required("value"): vol.All(vol.Coerce(int), vol.Range(min=-32768, max=65535)),
    }
)

SERVICE_DETECT_GRID_ORIENTATION_SCHEMA = vol.Schema(
    {
        vol.Optional("device_id"): cv.string,  # If not provided, uses first found integration
    }
)

SERVICE_READ_REGISTER_SCHEMA = vol.Schema(
    {
        vol.Required("device_id"): cv.string,
        vol.Required("register"): vol.All(vol.Coerce(int), vol.Range(min=0, max=65535)),
        vol.Optional("register_type", default="input"): vol.In(["input", "holding"]),
    }
)


def _read_single_register(client, register: int, register_type: str = 'input') -> dict:
    """
    Read a single Modbus register.

    Args:
        client: GrowattModbus client with read_input_registers or read_holding_registers methods
        register: Register address to read
        register_type: 'input' or 'holding'

    Returns:
        dict with 'success', 'value', and 'error' keys
    """
    try:
        # Choose read method based on register type
        # GrowattModbus methods return Optional[list] - list on success, None on error
        if register_type == 'holding':
            result = client.read_holding_registers(start_address=register, count=1)
        else:  # 'input'
            result = client.read_input_registers(start_address=register, count=1)

        if result is not None and len(result) > 0:
            return {
                'success': True,
                'value': result[0],
                'error': None
            }
        else:
            return {
                'success': False,
                'value': None,
                'error': "Register read failed or returned no data"
            }

    except Exception as e:
        return {
            'success': False,
            'value': None,
            'error': f"{type(e).__name__}: {str(e)}"
        }


def _lookup_register_info(register_addr: int) -> Optional[str]:
    """
    Look up register information from the register maps.

    Returns formatted string like "Grid_Voltage (×0.1, V)" or None if not found.
    """
    if not REGISTER_MAPS_AVAILABLE:
        return None

    # Check all register maps
    reg_info = None
    if register_addr in INPUT_REGISTERS_BASE:
        reg_info = INPUT_REGISTERS_BASE[register_addr]
    elif register_addr in INPUT_REGISTERS_STORAGE:
        reg_info = INPUT_REGISTERS_STORAGE[register_addr]
    elif register_addr in HOLDING_REGISTERS:
        reg_info = HOLDING_REGISTERS[register_addr]

    if reg_info:
        name = reg_info.get("name", "")
        scale = reg_info.get("scale", 1)
        unit = reg_info.get("unit", "")
        description = reg_info.get("description", "")

        # Format: "Name (×scale, unit) - description"
        parts = [name]

        # Add scale and unit if present
        if scale != 1 or unit:
            detail = []
            if scale != 1:
                detail.append(f"×{scale}")
            if unit:
                detail.append(unit)
            parts.append(f"({', '.join(detail)})")

        # Add description if present and different from name
        if description and description != name:
            parts.append(f"- {description}")

        return " ".join(parts)

    return None


def _get_entity_value_for_register(register_addr: int, coordinator, register_type: str = 'input') -> Optional[str]:
    """
    Get the calculated entity value for a register from the coordinator.

    Args:
        register_addr: Register address to look up
        coordinator: Coordinator instance with data and register_map
        register_type: 'input' or 'holding'

    Returns:
        Formatted string with entity value(s) or None if not found
    """
    if not coordinator or not coordinator.data:
        return None

    # Get the register map from coordinator
    if not hasattr(coordinator, '_client') or not hasattr(coordinator._client, 'register_map'):
        return None

    register_map = coordinator._client.register_map
    register_dict = register_map.get('input_registers' if register_type == 'input' else 'holding_registers', {})

    if register_addr not in register_dict:
        return None

    reg_info = register_dict[register_addr]
    reg_name = reg_info.get('name', '')

    # Check if this register maps to a coordinator data attribute
    # Try to get the value from coordinator.data using the register name
    entity_value = getattr(coordinator.data, reg_name, None)

    if entity_value is None:
        # Try common name variations (e.g., battery_power_low -> battery_power)
        # For paired registers, the _low register usually has the combined value
        if reg_name.endswith('_low'):
            base_name = reg_name[:-4]  # Remove '_low'
            entity_value = getattr(coordinator.data, base_name, None)
        elif reg_name.endswith('_high'):
            # High registers don't typically have separate entity values
            return None

    if entity_value is not None:
        # Format the value with unit
        unit = reg_info.get('combined_unit') or reg_info.get('unit', '')
        if isinstance(entity_value, (int, float)):
            if unit:
                return f"{entity_value} {unit}"
            else:
                return str(entity_value)
        else:
            return str(entity_value)

    return None


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up diagnostic services."""

    async def export_register_dump(call: ServiceCall) -> None:
        """Universal register scanner - scans all ranges and auto-detects model."""
        connection_type = call.data.get("connection_type", "tcp")
        host = call.data.get("host")
        port = call.data.get("port", 502)
        device = call.data.get("device")
        baudrate = call.data.get("baudrate", 9600)
        slave_id = call.data.get("slave_id", 1)
        send_notification = call.data.get("notify", True)
        offgrid_mode = call.data.get("offgrid_mode", False)
        device_id = call.data.get("device_id")

        # Validate required parameters based on connection type
        if connection_type == "tcp":
            if not host:
                _LOGGER.error("host parameter required for TCP connection")
                return
        elif connection_type == "serial":
            if not device:
                _LOGGER.error("device parameter required for serial connection")
                return

        # Get coordinator if device_id provided
        coordinator = None
        if device_id:
            device_reg = dr.async_get(hass)
            device_entry = device_reg.async_get(device_id)

            if device_entry:
                # Find coordinator for this device
                for entry_id in device_entry.config_entries:
                    if entry_id in hass.data.get(DOMAIN, {}):
                        coordinator = hass.data[DOMAIN][entry_id]
                        _LOGGER.info("Using coordinator from device %s for entity value mapping", device_id)
                        break

            if not coordinator:
                _LOGGER.warning("Device ID provided but coordinator not found - entity values will not be included")

        if offgrid_mode:
            _LOGGER.warning("⚠️ OffGrid mode ENABLED - skipping VPP registers to prevent power reset on SPF inverters")

        # Log connection info
        if connection_type == "tcp":
            _LOGGER.info("Starting %s register scan at %s:%s", "OffGrid" if offgrid_mode else "universal", host, port)
        else:
            _LOGGER.info("Starting %s register scan on %s @ %d baud", "OffGrid" if offgrid_mode else "universal", device, baudrate)

        # Run export in executor
        result = await hass.async_add_executor_job(
            _export_registers_to_csv, hass, connection_type, host, port, device, baudrate, slave_id, offgrid_mode, coordinator
        )
        
        if result["success"]:
            detection = result.get("detection", {})
            confidence = detection.get("confidence", "Unknown")
            model = detection.get("model", "Unknown")
            profile_key = detection.get("profile_key", "N/A")
            dtc_code = detection.get("dtc_code")
            protocol_version = detection.get("protocol_version")

            message_lines = [
                f"**File saved:** `{result['filename']}`\n",
                f"**Detected Model:** {model}",
                f"**Confidence:** {confidence}",
            ]

            # Add DTC/Protocol info if available
            if dtc_code:
                message_lines.append(f"**DTC Code:** {dtc_code}")
            if protocol_version:
                protocol_str = f"{protocol_version // 100}.{protocol_version % 100:02d}" if protocol_version >= 100 else str(protocol_version)
                message_lines.append(f"**Protocol:** V{protocol_str}")

            message_lines.extend([
                f"**Suggested Profile:** `{profile_key}`\n",
                f"**Scan Results:**",
                f"• Total registers scanned: {result['total_registers']}",
                f"• Non-zero registers: {result['non_zero']}",
                f"• Responding ranges: {result['responding_ranges']}\n",
                f"Download from File Editor or `/config/{result['filename']}`",
            ])
            
            if send_notification:
                await hass.services.async_call(
                    "persistent_notification",
                    "create",
                    {
                        "title": f"✅ Universal Scanner: {model}",
                        "message": "\n".join(message_lines),
                        "notification_id": "growatt_register_export",
                    },
                )
        else:
            if send_notification:
                await hass.services.async_call(
                    "persistent_notification",
                    "create",
                    {
                        "title": "❌ Register Scan Failed",
                        "message": result.get("error", "Unknown error"),
                        "notification_id": "growatt_register_export",
                    },
                )

    async def write_register(call: ServiceCall) -> None:
        """Write a value to a Modbus holding register."""
        device_id = call.data["device_id"]
        register = call.data["register"]
        value = call.data["value"]

        _LOGGER.info("Write register service called: device=%s, register=%d, value=%d", device_id, register, value)

        # Get device registry
        device_reg = dr.async_get(hass)
        device_entry = device_reg.async_get(device_id)

        if not device_entry:
            _LOGGER.error("Device %s not found", device_id)
            raise ValueError(f"Device {device_id} not found")

        # Find the config entry for this device
        config_entry_id = None
        for entry_id in device_entry.config_entries:
            if entry_id in hass.data.get(DOMAIN, {}):
                config_entry_id = entry_id
                break

        if not config_entry_id:
            _LOGGER.error("No config entry found for device %s", device_id)
            raise ValueError(f"No config entry found for device {device_id}")

        # Get the coordinator
        coordinator = hass.data[DOMAIN][config_entry_id]

        if not coordinator:
            _LOGGER.error("Coordinator not found for config entry %s", config_entry_id)
            raise ValueError(f"Coordinator not found for device {device_id}")

        # Write the register using the coordinator's client
        success = await hass.async_add_executor_job(
            coordinator._client.write_register, register, value
        )

        if success:
            _LOGGER.info("Successfully wrote value %d to register %d", value, register)
            # Trigger a refresh to update the UI
            await coordinator.async_request_refresh()
        else:
            _LOGGER.error("Failed to write value %d to register %d", value, register)
            raise ValueError(f"Failed to write to register {register}")

    async def detect_grid_orientation(call: ServiceCall) -> None:
        """Detect if grid power CT clamp needs inversion based on current power flow."""
        device_id = call.data.get("device_id")

        # Find coordinator
        if device_id:
            device_reg = dr.async_get(hass)
            device_entry = device_reg.async_get(device_id)
            if not device_entry:
                raise ValueError(f"Device {device_id} not found")

            config_entry_id = None
            for entry_id in device_entry.config_entries:
                if entry_id in hass.data.get(DOMAIN, {}):
                    config_entry_id = entry_id
                    break

            if not config_entry_id:
                raise ValueError(f"No config entry found for device {device_id}")

            coordinator = hass.data[DOMAIN][config_entry_id]
        else:
            # Use first available coordinator
            if not hass.data.get(DOMAIN):
                raise ValueError("No Growatt Modbus integrations found")

            coordinator = next(iter(hass.data[DOMAIN].values()))
            if not coordinator:
                raise ValueError("No coordinator found")

        # Check if inverter is online and producing
        if not coordinator.data:
            message = (
                "❌ **Grid Orientation Detection Failed**\n\n"
                "No data available from inverter.\n"
                "Please ensure the inverter is online and try again."
            )
            await hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": "Grid Orientation Detection",
                    "message": message,
                    "notification_id": "growatt_grid_detection",
                },
            )
            return

        data = coordinator.data
        pv_power = getattr(data, "pv_total_power", 0)
        consumption = getattr(data, "house_consumption", 0) or getattr(data, "power_to_load", 0)

        # Read RAW grid power (before inversion)
        raw_grid_power = getattr(data, "power_to_grid", 0)

        # Need clear export scenario for reliable detection
        if pv_power < 1000:
            message = (
                "⚠️ **Grid Orientation Detection: Insufficient Solar**\n\n"
                f"Current solar production: **{pv_power:.0f} W**\n\n"
                "Detection requires at least **1000 W** of solar production for reliability.\n\n"
                "**Please try again when:**\n"
                "• The sun is shining\n"
                "• Solar panels are producing > 1 kW\n"
                "• Preferably during midday"
            )
            await hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": "Grid Orientation Detection",
                    "message": message,
                    "notification_id": "growatt_grid_detection",
                },
            )
            return

        # Check if we're clearly exporting
        expected_export = pv_power - consumption
        if expected_export < 100:
            message = (
                "⚠️ **Grid Orientation Detection: Not Exporting Enough**\n\n"
                f"• Solar production: **{pv_power:.0f} W**\n"
                f"• House consumption: **{consumption:.0f} W**\n"
                f"• Expected export: **{expected_export:.0f} W**\n\n"
                "Detection requires at least **100 W** net export for reliability.\n\n"
                "**Please try again when:**\n"
                "• Solar production exceeds consumption by > 100 W\n"
                "• Turn off high-power appliances temporarily if needed"
            )
            await hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": "Grid Orientation Detection",
                    "message": message,
                    "notification_id": "growatt_grid_detection",
                },
            )
            return

        # Analyze grid power sign
        _LOGGER.info(
            "Grid orientation detection: PV=%.0fW, Consumption=%.0fW, "
            "Expected export=%.0fW, Raw grid=%.0fW",
            pv_power, consumption, expected_export, raw_grid_power
        )

        # IEC 61850 standard: positive = export, negative = import
        # When exporting, raw_grid_power should be positive in IEC standard
        # HA convention: negative = export, positive = import

        current_invert_setting = coordinator.entry.options.get("invert_grid_power", False)

        # Expected: exporting, so raw_grid_power should be positive (IEC standard)
        if raw_grid_power > 100:
            # Positive grid power while exporting = IEC standard (correct)
            # Need to invert FOR Home Assistant visualization
            recommended_invert = True
            confidence = "High"
            explanation = (
                "Your inverter follows **IEC 61850 standard** (positive = export).\n"
                "Home Assistant expects **negative = export** for visualization.\n"
                "**Inversion is needed** for correct display."
            )
        elif raw_grid_power < -100:
            # Negative grid power while exporting = already inverted or wrong
            recommended_invert = False
            confidence = "High"
            explanation = (
                "Your grid power is already in **Home Assistant format** (negative = export).\n"
                "**No inversion needed** for correct display."
            )
        else:
            # Close to zero - ambiguous
            confidence = "Low"
            recommended_invert = current_invert_setting  # Keep current
            explanation = (
                "Grid power too close to zero for reliable detection.\n"
                "Try again with higher export levels."
            )

        # Determine action needed
        if confidence == "Low":
            action = "⚠️ **Unable to determine** - insufficient export"
            title_emoji = "⚠️"
        elif recommended_invert == current_invert_setting:
            action = "✅ **Already configured correctly** - no changes needed"
            title_emoji = "✅"
        else:
            action = f"🔧 **Change needed**: Set 'Invert Grid Power' to **{'ON' if recommended_invert else 'OFF'}**"
            title_emoji = "🔧"

        message = (
            f"{action}\n\n"
            f"**Current Measurements:**\n"
            f"• Solar production: **{pv_power:.0f} W**\n"
            f"• House consumption: **{consumption:.0f} W**\n"
            f"• Net export: **{expected_export:.0f} W**\n"
            f"• Raw grid power: **{raw_grid_power:.0f} W**\n\n"
            f"**Analysis:**\n"
            f"{explanation}\n\n"
            f"**Current Setting:** Invert = **{'ON' if current_invert_setting else 'OFF'}**\n"
            f"**Recommended:** Invert = **{'ON' if recommended_invert else 'OFF'}**\n"
            f"**Confidence:** {confidence}\n\n"
            f"**To change setting:**\n"
            f"1. Go to Settings → Devices & Services\n"
            f"2. Find Growatt Modbus → Configure\n"
            f"3. Set 'Invert Grid Power' to **{'ON' if recommended_invert else 'OFF'}**\n"
            f"4. Save and reload the integration"
        )

        await hass.services.async_call(
            "persistent_notification",
            "create",
            {
                "title": f"{title_emoji} Grid Orientation Detection",
                "message": message,
                "notification_id": "growatt_grid_detection",
            },
        )

        _LOGGER.info(
            "Grid orientation detection complete: current=%s, recommended=%s, confidence=%s",
            current_invert_setting, recommended_invert, confidence
        )

    async def read_register(call: ServiceCall) -> None:
        """Read a specific Modbus register with detailed profile-aware output."""
        device_id = call.data["device_id"]
        register = call.data["register"]
        register_type = call.data.get("register_type", "input")

        _LOGGER.info("Read register service called: device=%s, register=%d, type=%s", device_id, register, register_type)

        # Get device registry
        device_reg = dr.async_get(hass)
        device_entry = device_reg.async_get(device_id)

        if not device_entry:
            _LOGGER.error("Device %s not found", device_id)
            raise ValueError(f"Device {device_id} not found")

        # Find the config entry for this device
        config_entry_id = None
        for entry_id in device_entry.config_entries:
            if entry_id in hass.data.get(DOMAIN, {}):
                config_entry_id = entry_id
                break

        if not config_entry_id:
            _LOGGER.error("No config entry found for device %s", device_id)
            raise ValueError(f"No config entry found for device {device_id}")

        # Get the coordinator
        coordinator = hass.data[DOMAIN][config_entry_id]

        if not coordinator:
            _LOGGER.error("Coordinator not found for config entry %s", config_entry_id)
            raise ValueError(f"Coordinator not found for device {device_id}")

        # Read the register using the coordinator's client
        read_result = await hass.async_add_executor_job(
            lambda: _read_single_register(coordinator._client, register, register_type)
        )

        if not read_result["success"]:
            error_msg = read_result.get("error", "Unknown error")
            _LOGGER.error("Failed to read register %d: %s", register, error_msg)

            await hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": f"❌ Register Read Failed: {register}",
                    "message": f"**Error reading register {register} ({register_type}):**\n\n{error_msg}",
                    "notification_id": "growatt_register_read",
                },
            )
            return

        # Build notification message
        raw_value = read_result["value"]
        message_lines = [
            f"**Register:** {register} (0x{register:04X})",
            f"**Type:** {register_type.capitalize()}",
            f"**Raw Value:** {raw_value}",
        ]

        # Check if register is in profile
        register_map = coordinator._client.register_map
        register_dict = register_map.get('input_registers' if register_type == 'input' else 'holding_registers', {})

        if register in register_dict:
            reg_info = register_dict[register]
            reg_name = reg_info.get('name', 'Unknown')
            scale = reg_info.get('scale', 1)
            unit = reg_info.get('unit', '')
            pair = reg_info.get('pair')
            combined_scale = reg_info.get('combined_scale')
            combined_unit = reg_info.get('combined_unit', '')
            is_signed = reg_info.get('signed', False)

            message_lines.append(f"\n**Profile Info:**")
            message_lines.append(f"• Name: `{reg_name}`")
            message_lines.append(f"• Scale: ×{scale}")
            if unit:
                message_lines.append(f"• Unit: {unit}")

            # Calculate scaled value for this register alone
            scaled_value = raw_value * scale
            if unit:
                message_lines.append(f"• Scaled Value: {scaled_value} {unit}")
            else:
                message_lines.append(f"• Scaled Value: {scaled_value}")

            # Handle signed interpretation
            if is_signed and raw_value > 32767:
                signed_value = raw_value - 65536
                message_lines.append(f"• Signed Value: {signed_value}")

            # Check for paired register
            if pair is not None:
                message_lines.append(f"\n**Paired Register Detected:**")
                message_lines.append(f"• Pair Address: {pair} (0x{pair:04X})")

                # Read the paired register
                pair_result = await hass.async_add_executor_job(
                    lambda: _read_single_register(coordinator._client, pair, register_type)
                )

                if pair_result["success"]:
                    pair_value = pair_result["value"]
                    message_lines.append(f"• Pair Raw Value: {pair_value}")

                    # Determine which is high/low
                    if register < pair:
                        # Current register is high word
                        high_word = raw_value
                        low_word = pair_value
                    else:
                        # Current register is low word
                        high_word = pair_value
                        low_word = raw_value

                    # Combine into 32-bit value
                    combined_raw = (high_word << 16) | low_word

                    # Handle signed 32-bit if specified
                    if is_signed and combined_raw > 0x7FFFFFFF:
                        combined_raw = combined_raw - 0x100000000

                    message_lines.append(f"\n**Combined 32-bit Value:**")
                    message_lines.append(f"• Raw Combined: {combined_raw}")

                    # Apply combined scale if specified
                    if combined_scale is not None:
                        combined_computed = combined_raw * combined_scale
                        if combined_unit:
                            message_lines.append(f"• Combined Scale: ×{combined_scale}")
                            message_lines.append(f"• **Computed Value: {combined_computed} {combined_unit}**")
                        else:
                            message_lines.append(f"• Combined Scale: ×{combined_scale}")
                            message_lines.append(f"• **Computed Value: {combined_computed}**")
                    else:
                        message_lines.append(f"• (No combined scale defined)")
                else:
                    message_lines.append(f"• ⚠️ Failed to read paired register: {pair_result.get('error', 'Unknown error')}")
        else:
            message_lines.append(f"\n**Profile Info:**")
            message_lines.append(f"• ⚠️ Register {register} not defined in current profile")
            message_lines.append(f"• Profile: `{coordinator._client.register_map.get('profile_name', 'Unknown')}`")

            # Provide common interpretations
            message_lines.append(f"\n**Common Interpretations:**")
            message_lines.append(f"• ×0.1 = {raw_value * 0.1}")
            message_lines.append(f"• ×0.01 = {raw_value * 0.01}")
            if raw_value > 32767:
                signed = raw_value - 65536
                message_lines.append(f"• Signed (INT16) = {signed}")

        # Try to get entity value from coordinator
        entity_value = _get_entity_value_for_register(register, coordinator, register_type)
        if entity_value:
            message_lines.append(f"\n**Current Entity Value:**")
            message_lines.append(f"• {entity_value}")

        _LOGGER.info("Successfully read register %d: raw=%d", register, raw_value)

        await hass.services.async_call(
            "persistent_notification",
            "create",
            {
                "title": f"📋 Register {register} ({register_type.capitalize()})",
                "message": "\n".join(message_lines),
                "notification_id": "growatt_register_read",
            },
        )

    # Register services
    hass.services.async_register(
        DOMAIN,
        SERVICE_EXPORT_DUMP,
        export_register_dump,
        schema=SERVICE_EXPORT_DUMP_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_WRITE_REGISTER,
        write_register,
        schema=SERVICE_WRITE_REGISTER_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_DETECT_GRID_ORIENTATION,
        detect_grid_orientation,
        schema=SERVICE_DETECT_GRID_ORIENTATION_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_READ_REGISTER,
        read_register,
        schema=SERVICE_READ_REGISTER_SCHEMA,
    )


def _read_registers_chunked(client, start: int, count: int, slave_id: int, chunk_size: int = 50, register_type: str = 'input') -> Dict[int, Dict[str, Any]]:
    """
    Read registers in chunks to avoid timeouts.

    Args:
        register_type: 'input' for input registers (default), 'holding' for holding registers

    Returns dict mapping register address to: {
        'value': int or None,
        'status': 'success'|'error'|'exception',
        'error': str (error description if status != 'success')
    }
    """
    register_data = {}

    for chunk_start in range(0, count, chunk_size):
        chunk_count = min(chunk_size, count - chunk_start)
        chunk_address = start + chunk_start

        try:
            # Choose read method based on register type
            if register_type == 'holding':
                response = client.read_holding_registers(
                    address=chunk_address,
                    count=chunk_count,
                    device_id=slave_id
                )
            else:  # 'input'
                response = client.read_input_registers(
                    address=chunk_address,
                    count=chunk_count,
                    device_id=slave_id
                )

            if not response.isError():
                # Store ALL values, including zeros
                for i, value in enumerate(response.registers):
                    register_data[chunk_address + i] = {
                        'value': value,
                        'status': 'success',
                        'error': None
                    }
                _LOGGER.debug(f"Read chunk {chunk_address}-{chunk_address+chunk_count-1}: {chunk_count} registers")
            else:
                # Store error for each register in the chunk
                error_msg = str(response)
                # Try to extract specific error type
                if hasattr(response, 'exception_code'):
                    error_code = response.exception_code
                    error_names = {
                        1: "Illegal Function",
                        2: "Illegal Data Address",
                        3: "Illegal Data Value",
                        4: "Slave Device Failure",
                        5: "Acknowledge",
                        6: "Slave Device Busy",
                        10: "Gateway Path Unavailable",
                        11: "Gateway Target Failed to Respond"
                    }
                    error_msg = error_names.get(error_code, f"Error Code {error_code}")

                for i in range(chunk_count):
                    register_data[chunk_address + i] = {
                        'value': None,
                        'status': 'error',
                        'error': error_msg
                    }
                _LOGGER.debug(f"Chunk {chunk_address}-{chunk_address+chunk_count-1} returned error: {error_msg}")

        except Exception as e:
            # Store exception for each register in the chunk
            error_msg = f"Exception: {type(e).__name__}: {str(e)}"
            for i in range(chunk_count):
                register_data[chunk_address + i] = {
                    'value': None,
                    'status': 'exception',
                    'error': error_msg
                }
            _LOGGER.debug(f"Chunk {chunk_address} exception: {e}")

    return register_data


def _detect_inverter_model(register_data: Dict[int, Dict[str, Any]]) -> Dict[str, str]:
    """
    Analyze register responses to detect inverter model.

    Returns dict with: model, confidence, profile_key, register_map, reasoning, dtc_code, protocol_version
    """
    detection = {
        "model": "Unknown",
        "confidence": "Low",
        "profile_key": "unknown",
        "register_map": "UNKNOWN",
        "reasoning": [],
        "dtc_code": None,
        "protocol_version": None,
    }

    # Helper to check if register exists with valid data
    def has_reg(addr):
        return addr in register_data and register_data[addr]['status'] == 'success' and register_data[addr]['value'] is not None and register_data[addr]['value'] > 0

    # Check for DTC code (holding register 30000)
    if 30000 in register_data and register_data[30000]['status'] == 'success' and register_data[30000]['value']:
        dtc_code = register_data[30000]['value']
        detection["dtc_code"] = dtc_code
        detection["reasoning"].append(f"✓ DTC Code: {dtc_code} (register 30000)")

        # Map DTC to profile (from auto_detection.py)
        dtc_map = {
            3502: ('SPH 3-6kW', 'sph_3000_6000_v201'),
            3735: ('SPA 3-6kW', 'sph_3000_6000_v201'),
            3601: ('SPH-TL3 4-10kW', 'sph_tl3_3000_10000_v201'),
            3725: ('SPA-TL3 4-10kW', 'sph_tl3_3000_10000_v201'),
            5100: ('TL-XH 3-10kW', 'tl_xh_3000_10000_v201'),
            5200: ('MIN/MIC 2.5-6kW', 'min_3000_6000_tl_x_v201'),
            5201: ('MIN 7-10kW', 'min_7000_10000_tl_x_v201'),
            5400: ('MOD-XH/MID-XH', 'mod_6000_15000tl3_xh_v201'),
            5603: ('WIT 4-15kW Hybrid', 'wit_4000_15000tl3'),
            5601: ('WIT 100kW Commercial', 'mid_15000_25000tl3_x_v201'),
            5800: ('WIS 215kW Commercial', 'mid_15000_25000tl3_x_v201'),
        }

        if dtc_code in dtc_map:
            model_name, profile_key = dtc_map[dtc_code]
            detection["model"] = f"{model_name} (DTC {dtc_code})"
            detection["profile_key"] = profile_key
            detection["confidence"] = "Very High"
            detection["reasoning"].append(f"✓ DTC {dtc_code} matches: {model_name}")
            detection["reasoning"].append("  → Auto-detection via DTC is most reliable method")
        else:
            detection["reasoning"].append(f"⚠ Unknown DTC code {dtc_code} - not in supported models")

    # Check for protocol version (holding register 30099)
    if 30099 in register_data and register_data[30099]['status'] == 'success' and register_data[30099]['value']:
        protocol_ver = register_data[30099]['value']
        detection["protocol_version"] = protocol_ver
        protocol_str = f"{protocol_ver // 100}.{protocol_ver % 100:02d}" if protocol_ver >= 100 else str(protocol_ver)
        detection["reasoning"].append(f"✓ Protocol Version: {protocol_str} (register 30099 = {protocol_ver})")

        if protocol_ver >= 201:
            detection["reasoning"].append(f"  → VPP Protocol V{protocol_str} - supports advanced features")

    # If DTC detected model, skip other detection logic
    if detection["confidence"] == "Very High":
        return detection
    
    # Check register ranges (only successful reads with non-zero values)
    has_0_124 = any(0 <= r <= 124 and register_data[r]['status'] == 'success' and register_data[r]['value'] > 0 for r in register_data.keys())
    has_1000_1124 = any(1000 <= r <= 1124 and register_data[r]['status'] == 'success' and register_data[r]['value'] > 0 for r in register_data.keys())
    has_3000_3124 = any(3000 <= r <= 3124 and register_data[r]['status'] == 'success' and register_data[r]['value'] > 0 for r in register_data.keys())
    has_3125_3249 = any(3125 <= r <= 3249 and register_data[r]['status'] == 'success' and register_data[r]['value'] > 0 for r in register_data.keys())
    
    # Key register checks
    has_pv1_at_3 = has_reg(3)  # PV1 voltage in 0-124 range
    has_pv1_at_3003 = has_reg(3003)  # PV1 voltage in 3000 range
    has_pv3_at_11 = has_reg(11)  # PV3 voltage in 0-124 range
    has_pv3_at_3011 = has_reg(3011)  # PV3 voltage in 3000 range
    has_battery_at_13 = has_reg(13)  # Battery voltage in 0-124 range (SPH)
    has_battery_at_1013 = has_reg(1013)  # Battery voltage in 1000 range (SPH TL3)
    has_battery_at_3169 = has_reg(3169)  # Battery voltage in 3000 range (MOD)
    has_phase_s = has_reg(42)  # S-phase voltage
    has_phase_t = has_reg(46)  # T-phase voltage
    has_storage_range = has_1000_1124  # Storage registers
    
    # DETECTION LOGIC
    
    # Check for MIN or MOD series (3000 range)
    if has_pv1_at_3003:
        detection["reasoning"].append("✓ Found PV1 at register 3003 (3000 range detected)")

        if has_battery_at_3169:
            # MOD-XH series - 3-phase hybrid with battery
            detection["model"] = "MOD 6000-15000TL3-XH (Hybrid)"
            detection["confidence"] = "High"
            detection["profile_key"] = "mod_6000_15000tl3_xh"
            detection["register_map"] = "MOD_6000_15000TL3_XH"
            detection["reasoning"].append("✓ Found battery at register 3169 (SOC > 0) → MOD-XH hybrid")
            if has_pv3_at_3011:
                detection["reasoning"].append("✓ Found PV3 at register 3011 → Confirms 3-string MOD")

        else:
            # No battery - could be MIN (single/3-phase) or MOD-X (3-phase grid-tied)
            if has_phase_s and has_phase_t:
                # 3-phase without battery = MOD-X grid-tied
                detection["model"] = "MOD 6000-15000TL3-X (Grid-Tied)"
                detection["confidence"] = "High"
                detection["profile_key"] = "mod_6000_15000tl3_x"
                detection["register_map"] = "MOD_6000_15000TL3_X"
                detection["reasoning"].append("✓ Found 3-phase (registers 42, 46) without battery → MOD-X grid-tied")
                if has_pv3_at_3011:
                    detection["reasoning"].append("✓ Found PV3 at register 3011 → Confirms 3-string MOD")
            elif has_pv3_at_3011:
                # Single-phase with 3 PV strings = MIN 7-10kW
                detection["model"] = "MIN 7000-10000TL-X"
                detection["confidence"] = "High"
                detection["profile_key"] = "min_7000_10000_tl_x"
                detection["register_map"] = "MIN_7000_10000TL_X"
                detection["reasoning"].append("✓ Found PV3 at register 3011 → MIN 7-10kW (3 PV strings)")
            else:
                # Single-phase with 2 PV strings = MIN 3-6kW
                detection["model"] = "MIN 3000-6000TL-X"
                detection["confidence"] = "High"
                detection["profile_key"] = "min_3000_6000_tl_x"
                detection["register_map"] = "MIN_3000_6000TL_X"
                detection["reasoning"].append("✗ No PV3 at register 3011 → MIN 3-6kW (2 PV strings)")
    
    # Check for SPH, SPH TL3, or MID/MAX/MAC series (0-124 range)
    elif has_pv1_at_3:
        detection["reasoning"].append("✓ Found PV1 at register 3 (0-124 base range detected)")
        
        if not has_1000_1124 and not has_3000_3124 and not has_3125_3249:
        # Only base range responds, no extended ranges → MIC micro inverter
            detection["model"] = "MIC 600-3300TL-X"
            detection["confidence"] = "High"
            detection["profile_key"] = "mic_600_3300tl_x"
            detection["register_map"] = "MIC_600_3300TL_X"
            detection["reasoning"].append("✓ Only 0-179 register range responds → MIC micro inverter (V3.05 protocol)")
            detection["reasoning"].append("✓ Single PV string, legacy protocol from 2013")

        # Check for battery (SPH series)
        elif has_battery_at_13 or has_battery_at_1013 or has_storage_range:
            detection["reasoning"].append("✓ Battery detected → SPH hybrid series")
            
            # Check for 3-phase
            if has_phase_s and has_phase_t:
                detection["reasoning"].append("✓ Found S-phase (42) and T-phase (46) → 3-phase inverter")
                
                # Check for storage range to confirm SPH TL3
                if has_storage_range:
                    detection["model"] = "SPH-TL3 3000-10000"
                    detection["confidence"] = "High"
                    detection["profile_key"] = "sph_tl3_3000_10000"
                    detection["register_map"] = "SPH_TL3_3000_10000"
                    detection["reasoning"].append("✓ Found storage range (1000-1124) → SPH TL3 (3-phase hybrid)")
                else:
                    detection["model"] = "SPH-TL3 3000-10000 (or MOD)"
                    detection["confidence"] = "Medium"
                    detection["profile_key"] = "sph_tl3_3000_10000"
                    detection["register_map"] = "SPH_TL3_3000_10000"
                    detection["reasoning"].append("⚠ No storage range but 3-phase + battery → likely SPH TL3")
            
            else:
                # Single-phase SPH
                detection["reasoning"].append("✗ No 3-phase detected → Single-phase SPH")
                
                if has_storage_range or has_battery_at_1013:
                    detection["model"] = "SPH 7000-10000"
                    detection["confidence"] = "High"
                    detection["profile_key"] = "sph_7000_10000"
                    detection["register_map"] = "SPH_7000_10000"
                    detection["reasoning"].append("✓ Storage range or battery at 1013 → SPH 7-10kW")
                else:
                    detection["model"] = "SPH 3000-6000"
                    detection["confidence"] = "High"
                    detection["profile_key"] = "sph_3000_6000"
                    detection["register_map"] = "SPH_3000_6000"
                    detection["reasoning"].append("✗ No storage range → SPH 3-6kW")
        
        # No battery - check for 3-phase grid-tied (MID/MAX/MAC)
        elif has_phase_s and has_phase_t:
            detection["model"] = "MID/MAX/MAC Series (3-phase)"
            detection["confidence"] = "Medium"
            detection["profile_key"] = "mid_15000_25000tl3_x"
            detection["register_map"] = "MID_15000_25000TL3_X"
            detection["reasoning"].append("✓ 3-phase detected without battery → MID/MAX/MAC series")
            detection["reasoning"].append("⚠ Cannot distinguish between MID/MAX/MAC without power rating")
        
        else:
            # Single-phase without clear battery - might be SPH or other
            detection["model"] = "SPH or TL-XH Series (Single-phase)"
            detection["confidence"] = "Low"
            detection["profile_key"] = "sph_3000_6000"
            detection["register_map"] = "SPH_3000_6000"
            detection["reasoning"].append("⚠ Single-phase in 0-124 range without clear battery signature")
    
    else:
        # FALLBACK DETECTION for night/standby mode (no PV voltage detected)
        detection["reasoning"].append("✗ No PV1 voltage found in expected registers (3 or 3003)")
        detection["reasoning"].append("⚠ Inverter may be off, in standby, or scanning at night")

        # Try to detect based on other indicators and range responses
        if has_0_124 or has_1000_1124 or has_3000_3124:
            detection["reasoning"].append("✓ However, some registers responded - attempting fallback detection...")

            # Check for 3-phase + battery + storage range → SPH TL3
            if has_phase_s and has_phase_t and (has_storage_range or has_battery_at_1013):
                detection["model"] = "SPH-TL3 3000-10000 (Night/Standby Mode)"
                detection["confidence"] = "Medium"
                detection["profile_key"] = "sph_tl3_3000_10000"
                detection["register_map"] = "SPH_TL3_3000_10000"
                detection["reasoning"].append("✓ Found S-phase (42) and T-phase (46) → 3-phase inverter")
                detection["reasoning"].append("✓ Found storage range (1000-1124) or battery at 1013 → SPH TL3")
                detection["reasoning"].append("⚠ No PV voltage detected → likely night or standby mode")

            # Check for single-phase battery system (SPH)
            elif (has_battery_at_13 or has_battery_at_1013 or has_storage_range) and has_0_124:
                if has_storage_range or has_battery_at_1013:
                    detection["model"] = "SPH 7000-10000 (Night/Standby Mode)"
                    detection["confidence"] = "Medium"
                    detection["profile_key"] = "sph_7000_10000"
                    detection["register_map"] = "SPH_7000_10000"
                    detection["reasoning"].append("✓ Found battery indicators in storage range → SPH 7-10kW")
                else:
                    detection["model"] = "SPH 3000-6000 (Night/Standby Mode)"
                    detection["confidence"] = "Medium"
                    detection["profile_key"] = "sph_3000_6000"
                    detection["register_map"] = "SPH_3000_6000"
                    detection["reasoning"].append("✓ Found battery at register 13 → SPH 3-6kW")
                detection["reasoning"].append("✗ No 3-phase detected → Single-phase SPH")
                detection["reasoning"].append("⚠ No PV voltage detected → likely night or standby mode")

            # Check for 3000 range responses (MIN/MOD series in standby)
            elif has_3000_3124 or has_3125_3249:
                if has_battery_at_3169:
                    detection["model"] = "MOD 6000-15000TL3-XH (Hybrid, Night/Standby)"
                    detection["confidence"] = "Medium"
                    detection["profile_key"] = "mod_6000_15000tl3_xh"
                    detection["register_map"] = "MOD_6000_15000TL3_XH"
                    detection["reasoning"].append("✓ Found battery at register 3169 → MOD-XH hybrid")
                else:
                    # No battery - check for 3-phase to distinguish MOD-X from MIN
                    if has_phase_s and has_phase_t:
                        detection["model"] = "MOD 6000-15000TL3-X (Grid-Tied, Night/Standby)"
                        detection["confidence"] = "Medium"
                        detection["profile_key"] = "mod_6000_15000tl3_x"
                        detection["register_map"] = "MOD_6000_15000TL3_X"
                        detection["reasoning"].append("✓ Found 3-phase without battery → MOD-X grid-tied")
                    else:
                        detection["model"] = "MIN Series (Night/Standby Mode)"
                        detection["confidence"] = "Low"
                        detection["profile_key"] = "min_3000_6000_tl_x"
                        detection["register_map"] = "MIN_3000_6000TL_X"
                        detection["reasoning"].append("✓ Found 3000 range without battery/3-phase → MIN series")
                detection["reasoning"].append("⚠ No PV voltage detected → likely night or standby mode")

            # Check for 3-phase grid-tied based on phase detection alone
            elif has_phase_s and has_phase_t and has_0_124:
                detection["model"] = "MID/MAX/MAC Series (Night/Standby Mode)"
                detection["confidence"] = "Low"
                detection["profile_key"] = "mid_15000_25000tl3_x"
                detection["register_map"] = "MID_15000_25000TL3_X"
                detection["reasoning"].append("✓ Found S-phase (42) and T-phase (46) → 3-phase inverter")
                detection["reasoning"].append("✗ No battery detected → Grid-tied MID/MAX/MAC series")
                detection["reasoning"].append("⚠ No PV voltage detected → likely night or standby mode")

            # Generic detection based on range responses only
            else:
                detection["model"] = "Unknown Growatt (Registers Responding)"
                detection["confidence"] = "Very Low"
                detection["reasoning"].append("✓ Some registers responded but cannot determine specific model")
                if has_0_124:
                    detection["reasoning"].append("  - Base range (0-124) responding")
                if has_1000_1124:
                    detection["reasoning"].append("  - Storage range (1000-1124) responding")
                if has_3000_3124:
                    detection["reasoning"].append("  - MIN/MOD range (3000-3124) responding")
                if has_3125_3249:
                    detection["reasoning"].append("  - MOD extended range (3125-3249) responding")
                detection["reasoning"].append("⚠ Try scanning during daytime when PV is generating for better detection")

    return detection


def _export_registers_to_csv(hass, connection_type: str, host: str, port: int, device: str, baudrate: int, slave_id: int, offgrid_mode: bool = False, coordinator=None) -> dict:
    """
    Export all registers to CSV file with auto-detection (blocking).

    Args:
        connection_type: 'tcp' or 'serial'
        host: IP address for TCP connection
        port: Port for TCP connection
        device: Serial device path for serial connection
        baudrate: Serial baudrate for serial connection
        slave_id: Modbus slave ID
        offgrid_mode: If True, skip VPP registers (30000+, 31000+) to prevent SPF power resets
        coordinator: Optional coordinator to include entity values in CSV
    """
    result = {
        "success": False,
        "filename": "",
        "total_registers": 0,
        "non_zero": 0,
        "responding_ranges": 0,
    }

    try:
        # Connect with appropriate client type
        if connection_type == "tcp":
            try:
                from pymodbus.client import ModbusTcpClient
            except ImportError:
                from pymodbus.client.sync import ModbusTcpClient

            client = ModbusTcpClient(host=host, port=port, timeout=15)
            connection_str = f"{host}:{port}"
        else:  # serial
            try:
                from pymodbus.client import ModbusSerialClient
            except ImportError:
                from pymodbus.client.sync import ModbusSerialClient

            client = ModbusSerialClient(
                port=device,
                baudrate=baudrate,
                timeout=15,
                parity='N',
                stopbits=1,
                bytesize=8
            )
            connection_str = f"{device} @ {baudrate} baud"

        if not client.connect():
            result["error"] = f"Cannot connect to {connection_str}"
            return result

        mode_str = "OffGrid scan (safe for SPF)" if offgrid_mode else "universal scan"
        _LOGGER.info(f"Connected, starting {mode_str}...")

        # Scan ALL ranges
        all_register_data = {}
        range_responses = {}

        # FIRST: Read DTC code and protocol version (holding registers - critical for identification)
        # SKIP if OffGrid mode to prevent SPF power resets!
        if not offgrid_mode:
            _LOGGER.info("Reading identification registers (DTC code, protocol version)...")
            id_registers = _read_registers_chunked(client, 30000, 100, slave_id, chunk_size=50, register_type='holding')
            if id_registers:
                all_register_data.update(id_registers)
                dtc_found = 30000 in id_registers and id_registers[30000]['status'] == 'success' and id_registers[30000]['value']
                protocol_found = 30099 in id_registers and id_registers[30099]['status'] == 'success' and id_registers[30099]['value']
                if dtc_found or protocol_found:
                    _LOGGER.info(f"  DTC: {id_registers[30000]['value'] if dtc_found else 'Not found'}")
                    _LOGGER.info(f"  Protocol: {id_registers[30099]['value'] if protocol_found else 'Not found'}")
                    range_responses["VPP Identification (30000-30099)"] = 1 if (dtc_found or protocol_found) else 0
                else:
                    _LOGGER.info("  No identification registers found (likely legacy protocol)")
                    range_responses["VPP Identification (30000-30099)"] = 0
            else:
                range_responses["VPP Identification (30000-30099)"] = 0
        else:
            _LOGGER.info("⚠️ Skipping VPP identification registers (OffGrid mode)")
            range_responses["VPP Identification (SKIPPED - OffGrid mode)"] = 0

        # THEN: Scan input register ranges - use safe ranges for OffGrid mode
        scan_ranges = OFFGRID_SCAN_RANGES if offgrid_mode else UNIVERSAL_SCAN_RANGES

        for range_config in scan_ranges:
            range_name = range_config["name"]
            start = range_config["start"]
            count = range_config["count"]

            _LOGGER.info(f"Scanning {range_name}...")

            registers = _read_registers_chunked(client, start, count, slave_id, chunk_size=50, register_type='input')

            if registers:
                all_register_data.update(registers)
                # Count successful non-zero reads for range summary
                successful_count = sum(1 for r in registers.values() if r['status'] == 'success' and r['value'] > 0)
                range_responses[range_name] = successful_count
                _LOGGER.info(f"{range_name}: {successful_count} non-zero registers out of {len(registers)} attempted")
            else:
                range_responses[range_name] = 0
                _LOGGER.info(f"{range_name}: No response")

        # Scan holding registers for OffGrid mode (up to register 426)
        if offgrid_mode:
            _LOGGER.info("Scanning OffGrid holding registers (0-426)...")
            offgrid_holding_ranges = [
                {"name": "OffGrid Holding 0-124", "start": 0, "count": 125},
                {"name": "OffGrid Holding 125-249", "start": 125, "count": 125},
                {"name": "OffGrid Holding 250-374", "start": 250, "count": 125},
                {"name": "OffGrid Holding 375-426", "start": 375, "count": 52},  # Up to 426
            ]

            for range_config in offgrid_holding_ranges:
                range_name = range_config["name"]
                start = range_config["start"]
                count = range_config["count"]

                _LOGGER.info(f"Scanning {range_name}...")

                registers = _read_registers_chunked(client, start, count, slave_id, chunk_size=50, register_type='holding')

                if registers:
                    all_register_data.update(registers)
                    # Count successful non-zero reads for range summary
                    successful_count = sum(1 for r in registers.values() if r['status'] == 'success' and r['value'] > 0)
                    range_responses[range_name] = successful_count
                    _LOGGER.info(f"{range_name}: {successful_count} non-zero registers out of {len(registers)} attempted")
                else:
                    range_responses[range_name] = 0
                    _LOGGER.info(f"{range_name}: No response")

        client.close()

        # Auto-detect model
        detection = _detect_inverter_model(all_register_data)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"growatt_register_scan_{timestamp}.csv"
        filepath = hass.config.path(filename)
        
        # Write CSV
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Metadata section
            writer.writerow(["SCAN METADATA"])
            writer.writerow(["Integration Version", _get_integration_version()])
            writer.writerow(["Timestamp", datetime.now().isoformat()])
            writer.writerow(["Connection", connection_str])
            writer.writerow(["Connection Type", connection_type.upper()])
            writer.writerow(["Slave ID", slave_id])
            writer.writerow([])
            
            # Detection analysis section
            writer.writerow(["DETECTION ANALYSIS"])
            writer.writerow(["Detected Model", detection["model"]])
            writer.writerow(["Confidence", detection["confidence"]])

            # Add DTC code and protocol version if available
            if detection.get("dtc_code"):
                writer.writerow(["DTC Code", detection["dtc_code"]])
            if detection.get("protocol_version"):
                protocol_ver = detection["protocol_version"]
                protocol_str = f"{protocol_ver // 100}.{protocol_ver % 100:02d}" if protocol_ver >= 100 else str(protocol_ver)
                writer.writerow(["Protocol Version", f"V{protocol_str} (register value: {protocol_ver})"])

            writer.writerow(["Suggested Profile Key", detection["profile_key"]])
            writer.writerow(["Register Map", detection["register_map"]])
            writer.writerow([])
            writer.writerow(["Detection Reasoning:"])
            for reason in detection["reasoning"]:
                writer.writerow(["", reason])
            writer.writerow([])
            
            # Range summary
            writer.writerow(["RANGE SUMMARY"])
            for range_name, count in range_responses.items():
                status = "✓ Responding" if count > 0 else "✗ No response"
                writer.writerow([range_name, status, f"{count} registers" if count > 0 else ""])
            writer.writerow([])
            
            # Register data header
            writer.writerow(["REGISTER DATA"])
            writer.writerow([])

            # Add Entity Value column header if coordinator is available
            header_row = [
                "Register",
                "Hex",
                "Raw Value",
                "×0.1",
                "×0.01",
                "Signed",
                "32-bit Combined (with next reg)",
                "Entity Value",
                "Suggested Match",
                "Status/Comment"
            ]
            writer.writerow(header_row)
            
            # Write all registers sorted by address
            total = 0
            non_zero = 0

            # FIRST: Write holding registers (30000-30099) - Identification
            id_range_registers = {k: v for k, v in all_register_data.items() if 30000 <= k < 30100}
            if id_range_registers:
                writer.writerow([])
                writer.writerow([f"--- VPP Identification (Holding Registers 30000-30099) ---"])
                for reg_addr in range(30000, 30100):
                    if reg_addr in id_range_registers:
                        reg_info = id_range_registers[reg_addr]
                        value = reg_info['value']
                        status = reg_info['status']
                        error = reg_info['error']

                        total += 1

                        # Build status/comment field
                        if status == 'success':
                            if value == 0:
                                status_comment = "Read OK (zero value)"
                            else:
                                status_comment = "Read OK"
                                non_zero += 1

                            # Special handling for known registers
                            if reg_addr == 30000 and value:
                                status_comment += f" [DTC Code - Device Type: {value}]"
                            elif reg_addr == 30099 and value:
                                protocol_str = f"{value // 100}.{value % 100:02d}" if value >= 100 else str(value)
                                status_comment += f" [Protocol Version V{protocol_str}]"

                        elif status == 'error':
                            status_comment = f"Modbus Error: {error}"
                            value = ""  # Clear value field for errors
                        else:  # exception
                            status_comment = error
                            value = ""  # Clear value field for exceptions

                        # Calculate interpretations only for successful reads
                        if status == 'success' and value is not None:
                            scaled_01 = value * 0.1
                            scaled_001 = value * 0.01
                            signed = value - 65536 if value > 32767 else value
                            combined_32bit = ""  # Not relevant for these registers
                        else:
                            scaled_01 = ""
                            scaled_001 = ""
                            signed = ""
                            combined_32bit = ""

                        # Look up entity value from coordinator if available
                        entity_value = _get_entity_value_for_register(reg_addr, coordinator, 'holding') or ""

                        # Look up suggested match from register map
                        suggested_match = _lookup_register_info(reg_addr) or ""

                        # Add manual descriptions for key registers
                        if reg_addr == 30000:
                            suggested_match = "dtc_code (Device Type Code)"
                        elif reg_addr == 30099:
                            suggested_match = "protocol_version (VPP Protocol Version)"

                        writer.writerow([
                            reg_addr,
                            f"0x{reg_addr:04X}",
                            value,
                            f"{scaled_01:.1f}" if scaled_01 != "" else "",
                            f"{scaled_001:.2f}" if scaled_001 != "" else "",
                            signed,
                            combined_32bit,
                            entity_value,
                            suggested_match,
                            status_comment
                        ])

            # THEN: Group by input register ranges for organized output
            for range_config in UNIVERSAL_SCAN_RANGES:
                range_name = range_config["name"]
                start = range_config["start"]
                end = start + range_config["count"]

                # Get all registers in this range
                range_registers = {k: v for k, v in all_register_data.items() if start <= k < end}

                if range_registers:
                    writer.writerow([])
                    writer.writerow([f"--- {range_name} ---"])

                    # Write ALL registers in sequential order
                    for reg_addr in range(start, end):
                        if reg_addr in range_registers:
                            reg_info = range_registers[reg_addr]
                            value = reg_info['value']
                            status = reg_info['status']
                            error = reg_info['error']

                            total += 1

                            # Build status/comment field
                            if status == 'success':
                                if value == 0:
                                    status_comment = "Read OK (zero value)"
                                else:
                                    status_comment = "Read OK"
                                    non_zero += 1
                            elif status == 'error':
                                status_comment = f"Modbus Error: {error}"
                                value = ""  # Clear value field for errors
                            else:  # exception
                                status_comment = error
                                value = ""  # Clear value field for exceptions

                            # Calculate interpretations only for successful reads
                            if status == 'success' and value is not None:
                                scaled_01 = value * 0.1
                                scaled_001 = value * 0.01
                                signed = value - 65536 if value > 32767 else value

                                # Try to combine with next register for 32-bit values
                                combined_32bit = ""
                                if reg_addr + 1 in all_register_data:
                                    next_info = all_register_data[reg_addr + 1]
                                    if next_info['status'] == 'success' and next_info['value'] is not None:
                                        next_val = next_info['value']
                                        combined = (value << 16) | next_val
                                        if 0 < combined < 10000000:
                                            combined_32bit = f"{combined} (×0.1={combined*0.1:.1f})"
                            else:
                                scaled_01 = ""
                                scaled_001 = ""
                                signed = ""
                                combined_32bit = ""

                            # Look up entity value from coordinator if available
                            entity_value = _get_entity_value_for_register(reg_addr, coordinator, 'input') or ""

                            # Look up suggested match from register map
                            suggested_match = _lookup_register_info(reg_addr) or ""

                            writer.writerow([
                                reg_addr,
                                f"0x{reg_addr:04X}",
                                value,
                                f"{scaled_01:.1f}" if scaled_01 != "" else "",
                                f"{scaled_001:.2f}" if scaled_001 != "" else "",
                                signed,
                                combined_32bit,
                                entity_value,
                                suggested_match,
                                status_comment
                            ])
        
        result["success"] = True
        result["filename"] = filename
        result["total_registers"] = total
        result["non_zero"] = non_zero
        result["responding_ranges"] = sum(1 for count in range_responses.values() if count > 0)
        result["detection"] = detection
        
        _LOGGER.info(f"Universal scan complete: {filename}")
        _LOGGER.info(f"Detected: {detection['model']} (confidence: {detection['confidence']})")
        
        return result
        
    except Exception as e:
        _LOGGER.error(f"Universal scan failed: {e}")
        result["error"] = str(e)
        return result