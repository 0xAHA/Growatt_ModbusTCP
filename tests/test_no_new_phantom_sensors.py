"""No profile may gain a sensor it cannot populate (#445).

An entity is created from the profile's **sensor set**. Whether anything can fill it is a
separate question and nothing checked that the two agree, so a sensor on the list with no
source publishes its dataclass default - `0.0` - for ever, indistinguishable from a real
reading of zero.

`device_profiles.py` documents the consequence at length for `dcdc_temp` (#362): added to a
shared group on the reasoning that it "only appears where a profile actually defines the
register", it put 0.0 C on twenty-six profiles. The lesson was applied to that sensor and
the general case was never swept. @takisbg reported four of them on SPF in #443.

**This is a ratchet, not a clean bill of health.** There are 450 such sensors today across
32 profiles. Removing an entity is user-visible - it vanishes from dashboards and its history
stops - so they come out in reviewed batches with release notes, not in one pass. What this
file does is stop the number growing while that happens.

## How the check works

Not by comparing names. That misses the `_high`/`_low` pair convention, `alias`, `maps_to`,
derived fields like the battery charge/discharge split, and code-level fallbacks such as
`ac_power` falling back to `load_power_low` - none of which a register map shows.

Instead it runs the **real decode**: every mapped register answers a distinctive non-zero
value, `read_all_data()` runs, and any sensor-set field still sitting at its dataclass
default is one that nothing wrote. Sensors whose `attr` is `calculated` are computed in the
entity rather than read, and are excluded.

Known imprecision, left in the baseline rather than special-cased: a poll writes either
`charge_power` or `discharge_power` depending on sign, never both, so one of that pair
always looks unpopulated. Anything removed from the baseline gets checked by hand anyway.
"""
from __future__ import annotations

import ast
import importlib
import json
from pathlib import Path

import pytest

_gm = importlib.import_module("growatt_under_test.growatt_modbus")
_const = importlib.import_module("growatt_under_test.const")
_dp = importlib.import_module("growatt_under_test.device_profiles")

COMPONENT = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
BASELINE_PATH = Path(__file__).parent / "phantom_sensor_baseline.json"

DEFAULTS = _gm.GrowattData()
PROBE = 7          # what every mapped register answers


def _sensor_attrs() -> dict[str, str]:
    """sensor key -> GrowattData attribute, parsed from SENSOR_DEFINITIONS.

    Read with `ast` rather than imported: `sensor.py` needs the Home Assistant entity stack,
    which this suite deliberately does without.
    """
    source = (COMPONENT / "sensor.py").read_text(encoding="utf-8")
    definitions = next(
        node.value
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "SENSOR_DEFINITIONS" for t in node.targets)
    )

    mapping: dict[str, str] = {}
    for key, value in zip(definitions.keys, definitions.values):
        if not isinstance(key, ast.Constant):
            continue
        attr = key.value
        if isinstance(value, ast.Dict):
            for inner_key, inner_value in zip(value.keys, value.values):
                if (isinstance(inner_key, ast.Constant) and inner_key.value == "attr"
                        and isinstance(inner_value, ast.Constant)):
                    attr = inner_value.value
        mapping[key.value] = attr
    return mapping


ATTRS = _sensor_attrs()


def _unpopulated(profile_key: str) -> list[str]:
    """Sensors this profile lists that a complete poll leaves at their default."""
    profile = _dp.INVERTER_PROFILES[profile_key]
    register_map = _const.REGISTER_MAPS[profile["register_map"]]

    client = _gm.GrowattModbus(connection_type="tcp", host="10.0.0.1", port=502,
                               register_map=profile["register_map"])
    client._shared_conn = None
    client.client = None

    mapped_input = set(register_map.get("input_registers", {}))
    mapped_holding = set(register_map.get("holding_registers", {}))

    client.read_input_registers = (
        lambda address, count, *a, **k:
        [PROBE if x in mapped_input else 0 for x in range(address, address + count)]
    )
    client.read_holding_registers = (
        lambda address, count, *a, **k:
        [PROBE if x in mapped_holding else 0 for x in range(address, address + count)]
    )

    data = client.read_all_data()
    if data is None:
        pytest.fail(f"{profile_key}: read_all_data() returned None on a fully answering poll")

    missing = []
    for sensor_key in sorted(profile["sensors"]):
        attr = ATTRS.get(sensor_key, sensor_key)
        if attr == "calculated":
            continue
        if not hasattr(data, attr):
            missing.append(sensor_key)      # dynamic attribute never set, e.g. the BMS block
        elif getattr(data, attr) == getattr(DEFAULTS, attr, None):
            missing.append(sensor_key)
    return missing


def _baseline() -> dict[str, list[str]]:
    return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))


def test_the_baseline_exists_and_is_not_empty():
    """If this file goes missing the ratchet silently stops holding."""
    baseline = _baseline()
    assert baseline, "the phantom-sensor baseline is empty"
    assert sum(len(v) for v in baseline.values()) > 100, (
        "the baseline has shrunk dramatically - if that is real, excellent, but check it is "
        "not the audit silently failing to find anything"
    )


@pytest.mark.parametrize("profile_key", sorted(_dp.INVERTER_PROFILES))
def test_no_profile_gains_an_unpopulatable_sensor(profile_key):
    """THE ratchet. A sensor added to a group its profile cannot fill fails here rather
    than shipping a confident zero to everyone on that profile."""
    expected = set(_baseline().get(profile_key, []))
    actual = set(_unpopulated(profile_key))

    added = actual - expected
    assert not added, (
        f"{profile_key} now lists {sorted(added)}, which a complete poll leaves at the "
        f"dataclass default - the entity would publish 0 for ever. Either map a register "
        f"for it, or leave it out of this profile's sensor set (#445)."
    )


@pytest.mark.parametrize("profile_key", sorted(_dp.INVERTER_PROFILES))
def test_the_baseline_is_kept_honest(profile_key):
    """The other direction: when a phantom is removed or given a register, the baseline has
    to be updated. Without this the file drifts into fiction and stops meaning anything."""
    expected = set(_baseline().get(profile_key, []))
    actual = set(_unpopulated(profile_key))

    fixed = expected - actual
    assert not fixed, (
        f"{profile_key}: {sorted(fixed)} no longer reads as unpopulated. That is progress - "
        f"remove those entries from tests/phantom_sensor_baseline.json."
    )
