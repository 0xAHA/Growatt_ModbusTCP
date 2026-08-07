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

from .conftest import setup_entry


async def _open_options(hass: HomeAssistant, entry):
    await setup_entry(hass, entry)
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


class _StubClient:
    """Minimal stand-in for GrowattModbus — only what _apply_client_options touches."""

    def __init__(self):
        self._battery_voltage_range = None
        self._block_size_override = None
        self._default_min_read_interval = None
        self._backed_off = False
        self.min_read_interval = None


@pytest.mark.parametrize("label,expected", list(BLOCK_SIZE_OPTIONS.items()))
async def test_saved_block_size_reaches_the_client(
    hass: HomeAssistant, mock_entry, bypass_connection, label, expected
):
    """Saving is only half of it — the value must arrive at the client.

    The previous version of this test called resolve_block_size() on the stored option
    itself, which proved only that the helper works. It was a tautology, and it passed
    happily while `_fetch_data` still did `int(_bs)` on the label and raised ValueError
    on every poll for anyone not on a shared connection (#367).

    This drives the coordinator's own code instead, which is the part that was broken.
    Both fetch paths now route through `_apply_client_options`, so this covers both.
    """
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
            "max_block_size": label,
        },
    )
    await hass.async_block_till_done()

    coordinator = mock_entry.runtime_data
    coordinator._client = _StubClient()

    # The regression was an unhandled ValueError here, not a wrong value.
    coordinator._apply_client_options()

    # 0 ("Auto") means "defer to the profile", which is carried as None, not 0.
    assert coordinator._client._block_size_override == (expected or None)


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
