# Protocol Database Proposal

## Assessment of Restructured VPP 2.03 File

### File Structure ✅ EXCELLENT

The restructured `GI-BK-E060_GROWATT.VPP.COMMUNICATION.PROTOCOL.OF.INVERTER_V2.03.xlsx` now contains:

1. **HOLDING REGISTERS** sheet (140 rows × 59 cols)
2. **input registers** sheet (98 rows × 14 cols)
3. **TABLES** sheet (155 rows × 62 cols) - Reference data (DTC codes, fault codes, etc.)
4. **Table 1** sheet (618 rows × 63 cols) - Original full document for reference

### Data Quality Assessment

#### ✅ HOLDING REGISTERS Sheet

**Header Row:** Row 2
**Columns Identified:**
- Column 1: `N O.` - Sequential number
- Column 2: `Parameter name` - Register description
- Column 16: `Rea d/w rite` - Access mode (RO/RW/WO)
- Column 20: `Type` - Data type (UINT16, UINT32, INT16, INT32, STR, etc.)
- Column 27: `Unit` - Measurement unit (W, V, A, %, °C, etc.)
- Column 32: `Address` - Register address (e.g., 30000, 30001, etc.)
- Column 36: `Num ber` - Number of registers (1 for single, 2 for 32-bit, etc.)
- Column 41: `Range` - Valid range or reference to lookup table

**Sample Data:**
```
Row 4: NO=1, Name="Equipment type (DTC)", Access=RO, Type=UINT16, Unit=-, Address=30000, Number=1, Range="See Table 3-1"
Row 5: NO=2, Name="SN", Access=RO, Type=UINT16, Unit=-, Address=30001, Number=15, Range=-
Row 6: NO=3, Name="Rated power (Pn)", Access=RO, Type=UINT32, Unit=0.1W, Address=30016, Number=2, Range=-
```

**Assessment:** ✅ Clean, consistent structure. Ready for database import.

---

#### ✅ input registers Sheet

**Header Row:** Row 2
**Columns Identified:**
- Column 1: `N O.`
- Column 2: `Parameter name`
- Column 3: `Rea d/w rite`
- Column 4: `Type`
- Column 5: `Unit`
- Column 6: `Address`
- Column 7: `Num ber`
- Column 8: `Range`

**Sample Data:**
```
Row 4: NO=1, Name="Working state of inverter", Access=RO, Type=UINT16, Unit=1, Address=31000, Number=1, Range="0: standby, 1: self-test..."
```

**Assessment:** ✅ Clean, consistent structure. Column layout simpler than holding registers.

---

#### ✅ TABLES Sheet

**Content:** Reference tables for lookups
- **Table 3-1: DTC Codes** (Device Type Codes)
  - Column 2: Type (SPH/SPA, MIN-XH, MOD-XH, WIT/WIS, etc.)
  - Column 19: Full name (model descriptions)
  - Column 44: DTC code (numerical code)

**Sample DTC Data:**
```
SPH/SPA → "SPH 3000-6000TL BL" → DTC: 3501
MIN-XH → "MIN 2500-6000TL-XH/XH2/XHE/XA" → DTC: 5100
WIT/WIS → "WIT 50-100K-H/HE/HU..." → DTC: 5600
MIC/MIN-X → "MIC 600-3300TL-X/X2..." → DTC: 5200
```

- **Table 3-2:** Charging/discharging time interval parameters
- **Table 3-3:** Fault codes
- **Table 3-4:** Alarm codes

**Assessment:** ✅ Very usable for reference data. Can extract and normalize.

---

## ⚠️ Issues Identified

### 1. Column Header Wrapping
Some headers have line breaks (e.g., `"Rea d/w\nrite"` instead of `"Read/write"`). This is cosmetic but should be cleaned during import.

### 2. Inconsistent Column Positions
- HOLDING REGISTERS uses columns 1, 2, 16, 20, 27, 32, 36, 41 (sparse)
- input registers uses columns 1, 2, 3, 4, 5, 6, 7, 8 (dense)

