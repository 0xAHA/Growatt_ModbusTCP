"""A failed write must say why, through Home Assistant's service boundary.

`write_register` raised plain `ValueError` on every failure, including the WIT's
own write cooldown. Home Assistant renders an unhandled exception from a service
as an HTTP 500 whose body is the generic "Server got itself in trouble" — the
message does not survive. A caller over the REST API therefore could not tell a
transient cooldown refusal (retry in 30 s) from a hard Modbus failure, and the
battery-optimizer commissioning backend, which classifies exactly that by
matching on the message text, saw both as a hard failure.

`HomeAssistantError` is what crosses that boundary with its message intact. Per
the integration quality scale, it is also the right class here: bad caller input
is `ServiceValidationError`, while a device that refused the write right now is
an operational failure. The device/config-entry lookups below it are left as
they are — those are argument errors, not device failures.
"""
from __future__ import annotations

import asyncio
import importlib
from pathlib import Path

import pytest

_diag = importlib.import_module("growatt_under_test.diagnostic")
_gm = importlib.import_module("growatt_under_test.growatt_modbus")

HomeAssistantError = importlib.import_module("homeassistant.exceptions").HomeAssistantError

COMPONENT = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"


class _Client:
    """A client whose write fails the way each test needs it to."""

    def __init__(self, *, rate_limited=False, error=None):
        self.rate_limited = rate_limited
        self.error = error

    def write_register(self, register, value):
        if self.error is not None:
            raise _gm.ModbusWriteError(register, [value], self.error)
        # False -- not an exception -- is how the client reports the WIT cooldown.
        return not self.rate_limited

    def write_registers(self, register, values):
        if self.error is not None:
            raise _gm.ModbusWriteError(register, list(values), self.error)
        return True


class _Coordinator:
    def __init__(self, client):
        self._client = client
        self.refreshed = 0
        # The write-reversion tracker the service clears on a successful write
        # (#411). Present so this fake stays a fake of the real coordinator.
        self._pending_write_checks: dict = {}

    async def async_request_refresh(self):
        self.refreshed += 1


class _Hass:
    """Only what the service handlers touch."""

    def __init__(self):
        self.services = self
        self.handlers = {}

    def async_register(self, domain, name, handler, schema=None, **kwargs):
        self.handlers[name] = handler

    async def async_add_executor_job(self, func, *args):
        return func(*args)


class _Call:
    def __init__(self, **data):
        self.data = data


def _service(monkeypatch, name, client):
    """Register the real services against fakes and hand back one handler."""
    hass = _Hass()
    coordinator = _Coordinator(client)

    device_registry = type("Reg", (), {"async_get": lambda self, device_id: object()})()
    monkeypatch.setattr(_diag.dr, "async_get", lambda hass: device_registry,
                        raising=False)
    monkeypatch.setattr(_diag, "_config_entry_id_for_device",
                        lambda hass, entry: "entry_id")
    monkeypatch.setattr(_diag, "_coordinator_for_entry",
                        lambda hass, entry_id: coordinator)

    asyncio.run(_diag.async_setup_services(hass))
    return hass.handlers[name], coordinator


def test_the_wit_cooldown_reaches_the_caller_as_a_ha_service_error(monkeypatch):
    """The case this was written for: a refusal the caller should retry, not report."""
    handler, _ = _service(monkeypatch, "write_register", _Client(rate_limited=True))

    with pytest.raises(HomeAssistantError) as raised:
        asyncio.run(handler(_Call(device_id="dev", register=30100, value=1)))

    message = str(raised.value)
    assert "rate-limited" in message
    assert "30100" in message, "the caller cannot tell which register was refused"


def test_the_cooldown_is_not_a_bare_valueerror(monkeypatch):
    """A ValueError becomes a 500 with a generic body, and the message is lost.

    Asserting the class, not just the message, is the whole point: the text was
    always correct -- it just never left the Home Assistant process.
    """
    handler, _ = _service(monkeypatch, "write_register", _Client(rate_limited=True))

    with pytest.raises(HomeAssistantError):
        asyncio.run(handler(_Call(device_id="dev", register=30100, value=1)))


def test_a_modbus_failure_reaches_the_caller_with_its_reason(monkeypatch):
    handler, _ = _service(monkeypatch, "write_register",
                          _Client(error="Illegal data address"))

    with pytest.raises(HomeAssistantError) as raised:
        asyncio.run(handler(_Call(device_id="dev", register=30407, value=1)))

    assert "Illegal data address" in str(raised.value)


def test_write_registers_fails_the_same_way(monkeypatch):
    """The multi-register write shares the boundary and must share the behaviour."""
    handler, _ = _service(monkeypatch, "write_registers",
                          _Client(error="Gateway target device failed to respond"))

    with pytest.raises(HomeAssistantError) as raised:
        asyncio.run(handler(_Call(device_id="dev", register=30412,
                                  values=[0, 1439, 1])))

    assert "Gateway target device failed to respond" in str(raised.value)


def test_a_write_that_succeeds_still_refreshes_the_coordinator(monkeypatch):
    """Guards the happy path against the error handling above."""
    handler, coordinator = _service(monkeypatch, "write_register", _Client())

    asyncio.run(handler(_Call(device_id="dev", register=30408, value=5)))

    assert coordinator.refreshed == 1


@pytest.mark.parametrize("action", ("set_battery_mode", "sync_tou_schedule"))
def test_the_broad_handler_does_not_re_wrap_a_ha_error(action):
    """Both actions end in `except Exception` -- which would catch the
    HomeAssistantErrors raised inside them and bury the reason inside a second
    message. Source-level because reaching those branches needs the whole VPP
    write sequence stubbed, and the guard is one line."""
    source = (COMPONENT / "diagnostic.py").read_text(encoding="utf-8")
    tree = importlib.import_module("ast").parse(source)
    func = next(
        n for n in importlib.import_module("ast").walk(tree)
        if getattr(n, "name", None) == action
    )
    body = importlib.import_module("ast").get_source_segment(source, func)
    assert "except HomeAssistantError:" in body, (
        f"{action} re-wraps a HomeAssistantError, losing the original reason"
    )
    for failure in ('raise ValueError("Failed', 'raise ValueError(f"Failed'):
        assert failure not in body, (
            f"{action} still reports a device failure as a ValueError"
        )
