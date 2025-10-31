"""Growatt Inverter Profile Collection.

This package contains individual profile files for each inverter series.
Each profile defines register maps with proper integer keys and paired registers.

Profile Structure:
- min.py: MIN series (3-10kW single-phase)
- mid.py: MID series (15-25kW three-phase)
- mod.py: MOD series (6-15kW three-phase hybrid)
- tl_xh.py: TL-XH series (3-10kW hybrid)
- sph.py: SPH series (storage/battery)
- max.py: MAX series (50-125kW commercial)
- mac.py: MAC series (20-40kW compact)
- mix.py: MIX series (legacy storage)
- spa.py: SPA series (AC-coupled storage)
- wit.py: WIT series (business storage)
"""

from typing import Dict, List, Optional

# Import register maps from individual profile files
from .min import MIN_REGISTER_MAPS
from .mid import MID_REGISTER_MAPS
from .sph import SPH_REGISTER_MAPS
from .sph_tl3 import SPH_TL3_REGISTER_MAPS
from .mod import MOD_REGISTER_MAPS
from .tl_xh import TL_XH_REGISTER_MAPS
from .max import MAX_REGISTER_MAPS
from .mac import MAC_REGISTER_MAPS
from .mix import MIX_REGISTER_MAPS
from .spa import SPA_REGISTER_MAPS
from .wit import WIT_REGISTER_MAPS

# Combine all register maps into single dict
REGISTER_MAPS = {
    **MIN_REGISTER_MAPS,
    **MID_REGISTER_MAPS,
    **SPH_REGISTER_MAPS,
    **SPH_TL3_REGISTER_MAPS,
    **MOD_REGISTER_MAPS,
    **TL_XH_REGISTER_MAPS,
    **MAX_REGISTER_MAPS,
    **MAC_REGISTER_MAPS,
    **MIX_REGISTER_MAPS,
    **SPA_REGISTER_MAPS,
    **WIT_REGISTER_MAPS,
}


def get_profile(profile_key: str) -> Optional[Dict]:
    """Get a profile by its key.
    
    Args:
        profile_key: Profile identifier (e.g., 'MIN_7000_10000TL_X')
    
    Returns:
        Profile dictionary with 'input_registers' and 'holding_registers' keys
        or None if not found
    """
    return REGISTER_MAPS.get(profile_key)


def get_available_profiles() -> Dict[str, str]:
    """Get all available profiles as key: name pairs.
    
    Returns:
        Dictionary mapping profile keys to display names
    """
    return {
        key: profile.get("name", key)
        for key, profile in REGISTER_MAPS.items()
    }


def get_profile_keys() -> List[str]:
    """Get list of all profile keys.
    
    Returns:
        List of profile key strings
    """
    return list(REGISTER_MAPS.keys())


def list_profiles():
    """Print all available profiles with descriptions."""
    print("Available Growatt Inverter Profiles")
    print("=" * 60)
    for key, profile in REGISTER_MAPS.items():
        print(f"\n{key}:")
        print(f"  Name: {profile.get('name', 'N/A')}")
        print(f"  Description: {profile.get('description', 'N/A')}")
        if 'notes' in profile:
            print(f"  Notes: {profile['notes']}")
        # Count registers
        input_regs = len(profile.get('input_registers', {}))
        holding_regs = len(profile.get('holding_registers', {}))
        print(f"  Registers: {input_regs} input, {holding_regs} holding")


__all__ = [
    "REGISTER_MAPS",
    "get_profile",
    "get_available_profiles",
    "get_profile_keys",
    "list_profiles",
]