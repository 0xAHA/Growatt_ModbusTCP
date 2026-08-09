#!/usr/bin/env python3
"""Report registers that the protocol documents but no profile maps.

Why this exists
---------------
`docs/developer/protocol-v139.md` is a ~105 KB extraction of the Growatt V1.39 protocol.
The profiles in `custom_components/growatt_modbus/profiles/` were mostly built from field
scans instead. Nobody had ever compared the two, so a register could be fully documented
and simply never asked for -- invisible, because nothing fails when a register is absent.

That is not hypothetical. The SPA extended range (2000-2124) sat extracted in the
reference for months while an SPA profile shipped with no AC current, no output power, no
inverter status, no AC energy and no temperature at all. It was noticed only when a user
photographed the same table out of the PDF and posted it to an issue -- and the first
response was to treat the photo as new information (#360).

Run this before concluding a value is unavailable on some model. "We never asked for it"
looks identical to "the hardware doesn't report it" from the outside.

Usage
-----
    python tools/protocol_coverage.py                 # every profile, summary
    python tools/protocol_coverage.py --profile SPA   # one family, full detail
    python tools/protocol_coverage.py --ranges        # per-range totals only

Limits, stated plainly
----------------------
This compares addresses, not meanings. It cannot tell you a mapping is *wrong*, only that
an address is documented and unmapped. A register listed as Reserved is skipped. Ranges a
model does not serve will show as gaps -- that is expected and not automatically a defect;
the SPA-TL3 case is exactly that, a profile correctly ignoring a documented range because
its hardware answers nothing there.
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REFERENCE = ROOT / "docs" / "developer" / "protocol-v139.md"

sys.path.insert(0, str(ROOT))
# tests/conftest.py binds the component directory as `growatt_under_test` WITHOUT running
# custom_components/growatt_modbus/__init__.py, which imports Home Assistant. Reusing it
# keeps one copy of that shim instead of a second that drifts.
sys.path.insert(0, str(ROOT / "tests"))
import conftest  # noqa: E402,F401

# Rows look like:  | 2039 | Iac1 | SPA R-phase grid output current | 0.1A | |
# Group headers look like:  | *Thirteenth group -- SPA storage (2000-2124)* | | | | |
ROW = re.compile(r"^\|\s*(\d+)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|")
GROUP = re.compile(r"^\|\s*\*([^*]+)\*\s*\|")
SECTION = re.compile(r"^#{1,3}\s+(.*)$")

SKIP_NAMES = {"reserved", "", "-", "--"}


def documented_registers(space: str) -> dict[int, dict]:
    """Numbered, non-reserved rows from one register space of the reference.

    The two spaces MUST be kept apart. They overlap at the same addresses and mean
    entirely different things -- 1083-1088 are Grid First time periods as holding
    registers and BMS status/SOC/voltage/current/temperature as input registers. An
    earlier version of this script ignored the boundary and duly reported every Bat
    First time slot as a "missing input register", which is worse than no report: it
    buries the real gaps in dozens of confident false ones.
    """
    if not REFERENCE.exists():
        sys.exit(f"protocol reference not found: {REFERENCE}")

    want = space.lower()
    out: dict[int, dict] = {}
    group = "(ungrouped)"
    current = None
    for line in REFERENCE.read_text(encoding="utf-8").splitlines():
        h = SECTION.match(line)
        if h:
            heading = h.group(1).lower()
            current = ("holding" if "holding" in heading
                       else "input" if "input" in heading else None)
            continue
        if current != want:
            continue
        g = GROUP.match(line)
        if g:
            group = g.group(1).strip()
            continue
        m = ROW.match(line)
        if not m:
            continue
        addr, name, desc, scale = (m.group(i).strip() for i in (1, 2, 3, 4))
        if name.lower() in SKIP_NAMES or desc.lower() in SKIP_NAMES:
            continue
        # First definition wins; the reference repeats some addresses across families.
        out.setdefault(int(addr), {"name": name, "desc": desc, "scale": scale,
                                   "group": group})
    return out


def mapped_registers(space: str) -> dict[str, set[int]]:
    """Addresses each profile asks for in one register space."""
    from growatt_under_test.profiles import REGISTER_MAPS

    field = "input_registers" if space == "input" else "holding_registers"
    return {
        key: set(prof.get(field, {}))
        for key, prof in REGISTER_MAPS.items()
    }


def profile_ranges(addrs: set[int]) -> list[tuple[int, int]]:
    """The 1000-blocks a profile touches, so gaps are judged against ranges it uses."""
    blocks = sorted({a // 1000 * 1000 for a in addrs})
    return [(b, b + 999) for b in blocks]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--profile", help="substring of a profile key, case-insensitive")
    ap.add_argument("--ranges", action="store_true", help="per-range totals only")
    ap.add_argument("--all-ranges", action="store_true",
                    help="include documented ranges the profile does not use at all")
    ap.add_argument("--space", choices=["input", "holding"], default="input",
                    help="register space to audit (default: input). The two are "
                         "separate address spaces and are never compared together.")
    args = ap.parse_args()

    doc = documented_registers(args.space)
    mapped = mapped_registers(args.space)
    fc = "FC04" if args.space == "input" else "FC03"
    print(f"Protocol reference: {len(doc)} documented {args.space} registers ({fc})\n")

    keys = sorted(mapped)
    if args.profile:
        needle = args.profile.lower()
        keys = [k for k in keys if needle in k.lower()]
        if not keys:
            sys.exit(f"no profile key matching {args.profile!r}")

    for key in keys:
        addrs = mapped[key]
        if not addrs:
            continue
        used = profile_ranges(addrs)

        gaps = {}
        for addr, info in doc.items():
            if addr in addrs:
                continue
            in_used_range = any(lo <= addr <= hi for lo, hi in used)
            if in_used_range or args.all_ranges:
                gaps[addr] = info

        covered = len(addrs & set(doc))
        print(f"{'=' * 76}\n{key}")
        print(f"  mapped {len(addrs)} registers, {covered} of them documented; "
              f"{len(gaps)} documented but unmapped"
              f"{' (within ranges it uses)' if not args.all_ranges else ''}")

        if not gaps:
            print("  no gaps\n")
            continue

        by_group = defaultdict(list)
        for addr, info in sorted(gaps.items()):
            by_group[info["group"]].append((addr, info))

        if args.ranges:
            for group, items in by_group.items():
                print(f"    {len(items):4}  {group}")
            print()
            continue

        for group, items in by_group.items():
            print(f"\n  -- {group} --")
            for addr, info in items:
                scale = f"  [{info['scale']}]" if info["scale"] not in ("-", "") else ""
                print(f"    {addr:>6}  {info['name'][:28]:28} {info['desc'][:44]}{scale}")
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
