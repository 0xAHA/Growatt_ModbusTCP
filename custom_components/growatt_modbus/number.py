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
    control_is_blocked,
    get_device_type_for_control,
    is_read_only_register,
)
from .coordinator import GrowattModbusCoordinator
from .entity import GrowattEntity
from .growatt_modbus import ModbusWriteError

_LOGGER = logging.getLogger(__name__)

# 1, not 0: these entities WRITE to the inverter. An RS485 bus cannot carry
# concurrent transactions — that constraint is why SharedModbusConnection holds a
# lock at all. Serialising at the platform level keeps HA from issuing overlapping
# service calls that would only queue on that lock anyway.
PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Growatt Modbus number entities."""
    coordinator = config_entry.runtime_data
    
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
    is_wit = str(register_map_name).upper() in ("WIT_4000_15000TL3", "WIT_29900_50000TL3_XHU")

    if is_wit:
        # Only create controls if the registers exist in this map
        # NOTE: reg 203 (export_limit_w) is intentionally NOT exposed as a writable entity —
        # writes are rejected by WIT firmware (exception_code=0) even with all VPP enables set.
        # The register is still polled for reading; add a sensor if display-only is desired.
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

        # TOU period power entities (periods 1-10, power only — start/end are TimeEntity in time.py)
        for _period in range(1, 11):
            _base = 30412 + (_period - 1) * 3
            if _base in holding_registers:
                entities.append(GrowattWitVppTouPeriodNumber(coordinator, config_entry, _period, 'power'))

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
        # Time period start/end use hex-packed encoding — handled as TimeEntity in time.py
        if 'time_period' in control_name and control_name.endswith(('_start', '_end')):
            continue

        register_num = control_config['register']
        if register_num not in holding_registers:
            continue  # Skip if register not in this profile

        # A profile marking the register read-only means "this model has the address but
        # will not accept a write" — so do not offer a control for it (#374).
        #
        # Until v1.6.1 `access` was documentation that nothing read. v1.6.0 added the VPP
        # registers to the MOD profile as 'RO' expecting that to be enough, and this loop
        # created five writable controls anyway — including the power setpoint measured
        # importing from the grid to reach its target. The flag now means what everyone
        # already assumed it meant.
        if is_read_only_register(holding_registers.get(register_num)):
            _LOGGER.debug(
                "Skipping %s: register %d is read-only on this profile",
                control_name, register_num,
            )
            continue

        # Profile-specific filter: only_profiles restricts to named maps; not_profiles excludes them
        _only = control_config.get('only_profiles')
        if _only and register_map_name not in _only:
            continue
        _not = control_config.get('not_profiles')
        if _not and register_map_name in _not:
            continue

        # VPP export limit requires live confirmation that the inverter responds to 30200-30201
        if control_name == 'vpp_export_limit_power_rate':
            if coordinator.data is None or not coordinator.data.vpp_export_limit_available:
                _LOGGER.debug("Skipping vpp_export_limit_power_rate: register 30201 not confirmed responsive")
                continue

        entities.append(
            GrowattGenericNumber(coordinator, config_entry, control_name, control_config)
        )
        _LOGGER.info("%s control enabled (register %d found)", control_name, register_num)

    if entities:
        _LOGGER.info("Created %d number entities for %s", len(entities), config_entry.data['name'])
        async_add_entities(entities)


class GrowattGenericNumber(GrowattEntity, NumberEntity):
    """Generic number entity for any numeric control."""

    # has_entity_name comes from GrowattEntity, as do unique_id and device_info.
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
        super().__init__(
            coordinator,
            config_entry,
            control_name,
            get_device_type_for_control(control_name),
        )

        self._control_name = control_name
        self._control_config = control_config

        # Controls that should exist but not be operable until someone chooses to enable
        # them. Used for the SPF bulk and float charging voltages (#384), where a wrong
        # in-range value damages a battery bank rather than producing a wrong reading —
        # unlike every other control here, where the worst case is a visible mistake.
        if control_config.get('disabled_by_default'):
            self._attr_entity_registry_enabled_default = False

        # Generate friendly name
        friendly_overrides = {
            'active_power_rate': 'VPP Active Power Rate',
            'export_limit_w': 'VPP Export Limit (W)',
            'export_limit_failed_power_rate': 'Export Limit Fallback Power Rate',
            'max_output_power_rate': 'Max Output Power Rate',
            'vpp_export_limit_power_rate': 'VPP Export Limit Power Rate',
            'load_first_battery_minimum_soc': 'Load First Battery Minimum SOC',
            # Register 3067. Growatt calls it "Grid First", but #362 demonstrated it
            # also governs discharge in Load/self-consumption operation, so the mode
            # prefix misleads more than it describes. The entity_id of existing
            # installs is unaffected — that is fixed at creation from the unique_id.
            'grid_first_discharge_stopped_soc': 'Discharge Stopped SOC',
            # Register 3048, and the same correction for the same reason (#362): measured
            # to stop charging under Load Priority with all TOU periods disabled, so the
            # "(Battery First)" suffix told users it could be ignored outside that mode.
            'batt_first_charge_stopped_soc': 'Charge Stopped SOC',
            # Register 3312 (#372). "Grid" rather than "AC" deliberately: the cloud calls
            # it ub_ac_charging_stop_soc, but next to "Charge Stopped SOC" above, "AC" does
            # not tell a user which of the two applies to them.
            'grid_charge_stopped_soc': 'Grid Charge Stopped SOC',
        }
        friendly_name = friendly_overrides.get(control_name, control_name.replace('_', ' ').title())
        self._attr_name = friendly_name

        # Set icon
        self._attr_icon = self._get_icon(control_name)

        # Configure range and unit
        self._configure_range_and_unit()

    @property
    def available(self) -> bool:
        """Withhold the control when the inverter will not accept a write.

        Some settings are conditional on another register rather than on the profile. The
        SPF's max charge current cannot be set while battery type is Lithium — the BMS takes
        over charge control — and this hardware discards a rejected save silently rather
        than refusing it, so an offered-but-ignored slider would look like it worked (#376).

        Declarative as `('field', value)` rather than a callable: a lambda here would be
        hard to test and easy to make decorative, which is a mistake this project has
        already shipped once.
        """
        if not super().available:
            return False
        return not control_is_blocked(self._control_config, self.coordinator.data)

    def _get_icon(self, control_name: str) -> str:
        """Get icon based on control name."""
        icon_map = {
            'export_limit_power': 'mdi:speedometer',
            'export_limit_failed_power_rate': 'mdi:transmission-tower-export',
            'active_power_rate': 'mdi:speedometer',
            'max_charge_current': 'mdi:battery-charging-high',
            'bulk_charge_voltage': 'mdi:battery-charging-100',
            'float_charge_voltage': 'mdi:battery-charging-60',
            'ac_charge_current': 'mdi:current-ac',
            'gen_charge_current': 'mdi:current-ac',
            'bat_low_to_uti': 'mdi:battery-alert',
            'ac_to_bat_volt': 'mdi:battery-charging',
            'vpp_export_limit_power_rate': 'mdi:transmission-tower-export',
            'load_first_battery_minimum_soc': 'mdi:battery-sync',
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

        # Write to Modbus register with read-back verification
        register = self._control_config['register']

        # Skip a write that would change nothing (#384).
        #
        # These registers are held in EEPROM, which has a finite write endurance. Nothing in
        # the integration writes on its own - a write happens only when this method is
        # called - but an automation that re-applies the same value on a schedule would
        # burn a write cycle every time it ran, for no effect. A repairer working on this
        # inverter family reported four SPF6000ES units with failed EEPROMs in a year, and
        # while that is not attributable to anything here, there is no reason to spend
        # cycles on writes that cannot change the value.
        #
        # Gated on having a current reading: when the register has not been read yet the
        # comparison is meaningless and the write goes ahead. A skipped write that should
        # have happened is worse than a redundant one.
        current_raw = getattr(self.coordinator.data, self._control_name, None) \
            if self.coordinator.data is not None else None
        if current_raw is not None and int(current_raw) == raw_value:
            _LOGGER.debug(
                "%s already reads %s (raw %d) — skipping write to register %d",
                self._control_name, value, raw_value, register,
            )
            return
        try:
            write_ok, verified = await self.hass.async_add_executor_job(
                self.coordinator.modbus_client.write_register_verified,
                register,
                raw_value,
            )
        except ModbusWriteError:
            _LOGGER.error("Failed to write %s (register %d)", self._control_name, register)
            return

        if write_ok:
            if verified:
                _LOGGER.info("Set %s to %.1f (raw=%d, verified)", self._control_name, value, raw_value)
            else:
                _LOGGER.warning(
                    "%s: write succeeded but value reverted (possible cloud override)",
                    self._control_name,
                )
            self.coordinator.track_write(register, raw_value, self._control_name)
            await self.coordinator.async_request_refresh()


# Legacy class for backwards compatibility (remove in future version)
class GrowattExportLimitPowerNumber(GrowattEntity, NumberEntity):
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
        super().__init__(
            coordinator,
            config_entry,
            "export_limit_power",
            get_device_type_for_control('export_limit_power'),
        )

        self._attr_name = "Export Limit Power"
        self._attr_icon = "mdi:speedometer"


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
        
        # Write to Modbus register with read-back verification
        register = WRITABLE_REGISTERS['export_limit_power']['register']
        try:
            write_ok, verified = await self.hass.async_add_executor_job(
                self.coordinator.modbus_client.write_register_verified,
                register,
                raw_value,
            )
        except ModbusWriteError:
            _LOGGER.error("Failed to write export_limit_power (register %d)", register)
            return

        if write_ok:
            if verified:
                _LOGGER.info("Set export_limit_power to %.1f%% (raw=%d, verified)", value, raw_value)
            else:
                _LOGGER.warning("export_limit_power: write succeeded but value reverted (possible cloud override)")
            self.coordinator.track_write(register, raw_value, 'export_limit_power')
            await self.coordinator.async_request_refresh()


class GrowattActivePowerRateNumber(GrowattEntity, NumberEntity):
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
        super().__init__(
            coordinator,
            config_entry,
            "active_power_rate",
            get_device_type_for_control('active_power_rate'),
        )

        self._attr_name = "Active Power Rate"
        self._attr_icon = "mdi:speedometer"


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

        # Write to Modbus register with read-back verification
        register = WRITABLE_REGISTERS['active_power_rate']['register']
        try:
            write_ok, verified = await self.hass.async_add_executor_job(
                self.coordinator.modbus_client.write_register_verified,
                register,
                raw_value,
            )
        except ModbusWriteError:
            _LOGGER.error("Failed to write active_power_rate (register %d)", register)
            return

        if write_ok:
            if verified:
                _LOGGER.info("Set active_power_rate to %d%% (verified)", raw_value)
            else:
                _LOGGER.warning("active_power_rate: write succeeded but value reverted (possible cloud override)")
            self.coordinator.track_write(register, raw_value, 'active_power_rate')
            await self.coordinator.async_request_refresh()


class GrowattWitExportLimitWNumber(GrowattEntity, NumberEntity):
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
        super().__init__(
            coordinator,
            config_entry,
            "export_limit_w",
            get_device_type_for_control("export_limit_w"),
        )
        self._attr_name = "Export Limit (W)"
        self._attr_icon = "mdi:transmission-tower-export"


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
            # WIT inverter rejects FC06 (Write Single Register) on reg 203 with Illegal Function.
            # Must use FC16 (Write Multiple Registers) instead.
            success = await self.hass.async_add_executor_job(
                self.coordinator.modbus_client.write_registers,
                203,
                [raw_value],
            )
        except Exception as err:  # noqa: BLE001
            _LOGGER.exception("[WIT] export_limit_w write failed: %s", err)
            return

        if success:
            _LOGGER.info("[WIT] Set export_limit_w to %dW", raw_value)
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error("[WIT] Failed to write export_limit_w")


class GrowattWitActivePowerRateNumber(GrowattEntity, NumberEntity):
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
        super().__init__(
            coordinator,
            config_entry,
            "active_power_rate_vpp",
            get_device_type_for_control("active_power_rate"),
        )
        self._attr_name = "Active Power Rate (VPP %)"
        self._attr_icon = "mdi:speedometer"


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

class GrowattWitVppPowerPercentNumber(GrowattEntity, NumberEntity):
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
        super().__init__(
            coordinator,
            config_entry,
            "vpp_power_percent",
            get_device_type_for_control("active_power_rate"),
        )
        self._attr_name = "VPP Power Rate"


    @property
    def native_value(self) -> float | None:
        return float(getattr(self.coordinator, "wit_vpp_power_percent", 100))

    async def async_set_native_value(self, value: float) -> None:
        """Store the power percentage for use by Battery Mode entity."""
        power_percent = int(value)
        setattr(self.coordinator, "wit_vpp_power_percent", power_percent)
        _LOGGER.info("[WIT-VPP] Set power rate to %d%% (will apply on next mode change)", power_percent)


class GrowattWitVppChargeCutoffSocNumber(GrowattEntity, NumberEntity):
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
        super().__init__(
            coordinator,
            config_entry,
            "vpp_charge_cutoff_soc",
            get_device_type_for_control("work_mode"),
        )
        self._attr_name = "Charge Cutoff SOC"


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


class GrowattWitVppDischargeCutoffSocNumber(GrowattEntity, NumberEntity):
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
        super().__init__(
            coordinator,
            config_entry,
            "vpp_discharge_cutoff_soc",
            get_device_type_for_control("work_mode"),
        )
        self._attr_name = "Discharge Cutoff SOC"


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


class GrowattWitVppTouPeriodsNumber(GrowattEntity, NumberEntity):
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
        super().__init__(
            coordinator,
            config_entry,
            "vpp_tou_periods",
            get_device_type_for_control("work_mode"),
        )
        self._attr_name = "TOU Active Periods"


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


class GrowattWitVppTouPeriodNumber(GrowattEntity, NumberEntity):
    """WIT VPP TOU period power entity.

    Handles the power level for a single TOU period (+100 = full charge, -100 = full discharge).
    Start/end times are TimeEntity instances in time.py.

    Register: base 30412 + (period-1)*3 + 2 (power offset).
    Writes use FC16 (write_registers) — WIT inverter rejects FC06 on VPP registers.
    """

    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_min_value = -100.0
    _attr_native_max_value = 100.0
    _attr_native_step = 1.0
    _attr_native_unit_of_measurement = '%'
    _attr_mode = NumberMode.SLIDER
    _attr_icon = 'mdi:battery-arrow-up-outline'

    def __init__(
        self,
        coordinator: GrowattModbusCoordinator,
        config_entry: ConfigEntry,
        period: int,
        slot: str = 'power',
    ) -> None:
        super().__init__(
            coordinator,
            config_entry,
            f"vpp_tou_p{period}_power",
            get_device_type_for_control("work_mode"),
        )
        self._period = period
        self._slot = 'power'
        self._register = 30412 + (period - 1) * 3 + 2  # power offset within the period triplet
        self._coordinator_attr = f"wit_vpp_tou_p{period}_power"

        self._attr_name = f"TOU Period {period} Power"

    @property
    def native_value(self) -> float | None:
        default = 0.0
        return float(getattr(self.coordinator, self._coordinator_attr, default))

    async def async_set_native_value(self, value: float) -> None:
        raw = int(value)
        # Two's complement for negative power values
        encoded = raw & 0xFFFF
        _LOGGER.info("[WIT-TOU] Period %d %s → %d (reg %d)", self._period, self._slot, raw, self._register)
        try:
            success = await self.hass.async_add_executor_job(
                self.coordinator.modbus_client.write_registers,
                self._register,
                [encoded],
            )
            if success:
                setattr(self.coordinator, self._coordinator_attr, raw)
                _LOGGER.info("[WIT-TOU] Period %d %s set to %d", self._period, self._slot, raw)
                await self.coordinator.async_request_refresh()
            else:
                _LOGGER.error("[WIT-TOU] Failed to write period %d %s", self._period, self._slot)
        except Exception as err:  # noqa: BLE001
            _LOGGER.exception("[WIT-TOU] Period %d %s write error: %s", self._period, self._slot, err)
