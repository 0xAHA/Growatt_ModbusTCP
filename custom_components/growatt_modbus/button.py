"""Button platform for Growatt Modbus Integration.

One button so far: Inverter Clock Sync. It is the entity form of the
`growatt_modbus.sync_inverter_time` action, for people who want a press rather than a
scripted call, and it is deliberately disabled by default - see the class docstring.
"""
import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
import homeassistant.util.dt as dt_util

from .const import DEVICE_TYPE_INVERTER
from .entity import GrowattEntity
from .growatt_modbus import ModbusWriteError

_LOGGER = logging.getLogger(__name__)

# Writable platform - serialise. See number.py for the reasoning.
PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Growatt Modbus buttons."""
    coordinator = config_entry.runtime_data

    entities = []

    # Off-grid profiles store the year differently and give register 51 to Chip Select
    # rather than the weekday, so the clock write is not offered there at all (#393).
    if coordinator.modbus_client.is_clock_supported:
        entities.append(GrowattSyncClockButton(coordinator, config_entry))

    async_add_entities(entities)


class GrowattSyncClockButton(GrowattEntity, ButtonEntity):
    """Set the inverter's real-time clock from Home Assistant's local time.

    Disabled by default, and categorised as diagnostic so it sits alongside the Inverter
    Clock sensor rather than in the main controls card.

    Disabled rather than merely rare: these are holding registers and very likely
    EEPROM-backed (#392), so this writes six of them on every press. A button that is
    present but off is the right default for something with a finite write budget - it
    takes one toggle to enable, and nobody presses it by accident in the meantime.
    """

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False
    _attr_icon = "mdi:clock-check-outline"
    _attr_translation_key = "sync_inverter_clock"

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        """Initialise the clock sync button."""
        super().__init__(
            coordinator,
            config_entry,
            unique_key="sync_inverter_clock",
            device_type=DEVICE_TYPE_INVERTER,
        )

    async def async_press(self) -> None:
        """Write the current local time to the inverter.

        Local time, not UTC: the inverter has no timezone concept and its time-of-use
        windows are set in wall-clock terms.
        """
        client = self.coordinator.modbus_client
        now = dt_util.now().replace(tzinfo=None)

        try:
            await self.hass.async_add_executor_job(client.write_inverter_time, now)
        except ModbusWriteError as err:
            # The message carries whether anything was written, which is the part the
            # user needs. Do not flatten it into a generic failure.
            raise HomeAssistantError(f"Could not set the inverter clock: {err}") from err
        except Exception as err:
            raise HomeAssistantError(f"Could not set the inverter clock: {err}") from err

        _LOGGER.info("Inverter clock set to %s", now.strftime("%Y-%m-%d %H:%M:%S"))

        # Refresh so the Inverter Clock sensor reflects the write rather than waiting out
        # the poll interval.
        await self.coordinator.async_request_refresh()
