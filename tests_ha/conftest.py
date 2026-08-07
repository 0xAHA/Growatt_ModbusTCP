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
    """Stop the coordinator opening a socket.

    The config and options flows are what these tests exercise; letting them attempt a
    real connection would make them slow and dependent on network behaviour.
    """
    with patch(
        "custom_components.growatt_modbus.GrowattModbusCoordinator._fetch_data",
        return_value=None,
    ):
        yield
