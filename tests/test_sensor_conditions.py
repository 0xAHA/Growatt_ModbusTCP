"""Sensor conditions that can never fail (Issue #362).

Many sensors are gated with `condition: lambda data: hasattr(data, 'x')`, written as
"only create this sensor if the profile actually provides x". That works only when `x` is
set *dynamically* — the BMS attributes, for instance, are assigned with setattr() when
their register responds, so hasattr() is a genuine test.

It does **not** work when `x` is a field on the GrowattData dataclass. Those fields always
exist and carry a default, so hasattr() is always True and the gate is decorative. The
sensor is created whether or not any register populated it, and reports the default.

That is how MOD/MID users ended up with a Battery Temperature entity reading **0.0 °C**
after register 3176 was identified as the DC-DC converter stage and removed from the
profile. Not "unavailable" — zero. A dashboard shows a battery sitting at freezing rather
than a sensor that no longer exists, and on a cold morning that is a number someone might
act on.

The only hard filter is the profile's sensor set, so a sensor whose gate cannot fail must
be excluded there instead.

This test does not require every no-op gate to be fixed — most are harmless, because the
profiles that list them also define the register. It requires them to be *known*: adding a
new one, or removing a field from the dataclass, has to be a deliberate act.
"""
from __future__ import annotations

import ast
import importlib
import re
from pathlib import Path

import pytest

_dp = importlib.import_module("growatt_under_test.device_profiles")

COMPONENT_DIR = Path(_dp.__file__).parent


def _dataclass_fields() -> set[str]:
    """Field names declared on GrowattData."""
    tree = ast.parse((COMPONENT_DIR / "growatt_modbus.py").read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "GrowattData":
            return {
                stmt.target.id
                for stmt in node.body
                if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name)
            }
    raise AssertionError("GrowattData class not found")


def _sensors_with_hasattr_gates() -> dict[str, list[str]]:
    """Sensor key -> attribute names its hasattr() condition tests."""
    text = (COMPONENT_DIR / "sensor.py").read_text(encoding="utf-8")
    found: dict[str, list[str]] = {}
    for key, body in re.findall(r'\n    "([a-z0-9_]+)":\s*\{(.*?)\n    \},', text, re.S):
        cond = re.search(r'"condition":\s*(.*)', body)
        if not cond:
            continue
        attrs = re.findall(r"hasattr\(\s*data\s*,\s*'([a-z0-9_]+)'\s*\)", cond.group(1))
        if attrs:
            found[key] = attrs
    return found


# Sensors whose hasattr() gate names only dataclass fields, and so can never fail.
#
# Harmless where every profile listing the sensor also defines the register — the gate is
# simply redundant. Dangerous where it does not: the sensor is created anyway and reports
# the dataclass default, which for a numeric field is a plausible-looking 0.
#
# battery_temp is deliberately NOT here. It is excluded from the MOD/MID sensor sets via
# NO_BATTERY_TEMP instead, because on that hardware there is no battery temperature to
# read and a decorative gate let it publish 0.0 °C.
KNOWN_NOOP_GATES = {
    "grid_energy_today", "grid_energy_total",
    "grid_import_energy_today", "grid_import_energy_total",
    "dcdc_temp", "buck1_temp", "buck2_temp",
    "battery_current", "battery_temp",
    "battery_charge_power", "battery_discharge_power",
    "battery_charge_today", "battery_discharge_today",
    "battery_charge_total", "battery_discharge_total",
    "ac_charge_energy_today", "ac_charge_energy_total",
    "ac_discharge_energy_today", "ac_discharge_energy_total",
    "op_discharge_energy_today", "op_discharge_energy_total",
    "extra_power_to_grid", "extra_energy_today", "extra_energy_total",
    "load_percentage",
    # SPF off-grid. Only the SPF/SPE profiles list these, and those profiles define the
    # registers, so the redundant gate has never been reachable in a harmful way.
    "generator_power", "generator_voltage",
    "generator_discharge_today", "generator_discharge_total",
    "mppt_fan_speed", "inverter_fan_speed",
}


def test_no_new_decorative_hasattr_gates():
    """A gate that cannot fail must be a deliberate, listed choice.

    If this fails on a sensor you just added, its condition is not doing what it reads as
    doing. Either set the attribute dynamically so hasattr() means something, or exclude
    the sensor from the profiles that lack the register.
    """
    fields = _dataclass_fields()
    noop = {
        key for key, attrs in _sensors_with_hasattr_gates().items()
        if all(attr in fields for attr in attrs)
    }

    new = noop - KNOWN_NOOP_GATES
    assert not new, (
        "these sensors have a hasattr() condition that can never be False, because every "
        "attribute it names is a GrowattData field with a default:\n  "
        + "\n  ".join(sorted(new))
    )


def test_allowlist_does_not_rot():
    """Entries that stopped being no-ops should leave the list, so it reflects reality."""
    fields = _dataclass_fields()
    gates = _sensors_with_hasattr_gates()
    stale = {
        key for key in KNOWN_NOOP_GATES
        if key not in gates or not all(a in fields for a in gates[key])
    }
    assert not stale, (
        "allowlisted as decorative, but no longer are (gate removed, sensor removed, or "
        "attribute is now dynamic) — remove from KNOWN_NOOP_GATES:\n  "
        + "\n  ".join(sorted(stale))
    )


# ---------------------------------------------------------------------------
# The specific regression
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "profile_id",
    ["mod_6000_15000tl3_xh", "mod_6000_15000tl3_xh_v201", "mid_11000_30000tl3_xh_v201"],
)
def test_mod_mid_profiles_do_not_offer_battery_temperature(profile_id):
    """Register 3176 is the DC-DC converter stage, not the pack, and these systems expose
    no cell temperature at all. The sensor set is the only thing that can keep the entity
    from being created, since its condition cannot."""
    sensors = _dp.INVERTER_PROFILES[profile_id]["sensors"]
    assert "battery_temp" not in sensors
    assert "dcdc_temp" in sensors, "the DC-DC reading should still be exposed"


@pytest.mark.parametrize(
    "profile_id",
    ["mid_15000_25000tl3_x_v201", "sph_tl3_3000_10000_v201", "spa_3000_6000_tl_bl"],
)
def test_other_profiles_keep_battery_temperature(profile_id):
    """The exclusion must stay narrow — these profiles read a real battery temperature."""
    assert "battery_temp" in _dp.INVERTER_PROFILES[profile_id]["sensors"]
