"""
Growatt Modbus Integration for Home Assistant
"""
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import device_registry as dr


from .const import (
    DOMAIN,
    CONF_DEVICE_STRUCTURE_VERSION,
    CONF_INVERTER_SERIES,
    CONF_REGISTER_MAP,
    CURRENT_DEVICE_STRUCTURE_VERSION,
    WRITABLE_REGISTERS,
    DEVICE_TYPE_INVERTER,
)
from .coordinator import GrowattModbusCoordinator
from .diagnostic import async_setup_services

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.SELECT, Platform.NUMBER, Platform.TIME]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Growatt Modbus integration."""
    hass.data.setdefault(DOMAIN, {})
    
    # Set up diagnostic service
    await async_setup_services(hass)
    
    return True


def _migrate_entity_ids(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Rename entity IDs in the registry to match the has_entity_name=True convention.

    With has_entity_name=True, HA composes entity IDs as:
      {domain}.{device_name_slug}_{entity_short_name_slug}

    Previous naming included the integration name in _attr_name, producing double-prefix
    IDs once sub-devices (via_device) were introduced in v0.6.6.

    unique_id is the stable anchor used to find each entity regardless of its current ID.
    """
    from homeassistant.util import slugify as ha_slugify
    from .sensor import SENSOR_DEFINITIONS
    from .const import (
        get_device_type_for_sensor,
        get_device_type_for_control,
        DEVICE_TYPE_SOLAR,
        DEVICE_TYPE_GRID,
        DEVICE_TYPE_LOAD,
        DEVICE_TYPE_BATTERY,
    )

    _DEVICE_SUFFIX = {
        DEVICE_TYPE_SOLAR: "Solar",
        DEVICE_TYPE_GRID: "Grid",
        DEVICE_TYPE_LOAD: "Load",
        DEVICE_TYPE_BATTERY: "Battery",
    }

    ent_name = entry.data['name']
    entity_registry = er.async_get(hass)

    def _new_eid(domain: str, device_type: str, short_name: str) -> str:
        suffix = _DEVICE_SUFFIX.get(device_type)
        dev_name = f"{ent_name} {suffix}" if suffix else ent_name
        return f"{domain}.{ha_slugify(dev_name)}_{ha_slugify(short_name)}"

    def _try_rename(current_eid: str, expected_eid: str) -> None:
        if current_eid == expected_eid:
            return
        try:
            entity_registry.async_update_entity(current_eid, new_entity_id=expected_eid)
            _LOGGER.info("v0.6.7 entity ID migration: %s → %s", current_eid, expected_eid)
        except Exception as exc:  # noqa: BLE001
            _LOGGER.debug("v0.6.7 entity ID migration skipped %s → %s: %s", current_eid, expected_eid, exc)

    # Sensors
    for sensor_key, sensor_def in SENSOR_DEFINITIONS.items():
        uid = f"{entry.entry_id}_{sensor_key}"
        current = entity_registry.async_get_entity_id("sensor", DOMAIN, uid)
        if current:
            _try_rename(current, _new_eid("sensor", get_device_type_for_sensor(sensor_key), sensor_def['name']))

    # Binary sensor (inverter online)
    bin_uid = f"{entry.entry_id}_inverter_online"
    bin_current = entity_registry.async_get_entity_id("binary_sensor", DOMAIN, bin_uid)
    if bin_current:
        _try_rename(bin_current, f"binary_sensor.{ha_slugify(ent_name)}_inverter_online")

    # Select / Number / Time controls
    _NUMBER_FRIENDLY_OVERRIDES = {
        'active_power_rate': 'VPP Active Power Rate',
        'export_limit_w': 'VPP Export Limit (W)',
        'max_output_power_rate': 'Max Output Power Rate',
        'vpp_export_limit_power_rate': 'VPP Export Limit Power Rate',
    }
    for control_name in WRITABLE_REGISTERS:
        base_friendly = control_name.replace('_', ' ').title()
        for domain in ("select", "number", "time"):
            uid = f"{entry.entry_id}_{control_name}"
            current = entity_registry.async_get_entity_id(domain, DOMAIN, uid)
            if not current:
                continue
            friendly = _NUMBER_FRIENDLY_OVERRIDES.get(control_name, base_friendly) if domain == "number" else base_friendly
            device_type = get_device_type_for_control(control_name)
            _try_rename(current, _new_eid(domain, device_type, friendly))


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Growatt Modbus from a config entry."""

    # Check if we need to migrate device structure
    current_version = entry.data.get(CONF_DEVICE_STRUCTURE_VERSION, 1)

    if current_version < CURRENT_DEVICE_STRUCTURE_VERSION:
        _LOGGER.info(
            "Upgrading device structure from v%s to v%s for %s",
            current_version,
            CURRENT_DEVICE_STRUCTURE_VERSION,
            entry.title,
        )

        # Update version in config entry
        new_data = {**entry.data}
        new_data[CONF_DEVICE_STRUCTURE_VERSION] = CURRENT_DEVICE_STRUCTURE_VERSION
        hass.config_entries.async_update_entry(entry, data=new_data)

        _LOGGER.info(
            "Device structure upgraded successfully. "
            "Entities will now be organized into separate devices: "
            "Inverter (with system controls), Solar, Grid, Load, and Battery (if present)"
        )

    # Auto-migrate: downgrade incorrectly assigned _v201 profiles (added v0.7.8)
    # Before v0.7.8, the setup flow used auto_detected=True as evidence of V2.01 support.
    # That flag is True for ANY successful detection (including legacy register probing),
    # so non-VPP inverters were silently assigned _v201 profiles and flooded logs with
    # "Modbus Error: Illegal Function" every poll cycle.
    # Fix: vpp_protocol_confirmed (added v0.7.8) is True only when DTC read from register
    # 30000 confirmed V2.01. Absent/False on old installs means V2.01 was never confirmed.
    current_series = entry.data.get(CONF_INVERTER_SERIES, "")
    if "_v201" in current_series and not entry.data.get("vpp_protocol_confirmed", False):
        from .auto_detection import convert_to_legacy_profile
        from .device_profiles import get_profile as _get_profile
        legacy_series = convert_to_legacy_profile(current_series)
        legacy_profile = _get_profile(legacy_series)
        if legacy_series != current_series and legacy_profile:
            new_data = {
                **entry.data,
                CONF_INVERTER_SERIES: legacy_series,
                CONF_REGISTER_MAP: legacy_profile["register_map"],
                "vpp_protocol_confirmed": False,
            }
            hass.config_entries.async_update_entry(entry, data=new_data)
            _LOGGER.warning(
                "Growatt Modbus: auto-migrated '%s' → '%s' "
                "(vpp_protocol_confirmed was not set — V2.01 protocol was never confirmed at setup). "
                "If this inverter genuinely supports V2.01, reconfigure to restore it.",
                current_series,
                legacy_series,
            )

    # Auto-migrate: resolve profile key aliases (added v0.7.9)
    # PROFILE_ALIASES maps retired/duplicate keys to their canonical replacement.
    # When two profile keys are functionally identical (same register_map, same sensors),
    # one is designated canonical and the other added to PROFILE_ALIASES so existing
    # config entries are silently updated without any behaviour change.
    from .device_profiles import PROFILE_ALIASES, get_profile as _get_profile_alias
    _current_series = entry.data.get(CONF_INVERTER_SERIES, "")
    if _current_series in PROFILE_ALIASES:
        _canonical = PROFILE_ALIASES[_current_series]
        _canonical_profile = _get_profile_alias(_canonical)
        hass.config_entries.async_update_entry(entry, data={
            **entry.data,
            CONF_INVERTER_SERIES: _canonical,
            CONF_REGISTER_MAP: _canonical_profile["register_map"],
        })
        _LOGGER.info(
            "Growatt Modbus: profile key alias resolved '%s' → '%s' "
            "(both keys are functionally identical — no behaviour change).",
            _current_series,
            _canonical,
        )

    # Remove stale number entities for time_period start/end controls (migrated to TimeEntity in v0.6.4)
    entity_registry = er.async_get(hass)
    stale_time_controls = {k for k in WRITABLE_REGISTERS if 'time_period' in k and k.endswith(('_start', '_end'))}
    for control_name in stale_time_controls:
        old_entity_id = entity_registry.async_get_entity_id("number", DOMAIN, f"{entry.entry_id}_{control_name}")
        if old_entity_id:
            _LOGGER.info("Removing stale number entity %s (migrated to time entity)", old_entity_id)
            entity_registry.async_remove(old_entity_id)

    coordinator = GrowattModbusCoordinator(hass, entry)

    await coordinator.async_config_entry_first_refresh()

    # Remove stale VPP export limit entities if the inverter doesn't respond to these registers.
    # Guard: only remove when the inverter actually connected (serial_number non-empty) —
    # if the inverter was offline at startup we have an empty placeholder and can't know yet
    # whether these registers are supported (Issue #255).
    inverter_connected = coordinator.data is not None and bool(coordinator.data.serial_number)
    if inverter_connected and not coordinator.data.vpp_export_limit_available:
        entity_registry = er.async_get(hass)
        for control_name in ('vpp_export_limit_enable', 'vpp_export_limit_power_rate'):
            stale_uid = f"{entry.entry_id}_{control_name}"
            for platform in ('select', 'number'):
                stale_eid = entity_registry.async_get_entity_id(platform, DOMAIN, stale_uid)
                if stale_eid:
                    _LOGGER.info("Removing stale VPP export limit entity %s (register 30200/30201 not responsive)", stale_eid)
                    entity_registry.async_remove(stale_eid)

    # Remove stale control_authority entity if the inverter doesn't respond to register 30100
    if inverter_connected and not coordinator.data.vpp_control_authority_available:
        entity_registry = er.async_get(hass)
        stale_uid = f"{entry.entry_id}_control_authority"
        stale_eid = entity_registry.async_get_entity_id("select", DOMAIN, stale_uid)
        if stale_eid:
            _LOGGER.info("Removing stale control_authority entity %s (register 30100 not responsive)", stale_eid)
            entity_registry.async_remove(stale_eid)

    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Pre-create the parent inverter device so sub-devices (solar, grid, load, battery)
    # can safely reference it via via_device before their sensors are added.
    # Without this, HA 2025.12+ raises "referencing a non-existing via_device".
    _inv_info = coordinator.get_device_info(DEVICE_TYPE_INVERTER)
    dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers=_inv_info["identifiers"],
        name=_inv_info.get("name"),
        manufacturer=_inv_info.get("manufacturer"),
        model=_inv_info.get("model"),
        hw_version=_inv_info.get("hw_version"),
    )

    # v0.6.7: Rename entity IDs to has_entity_name=True convention.
    # HA 2025.x generates entity IDs as {device_slug}_{entity_slug} for entities on sub-devices.
    # Before v0.6.6: _attr_name included the integration prefix → entity IDs were correct by accident.
    # v0.6.6 introduced via_device (sub-devices); without has_entity_name=True the device slug was
    # prepended, producing double-prefix IDs like growatt_modbus_grid_growatt_modbus_energy_to_grid.
    # This migration renames existing registry entries to the new short-name IDs.
    _migrate_entity_ids(hass, entry)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await hass.async_add_executor_job(coordinator.modbus_client.disconnect)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
