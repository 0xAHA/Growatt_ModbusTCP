#!/usr/bin/env python3
"""
Growatt MIN-10000 Modbus Reader
Home Assistant Integration Module

This module handles communication with Growatt MIN series inverters via RS485 Modbus.
Based on Growatt Modbus RTU Protocol V1.39 documentation.

REQUIREMENTS:
- Python 3.7+
- pymodbus (pip install pymodbus)
- pyserial (pip install pyserial) 

Hardware Setup:
- Connect RS485-to-USB/TCP converter to inverter SYS COM port pins 3&4
- Set converter to 9600 baud, 8N1, no flow control
"""

import time
import logging
import threading
from datetime import datetime, timedelta
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple, Union
from homeassistant.config_entries import ConfigEntry

# Import register definitions
from .const import STATUS_CODES, combine_registers, REGISTER_MAPS

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pymodbus.client import ModbusTcpClient, ModbusSerialClient

try:
    # For RS485-to-USB connection
    import serial
    # Try new import style first (pymodbus 3.x+)
    try:
        from pymodbus.client import ModbusSerialClient as ModbusClient
    except ImportError:
        # Fall back to old import style (pymodbus 2.x)
        from pymodbus.client.sync import ModbusSerialClient as ModbusClient
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False

try:
    # For RS485-to-TCP connection (like EW11)
    # Try new import style first (pymodbus 3.x+)
    try:
        from pymodbus.client import ModbusTcpClient
    except ImportError:
        # Fall back to old import style (pymodbus 2.x)
        from pymodbus.client.sync import ModbusTcpClient
    TCP_AVAILABLE = True
except ImportError:
    TCP_AVAILABLE = False

# Configure logging
logger = logging.getLogger(__name__)


# =============================================================================
# Custom Exceptions for better error reporting
# =============================================================================

class ModbusWriteError(Exception):
    """Exception raised when a Modbus write operation fails.

    Contains detailed error information including the register address,
    values attempted, and the actual Modbus error message.
    """
    def __init__(self, register: int, values: list, error_message: str):
        self.register = register
        self.values = values
        self.error_message = error_message
        super().__init__(f"Failed to write registers {register}-{register + len(values) - 1}: {error_message}")


def _format_modbus_error(result) -> str:
    """Format a Modbus error response into a human-readable string.

    Extracts exception codes and provides descriptive messages for common errors.
    """
    EXCEPTION_CODES = {
        1: "Illegal function (function code not supported)",
        2: "Illegal data address (register address not valid)",
        3: "Illegal data value (value rejected by device)",
        4: "Slave device failure (device internal error)",
        5: "Acknowledge (request accepted, processing)",
        6: "Slave device busy (device is busy, retry later)",
        7: "Negative acknowledge",
        8: "Memory parity error",
        10: "Gateway path unavailable",
        11: "Gateway target device failed to respond",
    }

    error_parts = []

    exception_code = None
    if hasattr(result, 'exception_code'):
        exception_code = result.exception_code
    elif hasattr(result, 'function_code') and result.function_code >= 0x80:
        exception_code = getattr(result, 'exception_code', None)

    if exception_code is not None:
        code_desc = EXCEPTION_CODES.get(exception_code, f"Unknown exception code {exception_code}")
        error_parts.append(f"Modbus exception {exception_code}: {code_desc}")

    result_str = str(result)
    if result_str and result_str not in str(error_parts):
        error_parts.append(f"Raw response: {result_str}")

    return " | ".join(error_parts) if error_parts else str(result)


# =============================================================================
# Write verification constants (cloud override detection)
# =============================================================================

WRITE_VERIFY_DELAY = 0.5           # seconds — delay before read-back after write
WRITE_VERIFY_MAX_RETRIES = 3       # read-back checks after the single write (#402)
WRITE_VERIFY_MAX_DELAY = 2.0       # seconds - ceiling for the backoff between checks

# Minimum battery power before the WIT scale detection will draw a conclusion (#406).
# Below this the current registers disagree and the comparison is meaningless.
_BATTERY_SCALE_MIN_POWER_W = 500.0
WRITE_VERIFY_RETRY_DELAY = 1.5     # seconds — delay between retry attempts


@dataclass
class GrowattData:
    """Container for Growatt inverter data"""

    # Fields whose register could not be read this poll (#384).
    #
    # A block read that fails leaves its addresses absent from the register cache, and the
    # decode below turned that into 0.0 - so a single dropped frame published "the sun went
    # out" for one poll, with no error anywhere because from Home Assistant's side the poll
    # succeeded. A reporter's graph showed PV voltage, current and power all dropping to zero
    # together and recovering on the next poll, which is what a shared block failing looks
    # like.
    #
    # Recorded as names rather than by setting the fields to None, because several are summed
    # (pv_total_power = pv1 + pv2 + pv3 + pv4) and None would raise. The value keeps its
    # previous or default number and the sensor consults this set to decide whether to report
    # it at all - so the entity goes unknown for that poll and leaves a gap in history, rather
    # than recording a zero that reads as a real measurement.
    unread_fields: set = field(default_factory=set)

    # Solar Input
    pv1_voltage: float = 0.0          # V
    pv1_current: float = 0.0          # A
    pv1_power: float = 0.0            # W
    pv1_energy_today: float = 0.0     # kWh (WIT per-MPPT energy tracking - Issue #146)
    pv1_energy_total: float = 0.0     # kWh (MIN per-MPPT lifetime total - Issue #265)
    pv2_voltage: float = 0.0          # V
    pv2_current: float = 0.0          # A
    pv2_power: float = 0.0            # W
    pv2_energy_today: float = 0.0     # kWh (WIT per-MPPT energy tracking - Issue #146)
    pv2_energy_total: float = 0.0     # kWh (MIN per-MPPT lifetime total - Issue #265)
    pv3_voltage: float = 0.0          # V
    pv3_current: float = 0.0          # A
    pv3_power: float = 0.0            # W
    pv3_energy_today: float = 0.0     # kWh (3-string models like SPH TL3 10000 - Issue #211)
    pv3_energy_total: float = 0.0     # kWh (MIN 7-10kW per-MPPT lifetime total - Issue #265)
    pv4_voltage: float = 0.0          # V (WIT 29.9-50K-XHU 4th MPPT - Issue #338)
    pv4_current: float = 0.0          # A
    pv4_power: float = 0.0            # W
    pv4_energy_today: float = 0.0     # kWh
    pv4_energy_total: float = 0.0     # kWh
    pv_total_power: float = 0.0       # W
    pv_energy_total: float = 0.0      # kWh (WIT total PV lifetime energy - Issue #146)
    
    # AC Output (generic - usually Phase R for 3-phase)
    ac_voltage: float = 0.0           # V
    ac_current: float = 0.0           # A
    ac_power: float = 0.0             # W
    ac_frequency: float = 0.0         # Hz

    # Three-Phase AC Output (individual phases)
    ac_voltage_r: float = 0.0         # V (Phase R/L1)
    ac_current_r: float = 0.0         # A (Phase R/L1)
    ac_power_r: float = 0.0           # W (Phase R/L1)
    ac_voltage_s: float = 0.0         # V (Phase S/L2)
    ac_current_s: float = 0.0         # A (Phase S/L2)
    ac_power_s: float = 0.0           # W (Phase S/L2)
    ac_voltage_t: float = 0.0         # V (Phase T/L3)
    ac_current_t: float = 0.0         # A (Phase T/L3)
    ac_power_t: float = 0.0           # W (Phase T/L3)

    # Line-to-Line Voltages (3-phase only)
    ac_voltage_rs: float = 0.0        # V
    ac_voltage_st: float = 0.0        # V
    ac_voltage_tr: float = 0.0        # V
    
    # Power Flow (storage/hybrid models)
    power_to_user: float = 0.0        # W
    power_to_grid: float = 0.0        # W (export)
    power_to_load: float = 0.0        # W
    # SPH-HU US split-phase CT / local-load legs (#418). R maps to L1, S maps to L2.
    ct_grid_import_l1: float = 0.0    # W
    ct_grid_import_l2: float = 0.0    # W
    ct_grid_export_l1: float = 0.0    # W
    ct_grid_export_l2: float = 0.0    # W
    inverter_to_load_l1: float = 0.0  # W
    inverter_to_load_l2: float = 0.0  # W
    system_output_power: float = 0.0  # W (total system output per inverter)
    
    # Energy & Status
    energy_today: float = 0.0         # kWh
    energy_total: float = 0.0         # kWh
    energy_to_user_today: float = 0.0 # kWh
    energy_to_user_total: float = 0.0 # kWh
    energy_to_grid_today: float = 0.0 # kWh
    energy_to_grid_total: float = 0.0 # kWh
    load_energy_today: float = 0.0    # kWh
    load_energy_total: float = 0.0    # kWh

    # SPF Off-Grid AC Input (from grid/generator)
    grid_voltage: float = 0.0         # V (AC input voltage)
    grid_frequency: float = 0.0       # Hz (AC input frequency)
    ac_input_power: float = 0.0       # W (AC input power)
    ac_apparent_power: float = 0.0    # VA (AC apparent power)
    load_percentage: float = 0.0      # % (Load percentage)

    # SPF Generator Sensors
    generator_power: float = 0.0      # W
    generator_voltage: float = 0.0    # V
    generator_discharge_today: float = 0.0  # kWh
    generator_discharge_total: float = 0.0  # kWh

    # SPF/WIT AC Charge/Discharge Energy (from grid/generator)
    ac_charge_energy_today: float = 0.0     # kWh
    ac_charge_energy_total: float = 0.0     # kWh (WIT/SPF)
    ac_discharge_energy_today: float = 0.0  # kWh
    ac_discharge_energy_total: float = 0.0  # kWh

    # SPF Operational Discharge Energy
    op_discharge_energy_today: float = 0.0  # kWh
    op_discharge_energy_total: float = 0.0  # kWh

    # WIT Extra/Parallel Inverter Sensors (multi-inverter systems)
    extra_power_to_grid: float = 0.0  # W
    extra_energy_today: float = 0.0   # kWh
    extra_energy_total: float = 0.0   # kWh

    # Backup Box (Growatt ARK transfer switch, RS485 via TL-X/TL-XH inverter, input regs 3281-3342)
    box_connect_flag: int = 0          # 0=Abnormal/absent, 1=Normal/connected (reg 3320)
    box_bypass_status: int = 0         # 0=Off, 1=On (reg 3281)
    box_work_mode: int = 0             # 0=Offgrid, 1=Ongrid, 2=Generator (reg 3282)
    box_error_code: int = 0            # Error code 700-800 range (reg 3284)
    box_warning_code: int = 0          # Warning code 700-800 range (reg 3285)
    box_temperature: float = 0.0       # °C, scale 1, signed Int8 (reg 3286)
    box_grid_voltage: float = 0.0      # V, scale 0.1 (reg 3287)
    box_grid_power: float = 0.0        # W, scale 0.1, signed Int32 (regs 3289-3290)
    box_load_power: float = 0.0        # W, scale 0.1, Uint32 (regs 3297-3298)
    box_relay_status: int = 0          # 0=Not supported/comm error, 1=Open, 2=Close (reg 3342)

    # Temperatures
    inverter_temp: float = 0.0        # °C
    ipm_temp: float = 0.0             # °C
    boost_temp: float = 0.0           # °C
    dcdc_temp: float = 0.0            # °C (SPF off-grid)
    buck1_temp: float = 0.0           # °C (SPF off-grid MPPT1)
    buck2_temp: float = 0.0           # °C (SPF off-grid MPPT2)

    # Fan Speeds (SPF off-grid)
    mppt_fan_speed: float = 0.0       # %
    inverter_fan_speed: float = 0.0   # %

    # Battery (storage/hybrid models)
    battery_voltage: float = 0.0      # V
    battery_current: float = 0.0      # A (signed: +discharge, -charge)
    battery_soc: float = 0.0          # %
    battery_temp: float = 0.0         # °C
    # battery_soh and battery_voltage_bms are NOT in the dataclass — they are added
    # dynamically via setattr() only when the register is present in the active profile.
    # This makes hasattr(data, 'battery_soh') a reliable profile gate.
    # NOTE: all other fields above have float defaults, so hasattr() on them is always True.
    # Sensor conditions that use hasattr() on dataclass fields are effectively dead code;
    # the sensor group system (device_profiles.py) is the actual profile gate.
    # Phase 4 plan: change profile-specific fields to Optional[float] = None and update
    # conditions to `is not None` to restore meaningful hasattr-style gating.
    charge_power: float = 0.0         # W
    discharge_power: float = 0.0      # W
    charge_energy_today: float = 0.0  # kWh
    discharge_energy_today: float = 0.0  # kWh
    charge_energy_total: float = 0.0  # kWh
    discharge_energy_total: float = 0.0  # kWh
        
    # Diagnostics
    status: int = 0                   # Inverter status
    equipment_status: int = 0         # VPP hybrid equipment status (reg 31000); see equipment_status_valid
    equipment_status_valid: bool = False  # True when reg 31000 was read from the active profile
    derating_mode: int = 0
    fault_code: int = 0
    warning_code: int = 0
    pv_iso: float = 0.0          # kΩ — PV insulation resistance (reg 3087)
    dci_r: float = 0.0           # mA — DC injection R-phase (reg 3088)
    dci_s: float = 0.0           # mA — DC injection S-phase (reg 3089, 3-phase only)
    dci_t: float = 0.0           # mA — DC injection T-phase (reg 3090, 3-phase only)
    gfci: float = 0.0            # mA — residual/leakage current (reg 3091)
    # Safety/compliance diagnostic registers 235-238 (read-only, Issue #282)
    ntognd_detect: int = 0           # reg 235 — NToGND grounding protection detection
    nonstd_vac_enable: int = 0       # reg 236 — non-standard VAC enable
    enable_spec_set: int = 0         # reg 237 — appointed spec / grid-code setting
    fast_mppt_enable: int = 0        # reg 238 — fast MPPT algorithm enable

    # Control registers (writable holding registers)
    export_limit_mode: int = 0        # 0=Disabled, 1=RS485, 2=RS232, 3=CT
    export_limit_power: int = 0       # 0-1000 (0-100.0%)
    export_limit_failed_power_rate: int = 0       # 0-1000 raw (×0.1 = 0-100%); fallback output power cap when export limit fails
    active_power_rate: int = 100      # 0-100 (max output power %)
    export_limit_w: int = 0           # WIT holding reg 203: export limit in watts (0=zero export)

    # SPH/SPM Battery Control registers (1000+ range)
    priority_mode: int = 0            # 0=Load First, 1=Battery First, 2=Grid First
    load_first_battery_minimum_soc: int = 10  # 10-100 (min SOC % in Load First mode, register 608)
    discharge_power_rate: int = 0     # 0-100 (battery discharge power %)
    discharge_stopped_soc: int = 0    # 0-100 (stop discharge at SOC %)
    charge_power_rate: int = 0        # 0-100 (battery charge power %)
    charge_stopped_soc: int = 0       # 0-100 (stop charge at SOC %)
    ac_charge_enable: int = 0         # 0=Disabled, 1=Enabled

    # WIT VPP Remote Control (30000+ range)
    control_authority: int = 0        # 0=Disabled, 1=Enabled (VPP master enable)
    remote_power_control_enable: int = 0  # 0=Disabled, 1=Enabled (timed override enable)
    remote_power_control_charging_time: int = 0  # 0-1440 minutes (duration)
    remote_charge_and_discharge_power: int = 0   # -100 to +100% (negative=discharge, positive=charge)
    vpp_ac_charge_enable: int = 0                # 0=off, 1=PV priority, 2=AC priority
    vpp_export_limit_enable: int = 0          # 0=Disabled, 1=Enabled
    vpp_export_limit_power_rate: int = 0      # -100 to +100% (positive=export, 0=zero export)
    vpp_export_limit_available: bool = False  # True if inverter actually responded to registers 30200-30201
    vpp_control_authority_available: bool = False  # True if inverter actually responded to register 30100

    # MOD TL3-XH TOU periods (FC04 holding registers 3038-3045, raw packed values)
    # Start reg: bit15=enable, bit13-14=priority(0=Load,1=Batt,2=Grid), bit8-12=hour, bit0-7=min
    # End reg: bit8-12=hour, bit0-7=min (hex-packed, same as SPH time periods)
    mod_tou_1_start: int = 0
    mod_tou_1_end:   int = 0
    mod_tou_2_start: int = 0
    mod_tou_2_end:   int = 0
    mod_tou_3_start: int = 0
    mod_tou_3_end:   int = 0
    mod_tou_4_start: int = 0
    mod_tou_4_end:   int = 0
    # MOD GEN4 TOU slots 5-9 (registers 3050-3059; gap at 3046-3049 is EMS/grid-charge controls)
    mod_tou_5_start: int = 0
    mod_tou_5_end:   int = 0
    mod_tou_6_start: int = 0
    mod_tou_6_end:   int = 0
    mod_tou_7_start: int = 0
    mod_tou_7_end:   int = 0
    mod_tou_8_start: int = 0
    mod_tou_8_end:   int = 0
    mod_tou_9_start: int = 0
    mod_tou_9_end:   int = 0
    # MOD GEN4 prerequisite gate for TOU persistence (register 3049)
    allow_grid_charge: int = 0
    # MOD GEN4 power rate limits per priority mode
    grid_first_discharge_power_rate: int = 0  # 0-100% discharge rate when Grid First (register 3036)
    batt_first_charge_power_rate: int = 0      # 0-100% charge rate when Battery First (register 3047)
    tl_xh_priority_mode: int = 3               # MIN TL-XH priority mode: 0=Load First, 2=Battery First, 3=Grid First (register 3018)
    batt_first_charge_stopped_soc: int = 0     # SOC % to stop charging in Battery First mode (register 3048)
    grid_first_discharge_stopped_soc: int = 0  # SOC % to stop discharging in Grid First mode (register 3067)

    # MOD TL3-XH peak shaving / demand management (holding 3307-3312, #372).
    # Undocumented in any public protocol; mapped from portal round-trips. See mod.py.
    # None rather than 0.0 so an unset limit publishes nothing instead of a plausible
    # number. These sit at a ceiling (30000 / 65535) when peak shaving was never
    # configured, and the read succeeds, so 0.0 would be indistinguishable from a real
    # reading of zero. See PEAK_SHAVING_UNSET_RAW (#380).
    demand_import_limit: Optional[float] = None   # kW  (3307, x0.1)
    demand_export_limit: Optional[float] = None   # kW  (3308, x0.1)
    peak_shaving_reserve_soc: int = 0             # %   (3310) — unset not detectable
    ac_charge_max_power: Optional[float] = None   # kW  (3311, x0.1)
    grid_charge_stopped_soc: int = 0       # %   (3312) — grid-charge cap, distinct from 3048

    # Mirror of the last commanded VPP power setpoint (holding 30474, #373). Write-ignored.
    vpp_last_setpoint: int = 0             # % (-100..+100)

    # Dry Contact (SPH/MIN TL-X/TL-XH — V1.39 registers 3016/3017/3019/3119)
    dry_contact_state: int = 0       # input reg 3119: current relay state (0=Off, 1=On)
    dry_contact_enable: int = 0      # holding reg 3016: function enable (0=Disabled, 1=Enabled)
    dry_contact_on_rate: int = 0     # holding reg 3017: close relay power threshold (raw ×0.1%)
    dry_contact_off_rate: int = 0    # holding reg 3019: open relay power threshold (raw ×0.1%)

    time_period_1_enable: int = 0     # 0=Disabled, 1=Enabled
    time_period_1_start: int = 0      # hex-packed (hours*256+minutes, e.g. 06:00 = 0x0600 = 1536)
    time_period_1_end: int = 0        # hex-packed
    time_period_2_enable: int = 0     # 0=Disabled, 1=Enabled
    time_period_2_start: int = 0      # hex-packed
    time_period_2_end: int = 0        # hex-packed
    time_period_3_enable: int = 0     # 0=Disabled, 1=Enabled
    time_period_3_start: int = 0      # hex-packed
    time_period_3_end: int = 0        # hex-packed
    # SPH GEN3 Battery First extended slots 4-6 (registers 1017-1025)
    batt_first_time_period_4_start: int = 0
    batt_first_time_period_4_end:   int = 0
    batt_first_time_period_4_enable: int = 0
    batt_first_time_period_5_start: int = 0
    batt_first_time_period_5_end:   int = 0
    batt_first_time_period_5_enable: int = 0
    batt_first_time_period_6_start: int = 0
    batt_first_time_period_6_end:   int = 0
    batt_first_time_period_6_enable: int = 0
    # SPH GEN3 Grid First extended slots 4-6 (registers 1026-1034)
    grid_first_time_period_4_start: int = 0
    grid_first_time_period_4_end:   int = 0
    grid_first_time_period_4_enable: int = 0
    grid_first_time_period_5_start: int = 0
    grid_first_time_period_5_end:   int = 0
    grid_first_time_period_5_enable: int = 0
    grid_first_time_period_6_start: int = 0
    grid_first_time_period_6_end:   int = 0
    grid_first_time_period_6_enable: int = 0
    # SPH GEN3 Grid First extended slots 7-9 (registers 1080-1088)
    grid_first_time_period_7_start: int = 0
    grid_first_time_period_7_end:   int = 0
    grid_first_time_period_7_enable: int = 0
    grid_first_time_period_8_start: int = 0
    grid_first_time_period_8_end:   int = 0
    grid_first_time_period_8_enable: int = 0
    grid_first_time_period_9_start: int = 0
    grid_first_time_period_9_end:   int = 0
    grid_first_time_period_9_enable: int = 0

    # SPF Off-Grid Control registers
    output_config: int = 0            # 0=SBU, 1=SOL, 2=UTI, 3=SUB
    charge_config: int = 0            # 0=CSO, 1=SNU, 2=OSO
    ac_input_mode: int = 0            # 0=APL, 1=UPS, 2=GEN
    battery_type: int = 0             # 0=AGM, 1=FLD, 2=USE, 3=Lithium, 4=USE2
    max_charge_current: int = 0       # A, total solar + utility (holding 34, LCD Program 02)
    bulk_charge_voltage: int = 0      # raw, x0.1 V (holding 35, LCD Program 19)
    float_charge_voltage: int = 0     # raw, x0.1 V (holding 36, LCD Program 20)
    ac_charge_current: int = 0        # 0-800 (0-80A with scale 0.1)
    gen_charge_current: int = 0       # 0-800 (0-80A with scale 0.1)
    bat_low_to_uti: int = 0           # Battery-dependent: Non-Lithium 200-640 (20-64V), Lithium 5-100 (0.5-10%)
    ac_to_bat_volt: int = 0           # Battery-dependent: Non-Lithium 200-640 (20-64V), Lithium 5-100 (0.5-10%)

    # Device Info
    firmware_version: str = ""
    serial_number: str = ""

