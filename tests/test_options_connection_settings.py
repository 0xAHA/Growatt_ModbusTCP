"""Connection settings must be changeable after setup (#383).

Until now they could only be set during initial setup, so a USB port that moved after a
reboot — or a gateway that changed IP — could only be fixed by deleting the config entry and
adding it again. That loses entity IDs, and with them automations, dashboards and statistics
history. The reporter was re-passing USB devices through Proxmox to force the old path back
rather than face that.

The port list also has to offer /dev/serial/by-id/ paths. They are keyed on the adapter's
own vendor, product and serial number, so they survive a reboot; /dev/ttyUSBn is assigned in
plug order and swaps between devices when more than one adapter is present, which is the
reporter's actual fault condition.
"""
from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path

import pytest

CONFIG_FLOW = (Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
               / "config_flow.py")
SOURCE = CONFIG_FLOW.read_text(encoding="utf-8")


def _load_port_helper():
    """Import just the port-options helper.

    config_flow.py imports Home Assistant and voluptuous, which this suite does not have, so
    the function is compiled in isolation with only the two names it actually touches.
    """
    import ast

    tree = ast.parse(SOURCE)
    wanted = {"SERIAL_BY_ID_DIR", "SERIAL_BY_PATH_DIR", "MANUAL_PATH_SENTINEL",
              "_serial_port_options"}
    keep = [
        node for node in tree.body
        if (isinstance(node, ast.FunctionDef) and node.name in wanted)
        or (isinstance(node, ast.Assign)
            and any(getattr(t, "id", None) in wanted for t in node.targets))
    ]
    assert len(keep) == 4, f"expected 4 definitions, found {len(keep)}"

    module = types.ModuleType("_port_helper")
    fake_serial = types.ModuleType("serial")
    tools = types.ModuleType("serial.tools")
    list_ports = types.ModuleType("serial.tools.list_ports")
    list_ports.comports = lambda: []
    tools.list_ports = list_ports
    fake_serial.tools = tools
    module.__dict__["serial"] = fake_serial
    module.__dict__["_LOGGER"] = types.SimpleNamespace(debug=lambda *a, **k: None)

    exec(compile(ast.Module(body=keep, type_ignores=[]), "<helper>", "exec"), module.__dict__)
    return module


HELPER = _load_port_helper()


def test_the_configured_path_is_always_offered():
    """The load-bearing case. This form exists to be used *after* a path stopped working,
    so the device is usually absent when someone opens it. A vol.In whose default is not
    among its own options renders as an error instead of a form."""
    options = HELPER._serial_port_options("/dev/ttyUSB7")
    assert "/dev/ttyUSB7" in options
    assert "not detected" in options["/dev/ttyUSB7"]


def test_manual_entry_is_always_available():
    assert HELPER.MANUAL_PATH_SENTINEL in HELPER._serial_port_options(None)


def test_by_id_paths_are_listed_and_labelled(tmp_path, monkeypatch):
    """The durable answer to the reporter's problem, and it has to be visible as such —
    a user picking from a list has no way to know one path is stable and another is not."""
    by_id = tmp_path / "by-id"
    by_id.mkdir()
    (by_id / "usb-1a86_USB_Serial-if00-port0").write_text("")
    monkeypatch.setattr(HELPER, "SERIAL_BY_ID_DIR", str(by_id))

    options = HELPER._serial_port_options(None)
    path = f"{by_id}/usb-1a86_USB_Serial-if00-port0"
    assert path in options, "by-id paths are not offered"
    assert "stable" in options[path].lower(), "nothing tells the user which path survives a reboot"


def test_a_missing_by_id_directory_is_not_fatal():
    """Absent on Windows, and on Linux systems with no USB serial devices attached."""
    assert HELPER._serial_port_options("/dev/ttyUSB0")


