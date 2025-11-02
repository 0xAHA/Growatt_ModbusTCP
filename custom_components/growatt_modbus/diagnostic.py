"""Diagnostic service for Growatt Modbus Integration."""
import logging
import csv
from datetime import datetime
from typing import Any

import voluptuous as vol
from pymodbus.client import ModbusTcpClient

from homeassistant.core import HomeAssistant, ServiceCall
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Service names
SERVICE_DIAGNOSTIC = "run_diagnostic"
SERVICE_SCAN_REGISTERS = "scan_registers"
SERVICE_EXPORT_DUMP = "export_register_dump"

# Test profiles with key registers
DIAGNOSTIC_PROFILES = {
    "min_3000_6000_tl_x": {
        "name": "MIN 3000-6000TL-X",
        "registers": [
            (3000, "Status", 1, ""),
            (3003, "PV1 Voltage", 0.1, "V"),
            (3007, "PV2 Voltage", 0.1, "V"),
            (3026, "AC Voltage", 0.1, "V"),
            (3025, "AC Frequency", 0.01, "Hz"),
        ],
    },
    "min_7000_10000_tl_x": {
        "name": "MIN 7000-10000TL-X",
        "registers": [
            (3000, "Status", 1, ""),
            (3003, "PV1 Voltage", 0.1, "V"),
            (3007, "PV2 Voltage", 0.1, "V"),
            (3011, "PV3 Voltage", 0.1, "V"),
            (3026, "AC Voltage", 0.1, "V"),
        ],
    },
    "sph_3000_10000": {
        "name": "SPH 3000-10000",
        "registers": [
            (0, "Status (Base)", 1, ""),
            (3, "PV1 Voltage", 0.1, "V"),
            (7, "PV2 Voltage", 0.1, "V"),
            (38, "AC Voltage", 0.1, "V"),
            (1013, "Battery Voltage", 0.1, "V"),
            (1014, "Battery SOC", 1, "%"),
        ],
    },
    "mid_15000_25000tl3_x": {
        "name": "MID 15000-25000TL3-X",
        "registers": [
            (0, "Status", 1, ""),
            (3, "PV1 Voltage", 0.1, "V"),
            (38, "Grid Voltage R", 0.1, "V"),
            (42, "Grid Voltage S", 0.1, "V"),
            (37, "Grid Frequency", 0.01, "Hz"),
        ],
    },
    "mod_6000_15000tl3_xh": {
        "name": "MOD 6000-15000TL3-XH",
        "registers": [
            (3000, "Status", 1, ""),
            (3003, "PV1 Voltage", 0.1, "V"),
            (3026, "AC Voltage R", 0.1, "V"),
            (3169, "Battery Voltage", 0.01, "V"),
            (3171, "Battery SOC", 1, "%"),
        ],
    },
}

# Scan profiles for different inverter series
SCAN_PROFILES = {
    "sph": {
        "name": "SPH Series (Hybrid)",
        "series_key": "sph_3000_10000",
        "ranges": [
            {"start": 0, "count": 125, "name": "Base Range"},
            {"start": 1000, "count": 125, "name": "Storage Range"},
        ],
        "has_battery": True,
    },
    "min": {
        "name": "MIN Series (String)",
        "series_key": "min_7000_10000_tl_x",
        "ranges": [
            {"start": 3000, "count": 125, "name": "MIN Range"},
        ],
        "has_battery": False,
    },
    "mod": {
        "name": "MOD Series (Hybrid)",
        "series_key": "mod_6000_15000tl3_xh",
        "ranges": [
            {"start": 3000, "count": 250, "name": "MOD Range"},
        ],
        "has_battery": True,
    },
    "mid_max": {
        "name": "MID Series (3-Phase)",
        "series_key": "mid_15000_25000tl3_x",
        "ranges": [
            {"start": 0, "count": 125, "name": "Base Range"},
            {"start": 125, "count": 125, "name": "Extended Range"},
        ],
        "has_battery": False,
    },
}

# Service schemas
SERVICE_DIAGNOSTIC_SCHEMA = vol.Schema(
    {
        vol.Required("host"): cv.string,
        vol.Optional("port", default=502): cv.port,
        vol.Optional("slave_id", default=1): vol.All(vol.Coerce(int), vol.Range(min=1, max=247)),
        vol.Required("inverter_series"): vol.In(list(DIAGNOSTIC_PROFILES.keys())),
        vol.Optional("notify", default=True): cv.boolean,
    }
)

