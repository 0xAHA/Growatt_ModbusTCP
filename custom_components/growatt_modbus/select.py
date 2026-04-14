"""Select platform for Growatt Modbus Integration."""
import logging
import asyncio
from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import EntityCategory

from .const import (
    DOMAIN,
    WRITABLE_REGISTERS,
    CONF_REGISTER_MAP,
    get_device_type_for_control,
    DEVICE_TYPE_BATTERY,
    MOD_TOU_PERIODS,
)
from .coordinator import GrowattModbusCoordinator
from .growatt_modbus import ModbusWriteError

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

        # VPP Remote Control selects (30100, 30200, 30407)
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

        # allow_grid_charge is handled by GrowattModAllowGridChargeSelect below
        if control_name == 'allow_grid_charge':
            continue

        # VPP export limit requires live confirmation that the inverter responds to 30200
        if control_name == 'vpp_export_limit_enable':
            if coordinator.data is None or not coordinator.data.vpp_export_limit_available:
                _LOGGER.debug("Skipping vpp_export_limit_enable: register 30200 not confirmed responsive")
                continue

        # control_authority requires live confirmation that the inverter responds to 30100
        if control_name == 'control_authority':
            if coordinator.data is None or not coordinator.data.vpp_control_authority_available:
                _LOGGER.debug("Skipping control_authority: register 30100 not confirmed responsive")
                continue

        entities.append(
            GrowattGenericSelect(coordinator, config_entry, control_name, control_config)
        )
        _LOGGER.info("%s control enabled (register %d found)", control_name, register_num)

    # MOD TL3-XH TOU priority and enable selects (9 periods × 2 = 18 entities)
    if 3038 in holding_registers:
        for period_def in MOD_TOU_PERIODS:
            entities.append(GrowattModTouPriority(coordinator, config_entry, period_def))
            entities.append(GrowattModTouEnable(coordinator, config_entry, period_def))
        _LOGGER.info("MOD TOU priority/enable controls enabled (%d select entities for %d periods)",
                     len(MOD_TOU_PERIODS) * 2, len(MOD_TOU_PERIODS))

    # MOD GEN4 Allow Grid Charge gate (register 3049) — prerequisite for TOU persistence
    if 3049 in holding_registers:
        entities.append(GrowattModAllowGridChargeSelect(coordinator, config_entry))
        _LOGGER.info("MOD Allow Grid Charge control enabled (register 3049)")

    if entities:
        entry_name = config_entry.data.get("name", config_entry.title)
        _LOGGER.info("Created %d select entities for %s", len(entities), entry_name)
        async_add_entities(entities)

    # Deferred registration for VPP controls that require live hardware confirmation.
    # vpp_export_limit_enable and control_authority are only created once the inverter
    # has confirmed the relevant registers respond (vpp_export_limit_available /
    # vpp_control_authority_available flags set during first real poll). Because
    # async_config_entry_first_refresh seeds coordinator.data with an empty placeholder,
    # these flags are always False at setup time — so the controls are always skipped.
    # Register a coordinator listener that adds them once real data arrives. (Issue #262)
    deferred_vpp: list[tuple[str, dict]] = []
    for ctrl in ("vpp_export_limit_enable", "control_authority"):
        if ctrl not in WRITABLE_REGISTERS:
            continue
        cfg = WRITABLE_REGISTERS[ctrl]
        if cfg["register"] not in holding_registers:
            continue
        # Only defer if it was actually skipped above (flag was False at setup time)
        already_created = any(
            getattr(e, "_control_name", None) == ctrl for e in entities
        )
        if not already_created:
            deferred_vpp.append((ctrl, cfg))

    if deferred_vpp:
        _LOGGER.debug(
            "%d VPP select(s) deferred pending first real inverter data: %s",
            len(deferred_vpp),
            [ctrl for ctrl, _ in deferred_vpp],
        )

        @callback
        def _async_check_deferred_vpp() -> None:
            if not coordinator.has_real_data:
                return
            new_entities: list[SelectEntity] = []
            still_waiting: list[tuple[str, dict]] = []
            for ctrl_name, ctrl_cfg in deferred_vpp:
                available = (
                    coordinator.data.vpp_export_limit_available
                    if ctrl_name == "vpp_export_limit_enable"
                    else coordinator.data.vpp_control_authority_available
                )
                if available:
                    new_entities.append(
                        GrowattGenericSelect(coordinator, config_entry, ctrl_name, ctrl_cfg)
                    )
                    _LOGGER.debug("Deferred VPP control %s now available — adding entity", ctrl_name)
                else:
                    still_waiting.append((ctrl_name, ctrl_cfg))
            deferred_vpp.clear()
            deferred_vpp.extend(still_waiting)
            if new_entities:
                async_add_entities(new_entities)
            if not deferred_vpp:
                _remove_vpp_listener()

        _remove_vpp_listener = coordinator.async_add_listener(_async_check_deferred_vpp)
        config_entry.async_on_unload(_remove_vpp_listener)


