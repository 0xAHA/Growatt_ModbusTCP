"""Number platform for Growatt Modbus Integration."""
import asyncio
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

    # ---------------------------------------------------------------------
    # WIT-specific controls (VPP remote) - use dedicated entities with
    # work mode re-assertion logic
    # ---------------------------------------------------------------------
    is_wit = str(register_map_name).upper() == "WIT_4000_15000TL3"

    if is_wit:
        # Only create controls if the registers exist in this map
        if 203 in holding_registers:
            entities.append(GrowattWitExportLimitWNumber(coordinator, config_entry))
        if 201 in holding_registers:
            entities.append(GrowattWitActivePowerRateNumber(coordinator, config_entry))

        # VPP Remote Control number entities (30408, 30409, 30201)
        for control_name in ['remote_power_control_charging_time', 'remote_charge_and_discharge_power', 'vpp_export_limit_power_rate']:
            if control_name in WRITABLE_REGISTERS:
                control_config = WRITABLE_REGISTERS[control_name]
                register_num = control_config['register']
                if register_num in holding_registers:
                    entities.append(
                        GrowattGenericNumber(coordinator, config_entry, control_name, control_config)
                    )
                    _LOGGER.info("%s control enabled (register %d found)", control_name, register_num)

        # VPP Battery Control number entities (30xxx registers)
        entities.append(GrowattWitVppPowerPercentNumber(coordinator, config_entry))
        if 30404 in holding_registers:
            entities.append(GrowattWitVppChargeCutoffSocNumber(coordinator, config_entry))
        if 30405 in holding_registers:
            entities.append(GrowattWitVppDischargeCutoffSocNumber(coordinator, config_entry))
        if 30411 in holding_registers:
            entities.append(GrowattWitVppTouPeriodsNumber(coordinator, config_entry))

        # NOTE: work_mode is a Select entity (in select.py)
        if entities:
            entry_name = config_entry.data.get("name", config_entry.title)
            _LOGGER.info("Created %d WIT number entities for %s", len(entities), entry_name)
            async_add_entities(entities)
        return

    # ---------------------------------------------------------------------
    # Non-WIT: auto-generate number entities for all writable registers
    # without 'options'
    # ---------------------------------------------------------------------

    # Auto-generate number entities for all writable registers without 'options'
    for control_name, control_config in WRITABLE_REGISTERS.items():
        if 'options' in control_config:
            continue  # Skip select controls

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
            'vpp_export_limit_power_rate': 'VPP Export Limit Power Rate',
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
            'vpp_export_limit_power_rate': 'mdi:transmission-tower-export',
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


class GrowattWitExportLimitWNumber(CoordinatorEntity, NumberEntity):
    """WIT VPP: Export limit in watts (holding register 203)."""

    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = 0.0
    _attr_native_max_value = 20000.0
    _attr_native_step = 1.0
    _attr_native_unit_of_measurement = "W"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: GrowattModbusCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._config_entry = config_entry
        entry_name = config_entry.data.get("name", config_entry.title)
        self._attr_name = f"{entry_name} Export Limit (W)"
        self._attr_unique_id = f"{config_entry.entry_id}_export_limit_w"
        self._attr_icon = "mdi:transmission-tower-export"

    @property
    def device_info(self) -> dict[str, Any]:
        device_type = get_device_type_for_control("export_limit_w")
        return self.coordinator.get_device_info(device_type)

    @property
    def native_value(self) -> float | None:
        data = self.coordinator.data
        if data is None:
            return None
        raw_value = getattr(data, "export_limit_w", None)
        if raw_value is None:
            return None
        return float(raw_value)

    async def async_set_native_value(self, value: float) -> None:
        raw_value = int(max(0, min(int(value), 20000)))
        _LOGGER.debug("[WIT] Writing export_limit_w (203) = %d", raw_value)
        try:
            success = await self.hass.async_add_executor_job(
                self.coordinator.modbus_client.write_register,
                203,
                raw_value,
            )
        except Exception as err:  # noqa: BLE001
            _LOGGER.exception("[WIT] export_limit_w write failed: %s", err)
            return

        if success:
            _LOGGER.info("[WIT] Set export_limit_w to %dW", raw_value)
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error("[WIT] Failed to write export_limit_w")


