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

        # VPP Battery Mode (uses 30100, 30407, 30409, 30410, 30411, 30412-30414)
        entities.append(GrowattWitVppBatteryModeSelect(coordinator, config_entry))

        # VPP TOU Default Mode (30476) - behavior outside scheduled periods
        if 30476 in holding_registers:
            entities.append(GrowattWitVppTouDefaultModeSelect(coordinator, config_entry))

        # VPP Remote Control selects (30100, 30407)
        for control_name in ['control_authority', 'remote_power_control_enable', 'vpp_export_limit_enable']:
            if control_name in WRITABLE_REGISTERS:
                control_config = WRITABLE_REGISTERS[control_name]
                register_num = control_config['register']
                if register_num in holding_registers:
                    entities.append(
                        GrowattGenericSelect(coordinator, config_entry, control_name, control_config)
                    )
                    _LOGGER.info("%s control enabled (register %d found)", control_name, register_num)

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

        # Look up register address from profile (supports multiple profiles with same control name)
        register_addr = self.coordinator.modbus_client._find_register_by_name(self._control_name)
        if not register_addr:
            # Fallback to hardcoded register if not in profile
            register_addr = self._control_config['register']
            _LOGGER.debug("Using fallback register %d for %s", register_addr, self._control_name)

        # Write to Modbus register
        success = await self.hass.async_add_executor_job(
            self.coordinator.modbus_client.write_register,
            register_addr,
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


class GrowattWitVppBatteryModeSelect(CoordinatorEntity, SelectEntity):
    """WIT VPP: Battery mode via VPP protocol registers (30xxx).

    This uses the correct VPP protocol registers for WIT inverters:
    - 30100: VPP Control Authority (must be 1)
    - 30407: Remote Power Control Enable (0=off, 1=on)
    - 30409: Remote Power Percent (+100=charge, -100=discharge)
    - 30410: AC Charging Enable (required for grid charging)
    - 30411: Number of TOU periods
    - 30412-30414: TOU Period 1 (start, end, power)

    CRITICAL - HOLD Mode Implementation:
    - Simply setting 30407=0 returns to SELF-CONSUMPTION, NOT true HOLD!
    - In self-consumption, battery WILL discharge to supply house load
    - True HOLD requires TOU workaround: Set +1% charge via TOU period
    - This firmware quirk creates actual idle state (battery neither charges nor discharges)
    - WARNING: +1% = HOLD, but -1% = FULL DISCHARGE (asymmetric behavior!)

    NOTE: Legacy registers 201/202 do NOT work on WIT inverters!
    """

    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:battery-clock"
    _attr_options = ["Hold", "Charge", "Discharge"]

    # VPP Register addresses
    VPP_CONTROL_AUTHORITY = 30100
    VPP_REMOTE_POWER_ENABLE = 30407
    VPP_REMOTE_POWER_PERCENT = 30409
    VPP_AC_CHARGE_ENABLE = 30410
    VPP_TOU_NUM_PERIODS = 30411
    VPP_TOU_PERIOD1_BASE = 30412

    def __init__(
        self,
        coordinator: GrowattModbusCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._config_entry = config_entry
        entry_name = config_entry.data.get("name", config_entry.title)
        self._attr_name = f"{entry_name} Battery Mode (VPP)"
        self._attr_unique_id = f"{config_entry.entry_id}_vpp_battery_mode"

    @property
    def device_info(self) -> dict[str, Any]:
        device_type = get_device_type_for_control("work_mode")
        return self.coordinator.get_device_info(device_type)

    @property
    def current_option(self) -> str | None:
        # Use the last command we sent (VPP registers are write-only in some firmware)
        last_mode = getattr(self.coordinator, "wit_vpp_last_mode", None)
        if last_mode in ("Hold", "Charge", "Discharge"):
            return last_mode
        return "Hold"  # Default assumption

    async def async_select_option(self, option: str) -> None:
        if option not in ("Hold", "Charge", "Discharge"):
            _LOGGER.error("[WIT-VPP] Invalid battery mode option: %s", option)
            return

        _LOGGER.info("[WIT-VPP] Setting battery mode to %s", option)

        try:
            client = self.coordinator.modbus_client

            # Step 1: Enable VPP control authority (persists across power cycles)
            _LOGGER.debug("[WIT-VPP] Enabling VPP control authority (30100=1)")
            await self.hass.async_add_executor_job(
                client.write_register, self.VPP_CONTROL_AUTHORITY, 1
            )

            if option == "Hold":
                # HOLD: Use TOU +1% charge workaround for TRUE standby
                # Simply disabling remote control (30407=0) returns to self-consumption
                # where battery WILL discharge! This TOU workaround creates true idle.
                # CRITICAL: +1% = HOLD, but -1% = FULL DISCHARGE (asymmetric!)
                _LOGGER.debug("[WIT-VPP] Setting HOLD mode via TOU +1%% workaround")

                # Enable AC charging (required for TOU charge to work)
                try:
                    await self.hass.async_add_executor_job(
                        client.write_register, self.VPP_AC_CHARGE_ENABLE, 1
                    )
                except Exception as e:  # noqa: BLE001
                    _LOGGER.warning("[WIT-VPP] AC charge enable (30410) failed: %s", e)

                # Get current time for TOU period
                from datetime import datetime
                now = datetime.now()
                current_minutes = now.hour * 60 + now.minute

                # Create TOU period: (now - 5min) to (now + 2 hours) at +1% charge
                start_min = max(0, current_minutes - 5)
                end_min = min(1439, current_minutes + 120)

                # Write TOU period using function 0x10 (write multiple registers)
                _LOGGER.debug("[WIT-VPP] Writing TOU period %02d:%02d-%02d:%02d @ +1%%",
                             start_min // 60, start_min % 60, end_min // 60, end_min % 60)
                success = await self.hass.async_add_executor_job(
                    client.write_registers, self.VPP_TOU_PERIOD1_BASE,
                    [start_min, end_min, 1]  # +1% = HOLD (NOT -1% which = full discharge!)
                )
                if not success:
                    _LOGGER.error("[WIT-VPP] Failed to write TOU period for HOLD mode")
                    return

                # Enable 1 TOU period
                success = await self.hass.async_add_executor_job(
                    client.write_register, self.VPP_TOU_NUM_PERIODS, 1
                )
                if not success:
                    _LOGGER.error("[WIT-VPP] Failed to enable TOU period for HOLD mode")
                    return

            elif option == "Charge":
                # CHARGE: Enable AC charging, enable remote control, set +100%
                _LOGGER.debug("[WIT-VPP] Setting CHARGE mode")

                # Clear any HOLD TOU periods first
                success = await self.hass.async_add_executor_job(
                    client.write_register, self.VPP_TOU_NUM_PERIODS, 0
                )
                if not success:
                    _LOGGER.error("[WIT-VPP] Failed to clear TOU periods for CHARGE mode")
                    return

                # Enable AC charging (PV priority)
                try:
                    await self.hass.async_add_executor_job(
                        client.write_register, self.VPP_AC_CHARGE_ENABLE, 1
                    )
                except Exception as e:  # noqa: BLE001
                    _LOGGER.warning("[WIT-VPP] AC charge enable (30410) failed: %s", e)

                # Enable remote power control
                success = await self.hass.async_add_executor_job(
                    client.write_register, self.VPP_REMOTE_POWER_ENABLE, 1
                )
                if not success:
                    _LOGGER.error("[WIT-VPP] Failed to enable remote power control for CHARGE mode")
                    return

                # Set charge power (+100%)
                power_percent = getattr(self.coordinator, "wit_vpp_power_percent", 100)
                success = await self.hass.async_add_executor_job(
                    client.write_register, self.VPP_REMOTE_POWER_PERCENT, power_percent
                )
                if not success:
                    _LOGGER.error("[WIT-VPP] Failed to set charge power percentage")
                    return

            elif option == "Discharge":
                # DISCHARGE: Enable remote control, set -100%
                _LOGGER.debug("[WIT-VPP] Setting DISCHARGE mode")

                # Clear any HOLD TOU periods first
                success = await self.hass.async_add_executor_job(
                    client.write_register, self.VPP_TOU_NUM_PERIODS, 0
                )
                if not success:
                    _LOGGER.error("[WIT-VPP] Failed to clear TOU periods for DISCHARGE mode")
                    return

                # Enable remote power control
                success = await self.hass.async_add_executor_job(
                    client.write_register, self.VPP_REMOTE_POWER_ENABLE, 1
                )
                if not success:
                    _LOGGER.error("[WIT-VPP] Failed to enable remote power control for DISCHARGE mode")
                    return

                # Set discharge power (-100% = 65436 unsigned)
                power_percent = getattr(self.coordinator, "wit_vpp_power_percent", 100)
                power_value = 65536 - power_percent  # Convert to unsigned 16-bit
                success = await self.hass.async_add_executor_job(
                    client.write_register, self.VPP_REMOTE_POWER_PERCENT, power_value
                )
                if not success:
                    _LOGGER.error("[WIT-VPP] Failed to set discharge power percentage")
                    return

            # Store last mode for UI feedback (only reached if all writes succeeded)
            setattr(self.coordinator, "wit_vpp_last_mode", option)
            _LOGGER.info("[WIT-VPP] Successfully set battery mode to %s", option)

            await self.coordinator.async_request_refresh()

        except Exception as err:  # noqa: BLE001
            _LOGGER.exception("[WIT-VPP] Failed to set battery mode: %s", err)


class GrowattWitVppTouDefaultModeSelect(CoordinatorEntity, SelectEntity):
    """WIT VPP: TOU default mode (behavior outside scheduled periods)."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:calendar-clock"
    _attr_options = ["Load First (Hold)", "Battery First", "Grid First"]

    VPP_TOU_DEFAULT_MODE = 30476

    def __init__(
        self,
        coordinator: GrowattModbusCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._config_entry = config_entry
        entry_name = config_entry.data.get("name", config_entry.title)
        self._attr_name = f"{entry_name} TOU Default Mode"
        self._attr_unique_id = f"{config_entry.entry_id}_vpp_tou_default_mode"

    @property
    def device_info(self) -> dict[str, Any]:
        device_type = get_device_type_for_control("work_mode")
        return self.coordinator.get_device_info(device_type)

    @property
    def current_option(self) -> str | None:
        last_mode = getattr(self.coordinator, "wit_vpp_tou_default_mode", 0)
        mode_map = {0: "Load First (Hold)", 1: "Battery First", 2: "Grid First"}
        return mode_map.get(last_mode, "Load First (Hold)")

    async def async_select_option(self, option: str) -> None:
        mode_map = {"Load First (Hold)": 0, "Battery First": 1, "Grid First": 2}
        value = mode_map.get(option)

        if value is None:
            _LOGGER.error("[WIT-VPP] Invalid TOU default mode: %s", option)
            return

        _LOGGER.info("[WIT-VPP] Setting TOU default mode to %s (value=%d)", option, value)

        try:
            success = await self.hass.async_add_executor_job(
                self.coordinator.modbus_client.write_register,
                self.VPP_TOU_DEFAULT_MODE,
                value
            )

            if success:
                setattr(self.coordinator, "wit_vpp_tou_default_mode", value)
                _LOGGER.info("[WIT-VPP] Successfully set TOU default mode to %s", option)
                await self.coordinator.async_request_refresh()
            else:
                _LOGGER.error("[WIT-VPP] Failed to set TOU default mode")

        except Exception as err:  # noqa: BLE001
            _LOGGER.exception("[WIT-VPP] Failed to set TOU default mode: %s", err)
