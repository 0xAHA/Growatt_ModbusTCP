"""Binary sensor platform for Growatt Modbus Integration."""
import logging
from datetime import datetime
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
from .entity import GrowattEntity

_LOGGER = logging.getLogger(__name__)

# Read-only, coordinator-backed — see sensor.py.
PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Growatt Modbus binary sensors."""
    coordinator = config_entry.runtime_data
    
    entities = [
        GrowattInverterOnlineSensor(coordinator, config_entry),
    ]
    
    async_add_entities(entities)


class GrowattInverterOnlineSensor(GrowattEntity, BinarySensorEntity):
    """Binary sensor for inverter online status."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: GrowattModbusCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the binary sensor."""
        # unique_key "inverter_online" preserves the existing unique ID exactly.
        super().__init__(coordinator, config_entry, "inverter_online", DEVICE_TYPE_INVERTER)

        self._attr_name = "Inverter Online"
        self._attr_icon = "mdi:solar-power-variant"

    @property
    def is_on(self) -> bool:
        """Return true if inverter is online (responding to Modbus)."""
        return self.coordinator.is_online

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