"""The HOLD action must not promise an exact zero it does not deliver (#400).

The Set Battery Mode and Sync TOU Schedule descriptions called the +1% roster workaround
"true standby". Measured on hardware it is close to idle, not zero: a MOD 10KTL3-XH
(DTC 5400) under the integration's own HOLD sequence settled at about +140 W at night with
no PV (@KevlarD-67), and a MIN 4600TL-XH (DTC 5100) charged at roughly 270-310 W under the
same roster +1% with AC charge on (@GoncaloRibeiro11). services.yaml is what Home Assistant
shows in the action UI, so the claim reached users directly.
"""
from pathlib import Path

SERVICES = (Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
            / "services.yaml").read_text(encoding="utf-8")


def test_hold_is_not_described_as_true_standby():
    assert "true standby" not in SERVICES.lower(), (
        "services.yaml still calls HOLD 'true standby' - measured on MOD and MIN it is "
        "close to idle but not zero (#400)"
    )


def test_hold_description_says_it_is_not_an_exact_zero():
    assert "not an exact zero" in SERVICES, (
        "the HOLD wording no longer tells users it is not an exact zero"
    )
