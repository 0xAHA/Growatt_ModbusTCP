"""An entry that has never once responded should suggest the Modbus unit ID (#424).

A wrong unit ID gives no clue that it is wrong. Every block read times out and surfaces as
`transport error during block read`, which reads as a link fault - so on #414 a WIT
configured for unit 2, on hardware that answered only on unit 1, was reported as a
connection that would not recover. It took two days and a standalone Modbus client. The
EMS COM address had been set to 2 in ShineTools and firmware 5050 ignored it.

The discrimination that makes this safe to say is *never succeeded since setup* versus
*succeeded and then stopped*. The second is an inverter asleep, powered down or briefly
unreachable - the overwhelmingly common case - and naming the unit ID there would send
people to check a setting that is demonstrably correct.

The method is extracted and run against a stub coordinator rather than asserted from its
source, because the whole value is in when it stays silent.
"""
from __future__ import annotations

import ast
import types
from pathlib import Path

import pytest

SOURCE = (Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
          / "coordinator.py").read_text(encoding="utf-8")


class _Recorder:
    """Stands in for homeassistant.helpers.issue_registry."""

    class IssueSeverity:
        WARNING = "warning"

    def __init__(self):
        self.created: list[dict] = []
        self.deleted: list[str] = []

    def async_create_issue(self, hass, domain, issue_id, **kwargs):
        self.created.append({"issue_id": issue_id, **kwargs})

    def async_delete_issue(self, hass, domain, issue_id):
        self.deleted.append(issue_id)


class _Logger:
    def __init__(self):
        self.warnings: list[str] = []

    def warning(self, msg, *args):
        self.warnings.append(msg % args if args else msg)

    def debug(self, *a, **k):
        pass


def _load_check(recorder, logger):
    fn = next(
        node for node in ast.walk(ast.parse(SOURCE))
        if isinstance(node, ast.FunctionDef) and node.name == "_check_never_responded"
    )
    namespace = {
        # The method carries @callback. Extracting a decorated function without it in scope
        # fails at exec, which is how a misplaced insertion that stole the decorator from
        # the function below it was caught.
        "callback": lambda fn: fn,
        "ir": recorder,
        "_LOGGER": logger,
        "DOMAIN": "growatt_modbus",
        "CONF_SLAVE_ID": "slave_id",
        "CONF_CONNECTION_TYPE": "connection_type",
        "CONF_DEVICE_PATH": "device_path",
        "CONF_HOST": "host",
        "CONF_PORT": "port",
    }
    exec(compile(ast.Module(body=[fn], type_ignores=[]), "<check>", "exec"), namespace)
    return namespace["_check_never_responded"]


class _Coordinator:
    def __init__(self, *, ever=False, failures=5, raised=False, data=None):
        self._ever_polled_successfully = ever
        self._consecutive_failures = failures
        self._failure_threshold = 5
        self._unit_id_issue_raised = raised
        self.hass = object()
        self.config_entry = types.SimpleNamespace(
            entry_id="abc123",
            data=data if data is not None else {
                "slave_id": 2, "connection_type": "tcp",
                "host": "192.168.1.50", "port": 503,
            },
        )


def _run(coordinator):
    recorder, logger = _Recorder(), _Logger()
    _load_check(recorder, logger)(coordinator)
    return recorder, logger


def test_it_fires_when_nothing_has_ever_responded():
    """THE case. Five attempts, no success since setup."""
    recorder, _ = _run(_Coordinator())

    assert len(recorder.created) == 1, "no repair issue was raised"
    assert recorder.created[0]["translation_key"] == "unit_id_never_responded"


def test_the_notice_names_the_configured_unit_id_and_target():
    """A notice that does not say which unit ID is in use leaves the reader to go and find
    it - which is most of the friction this exists to remove."""
    recorder, _ = _run(_Coordinator())
    placeholders = recorder.created[0]["translation_placeholders"]

    assert placeholders["slave_id"] == "2"
    assert placeholders["target"] == "192.168.1.50:503"


def test_a_working_entry_that_goes_offline_says_nothing():
    """THE guard, and the more important half. An inverter asleep at night is the common
    case by a wide margin; pointing at the unit ID there would send people to check a
    setting that has already been proven correct."""
    recorder, logger = _run(_Coordinator(ever=True, failures=500))

    assert recorder.created == [], (
        "the unit ID was blamed for an entry that had previously been reading successfully"
    )
    assert logger.warnings == []


def test_it_waits_for_the_failure_threshold():
    """One or two failures at startup are normal - a gateway still booting, an inverter
    mid-wake. Firing immediately would make this noise."""
    recorder, _ = _run(_Coordinator(failures=1))

    assert recorder.created == []


def test_it_raises_at_most_once():
    """The condition persists on every poll for as long as the entry is misconfigured. One
    repair issue is the point; a fresh one each minute is a different bug."""
    coordinator = _Coordinator()
    recorder, logger = _Recorder(), _Logger()
    check = _load_check(recorder, logger)
    for _ in range(10):
        check(coordinator)

    assert len(recorder.created) == 1, f"raised {len(recorder.created)} times"
    assert len(logger.warnings) == 1


def test_a_serial_entry_names_its_device_path():
    """A serial user shown 'None:None' would reasonably conclude the notice is broken."""
    recorder, _ = _run(_Coordinator(data={
        "slave_id": 3, "connection_type": "serial", "device_path": "/dev/ttyUSB0",
    }))

    assert recorder.created[0]["translation_placeholders"]["target"] == "/dev/ttyUSB0"


def test_the_first_success_withdraws_the_notice():
    """Asserted against the poll's success path: once any read works, the suggestion is
    wrong and must not be left standing in the user's repairs list."""
    assert "ir.async_delete_issue(" in SOURCE, (
        "nothing ever clears the unit ID repair issue"
    )
    assert 'f"unit_id_never_responded_{self.config_entry.entry_id}"' in SOURCE
    assert "self._ever_polled_successfully = True" in SOURCE, (
        "the success path never records that a read has worked, so the notice could fire "
        "later on an entry that has been polling fine"
    )


@pytest.mark.parametrize("path", ["strings.json", "translations/en.json"])
def test_the_notice_has_text_and_says_what_to_do(path):
    """A repair issue with no strings entry renders as its raw translation key."""
    import json

    component = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
    issues = json.loads((component / path).read_text(encoding="utf-8"))["issues"]

    assert "unit_id_never_responded" in issues, f"{path}: the repair notice has no text"
    body = issues["unit_id_never_responded"]["description"].lower()

    assert "{slave_id}" in body and "{target}" in body, (
        f"{path}: the description does not report the configured values"
    )
    assert "shinetools" in body, (
        f"{path}: the description does not warn that the address set in ShineTools may be "
        f"ignored, which is the trap that produced the report"
    )
    assert "configure" in body, (
        f"{path}: the description does not tell the user where to correct it"
    )
