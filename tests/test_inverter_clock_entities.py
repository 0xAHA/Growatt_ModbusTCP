"""Guards for the Inverter Clock sensor and Inverter Clock Sync button (#393).

These are source-level checks. The tests/ suite runs without Home Assistant installed, so
importing the coordinator or the entity platforms is not possible here - see tests_ha/ for
anything that needs a real hass. What can still be pinned is the shape of the code, and
the two things most likely to break quietly are exactly that shape: a refresh added to one
fetch path but not the other, and a default that flips from disabled to enabled.
"""
import ast
import json
from pathlib import Path

import pytest

COMPONENT = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"


def _source(name: str) -> str:
    return (COMPONENT / name).read_text(encoding="utf-8")


def _function_body(source: str, class_name: str | None, func_name: str) -> str:
    """Return the source segment of a function, optionally inside a class."""
    tree = ast.parse(source)

    scope = tree
    if class_name is not None:
        scope = next(
            node for node in ast.walk(tree)
            if isinstance(node, ast.ClassDef) and node.name == class_name
        )

    func = next(
        node for node in ast.walk(scope)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == func_name
    )
    return ast.get_source_segment(source, func)


# ---------------------------------------------------------------------------
# The two fetch paths
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("fetch_path", ["_fetch_data_shared", "_fetch_data_direct"])
def test_both_fetch_paths_refresh_the_clock(fetch_path):
    """The coordinator has a shared-connection fetch path and a direct one, and they have
    diverged before: v1.3.5 fixed block-size parsing in the shared path only and the other
    raised on every poll. A clock refresh in one but not the other would leave half the
    users with a sensor frozen at its first reading."""
    body = _function_body(_source("coordinator.py"), "GrowattModbusCoordinator", fetch_path)
    assert "_refresh_inverter_clock()" in body, (
        f"{fetch_path} does not refresh the inverter clock"
    )


def test_the_direct_poll_still_runs_under_the_bus_lock():
    """_fetch_data delegates to _fetch_data_direct inside self._client._bus(), so the whole
    poll is atomic against writes rather than only its individual transactions. Holding it
    per transaction leaves the gap between blocks open, and a write landing there closes
    the port out from under the poll (#398)."""
    body = _function_body(_source("coordinator.py"), "GrowattModbusCoordinator", "_fetch_data")
    assert "_bus(" in body, "the direct poll no longer holds the bus for its whole duration"
    assert "_fetch_data_direct()" in body, "the direct poll body is no longer delegated"


def test_the_clock_is_not_read_until_something_asks():
    """The sensor is disabled by default. Reading the RTC anyway would spend an extra
    holding-register read every poll on every install, which is not free on a gateway that
    needs small blocks - the #360 machine already ran 216 reads against a 60 s interval."""
    body = _function_body(
        _source("coordinator.py"), "GrowattModbusCoordinator", "_refresh_inverter_clock"
    )
    tree = ast.parse(body.strip())
    func = tree.body[0]

    guard = next(
        (node for node in func.body if isinstance(node, ast.If)), None
    )
    assert guard is not None, "_refresh_inverter_clock has no early-exit guard"
    assert isinstance(guard.body[0], ast.Return), "the guard does not return early"
    assert "_clock_poll_wanted" in ast.get_source_segment(body, guard.test), (
        "the guard does not test whether clock polling was asked for"
    )


def test_the_sensor_turns_clock_polling_on_when_added():
    """Nothing else sets the flag, so without this the sensor would sit unavailable
    forever - available() gates on the clock being non-None."""
    body = _function_body(
        _source("sensor.py"), "GrowattInverterClockSensor", "async_added_to_hass"
    )
    assert "enable_clock_polling()" in body


# ---------------------------------------------------------------------------
# Entity defaults
# ---------------------------------------------------------------------------

CLOCK_ENTITIES = [
    ("sensor.py", "GrowattInverterClockSensor"),
    ("button.py", "GrowattSyncClockButton"),
]


@pytest.mark.parametrize("filename,class_name", CLOCK_ENTITIES)
def test_clock_entities_are_disabled_by_default(filename, class_name):
    """The sensor costs a read per poll and the button writes six EEPROM-backed holding
    registers per press (#392). Both are opt-in."""
    source = _source(filename)
    tree = ast.parse(source)
    cls = next(
        node for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef) and node.name == class_name
    )
    assigns = {
        target.id: ast.get_source_segment(source, node.value)
        for node in cls.body if isinstance(node, ast.Assign)
        for target in node.targets if isinstance(target, ast.Name)
    }
    assert assigns.get("_attr_entity_registry_enabled_default") == "False", (
        f"{class_name} is enabled by default"
    )


