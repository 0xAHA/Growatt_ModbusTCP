"""Optional VPP holding blocks must recover from a transient failure (#370).

30100 (control authority), 30200-30201 (export limit) and 30407-30410 (remote power
control) are read only when the profile defines them, and a failing anchor is recorded so
the block is skipped rather than retried every poll — the request goes unanswered and
accumulates transaction-ID mismatches.

Until #370 that record was a set with no expiry and no removal. One dropped frame latched
`vpp_control_authority_available = False` for the rest of the session. The reporter's WIT
sat with the control entity showing Disabled for six hours while Growatt's own cloud read
the register as Enabled throughout, and neither reloading the entry nor restarting Home
Assistant held for more than a single poll.

The identical defect on the input-register side was #340, fixed in #341 by retrying after
300 s. This set is a few hundred lines away in the same file and never got the same
treatment — which is the reason for these tests: the two mechanisms have to stay in step.

Parsed from source rather than executed: growatt_modbus.py needs pymodbus and a live
client to reach this code path.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

CLIENT = (Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
          / "growatt_modbus.py")
SOURCE = CLIENT.read_text(encoding="utf-8")

ANCHORS = (30100, 30200, 30407)


def test_the_record_is_time_based_not_a_bare_set():
    """A set can only answer "did this ever fail", which is not the question."""
    assert re.search(r"_failed_optional_holding_addrs:\s*dict", SOURCE), (
        "_failed_optional_holding_addrs is not a dict, so it cannot hold the failure "
        "time each anchor needs in order to be retried"
    )
    assert not re.search(r"_failed_optional_holding_addrs\.add\(", SOURCE), (
        "something still calls .add() on the failure record — that is the permanent-skip "
        "behaviour #370 removed"
    )


def test_a_retry_window_exists_and_matches_the_input_side():
    """300 s is what #341 chose for _failed_optional_ranges. Two different windows for
    the same idea is a difference someone will eventually have to explain."""
    holding = re.search(r"_VPP_HOLDING_RETRY_S\s*=\s*(\d+)", SOURCE)
    assert holding, "no retry window defined for the VPP holding blocks"
    ranges = re.search(r"_OPTIONAL_RANGE_RETRY_SECONDS\s*=\s*(\d+)", SOURCE)
    assert ranges, "the input-range retry constant has moved or been renamed"
    assert holding.group(1) == ranges.group(1), (
        f"VPP holding blocks retry after {holding.group(1)}s but optional input ranges "
        f"retry after {ranges.group(1)}s — same mechanism, different numbers"
    )


@pytest.mark.parametrize("anchor", ANCHORS)
def test_every_anchor_is_gated_by_the_retry_helper(anchor):
    """Each block guards itself. One left on a raw membership test keeps the old bug for
    that block only, which is harder to spot than all three being broken."""
    assert not re.search(rf"{anchor} not in self\._failed_optional_holding_addrs", SOURCE), (
        f"anchor {anchor} still uses a bare membership test instead of the retry helper"
    )
    assert re.search(rf"_vpp_block_skipped\({anchor}\)", SOURCE), (
        f"anchor {anchor} is not gated by _vpp_block_skipped()"
    )


@pytest.mark.parametrize("anchor", ANCHORS)
def test_a_successful_read_clears_the_record(anchor):
    """Otherwise the block re-reads every 300 s forever after one failure, and the
    'first failure only' log line never fires again."""
    assert re.search(rf"_failed_optional_holding_addrs\.pop\({anchor},", SOURCE), (
        f"a successful read of block {anchor} does not clear its failure record"
    )


def test_the_suppression_is_visible_in_diagnostics():
    """#370 was diagnosed by reading the source, because the diagnostics showed the
    consequence (`..._available: false`) and nothing about the cause."""
    diag = (CLIENT.parent / "diagnostics.py").read_text(encoding="utf-8")
    assert "_failed_optional_holding_addrs" in diag, (
        "the VPP holding suppression is not reported in diagnostics, so a user hitting "
        "it cannot show it to anyone"
    )