class SharedModbusConnection:
    """One Modbus client shared across every GrowattModbus instance on the same transport.

    For TCP that means the same host:port; for serial, the same device path.

    Serializes all Modbus transactions with a threading.Lock (because _fetch_data runs in
    executor threads, not on the asyncio event loop).  Reference-counted so the connection
    stays open as long as at least one coordinator needs it.

    **Serial was excluded from this until v1.7.0**, which was backwards. The hub's stated
    purpose is preventing RS485 cross-talk, and an RS485 bus is exactly where two
    uncoordinated masters collide: each config entry opened its own ModbusSerialClient on
    the same adapter and paced itself with a per-instance `min_read_interval`, which says
    nothing about what the other entry is doing. Two inverters on one USB-RS485 adapter —
    the normal way to wire a parallel SPF stack — interleaved their frames on one physical
    bus with nothing serializing them.
    """

    def __init__(
        self,
        host: str = "",
        port: int = 502,
        timeout: int = 10,
        device: str = "",
        baudrate: int = 9600,
        parity: str = "N",
        stopbits: int = 1,
        bytesize: int = 8,
    ) -> None:
        self.host = host
        self.port = port
        self.device = device
        self.baudrate = baudrate
        self.parity = parity
        self.stopbits = stopbits
        self.bytesize = bytesize
        self._timeout = timeout
        self._client: Optional[Union['ModbusTcpClient', 'ModbusSerialClient']] = None
        # Reentrant so a caller can hold the bus across a sequence of writes while the
        # individual write methods still take it themselves (#331). A plain Lock would
        # deadlock the moment write_batch() wrapped anything. Reentrancy is per-thread,
        # which is why the batched sequence has to run in ONE executor job — see
        # GrowattModbus.write_batch().
        self._lock = threading.RLock()
        self._refcount = 0
        self._connected = False
        # Per-poll budget for transport-error recoveries (Issue #364). A block-level
        # reset+retry (see read_input_registers/read_holding_registers) is cheap for the
        # one-off silent connection loss it's meant to catch, but on a gateway that is
        # genuinely down every block would trip it, turning one poll into a chain of full
        # TCP reconnects. begin_poll() resets the budget once per poll cycle.
        self._recoveries_this_poll = 0
        self._max_recoveries_per_poll = 2

        # Lifetime tallies of frames this gateway answered correctly vs. answered with
        # something that was not a reply to the question asked. Read by the coordinator to
        # decide whether to raise a repair issue — a gateway can sit at a double-digit
        # failure rate indefinitely and the only visible sign is log lines nobody reads.
        self.good_reads = 0
        self.malformed_reads = 0

    @property
    def is_serial(self) -> bool:
        return bool(self.device)

    @property
    def connection_id(self) -> str:
        """Identifier used in log lines — the device path, or host:port."""
        return self.device if self.is_serial else f"{self.host}:{self.port}"

    # ------------------------------------------------------------------
    # Reference counting
    # ------------------------------------------------------------------

    def acquire_ref(self) -> None:
        self._refcount += 1

    def begin_poll(self) -> None:
        """Reset the per-poll recovery budget. Call once per poll, before any reads."""
        self._recoveries_this_poll = 0

    def end_poll(self) -> None:
        """Give an exclusive serial port back between polls.

        A TCP socket is cheap to hold and reconnecting costs a round trip, so TCP keeps its
        connection open across polls. A serial port is different: it is **exclusive**, and
        holding it denies it to every other process on the machine — including a second
        config entry that names the same adapter by a different path.

        Before v1.7.0 the port was opened and closed per poll, so two such entries alternated
        and mostly worked, with occasional collisions. Holding it open turned that into a
        permanent lockout for whichever entry lost the race, with pyserial reporting
        "Could not exclusively lock port" on every poll thereafter (#384).

        Reopening a serial port costs about 2 ms, which is nothing next to a poll that reads
        98 registers. The lock still serializes entries that do share a hub.
        """
        if not self.is_serial:
            return
        with self._lock:
            self.disconnect()
            self._client = None

    def _begin_recovery(self) -> bool:
        """True if a reset+retry is still within this poll's recovery budget."""
        if self._recoveries_this_poll >= self._max_recoveries_per_poll:
            return False
        self._recoveries_this_poll += 1
        return True

    def release_ref(self) -> None:
        self._refcount -= 1
        if self._refcount <= 0:
            self.disconnect()
            self._client = None

    # ------------------------------------------------------------------
    # Connection lifecycle (call only while lock is held)
    # ------------------------------------------------------------------

    def ensure_connected(self) -> bool:
        """Connect if not already open; flush stale bytes on a new connection."""
        if self._client is None:
            if self.is_serial:
                if not SERIAL_AVAILABLE:
                    logger.error(
                        "[SharedConn %s] pyserial/pymodbus serial support is not installed",
                        self.connection_id,
                    )
                    return False
                # NB: the runtime name is ModbusClient — ModbusSerialClient is imported only
                # under TYPE_CHECKING and does not exist when this executes.
                self._client = ModbusClient(
                    port=self.device,
                    baudrate=self.baudrate,
                    parity=self.parity,
                    stopbits=self.stopbits,
                    bytesize=self.bytesize,
                    timeout=self._timeout,
                )
            else:
                try:
                    self._client = ModbusTcpClient(host=self.host, port=self.port, timeout=self._timeout)
                except TypeError:
                    self._client = ModbusTcpClient(self.host, self.port)
                    if hasattr(self._client, 'timeout'):
                        self._client.timeout = self._timeout

        try:
            if hasattr(self._client, 'is_socket_open') and self._client.is_socket_open():
                return True
        except Exception:
            pass

        result = self._client.connect()
        if result:
            self._connected = True
            self._flush_receive_buffer()
        elif self.is_serial:
            # pyserial logs "[Errno 11] Could not exclusively lock port ..." and pymodbus
            # turns it into a bare "Failed to connect", which tells the user nothing about
            # the one cause that actually matters: somebody else already has this port.
            #
            # The usual somebody else is a second config entry naming the same adapter by a
            # different path. That is easy to do by accident with cheap CH340 adapters
            # (USB vendor 1a86), which ship without a serial number — so two of them produce
            # by-id names that do not distinguish them, and the /dev/ttyUSBn numbering swaps
            # on reboot. by-path is stable per physical socket and is the right choice there.
            logger.warning(
                "[SharedConn %s] Could not open the serial port. If the log above shows "
                "'Could not exclusively lock port', another process or another Growatt "
                "config entry already has it open. Check whether two entries point at the "
                "same adapter under different names (/dev/ttyUSBn vs /dev/serial/by-id/... "
                "vs /dev/serial/by-path/...) — run: ls -l /dev/serial/by-id/ "
                "/dev/serial/by-path/",
                self.connection_id,
            )
        return result

    def disconnect(self) -> None:
        if self._client is not None:
            try:
                self._client.close()
            except Exception:
                pass
            self._connected = False

    def reset(self, reason: str = "") -> None:
        """Force-close the socket so the next ensure_connected() does a real reconnect.

        pymodbus sync clients never clear their socket after a silent connection loss
        (receive timeouts don't trigger close(), and connection_lost() is a no-op for
        sync clients), so is_socket_open() keeps returning True and ensure_connected()
        would reuse the dead socket forever. Without this, only an HA restart recovers
        a wedged connection.
        """
        logger.warning(
            "[SharedConn %s] Resetting connection%s",
            self.connection_id, f": {reason}" if reason else "",
        )
        self.disconnect()

    def _flush_receive_buffer(self) -> None:
        """Drain stale Modbus responses left in the adapter's buffer after reconnect."""
        if self.is_serial:
            # pyserial exposes its own drain; the socket recv() path below does not apply
            # and would raise on a Serial object.
            serial_port = getattr(self._client, 'socket', None)
            if serial_port is None:
                return
            try:
                waiting = getattr(serial_port, 'in_waiting', 0)
                serial_port.reset_input_buffer()
                if waiting:
                    logger.debug(
                        "[SharedConn %s] Flushed %d stale bytes from serial input buffer",
                        self.connection_id, waiting,
                    )
            except Exception as exc:
                logger.debug(
                    "[SharedConn %s] Serial buffer flush failed (non-critical): %s",
                    self.connection_id, exc,
                )
            return

        sock = getattr(self._client, 'socket', None)
        if sock is None:
            transport = getattr(self._client, 'transport', None)
            if transport is not None:
                sock = getattr(transport, 'socket', None) or getattr(transport, '_sock', None)
        if sock is None:
            return
        try:
            original_timeout = sock.gettimeout()
            sock.settimeout(0)
            discarded = 0
            try:
                while True:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    discarded += len(chunk)
            except (BlockingIOError, OSError):
                pass
            finally:
                sock.settimeout(original_timeout)
            if discarded:
                logger.debug(
                    "[SharedConn %s] Flushed %d stale bytes from receive buffer after reconnect",
                    self.connection_id, discarded,
                )
        except Exception as exc:
            logger.debug("[SharedConn %s] Buffer flush failed (non-critical): %s", self.connection_id, exc)

    # ------------------------------------------------------------------
    # Register access (slave_id passed per call, not stored on hub)
    # ------------------------------------------------------------------

    def _validate_registers(self, resp, start: int, count: int) -> Optional[list]:
        """Return the response's registers, or None if the frame cannot be trusted.

        Callers write results into the register cache *positionally* — regs[0] is assumed
        to be `start`, regs[1] to be `start + 1`, and so on across 11 call sites. So a
        response whose length doesn't match the request is not a partial success to
        salvage: every word in it lands on an address it does not belong to. That is how
        string registers (a serial number, a firmware version string) ended up decoded and
        published as instantaneous power — 0x33325354 is "32ST", four characters of the
        reporter's serial number, shown as 85,893,614.8 W (#367).

        The non-shared path has guarded this since v1.3.5, but every TCP entry goes through
        the shared hub (a hub is created even for a single entry), so in practice the guard
        only ever protected serial/RTU users — the ones least exposed to gateway framing
        problems in the first place.

        Length is compared with != rather than <: a response *longer* than requested is an
        equally strong sign of a misaligned or stale frame, and costs nothing to catch.
        """
        if hasattr(resp, 'isError') and callable(resp.isError) and resp.isError():
            return None

        registers = resp.registers if hasattr(resp, 'registers') else None
        if registers is None:
            return None

        if len(registers) != count:
            logger.warning(
                "[SharedConn %s] Short/misaligned read at %d: got %d of %d registers — "
                "discarding frame and flushing buffer",
                self.connection_id, start, len(registers), count,
            )
            # A misaligned stream stays misaligned — which is why the corrupt values
            # repeat byte-for-byte rather than varying. Draining the buffer here gives the
            # next read a clean start instead of inheriting the same offset.
            self._flush_receive_buffer()
            # Counted so the coordinator can surface a repair issue. Field reports put
            # this at roughly one poll in three on an affected gateway, and the only way
            # anyone noticed was by reading the log (#367).
            self.malformed_reads += 1
            return None

        self.good_reads += 1
        return registers

    def read_input_registers(self, start: int, count: int, slave_id: int) -> Optional[list]:
        if self._client is None:
            return None
        # Issue #364: a block read can fail two structurally different ways.
        #
        # - Transport failure (raised exception: socket dropped, frame corruption). The
        #   connection is suspect and pymodbus's sync client won't notice on its own
        #   (see reset()'s docstring) — reset and retry once, budget permitting.
        # - Protocol refusal (isError(), e.g. Illegal Function/Address). The device
        #   answered and declined. The socket is healthy; several profiles legitimately
        #   probe ranges their hardware rejects on every poll (#360, #361), so resetting
        #   here would be a permanent tax rather than a recovery.
        for attempt in (0, 1):
            try:
                try:
                    resp = self._client.read_input_registers(address=start, count=count, device_id=slave_id)
                except TypeError:
                    try:
                        resp = self._client.read_input_registers(address=start, count=count, slave=slave_id)
                    except TypeError:
                        try:
                            resp = self._client.read_input_registers(address=start, count=count, unit=slave_id)
                        except TypeError:
                            resp = self._client.read_input_registers(start, count)
            except Exception as exc:
                if attempt == 0 and self._begin_recovery():
                    logger.debug(
                        "[SharedConn %s] read_input_registers(%d, %d) transport error "
                        "(%s) — resetting and retrying once",
                        self.connection_id, start, count, exc,
                    )
                    self.reset("transport error during block read")
                    if self.ensure_connected():
                        continue
                logger.debug("[SharedConn %s] read_input_registers(%d, %d, slave=%d) error: %s",
                             self.connection_id, start, count, slave_id, exc)
                return None

            return self._validate_registers(resp, start, count)
        return None

    def read_holding_registers(self, start: int, count: int, slave_id: int) -> Optional[list]:
        if self._client is None:
            return None
        # Same transport-vs-protocol distinction as read_input_registers() above.
        for attempt in (0, 1):
            try:
                try:
                    resp = self._client.read_holding_registers(address=start, count=count, slave=slave_id)
                except TypeError:
                    try:
                        resp = self._client.read_holding_registers(address=start, count=count, unit=slave_id)
                    except TypeError:
                        resp = self._client.read_holding_registers(address=start, count=count)
            except Exception as exc:
                if attempt == 0 and self._begin_recovery():
                    logger.debug(
                        "[SharedConn %s] read_holding_registers(%d, %d) transport error "
                        "(%s) — resetting and retrying once",
                        self.connection_id, start, count, exc,
                    )
                    self.reset("transport error during block read")
                    if self.ensure_connected():
                        continue
                logger.debug("[SharedConn %s] read_holding_registers(%d, %d, slave=%d) error: %s",
                             self.connection_id, start, count, slave_id, exc)
                return None

            return self._validate_registers(resp, start, count)
        return None

    # Writes reset and retry once on a transport error, exactly as the reads above do
    # (#375). They did not until then: they dropped the socket and returned False, with a
    # comment saying the *next* call would reconnect — so on a gateway or datalogger that
    # reaps idle sockets, the first read after a drop recovered silently and the first
    # write after a drop failed. The user saw a control that did not take effect and an
    # ERROR in the log; whether anything retried depended on having an external controller
    # that did so. Found by @alanmk while field-testing #358.
    #
    # Retrying a write is safe in this integration because every write is idempotent —
    # each sets a register to an absolute value, none increments or toggles relative to
    # the current one. Replaying one whose transport attempt failed cannot compound, and
    # the failure it prevents (a silently ineffective control) is worse than the one it
    # risks (writing the same value twice).
    #
    # Only transport-level exceptions retry. A register-level refusal arrives as an
    # isError() response, not an exception, and still fails immediately — retrying an
    # illegal-address write achieves nothing and doubles the log volume on the registers
    # known to reject writes (#371).

    def write_register(self, register: int, value: int, slave_id: int) -> bool:
        if self._client is None:
            return False
        if value < 0:
            value = value & 0xFFFF
        for attempt in (0, 1):
            try:
                try:
                    result = self._client.write_register(address=register, value=value, unit=slave_id)
                except TypeError:
                    try:
                        result = self._client.write_register(address=register, value=value, slave=slave_id)
                    except TypeError:
                        try:
                            result = self._client.write_register(address=register, value=value, device_id=slave_id)
                        except TypeError:
                            result = self._client.write_register(register, value)
            except Exception as exc:
                if attempt == 0 and self._begin_recovery():
                    logger.debug(
                        "[SharedConn %s] write_register(%d, %d) transport error (%s) — "
                        "resetting and retrying once",
                        self.connection_id, register, value, exc,
                    )
                    self.reset("transport error during write")
                    if self.ensure_connected():
                        continue
                logger.debug("[SharedConn %s] write_register(%d, %d, slave=%d) error: %s",
                             self.connection_id, register, value, slave_id, exc)
                self.disconnect()
                return False

            if hasattr(result, 'isError') and callable(result.isError) and result.isError():
                # Same reasoning as write_registers above: keep the device's own reason.
                logger.warning(
                    "[SharedConn %s] write_register(%d, %d) refused by the device: %s",
                    self.connection_id, register, value, result,
                )
                return False
            return True
        return False

    def write_registers(self, register: int, values: list, slave_id: int) -> bool:
        if self._client is None:
            return False
        for attempt in (0, 1):
            try:
                try:
                    result = self._client.write_registers(address=register, values=values, slave=slave_id)
                except TypeError:
                    try:
                        result = self._client.write_registers(address=register, values=values, unit=slave_id)
                    except TypeError:
                        result = self._client.write_registers(register, values)
            except Exception as exc:
                if attempt == 0 and self._begin_recovery():
                    logger.debug(
                        "[SharedConn %s] write_registers(%d, %d values) transport error "
                        "(%s) — resetting and retrying once",
                        self.connection_id, register, len(values), exc,
                    )
                    self.reset("transport error during write")
                    if self.ensure_connected():
                        continue
                logger.debug("[SharedConn %s] write_registers(%d, slave=%d) error: %s",
                             self.connection_id, register, slave_id, exc)
                self.disconnect()
                return False

            if hasattr(result, 'isError') and callable(result.isError) and result.isError():
                # Surface the device's own reason. Reducing this to False threw away the
                # only thing that distinguishes "this register does not exist" (Illegal
                # Data Address) from "this value is not acceptable" (Slave Device Failure),
                # and the caller could then only report "returned error" — which is what a
                # clock write failure looked like from the outside (#393).
                logger.warning(
                    "[SharedConn %s] write_registers(%d, %d values) refused by the device: %s",
                    self.connection_id, register, len(values), result,
                )
                return False
            return True
        return False


