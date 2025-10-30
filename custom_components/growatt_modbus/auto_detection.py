"""
Auto-Detection System for Growatt Inverters

This module implements automatic inverter type detection similar to the
solax-modbus plugin's async_determineInverterType function.

It reads the inverter's serial number and model information to automatically
select the correct profile.
"""

import logging
from typing import Optional, Tuple

from homeassistant.core import HomeAssistant

from .device_profiles import INVERTER_PROFILES, get_profile
from .growatt_modbus import GrowattModbus

_LOGGER = logging.getLogger(__name__)


def detect_profile_from_model_name(model_name: str) -> Optional[str]:
    """
    Match a model name string to a profile key.
    
    Args:
        model_name: Model name read from inverter (e.g., "MIN 10000TL-X")
    
    Returns:
        Profile key or None if no match
    """
    if not model_name:
        return None
    
    # Normalize model name for comparison
    model_upper = model_name.upper().replace("-", "").replace(" ", "")
    
    # Model name patterns to profile mappings
    patterns = {
        # MIN series
        'MIN3000': 'min_3000_6000_tl_x',
        'MIN4000': 'min_3000_6000_tl_x',
        'MIN5000': 'min_3000_6000_tl_x',
        'MIN6000': 'min_3000_6000_tl_x',
        'MIN7000': 'min_7000_10000_tl_x',
        'MIN8000': 'min_7000_10000_tl_x',
        'MIN9000': 'min_7000_10000_tl_x',
        'MIN10000': 'min_7000_10000_tl_x',
        
        # TL-XH series
        'TLXH3000': 'tl_xh_3000_10000',
        'TLXH5000': 'tl_xh_3000_10000',
        'TLXH6000': 'tl_xh_3000_10000',
        'TLXH8000': 'tl_xh_3000_10000',
        'TLXH10000': 'tl_xh_3000_10000',
        'TLXHUS': 'tl_xh_us_3000_10000',
        
        # MID series
        'MID15000': 'mid_15000_25000tl3_x',
        'MID17000': 'mid_15000_25000tl3_x',
        'MID20000': 'mid_15000_25000tl3_x',
        'MID22000': 'mid_15000_25000tl3_x',
        'MID25000': 'mid_15000_25000tl3_x',
        
        # MAC series
        'MAC20000': 'mac_20000_40000tl3_x',
        'MAC25000': 'mac_20000_40000tl3_x',
        'MAC30000': 'mac_20000_40000tl3_x',
        'MAC36000': 'mac_20000_40000tl3_x',
        'MAC40000': 'mac_20000_40000tl3_x',
        
        # MAX series
        'MAX50': 'max_50000_125000tl3_x',
        'MAX60': 'max_50000_125000tl3_x',
        'MAX75': 'max_50000_125000tl3_x',
        'MAX100': 'max_50000_125000tl3_x',
        'MAX110': 'max_50000_125000tl3_x',
        'MAX125': 'max_50000_125000tl3_x',
        'MAX1500V': 'max_1500v_series',
        'MAXXLV': 'max_x_lv_series',
        
        # SPH series
        'SPH3000': 'sph_3000_10000',
        'SPH3600': 'sph_3000_10000',
        'SPH4000': 'sph_3000_10000',
        'SPH5000': 'sph_3000_10000',
        'SPH6000': 'sph_3000_10000',
        'SPH8000': 'sph_3000_10000',
        'SPH10000': 'sph_3000_10000',
        
        # MOD series
        'MOD6000': 'mod_6000_15000tl3_xh',
        'MOD8000': 'mod_6000_15000tl3_xh',
        'MOD10000': 'mod_6000_15000tl3_xh',
        'MOD12000': 'mod_6000_15000tl3_xh',
        'MOD15000': 'mod_6000_15000tl3_xh',
        
        # MIX series
        'MIX': 'mix_series',
        
        # SPA series
        'SPA': 'spa_series',
        
        # WIT series
        'WIT': 'wit_tl3_series',
    }
    
    # Try to find a match
    for pattern, profile_key in patterns.items():
        if pattern in model_upper:
            _LOGGER.info(f"Matched model '{model_name}' to profile '{profile_key}'")
            return profile_key
    
    _LOGGER.warning(f"No profile match found for model name: {model_name}")
    return None


async def async_read_serial_number(
    hass: HomeAssistant,
    client: GrowattModbus,
    device_id: int = 1
) -> Optional[str]:
    """
    Read inverter serial number from holding registers.
    
    Args:
        hass: HomeAssistant instance
        client: GrowattModbus client
        device_id: Modbus device ID (default 1)
    
    Returns:
        Serial number string or None
    """
    try:
        # Read 10 registers starting at address 23
        result = await hass.async_add_executor_job(
            client.client.read_holding_registers,
            23, 10
        )
        
        if result.isError():
            _LOGGER.debug(f"Error reading serial number: {result}")
            return None
        
        # Convert registers to string
        serial_bytes = []
        for register in result.registers:
            high_byte = (register >> 8) & 0xFF
            low_byte = register & 0xFF
            serial_bytes.extend([high_byte, low_byte])
        
        # Convert bytes to string and strip null characters
        serial_number = bytes(serial_bytes).decode('ascii', errors='ignore').strip('\x00').strip()
        
        if serial_number:
            _LOGGER.info(f"Read serial number: {serial_number}")
            return serial_number
        
        return None
        
    except Exception as e:
        _LOGGER.debug(f"Exception reading serial number: {str(e)}")
        return None


