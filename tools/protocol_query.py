#!/usr/bin/env python3
"""
Protocol Database Query Tool

Query the protocol database for register information, DTC codes, etc.

Usage:
    python protocol_query.py search <name>           - Search for register by name
    python protocol_query.py addr <address>          - Look up register by address
    python protocol_query.py dtc <model>             - Find DTC codes for model
    python protocol_query.py stats                   - Show database statistics
"""

import sqlite3
import sys
from pathlib import Path


class ProtocolDatabase:
    def __init__(self, db_path='docs/protocol_database.db'):
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            print(f"Error: Database not found at {self.db_path}")
            print("Run tools/import_vpp_protocol.py first!")
            sys.exit(1)
        self.db = sqlite3.connect(self.db_path)
        self.db.row_factory = sqlite3.Row

    def search_register(self, name_pattern):
        """Search for registers by name"""
        query = """
            SELECT p.name as protocol, r.register_type, r.address,
                   r.name, r.parameter_name, r.data_type, r.unit,
                   r.access, r.valid_range
            FROM registers r
            JOIN protocols p ON r.protocol_id = p.id
            WHERE r.name LIKE ? OR r.parameter_name LIKE ?
            ORDER BY r.address
        """
        pattern = f"%{name_pattern}%"
        return self.db.execute(query, (pattern, pattern)).fetchall()

    def lookup_address(self, address, reg_type=None):
        """Look up register by address"""
        query = """
            SELECT p.name as protocol, r.register_type, r.address,
                   r.name, r.parameter_name, r.data_type, r.unit,
                   r.access, r.register_count, r.valid_range
            FROM registers r
            JOIN protocols p ON r.protocol_id = p.id
            WHERE r.address = ?
        """
        if reg_type:
            query += " AND r.register_type = ?"
            return self.db.execute(query, (address, reg_type)).fetchall()
        return self.db.execute(query, (address,)).fetchall()

    def find_dtc(self, model_pattern):
        """Find DTC codes for model"""
        query = """
            SELECT dtc_code, inverter_type, full_name, model_series
            FROM dtc_codes
            WHERE full_name LIKE ? OR inverter_type LIKE ? OR model_series LIKE ?
            ORDER BY dtc_code
        """
        pattern = f"%{model_pattern}%"
        return self.db.execute(query, (pattern, pattern, pattern)).fetchall()

    def get_stats(self):
        """Get database statistics"""
        stats = {}

        # Protocols
        cursor = self.db.execute("SELECT COUNT(*) FROM protocols")
        stats['protocols'] = cursor.fetchone()[0]

        # Registers by type
        cursor = self.db.execute("""
            SELECT register_type, COUNT(*) as count
            FROM registers
            GROUP BY register_type
        """)
        stats['registers'] = dict(cursor.fetchall())

        # DTC codes
        cursor = self.db.execute("SELECT COUNT(*) FROM dtc_codes")
        stats['dtc_codes'] = cursor.fetchone()[0]

        # Address ranges
        cursor = self.db.execute("""
            SELECT register_type, MIN(address) as min_addr, MAX(address) as max_addr
            FROM registers
            GROUP BY register_type
        """)
        stats['address_ranges'] = dict((row[0], (row[1], row[2])) for row in cursor.fetchall())

        return stats

    def close(self):
        self.db.close()


def print_registers(registers):
    """Pretty print register results"""
    if not registers:
        print("No results found")
        return

    print(f"\nFound {len(registers)} register(s):\n")
    print(f"{'Protocol':<12} {'Type':<8} {'Addr':<7} {'Name':<30} {'Type':<10} {'Unit':<8} {'Access':<6} {'Range':<20}")
    print("-" * 120)

    for reg in registers:
        print(f"{reg['protocol']:<12} {reg['register_type']:<8} {reg['address']:<7} "
              f"{(reg['name'] or '')[:30]:<30} {(reg['data_type'] or ''):<10} "
              f"{(reg['unit'] or ''):<8} {(reg['access'] or ''):<6} {(reg['valid_range'] or '')[:20]:<20}")


def print_dtc_codes(codes):
    """Pretty print DTC code results"""
    if not codes:
        print("No DTC codes found")
        return

    print(f"\nFound {len(codes)} DTC code(s):\n")
    print(f"{'DTC Code':<10} {'Type':<15} {'Series':<10} {'Full Name':<60}")
    print("-" * 120)

    for code in codes:
        print(f"{code['dtc_code']:<10} {(code['inverter_type'] or ''):<15} "
              f"{(code['model_series'] or ''):<10} {(code['full_name'] or '')[:60]:<60}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    db = ProtocolDatabase()
    command = sys.argv[1].lower()

    try:
        if command == 'search':
            if len(sys.argv) < 3:
                print("Usage: protocol_query.py search <name_pattern>")
                sys.exit(1)
            pattern = sys.argv[2]
            results = db.search_register(pattern)
            print_registers(results)

        elif command == 'addr':
            if len(sys.argv) < 3:
                print("Usage: protocol_query.py addr <address> [holding|input]")
                sys.exit(1)
            address = int(sys.argv[2])
            reg_type = sys.argv[3] if len(sys.argv) > 3 else None
            results = db.lookup_address(address, reg_type)
            print_registers(results)

        elif command == 'dtc':
            if len(sys.argv) < 3:
                print("Usage: protocol_query.py dtc <model_pattern>")
                sys.exit(1)
            pattern = sys.argv[2]
            results = db.find_dtc(pattern)
            print_dtc_codes(results)

        elif command == 'stats':
            stats = db.get_stats()
            print("\nProtocol Database Statistics")
            print("=" * 60)
            print(f"Protocols: {stats['protocols']}")
            print(f"\nRegisters:")
            for reg_type, count in stats['registers'].items():
                addr_range = stats['address_ranges'].get(reg_type, (None, None))
                print(f"  {reg_type.capitalize()}: {count} registers (range: {addr_range[0]}-{addr_range[1]})")
            print(f"\nDTC Codes: {stats['dtc_codes']}")

        else:
            print(f"Unknown command: {command}")
            print(__doc__)
            sys.exit(1)

    finally:
        db.close()


if __name__ == '__main__':
    main()
