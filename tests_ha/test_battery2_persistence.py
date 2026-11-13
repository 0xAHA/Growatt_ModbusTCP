"""A second pack in standby must not lose its entities across a restart (#500).

MID 25KTL3-XH with a 10 kWh and a 20 kWh APX. When pack 2 went into deep standby its
voltage register (input 31314) read 0, and after the entry was set up again the Battery 2
sensors were "no longer provided" until the pack woke.

Their creation is gated on that voltage, and setup only ever sees the empty placeholder,
so the gate is decided by the first poll. Once a second pack has been registered for an
entry, its sensors are created at setup and show unavailable while the pack is asleep.
"""
from __future__ import annotations

from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.growatt_modbus.const import DOMAIN

from .conftest import setup_entry


def _mod_entry() -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        title="Growatt MID",
        data={
            "name": "Growatt MID",
            "connection_type": "tcp",
            "host": "192.0.2.11",
            "port": 502,
            "slave_id": 1,
            "inverter_series": "mod_6000_15000tl3_xh",
            "register_map": "MOD_6000_15000TL3_XH",
            "vpp_protocol_confirmed": False,
        },
        options={"scan_interval": 60, "modbus_delay": 250},
    )


def _register(hass: HomeAssistant, entry: MockConfigEntry, key: str) -> None:
    """What a previous session with pack 2 awake would have left in the registry."""
    er.async_get(hass).async_get_or_create(
        "sensor", DOMAIN, f"{entry.entry_id}_{key}", config_entry=entry,
    )


async def test_a_pack_seen_before_is_created_while_it_sleeps(
    hass: HomeAssistant, bypass_connection
):
    entry = _mod_entry()
    entry.add_to_hass(hass)
    _register(hass, entry, "battery2_soc")

    # Already added above (the registry entry needs it), so not via setup_entry().
    assert await hass.config_entries.async_setup(entry.entry_id), entry.reason
    await hass.async_block_till_done()

    # Looked up again: setup's entity-ID migration renames the registered ID.
    entity_id = er.async_get(hass).async_get_entity_id(
        "sensor", DOMAIN, f"{entry.entry_id}_battery2_soc")
    assert entity_id is not None, "the registry entry was removed"
    state = hass.states.get(entity_id)
    assert state is not None, "Battery 2 SOC was not created"
    assert not state.attributes.get("restored"), (
        "the entity is only a restored placeholder - 'no longer provided'"
    )
    assert state.state == STATE_UNAVAILABLE


async def test_a_system_without_a_second_pack_still_gets_none(
    hass: HomeAssistant, bypass_connection
):
    """The gate exists to keep these off single-pack systems; nothing registered, nothing
    created."""
    entry = _mod_entry()
    await setup_entry(hass, entry)

    registry = er.async_get(hass)
    assert registry.async_get_entity_id(
        "sensor", DOMAIN, f"{entry.entry_id}_battery2_soc") is None
