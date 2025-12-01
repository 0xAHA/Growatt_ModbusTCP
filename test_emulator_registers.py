#!/usr/bin/env python3
"""
Test emulator register loading and serving
"""

import sys
sys.path.insert(0, '.')

from emulator.models import InverterModel, INVERTER_PROFILES, REGISTER_MAPS
from emulator.simulator import InverterSimulator

def test_model_loading():
    """Test loading a MIN model."""
    print("=" * 70)
    print("Testing Model Loading")
    print("=" * 70)

    model_key = 'min_3000_6000_tl_x'
    print(f"\nLoading model: {model_key}")

    try:
        model = InverterModel(model_key)
        print(f"✓ Model loaded: {model.name}")
        print(f"  Profile key: {model.profile_key}")
        print(f"  Register map key: {model.register_map_key}")
        print(f"  Has battery: {model.has_battery}")
        print(f"  Phases: {model.phases}")

        # Check registers
        input_regs = model.get_input_registers()
        holding_regs = model.get_holding_registers()

        print(f"\n  Input registers: {len(input_regs)}")
        print(f"  Holding registers: {len(holding_regs)}")

        # Show address range
        if input_regs:
            min_addr = min(input_regs.keys())
            max_addr = max(input_regs.keys())
            print(f"  Input register range: {min_addr} - {max_addr}")

            # Show first 5 registers
            print(f"\n  First 5 input registers:")
            for addr in sorted(list(input_regs.keys())[:5]):
                reg = input_regs[addr]
                print(f"    {addr}: {reg['name']}")

        return model

    except Exception as e:
        print(f"✗ Error loading model: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_simulator(model):
    """Test simulator with the model."""
    print("\n" + "=" * 70)
    print("Testing Simulator")
    print("=" * 70)

    try:
        print(f"\nCreating simulator for {model.name}...")
        sim = InverterSimulator(model, port=5020)
        print(f"✓ Simulator created")
        print(f"  Serial: {sim.serial_number}")

        # Force an update
        print(f"\nRunning simulator update...")
        sim.update()
        print(f"✓ Update completed")

        # Check values
        print(f"\n  Simulated values:")
        print(f"    PV Total: {sim.values['pv_power']['total']:.1f} W")
        print(f"    Grid Power: {sim.values['grid_power']['grid']:.1f} W")
        print(f"    House Load: {sim.house_load:.1f} W")
        print(f"    Inverter Temp: {sim.values['temperatures']['inverter']:.1f} °C")

        # Test register reads
        print(f"\n  Testing register reads:")

        test_regs = [
            (3000, 'input', 'inverter_status'),
            (3001, 'input', 'pv_total_power_high'),
            (3002, 'input', 'pv_total_power_low'),
            (3003, 'input', 'pv1_voltage'),
            (3004, 'input', 'pv1_current'),
        ]

        for addr, reg_type, expected_name in test_regs:
            value = sim.get_register_value(reg_type, addr)
            print(f"    Register {addr} ({expected_name}): {value}")

        return sim

    except Exception as e:
        print(f"✗ Error creating simulator: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_v201_model():
    """Test V2.01 model loading."""
    print("\n" + "=" * 70)
    print("Testing V2.01 Model")
    print("=" * 70)

    model_key = 'min_3000_6000_tl_x_v201'
    print(f"\nLoading V2.01 model: {model_key}")

    try:
        model = InverterModel(model_key)
        print(f"✓ Model loaded: {model.name}")
        print(f"  Register map key: {model.register_map_key}")

        input_regs = model.get_input_registers()
        print(f"\n  Input registers: {len(input_regs)}")

        if input_regs:
            min_addr = min(input_regs.keys())
            max_addr = max(input_regs.keys())
            print(f"  Address range: {min_addr} - {max_addr}")

            # Check for VPP registers (30000+)
            vpp_regs = [addr for addr in input_regs.keys() if addr >= 30000]
            legacy_regs = [addr for addr in input_regs.keys() if addr < 30000]

            print(f"\n  Legacy registers (< 30000): {len(legacy_regs)}")
            print(f"  VPP registers (>= 30000): {len(vpp_regs)}")

            if vpp_regs:
                print(f"\n  First 5 VPP registers:")
                for addr in sorted(vpp_regs[:5]):
                    reg = input_regs[addr]
                    print(f"    {addr}: {reg['name']}")

        return model

    except Exception as e:
        print(f"✗ Error loading V2.01 model: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == '__main__':
    print("\n🔧 Growatt Emulator Register Test\n")

    # Test legacy model
    model = test_model_loading()
    if model:
        sim = test_simulator(model)

    # Test V2.01 model
    v201_model = test_v201_model()

    print("\n" + "=" * 70)
    print("Test Complete")
    print("=" * 70)
