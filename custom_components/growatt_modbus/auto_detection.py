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
        # MIC series - Micro inverters
        'MIC600': 'mic_600_3300tl_x',
        'MIC750': 'mic_600_3300tl_x',
        'MIC1000': 'mic_600_3300tl_x',
        'MIC1500': 'mic_600_3300tl_x',
        'MIC2000': 'mic_600_3300tl_x',
        'MIC2500': 'mic_600_3300tl_x',
        'MIC3000': 'mic_600_3300tl_x',
        'MIC3300': 'mic_600_3300tl_x',
        
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

        # SPH series (single-phase hybrid)
        'SPH3000': 'sph_3000_6000',
        'SPH3600': 'sph_3000_6000',
        'SPH4000': 'sph_3000_6000',
        'SPH5000': 'sph_3000_6000',
        'SPH6000': 'sph_3000_6000',
        'SPH7000': 'sph_7000_10000',
        'SPH8000': 'sph_7000_10000',
        'SPH9000': 'sph_7000_10000',
        'SPH10000': 'sph_7000_10000',
        
        # SPH TL3 series (three-phase hybrid) - MUST CHECK BEFORE SPH
        'SPHTL3': 'sph_tl3_3000_10000',
        'SPH3000TL3': 'sph_tl3_3000_10000',
        'SPH4000TL3': 'sph_tl3_3000_10000',
        'SPH5000TL3': 'sph_tl3_3000_10000',
        'SPH6000TL3': 'sph_tl3_3000_10000',
        'SPH7000TL3': 'sph_tl3_3000_10000',
        'SPH8000TL3': 'sph_tl3_3000_10000',
        'SPH9000TL3': 'sph_tl3_3000_10000',
        'SPH10000TL3': 'sph_tl3_3000_10000',
        
        # MOD series
        'MOD6000': 'mod_6000_15000tl3_xh',
        'MOD8000': 'mod_6000_15000tl3_xh',
        'MOD10000': 'mod_6000_15000tl3_xh',
        'MOD12000': 'mod_6000_15000tl3_xh',
        'MOD15000': 'mod_6000_15000tl3_xh',

        # WIT series (three-phase hybrid residential)
        'WIT4000': 'wit_4000_15000tl3',
        'WIT5000': 'wit_4000_15000tl3',
        'WIT6000': 'wit_4000_15000tl3',
        'WIT8000': 'wit_4000_15000tl3',
        'WIT10000': 'wit_4000_15000tl3',
        'WIT12000': 'wit_4000_15000tl3',
        'WIT15000': 'wit_4000_15000tl3',

    }
    
    # Try to find a match - check longer patterns first to match specific models
    for pattern, profile_key in sorted(patterns.items(), key=lambda x: len(x[0]), reverse=True):
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
            lambda: client.client.read_holding_registers(address=23, count=10)
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
            _LOGGER.debug(f"Read serial number: {serial_number}")
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
            lambda: client.client.read_holding_registers(address=0, count=5)
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
            _LOGGER.debug(f"Read model name: {model_name}")
            return model_name
        
        return None
        
    except Exception as e:
        _LOGGER.debug(f"Exception reading model name: {str(e)}")
        return None


