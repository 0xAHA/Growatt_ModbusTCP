"""Inverter on/off: which register, and how each protocol encodes it.

Every protocol family puts remote on/off somewhere different, or packs it alongside a
second setting that a naive 0/1 write would clobber:

- V1.39 (MIN, MID, MOD, SPH, SPA, TL-XH, WIT), holding 0: 1 = on, 0 = off. The same
  register takes 3/2 for the battery DC converter (BDC); this module never writes those.
- Legacy V3.14 (MIC, TL3-S), holding 0: low byte on/off, high byte auto start - whether
  the inverter powers its AC side back up after its next power-on. The documented default
  is 0x0101, and a TL3-S reads back exactly that (#432). Writing a bare 0 or 1 would turn
  auto start off, leaving an inverter that stays off after a power cut until someone
  switches it back on by hand.
- Off-grid (SPF, SPE), holding 0: high byte AC output, inverted (0 = enabled, 1 = disabled);
  low byte standby. The documented values are 0x0000 (output on) and 0x0100 (output off).
- VPP (only profiles with no holding 0, e.g. MIN TL-XH2), holding 30101: 1 = on, 0 = off,
  "Not storage" - it returns to on after a reboot.

The two byte-packed encodings are read-modify-write: the other byte is read from the
inverter at press time and written back unchanged. If that read fails nothing is written,
because guessing the other byte is exactly the mistake being avoided.
"""
from __future__ import annotations

from dataclasses import dataclass

from .growatt_modbus import ModbusWriteError

ENCODING_PLAIN = "plain"
ENCODING_LEGACY_AUTOSTART = "legacy_autostart"
ENCODING_OFFGRID_OUTPUT = "offgrid_output"
ENCODING_VPP = "vpp"

VPP_ONOFF_REGISTER = 30101


class PowerControlError(Exception):
    """The on/off command could not be sent safely."""


@dataclass(frozen=True)
class PowerControl:
    """Where this profile's on/off lives and how it is encoded.

    `readback` is set only where a real unit has been seen to read back its state - 0 while
    off AND 1 while on, not a single reading, which cannot tell a live register from one
    stuck at a value. Everywhere else the switch shows the last command sent.
    """

    register: int
    encoding: str
    readback: bool = False

    @property
    def is_read_modify_write(self) -> bool:
        return self.encoding in (ENCODING_LEGACY_AUTOSTART, ENCODING_OFFGRID_OUTPUT)

    @property
    def is_ac_output(self) -> bool:
        """Off-grid models: the documented control is the AC output, not the inverter."""
        return self.encoding == ENCODING_OFFGRID_OUTPUT


def resolve_power_control(register_map: dict) -> PowerControl | None:
    """Pick the on/off register and encoding for a register map, or None if it has none.

    Holding 0 is preferred whenever the profile declares it, including on V2.01 profiles
    that also carry 30101: it is the same hardware as their legacy siblings, and 30101 is
    only known to act alongside control authority (30100) on other VPP controls - which
    this deliberately does not grant just to flip power.
    """
    holding = register_map.get("holding_registers", {})
    if 0 in holding:
        readback = bool(holding[0].get("onoff_readback"))
        if register_map.get("offgrid_protocol"):
            return PowerControl(0, ENCODING_OFFGRID_OUTPUT, readback)
        return PowerControl(0, holding[0].get("onoff_encoding", ENCODING_PLAIN), readback)
    if VPP_ONOFF_REGISTER in holding:
        return PowerControl(VPP_ONOFF_REGISTER, ENCODING_VPP,
                            bool(holding[VPP_ONOFF_REGISTER].get("onoff_readback")))
    return None


def decode(control: PowerControl, raw: int | None) -> bool | None:
    """On/off from a register read, or None when the value is not one this encoding defines.

    Anything outside the documented values is unknown rather than guessed - a register
    answering garbage must not show as a confident on or off.
    """
    if raw is None:
        return None
    if control.encoding in (ENCODING_PLAIN, ENCODING_VPP):
        return {1: True, 0: False}.get(raw)
    if control.encoding == ENCODING_LEGACY_AUTOSTART:
        return {0x0000: False, 0x0100: False, 0x0001: True, 0x0101: True}.get(raw)
    if control.encoding == ENCODING_OFFGRID_OUTPUT:
        return {0x0000: True, 0x0001: True, 0x0100: False, 0x0101: False}.get(raw)
    return None


def encode(control: PowerControl, on: bool, current: int | None = None) -> int:
    """The value to write for on/off, preserving the other byte where there is one."""
    if control.encoding in (ENCODING_PLAIN, ENCODING_VPP):
        return 1 if on else 0
    if current is None:
        raise ValueError(f"{control.encoding} needs the register's current value")
    if control.encoding == ENCODING_LEGACY_AUTOSTART:
        return (current & 0xFF00) | (0x01 if on else 0x00)
    if control.encoding == ENCODING_OFFGRID_OUTPUT:
        return (current & 0x00FF) | (0x0000 if on else 0x0100)
    raise ValueError(f"Unknown on/off encoding: {control.encoding}")


def set_power(client, control: PowerControl, on: bool) -> int:
    """Send the on/off command. Returns the value written. Runs in the executor."""
    current = None
    if control.is_read_modify_write:
        regs = client.read_holding_registers(control.register, 1)
        if not regs:
            raise PowerControlError(
                f"Could not read register {control.register} to preserve its other "
                f"setting - nothing was written"
            )
        current = int(regs[0])

    value = encode(control, on, current)
    try:
        written = client.write_register(control.register, value)
    except ModbusWriteError as err:
        raise PowerControlError(str(err)) from err
    if not written:
        raise PowerControlError(f"The inverter did not accept register {control.register} = {value}")
    return value