This is fine - we can normalize during import.

### 3. Section Headers Mixed with Data
Some rows contain section headers (e.g., "Basic Parameter:30000~30099") rather than register data. We'll need to filter these during import.

---

## Recommended Database Structure

### Approach: SQLite Database + CSV Exports

**Why SQLite:**
- Single file, portable
- SQL queries for complex lookups
- Can export to CSV anytime
- Version controllable (can commit to git with caution)

**Why Also CSV:**
- Easy to edit in Excel
- Git-friendly (readable diffs)
- Can regenerate SQLite from CSV

---

## Proposed Schema

### Table: `protocols`
Metadata about each protocol version.

```sql
CREATE TABLE protocols (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,               -- "VPP_2.03", "SPF_0.26", "WIT_1.39"
    full_name TEXT,                   -- "VPP Communication Protocol V2.03"
    version TEXT,                     -- "2.03"
    source_file TEXT,                 -- Original Excel filename
    notes TEXT,
    created_date DATE,
    updated_date DATE
);
```

---

### Table: `registers`
All register definitions across all protocols.

```sql
CREATE TABLE registers (
    id INTEGER PRIMARY KEY,
    protocol_id INTEGER,              -- FK to protocols
    register_type TEXT,               -- "holding" or "input"
    address INTEGER NOT NULL,         -- Register address (30000, 31000, etc.)
    name TEXT NOT NULL,               -- "grid_voltage", "battery_power", etc.
    parameter_name TEXT,              -- Original name from spec
    description TEXT,                 -- Human-readable description
    data_type TEXT,                   -- "UINT16", "UINT32", "INT16", "INT32", "STR"
    unit TEXT,                        -- "V", "W", "A", "%", "°C", "-"
    scale REAL,                       -- Scale factor (0.1, 0.01, 1, etc.)
    access TEXT,                      -- "RO", "RW", "WO"
    register_count INTEGER,           -- Number of registers (1, 2, 15, etc.)
    valid_range TEXT,                 -- "(0, 100)" or "See Table 3-1"
    paired_with INTEGER,              -- For 32-bit: address of paired register
    signed BOOLEAN,                   -- TRUE if signed value
    notes TEXT,

    FOREIGN KEY (protocol_id) REFERENCES protocols(id),
    UNIQUE(protocol_id, register_type, address)
);
```

**Indexes:**
```sql
CREATE INDEX idx_registers_protocol ON registers(protocol_id);
CREATE INDEX idx_registers_address ON registers(address);
CREATE INDEX idx_registers_name ON registers(name);
```

---

### Table: `dtc_codes`
Device Type Codes for auto-detection.

```sql
CREATE TABLE dtc_codes (
    id INTEGER PRIMARY KEY,
    protocol_id INTEGER,              -- FK to protocols (which protocol defines this)
    dtc_code INTEGER NOT NULL,        -- DTC value (3501, 5100, etc.)
    inverter_type TEXT,               -- "SPH/SPA", "MIN-XH", "WIT/WIS"
    full_name TEXT,                   -- "SPH 3000-6000TL BL"
    model_series TEXT,                -- "SPH", "MIN", "WIT"
    profile_name TEXT,                -- Maps to our profile (e.g., "sph_3000_6000_tl_bl")
    notes TEXT,

    FOREIGN KEY (protocol_id) REFERENCES protocols(id),
    UNIQUE(dtc_code, protocol_id)
);
```

---

### Table: `fault_codes`
Fault and alarm code definitions.

```sql
CREATE TABLE fault_codes (
    id INTEGER PRIMARY KEY,
    protocol_id INTEGER,
    code_type TEXT,                   -- "fault" or "alarm"
    code_number INTEGER,              -- Numerical fault/alarm code
    description TEXT,                 -- Fault description
    severity TEXT,                    -- "critical", "warning", "info"
    notes TEXT,

    FOREIGN KEY (protocol_id) REFERENCES protocols(id)
);
```

---