async def async_read_dtc_code_offgrid(
    hass: HomeAssistant,
    client: GrowattModbus,
    device_id: int = 1
) -> Optional[int]:
    """
    Read DTC (Device Type Code) from OffGrid protocol registers.

    OffGrid inverters (SPF series) use a different register layout than VPP 2.01.
    CRITICAL: Reading VPP registers (30000+, 31000+) causes POWER RESETS on SPF inverters!

    OffGrid DTC locations (Protocol v0.11):
    - Input register 44 (PRIMARY per Protocol v0.11)
    - Holding register 43 (FALLBACK)
    - Input register 34 (LEGACY - now used for ac_current in newer protocol)

    Args:
        hass: HomeAssistant instance
        client: GrowattModbus client
        device_id: Modbus device ID (default 1)

    Returns:
        DTC code (int) or None if read fails
    """
    # Try input register 44 first (Protocol v0.11 standard)
    try:
        result = await hass.async_add_executor_job(
            client.read_input_registers, 44, 1
        )

        if result is not None and len(result) > 0:
            dtc_code = result[0]
            if dtc_code and dtc_code > 0:
                _LOGGER.info(f"✓ OffGrid DTC Detection - Read DTC code: {dtc_code} from input register 44")
                return dtc_code

    except Exception as e:
        _LOGGER.debug(f"Could not read DTC from input register 44: {str(e)}")

    # Fallback to holding register 43
    try:
        result = await hass.async_add_executor_job(
            lambda: client.client.read_holding_registers(address=43, count=1)
        )

        if not result.isError():
            dtc_code = result.registers[0]
            if dtc_code and dtc_code > 0:
                _LOGGER.info(f"✓ OffGrid DTC Detection - Read DTC code: {dtc_code} from holding register 43")
                return dtc_code

    except Exception as e:
        _LOGGER.debug(f"Could not read DTC from holding register 43: {str(e)}")

    # Legacy: Try input register 34 (backward compatibility - this register now used for ac_current)
    try:
        result = await hass.async_add_executor_job(
            client.read_input_registers, 34, 1
        )

        if result is not None and len(result) > 0:
            dtc_code = result[0]
            if dtc_code and dtc_code > 0 and dtc_code in (3400, 3401, 3402, 3403):  # Only accept valid SPF DTC codes
                _LOGGER.info(f"✓ OffGrid DTC Detection - Read DTC code: {dtc_code} from input register 34 (legacy)")
                return dtc_code

    except Exception as e:
        _LOGGER.debug(f"Could not read DTC from input register 34: {str(e)}")

    _LOGGER.debug("No OffGrid DTC found in registers 44, 43, or 34")
    return None


async def async_read_dtc_code(
    hass: HomeAssistant,
    client: GrowattModbus,
    device_id: int = 1
) -> Optional[int]:
    """
    Read DTC (Device Type Code) from VPP 2.01 holding register 30000.

    WARNING: This register causes POWER RESETS on OffGrid inverters (SPF series)!
    Use async_read_dtc_code_offgrid() first to safely detect OffGrid models.

    This is the standard DTC location for VPP 2.01 protocol inverters.

    Args:
        hass: HomeAssistant instance
        client: GrowattModbus client
        device_id: Modbus device ID (default 1)

    Returns:
        DTC code (int) or None if read fails
    """
    try:
        # Read DTC from holding register 30000
        result = await hass.async_add_executor_job(
            lambda: client.client.read_holding_registers(address=30000, count=1)
        )

        if result.isError():
            _LOGGER.warning(f"Failed to read DTC code from register 30000: {result}")
            return None

        dtc_code = result.registers[0]
        if dtc_code and dtc_code > 0:
            _LOGGER.info(f"✓ VPP DTC Detection - Read DTC code: {dtc_code} from holding register 30000")
            return dtc_code
        else:
            _LOGGER.warning(f"DTC code register 30000 returned 0 or invalid value: {dtc_code}")
            return None

    except Exception as e:
        _LOGGER.warning(f"Exception reading DTC code from register 30000: {str(e)}")
        return None


async def async_read_protocol_version(
    hass: HomeAssistant,
    client: GrowattModbus,
    device_id: int = 1
) -> Optional[int]:
    """
    Read VPP Protocol Version from holding register 30099.

    Returns:
        - 200: V2.00
        - 201: V2.01
        - 202: V2.02
        - 0 or None: Legacy protocol (V1.39/V3.05) - no V2.01 support

    Args:
        hass: HomeAssistant instance
        client: GrowattModbus client
        device_id: Modbus device ID (default 1)

    Returns:
        Protocol version code (int) or None if not readable
    """
    try:
        # Read protocol version from holding register 30099
        result = await hass.async_add_executor_job(
            lambda: client.client.read_holding_registers(address=30099, count=1)
        )

        if result.isError():
            _LOGGER.debug(f"Protocol version register 30099 not readable (legacy inverter)")
            return None

        protocol_version = result.registers[0]

        if protocol_version == 0:
            _LOGGER.info(f"✓ Protocol version check - Register 30099 = 0 (Legacy protocol, no V2.01 support)")
            return 0
        elif protocol_version in (200, 201, 202):
            version_str = f"V{protocol_version // 100}.{protocol_version % 100:02d}"
            _LOGGER.info(f"✓ Protocol version check - Register 30099 = {protocol_version} (Protocol {version_str})")
            return protocol_version
        else:
            _LOGGER.warning(f"Unexpected protocol version value: {protocol_version}")
            return protocol_version

    except Exception as e:
        _LOGGER.debug(f"Exception reading protocol version from register 30099: {str(e)}")
        return None


