"""Base entity for the Growatt Modbus integration.

Every entity across the five platforms repeated the same three things: storing the
config entry, composing a unique ID as `{entry_id}_{key}`, and returning
`coordinator.get_device_info(...)`. That last one existed 22 times, differing only in
how the device type was derived.

Subclasses work out their own device type — some from the control name, some fixed —
and pass it up. Everything after that is shared.

Note on `available`: only the sensor platform overrides it, gating on
`coordinator.is_online` as well as `last_update_success` so entities go unavailable
when the inverter stops responding rather than sitting on stale values (Issue #357).
The other platforms use CoordinatorEntity's default, which is correct for them —
controls should remain settable while a read is failing. That difference is
deliberate, so it is not hoisted here.
"""
from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import GrowattModbusCoordinator


class GrowattEntity(CoordinatorEntity[GrowattModbusCoordinator]):
    """Common base for all Growatt Modbus entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: GrowattModbusCoordinator,
        config_entry: ConfigEntry,
        unique_key: str,
        device_type: str,
    ) -> None:
        """Initialise shared entity state.

        Args:
            coordinator: The data coordinator for this config entry.
            config_entry: Used for the unique ID and for options lookups in
                subclasses that need them.
            unique_key: Stable per-entity suffix. Combined with the entry id to form
                the unique ID — this is the anchor the v0.6.7 entity-ID migration
                relies on, so it must not change for an existing entity.
            device_type: Which sub-device this entity belongs to (inverter, solar,
                grid, load, battery). See const.DEVICE_TYPE_*.
        """
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._device_type = device_type
        self._attr_unique_id = f"{config_entry.entry_id}_{unique_key}"

    @property
    def device_info(self) -> dict[str, Any]:
        """Return the sub-device this entity is attached to."""
        return self.coordinator.get_device_info(self._device_type)