def test_by_path_options_are_offered_alongside_by_id(tmp_path, monkeypatch):
    """by-id needs the adapter to carry a serial number, and CH340 chips - most cheap RS485
    adapters - do not have one. Two identical CH340s then produce by-id names that cannot
    distinguish them, so a user with two adapters can point both config entries at the same
    one without noticing (#384). by-path names the USB socket and cannot be ambiguous.

    Offering only by-id meant the correct choice for that hardware was not in the list at
    all, and the user had to know to type it by hand."""
    by_id = tmp_path / "by-id"
    by_path = tmp_path / "by-path"
    by_id.mkdir()
    by_path.mkdir()
    # Real by-path names contain colons (pci-0000:00:14.0-usb-0:5:1.0-port0), which cannot
    # be used in a filename on Windows, where this suite also runs. The name is irrelevant
    # to what is being asserted.
    by_path_name = "pci-0000_00_14.0-usb-0_5_1.0-port0"
    (by_id / "usb-1a86_USB2.0-Serial-if00-port0").write_text("")
    (by_path / by_path_name).write_text("")
    monkeypatch.setattr(HELPER, "SERIAL_BY_ID_DIR", str(by_id))
    monkeypatch.setattr(HELPER, "SERIAL_BY_PATH_DIR", str(by_path))

    options = HELPER._serial_port_options(None)

    id_path = f"{by_id}/usb-1a86_USB2.0-Serial-if00-port0"
    path_path = f"{by_path}/{by_path_name}"
    assert id_path in options, "by-id paths are no longer offered"
    assert path_path in options, "by-path paths are not offered"

    # The labels have to distinguish them, or the user cannot tell which one suits their
    # hardware - both being called 'stable' is what made this invisible.
    assert "adapter" in options[id_path].lower()
    assert "socket" in options[path_path].lower()


def test_a_missing_by_path_directory_is_not_fatal(tmp_path, monkeypatch):
    monkeypatch.setattr(HELPER, "SERIAL_BY_PATH_DIR", str(tmp_path / "nope"))
    assert HELPER._serial_port_options("/dev/ttyUSB0")


def test_serial_and_tcp_fields_are_both_wired_up():
    """Both were asked for. Serial alone would leave a TCP user whose gateway changed IP
    with the same delete-and-re-add cost."""
    for token in ("CONF_DEVICE_PATH,", "CONF_BAUDRATE,", "CONF_HOST,", "CONF_PORT,"):
        assert token in SOURCE, f"{token} is not part of the options schema"


def test_connection_changes_are_written_to_entry_data():
    """Connection settings live in entry.data, not options — that is where __init__ reads
    them. Writing them to options would save silently and change nothing."""
    assert "new_data[CONF_DEVICE_PATH] = selected_path" in SOURCE
    assert "new_data[CONF_HOST] = new_host" in SOURCE


def test_the_schema_is_split_by_connection_type():
    """A serial entry has no use for a host field, and showing both invites filling in the
    wrong one."""
    assert 'if current_connection_type == "serial":' in SOURCE


def test_an_empty_manual_path_is_rejected_not_saved():
    """Selecting 'enter manually' and typing nothing must not save an empty device path."""
    assert 'errors["base"] = "manual_path_required"' in SOURCE
    assert "if not errors:" in SOURCE, (
        "the save block is not guarded, so an invalid entry would persist a partial change"
    )


def test_setup_and_options_offer_the_same_ports():
    """First setup is the better moment to pick a stable path — nothing is built on the
    entity IDs yet. Offering by-id only on the reconfigure page meant a new user got the
    fragile name and discovered the durable one only after it bit them."""
    assert SOURCE.count("_serial_port_options") >= 3, (
        "the setup wizard and the options page do not share the port list, so one of them "
        "is missing the stable by-id paths"
    )
    assert "port_options[port.device] = desc" not in SOURCE, (
        "the setup wizard still builds its own port list from comports() alone"
    )


def test_port_enumeration_never_runs_on_the_event_loop():
    """Listing serial ports globs /dev and opens sysfs files. Home Assistant flags that as a
    blocking call and logs a traceback asking the user to file a bug (#384).

    The setup wizard always wrapped it in an executor. The options page was added later and
    called it directly - the same helper, one of two call sites converted, which is the
    failure shape CLAUDE.md rule 5 exists for.

    Asserted with ast rather than a string search: handing the function to
    async_add_executor_job leaves it a bare Name, so *any* Call node naming it is by
    definition a direct invocation on the loop.
    """
    import ast
    from pathlib import Path

    path = (Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
            / "config_flow.py")
    tree = ast.parse(path.read_text(encoding="utf-8"))

    direct = [
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_serial_port_options"
    ]
    assert not direct, (
        f"_serial_port_options is called directly at config_flow.py line(s) "
        f"{direct} - it must go through hass.async_add_executor_job"
    )
