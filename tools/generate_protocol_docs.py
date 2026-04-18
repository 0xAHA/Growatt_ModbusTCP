#!/usr/bin/env python3
"""
Generate Growatt protocol reference documentation pages for MkDocs.

Outputs three markdown files:
  docs/developer/protocol-v139.md     — Modbus RTU Protocol II V1.39
  docs/developer/protocol-vpp.md      — VPP Protocol (V2.01/V2.03)
  docs/developer/protocol-offgrid.md  — Off-Grid Protocol V0.26

Source files:
  Protocols/Growatt_WIT-Modbus-RTU-Protocol-II-V1.39.xlsx
  Protocols/GI-BK-E060_GROWATT.VPP.COMMUNICATION.PROTOCOL.OF.INVERTER_V2.03.xlsx
  Protocols/OffGrid-Modbus-RS485-RS232-RTU-Protocol-V0-26.xlsx
  Protocols/growatt_vpp_protocol_v2.01_registers.csv
"""

import csv
import sys
from pathlib import Path

try:
    import openpyxl
except ImportError:
    sys.exit("ERROR: openpyxl not installed. Run: pip install openpyxl")

REPO_ROOT = Path(__file__).parent.parent
PROTOCOLS_DIR = REPO_ROOT / "Protocols"
DOCS_DIR = REPO_ROOT / "docs" / "developer"

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def clean(value):
    """Normalise a cell value to a stripped string, or empty string if None."""
    if value is None:
        return ""
    text = str(value).strip()
    return " ".join(text.split())


def escape_md(text: str) -> str:
    """Escape characters that break Markdown table cells."""
    return text.replace("|", "\\|").replace("\n", " ")


def md_row(*cells) -> str:
    return "| " + " | ".join(escape_md(str(c)) for c in cells) + " |"


# ---------------------------------------------------------------------------
# V1.39 — Modbus RTU Protocol II
# ---------------------------------------------------------------------------

V139_EXCEL = PROTOCOLS_DIR / "Growatt_WIT-Modbus-RTU-Protocol-II-V1.39.xlsx"

# Verified bounds (1-indexed rows)
V139_HOLDING_START = 37
V139_HOLDING_END   = 862
V139_INPUT_START   = 864
V139_INPUT_END     = 2004

COL_V139_ADDR   = 1   # int = register address; str = section marker
COL_V139_NAME   = 4
COL_V139_DESC   = 8
COL_V139_ACCESS = 20

SECTION_KEYWORDS = (
    "group", "use for", "for tl", "for wit", "for sph", "for spa",
    "note", "register table", "appendix", "bms", "apx", "reserved",
    "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth",
    "ninth", "tenth", "eleventh", "twelfth", "thirteenth",
)


def _is_v139_section_marker(value) -> bool:
    if not isinstance(value, str):
        return False
    vl = value.lower().strip()
    return any(k in vl for k in SECTION_KEYWORDS)


def _parse_v139_section(rows, start_row, end_row):
    """
    Yield dicts: {address, name, desc, access, section}.
    rows is a 0-indexed list matching 1-indexed spreadsheet rows.
    Section markers become the 'section' label for subsequent registers.
    """
    current_section = None
    current_reg = None

    def emit(reg):
        if reg:
            yield reg

    for sheet_row in range(start_row, end_row + 1):
        row = rows[sheet_row - 1]

        addr_val   = row[COL_V139_ADDR   - 1] if len(row) >= COL_V139_ADDR   else None
        name_val   = row[COL_V139_NAME   - 1] if len(row) >= COL_V139_NAME   else None
        desc_val   = row[COL_V139_DESC   - 1] if len(row) >= COL_V139_DESC   else None
        access_val = row[COL_V139_ACCESS - 1] if len(row) >= COL_V139_ACCESS else None

        if isinstance(addr_val, str) and _is_v139_section_marker(addr_val):
            if current_reg:
                yield current_reg
                current_reg = None
            current_section = clean(addr_val)
            continue

        if isinstance(addr_val, (int, float)) and 0 <= int(addr_val) <= 70000:
            if current_reg:
                yield current_reg
            addr_int = int(addr_val)
            current_reg = {
                "address": addr_int,
                "name": clean(name_val) or f"reg_{addr_int}",
                "desc": clean(desc_val) or "",
                "access": clean(access_val) or "",
                "section": current_section or "",
            }
        elif current_reg:
            # Continuation row — append to description
            for col_val in (desc_val, name_val):
                if col_val is not None:
                    extra = clean(col_val)
                    if extra:
                        current_reg["desc"] = (current_reg["desc"] + " " + extra).strip()
                        break

    if current_reg:
        yield current_reg