def test_clock_entities_share_an_entity_category():
    """They were asked for as a pair so they sit next to each other. Home Assistant groups
    a device page by entity category, so a sensor and a button only appear together if
    both carry the same one - drop it from either and they land in separate cards."""
    categories = {}
    for filename, class_name in CLOCK_ENTITIES:
        source = _source(filename)
        tree = ast.parse(source)
        cls = next(
            node for node in ast.walk(tree)
            if isinstance(node, ast.ClassDef) and node.name == class_name
        )
        categories[class_name] = {
            target.id: ast.get_source_segment(source, node.value)
            for node in cls.body if isinstance(node, ast.Assign)
            for target in node.targets if isinstance(target, ast.Name)
        }.get("_attr_entity_category")

    assert len(set(categories.values())) == 1, (
        f"the clock entities would appear in different sections: {categories}"
    )
    assert set(categories.values()) == {"EntityCategory.DIAGNOSTIC"}, categories


@pytest.mark.parametrize("filename", ["sensor.py", "button.py"])
def test_clock_entities_are_withheld_on_off_grid(filename):
    """Off-grid profiles store the year as an offset from 2000 and give register 51 to Chip
    Select rather than the weekday, so neither reading nor writing the standard layout is
    safe there. is_clock_supported is the one gate."""
    assert "is_clock_supported" in _source(filename), (
        f"{filename} creates a clock entity without checking profile support"
    )


# ---------------------------------------------------------------------------
# Wiring
# ---------------------------------------------------------------------------

def test_the_button_platform_is_registered():
    """A platform file that is not in PLATFORMS is never set up, and nothing warns."""
    assert "Platform.BUTTON" in _source("__init__.py")


def test_clock_entities_have_names_in_both_string_files():
    """has_entity_name with a translation_key and no matching entry gives an entity with
    no name at all rather than a fallback."""
    for filename in ("strings.json", "translations/en.json"):
        data = json.loads((COMPONENT / filename).read_text(encoding="utf-8"))
        assert data["entity"]["sensor"]["inverter_clock"]["name"] == "Inverter Clock", filename
        assert (
            data["entity"]["button"]["sync_inverter_clock"]["name"] == "Inverter Clock Sync"
        ), filename


def test_the_clock_sensor_is_not_a_timestamp_device_class():
    """Home Assistant renders a timestamp sensor as relative time - "12 seconds ago",
    ticking every second. For a clock that is unreadable, and it looks like a broken "last
    updated" field rather than the inverter's time; that is exactly how it was first
    reported. The state is the formatted wall-clock time instead, with the parseable form
    kept as the `timestamp` attribute."""
    source = _source("sensor.py")
    body = _function_body(source, "GrowattInverterClockSensor", "native_value")
    assert "strftime" in body, "the clock sensor no longer formats a readable time"

    tree = ast.parse(source)
    cls = next(
        node for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef) and node.name == "GrowattInverterClockSensor"
    )
    assigns = {
        target.id: ast.get_source_segment(source, node.value)
        for node in cls.body if isinstance(node, ast.Assign)
        for target in node.targets if isinstance(target, ast.Name)
    }
    assert "_attr_device_class" not in assigns, (
        "the clock sensor has a device class again; TIMESTAMP renders as relative time"
    )

    attrs = _function_body(source, "GrowattInverterClockSensor", "extra_state_attributes")
    assert "timestamp" in attrs, "the parseable timestamp attribute is gone"


def test_the_clock_sensor_is_excluded_from_the_sensor_key_set():
    """`created_keys` feeds the deferred-registration block, and it is built from the same
    list the clock sensor is appended to. Only GrowattModbusSensor carries `_sensor_key`,
    so an unguarded comprehension raises AttributeError there - which is what shipped in
    v1.8.6 and aborted sensor setup after the unconditioned entities had been added,
    silently removing every condition-gated sensor for every user (#399)."""
    source = _source("sensor.py")
    tree = ast.parse(source)

    setup = _function_body(source, None, "async_setup_entry")
    assert "created_keys" in setup, "created_keys moved; this guard needs rewriting"

    node = next(
        n for n in ast.walk(ast.parse(setup.strip()))
        if isinstance(n, ast.Assign)
        and any(getattr(t, "id", None) == "created_keys" for t in n.targets)
    )
    comp = node.value
    assert isinstance(comp, ast.SetComp), "created_keys is no longer a set comprehension"
    assert comp.generators[0].ifs, (
        "created_keys iterates every entity unguarded; the clock sensor has no "
        "_sensor_key and this raises AttributeError, aborting sensor setup"
    )
