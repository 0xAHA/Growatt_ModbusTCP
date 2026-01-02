"""Number platform for Growatt Modbus Integration."""
import logging
from typing import Any

from homeassistant.components.number import NumberEntity, NumberMode
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
    """Set up Growatt Modbus number entities."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    # Get the register map for this inverter
    register_map_name = config_entry.data.get(CONF_REGISTER_MAP)
    from .const import REGISTER_MAPS
    register_map = REGISTER_MAPS.get(register_map_name, {})
    holding_registers = register_map.get('holding_registers', {})
    
    entities = []

    # Export Limit Power - only if register exists in this profile
    export_power_reg = WRITABLE_REGISTERS['export_limit_power']['register']
    if export_power_reg in holding_registers:
        entities.append(
            GrowattExportLimitPowerNumber(coordinator, config_entry)
        )
        _LOGGER.info("Export limit power control enabled (register %d found)", export_power_reg)

    # Active Power Rate - only if register exists in this profile
    active_power_reg = WRITABLE_REGISTERS['active_power_rate']['register']
    if active_power_reg in holding_registers:
        entities.append(
            GrowattActivePowerRateNumber(coordinator, config_entry)
        )
        _LOGGER.info("Active power rate control enabled (register %d found)", active_power_reg)

    if entities:
        _LOGGER.info("Created %d number entities for %s", len(entities), config_entry.data['name'])
        async_add_entities(entities)


class GrowattExportLimitPowerNumber(CoordinatorEntity, NumberEntity):
    """Number entity for export limit power percentage."""

    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = 0.0
    _attr_native_max_value = 100.0
    _attr_native_step = 0.1
    _attr_native_unit_of_measurement = "%"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: GrowattModbusCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)

        self._config_entry = config_entry
        self._attr_name = f"{config_entry.data['name']} Export Limit Power"
        self._attr_unique_id = f"{config_entry.entry_id}_export_limit_power"
        self._attr_icon = "mdi:speedometer"

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        # Determine device based on control type
        device_type = get_device_type_for_control('export_limit_power')
        return self.coordinator.get_device_info(device_type)

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        data = self.coordinator.data
        if data is None:
            return None
        
        # Read raw value (0-1000) and convert to percentage (0-100.0)
        raw_value = getattr(data, 'export_limit_power', None)
        if raw_value is None:
            return None
        
        # Apply scale: raw is 0-1000, display as 0-100.0%
        scale = WRITABLE_REGISTERS['export_limit_power']['scale']
        return round(float(raw_value) * scale, 1)

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        # Convert percentage (0-100.0) to raw value (0-1000)
        scale = WRITABLE_REGISTERS['export_limit_power']['scale']
        raw_value = int(value / scale)
        
        # Validate range
        valid_range = WRITABLE_REGISTERS['export_limit_power']['valid_range']
        raw_value = max(valid_range[0], min(raw_value, valid_range[1]))
        
        # Write to Modbus register
        register = WRITABLE_REGISTERS['export_limit_power']['register']
        success = await self.hass.async_add_executor_job(
            self.coordinator.modbus_client.write_register,
            register,
            raw_value
        )
        
        if success:
            _LOGGER.info("Set export_limit_power to %.1f%% (raw=%d)", value, raw_value)
            # Request immediate refresh to show new value
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error("Failed to write export_limit_power")


class GrowattActivePowerRateNumber(CoordinatorEntity, NumberEntity):
    """Number entity for active power rate (max output power %)."""

    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = 0.0
    _attr_native_max_value = 100.0
    _attr_native_step = 1.0
    _attr_native_unit_of_measurement = "%"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: GrowattModbusCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)

        self._config_entry = config_entry
        self._attr_name = f"{config_entry.data['name']} Active Power Rate"
        self._attr_unique_id = f"{config_entry.entry_id}_active_power_rate"
        self._attr_icon = "mdi:speedometer"

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        # Determine device based on control type (should go to Solar device)
        device_type = get_device_type_for_control('active_power_rate')
        return self.coordinator.get_device_info(device_type)

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        data = self.coordinator.data
        if data is None:
            return None

        # Read raw value (0-100) directly as percentage
        raw_value = getattr(data, 'active_power_rate', None)
        if raw_value is None:
            return None

        # Direct percentage value (scale = 1)
        return float(raw_value)

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        # Direct integer value (0-100%)
        raw_value = int(value)

        # Validate range
        valid_range = WRITABLE_REGISTERS['active_power_rate']['valid_range']
        raw_value = max(valid_range[0], min(raw_value, valid_range[1]))

        # Write to Modbus register
        register = WRITABLE_REGISTERS['active_power_rate']['register']
        success = await self.hass.async_add_executor_job(
            self.coordinator.modbus_client.write_register,
            register,
            raw_value
        )

        if success:
            _LOGGER.info("Set active_power_rate to %d%%", raw_value)
            # Request immediate refresh to show new value
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error("Failed to write active_power_rate")