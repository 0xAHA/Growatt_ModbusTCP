"""Gateway health thresholds for the repair issue (Issue #367).

Since v1.3.7 a frame that doesn't match the request is discarded rather than decoded, so
the *data* is safe. The reads are still lost though, and the only evidence is a log line.
One reporter's gateway was answering roughly one poll in three with a complete response to
an earlier request, and only found out because he reads logs. Nobody else would.

A repair issue puts that in front of the user, which means the thresholds have to be right
in both directions: silent when a gateway is merely having a moment, and loud when one is
genuinely misbehaving. A repair that cries wolf gets dismissed and then ignored when it
matters.

The logic is mirrored here rather than imported because the coordinator needs Home
Assistant. `tests_ha/` covers the wiring; this covers the arithmetic.
"""
from __future__ import annotations

import pytest

MIN_SAMPLE = 200
BAD_FRACTION = 0.05


def should_flag(good: int, bad: int) -> bool:
    """Mirror of GrowattModbusCoordinator._check_gateway_health thresholds."""
    total = bad + good
    if total < MIN_SAMPLE or not bad:
        return False
    return bad / total >= BAD_FRACTION


# ---------------------------------------------------------------------------
# Must stay quiet
# ---------------------------------------------------------------------------

def test_silent_on_a_perfect_gateway():
    assert should_flag(good=10_000, bad=0) is False


def test_silent_before_there_is_enough_data():
    """A gateway rebooting mid-poll can produce a burst of bad frames. Judging it on 20
    reads would flag hardware that is fine."""
    assert should_flag(good=0, bad=19) is False
    assert should_flag(good=10, bad=10) is False


def test_silent_on_an_occasional_glitch():
    """Under the 5% bar across a large sample — real, but not worth interrupting anyone."""
    assert should_flag(good=9_900, bad=100) is False


@pytest.mark.parametrize("bad", [1, 5, 9])
def test_silent_on_a_handful_of_bad_frames_in_a_long_run(bad):
    assert should_flag(good=5_000, bad=bad) is False


# ---------------------------------------------------------------------------
# Must speak up
# ---------------------------------------------------------------------------

def test_flags_the_reported_gateway():
    """The #367 case: roughly one poll in three answered with the wrong frame."""
    assert should_flag(good=200, bad=100) is True


def test_flags_at_exactly_the_threshold():
    assert should_flag(good=190, bad=10) is True     # 5.0% of 200


def test_does_not_flag_just_below_the_threshold():
    assert should_flag(good=1_902, bad=98) is False  # 4.9% of 2000


def test_flags_a_catastrophically_bad_gateway():
    assert should_flag(good=10, bad=490) is True


# ---------------------------------------------------------------------------
# Boundaries
# ---------------------------------------------------------------------------

def test_sample_size_is_counted_across_both_tallies():
    """199 reads is below the bar however they are split; 200 is not."""
    assert should_flag(good=100, bad=99) is False
    assert should_flag(good=100, bad=100) is True


def test_no_division_by_zero_on_a_fresh_connection():
    assert should_flag(good=0, bad=0) is False


# ---------------------------------------------------------------------------
# Repair issue strings
# ---------------------------------------------------------------------------
#
# A translation_key with no matching entry renders in the UI as the raw key. The repair
# still appears, so it looks like it works — it just says "gateway_malformed_frames" to
# the user instead of explaining anything.

import ast
import io
import json
import re
from pathlib import Path

COMPONENT = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"


def _translation_keys_used_in_code() -> set[str]:
    keys: set[str] = set()
    for name in ("coordinator.py", "__init__.py", "config_flow.py"):
        path = COMPONENT / name
        if path.exists():
            keys |= set(re.findall(
                r'translation_key\s*=\s*["\']([a-z0-9_]+)["\']',
                path.read_text(encoding="utf-8"),
            ))
    return keys


@pytest.mark.parametrize("filename", ["strings.json", "translations/en.json"])
def test_every_repair_translation_key_has_text(filename):
    data = json.load(io.open(COMPONENT / filename, encoding="utf-8"))
    defined = set(data.get("issues", {}))
    missing = _translation_keys_used_in_code() - defined
    assert not missing, (
        f"{filename} has no 'issues' entry for: {sorted(missing)} — the repair would "
        f"render as the raw key"
    )


@pytest.mark.parametrize("filename", ["strings.json", "translations/en.json"])
def test_repair_strings_have_title_and_description(filename):
    data = json.load(io.open(COMPONENT / filename, encoding="utf-8"))
    for key, body in data.get("issues", {}).items():
        assert body.get("title"), f"{filename}: issue '{key}' has no title"
        assert body.get("description"), f"{filename}: issue '{key}' has no description"


def _supplied_placeholders() -> dict[str, set[str]]:
    """Placeholder names each repair issue actually passes, read from the source.

    Keyed by translation_key, taken from the `translation_placeholders={...}` dict in the
    same `ir.async_create_issue(...)` call. Repairs are raised from more than one module,
    so every file that creates them has to be searched — an earlier version of this test
    looked only in coordinator.py and compared against a hard-coded list, which meant it
    verified nothing about a repair raised anywhere else.

    Parsed with `ast` rather than regex: the placeholder values are f-strings such as
    f"{hub.host}:{hub.port}", whose own braces terminate any non-greedy brace match and
    silently drop every key after the first.
    """
    supplied: dict[str, set[str]] = {}
    for filename in ("coordinator.py", "__init__.py"):
        tree = ast.parse((COMPONENT / filename).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not (isinstance(func, ast.Attribute) and func.attr == "async_create_issue"):
                continue
            kwargs = {kw.arg: kw.value for kw in node.keywords if kw.arg}
            key_node = kwargs.get("translation_key")
            if not isinstance(key_node, ast.Constant):
                continue
            names: set[str] = set()
            ph = kwargs.get("translation_placeholders")
            if isinstance(ph, ast.Dict):
                names = {
                    k.value for k in ph.keys
                    if isinstance(k, ast.Constant) and isinstance(k.value, str)
                }
            supplied.setdefault(key_node.value, set()).update(names)
    return supplied


def test_placeholders_used_in_strings_are_supplied_by_the_code():
    """A placeholder with no matching value raises at render time, so the repair never
    appears — the failure is invisible rather than ugly."""
    data = json.load(io.open(COMPONENT / "strings.json", encoding="utf-8"))
    supplied = _supplied_placeholders()

    for key, body in data.get("issues", {}).items():
        used = set(re.findall(r"\{([a-z_]+)\}", body["title"] + body["description"]))
        assert key in supplied, (
            f"issue '{key}' is defined in strings.json but no ir.async_create_issue() "
            f"call raises it — either it is dead, or it is raised from a module this "
            f"test does not search"
        )
        assert used == supplied[key], (
            f"issue '{key}' uses placeholders {sorted(used)}; "
            f"the code supplies {sorted(supplied[key])}"
        )
