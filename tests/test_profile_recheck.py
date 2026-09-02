"""Re-checking the profile against the device type code (#405).

Detection runs once, in the config flow, and is never revisited. One failed read of
register 30000 at that moment strands an inverter on a lesser profile permanently, and
nothing tells the owner. A MOD 5000TL3-X owner spent weeks hunting a grid power register
by hand when his own DTC already named a profile that mapped it (#228).

These are source-level checks: the tests/ suite runs without Home Assistant, so the
coordinator cannot be imported. What they pin is the shape of the thing - and the two
properties that matter most are safety properties, not behaviour.
"""
import ast
import json
from pathlib import Path

COMPONENT = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"


def _method(name: str) -> str:
    source = (COMPONENT / "coordinator.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    fn = next(
        n for n in ast.walk(tree)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name
    )
    return ast.get_source_segment(source, fn)


def test_it_never_reads_vpp_registers_on_an_off_grid_profile():
    """THE safety property. auto_detection.py warns in capitals that reading 30000+ causes
    POWER RESETS on SPF inverters. A convenience check must not be able to switch somebody's
    inverter off, so off-grid profiles are excluded before any read happens."""
    body = _method("_recheck_profile_against_dtc")

    guard = body[:body.index("read_holding_registers")]
    assert "offgrid_protocol" in guard, (
        "the off-grid check does not happen before the register read - this can power-cycle "
        "an SPF inverter"
    )


def test_the_off_grid_guard_comes_before_the_read_in_the_source_order():
    """Belt and braces on the above: assert the ordering explicitly rather than relying on
    the slice."""
    body = _method("_recheck_profile_against_dtc")
    assert body.index("offgrid_protocol") < body.index("read_holding_registers")


def test_a_silent_register_is_not_treated_as_a_wrong_profile():
    """A failed read means "no information". Treating it as evidence would make every flaky
    gateway raise a false alarm - which is the same class of bug being fixed here."""
    body = _method("_recheck_profile_against_dtc")
    assert "if not regs" in body, "an empty read is not handled"
    # The 'done' flag must be set only after a successful read, so a later poll retries.
    before_done = body[:body.index("self._profile_recheck_done = True\n        dtc")]
    assert "if not regs" in before_done, (
        "the check is marked done before confirming the read succeeded, so one failed read "
        "would again decide things permanently"
    )


def test_it_does_not_switch_the_profile_itself():
    """Changing someone's register map unasked would alter their entities, and a false
    positive would do real damage. The repair issue offers the change; the user takes it."""
    body = _method("_recheck_profile_against_dtc")
    for forbidden in ("async_update_entry", "CONF_INVERTER_SERIES]", "hass.config_entries.async_"):
        assert forbidden not in body, f"the re-check appears to modify the config entry ({forbidden})"


def test_it_says_nothing_when_the_dtc_agrees():
    body = _method("_recheck_profile_against_dtc")
    assert "suggested == configured" in body, "no comparison against the configured profile"


def test_the_repair_issue_has_text_in_both_string_files():
    """has_entity_name aside, a repair issue with no translation renders as a bare key."""
    for filename in ("strings.json", "translations/en.json"):
        data = json.loads((COMPONENT / filename).read_text(encoding="utf-8"))
        issue = data["issues"]["profile_mismatch"]
        assert issue["title"], filename
        for placeholder in ("{dtc}", "{model}", "{suggested}", "{configured}"):
            assert placeholder in issue["description"], f"{filename} omits {placeholder}"


def test_it_runs_from_a_poll_that_succeeded():
    """Reading the DTC on a connection that is not working proves nothing, and both fetch
    paths have diverged before."""
    source = (COMPONENT / "coordinator.py").read_text(encoding="utf-8")
    assert source.count("_recheck_profile_against_dtc()") >= 2, (
        "the re-check is not called from both the shared and direct fetch paths"
    )