def detect_profile_from_dtc(dtc_code: int) -> Optional[str]:
    """
    Match DTC (Device Type Code) to a profile.

    DTC Location by Protocol:
    - OffGrid Protocol (SPF): Input reg 34 or Holding reg 43
    - VPP 2.01 Protocol: Holding reg 30000

    DTC Codes by Protocol:

    ** OffGrid Protocol (SPF series) **
    - SPF 3000-6000 ES PLUS: 3400-3403
    CRITICAL: OffGrid inverters will RESET if VPP registers (30000+, 31000+) are accessed!

    ** VPP 2.01 Protocol **
    - SPH 3000-6000TL BL: 3502
    - SPA 3000-6000TL BL: 3735
    - SPA 4000-10000TL3 BH-UP: 3725
    - SPH 4000-10000TL3 BH-UP: 3601
    - MIN 2500-6000TL-XH/XH(P): 5100
    - MIC/MIN 2500-6000TL-X/X2: 5200
    - MIN 7000-10000TL-X/X2: 5201
    - MOD-XH/MID-XH: 5400
    - WIT 4-15kW: 5603
    - WIT 100KTL3-H: 5601
    - WIS 215KTL3: 5800

    Args:
        dtc_code: DTC code from OffGrid (reg 44/43/34) or VPP (reg 30000)

    Returns:
        Profile key or None if no match
    """
    # Only official DTC codes from Growatt VPP 2.01 Protocol documentation Table 3-1
    # Note: Some legacy models use DTC register but don't support full V2.01 protocol
    dtc_map = {
        # SPH series - Official Growatt DTCs
        3501: 'sph_3000_6000_v201',       # SPH 3000-6000TL BL (legacy/pre-UP, may need protocol check)
        3502: 'sph_3000_6000_v201',       # SPH 3000-6000TL BL -UP (upgraded model)
        3735: 'sph_3000_6000_v201',       # SPA 3000-6000TL BL (similar to SPH)
        3601: 'sph_tl3_3000_10000_v201',  # SPH 4000-10000TL3 BH-UP
        3725: 'sph_tl3_3000_10000_v201',  # SPA 4000-10000TL3 BH-UP

        # SPF series - Off-Grid (034xx range from SPF protocol documentation)
        3400: 'spf_3000_6000_es_plus',         # SPF 3000-6000 ES PLUS (off-grid)
        3401: 'spf_3000_6000_es_plus',         # SPF 3000-6000 ES PLUS variant
        3402: 'spf_3000_6000_es_plus',         # SPF 3000-6000 ES PLUS variant
        3403: 'spf_3000_6000_es_plus',         # SPF 3000-6000 ES PLUS variant

        # MIN/TL-XH/MIC series - Official Growatt DTCs
        5100: 'tl_xh_3000_10000_v201',    # MIN 2500-6000TL-XH/XH(P) - covers TL-XH
        5200: 'min_3000_6000_tl_x_v201',  # MIC/MIN 2500-6000TL-X/X2 - shared code, prioritize MIN
        5201: 'min_7000_10000_tl_x_v201', # MIN 7000-10000TL-X/X2

        # MOD/MID series - Official Growatt DTC
        5400: 'mod_6000_15000tl3_xh_v201', # MOD-XH\MID-XH - covers both MOD and MID

        # WIT/WIS series - Official Growatt DTCs
        # Register 988 can distinguish: 0=WIT, 1=WIS
        5603: 'wit_4000_15000tl3',          # WIT 4-15kW (residential three-phase hybrid) - Protocol V2.02
        5601: 'mid_15000_25000tl3_x_v201',  # WIT 100KTL3-H (commercial)
        5800: 'mid_15000_25000tl3_x_v201',  # WIS 215KTL3 (commercial)
    }

    profile_key = dtc_map.get(dtc_code)
    if profile_key:
        _LOGGER.info(f"Matched DTC code {dtc_code} to V2.01 profile '{profile_key}'")
        return profile_key

    _LOGGER.warning(f"✗ DTC Detection - Unknown DTC code: {dtc_code} (not in supported models)")
    return None


