"""Fixtures for the Home Assistant integration tests.

These run only in CI, on Linux, where `pytest-homeassistant-custom-component` installs
from prebuilt wheels. They cannot run on Windows: Home Assistant pins
`lru-dict==1.3.0`, which has no CPython 3.13 Windows wheel and needs a C compiler.

Kept separate from `tests/` deliberately. That suite has three small dependencies and
runs in half a second, which is what makes it usable on every register-map change.
Merging the two would drag Home Assistant into every run and lose that.
"""
from __future__ import annotations

from unittest.mock import patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.growatt_modbus.const import DOMAIN


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Load `custom_components/` — without this HA ignores the integration entirely."""
    yield


@pytest.fixture
def mock_entry() -> MockConfigEntry:
    """A TCP config entry resembling a real installation."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Growatt Test",
        data={
            "name": "Growatt Test",
            "connection_type": "tcp",
            "host": "192.0.2.10",     # TEST-NET-1, guaranteed unroutable
            "port": 502,
            "slave_id": 1,
            "inverter_series": "min_7000_10000_tl_x",
            "register_map": "MIN_7000_10000TL_X",
            "vpp_protocol_confirmed": False,
        },
        options={
            "scan_interval": 60,
            "modbus_delay": 250,
        },
    )


@pytest.fixture
def bypass_connection():
    """Stop the integration touching a socket.

    Two reasons. The flows and lifecycle are what these tests exercise, so a real
    connection would only add latency and flakiness — and `pytest-socket`, which ships
    with the harness, blocks socket creation outright, so anything that reaches the
    transport raises rather than merely being slow.

    Patched at several levels because setup can reach the transport by more than one
    route: the coordinator's poll, the shared hub's connect, and the client's own
    connect used by device identification.
    """
    with (
        patch(
            "custom_components.growatt_modbus.coordinator.GrowattModbusCoordinator._fetch_data",
            return_value=None,
        ),
        patch(
            "custom_components.growatt_modbus.growatt_modbus.SharedModbusConnection.ensure_connected",
            return_value=True,
        ),
        patch(
            "custom_components.growatt_modbus.growatt_modbus.SharedModbusConnection.disconnect",
            return_value=None,
        ),
        patch(
            "custom_components.growatt_modbus.growatt_modbus.GrowattModbus.connect",
            return_value=True,
        ),
        patch(
            "custom_components.growatt_modbus.growatt_modbus.GrowattModbus.disconnect",
            return_value=None,
        ),
    ):
        yield


async def setup_entry(hass, entry) -> None:
    """Set the entry up, failing with the reason rather than a bare False.

    `async_setup` returns False and swallows the exception into ConfigEntryState, so a
    plain `assert await ...` reports only "assert False" — useless in CI, where a log
    round-trip costs minutes. Surfacing `entry.reason` makes one run diagnostic.
    """
    entry.add_to_hass(hass)
    ok = await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert ok, f"setup failed — state={entry.state}, reason={entry.reason!r}"
