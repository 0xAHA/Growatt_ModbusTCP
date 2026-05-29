from .mod import MOD_6000_15000TL3_XH
from .vpp_v201 import (
    VPP_V201_PV2_INPUT,
    VPP_V201_PV3_AND_TOTAL,
)

# MID 11-30KTL3-XH V2.01 Protocol
MID_11000_30000TL3_XH_V201 = {
    **MOD_6000_15000TL3_XH,
    'name': 'MID-XH Series (V2.01)',
    'description': 'Three-phase commercial hybrid inverter (11-30kW) with VPP Protocol V2.01',
    'input_registers': {
        **MOD_6000_15000TL3_XH['input_registers'],
        **VPP_V201_PV2_INPUT,
        **VPP_V201_PV3_AND_TOTAL,
    }
}

MID_XH_REGISTER_MAPS = {
    'MID_11000_30000TL3_XH_V201': MID_11000_30000TL3_XH_V201,
}
