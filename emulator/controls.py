"""
Control Handler for Inverter Emulator

Handles user input and adjusts simulation parameters.
Cross-platform support for Windows, Linux, and macOS.
"""

import sys
import platform
import threading
import time
from typing import Callable, Optional


# Detect platform and import appropriate modules
IS_WINDOWS = platform.system() == 'Windows'

if IS_WINDOWS:
    try:
        import msvcrt
        KEYBOARD_AVAILABLE = True
    except ImportError:
        KEYBOARD_AVAILABLE = False
        print("Warning: Keyboard input not available on this platform")
else:
    # Unix-like systems (Linux, macOS)
    try:
        import tty
        import termios
        import select
        KEYBOARD_AVAILABLE = True
    except ImportError:
        KEYBOARD_AVAILABLE = False
        print("Warning: Keyboard input not available on this platform")


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
        if not KEYBOARD_AVAILABLE:
            print("\nKeyboard controls disabled (platform not supported)")
            print("You can still view the emulator output\n")
            return

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
        if IS_WINDOWS:
            self._input_loop_windows()
        else:
            self._input_loop_unix()

    def _input_loop_unix(self) -> None:
        """Unix/Linux/macOS input loop."""
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

    def _input_loop_windows(self) -> None:
        """Windows input loop using msvcrt."""
        try:
            while self.running:
                if msvcrt.kbhit():
                    char = msvcrt.getch().decode('utf-8', errors='ignore').lower()
                    self._handle_key(char)
                time.sleep(0.1)
        except Exception as e:
            print(f"\nInput error: {e}")

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
            time.sleep(1)

        except (ValueError, EOFError, KeyboardInterrupt):
            print("✗ Invalid input")
            time.sleep(1)

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
            time.sleep(1)

        except (ValueError, EOFError, KeyboardInterrupt):
            print("✗ Invalid input")
            time.sleep(1)

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
            time.sleep(1)

        except (ValueError, EOFError, KeyboardInterrupt):
            print("✗ Invalid input")
            time.sleep(1)

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
            time.sleep(1)

        except (ValueError, EOFError, KeyboardInterrupt):
            print("✗ Invalid input")
            time.sleep(1)

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

            time.sleep(1)

        except (ValueError, EOFError, KeyboardInterrupt):
            print("✗ Invalid input")
            time.sleep(1)
