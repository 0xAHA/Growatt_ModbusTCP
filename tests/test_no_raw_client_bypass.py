"""Nothing may reach past the client wrapper to the raw pymodbus client (#426).

`GrowattModbus` wraps a pymodbus client and branches every read and write on whether a shared
connection hub is in charge. Reaching `self._client.client` skips that branch - and pymodbus
sync clients **auto-connect on their first transaction**, so such a call opens a second socket
to the gateway: one the hub never saw, never closed, and could not close, because the hub only
owns its own client.

That was the leak. `_read_device_identification()` runs after the first successful poll, so:

    setup            hub opens socket A
    first poll       succeeds
    identification   raw client auto-connects, opening socket B - the orphan
    reload           unload closes A; B has no owner and stays

A clean start therefore ended at two connections and every reload added one. On an Elfin EW11,
which accepts five clients, the slots ran out. Diagnosed by @KevlarD-67, who paired the local
ports from the debug log against `ss -tn` and named both sockets:

    hub     192.168.1.65:37172 -> 192.168.1.226:502
    orphan  192.168.1.65:47438 -> 192.168.1.226:502

This test is a grep with a reason attached. The failure it guards is invisible in every other
way: the reads succeed, the data is correct, and the only symptom is a socket count that nobody
watches until a gateway runs out of them.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

COMPONENT = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"

# Modules that hold a GrowattModbus and could reach through it.
MODULES = ["coordinator.py", "sensor.py", "number.py", "select.py", "diagnostic.py"]

# `x.client.client` or `self._client.client.<call>` - the wrapper's inner pymodbus object.
BYPASS = re.compile(r"\b\w*_?client\.client\.(read_|write_|connect|close)")


@pytest.mark.parametrize("module", MODULES)
def test_no_module_reaches_past_the_wrapper(module):
    """THE regression. Any transaction on the inner client opens a socket the hub cannot see."""
    path = COMPONENT / module
    if not path.exists():
        pytest.skip(f"{module} not present")

    offenders = [
        f"{module}:{number}  {line.strip()[:88]}"
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        if BYPASS.search(line)
    ]

    assert not offenders, (
        "these reach past the client wrapper to the raw pymodbus client, which skips the "
        "shared-connection branch and opens a socket nothing closes:\n  "
        + "\n  ".join(offenders)
    )


def test_the_coordinator_has_a_helper_to_use_instead():
    """Removing the bypass is only half of it - there has to be a supported way to read a
    holding register from the coordinator, or the next person reintroduces it."""
    source = (COMPONENT / "coordinator.py").read_text(encoding="utf-8")
    tree = ast.parse(source)

    helper = next(
        (node for node in ast.walk(tree)
         if isinstance(node, ast.FunctionDef) and node.name == "_read_holding"),
        None,
    )
    assert helper is not None, "the coordinator has no wrapper-respecting holding read"

    body = ast.unparse(helper)
    assert "self._client.read_holding_registers" in body, (
        "_read_holding does not go through the wrapper, so it has the same problem"
    )
    assert ".client.read_holding" not in body.replace("self._client.read_holding", ""), (
        "_read_holding reaches the inner client"
    )


def test_the_identification_reads_go_through_it():
    """The specific path that produced the orphan: it runs once, after the first successful
    poll, which is why the leak appeared 76 seconds into a session rather than at setup."""
    source = (COMPONENT / "coordinator.py").read_text(encoding="utf-8")
    fn = next(
        node for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.FunctionDef) and node.name == "_read_device_identification"
    )
    body = ast.unparse(fn)

    assert "_read_holding(" in body, "device identification no longer uses the safe helper"
    assert "client.client" not in body, "device identification reaches the raw client again"


def test_the_clock_read_goes_through_it_too():
    """It runs on every poll, so a bypass here would open an orphan per poll rather than per
    session - and it consumes the registers directly, which is where a half-finished
    conversion left a name that no longer existed.

    Note the function is `_check_inverter_clock`, which does the register read.
    `_refresh_inverter_clock` is a different method that only reads a cached value - naming
    the wrong one is how this test first passed against code it was not looking at.
    """
    source = (COMPONENT / "coordinator.py").read_text(encoding="utf-8")
    fn = next(
        node for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.FunctionDef) and node.name == "_check_inverter_clock"
    )
    body = ast.unparse(fn)

    assert "_read_holding(" in body
    assert "client.client" not in body

    # The conversion has to be complete, not just started: every name the function reads must
    # be one it assigns, a parameter, or an attribute. A leftover `result.registers` from the
    # old pymodbus shape parses fine and raises NameError only when that branch runs.
    assigned = {n.id for n in ast.walk(fn) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)}
    used = {n.id for n in ast.walk(fn) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
    assert "result" not in (used - assigned), (
        "_check_inverter_clock still reads `result`, which the wrapper no longer produces"
    )