SERVICE_SCAN_REGISTERS_SCHEMA = vol.Schema(
    {
        vol.Required("host"): cv.string,
        vol.Optional("port", default=502): cv.port,
        vol.Optional("slave_id", default=1): vol.All(vol.Coerce(int), vol.Range(min=1, max=247)),
        vol.Required("inverter_series"): vol.In(list(SCAN_PROFILES.keys())),
        vol.Optional("notify", default=True): cv.boolean,
    }
)

SERVICE_EXPORT_DUMP_SCHEMA = vol.Schema(
    {
        vol.Required("host"): cv.string,
        vol.Optional("port", default=502): cv.port,
        vol.Optional("slave_id", default=1): vol.All(vol.Coerce(int), vol.Range(min=1, max=247)),
        vol.Required("inverter_series"): vol.In(list(SCAN_PROFILES.keys())),
    }
)


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up diagnostic services."""

    async def run_diagnostic(call: ServiceCall) -> None:
        """Run diagnostic test on inverter."""
        host = call.data["host"]
        port = call.data["port"]
        slave_id = call.data["slave_id"]
        series = call.data["inverter_series"]
        send_notification = call.data["notify"]

        profile = DIAGNOSTIC_PROFILES[series]
        
        _LOGGER.info("Starting diagnostic for %s at %s:%s", profile["name"], host, port)

        # Run test in executor (blocking I/O)
        result = await hass.async_add_executor_job(
            _test_connection, host, port, slave_id, profile
        )

        # Log results
        _LOGGER.info("Diagnostic complete: %s", result["summary"])
        for line in result["details"]:
            _LOGGER.info(line)

        # Send notification if requested
        if send_notification:
            await hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": f"🔌 Growatt Diagnostic: {profile['name']}",
                    "message": _format_notification(result),
                    "notification_id": "growatt_diagnostic",
                },
            )

    async def scan_registers(call: ServiceCall) -> None:
        """Scan registers to find battery and power data."""
        host = call.data["host"]
        port = call.data.get("port", 502)
        slave_id = call.data.get("slave_id", 1)
        series = call.data["inverter_series"]
        send_notification = call.data.get("notify", True)

        # Get scan profile
        profile = SCAN_PROFILES[series].copy()
        
        _LOGGER.info("Starting register scan for %s at %s:%s", profile["name"], host, port)

        # Run scan in executor (blocking I/O)
        result = await hass.async_add_executor_job(
            _scan_registers_with_profile, host, port, slave_id, profile
        )

        # Log results
        _LOGGER.info("Register scan complete")
        for line in result["details"]:
            _LOGGER.info(line)

        # Send notification if requested
        if send_notification:
            await hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": f"🔍 Growatt Register Scanner: {profile['name']}",
                    "message": _format_scan_notification(result),
                    "notification_id": "growatt_register_scan",
                },
            )

    async def export_register_dump(call: ServiceCall) -> None:
        """Export complete register dump to CSV file."""
        host = call.data["host"]
        port = call.data.get("port", 502)
        slave_id = call.data.get("slave_id", 1)
        series = call.data["inverter_series"]
        
        _LOGGER.info("Starting register export for %s at %s:%s", series, host, port)
        
        # Get the register map that would be used
        from .device_profiles import get_profile
        scan_profile = SCAN_PROFILES[series]
        series_key = scan_profile.get("series_key", "sph_3000_10000")
        profile = get_profile(series_key)
        register_map_name = profile.get("register_map", "UNKNOWN")
        
        # Run export in executor
        result = await hass.async_add_executor_job(
            _export_registers_to_csv, hass, host, port, slave_id, series, register_map_name, scan_profile
        )
        
        if result["success"]:
            await hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": "✅ Register Export Complete",
                    "message": f"**File saved:** `{result['filename']}`\n\n"
                              f"**Total registers:** {result['total_registers']}\n"
                              f"**Non-zero:** {result['non_zero']}\n"
                              f"**Register map:** {register_map_name}\n\n"
                              f"Download from File Editor or `/config/{result['filename']}`",
                    "notification_id": "growatt_register_export",
                },
            )
        else:
            await hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": "❌ Register Export Failed",
                    "message": result.get("error", "Unknown error"),
                    "notification_id": "growatt_register_export",
                },
            )

    # Register all services
    hass.services.async_register(
        DOMAIN,
        SERVICE_DIAGNOSTIC,
        run_diagnostic,
        schema=SERVICE_DIAGNOSTIC_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SCAN_REGISTERS,
        scan_registers,
        schema=SERVICE_SCAN_REGISTERS_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_EXPORT_DUMP,
        export_register_dump,
        schema=SERVICE_EXPORT_DUMP_SCHEMA,
    )


def _read_registers_chunked(client, start: int, count: int, slave_id: int, chunk_size: int = 50) -> list:
    """
    Read registers in chunks to avoid timeouts.
    
    Returns list of register values or None if completely failed.
    """
    all_registers = []
    
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
                all_registers.extend(response.registers)
                _LOGGER.debug(f"Successfully read chunk {chunk_address}-{chunk_address+chunk_count-1}")
            else:
                _LOGGER.warning(f"Failed to read chunk {chunk_address}-{chunk_address+chunk_count-1}")
                # Pad with zeros for failed chunks
                all_registers.extend([0] * chunk_count)
                
        except Exception as e:
            _LOGGER.warning(f"Error reading chunk {chunk_address}: {e}")
            # Pad with zeros for failed chunks
            all_registers.extend([0] * chunk_count)
    
    return all_registers if len(all_registers) == count else None


def _test_connection(host: str, port: int, slave_id: int, profile: dict) -> dict:
    """Test connection and read registers (blocking)."""
    results = {
        "success": False,
        "connected": False,
        "total": len(profile["registers"]),
        "passed": 0,
        "details": [],
        "summary": "",
    }

    # Test TCP connection with longer timeout
    try:
        client = ModbusTcpClient(host=host, port=port, timeout=10)
        if not client.connect():
            results["summary"] = "❌ Failed to connect"
            results["details"].append(f"Cannot connect to {host}:{port}")
            return results
        
        results["connected"] = True
        results["details"].append(f"✅ Connected to {host}:{port}")

    except Exception as e:
        results["summary"] = f"❌ Connection error: {e}"
        results["details"].append(f"Error: {e}")
        return results

    # Test each register
    try:
        for address, name, scale, unit in profile["registers"]:
            try:
                result = client.read_input_registers(address=address, count=1, device_id=slave_id)
                
                if result.isError():
                    results["details"].append(f"❌ Register {address} ({name}): Read error")
                else:
                    raw = result.registers[0]
                    scaled = raw * scale
                    
                    # Format value
                    if "Status" in name:
                        status_map = {0: "Waiting", 1: "Normal", 3: "Fault", 5: "Standby"}
                        value_str = status_map.get(int(scaled), f"Unknown ({scaled})")
                    else:
                        value_str = f"{scaled:.2f} {unit}" if unit else f"{scaled}"
                    
                    results["details"].append(f"✅ Register {address} ({name}): {value_str}")
                    results["passed"] += 1
                    
            except Exception as e:
                results["details"].append(f"❌ Register {address} ({name}): {e}")

    finally:
        client.close()

    # Summary
    if results["passed"] == results["total"]:
        results["success"] = True
        results["summary"] = f"✅ All tests passed ({results['passed']}/{results['total']})"
    elif results["passed"] > 0:
        results["summary"] = f"⚠️ Partial success ({results['passed']}/{results['total']})"
    else:
        results["summary"] = f"❌ All tests failed (0/{results['total']})"

    return results


def _scan_registers_with_profile(host: str, port: int, slave_id: int, profile: dict) -> dict:
    """Scan registers using a profile (blocking)."""
    results = {
        "connected": False,
        "details": [],
        "ranges": {},
        "battery_candidates": [],
    }

    # Connect with longer timeout
    try:
        client = ModbusTcpClient(host=host, port=port, timeout=10)
        if not client.connect():
            results["details"].append(f"❌ Cannot connect to {host}:{port}")
            return results
        
        results["connected"] = True
        results["details"].append(f"✅ Connected to {host}:{port}")
        results["details"].append(f"📋 Scanning: {profile['name']}")
        results["details"].append("")

    except Exception as e:
        results["details"].append(f"❌ Connection error: {e}")
        return results

    try:
        # Scan each range in profile
        for range_config in profile["ranges"]:
            range_start = range_config["start"]
            range_count = range_config["count"]
            range_name = range_config.get("name", f"Range {range_start}-{range_start+range_count-1}")
            
            results["details"].append(f"📊 SCANNING {range_name.upper()}:")
            results["details"].append("="*60)
            
            range_key = f"{range_start}_{range_start+range_count-1}"
            results["ranges"][range_key] = []
            
            # Read in chunks of 50
            registers = _read_registers_chunked(client, range_start, range_count, slave_id, chunk_size=50)
            
            if registers:
                non_zero = 0
                for i, value in enumerate(registers):
                    if value > 0:
                        reg_num = range_start + i
                        non_zero += 1
                        
                        # Analyze value with multiple interpretations
                        interpretations = []
                        interpretations.append(f"Raw={value}")
                        
                        # Signed interpretation
                        if value > 32767:
                            signed = value - 65536
                            interpretations.append(f"Signed={signed}")
                        
                        # Common scaling factors
                        interpretations.append(f"×0.1={value*0.1:.1f}")
                        interpretations.append(f"×0.01={value*0.01:.2f}")
                        
                        # Check if it's a 32-bit pair candidate
                        if i < len(registers) - 1:
                            next_val = registers[i + 1]
                            combined = (value << 16) | next_val
                            if 0 < combined < 10000000:  # Reasonable range
                                interpretations.append(f"32bit={combined} (×0.1={combined*0.1:.1f})")
                        
                        analysis = " | ".join(interpretations)
                        results["details"].append(f"  Reg {reg_num:4d}: {analysis}")
                        results["ranges"][range_key].append((reg_num, value))
                
                results["details"].append(f"\n  Found {non_zero} non-zero registers in {range_name}")
            else:
                results["details"].append(f"  ❌ Failed to read {range_name}")
            
            results["details"].append("")

        # Battery analysis (only if profile indicates battery capability)
        if profile["has_battery"]:
            results["details"].append("🔋 BATTERY DETECTION ANALYSIS:")
            results["details"].append("="*60)
            
            # Check common battery register locations
            battery_patterns = []
            
            for range_config in profile["ranges"]:
                range_start = range_config["start"]
                
                if range_start == 1000:  # SPH storage range
                    battery_patterns.append({
                        "base": 1000,
                        "name": "SPH Pattern",
                        "voltage_offset": 13,
                        "voltage_scale": 0.1,
                        "soc_offset": 14,
                        "temp_offset": 40,
                        "type_offset": 41,
                    })
                elif range_start == 3000:  # MOD range
                    battery_patterns.append({
                        "base": 3000,
                        "name": "MOD Pattern",
                        "voltage_offset": 169,
                        "voltage_scale": 0.01,
                        "soc_offset": 171,
                        "temp_offset": 175,
                        "type_offset": None,
                    })
            
            for pattern in battery_patterns:
                base = pattern["base"]
                
                results["details"].append(f"\n  Checking {pattern['name']} at base {base}:")
                
                try:
                    max_offset = max([v for k, v in pattern.items() if k.endswith("_offset") and v is not None])
                    battery_regs = client.read_input_registers(
                        address=base, 
                        count=max_offset + 2,
                        device_id=slave_id
                    )
                    
                    if not battery_regs.isError():
                        # Voltage check
                        voltage_reg = base + pattern["voltage_offset"]
                        voltage_raw = battery_regs.registers[pattern["voltage_offset"]]
                        voltage_scaled = voltage_raw * pattern["voltage_scale"]
                        voltage_ok = 40 <= voltage_scaled <= 60
                        
                        status = "✅" if voltage_ok and voltage_raw > 0 else "❌"
                        results["details"].append(f"    {status} Reg {voltage_reg}: Voltage = {voltage_raw} raw → {voltage_scaled:.1f}V")
                        
                        if voltage_ok and voltage_raw > 0:
                            results["battery_candidates"].append((voltage_reg, "Battery Voltage", voltage_raw, voltage_scaled, "V"))
                        
                        # SOC check
                        soc_reg = base + pattern["soc_offset"]
                        soc_raw = battery_regs.registers[pattern["soc_offset"]]
                        soc_ok = 0 <= soc_raw <= 100
                        
                        status = "✅" if soc_ok and soc_raw > 0 else "❌"
                        results["details"].append(f"    {status} Reg {soc_reg}: SOC = {soc_raw}%")
                        
                        if soc_ok and soc_raw > 0:
                            results["battery_candidates"].append((soc_reg, "Battery SOC", soc_raw, soc_raw, "%"))
                        
                        # Temp check
                        if pattern["temp_offset"]:
                            temp_reg = base + pattern["temp_offset"]
                            temp_raw = battery_regs.registers[pattern["temp_offset"]]
                            temp_scaled = temp_raw * 0.1
                            temp_ok = -20 <= temp_scaled <= 60
                            
                            status = "✅" if temp_ok and temp_raw > 0 else "❌"
                            results["details"].append(f"    {status} Reg {temp_reg}: Temp = {temp_raw} raw → {temp_scaled:.1f}°C")
                            
                            if temp_ok and temp_raw > 0:
                                results["battery_candidates"].append((temp_reg, "Battery Temp", temp_raw, temp_scaled, "°C"))
                        
                        # Type check
                        if pattern["type_offset"]:
                            type_reg = base + pattern["type_offset"]
                            type_raw = battery_regs.registers[pattern["type_offset"]]
                            type_names = {0: "Lead Acid", 1: "Lithium", 2: "Other"}
                            type_str = type_names.get(type_raw, f"Unknown ({type_raw})")
                            
                            status = "✅" if 0 <= type_raw <= 2 else "❌"
                            results["details"].append(f"    {status} Reg {type_reg}: Type = {type_str}")
                            
                            if 0 <= type_raw <= 2:
                                results["battery_candidates"].append((type_reg, "Battery Type", type_raw, type_raw, type_str))
                
                except Exception as e:
                    results["details"].append(f"    ❌ Error checking battery pattern at {base}: {e}")
            
            # Generic scan for battery-like values
            results["details"].append(f"\n  Generic battery value scan across all ranges:")
            
            soc_candidates = []
            voltage_candidates = []
            power_candidates = []
            
            for range_key, registers in results["ranges"].items():
                for reg_num, value in registers:
                    if 1 <= value <= 100:
                        soc_candidates.append((reg_num, value))
                    if 400 <= value <= 600:
                        voltage_candidates.append((reg_num, value))
                    if 1000 <= value <= 100000:
                        power_candidates.append((reg_num, value))
            
            if soc_candidates:
                results["details"].append(f"    🔍 Found {len(soc_candidates)} SOC candidates (0-100 range):")
                for reg, val in soc_candidates[:10]:
                    results["details"].append(f"       Reg {reg}: {val}%")
            else:
                results["details"].append("    ❌ No SOC candidates found (0-100 range)")
            
            if voltage_candidates:
                results["details"].append(f"    🔍 Found {len(voltage_candidates)} voltage candidates (40-60V range):")
                for reg, val in voltage_candidates[:10]:
                    results["details"].append(f"       Reg {reg}: {val} raw = {val*0.1:.1f}V")
            else:
                results["details"].append("    ❌ No voltage candidates found (400-600 raw)")
            
            if power_candidates:
                results["details"].append(f"    🔍 Found {len(power_candidates)} power candidates (0.1-10kW range):")
                for reg, val in power_candidates[:10]:
                    results["details"].append(f"       Reg {reg}: {val} raw = {val*0.1:.0f}W")
            else:
                results["details"].append("    ⚠️  No significant power values found")

    finally:
        client.close()

    return results


def _export_registers_to_csv(hass, host: str, port: int, slave_id: int, series: str, register_map_name: str, scan_profile: dict) -> dict:
    """Export all registers to CSV file (blocking)."""
    result = {
        "success": False,
        "filename": "",
        "total_registers": 0,
        "non_zero": 0,
    }
    
    try:
        # Connect with longer timeout
        client = ModbusTcpClient(host=host, port=port, timeout=15)
        if not client.connect():
            result["error"] = f"Cannot connect to {host}:{port}"
            return result
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"growatt_registers_{series}_{timestamp}.csv"
        filepath = hass.config.path(filename)
        
        # Get register map from const
        from .const import REGISTER_MAPS
        register_map = REGISTER_MAPS.get(register_map_name, {})
        input_regs_map = register_map.get("input_registers", {})
        
        # Determine which ranges to scan from profile
        ranges_to_scan = []
        for range_config in scan_profile.get("ranges", []):
            ranges_to_scan.append((
                range_config.get("name", f"Range {range_config['start']}"),
                range_config["start"],
                range_config["count"]
            ))
        
        # Open CSV file
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            writer.writerow([
                "Register Address",
                "Hex Address", 
                "Raw Value",
                "Scaled x0.1",
                "Scaled x0.01",
                "Signed Value",
                "Register Name (from const.py)",
                "Scale Factor",
                "Description"
            ])
            
            # Write metadata
            writer.writerow([])
            writer.writerow(["SCAN METADATA"])
            writer.writerow(["Timestamp", datetime.now().isoformat()])
            writer.writerow(["Host", f"{host}:{port}"])
            writer.writerow(["Slave ID", slave_id])
            writer.writerow(["Inverter Series", series])
            writer.writerow(["Register Map", register_map_name])
            writer.writerow(["Ranges Scanned", ", ".join([r[0] for r in ranges_to_scan])])
            writer.writerow([])
            writer.writerow(["REGISTER DATA"])
            writer.writerow([])
            
            total = 0
            non_zero = 0
            
            # Scan each range
            for range_name, start, count in ranges_to_scan:
                writer.writerow([f"--- {range_name} ({start}-{start+count-1}) ---"])
                
                # Read in chunks
                registers = _read_registers_chunked(client, start, count, slave_id, chunk_size=50)
                
                if registers:
                    for i, value in enumerate(registers):
                        reg_addr = start + i
                        total += 1
                        
                        if value > 0:
                            non_zero += 1
                        
                        # Get register info from map if available
                        reg_info = input_regs_map.get(reg_addr, {})
                        reg_name = reg_info.get("name", "")
                        scale = reg_info.get("scale", "")
                        desc = reg_info.get("desc", "")
                        
                        # Calculate different interpretations
                        scaled_01 = value * 0.1
                        scaled_001 = value * 0.01
                        signed = value - 65536 if value > 32767 else value
                        
                        writer.writerow([
                            reg_addr,
                            f"0x{reg_addr:04X}",
                            value,
                            f"{scaled_01:.1f}",
                            f"{scaled_001:.2f}",
                            signed,
                            reg_name,
                            scale,
                            desc
                        ])
                else:
                    writer.writerow([f"ERROR: Failed to read {range_name}"])
                
                writer.writerow([])  # Blank line between ranges
        
        client.close()
        
        result["success"] = True
        result["filename"] = filename
        result["total_registers"] = total
        result["non_zero"] = non_zero
        
        _LOGGER.info(f"CSV export complete: {filename} ({non_zero}/{total} non-zero registers)")
        
        return result
        
    except Exception as e:
        _LOGGER.error(f"CSV export failed: {e}")
        result["error"] = str(e)
        return result


def _format_notification(result: dict) -> str:
    """Format result as notification message."""
    lines = [
        f"**{result['summary']}**",
        "",
        "**Results:**",
    ]
    
    for detail in result["details"]:
        lines.append(f"• {detail}")
    
    lines.append("")
    
    if result["success"]:
        lines.extend([
            "**✅ Next Steps:**",
            "Your inverter is responding correctly!",
            "You can now install the integration.",
        ])
    elif result["passed"] > 0:
        lines.extend([
            "**⚠️ Troubleshooting:**",
            "Some registers failed. Try:",
            "• Test during daytime (inverter on)",
            "• Check if correct model selected",
            "• Wait for inverter to fully boot",
        ])
    else:
        lines.extend([
            "**❌ Troubleshooting:**",
            "No registers responded. Check:",
            "• Wiring (try swapping A/B)",
            "• Slave ID (try 1, 2, or 3)",
            "• Inverter is powered on",
        ])
    
    return "\n".join(lines)


def _format_scan_notification(result: dict) -> str:
    """Format scan result as notification message."""
    lines = []
    
    if not result["connected"]:
        lines.append("**❌ Connection Failed**")
        lines.append("")
        for detail in result["details"][:5]:
            lines.append(detail)
        return "\n".join(lines)
    
    lines.append("**🔍 Register Scan Complete**")
    lines.append("")
    
    # Summary
    total_non_zero = sum(len(registers) for registers in result["ranges"].values())
    battery_count = len(result["battery_candidates"])
    
    lines.append(f"**Summary:**")
    lines.append(f"• Total non-zero registers: {total_non_zero}")
    lines.append(f"• Battery candidates: {battery_count} found")
    lines.append("")
    
    # Battery candidates
    if battery_count > 0:
        lines.append("**🔋 Battery Candidates Found:**")
        for reg, name, raw, scaled, unit in result["battery_candidates"][:10]:
            lines.append(f"• Reg {reg}: {name} = {scaled:.1f} {unit}")
        lines.append("")
        lines.append("**✅ Batteries detected!**")
        lines.append("Check logs for register addresses to use in const.py")
    else:
        lines.append("**❌ No battery data found**")
        lines.append("Possible reasons:")
        lines.append("• Batteries not connected")
        lines.append("• Wrong inverter series selected")
        lines.append("• Batteries not initialized")
    
    lines.append("")
    lines.append("**📄 Full details in Home Assistant logs**")
    lines.append("Settings → System → Logs")
    
    return "\n".join(lines)