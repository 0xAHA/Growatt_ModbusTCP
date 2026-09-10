"""Setup asks what the inverter is reached through, and seeds timings to match (#433).

A ShineWiFi-X reporter's entities went unavailable a minute or two after setup, with
transaction IDs coming back exactly one behind. The defaults are tuned for a dedicated
RS485 gateway - one 125-register read, a 10 s timeout, 250 ms between requests - and on a
Growatt WiFi dongle that is enough to make a read time out. pymodbus then re-sends with the
SAME transaction ID, the dongle answers both copies, and every read from then on receives
the previous read's answer.

Every setting that avoids it was already adjustable. What was missing was any way for a new
owner to know which ones mattered before it broke, so the question is now asked once at
setup.

Two properties matter more than the numbers, and both are tested here:

  * an unrecognised or absent answer gets the standard timings, never an empty dict - a
    stored value from a future version must not leave an entry with no scan interval
  * changing the answer later must not overwrite tuning the user found themselves. Someone
    who spent an evening arriving at "5 registers" cannot lose it by answering a question
    about their adapter, so only fields still at their stored value are re-seeded.

The numbers themselves are starting points from field reports, not measured optima, so the
assertions on them are about shape - slower than standard, within the form's own limits -
rather than exact equality with a constant this file would just be restating.
"""
from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

_const = importlib.import_module("growatt_under_test.const")

COMPONENT = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"

TUNED_FIELDS = ("scan_interval", "timeout", "modbus_delay", "max_block_size")

STANDARD = _const.GATEWAY_TYPE_STANDARD
DONGLE = _const.GATEWAY_TYPE_GROWATT_DONGLE
X2 = _const.GATEWAY_TYPE_SHINEWILAN_X2


def test_every_choice_sets_every_field():
    """A preset missing a field would leave that entry on whatever the read path defaults
    to, which is how the manual setup path ended up with no modbus_delay at all."""
    for name, tuning in _const.GATEWAY_PROFILES.items():
        assert set(tuning) == set(TUNED_FIELDS), f"{name} sets {sorted(tuning)}"


def test_the_standard_choice_is_todays_defaults():
    """Answering "dedicated gateway or not sure" must change nothing for anybody. If this
    drifts, every new install silently gets different timings than the docs describe."""
    assert _const.GATEWAY_PROFILES[STANDARD] == {
        "scan_interval": 60,
        "timeout": 10,
        "modbus_delay": 250,
        "max_block_size": "Auto (recommended)",
    }


def test_an_unknown_answer_falls_back_to_standard_not_to_nothing():
    """THE property. An empty dict here would create an entry with no scan interval."""
    for answer in (None, "", "something a later version wrote", "ShineWiFi-Z"):
        assert _const.gateway_tuning(answer) == _const.GATEWAY_PROFILES[STANDARD], answer


def test_the_dongle_preset_is_slower_in_every_dimension():
    """The whole point is to keep a read short enough to be answered before the timeout,
    and to leave the device alone between reads."""
    standard = _const.GATEWAY_PROFILES[STANDARD]
    dongle = _const.GATEWAY_PROFILES[DONGLE]

    assert dongle["scan_interval"] > standard["scan_interval"]
    assert dongle["timeout"] > standard["timeout"]
    assert dongle["modbus_delay"] > standard["modbus_delay"]
    assert _const.resolve_block_size(dongle["max_block_size"]) > 0, (
        "the dongle preset left block size on Auto, so the 125-register read that times out "
        "is still being made"
    )
    assert _const.resolve_block_size(dongle["max_block_size"]) < 125


def test_the_x2_preset_slows_the_rate_without_shrinking_the_reads():
    """Documented limitation on the X2 is sustained polling load, not frame size - nothing
    has shown it truncates. Lowering block size would cost reads per poll for nothing."""
    x2 = _const.GATEWAY_PROFILES[X2]
    assert x2["scan_interval"] > _const.GATEWAY_PROFILES[STANDARD]["scan_interval"]
    assert _const.resolve_block_size(x2["max_block_size"]) == 0


@pytest.mark.parametrize("name", list(_const.GATEWAY_PROFILES))
def test_every_preset_is_accepted_by_the_options_form(name):
    """A preset outside the form's own validation would be stored and then refuse to save
    on the next visit - the failure mode of the v1.2.0 block-size selector."""
    tuning = _const.GATEWAY_PROFILES[name]

    assert 5 <= tuning["scan_interval"] <= 300
    assert 1 <= tuning["timeout"] <= 60
    assert 50 <= tuning["modbus_delay"] <= 1000
    assert tuning["max_block_size"] in _const.BLOCK_SIZE_OPTIONS, (
        "block size presets are stored as the dropdown's label, not its integer - the "
        "frontend submits strings and an int never matches (#360)"
    )


