"""Select platform for Growatt Modbus Integration."""
import logging
from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import EntityCategory

from .const import (
    DOMAIN,
    WRITABLE_REGISTERS,
    CONF_REGISTER_MAP,
    DEVICE_TYPE_INVERTER,
)
from .coordinator import GrowattModbusCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Growatt Modbus select entities."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    # Get the register map for this inverter
    register_map_name = config_entry.data.get(CONF_REGISTER_MAP)
    from .const import REGISTER_MAPS
    register_map = REGISTER_MAPS.get(register_map_name, {})
    holding_registers = register_map.get('holding_registers', {})
    
    entities = []
    
    # Export Limit Mode - only if register exists in this profile
    export_mode_reg = WRITABLE_REGISTERS['export_limit_mode']['register']
    if export_mode_reg in holding_registers:
        entities.append(
            GrowattExportLimitModeSelect(coordinator, config_entry)
        )
        _LOGGER.info("Export limit mode control enabled (register %d found)", export_mode_reg)
    
    if entities:
        _LOGGER.info("Created %d select entities for %s", len(entities), config_entry.data['name'])
        async_add_entities(entities)


class GrowattExportLimitModeSelect(CoordinatorEntity, SelectEntity):
    """Select entity for export limit mode."""

    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: GrowattModbusCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator)

        self._config_entry = config_entry
        self._attr_name = f"{config_entry.data['name']} Export Limit Mode"
        self._attr_unique_id = f"{config_entry.entry_id}_export_limit_mode"
        self._attr_icon = "mdi:transmission-tower-export"

        # Set options from const.py
        self._attr_options = list(WRITABLE_REGISTERS['export_limit_mode']['options'].values())

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        # Export limit is a system-wide inverter setting
        return self.coordinator.get_device_info(DEVICE_TYPE_INVERTER)

    @property
    def current_option(self) -> str | None:
        """Return the current selected option."""
        data = self.coordinator.data
        if data is None:
            return None
        
        # Read raw value from coordinator data
        raw_value = getattr(data, 'export_limit_mode', None)
        if raw_value is None:
            return None
        
        # Map numeric value to friendly name
        options_map = WRITABLE_REGISTERS['export_limit_mode']['options']
        return options_map.get(int(raw_value))

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        # Reverse lookup: friendly name -> numeric value
        options_map = WRITABLE_REGISTERS['export_limit_mode']['options']
        value = next((k for k, v in options_map.items() if v == option), None)
        
        if value is None:
            _LOGGER.error("Invalid option selected: %s", option)
            return
        
        # Write to Modbus register
        register = WRITABLE_REGISTERS['export_limit_mode']['register']
        success = await self.hass.async_add_executor_job(
            self.coordinator.modbus_client.write_register,
            register,
            value
        )
        
        if success:
            _LOGGER.info("Set export_limit_mode to %s (value=%d)", option, value)
            # Request immediate refresh to show new value
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error("Failed to write export_limit_mode")