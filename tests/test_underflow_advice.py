"""The underflow warning must not advise adding 'signed' to a not-implemented register (#401).

A 32-bit pair that is not declared signed but arrives with the sign bit set is withheld,
and the warning used to say the same thing every time:

    If this repeats, the profile is probably missing 'signed': True for this register

That is right for the fault the guard was built for - a daily counter dipping one count
below zero, which arrives as 4,294,967,279 and is -17 - and wrong for a register the
firmware does not implement, which answers with an all-ones pattern.

An SPH 10000TL3 owner read exactly that advice and concluded the flag was missing on the
per-phase grid-import pairs:

    power_to_user_t (1019/1020)  0xFFED0000 -> -1,245,184 -> -124,518 W
    power_to_user_s (1017/1018)  0xFFE5FFE5 -> -1,703,963 -> -170,396 W

On a 10 kW inverter. Adding the flag would have published those instead of withholding
them, turning a correctly-refused reading into a confident wrong one - which is the whole
failure mode this project treats as the worst outcome.

The registers themselves are mapped correctly: V1.39 gives input 1015-1020 as
`Pactouser R/S/T` high/low at 0.1 W, with no sign, and directional import is a one-way
quantity. The hardware simply does not populate them.
"""
from __future__ import annotations

import importlib

import pytest

_gm = importlib.import_module("growatt_under_test.growatt_modbus")
SOURCE = open(_gm.__file__, encoding="utf-8").read()

# The reporter's two readings, and the original #401 underflow for contrast.
SENTINELS = {
    "power_to_user_t": 4293722112,   # 0xFFED0000
    "power_to_user_s": 4293263333,   # 0xFFE5FFE5
}
GENUINE_UNDERFLOW = 4294967279       # -17, a counter one count below zero


def _as_signed(raw: int) -> int:
    return raw - 0x100000000


def test_the_threshold_exists():
    assert hasattr(_gm, "_UNDERFLOW_PLAUSIBLE_MAGNITUDE"), (
        "the sentinel discriminator is gone, so every sign-bit reading is advised as a "
        "missing signed flag again"
    )


@pytest.mark.parametrize("name,raw", sorted(SENTINELS.items()))
def test_the_reporters_values_are_called_sentinels(name, raw):
    """THE regression, at his numbers."""
    assert abs(_as_signed(raw)) > _gm._UNDERFLOW_PLAUSIBLE_MAGNITUDE, (
        f"{name} reading {raw:#010x} would still be advised as a missing 'signed' flag, "
        f"which would publish {_as_signed(raw) * 0.1:.0f} W"
    )


def test_a_genuine_underflow_is_not_called_a_sentinel():
    """The guard this message was written for. -17 must still get the 'add signed' advice,
    or the original #401 fix loses its diagnostic."""
    assert abs(_as_signed(GENUINE_UNDERFLOW)) <= _gm._UNDERFLOW_PLAUSIBLE_MAGNITUDE


@pytest.mark.parametrize("watts", [-1, -50, -4000, -90000])
def test_plausible_negative_powers_keep_the_original_advice(watts):
    """Anything a domestic or light-commercial inverter could actually produce, as a raw
    0.1-scale value, must read as a genuine negative rather than as garbage."""
    raw_signed = watts * 10          # 0.1 W scale
    assert abs(raw_signed) <= _gm._UNDERFLOW_PLAUSIBLE_MAGNITUDE


def test_both_branches_are_in_the_shipped_message():
    assert "Do NOT add 'signed': True" in SOURCE, (
        "the sentinel branch no longer warns against the change that would publish it"
    )
    assert "probably missing" in SOURCE, (
        "the genuine-underflow advice was removed along with the fix"
    )


def test_the_raw_value_is_logged_in_hex():
    """0xFFE5FFE5 says 'not implemented' at a glance in a way that 4293263333 does not."""
    assert "0x%08X" in SOURCE, "the warning no longer shows the raw pattern in hex"


def test_the_per_phase_import_registers_are_left_unsigned():
    """Guard against the change the reporter asked for being made later by someone reading
    only the issue title. V1.39 documents these as unsigned, and the values that prompted
    the request are not measurements."""
    rmap = importlib.import_module("growatt_under_test.const").REGISTER_MAPS
    profile = rmap["SPH_TL3_3000_10000_V201"]["input_registers"]

    for address in (1015, 1016, 1017, 1018, 1019, 1020):
        info = profile.get(address)
        assert info is not None, f"register {address} is no longer mapped"
        assert not info.get("signed"), (
            f"register {address} ({info.get('name')}) has been declared signed. V1.39 gives "
            f"it as Pactouser at 0.1 W with no sign, and the readings that prompted this "
            f"are sentinels - the flag would publish -124 kW"
        )