class GrowattWitActivePowerRateNumber(CoordinatorEntity, NumberEntity):
    """WIT VPP: Active power rate percent (holding register 201).

    WIT requires work_mode (202) to be written for charging/discharging.
    We re-assert work_mode before writing power rate when possible.
    """

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
        super().__init__(coordinator)
        self._config_entry = config_entry
        entry_name = config_entry.data.get("name", config_entry.title)
        self._attr_name = f"{entry_name} Active Power Rate (VPP %)"
        self._attr_unique_id = f"{config_entry.entry_id}_active_power_rate_vpp"
        self._attr_icon = "mdi:speedometer"

    @property
    def device_info(self) -> dict[str, Any]:
        device_type = get_device_type_for_control("active_power_rate")
        return self.coordinator.get_device_info(device_type)

    @property
    def native_value(self) -> float | None:
        data = self.coordinator.data
        if data is None:
            return None
        raw_value = getattr(data, "active_power_rate", None)
        if raw_value is None:
            return None
        return float(raw_value)

    async def async_set_native_value(self, value: float) -> None:
        raw_value = int(max(0, min(int(value), 100)))

        # Re-assert last known work_mode if we have it.
        last_mode = getattr(self.coordinator, "wit_last_work_mode", None)
        if last_mode is None:
            _LOGGER.warning(
                "[WIT] work_mode not set yet. Set Work Mode (Standby/Charge/Discharge) first; writing power_rate anyway."
            )
        else:
            _LOGGER.debug("[WIT] Re-asserting work_mode (202) = %s", last_mode)

        _LOGGER.debug("[WIT] Writing active_power_rate (201) = %d", raw_value)
        try:
            # If we have a non-standby mode, write it first.
            if isinstance(last_mode, int) and last_mode in (1, 2):
                ok_mode = await self.hass.async_add_executor_job(
                    self.coordinator.modbus_client.write_register,
                    202,
                    last_mode,
                )
                if not ok_mode:
                    _LOGGER.error("[WIT] Failed to write work_mode before power_rate")
                # ShineWiLan / WIT often benefits from a short delay between writes.
                await asyncio.sleep(0.4)

            success = await self.hass.async_add_executor_job(
                self.coordinator.modbus_client.write_register,
                201,
                raw_value,
            )
        except Exception as err:  # noqa: BLE001
            _LOGGER.exception("[WIT] active_power_rate write failed: %s", err)
            return

        if success:
            setattr(self.coordinator, "wit_last_power_rate", raw_value)
            _LOGGER.info("[WIT] Set active_power_rate to %d%%", raw_value)
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error("[WIT] Failed to write active_power_rate")


# =============================================================================
# WIT VPP-specific Number Entities (30xxx registers)
# =============================================================================

