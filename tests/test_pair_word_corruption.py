"""A 32-bit pair with its value in the wrong half is withheld (#446).

An SPH 10000TL3 BH-UP owner captured 16 absurd grid-import samples over two days. Every one
had the same shape: the HIGH word carrying a small integer where a correct reading has 0,
and the LOW word jammed against one end of its range.

    date   time    published W          raw          hex      high     low
    15.09  06:00       72,088.7      720887   0x000AFFF7      10    65527
    15.09  12:00       65,536.0      655360   0x000A0000      10        0
    15.09  16:00    1,841,481.3    18414813   0x0118FCDD     280    64733
    16.09  08:05        6,553.8       65538   0x00010002       1        2
    16.09  13:50       98,301.9      983019   0x000EFFEB      14    65515

The published figure is about `high x 6553.6 W`, with the real reading - a small value
either side of zero - sitting in the low word. The rest of the frame decoded cleanly in the
same poll, so this is not a corrupt frame: RTU checksums the whole frame, and a bad one
costs every value in it, not one pair.

**Magnitude cannot catch this.** His smallest sample published 6,553.8 W, which is an
ordinary reading for a house with an EV charger. Only the word shape separates it, which is
what the reporter proposed:

> the signature here is not simply "large". It is `high` non-zero and small while `low` sits
> at one end of its range - 16 of 16.

The cost of that rule is a genuine reading near a multiple of 65536 raw counts, which has
the same shape. A corruption is transient - his lasted one poll and was normal ten seconds
later - so the same shape repeating three polls in a row is believed and published.
"""
from __future__ import annotations

import importlib

import pytest

_gm = importlib.import_module("growatt_under_test.growatt_modbus")

looks_corrupted = _gm.GrowattModbus._pair_words_look_corrupted

# His 16 samples, as (high, low).
REPORTED = [
    (10, 65527), (10, 0), (71, 65461), (23, 65503), (280, 64733),
    (3, 2), (2, 3), (1, 2), (23, 65517), (4, 2),
    (5, 0), (3, 2), (3, 2), (4, 65525), (1, 7), (14, 65515),
]


@pytest.mark.parametrize("high,low", REPORTED)
def test_every_reported_sample_is_recognised(high, low):
    assert looks_corrupted(high, low) is True, f"HIGH={high} LOW={low} not recognised"


def test_a_correct_small_reading_is_untouched():
    """The normal case, from his own read of 1021/1022: high 0, value in low."""
    assert looks_corrupted(0, 7000) is False


def test_a_genuine_large_reading_is_untouched():
    """His real 11 kW EV charge: high is non-zero, but the low word is mid-range."""
    assert looks_corrupted(1, 44400) is False


def test_the_boundary_is_where_the_margin_says():
    margin = _gm._PAIR_WORD_EXTREME_MARGIN
    assert looks_corrupted(1, margin) is True
    assert looks_corrupted(1, margin + 1) is False
    assert looks_corrupted(1, 0xFFFF - margin) is True
    assert looks_corrupted(1, 0xFFFF - margin - 1) is False


def test_a_large_high_word_is_not_this_fault():
    """0x7FFFFFFF is high 32767, low 65535 - the same low-word shape, but the high word is
    nothing like the 1-280 measured here. tests/test_register_decoding.py pins it as
    decoding normally: that line is drawn at the sign bit, not at plausibility (#401), and
    this guard must not quietly move it."""
    assert looks_corrupted(0x7FFF, 0xFFFF) is False


def test_the_high_word_bound_is_where_the_constant_says():
    limit = _gm._PAIR_HIGH_WORD_MAX_FOR_CORRUPTION
    assert looks_corrupted(limit, 0) is True
    assert looks_corrupted(limit + 1, 0) is False