class GrowattGenericSelect(CoordinatorEntity, SelectEntity):
    """Generic select entity for any control with options."""

    _attr_has_entity_name = True
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
        self._attr_name = friendly_name
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

        # WIT side-effect: disabling control_authority (30100=0) transiently resets register 122
        # (export_limit_mode) to 0. On older WIT firmware it may not auto-restore when re-enabled.
        # Save before disabling so we can restore after re-enabling.
        is_wit = 'WIT' in self.coordinator.modbus_client.register_map.get('name', '')
        if self._control_name == 'control_authority' and is_wit:
            if value == 0:
                saved = await self.hass.async_add_executor_job(
                    self.coordinator.modbus_client.read_holding_registers, 122, 1
                )
                self.coordinator._saved_export_limit_mode_wit = saved[0] if saved else 0
                _LOGGER.debug(
                    "WIT: saved export_limit_mode=%d before disabling control authority",
                    self.coordinator._saved_export_limit_mode_wit,
                )

        # Write to Modbus register with read-back verification
        try:
            write_ok, verified = await self.hass.async_add_executor_job(
                self.coordinator.modbus_client.write_register_verified,
                register_addr,
                value,
            )
        except ModbusWriteError:
            _LOGGER.error("Failed to write %s (register %d)", self._control_name, register_addr)
            return

        if write_ok:
            if verified:
                _LOGGER.info("Set %s to %s (value=%d, verified)", self._control_name, option, value)
            else:
                _LOGGER.warning(
                    "%s: write succeeded but value reverted. Possible causes: "
                    "ShineWiFi/cloud dongle overriding local writes, inverter firmware "
                    "rejecting the value, or a prerequisite setting not enabled.",
                    self._control_name,
                )
            self.coordinator.track_write(register_addr, value, self._control_name)

            # WIT: restore export_limit_mode after re-enabling control authority
            if self._control_name == 'control_authority' and is_wit and value == 1:
                saved = self.coordinator._saved_export_limit_mode_wit
                if saved > 0:
                    await asyncio.sleep(0.3)
                    restored = await self.hass.async_add_executor_job(
                        self.coordinator.modbus_client.write_register, 122, saved
                    )
                    if restored:
                        _LOGGER.info(
                            "WIT: restored export_limit_mode=%d after re-enabling control authority",
                            saved,
                        )
                    else:
                        _LOGGER.warning(
                            "WIT: failed to restore export_limit_mode=%d after re-enabling control authority",
                            saved,
                        )

            await self.coordinator.async_request_refresh()


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


