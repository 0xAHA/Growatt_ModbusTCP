"""Diagnostic service for Growatt Modbus Integration."""
import logging
import csv
import json
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple, Optional

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.helpers import device_registry as dr
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN, CONF_INVERTER_SERIES
from .device_profiles import get_display_name_for_profile, get_profile
from .auto_detection import convert_to_legacy_profile

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
SERVICE_WRITE_REGISTERS = "write_registers"
SERVICE_DETECT_GRID_ORIENTATION = "detect_grid_orientation"
SERVICE_READ_REGISTER = "read_register"
SERVICE_SET_BATTERY_MODE = "set_battery_mode"
SERVICE_SYNC_TOU_SCHEDULE = "sync_tou_schedule"
SERVICE_GET_REGISTER_DATA = "get_register_data"

# Universal scan ranges - covers all Grid-Tied Growatt series
# Split into chunks of max 125 registers to respect Modbus limits
UNIVERSAL_SCAN_RANGES = [
    # Legacy protocol ranges (all grid-tied/hybrid models)
    {"name": "Base Range 0-124",         "start": 0,     "count": 125, "group": "legacy"},
    {"name": "Extended Range 125-249",   "start": 125,   "count": 125, "group": "legacy"},
    # Battery/storage range (SPH, SPM, MIN battery models)
    {"name": "Storage Range 1000-1124",  "start": 1000,  "count": 125, "group": "storage"},
    # MIN/MOD extended data ranges (input registers FC03)
    {"name": "MIN/MOD Range 3000-3124",         "start": 3000, "count": 125, "group": "mod_extended"},
    {"name": "MOD Extended 3125-3249",          "start": 3125, "count": 125, "group": "mod_extended"},
    {"name": "MOD Extended Input 3250-3374",    "start": 3250, "count": 125, "group": "mod_extended"},
    # Legacy holding registers — writable controls present on all grid-tied/hybrid models
    # (TOU schedule, charge/discharge control, AC charge enable, priority mode, etc.)
    {"name": "Legacy Holding 0-124",    "start": 0,    "count": 125, "group": "legacy",  "register_type": "holding"},
    {"name": "Legacy Holding 1000-1124","start": 1000, "count": 125, "group": "storage", "register_type": "holding"},
    # MOD TL3-XH holding registers (FC04) — includes TOU schedule (3038-3045) and other settings
    {"name": "MOD Holding 3000-3124",           "start": 3000, "count": 125, "group": "mod_extended", "register_type": "holding"},
    {"name": "MOD Holding 3125-3249",           "start": 3125, "count": 125, "group": "mod_extended", "register_type": "holding"},
    {"name": "MOD Extended Holding 3250-3374",  "start": 3250, "count": 125, "group": "mod_extended", "register_type": "holding"},
    # WIT/WIS battery range
    {"name": "WIT/WIS Battery Range 8000-8124", "start": 8000, "count": 125, "group": "wit"},
    # VPP Control holding registers (30100-30499) — system/AC/battery control settings
    {"name": "VPP System Control 30100-30129",  "start": 30100, "count": 30,  "group": "vpp_control", "register_type": "holding"},
    {"name": "VPP AC Control 30150-30216",      "start": 30150, "count": 67,  "group": "vpp_control", "register_type": "holding"},
    {"name": "VPP Battery Control 30300-30424", "start": 30300, "count": 125, "group": "vpp_control", "register_type": "holding"},
    {"name": "VPP Battery Control 30425-30499", "start": 30425, "count": 75,  "group": "vpp_control", "register_type": "holding"},
    # VPP Protocol V2.01 data ranges (31000+)
    {"name": "VPP Status/PV: 31000-31099",       "start": 31000, "count": 100, "group": "vpp_data"},  # Equipment status, PV data, faults
    {"name": "VPP AC/Grid/Load: 31100-31199",    "start": 31100, "count": 100, "group": "vpp_data"},  # AC output, meter/grid power, load power, energy, temps
    {"name": "VPP Battery 1: 31200-31299",       "start": 31200, "count": 100, "group": "vpp_data"},  # Battery cluster 1 data
    {"name": "VPP Battery 2: 31300-31399",       "start": 31300, "count": 100, "group": "vpp_data"},  # Battery cluster 2 data (optional)
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
        # Optional: select a configured integration entry to pre-fill connection details.
        # When provided, connection_type/host/port/device/baudrate/slave_id are all ignored —
        # they are read directly from the config entry. Profile and entity values are always
        # included. When omitted, manual connection parameters below are required.
        vol.Optional("config_entry"): cv.string,

        # Connection type selection (ignored when config_entry is set)
        vol.Optional("connection_type", default="tcp"): vol.In(["tcp", "serial"]),

        # TCP parameters (required if connection_type=tcp and no config_entry)
        vol.Optional("host"): cv.string,
        vol.Optional("port", default=502): cv.port,

        # Serial parameters (required if connection_type=serial and no config_entry)
        vol.Optional("device"): cv.string,  # e.g., /dev/ttyUSB0, COM3
        vol.Optional("baudrate", default=9600): vol.All(vol.Coerce(int), vol.In([4800, 9600, 19200, 38400, 57600, 115200])),

        # Common parameters (ignored when config_entry is set — slave_id read from entry)
        vol.Optional("slave_id", default=1): vol.All(vol.Coerce(int), vol.Range(min=1, max=247)),
        vol.Optional("notify", default=True): cv.boolean,
        vol.Optional("offgrid_mode", default=False): cv.boolean,  # CRITICAL: Enable for SPF to prevent power reset
        # Range group selection (all enabled by default)
        vol.Optional("scan_legacy",       default=False): cv.boolean,  # Base 0-249 (all models)
        vol.Optional("scan_storage",      default=False): cv.boolean,  # Storage 1000-1124 (SPH/MIN battery)
        vol.Optional("scan_mod_extended", default=False): cv.boolean,  # MIN/MOD 3000-3249
        vol.Optional("scan_wit",          default=False): cv.boolean,  # WIT/WIS 8000-8124
        vol.Optional("scan_vpp_control",  default=False): cv.boolean,  # VPP control 30100-30499
        vol.Optional("scan_vpp_data",     default=False): cv.boolean,  # VPP data 31000-31399
        # Block size for range reads: 125 (default, fastest), 25 (for finicky inverters), 1 (single-register, slowest but most compatible)
        vol.Optional("block_size", default=125): vol.All(vol.Coerce(int), vol.In([125, 25, 1])),
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

SERVICE_WRITE_REGISTERS_SCHEMA = vol.Schema(
    {
        vol.Required("device_id"): cv.string,
        vol.Required("register"): vol.All(vol.Coerce(int), vol.Range(min=0, max=65535)),
        vol.Required("values"): vol.All(cv.ensure_list, vol.Length(min=1, max=123), [vol.All(vol.Coerce(int), vol.Range(min=0, max=65535))]),
    }
)

SERVICE_READ_REGISTER_SCHEMA = vol.Schema(
    {
        vol.Required("device_id"): cv.string,
        vol.Required("register"): vol.All(vol.Coerce(int), vol.Range(min=0, max=65535)),
        vol.Optional("register_type", default="input"): vol.In(["input", "holding"]),
    }
)

SERVICE_SET_BATTERY_MODE_SCHEMA = vol.Schema(
    {
        vol.Required("device_id"): cv.string,
        vol.Required("mode"): vol.In(["charge", "discharge", "hold"]),
        vol.Optional("power_percent", default=100): vol.All(vol.Coerce(int), vol.Range(min=1, max=100)),
    }
)

SERVICE_SYNC_TOU_SCHEDULE_SCHEMA = vol.Schema(
    {
        vol.Required("device_id"): cv.string,
        vol.Required("periods"): vol.All(cv.ensure_list, [
            vol.Schema({
                vol.Required("start"): vol.All(vol.Coerce(int), vol.Range(min=0, max=1439)),
                vol.Required("end"): vol.All(vol.Coerce(int), vol.Range(min=0, max=1439)),
                vol.Required("power"): vol.All(vol.Coerce(int), vol.Range(min=-100, max=100)),
            })
        ]),
        vol.Optional("default_mode", default=0): vol.All(vol.Coerce(int), vol.Range(min=0, max=2)),
    }
)
SERVICE_GET_REGISTER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("device_id"): cv.string,
        vol.Optional("register_type", default="input"): vol.In(["input", "holding"]),
        vol.Required("start_address"): vol.All(vol.Coerce(int), vol.Range(min=0, max=65535)),
        vol.Required("count"): vol.All(vol.Coerce(int), vol.Range(min=1, max=50)),
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


def _get_holding_register_name(register_addr: int, coordinator) -> Optional[str]:
    """
    Return the profile-defined name for a holding register.
    Only uses the active profile's holding_registers definition — does NOT fall back
    to input register names, which would be misleading for the same address.
    """
    if coordinator and hasattr(coordinator, '_client') and hasattr(coordinator._client, 'register_map'):
        reg_info = coordinator._client.register_map.get('holding_registers', {}).get(register_addr)
        if reg_info:
            name = reg_info.get('name', '')
            desc = reg_info.get('desc', '')
            if name:
                return f"{name} — {desc}" if desc else name
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
        send_notification = call.data.get("notify", True)
        offgrid_mode = call.data.get("offgrid_mode", False)
        block_size = call.data.get("block_size", 125)

        # Build enabled scan groups from boolean flags.
        # If none are explicitly checked, scan everything (full scan is the default).
        # Check one or more to restrict the scan to those register ranges only.
        _SCAN_FLAGS = {
            "scan_legacy":       "legacy",
            "scan_storage":      "storage",
            "scan_mod_extended": "mod_extended",
            "scan_wit":          "wit",
            "scan_vpp_control":  "vpp_control",
            "scan_vpp_data":     "vpp_data",
        }
        _any_flag_set = any(call.data.get(k) for k in _SCAN_FLAGS)
        enabled_groups = set()
        for flag, group in _SCAN_FLAGS.items():
            if not _any_flag_set or call.data.get(flag):
                enabled_groups.add(group)

        # --- Resolve connection parameters ---
        # If config_entry is provided, pull all connection details directly from the
        # coordinator — no manual entry needed, profile/entity values always included.
        pre_resolved_coordinator = None
        config_entry_id = call.data.get("config_entry")

        if config_entry_id:
            coordinator = hass.data.get(DOMAIN, {}).get(config_entry_id)
            if not coordinator or not hasattr(coordinator, 'entry'):
                _LOGGER.error("config_entry '%s' not found in Growatt Modbus integration", config_entry_id)
                return

            entry_data = coordinator.entry.data
            connection_type = entry_data.get("connection_type", "tcp")
            host = entry_data.get("host")
            port = entry_data.get("port", 502)
            device = entry_data.get("device")
            baudrate = entry_data.get("baudrate", 9600)
            slave_id = entry_data.get("slave_id", 1)
            pre_resolved_coordinator = coordinator
            _LOGGER.info(
                "Using config entry '%s' (%s) for register scan",
                coordinator.entry.title, config_entry_id
            )
        else:
            connection_type = call.data.get("connection_type", "tcp")
            host = call.data.get("host")
            port = call.data.get("port", 502)
            device = call.data.get("device")
            baudrate = call.data.get("baudrate", 9600)
            slave_id = call.data.get("slave_id", 1)

            # Validate required manual parameters
            if connection_type == "tcp":
                if not host:
                    _LOGGER.error("host parameter required for TCP connection (or select a config_entry)")
                    return
            elif connection_type == "serial":
                if not device:
                    _LOGGER.error("device parameter required for serial connection (or select a config_entry)")
                    return

        if offgrid_mode:
            _LOGGER.warning("⚠️ OffGrid mode ENABLED - skipping VPP registers to prevent power reset on SPF inverters")

        # Log connection info
        if connection_type == "tcp":
            _LOGGER.info("Starting %s register scan at %s:%s", "OffGrid" if offgrid_mode else "universal", host, port)
        else:
            _LOGGER.info("Starting %s register scan on %s @ %d baud", "OffGrid" if offgrid_mode else "universal", device, baudrate)

        # Run export in executor — pass pre-resolved coordinator if available
        result = await hass.async_add_executor_job(
            _export_registers_to_csv, hass, connection_type, host, port, device, baudrate, slave_id, offgrid_mode, enabled_groups, pre_resolved_coordinator, block_size
        )
        
        if result["success"]:
            detection = result.get("detection", {})
            confidence = detection.get("confidence", "Unknown")
            model = detection.get("model", "Unknown")
            profile_key = detection.get("profile_key", "N/A")
            dtc_code = detection.get("dtc_code")
            protocol_version = detection.get("protocol_version")
            firmware_version = result.get("firmware_version")

            message_lines = [
                f"**File saved:** `{result['filename']}`\n",
                f"**Detected Model:** {model}",
                f"**Confidence:** {confidence}",
            ]

            # Add DTC/Protocol/Firmware info — always show both DTC registers
            vpp_dtc = result.get("vpp_dtc")
            leg_dtc = result.get("leg_dtc")
            message_lines.append(f"**VPP DTC (reg 30000):** {'no response' if vpp_dtc is None else vpp_dtc}")
            message_lines.append(f"**Legacy DTC (reg 43):** {'no response' if leg_dtc is None else leg_dtc}")
            if protocol_version:
                protocol_str = f"{protocol_version // 100}.{protocol_version % 100:02d}" if protocol_version >= 100 else str(protocol_version)
                message_lines.append(f"**Protocol:** V{protocol_str}")
            if firmware_version:
                message_lines.append(f"**Firmware:** {firmware_version}")

            message_lines.extend([
                f"**Suggested Profile:** `{profile_key}`\n",
                f"**Scan Results:**",
                f"• Block size: {block_size} registers/request",
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
        from .growatt_modbus import ModbusWriteError

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
        # write_register() raises ModbusWriteError on failure, returns False
        # only for WIT rate limiting
        try:
            success = await hass.async_add_executor_job(
                coordinator._client.write_register, register, value
            )

            if success:
                _LOGGER.info("Successfully wrote value %d to register %d", value, register)
                await coordinator.async_request_refresh()
            else:
                _LOGGER.warning("Write to register %d was rate-limited", register)
                raise ValueError(f"Write to register {register} was rate-limited (WIT cooldown)")

        except ModbusWriteError as e:
            _LOGGER.error("Modbus write error: %s", e.error_message)
            raise ValueError(f"Modbus write failed: {e.error_message}")

    async def write_registers(call: ServiceCall) -> None:
        """Write multiple consecutive Modbus holding registers (function 0x10)."""
        from .growatt_modbus import ModbusWriteError

        device_id = call.data["device_id"]
        register = call.data["register"]
        values = call.data["values"]

        _LOGGER.info("Write registers service called: device=%s, register=%d, values=%s", device_id, register, values)

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

        # Write the registers using the coordinator's client
        # write_registers() always raises ModbusWriteError on failure
        try:
            await hass.async_add_executor_job(
                coordinator._client.write_registers, register, values
            )
            _LOGGER.info("Successfully wrote %d values to registers starting at %d", len(values), register)
            await coordinator.async_request_refresh()

        except ModbusWriteError as e:
            _LOGGER.error("Modbus write error: %s", e.error_message)
            raise ValueError(f"Modbus write failed: {e.error_message}")

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

        # SPH-TL3 specific: Check both power_to_grid AND power_to_user
        # Different CT sensor configs (no sensor/single/dual) affect which registers are active
        power_to_grid = getattr(data, "power_to_grid", 0)
        power_to_user = getattr(data, "power_to_user", 0)

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

        # Determine which register has the actual grid power value
        # Typically one register shows export, the other shows import
        if abs(power_to_grid) > abs(power_to_user):
            # power_to_grid has the dominant value
            raw_grid_power = power_to_grid
            register_name = "power_to_grid"
        else:
            # power_to_user has the dominant value (or they're equal)
            # For import scenarios, power_to_user is typically positive
            # We need to negate it to get the grid power sign
            raw_grid_power = -power_to_user
            register_name = "power_to_user"

        # Analyze grid power sign
        _LOGGER.info(
            "Grid orientation detection: PV=%.0fW, Consumption=%.0fW, "
            "Expected export=%.0fW, power_to_grid=%.0fW, power_to_user=%.0fW, "
            "Using %s=%.0fW",
            pv_power, consumption, expected_export, power_to_grid, power_to_user,
            register_name, raw_grid_power
        )

        # Integration convention: positive = export, negative = import.
        # Inversion is only needed when the inverter itself reports the opposite sign.
        # Most Growatt inverters report positive = export, which requires NO inversion.

        current_invert_setting = coordinator.entry.options.get("invert_grid_power", False)

        if raw_grid_power > 100:
            # Positive while exporting = matches integration convention → no inversion needed
            recommended_invert = False
            confidence = "High"
            explanation = (
                f"Your inverter reports **positive = export** — this matches the integration convention.\n"
                f"Register used: **{register_name}** = {power_to_grid if register_name == 'power_to_grid' else power_to_user:.0f}W\n"
                f"**No inversion needed.**"
            )
        elif raw_grid_power < -100:
            # Negative while exporting = inverter uses opposite sign → inversion needed
            recommended_invert = True
            confidence = "High"
            explanation = (
                f"Your inverter reports **negative = export**, which is opposite to the integration convention.\n"
                f"Register used: **{register_name}** = {power_to_grid if register_name == 'power_to_grid' else power_to_user:.0f}W\n"
                f"**Inversion is needed** to correct the sign."
            )
        else:
            # Close to zero - ambiguous
            confidence = "Low"
            recommended_invert = current_invert_setting  # Keep current
            explanation = (
                f"Grid power too close to zero for reliable detection.\n"
                f"power_to_grid = {power_to_grid:.0f}W, power_to_user = {power_to_user:.0f}W\n"
                f"Try again with higher export levels."
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

        # Get profile name from coordinator client
        profile_name = getattr(coordinator._client, 'register_map_name', 'Unknown')

        message_lines = [
            f"**Register:** {register} (0x{register:04X})",
            f"**Type:** {register_type.capitalize()}",
            f"**Profile:** {profile_name}",
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
                message_lines.append(f"• Scaled Value: {scaled_value:.2f} {unit}")
            else:
                message_lines.append(f"• Scaled Value: {scaled_value:.2f}")

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

                    # Check for combined_scale - may be on current register OR paired register
                    if combined_scale is None and pair in register_dict:
                        pair_info = register_dict[pair]
                        combined_scale = pair_info.get('combined_scale')
                        if combined_unit == '' and combined_scale is not None:
                            combined_unit = pair_info.get('combined_unit', '')

                    # Apply combined scale if specified
                    if combined_scale is not None:
                        combined_computed = combined_raw * combined_scale
                        if combined_unit:
                            message_lines.append(f"• Combined Scale: ×{combined_scale}")
                            message_lines.append(f"• **Computed Value: {combined_computed:.2f} {combined_unit}**")
                        else:
                            message_lines.append(f"• Combined Scale: ×{combined_scale}")
                            message_lines.append(f"• **Computed Value: {combined_computed:.2f}**")
                    else:
                        # No combined scale defined - provide common interpretations
                        message_lines.append(f"• ⚠️ No combined scale defined in profile")
                        message_lines.append(f"\n**Possible Interpretations:**")
                        message_lines.append(f"• ×0.1 = {combined_raw * 0.1:.2f}")
                        message_lines.append(f"• ×0.01 = {combined_raw * 0.01:.2f}")
                        message_lines.append(f"• ×1 = {combined_raw:.2f}")
                else:
                    message_lines.append(f"• ⚠️ Failed to read paired register: {pair_result.get('error', 'Unknown error')}")
        else:
            message_lines.append(f"\n**Profile Info:**")
            message_lines.append(f"• ⚠️ Register {register} not defined in current profile")
            message_lines.append(f"• Profile: `{profile_name}`")

            # Provide common interpretations
            message_lines.append(f"\n**Common Interpretations:**")
            message_lines.append(f"• ×0.1 = {raw_value * 0.1:.2f}")
            message_lines.append(f"• ×0.01 = {raw_value * 0.01:.2f}")
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

    async def set_battery_mode(call: ServiceCall) -> None:
        """Set battery mode via VPP protocol registers (30xxx) for WIT inverters.

        CRITICAL - HOLD Mode Implementation:
        - Simply setting 30407=0 returns to SELF-CONSUMPTION, NOT true HOLD!
        - In self-consumption, battery WILL discharge to supply house load
        - True HOLD requires TOU workaround: Set +1% charge via TOU period
        - This firmware quirk creates actual idle state
        - WARNING: +1% = HOLD, but -1% = FULL DISCHARGE (asymmetric behavior!)
        """
        device_id = call.data["device_id"]
        mode = call.data["mode"]
        power_percent = call.data.get("power_percent", 100)

        _LOGGER.info("Set battery mode service called: device=%s, mode=%s, power=%d%%", device_id, mode, power_percent)

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
            raise ValueError(f"No config entry found for device {device_id}")

        coordinator = hass.data[DOMAIN][config_entry_id]
        if not coordinator:
            _LOGGER.error("Coordinator not found for config entry %s", config_entry_id)
            raise ValueError(f"Coordinator not found for device {device_id}")

        client = coordinator._client

        # VPP Register addresses
        VPP_CONTROL_AUTHORITY = 30100
        VPP_AC_CHARGE_ENABLE = 30410
        VPP_REMOTE_POWER_ENABLE = 30407
        VPP_REMOTE_POWER_PERCENT = 30409
        VPP_TOU_NUM_PERIODS = 30411
        VPP_TOU_PERIOD1_BASE = 30412

        try:
            # Step 1: Enable VPP control authority
            success = await hass.async_add_executor_job(client.write_register, VPP_CONTROL_AUTHORITY, 1)
            if not success:
                _LOGGER.warning("Failed to enable VPP control authority, continuing anyway...")

            if mode == "hold":
                # HOLD: Use TOU +1% charge workaround for TRUE standby
                _LOGGER.debug("Setting HOLD mode via TOU +1%% workaround")

                success = await hass.async_add_executor_job(client.write_register, VPP_AC_CHARGE_ENABLE, 1)
                if not success:
                    _LOGGER.warning("Failed to enable AC charging (30410)")

                from datetime import datetime as dt
                now = dt.now()
                current_minutes = now.hour * 60 + now.minute
                start_min = max(0, current_minutes - 5)
                end_min = min(1439, current_minutes + 120)

                success = await hass.async_add_executor_job(
                    client.write_registers, VPP_TOU_PERIOD1_BASE,
                    [start_min, end_min, 1]  # +1% = HOLD (NOT -1% which = full discharge!)
                )
                if not success:
                    raise ValueError("Failed to write TOU period for HOLD mode")

                success = await hass.async_add_executor_job(client.write_register, VPP_TOU_NUM_PERIODS, 1)
                if not success:
                    raise ValueError("Failed to enable TOU period")

            elif mode == "charge":
                await hass.async_add_executor_job(client.write_register, VPP_TOU_NUM_PERIODS, 0)

                success = await hass.async_add_executor_job(client.write_register, VPP_AC_CHARGE_ENABLE, 1)
                if not success:
                    _LOGGER.warning("Failed to enable AC charging (30410)")

                success = await hass.async_add_executor_job(client.write_register, VPP_REMOTE_POWER_ENABLE, 1)
                if not success:
                    raise ValueError("Failed to enable remote power control")

                success = await hass.async_add_executor_job(client.write_register, VPP_REMOTE_POWER_PERCENT, power_percent)
                if not success:
                    raise ValueError("Failed to set charge power percentage")

            elif mode == "discharge":
                await hass.async_add_executor_job(client.write_register, VPP_TOU_NUM_PERIODS, 0)

                success = await hass.async_add_executor_job(client.write_register, VPP_REMOTE_POWER_ENABLE, 1)
                if not success:
                    raise ValueError("Failed to enable remote power control")

                power_value = 65536 - power_percent  # -100 becomes 65436
                success = await hass.async_add_executor_job(client.write_register, VPP_REMOTE_POWER_PERCENT, power_value)
                if not success:
                    raise ValueError("Failed to set discharge power percentage")

            _LOGGER.info("Successfully set battery mode to %s at %d%%", mode.upper(), power_percent)
            await coordinator.async_request_refresh()

        except Exception as e:
            _LOGGER.error("Failed to set battery mode: %s", e)
            raise ValueError(f"Failed to set battery mode: {e}")

    async def get_register_data(call: ServiceCall):
        """Read specific Modbus registers and return values programmatically."""
        device_id = call.data["device_id"]
        register_type = call.data.get("register_type", "input")
        start_address = call.data["start_address"]
        count = call.data["count"]

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
            raise ValueError(f"No config entry found for device {device_id}")

        coordinator = hass.data[DOMAIN][config_entry_id]
        if not coordinator:
            _LOGGER.error("Coordinator not found for config entry %s", config_entry_id)
            raise ValueError(f"Coordinator not found for device {device_id}")

        client = coordinator._client

        def _read():
            if register_type == "holding":
                return client.read_holding_registers(start_address=start_address, count=count)
            else:
                return client.read_input_registers(start_address=start_address, count=count)

        result = await hass.async_add_executor_job(_read)

        if result is not None:
            values = list(result) if not isinstance(result, list) else result
            return {"success": True, "values": values}
        else:
            return {"success": False, "values": [], "error": "Register read failed"}

    async def sync_tou_schedule(call: ServiceCall) -> None:
        """Sync TOU schedule to inverter registers for autonomous operation.

        CRITICAL: TOU periods CANNOT overlap or touch!
        - End times should be XX:59 format (e.g., 359 = 05:59)
        - Next period starts at XX:00 (e.g., 360 = 06:00)
        - The inverter will REJECT writes if periods overlap!

        For HOLD mode, use power=1 (+1% charge = true standby)
        """
        device_id = call.data["device_id"]
        periods = call.data["periods"]
        default_mode = call.data.get("default_mode", 0)

        _LOGGER.info("Sync TOU schedule service called: device=%s, %d periods, default_mode=%d",
                     device_id, len(periods), default_mode)

        if len(periods) > 20:
            raise ValueError("Maximum 20 TOU periods supported")

        # Validate periods don't overlap
        sorted_periods = sorted(periods, key=lambda p: p["start"])
        for i in range(len(sorted_periods) - 1):
            current_end = sorted_periods[i]["end"]
            next_start = sorted_periods[i + 1]["start"]
            if current_end >= next_start:
                raise ValueError(
                    f"TOU periods CANNOT overlap! Period {i+1} ends at {current_end} "
                    f"but period {i+2} starts at {next_start}. "
                    f"Use XX:59 end times (e.g., 359 for 05:59) with XX:00 start times."
                )

        # Get device registry
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
        if not coordinator:
            raise ValueError(f"Coordinator not found for device {device_id}")

        client = coordinator._client

        VPP_CONTROL_AUTHORITY = 30100
        VPP_TOU_NUM_PERIODS = 30411
        VPP_TOU_DEFAULT_MODE = 30476
        VPP_TOU_PERIOD_BASE = 30412

        try:
            # Step 1: Enable VPP control authority
            success = await hass.async_add_executor_job(client.write_register, VPP_CONTROL_AUTHORITY, 1)
            if not success:
                _LOGGER.warning("Failed to enable VPP control authority, continuing anyway...")

            # Step 2: Set default mode (behavior outside scheduled periods)
            success = await hass.async_add_executor_job(client.write_register, VPP_TOU_DEFAULT_MODE, default_mode)
            if not success:
                _LOGGER.warning("Failed to set TOU default mode")

            # Step 3: Write each period's registers
            for i, period in enumerate(periods):
                base_addr = VPP_TOU_PERIOD_BASE + (i * 3)
                start = period["start"]
                end = period["end"]
                power = period["power"]

                # Convert negative power to unsigned 16-bit
                power_unsigned = power if power >= 0 else 65536 + power

                _LOGGER.debug("Writing TOU period %d: addr=%d, start=%d, end=%d, power=%d (unsigned=%d)",
                             i + 1, base_addr, start, end, power, power_unsigned)

                success = await hass.async_add_executor_job(
                    client.write_registers, base_addr, [start, end, power_unsigned]
                )
                if not success:
                    raise ValueError(f"Failed to write TOU period {i + 1}")

            # Step 4: Set number of active periods (activates the schedule)
            success = await hass.async_add_executor_job(client.write_register, VPP_TOU_NUM_PERIODS, len(periods))
            if not success:
                raise ValueError("Failed to set number of TOU periods")

            _LOGGER.info("Successfully synced %d TOU periods to inverter", len(periods))
            await coordinator.async_request_refresh()

        except Exception as e:
            _LOGGER.error("Failed to sync TOU schedule: %s", e)
            raise ValueError(f"Failed to sync TOU schedule: {e}")

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

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_BATTERY_MODE,
        set_battery_mode,
        schema=SERVICE_SET_BATTERY_MODE_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_WRITE_REGISTERS,
        write_registers,
        schema=SERVICE_WRITE_REGISTERS_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SYNC_TOU_SCHEDULE,
        sync_tou_schedule,
        schema=SERVICE_SYNC_TOU_SCHEDULE_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_REGISTER_DATA,
        get_register_data,
        schema=SERVICE_GET_REGISTER_DATA_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
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

    # Helper to check if register responds at all (value may be 0 — e.g. PV string at night)
    def reg_exists(addr):
        return addr in register_data and register_data[addr]['status'] == 'success' and register_data[addr]['value'] is not None

    # DTC code → (display name, profile key) — keep in sync with auto_detection.py dtc_map
    _DTC_MAP = {
        3501: ('SPH 3-6kW', 'sph_3000_6000_v201'),
        3502: ('SPH 3-6kW', 'sph_3000_6000_v201'),
        3503: ('SPH 3-6kW HU', 'sph_3000_6000_v201'),
        3504: ('SPH 3-6kW HUB', 'sph_3000_6000_v201'),
        3601: ('SPH-TL3 4-10kW', 'sph_tl3_3000_10000_v201'),
        3701: ('SPA 1-3kW BL', 'sph_3000_6000_v201'),
        3715: ('SPA 3-6kW AU', 'sph_3000_6000_v201'),
        3716: ('SPA 3-6kW AUB', 'sph_3000_6000_v201'),
        3725: ('SPA-TL3 4-10kW', 'sph_tl3_3000_10000_v201'),
        3735: ('SPA 3-6kW BL', 'sph_3000_6000_v201'),
        5001: ('MID 17-25KTL3-X / MID 20-30KTL3-X2', 'mid_15000_25000tl3_x_v201'),
        5002: ('MID 33-36KTL3-X / MOD 3-15KTL3-X', 'mid_15000_25000tl3_x_v201'),
        5003: ('MAC 30-70KTL3-X', 'mid_15000_25000tl3_x_v201'),
        5100: ('TL-XH 3-10kW', 'tl_xh_3000_10000_v201'),
        5200: ('MIN/MIC 2.5-6kW', 'min_3000_6000_tl_x_v201'),
        5201: ('MIN 7-10kW', 'min_7000_10000_tl_x_v201'),
        5400: ('MOD-XH/MID-XH', 'mod_6000_15000tl3_xh_v201'),
        5600: ('WIS 100K-AM / WIT 50-100K-H', 'mid_15000_25000tl3_x_v201'),
        5601: ('WIT 100kW Commercial', 'mid_15000_25000tl3_x_v201'),
        5603: ('WIT 4-15kW Hybrid', 'wit_4000_15000tl3'),
        5800: ('WIS 215kW Commercial', 'mid_15000_25000tl3_x_v201'),
        5801: ('WIS 215K-AM', 'mid_15000_25000tl3_x_v201'),
    }

    # Check VPP DTC (holding 30000) first, then V1.39 DTC (holding 43) as fallback.
    # V1.39 grid-tied inverters (MIN TL-X etc.) return 0 from holding 30000 but carry
    # their DTC at holding 43 per the V1.39 Modbus protocol spec.
    _dtc_source = None
    if 30000 in register_data and register_data[30000]['status'] == 'success' and register_data[30000]['value']:
        dtc_code = register_data[30000]['value']
        _dtc_source = "holding 30000 (VPP)"
    elif 43 in register_data and register_data[43]['status'] == 'success' and register_data[43]['value']:
        dtc_code = register_data[43]['value']
        _dtc_source = "holding 43 (V1.39)"
    else:
        dtc_code = None

    if dtc_code:
        detection["dtc_code"] = dtc_code
        detection["reasoning"].append(f"✓ DTC Code: {dtc_code} ({_dtc_source})")

        if dtc_code in _DTC_MAP:
            model_name, profile_key = _DTC_MAP[dtc_code]
            detection["model"] = f"{model_name} (DTC {dtc_code})"
            detection["profile_key"] = profile_key
            detection["confidence"] = "Very High"
            detection["reasoning"].append(f"✓ DTC {dtc_code} matches: {model_name}")
            detection["reasoning"].append("  → Auto-detection via DTC is most reliable method")

            # Apply protocol version downgrade BEFORE returning — mirrors actual HA detection.
            # Must check here (not in the standalone block below) because the early return at
            # the end of this section exits before that block runs.
            # Fix for issue #251: use `is not None` (not truthy) so value=0 is handled correctly.
            # V1.39 DTC detections (holding 43) have no 30099 entry — skip downgrade for them.
            proto_entry = register_data.get(30099, {})
            if proto_entry.get('status') == 'success' and proto_entry.get('value') is not None:
                proto_ver = proto_entry['value']
                detection["protocol_version"] = proto_ver
                if proto_ver == 0:
                    legacy_key = convert_to_legacy_profile(profile_key)
                    if legacy_key != profile_key:
                        detection["profile_key"] = legacy_key
                        detection["confidence"] = "High"
                        detection["reasoning"].append(
                            f"⚠ Register 30099 = 0 (legacy protocol) "
                            f"→ downgraded from {profile_key} to {legacy_key}"
                        )
                elif proto_ver >= 100:
                    proto_str = f"{proto_ver // 100}.{proto_ver % 100:02d}"
                    detection["reasoning"].append(
                        f"✓ Protocol Version: V{proto_str} (register 30099 = {proto_ver})"
                    )
                    if proto_ver >= 201:
                        detection["reasoning"].append(f"  → VPP Protocol V{proto_str} - supports advanced features")
            elif _dtc_source and "V1.39" in _dtc_source:
                # V1.39 inverter — no VPP protocol version register; downgrade to legacy profile
                legacy_key = convert_to_legacy_profile(profile_key)
                if legacy_key != profile_key:
                    detection["profile_key"] = legacy_key
                    detection["confidence"] = "High"
                    detection["reasoning"].append(
                        f"⚠ DTC from V1.39 register (holding 43) — no VPP support "
                        f"→ using legacy profile {legacy_key}"
                    )
        else:
            detection["reasoning"].append(f"⚠ Unknown DTC code {dtc_code} - not in supported models")

    # Check for protocol version (holding register 30099) — for non-DTC detections only.
    # (DTC detections handle this inline above before early return.)
    if detection["confidence"] != "Very High":
        if 30099 in register_data and register_data[30099]['status'] == 'success' and register_data[30099]['value'] is not None:
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
    has_pv3_at_11 = reg_exists(11)  # PV3 voltage in 0-124 range (0 when not producing)
    has_pv3_at_3011 = reg_exists(3011)  # PV3 voltage in 3000 range (0 when not producing)
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
                    # Check for PV3 to differentiate SPH_8000_10000_HU from SPH_7000_10000
                    if has_pv3_at_11:
                        detection["model"] = "SPH/SPM 8000-10000TL-HU"
                        detection["confidence"] = "High"
                        detection["profile_key"] = "sph_8000_10000_hu"
                        detection["register_map"] = "SPH_8000_10000_HU"
                        detection["reasoning"].append("✓ Storage range + PV3 at register 11 → SPH/SPM 8-10kW HU (3 MPPT)")
                        detection["reasoning"].append("  → HU models have 3 MPPT inputs and extended energy registers")
                    else:
                        detection["model"] = "SPH 7000-10000"
                        detection["confidence"] = "High"
                        detection["profile_key"] = "sph_7000_10000"
                        detection["register_map"] = "SPH_7000_10000"
                        detection["reasoning"].append("✓ Storage range or battery at 1013 → SPH 7-10kW")
                        detection["reasoning"].append("✗ No PV3 at register 11 → Standard model (2 MPPT)")
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
                    # Check for PV3 to differentiate SPH_8000_10000_HU from SPH_7000_10000
                    if has_pv3_at_11:
                        detection["model"] = "SPH/SPM 8000-10000TL-HU (Night/Standby Mode)"
                        detection["confidence"] = "Medium"
                        detection["profile_key"] = "sph_8000_10000_hu"
                        detection["register_map"] = "SPH_8000_10000_HU"
                        detection["reasoning"].append("✓ Found storage range + PV3 at register 11 → SPH/SPM 8-10kW HU (3 MPPT)")
                    else:
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


def _export_registers_to_csv(hass, connection_type: str, host: str, port: int, device: str, baudrate: int, slave_id: int, offgrid_mode: bool = False, enabled_groups: set = None, coordinator=None, block_size: int = 125) -> dict:
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
        coordinator: Pre-resolved coordinator (from config_entry selection). When provided,
                     the auto-detection loop is skipped entirely — connection parameters and
                     profile/entity values are sourced directly from this coordinator.
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

        # Allow the TCP connection to settle before the first request.
        # Without this, the inverter (which typically handles one TCP connection at a time)
        # may still be tearing down the coordinator's connection when the first reads fire,
        # causing DTC and other early registers to come back as 0 even though they work fine
        # on an established connection. 1.5 s is needed for some models (e.g. MIN TL-X).
        time.sleep(1.5)

        mode_str = "OffGrid scan (safe for SPF)" if offgrid_mode else "universal scan"
        _LOGGER.info(f"Connected, starting {mode_str}...")

        # Resolve coordinator for profile/entity data.
        # If pre-resolved via config_entry selection, use it directly.
        # Otherwise fall back to matching by connection parameters.
        if coordinator is not None:
            _LOGGER.info("Using pre-resolved coordinator from config entry — entity values will be included")
        else:
            if hass.data.get(DOMAIN):
                for entry_id, coord in hass.data[DOMAIN].items():
                    if not coord or not hasattr(coord, 'entry'):
                        continue

                    entry_data = coord.entry.data

                    # Match based on connection type
                    if connection_type == "tcp":
                        if (entry_data.get("connection_type") == "tcp" and
                            entry_data.get("host") == host and
                            entry_data.get("port", 502) == port):
                            coordinator = coord
                            _LOGGER.info(f"Auto-detected coordinator for {host}:{port} - entity values will be included")
                            break
                    else:  # serial
                        if (entry_data.get("connection_type") == "serial" and
                            entry_data.get("device") == device):
                            coordinator = coord
                            _LOGGER.info(f"Auto-detected coordinator for {device} - entity values will be included")
                            break

            if not coordinator:
                _LOGGER.info("No matching coordinator found - entity values will not be included in CSV")

        # Extract currently selected profile from coordinator (if available)
        selected_profile_key = None
        selected_profile_name = None
        current_entity_values = {}
        if coordinator and hasattr(coordinator, 'entry') and coordinator.entry.data:
            selected_profile_key = coordinator.entry.data.get(CONF_INVERTER_SERIES)
            if selected_profile_key:
                selected_profile_name = get_display_name_for_profile(selected_profile_key)
                _LOGGER.info(f"Currently selected profile: {selected_profile_name} ({selected_profile_key})")

            # Get current entity values from coordinator data
            if coordinator.data:
                _LOGGER.info("Extracting current entity values from coordinator...")
                # Get all attributes from the GrowattData object
                for attr_name in dir(coordinator.data):
                    # Skip private/magic methods
                    if attr_name.startswith('_'):
                        continue
                    # Get the value
                    try:
                        value = getattr(coordinator.data, attr_name, None)
                        # Include all non-callable values (including None, zero, etc.)
                        if not callable(value):
                            current_entity_values[attr_name] = value
                    except Exception as e:
                        _LOGGER.debug(f"Could not get value for {attr_name}: {e}")

                _LOGGER.info(f"Extracted {len(current_entity_values)} current entity values")

        # Scan ALL ranges
        all_register_data = {}     # input registers (FC04)
        holding_range_data = {}    # holding registers (FC03) from scan loop — kept separate
        #                            so holding and input addresses don't overwrite each other
        range_responses = {}

        # FIRST: Read DTC code, protocol version, and firmware version (holding registers - critical for identification)
        # SKIP VPP registers if OffGrid mode to prevent SPF power resets!
        # Always read firmware version (registers 9-11) - safe for all inverters
        _LOGGER.info("Reading firmware version (holding registers 9-11)...")
        fw_registers = _read_registers_chunked(client, 9, 3, slave_id, chunk_size=3, register_type='holding')
        if fw_registers:
            all_register_data.update(fw_registers)

        if not offgrid_mode:
            # Read V1.39 identification registers: holding 43 (DTC) and 3099 (DSP firmware code).
            # Legacy grid-tied inverters (MIN TL-X etc.) carry DTC at holding 43 rather than 30000.
            _LOGGER.info("Reading V1.39 identification registers (holding 43, 3099)...")
            v139_dtc = _read_registers_chunked(client, 43, 1, slave_id, chunk_size=1, register_type='holding')
            if v139_dtc:
                all_register_data.update(v139_dtc)
            v139_dsp = _read_registers_chunked(client, 3099, 1, slave_id, chunk_size=1, register_type='holding')
            if v139_dsp:
                all_register_data.update(v139_dsp)

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
                    # DTC came back zero — the inverter may still be settling after the fresh
                    # TCP connection displaced the coordinator's session. Retry once after a
                    # short pause before concluding there is no VPP DTC.
                    _LOGGER.info("  VPP DTC returned zero — retrying after 500 ms...")
                    time.sleep(0.5)
                    id_registers_retry = _read_registers_chunked(client, 30000, 100, slave_id, chunk_size=50, register_type='holding')
                    if id_registers_retry:
                        all_register_data.update(id_registers_retry)
                        dtc_found = 30000 in id_registers_retry and id_registers_retry[30000]['status'] == 'success' and id_registers_retry[30000]['value']
                        protocol_found = 30099 in id_registers_retry and id_registers_retry[30099]['status'] == 'success' and id_registers_retry[30099]['value']
                    if dtc_found or protocol_found:
                        _LOGGER.info(f"  DTC (retry): {id_registers_retry[30000]['value'] if dtc_found else 'Not found'}")
                        range_responses["VPP Identification (30000-30099)"] = 1
                    else:
                        _LOGGER.info("  No identification registers found (likely legacy protocol)")
                        range_responses["VPP Identification (30000-30099)"] = 0
            else:
                range_responses["VPP Identification (30000-30099)"] = 0

            # Retry legacy DTC (holding 43) if it came back zero — same settling issue.
            _leg_dtc_entry = all_register_data.get(43)
            if _leg_dtc_entry and _leg_dtc_entry.get('status') == 'success' and not _leg_dtc_entry.get('value'):
                _LOGGER.info("  Legacy DTC (holding 43) returned zero — retrying after 1 s...")
                time.sleep(1.0)
                v139_dtc_retry = _read_registers_chunked(client, 43, 1, slave_id, chunk_size=1, register_type='holding')
                if v139_dtc_retry:
                    all_register_data.update(v139_dtc_retry)
        else:
            _LOGGER.info("⚠️ Skipping VPP identification registers (OffGrid mode)")
            range_responses["VPP Identification (SKIPPED - OffGrid mode)"] = 0

        # THEN: Scan register ranges - use safe ranges for OffGrid mode, or filter by enabled groups
        if offgrid_mode:
            scan_ranges = OFFGRID_SCAN_RANGES
        else:
            all_groups = {"legacy", "storage", "mod_extended", "wit", "vpp_control", "vpp_data"}
            active_groups = enabled_groups if enabled_groups is not None else all_groups
            scan_ranges = [r for r in UNIVERSAL_SCAN_RANGES if r.get("group", "legacy") in active_groups]

        for range_config in scan_ranges:
            range_name = range_config["name"]
            start = range_config["start"]
            count = range_config["count"]
            reg_type = range_config.get("register_type", "input")

            _LOGGER.info(f"Scanning {range_name} ({reg_type}, block_size={block_size})...")

            registers = _read_registers_chunked(client, start, count, slave_id, chunk_size=block_size, register_type=reg_type)

            if registers:
                # Holding ranges go into a separate dict so they don't overwrite
                # input register data at the same addresses (e.g. 0-124, 1000-1124).
                if reg_type == 'holding':
                    holding_range_data.update(registers)
                else:
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

                registers = _read_registers_chunked(client, start, count, slave_id, chunk_size=block_size, register_type='holding')

                if registers:
                    all_register_data.update(registers)
                    # Count successful non-zero reads for range summary
                    successful_count = sum(1 for r in registers.values() if r['status'] == 'success' and r['value'] > 0)
                    range_responses[range_name] = successful_count
                    _LOGGER.info(f"{range_name}: {successful_count} non-zero registers out of {len(registers)} attempted")
                else:
                    range_responses[range_name] = 0
                    _LOGGER.info(f"{range_name}: No response")

        # Re-read identification registers now that the connection is settled.
        # By the time the range scan finishes, several seconds have elapsed since the
        # scanner connected — the inverter is no longer reinitialising its Modbus state
        # and these reads are reliable. This avoids using the coordinator's client
        # (which races with the coordinator's own polling thread).
        _LOGGER.info("Re-reading identification registers (connection now settled)...")
        _settled_fw = _read_registers_chunked(client, 9, 3, slave_id, chunk_size=3, register_type='holding')
        if _settled_fw:
            for _addr, _val in _settled_fw.items():
                if _val.get('status') == 'success' and _val.get('value') is not None:
                    all_register_data[_addr] = _val

        _settled_dtc43 = _read_registers_chunked(client, 43, 1, slave_id, chunk_size=1, register_type='holding')
        if _settled_dtc43:
            _e43 = _settled_dtc43.get(43)
            if _e43 and _e43.get('status') == 'success':
                all_register_data[43] = _e43

        _settled_dsp = _read_registers_chunked(client, 3099, 1, slave_id, chunk_size=1, register_type='holding')
        if _settled_dsp:
            _edsp = _settled_dsp.get(3099)
            if _edsp and _edsp.get('status') == 'success':
                all_register_data[3099] = _edsp

        # Only retry VPP DTC if it previously returned 0 (not if it threw an exception —
        # that means the device doesn't support VPP registers at all).
        _vpp_prev = all_register_data.get(30000)
        if _vpp_prev and _vpp_prev.get('status') == 'success' and not _vpp_prev.get('value'):
            _settled_vpp = _read_registers_chunked(client, 30000, 1, slave_id, chunk_size=1, register_type='holding')
            if _settled_vpp:
                _evpp = _settled_vpp.get(30000)
                if _evpp and _evpp.get('status') == 'success' and _evpp.get('value'):
                    all_register_data[30000] = _evpp

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
            writer.writerow(["Timestamp", datetime.now().astimezone().isoformat()])
            writer.writerow(["Connection", connection_str])
            writer.writerow(["Connection Type", connection_type.upper()])
            writer.writerow(["Slave ID", slave_id])
            writer.writerow(["Block Size", block_size, "registers per Modbus request"])

            # Add currently selected/configured profile (if coordinator found)
            if selected_profile_key and selected_profile_name:
                writer.writerow([])
                writer.writerow(["CURRENTLY CONFIGURED PROFILE"])
                writer.writerow(["Selected Profile", selected_profile_name])
                writer.writerow(["Selected Profile Key", selected_profile_key])

            # Add current entity values from the integration (if coordinator found)
            if current_entity_values:
                writer.writerow([])
                writer.writerow(["CURRENT ENTITY VALUES FROM INTEGRATION"])
                writer.writerow(["Entity Name", "Current Value"])

                # Sort entities by name for easier reading
                for entity_name in sorted(current_entity_values.keys()):
                    value = current_entity_values[entity_name]
                    # Format the value nicely - show ALL values including zeros and None
                    if value is None:
                        writer.writerow([entity_name, "None (unavailable)"])
                    elif isinstance(value, float):
                        writer.writerow([entity_name, f"{value:.3f}"])
                    elif isinstance(value, bool):
                        writer.writerow([entity_name, str(value)])
                    elif isinstance(value, (int, str)):
                        writer.writerow([entity_name, value])
                    else:
                        # Other types, just convert to string
                        writer.writerow([entity_name, str(value)])

            writer.writerow([])

            # Detection analysis section
            writer.writerow(["DETECTION ANALYSIS"])
            writer.writerow(["Detected Model", detection["model"]])
            writer.writerow(["Confidence", detection["confidence"]])

            # Always show both DTC registers so users can compare them
            _vpp_dtc_entry = all_register_data.get(30000)
            _leg_dtc_entry = all_register_data.get(43)
            _vpp_dtc_val = _vpp_dtc_entry['value'] if _vpp_dtc_entry and _vpp_dtc_entry.get('status') == 'success' else None
            _leg_dtc_val = _leg_dtc_entry['value'] if _leg_dtc_entry and _leg_dtc_entry.get('status') == 'success' else None
            writer.writerow(["VPP DTC (holding 30000)", _vpp_dtc_val if _vpp_dtc_val is not None else "not read / no response"])
            writer.writerow(["Legacy DTC (holding 43)", _leg_dtc_val if _leg_dtc_val is not None else "not read / no response"])
            if detection.get("dtc_code"):
                writer.writerow(["DTC Code (used)", detection["dtc_code"]])
            if detection.get("protocol_version"):
                protocol_ver = detection["protocol_version"]
                protocol_str = f"{protocol_ver // 100}.{protocol_ver % 100:02d}" if protocol_ver >= 100 else str(protocol_ver)
                writer.writerow(["Protocol Version", f"V{protocol_str} (register value: {protocol_ver})"])

            # Add firmware version — match coordinator's _registers_to_ascii decoding.
            # Holding 9-11: standard firmware string for all models.
            # Holding 3099: DSP software code for V1.39 3000-range models (MIN TL-X etc.).
            def _regs_to_ascii(reg_addrs):
                vals = [all_register_data.get(a) for a in reg_addrs]
                if not all(v and v.get('status') == 'success' and v.get('value') is not None for v in vals):
                    return None
                raw = []
                for v in vals:
                    w = v['value']
                    raw.extend([(w >> 8) & 0xFF, w & 0xFF])
                return bytes(raw).decode('ascii', errors='ignore').strip('\x00').strip() or None

            # Firmware version: ASCII decode of holding 9-11 is the primary source.
            # Registers 9-11 are now read via coordinator supplement so values are correct.
            # DSP code from holding 3099 is appended for V1.39 3000-range models.
            firmware_version = _regs_to_ascii([9, 10, 11])
            if firmware_version and len(firmware_version.strip()) < 3:
                firmware_version = None
            dsp_code = all_register_data.get(3099)
            if dsp_code and dsp_code.get('status') == 'success' and dsp_code.get('value'):
                dsp_val = dsp_code['value']
                # Valid DSP protocol codes are in range 100–999 (e.g. 126=V1.26, 139=V1.39).
                # Values outside this range (e.g. 8224=0x2020, two space bytes) are garbled.
                dsp_str = str(dsp_val) if 100 <= dsp_val <= 999 else None
                if dsp_str:
                    firmware_version = f"{firmware_version} (DSP: {dsp_str})" if firmware_version else f"DSP: {dsp_str}"
            if firmware_version:
                writer.writerow(["Firmware Version", firmware_version])

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

            # THEN: Output key holding registers (9-11 firmware)
            # Note: Scan currently only reads holding registers 9-11 (firmware) and 30000-30099 (VPP ID)
            key_holding_registers = {k: v for k, v in all_register_data.items() if k in [9, 10, 11]}
            if key_holding_registers:
                writer.writerow([])
                writer.writerow([f"--- Holding Registers (Key Registers) ---"])

                for reg_addr in sorted(key_holding_registers.keys()):
                    reg_info = key_holding_registers[reg_addr]
                    value = reg_info['value']
                    status = reg_info['status']
                    error = reg_info['error']

                    total += 1

                    # Build status/comment field with register name
                    if status == 'success':
                        if value == 0:
                            status_comment = "Read OK (zero value)"
                        else:
                            status_comment = "Read OK"
                            non_zero += 1

                        # Special handling for known holding registers
                        if reg_addr == 9:
                            status_comment += " [Firmware version byte 1-2]"
                            # Decode ASCII characters
                            high_byte = (value >> 8) & 0xFF
                            low_byte = value & 0xFF
                            chars = ""
                            if 32 <= high_byte <= 126:
                                chars += chr(high_byte)
                            if 32 <= low_byte <= 126:
                                chars += chr(low_byte)
                            if chars:
                                status_comment += f" ASCII: '{chars}'"
                        elif reg_addr == 10:
                            status_comment += " [Firmware version byte 3-4]"
                            high_byte = (value >> 8) & 0xFF
                            low_byte = value & 0xFF
                            chars = ""
                            if 32 <= high_byte <= 126:
                                chars += chr(high_byte)
                            if 32 <= low_byte <= 126:
                                chars += chr(low_byte)
                            if chars:
                                status_comment += f" ASCII: '{chars}'"
                        elif reg_addr == 11:
                            status_comment += " [Firmware version byte 5-6]"
                            high_byte = (value >> 8) & 0xFF
                            low_byte = value & 0xFF
                            chars = ""
                            if 32 <= high_byte <= 126:
                                chars += chr(high_byte)
                            if 32 <= low_byte <= 126:
                                chars += chr(low_byte)
                            if chars:
                                status_comment += f" ASCII: '{chars}'"

                    elif status == 'error':
                        status_comment = f"Modbus Error: {error}"
                        value = ""
                    else:  # exception
                        status_comment = error
                        value = ""

                    # Calculate interpretations only for successful reads
                    if status == 'success' and value is not None:
                        scaled_01 = value * 0.1
                        scaled_001 = value * 0.01
                        signed = value - 65536 if value > 32767 else value
                        combined_32bit = ""
                    else:
                        scaled_01 = ""
                        scaled_001 = ""
                        signed = ""
                        combined_32bit = ""

                    # No entity lookup for holding registers in current implementation
                    entity_value = ""
                    suggested_match = ""

                    writer.writerow([
                        f"H{reg_addr}",  # Mark as holding register with H prefix
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
            # Skip holding ranges — they are written separately below to avoid
            # showing holding values in what should be an input-register section.
            for range_config in UNIVERSAL_SCAN_RANGES:
                if range_config.get("register_type") == "holding":
                    continue
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
        
            # Holding register ranges (separate from input — H-prefix, FC03)
            holding_scan_ranges = [r for r in UNIVERSAL_SCAN_RANGES if r.get("register_type") == "holding"]
            for range_config in holding_scan_ranges:
                range_name = range_config["name"]
                start = range_config["start"]
                end = start + range_config["count"]

                range_registers = {k: v for k, v in holding_range_data.items() if start <= k < end}

                if range_registers:
                    writer.writerow([])
                    writer.writerow([f"--- {range_name} (Holding Registers) ---"])

                    for reg_addr in range(start, end):
                        if reg_addr not in range_registers:
                            continue
                        reg_info = range_registers[reg_addr]
                        value = reg_info['value']
                        status = reg_info['status']
                        error = reg_info['error']

                        total += 1

                        if status == 'success':
                            if value == 0:
                                status_comment = "Read OK (zero value)"
                            else:
                                status_comment = "Read OK"
                                non_zero += 1
                        elif status == 'error':
                            status_comment = f"Modbus Error: {error}"
                            value = ""
                        else:
                            status_comment = error
                            value = ""

                        if status == 'success' and value != "":
                            scaled_01 = value * 0.1
                            scaled_001 = value * 0.01
                            signed = value - 65536 if value > 32767 else value
                            combined_32bit = ""
                            if reg_addr + 1 in holding_range_data:
                                next_info = holding_range_data[reg_addr + 1]
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

                        entity_value = _get_entity_value_for_register(reg_addr, coordinator, 'holding') or ""
                        suggested_match = _get_holding_register_name(reg_addr, coordinator) or ""

                        writer.writerow([
                            f"H{reg_addr}",
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

        # Extract firmware version from holding registers 9-11 (ASCII encoded)
        firmware_version = None
        if 9 in all_register_data and 10 in all_register_data and 11 in all_register_data:
            fw_regs = [all_register_data[9], all_register_data[10], all_register_data[11]]
            if all(r['status'] == 'success' and r['value'] is not None for r in fw_regs):
                fw_chars = []
                for reg_data in fw_regs:
                    val = reg_data['value']
                    high_byte = (val >> 8) & 0xFF
                    low_byte = val & 0xFF
                    if 32 <= high_byte <= 126:
                        fw_chars.append(chr(high_byte))
                    if 32 <= low_byte <= 126:
                        fw_chars.append(chr(low_byte))
                firmware_version = ''.join(fw_chars).strip()

        # Extract both DTC values for the notification message
        _vpp_dtc_rd = all_register_data.get(30000)
        _leg_dtc_rd = all_register_data.get(43)
        result["vpp_dtc"] = _vpp_dtc_rd['value'] if _vpp_dtc_rd and _vpp_dtc_rd.get('status') == 'success' and _vpp_dtc_rd.get('value') is not None else None
        result["leg_dtc"] = _leg_dtc_rd['value'] if _leg_dtc_rd and _leg_dtc_rd.get('status') == 'success' and _leg_dtc_rd.get('value') is not None else None

        result["success"] = True
        result["filename"] = filename
        result["total_registers"] = total
        result["non_zero"] = non_zero
        result["responding_ranges"] = sum(1 for count in range_responses.values() if count > 0)
        result["detection"] = detection
        result["firmware_version"] = firmware_version

        _LOGGER.info(f"Universal scan complete: {filename}")
        _LOGGER.info(f"Detected: {detection['model']} (confidence: {detection['confidence']})")
        if firmware_version:
            _LOGGER.info(f"Firmware: {firmware_version}")
        
        return result
        
    except Exception as e:
        _LOGGER.error(f"Universal scan failed: {e}")
        result["error"] = str(e)
        return result