"""Select platform for Growatt Modbus Integration."""
import logging
import asyncio
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
    
    entities: list[SelectEntity] = []

    # ---------------------------------------------------------------------
    # WIT-specific control (VPP remote work_mode) - only when WIT register map
    # is selected. This avoids relying on global WRITABLE_REGISTERS collisions.
    # ---------------------------------------------------------------------
    is_wit = str(register_map_name).upper() == "WIT_4000_15000TL3"
    if is_wit:
        if 202 in holding_registers:
            entities.append(GrowattWitWorkModeSelect(coordinator, config_entry))

        if entities:
            entry_name = config_entry.data.get("name", config_entry.title)
            _LOGGER.info("Created %d WIT select entities for %s", len(entities), entry_name)
            async_add_entities(entities)
        return

    # ---------------------------------------------------------------------
    # Non-WIT: auto-generate selects from WRITABLE_REGISTERS
    # ---------------------------------------------------------------------

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
        entry_name = config_entry.data.get("name", config_entry.title)
        _LOGGER.info("Created %d select entities for %s", len(entities), entry_name)
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
        entry_name = config_entry.data.get("name", config_entry.title)
        self._attr_name = f"{entry_name} {friendly_name}"
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


class GrowattWitWorkModeSelect(CoordinatorEntity, SelectEntity):
    """WIT VPP: Work mode / remote command (holding register 202)."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:battery-clock"
    _attr_options = ["Standby", "Charge", "Discharge"]

    def __init__(
        self,
        coordinator: GrowattModbusCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._config_entry = config_entry
        entry_name = config_entry.data.get("name", config_entry.title)
        self._attr_name = f"{entry_name} Work Mode"
        self._attr_unique_id = f"{config_entry.entry_id}_work_mode"

    @property
    def device_info(self) -> dict[str, Any]:
        device_type = get_device_type_for_control("work_mode")
        return self.coordinator.get_device_info(device_type)

    @property
    def current_option(self) -> str | None:
        # Prefer the last command we sent.
        last_mode = getattr(self.coordinator, "wit_last_work_mode", None)
        if isinstance(last_mode, int) and last_mode in (0, 1, 2):
            return {0: "Standby", 1: "Charge", 2: "Discharge"}[last_mode]

        # Fallback: try coordinator data if available.
        data = self.coordinator.data
        if data is None:
            return None
        raw_value = getattr(data, "work_mode", None)
        if raw_value is None:
            return None
        return {0: "Standby", 1: "Charge", 2: "Discharge"}.get(int(raw_value))

    async def async_select_option(self, option: str) -> None:
        value_map = {"Standby": 0, "Charge": 1, "Discharge": 2}
        value = value_map.get(option)
        if value is None:
            _LOGGER.error("[WIT] Invalid work_mode option: %s", option)
            return

        _LOGGER.debug("[WIT] Writing work_mode (202) = %d", value)
        try:
            success = await self.hass.async_add_executor_job(
                self.coordinator.modbus_client.write_register,
                202,
                value,
            )
        except Exception as err:  # noqa: BLE001
            _LOGGER.exception("[WIT] work_mode write failed: %s", err)
            return

        if success:
            setattr(self.coordinator, "wit_last_work_mode", int(value))
            _LOGGER.info("[WIT] Set work_mode to %s", option)

            # If we have a previously set power rate (>0), re-apply it after
            # setting work_mode. This matches field-tested manual sequences.
            last_power = getattr(self.coordinator, "wit_last_power_rate", None)
            if isinstance(last_power, int) and last_power > 0 and value in (1, 2):
                await asyncio.sleep(0.4)
                _LOGGER.debug("[WIT] Re-applying active_power_rate (201) = %d", last_power)
                try:
                    await self.hass.async_add_executor_job(
                        self.coordinator.modbus_client.write_register,
                        201,
                        last_power,
                    )
                except Exception as err:  # noqa: BLE001
                    _LOGGER.exception("[WIT] power re-apply failed: %s", err)

            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error("[WIT] Failed to write work_mode")