async def async_read_model_name(
    hass: HomeAssistant,
    client: GrowattModbus,
    device_id: int = 1
) -> Optional[str]:
    """
    Read inverter model name from holding registers.
    
    Args:
        hass: HomeAssistant instance
        client: GrowattModbus client
        device_id: Modbus device ID (default 1)
    
    Returns:
        Model name string or None
    """
    try:
        # Read 5 registers starting at address 0
        result = await hass.async_add_executor_job(
            client.client.read_holding_registers,
            0, 5
        )
        
        if result.isError():
            _LOGGER.debug(f"Error reading model name: {result}")
            return None
        
        # Convert registers to string
        model_bytes = []
        for register in result.registers:
            high_byte = (register >> 8) & 0xFF
            low_byte = register & 0xFF
            model_bytes.extend([high_byte, low_byte])
        
        # Convert bytes to string and strip null characters
        model_name = bytes(model_bytes).decode('ascii', errors='ignore').strip('\x00').strip()
        
        if model_name:
            _LOGGER.info(f"Read model name: {model_name}")
            return model_name
        
        return None
        
    except Exception as e:
        _LOGGER.debug(f"Exception reading model name: {str(e)}")
        return None


async def async_detect_inverter_series(
    hass: HomeAssistant,
    client: GrowattModbus,
    device_id: int = 1
) -> Optional[str]:
    """
    Detect inverter series by probing different register ranges.
    
    Args:
        hass: HomeAssistant instance
        client: GrowattModbus client
        device_id: Modbus device ID
    
    Returns:
        Profile key or None
    """
    try:
        # Test for battery registers at 3169 (SPH/TL-XH/MOD specific)
        result = await hass.async_add_executor_job(
            client.client.read_input_registers,
            3169, 1,
        )
        if not result.isError() and result.registers[0] > 0:
            _LOGGER.info("Detected battery voltage register - hybrid inverter")
            
            # Check for 3-phase at register 42 (MOD uses R/S/T phases)
            phase_test = await hass.async_add_executor_job(
                client.client.read_input_registers,
                42, 1
            )
            if not phase_test.isError():
                _LOGGER.info("Detected 3-phase hybrid - MOD series")
                return 'mod_6000_15000tl3_xh'
            else:
                _LOGGER.info("Detected single-phase hybrid - SPH/TL-XH series")
                return 'sph_3000_10000'  # Default to SPH
        
        # Test for 3-phase at register 38 (MID/MAC/MAX)
        result = await hass.async_add_executor_job(
            client.client.read_input_registers,
            38, 1
        )
        if not result.isError():
            # Check register 42 for second phase
            phase2 = await hass.async_add_executor_job(
                client.client.read_input_registers,
                42, 1
            )
            if not phase2.isError():
                _LOGGER.info("Detected 3-phase grid-tied inverter - MID/MAX series")
                return 'mid_15000_25000tl3_x'  # Default to MID
        
        # Test for PV3 at register 11 (MIN 7-10k has 3 strings)
        result = await hass.async_add_executor_job(
            client.client.read_input_registers,
            11, 1
        )
        if not result.isError() and result.registers[0] > 0:
            _LOGGER.info("Detected 3 PV strings - MIN 7000-10000TL-X")
            return 'min_7000_10000_tl_x'
        
        # Default to MIN 3-6k if nothing else detected
        _LOGGER.info("Detected single-phase with 2 PV strings - MIN 3000-6000TL-X")
        return 'min_3000_6000_tl_x'
        
    except Exception as e:
        _LOGGER.error(f"Exception detecting inverter series: {str(e)}")
        return None


async def async_determine_inverter_type(
    hass: HomeAssistant,
    client: GrowattModbus,
    device_id: int = 1
) -> Tuple[Optional[str], Optional[dict]]:
    """
    Automatically determine the inverter type and return appropriate profile.
    
    Process:
    1. Read model name from holding registers
    2. Attempt to match model name to known profiles
    3. If no match, detect series by probing registers
    4. Return the appropriate profile
    
    Args:
        hass: HomeAssistant instance
        client: GrowattModbus client
        device_id: Modbus device ID (default 1)
    
    Returns:
        Tuple of (profile_key, profile_dict) or (None, None) if detection fails
    """
    _LOGGER.info("Starting automatic inverter type detection")
    
    # Step 1: Try to read model name
    model_name = await async_read_model_name(hass, client, device_id)
    
    if model_name:
        # Step 2: Try to match model name to profile
        profile_key = detect_profile_from_model_name(model_name)
        
        if profile_key:
            profile = get_profile(profile_key)
            if profile:
                _LOGGER.info(f"✓ Auto-detected from model name: {profile['name']}")
                return profile_key, profile
    
    # Step 3: Model name didn't work, try series detection
    _LOGGER.info("Model name detection failed, trying register-based detection...")
    profile_key = await async_detect_inverter_series(hass, client, device_id)
    
    if profile_key:
        profile = get_profile(profile_key)
        if profile:
            _LOGGER.warning(
                f"⚠ Auto-detected by probing registers: {profile['name']}. "
                "Consider manually verifying the exact model for best accuracy."
            )
            return profile_key, profile
    
    # Step 4: Everything failed
    _LOGGER.error("❌ Could not auto-detect inverter type")
    return None, None