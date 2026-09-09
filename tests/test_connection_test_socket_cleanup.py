"""The connection test must close its socket even when the read throws (#426).

`test_connection()` is the only place in the integration that opens a socket outside the
shared hub - it builds a `GrowattModbus` with no `shared_conn`, so the client owns its own
connection. The close sat immediately after `read_all_data()`, outside any `finally`, and the
function wraps everything in `except Exception`. So a read that raised skipped the close,
the error was swallowed into a friendly return value, and the socket stayed established with
nothing holding a reference that could close it.

This is not free. A gateway has a hard client limit - an Elfin EW11 accepts five - and this
runs on every connection test in the config and options flows. That is the retry loop someone
works through when the connection is not right yet, which is precisely when the read is most
likely to throw. Each attempt burned a slot until Home Assistant restarted.

Found while investigating a separate socket leak on reload (#426); this one is in the config
flow rather than the reload path, so it is not that bug, but it is the same failure.

The suite has no Home Assistant, so the function is extracted and run against stubs.
"""
from __future__ import annotations

import ast
import sys
import types
from pathlib import Path

import pytest

sys.path.insert(0, "tests")

COMPONENT = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
SOURCE = (COMPONENT / "coordinator.py").read_text(encoding="utf-8")


class _Client:
    """Records connect/disconnect so a leak is visible as a missing close."""

    def __init__(self, *, connects=True, read=None, raises=None):
        self._connects = connects
        self._read = read
        self._raises = raises
        self.connected = False
        self.disconnects = 0

    def connect(self):
        self.connected = self._connects
        return self._connects

    def read_all_data(self):
        if self._raises is not None:
            raise self._raises
        return self._read

    def disconnect(self):
        self.disconnects += 1
        self.connected = False


def _load(client):
    """Extract test_connection() and run it against a stub client."""
    fn = next(
        node for node in ast.parse(SOURCE).body
        if isinstance(node, ast.FunctionDef) and node.name == "test_connection"
    )
    module = types.ModuleType("_tc")
    module.__dict__.update({
        "GrowattModbus": lambda **kwargs: client,
        "REGISTER_MAPS": {"MIN_7000_10000TL_X": {}},
        "CONF_REGISTER_MAP": "register_map",
        "CONF_CONNECTION_TYPE": "connection_type",
        "CONF_HOST": "host", "CONF_PORT": "port", "CONF_SLAVE_ID": "slave_id",
        "CONF_DEVICE_PATH": "device_path", "CONF_BAUDRATE": "baudrate",
        "_LOGGER": types.SimpleNamespace(exception=lambda *a, **k: None,
                                         debug=lambda *a, **k: None),
    })
    exec(compile(ast.Module(body=[fn], type_ignores=[]), "<tc>", "exec"), module.__dict__)
    return module.test_connection


CONFIG = {"host": "10.0.0.1", "port": 502, "slave_id": 1, "connection_type": "tcp"}


def test_a_read_that_throws_still_closes_the_socket():
    """THE regression. The exception is caught and reported as a failed test either way -
    the difference is whether the socket went with it."""
    client = _Client(raises=OSError("connection reset by peer"))

    result = _load(client)(CONFIG)

    assert client.disconnects == 1, (
        "the socket was left open when the read raised; on a gateway with a five-client "
        "limit each failed attempt burns a slot until Home Assistant restarts"
    )
    assert result["success"] is False


def test_the_error_still_reaches_the_caller():
    """Guard against fixing the leak by swallowing the failure differently."""
    client = _Client(raises=OSError("connection reset by peer"))

    result = _load(client)(CONFIG)

    assert "reset by peer" in result["error"]


def test_a_successful_read_closes_too():
    """The path that already worked must keep working."""
    data = types.SimpleNamespace(serial_number="ABC123", firmware_version="1.0")
    client = _Client(read=data)

    result = _load(client)(CONFIG)

    assert client.disconnects == 1
    assert result["success"] is True
    assert result["serial_number"] == "ABC123"


def test_a_read_returning_nothing_closes_too():
    """`None` is a failure without an exception - a third path through the same code."""
    client = _Client(read=None)

    result = _load(client)(CONFIG)

    assert client.disconnects == 1
    assert result["success"] is False


def test_a_failed_connect_does_not_close_what_was_never_opened():
    """Guard against over-correcting. Calling disconnect() on a client that never connected
    is harmless here, but it would mean the close had moved somewhere that cannot tell the
    two apart."""
    client = _Client(connects=False)

    result = _load(client)(CONFIG)

    assert client.disconnects == 0
    assert result["success"] is False
    assert "connect" in result["error"].lower()


def test_the_close_is_in_a_finally():
    """Asserted structurally as well as behaviourally.

    The behavioural tests above would also pass if someone wrapped the read in its own
    try/except and closed in both arms - which works until a third exit is added. The
    `finally` is what makes it hold for exits nobody has written yet.
    """
    fn = next(
        node for node in ast.parse(SOURCE).body
        if isinstance(node, ast.FunctionDef) and node.name == "test_connection"
    )
    finallys = [n for n in ast.walk(fn) if isinstance(n, ast.Try) and n.finalbody]

    assert finallys, "test_connection() has no try/finally, so a new exit can leak again"
    assert any(
        "disconnect" in ast.unparse(stmt)
        for node in finallys for stmt in node.finalbody
    ), "the finally block does not close the client"