### Table: `value_mappings`
Enumerated values for registers (e.g., status codes).

```sql
CREATE TABLE value_mappings (
    id INTEGER PRIMARY KEY,
    register_id INTEGER,              -- FK to registers
    value INTEGER,                    -- Numerical value
    label TEXT,                       -- String label
    description TEXT,

    FOREIGN KEY (register_id) REFERENCES registers(id)
);
```

**Example:**
```
register_id=123 (inverter_status), value=0, label="Standby"
register_id=123, value=1, label="No Use"
register_id=123, value=2, label="Discharge"
```

---

## Import Process

### Step 1: Python Import Script

```python
# tools/import_protocol_excel.py

import sqlite3
import openpyxl
from pathlib import Path
from datetime import datetime

def import_vpp_203():
    """Import VPP 2.03 protocol from restructured Excel"""

    wb = load_workbook('Protocols/GI-BK-E060_GROWATT.VPP.COMMUNICATION.PROTOCOL.OF.INVERTER_V2.03.xlsx')
    db = sqlite3.connect('docs/protocol_database.db')

    # Create protocol entry
    protocol_id = create_protocol(db, {
        'name': 'VPP_2.03',
        'full_name': 'VPP Communication Protocol V2.03',
        'version': '2.03',
        'source_file': 'GI-BK-E060_GROWATT.VPP.COMMUNICATION.PROTOCOL.OF.INVERTER_V2.03.xlsx'
    })

    # Import holding registers
    import_holding_registers(wb['HOLDING REGISTERS'], db, protocol_id)

    # Import input registers
    import_input_registers(wb['input registers'], db, protocol_id)

    # Import DTC codes
    import_dtc_codes(wb['TABLES'], db, protocol_id)

    db.commit()
    db.close()
```

---

### Step 2: Export to CSV for Git

```python
# tools/export_to_csv.py

def export_database_to_csv():
    """Export database tables to CSV for version control"""

    db = sqlite3.connect('docs/protocol_database.db')

    # Export each table
    tables = ['protocols', 'registers', 'dtc_codes', 'fault_codes', 'value_mappings']

    for table in tables:
        df = pd.read_sql(f"SELECT * FROM {table}", db)
        df.to_csv(f"docs/protocol_data/{table}.csv", index=False)

    db.close()
```

---

## Query Tool

```python
# tools/protocol_query.py

class ProtocolDatabase:
    def __init__(self, db_path='docs/protocol_database.db'):
        self.db = sqlite3.connect(db_path)

    def find_register_by_name(self, name, protocol=None):
        """Find register by name across protocols"""
        query = """
            SELECT p.name as protocol, r.register_type, r.address,
                   r.name, r.scale, r.unit, r.data_type
            FROM registers r
            JOIN protocols p ON r.protocol_id = p.id
            WHERE r.name LIKE ?
        """
        if protocol:
            query += " AND p.name = ?"
            return self.db.execute(query, (f"%{name}%", protocol)).fetchall()
        return self.db.execute(query, (f"%{name}%",)).fetchall()

    def compare_register_across_protocols(self, register_name):
        """Compare how a register differs across protocols"""
        results = self.find_register_by_name(register_name)
        return {
            row[0]: {  # protocol name
                'type': row[1],
                'address': row[2],
                'scale': row[4],
                'unit': row[5]
            }
            for row in results
        }

    def get_dtc_for_model(self, model_pattern):
        """Find DTC codes for model"""
        query = """
            SELECT dtc_code, inverter_type, full_name, profile_name
            FROM dtc_codes
            WHERE full_name LIKE ? OR inverter_type LIKE ?
        """
        return self.db.execute(query, (f"%{model_pattern}%", f"%{model_pattern}%")).fetchall()

    def validate_profile(self, profile_dict, protocol_name):
        """Validate profile against protocol spec"""
        issues = []

        # Get expected registers from database
        query = """
            SELECT address, name, scale, unit, data_type
            FROM registers r
            JOIN protocols p ON r.protocol_id = p.id
            WHERE p.name = ? AND r.register_type = 'input'
        """

        expected = {row[0]: row for row in self.db.execute(query, (protocol_name,))}

        # Check profile registers
        for addr, reg_def in profile_dict.get('input_registers', {}).items():
            if addr not in expected:
                issues.append(f"Register {addr} not in {protocol_name} spec")
            else:
                exp = expected[addr]
                if reg_def.get('scale') != exp[2]:
                    issues.append(f"Register {addr}: scale mismatch")

        return issues
```