def convert_to_legacy_profile(profile_key: str) -> str:
    """
    Convert V2.01 profile key to legacy equivalent when inverter doesn't support V2.01.

    This is needed for inverters that have DTC codes in register 30000 but return
    protocol version 0 from register 30099, indicating legacy protocol support only.

    Args:
        profile_key: V2.01 profile key (e.g., 'sph_3000_6000_v201')

    Returns:
        Legacy profile key (e.g., 'sph_3000_6000') or original if no conversion needed
    """
    # Mapping from V2.01 profiles to legacy equivalents
    v201_to_legacy = {
        'sph_3000_6000_v201': 'sph_3000_6000',
        'sph_7000_10000_v201': 'sph_7000_10000',
        'sph_tl3_3000_10000_v201': 'sph_tl3_3000_10000',
        'min_3000_6000_tl_x_v201': 'min_3000_6000_tl_x',
        'min_7000_10000_tl_x_v201': 'min_7000_10000_tl_x',
        'tl_xh_3000_10000_v201': 'tl_xh_3000_10000',
        'mic_600_3300tl_x_v201': 'mic_600_3300tl_x',
        'mod_6000_15000tl3_xh_v201': 'mod_6000_15000tl3_xh',
        'mid_15000_25000tl3_x_v201': 'mid_15000_25000tl3_x',
    }

    legacy_key = v201_to_legacy.get(profile_key, profile_key)

    if legacy_key != profile_key:
        _LOGGER.info(f"Converting V2.01 profile '{profile_key}' to legacy '{legacy_key}' (protocol version 0)")

    return legacy_key


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
        # Ensure client is connected
        if not await hass.async_add_executor_job(client.connect):
            _LOGGER.error("Failed to connect to inverter for detection")
            return None

        # CHECK MIC SERIES FIRST (uses 0-179 range, legacy V3.05 protocol)
        # MIC micro inverters use compact register range and should be detected before MIN
        # Test for PV1 voltage at register 3 (0-179 range indicator)
        mic_test = await hass.async_add_executor_job(
            client.read_input_registers, 3, 1
        )
        if mic_test is not None and len(mic_test) > 0:
            # Verify this is MIC not MIN by checking that 3000 range is NOT available
            # MIN uses 3000+, MIC uses 0-179
            min_range_test = await hass.async_add_executor_job(
                client.read_input_registers, 3003, 1
            )
            if min_range_test is None:
                # Has 0-179 range but NOT 3000 range = MIC series
                _LOGGER.debug("Detected 0-179 range without 3000 range - MIC micro inverter")
                await hass.async_add_executor_job(client.disconnect)
                return 'mic_600_3300tl_x'

        # CHECK MIN SERIES (uses 3000 range)
        # Test for PV1 at register 3003 to confirm MIN series
        min_test = await hass.async_add_executor_job(
            client.read_input_registers, 3003, 1
        )
        if min_test is not None:
            _LOGGER.debug("Detected 3000-range registers - MIN series inverter")

            # Check for battery in VPP range (31200+) to detect MIN TL-XH hybrid variant
            battery_test = await hass.async_add_executor_job(
                client.read_input_registers, 31217, 1  # Battery SOC in VPP range
            )
            if battery_test is not None and len(battery_test) > 0 and battery_test[0] > 0:
                _LOGGER.debug("Detected battery in 31200+ range - MIN TL-XH hybrid variant")
                await hass.async_add_executor_job(client.disconnect)
                return 'min_tl_xh_3000_10000_v201'

            # Test for PV3 at register 3011 (MIN 7-10k has 3 strings)
            pv3_test = await hass.async_add_executor_job(
                client.read_input_registers, 3011, 1
            )
            if pv3_test is not None:  # Register exists, even if value is 0
                _LOGGER.debug("Detected PV3 register - MIN 7000-10000TL-X")
                await hass.async_add_executor_job(client.disconnect)
                return 'min_7000_10000_tl_x'
            else:
                _LOGGER.debug("No PV3 register - MIN 3000-6000TL-X")
                await hass.async_add_executor_job(client.disconnect)
                return 'min_3000_6000_tl_x'
        
        # Test for battery registers at 3169 (SPH/TL-XH/MOD specific)
        result = await hass.async_add_executor_job(
            client.read_input_registers, 3169, 1
        )
        if result is not None:
            _LOGGER.debug("Detected battery voltage register returns value")
            
            # Check for 3-phase at register 42 (S-phase voltage)
            phase_s_test = await hass.async_add_executor_job(
                client.read_input_registers, 42, 1
            )
            # Check for 3-phase at register 46 (T-phase voltage)
            phase_t_test = await hass.async_add_executor_job(
                client.read_input_registers, 46, 1
            )
            
            if phase_s_test and phase_t_test:
                _LOGGER.debug("Detected 3-phase with battery register - SPH TL3 or MOD series")

                # Check for MOD-specific 31200 range (battery power per VPP Protocol V2.01)
                mod_test = await hass.async_add_executor_job(
                    client.read_input_registers, 31200, 1
                )
                if mod_test is not None:
                    _LOGGER.debug("Detected 31200 range (VPP Protocol) - MOD-XH hybrid")
                    await hass.async_add_executor_job(client.disconnect)
                    return 'mod_6000_15000tl3_xh'

                # Check for register 1000 range (SPH TL3 specific)
                storage_test = await hass.async_add_executor_job(
                    client.read_input_registers, 1000, 1
                )
                if storage_test is not None:
                    _LOGGER.debug("Detected storage range - SPH TL3 series")
                    await hass.async_add_executor_job(client.disconnect)
                    return 'sph_tl3_3000_10000'
                else:
                    _LOGGER.info("No distinctive registers found - defaulting to MOD-XH hybrid")
                    await hass.async_add_executor_job(client.disconnect)
                    return 'mod_6000_15000tl3_xh'
            else:
                _LOGGER.debug("Detected single-phase hybrid - SPH or TL-XH series")

                # Check for storage range 1000+ (SPH HU models)
                storage_test = await hass.async_add_executor_job(
                    client.read_input_registers, 1086, 1  # BMS SOC at 1086
                )
                if storage_test is not None:
                    _LOGGER.debug("Detected storage range with BMS - SPH/SPM 8000-10000TL-HU")
                    await hass.async_add_executor_job(client.disconnect)
                    return 'sph_8000_10000_hu'

                # Check for PV3 (7-10kW has 3 strings, 3-6kW has 2 strings)
                pv3_test = await hass.async_add_executor_job(
                    client.read_input_registers, 11, 1  # PV3 voltage
                )
                if pv3_test is not None and len(pv3_test) > 0 and pv3_test[0] > 0:
                    _LOGGER.debug("Detected PV3 string - SPH 7-10kW")
                    await hass.async_add_executor_job(client.disconnect)
                    return 'sph_7000_10000'
                else:
                    _LOGGER.debug("No PV3 string - SPH 3-6kW")
                    await hass.async_add_executor_job(client.disconnect)
                    return 'sph_3000_6000'
        
        # Test for 3-phase at register 38 (MID/MAX/MOD-X grid-tied)
        result = await hass.async_add_executor_job(
            client.read_input_registers, 38, 1
        )
        if result:
            # Check register 42 for second phase
            phase2 = await hass.async_add_executor_job(
                client.read_input_registers, 42, 1
            )
            if phase2:
                _LOGGER.debug("Detected 3-phase grid-tied inverter")

                # Check for 3000 range (MOD-X uses 3000 range, MID uses 0-124)
                mod_range_test = await hass.async_add_executor_job(
                    client.read_input_registers, 3003, 1
                )
                if mod_range_test is not None:
                    _LOGGER.debug("Detected 3000 range - MOD-X grid-tied (no battery)")
                    await hass.async_add_executor_job(client.disconnect)
                    return 'mod_6000_15000tl3_x'
                else:
                    _LOGGER.debug("No 3000 range - MID series")
                    await hass.async_add_executor_job(client.disconnect)
                    return 'mid_15000_25000tl3_x'
        
        # Default fallback
        _LOGGER.warning("Could not definitively detect inverter series, defaulting to MIN 3000-6000TL-X")
        await hass.async_add_executor_job(client.disconnect)
        return 'min_3000_6000_tl_x'
        
    except Exception as e:
        _LOGGER.error(f"Exception detecting inverter series: {str(e)}")
        try:
            await hass.async_add_executor_job(client.disconnect)
        except:
            pass
        return None