def _registers_to_md_table(registers, has_range=False):
    """Render a list of register dicts as a markdown table string."""
    lines = []
    if has_range:
        lines.append("| Address | Name | Description | Access | Range |")
        lines.append("| --- | --- | --- | --- | --- |")
    else:
        lines.append("| Address | Name | Description | Access |")
        lines.append("| --- | --- | --- | --- |")

    last_section = None
    for reg in registers:
        sec = reg.get("section", "")
        if sec and sec != last_section:
            # Section divider as italic row
            if has_range:
                lines.append(md_row(f"*{sec}*", "", "", "", ""))
            else:
                lines.append(md_row(f"*{sec}*", "", "", ""))
            last_section = sec

        if has_range:
            lines.append(md_row(
                reg["address"],
                reg["name"],
                reg["desc"],
                reg["access"],
                reg.get("range", ""),
            ))
        else:
            lines.append(md_row(
                reg["address"],
                reg["name"],
                reg["desc"],
                reg["access"],
            ))

    return "\n".join(lines)


def generate_v139():
    print(f"Loading {V139_EXCEL.name}...")
    wb = openpyxl.load_workbook(V139_EXCEL, data_only=True, read_only=True)
    ws = wb.worksheets[0]
    rows = list(ws.iter_rows(max_row=V139_INPUT_END + 5, values_only=True))
    wb.close()
    print(f"  {len(rows)} rows loaded")

    print("  Parsing holding registers...")
    holding = list(_parse_v139_section(rows, V139_HOLDING_START, V139_HOLDING_END))
    print(f"  {len(holding)} holding registers")

    print("  Parsing input registers...")
    inputs = list(_parse_v139_section(rows, V139_INPUT_START, V139_INPUT_END))
    print(f"  {len(inputs)} input registers")

    out = DOCS_DIR / "protocol-v139.md"

    content = f"""\
# Modbus RTU Protocol II V1.39

> **Source document:** Growatt WIT Modbus RTU Protocol II V1.39
> (`Growatt_WIT-Modbus-RTU-Protocol-II-V1.39.xlsx`)
>
> This is the definitive Protocol II document. V1.39 is a verified superset of
> V1.13, V1.20, and V1.24.
>
> **Applicable models:** WIT, WIS, SPH, SPA, MIN, MOD, MID, MAX, MAC

---

## Register Ranges by Model Family

| Family | Register Ranges |
| --- | --- |
| TL-X / TL-XH (MIN type) | 0–124, 3000–3124, 3125–3249, 3250–3374 |
| TL3-X (MAX / MID / MAC) | 0–124, 3000–3124, 3125–3249 |
| SPA / SPH (hybrid) | 0–124, 1000–1124, 2000–2124, 3000–3124, 3125–3249 |
| WIT TL3 | 0–124, 875–999, 3000–3124, 3125–3249, 8000–8139 |

---

## Holding Registers ({len(holding)} registers)

{_registers_to_md_table(holding)}

---

## Input Registers ({len(inputs)} registers)

{_registers_to_md_table(inputs)}
"""

    out.write_text(content, encoding="utf-8")
    print(f"  Written: {out}")


# ---------------------------------------------------------------------------
# VPP Protocol
# ---------------------------------------------------------------------------

VPP_CSV   = PROTOCOLS_DIR / "growatt_vpp_protocol_v2.01_registers.csv"
VPP_EXCEL = PROTOCOLS_DIR / "GI-BK-E060_GROWATT.VPP.COMMUNICATION.PROTOCOL.OF.INVERTER_V2.03.xlsx"