def _apply_change(stored: dict, submitted: dict) -> dict:
    """The options-flow re-seed rule, extracted from config_flow.py by behaviour.

    Mirrors: on a changed gateway answer, re-seed the fields still sitting at their stored
    value; leave anything edited in the same submission alone.
    """
    new_options = {**stored, **submitted}
    previous = stored.get(_const.CONF_GATEWAY_TYPE, STANDARD)
    selected = submitted.get(_const.CONF_GATEWAY_TYPE)
    if selected and selected != previous:
        for field, value in _const.gateway_tuning(selected).items():
            if submitted.get(field, stored.get(field)) != stored.get(field):
                continue
            new_options[field] = value
    return new_options


def test_the_shipped_code_still_implements_that_rule():
    """The test above runs extracted logic, so this pins the component to it."""
    source = (COMPONENT / "config_flow.py").read_text(encoding="utf-8")
    assert "_selected_gateway != _previous_gateway" in source, (
        "the options flow no longer re-seeds on a changed gateway answer"
    )
    assert "CONF_GATEWAY_TYPE, GATEWAY_TYPE_STANDARD)" in source, (
        "an entry with nothing stored no longer reads as 'standard', so the first save "
        "after upgrading counts as a change and re-seeds timings the user chose"
    )
    assert "if _submitted != _stored:" in source, (
        "the options flow no longer protects fields the user edited in the same save - "
        "answering a question about the adapter would overwrite their own tuning"
    )


def test_changing_the_answer_applies_the_new_timings():
    stored = {_const.CONF_GATEWAY_TYPE: STANDARD, **_const.GATEWAY_PROFILES[STANDARD]}
    submitted = {_const.CONF_GATEWAY_TYPE: DONGLE, **_const.GATEWAY_PROFILES[STANDARD]}

    result = _apply_change(stored, submitted)

    for field, value in _const.GATEWAY_PROFILES[DONGLE].items():
        assert result[field] == value, field


def test_a_value_edited_in_the_same_save_wins():
    """THE guard. He picked the dongle preset but also typed his own block size; the block
    size he typed must survive and the rest of the preset must still apply."""
    stored = {_const.CONF_GATEWAY_TYPE: STANDARD, **_const.GATEWAY_PROFILES[STANDARD]}
    submitted = {
        _const.CONF_GATEWAY_TYPE: DONGLE,
        **_const.GATEWAY_PROFILES[STANDARD],
        "max_block_size": "5 registers",
    }

    result = _apply_change(stored, submitted)

    assert result["max_block_size"] == "5 registers", "the user's own tuning was overwritten"
    assert result["modbus_delay"] == _const.GATEWAY_PROFILES[DONGLE]["modbus_delay"]


def test_saving_without_changing_the_answer_touches_nothing():
    """An existing entry has no stored gateway type and the form defaults to standard, so
    the first save after upgrading must not re-seed anyone's timings."""
    stored = {"scan_interval": 300, "timeout": 45, "modbus_delay": 900,
              "max_block_size": "5 registers"}
    submitted = {_const.CONF_GATEWAY_TYPE: STANDARD, **stored}

    result = _apply_change(stored, submitted)

    for field, value in stored.items():
        assert result[field] == value, (
            f"{field} was changed on an ordinary save by an entry that predates this field"
        )


def test_the_setup_form_offers_the_question():
    source = (COMPONENT / "config_flow.py").read_text(encoding="utf-8")
    tcp_step = source.split("async def async_step_tcp")[1].split("async def async_step_serial")[0]
    assert "CONF_GATEWAY_TYPE" in tcp_step, "the TCP setup step does not ask"
    assert "vol.In(list(GATEWAY_PROFILES))" in tcp_step, (
        "the field is not constrained to the known choices"
    )


def test_both_translation_files_name_the_field():
    """An unnamed config field shows as its raw key. Nothing local catches that."""
    for name in ("strings.json", "translations/en.json"):
        data = json.loads((COMPONENT / name).read_text(encoding="utf-8"))
        for section, step in (("config", "tcp"), ("options", "init")):
            fields = data[section]["step"][step]["data"]
            assert fields.get(_const.CONF_GATEWAY_TYPE), (
                f"{name}: {section}.{step} has no label for {_const.CONF_GATEWAY_TYPE}"
            )
