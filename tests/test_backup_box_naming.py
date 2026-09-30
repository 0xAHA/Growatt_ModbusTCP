"""The backup box is not an ARK battery (#460).

The device for registers 3250-3342 was labelled "ARK Backup Box", and the code called it a
"Growatt ARK transfer switch". ARK is a Growatt battery line. The protocol names the unit a
"Backup box" (V1.39) and "SYN" (VPP 30115, "SYN enable - offline box enable"), and an owner
with APX batteries saw his transfer switch shown as someone else's battery.
"""
from pathlib import Path

COMPONENT = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"


def test_the_backup_box_device_carries_the_protocols_name():
    source = (COMPONENT / "coordinator.py").read_text(encoding="utf-8")
    assert '"model": "Backup Box (SYN)"' in source
    assert "ARK Backup Box" not in source


def test_nothing_calls_the_box_an_ark():
    for path in COMPONENT.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "ARK transfer switch" not in text, f"{path.name} calls the backup box an ARK"
