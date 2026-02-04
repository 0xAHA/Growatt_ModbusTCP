#!/usr/bin/env python3
"""
Protocol Overlap and Conflict Detection Tool

Demonstrates how the database schema handles multiple protocols and
identifies overlaps, conflicts, and inconsistencies.
"""

import sqlite3
from pathlib import Path


class ProtocolOverlapAnalyzer:
    def __init__(self, db_path='docs/protocol_database.db'):
        self.db = sqlite3.connect(db_path)
        self.db.row_factory = sqlite3.Row

    def find_same_address_different_meanings(self):
        """
        Find registers at same address but with different purposes across protocols.
        Example: Address 3 could be different things in VPP vs SPF.
        """
        query = """
            SELECT r.address, r.register_type,
                   GROUP_CONCAT(p.name || ': ' || r.parameter_name, ' | ') as meanings,
                   COUNT(DISTINCT r.parameter_name) as distinct_meanings
            FROM registers r
            JOIN protocols p ON r.protocol_id = p.id
            GROUP BY r.address, r.register_type
            HAVING COUNT(DISTINCT r.parameter_name) > 1
            ORDER BY r.address
        """
        return self.db.execute(query).fetchall()

    def find_same_register_different_scales(self):
        """
        Find registers with same name but different scale factors across protocols.
        Critical for finding bugs!
        """
        query = """
            SELECT r.name,
                   GROUP_CONCAT(p.name || ': ' || r.scale || r.unit, ' | ') as scale_info,
                   COUNT(DISTINCT r.scale) as distinct_scales
            FROM registers r
            JOIN protocols p ON r.protocol_id = p.id
            GROUP BY r.name
            HAVING COUNT(DISTINCT r.scale) > 1
            ORDER BY r.name
        """
        return self.db.execute(query).fetchall()

    def find_same_register_different_addresses(self):
        """
        Find registers with same logical purpose but at different addresses.
        Example: battery_voltage could be at reg 17 (SPF) vs 31214 (VPP)
        """
        query = """
            SELECT r.name,
                   GROUP_CONCAT(p.name || ': addr=' || r.address || ' (' || r.register_type || ')', ' | ') as locations,
                   COUNT(DISTINCT r.address) as distinct_addresses
            FROM registers r
            JOIN protocols p ON r.protocol_id = p.id
            GROUP BY r.name
            HAVING COUNT(DISTINCT r.address) > 1
            ORDER BY COUNT(DISTINCT r.address) DESC
        """
        return self.db.execute(query).fetchall()

    def get_protocol_coverage(self):
        """Show what's in each protocol"""
        query = """
            SELECT p.name, p.version,
                   COUNT(CASE WHEN r.register_type='holding' THEN 1 END) as holding_count,
                   COUNT(CASE WHEN r.register_type='input' THEN 1 END) as input_count,
                   MIN(r.address) as min_addr,
                   MAX(r.address) as max_addr
            FROM protocols p
            LEFT JOIN registers r ON p.id = r.protocol_id
            GROUP BY p.id
        """
        return self.db.execute(query).fetchall()

    def find_missing_in_profile(self, profile_registers, protocol_name='VPP_2.03'):
        """
        Compare a profile dict against protocol spec to find:
        - Registers in spec but not in profile (missing implementation)
        - Registers in profile but not in spec (potentially wrong)
        """
        query = """
            SELECT address, name, parameter_name, data_type, unit, scale, access
            FROM registers r
            JOIN protocols p ON r.protocol_id = p.id
            WHERE p.name = ? AND r.register_type = 'input'
        """

        spec_regs = {row['address']: dict(row) for row in self.db.execute(query, (protocol_name,))}
        profile_addrs = set(profile_registers.keys())
        spec_addrs = set(spec_regs.keys())

        missing = spec_addrs - profile_addrs  # In spec, not in profile
        extra = profile_addrs - spec_addrs    # In profile, not in spec

        return {
            'missing_from_profile': [spec_regs[addr] for addr in sorted(missing)],
            'extra_in_profile': sorted(extra),
            'in_both': len(spec_addrs & profile_addrs)
        }

    def close(self):
        self.db.close()


def main():
    """Demonstrate overlap detection"""

    analyzer = ProtocolOverlapAnalyzer()

    print("Protocol Database - Overlap and Conflict Analysis")
    print("=" * 100)

    # Coverage
    print("\n1. Protocol Coverage")
    print("-" * 100)
    coverage = analyzer.get_protocol_coverage()
    for row in coverage:
        print(f"{row['name']:15} v{row['version']:6} | "
              f"Holding: {row['holding_count']:3} | "
              f"Input: {row['input_count']:3} | "
              f"Range: {row['min_addr']}-{row['max_addr']}")

    # Same address, different meanings (IMPORTANT for multi-protocol support!)
    print("\n2. Same Address, Different Meanings Across Protocols")
    print("-" * 100)
    conflicts = analyzer.find_same_address_different_meanings()
    if conflicts:
        print(f"Found {len(conflicts)} address conflicts:\n")
        for row in conflicts[:10]:  # Show first 10
            print(f"Address {row['address']} ({row['register_type']}):")
            print(f"  {row['meanings'][:150]}")
            print()
    else:
        print("(None found yet - will appear when multiple protocols imported)")

    # Same name, different scales (BUG DETECTOR!)
    print("\n3. Same Register Name, Different Scale Factors")
    print("-" * 100)
    scale_diffs = analyzer.find_same_register_different_scales()
    if scale_diffs:
        print(f"Found {len(scale_diffs)} scale conflicts:\n")
        for row in scale_diffs[:10]:
            print(f"{row['name']:30} | {row['scale_info'][:100]}")
    else:
        print("(None found yet - single protocol imported)")

    # Same name, different addresses (PROTOCOL COMPARISON!)
    print("\n4. Same Register Name, Different Addresses")
    print("-" * 100)
    addr_diffs = analyzer.find_same_register_different_addresses()
    if addr_diffs:
        print(f"Found {len(addr_diffs)} registers at different addresses:\n")
        for row in addr_diffs[:10]:
            print(f"{row['name']:30} | {row['locations'][:100]}")
    else:
        print("(None found yet - single protocol imported)")

    # Example: Validate SPF profile against database
    print("\n5. Example: Profile Validation")
    print("-" * 100)
    print("Simulating SPF profile validation...")

    # Mock SPF registers (from actual SPF profile)
    spf_registers = {
        0: 'inverter_status',
        1: 'pv1_voltage',
        17: 'battery_voltage',
        18: 'battery_soc',
        20: 'grid_voltage',
        # etc.
    }

    # This would show which VPP registers are missing from SPF
    # (demonstrating cross-protocol comparison)
    print("  (Would compare SPF input registers 0-88 against VPP spec 31000-31229)")
    print("  (Shows which features are protocol-specific vs common)")

    analyzer.close()

    print("\n" + "=" * 100)
    print("SCHEMA BENEFITS:")
    print("  ✓ protocol_id foreign key enables multi-protocol storage")
    print("  ✓ UNIQUE(protocol_id, register_type, address) prevents duplicates within protocol")
    print("  ✓ Allows SAME address to have DIFFERENT meanings in different protocols")
    print("  ✓ Query by address across protocols to find conflicts")
    print("  ✓ Query by name across protocols to find implementation differences")
    print("  ✓ Perfect for detecting bugs like scale mismatches or inverted signs")


if __name__ == '__main__':
    main()
