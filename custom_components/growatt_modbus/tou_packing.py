"""Packed time-of-use period words: MOD TL3-XH / MID-XH / MIN TL-XH, holding 3038-3059.

Each period is two registers. The start word packs enable (bit 15), priority (bits 13-14:
0 Load, 1 Battery, 2 Grid) and the start time (hour in bits 8-12, minute in bits 0-7). The
end word holds the end time. A period's Start, End, Priority and Enable entities therefore
edit the same register, and each write is read-modify-write of the whole pair.

The Priority and Enable selects used to take "current" from the coordinator's last poll,
which is up to a scan interval old. Change a period's priority, then its enable before the
next poll, and the second write rebuilt the start word from the stale copy and put the old
priority back. A MID 25KTL3-XH owner setting several TOU values in a row found it hit and
miss (#475). The time entities already read the pair fresh; all three now share this.
"""
from __future__ import annotations

from typing import Any, Optional, Sequence

PRIORITY_MASK = 0x6000   # bits 13-14
ENABLE_MASK = 0x8000     # bit 15
FLAGS_MASK = 0xE000      # enable + priority


def with_priority(start: int, priority: int) -> int:
    """Start word with its priority replaced, time and enable kept."""
    return (int(start) & ~PRIORITY_MASK & 0xFFFF) | ((int(priority) & 0x3) << 13)


def with_enable(start: int, enabled: bool) -> int:
    """Start word with its enable bit replaced, time and priority kept."""
    return (int(start) & ~ENABLE_MASK & 0xFFFF) | (ENABLE_MASK if enabled else 0)


def with_time(start: int, hour: int, minute: int) -> int:
    """Start word with its time replaced, enable and priority kept."""
    return (int(start) & FLAGS_MASK) | ((int(hour) & 0x1F) << 8) | (int(minute) & 0xFF)


def current_pair(
    fresh: Optional[Sequence[int]], data: Any, start_field: str, end_field: str,
) -> tuple[int, int, bool]:
    """(start, end, is_fresh): the pair just read from the inverter, else the last poll's.

    The cached copy is only a fallback for a failed read - see the module docstring for
    what using it by default cost.
    """
    if fresh is not None and len(fresh) >= 2:
        return int(fresh[0]), int(fresh[1]), True
    if data is None:
        return 0, 0, False
    return int(getattr(data, start_field, 0) or 0), int(getattr(data, end_field, 0) or 0), False


def publish(data: Any, start_field: str, end_field: str, start: int, end: int) -> None:
    """Put a written pair into the coordinator's data so every entity of the period shows it
    now, rather than after the next poll - and so a cached fallback is never older than
    the last write."""
    if data is None:
        return
    setattr(data, start_field, int(start))
    setattr(data, end_field, int(end))
