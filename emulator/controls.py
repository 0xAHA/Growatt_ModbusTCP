"""
Control Handler for Inverter Emulator

Handles user input and adjusts simulation parameters.
"""

import sys
import tty
import termios
import threading
from typing import Callable, Optional


class ControlHandler:
    """Handles keyboard controls for the emulator."""

    def __init__(self, simulator, on_quit: Optional[Callable] = None):
        """Initialize control handler.

        Args:
            simulator: InverterSimulator instance
            on_quit: Callback function when user quits
        """
        self.simulator = simulator
        self.on_quit = on_quit
        self.running = False
        self.input_thread = None

    def start(self) -> None:
        """Start listening for keyboard input."""
        self.running = True
        self.input_thread = threading.Thread(target=self._input_loop, daemon=True)
        self.input_thread.start()

    def stop(self) -> None:
        """Stop listening for input."""
        self.running = False
        if self.input_thread:
            self.input_thread.join(timeout=1.0)

    def _input_loop(self) -> None:
        """Main input loop (runs in thread)."""
        # Save terminal settings
        old_settings = None
        try:
            old_settings = termios.tcgetattr(sys.stdin)
            tty.setcbreak(sys.stdin.fileno())

            while self.running:
                if sys.stdin in select.select([sys.stdin], [], [], 0.1)[0]:
                    char = sys.stdin.read(1).lower()
                    self._handle_key(char)

        except Exception as e:
            print(f"\nInput error: {e}")
        finally:
            # Restore terminal settings
            if old_settings:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

    def _handle_key(self, key: str) -> None:
        """Handle keyboard input.

        Args:
            key: Key character
        """
        if key == 'q':
            # Quit
            self.running = False
            if self.on_quit:
                self.on_quit()

        elif key == 'i':
            # Adjust irradiance
            self._prompt_irradiance()

        elif key == 'c':
            # Adjust cloud cover
            self._prompt_clouds()

        elif key == 'l':
            # Adjust house load
            self._prompt_load()

        elif key == 't':
            # Adjust time speed
            self._prompt_time_speed()

        elif key == 'b' and self.simulator.model.has_battery:
            # Adjust battery mode
            self._prompt_battery()

        elif key == 'r':
            # Reset daily totals
            self.simulator._reset_daily_totals()

    def _prompt_irradiance(self) -> None:
        """Prompt for irradiance value."""
        try:
            print("\n\n")
            print("=" * 50)
            print("Adjust Solar Irradiance")
            print("=" * 50)
            print(f"Current: {self.simulator.solar_irradiance:.0f} W/m²")
            print("Enter new value (0-1000 W/m²): ", end='', flush=True)

            value = float(input())
            self.simulator.set_irradiance(value)
            print(f"✓ Irradiance set to {self.simulator.solar_irradiance:.0f} W/m²")

        except (ValueError, EOFError, KeyboardInterrupt):
            print("✗ Invalid input")

    def _prompt_clouds(self) -> None:
        """Prompt for cloud cover."""
        try:
            print("\n\n")
            print("=" * 50)
            print("Adjust Cloud Cover")
            print("=" * 50)
            print(f"Current: {self.simulator.cloud_cover * 100:.0f}%")
            print("Enter new value (0-100%): ", end='', flush=True)

            value = float(input()) / 100.0
            self.simulator.set_cloud_cover(value)
            print(f"✓ Cloud cover set to {self.simulator.cloud_cover * 100:.0f}%")

        except (ValueError, EOFError, KeyboardInterrupt):
            print("✗ Invalid input")

    def _prompt_load(self) -> None:
        """Prompt for house load."""
        try:
            print("\n\n")
            print("=" * 50)
            print("Adjust House Load")
            print("=" * 50)
            print(f"Current: {self.simulator.house_load:.0f}W")
            print("Enter new value (W): ", end='', flush=True)

            value = float(input())
            self.simulator.set_house_load(value)
            print(f"✓ House load set to {self.simulator.house_load:.0f}W")

        except (ValueError, EOFError, KeyboardInterrupt):
            print("✗ Invalid input")

    def _prompt_time_speed(self) -> None:
        """Prompt for time multiplier."""
        try:
            print("\n\n")
            print("=" * 50)
            print("Adjust Time Speed")
            print("=" * 50)
            print(f"Current: {self.simulator.time_multiplier}x")
            print("Enter new multiplier (0.1-100): ", end='', flush=True)

            value = float(input())
            self.simulator.set_time_multiplier(value)
            print(f"✓ Time speed set to {self.simulator.time_multiplier}x")

        except (ValueError, EOFError, KeyboardInterrupt):
            print("✗ Invalid input")

    def _prompt_battery(self) -> None:
        """Prompt for battery control."""
        try:
            print("\n\n")
            print("=" * 50)
            print("Battery Control")
            print("=" * 50)
            print("1. Auto (charge from PV, discharge to load)")
            print("2. Manual charge rate")
            print("3. Manual discharge rate")
            print("4. Force idle")
            print("Enter choice (1-4): ", end='', flush=True)

            choice = input().strip()

            if choice == '1':
                self.simulator.set_battery_override(None)
                print("✓ Battery set to AUTO mode")

            elif choice == '2':
                print("Enter charge power (W): ", end='', flush=True)
                power = float(input())
                self.simulator.set_battery_override(abs(power))
                print(f"✓ Battery charging at {abs(power):.0f}W")

            elif choice == '3':
                print("Enter discharge power (W): ", end='', flush=True)
                power = float(input())
                self.simulator.set_battery_override(-abs(power))
                print(f"✓ Battery discharging at {abs(power):.0f}W")

            elif choice == '4':
                self.simulator.set_battery_override(0)
                print("✓ Battery set to IDLE")

        except (ValueError, EOFError, KeyboardInterrupt):
            print("✗ Invalid input")