def test_every_reported_high_word_is_inside_the_bound():
    """The bound has to cover the measured range or a sample publishes anyway."""
    limit = _gm._PAIR_HIGH_WORD_MAX_FOR_CORRUPTION
    assert max(high for high, _low in REPORTED) <= limit


def test_the_widest_reported_sample_is_inside_the_margin():
    """280/64733 is the loosest fit of the 16 - 802 counts below 0xFFFF. The margin has to
    cover it, or that sample publishes 1.84 MW."""
    assert looks_corrupted(280, 64733) is True


# ---------------------------------------------------------------------------
# Through the real decode
# ---------------------------------------------------------------------------

UNSIGNED_PAIR = {
    'name': 'SPH-TL3 test map',
    'input_registers': {
        1021: {'name': 'power_to_user_high', 'scale': 1, 'unit': '', 'pair': 1022},
        1022: {'name': 'power_to_user_low', 'scale': 1, 'unit': '', 'pair': 1021,
               'combined_scale': 0.1, 'combined_unit': 'W'},
    },
}

SIGNED_PAIR = {
    'name': 'signed test map',
    'input_registers': {
        100: {'name': 'meter_power_high', 'scale': 1, 'unit': '', 'pair': 101},
        101: {'name': 'meter_power_low', 'scale': 1, 'unit': '', 'pair': 100,
              'combined_scale': 0.1, 'combined_unit': 'W', 'signed': True},
    },
}


def _client(register_map, high, low, addr=1021, pair=1022):
    client = _gm.GrowattModbus.__new__(_gm.GrowattModbus)
    client.register_map = register_map
    client._register_cache = {addr: high, pair: low}
    client._pair_shape_suspect = {}
    client._pair_shape_warned = set()
    client._underflow_warned = set()
    client._battery_power_scale_override = None
    return client


def test_the_decode_withholds_a_corrupted_pair():
    """THE fault, through _get_register_value: 14/65515 published 98,301.9 W."""
    client = _client(UNSIGNED_PAIR, 14, 65515)
    assert client._get_register_value(1022) is None


def test_the_decode_publishes_a_normal_reading():
    client = _client(UNSIGNED_PAIR, 0, 7000)
    assert client._get_register_value(1022) == pytest.approx(700.0)


def test_a_persistent_shape_is_published_after_three_polls():
    """A genuine steady reading near a multiple of 65536 raw has this shape too, and must
    not be withheld for ever."""
    client = _client(UNSIGNED_PAIR, 2, 3)
    assert client._get_register_value(1022) is None
    assert client._get_register_value(1022) is None
    assert client._get_register_value(1022) == pytest.approx(13107.5), (
        "a shape that persists is a reading, not a glitch"
    )


def test_a_normal_reading_clears_the_suspicion():
    """Otherwise two glitches an hour apart would publish the second one."""
    client = _client(UNSIGNED_PAIR, 14, 65515)
    assert client._get_register_value(1022) is None

    client._register_cache = {1021: 0, 1022: 7000}
    assert client._get_register_value(1022) == pytest.approx(700.0)

    client._register_cache = {1021: 14, 1022: 65515}
    assert client._get_register_value(1022) is None, (
        "the counter was not reset by the good reading in between"
    )


def test_a_signed_pair_is_never_touched():
    """A signed pair carries 0xFFFF in its high word for any small negative - the same
    shape. -9 must decode as -0.9 W, not be withheld."""
    client = _client(SIGNED_PAIR, 0xFFFF, 0xFFF7, addr=100, pair=101)
    assert client._get_register_value(101) == pytest.approx(-0.9)


def test_the_underflow_path_still_owns_its_case():
    """An unsigned pair with the sign bit set is #401's case and keeps its own handling -
    this guard must not intercept it."""
    client = _client(UNSIGNED_PAIR, 0xFFE5, 0xFFE5)
    assert client._get_register_value(1022) is None
    assert client._pair_shape_suspect == {}, (
        "the shape guard claimed a reading that belongs to the underflow guard"
    )
