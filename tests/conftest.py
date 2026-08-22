"""Test configuration.

Home Assistant is not a test dependency, and it does not need to be: the protocol
layer is almost entirely HA-free already. `growatt_modbus.py` imports
`homeassistant.config_entries.ConfigEntry` at module scope but never uses it, and
`const.py` / `profiles/` import nothing outside the standard library.

Two pieces of setup make that layer directly testable:

1. A minimal `homeassistant` stub, purely to satisfy the dead import above. If that
   import is ever removed this stub becomes a no-op and can go with it.

2. A synthetic package rooted at the component directory. The modules use relative
   imports (`from .const import ...`), so they need a package context — but the real
   `__init__.py` pulls in the coordinator and the HA entity stack. Binding a bare
   package object to the component directory gives relative imports somewhere to
   resolve without executing the integration's setup code.
"""
from __future__ import annotations

import importlib
import importlib.util
import sys
import types
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
COMPONENT_DIR = REPO_ROOT / "custom_components" / "growatt_modbus"

PKG = "growatt_under_test"


def _stub_homeassistant() -> None:
    # Step aside when a real Home Assistant is installed. Checking importability rather
    # than "already imported" matters: pytest loads this conftest before anything touches
    # HA, so an unconditional stub would shadow the real package for the whole session
    # and break the tests_ha/ suite in confusing ways.
    if importlib.util.find_spec("homeassistant") is not None:
        return
    if "homeassistant" in sys.modules:
        return
    # A package, not a plain module: submodules are imported as `homeassistant.core`,
    # which only resolves if the parent declares a __path__.
    ha = types.ModuleType("homeassistant")
    ha.__path__ = []  # namespace-package marker

    config_entries = types.ModuleType("homeassistant.config_entries")

    class ConfigEntry:  # noqa: D401 - stand-in for an unused annotation
        """Placeholder; never exercised by these tests."""

    config_entries.ConfigEntry = ConfigEntry

    # auto_detection imports HomeAssistant for a type annotation only.
    core = types.ModuleType("homeassistant.core")

    class HomeAssistant:  # noqa: D401 - stand-in for an unused annotation
        """Placeholder; never exercised by these tests."""

    core.HomeAssistant = HomeAssistant

    # diagnostic.py imports these at module scope. Only the register-reading helpers in it
    # are exercised here — they take a client and plain ints — but the module has to import
    # before those can be reached.
    class ServiceCall:  # noqa: D401 - stand-in for an unused annotation
        """Placeholder; never exercised by these tests."""

    class SupportsResponse:  # noqa: D401 - stand-in for an unused annotation
        """Placeholder; never exercised by these tests."""

        ONLY = "only"
        OPTIONAL = "optional"

    core.ServiceCall = ServiceCall
    core.SupportsResponse = SupportsResponse

    helpers = types.ModuleType("homeassistant.helpers")
    helpers.__path__ = []
    device_registry = types.ModuleType("homeassistant.helpers.device_registry")
    config_validation = types.ModuleType("homeassistant.helpers.config_validation")
    # cv is only used to build voluptuous schemas at import time, and the set of validators
    # referenced grows whenever a service schema does. PEP 562 module __getattr__ hands back
    # a passthrough for any name rather than listing them and breaking on the next addition.
    config_validation.__getattr__ = lambda name: (lambda value: value)
    helpers.device_registry = device_registry
    helpers.config_validation = config_validation

    ha.config_entries = config_entries
    ha.core = core
    ha.helpers = helpers
    sys.modules["homeassistant"] = ha
    sys.modules["homeassistant.config_entries"] = config_entries
    sys.modules["homeassistant.core"] = core
    sys.modules["homeassistant.helpers"] = helpers
    sys.modules["homeassistant.helpers.device_registry"] = device_registry
    sys.modules["homeassistant.helpers.config_validation"] = config_validation


def _stub_voluptuous() -> None:
    """Minimal voluptuous, for the same reason as the HA stub above.

    Schemas in diagnostic.py are built at import time and never validated here, so every
    construct only has to be constructible.
    """
    if importlib.util.find_spec("voluptuous") is not None:
        return
    if "voluptuous" in sys.modules:
        return
    vol = types.ModuleType("voluptuous")

    class _Marker:
        def __init__(self, schema=None, *args, **kwargs):
            self.schema = schema

        def __call__(self, value):
            return value

        def __hash__(self):
            return hash(str(self.schema))

    for _name in ("Schema", "Required", "Optional", "All", "Any", "In", "Range",
                  "Coerce", "Length", "Invalid", "Exclusive", "Inclusive"):
        setattr(vol, _name, type(_name, (_Marker,), {}))
    sys.modules["voluptuous"] = vol


def _bind_component_package() -> None:
    """Expose the component directory as an importable package.

    Deliberately does NOT execute custom_components/growatt_modbus/__init__.py —
    that file wires up the HA integration. We only want the protocol modules.
    """
    if PKG in sys.modules:
        return
    pkg = types.ModuleType(PKG)
    pkg.__path__ = [str(COMPONENT_DIR)]
    sys.modules[PKG] = pkg


_stub_homeassistant()
_stub_voluptuous()
_bind_component_package()


def component(module: str):
    """Import a component module by name, e.g. component('growatt_modbus')."""
    return importlib.import_module(f"{PKG}.{module}")
