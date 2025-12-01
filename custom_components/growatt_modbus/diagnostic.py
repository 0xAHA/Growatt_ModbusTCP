"""Diagnostic service for Growatt Modbus Integration."""
import logging
import csv
from datetime import datetime
from typing import Any, Dict, List, Tuple, Optional

import voluptuous as vol
from pymodbus.client import ModbusTcpClient

from homeassistant.core import HomeAssistant, ServiceCall
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

# Service names
SERVICE_EXPORT_DUMP = "export_register_dump"

# Universal scan ranges - covers all Growatt series
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

# Service schema
SERVICE_EXPORT_DUMP_SCHEMA = vol.Schema(
    {
        vol.Required("host"): cv.string,
        vol.Optional("port", default=502): cv.port,
        vol.Optional("slave_id", default=1): vol.All(vol.Coerce(int), vol.Range(min=1, max=247)),
        vol.Optional("notify", default=True): cv.boolean,
    }
)


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


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up diagnostic services."""

    async def export_register_dump(call: ServiceCall) -> None:
        """Universal register scanner - scans all ranges and auto-detects model."""
        host = call.data["host"]
        port = call.data.get("port", 502)
        slave_id = call.data.get("slave_id", 1)
        send_notification = call.data.get("notify", True)
        
        _LOGGER.info("Starting universal register scan at %s:%s", host, port)
        
        # Run export in executor
        result = await hass.async_add_executor_job(
            _export_registers_to_csv, hass, host, port, slave_id
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

    # Register service
    hass.services.async_register(
        DOMAIN,
        SERVICE_EXPORT_DUMP,
        export_register_dump,
        schema=SERVICE_EXPORT_DUMP_SCHEMA,
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


def _export_registers_to_csv(hass, host: str, port: int, slave_id: int) -> dict:
    """Export all registers to CSV file with auto-detection (blocking)."""
    result = {
        "success": False,
        "filename": "",
        "total_registers": 0,
        "non_zero": 0,
        "responding_ranges": 0,
    }

    try:
        # Connect with longer timeout
        client = ModbusTcpClient(host=host, port=port, timeout=15)
        if not client.connect():
            result["error"] = f"Cannot connect to {host}:{port}"
            return result

        _LOGGER.info("Connected, starting universal scan...")

        # Scan ALL ranges
        all_register_data = {}
        range_responses = {}

        # FIRST: Read DTC code and protocol version (holding registers - critical for identification)
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

        # THEN: Scan input register ranges
        for range_config in UNIVERSAL_SCAN_RANGES:
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
            writer.writerow(["Timestamp", datetime.now().isoformat()])
            writer.writerow(["Host", f"{host}:{port}"])
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
            writer.writerow([
                "Register",
                "Hex",
                "Raw Value",
                "×0.1",
                "×0.01",
                "Signed",
                "32-bit Combined (with next reg)",
                "Suggested Match",
                "Status/Comment"
            ])
            
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