async def async_refine_dtc_detection(
    hass: HomeAssistant,
    client: GrowattModbus,
    dtc_code: int,
    initial_profile_key: str,
    device_id: int = 1
) -> str:
    """
    Refine DTC detection for models that share the same DTC code.

    Uses additional V2.01 register checks to differentiate (with legacy fallback):
    - SPH 3-6kW vs 7-10kW (DTC 3502): Check PV3 presence (31018 or 11)
    - MOD vs MID (DTC 5400): Check battery SOC (31217) or voltage (3169)
    - MIC vs MIN (DTC 5200): Check MIN range (31010 or 3003)

    Since DTC exists, prefer V2.01 registers (30000+ range) first, then
    fallback to legacy registers for robustness.

    Args:
        hass: HomeAssistant instance
        client: GrowattModbus client
        dtc_code: DTC code from register 30000
        initial_profile_key: Initial profile from DTC mapping
        device_id: Modbus device ID

    Returns:
        Refined profile key
    """
    try:
        # DTC 3502: SPH 3-6kW vs 7-10kW vs 8-10kW HU
        # Priority: Storage Range (HU) > PV3 (7-10kW) > No PV3 (3-6kW)
        if dtc_code == 3502:
            # Check for storage range 1000-1124 (SPH/SPM 8000-10000TL-HU exclusive)
            # HU models have extended storage range with BMS registers at 1082+
            result = await hass.async_add_executor_job(
                client.read_input_registers, 1086, 1  # BMS SOC register (HU-specific)
            )
            if result is not None:
                _LOGGER.info("Detected storage range 1000+ with BMS registers - SPH/SPM 8000-10000TL-HU")
                return 'sph_8000_10000_hu'

            # Check V2.01 PV3 voltage register (31018)
            result = await hass.async_add_executor_job(
                client.read_input_registers, 31018, 1  # V2.01 PV3 voltage
            )
            if result is not None and len(result) > 0 and result[0] > 0:
                _LOGGER.info("Detected PV3 in V2.01 range (3PV) - SPH 7-10kW")
                return 'sph_7000_10000_v201'

            # Fallback to legacy register 11 (base range PV3 voltage)
            result = await hass.async_add_executor_job(
                client.read_input_registers, 11, 1  # Legacy PV3 voltage
            )
            if result is not None and len(result) > 0 and result[0] > 0:
                _LOGGER.info("Detected PV3 in legacy range (3PV) - SPH 7-10kW")
                return 'sph_7000_10000_v201'
            else:
                _LOGGER.info("No PV3 string (2PV) - SPH 3-6kW")
                return 'sph_3000_6000_v201'

        # DTC 5400: MOD-XH (hybrid) vs MOD-X (grid-tied) vs MID
        # Check V2.01 battery registers (MOD-XH has battery, MOD-X/MID don't)
        elif dtc_code == 5400:
            # Try V2.01 battery SOC register (31217)
            result = await hass.async_add_executor_job(
                client.read_input_registers, 31217, 1  # V2.01 Battery SOC
            )
            if result is not None and len(result) > 0 and result[0] > 0:
                _LOGGER.info("Detected V2.01 battery SOC register (31217) with valid value - MOD-XH hybrid")
                return 'mod_6000_15000tl3_xh_v201'

            # Fallback to legacy battery register (3169)
            result = await hass.async_add_executor_job(
                client.read_input_registers, 3169, 1  # Legacy battery voltage
            )
            if result is not None and len(result) > 0 and result[0] > 0:
                _LOGGER.info("Detected legacy battery voltage register (3169) with valid value - MOD-XH hybrid")
                return 'mod_6000_15000tl3_xh_v201'

            # Check for 3000+ range to distinguish MOD (grid-tied) from MID
            result = await hass.async_add_executor_job(
                client.read_input_registers, 3003, 1  # MOD uses 3000 range, MID uses 0-124
            )
            if result is not None:
                _LOGGER.info("No battery but 3000+ range detected - MOD-X grid-tied")
                return 'mod_6000_15000tl3_x'  # Grid-tied MOD without V2.01 suffix (uses legacy registers)
            else:
                _LOGGER.info("No battery, no 3000+ range - MID series")
                return 'mid_15000_25000tl3_x_v201'

        # DTC 5100: TL-XH standard (0-124 range) vs MIN TL-XH hybrid (3000+ range)
        # Check if inverter uses MIN series 3000+ range instead of standard TL-XH 0-124 range
        elif dtc_code == 5100:
            # Check for MIN range (3000+) - PV1 voltage at 3003
            result = await hass.async_add_executor_job(
                client.read_input_registers, 3003, 1  # MIN PV1 voltage
            )
            if result is not None and len(result) > 0:
                # This is MIN TL-XH variant using 3000+ range with battery in 31200+ range
                _LOGGER.info("Detected 3000+ range with DTC 5100 - MIN TL-XH hybrid variant")
                # Verify battery registers exist in VPP range (31200+)
                battery_test = await hass.async_add_executor_job(
                    client.read_input_registers, 31217, 1  # Battery SOC in VPP range
                )
                if battery_test is not None:
                    _LOGGER.info("Confirmed battery in 31200+ range - MIN TL-XH V2.01")
                    return 'min_tl_xh_3000_10000_v201'
                else:
                    _LOGGER.warning("No battery found in 31200+ range despite 3000+ base range")
                    return 'min_tl_xh_3000_10000_v201'  # Still use MIN TL-XH profile
            else:
                # Standard TL-XH using 0-124 range
                _LOGGER.info("No 3000+ range detected - Standard TL-XH with 0-124 range")
                return 'tl_xh_3000_10000_v201'

        # DTC 5200: MIC vs MIN - Check register range (MIC uses 0-179, MIN uses 3000+)
        elif dtc_code == 5200:
            # Try V2.01 MIN range first (31010 - PV1 voltage in V2.01)
            result = await hass.async_add_executor_job(
                client.read_input_registers, 31010, 1  # V2.01 MIN PV1 voltage
            )
            if result is not None:
                _LOGGER.info("Detected V2.01 31000+ range - MIN series")
                return 'min_3000_6000_tl_x_v201'

            # Fallback to legacy MIN's 3000 range
            result = await hass.async_add_executor_job(
                client.read_input_registers, 3003, 1  # Legacy MIN PV1 voltage
            )
            if result is not None:
                _LOGGER.info("Detected legacy 3000+ range - MIN series")
                return 'min_3000_6000_tl_x_v201'
            else:
                _LOGGER.info("No 3000+ range - MIC series")
                return 'mic_600_3300tl_x_v201'

    except Exception as e:
        _LOGGER.debug(f"Error during DTC refinement: {e}")

    # Return initial profile if refinement fails or not applicable
    return initial_profile_key


