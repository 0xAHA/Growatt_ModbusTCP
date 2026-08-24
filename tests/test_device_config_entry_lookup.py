"""Resolving a device to its config entry, across Home Assistant versions.

`DeviceEntry.config_entries` is a set of config entry ids. Core 2026.8 deprecates it in
favour of a single `config_entry_id` — a device now belongs to exactly one config entry —
with removal in Core 2027.8.

Reading the deprecated attribute on a new core writes a warning naming this integration
into the user's log. That is how another project's rename becomes bug reports here, so the
old attribute must not be touched at all when the new one is available.

Seven service handlers each carried their own byte-identical copy of this lookup. They now
share one helper — the same de-duplication the v1.3.5/v1.3.6 block-size bug argued for,
where a fix applied to one of two identical blocks left the other raising on every poll.
"""
from __future__ import annotations

import importlib

import pytest

_diag = importlib.import_module("growatt_under_test.diagnostic")


class _ModernDeviceEntry:
    """Core >= 2026.8: one config entry, exposed singly."""

    def __init__(self, entry_id):
        self.config_entry_id = entry_id

    @property
    def config_entries(self):  # pragma: no cover - must never be reached
        raise AssertionError(
            "the deprecated config_entries attribute was read on a modern core"
        )


class _LegacyDeviceEntry:
    """Core < 2026.8: a set, and no config_entry_id at all."""

    def __init__(self, *entry_ids):
        self.config_entries = set(entry_ids)


class _Hass:
    """Only what the helper touches: entry lookup returning runtime_data."""

    def __init__(self, loaded):
        self._loaded = loaded
        self.config_entries = self

    def async_get_entry(self, entry_id):
        if entry_id not in self._loaded:
            return None
        return type("Entry", (), {"runtime_data": self._loaded[entry_id]})()


def test_a_modern_core_uses_the_single_attribute():
    hass = _Hass({"abc": object()})
    assert _diag._config_entry_id_for_device(hass, _ModernDeviceEntry("abc")) == "abc"


def test_a_modern_core_never_touches_the_deprecated_attribute():
    """The point of the change. _ModernDeviceEntry raises if config_entries is read, so
    this fails loudly rather than silently emitting a deprecation warning in production."""
    hass = _Hass({"abc": object()})
    _diag._config_entry_id_for_device(hass, _ModernDeviceEntry("abc"))  # must not raise


def test_a_legacy_core_still_works():
    hass = _Hass({"abc": object()})
    assert _diag._config_entry_id_for_device(hass, _LegacyDeviceEntry("abc")) == "abc"


def test_an_unloaded_entry_is_not_returned():
    """A device can reference an entry that is disabled or not set up. Callers treat None
    as 'no config entry found' and raise a clear error; returning the id would have them
    resolve a coordinator that does not exist."""
    hass = _Hass({})
    assert _diag._config_entry_id_for_device(hass, _ModernDeviceEntry("abc")) is None
    assert _diag._config_entry_id_for_device(hass, _LegacyDeviceEntry("abc")) is None


def test_a_device_with_no_config_entry_is_handled():
    """config_entry_id can be None on a modern core for an orphaned device."""
    hass = _Hass({"abc": object()})
    assert _diag._config_entry_id_for_device(hass, _ModernDeviceEntry(None)) is None


def test_a_legacy_device_picks_the_entry_that_is_actually_ours():
    """Before the single-entry rule a device could span several integrations. Only one of
    them is a loaded Growatt entry, and that is the one to return."""
    ours = object()
    hass = _Hass({"growatt": ours})
    device = _LegacyDeviceEntry("somebody_else", "growatt")
    assert _diag._config_entry_id_for_device(hass, device) == "growatt"


def test_the_duplicated_lookup_blocks_are_gone():
    """Seven handlers had their own copy. Guards against a new service reintroducing one."""
    from pathlib import Path

    source = (Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
              / "diagnostic.py").read_text(encoding="utf-8")

    assert "for entry_id in device_entry.config_entries:" not in source, (
        "a service handler is reading DeviceEntry.config_entries directly again — it is "
        "deprecated in Core 2026.8 and removed in 2027.8"
    )
    # The compatibility branch inside the helper is the one permitted read.
    assert source.count("device_entry.config_entries") == 1
    # At least the seven handlers that existed when this was de-duplicated. Not an exact
    # count — a new service taking a device_id should use the helper too, and pinning the
    # number would fail on the addition rather than on a regression.
    assert source.count("_config_entry_id_for_device(hass, device_entry)") >= 7
