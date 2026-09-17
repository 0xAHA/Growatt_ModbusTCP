"""The same word-level corruption, on a pair that is allowed to go negative (#447).

#446 closed this for unsigned pairs: a high word carrying a small integer where a correct
reading has 0, with the low word jammed against an end. That guard deliberately skips signed
pairs, because on those a legitimate small negative *is* 0xFFFF in the high word - the exact
shape it withholds.

A second SPH 10000 TL3 BH-UP owner then reported the fault on grid power, which his profile
declares signed. His chart showed one afternoon of spikes to about 9 MW and 6 MW against a
baseline of -20 W, and his own register scan caught two corrupted high words live, at 1017
(65289) and 1019 (63726).

The discriminator is different here. Real values cluster at BOTH ends of the high word and
the corruption lands in between:

    legitimate                      corrupt
    -0.9 W      high 65535          high   579   ->  +3,800,000 W
    -246 W      high 65535          high   915   ->  +6,000,000 W
    -11,862 W   high 65534          high  1373   ->  +9,000,000 W
    +1,810 W    high     0          high 63726   -> -11,862,016 W
    +30,000 W   high     4          high 65289   ->  -1,618,739 W

16 counts of headroom at each end is about +/-107 kW at 0.1 W per count, well beyond any
inverter this integration supports - so no real reading can reach the middle.
"""
from __future__ import annotations

import importlib

import pytest

_gm = importlib.import_module("growatt_under_test.growatt_modbus")

suspect = _gm.GrowattModbus._signed_pair_words_look_corrupted

# His spikes, and the two his scan caught, as high words.
CORRUPT_HIGH_WORDS = [579, 915, 1373, 63726, 65289]

# Every legitimate value, as (label, high word). Nothing here may be withheld.
LEGITIMATE_HIGH_WORDS = [
    ("-0.9 W", 65535), ("-9 W", 65535), ("-246 W", 65535),
    ("-1,810 W", 65535), ("-11,862 W", 65534),
    ("+1,810 W", 0), ("+11,862 W", 1), ("+30,000 W", 4),
]


@pytest.mark.parametrize("high", CORRUPT_HIGH_WORDS)
def test_every_corrupt_high_word_is_recognised(high):
    assert suspect(high) is True, f"high={high} not recognised"


@pytest.mark.parametrize("label,high", LEGITIMATE_HIGH_WORDS)
def test_no_real_reading_is_flagged(label, high):
    assert suspect(high) is False, f"{label} (high={high}) would be withheld"


def test_the_bands_are_where_the_constant_says():
    band = _gm._SIGNED_PAIR_HIGH_WORD_BAND
    assert suspect(band) is False
    assert suspect(band + 1) is True
    assert suspect(0xFFFF - band) is False
    assert suspect(0xFFFF - band - 1) is True


def test_the_headroom_exceeds_any_supported_inverter():
    """The band has to be wide enough for the largest real reading and narrow enough to
    catch the corruption. 16 counts is about 107 kW at 0.1 W per count."""
    band = _gm._SIGNED_PAIR_HIGH_WORD_BAND
    watts = ((band + 1) << 16) * 0.1
    assert watts > 100_000, "the band is too tight for a large commercial inverter"
    assert min(CORRUPT_HIGH_WORDS) > band, "a reported spike falls inside the safe band"


# ---------------------------------------------------------------------------
# Through the real decode
# ---------------------------------------------------------------------------

SIGNED_PAIR = {
    "name": "SPH-TL3 test map",
    "input_registers": {
        1029: {"name": "power_to_grid_high", "scale": 1, "unit": "", "pair": 1030},
        1030: {"name": "power_to_grid_low", "scale": 1, "unit": "", "pair": 1029,
               "combined_scale": 0.1, "combined_unit": "W", "signed": True},
    },
}


def _client(high, low):
    client = _gm.GrowattModbus.__new__(_gm.GrowattModbus)
    client.register_map = SIGNED_PAIR
    client._register_cache = {1029: high, 1030: low}
    client._pair_shape_suspect = {}
    client._pair_shape_warned = set()
    client._underflow_warned = set()
    client._battery_power_scale_override = None
    return client


def test_his_nine_megawatt_spike_is_withheld():
    """THE fault: high 1373 decodes to +9,000,000.0 W and was published."""
    assert _client(1373, 19072)._get_register_value(1030) is None


def test_a_genuine_export_still_decodes():
    """1,810 W, the value his own scan held at 1029/1030."""
    assert _client(0, 18100)._get_register_value(1030) == pytest.approx(1810.0)


def test_a_genuine_import_still_decodes():
    """Negative is the whole reason this pair is signed - -258.6 W must survive."""
    assert _client(0xFFFF, 62950)._get_register_value(1030) == pytest.approx(-258.6)


def test_a_large_genuine_import_still_decodes():
    assert _client(65534, 12452)._get_register_value(1030) == pytest.approx(-11862.0)


def test_a_persistent_shape_is_published_after_three_polls():
    """A glitch does not persist; a real reading does. Same escape as the unsigned guard."""
    client = _client(1373, 19072)
    assert client._get_register_value(1030) is None
    assert client._get_register_value(1030) is None
    assert client._get_register_value(1030) == pytest.approx(9_000_000.0)


def test_a_good_reading_clears_the_suspicion():
    client = _client(1373, 19072)
    assert client._get_register_value(1030) is None

    client._register_cache = {1029: 0, 1030: 18100}
    assert client._get_register_value(1030) == pytest.approx(1810.0)

    client._register_cache = {1029: 1373, 1030: 19072}
    assert client._get_register_value(1030) is None, "the good reading did not reset it"


def test_the_unsigned_guard_is_untouched():
    """#446's rule must still own unsigned pairs - the two use different discriminators and
    must not be merged."""
    unsigned = _gm.GrowattModbus._pair_words_look_corrupted
    assert unsigned(14, 65515) is True      # acsel91's sample
    assert unsigned(1, 44400) is False      # his genuine 11 kW EV charge
