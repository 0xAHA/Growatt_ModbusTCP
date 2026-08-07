"""Setup and teardown tests.

These cover what I have been asking a user to confirm by hand after every release —
"does it load, does it reload" — which is the check that catches a broken `runtime_data`
migration or entity base class before anyone installs it.

v1.3.1 and v1.3.2 both shipped as pre-releases purely because I could not answer that
question locally.
"""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from custom_components.growatt_modbus.const import DOMAIN


async def test_entry_sets_up(hass: HomeAssistant, mock_entry, bypass_connection):
    mock_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_entry.state is ConfigEntryState.LOADED


async def test_coordinator_is_on_runtime_data(
    hass: HomeAssistant, mock_entry, bypass_connection
):
    """v1.3.1 moved the coordinator off `hass.data[DOMAIN]`.

    `hass.data[DOMAIN]` should now hold only the cross-entry connection registry — the
    two used to be mixed, which is why code walking it needed a defensive check.
    """
    mock_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()

    assert getattr(mock_entry, "runtime_data", None) is not None
    assert mock_entry.entry_id not in hass.data.get(DOMAIN, {})


async def test_entry_unloads(hass: HomeAssistant, mock_entry, bypass_connection):
    """The unload path can only fail on unload — a load test cannot reach it."""
    mock_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()

    assert await hass.config_entries.async_unload(mock_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_entry.state is ConfigEntryState.NOT_LOADED


async def test_entry_reloads(hass: HomeAssistant, mock_entry, bypass_connection):
    """Reload is unload followed by setup, so it exercises both directions."""
    mock_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()

    assert await hass.config_entries.async_reload(mock_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_entry.state is ConfigEntryState.LOADED


async def test_entities_are_created(hass: HomeAssistant, mock_entry, bypass_connection):
    """Guards the GrowattEntity migration (v1.3.2).

    A wrong base class shows up as entities silently not being created — the
    integration still loads, so a load check would pass.
    """
    mock_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()

    entities = [
        s for s in hass.states.async_all()
        if s.entity_id.startswith(("sensor.", "binary_sensor."))
    ]
    assert entities, "no entities were created"


async def test_diagnostics_can_be_produced(
    hass: HomeAssistant, mock_entry, bypass_connection
):
    """Diagnostics must never raise — it is needed when things are already broken."""
    from custom_components.growatt_modbus.diagnostics import (
        async_get_config_entry_diagnostics,
    )

    mock_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()

    diagnostics = await async_get_config_entry_diagnostics(hass, mock_entry)
    assert "entry" in diagnostics
    assert "coordinator" in diagnostics
    # Host is redacted — users paste these into public issues.
    assert diagnostics["entry"]["data"].get("host") != "192.0.2.10"
