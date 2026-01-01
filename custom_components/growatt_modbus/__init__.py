"""
Growatt Modbus Integration for Home Assistant
"""
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers import config_validation as cv


from .const import (
    DOMAIN,
    CONF_DEVICE_STRUCTURE_VERSION,
    CURRENT_DEVICE_STRUCTURE_VERSION,
)
from .coordinator import GrowattModbusCoordinator
from .diagnostic import async_setup_services

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.SELECT, Platform.NUMBER]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Growatt Modbus integration."""
    hass.data.setdefault(DOMAIN, {})
    
    # Set up diagnostic service
    await async_setup_services(hass)
    
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Growatt Modbus from a config entry."""

    # Check if we need to migrate device structure
    current_version = entry.data.get(CONF_DEVICE_STRUCTURE_VERSION, 1)

    if current_version < CURRENT_DEVICE_STRUCTURE_VERSION:
        _LOGGER.info(
            "Upgrading device structure from v%s to v%s for %s",
            current_version,
            CURRENT_DEVICE_STRUCTURE_VERSION,
            entry.title,
        )

        # Update version in config entry
        new_data = {**entry.data}
        new_data[CONF_DEVICE_STRUCTURE_VERSION] = CURRENT_DEVICE_STRUCTURE_VERSION
        hass.config_entries.async_update_entry(entry, data=new_data)

        _LOGGER.info(
            "Device structure upgraded successfully. "
            "Entities will now be organized into separate devices: "
            "Inverter (with system controls), Solar, Grid, Load, and Battery (if present)"
        )

    coordinator = GrowattModbusCoordinator(hass, entry)

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)