def _load_vpp_registers():
    """Load Hold and Input registers from the VPP V2.01 CSV."""
    holding = []
    inputs  = []
    with open(VPP_CSV, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rt = row["Register_Type"].strip()
            try:
                addr = int(row["Address"].strip())
            except (ValueError, KeyError):
                continue
            rec = {
                "address":  addr,
                "name":     clean(row.get("Parameter_Name", "")),
                "access":   clean(row.get("Read_Write", "")),
                "dtype":    clean(row.get("Data_Type", "")),
                "unit":     clean(row.get("Unit", "")),
                "count":    clean(row.get("Register_Count", "")),
                "range":    clean(row.get("Range_Notes", "")),
            }
            if rt == "Hold":
                holding.append(rec)
            elif rt == "Input":
                inputs.append(rec)
    return holding, inputs


def _load_vpp_dtc_codes():
    """Extract DTC codes from the VPP CSV reference table."""
    dtc_codes = []
    in_dtc = False
    with open(VPP_CSV, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rt = row["Register_Type"].strip()
            no = row["NO"].strip()
            if "TABLE 3-1" in rt.upper():
                in_dtc = True
                continue
            if in_dtc:
                if rt.startswith("TABLE 3-2") or rt.startswith("TABLE 3-3") or rt.startswith("TABLE 3-4"):
                    break
                if rt == "Model" or rt == "":
                    continue
                try:
                    dtc = int(no)
                    dtc_codes.append({"model": rt, "dtc": dtc})
                except ValueError:
                    pass
    return dtc_codes


def _vpp_registers_to_md_table(registers):
    lines = [
        "| Address | Parameter Name | R/W | Type | Unit | Count | Notes |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for reg in registers:
        lines.append(md_row(
            reg["address"],
            reg["name"],
            reg["access"],
            reg["dtype"],
            reg["unit"],
            reg["count"],
            reg["range"],
        ))
    return "\n".join(lines)


def generate_vpp():
    print(f"Loading VPP registers from {VPP_CSV.name}...")
    holding, inputs = _load_vpp_registers()
    print(f"  {len(holding)} holding, {len(inputs)} input registers")

    print("  Loading DTC codes...")
    dtc_codes = _load_vpp_dtc_codes()
    print(f"  {len(dtc_codes)} DTC codes")

    dtc_rows = "\n".join(
        f"| {d['dtc']} | {escape_md(d['model'])} |"
        for d in sorted(dtc_codes, key=lambda x: x["dtc"])
    )

    out = DOCS_DIR / "protocol-vpp.md"

    content = f"""\
# VPP Protocol

> **Source documents:** Growatt VPP Communication Protocol of Inverter V2.01 / V2.03
> (`GI-BK-E060_GROWATT.VPP.COMMUNICATION.PROTOCOL.OF.INVERTER_V2.03.xlsx`,
> `growatt_vpp_protocol_v2.01_registers.csv`)
>
> VPP (Virtual Power Plant) is Growatt's advanced monitoring and control protocol.
> It uses registers in the 30000+ range and is only supported by newer inverter models.
> Multiple protocol versions (V2.01, V2.02, V2.03) are in active use — all share the
> same core register layout described here.
>
> **Applicable models:** SPH, SPA, MIN TL-XH, MOD TL3-XH, MID TL3-XH, WIT, WIS, and others

---

## Register Ranges

| Range | Purpose |
| --- | --- |
| 30000–30099 | Device identification, rated parameters, system settings |
| 30100–30499 | Control registers (AC power, battery, TOU schedule) |
| 31000–31499 | Real-time data (status, PV, grid, battery, load) |
| 32000+ | Extended / model-specific |

---

## DTC Codes (Table 3-1)

The DTC (Device Type Code) is stored at holding register 30000 and uniquely identifies
the inverter model. The integration reads this at startup for automatic model detection.

| DTC Code | Model |
| --- | --- |
{dtc_rows}

---

## Holding Registers ({len(holding)} registers)

{_vpp_registers_to_md_table(holding)}

---

## Input Registers ({len(inputs)} registers)

{_vpp_registers_to_md_table(inputs)}
"""

    out.write_text(content, encoding="utf-8")
    print(f"  Written: {out}")


# ---------------------------------------------------------------------------
# Off-Grid Protocol V0.26
# ---------------------------------------------------------------------------

OFFGRID_EXCEL = PROTOCOLS_DIR / "OffGrid-Modbus-RS485-RS232-RTU-Protocol-V0-26.xlsx"

OFFGRID_HOLDING_START = 56
OFFGRID_HOLDING_END   = 436
OFFGRID_INPUT_START   = 438
OFFGRID_INPUT_END     = 1010

COL_OG_ADDR   = 1
COL_OG_NAME   = 7
COL_OG_DESC   = 21
COL_OG_ACCESS = 33
COL_OG_RANGE  = 37

OG_SECTION_KEYWORDS = (
    "group", "use for", "note", "register table", "bms", "battery",
    "ac output", "ac input", "solar", "utility", "second", "third",
    "fourth", "fifth", "sixth", "fault", "warning", "status",
    "set address", "reserved",
)


def _is_og_section_marker(value) -> bool:
    if not isinstance(value, str):
        return False
    vl = value.lower().strip()
    return any(k in vl for k in OG_SECTION_KEYWORDS)


def _parse_offgrid_section(rows, start_row, end_row):
    """Yield register dicts for one section of the Off-Grid Excel."""
    current_section = None
    current_reg = None

    for sheet_row in range(start_row, end_row + 1):
        row = rows[sheet_row - 1]

        addr_val   = row[COL_OG_ADDR   - 1] if len(row) >= COL_OG_ADDR   else None
        name_val   = row[COL_OG_NAME   - 1] if len(row) >= COL_OG_NAME   else None
        desc_val   = row[COL_OG_DESC   - 1] if len(row) >= COL_OG_DESC   else None
        access_val = row[COL_OG_ACCESS - 1] if len(row) >= COL_OG_ACCESS else None
        range_val  = row[COL_OG_RANGE  - 1] if len(row) >= COL_OG_RANGE  else None

        if isinstance(addr_val, str) and _is_og_section_marker(addr_val):
            if current_reg:
                yield current_reg
                current_reg = None
            current_section = clean(addr_val)
            continue

        if isinstance(addr_val, (int, float)) and 0 <= int(addr_val) <= 70000:
            if current_reg:
                yield current_reg
            addr_int = int(addr_val)
            current_reg = {
                "address": addr_int,
                "name":    clean(name_val) or f"reg_{addr_int}",
                "desc":    clean(desc_val) or "",
                "access":  clean(access_val) or "",
                "range":   clean(range_val) or "",
                "section": current_section or "",
            }
        elif current_reg:
            extra = clean(desc_val) or clean(name_val)
            if extra:
                current_reg["desc"] = (current_reg["desc"] + " " + extra).strip()
            if range_val and not current_reg.get("range"):
                current_reg["range"] = clean(range_val)

    if current_reg:
        yield current_reg


def generate_offgrid():
    print(f"Loading {OFFGRID_EXCEL.name}...")
    wb = openpyxl.load_workbook(OFFGRID_EXCEL, data_only=True, read_only=True)
    ws = wb.worksheets[0]
    rows = list(ws.iter_rows(max_row=OFFGRID_INPUT_END + 5, values_only=True))
    wb.close()
    print(f"  {len(rows)} rows loaded")

    print("  Parsing holding registers...")
    holding = list(_parse_offgrid_section(rows, OFFGRID_HOLDING_START, OFFGRID_HOLDING_END))
    print(f"  {len(holding)} holding registers")

    print("  Parsing input registers...")
    inputs = list(_parse_offgrid_section(rows, OFFGRID_INPUT_START, OFFGRID_INPUT_END))
    print(f"  {len(inputs)} input registers")

    out = DOCS_DIR / "protocol-offgrid.md"

    content = f"""\
# Off-Grid Protocol V0.26

> **Source document:** Growatt OffGrid Modbus RS485/RS232 RTU Protocol V0.26
> (`OffGrid-Modbus-RS485-RS232-RTU-Protocol-V0-26.xlsx`)
>
> This is the protocol used by Growatt's off-grid and AC-coupled inverter families.
> It covers registers 0–97 only; VPP registers are never used with these models.
>
> **Applicable models:**
> - **SPF 3000-6000 ES PLUS** — off-grid with battery, no grid export
> - **SPE 8000-12000 ES** — higher-capacity off-grid / AC-coupled storage

---

## Register Ranges

| Range | Purpose |
| --- | --- |
| 0–97 | All registers (holding and input share the same base range) |

---

## Holding Registers ({len(holding)} registers)

{_registers_to_md_table(holding, has_range=True)}

---

## Input Registers ({len(inputs)} registers)

{_registers_to_md_table(inputs, has_range=True)}
"""

    out.write_text(content, encoding="utf-8")
    print(f"  Written: {out}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    missing = [p for p in (V139_EXCEL, VPP_CSV, OFFGRID_EXCEL) if not p.exists()]
    if missing:
        for p in missing:
            print(f"ERROR: not found: {p}")
        sys.exit(1)

    print("\n=== Modbus RTU V1.39 ===")
    generate_v139()

    print("\n=== VPP Protocol ===")
    generate_vpp()

    print("\n=== Off-Grid V0.26 ===")
    generate_offgrid()

    print("\nDone. Three pages written to docs/developer/")


if __name__ == "__main__":
    main()
