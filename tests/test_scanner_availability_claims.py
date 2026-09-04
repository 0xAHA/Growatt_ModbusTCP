"""The scanner must not be advertised as usable before a device is added (#389).

`export_register_dump` is registered in `async_setup`, and `__init__.py` declares
`CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)`. Home Assistant only sets up a
config-entry-only integration once a config entry exists, so with no device added
`async_setup` never runs and the action is never registered.

Both the service description and the documentation promised the opposite:

- services.yaml: *"useful for scanning a new inverter before adding it to the integration"*
- diagnostic-service.md: *"test your connection **before** installing the integration"* and
  *"You don't need to configure the integration, just have the files installed... The
  diagnostic service will be available immediately!"*

The one audience the no-device mode existed for - somebody with an unsupported inverter
trying to produce a scan so support can be added - is exactly the audience that cannot
reach it. @gamer123 spent an evening on it before working out that `async_setup` was never
being called, which was a correct diagnosis of our own documentation being wrong.

Nothing enforces documentation, so this pins the claim rather than the prose.
"""
from __future__ import annotations

from pathlib import Path

import pytest

REPO = Path(__file__).parent.parent
SERVICES = REPO / "custom_components" / "growatt_modbus" / "services.yaml"
DOC = REPO / "docs" / "troubleshooting" / "diagnostic-service.md"
INIT = REPO / "custom_components" / "growatt_modbus" / "__init__.py"


def test_the_constraint_that_makes_this_necessary_still_holds():
    """Rule 4: if the integration stops being config-entry-only, or the services move out
    of async_setup, the claims below become true again and this file should be revisited
    rather than quietly enforcing an obsolete restriction."""
    source = INIT.read_text(encoding="utf-8")

    assert "config_entry_only_config_schema" in source, (
        "the integration is no longer config-entry-only - the scanner may now be reachable "
        "without a device, so re-read what this file is asserting"
    )
    assert "async_setup_services" in source, "service registration has moved"


def test_the_service_description_does_not_promise_pre_adoption_use():
    text = SERVICES.read_text(encoding="utf-8")

    assert "before adding it to the integration" not in text, (
        "services.yaml still advertises scanning before the integration has a device, "
        "which Home Assistant does not allow"
    )


def test_the_service_description_states_the_prerequisite():
    """Stating the constraint matters more than removing the false claim: somebody hunting
    a missing action needs to be told why it is missing."""
    text = SERVICES.read_text(encoding="utf-8").lower()

    assert "only exists once" in text or "does not load the integration" in text, (
        "services.yaml does not explain that a device must be added first"
    )


@pytest.mark.parametrize(
    "claim",
    [
        "test your connection **before** installing the integration",
        "The diagnostic service will be available immediately",
        "You don't need to *configure* the integration",
    ],
)
def test_the_docs_no_longer_make_the_unreachable_claim(claim):
    assert claim not in DOC.read_text(encoding="utf-8"), (
        f"diagnostic-service.md still claims: {claim!r}"
    )


def test_the_docs_give_a_route_for_an_unsupported_inverter():
    """Removing the false promise is not enough on its own - the people it misled still
    need a way to produce the scan that gets their model supported."""
    text = DOC.read_text(encoding="utf-8")

    assert "not supported yet" in text, (
        "the docs no longer explain how to scan an inverter that has no profile - which is "
        "the case the scanner matters most for"
    )
    assert "choose any profile manually" in text or "any profile chosen by hand" in text, (
        "the workaround does not tell the reader they can pick any profile to get through "
        "the config flow"
    )