async def async_determine_inverter_type(
    hass: HomeAssistant,
    client: GrowattModbus,
    device_id: int = 1
) -> Tuple[Optional[str], Optional[dict]]:
    """
    Automatically determine the inverter type and return appropriate profile.

    Process:
    1. Try OffGrid DTC (register 34/43) FIRST - prevents SPF power resets
    2. Try VPP DTC (register 30000) if OffGrid fails - standard method
    3. For ambiguous DTCs (shared codes), refine with additional register checks
    4. Verify protocol version (register 30099) - convert to legacy if version is 0
    5. Read model name from holding registers and match
    6. If no match, detect series by probing registers
    7. Return the appropriate profile

    CRITICAL: OffGrid inverters (SPF) will RESET if VPP registers (30000+, 31000+)
    are accessed! We detect OffGrid models first to prevent this.

    Protocol Version Check:
    - Register 30099 = 201: Full V2.01 support, use V2.01 profiles
    - Register 30099 = 0 or not readable: Legacy protocol only, use legacy profiles
    - This handles inverters with DTC codes but legacy firmware (e.g., SPH 3-6kW pre-UP)

    Args:
        hass: HomeAssistant instance
        client: GrowattModbus client
        device_id: Modbus device ID (default 1)

    Returns:
        Tuple of (profile_key, profile_dict) or (None, None) if detection fails
    """
    _LOGGER.info("Starting automatic inverter type detection")

    # Step 1: Try OffGrid DTC first (registers 34/43) - SAFE for all inverters
    # This prevents SPF inverters from power reset when reading VPP registers
    dtc_code = await async_read_dtc_code_offgrid(hass, client, device_id)

    if dtc_code:
        profile_key = detect_profile_from_dtc(dtc_code)

        if profile_key:
            # Check if this is an SPF (OffGrid) inverter
            if profile_key.startswith('spf_'):
                # SPF detected - skip VPP register probing to prevent resets
                profile = get_profile(profile_key)
                if profile:
                    _LOGGER.info(f"✓ Auto-detected OffGrid inverter from DTC code {dtc_code}: {profile['name']}")
                    _LOGGER.info("⚠ Skipping VPP register probing to prevent power reset on OffGrid inverter")
                    return profile_key, profile

            # Non-SPF OffGrid DTC or ambiguous - proceed with refinement
            profile_key = await async_refine_dtc_detection(hass, client, dtc_code, profile_key, device_id)

            profile = get_profile(profile_key)
            if profile:
                _LOGGER.info(f"✓ Auto-detected from OffGrid DTC code {dtc_code}: {profile['name']}")
                return profile_key, profile

    # Step 2: Try VPP 2.01 DTC (register 30000) if OffGrid detection failed
    # Safe now because SPF would have been detected in Step 1
    dtc_code = await async_read_dtc_code(hass, client, device_id)

    if dtc_code:
        profile_key = detect_profile_from_dtc(dtc_code)

        if profile_key:
            # Step 2.5: Refine DTC detection for ambiguous codes
            profile_key = await async_refine_dtc_detection(hass, client, dtc_code, profile_key, device_id)

            # Step 2.6: Verify protocol version support
            # Some inverters have DTC codes but don't support full V2.01 protocol
            # Check register 30099: 201 = V2.01, 0 = Legacy protocol
            protocol_version = await async_read_protocol_version(hass, client, device_id)

            if protocol_version == 0 or protocol_version is None:
                # Protocol version 0 or not readable = Legacy protocol only
                # Convert V2.01 profile to legacy equivalent
                profile_key = convert_to_legacy_profile(profile_key)
                _LOGGER.info(f"✓ Using legacy profile due to protocol version 0 or not readable")

            profile = get_profile(profile_key)
            if profile:
                _LOGGER.info(f"✓ Auto-detected from VPP DTC code {dtc_code}: {profile['name']}")
                return profile_key, profile

    # Step 2: Try to read model name
    model_name = await async_read_model_name(hass, client, device_id)

    if model_name:
        profile_key = detect_profile_from_model_name(model_name)

        if profile_key:
            profile = get_profile(profile_key)
            if profile:
                _LOGGER.info(f"✓ Auto-detected from model name: {profile['name']}")
                return profile_key, profile

    # Step 3: DTC and model name didn't work, try register probing
    _LOGGER.info("DTC and model name detection failed, trying register-based detection...")
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
