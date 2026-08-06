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
import sys
import types
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
COMPONENT_DIR = REPO_ROOT / "custom_components" / "growatt_modbus"

PKG = "growatt_under_test"


def _stub_homeassistant() -> None:
    if "homeassistant" in sys.modules:
        return
    ha = types.ModuleType("homeassistant")
    config_entries = types.ModuleType("homeassistant.config_entries")

    class ConfigEntry:  # noqa: D401 - stand-in for an unused annotation
        """Placeholder; never exercised by these tests."""

    config_entries.ConfigEntry = ConfigEntry
    ha.config_entries = config_entries
    sys.modules["homeassistant"] = ha
    sys.modules["homeassistant.config_entries"] = config_entries


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
_bind_component_package()


def component(module: str):
    """Import a component module by name, e.g. component('growatt_modbus')."""
    return importlib.import_module(f"{PKG}.{module}")
