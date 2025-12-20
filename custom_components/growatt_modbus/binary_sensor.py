"""Binary sensor platform for Growatt Modbus Integration."""
import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import EntityCategory

from .const import (
    DOMAIN,
    DEVICE_TYPE_INVERTER,
)
from .coordinator import GrowattModbusCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Growatt Modbus binary sensors."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = [
        GrowattInverterOnlineSensor(coordinator, config_entry),
    ]
    
    async_add_entities(entities)


class GrowattInverterOnlineSensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor for inverter online status."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: GrowattModbusCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)

        self._config_entry = config_entry
        self._attr_name = f"{config_entry.data['name']} Inverter Online"
        self._attr_unique_id = f"{config_entry.entry_id}_inverter_online"
        self._attr_icon = "mdi:solar-power-variant"

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return self.coordinator.get_device_info(DEVICE_TYPE_INVERTER)

    @property
    def is_on(self) -> bool:
        """Return true if inverter is online (responding to Modbus)."""
        if self.coordinator.last_successful_update is None:
            return False
        
        # Consider online if last update was within 5 minutes
        time_since_update = datetime.now() - self.coordinator.last_successful_update
        return time_since_update < timedelta(minutes=5)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional state attributes."""
        if self.coordinator.last_successful_update is None:
            return None
        
        time_since_update = datetime.now() - self.coordinator.last_successful_update
        
        return {
            "last_successful_update": self.coordinator.last_successful_update.isoformat(),
            "seconds_since_update": int(time_since_update.total_seconds()),
        }