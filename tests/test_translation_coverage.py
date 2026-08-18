"""Every field on the options form needs a label, and the two string files must agree.

Neither of these fails on its own. A field with no translation renders as its raw key —
`max_block_size` sat on the options page as exactly that, and the only cost was that it
looked unfinished and told the user nothing about what it does. `strings.json` and
`translations/en.json` drifting apart is quieter still: `en.json` is what Home Assistant
actually loads, so a field added only to `strings.json` shows a raw key while one added only
to `en.json` works fine and hides the omission until a translator or a lint pass finds it.

Both happened here. The connection fields added for #383 went into `en.json` alone.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

COMPONENT = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
STRINGS = json.loads((COMPONENT / "strings.json").read_text(encoding="utf-8"))
EN = json.loads((COMPONENT / "translations" / "en.json").read_text(encoding="utf-8"))
CONFIG_FLOW = (COMPONENT / "config_flow.py").read_text(encoding="utf-8")

# Constants used as schema keys, resolved to the string the form actually sees.
CONF_VALUES = {
    "CONF_DEVICE_PATH": "device_path",
    "CONF_BAUDRATE": "baudrate",
    "CONF_INVERTER_SERIES": "inverter_series",
    "CONF_SLAVE_ID": "slave_id",
    "CONF_HOST": "host",
    "CONF_PORT": "port",
    "CONF_NAME": "name",
}


def _all_keys(node, prefix: str = "") -> set[str]:
    found: set[str] = set()
    if isinstance(node, dict):
        for key, value in node.items():
            path = f"{prefix}.{key}" if prefix else key
            found.add(path)
            found |= _all_keys(value, path)
    return found


def _options_schema_fields() -> set[str]:
    """Field names declared on the options form, literals and constants alike."""
    start = CONFIG_FLOW.index("options_schema = vol.Schema({")
    end = CONFIG_FLOW.index("return self.async_show_form", start)
    region = CONFIG_FLOW[start:end]

    fields = set(re.findall(r'vol\.(?:Required|Optional)\(\s*"([a-z_0-9]+)"', region))
    for const in re.findall(r'vol\.(?:Required|Optional)\(\s*(CONF_[A-Z_]+)', region):
        if const in CONF_VALUES:
            fields.add(CONF_VALUES[const])
    return fields


def test_the_two_string_files_agree():
    """en.json is what Home Assistant loads; strings.json is the source translators work
    from. A key in one and not the other is invisible until someone notices a raw key on
    the page."""
    difference = _all_keys(STRINGS) ^ _all_keys(EN)
    assert not difference, (
        f"strings.json and translations/en.json have diverged: {sorted(difference)}"
    )


def test_the_options_form_declares_something_to_check():
    """Guards the extractor itself. If the schema is rewritten in a way this cannot parse,
    the coverage test below would pass by finding nothing."""
    fields = _options_schema_fields()
    assert len(fields) >= 8, f"only found {len(fields)} option fields: {sorted(fields)}"
    assert "max_block_size" in fields, "the extractor is not seeing literal-keyed fields"
    assert "device_path" in fields, "the extractor is not resolving CONF_ constants"


@pytest.mark.parametrize("field", sorted(_options_schema_fields()))
def test_every_options_field_has_a_label(field):
    labels = EN["options"]["step"]["init"].get("data", {})
    assert field in labels, (
        f"the options form shows a field named {field!r} with no translation, so Home "
        f"Assistant renders the raw key"
    )


def test_declared_error_keys_are_translated():
    """An untranslated error renders as its key, which is worse than useless at the moment
    something has gone wrong."""
    raised = set(re.findall(r'errors\["base"\]\s*=\s*"([a-z_0-9]+)"', CONFIG_FLOW))
    translated = set(EN.get("options", {}).get("error", {})) | set(
        EN.get("config", {}).get("error", {})
    )
    missing = raised - translated
    assert not missing, f"error keys raised but never translated: {sorted(missing)}"
