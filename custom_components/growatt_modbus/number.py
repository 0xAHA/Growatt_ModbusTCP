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

    # Auto-generate number entities for all writable registers without 'options'
    for control_name, control_config in WRITABLE_REGISTERS.items():
        if 'options' in control_config:
            continue  # Skip select controls

        # WIT-specific: avoid exposing legacy output limiter controls as 'Active Power' sliders
        # Only expose VPP remote controls (201/202/203) for WIT.
        if register_map_name and register_map_name.startswith('WIT_') and control_name in {'max_output_power_rate'}:
            continue

        register_num = control_config['register']
        if register_num not in holding_registers:
            continue  # Skip if register not in this profile

        entities.append(
            GrowattGenericNumber(coordinator, config_entry, control_name, control_config)
        )
        _LOGGER.info("%s control enabled (register %d found)", control_name, register_num)

    if entities:
        _LOGGER.info("Created %d number entities for %s", len(entities), config_entry.data['name'])
        async_add_entities(entities)


class GrowattGenericNumber(CoordinatorEntity, NumberEntity):
    """Generic number entity for any numeric control."""

    _attr_mode = NumberMode.SLIDER
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: GrowattModbusCoordinator,
        config_entry: ConfigEntry,
        control_name: str,
        control_config: dict,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)

        self._config_entry = config_entry
        self._control_name = control_name
        self._control_config = control_config

        # Generate friendly name
        friendly_overrides = {
            'active_power_rate': 'VPP Active Power Rate',
            'export_limit_w': 'VPP Export Limit (W)',
            'max_output_power_rate': 'Max Output Power Rate',
        }
        friendly_name = friendly_overrides.get(control_name, control_name.replace('_', ' ').title())
        self._attr_name = f"{config_entry.data['name']} {friendly_name}"
        self._attr_unique_id = f"{config_entry.entry_id}_{control_name}"

        # Set icon
        self._attr_icon = self._get_icon(control_name)

        # Configure range and unit
        self._configure_range_and_unit()

    def _get_icon(self, control_name: str) -> str:
        """Get icon based on control name."""
        icon_map = {
            'export_limit_power': 'mdi:speedometer',
            'active_power_rate': 'mdi:speedometer',
            'ac_charge_current': 'mdi:current-ac',
            'gen_charge_current': 'mdi:current-ac',
            'bat_low_to_uti': 'mdi:battery-alert',
            'ac_to_bat_volt': 'mdi:battery-charging',
        }
        return icon_map.get(control_name, 'mdi:tune')

    def _configure_range_and_unit(self):
        """Configure min/max/step/unit based on control config and battery type."""
        valid_range = self._control_config.get('valid_range', (0, 100))
        scale = self._control_config.get('scale', 1)
        unit = self._control_config.get('unit', '')

        # Check if battery-dependent
        if self._control_config.get('battery_dependent', False):
            # Read battery type from coordinator data
            battery_type = getattr(self.coordinator.data, 'battery_type', None) if self.coordinator.data else None
            is_lithium = (battery_type == 3)  # 3 = Lithium

            if is_lithium:
                # Lithium: 0-1000 raw = 0% - 100%
                self._attr_native_min_value = 0.0
                self._attr_native_max_value = 100.0
                self._attr_native_step = 1.0
                self._attr_native_unit_of_measurement = "%"
            else:
                # Non-Lithium: 200-640 raw = 20.0V - 64.0V
                self._attr_native_min_value = 20.0
                self._attr_native_max_value = 64.0
                self._attr_native_step = 0.1
                self._attr_native_unit_of_measurement = "V"
        else:
            # Normal number control
            self._attr_native_min_value = float(valid_range[0]) * scale
            self._attr_native_max_value = float(valid_range[1]) * scale

            # Check for explicit step override first
            if 'step' in self._control_config:
                self._attr_native_step = float(self._control_config['step'])
            else:
                # Determine step based on scale
                if scale >= 1:
                    self._attr_native_step = 1.0
                elif scale == 0.1:
                    self._attr_native_step = 0.1
                else:
                    self._attr_native_step = scale

            self._attr_native_unit_of_measurement = unit

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        device_type = get_device_type_for_control(self._control_name)
        return self.coordinator.get_device_info(device_type)

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        data = self.coordinator.data
        if data is None:
            return None

        raw_value = getattr(data, self._control_name, None)
        if raw_value is None:
            return None

        # Apply scale
        scale = self._control_config.get('scale', 1)
        return round(float(raw_value) * scale, 2)

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        scale = self._control_config.get('scale', 1)

        # Convert display value to raw value
        raw_value = int(value / scale)

        # Validate range
        valid_range = self._control_config.get('valid_range', (0, 100))
        raw_value = max(valid_range[0], min(raw_value, valid_range[1]))

        # Write to Modbus register
        register = self._control_config['register']
        success = await self.hass.async_add_executor_job(
            self.coordinator.modbus_client.write_register,
            register,
            raw_value
        )

        if success:
            _LOGGER.info("Set %s to %.1f (raw=%d)", self._control_name, value, raw_value)
            # Request immediate refresh to show new value
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error("Failed to write %s", self._control_name)


# Legacy class for backwards compatibility (remove in future version)
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