class GrowattWitVppPowerPercentNumber(CoordinatorEntity, NumberEntity):
    """WIT VPP: Power percentage for charge/discharge operations.

    This value is applied when Battery Mode is set to Charge or Discharge.
    It's stored locally and used by the Battery Mode select entity.
    """

    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = 1.0
    _attr_native_max_value = 100.0
    _attr_native_step = 1.0
    _attr_native_unit_of_measurement = "%"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:gauge"

    def __init__(
        self,
        coordinator: GrowattModbusCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._config_entry = config_entry
        entry_name = config_entry.data.get("name", config_entry.title)
        self._attr_name = f"{entry_name} VPP Power Rate"
        self._attr_unique_id = f"{config_entry.entry_id}_vpp_power_percent"

    @property
    def device_info(self) -> dict[str, Any]:
        device_type = get_device_type_for_control("active_power_rate")
        return self.coordinator.get_device_info(device_type)

    @property
    def native_value(self) -> float | None:
        return float(getattr(self.coordinator, "wit_vpp_power_percent", 100))

    async def async_set_native_value(self, value: float) -> None:
        """Store the power percentage for use by Battery Mode entity."""
        power_percent = int(value)
        setattr(self.coordinator, "wit_vpp_power_percent", power_percent)
        _LOGGER.info("[WIT-VPP] Set power rate to %d%% (will apply on next mode change)", power_percent)


class GrowattWitVppChargeCutoffSocNumber(CoordinatorEntity, NumberEntity):
    """WIT VPP: Charge cutoff SOC (30404) - stop charging when SOC reaches this %."""

    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = 10.0
    _attr_native_max_value = 100.0
    _attr_native_step = 1.0
    _attr_native_unit_of_measurement = "%"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:battery-charging-high"

    VPP_CHARGE_CUTOFF_SOC = 30404

    def __init__(
        self,
        coordinator: GrowattModbusCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._config_entry = config_entry
        entry_name = config_entry.data.get("name", config_entry.title)
        self._attr_name = f"{entry_name} Charge Cutoff SOC"
        self._attr_unique_id = f"{config_entry.entry_id}_vpp_charge_cutoff_soc"

    @property
    def device_info(self) -> dict[str, Any]:
        device_type = get_device_type_for_control("work_mode")
        return self.coordinator.get_device_info(device_type)

    @property
    def native_value(self) -> float | None:
        return float(getattr(self.coordinator, "wit_vpp_charge_cutoff_soc", 100))

    async def async_set_native_value(self, value: float) -> None:
        raw_value = int(value)
        _LOGGER.info("[WIT-VPP] Setting charge cutoff SOC to %d%%", raw_value)

        try:
            success = await self.hass.async_add_executor_job(
                self.coordinator.modbus_client.write_register,
                self.VPP_CHARGE_CUTOFF_SOC,
                raw_value
            )

            if success:
                setattr(self.coordinator, "wit_vpp_charge_cutoff_soc", raw_value)
                _LOGGER.info("[WIT-VPP] Successfully set charge cutoff SOC to %d%%", raw_value)
                await self.coordinator.async_request_refresh()
            else:
                _LOGGER.error("[WIT-VPP] Failed to set charge cutoff SOC")

        except Exception as err:  # noqa: BLE001
            _LOGGER.exception("[WIT-VPP] Failed to set charge cutoff SOC: %s", err)


class GrowattWitVppDischargeCutoffSocNumber(CoordinatorEntity, NumberEntity):
    """WIT VPP: Discharge cutoff SOC (30405) - stop discharging when SOC drops to this %."""

    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = 10.0
    _attr_native_max_value = 100.0
    _attr_native_step = 1.0
    _attr_native_unit_of_measurement = "%"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:battery-alert-variant-outline"

    VPP_DISCHARGE_CUTOFF_SOC = 30405

    def __init__(
        self,
        coordinator: GrowattModbusCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._config_entry = config_entry
        entry_name = config_entry.data.get("name", config_entry.title)
        self._attr_name = f"{entry_name} Discharge Cutoff SOC"
        self._attr_unique_id = f"{config_entry.entry_id}_vpp_discharge_cutoff_soc"

    @property
    def device_info(self) -> dict[str, Any]:
        device_type = get_device_type_for_control("work_mode")
        return self.coordinator.get_device_info(device_type)

    @property
    def native_value(self) -> float | None:
        return float(getattr(self.coordinator, "wit_vpp_discharge_cutoff_soc", 10))

    async def async_set_native_value(self, value: float) -> None:
        raw_value = int(value)
        _LOGGER.info("[WIT-VPP] Setting discharge cutoff SOC to %d%%", raw_value)

        try:
            success = await self.hass.async_add_executor_job(
                self.coordinator.modbus_client.write_register,
                self.VPP_DISCHARGE_CUTOFF_SOC,
                raw_value
            )

            if success:
                setattr(self.coordinator, "wit_vpp_discharge_cutoff_soc", raw_value)
                _LOGGER.info("[WIT-VPP] Successfully set discharge cutoff SOC to %d%%", raw_value)
                await self.coordinator.async_request_refresh()
            else:
                _LOGGER.error("[WIT-VPP] Failed to set discharge cutoff SOC")

        except Exception as err:  # noqa: BLE001
            _LOGGER.exception("[WIT-VPP] Failed to set discharge cutoff SOC: %s", err)


class GrowattWitVppTouPeriodsNumber(CoordinatorEntity, NumberEntity):
    """WIT VPP: Number of active TOU periods (30411).

    Setting this to 0 disables TOU schedule and returns to self-consumption.
    Maximum 20 periods supported.
    """

    _attr_mode = NumberMode.BOX
    _attr_native_min_value = 0.0
    _attr_native_max_value = 20.0
    _attr_native_step = 1.0
    _attr_native_unit_of_measurement = None
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:calendar-range"

    VPP_TOU_NUM_PERIODS = 30411

    def __init__(
        self,
        coordinator: GrowattModbusCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._config_entry = config_entry
        entry_name = config_entry.data.get("name", config_entry.title)
        self._attr_name = f"{entry_name} TOU Active Periods"
        self._attr_unique_id = f"{config_entry.entry_id}_vpp_tou_periods"

    @property
    def device_info(self) -> dict[str, Any]:
        device_type = get_device_type_for_control("work_mode")
        return self.coordinator.get_device_info(device_type)

    @property
    def native_value(self) -> float | None:
        return float(getattr(self.coordinator, "wit_vpp_tou_periods", 0))

    async def async_set_native_value(self, value: float) -> None:
        raw_value = int(value)
        _LOGGER.info("[WIT-VPP] Setting number of TOU periods to %d", raw_value)

        try:
            success = await self.hass.async_add_executor_job(
                self.coordinator.modbus_client.write_register,
                self.VPP_TOU_NUM_PERIODS,
                raw_value
            )

            if success:
                setattr(self.coordinator, "wit_vpp_tou_periods", raw_value)
                _LOGGER.info("[WIT-VPP] Successfully set TOU periods to %d", raw_value)
                await self.coordinator.async_request_refresh()
            else:
                _LOGGER.error("[WIT-VPP] Failed to set TOU periods")

        except Exception as err:  # noqa: BLE001
            _LOGGER.exception("[WIT-VPP] Failed to set TOU periods: %s", err)
