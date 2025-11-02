"""Diagnostic service for Growatt Modbus Integration."""
import logging
import csv
from datetime import datetime
from typing import Any, Dict, List, Tuple

import voluptuous as vol
from pymodbus.client import ModbusTcpClient

from homeassistant.core import HomeAssistant, ServiceCall
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Service names
SERVICE_EXPORT_DUMP = "export_register_dump"

# Universal scan ranges - covers all Growatt series
UNIVERSAL_SCAN_RANGES = [
    {"name": "Base Range 0-124", "start": 0, "count": 125},
    {"name": "Extended Range 125-249", "start": 125, "count": 125},
    {"name": "Storage Range 1000-1124", "start": 1000, "count": 125},
    {"name": "MIN/MOD Range 3000-3124", "start": 3000, "count": 125},
    {"name": "MOD Extended 3125-3249", "start": 3125, "count": 125},
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
            
            message_lines = [
                f"**File saved:** `{result['filename']}`\n",
                f"**Detected Model:** {model}",
                f"**Confidence:** {confidence}",
                f"**Suggested Profile:** `{profile_key}`\n",
                f"**Scan Results:**",
                f"• Total registers scanned: {result['total_registers']}",
                f"• Non-zero registers: {result['non_zero']}",
                f"• Responding ranges: {result['responding_ranges']}\n",
                f"Download from File Editor or `/config/{result['filename']}`",
            ]
            
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


def _read_registers_chunked(client, start: int, count: int, slave_id: int, chunk_size: int = 50) -> Dict[int, int]:
    """
    Read registers in chunks to avoid timeouts.
    
    Returns dict mapping register address to value (only non-zero values).
    """
    register_data = {}
    
    for chunk_start in range(0, count, chunk_size):
        chunk_count = min(chunk_size, count - chunk_start)
        chunk_address = start + chunk_start
        
        try:
            response = client.read_input_registers(
                address=chunk_address,
                count=chunk_count,
                device_id=slave_id
            )
            
            if not response.isError():
                for i, value in enumerate(response.registers):
                    if value > 0:  # Only store non-zero values
                        register_data[chunk_address + i] = value
                _LOGGER.debug(f"Read chunk {chunk_address}-{chunk_address+chunk_count-1}: {len([v for v in response.registers if v > 0])} non-zero")
            else:
                _LOGGER.debug(f"Chunk {chunk_address}-{chunk_address+chunk_count-1} returned error")
                
        except Exception as e:
            _LOGGER.debug(f"Chunk {chunk_address} exception: {e}")
    
    return register_data


def _detect_inverter_model(register_data: Dict[int, int]) -> Dict[str, str]:
    """
    Analyze register responses to detect inverter model.
    
    Returns dict with: model, confidence, profile_key, register_map, reasoning
    """
    detection = {
        "model": "Unknown",
        "confidence": "Low",
        "profile_key": "unknown",
        "register_map": "UNKNOWN",
        "reasoning": [],
    }
    
    # Helper to check if register exists
    def has_reg(addr):
        return addr in register_data
    
    # Check register ranges
    has_0_124 = any(0 <= r <= 124 for r in register_data.keys())
    has_1000_1124 = any(1000 <= r <= 1124 for r in register_data.keys())
    has_3000_3124 = any(3000 <= r <= 3124 for r in register_data.keys())
    has_3125_3249 = any(3125 <= r <= 3249 for r in register_data.keys())
    
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
            # MOD series - 3-phase hybrid with battery
            detection["model"] = "MOD 6000-15000TL3-XH"
            detection["confidence"] = "High"
            detection["profile_key"] = "mod_6000_15000tl3_xh"
            detection["register_map"] = "MOD_6000_15000TL3_XH"
            detection["reasoning"].append("✓ Found battery at register 3169 → MOD series (3-phase hybrid)")
            if has_pv3_at_3011:
                detection["reasoning"].append("✓ Found PV3 at register 3011 → Confirms 3-string MOD")
            
        else:
            # MIN series - string inverter, no battery
            if has_pv3_at_3011:
                detection["model"] = "MIN 7000-10000TL-X"
                detection["confidence"] = "High"
                detection["profile_key"] = "min_7000_10000_tl_x"
                detection["register_map"] = "MIN_7000_10000TL_X"
                detection["reasoning"].append("✓ Found PV3 at register 3011 → MIN 7-10kW (3 PV strings)")
            else:
                detection["model"] = "MIN 3000-6000TL-X"
                detection["confidence"] = "High"
                detection["profile_key"] = "min_3000_6000_tl_x"
                detection["register_map"] = "MIN_3000_6000TL_X"
                detection["reasoning"].append("✗ No PV3 at register 3011 → MIN 3-6kW (2 PV strings)")
    
    # Check for SPH, SPH TL3, or MID/MAX/MAC series (0-124 range)
    elif has_pv1_at_3:
        detection["reasoning"].append("✓ Found PV1 at register 3 (0-124 base range detected)")
        
        # Check for battery (SPH series)
        if has_battery_at_13 or has_battery_at_1013 or has_storage_range:
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
        detection["reasoning"].append("✗ No PV1 voltage found in expected registers (3 or 3003)")
        detection["reasoning"].append("⚠ Inverter may be off, in standby, or using unknown register layout")
    
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
        
        for range_config in UNIVERSAL_SCAN_RANGES:
            range_name = range_config["name"]
            start = range_config["start"]
            count = range_config["count"]
            
            _LOGGER.info(f"Scanning {range_name}...")
            
            registers = _read_registers_chunked(client, start, count, slave_id, chunk_size=50)
            
            if registers:
                all_register_data.update(registers)
                range_responses[range_name] = len(registers)
                _LOGGER.info(f"{range_name}: {len(registers)} non-zero registers")
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
                "32-bit Combined (with next reg)"
            ])
            
            # Write all registers sorted by address
            total = 0
            non_zero = len(all_register_data)
            
            # Group by ranges for organized output
            for range_config in UNIVERSAL_SCAN_RANGES:
                range_name = range_config["name"]
                start = range_config["start"]
                end = start + range_config["count"]
                
                range_registers = {k: v for k, v in all_register_data.items() if start <= k < end}
                
                if range_registers:
                    writer.writerow([])
                    writer.writerow([f"--- {range_name} ---"])
                    
                    for reg_addr in sorted(range_registers.keys()):
                        value = range_registers[reg_addr]
                        total += 1
                        
                        # Calculate interpretations
                        scaled_01 = value * 0.1
                        scaled_001 = value * 0.01
                        signed = value - 65536 if value > 32767 else value
                        
                        # Try to combine with next register for 32-bit values
                        combined_32bit = ""
                        if reg_addr + 1 in all_register_data:
                            next_val = all_register_data[reg_addr + 1]
                            combined = (value << 16) | next_val
                            if 0 < combined < 10000000:
                                combined_32bit = f"{combined} (×0.1={combined*0.1:.1f})"
                        
                        writer.writerow([
                            reg_addr,
                            f"0x{reg_addr:04X}",
                            value,
                            f"{scaled_01:.1f}",
                            f"{scaled_001:.2f}",
                            signed,
                            combined_32bit
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