---

## CLI Tool Examples

```bash
# Search for register
python tools/protocol_query.py search battery_voltage

Output:
VPP_2.03    input   31003   battery_voltage   0.1   V   UINT16
SPF_0.26    input   17      battery_voltage   0.1   V   UINT16
WIT_1.39    input   875     battery_voltage   0.1   V   UINT16

# Compare register across protocols
python tools/protocol_query.py compare battery_power

Output:
VPP_2.03:  Address=31004, Scale=0.1,  Signed=True
SPF_0.26:  Address=77,    Scale=-0.1, Signed=True  (INVERTED!)
WIT_1.39:  Address=876,   Scale=0.1,  Signed=True

# Find DTC codes
python tools/protocol_query.py dtc MIN

Output:
DTC 5100: MIN-XH → "MIN 2500-6000TL-XH/XH2/XHE/XA" → Profile: min_2500_6000tl_xh
DTC 5200: MIC/MIN-X → "MIC 600-3300TL-X/X2..." → Profile: min_2500_6000tl_x

# Validate profile
python tools/protocol_query.py validate profiles/min.py VPP_2.03

Output:
✓ All registers match specification
⚠ Register 3093: scale mismatch (expected 0.1, found 1.0)
```

---

## Next Steps

1. ✅ **VPP 2.03 structure verified** - Ready for import
2. **Import VPP 2.03 as proof of concept**
3. **Restructure other protocol files similarly** (SPF, WIT, etc.)
4. **Build import scripts**
5. **Create query/validation tools**
6. **Generate documentation from database**

---

## Benefits

### For Development
- ✅ Find conflicts between protocols instantly
- ✅ Validate new profiles against spec
- ✅ Auto-generate profile skeletons
- ✅ Cross-reference register names

### For Debugging
- ✅ Check if register exists in protocol
- ✅ Verify correct scale factors
- ✅ Look up DTC codes
- ✅ Compare expected vs. actual values

### For Documentation
- ✅ Auto-generate register tables
- ✅ Create protocol comparison matrices
- ✅ Build searchable docs site

---

## File Organization

```
Growatt_ModbusTCP/
├── docs/
│   ├── protocol_database.db          # SQLite database
│   ├── protocol_data/                # CSV exports (git-friendly)
│   │   ├── protocols.csv
│   │   ├── registers.csv
│   │   ├── dtc_codes.csv
│   │   ├── fault_codes.csv
│   │   └── value_mappings.csv
│   └── PROTOCOL_DATABASE_PROPOSAL.md # This document
├── Protocols/                        # Source Excel files
│   ├── GI-BK-E060_GROWATT.VPP.COMMUNICATION.PROTOCOL.OF.INVERTER_V2.03.xlsx
│   ├── OffGrid-Modbus-RS485-RS232-RTU-Protocol-V0-26.xlsx
│   └── ...
├── tools/
│   ├── import_protocol_excel.py      # Import scripts
│   ├── export_to_csv.py              # Export for git
│   ├── protocol_query.py             # Query tool
│   └── validate_profile.py           # Profile validator
```

---

## Conclusion

**The restructured VPP 2.03 file is EXCELLENT for database import!** ✅

The clean separation into sheets, consistent column structure, and inclusion of reference tables makes this a perfect foundation for the protocol database.

**Recommended Action:**
1. Proceed with VPP 2.03 import as proof of concept
2. Apply same restructuring to other protocol files
3. Build the database incrementally, one protocol at a time
