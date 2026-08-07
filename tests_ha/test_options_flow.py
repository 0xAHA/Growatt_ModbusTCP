"""Options flow tests.

These exist because of a specific failure. The "Max Register Block Size" selector
shipped in v1.2.0 declared as `vol.In({0: "Auto", 25: "25 registers", ...})` — keyed by
integers, with `default=0`. **The option could never be saved.**

It survived four releases. The read path was wired correctly, so code inspection looked
fine; the value simply never reached it. Two users found it independently, as two
different symptoms — "nothing is selected" (#360) and "the option had zero effect"
(#367) — and I initially told the second one the code was correct.

Nothing in the HA-free suite could have caught it: the defect is in a voluptuous schema
that only misbehaves when Home Assistant renders and submits it. That is the entire
argument for this directory existing.
"""
from __future__ import annotations

import pytest
from homeassistant.core import HomeAssistant

from custom_components.growatt_modbus.const import BLOCK_SIZE_OPTIONS


async def _open_options(hass: HomeAssistant, entry):
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return await hass.config_entries.options.async_init(entry.entry_id)


@pytest.mark.parametrize("label", list(BLOCK_SIZE_OPTIONS))
async def test_every_block_size_label_can_be_saved(
    hass: HomeAssistant, mock_entry, bypass_connection, label
):
    """The regression, stated directly: each offered choice must persist.

    Under the old schema this failed for every value — which is what made the option
    inert rather than merely awkward.
    """
    result = await _open_options(hass, mock_entry)

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "device_name": "Growatt Test",
            "inverter_series": "MIN (7-10kW)",
            "scan_interval": 60,
            "offline_scan_interval": 300,
            "invert_grid_power": False,
            "invert_battery_power": False,
            "battery_voltage_range": "Auto-detect",
            "modbus_delay": 250,
            "max_block_size": label,
        },
    )
    await hass.async_block_till_done()

    assert result["type"] == "create_entry"
    assert mock_entry.options["max_block_size"] == label


async def test_saved_block_size_reaches_the_read_path(
    hass: HomeAssistant, mock_entry, bypass_connection
):
    """Saving is only half of it — the value must arrive at the client.

    v1.2.0 wired this end correctly while the form end was broken, so verifying only the
    wiring gave a false positive. This asserts the whole chain.
    """
    from custom_components.growatt_modbus.const import resolve_block_size

    result = await _open_options(hass, mock_entry)
    await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "device_name": "Growatt Test",
            "inverter_series": "MIN (7-10kW)",
            "scan_interval": 60,
            "offline_scan_interval": 300,
            "invert_grid_power": False,
            "invert_battery_power": False,
            "battery_voltage_range": "Auto-detect",
            "modbus_delay": 250,
            "max_block_size": "25 registers",
        },
    )
    await hass.async_block_till_done()

    assert resolve_block_size(mock_entry.options["max_block_size"]) == 25


async def test_options_form_opens_with_a_valid_default(
    hass: HomeAssistant, mock_entry, bypass_connection
):
    """A default that matches no offered choice renders as nothing selected.

    That was the visible half of the bug (#360) — and because the field is Required,
    an unselected form also refuses to submit, blocking *every* option on the page.
    """
    result = await _open_options(hass, mock_entry)
    assert result["type"] == "form"
    assert result["errors"] in (None, {})


async def test_unrelated_option_can_be_changed_without_touching_block_size(
    hass: HomeAssistant, mock_entry, bypass_connection
):
    """The real user impact: a broken selector locked the whole form.

    #360 could not change scan interval, because the invalid block-size default failed
    validation for the entire submission.
    """
    result = await _open_options(hass, mock_entry)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "device_name": "Growatt Test",
            "inverter_series": "MIN (7-10kW)",
            "scan_interval": 120,
            "offline_scan_interval": 300,
            "invert_grid_power": False,
            "invert_battery_power": False,
            "battery_voltage_range": "Auto-detect",
            "modbus_delay": 250,
            "max_block_size": "Auto (recommended)",
        },
    )
    await hass.async_block_till_done()

    assert result["type"] == "create_entry"
    assert mock_entry.options["scan_interval"] == 120
