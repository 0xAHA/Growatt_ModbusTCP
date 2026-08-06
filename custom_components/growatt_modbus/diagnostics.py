"""Diagnostics support for Growatt Modbus.

Surfaces a one-click state dump from the integration and device pages, so the
questions that dominate issue triage — which profile is selected, which version is
running, what the options are, whether the coordinator thinks it is online — can be
answered without a round trip.

This is deliberately NOT a replacement for the Universal Register Scanner service.
The two answer different questions:

  diagnostics (here)  What is the integration's current state?
                      Works even when every read is failing, which is exactly when
                      it is needed. Cannot see registers the profile does not define.

  register scanner    What does the hardware actually respond to?
                      Probes ranges outside the selected profile, offers decode
                      candidates per register, and reports per-register error text.
                      That is how 31059 (total PV power) and the TL-XH2 VPP-only
                      layout were found — neither is visible to diagnostics.

Ask for diagnostics first; ask for a scan when register discovery is needed.
"""
from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

# Host/device path can identify a network or a person's hardware layout, and the
# serial number identifies the unit itself. Users routinely paste diagnostics into
# public issues, so redact by default rather than relying on them to remember.
TO_REDACT = {
    "host",
    "device_path",
    "serial_number",
    "unique_id",
}


def _safe(value: Any) -> Any:
    """Coerce a value into something JSON-serialisable.

    Diagnostics must never raise — a dump that fails is worse than one with a gap,
    because it fails precisely when the integration is already misbehaving.
    """
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, dict):
        return {str(k): _safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_safe(v) for v in value]
    return str(value)


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = hass.data.get(DOMAIN, {}).get(entry.entry_id)

    diagnostics: dict[str, Any] = {
        "entry": {
            "title": entry.title,
            "version": entry.version,
            "source": entry.source,
            "state": str(entry.state),
            "data": _safe(dict(entry.data)),
            "options": _safe(dict(entry.options)),
        },
    }

    if coordinator is None:
        # Entry not loaded — still worth returning what we have. This is a state a
        # user can genuinely be in (failed setup, disabled entry) and the entry data
        # alone answers "which profile" and "what options".
        diagnostics["coordinator"] = None
        diagnostics["note"] = (
            "Coordinator not loaded — the entry may be disabled, or setup may have "
            "failed. Entry data and options above are still accurate."
        )
        return async_redact_data(diagnostics, TO_REDACT)

    client = getattr(coordinator, "_client", None)
    hub = getattr(coordinator, "_hub", None)

    diagnostics["coordinator"] = {
        # Health — the first thing to look at when someone reports "unavailable"
        # or "stuck at zero".
        "inverter_online": getattr(coordinator, "_inverter_online", None),
        "ever_had_real_data": getattr(coordinator, "_ever_had_real_data", None),
        "last_update_success": getattr(coordinator, "last_update_success", None),
        "consecutive_failures": getattr(coordinator, "_consecutive_failures", None),
        "failure_threshold": getattr(coordinator, "_failure_threshold", None),
        "update_interval": _safe(getattr(coordinator, "update_interval", None)),
        "normal_update_interval": _safe(getattr(coordinator, "_normal_update_interval", None)),
        "offline_update_interval": _safe(getattr(coordinator, "_offline_update_interval", None)),
        "in_slow_poll_mode": (
            getattr(coordinator, "update_interval", None)
            == getattr(coordinator, "_offline_update_interval", None)
        ),
        # Identity
        "register_map_key": getattr(coordinator, "_register_map_key", None),
        "serial_number": getattr(coordinator, "_serial_number", None),
        "firmware_version": getattr(coordinator, "_firmware_version", None),
        # Energy-guard state — relevant to every "my totals look wrong" report
        "midnight_grace_expires": _safe(getattr(coordinator, "_midnight_grace_expires", None)),
        "retained_daily_totals": _safe(getattr(coordinator, "_retained_daily_totals", None)),
        "retained_lifetime_totals": _safe(getattr(coordinator, "_retained_lifetime_totals", None)),
        "pending_write_checks": _safe(getattr(coordinator, "_pending_write_checks", None)),
    }

    if client is not None:
        diagnostics["client"] = {
            "connection_type": getattr(client, "connection_type", None),
            "slave_id": getattr(client, "slave_id", None),
            "backed_off": getattr(client, "_backed_off", None),
            "consecutive_read_failures": getattr(client, "_consecutive_read_failures", None),
            "min_read_interval": getattr(client, "min_read_interval", None),
            "block_size_override": getattr(client, "_block_size_override", None),
            "profile_max_block_size": _safe(
                (getattr(client, "register_map", None) or {}).get("max_block_size")
            ),
            # Ranges suppressed after repeated failure — explains "why is this
            # sensor empty" without needing a scan.
            "failed_optional_ranges": _safe(getattr(client, "_failed_optional_ranges", None)),
        }

    if hub is not None:
        diagnostics["shared_connection"] = {
            "active": True,
            "port": getattr(hub, "port", None),
            "refcount": getattr(hub, "_refcount", None),
            "connected": getattr(hub, "_connected", None),
            "recoveries_this_poll": getattr(hub, "_recoveries_this_poll", None),
            "max_recoveries_per_poll": getattr(hub, "_max_recoveries_per_poll", None),
        }
    else:
        diagnostics["shared_connection"] = {"active": False}

    # Current decoded values. Shows at a glance which sensor groups are populated
    # and which are flat zero — the signature of a failed or unsupported range.
    data = getattr(coordinator, "data", None)
    if data is not None and is_dataclass(data):
        diagnostics["data"] = _safe(asdict(data))
    else:
        diagnostics["data"] = None

    return async_redact_data(diagnostics, TO_REDACT)
