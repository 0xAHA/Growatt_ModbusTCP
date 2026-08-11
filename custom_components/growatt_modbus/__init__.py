"""
Growatt Modbus Integration for Home Assistant
"""
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import device_registry as dr


from .const import (
    DOMAIN,
    CONF_DEVICE_STRUCTURE_VERSION,
    CONF_INVERTER_SERIES,
    CONF_REGISTER_MAP,
    CONF_CONNECTION_TYPE,
    CURRENT_DEVICE_STRUCTURE_VERSION,
    REGISTER_MAPS,
    WRITABLE_REGISTERS,
    DEVICE_TYPE_INVERTER,
)
from .coordinator import GrowattConfigEntry, GrowattModbusCoordinator
from .device_profiles import get_profile
from .diagnostic import async_setup_services
from .growatt_modbus import SharedModbusConnection

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.SELECT, Platform.NUMBER, Platform.TIME]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Growatt Modbus integration."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].setdefault("_connections", {})

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
    #
    # WARNING: this is a second copy of number.py's `friendly_overrides`, and it has
    # drifted. It is missing export_limit_failed_power_rate, load_first_battery_minimum_soc,
    # grid_first_discharge_stopped_soc and batt_first_charge_stopped_soc.
    #
    # The drift is not cosmetic. For any name missing here, this migration computes the
    # expected entity_id from `.title()` while number.py builds the entity from the
    # override — so the two disagree and this rename fights the platform on every setup.
    # grid_first_discharge_stopped_soc is the clear case: number.py creates
    # "Discharge Stopped SOC" and this renames it to "Grid First Discharge Stopped Soc".
    #
    # Not corrected here, deliberately: putting the four missing names back would rename
    # those entities for everyone already running them, breaking automations that use the
    # current IDs. That is a decision to take on its own, not a side effect of adding a
    # control. The permanent fix is to import number.py's dict rather than restate it.
    _NUMBER_FRIENDLY_OVERRIDES = {
        'active_power_rate': 'VPP Active Power Rate',
        'export_limit_w': 'VPP Export Limit (W)',
        'max_output_power_rate': 'Max Output Power Rate',
        'vpp_export_limit_power_rate': 'VPP Export Limit Power Rate',
        # New in #372. Listed in both copies from the outset so it cannot join the drift
        # above; both forms happen to slugify identically, so it is a no-op today.
        'grid_charge_stopped_soc': 'Grid Charge Stopped SOC',
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

    # Remove stale WIT TOU start/end number entities (migrated to TimeEntity in v0.9.7)
    for _p in range(1, 11):
        for _slot in ('start', 'end'):
            _stale_uid = f"{entry.entry_id}_vpp_tou_p{_p}_{_slot}"
            _stale_eid = entity_registry.async_get_entity_id("number", DOMAIN, _stale_uid)
            if _stale_eid:
                _LOGGER.info("Removing stale number entity %s (WIT TOU migrated to time entity)", _stale_eid)
                entity_registry.async_remove(_stale_eid)

    # Remove stale WIT export_limit_w number entity (removed in v0.9.8 — reg 203 not writable on WIT)
    _stale_export_eid = entity_registry.async_get_entity_id("number", DOMAIN, f"{entry.entry_id}_export_limit_w")
    if _stale_export_eid:
        _LOGGER.info("Removing stale number entity %s (WIT export_limit_w reg 203 not writable)", _stale_export_eid)
        entity_registry.async_remove(_stale_export_eid)

    # Shared connection hub: all TCP entries on the same host:port share one ModbusTcpClient
    # and a threading.Lock to serialize reads/writes and prevent RS485 cross-talk on the gateway.
    # This is transparent for single-entry setups (hub refcount=1, no actual sharing).
    hub: SharedModbusConnection | None = None
    connection_type = entry.data.get(CONF_CONNECTION_TYPE, "tcp")
    if connection_type == "tcp":
        from homeassistant.const import CONF_HOST, CONF_PORT
        host = entry.data.get(CONF_HOST, "")
        port = entry.data.get(CONF_PORT, 502)
        timeout = entry.options.get("timeout", 10)
        hub_key = f"{host}:{port}"
        connections = hass.data[DOMAIN].setdefault("_connections", {})
        if hub_key not in connections:
            connections[hub_key] = SharedModbusConnection(host=host, port=port, timeout=timeout)
            _LOGGER.debug("Created shared Modbus connection hub for %s", hub_key)
        hub = connections[hub_key]
        hub.acquire_ref()
        if hub._refcount > 1:
            _LOGGER.info(
                "Shared Modbus connection mode: entry %s joined hub for %s (refcount=%d) — "
                "RS485 gateway cross-talk prevention active",
                entry.entry_id, hub_key, hub._refcount,
            )

    coordinator = GrowattModbusCoordinator(hass, entry, hub=hub)

    await coordinator.async_config_entry_first_refresh()

    # Cleanup that depends on LIVE data has to wait for a real poll.
    #
    # These blocks used to run here, gated on coordinator.data.serial_number being
    # populated. They never fired. async_config_entry_first_refresh() deliberately does
    # not contact the inverter (#262): it seeds an empty GrowattData() and schedules the
    # real poll as a background task that runs *after* setup returns. So serial_number
    # was always "" at this point, the guard was always False, and every one of these
    # removals was dead code — silently, because a cleanup that does nothing looks
    # exactly like a cleanup with nothing to do.
    #
    # Hooked to the coordinator instead, running once on the first poll that actually
    # reached the inverter, then unsubscribing.
    _vpp_cleanup_done = False

    @callback
    def _cleanup_unsupported_vpp_entities() -> None:
        nonlocal _vpp_cleanup_done
        if _vpp_cleanup_done:
            return
        data = coordinator.data
        # An empty placeholder means no successful poll yet — we cannot tell an
        # unsupported register from an inverter that is simply offline (#255).
        if data is None or not data.serial_number:
            return
        _vpp_cleanup_done = True

        registry = er.async_get(hass)
        if not data.vpp_export_limit_available:
            for control_name in ('vpp_export_limit_enable', 'vpp_export_limit_power_rate'):
                stale_uid = f"{entry.entry_id}_{control_name}"
                for platform in ('select', 'number'):
                    stale_eid = registry.async_get_entity_id(platform, DOMAIN, stale_uid)
                    if stale_eid:
                        _LOGGER.info(
                            "Removing stale VPP export limit entity %s "
                            "(register 30200/30201 not responsive)", stale_eid,
                        )
                        registry.async_remove(stale_eid)

        if not data.vpp_control_authority_available:
            stale_uid = f"{entry.entry_id}_control_authority"
            stale_eid = registry.async_get_entity_id("select", DOMAIN, stale_uid)
            if stale_eid:
                _LOGGER.info(
                    "Removing stale control_authority entity %s "
                    "(register 30100 not responsive)", stale_eid,
                )
                registry.async_remove(stale_eid)

    entry.async_on_unload(coordinator.async_add_listener(_cleanup_unsupported_vpp_entities))

    # Remove SOC-limit entities whose register is no longer in the profile.
    #
    # 1071/1091 were dropped from the MOD/MID profile in #362: they exist on that
    # hardware but do nothing — writes are accepted and silently ignored, and the
    # registers read back 0 forever (#343, #362). Dropping them from the profile stops
    # the entities being created, but Home Assistant keeps previously-created entities
    # in its registry, where they would linger as unavailable and still look like the
    # control to reach for. Removing them points users at 3048/3067, which work.
    # No connectivity guard here, deliberately. Whether a register is in the profile is a
    # static fact about the selected profile — it needs no inverter and no poll. The
    # guard these blocks originally copied exists for the VPP checks above, which cannot
    # distinguish "unsupported" from "offline" without live data. Applying it here is
    # what stopped this running at all on v1.4.0 (#362).
    profile = get_profile(entry.data.get(CONF_INVERTER_SERIES, ""))
    register_map = REGISTER_MAPS.get((profile or {}).get("register_map", ""), {})
    holding = register_map.get("holding_registers", {})
    defined = {reg.get("name") for reg in holding.values() if isinstance(reg, dict)}
    entity_registry = er.async_get(hass)
    for control_name in ("discharge_stopped_soc", "charge_stopped_soc"):
        if control_name in defined:
            continue
        stale_uid = f"{entry.entry_id}_{control_name}"
        stale_eid = entity_registry.async_get_entity_id("number", DOMAIN, stale_uid)
        if stale_eid:
            _LOGGER.info(
                "Removing %s — the register is not in this profile because writes to "
                "it have no effect on this hardware. Use Charge/Discharge Stopped SOC "
                "(registers 3048/3067) instead.",
                stale_eid,
            )
            entity_registry.async_remove(stale_eid)

    # Battery Temperature on MOD/MID was register 3176, which #362 identified as
    # Bdc1Temp1 — the DC-DC converter stage, not the pack. It now reports as DC-DC
    # Temperature, and on these systems the BMS publishes no cell temperature at all, so
    # there is nothing for the old entity to show.
    #
    # Removing it from the registry is necessary but NOT sufficient: the sensor platform
    # recreates whatever its profile's sensor set lists, and battery_temp's condition
    # `hasattr(data, 'battery_temp')` can never be False because battery_temp is a
    # dataclass field with a 0.0 default. That is why v1.4.0 left it reporting 0.0 °C
    # instead of removing it — a plausible-looking reading rather than a missing sensor.
    # The real fix is dropping it from the MOD/MID sensor set in device_profiles.py;
    # this removal only clears what earlier versions already registered.
    inputs = register_map.get("input_registers", {})
    input_names = {reg.get("name") for reg in inputs.values() if isinstance(reg, dict)}
    if "battery_temp" not in input_names:
        stale_uid = f"{entry.entry_id}_battery_temp"
        stale_eid = entity_registry.async_get_entity_id("sensor", DOMAIN, stale_uid)
        if stale_eid:
            _LOGGER.info(
                "Removing %s — register 3176 is the DC-DC converter temperature, not "
                "the battery (#362). It is now reported as DC-DC Temperature.",
                stale_eid,
            )
            entity_registry.async_remove(stale_eid)

    # General rule: a sensor the current profile does not list cannot be recreated, so a
    # registry entry for it is stale by definition.
    #
    # The two blocks above each clean up one specific removal, which meant every future
    # removal needed its own block — and the next one didn't get it. v1.5.3 dropped
    # dcdc_temp from ~26 profiles that never had the register, and the entities did not
    # disappear: they sat in the registry showing "unavailable", which is arguably worse
    # than the 0.0 °C it replaced, because it looks like a broken sensor rather than one
    # that was never meant to exist.
    #
    # Safe as a blanket rule because sensor.py creates exactly
    # `SENSOR_DEFINITIONS ∩ get_sensors_for_profile(series)` and nothing else — anything
    # outside that intersection has no code path that could bring it back.
    #
    # Not gated on connectivity, for the same reason as the blocks above: profile
    # membership is a static fact needing no inverter and no poll. Gating it is what
    # stopped the v1.4.0 cleanup running at all (#362).
    # A profile key that no longer exists resolves to min_7000_10000_tl_x, which loads
    # cleanly and reports almost nothing on any other model. Nothing fails, so there is
    # nothing for the user to search for — #360 spent a round trip on "my phase sensors
    # show nothing" that turned out to be this.
    #
    # Raised before the cleanup below, which is skipped in that state: the fallback's
    # sensor set is not this device's, and treating it as authoritative would delete
    # every entity the real profile had created.
    from .device_profiles import profile_exists

    configured_profile = entry.data.get(CONF_INVERTER_SERIES, "")
    profile_is_known = profile_exists(configured_profile)
    if not profile_is_known:
        try:
            ir.async_create_issue(
                hass,
                DOMAIN,
                f"unknown_profile_{entry.entry_id}",
                is_fixable=False,
                severity=ir.IssueSeverity.ERROR,
                translation_key="unknown_profile",
                translation_placeholders={"profile": configured_profile or "(none)"},
                learn_more_url=(
                    "https://github.com/0xAHA/Growatt_ModbusTCP/blob/main/"
                    "docs/hardware/models.md"
                ),
            )
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug("Could not create unknown-profile repair issue: %s", err)

    # Imported here rather than at module scope: sensor.py imports coordinator.py, and
    # hoisting this creates a cycle at integration load.
    from .sensor import SENSOR_DEFINITIONS
    from .device_profiles import get_sensors_for_profile

    profile_sensors = get_sensors_for_profile(configured_profile) if profile_is_known else set()
    if profile_sensors:
        for sensor_key in SENSOR_DEFINITIONS:
            if sensor_key in profile_sensors:
                continue
            stale_eid = entity_registry.async_get_entity_id(
                "sensor", DOMAIN, f"{entry.entry_id}_{sensor_key}"
            )
            if stale_eid:
                _LOGGER.info(
                    "Removing %s — '%s' is not in the %s profile, so nothing can "
                    "populate it and it would linger as unavailable",
                    stale_eid, sensor_key, entry.data.get(CONF_INVERTER_SERIES, "?"),
                )
                entity_registry.async_remove(stale_eid)

    # The same rule for controls: a number, select or time entity whose register the
    # profile does not map cannot be recreated, so its registry entry is stale.
    #
    # This generalises what were per-removal blocks above (export_limit_w, the WIT TOU
    # start/end pairs, the time_period pairs), each written by hand when a control was
    # dropped. #371 shows the cost of that pattern: removing 1090 and 1092 from the MOD
    # profile stops the entities being created but leaves them in the registry showing
    # `unavailable`, and nobody would think to add a fourth block. It is the same defect
    # that hit sensors in v1.5.3 and was fixed for them in v1.5.4, one platform over.
    #
    # Safe as a blanket rule because number.py and select.py both create a generic control
    # only when `control_config['register']` is in the profile's holding_registers — so
    # anything failing that test has no code path that could bring it back.
    #
    # Bespoke classes are unaffected: they carry their own unique_ids (allow_grid_charge,
    # the MOD TOU selects, the WIT VPP entities) and are not keyed by a WRITABLE_REGISTERS
    # name, so they are never matched here.
    # `holding` is the active profile's holding_registers, resolved further up for the
    # SOC-limit cleanup.
    if profile_is_known and holding:
        for control_name, control_config in WRITABLE_REGISTERS.items():
            if control_config.get("register") in holding:
                continue
            for _domain in ("number", "select", "time"):
                stale_eid = entity_registry.async_get_entity_id(
                    _domain, DOMAIN, f"{entry.entry_id}_{control_name}"
                )
                if stale_eid:
                    _LOGGER.info(
                        "Removing %s — register %s ('%s') is not in the %s profile, so "
                        "the control cannot work and would linger as unavailable",
                        stale_eid, control_config.get("register"), control_name,
                        configured_profile,
                    )
                    entity_registry.async_remove(stale_eid)

    # Per-entry state lives on the entry itself. hass.data[DOMAIN] is now reserved
    # solely for "_connections", the cross-entry shared-connection registry.
    entry.runtime_data = coordinator

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


async def async_unload_entry(hass: HomeAssistant, entry: GrowattConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        # runtime_data is cleared by HA once unload succeeds; no pop needed.
        coordinator = entry.runtime_data
        hub = getattr(coordinator, '_hub', None)
        if hub is not None:
            # Release the hub reference; hub disconnects when refcount reaches 0
            connections = hass.data[DOMAIN].get("_connections", {})
            hub.release_ref()
            if hub._refcount <= 0:
                # Remove from registry — hub already disconnected in release_ref()
                hub_key = f"{hub.host}:{hub.port}"
                connections.pop(hub_key, None)
                _LOGGER.debug("Shared Modbus connection hub for %s removed (no more users)", hub_key)
        else:
            await hass.async_add_executor_job(coordinator.modbus_client.disconnect)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
