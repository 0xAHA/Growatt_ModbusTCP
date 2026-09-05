"""Setup must be completable when the inverter does not answer (#389).

A failed connection test used to be a dead end. The form re-rendered with the address
cleared and there was no route past it, which blocked two different people:

- somebody whose inverter is merely offline, or behind a wrong port, could not finish setup
  at all; and
- somebody with a model we do not support could not produce the register scan that would
  get it supported - because Home Assistant does not load a config-entry-only integration
  until an entry exists, so the scanner action is not registered either.

@gamer123 hit the second case on #389 and spent two evenings on it, including acting on
advice from me to "pick any profile manually" - which the flow never let him reach.

The escape is offered only *after* a failure. Showing it up front would invite skipping a
check that catches real mistakes: a typo, the wrong port, an unpowered adapter.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

COMPONENT = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
SOURCE = (COMPONENT / "config_flow.py").read_text(encoding="utf-8")


def _step_source(name: str) -> str:
    """Executable lines of one flow step, comments and docstring stripped."""
    fn = next(
        n for n in ast.walk(ast.parse(SOURCE))
        if isinstance(n, ast.AsyncFunctionDef) and n.name == name
    )
    body = fn.body
    if (
        body and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    ):
        body = body[1:]
    return "\n".join(ast.unparse(node) for node in body)


def test_the_escape_exists_and_skips_the_connection_test():
    """THE regression. Without this, a device that does not answer cannot be added, and the
    scanner that would diagnose it cannot be reached."""
    body = _step_source("async_step_tcp")

    assert "CONF_ADD_ANYWAY" in body, (
        "the TCP step has no way past a failed connection test"
    )
    escape = body.index("CONF_ADD_ANYWAY")
    test_call = body.index("client.connect")
    assert escape < test_call, (
        "the add-anyway branch runs after the connection test, so it cannot skip it"
    )


def test_it_goes_straight_to_manual_profile_selection():
    """Nothing was detected, so the user must choose. It is also the safest route: it reads
    no registers, and so cannot trip the SPF power-reset behaviour that the off-grid check
    exists to avoid."""
    body = _step_source("async_step_tcp")
    branch = body[body.index("CONF_ADD_ANYWAY"):]

    assert "async_step_manual" in branch, (
        "add-anyway does not lead to manual profile selection"
    )
    assert "async_step_offgrid_check" not in branch.split("async_step_manual")[0], (
        "add-anyway routes through the off-grid check, which reads registers from a device "
        "we already know is not answering"
    )


def test_the_option_is_not_offered_before_a_failure():
    """Offering it up front would invite skipping a check that catches typos and wrong
    ports - the cases where failing is the correct outcome."""
    body = _step_source("async_step_tcp")

    guarded = [
        line for line in body.splitlines()
        if "CONF_ADD_ANYWAY" in line and "fields[" in line
    ]
    assert guarded, "the add-anyway field is not added to the schema conditionally"
    assert "if errors:" in body, (
        "the add-anyway field is not gated on a prior failure"
    )


def test_what_was_typed_survives_a_failed_attempt():
    """The address field was cleared on every failure, so each retry meant retyping it.
    That is how a wrong port becomes an evening."""
    body = _step_source("async_step_tcp")

    assert "prior" in body and "prior.get" in body, (
        "the form no longer re-populates from the previous attempt"
    )


@pytest.mark.parametrize(
    "path", ["strings.json", "translations/en.json"]
)
def test_the_user_is_told_what_to_expect(path):
    """An entry that cannot reach its inverter produces entities that are all unavailable.
    Unless that is stated at the moment of choosing, it reads as a broken integration."""
    step = json.loads((COMPONENT / path).read_text(encoding="utf-8"))["config"]["step"]

    assert "add_anyway" in step["tcp"]["data"], f"{path}: the checkbox has no label"

    assert "manual" in step, f"{path}: the manual profile step has no description"
    description = step["manual"]["description"].lower()
    assert "unavailable" in description, (
        f"{path}: the profile step does not warn that entities will be unavailable"
    )
    assert "choose the profile yourself" in description, (
        f"{path}: the profile step does not say the user must pick"
    )