class GrowattModbus:
    """Growatt MIN series Modbus client"""
    
    def __init__(self, connection_type='tcp', host='192.168.1.100', port=502,
             device='/dev/ttyUSB0', baudrate=9600, slave_id=1,
             register_map='MIN_7000_10000TL_X', timeout=10, invert_battery_power=False,
             shared_conn: Optional['SharedModbusConnection'] = None):
        """
        Initialize Modbus connection

        Args:
            connection_type: 'tcp' for RS485-to-TCP converter, 'serial' for RS485-to-USB
            host: IP address for TCP connection
            port: Port for TCP connection
            device: Serial device path for USB connection
            baudrate: Serial baud rate (usually 9600)
            slave_id: Modbus slave ID (usually 1)
            register_map: Which register mapping to use (see const.py)
            timeout: Connection timeout in seconds (default: 10)
            invert_battery_power: Invert battery power sign for inverters with opposite convention (default: False)
            shared_conn: Optional shared connection hub (TCP only). When set, all socket
                operations are delegated to the hub and connect/disconnect become no-ops.
        """
        self._shared_conn = shared_conn

        # Serialises bus access when there is no shared hub - which is every serial entry,
        # since the hub is TCP-only. Without it a coordinator poll and a service-call write
        # could use the same client concurrently; when one path hit a transport timeout and
        # reconnected, the other was left holding a closed file descriptor and the write
        # died with [Errno 9] Bad file descriptor, roughly ten times a day for one reporter
        # (#398).
        #
        # Reentrant for the same reason the hub's lock is: write_batch() holds it across a
        # sequence while the individual writes still take it themselves. Reentrancy is
        # per-thread, so a batched sequence must run in one executor job.
        #
        # This is NOT the serial shared connection that was reverted in v1.7.5. Nothing
        # here opens the port - the client still owns its own socket. It only stops two
        # callers using that socket at once.
        self._local_bus_lock = threading.RLock()

        # Battery temperature scale detection (#397). Latched per connection so the
        # decision cannot flap between polls as the temperature moves.
        # Registers already warned about for 32-bit underflow, so a persistent case is
        # reported once rather than every poll (#401).
        self._underflow_warned: set = set()

        # Impossible-PV-zero suppressions this session. Warned once, then debug (#384).
        self._impossible_pv_zero_count: int = 0

        # Whether the battery current candidates agreed on the last poll, and whether we
        # have already said so. Gates the battery power scale detection (#406).
        self._battery_current_candidates_agree: bool = True
        self._battery_power_scale_input_warned: bool = False

        self._battery_temp_scale_confirmed = False
        self._battery_temp_whole_degrees = False

        self.connection_type = connection_type
        self.slave_id = slave_id
        self.client: Optional[Union['ModbusTcpClient', 'ModbusSerialClient']] = None
        self.last_read_time = 0
        self.min_read_interval = 0.25  # 250ms minimum between reads (reduced from 1s, safe for serial and TCP)
        self._timeout = timeout
        self._invert_battery_power = invert_battery_power
        self._battery_voltage_range = "Auto-detect"  # updated by coordinator from config_entry.options

        # Store connection details for logging
        self.host = host
        self.port = port
        self.device = device

        # Load register map
        if register_map not in REGISTER_MAPS:
            raise ValueError(f"Unknown register map: {register_map}. Available: {list(REGISTER_MAPS.keys())}")

        self.register_map = REGISTER_MAPS[register_map]
        self.register_map_name = register_map

        # Build connection identifier for logs
        if connection_type == 'tcp':
            self.connection_id = f"{host}:{port}"
        else:
            self.connection_id = f"{device}"

        logger.info(f"Initializing {self.register_map['name']} profile for {self.connection_id}")

        # Cache for raw register data
        self._register_cache = {}

        # Track failed optional register ranges with timestamps for retry.
        # Format: dict mapping (start_addr, count) → (first_fail_time, fail_count)
        # Entries expire after _OPTIONAL_RANGE_RETRY_SECONDS and are retried.
        self._failed_optional_ranges: dict = {}

        # Anchor address -> timestamp of its last failure, for the optional VPP holding
        # blocks (30100, 30200, 30407). Skipped while inside the retry window, then tried
        # again — see the read path for why this is a dict rather than the set it was
        # until #370, and what a permanent skip cost the user who found it.
        self._failed_optional_holding_addrs: dict = {}

        # Last successfully read battery SOC — used to hold value if VPP range is
        # temporarily unavailable rather than reporting a misleading 0%.
        self._cached_battery_soc: Optional[float] = None

        # WIT control rate limiting (v0.4.6) - track last write time per register
        # Prevents oscillation and unstable control behavior
        self._wit_control_last_write = {}  # {register: timestamp}
        self._wit_control_rate_limit_seconds = 30  # 30 second cooldown
        # WIT control registers that require rate limiting
        self._wit_control_registers = {
            201,    # active_power_rate (Legacy VPP)
            202,    # work_mode (Legacy VPP)
            203,    # export_limit_w
            30100,  # control_authority (VPP master enable)
            30200,  # vpp_export_limit_enable
            30201,  # vpp_export_limit_power_rate
            30407,  # remote_power_control_enable
            30408,  # remote_power_control_charging_time
            30409,  # remote_charge_and_discharge_power
        }

        # Adaptive polling: automatic backoff on errors
        self._consecutive_read_failures = 0
        self._read_failure_threshold = 5  # Back off after 5 consecutive failures
        self._default_min_read_interval = 0.25  # Fast polling default
        self._fallback_min_read_interval = 1.0  # Safe fallback on errors
        self._backed_off = False  # Track if we've backed off

        # User override for the maximum registers per Modbus request (Issue #360).
        # None = use the profile's 'max_block_size', or dense 125-register reads if it has
        # none. Set from the "Max Register Block Size" option by the coordinator.
        #
        # This is a property of the RS485 link, not of the inverter model, so it does not
        # belong in the profile: at 9600 baud a 125-register response is ~265 ms of
        # continuous serial data, and gateways with a shorter serial response window forward
        # a truncated frame. The client then decodes garbage — "Unable to decode request"
        # and unit-ID mismatches — and stays desynced. The same inverter on a faster or
        # better-behaved gateway has no such limit.
        self._block_size_override: int | None = None

        # Battery power scale auto-detection (WIT profile specific)
        self._battery_power_scale_override = None  # None = use profile default, 0.1 or 1.0 = detected scale
        self._battery_power_scale_samples = []  # Store validation samples
        self._battery_power_scale_validated = False  # Set to True once detection is complete

        # Battery register range detection (VPP vs fallback)
        self._battery_register_range = None  # 'vpp' or 'fallback' - determined on first read
        self._battery_range_detected = False  # Set to True once detection is complete

        if connection_type == 'tcp':
            if not TCP_AVAILABLE:
                raise ImportError("pymodbus not available for TCP connection")
            
            # Handle different pymodbus versions for TCP client
            try:
                # New style (pymodbus 3.x+) - supports timeout parameter
                self.client = ModbusTcpClient(host=host, port=port, timeout=self._timeout)
            except TypeError:
                # Old style (pymodbus 2.x) - timeout must be set after creation
                self.client = ModbusTcpClient(host, port)
                # Set timeout on the client object if supported
                if hasattr(self.client, 'timeout'):
                    self.client.timeout = self._timeout
            
            logger.info(f"Connecting to Growatt via TCP: {host}:{port} (timeout: {self._timeout}s)")
            
        elif connection_type == 'serial':
            if not SERIAL_AVAILABLE:
                raise ImportError("pymodbus and/or pyserial not available for serial connection")
            
            # Handle different pymodbus versions
            try:
                # New style (pymodbus 3.x+)
                self.client = ModbusClient(
                    port=device,
                    baudrate=baudrate,
                    timeout=self._timeout,  # Use configured timeout, not hardcoded 3
                    parity='N',
                    stopbits=1,
                    bytesize=8
                )
            except TypeError:
                # Old style (pymodbus 2.x)
                self.client = ModbusClient(
                    method='rtu',
                    port=device,
                    baudrate=baudrate,
                    timeout=self._timeout,  # Use configured timeout
                    parity='N',
                    stopbits=1,
                    bytesize=8
                )
            logger.info(f"Connecting to Growatt via Serial: {device} @ {baudrate} baud (timeout: {self._timeout}s)")
        else:
            raise ValueError("connection_type must be 'tcp' or 'serial'")
    
    def connect(self) -> bool:
        """Establish connection to inverter"""
        if self._shared_conn is not None:
            # Connection is managed by the hub; _fetch_data calls hub.ensure_connected() directly.
            return True
        try:
            # Check if already connected (prevents double-open and file descriptor leaks)
            if hasattr(self.client, 'is_socket_open'):
                try:
                    if self.client.is_socket_open():
                        logger.debug(f"[{self.register_map['name']}@{self.connection_id}] Already connected")
                        return True
                except Exception as e:
                    logger.debug(f"[{self.register_map['name']}@{self.connection_id}] is_socket_open() check failed: {e}")
                    # Continue to connect attempt below

            result = self.client.connect()
            if result:
                logger.info(f"[{self.register_map['name']}@{self.connection_id}] Successfully connected")
                self._flush_receive_buffer()
            else:
                logger.error(f"[{self.register_map['name']}@{self.connection_id}] Failed to connect")
                if self.connection_type == 'serial':
                    # pyserial logs "[Errno 11] Could not exclusively lock port ..." and
                    # pymodbus reduces it to a bare "Failed to connect", which says nothing
                    # about the one cause that matters: somebody else already holds the port.
                    #
                    # Usually that is a second config entry naming the same adapter by a
                    # different path. Easy to do by accident with CH340 adapters (USB vendor
                    # 1a86), which ship without a serial number — two of them produce by-id
                    # names that cannot be told apart, and /dev/ttyUSBn numbering is assigned
                    # in enumeration order. by-path is stable per physical socket (#384).
                    logger.warning(
                        "[%s@%s] Could not open the serial port. If the line above reads "
                        "'Could not exclusively lock port', another process or another "
                        "Growatt config entry already has it open. Check whether two entries "
                        "point at the same adapter under different names (/dev/ttyUSBn vs "
                        "/dev/serial/by-id/... vs /dev/serial/by-path/...) — run: "
                        "ls -l /dev/serial/by-id/ /dev/serial/by-path/",
                        self.register_map['name'], self.connection_id,
                    )
            return result
        except Exception as e:
            logger.error(f"[{self.register_map['name']}@{self.connection_id}] Connection error: {e}")
            return False

    def _flush_receive_buffer(self) -> None:
        """Drain stale Modbus TCP responses from the adapter's receive buffer after reconnect.

        RS485-to-TCP adapters buffer late responses from a previous connection session.
        When pymodbus restarts with a fresh transaction counter (e.g. after an HA restart),
        the old high-ID responses sitting in the adapter's buffer cause repeated
        transaction ID mismatches on every read until the buffer is drained (Issue #317).

        This method reads and discards all pending bytes on the socket immediately after
        connect() succeeds, before the first real request is sent.
        """
        if self.connection_type != 'tcp':
            return

        # Locate the underlying socket — attribute name varies by pymodbus version
        sock = getattr(self.client, 'socket', None)
        if sock is None:
            # pymodbus 3.4+ wraps in a transport; try common attribute paths
            transport = getattr(self.client, 'transport', None)
            if transport is not None:
                sock = getattr(transport, 'socket', None) or getattr(transport, '_sock', None)

        if sock is None:
            logger.debug(
                "[%s@%s] _flush_receive_buffer: socket not accessible (pymodbus transport abstraction)",
                self.register_map['name'], self.connection_id
            )
            return

        try:
            original_timeout = sock.gettimeout()
            sock.settimeout(0)  # non-blocking
            discarded = 0
            try:
                while True:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    discarded += len(chunk)
            except (BlockingIOError, OSError):
                pass  # no more data — expected
            finally:
                sock.settimeout(original_timeout)

            if discarded:
                logger.debug(
                    "[%s@%s] Flushed %d stale bytes from receive buffer after reconnect "
                    "(adapter had buffered responses from a previous session)",
                    self.register_map['name'], self.connection_id, discarded
                )
        except Exception as e:
            logger.debug(
                "[%s@%s] Receive buffer flush failed (non-critical): %s",
                self.register_map['name'], self.connection_id, e
            )

    def disconnect(self):
        """Close connection and release resources (critical for preventing file descriptor leaks)"""
        if self._shared_conn is not None:
            # Connection lifetime is managed by the hub — except for serial, where the hub
            # gives the port back between polls. See SharedModbusConnection.end_poll().
            self._shared_conn.end_poll()
            return
        if self.client:
            try:
                self.client.close()
                logger.info(f"[{self.register_map['name']}@{self.connection_id}] Disconnected successfully")
            except Exception as e:
                # Log disconnect errors - these can indicate resource leaks
                logger.warning(f"[{self.register_map['name']}@{self.connection_id}] Error during disconnect: {e}")
                # Re-raise if it's a critical error (file descriptor issues)
                if "Too many open files" in str(e) or "errno 24" in str(e):
                    logger.error(f"[{self.register_map['name']}@{self.connection_id}] CRITICAL: File descriptor leak detected!")
                    raise
    
    def _track_read_success(self):
        """Track successful read and restore fast polling if we had backed off"""
        if self._consecutive_read_failures > 0:
            self._consecutive_read_failures = 0
            if self._backed_off:
                logger.info(
                    "[%s@%s] Communication restored - resuming fast polling (%.0fms intervals)",
                    self.register_map['name'],
                    self.connection_id,
                    self._default_min_read_interval * 1000
                )
                self.min_read_interval = self._default_min_read_interval
                self._backed_off = False

    def _track_read_failure(self):
        """Track read failure and back off to safe polling if threshold exceeded"""
        self._consecutive_read_failures += 1

        if not self._backed_off and self._consecutive_read_failures >= self._read_failure_threshold:
            logger.warning(
                "[%s@%s] %d consecutive read failures detected - backing off to safe polling interval (%.0fs) to prevent communication errors. "
                "This may indicate serial connection issues, low baudrate, or device processing limitations.",
                self.register_map['name'],
                self.connection_id,
                self._consecutive_read_failures,
                self._fallback_min_read_interval
            )
            self.min_read_interval = self._fallback_min_read_interval
            self._backed_off = True

    def _enforce_read_interval(self):
        """Ensure minimum time between reads per Growatt spec"""
        current_time = time.time()
        time_since_last = current_time - self.last_read_time
        if time_since_last < self.min_read_interval:
            sleep_time = self.min_read_interval - time_since_last
            logger.debug(f"Sleeping {sleep_time:.2f}s to respect read interval")
            time.sleep(sleep_time)
        self.last_read_time = time.time()
    
    def read_input_registers(self, start_address: int, count: int, log_errors: bool = True) -> Optional[list]:
        """Read registers, holding the bus for the transaction (#398)."""
        with self._bus("read"):
            return self._read_input_registers_locked(start_address, count, log_errors)

    def _read_input_registers_locked(self, start_address: int, count: int, log_errors: bool = True) -> Optional[list]:
        """Read input registers with error handling.

        Args:
            start_address: First register address to read
            count: Number of registers to read
            log_errors: If False, downgrade Modbus errors to DEBUG (for optional ranges expected to fail on some models)
        """
        self._enforce_read_interval()

        if self._shared_conn is not None:
            registers = self._shared_conn.read_input_registers(start_address, count, self.slave_id)
            # This used to return directly, bypassing the failure counters below — so
            # _consecutive_read_failures never moved for any TCP entry and the adaptive
            # backoff could not engage for them at all (#367).
            if registers is None:
                self._track_read_failure()
            else:
                self._track_read_success()
            return registers

        try:
            # Try keyword arguments with different parameter names for pymodbus versions
            try:
                # Newer pymodbus uses device_id
                response = self.client.read_input_registers(
                    address=start_address,
                    count=count,
                    device_id=self.slave_id
                )
            except TypeError:
                # Try with 'slave' parameter
                try:
                    response = self.client.read_input_registers(
                        address=start_address, 
                        count=count, 
                        slave=self.slave_id
                    )
                except TypeError:
                    # Try with 'unit' parameter (pymodbus 2.5.x)
                    try:
                        response = self.client.read_input_registers(
                            start_address, 
                            count, 
                            unit=self.slave_id
                        )
                    except TypeError:
                        # Simplest - just address and count
                        response = self.client.read_input_registers(
                            start_address, 
                            count
                        )
            
            # Handle different pymodbus versions for error checking
            if hasattr(response, 'isError'):
                if response.isError():
                    _log = logger.warning if log_errors else logger.debug
                    _log(f"Modbus error reading input registers {start_address}-{start_address+count-1}: {response}")
                    self._track_read_failure()
                    return None
            elif hasattr(response, 'is_error') and callable(response.is_error):
                if response.is_error():
                    _log = logger.warning if log_errors else logger.debug
                    _log(f"Modbus error reading input registers {start_address}-{start_address+count-1}: {response}")
                    self._track_read_failure()
                    return None

            if hasattr(response, 'registers'):
                registers = response.registers
                if not registers:
                    logger.warning(
                        "Inverter returned empty register list for %d-%d "
                        "(adapter online but inverter not responding — likely night-time sleep)",
                        start_address, start_address + count - 1
                    )
                    self._track_read_failure()
                    return None
                if len(registers) < count:
                    logger.warning(
                        "Inverter returned only %d of %d requested registers at %d — treating as failure",
                        len(registers), count, start_address
                    )
                    self._track_read_failure()
                    return None
                logger.debug("Successfully read %d registers from %d", len(registers), start_address)
                self._track_read_success()
                return registers

            logger.warning(f"Unknown response type: {type(response)}, response: {response}")
            self._track_read_failure()
            return None

        except Exception as e:
            logger.debug(f"Exception reading input registers: {e}")
            self._track_read_failure()
            return None
    
    def read_holding_registers(self, start_address: int, count: int) -> Optional[list]:
        """Read registers, holding the bus for the transaction (#398)."""
        with self._bus("read"):
            return self._read_holding_registers_locked(start_address, count)

    def _read_holding_registers_locked(self, start_address: int, count: int) -> Optional[list]:
        """Read holding registers with error handling and slave_id compatibility fallback."""
        self._enforce_read_interval()

        if self._shared_conn is not None:
            registers = self._shared_conn.read_holding_registers(start_address, count, self.slave_id)
            # Same bypass as read_input_registers above (#367).
            if registers is None:
                self._track_read_failure()
            else:
                self._track_read_success()
            return registers

        try:
            try:
                response = self.client.read_holding_registers(address=start_address, count=count, slave=self.slave_id)
            except TypeError:
                try:
                    response = self.client.read_holding_registers(address=start_address, count=count, unit=self.slave_id)
                except TypeError:
                    response = self.client.read_holding_registers(address=start_address, count=count)
            if hasattr(response, "isError") and callable(response.isError) and response.isError():
                logger.debug("Modbus error reading holding registers %d-%d: %r", start_address, start_address + count - 1, response)
                self._track_read_failure()
                return None
            if hasattr(response, "registers"):
                self._track_read_success()
                return response.registers
            logger.debug("Unexpected response type from read_holding_registers(%d, %d): %r", start_address, count, response)
            self._track_read_failure()
            return None
        except Exception as e:
            logger.debug("Exception reading holding registers %d-%d: %s", start_address, start_address + count - 1, e)
            self._track_read_failure()
            return None

    def _validate_spf_battery_power_sign(self, battery_power: float, data: 'GrowattData') -> float:
        """
        Validate and correct battery power sign for SPF off-grid inverters.

        SPF intermittently reports the battery power register with wrong sign during
        PV charging. The inverter_status code is a reliable indicator of the actual
        operational mode and is used to detect and correct sign errors.

        Note: battery_current cannot be used here - SPF hardware only measures
        current during AC charging (register 68 returns 0 during PV charging or
        discharging), which is exactly when this bug manifests.

        Only applies when abs(battery_power) > 10W to avoid correcting near-zero noise.
        Only called when offgrid_protocol=True (SPF models only).

        SPF status codes:
          5=PV Charge, 6=AC Charge, 7=Combine Charge, 8=Combine Charge+Bypass,
          9=PV Charge+Bypass, 10=AC Charge+Bypass → battery_power must be positive
          2=Discharge → battery_power must be negative
          0,1,3,4,11,12 → skipped (ambiguous or no meaningful correction)
        """
        MIN_POWER_THRESHOLD = 10.0  # W - avoid correcting near-zero noise

        if abs(battery_power) < MIN_POWER_THRESHOLD:
            return battery_power

        status = int(data.status)

        # Charging states: battery is receiving power — sign must be positive
        CHARGING_STATES = {5, 6, 7, 8, 9, 10}
        # Discharging state: battery is supplying power — sign must be negative
        DISCHARGING_STATES = {2}
        # Status 0,1,3,4,11 are standby/fault/bypass — skip correction

        if status in CHARGING_STATES and battery_power < 0:
            pv_power = getattr(data, 'pv1_power', 0.0) + getattr(data, 'pv2_power', 0.0)
            logger.warning(
                f"[SPF sign correction] Status {status} indicates charging but "
                f"battery_power={battery_power:.1f}W is negative — correcting to "
                f"{-battery_power:.1f}W (PV={pv_power:.0f}W) [issue #174]"
            )
            return -battery_power

        if status in DISCHARGING_STATES and battery_power > 0:
            logger.warning(
                f"[SPF sign correction] Status {status} indicates discharging but "
                f"battery_power={battery_power:.1f}W is positive — correcting to "
                f"{-battery_power:.1f}W [issue #174]"
            )
            return -battery_power

        # Status 12 (PV Charge+Discharge): hardware sign is unreliable in this settled
        # off-grid state. Resolve direction from power balance: PV >> load means the
        # battery must be net charging; load >> PV means the battery must be net discharging.
        # A 200 W margin avoids flip-flopping when PV ≈ load.  Issue #345.
        #
        # Logged at debug, not warning. This is expected behaviour firing many times a day
        # on an off-grid inverter in normal operation, and at warning level it lands in Home
        # Assistant's error log looking like a fault — one reporter raised it twice as "this
        # error" while chasing something unrelated. A routine correction that is working as
        # designed should not train users to report it (#384).
        if status == 12:
            pv_power = getattr(data, 'pv1_power', 0.0) + getattr(data, 'pv2_power', 0.0)
            load_power = getattr(data, 'ac_power', 0.0)
            BALANCE_MARGIN = 200.0
            if pv_power > load_power + BALANCE_MARGIN and battery_power < 0:
                logger.debug(
                    "[SPF sign correction] Status 12 (PV Charge+Discharge): PV=%.0fW >> "
                    "Load=%.0fW — battery is net charging, correcting %.1fW to %.1fW [issue #345]",
                    pv_power, load_power, battery_power, -battery_power,
                )
                return -battery_power
            if load_power > pv_power + BALANCE_MARGIN and battery_power > 0:
                logger.debug(
                    "[SPF sign correction] Status 12 (PV Charge+Discharge): Load=%.0fW >> "
                    "PV=%.0fW — battery is net discharging, correcting %.1fW to %.1fW [issue #345]",
                    load_power, pv_power, battery_power, -battery_power,
                )
                return -battery_power

        return battery_power

    # Battery temperature scale detection (#397).
    #
    # A raw value of 100 or more can only come from a tenths device: it would mean 100 C
    # or hotter read as whole degrees, which no battery reaches. Seeing one proves the
    # documented scale is right and ends the question for this connection.
    _TEMP_TENTHS_PROOF_RAW = 100

    # The window in which a reading is implausible as tenths but ordinary as whole
    # degrees: raw 15-45 is 1.5-4.5 C on the documented scale. A battery that is actively
    # charging or discharging does not sit there, and 15-45 C is unremarkable.
    #
    # Deliberately narrow. Widening it to raw 50 would misread a spec-compliant inverter
    # at 5.0 C as 50 C - the exact failure of the "three digits means tenths" rule that
    # was proposed, which breaks in cold weather and nowhere else.
    _TEMP_WHOLE_DEGREE_RAW_MIN = 15
    _TEMP_WHOLE_DEGREE_RAW_MAX = 45
    _TEMP_IMPLAUSIBLE_AS_TENTHS_C = 5.0

    def _resolve_battery_temp_scale(self, register: int, scaled_value: float) -> float:
        """Correct battery temperature on firmware that reports whole degrees.

        V1.39 specifies register 1040 as 0.1 C and most hardware follows it: 24.0 C
        arrives as 240. An SPH3600 reports whole degrees instead - 25 for 25 C - which the
        documented scale renders as 2.5 C. Confirmed on that unit against an independent
        BMS temperature register reading the same 25, and against a thermal camera (#397).

        The two cases are genuinely ambiguous from a single reading: raw 25 is 25 C on one
        firmware and 2.5 C on the other. So this corrects only where the documented scale
        yields a value a working battery could not hold, and stops correcting for good the
        moment the device proves itself spec-compliant.

        Biased towards leaving the reading alone. The spec says tenths, exactly one unit is
        known to disagree, and reporting a wrong-but-plausible temperature is worse than
        reporting a right-but-odd one.
        """
        if scaled_value is None:
            return scaled_value

        definition = self.register_map.get('input_registers', {}).get(register, {})
        scale = definition.get('scale', 1)
        if scale == 1:
            return scaled_value  # nothing to undo

        raw = round(scaled_value / scale)

        # Proof of a tenths device. Latch it and never intervene again on this connection,
        # so a cold morning later in the session cannot undo the conclusion.
        if raw >= self._TEMP_TENTHS_PROOF_RAW:
            if not self._battery_temp_scale_confirmed:
                self._battery_temp_scale_confirmed = True
                logger.debug(
                    "[TEMP] Register %d reports the documented tenths scale (raw %d); "
                    "no correction will be applied on this connection.", register, raw,
                )
            return scaled_value

        if self._battery_temp_scale_confirmed:
            return scaled_value

        if (
            self._TEMP_WHOLE_DEGREE_RAW_MIN <= raw <= self._TEMP_WHOLE_DEGREE_RAW_MAX
            and scaled_value < self._TEMP_IMPLAUSIBLE_AS_TENTHS_C
        ):
            if not self._battery_temp_whole_degrees:
                self._battery_temp_whole_degrees = True
                logger.info(
                    "[TEMP] Battery temperature register %d appears to report whole "
                    "degrees on this firmware rather than the documented tenths: raw %d "
                    "reads as %.1f C, which a working battery would not hold. Reporting "
                    "%d C. If this is wrong, say so on issue #397.",
                    register, raw, scaled_value, raw,
                )
            return float(raw)

        return scaled_value

    @staticmethod
    def _candidates_agree(values: list) -> bool:
        """Do these candidate readings describe the same quantity?

        A single candidate agrees with itself. Several agree when they point the same way
        and are the same size; disagreement means at least one of them is not the register
        we think it is, and none of them can be trusted to validate anything.
        """
        if len(values) <= 1:
            return True
        signed = [v for v in values if abs(v) > 0.2]   # ignore near-zero noise for sign
        if signed and not (all(v > 0 for v in signed) or all(v < 0 for v in signed)):
            return False
        mags = [abs(v) for v in values]
        lo, hi = min(mags), max(mags)
        if hi - lo <= 0.5:            # same size to within half an amp
            return True
        return hi <= lo * 2.0         # or at least the same order of magnitude

    def _detect_battery_power_scale(self, voltage: float, current: float, power_register_value: int) -> Optional[float]:
        """
        Auto-detect correct battery power scale using V×I validation.

        WIT inverters have firmware variants - some use 0.1W scale (VPP spec), some use 1.0W.
        This method validates which scale is correct by comparing V×I with register reading.

        Args:
            voltage: Battery voltage in volts
            current: Battery current in amps (absolute value)
            power_register_value: Raw 32-bit power register value

        Returns:
            Detected scale (0.1 or 1.0), or None if detection uncertain
        """
        # Skip detection if already validated
        if self._battery_power_scale_validated:
            return self._battery_power_scale_override

        # Refuse to decide when the inputs are untrustworthy.
        #
        # This check compares the power register against voltage x current. That is only
        # meaningful if the current is right, and on some WIT hardware several registers
        # claim to be battery current while disagreeing by orders of magnitude. One
        # reporter's inverter offered -0.1 A, 6.3 A and -4.3 A simultaneously; the largest
        # was selected, the expected power came out roughly ten times too high, the 1.0
        # scale was chosen to match it, and the decision then latched for the session -
        # producing 40 kW readings on a 6.5 kW battery (#406).
        #
        # The three-sample consistency check did not catch it, because the current was
        # consistently wrong rather than noisy. Consistency is not accuracy.
        #
        # So when the candidates do not agree, no decision is made and the profile's
        # scale stands. That scale comes from the VPP specification, and the commit that
        # restored it (v0.1.8) recorded it as correct for 95%+ of WIT inverters, so it is
        # the right thing to fall back to rather than a guess built on a bad input.
        if not getattr(self, '_battery_current_candidates_agree', True):
            if not self._battery_power_scale_input_warned:
                self._battery_power_scale_input_warned = True
                logger.info(
                    "[SCALE] Not auto-detecting the battery power scale: the battery "
                    "current registers disagree, so voltage x current cannot validate it. "
                    "Using the profile's documented scale instead (#406)."
                )
            return None

        # Calculate expected power from V×I
        expected_power = abs(voltage * current)

        # Skip detection unless the battery is genuinely working.
        #
        # The threshold was 50 W, which is far too low to tell a 10x scale error apart from
        # a bad current reading. A reporter upgraded while his battery was full and his
        # house ran on PV alone: with almost no current flowing, detection fired at 144 W,
        # chose the wrong scale and latched it, giving 40 kW readings on a 6.5 kW battery.
        # Rebooting later while the battery was actually working produced the right scale
        # immediately - his own test, and the clearest evidence for this threshold (#406).
        #
        # At real load the current registers agree and the comparison means something. Near
        # idle they do not, and the arithmetic amplifies whichever one is wrong.
        if expected_power < _BATTERY_SCALE_MIN_POWER_W:
            return None

        # Test both possible scales
        power_with_0_1_scale = abs(power_register_value) * 0.1
        power_with_1_0_scale = abs(power_register_value) * 1.0

        # Calculate relative errors
        error_0_1 = abs(power_with_0_1_scale - expected_power) / expected_power if expected_power > 0 else 1.0
        error_1_0 = abs(power_with_1_0_scale - expected_power) / expected_power if expected_power > 0 else 1.0

        # Determine which scale is better (allow 20% tolerance for measurement variation)
        detected_scale = None
        if error_0_1 < 0.20 and error_0_1 < error_1_0:
            detected_scale = 0.1
        elif error_1_0 < 0.20 and error_1_0 < error_0_1:
            detected_scale = 1.0

        # Store sample for validation
        if detected_scale is not None:
            self._battery_power_scale_samples.append(detected_scale)

            # Validate after collecting 3 consistent samples
            if len(self._battery_power_scale_samples) >= 3:
                # Check if samples are consistent
                if all(s == detected_scale for s in self._battery_power_scale_samples[-3:]):
                    self._battery_power_scale_override = detected_scale
                    self._battery_power_scale_validated = True
                    logger.info(
                        f"WIT Battery Power Scale Auto-Detected: {detected_scale}W "
                        f"(V={voltage:.1f}V, I={current:.1f}A, Expected={expected_power:.0f}W, "
                        f"With 0.1={power_with_0_1_scale:.0f}W, With 1.0={power_with_1_0_scale:.0f}W)"
                    )
                    return detected_scale

        return None

    def _set_from_register(self, data: "GrowattData", field_name: str, address: int) -> None:
        """Assign a decoded register to a field, or record that it could not be read.

        Replaces `data.x = self._get_register_value(addr) or 0.0`, which could not tell a
        genuine zero from a failed read and published both as zero (#384).
        """
        value = self._get_register_value(address)
        if value is None:
            data.unread_fields.add(field_name)
            logger.debug(
                "[%s] %s: register %d not read this poll — reporting unknown rather than 0",
                self.register_map.get('name', '?'), field_name, address,
            )
            return
        setattr(data, field_name, value)

    # Deficit, in watts, that AC output must exceed before a PV reading of zero is treated
    # as impossible. Matches the margin the SPF sign correction uses for the same kind of
    # power-balance reasoning (#345), so the two agree about what counts as significant.
    PV_ZERO_BALANCE_MARGIN = 200.0

    def _suppress_impossible_pv_zero(self, data: "GrowattData") -> None:
        """Withhold a PV reading of zero the inverter's own registers contradict (#384).

        An off-grid SPF intermittently reports 0 in its PV registers while still producing.
        This is not a failed read — the block arrives complete, the registers are present,
        and their contents are zero. A reporter's poll showed 1,907 W of AC output with the
        battery supplying only 329 W, no grid, no generator, and PV reading 0. The missing
        ~1,578 W had nowhere to come from but the panels.

        We cannot recover the real figure; it is not in the response. But publishing zero
        writes a fabricated measurement into long-term statistics that can never afterwards
        be told from a genuine one, and it misleads the sign correction above, which reads a
        false PV=0 against a real load and concludes the battery must be discharging.

        So the field is marked unread and the sensor reports unknown — the same treatment a
        failed read gets, for the same reason: a gap is honest about what we know.

        Deliberately narrow, because the cost of a false positive is suppressing a genuine
        zero:

        * off-grid profiles only — this is where the behaviour is observed, and where the
          power balance is simple enough to be conclusive
        * every alternative source must read zero. An SPF has an AC input and a generator
          input; if either is supplying the load then PV need not be
        * the shortfall must exceed PV_ZERO_BALANCE_MARGIN, so a battery covering the load
          on its own never trips it
        * PV must read exactly zero. A low-but-nonzero reading may be real curtailment
        """
        if not self.register_map.get('offgrid_protocol', False):
            return
        if data.pv_total_power != 0:
            return

        ac_output = float(getattr(data, 'ac_power', 0.0) or 0.0)
        if ac_output <= 0:
            return  # nothing being produced — zero PV is entirely plausible

        # Anything else that could be supplying the load. Each is a real register on SPF,
        # and any of them being non-zero makes the balance inconclusive rather than wrong.
        from_elsewhere = (
            float(getattr(data, 'discharge_power', 0.0) or 0.0)
            + float(getattr(data, 'ac_input_power', 0.0) or 0.0)
            + float(getattr(data, 'generator_power', 0.0) or 0.0)
        )

        shortfall = ac_output - from_elsewhere
        if shortfall <= self.PV_ZERO_BALANCE_MARGIN:
            return

        for field in ('pv_total_power', 'pv1_power', 'pv2_power', 'pv3_power', 'pv4_power'):
            data.unread_fields.add(field)

        # Warn once per session, then debug.
        #
        # The condition is worth knowing about - the inverter is contradicting itself, and
        # the reporter found it useful to see the suppression working. But it is a firmware
        # fault we cannot cure, so once you know your unit does it, every further line is
        # noise. The frequency is unbounded: nine in three days on the reporting hardware,
        # but nothing stops a worse-affected inverter doing it on every poll.
        #
        # It also lands in Home Assistant's error log under "originated from a custom
        # integration", and the same reporter twice raised a different routine warning as
        # "this error" on that basis. One line tells them; a thousand tells them the
        # integration is broken.
        #
        # Same shape as the 32-bit underflow warning (#401).
        self._impossible_pv_zero_count += 1
        if self._impossible_pv_zero_count == 1:
            logger.warning(
                "[%s] PV reads 0 W while the inverter reports %.0f W of AC output with only "
                "%.0f W from battery, grid and generator combined — %.0f W is unaccounted "
                "for, so the PV registers cannot be correct. Reporting PV as unknown for "
                "this poll rather than publishing a zero. This is a known firmware fault on "
                "some units; further occurrences are logged at debug level (#384).",
                self.register_map.get('name', '?'), ac_output, from_elsewhere, shortfall,
            )
        else:
            logger.debug(
                "[%s] Impossible PV zero #%d: %.0f W AC output, %.0f W from elsewhere, "
                "%.0f W unaccounted - PV withheld (#384)",
                self.register_map.get('name', '?'), self._impossible_pv_zero_count,
                ac_output, from_elsewhere, shortfall,
            )

    def _inherit_unread(self, data: "GrowattData", target: str, *sources: str) -> bool:
        """Mark a derived field unread when any input it is computed from was not read.

        A calculated value is only as readable as its inputs. Unread inputs keep their 0.0
        default, so the arithmetic still succeeds and produces a confident-looking zero —
        which is the defect `_set_from_register` exists to prevent, reintroduced one step
        downstream (#384).

        Returns True when the target was marked unread, so callers can skip the calculation.
        """
        if any(source in data.unread_fields for source in sources):
            data.unread_fields.add(target)
            return True
        return False

    def _get_register_value(self, address: int) -> Optional[float]:
        """
        Get scaled value from register, handling 32-bit pairs automatically
        """
        reg_info = self.register_map['input_registers'].get(address)
        if not reg_info:
            return None
        
        raw_value = self._register_cache.get(address)
        if raw_value is None:
            return None
        
        # Check if this is part of a 32-bit pair
        pair_addr = reg_info.get('pair')
        if pair_addr is not None:
            # This register is part of a pair
            # Determine if we're HIGH or LOW word
            pair_info = self.register_map['input_registers'].get(pair_addr)
            if not pair_info:
                # Fallback to single register
                scale = reg_info.get('scale', 1)
                return raw_value * scale
            
            # A 32-bit value ALWAYS occupies both registers — the protocol defines
            # UINT32/INT32 as "high word first, low word last", and every 32-bit entry in
            # the register table declares a length of 2. So a partner missing from the
            # cache never means "zero"; it means the read did not complete.
            #
            # Substituting 0 here fabricated values out of data that never arrived. A
            # truncated block that captured the high word but not the low word decoded as
            # (high << 16): a high word of 10000 was published as 65,536,000 W of PV power,
            # and went straight into Home Assistant's long-term statistics (Issue #367).
            #
            # Returning None instead lets the caller treat the value as unread.
            partner_value = self._register_cache.get(pair_addr)
            if partner_value is None:
                logger.debug(
                    "Register %d is a 32-bit pair with %d, but %d was not read — "
                    "returning no value rather than assuming 0",
                    address, pair_addr, pair_addr,
                )
                return None

            # Check which register is HIGH and which is LOW
            if address < pair_addr:
                # Current address is HIGH, pair is LOW
                high_value = raw_value
                low_value = partner_value
                combined_scale = pair_info.get('combined_scale', 1)
            else:
                # Current address is LOW, pair is HIGH
                low_value = raw_value
                high_value = partner_value
                combined_scale = reg_info.get('combined_scale', 1)
            
            # Combine 32-bit value
            combined = (high_value << 16) | low_value

            # Handle signed values if specified
            if reg_info.get('signed') or pair_info.get('signed'):
                if combined > 0x7FFFFFFF:  # If sign bit is set
                    combined = combined - 0x100000000
            elif combined > 0x7FFFFFFF:
                # Sign bit set on a pair that is not declared signed: the inverter has
                # written a small negative value and we are reading it as a huge positive
                # one. Around the midnight rollover a daily counter can dip just below
                # zero, and -17 arrives as 4,294,967,279 - which at 0.1 kWh is
                # 429,496,727.9 kWh (#401).
                #
                # Every unsigned 32-bit pair we map is a physical quantity: energy in kWh,
                # power in W or VA, reactive power, charge in Ah, runtime. At the scales
                # involved a genuine value with this bit set would mean something like
                # 214 million kWh or 214 MW, so there is no case where it is real.
                #
                # Withheld rather than converted or clamped. Converting publishes a
                # negative daily energy to a total_increasing sensor; clamping to zero
                # invents a reading. Returning None marks the field unread, so the sensor
                # goes unknown for that poll and recovers on the next one - the same
                # treatment every other untrustworthy reading gets.
                # Two quite different faults land here and they cannot be told apart from
                # one reading:
                #
                #   * the register really is unsigned and the inverter glitched - rare,
                #     transient, nothing to fix (this issue)
                #   * the register is signed and the profile forgot the flag - persistent,
                #     and exactly how AC power shipped as 429,496,471 W in v1.2.1 (#361)
                #
                # Withholding is right for the reader either way; neither garbage nor a
                # wrongly-signed value belongs on a dashboard. But silently withholding
                # would hide the second case, which used to announce itself with an absurd
                # number somebody reported. So: warn once per register per session, naming
                # the value it would have had if signed, then drop to debug. A missing flag
                # shows up on the first negative reading; a rollover glitch costs one line
                # a day rather than one per poll.
                name = reg_info.get('name') or pair_info.get('name')
                if name not in self._underflow_warned:
                    self._underflow_warned.add(name)
                    logger.warning(
                        "[UNDERFLOW] %s (registers %d/%d) read %d, which has the sign bit "
                        "set on a pair not declared signed. As a signed value that is %s. "
                        "Withholding it. If this repeats, the profile is probably missing "
                        "'signed': True for this register (#401).",
                        name, address, pair_addr, combined, combined - 0x100000000,
                    )
                else:
                    logger.debug(
                        "[UNDERFLOW] %s: %d withheld again (signed: %s)",
                        name, combined, combined - 0x100000000,
                    )
                return None

            # WIT Battery Power Scale Override (auto-detected if needed)
            reg_name = reg_info.get('name') or pair_info.get('name')
            if reg_name in ('battery_power_low', 'battery_power') and self._battery_power_scale_override is not None:
                # Use detected scale instead of profile default
                combined_scale = self._battery_power_scale_override
                logger.debug(f"Applying detected battery power scale override: {combined_scale}W")

            return combined * combined_scale
        
        else:
            # Single register, apply its scale
            scale = reg_info.get('scale', 1)

            # Handle signed 16-bit values if specified
            if reg_info.get('signed'):
                if raw_value > 0x7FFF:  # If sign bit is set in 16-bit value
                    raw_value = raw_value - 0x10000  # Convert to negative

            return raw_value * scale

    def read_all_data(self) -> Optional[GrowattData]:
        """Read all relevant data from inverter"""
        data = GrowattData()
        
        # Determine register range based on map
        input_regs = self.register_map['input_registers']
        
        # Find min and max addresses to read
        addresses = list(input_regs.keys())
        if not addresses:
            logger.error("No input registers defined in map")
            return None
        
        min_addr = min(addresses)
        max_addr = max(addresses)

        logger.debug(f"[{self.register_map['name']}] Register range: {min_addr}-{max_addr} ({len(addresses)} registers defined)")

        # Clear cache
        self._register_cache = {}

        # Per-profile block size limit. When 'max_block_size' is set in the register map,
        # sparse mode is used: only the register addresses defined in the profile are read,
        # grouped into consecutive runs of at most max_block_size. This avoids reading unused
        # gaps and satisfies inverters that reject multi-register reads (e.g. MIC 2500-5500MTL-S).
        # Profiles without 'max_block_size' use the original dense mode (contiguous 0-to-max
        # range reads in 125-register chunks).
        # A user override takes precedence over the profile's own max_block_size, so a
        # marginal RS485 link can be accommodated without changing the profile for everyone
        # on that model (Issue #360).
        _raw_block_size = self._block_size_override or self.register_map.get('max_block_size')
        _sparse_mode = _raw_block_size is not None
        _block_size = int(_raw_block_size) if _sparse_mode else 125

        def _read_sparse(addr_list: list, fatal: bool = False) -> bool:
            """Read only the listed addresses, batching consecutive ones into runs."""
            idx = 0
            while idx < len(addr_list):
                run_start = addr_list[idx]
                run_end = run_start
                j = idx + 1
                while (j < len(addr_list)
                       and addr_list[j] == run_end + 1
                       and (run_end - run_start + 2) <= _block_size):
                    run_end = addr_list[j]
                    j += 1
                count = run_end - run_start + 1
                regs = self.read_input_registers(run_start, count)
                if regs is None:
                    if fatal:
                        logger.error("Failed to read register block (%d-%d)", run_start, run_end)
                        return False
                    logger.warning("Failed to read register block (%d-%d)", run_start, run_end)
                else:
                    for k, value in enumerate(regs):
                        self._register_cache[run_start + k] = value
                idx = j
            return True

        # Determine which ranges we need to read
        # Check if we have registers in different ranges
        # 875-999 is a separate WIT-only range handled below — exclude it from base range
        # to avoid requesting a single oversized read spanning the 0-874 gap up to ~999
        has_base_range = any(0 <= addr < 875 for addr in addresses)
        has_storage_range = any(1000 <= addr < 2000 for addr in addresses)
        has_3000_range = any(3000 <= addr < 4000 for addr in addresses)
        has_875_range = any(875 <= addr < 1000 for addr in addresses)
        has_8000_range = any(8000 <= addr < 8200 for addr in addresses)
        has_31000_range = any(31000 <= addr < 32000 for addr in addresses)

        # Is the base range this profile's ONLY source of input data?
        #
        # Same reasoning as _3000_is_primary below (Issue #361). A base-range failure was
        # unconditionally fatal, which is right for MIC/MID-X/WIT/TL3-S where 0-874 is all
        # there is — but wrong for hybrid profiles that also carry 3000+ and 31000+ ranges.
        #
        # MIN_TL_XH_3000_10000_V201 is the case that exposed it: 101 of its 104 input
        # registers live at 3000+/31000+, but three legacy stragglers (91, 92 fallback PV
        # energy and 97 boost_temp) make has_base_range true. On MIN TL-XH2 hardware, which
        # serves only the VPP ranges, the poll died reading 0-97 and never reached the
        # 31000 block that works — every entity unavailable despite live data being there.
        #
        # When other ranges exist, a base failure is now a warning and the poll continues.
        # The empty-cache guard further down still catches "every range failed".
        _base_is_primary = not (has_storage_range or has_3000_range
                                or has_875_range or has_8000_range or has_31000_range)

        # Read base range (0-N) if needed — size trimmed to profile's actual max address.
        # Excludes 875-999 (WIT range handled separately).
        if has_base_range:
            if _sparse_mode:
                base_addrs = sorted(a for a in addresses if a < 875)
                logger.debug("Reading base range sparse (%d registers, block_size=%d)",
                             len(base_addrs), _block_size)
                if not _read_sparse(base_addrs, fatal=_base_is_primary):
                    return None
            else:
                max_base_addr = max(a for a in addresses if a < 875)
                base_count = max_base_addr + 1
                logger.debug("Reading base range (0-%d, %d registers)", max_base_addr, base_count)
                for chunk_start in range(0, base_count, 125):
                    chunk_count = min(125, base_count - chunk_start)
                    chunk_regs = self.read_input_registers(chunk_start, chunk_count)
                    if chunk_regs is None:
                        if _base_is_primary:
                            logger.error("Failed to read base input register block (%d-%d)",
                                         chunk_start, chunk_start + chunk_count - 1)
                            return None
                        # Other ranges may still carry this profile's data — don't abort.
                        logger.warning(
                            "Failed to read base input register block (%d-%d) — continuing to "
                            "other ranges (this profile also defines 3000+/31000+ registers)",
                            chunk_start, chunk_start + chunk_count - 1
                        )
                        break
                    for i, value in enumerate(chunk_regs):
                        self._register_cache[chunk_start + i] = value

        # Read business storage range (875-999) if needed - WIT/WIS models
        if has_875_range:
            addrs_875 = sorted(a for a in addresses if 875 <= a < 1000)
            if _sparse_mode:
                logger.debug("Reading 875 range sparse (%d registers, block_size=%d)",
                             len(addrs_875), _block_size)
                _read_sparse(addrs_875)
            else:
                min_addr_875 = addrs_875[0]
                max_addr_875 = addrs_875[-1]
                count_875 = max_addr_875 - min_addr_875 + 1
                logger.debug("Reading 875 range (%d-%d, %d registers)", min_addr_875, max_addr_875, count_875)
                for chunk_start in range(min_addr_875, max_addr_875 + 1, 125):
                    chunk_count = min(125, max_addr_875 - chunk_start + 1)
                    registers = self.read_input_registers(chunk_start, chunk_count)
                    if registers is None:
                        logger.warning("Failed to read 875 block (%d-%d)", chunk_start, chunk_start + chunk_count - 1)
                    else:
                        for i, value in enumerate(registers):
                            self._register_cache[chunk_start + i] = value

        # Read storage range (1000-N) if needed — size trimmed to profile's actual max address.
        # Chunked if > 125 registers (defensive — current profiles peak at ~121).
        if has_storage_range:
            if _sparse_mode:
                storage_addrs = sorted(a for a in addresses if 1000 <= a < 2000)
                logger.debug("Reading storage range sparse (%d registers, block_size=%d)",
                             len(storage_addrs), _block_size)
                _read_sparse(storage_addrs)
            else:
                max_storage_addr = max(a for a in addresses if 1000 <= a < 2000)
                storage_count = max_storage_addr - 1000 + 1
                logger.debug("Reading storage range (1000-%d, %d registers)", max_storage_addr, storage_count)
                for chunk_start in range(1000, max_storage_addr + 1, 125):
                    chunk_count = min(125, max_storage_addr - chunk_start + 1)
                    chunk_regs = self.read_input_registers(chunk_start, chunk_count)
                    if chunk_regs is None:
                        logger.warning("Failed to read storage register block (%d-%d)",
                                       chunk_start, chunk_start + chunk_count - 1)
                    else:
                        for i, value in enumerate(chunk_regs):
                            self._register_cache[chunk_start + i] = value
        
        # Read 3000 range if needed - MIN/MOD models
        if has_3000_range:
            addrs_3000 = sorted([addr for addr in addresses if 3000 <= addr < 4000])
            max_3000_addr = max(addrs_3000)
            count_3000 = (max_3000_addr - 3000) + 1
            _3000_key = ('3000_block', count_3000)
            _3000_RETRY_S = 300

            # Is the 3000 range this profile's ONLY source of input data?
            #
            # If so, a total failure here means the poll produced nothing: suppressing
            # retries would leave _register_cache empty for 5 minutes, every field below
            # would decode to 0, and the coordinator would publish an all-zero reading as
            # if the inverter were healthy — sensors reading 0 instead of going unavailable,
            # with none of the reconnect/backoff paths running because the poll "succeeded"
            # (the overnight Waiting->Normal transition never picked up until a manual
            # reload — Issue #357).
            #
            # But it is NOT the only source when the profile also defines a base range
            # (0-874) or a VPP range (31000+). V2.01 profiles carry both 3000+ and 31000+,
            # and some hardware serves only the VPP range — notably MIN TL-XH2, where the
            # entire 3000 block is dead while 31000-31199 returns live data (Issue #361).
            # Treating 3000 as primary there aborted the poll before the working VPP range
            # was ever read. The empty-cache guard further down is the correct safety net
            # for "every range failed"; this flag only covers "the sole range failed".
            _3000_is_primary = not has_base_range and not has_31000_range

            # Skip-on-failure: after the first failure, suppress retries for 5 minutes.
            # This prevents log flooding when an inverter simply doesn't support this range
            # (e.g. one model in a two-inverter setup where only one uses 3000-range registers).
            # Never applied when the range is primary — see above.
            _3000_prev = self._failed_optional_ranges.get(_3000_key)
            _3000_skip = False
            if _3000_prev and not _3000_is_primary:
                _3000_fail_time, _3000_fail_count = _3000_prev
                if time.time() - _3000_fail_time < _3000_RETRY_S:
                    _3000_skip = True
                else:
                    logger.debug(f"Retrying previously failed 3000-range block (3000-{max_3000_addr})")

            if not _3000_skip:
                _3000_any_fail = False
                _3000_any_ok = False

                # Check if we need to split the read (max 125 registers per read)
                if count_3000 > 125:
                    # Split into contiguous blocks
                    logger.debug(f"Splitting 3000 range into blocks (total range: 3000-{max_3000_addr}, {count_3000} registers)")

                    blocks = []
                    current_block = [addrs_3000[0]]
                    for addr in addrs_3000[1:]:
                        if addr - current_block[-1] <= 10:  # Group if gap is small
                            current_block.append(addr)
                        else:
                            blocks.append(current_block)
                            current_block = [addr]
                    blocks.append(current_block)

                    # Read each block separately
                    for block in blocks:
                        min_addr_block = min(block)
                        max_addr_block = max(block)
                        count_block = (max_addr_block - min_addr_block) + 1

                        # Further split if block still exceeds 125 registers
                        if count_block > 125:
                            # Read in 125-register chunks
                            for chunk_start in range(min_addr_block, max_addr_block + 1, 125):
                                chunk_count = min(125, max_addr_block - chunk_start + 1)
                                logger.debug(f"Reading 3000 sub-chunk ({chunk_start}-{chunk_start+chunk_count-1}, {chunk_count} registers)")
                                registers = self.read_input_registers(chunk_start, chunk_count)
                                if registers is None:
                                    _3000_any_fail = True
                                    logger.debug(f"3000 sub-chunk failed ({chunk_start}-{chunk_start+chunk_count-1})")
                                else:
                                    _3000_any_ok = True
                                    for i, value in enumerate(registers):
                                        self._register_cache[chunk_start + i] = value
                        else:
                            logger.debug(f"Reading 3000 sub-range ({min_addr_block}-{max_addr_block}, {count_block} registers)")
                            registers = self.read_input_registers(min_addr_block, count_block)
                            if registers is None:
                                _3000_any_fail = True
                                logger.debug(f"3000 sub-range failed ({min_addr_block}-{max_addr_block})")
                            else:
                                _3000_any_ok = True
                                for i, value in enumerate(registers):
                                    addr = min_addr_block + i
                                    self._register_cache[addr] = value
                                    if addr in [3075, 3076, 3077, 3078]:
                                        logger.debug(f"[{self.register_map['name']}@{self.connection_id}] Cached 3000 range: reg {addr} = {value}")
                else:
                    # Single read is sufficient
                    logger.debug(f"Reading 3000 range (3000-{max_3000_addr}, {count_3000} registers)")
                    registers = self.read_input_registers(3000, count_3000)
                    if registers is None:
                        _3000_any_fail = True
                    else:
                        _3000_any_ok = True
                        for i, value in enumerate(registers):
                            self._register_cache[3000 + i] = value

                # Update failure tracking based on outcome
                if _3000_any_fail and not _3000_any_ok and _3000_is_primary:
                    # Primary range failed completely — there is no data to report. Return
                    # None so the coordinator marks the inverter offline, increments its
                    # failure counter and runs its reconnect/backoff path, rather than
                    # publishing zeros as a healthy reading.
                    logger.warning(
                        "Failed to read primary 3000 register block (3000-%d) — "
                        "reporting poll as failed",
                        max_3000_addr
                    )
                    return None

                if _3000_any_fail and not _3000_any_ok:
                    _prev = self._failed_optional_ranges.get(_3000_key)
                    _count = (_prev[1] + 1) if _prev else 1
                    self._failed_optional_ranges[_3000_key] = (time.time(), _count)
                    if _count == 1:
                        logger.warning(
                            f"Failed to read 3000 register block (extended data may be unavailable). "
                            f"Will suppress and retry in {_3000_RETRY_S}s."
                        )
                    else:
                        logger.debug(f"3000 register block still failing (attempt {_count})")
                elif _3000_any_ok:
                    self._failed_optional_ranges.pop(_3000_key, None)

        # Read 8000 range if needed - WIT/WIS battery/storage data
        if has_8000_range:
            addrs_8000 = sorted([addr for addr in addresses if 8000 <= addr < 8200])
            min_addr_8000 = min(addrs_8000)
            max_addr_8000 = max(addrs_8000)
            count_8000 = (max_addr_8000 - min_addr_8000) + 1

            is_wit_profile = 'WIT' in self.register_map['name']
            logger.debug(f"Reading 8000 range ({min_addr_8000}-{max_addr_8000}, {count_8000} registers)")
            # Critical WIT battery registers to retry individually on block failure
            _CRITICAL_8000 = [8034, 8035, 8093, 8094, 8095]

            if count_8000 > 125:
                for chunk_start in range(min_addr_8000, max_addr_8000 + 1, 125):
                    chunk_count = min(125, max_addr_8000 - chunk_start + 1)
                    chunk_end = chunk_start + chunk_count - 1
                    registers = self.read_input_registers(chunk_start, chunk_count)
                    if registers is None:
                        logger.warning(f"Failed to read 8000 block ({chunk_start}-{chunk_end}) - retrying critical registers individually")
                        for critical_addr in _CRITICAL_8000:
                            if chunk_start <= critical_addr <= chunk_end:
                                single = self.read_input_registers(critical_addr, 1)
                                if single:
                                    self._register_cache[critical_addr] = single[0]
                                    logger.debug(f"  8000-range retry OK: reg {critical_addr} = {single[0]}")
                                else:
                                    logger.debug(f"  8000-range retry failed: reg {critical_addr}")
                    else:
                        for i, value in enumerate(registers):
                            self._register_cache[chunk_start + i] = value
            else:
                registers = self.read_input_registers(min_addr_8000, count_8000)
                if registers is None:
                    logger.warning(f"Failed to read 8000 register block ({min_addr_8000}-{max_addr_8000}) - retrying critical battery registers individually")
                    for critical_addr in _CRITICAL_8000:
                        if min_addr_8000 <= critical_addr <= max_addr_8000:
                            single = self.read_input_registers(critical_addr, 1)
                            if single:
                                self._register_cache[critical_addr] = single[0]
                                logger.debug(f"  8000-range retry OK: reg {critical_addr} = {single[0]}")
                            else:
                                logger.debug(f"  8000-range retry failed: reg {critical_addr}")
                else:
                    for i, value in enumerate(registers):
                        self._register_cache[min_addr_8000 + i] = value

        # Read 31000 range if needed - MOD extended battery/BMS range
        if has_31000_range:
            # Split into contiguous blocks to avoid reading large gaps
            # (e.g., 31126-31127 and 31200-31209 are separate blocks with a 73-register gap)
            addrs_31000 = sorted([addr for addr in addresses if 31000 <= addr < 32000])

            # Group into contiguous blocks (max gap of 10 registers)
            blocks = []
            current_block = [addrs_31000[0]]
            for addr in addrs_31000[1:]:
                if addr - current_block[-1] <= 10:
                    current_block.append(addr)
                else:
                    blocks.append(current_block)
                    current_block = [addr]
            blocks.append(current_block)

            # Read each block separately
            for block in blocks:
                min_addr_block = min(block)
                max_addr_block = max(block)
                count_block = (max_addr_block - min_addr_block) + 1

                # Determine if this range is truly optional or critical
                # WIT profiles: 31200-31223 range contains CRITICAL battery data (no fallback)
                # MIN profiles: 31000+ ranges are optional VPP duplicates of 3000-range data
                is_wit_critical_range = (
                    'WIT' in self.register_map['name'] and
                    31200 <= min_addr_block <= 31224
                )

                # Check if this range recently failed — skip if within retry window
                _OPTIONAL_RANGE_RETRY_SECONDS = 300
                range_key = (min_addr_block, count_block)
                if not is_wit_critical_range and range_key in self._failed_optional_ranges:
                    _fail_time, _fail_count = self._failed_optional_ranges[range_key]
                    if time.time() - _fail_time < _OPTIONAL_RANGE_RETRY_SECONDS:
                        continue
                    # Retry window expired — fall through to re-read.
                    # Do NOT delete the entry here: the fail_count must survive so that
                    # "warn once, then DEBUG" works correctly. If the re-read fails below,
                    # _prev will find the existing entry and increment the count past 1,
                    # suppressing the WARNING. The entry is cleared only on a successful read.
                    logger.debug(f"Retrying previously failed optional VPP range ({min_addr_block}-{max_addr_block})")

                logger.debug(f"Reading 31000 sub-range ({min_addr_block}-{max_addr_block}, {count_block} registers)")
                registers = self.read_input_registers(min_addr_block, count_block, log_errors=is_wit_critical_range)
                if registers is None:
                    # Only track as failed if it's truly optional
                    if not is_wit_critical_range:
                        _prev = self._failed_optional_ranges.get(range_key)
                        _fail_count = (_prev[1] + 1) if _prev else 1
                        self._failed_optional_ranges[range_key] = (time.time(), _fail_count)
                        if _fail_count == 1:
                            logger.warning(
                                f"Optional VPP range ({min_addr_block}-{max_addr_block}) failed — "
                                f"battery sensors may be temporarily unavailable. "
                                f"Will retry in {_OPTIONAL_RANGE_RETRY_SECONDS}s."
                            )
                        else:
                            logger.debug(f"Optional VPP range ({min_addr_block}-{max_addr_block}) still failing (attempt {_fail_count}) - using 3000-range data")
                    else:
                        # Critical WIT battery range - keep trying, log warning
                        logger.warning(f"Failed to read critical WIT battery range ({min_addr_block}-{max_addr_block}) - will retry next poll")
                    # Don't return None - continue with what we have
                else:
                    # Range succeeded — clear any previous failure record so the
                    # next failure is treated as fresh (warn again on first failure).
                    self._failed_optional_ranges.pop(range_key, None)
                    # Populate cache
                    for i, value in enumerate(registers):
                        self._register_cache[min_addr_block + i] = value

        # Safety net: if every range failed or was suppressed the cache is empty and every
        # field below would decode to 0. Returning that as valid data makes the coordinator
        # read a dead link as a healthy inverter reporting zeros — entities stay "available"
        # showing 0, _consecutive_failures never increments, and no reconnect or adaptive
        # backoff ever runs, so the state persists until a manual reload.
        if not self._register_cache:
            logger.warning(
                "[%s@%s] No registers read this poll (all ranges failed or suppressed) — "
                "reporting poll as failed",
                self.register_map['name'], self.connection_id
            )
            return None

        # Now extract values using the register map
        try:
            # Status — look up by name rather than assuming it's at min_addr
            status_addr = self._find_register_by_name('inverter_status') or self._find_register_by_name('status')
            if status_addr:
                data.status = int(self._get_register_value(status_addr) or 0)
            else:
                data.status = int(self._get_register_value(min_addr) or 0)
            equipment_status_addr = self._find_register_by_name('equipment_status')
            if equipment_status_addr:
                data.equipment_status = int(self._get_register_value(equipment_status_addr) or 0)
                data.equipment_status_valid = True

            # PV String 1
            pv1_voltage_addr = self._find_register_by_name('pv1_voltage')
            pv1_current_addr = self._find_register_by_name('pv1_current')
            pv1_power_low_addr = self._find_register_by_name('pv1_power_low')
            
            if pv1_voltage_addr:
                self._set_from_register(data, 'pv1_voltage', pv1_voltage_addr)
            if pv1_current_addr:
                self._set_from_register(data, 'pv1_current', pv1_current_addr)
            if pv1_power_low_addr:
                self._set_from_register(data, 'pv1_power', pv1_power_low_addr)
            
            # PV String 2
            pv2_voltage_addr = self._find_register_by_name('pv2_voltage')
            pv2_current_addr = self._find_register_by_name('pv2_current')
            pv2_power_low_addr = self._find_register_by_name('pv2_power_low')
            
            if pv2_voltage_addr:
                self._set_from_register(data, 'pv2_voltage', pv2_voltage_addr)
            if pv2_current_addr:
                self._set_from_register(data, 'pv2_current', pv2_current_addr)
            if pv2_power_low_addr:
                self._set_from_register(data, 'pv2_power', pv2_power_low_addr)
            
            # PV String 3 (if available)
            pv3_voltage_addr = self._find_register_by_name('pv3_voltage')
            pv3_current_addr = self._find_register_by_name('pv3_current')
            pv3_power_low_addr = self._find_register_by_name('pv3_power_low')
            
            if pv3_voltage_addr:
                self._set_from_register(data, 'pv3_voltage', pv3_voltage_addr)
            if pv3_current_addr:
                self._set_from_register(data, 'pv3_current', pv3_current_addr)
            if pv3_power_low_addr:
                self._set_from_register(data, 'pv3_power', pv3_power_low_addr)

            # PV String 4 (if available — 4-MPPT models like WIT 29.9-50K-XHU)
            pv4_voltage_addr = self._find_register_by_name('pv4_voltage')
            pv4_current_addr = self._find_register_by_name('pv4_current')
            pv4_power_low_addr = self._find_register_by_name('pv4_power_low')

            if pv4_voltage_addr:
                self._set_from_register(data, 'pv4_voltage', pv4_voltage_addr)
            if pv4_current_addr:
                self._set_from_register(data, 'pv4_current', pv4_current_addr)
            if pv4_power_low_addr:
                self._set_from_register(data, 'pv4_power', pv4_power_low_addr)

            # Derive per-string power where the profile has no power register for that
            # string (Issue #361). Some hardware reports only per-string voltage and
            # current plus a single combined total — MIN TL-XH2 is the first confirmed
            # case. Without this the per-string power sensors sit at 0 while their own
            # voltage and current sensors show live values, which reads as a fault
            # rather than a gap in the register map.
            for _pv in (1, 2, 3, 4):
                if self._find_register_by_name(f'pv{_pv}_power_low'):
                    continue  # real register present — never override it
                # A derived value is only as readable as its inputs. If either was not
                # read this poll they are still sitting at their 0.0 default, so the
                # product would publish a confident zero (#384).
                if (f'pv{_pv}_voltage' in data.unread_fields
                        or f'pv{_pv}_current' in data.unread_fields):
                    data.unread_fields.add(f'pv{_pv}_power')
                    continue
                _v = getattr(data, f'pv{_pv}_voltage', 0.0) or 0.0
                _i = getattr(data, f'pv{_pv}_current', 0.0) or 0.0
                if _v and _i:
                    setattr(data, f'pv{_pv}_power', round(_v * _i, 1))

            # Total PV Power
            pv_total_addr = self._find_register_by_name('pv_total_power_low')
            if pv_total_addr:
                self._set_from_register(data, 'pv_total_power', pv_total_addr)
            elif any(f'pv{_pv}_power' in data.unread_fields for _pv in (1, 2, 3, 4)):
                # Summed from the strings, so it inherits their read state. Unread
                # strings keep their 0.0 default, which made the total the one PV field
                # still publishing a plausible zero after the #384 fix.
                data.unread_fields.add('pv_total_power')
            else:
                # Calculate from strings if not available
                data.pv_total_power = data.pv1_power + data.pv2_power + data.pv3_power + data.pv4_power

            # PV Energy (WIT per-MPPT tracking - Issue #146)
            # These registers track DC input from solar panels only (not total system output)
            pv1_energy_today_addr = self._find_register_by_name('pv1_energy_today_low')
            if pv1_energy_today_addr:
                self._set_from_register(data, 'pv1_energy_today', pv1_energy_today_addr)
                logger.debug(f"[{self.register_map['name']}] PV1 energy today from reg {pv1_energy_today_addr}: {data.pv1_energy_today} kWh")

            pv2_energy_today_addr = self._find_register_by_name('pv2_energy_today_low')
            if pv2_energy_today_addr:
                self._set_from_register(data, 'pv2_energy_today', pv2_energy_today_addr)
                logger.debug(f"[{self.register_map['name']}] PV2 energy today from reg {pv2_energy_today_addr}: {data.pv2_energy_today} kWh")

            pv3_energy_today_addr = self._find_register_by_name('pv3_energy_today_low')
            if pv3_energy_today_addr:
                self._set_from_register(data, 'pv3_energy_today', pv3_energy_today_addr)
                logger.debug(f"[{self.register_map['name']}] PV3 energy today from reg {pv3_energy_today_addr}: {data.pv3_energy_today} kWh")

            pv4_energy_today_addr = self._find_register_by_name('pv4_energy_today_low')
            if pv4_energy_today_addr:
                self._set_from_register(data, 'pv4_energy_today', pv4_energy_today_addr)
                logger.debug(f"[{self.register_map['name']}] PV4 energy today from reg {pv4_energy_today_addr}: {data.pv4_energy_today} kWh")

            pv1_energy_total_addr = self._find_register_by_name('pv1_energy_total_low')
            if pv1_energy_total_addr:
                self._set_from_register(data, 'pv1_energy_total', pv1_energy_total_addr)
                logger.debug(f"[{self.register_map['name']}] PV1 energy total from reg {pv1_energy_total_addr}: {data.pv1_energy_total} kWh")

            pv2_energy_total_addr = self._find_register_by_name('pv2_energy_total_low')
            if pv2_energy_total_addr:
                self._set_from_register(data, 'pv2_energy_total', pv2_energy_total_addr)
                logger.debug(f"[{self.register_map['name']}] PV2 energy total from reg {pv2_energy_total_addr}: {data.pv2_energy_total} kWh")

            pv3_energy_total_addr = self._find_register_by_name('pv3_energy_total_low')
            if pv3_energy_total_addr:
                self._set_from_register(data, 'pv3_energy_total', pv3_energy_total_addr)
                logger.debug(f"[{self.register_map['name']}] PV3 energy total from reg {pv3_energy_total_addr}: {data.pv3_energy_total} kWh")

            pv4_energy_total_addr = self._find_register_by_name('pv4_energy_total_low')
            if pv4_energy_total_addr:
                self._set_from_register(data, 'pv4_energy_total', pv4_energy_total_addr)
                logger.debug(f"[{self.register_map['name']}] PV4 energy total from reg {pv4_energy_total_addr}: {data.pv4_energy_total} kWh")

            pv_energy_total_addr = self._find_register_by_name('pv_energy_total_low')
            if pv_energy_total_addr:
                self._set_from_register(data, 'pv_energy_total', pv_energy_total_addr)
                logger.debug(f"[{self.register_map['name']}] PV energy total from reg {pv_energy_total_addr}: {data.pv_energy_total} kWh")
                if data.pv_energy_total == 0.0:
                    # Some MIN TL-XH firmware variants return 0 in the 3000-range Epv registers
                    # (3053/3054) but report valid lifetime totals in the legacy 0-range registers
                    # (91/92). Fall back when the primary read produces exactly zero so that a
                    # genuinely zero value is still honoured if the legacy register is also zero.
                    pv_energy_total_legacy_addr = self._find_register_by_name('pv_energy_total_legacy_low')
                    if pv_energy_total_legacy_addr:
                        legacy_value = self._get_register_value(pv_energy_total_legacy_addr) or 0.0
                        if legacy_value > 0.0:
                            data.pv_energy_total = legacy_value
                            logger.debug(f"[{self.register_map['name']}] PV energy total fallback to legacy reg {pv_energy_total_legacy_addr}: {data.pv_energy_total} kWh")

            # AC Output (generic - will use Phase R via alias for 3-phase)
            ac_voltage_addr = self._find_register_by_name('ac_voltage')
            ac_current_addr = self._find_register_by_name('ac_current')
            ac_power_addr = self._find_register_by_name('ac_power_low')
            if not ac_power_addr:
                # SPF off-grid models use 'load_power_low' instead
                ac_power_addr = self._find_register_by_name('load_power_low')
            ac_freq_addr = self._find_register_by_name('ac_frequency')

            if ac_voltage_addr:
                self._set_from_register(data, 'ac_voltage', ac_voltage_addr)
            if ac_current_addr:
                self._set_from_register(data, 'ac_current', ac_current_addr)
            if ac_power_addr:
                self._set_from_register(data, 'ac_power', ac_power_addr)
                logger.debug(f"AC Power from reg {ac_power_addr}: {data.ac_power}W")
            if ac_freq_addr:
                self._set_from_register(data, 'ac_frequency', ac_freq_addr)

            # AC Apparent Power (SPF Off-Grid, some other models)
            ac_apparent_power_addr = self._find_register_by_name('ac_apparent_power_low')
            if ac_apparent_power_addr:
                self._set_from_register(data, 'ac_apparent_power', ac_apparent_power_addr)
                logger.debug(f"AC Apparent Power from reg {ac_apparent_power_addr}: {data.ac_apparent_power} VA")

            # Load Percentage (SPF Off-Grid)
            load_percentage_addr = self._find_register_by_name('load_percentage')
            if load_percentage_addr:
                self._set_from_register(data, 'load_percentage', load_percentage_addr)
                logger.debug(f"Load Percentage from reg {load_percentage_addr}: {data.load_percentage}%")

            # Grid/AC Input (SPF Off-Grid, other models)
            grid_voltage_addr = self._find_register_by_name('grid_voltage')
            grid_frequency_addr = self._find_register_by_name('grid_frequency')
            ac_input_power_low_addr = self._find_register_by_name('ac_input_power_low')
            if grid_voltage_addr:
                self._set_from_register(data, 'grid_voltage', grid_voltage_addr)
                logger.debug(f"Grid voltage from reg {grid_voltage_addr}: {data.grid_voltage} V (raw cache: {self._register_cache.get(grid_voltage_addr)})")
            else:
                logger.debug("Grid voltage register not found in profile")
            if grid_frequency_addr:
                self._set_from_register(data, 'grid_frequency', grid_frequency_addr)
                logger.debug(f"Grid frequency from reg {grid_frequency_addr}: {data.grid_frequency} Hz (raw cache: {self._register_cache.get(grid_frequency_addr)})")
            else:
                logger.debug("Grid frequency register not found in profile")
            if ac_input_power_low_addr:
                self._set_from_register(data, 'ac_input_power', ac_input_power_low_addr)
                logger.debug(f"AC input power from reg {ac_input_power_low_addr}: {data.ac_input_power} W")
            else:
                logger.debug("AC input power register not found in profile")

            # Generator Sensors (SPF Off-Grid with generator input)
            generator_power_addr = self._find_register_by_name('generator_power')
            generator_voltage_addr = self._find_register_by_name('generator_voltage')
            generator_discharge_today_low_addr = self._find_register_by_name('generator_discharge_today_low')
            generator_discharge_total_low_addr = self._find_register_by_name('generator_discharge_total_low')
            if generator_power_addr:
                self._set_from_register(data, 'generator_power', generator_power_addr)
                logger.debug(f"Generator power from reg {generator_power_addr}: {data.generator_power} W (raw cache: {self._register_cache.get(generator_power_addr)})")
            else:
                logger.debug("Generator power register not found in profile")
            if generator_voltage_addr:
                self._set_from_register(data, 'generator_voltage', generator_voltage_addr)
                logger.debug(f"Generator voltage from reg {generator_voltage_addr}: {data.generator_voltage} V (raw cache: {self._register_cache.get(generator_voltage_addr)})")
            else:
                logger.debug("Generator voltage register not found in profile")
            if generator_discharge_today_low_addr:
                self._set_from_register(data, 'generator_discharge_today', generator_discharge_today_low_addr)
                logger.debug(f"Generator discharge today from reg {generator_discharge_today_low_addr}: {data.generator_discharge_today} kWh")
            else:
                logger.debug("Generator discharge today register not found in profile")
            if generator_discharge_total_low_addr:
                self._set_from_register(data, 'generator_discharge_total', generator_discharge_total_low_addr)
                logger.debug(f"Generator discharge total from reg {generator_discharge_total_low_addr}: {data.generator_discharge_total} kWh")
            else:
                logger.debug("Generator discharge total register not found in profile")

            # Three-Phase AC Output (individual phases)
            # Read voltages, currents, and power registers for all phases upfront so we can
            # decide whether to use register values or fall back to V×I consistently.
            ac_voltage_r_addr = self._find_register_by_name('ac_voltage_r')
            ac_current_r_addr = self._find_register_by_name('ac_current_r')
            ac_power_r_addr = self._find_register_by_name('ac_power_r_low')
            ac_voltage_s_addr = self._find_register_by_name('ac_voltage_s')
            ac_current_s_addr = self._find_register_by_name('ac_current_s')
            ac_power_s_addr = self._find_register_by_name('ac_power_s_low')
            ac_voltage_t_addr = self._find_register_by_name('ac_voltage_t')
            ac_current_t_addr = self._find_register_by_name('ac_current_t')
            ac_power_t_addr = self._find_register_by_name('ac_power_t_low')

            if ac_voltage_r_addr:
                self._set_from_register(data, 'ac_voltage_r', ac_voltage_r_addr)
            if ac_current_r_addr:
                self._set_from_register(data, 'ac_current_r', ac_current_r_addr)
            if ac_voltage_s_addr:
                self._set_from_register(data, 'ac_voltage_s', ac_voltage_s_addr)
            if ac_current_s_addr:
                self._set_from_register(data, 'ac_current_s', ac_current_s_addr)
            if ac_voltage_t_addr:
                self._set_from_register(data, 'ac_voltage_t', ac_voltage_t_addr)
            if ac_current_t_addr:
                self._set_from_register(data, 'ac_current_t', ac_current_t_addr)

            power_r_reg = (self._get_register_value(ac_power_r_addr) or 0.0) if ac_power_r_addr else 0.0
            power_s_reg = (self._get_register_value(ac_power_s_addr) or 0.0) if ac_power_s_addr else 0.0
            power_t_reg = (self._get_register_value(ac_power_t_addr) or 0.0) if ac_power_t_addr else 0.0

            # For 3-phase models, only use register values if ALL three phases return valid data.
            # Some firmware (e.g. SPH-TL3, MOD TL3-X) only populates the phase R register
            # (which holds total output power, not a true per-phase R value) while returning 0
            # for S and T. In that case, calculate all three phases from V×I so values are
            # consistent with each other. Models with fully-functional per-phase registers
            # (e.g. MOD TL3-XH, WIT) never take this path.
            is_three_phase = ac_power_s_addr is not None or ac_power_t_addr is not None
            all_phase_powers_valid = bool(power_r_reg and power_s_reg and power_t_reg)

            if is_three_phase and not all_phase_powers_valid:
                for _ph in ('r', 's', 't'):
                    if self._inherit_unread(data, f'ac_power_{_ph}',
                                            f'ac_voltage_{_ph}', f'ac_current_{_ph}'):
                        continue
                    _v = getattr(data, f'ac_voltage_{_ph}')
                    _i = getattr(data, f'ac_current_{_ph}')
                    if _v > 0 and _i > 0:
                        setattr(data, f'ac_power_{_ph}', round(_v * _i, 1))
                logger.debug(
                    f"Phase power registers incomplete (R={power_r_reg}, S={power_s_reg}, T={power_t_reg}), "
                    f"using V×I: R={data.ac_power_r}W, S={data.ac_power_s}W, T={data.ac_power_t}W"
                )
            else:
                data.ac_power_r = power_r_reg
                data.ac_power_s = power_s_reg
                data.ac_power_t = power_t_reg

            # Line-to-Line Voltages
            ac_voltage_rs_addr = self._find_register_by_name('line_voltage_rs')
            ac_voltage_st_addr = self._find_register_by_name('line_voltage_st')
            ac_voltage_tr_addr = self._find_register_by_name('line_voltage_tr')
            if ac_voltage_rs_addr:
                self._set_from_register(data, 'ac_voltage_rs', ac_voltage_rs_addr)
            if ac_voltage_st_addr:
                self._set_from_register(data, 'ac_voltage_st', ac_voltage_st_addr)
            if ac_voltage_tr_addr:
                self._set_from_register(data, 'ac_voltage_tr', ac_voltage_tr_addr)
            
            # System output power (total per inverter)
            system_output_addr = self._find_register_by_name('system_output_power_low')
            if system_output_addr:
                self._set_from_register(data, 'system_output_power', system_output_addr)

            # Power Flow (if available - storage/hybrid models)
            power_to_user_addr = self._find_register_by_name('power_to_user_low')
            power_to_load_addr = self._find_register_by_name('power_to_load_low')

            # Grid flow: take the first address carrying a reading, wherever it lives.
            #
            # These used to defer to _find_register_by_name_with_fallback(), which picks a
            # range using _detect_battery_register_range(). That is battery detection, and
            # it has nothing to do with a grid meter — but on an inverter with **no
            # battery** every battery test sensor reads zero, so the detector takes its
            # "both ranges are zero" branch and returns 'fallback'. The VPP address is then
            # filtered out, the fallback resolves to the same 3000-range address it started
            # from, and the guard `vpp_addr != power_to_grid_addr` refuses to fire.
            #
            # Net effect: on a batteryless grid-tied inverter the metered value at
            # 31112/31113 could never be reached, however good the meter. A reporter with a
            # working DTSU666 — reading -211.2 W from those registers with his own script at
            # the same moment — had his grid sensors falling through to an estimate, because
            # 3043/3044 read 0 on that firmware and nothing was allowed to look further
            # (#228).
            #
            # Note 31113 is meter_power, NOT 31101 active power: on a grid-tied MID,
            # 31100/31101 is the inverter's own 3-phase output while 31112/31113 is metered
            # grid exchange. v0.8.6 remapped it for that reason; re-read mid.py before
            # changing it.
            for _flow_attr, _flow_name, _phase_names in (
                ('power_to_grid', 'power_to_grid_low', ()),
                ('power_to_user', 'power_to_user_low',
                 ('power_to_user_r_low', 'power_to_user_s_low', 'power_to_user_t_low')),
            ):
                self._resolve_phase_total(data, _flow_attr, _flow_name, _phase_names)
            if power_to_load_addr:
                self._set_from_register(data, 'power_to_load', power_to_load_addr)

            # SPH-HU split-phase CT/local-load legs. These names exist only on the HU
            # profile, so this loop is a no-op for every other inverter family.
            for _leg_attr in (
                'ct_grid_import_l1', 'ct_grid_import_l2',
                'ct_grid_export_l1', 'ct_grid_export_l2',
                'inverter_to_load_l1', 'inverter_to_load_l2',
            ):
                _leg_addr = self._find_register_by_name(f'{_leg_attr}_low')
                if _leg_addr is not None:
                    self._set_from_register(data, _leg_attr, _leg_addr)
            
            # Energy Today
            # For hybrid inverters (WIT/SPH-TL3 etc.), the AC energy_today register (e.g. reg 53/54)
            # reflects total system output including battery discharge — not solar-only production.
            # Those profiles set 'use_mppt_energy_today': True so we sum the per-MPPT DC string
            # registers instead, which track true solar input unaffected by battery activity.
            # Issue #146, #225: do NOT gate on pv*_connected (voltage drops at sunset but
            # accumulated daily totals remain valid until midnight reset).
            # For pure grid-tied profiles (MIN, MIC, MOD) this flag is absent/False and
            # energy_today is read directly from its register — no summation.
            use_mppt = self.register_map.get('use_mppt_energy_today', False)
            pv1_energy_addr = self._find_register_by_name('pv1_energy_today_low')

            if use_mppt and pv1_energy_addr:
                # SPH/WIT hybrid: reg 53/54 counts all AC output including battery discharge,
                # so it rises at night as the battery powers the house. Per-MPPT DC registers
                # track solar input only — 0 at night or on a cloudy day is the correct value.
                # Gate on register *existence* not *value > 0* to avoid falling back to the
                # battery-inflated register at night when the daily total resets to zero.
                pv_energy_sum = data.pv1_energy_today + data.pv2_energy_today + data.pv3_energy_today + data.pv4_energy_today

                # Sanity check: guard against corrupt/unresponsive register reads (e.g. 65535 values).
                # 1000 kWh threshold accommodates large 4-MPPT commercial systems (50 kW × 8 hrs × 2.5× = ~1000).
                if pv_energy_sum < 1000:
                    data.energy_today = pv_energy_sum
                    logger.debug(f"[{self.register_map['name']}@{self.connection_id}] Energy today from per-MPPT registers: PV1={data.pv1_energy_today} + PV2={data.pv2_energy_today} + PV3={data.pv3_energy_today} + PV4={data.pv4_energy_today} = {data.energy_today} kWh")
                else:
                    # Garbage data — fall back to direct register
                    logger.warning(f"[{self.register_map['name']}@{self.connection_id}] Per-MPPT energy {pv_energy_sum} kWh unrealistic - using fallback register instead")
                    energy_today_addr = self._find_register_by_name('energy_today_low')
                    if energy_today_addr:
                        self._set_from_register(data, 'energy_today', energy_today_addr)
                        logger.debug(f"[{self.register_map['name']}@{self.connection_id}] Energy today from reg {energy_today_addr}: {data.energy_today} kWh")
            else:
                # Grid-tied profiles (MIC/MIN/MOD): energy_today register is solar-only, read directly
                energy_today_addr = self._find_register_by_name('energy_today_low')
                if energy_today_addr:
                    self._set_from_register(data, 'energy_today', energy_today_addr)
                    logger.debug(f"[{self.register_map['name']}@{self.connection_id}] Energy today from reg {energy_today_addr}: {data.energy_today} kWh (cache: {self._register_cache.get(energy_today_addr)})")

            # Energy Total — read directly from register; no override.
            # pv_energy_total (Epv) is a separate entity from energy_total (Eac).
            # On hybrids: Eac inflates with battery discharge; Epv is pure solar DC input.
            # On pure grid-tied: Eac is the correct total; Epv is slightly higher (~7% losses).
            # Both are exposed as distinct sensor entities — do not substitute one for the other.
            energy_total_addr = self._find_register_by_name('energy_total_low')
            if energy_total_addr:
                self._set_from_register(data, 'energy_total', energy_total_addr)
            
            # Energy Breakdown (if available)
            self._read_energy_breakdown(data)
            
            # Battery Data (if available - storage/hybrid models)
            self._read_battery_data(data)

            # Backup Box Data (Growatt ARK transfer switch, regs 3281-3342)
            self._read_backup_box_data(data)

            # Temperatures
            inverter_temp_addr = self._find_register_by_name('inverter_temp')
            ipm_temp_addr = self._find_register_by_name('ipm_temp')
            boost_temp_addr = self._find_register_by_name('boost_temp')
            
            if inverter_temp_addr:
                self._set_from_register(data, 'inverter_temp', inverter_temp_addr)
            if ipm_temp_addr:
                self._set_from_register(data, 'ipm_temp', ipm_temp_addr)
            if boost_temp_addr:
                self._set_from_register(data, 'boost_temp', boost_temp_addr)

            # SPF Off-Grid additional temperatures
            dcdc_temp_addr = self._find_register_by_name('dcdc_temp')
            buck1_temp_addr = self._find_register_by_name('buck1_temp')
            buck2_temp_addr = self._find_register_by_name('buck2_temp')

            if dcdc_temp_addr:
                self._set_from_register(data, 'dcdc_temp', dcdc_temp_addr)
            if buck1_temp_addr:
                self._set_from_register(data, 'buck1_temp', buck1_temp_addr)
            if buck2_temp_addr:
                self._set_from_register(data, 'buck2_temp', buck2_temp_addr)

            # SPF Off-Grid fan speeds
            mppt_fan_speed_addr = self._find_register_by_name('mppt_fan_speed')
            inverter_fan_speed_addr = self._find_register_by_name('inverter_fan_speed')

            if mppt_fan_speed_addr:
                self._set_from_register(data, 'mppt_fan_speed', mppt_fan_speed_addr)
            if inverter_fan_speed_addr:
                self._set_from_register(data, 'inverter_fan_speed', inverter_fan_speed_addr)

            # Diagnostics
            derating_addr = self._find_register_by_name('derating_mode')
            fault_addr = self._find_register_by_name('fault_code')
            warning_addr = self._find_register_by_name('warning_code')
            
            if derating_addr:
                data.derating_mode = int(self._get_register_value(derating_addr) or 0)
            if fault_addr:
                data.fault_code = int(self._get_register_value(fault_addr) or 0)
            if warning_addr:
                data.warning_code = int(self._get_register_value(warning_addr) or 0)

            # Insulation resistance, DC injection and leakage current (ISO/DCI/GFCI)
            for _attr, _reg in (
                ('pv_iso', 'pv_iso'),
                ('dci_r',  'dci_r'),
                ('dci_s',  'dci_s'),
                ('dci_t',  'dci_t'),
                ('gfci',   'gfci'),
            ):
                _a = self._find_register_by_name(_reg)
                if _a is not None:
                    _v = self._get_register_value(_a)
                    if _v is not None:
                        setattr(data, _attr, float(_v))

            # Dry Contact State (input reg 3119 — SPH/MIN TL-X/TL-XH)
            dry_contact_state_addr = self._find_register_by_name('dry_contact_state')
            if dry_contact_state_addr:
                data.dry_contact_state = int(self._get_register_value(dry_contact_state_addr) or 0)

            self._suppress_impossible_pv_zero(data)

            logger.debug(f"Read data: PV={data.pv_total_power}W, AC={data.ac_power}W, Battery={getattr(data, 'battery_soc', 'N/A')}%, Temp={data.inverter_temp}°C")
            
        except Exception as e:
            logger.error(f"Error parsing register data: {e}", exc_info=True)
            return None
        
        # Read device info from holding registers
        self._read_device_info(data)
        
        return data
    
    def _ensure_connection(self, tag: str) -> None:
        """Ensure Modbus client is initialized and socket is connected.

        Checks socket state and attempts reconnection if needed.
        Used by write_register() and write_registers() to avoid duplication.

        Args:
            tag: Log prefix for identifying the caller (e.g. "[WRITE]")

        Raises:
            ModbusWriteError: If client is not initialized or reconnection fails
        """
        if not self.client:
            raise ModbusWriteError(0, [], "Client not initialized")

        if hasattr(self.client, 'is_socket_open'):
            try:
                socket_is_open = self.client.is_socket_open()
                logger.debug(f"{tag} is_socket_open() returned: {socket_is_open}")

                if not socket_is_open:
                    logger.debug(f"{tag} Socket not open, attempting reconnect...")
                    if not self.connect():
                        raise ModbusWriteError(0, [], "Reconnect failed - not connected")
                    logger.info(f"{tag} Reconnect successful, proceeding with write")

            except ModbusWriteError:
                raise
            except Exception as e:
                logger.warning(f"{tag} is_socket_open() threw exception: {e}")
                logger.warning(f"{tag} Attempting reconnect due to error...")
                if not self.connect():
                    raise ModbusWriteError(0, [], "Reconnect failed after exception")
                logger.info(f"{tag} Reconnect successful after exception")
        else:
            logger.debug(f"{tag} Client has no is_socket_open(), attempting reconnect...")
            if not self.connect():
                raise ModbusWriteError(0, [], "Reconnect failed - cannot determine socket state")
            logger.info(f"{tag} Reconnect successful (no is_socket_open available)")

    @contextmanager
    def _bus(self, what: str = "bus operation"):
        """Hold the bus for the duration of the block.

        Returns the hub's lock when a shared connection is in use and the per-client lock
        otherwise, so both transports serialise the same way. Both are RLocks, so the
        nested acquisition inside the individual read/write methods re-enters rather than
        deadlocking.
        """
        from .const import SHARED_LOCK_TIMEOUT

        lock = (
            self._shared_conn._lock if self._shared_conn is not None
            else self._local_bus_lock
        )
        if not lock.acquire(timeout=SHARED_LOCK_TIMEOUT):
            raise ModbusWriteError(
                0, [], f"Modbus bus busy (lock timeout after {SHARED_LOCK_TIMEOUT}s on {what})"
            )
        try:
            yield
        finally:
            lock.release()

    @contextmanager
    def write_batch(self, what: str = "write sequence"):
        """Hold the shared bus for a sequence of writes that must not be interleaved.

        Some controls are not one register. The WIT VPP mode select writes six to eight —
        control authority, AC charge enable, a TOU period, the period count, remote enable,
        the power setpoint — and they only mean anything together. Each one used to take
        the shared lock separately, so a poll could land in the middle of the sequence and
        any single acquisition could time out, leaving the inverter with authority granted
        and no setpoint, or a TOU period with no count. A half-applied command is worse
        than one that plainly failed, and it is what drove one user to bypass the
        integration entirely (#331).

        Inside this block the bus is held from first write to last, so the sequence either
        lands complete or fails without having started.

        TWO CONSTRAINTS, both easy to get wrong:

        1. Everything inside must run on ONE thread. The lock is an RLock, and reentrancy
           is per-thread — so a sequence split across several executor jobs would deadlock
           against itself rather than nest. Call the whole sequence from a single
           hass.async_add_executor_job().
        2. Keep the block short. The poll waits on this same lock, so a long batch delays
           polling for every entity on the connection.

        It is NOT a no-op without a shared connection. That was the original shape, on the
        reasoning that a direct client owns its socket outright and has nothing to contend
        with — true when it was written, false since #398 gave the direct path a
        `_local_bus_lock` and made a whole poll hold it. With the no-op, each write inside
        the batch took and released that lock on its own, so a poll could land between two
        registers of the sequence, and a mid-sequence acquisition could time out with
        authority already granted and no setpoint written — exactly the half-applied
        command this method exists to prevent, reached on the one transport that was
        supposed to be exempt from it.

        Both locks are RLocks, so holding the local one here and re-entering it per write
        behaves identically to the shared path.
        """
        from .const import SHARED_LOCK_TIMEOUT

        lock = (
            self._shared_conn._lock if self._shared_conn is not None
            else self._local_bus_lock
        )
        scope = "shared" if self._shared_conn is not None else "local"
        if not lock.acquire(timeout=SHARED_LOCK_TIMEOUT):
            raise ModbusWriteError(
                0, [], f"Modbus bus busy (lock timeout on {what})"
            )
        try:
            logger.debug("[BATCH] Holding %s bus for %s", scope, what)
            yield
        finally:
            # Released even if a write inside raised. A leaked lock would stall every
            # subsequent poll on this connection — a worse failure than the one this
            # method exists to prevent.
            lock.release()
            logger.debug("[BATCH] Released %s bus after %s", scope, what)

    def write_register(self, register: int, value: int) -> bool:
        """Write, holding the bus for the transaction (#398)."""
        with self._bus("write"):
            return self._write_register_locked(register, value)

    def _write_register_locked(self, register: int, value: int) -> bool:
        """
        Write a single holding register.

        Args:
            register: Register address (relative to base address 0)
            value: Value to write (already scaled as integer)

        Returns:
            bool: True if write successful, False only for WIT rate limiting

        Raises:
            ModbusWriteError: If the write fails, with detailed error information
        """
        try:
            logger.debug(f"[WRITE] Request to write register {register} with value {value}")

            # WIT control rate limiting (v0.4.6) - prevent oscillation
            if register in self._wit_control_registers:
                import time
                current_time = time.time()
                last_write_time = self._wit_control_last_write.get(register, 0)
                time_since_last_write = current_time - last_write_time

                if time_since_last_write < self._wit_control_rate_limit_seconds:
                    remaining = self._wit_control_rate_limit_seconds - time_since_last_write
                    logger.warning(
                        f"[WIT CTRL] Rate limit: Register {register} write blocked. "
                        f"Must wait {remaining:.1f}s more (30s cooldown between WIT control writes). "
                        f"See docs/WIT_CONTROL_GUIDE.md for details."
                    )
                    return False

                logger.debug(f"[WIT CTRL] Rate limit check passed for register {register}")

            # Shared connection path — acquire hub lock, delegate to hub
            if self._shared_conn is not None:
                from .const import SHARED_LOCK_TIMEOUT
                acquired = self._shared_conn._lock.acquire(timeout=SHARED_LOCK_TIMEOUT)
                if not acquired:
                    raise ModbusWriteError(register, [value], "Shared connection busy (lock timeout on write)")
                try:
                    if not self._shared_conn.ensure_connected():
                        raise ModbusWriteError(register, [value], "Could not connect to shared Modbus gateway")
                    success = self._shared_conn.write_register(register, value, self.slave_id)
                finally:
                    self._shared_conn._lock.release()
                if not success:
                    raise ModbusWriteError(register, [value], "Shared connection write_register returned error")
                logger.info(f"[WRITE] Successfully wrote value {value} → register {register} (shared conn)")
                if register in self._wit_control_registers:
                    self._wit_control_last_write[register] = time.time()
                    self._check_wit_control_conflicts(register, value)
                return True

            self._ensure_connection("[WRITE]")

            # ---- Perform actual write ---------------------------------------------
            # Modbus FC06 requires an unsigned 16-bit value; convert signed Python int
            if value < 0:
                value = value & 0xFFFF
            logger.debug(f"[WRITE] Sending write_register({register}, {value}) to inverter")

            # Try different keyword arguments for pymodbus version compatibility
            result = None
            try:
                # Preferred for ModbusTcpClient / recent pymodbus
                result = self.client.write_register(address=register, value=value, unit=self.slave_id)
            except TypeError:
                try:
                    # Some versions use 'slave'
                    result = self.client.write_register(address=register, value=value, slave=self.slave_id)
                except TypeError:
                    try:
                        # Older/newer variants may accept 'device_id'
                        result = self.client.write_register(address=register, value=value, device_id=self.slave_id)
                    except TypeError:
                        # Fallback: positional args only
                        result = self.client.write_register(register, value)

            # Handle different pymodbus error APIs
            if result is None:
                error_msg = "No response from inverter"
                logger.error(f'[WRITE] {error_msg}')
                raise ModbusWriteError(register, [value], error_msg)

            if hasattr(result, 'isError') and callable(getattr(result, 'isError')) and result.isError():
                error_msg = _format_modbus_error(result)
                logger.error(f"[WRITE] Inverter responded with error: {error_msg}")
                raise ModbusWriteError(register, [value], error_msg)

            logger.info(f"[WRITE] Successfully wrote value {value} → register {register}")

            # Update WIT cooldown timestamp only after confirmed successful write (F-005)
            if register in self._wit_control_registers:
                import time
                self._wit_control_last_write[register] = time.time()
                self._check_wit_control_conflicts(register, value)

            return True
            # -----------------------------------------------------------------------

        except ModbusWriteError:
            raise  # Re-raise our custom exceptions
        except Exception as e:
            error_msg = f"Exception: {type(e).__name__}: {e}"
            logger.error(f"[WRITE] {error_msg}")
            raise ModbusWriteError(register, [value], error_msg)

    def write_single_register_any_fc(self, register: int, value: int) -> bool:
        """Write one register, falling back to FC 0x10 when FC 0x06 is refused.

        Some VPP registers accept only Write Multiple Registers, even for a single value.
        30410 (VPP AC charge enable) is the reported case: on a WIT 8000TL3-HU it rejects
        FC 0x06 and accepts FC 0x10 with count=1 (#353).

        That mattered more than a rejected write usually does, because the caller logged a
        warning and carried on. Every other register in the mode sequence succeeded, so grid
        charging silently never engaged while the control reported success.

        FC 0x06 is tried first deliberately. It is what the rest of the integration uses and
        what most hardware expects; switching everything to FC 0x10 would risk the opposite
        failure on devices that only accept the single-register form. This only adds a second
        attempt where the first is refused outright, so it cannot make a working write worse.
        """
        try:
            if self.write_register(register, value):
                return True
            logger.debug(
                "[FC FALLBACK] register %d refused FC 0x06 (no exception) — trying FC 0x10",
                register,
            )
        except Exception as exc:  # noqa: BLE001
            logger.debug(
                "[FC FALLBACK] register %d raised on FC 0x06 (%s) — trying FC 0x10",
                register, exc,
            )

        try:
            if self.write_registers(register, [value]):
                logger.info(
                    "[FC FALLBACK] register %d accepted FC 0x10 after refusing FC 0x06",
                    register,
                )
                return True
        except Exception as exc:  # noqa: BLE001
            logger.debug("[FC FALLBACK] register %d also refused FC 0x10: %s", register, exc)

        return False

    def write_register_verified(self, register: int, value: int) -> tuple:
        """Write a holding register with read-back verification and retry.

        After each write, reads the register back to confirm the value stuck.
        If the read-back differs, retries up to WRITE_VERIFY_MAX_RETRIES times.
        Reversion can be caused by a ShineWiFi/cloud override, inverter firmware
        rejecting the value, or another controller on the bus.

        Returns:
            tuple of (write_success: bool, value_verified: bool):
            - (True, True)   — write succeeded and read-back confirmed
            - (True, False)  — write succeeded but read-back differs (value reverted)
            - (False, False) — write itself failed (Modbus error)
        """
        # ONE write, then read until it settles. Never re-write.
        #
        # This used to write, wait 0.5 s, read, and write again on a mismatch - up to three
        # times. On an inverter that commits slowly the read-back returns the *previous*
        # value, which is indistinguishable from a reversion, so every write was re-issued
        # two more times for no reason. A reporter dragging a slider produced this on an
        # SPF 6000, each read-back showing the value from the write before it (#402).
        #
        # That is the wrong response twice over. The Modbus write already succeeded - the
        # inverter acknowledged it - so re-writing is speculative, and these registers are
        # likely EEPROM-backed (#392), so it spends a write cycle to learn nothing. A
        # genuine cloud override re-reverts anyway and the extra writes do not win the
        # race; a genuine firmware rejection is deterministic and will refuse them all.
        #
        # So the read-back is now purely diagnostic: write once, then poll the register
        # with a growing delay until it either matches or the budget runs out.
        try:
            self.write_register(register, value)
        except ModbusWriteError:
            raise

        expected = value & 0xFFFF
        delay = WRITE_VERIFY_DELAY
        last_seen = None

        for attempt in range(WRITE_VERIFY_MAX_RETRIES):
            time.sleep(delay)

            read_back = self.read_holding_registers(register, 1)
            if read_back is None:
                logger.debug(
                    "[WRITE VERIFY] Could not read back register %d (comm error) - "
                    "treating as unverifiable", register,
                )
                return (True, True)  # Don't fail the write on a read error

            last_seen = read_back[0]
            if last_seen == expected:
                if attempt:
                    logger.debug(
                        "[WRITE VERIFY] Register %d settled to %d after %.1f s - this "
                        "inverter commits slowly, which is normal",
                        register, value, delay * attempt,
                    )
                else:
                    logger.debug("[WRITE VERIFY] Register %d verified (value=%d)", register, value)
                return (True, True)

            # Not there yet. Give it longer before looking again rather than writing again.
            delay = min(delay * 2, WRITE_VERIFY_MAX_DELAY)

        # Never settled. The write was accepted at the Modbus level and the register still
        # does not hold it, which is the silent-rejection case (#400) or an override.
        logger.warning(
            "[WRITE VERIFY] Register %d: wrote %d, still reads %s after %d checks. The "
            "write was accepted but the value did not stick. Either the inverter firmware "
            "rejected it silently - some models discard out-of-range SOC limits and "
            "voltages this way - the Growatt cloud overwrote it, or a prerequisite "
            "register is not set. No further write was attempted.",
            register, value, last_seen, WRITE_VERIFY_MAX_RETRIES,
        )
        return (True, False)

    def write_registers(self, register: int, values: list) -> bool:
        """Write, holding the bus for the transaction (#398)."""
        with self._bus("write"):
            return self._write_registers_locked(register, values)

    def _write_registers_locked(self, register: int, values: list) -> bool:
        """
        Write multiple consecutive holding registers (Modbus function 0x10).

        Required for atomic multi-register writes such as TOU period configuration
        where all registers (start, end, power) must be written together.

        Note: WIT control rate limiting is intentionally not applied here.
        This method is for TOU period configuration, not WIT control registers
        which use single-register writes via write_register().

        Args:
            register: Starting register address
            values: List of integer values to write to consecutive registers

        Returns:
            bool: True if write successful

        Raises:
            ModbusWriteError: If the write fails, with detailed error information
        """
        try:
            logger.debug(f"[WRITE_MULTI] Request to write {len(values)} registers starting at {register}: {values}")

            if not values:
                raise ModbusWriteError(register, values, "Cannot write empty values list")

            # Shared connection path — acquire hub lock, delegate to hub
            if self._shared_conn is not None:
                from .const import SHARED_LOCK_TIMEOUT
                acquired = self._shared_conn._lock.acquire(timeout=SHARED_LOCK_TIMEOUT)
                if not acquired:
                    raise ModbusWriteError(register, values, "Shared connection busy (lock timeout on write_registers)")
                try:
                    if not self._shared_conn.ensure_connected():
                        raise ModbusWriteError(register, values, "Could not connect to shared Modbus gateway")
                    success = self._shared_conn.write_registers(register, values, self.slave_id)
                finally:
                    self._shared_conn._lock.release()
                if not success:
                    raise ModbusWriteError(register, values, "Shared connection write_registers returned error")
                logger.info(f"[WRITE_MULTI] Successfully wrote {len(values)} registers starting at {register} (shared conn)")
                return True

            self._ensure_connection("[WRITE_MULTI]")

            # ---- Perform actual write (function 0x10) -----------------------------
            logger.debug(f"[WRITE_MULTI] Sending write_registers({register}, {values}) to inverter")

            result = None
            try:
                result = self.client.write_registers(address=register, values=values, unit=self.slave_id)
            except TypeError:
                try:
                    result = self.client.write_registers(address=register, values=values, slave=self.slave_id)
                except TypeError:
                    try:
                        result = self.client.write_registers(address=register, values=values, device_id=self.slave_id)
                    except TypeError:
                        result = self.client.write_registers(register, values)

            # Handle different pymodbus error APIs
            if result is None:
                error_msg = "No response from inverter"
                logger.error(f'[WRITE_MULTI] {error_msg}')
                raise ModbusWriteError(register, values, error_msg)

            if hasattr(result, 'isError') and callable(getattr(result, 'isError')) and result.isError():
                error_msg = _format_modbus_error(result)
                logger.error(f"[WRITE_MULTI] Inverter responded with error: {error_msg}")
                raise ModbusWriteError(register, values, error_msg)

            logger.info(f"[WRITE_MULTI] Successfully wrote {len(values)} values → registers {register}-{register + len(values) - 1}")
            return True
            # -----------------------------------------------------------------------

        except ModbusWriteError:
            raise  # Re-raise our custom exceptions
        except Exception as e:
            error_msg = f"Exception: {type(e).__name__}: {e}"
            logger.error(f"[WRITE_MULTI] {error_msg}")
            raise ModbusWriteError(register, values, error_msg)

    # ------------------------------------------------------------------
    # Inverter real-time clock — holding registers 45-51 (#393)
    # ------------------------------------------------------------------
    #
    # Protocol V1.39 documents the block as writable:
    #
    #   45 Sys Year | 46 Sys Month | 47 Sys Day
    #   48 Sys Hour | 49 Sys Min   | 50 Sys Sec  | 51 Sys Weekly
    #
    # Confirmed on hardware from two unrelated device classes. An SPH 3600 scan read
    # 2026/8/22 14:08:19 with weekday 6 — 22 August 2026 was a Saturday, so the weekday
    # field counts Monday as 1. A GroHomeManager-X (DTC 82) on a different site read
    # 2026/8/22 09:42:17 in the same registers. The year is the full four digits, not an
    # offset.
    #
    # NOT off-grid. The off-grid protocol puts the clock at the same addresses but records
    # "Year offset is 2000" and gives register 51 to Chip Select rather than a weekday, so
    # writing this block unchanged to an SPF would set the year wrong and overwrite an
    # unrelated register. No SPF scan has been offered to confirm the encoding, and guessing
    # at a clock write is not worth the risk — see is_clock_supported().
    CLOCK_REGISTER_START = 45
    CLOCK_REGISTER_COUNT = 7  # 45-51 inclusive

    # Pacing between the six single-register clock writes. The reference implementation
    # spaces them by 200 ms; these registers are committed individually and are not a
    # burst target.
    CLOCK_WRITE_INTERVAL = 0.2

    # How far the read-back may differ before it is reported. Six paced writes take about a
    # second, and the seconds field is written first-to-last, so the clock legitimately
    # lands a little behind the value asked for.
    CLOCK_VERIFY_TOLERANCE = 5.0

    # Worst-case wall time for the six paced writes including Modbus round-trips. Used
    # only to keep the sequence off a minute boundary; being generous here costs at most
    # this many seconds of waiting, and only on a sync that starts late in a minute.
    CLOCK_WRITE_BUDGET = 6.0

    @property
    def is_clock_supported(self) -> bool:
        """Whether this profile's clock encoding is confirmed."""
        return not self.register_map.get('offgrid_protocol', False)

    def read_inverter_time(self) -> Optional[datetime]:
        """Read the inverter's real-time clock, or None if it cannot be decoded."""
        if not self.is_clock_supported:
            return None

        regs = self.read_holding_registers(self.CLOCK_REGISTER_START, self.CLOCK_REGISTER_COUNT)
        if not regs or len(regs) < 6:
            logger.debug("[CLOCK] Could not read registers %d-%d",
                         self.CLOCK_REGISTER_START, self.CLOCK_REGISTER_START + 5)
            return None

        year, month, day, hour, minute, second = (int(v) for v in regs[:6])

        # Two conventions in the wild for the same register. Most V1.39 devices read back a
        # full four-digit year; some store it as an offset from 2000, which the off-grid
        # protocol documents explicitly. Without this a "26" would decode as the year 26 AD
        # and the drift would come out as two millennia (#393).
        if 0 <= year < 100:
            year += 2000

        try:
            return datetime(year, month, day, hour, minute, second)
        except ValueError as err:
            # A freshly reset or unconfigured inverter can hold zeroes or nonsense here.
            # Returning None rather than raising lets the caller still set the clock.
            logger.debug(
                "[CLOCK] Registers %d-%d do not form a valid date (%s): %s",
                self.CLOCK_REGISTER_START, self.CLOCK_REGISTER_START + 5, list(regs[:6]), err,
            )
            return None

    def write_inverter_time(self, when: datetime) -> bool:
        """Set the inverter's real-time clock.

        Follows the method in a published, working ESP32 implementation for an SPH5000
        (cosminpop.uk, Feb 2026), corroborated by an ESPHome forum finding three years
        earlier and by two failures on this tracker:

        **The year is written as `year - 2000`, and read back as the full four digits.**
        Write 26, read 2026. That asymmetry is the whole problem — it is not in either
        protocol document for the V1.39 range, and an earlier version of this method
        detected the format by reading the register, which can only ever produce the
        four-digit form and therefore always wrote a value the inverter rejects (#393).

        Each field is written on its own with FC 0x06, spaced apart, in the reference's
        order. Its author notes that settings registers on that hardware generally need
        FC 0x10 and answer FC 0x06 with Illegal Function, but that the RTC block at 45-50
        is an exception and does take single writes.

        The year goes first on purpose. It is the field observed to fail, so a refusal
        leaves the clock untouched rather than half-written — a MIN TL-X reset its RTC to
        the year 2000 when five fields landed and the year did not.
        """
        if not self.is_clock_supported:
            raise ModbusWriteError(
                self.CLOCK_REGISTER_START, [],
                "clock sync is not supported on off-grid profiles — register 51 carries "
                "Chip Select there rather than a weekday, and no scan has confirmed the "
                "rest of the block (#393)",
            )

        # Seconds is written last, roughly 1.2-1.5 s after the first field on TCP and
        # longer on a slow gateway. Writing `when.second` therefore lands the clock that
        # far behind: a reporter measured a consistent 1.4-1.6 s residual immediately
        # after every sync, which was this and not his inverter (#393). The seconds value
        # is computed at the moment it is written instead, from elapsed monotonic time.
        #
        # That compensation can only push seconds forward, so it must never cross a minute
        # boundary - the minute has already been written by then. If there is not room in
        # the current minute, wait for the next one and start there.
        if when.second + self.CLOCK_WRITE_BUDGET >= 60:
            wait = 60 - when.second
            logger.debug(
                "[CLOCK] Starting %.0f s late in the minute; waiting for the next one so "
                "the write cannot cross the boundary", when.second,
            )
            time.sleep(wait)
            when = when + timedelta(seconds=wait)

        # Year first, and as an offset. Seconds is a placeholder - see below.
        fields = [
            (self.CLOCK_REGISTER_START,     when.year - 2000, "year"),
            (self.CLOCK_REGISTER_START + 1, when.month,       "month"),
            (self.CLOCK_REGISTER_START + 2, when.day,         "day"),
            (self.CLOCK_REGISTER_START + 3, when.hour,        "hour"),
            (self.CLOCK_REGISTER_START + 4, when.minute,      "minute"),
            (self.CLOCK_REGISTER_START + 5, when.second,      "second"),
        ]

        logger.info(
            "[CLOCK] Setting inverter clock to %s (year written as %d)",
            when.strftime("%Y-%m-%d %H:%M:%S"), when.year - 2000,
        )

        started = time.monotonic()

        for index, (register, value, label) in enumerate(fields):
            if index:
                # The reference paces its writes; these registers are not a burst target
                # and the inverter has to commit each one.
                time.sleep(self.CLOCK_WRITE_INTERVAL)

            if label == "second":
                # How long the five preceding writes actually took, rather than an
                # assumption about it - a LoRa bridge is far slower than TCP.
                value = when.second + int(round(time.monotonic() - started))

            if self.write_single_register_any_fc(register, value):
                continue

            if index == 0:
                raise ModbusWriteError(
                    register, [value],
                    f"the inverter refused register {register} (year, written as "
                    f"{value}). Nothing else was written, so the clock is exactly as it "
                    f"was. This model may not allow its clock to be set over Modbus.",
                )

            raise ModbusWriteError(
                register, [value],
                f"register {register} ({label}) was refused after the year had already "
                f"been written, so the clock is now part-updated. Check it in the Growatt "
                f"app.",
            )

        self._verify_clock_write(when)
        return True

    def _verify_clock_write(self, intended: datetime) -> None:
        """Read the clock back and complain if it does not match.

        Compares against the four-digit year, because that is what the register reports
        regardless of the two-digit value used to set it.

        Advisory only — the write has already happened. This exists because a write can be
        acknowledged and quietly discarded, which is how a MIN TL-X reported success for a
        year it never stored.
        """
        actual = self.read_inverter_time()
        if actual is None:
            logger.debug("[CLOCK] Could not read the clock back to verify it")
            return

        drift = abs((actual - intended).total_seconds())
        if drift > self.CLOCK_VERIFY_TOLERANCE:
            logger.warning(
                "[CLOCK] The inverter did not store what was written: asked for %s, reads "
                "%s. The clock may be wrong — check it in the Growatt app before relying "
                "on time-based schedules.",
                intended.strftime("%Y-%m-%d %H:%M:%S"),
                actual.strftime("%Y-%m-%d %H:%M:%S"),
            )
        else:
            logger.info("[CLOCK] Verified: inverter now reads %s",
                        actual.strftime("%Y-%m-%d %H:%M:%S"))


    def _check_wit_control_conflicts(self, register: int, value: int) -> None:
        """
        Check for potential WIT control conflicts (v0.4.6 - Issue #143).

        Detects situations that may cause unstable control behavior:
        - Multiple VPP remote control registers active simultaneously
        - Conflicting control commands within short time windows
        - Potential TOU vs remote control conflicts

        Args:
            register: The register that was just written
            value: The value that was written
        """
        try:
            # Check for multiple active VPP remote controls
            active_controls = []

            # Check if remote power control is being enabled
            if register == 30407 and value == 1:
                active_controls.append("Remote Power Control (30407)")

                # Check if control authority is also enabled
                control_authority = self._register_cache.get(30100, 0)
                if control_authority == 1:
                    active_controls.append("Control Authority (30100)")

            # Check for legacy VPP controls being active
            if register == 202:  # work_mode
                if value > 0:  # 1=charge, 2=discharge
                    active_controls.append(f"Legacy Work Mode (202={value})")

            # Warn if multiple control mechanisms are active
            if len(active_controls) > 1:
                logger.warning(
                    f"[WIT CTRL] Multiple control mechanisms active simultaneously: {', '.join(active_controls)}. "
                    f"This may cause conflicts. See docs/WIT_CONTROL_GUIDE.md for recommended patterns."
                )

            # Detect potential TOU conflicts when enabling remote control
            if register == 30407 and value == 1:
                # Check if any TOU periods are enabled (registers 954, 957, 960, 963, 966, 969)
                tou_enabled_registers = [954, 957, 960, 963, 966, 969]
                tou_periods_active = False

                for tou_reg in tou_enabled_registers:
                    if tou_reg in self._register_cache:
                        # Bit 15 indicates if period is enabled
                        tou_value = self._register_cache[tou_reg]
                        if tou_value & 0x8000:  # Check bit 15
                            tou_periods_active = True
                            break

                if tou_periods_active:
                    logger.warning(
                        f"[WIT CTRL] Remote power control enabled while TOU periods are configured. "
                        f"TOU schedule may override remote commands during scheduled periods. "
                        f"Consider disabling TOU via inverter panel if full remote control is needed."
                    )

        except Exception as e:
            # Don't fail the write if conflict detection has issues
            logger.debug(f"[WIT CTRL] Conflict detection error (non-critical): {e}")

    def _find_register_by_name(self, name: str) -> Optional[int]:
        """Find register address by its name, alias, or maps_to attribute.

        Searches input_registers for a matching register using three strategies:
        1. Exact name match - standard register lookup
        2. Alias match - for 3-phase registers that alias single-phase names
        3. maps_to match - for VPP registers that map to standard sensor names
           (e.g., a VPP register with maps_to='grid_power' resolves when
           looking up 'grid_power')
        """
        input_regs = self.register_map['input_registers']
        for addr, reg_info in input_regs.items():
            if reg_info['name'] == name:
                return addr
            if reg_info.get('alias') == name:
                return addr
            if reg_info.get('maps_to') == name:
                return addr
        return None

    def _resolve_phase_total(self, data, attr: str, total_name: str,
                             phase_names: tuple = ()) -> None:
        """Whole-service value for a quantity the inverter also reports per phase.

        V1.39 lays the storage power-flow range out as R / S / T / Total. Grid import was
        read from `PactouserR` - **one phase** - because on the single-phase hardware it was
        first mapped against, R and Total are the same measurement and the choice was
        invisible. On a three-phase SPH it reports a third of the truth, and on a US
        split-phase HU, half (#419).

        The total is now the primary source. It is not blindly trusted, because we have
        never confirmed 1021 populates on every firmware while we know 1015 does on at
        least one device - so a swap alone could take working users to zero:

            total > 0            -> total          the firmware fills it; authoritative
            sum(phases) > 0      -> sum(phases)    the firmware fills only per-phase
            otherwise            -> 0              genuinely nothing flowing

        **A zero total is never accepted while the phases carry real values.** A zero there
        is a register the firmware does not populate, not a measurement, and publishing it
        would repeat #228 - a plausible number that means nothing.

        Summing rather than preferring R costs nothing and needs no knowledge of the phase
        count: on single-phase, S and T read zero and the sum *is* R.

        Three states, not two. A phase that failed to read is not a phase reading zero, so
        a partial sum is withheld rather than published as a confidently wrong number.
        Quantities with no phase registers mapped degrade to total-only, which is what
        export and load do today.
        """
        addresses = self._find_all_registers_by_name(total_name)
        if not addresses:
            return

        total = None
        for addr in addresses:
            candidate = self._get_register_value(addr)
            if candidate is None:
                continue
            if total is None:
                total = candidate
            if candidate != 0.0:
                total = candidate
                break

        if total:
            setattr(data, attr, total)
            return

        phase_sum = 0.0
        any_phase_mapped = False
        for phase_name in phase_names:
            phase_addr = self._find_register_by_name(phase_name)
            if phase_addr is None:
                continue
            any_phase_mapped = True
            value = self._get_register_value(phase_addr)
            if value is None:
                # Unread, not zero. Summing what did arrive would understate the total.
                data.unread_fields.add(attr)
                logger.debug(
                    "%s: %s did not read this poll and the total is %s - reporting nothing "
                    "rather than a partial sum", attr, phase_name,
                    "zero" if total is not None else "unavailable",
                )
                return
            phase_sum += value

        if any_phase_mapped and phase_sum:
            logger.debug(
                "%s: total register read %s but the phases sum to %.1f W - the firmware "
                "does not populate the total on this device, using the sum",
                attr, "0" if total is not None else "nothing", phase_sum,
            )
            setattr(data, attr, phase_sum)
            return

        setattr(data, attr, total if total is not None else 0.0)

    def _find_all_registers_by_name(self, name: str) -> list[int]:
        """Find ALL register addresses matching a name, alias, or maps_to attribute.

        Returns a list of all matching addresses, sorted by preference:
        1. Fallback ranges first (1000-1999, 3000-3999)
        2. VPP ranges last (31000+)

        This allows smart fallback when VPP registers return zero but fallback registers have valid data.
        """
        input_regs = self.register_map['input_registers']
        matches = []

        for addr, reg_info in input_regs.items():
            if (reg_info['name'] == name or
                reg_info.get('alias') == name or
                reg_info.get('maps_to') == name):
                matches.append(addr)

        # Sort by priority: fallback ranges (1000-3999) before VPP (31000+)
        def register_priority(addr):
            if 1000 <= addr < 4000:  # Fallback ranges
                return 0
            elif addr >= 31000:  # VPP range
                return 1
            else:  # Other ranges
                return 2

        matches.sort(key=register_priority)
        return matches

    def _detect_battery_register_range(self) -> str:
        """Detect which register range contains valid battery data (VPP vs fallback).

        Checks multiple key battery sensors to determine if VPP (31000+) or
        fallback (1000+/3000+) registers contain the active data. This ensures
        consistent register usage across all battery sensors.

        Returns:
            'vpp', 'fallback', 'legacy', or 'unknown'
        """
        if self._battery_range_detected:
            return self._battery_register_range

        # SPF off-grid inverters use legacy 0-97 range only — skip VPP/fallback detection
        # (Issue #204: range scoring only covers 1000-3999 and 31000+, so SPF registers
        # at 0-97 always scored 0 and defaulted to 'fallback', filtering out register 17)
        if self.register_map.get('offgrid_protocol', False):
            self._battery_register_range = 'legacy'
            self._battery_range_detected = True
            logger.debug("Battery register range: legacy (0-999) — offgrid_protocol=True")
            return 'legacy'

        # Key sensors to check for valid data (non-zero indicates active range)
        # Include both naming conventions: battery_*_today_low (most profiles) and
        # discharge_energy_today_low / charge_energy_today_low (SPH TL3 profile)
        test_sensors = [
            'battery_voltage',
            'battery_soc',
            'battery_power_low',
            'battery_discharge_today_low',
            'battery_charge_today_low',
            'discharge_energy_today_low',
            'charge_energy_today_low',
        ]

        vpp_score = 0
        fallback_score = 0

        for sensor_name in test_sensors:
            addresses = self._find_all_registers_by_name(sensor_name)

            for addr in addresses:
                value = self._register_cache.get(addr)
                if value is not None and value > 0:
                    # This register has valid data
                    if addr >= 31000:
                        vpp_score += 1
                        logger.debug(f"VPP range active for {sensor_name}: reg {addr} = {value}")
                    elif 8000 <= addr < 9000:
                        # WIT 8000-range is a native battery range equivalent to VPP
                        vpp_score += 1
                        logger.debug(f"WIT 8000-range active for {sensor_name}: reg {addr} = {value}")
                    elif 1000 <= addr < 4000:
                        fallback_score += 1
                        logger.debug(f"Fallback range active for {sensor_name}: reg {addr} = {value}")

        # Determine winner
        if vpp_score > fallback_score:
            self._battery_register_range = 'vpp'
            logger.info(f"Battery register range detected: VPP (31000+) - VPP score: {vpp_score}, Fallback score: {fallback_score}")
        elif fallback_score > 0:
            self._battery_register_range = 'fallback'
            logger.info(f"Battery register range detected: Fallback (1000-3999) - VPP score: {vpp_score}, Fallback score: {fallback_score}")
        else:
            # Both ranges are zero - default to fallback (more universal)
            self._battery_register_range = 'fallback'
            logger.info(f"Battery register range detected: Fallback (default) - All sensors zero or unavailable")

        self._battery_range_detected = True
        return self._battery_register_range

    def _find_register_by_name_with_fallback(self, name: str) -> Optional[int]:
        """Find register address by name, respecting detected battery register range.

        Similar to _get_register_value_with_fallback() but returns the address instead of the value.
        This is useful when we need the address for debugging or accessing paired registers.

        Args:
            name: The register name to look up (e.g., 'charge_power_low')

        Returns:
            The register address in the preferred range, or None if not found
        """
        addresses = self._find_all_registers_by_name(name)

        if not addresses:
            return None

        # Detect which register range to use (only done once per session)
        preferred_range = self._detect_battery_register_range()

        # Filter addresses by preferred range
        if preferred_range == 'vpp':
            # Prefer VPP range (31000+), then WIT 8000-range (native battery range with no VPP counterpart)
            preferred_addrs = [a for a in addresses if a >= 31000]
            if not preferred_addrs:
                # Also check 8000-range (WIT extended battery registers with no VPP counterpart, e.g. battery_current at 8035)
                preferred_addrs = [a for a in addresses if 8000 <= a < 9000]
                if not preferred_addrs:
                    # Register doesn't exist in VPP or 8000 range - return None to trigger fallback logic
                    return None
        elif preferred_range == 'legacy':
            # Off-grid/SPF: registers in base range 0-999 (Issue #204)
            preferred_addrs = [a for a in addresses if a < 1000]
            if not preferred_addrs:
                # Also check 8000-range as secondary for any legacy models that use it
                preferred_addrs = [a for a in addresses if 8000 <= a < 9000]
                if not preferred_addrs:
                    return None
        else:  # 'fallback' or 'unknown'
            # Prefer fallback range (1000-3999), strict - no fallback
            preferred_addrs = [a for a in addresses if 1000 <= a < 4000]
            if not preferred_addrs:
                # Also check 8000-range as secondary
                preferred_addrs = [a for a in addresses if 8000 <= a < 9000]
                if not preferred_addrs:
                    # Register doesn't exist in fallback range - return None to trigger alternative registers
                    return None

        # Return the first address from preferred range
        return preferred_addrs[0]

    def _get_register_value_with_fallback(self, name: str) -> Optional[float]:
        """Get register value using detected battery register range preference.

        When both VPP (31000+) and fallback (1000+/3000+) registers exist for the same sensor:
        1. On first call, detect which range has valid data by checking multiple key sensors
        2. Use the detected range consistently for all subsequent reads
        3. This prevents mixing VPP and fallback values and handles legitimate zeros correctly

        Args:
            name: The register name to look up (e.g., 'battery_discharge_today_low')

        Returns:
            The scaled register value, or None if no valid value found
        """
        addr = self._find_register_by_name_with_fallback(name)

        if addr is None:
            return None

        value = self._get_register_value(addr)
        preferred_range = self._battery_register_range

        if value is not None:
            logger.debug(f"Using {preferred_range} range register {addr} for '{name}': {value}")

        return value

    def _read_energy_breakdown(self, data: GrowattData) -> None:
        """Read detailed energy breakdown (storage/hybrid models)"""
        try:
            # Energy to user
            addr = self._find_register_by_name('energy_to_user_today_low')
            if addr:
                self._set_from_register(data, 'energy_to_user_today', addr)
            
            addr = self._find_register_by_name('energy_to_user_total_low')
            if addr:
                self._set_from_register(data, 'energy_to_user_total', addr)
            
            # Energy to grid
            # Prefer 32-bit pair (_low suffix); fall back to standalone single register.
            # SPE uses a single 16-bit register for today (Protocol V0.26 reg 45).
            addr = self._find_register_by_name('energy_to_grid_today_low') or \
                   self._find_register_by_name('energy_to_grid_today')
            if addr:
                self._set_from_register(data, 'energy_to_grid_today', addr)

            addr = self._find_register_by_name('energy_to_grid_total_low')
            if addr:
                self._set_from_register(data, 'energy_to_grid_total', addr)
            
            # Load energy
            addr = self._find_register_by_name('load_energy_today_low')
            if addr:
                self._set_from_register(data, 'load_energy_today', addr)
                logger.debug(f"[{self.register_map['name']}@{self.connection_id}] Load energy today from reg {addr}: {data.load_energy_today} kWh (cache: {self._register_cache.get(addr)})")
            else:
                logger.debug(f"[{self.register_map['name']}@{self.connection_id}] load_energy_today_low register not found (expected for off-grid models like SPF)")

            addr = self._find_register_by_name('load_energy_total_low')
            if addr:
                self._set_from_register(data, 'load_energy_total', addr)
                logger.debug(f"[{self.register_map['name']}@{self.connection_id}] Load energy total from reg {addr}: {data.load_energy_total} kWh (cache: {self._register_cache.get(addr)})")

            # Operational discharge energy (SPF off-grid models)
            addr = self._find_register_by_name('op_discharge_energy_today_low')
            if addr:
                self._set_from_register(data, 'op_discharge_energy_today', addr)
                logger.debug(f"[{self.register_map['name']}@{self.connection_id}] Operational discharge energy today from reg {addr}: {data.op_discharge_energy_today} kWh (cache: {self._register_cache.get(addr)})")

            addr = self._find_register_by_name('op_discharge_energy_total_low')
            if addr:
                self._set_from_register(data, 'op_discharge_energy_total', addr)
                logger.debug(f"[{self.register_map['name']}@{self.connection_id}] Operational discharge energy total from reg {addr}: {data.op_discharge_energy_total} kWh (cache: {self._register_cache.get(addr)})")

            # AC Discharge Energy (SPF off-grid models - battery to load via inverter)
            addr = self._find_register_by_name('ac_discharge_energy_today_low')
            if addr:
                self._set_from_register(data, 'ac_discharge_energy_today', addr)
                logger.debug(f"[{self.register_map['name']}@{self.connection_id}] AC discharge energy today from reg {addr}: {data.ac_discharge_energy_today} kWh (cache: {self._register_cache.get(addr)})")

            addr = self._find_register_by_name('ac_discharge_energy_total_low')
            if addr:
                self._set_from_register(data, 'ac_discharge_energy_total', addr)
                logger.debug(f"[{self.register_map['name']}@{self.connection_id}] AC discharge energy total from reg {addr}: {data.ac_discharge_energy_total} kWh (cache: {self._register_cache.get(addr)})")

        except Exception as e:
            logger.debug(f"Energy breakdown not available: {e}")
    
    def _read_battery_data(self, data: GrowattData) -> None:
        """Read battery data (storage/hybrid models)"""
        try:
            # Battery voltage
            # Issue #247: on some WIT firmware variants, VPP register 31214 (maps_to='battery_voltage')
            # reports a spuriously low value (e.g. 5.2 V) while the native 8034 register is correct
            # (53.7 V). Apply the same multi-candidate / largest-plausible-value strategy used for
            # battery_current: read all available voltage registers, discard implausibly low values,
            # and pick the highest (most likely correct) reading.
            _VOLTAGE_LOOKUP_NAMES = (
                'battery_voltage',       # native 8000-range or VPP maps_to (e.g. WIT 8034 / 31214)
                'battery_voltage_bms',   # BMS voltage (WIT-only, typically more accurate)
                'battery_voltage_legacy',
            )
            _VOLTAGE_MIN_V = 10.0    # below this is implausible for any connected battery pack
            _VOLTAGE_MAX_V = 1100.0  # MOD TL3-XH HV batteries operate up to 950V
            _bvr = self._battery_voltage_range

            seen_voltage_addrs: set = set()
            voltage_candidates: list = []
            for _vname in _VOLTAGE_LOOKUP_NAMES:
                # Use _find_all_registers_by_name to get EVERY address for this name
                # (including maps_to matches across all ranges). Previously only one
                # address was returned (the preferred-range winner), so when the VPP range
                # was preferred the native 8000-range register was never evaluated as a
                # candidate — meaning the spurious VPP value was never compared against
                # the correct native value. (Issue #247 root cause)
                for _a in self._find_all_registers_by_name(_vname):
                    if _a not in seen_voltage_addrs:
                        seen_voltage_addrs.add(_a)
                        _v = self._get_register_value(_a)
                        if _v is not None and _VOLTAGE_MIN_V <= _v <= _VOLTAGE_MAX_V:
                            voltage_candidates.append((_a, _v))
                            logger.debug(f"Battery voltage candidate reg {_a} ({_vname}): {_v}V")

            if voltage_candidates:
                _best_addr, _best_val = max(voltage_candidates, key=lambda c: c[1])

                # Validate result against user-selected battery voltage range.
                # The cascade above runs identically regardless of this setting;
                # the selection acts as a post-hoc sanity gate on the winning value.
                if "High-voltage" in _bvr and _best_val < 100:
                    # HV gate: result below 100V on a declared HV system means register 3169
                    # overflowed (16-bit wrap at 655.36V when using 0.01V/unit scale).
                    _corrected = _best_val + 655.36
                    logger.debug(f"Battery voltage {_best_val}V below HV range — overflow correction → {_corrected:.1f}V")
                    _best_val = _corrected
                elif "Standard" in _bvr and _best_val > 600:
                    # Standard gate: result above 600V is implausible for a standard battery.
                    # Try reading register 3169 directly (0.01V/unit, no overflow for <600V).
                    _3169_raw = self._get_register_value(3169)
                    if _3169_raw is not None and _VOLTAGE_MIN_V <= _3169_raw <= 600:
                        logger.debug(f"Battery voltage {_best_val}V outside standard range — using reg 3169 directly: {_3169_raw:.1f}V")
                        _best_val = _3169_raw
                    else:
                        logger.warning(f"Battery voltage {_best_val}V outside expected standard range (<600V); check battery_voltage_range setting")

                data.battery_voltage = _best_val
                logger.debug(f"Battery voltage: {_best_val}V (selected from {len(voltage_candidates)} candidate(s), reg {_best_addr})")
            else:
                # All candidates out of range or absent — fall back to smart-fallback lookup
                value = self._get_register_value_with_fallback('battery_voltage')
                data.battery_voltage = value if value is not None else 0.0

            # Battery current (signed: positive=discharge, negative=charge)
            # Issue #226: some WIT firmware returns a small wrong non-zero on VPP reg 31215
            # while the native reg 8035 carries the correct value.  Rather than a zero-only
            # fallback, read all available registers and pick the one with the largest
            # absolute value (bounded to a plausible ±300 A range).
            _CURRENT_LOOKUP_NAMES = (
                'battery_current_low',   # 32-bit paired VPP (e.g. WIT 31215 via maps_to)
                'battery_current',       # native 8000-range (e.g. WIT 8035)
                'battery_current_legacy',
                'battery_current_3k',    # 3k-range fallback (e.g. WIT 3170)
            )
            _CURRENT_MAX_A = 300.0  # sanity ceiling — discard clearly out-of-range readings

            seen_current_addrs: set = set()
            current_candidates: list = []
            for _cname in _CURRENT_LOOKUP_NAMES:
                # Same fix as voltage: iterate ALL addresses per name so the native
                # 8000-range register is always evaluated alongside the VPP register.
                for _a in self._find_all_registers_by_name(_cname):
                    if _a not in seen_current_addrs:
                        seen_current_addrs.add(_a)
                        _v = self._get_register_value(_a)
                        if _v is not None and abs(_v) <= _CURRENT_MAX_A:
                            current_candidates.append((_a, _v))
                            logger.debug(f"Battery current candidate reg {_a} ({_cname}): {_v}A")

            if current_candidates:
                _best_addr, _best_val = max(current_candidates, key=lambda c: abs(c[1]))
                data.battery_current = _best_val
                logger.debug(f"Battery current: {_best_val}A (selected from {len(current_candidates)} candidate(s), reg {_best_addr})")

                # Record whether the candidates actually agree. Several registers claim to
                # be battery current and on some WIT hardware they disagree wildly - one
                # reporter's inverter returned -0.1 A, 6.3 A and -4.3 A at the same instant
                # (#406). Picking the largest is a guess; what matters here is that the
                # guess must not then be used to validate anything else.
                self._battery_current_candidates_agree = self._candidates_agree(
                    [v for _a, v in current_candidates]
                )
            else:
                data.battery_current = 0.0
                self._battery_current_candidates_agree = False

            # Battery SOC (use smart fallback if multiple ranges available)
            value = self._get_register_value_with_fallback('battery_soc')
            # If preferred-range returns None (e.g. MIN TL-XH: VPP detected for other sensors
            # but 'battery_soc' only exists at 3171 in the 3000-range), fall through to any
            # address named 'battery_soc' so we never cache-freeze when VPP range is latched.
            if value is None:
                for _soc_addr in self._find_all_registers_by_name('battery_soc'):
                    _soc_v = self._get_register_value(_soc_addr)
                    if _soc_v is not None:
                        value = _soc_v
                        logger.debug(
                            "battery_soc preferred-range miss — using fallback reg %d: %.1f%%",
                            _soc_addr, value,
                        )
                        break
            if value is not None:
                data.battery_soc = value
                self._cached_battery_soc = value
            elif self._cached_battery_soc is not None:
                # All register ranges unavailable — use last known value to avoid reporting
                # 0% to battery control consumers. Recovers on next successful range read.
                data.battery_soc = self._cached_battery_soc
                logger.warning(
                    "battery_soc unavailable across all register ranges — "
                    "serving last cached value %.1f%%",
                    self._cached_battery_soc,
                )
            else:
                data.battery_soc = 0.0

            # Battery temperature
            # Use range-aware lookup to respect VPP vs fallback detection
            addr = self._find_register_by_name_with_fallback('battery_temp')
            if addr:
                self._set_from_register(data, 'battery_temp', addr)
                data.battery_temp = self._resolve_battery_temp_scale(addr, data.battery_temp)
                logger.debug(f"Battery temp from reg {addr}: {data.battery_temp}°C")

            # Battery State of Health (WIT-only - only set if register exists in profile)
            addr = self._find_register_by_name('battery_soh')
            if addr:
                value = self._get_register_value(addr)
                if value is not None:
                    setattr(data, 'battery_soh', value)
                    logger.debug(f"Battery SOH from reg {addr}: {value}%")

            # Battery Voltage BMS (WIT-only - more accurate than standard battery_voltage)
            addr = self._find_register_by_name('battery_voltage_bms')
            if addr:
                value = self._get_register_value(addr)
                if value is not None:
                    # Some BMS firmware (e.g. JK BMS DIY) report in whole volts (raw ~54 for 54V)
                    # while the profile scale of 0.1 assumes tenths (raw ~527 for 52.7V).
                    # If the result is ~1/10th of battery_voltage (reg 8034, same 0.1 scale),
                    # multiply by 10 to correct for whole-volt BMS firmware.
                    if data.battery_voltage > 0 and value > 0 and value < data.battery_voltage * 0.2:
                        value = round(value * 10, 1)
                        logger.debug(f"Battery voltage BMS from reg {addr}: whole-volt BMS detected, corrected to {value}V")
                    else:
                        logger.debug(f"Battery voltage BMS from reg {addr}: {value}V")
                    setattr(data, 'battery_voltage_bms', value)

            # Battery power (signed: positive=charging, negative=discharging)
            # Use range-aware lookup to respect VPP vs fallback detection
            addr = self._find_register_by_name_with_fallback('battery_power_low')
            if addr:
                raw_low = self._register_cache.get(addr, 0)
                pair_addr = self._find_register_by_name_with_fallback('battery_power_high')
                raw_high = self._register_cache.get(pair_addr, 0) if pair_addr else 0

                # WIT Battery Power Scale Auto-Detection (before applying scale)
                # Combine raw 32-bit value for detection
                combined_raw = (raw_high << 16) | raw_low
                if combined_raw > 0x7FFFFFFF:  # Handle signed
                    combined_raw = combined_raw - 0x100000000

                # Attempt scale detection if we have V and I data
                if data.battery_voltage > 0 and data.battery_current != 0:
                    detected_scale = self._detect_battery_power_scale(
                        data.battery_voltage,
                        abs(data.battery_current),
                        abs(combined_raw)
                    )

                # BUGFIX: When battery is truly disconnected/dead (both voltage AND SOC near zero),
                # power registers may contain garbage values that produce astronomical
                # power readings when combined as signed 32-bit (e.g., SPF 5000 ES reports
                # reg77=50000, reg78=0 → combined=-1018167296 → scaled to 101MW).
                # Guard condition: voltage < 10V AND SOC < 5% — both must be near-zero.
                # If SOC > 5%, battery is connected; some SPF hardware reports 0V in certain
                # modes (e.g. bypass/standby) while battery is actually present and active.
                BATTERY_VOLTAGE_THRESHOLD = 10.0  # Volts
                BATTERY_SOC_THRESHOLD = 5.0       # % (below this = battery may be disconnected)
                battery_appears_disconnected = (data.battery_voltage < BATTERY_VOLTAGE_THRESHOLD
                                                and data.battery_soc < BATTERY_SOC_THRESHOLD)
                if battery_appears_disconnected:
                    battery_power = 0.0
                    logger.debug(f"Battery power set to 0W (voltage {data.battery_voltage}V < {BATTERY_VOLTAGE_THRESHOLD}V AND SOC {data.battery_soc}% < {BATTERY_SOC_THRESHOLD}% — battery appears disconnected, ignoring registers HIGH={raw_high} LOW={raw_low})")
                else:
                    _bp = self._get_register_value(addr)
                    if _bp is None:
                        # Not read this poll. Coercing to 0 here is worse than elsewhere:
                        # the sign split below would then set BOTH charge and discharge to
                        # zero, which is indistinguishable from an idle battery (#384).
                        data.unread_fields.update(
                            ('battery_power', 'charge_power', 'discharge_power')
                        )
                    battery_power = 0.0 if _bp is None else _bp
                    logger.debug(f"Battery power (signed): HIGH={raw_high} (reg {pair_addr}), LOW={raw_low} (reg {addr}) → {battery_power}W")

                # Apply inversion if configured (for inverters with opposite sign convention)
                if self._invert_battery_power:
                    battery_power = -battery_power
                    logger.debug(f"  → Inverted battery power: {battery_power}W (invert_battery_power=True)")

                # SPF-only: validate sign against inverter status code to correct
                # intermittent hardware sign errors during PV charging (issue #174)
                if self.register_map.get('offgrid_protocol', False):
                    battery_power = self._validate_spf_battery_power_sign(battery_power, data)

                # Split into charge/discharge based on sign
                # Convention: positive=charging, negative=discharging
                if battery_power > 0:
                    data.charge_power = battery_power
                    data.discharge_power = 0.0
                    logger.debug(f"  → Charging: {data.charge_power}W")
                elif battery_power < 0:
                    data.charge_power = 0.0
                    data.discharge_power = abs(battery_power)
                    logger.debug(f"  → Discharging: {data.discharge_power}W")
                else:
                    data.charge_power = 0.0
                    data.discharge_power = 0.0
            else:
                # Fallback: Try old separate charge/discharge registers (SPH series)
                # These registers are absolute values, but may be swapped for opposite convention inverters
                # Use range-aware lookup to respect VPP vs fallback detection
                addr = self._find_register_by_name_with_fallback('charge_power_low')
                if addr:
                    raw_low = self._register_cache.get(addr, 0)
                    pair_addr = self._find_register_by_name_with_fallback('charge_power_high')
                    raw_high = self._register_cache.get(pair_addr, 0) if pair_addr else 0
                    _rcp = self._get_register_value(addr)
                    if _rcp is None:
                        data.unread_fields.add(
                            'discharge_power' if self._invert_battery_power else 'charge_power'
                        )
                    raw_charge_power = 0.0 if _rcp is None else _rcp
                    logger.debug(f"Charge power (raw): HIGH={raw_high} (reg {pair_addr}), LOW={raw_low} (reg {addr}) → {raw_charge_power}W")

                    # Apply swapping if battery power is inverted (opposite convention)
                    if self._invert_battery_power:
                        # Opposite convention: "charge" register contains discharge, "discharge" contains charge
                        data.discharge_power = raw_charge_power
                        logger.debug(f"  → Swapped charge→discharge: {data.discharge_power}W (invert_battery_power=True)")
                    else:
                        data.charge_power = raw_charge_power
                elif data.battery_voltage > 0 and data.battery_current < 0:
                    # Fallback: Calculate from V×I when charging (negative current)
                    data.charge_power = data.battery_voltage * abs(data.battery_current)
                    logger.debug(f"Charge power (calculated): {data.battery_voltage}V × {abs(data.battery_current)}A = {data.charge_power}W")

                addr = self._find_register_by_name_with_fallback('discharge_power_low')
                if addr:
                    raw_low = self._register_cache.get(addr, 0)
                    pair_addr = self._find_register_by_name_with_fallback('discharge_power_high')
                    raw_high = self._register_cache.get(pair_addr, 0) if pair_addr else 0
                    _rdp = self._get_register_value(addr)
                    if _rdp is None:
                        data.unread_fields.add(
                            'charge_power' if self._invert_battery_power else 'discharge_power'
                        )
                    raw_discharge_power = 0.0 if _rdp is None else _rdp
                    logger.debug(f"Discharge power (raw): HIGH={raw_high} (reg {pair_addr}), LOW={raw_low} (reg {addr}) → {raw_discharge_power}W")

                    # Apply swapping if battery power is inverted (opposite convention)
                    if self._invert_battery_power:
                        # Opposite convention: "discharge" register contains charge, "charge" contains discharge
                        data.charge_power = raw_discharge_power
                        logger.debug(f"  → Swapped discharge→charge: {data.charge_power}W (invert_battery_power=True)")
                    else:
                        data.discharge_power = raw_discharge_power
                elif data.battery_voltage > 0 and data.battery_current > 0:
                    # Fallback: Calculate from V×I when discharging (positive current)
                    data.discharge_power = data.battery_voltage * data.battery_current
                    logger.debug(f"Discharge power (calculated): {data.battery_voltage}V × {data.battery_current}A = {data.discharge_power}W")
            
            # Charge energy today
            # Try both naming conventions with smart fallback: "charge_energy_today" and "battery_charge_today"
            value = self._get_register_value_with_fallback('charge_energy_today_low')
            if value is None:
                value = self._get_register_value_with_fallback('battery_charge_today_low')
            if value is not None:
                data.charge_energy_today = value
                # On an off-grid inverter every charge is an AC charge, so the same counter
                # serves both. On a grid-tied hybrid it does not: this register is total
                # battery charge (PV + grid), while AC charge is grid-only and lives at
                # 112-115. Copying it here made AC Charge Energy report battery charge —
                # 13820.7 kWh against a true 7099.8 on the reporter's SPH (#390).
                if self.register_map.get('offgrid_protocol', False):
                    data.ac_charge_energy_today = data.charge_energy_today
                # Log which register was used
                addr = self._find_register_by_name('charge_energy_today_low') or self._find_register_by_name('battery_charge_today_low')
                logger.debug(f"Charge energy today from register {addr}: {data.charge_energy_today} kWh")
            else:
                data.charge_energy_today = 0.0

            # Discharge energy today
            # Try both naming conventions with smart fallback: "discharge_energy_today" and "battery_discharge_today"
            value = self._get_register_value_with_fallback('discharge_energy_today_low')
            if value is None:
                value = self._get_register_value_with_fallback('battery_discharge_today_low')
            if value is not None:
                data.discharge_energy_today = value
                # Log which register was used
                addr = self._find_register_by_name('discharge_energy_today_low') or self._find_register_by_name('battery_discharge_today_low')
                logger.debug(f"Discharge energy today from register {addr}: {data.discharge_energy_today} kWh")
            else:
                data.discharge_energy_today = 0.0

            # Charge energy total
            # Try both naming conventions with smart fallback: "charge_energy_total" and "battery_charge_total"
            value = self._get_register_value_with_fallback('charge_energy_total_low')
            if value is None:
                value = self._get_register_value_with_fallback('battery_charge_total_low')
            if value is not None:
                data.charge_energy_total = value
                # Off-grid only — see the matching note on charge_energy_today above.
                if self.register_map.get('offgrid_protocol', False):
                    data.ac_charge_energy_total = data.charge_energy_total
                # Log which register was used
                addr = self._find_register_by_name('charge_energy_total_low') or self._find_register_by_name('battery_charge_total_low')
                logger.debug(f"Charge energy total from register {addr}: {data.charge_energy_total} kWh")
            else:
                data.charge_energy_total = 0.0

            # Discharge energy total
            # Try both naming conventions with smart fallback: "discharge_energy_total" and "battery_discharge_total"
            value = self._get_register_value_with_fallback('discharge_energy_total_low')
            if value is None:
                value = self._get_register_value_with_fallback('battery_discharge_total_low')
            if value is not None:
                data.discharge_energy_total = value
                # Log which register was used
                addr = self._find_register_by_name('discharge_energy_total_low') or self._find_register_by_name('battery_discharge_total_low')
                logger.debug(f"Discharge energy total from register {addr}: {data.discharge_energy_total} kWh")
            else:
                data.discharge_energy_total = 0.0

            # AC Charge Energy Today (WIT-specific - SPF populates this from charge_energy_today above)
            addr = self._find_register_by_name('ac_charge_energy_today_low')
            if addr:
                raw_low = self._register_cache.get(addr, 0)
                pair_addr = self._find_register_by_name('ac_charge_energy_today_high')
                raw_high = self._register_cache.get(pair_addr, 0) if pair_addr else 0
                self._set_from_register(data, 'ac_charge_energy_today', addr)
                logger.debug(f"AC charge energy today: HIGH={raw_high} (reg {pair_addr}), LOW={raw_low} (reg {addr}) → {data.ac_charge_energy_today} kWh")

            # AC Charge Energy Total (WIT-specific - SPF populates this from charge_energy_total above)
            addr = self._find_register_by_name('ac_charge_energy_total_low')
            if addr:
                raw_low = self._register_cache.get(addr, 0)
                pair_addr = self._find_register_by_name('ac_charge_energy_total_high')
                raw_high = self._register_cache.get(pair_addr, 0) if pair_addr else 0
                self._set_from_register(data, 'ac_charge_energy_total', addr)
                logger.debug(f"AC charge energy total: HIGH={raw_high} (reg {pair_addr}), LOW={raw_low} (reg {addr}) → {data.ac_charge_energy_total} kWh")

            if data.battery_voltage > 0:
                logger.debug(f"Battery summary: {data.battery_voltage}V, {data.battery_current}A, {data.battery_soc}%, {data.battery_temp}°C, Charge={data.charge_power}W, Discharge={data.discharge_power}W")

            # Battery clusters 2/3/4 (VPP 31300/31400/31500 — multi-battery models e.g. WIT-XHU, MOD)
            # Only populated when voltage > 0 so hasattr(data, 'batteryN_voltage') is a reliable gate.
            for _bn in (2, 3, 4):
                _pfx = f"battery{_bn}"
                _volt_addr = self._find_register_by_name(f"{_pfx}_voltage")
                if _volt_addr is None:
                    continue
                _volt = self._get_register_value(_volt_addr) or 0.0
                if _volt <= 0:
                    continue
                setattr(data, f"{_pfx}_voltage", _volt)
                for _reg in (
                    f"{_pfx}_power",
                    f"{_pfx}_current_low",
                    f"{_pfx}_soc",
                    f"{_pfx}_soh",
                    f"{_pfx}_temp",
                    f"{_pfx}_charge_energy_today",
                    f"{_pfx}_charge_energy_total",
                    f"{_pfx}_discharge_energy_today",
                    f"{_pfx}_discharge_energy_total",
                ):
                    _addr = self._find_register_by_name(_reg)
                    if _addr is not None:
                        setattr(data, _reg, self._get_register_value(_addr) or 0.0)
                logger.debug(
                    f"Battery {_bn}: {_volt}V "
                    f"SOC={getattr(data, f'{_pfx}_soc', 'N/A')}% "
                    f"P={getattr(data, f'{_pfx}_power', 0):.0f}W"
                )

            # BMS Information (SPH HU and other models with BMS monitoring)
            # Registers 1082-1120 contain detailed battery management system data
            bms_attrs = [
                ('bms_status_old', 'BMS Status Old'),
                ('bms_status', 'BMS Status'),
                ('bms_error_old', 'BMS Error Old'),
                ('bms_error', 'BMS Error'),
                ('bms_max_current', 'BMS Max Current'),
                ('bms_gauge_rm', 'BMS Gauge RM'),
                ('bms_gauge_fcc', 'BMS Gauge FCC'),
                ('bms_fw_version', 'BMS FW Version'),
                ('bms_delta_volt', 'BMS Delta Volt'),
                ('bms_cycle_count', 'BMS Cycle Count'),
                ('bms_soh', 'Battery State of Health'),
                ('bms_constant_volt', 'BMS Constant Voltage'),
                ('bms_warn_info_old', 'BMS Warning Old'),
                ('bms_warn_info', 'BMS Warning'),
                ('bms_max_cell_volt', 'BMS Max Cell Voltage'),
                ('bms_min_cell_volt', 'BMS Min Cell Voltage'),
                ('bms_module_num', 'BMS Module Count'),
                ('bms_battery_count', 'BMS Battery Count'),
                ('bms_max_soc', 'BMS Max SOC'),
                ('bms_min_soc', 'BMS Min SOC'),
            ]

            bms_found = False
            for attr_name, friendly_name in bms_attrs:
                addr = self._find_register_by_name(attr_name)
                if addr:
                    value = self._get_register_value(addr)
                    if value is not None:
                        setattr(data, attr_name, value)
                        if not bms_found:
                            logger.debug(f"BMS data available - reading BMS attributes")
                            bms_found = True
                        logger.debug(f"  {friendly_name} from reg {addr}: {value}")

        except Exception as e:
            logger.debug(f"Battery data not available: {e}")

    @staticmethod
    def _peak_shaving_kw(raw: int) -> Optional[float]:
        """Decode a demand-management power limit, or None if it was never configured.

        Returning None matters more than it looks. The register read succeeds — an unset
        limit answers with a ceiling rather than an error — so a caller that trusts the
        read publishes 3000 kW on a 25 kW inverter and nothing anywhere reports a fault
        (#380).
        """
        from .const import PEAK_SHAVING_UNSET_RAW, PEAK_SHAVING_MAX_PLAUSIBLE_KW

        if raw in PEAK_SHAVING_UNSET_RAW:
            return None
        kw = round(raw * 0.1, 1)
        if kw > PEAK_SHAVING_MAX_PLAUSIBLE_KW:
            return None
        return kw

    def _read_peak_shaving(self, data: GrowattData) -> None:
        """MOD/MID TL3-XH peak shaving and demand management (3307-3312, #372).

        Read as one 6-register block: 3307-3312 is contiguous and the two addresses we
        deliberately do not map (3309, 3313) fall inside or beside it, so a block read
        costs no more than the five individual reads would and is gentler on a marginal
        gateway.

        Applies to MID as well as MOD — the MID profile loads the same register map, which
        is how #380 was found.
        """
        try:
            ps_regs = self.read_holding_registers(3307, 6)
            if ps_regs is None or len(ps_regs) < 6:
                return

            data.demand_import_limit = self._peak_shaving_kw(ps_regs[0])
            data.demand_export_limit = self._peak_shaving_kw(ps_regs[1])
            # ps_regs[2] is 3309 — unidentified, deliberately unmapped
            # SOCs are assigned raw: unset is indistinguishable from configured on these
            data.peak_shaving_reserve_soc = int(ps_regs[3])
            data.ac_charge_max_power = self._peak_shaving_kw(ps_regs[4])
            data.grid_charge_stopped_soc = int(ps_regs[5])

            unset = [
                name for name, value in (
                    ("import_limit", data.demand_import_limit),
                    ("export_limit", data.demand_export_limit),
                    ("ac_charge_max", data.ac_charge_max_power),
                ) if value is None
            ]
            if unset:
                logger.debug(
                    "[MOD PEAK] peak shaving not configured for %s (raw %s/%s/%s) — "
                    "these sensors stay unavailable rather than publishing a ceiling",
                    ", ".join(unset), ps_regs[0], ps_regs[1], ps_regs[4],
                )
            logger.debug(
                "[MOD PEAK] import_limit=%s export_limit=%s reserve_soc=%s%% "
                "ac_charge_max=%s grid_charge_stop=%s%%",
                data.demand_import_limit, data.demand_export_limit,
                data.peak_shaving_reserve_soc, data.ac_charge_max_power,
                data.grid_charge_stopped_soc,
            )
        except Exception as e:
            logger.debug(f"Could not read peak shaving registers 3307-3312: {e}")

    def _read_backup_box_data(self, data: GrowattData) -> None:
        """Populate backup box (Growatt ARK) fields from cached 3000-range registers."""
        try:
            # Connection flag — must be read first so sensors.py deferred mechanism
            # can gate the remaining 8 conditional sensors on box_connect_flag == 1.
            addr = self._find_register_by_name('box_connect_flag')
            if addr is None:
                return  # Profile has no backup box registers — skip entirely
            value = self._get_register_value(addr)
            if value is not None:
                data.box_connect_flag = int(value)

            for attr, reg_name in (
                ('box_bypass_status', 'box_bypass_status'),
                ('box_work_mode',     'box_work_mode'),
                ('box_error_code',    'box_error_code'),
                ('box_warning_code',  'box_warning_code'),
                ('box_relay_status',  'box_relay_status'),
            ):
                a = self._find_register_by_name(reg_name)
                if a is not None:
                    v = self._get_register_value(a)
                    if v is not None:
                        setattr(data, attr, int(v))

            for attr, reg_name in (
                ('box_temperature',   'box_temperature'),
                ('box_grid_voltage',  'box_grid_voltage'),
            ):
                a = self._find_register_by_name(reg_name)
                if a is not None:
                    v = self._get_register_value(a)
                    if v is not None:
                        setattr(data, attr, float(v))

            # 32-bit paired: call _get_register_value on the _low address
            for attr, low_name in (
                ('box_grid_power', 'box_grid_power_low'),
                ('box_load_power', 'box_load_power_low'),
            ):
                a = self._find_register_by_name(low_name)
                if a is not None:
                    v = self._get_register_value(a)
                    if v is not None:
                        setattr(data, attr, float(v))

            if data.box_connect_flag:
                logger.debug(
                    "Backup box: connect=%d bypass=%d mode=%d temp=%.0f°C "
                    "grid=%.0fW load=%.0fW relay=%d",
                    data.box_connect_flag, data.box_bypass_status, data.box_work_mode,
                    data.box_temperature, data.box_grid_power, data.box_load_power,
                    data.box_relay_status,
                )
        except Exception as e:
            logger.debug(f"Backup box data not available: {e}")

    def _read_device_info(self, data: GrowattData) -> None:
        """Read device info from holding registers"""

        # Get holding register map once so we can use it even if 0–19 read fails
        holding_map = self.register_map.get("holding_registers", {})

        # --- Device info (0–19) ---
        holding_regs = self.read_holding_registers(0, 20)
        if holding_regs is None:
            logger.debug("Could not read holding registers 0–19 for device info")
        else:
            try:
                # Firmware version at register 3
                if len(holding_regs) > 3 and 3 in holding_map:
                    fw_version = holding_regs[3]
                    data.firmware_version = f"{fw_version >> 8}.{fw_version & 0xFF}"

                # Serial number from registers 9-13 (legacy range, used by TL-X and base models)
                if len(holding_regs) > 13:
                    serial_parts = []
                    for i in range(9, 14):
                        if i < len(holding_regs):
                            reg_val = holding_regs[i]
                            # Convert 16-bit register to 2 ASCII characters
                            if reg_val > 0:
                                char1 = (reg_val >> 8) & 0xFF
                                char2 = reg_val & 0xFF
                                if char1 > 0 and 32 <= char1 <= 126:
                                    serial_parts.append(chr(char1))
                                if char2 > 0 and 32 <= char2 <= 126:
                                    serial_parts.append(chr(char2))
                    data.serial_number = ''.join(serial_parts).rstrip('\x00')
            except Exception as e:
                logger.warning(f"Error reading device info: {e}")

        # VPP-range models (TL-XH, MOD, WIT) store serial in holding registers 3001-3005.
        # Try that range and override the legacy serial if it returns a valid result.
        _VPP_SERIAL_MAPS = ('TL_XH', 'MOD_', 'WIT_')
        if any(m in self.register_map_name for m in _VPP_SERIAL_MAPS):
            try:
                vpp_serial_regs = self.read_holding_registers(3001, 5)  # 5 regs = 10 ASCII chars
                if vpp_serial_regs is not None and len(vpp_serial_regs) >= 5:
                    vpp_parts = []
                    for reg_val in vpp_serial_regs:
                        for byte_val in ((reg_val >> 8) & 0xFF, reg_val & 0xFF):
                            if 32 <= byte_val <= 126:
                                vpp_parts.append(chr(byte_val))
                    vpp_serial = ''.join(vpp_parts).strip()
                    # Validate: reasonable length and starts with two letters (Growatt serial format)
                    if len(vpp_serial) >= 4 and vpp_serial[:2].isalpha():
                        data.serial_number = vpp_serial
                        logger.debug("[DEVICE INFO] VPP serial (3001-3005): %s", vpp_serial)
                    else:
                        logger.debug("[DEVICE INFO] VPP serial read returned unexpected data, keeping legacy: %r", vpp_serial)
            except Exception as e:
                logger.debug("[DEVICE INFO] VPP serial read failed, keeping legacy: %s", e)

        # --- Export control (122–123) --- ALWAYS ATTEMPTED
        if 122 in holding_map or 123 in holding_map:
            try:
                export_regs = self.read_holding_registers(122, 2)
                logger.debug("[EXPORT CTRL] Raw export_regs from 122–123: %r", export_regs)

                if export_regs is not None and len(export_regs) >= 2:
                    if 122 in holding_map:
                        data.export_limit_mode = int(export_regs[0])
                    if 123 in holding_map:
                        data.export_limit_power = int(export_regs[1])

                    logger.debug("[EXPORT CTRL] Read export control: mode=%s, power=%s",
                               data.export_limit_mode, data.export_limit_power)
            except Exception as e:
                logger.debug(f"Could not read export control registers: {e}")

        # --- Active Power Rate (3) --- Read if present in profile
        if 3 in holding_map:
            try:
                power_rate_regs = self.read_holding_registers(3, 1)
                logger.debug("[POWER CTRL] Raw active_power_rate from reg 3: %r", power_rate_regs)

                if power_rate_regs is not None and len(power_rate_regs) >= 1:
                    data.active_power_rate = int(power_rate_regs[0])
                    data.max_output_power_rate = data.active_power_rate  # Alias for number entity
                    logger.debug("[POWER CTRL] Read active_power_rate: %s%%", data.active_power_rate)
            except Exception as e:
                logger.debug(f"Could not read active_power_rate register: {e}")

        # --- WIT Export Limit W (holding 203) ---
        if 203 in holding_map:
            try:
                export_w_regs = self.read_holding_registers(203, 1)
                if export_w_regs is not None and len(export_w_regs) >= 1:
                    data.export_limit_w = int(export_w_regs[0])
                    logger.debug("[WIT CTRL] Read export_limit_w: %dW", data.export_limit_w)
            except Exception as e:
                logger.debug(f"Could not read export_limit_w register 203: {e}")

        # --- Export Limit Fallback Power Rate (holding 3000, TL-X / TL-XH) ---
        if 3000 in holding_map:
            try:
                elfpr_regs = self.read_holding_registers(3000, 1)
                if elfpr_regs is not None and len(elfpr_regs) >= 1:
                    data.export_limit_failed_power_rate = int(elfpr_regs[0])
                    logger.debug("[EXPORT CTRL] export_limit_failed_power_rate raw=%d (%.1f%%)",
                                 data.export_limit_failed_power_rate,
                                 data.export_limit_failed_power_rate * 0.1)
            except Exception as e:
                logger.debug(f"Could not read export_limit_failed_power_rate register 3000: {e}")

        # --- Dry Contact Controls (holding 3016/3017/3019, SPH/MIN TL-X/TL-XH) ---
        # Read as a 4-register block (3016–3019); index 2 (reg 3018 = tl_xh_priority_mode) is skipped.
        if any(reg in holding_map for reg in [3016, 3017, 3019]):
            try:
                dc_regs = self.read_holding_registers(3016, 4)
                if dc_regs is not None and len(dc_regs) >= 4:
                    if 3016 in holding_map:
                        data.dry_contact_enable = int(dc_regs[0])
                    if 3017 in holding_map:
                        data.dry_contact_on_rate = int(dc_regs[1])
                    if 3019 in holding_map:
                        data.dry_contact_off_rate = int(dc_regs[3])
                    logger.debug("[DRY CONTACT CTRL] enable=%d on_rate=%d off_rate=%d",
                                 data.dry_contact_enable, data.dry_contact_on_rate, data.dry_contact_off_rate)
            except Exception as e:
                logger.debug(f"Could not read dry contact control registers 3016-3019: {e}")

        # --- SPF Off-Grid Controls --- Read if present in profile
        # Read registers 1, 2, 8 (output config, charge config, AC input mode)
        if any(reg in holding_map for reg in [1, 2, 8]):
            try:
                spf_ctrl_regs = self.read_holding_registers(1, 8)
                logger.debug("[SPF CTRL] Raw SPF control regs 1-8: %r", spf_ctrl_regs)

                if spf_ctrl_regs is not None and len(spf_ctrl_regs) >= 8:
                    if 1 in holding_map:
                        data.output_config = int(spf_ctrl_regs[0])
                    if 2 in holding_map:
                        data.charge_config = int(spf_ctrl_regs[1])
                    if 8 in holding_map:
                        data.ac_input_mode = int(spf_ctrl_regs[7])
                    logger.debug("[SPF CTRL] output_config=%s, charge_config=%s, ac_input_mode=%s",
                               data.output_config, data.charge_config, data.ac_input_mode)
            except Exception as e:
                logger.debug(f"Could not read SPF control registers 1-8: {e}")

        # Read battery configuration registers (34-39)
        #
        # One block of six rather than 34 on its own plus 37-39: the addresses are
        # contiguous and 35/36 (bulk and float charge voltage) sit between them unmapped, so
        # a single read costs no more round trips than the old three-register one and is
        # gentler on a marginal gateway.
        if any(reg in holding_map for reg in [34, 37, 38, 39]):
            try:
                battery_ctrl_regs = self.read_holding_registers(34, 6)
                logger.debug("[SPF CTRL] Raw battery ctrl regs 34-39: %r", battery_ctrl_regs)

                if battery_ctrl_regs is not None and len(battery_ctrl_regs) >= 6:
                    if 34 in holding_map:
                        data.max_charge_current = int(battery_ctrl_regs[0])
                    if 35 in holding_map:
                        data.bulk_charge_voltage = int(battery_ctrl_regs[1])
                    if 36 in holding_map:
                        data.float_charge_voltage = int(battery_ctrl_regs[2])
                    if 37 in holding_map:
                        data.bat_low_to_uti = int(battery_ctrl_regs[3])
                    if 38 in holding_map:
                        data.ac_charge_current = int(battery_ctrl_regs[4])
                    if 39 in holding_map:
                        data.battery_type = int(battery_ctrl_regs[5])
                    logger.debug(
                        "[SPF CTRL] max_charge_current=%s, bat_low_to_uti=%s, "
                        "ac_charge_current=%s, battery_type=%s",
                        data.max_charge_current, data.bat_low_to_uti,
                        data.ac_charge_current, data.battery_type,
                    )
            except Exception as e:
                logger.debug(f"Could not read battery control registers 34-39: {e}")

        # Read generator charge current (83) and AC to battery voltage (95)
        if 83 in holding_map:
            try:
                gen_charge_regs = self.read_holding_registers(83, 1)
                logger.debug("[SPF CTRL] Raw gen_charge_current from reg 83: %r", gen_charge_regs)

                if gen_charge_regs is not None and len(gen_charge_regs) >= 1:
                    data.gen_charge_current = int(gen_charge_regs[0])
                    logger.debug("[SPF CTRL] gen_charge_current=%s A", data.gen_charge_current)
            except Exception as e:
                logger.debug(f"Could not read gen_charge_current register: {e}")

        if 95 in holding_map:
            try:
                ac_to_bat_regs = self.read_holding_registers(95, 1)
                logger.debug("[SPF CTRL] Raw ac_to_bat_volt from reg 95: %r", ac_to_bat_regs)

                if ac_to_bat_regs is not None and len(ac_to_bat_regs) >= 1:
                    data.ac_to_bat_volt = int(ac_to_bat_regs[0])
                    logger.debug("[SPF CTRL] ac_to_bat_volt=%s", data.ac_to_bat_volt)
            except Exception as e:
                logger.debug(f"Could not read ac_to_bat_volt register: {e}")

        # --- SPH/SPM Battery Control registers (1000+ range) ---
        # Priority Mode (1044 for SPH/SPH-TL3, 30476 for WIT)
        priority_addr = 1044 if 1044 in holding_map else (30476 if 30476 in holding_map else None)
        if priority_addr:
            try:
                priority_regs = self.read_holding_registers(priority_addr, 1)
                if priority_regs is not None and len(priority_regs) >= 1:
                    data.priority_mode = int(priority_regs[0])
                    profile_name = "WIT" if priority_addr == 30476 else "SPH"
                    logger.debug("[%s CTRL] priority_mode=%s", profile_name, data.priority_mode)
            except Exception as e:
                logger.debug(f"Could not read priority_mode register {priority_addr}: {e}")

        # Load First Battery Minimum SOC (register 608 — undocumented, SPH hybrid only)
        if 608 in holding_map:
            try:
                load_first_regs = self.read_holding_registers(608, 1)
                if load_first_regs is not None and len(load_first_regs) >= 1:
                    data.load_first_battery_minimum_soc = int(load_first_regs[0])
                    logger.debug("[SPH CTRL] load_first_battery_minimum_soc=%s%%",
                                 data.load_first_battery_minimum_soc)
            except Exception as e:
                logger.debug(f"Could not read load_first_battery_minimum_soc register 608: {e}")

        # Discharge Control (1070-1071)
        if any(reg in holding_map for reg in [1070, 1071]):
            try:
                discharge_regs = self.read_holding_registers(1070, 2)
                if discharge_regs is not None and len(discharge_regs) >= 2:
                    if 1070 in holding_map:
                        data.discharge_power_rate = int(discharge_regs[0])
                    if 1071 in holding_map:
                        data.discharge_stopped_soc = int(discharge_regs[1])
                    logger.debug("[SPH CTRL] discharge_power_rate=%s%%, discharge_stopped_soc=%s%%",
                               data.discharge_power_rate, data.discharge_stopped_soc)
            except Exception as e:
                logger.debug(f"Could not read discharge control registers: {e}")

        # Charge Control (1090-1092)
        if any(reg in holding_map for reg in [1090, 1091, 1092]):
            try:
                charge_regs = self.read_holding_registers(1090, 3)
                if charge_regs is not None and len(charge_regs) >= 3:
                    if 1090 in holding_map:
                        data.charge_power_rate = int(charge_regs[0])
                    if 1091 in holding_map:
                        data.charge_stopped_soc = int(charge_regs[1])
                    if 1092 in holding_map:
                        data.ac_charge_enable = int(charge_regs[2])
                    logger.debug("[SPH CTRL] charge_power_rate=%s%%, charge_stopped_soc=%s%%, ac_charge_enable=%s",
                               data.charge_power_rate, data.charge_stopped_soc, data.ac_charge_enable)
            except Exception as e:
                logger.debug(f"Could not read charge control registers: {e}")

        # Time Period Controls (1100-1108)
        if any(reg in holding_map for reg in range(1100, 1109)):
            try:
                time_period_regs = self.read_holding_registers(1100, 9)
                if time_period_regs is not None and len(time_period_regs) >= 9:
                    if 1100 in holding_map:
                        data.time_period_1_start = int(time_period_regs[0])
                    if 1101 in holding_map:
                        data.time_period_1_end = int(time_period_regs[1])
                    if 1102 in holding_map:
                        data.time_period_1_enable = int(time_period_regs[2])
                    if 1103 in holding_map:
                        data.time_period_2_start = int(time_period_regs[3])
                    if 1104 in holding_map:
                        data.time_period_2_end = int(time_period_regs[4])
                    if 1105 in holding_map:
                        data.time_period_2_enable = int(time_period_regs[5])
                    if 1106 in holding_map:
                        data.time_period_3_start = int(time_period_regs[6])
                    if 1107 in holding_map:
                        data.time_period_3_end = int(time_period_regs[7])
                    if 1108 in holding_map:
                        data.time_period_3_enable = int(time_period_regs[8])
                    logger.debug("[SPH CTRL] time_period_1: %s-%s (enabled=%s), time_period_2: %s-%s (enabled=%s), time_period_3: %s-%s (enabled=%s)",
                               data.time_period_1_start, data.time_period_1_end, data.time_period_1_enable,
                               data.time_period_2_start, data.time_period_2_end, data.time_period_2_enable,
                               data.time_period_3_start, data.time_period_3_end, data.time_period_3_enable)
            except Exception as e:
                logger.debug(f"Could not read time period control registers: {e}")

        # SPH GEN3 Battery First extended slots 4-6 (registers 1017-1025)
        if any(reg in holding_map for reg in range(1017, 1026)):
            try:
                bf_regs = self.read_holding_registers(1017, 9)
                if bf_regs is not None and len(bf_regs) >= 9:
                    if 1017 in holding_map: data.batt_first_time_period_4_start  = int(bf_regs[0])
                    if 1018 in holding_map: data.batt_first_time_period_4_end    = int(bf_regs[1])
                    if 1019 in holding_map: data.batt_first_time_period_4_enable = int(bf_regs[2])
                    if 1020 in holding_map: data.batt_first_time_period_5_start  = int(bf_regs[3])
                    if 1021 in holding_map: data.batt_first_time_period_5_end    = int(bf_regs[4])
                    if 1022 in holding_map: data.batt_first_time_period_5_enable = int(bf_regs[5])
                    if 1023 in holding_map: data.batt_first_time_period_6_start  = int(bf_regs[6])
                    if 1024 in holding_map: data.batt_first_time_period_6_end    = int(bf_regs[7])
                    if 1025 in holding_map: data.batt_first_time_period_6_enable = int(bf_regs[8])
                    logger.debug("[SPH CTRL] Battery First periods 4-6 loaded")
            except Exception as e:
                logger.debug(f"Could not read Battery First extended time period registers 1017-1025: {e}")

        # SPH GEN3 Grid First extended slots 4-6 (registers 1026-1034)
        if any(reg in holding_map for reg in range(1026, 1035)):
            try:
                gf46_regs = self.read_holding_registers(1026, 9)
                if gf46_regs is not None and len(gf46_regs) >= 9:
                    if 1026 in holding_map: data.grid_first_time_period_4_start  = int(gf46_regs[0])
                    if 1027 in holding_map: data.grid_first_time_period_4_end    = int(gf46_regs[1])
                    if 1028 in holding_map: data.grid_first_time_period_4_enable = int(gf46_regs[2])
                    if 1029 in holding_map: data.grid_first_time_period_5_start  = int(gf46_regs[3])
                    if 1030 in holding_map: data.grid_first_time_period_5_end    = int(gf46_regs[4])
                    if 1031 in holding_map: data.grid_first_time_period_5_enable = int(gf46_regs[5])
                    if 1032 in holding_map: data.grid_first_time_period_6_start  = int(gf46_regs[6])
                    if 1033 in holding_map: data.grid_first_time_period_6_end    = int(gf46_regs[7])
                    if 1034 in holding_map: data.grid_first_time_period_6_enable = int(gf46_regs[8])
                    logger.debug("[SPH CTRL] Grid First periods 4-6 loaded")
            except Exception as e:
                logger.debug(f"Could not read Grid First extended time period registers 1026-1034: {e}")

        # SPH GEN3 Grid First extended slots 7-9 (registers 1080-1088)
        if any(reg in holding_map for reg in range(1080, 1089)):
            try:
                gf79_regs = self.read_holding_registers(1080, 9)
                if gf79_regs is not None and len(gf79_regs) >= 9:
                    if 1080 in holding_map: data.grid_first_time_period_7_start  = int(gf79_regs[0])
                    if 1081 in holding_map: data.grid_first_time_period_7_end    = int(gf79_regs[1])
                    if 1082 in holding_map: data.grid_first_time_period_7_enable = int(gf79_regs[2])
                    if 1083 in holding_map: data.grid_first_time_period_8_start  = int(gf79_regs[3])
                    if 1084 in holding_map: data.grid_first_time_period_8_end    = int(gf79_regs[4])
                    if 1085 in holding_map: data.grid_first_time_period_8_enable = int(gf79_regs[5])
                    if 1086 in holding_map: data.grid_first_time_period_9_start  = int(gf79_regs[6])
                    if 1087 in holding_map: data.grid_first_time_period_9_end    = int(gf79_regs[7])
                    if 1088 in holding_map: data.grid_first_time_period_9_enable = int(gf79_regs[8])
                    logger.debug("[SPH CTRL] Grid First periods 7-9 loaded")
            except Exception as e:
                logger.debug(f"Could not read Grid First extended time period registers 1080-1088: {e}")

        # MOD TL3-XH TOU schedule (FC04 holding registers 3038-3045)
        if 3038 in holding_map:
            try:
                tou_regs = self.read_holding_registers(3038, 8)
                if tou_regs is not None and len(tou_regs) >= 8:
                    data.mod_tou_1_start = int(tou_regs[0])
                    data.mod_tou_1_end   = int(tou_regs[1])
                    data.mod_tou_2_start = int(tou_regs[2])
                    data.mod_tou_2_end   = int(tou_regs[3])
                    data.mod_tou_3_start = int(tou_regs[4])
                    data.mod_tou_3_end   = int(tou_regs[5])
                    data.mod_tou_4_start = int(tou_regs[6])
                    data.mod_tou_4_end   = int(tou_regs[7])
                    logger.debug("[MOD TOU] periods 1-4 start: %s %s %s %s, end: %s %s %s %s",
                                 data.mod_tou_1_start, data.mod_tou_2_start, data.mod_tou_3_start, data.mod_tou_4_start,
                                 data.mod_tou_1_end, data.mod_tou_2_end, data.mod_tou_3_end, data.mod_tou_4_end)
            except Exception as e:
                logger.debug(f"Could not read MOD TOU registers 3038-3045: {e}")

        # MOD GEN4 Allow Grid Charge gate (register 3049)
        if 3049 in holding_map:
            try:
                agc_regs = self.read_holding_registers(3049, 1)
                if agc_regs is not None and len(agc_regs) >= 1:
                    data.allow_grid_charge = int(agc_regs[0])
                    logger.debug("[MOD TOU] allow_grid_charge=%s", data.allow_grid_charge)
            except Exception as e:
                logger.debug(f"Could not read allow_grid_charge register 3049: {e}")

        # MOD GEN4 Grid First discharge rate (register 3036)
        if 3036 in holding_map:
            try:
                gfdr_regs = self.read_holding_registers(3036, 1)
                if gfdr_regs is not None and len(gfdr_regs) >= 1:
                    data.grid_first_discharge_power_rate = int(gfdr_regs[0])
                    logger.debug("[MOD CTRL] grid_first_discharge_power_rate=%s%%", data.grid_first_discharge_power_rate)
            except Exception as e:
                logger.debug(f"Could not read grid_first_discharge_power_rate register 3036: {e}")

        # MOD GEN4 Battery First charge rate (register 3047)
        if 3047 in holding_map:
            try:
                bfcr_regs = self.read_holding_registers(3047, 1)
                if bfcr_regs is not None and len(bfcr_regs) >= 1:
                    data.batt_first_charge_power_rate = int(bfcr_regs[0])
                    logger.debug("[MOD CTRL] batt_first_charge_power_rate=%s%%", data.batt_first_charge_power_rate)
            except Exception as e:
                logger.debug(f"Could not read batt_first_charge_power_rate register 3047: {e}")

        # MIN TL-XH Priority Mode (register 3018: 0=Load First, 2=Battery First, 3=Grid First)
        if 3018 in holding_map:
            try:
                pm_regs = self.read_holding_registers(3018, 1)
                if pm_regs is not None and len(pm_regs) >= 1:
                    data.tl_xh_priority_mode = int(pm_regs[0])
                    logger.debug("[TL-XH CTRL] tl_xh_priority_mode=%s", data.tl_xh_priority_mode)
            except Exception as e:
                logger.debug(f"Could not read tl_xh_priority_mode register 3018: {e}")

        # TL-XH / MOD Battery First charge stopped SOC (register 3048)
        if 3048 in holding_map:
            try:
                bfcs_regs = self.read_holding_registers(3048, 1)
                if bfcs_regs is not None and len(bfcs_regs) >= 1:
                    data.batt_first_charge_stopped_soc = int(bfcs_regs[0])
                    logger.debug("[TL-XH CTRL] batt_first_charge_stopped_soc=%s%%", data.batt_first_charge_stopped_soc)
            except Exception as e:
                logger.debug(f"Could not read batt_first_charge_stopped_soc register 3048: {e}")

        # TL-XH Grid First discharge stopped SOC (register 3067; US model / firmware ZACA-08+)
        if 3067 in holding_map:
            try:
                gfds_regs = self.read_holding_registers(3067, 1)
                if gfds_regs is not None and len(gfds_regs) >= 1:
                    data.grid_first_discharge_stopped_soc = int(gfds_regs[0])
                    logger.debug("[TL-XH CTRL] grid_first_discharge_stopped_soc=%s%%", data.grid_first_discharge_stopped_soc)
            except Exception as e:
                logger.debug(f"Could not read grid_first_discharge_stopped_soc register 3067: {e}")

        # MOD TL3-XH peak shaving / demand management (3307-3312, #372).
        #
        # Read as one 6-register block: 3307-3312 is contiguous and the two addresses we
        # deliberately do not map (3309, 3313) fall inside or beside it, so a block read
        # costs no more than the five individual reads would and is gentler on a marginal
        # gateway. Values we do not trust are simply not assigned.
        if 3307 in holding_map:
            self._read_peak_shaving(data)

        # Mirror of the last commanded VPP power setpoint (30474, #373).
        #
        # Not part of the 30407-30410 block and not covered by its availability probe, so
        # it gets its own guarded read. Signed: the setpoint runs -100..+100.
        if 30474 in holding_map:
            try:
                sp_regs = self.read_holding_registers(30474, 1)
                if sp_regs is not None and len(sp_regs) >= 1:
                    raw = sp_regs[0]
                    if raw > 32767:
                        raw -= 65536
                    data.vpp_last_setpoint = int(raw)
                    logger.debug("[VPP] last commanded setpoint (30474) = %s%%", data.vpp_last_setpoint)
            except Exception as e:
                logger.debug(f"Could not read VPP setpoint mirror register 30474: {e}")

        # MOD TL3-XH TOU slots 5-9 (registers 3050-3059)
        if 3050 in holding_map:
            try:
                tou59_regs = self.read_holding_registers(3050, 10)
                if tou59_regs is not None and len(tou59_regs) >= 10:
                    data.mod_tou_5_start = int(tou59_regs[0])
                    data.mod_tou_5_end   = int(tou59_regs[1])
                    data.mod_tou_6_start = int(tou59_regs[2])
                    data.mod_tou_6_end   = int(tou59_regs[3])
                    data.mod_tou_7_start = int(tou59_regs[4])
                    data.mod_tou_7_end   = int(tou59_regs[5])
                    data.mod_tou_8_start = int(tou59_regs[6])
                    data.mod_tou_8_end   = int(tou59_regs[7])
                    data.mod_tou_9_start = int(tou59_regs[8])
                    data.mod_tou_9_end   = int(tou59_regs[9])
                    logger.debug("[MOD TOU] periods 5-9 start: %s %s %s %s %s, end: %s %s %s %s %s",
                                 data.mod_tou_5_start, data.mod_tou_6_start, data.mod_tou_7_start,
                                 data.mod_tou_8_start, data.mod_tou_9_start,
                                 data.mod_tou_5_end, data.mod_tou_6_end, data.mod_tou_7_end,
                                 data.mod_tou_8_end, data.mod_tou_9_end)
            except Exception as e:
                logger.debug(f"Could not read MOD TOU registers 3050-3059: {e}")

        # --- Safety/compliance diagnostic registers 235-238 (read-only, Issue #282) ---
        if any(reg in holding_map for reg in [235, 236, 237, 238]):
            try:
                diag_regs = self.read_holding_registers(235, 4)
                if diag_regs is not None and len(diag_regs) >= 4:
                    if 235 in holding_map:
                        data.ntognd_detect = int(diag_regs[0])
                    if 236 in holding_map:
                        data.nonstd_vac_enable = int(diag_regs[1])
                    if 237 in holding_map:
                        data.enable_spec_set = int(diag_regs[2])
                    if 238 in holding_map:
                        data.fast_mppt_enable = int(diag_regs[3])
                    logger.debug("[DIAG] ntognd=%s nonstd_vac=%s enable_spec=%s fast_mppt=%s",
                                 data.ntognd_detect, data.nonstd_vac_enable,
                                 data.enable_spec_set, data.fast_mppt_enable)
            except Exception as e:
                logger.debug(f"Could not read diagnostic registers 235-238: {e}")

        # --- VPP holding registers (30000+ range) ---
        # These are optional — some firmware variants don't implement them. A failing
        # anchor address is recorded so the block is skipped for a while, avoiding
        # repeated transaction-ID mismatches from unanswered requests.
        #
        # The skip is time-limited (#370). It used to be permanent: the anchor went into
        # a set that was only ever added to, with no expiry, so a single dropped frame
        # latched "not supported by this firmware" for the rest of the session. A WIT
        # owner had control_authority frozen at Disabled for six hours while Growatt's
        # own cloud read the register as Enabled the whole time, and neither reloading
        # the entry nor restarting Home Assistant fixed it for more than one poll.
        #
        # That is the same defect #340 had on the input-register side, which #341 fixed
        # with exactly this retry. This set never received the same treatment — the two
        # mechanisms sit a few hundred lines apart and only one of them was corrected.
        #
        # Worth stating the limitation honestly: a transport error and a genuine
        # "illegal data address" are still conflated here, because read_holding_registers
        # returns None for both. Retrying every 5 minutes makes an unsupported register
        # cost one wasted read per 5 minutes, which is cheap; the previous behaviour made
        # a supported register cost everything.
        _VPP_HOLDING_RETRY_S = 300

        def _vpp_block_skipped(anchor: int) -> bool:
            """True while this anchor is inside its retry window."""
            prev = self._failed_optional_holding_addrs.get(anchor)
            if prev is None:
                return False
            if time.time() - prev >= _VPP_HOLDING_RETRY_S:
                logger.debug("[VPP] Retrying previously failed holding block at %d", anchor)
                return False
            return True

        def _vpp_block_failed(anchor: int, what: str) -> None:
            first = anchor not in self._failed_optional_holding_addrs
            self._failed_optional_holding_addrs[anchor] = time.time()
            if first:
                logger.debug(
                    "[VPP] %s did not respond — skipping for %ds, then retrying. "
                    "If this repeats indefinitely the firmware likely does not "
                    "implement it.", what, _VPP_HOLDING_RETRY_S,
                )

        # Control Authority (30100)
        if 30100 in holding_map and not _vpp_block_skipped(30100):
            try:
                vpp_ctrl_regs = self.read_holding_registers(30100, 1)
                if vpp_ctrl_regs is not None and len(vpp_ctrl_regs) >= 1:
                    data.control_authority = int(vpp_ctrl_regs[0])
                    data.vpp_control_authority_available = True
                    self._failed_optional_holding_addrs.pop(30100, None)
                    logger.debug("[VPP] control_authority=%s", data.control_authority)
                else:
                    _vpp_block_failed(30100, "Register 30100 (control authority)")
            except Exception as e:
                logger.debug(f"Could not read VPP control_authority register 30100: {e}")

        # VPP Export Limitation (30200-30201)
        if any(reg in holding_map for reg in [30200, 30201]) and not _vpp_block_skipped(30200):
            try:
                vpp_export_regs = self.read_holding_registers(30200, 2)
                if vpp_export_regs is not None and len(vpp_export_regs) >= 2:
                    if 30200 in holding_map:
                        data.vpp_export_limit_enable = int(vpp_export_regs[0])
                    if 30201 in holding_map:
                        # Register 30201 is signed (-100 to +100)
                        raw_val = vpp_export_regs[1]
                        if raw_val > 32767:  # Handle signed 16-bit
                            raw_val = raw_val - 65536
                        data.vpp_export_limit_power_rate = int(raw_val)
                    data.vpp_export_limit_available = True
                    self._failed_optional_holding_addrs.pop(30200, None)
                    logger.debug("[VPP] vpp_export_limit_enable=%s, vpp_export_limit_power_rate=%s%%",
                               data.vpp_export_limit_enable, data.vpp_export_limit_power_rate)
                else:
                    _vpp_block_failed(30200, "Registers 30200-30201 (export limit)")
            except Exception as e:
                logger.debug(f"Could not read VPP export limitation registers 30200-30201: {e}")

        # Remote Power Control (30407-30410)
        if any(reg in holding_map for reg in [30407, 30408, 30409, 30410]) and not _vpp_block_skipped(30407):
            try:
                vpp_power_regs = self.read_holding_registers(30407, 4)
                if vpp_power_regs is not None and len(vpp_power_regs) >= 3:
                    if 30407 in holding_map:
                        data.remote_power_control_enable = int(vpp_power_regs[0])
                    if 30408 in holding_map:
                        data.remote_power_control_charging_time = int(vpp_power_regs[1])
                    if 30409 in holding_map:
                        # Register 30409 is signed (-100 to +100)
                        raw_val = vpp_power_regs[2]
                        if raw_val > 32767:  # Handle signed 16-bit
                            raw_val = raw_val - 65536
                        data.remote_charge_and_discharge_power = int(raw_val)
                    if 30410 in holding_map and len(vpp_power_regs) >= 4:
                        data.vpp_ac_charge_enable = int(vpp_power_regs[3])
                    logger.debug("[VPP] remote_power_control_enable=%s, charging_time=%s min, charge_discharge_power=%s%%, ac_charge_enable=%s",
                               data.remote_power_control_enable, data.remote_power_control_charging_time,
                               data.remote_charge_and_discharge_power, data.vpp_ac_charge_enable)
                    self._failed_optional_holding_addrs.pop(30407, None)
                else:
                    _vpp_block_failed(30407, "Registers 30407-30410 (remote power control)")
            except Exception as e:
                logger.debug(f"Could not read VPP remote power control registers 30407-30410: {e}")

    def get_status_text(self, status_code: int) -> str:
        """Convert status code to human readable text"""
        status_info = STATUS_CODES.get(status_code, {'name': f'Unknown ({status_code})', 'desc': 'Unknown status code'})
        return status_info['name']
