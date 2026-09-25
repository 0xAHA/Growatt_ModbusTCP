"""Switch platform for Growatt Modbus Integration.

One switch: remote on/off (the AC output, on off-grid models). Disabled by default on
every profile, so nobody turns an inverter off by accident - see power_control.py for why
each protocol family needs its own encoding.
"""
import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DEVICE_TYPE_INVERTER
from .entity import GrowattEntity
from .power_control import (
    PowerControl,
    PowerControlError,
    decode,
    resolve_power_control,
    set_power,
)

_LOGGER = logging.getLogger(__name__)

# Writable platform - serialise. See number.py for the reasoning.
PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the on/off switch when the profile has an on/off register."""
    coordinator = config_entry.runtime_data
    control = resolve_power_control(coordinator.modbus_client.register_map)
    if control is None:
        return
    async_add_entities([GrowattPowerSwitch(coordinator, config_entry, control)])


class GrowattPowerSwitch(GrowattEntity, SwitchEntity):
    """Remote on/off.

    Where the profile marks the register as reading back (confirmed on a real unit), the
    state is read from the inverter each poll and the switch is an ordinary toggle.
    Elsewhere it shows the last command sent: V1.39 documents register 0 as write-only and
    VPP 30101 as not stored, so an unconfirmed read cannot be trusted to reflect the
    inverter, and `assumed_state` makes Home Assistant offer both actions instead.
    """

    _attr_entity_category = EntityCategory.CONFIG
    _attr_entity_registry_enabled_default = False
    _attr_assumed_state = True
    _attr_icon = "mdi:power"

    def __init__(self, coordinator, config_entry: ConfigEntry, control: PowerControl) -> None:
        """Initialise the on/off switch."""
        super().__init__(
            coordinator,
            config_entry,
            unique_key="inverter_power",
            device_type=DEVICE_TYPE_INVERTER,
        )
        self._control = control
        self._attr_translation_key = "ac_output" if control.is_ac_output else "inverter_power"
        self._attr_is_on = None
        if control.readback:
            self._attr_assumed_state = False

    async def async_added_to_hass(self) -> None:
        """Ask the coordinator to start reading the register, where it reads back.

        Disabled entities are never added, so leaving the switch off costs no reads.
        """
        await super().async_added_to_hass()
        if self._control.readback:
            self.coordinator.enable_onoff_polling(self._control.register)

    @property
    def is_on(self) -> bool | None:
        if self._control.readback:
            return decode(self._control, self.coordinator.onoff_raw)
        return self._attr_is_on

    async def async_turn_on(self, **kwargs) -> None:
        await self._async_set(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self._async_set(False)

    async def _async_set(self, on: bool) -> None:
        try:
            value = await self.hass.async_add_executor_job(
                set_power, self.coordinator.modbus_client, self._control, on,
            )
        except PowerControlError as err:
            raise HomeAssistantError(f"Could not switch the inverter {'on' if on else 'off'}: {err}") from err

        _LOGGER.info(
            "Inverter %s: wrote %d (0x%04X) to holding register %d (%s)",
            "on" if on else "off", value, value, self._control.register, self._control.encoding,
        )
        if self._control.readback:
            await self.coordinator.async_request_refresh()
            return
        self._attr_is_on = on
        self.async_write_ha_state()
