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
    get_device_type_for_control,
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

    # Auto-generate select entities for all writable registers with 'options'
    for control_name, control_config in WRITABLE_REGISTERS.items():
        if 'options' not in control_config:
            continue  # Skip number controls

        register_num = control_config['register']
        if register_num not in holding_registers:
            continue  # Skip if register not in this profile

        entities.append(
            GrowattGenericSelect(coordinator, config_entry, control_name, control_config)
        )
        _LOGGER.info("%s control enabled (register %d found)", control_name, register_num)

    if entities:
        _LOGGER.info("Created %d select entities for %s", len(entities), config_entry.data['name'])
        async_add_entities(entities)


class GrowattGenericSelect(CoordinatorEntity, SelectEntity):
    """Generic select entity for any control with options."""

    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: GrowattModbusCoordinator,
        config_entry: ConfigEntry,
        control_name: str,
        control_config: dict,
    ) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator)

        self._config_entry = config_entry
        self._control_name = control_name
        self._control_config = control_config

        # Generate friendly name (e.g., "output_config" -> "Output Config")
        friendly_name = control_name.replace('_', ' ').title()
        self._attr_name = f"{config_entry.data['name']} {friendly_name}"
        self._attr_unique_id = f"{config_entry.entry_id}_{control_name}"

        # Set icon based on control type
        self._attr_icon = self._get_icon(control_name)

        # Set options from control_config
        self._attr_options = list(control_config['options'].values())

    def _get_icon(self, control_name: str) -> str:
        """Get icon based on control name."""
        icon_map = {
            'export_limit_mode': 'mdi:transmission-tower-export',
            'output_config': 'mdi:power-plug',
            'charge_config': 'mdi:battery-charging',
            'ac_input_mode': 'mdi:power-socket',
            'battery_type': 'mdi:battery',
        }
        return icon_map.get(control_name, 'mdi:tune')

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        # Determine device based on control type
        device_type = get_device_type_for_control(self._control_name)
        return self.coordinator.get_device_info(device_type)

    @property
    def current_option(self) -> str | None:
        """Return the current selected option."""
        data = self.coordinator.data
        if data is None:
            return None

        # Read raw value from coordinator data
        raw_value = getattr(data, self._control_name, None)
        if raw_value is None:
            return None

        # Map numeric value to friendly name
        options_map = self._control_config['options']
        return options_map.get(int(raw_value))

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        # Reverse lookup: friendly name -> numeric value
        options_map = self._control_config['options']
        value = next((k for k, v in options_map.items() if v == option), None)

        if value is None:
            _LOGGER.error("Invalid option selected: %s", option)
            return

        # Write to Modbus register
        register = self._control_config['register']
        success = await self.hass.async_add_executor_job(
            self.coordinator.modbus_client.write_register,
            register,
            value
        )

        if success:
            _LOGGER.info("Set %s to %s (value=%d)", self._control_name, option, value)
            # Request immediate refresh to show new value
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error("Failed to write %s", self._control_name)