# For systems without select module (Windows compatibility)
try:
    import select
except ImportError:
    # Fallback for Windows - use simpler polling
    import msvcrt

    class ControlHandler:
        """Windows-compatible control handler."""

        def __init__(self, simulator, on_quit: Optional[Callable] = None):
            self.simulator = simulator
            self.on_quit = on_quit
            self.running = False
            self.input_thread = None

        def start(self) -> None:
            self.running = True
            self.input_thread = threading.Thread(target=self._input_loop, daemon=True)
            self.input_thread.start()

        def stop(self) -> None:
            self.running = False

        def _input_loop(self) -> None:
            """Windows input loop."""
            import time

            while self.running:
                if msvcrt.kbhit():
                    char = msvcrt.getch().decode('utf-8', errors='ignore').lower()
                    self._handle_key(char)
                time.sleep(0.1)

        def _handle_key(self, key: str) -> None:
            """Handle keyboard input."""
            if key == 'q':
                self.running = False
                if self.on_quit:
                    self.on_quit()
            elif key == 'i':
                self._prompt_irradiance()
            elif key == 'c':
                self._prompt_clouds()
            elif key == 'l':
                self._prompt_load()
            elif key == 't':
                self._prompt_time_speed()
            elif key == 'b' and self.simulator.model.has_battery:
                self._prompt_battery()
            elif key == 'r':
                self.simulator._reset_daily_totals()

        def _prompt_irradiance(self) -> None:
            try:
                print("\n\nEnter irradiance (0-1000 W/m²): ", end='', flush=True)
                value = float(input())
                self.simulator.set_irradiance(value)
                print(f"✓ Set to {self.simulator.solar_irradiance:.0f} W/m²")
            except:
                print("✗ Invalid input")

        def _prompt_clouds(self) -> None:
            try:
                print("\n\nEnter cloud cover (0-100%): ", end='', flush=True)
                value = float(input()) / 100.0
                self.simulator.set_cloud_cover(value)
                print(f"✓ Set to {self.simulator.cloud_cover * 100:.0f}%")
            except:
                print("✗ Invalid input")

        def _prompt_load(self) -> None:
            try:
                print("\n\nEnter house load (W): ", end='', flush=True)
                value = float(input())
                self.simulator.set_house_load(value)
                print(f"✓ Set to {self.simulator.house_load:.0f}W")
            except:
                print("✗ Invalid input")

        def _prompt_time_speed(self) -> None:
            try:
                print("\n\nEnter time multiplier (0.1-100): ", end='', flush=True)
                value = float(input())
                self.simulator.set_time_multiplier(value)
                print(f"✓ Set to {self.simulator.time_multiplier}x")
            except:
                print("✗ Invalid input")

        def _prompt_battery(self) -> None:
            try:
                print("\n\nBattery: 1=Auto 2=Charge 3=Discharge 4=Idle: ", end='', flush=True)
                choice = input().strip()
                if choice == '1':
                    self.simulator.set_battery_override(None)
                    print("✓ AUTO mode")
                elif choice == '2':
                    print("Charge power (W): ", end='', flush=True)
                    power = float(input())
                    self.simulator.set_battery_override(abs(power))
                    print(f"✓ Charging at {abs(power):.0f}W")
                elif choice == '3':
                    print("Discharge power (W): ", end='', flush=True)
                    power = float(input())
                    self.simulator.set_battery_override(-abs(power))
                    print(f"✓ Discharging at {abs(power):.0f}W")
                elif choice == '4':
                    self.simulator.set_battery_override(0)
                    print("✓ IDLE")
            except:
                print("✗ Invalid input")