class GrowattModTouPriority(CoordinatorEntity, SelectEntity):
    """Priority select for one MOD TL3-XH TOU period.

    Extracts bits 13-14 from the period's start register.
    Write uses read-modify-write to preserve time (bits 0-12) and enable (bit 15).
    """

    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:priority-high"
    _attr_options = ["Load Priority", "Battery Priority", "Grid Priority"]

    _PRIORITY_MAP = {0: "Load Priority", 1: "Battery Priority", 2: "Grid Priority"}
    _PRIORITY_REVERSE = {"Load Priority": 0, "Battery Priority": 1, "Grid Priority": 2}

    def __init__(self, coordinator, config_entry, period_def: dict) -> None:
        """Initialize priority select."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._period = period_def["period"]
        self._start_reg = period_def["start_reg"]
        self._end_reg = period_def["end_reg"]
        self._start_field = period_def["start_field"]
        self._end_field = period_def["end_field"]

        entry_name = config_entry.data.get("name", config_entry.title)
        self._attr_name = f"{entry_name} TOU Period {self._period} Priority"
        self._attr_unique_id = f"{config_entry.entry_id}_mod_tou_{self._period}_priority"

    @property
    def device_info(self):
        """Return device information."""
        return self.coordinator.get_device_info(DEVICE_TYPE_BATTERY)

    @property
    def current_option(self) -> str | None:
        """Return current priority option."""
        data = self.coordinator.data
        if data is None:
            return None
        raw = getattr(data, self._start_field, 0)
        priority = (int(raw) >> 13) & 0x3
        return self._PRIORITY_MAP.get(priority)

    async def async_select_option(self, option: str) -> None:
        """Write new priority atomically — always write start+end together as a single FC16 transaction."""
        priority = self._PRIORITY_REVERSE.get(option)
        if priority is None:
            return
        data = self.coordinator.data
        current_raw = getattr(data, self._start_field, 0) if data else 0
        new_raw = (int(current_raw) & 0x9FFF) | (priority << 13)
        current_end = int(getattr(data, self._end_field, 0) if data else 0)
        try:
            success = await self.hass.async_add_executor_job(
                self.coordinator.modbus_client.write_registers,
                self._start_reg,
                [new_raw, current_end],
            )
        except ModbusWriteError:
            _LOGGER.error("Failed to write MOD TOU period %d priority (register %d, atomic FC16)", self._period, self._start_reg)
            return
        if success:
            _LOGGER.info("Set MOD TOU period %d priority to %s (start=0x%04X, end=0x%04X, atomic FC16)", self._period, option, new_raw, current_end)
            self.coordinator.track_write(self._start_reg, new_raw, self._start_field)
            self.coordinator.track_write(self._end_reg, current_end, self._end_field)
            await self.coordinator.async_request_refresh()


class GrowattModTouEnable(CoordinatorEntity, SelectEntity):
    """Enable/disable select for one MOD TL3-XH TOU period.

    Extracts bit 15 from the period's start register.
    Write uses read-modify-write to preserve time (bits 0-12) and priority (bits 13-14).
    """

    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:toggle-switch-outline"
    _attr_options = ["Disabled", "Enabled"]

    def __init__(self, coordinator, config_entry, period_def: dict) -> None:
        """Initialize enable select."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._period = period_def["period"]
        self._start_reg = period_def["start_reg"]
        self._end_reg = period_def["end_reg"]
        self._start_field = period_def["start_field"]
        self._end_field = period_def["end_field"]

        entry_name = config_entry.data.get("name", config_entry.title)
        self._attr_name = f"{entry_name} TOU Period {self._period} Enable"
        self._attr_unique_id = f"{config_entry.entry_id}_mod_tou_{self._period}_enable"

    @property
    def device_info(self):
        """Return device information."""
        return self.coordinator.get_device_info(DEVICE_TYPE_BATTERY)

    @property
    def current_option(self) -> str | None:
        """Return current enable state."""
        data = self.coordinator.data
        if data is None:
            return None
        raw = getattr(data, self._start_field, 0)
        enabled = (int(raw) >> 15) & 0x1
        return "Enabled" if enabled else "Disabled"

    async def async_select_option(self, option: str) -> None:
        """Write new enable state atomically — always write start+end together as a single FC16 transaction."""
        enable = 1 if option == "Enabled" else 0
        data = self.coordinator.data
        current_raw = getattr(data, self._start_field, 0) if data else 0
        new_raw = (int(current_raw) & 0x7FFF) | (enable << 15)
        current_end = int(getattr(data, self._end_field, 0) if data else 0)
        try:
            success = await self.hass.async_add_executor_job(
                self.coordinator.modbus_client.write_registers,
                self._start_reg,
                [new_raw, current_end],
            )
        except ModbusWriteError:
            _LOGGER.error("Failed to write MOD TOU period %d enable (register %d, atomic FC16)", self._period, self._start_reg)
            return
        if success:
            _LOGGER.info("Set MOD TOU period %d enable to %s (start=0x%04X, end=0x%04X, atomic FC16)", self._period, option, new_raw, current_end)
            self.coordinator.track_write(self._start_reg, new_raw, self._start_field)
            self.coordinator.track_write(self._end_reg, current_end, self._end_field)
            await self.coordinator.async_request_refresh()


class GrowattModAllowGridChargeSelect(CoordinatorEntity, SelectEntity):
    """Select entity for the MOD GEN4 'Allow Grid Charge' gate (register 3049).

    This register must be set to Enabled (1) before TOU time slot registers
    (3038-3059) will persist on GEN4 hardware.  Plain 0/1 register — no bit masking.
    """

    _REGISTER = 3049
    _DATA_FIELD = "allow_grid_charge"

    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:transmission-tower-export"
    _attr_options = ["Disabled", "Enabled"]

    def __init__(self, coordinator, config_entry) -> None:
        """Initialize the Allow Grid Charge select."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        entry_name = config_entry.data.get("name", config_entry.title)
        self._attr_name = f"{entry_name} Allow Grid Charge"
        self._attr_unique_id = f"{config_entry.entry_id}_allow_grid_charge"

    @property
    def device_info(self):
        """Return device information."""
        return self.coordinator.get_device_info(DEVICE_TYPE_BATTERY)

    @property
    def current_option(self) -> str | None:
        """Return current state."""
        data = self.coordinator.data
        if data is None:
            return None
        raw = getattr(data, self._DATA_FIELD, 0)
        return "Enabled" if int(raw) else "Disabled"

    async def async_select_option(self, option: str) -> None:
        """Write new state to register 3049."""
        value = 1 if option == "Enabled" else 0
        try:
            write_ok, verified = await self.hass.async_add_executor_job(
                self.coordinator.modbus_client.write_register_verified, self._REGISTER, value,
            )
        except ModbusWriteError:
            _LOGGER.error("Failed to write allow_grid_charge (register %d)", self._REGISTER)
            return
        if write_ok:
            if verified:
                _LOGGER.info("Set allow_grid_charge to %s (value=%d, verified)", option, value)
            else:
                _LOGGER.warning(
                    "allow_grid_charge: write succeeded but value reverted. "
                    "Possible causes: ShineWiFi/cloud dongle overriding local writes, "
                    "or inverter firmware rejecting the value."
                )
            self.coordinator.track_write(self._REGISTER, value, self._DATA_FIELD)
            await self.coordinator.async_request_refresh()
