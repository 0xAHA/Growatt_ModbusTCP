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

    def __init__(self, simulator, display=None, on_quit: Optional[Callable] = None):
        """Initialize control handler.

        Args:
            simulator: InverterSimulator instance
            display: EmulatorDisplay instance (optional, for pausing)
            on_quit: Callback function when user quits
        """
        self.simulator = simulator
        self.display = display
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
            if self.display and self.display.console:
                self.display.console.print(f"\n[cyan]Solar Irradiance[/cyan] (current: {self.simulator.solar_irradiance:.0f} W/m²)")
                self.display.console.print("[white]Enter new value (0-1000): [/white]", end='')
            else:
                print(f"\nSolar Irradiance (current: {self.simulator.solar_irradiance:.0f} W/m²)")
                print("Enter new value (0-1000): ", end='', flush=True)

            value = float(input())
            self.simulator.set_irradiance(value)

            if self.display and self.display.console:
                self.display.console.print(f"[green]✓ Irradiance set to {self.simulator.solar_irradiance:.0f} W/m²[/green]")
            else:
                print(f"✓ Irradiance set to {self.simulator.solar_irradiance:.0f} W/m²")

        except (ValueError, EOFError, KeyboardInterrupt):
            if self.display and self.display.console:
                self.display.console.print("[red]✗ Invalid input[/red]")
            else:
                print("✗ Invalid input")

    def _prompt_clouds(self) -> None:
        """Prompt for cloud cover."""
        try:
            if self.display and self.display.console:
                self.display.console.print(f"\n[cyan]Cloud Cover[/cyan] (current: {self.simulator.cloud_cover * 100:.0f}%)")
                self.display.console.print("[white]Enter new value (0-100): [/white]", end='')
            else:
                print(f"\nCloud Cover (current: {self.simulator.cloud_cover * 100:.0f}%)")
                print("Enter new value (0-100): ", end='', flush=True)

            value = float(input()) / 100.0
            self.simulator.set_cloud_cover(value)

            if self.display and self.display.console:
                self.display.console.print(f"[green]✓ Cloud cover set to {self.simulator.cloud_cover * 100:.0f}%[/green]")
            else:
                print(f"✓ Cloud cover set to {self.simulator.cloud_cover * 100:.0f}%")

        except (ValueError, EOFError, KeyboardInterrupt):
            if self.display and self.display.console:
                self.display.console.print("[red]✗ Invalid input[/red]")
            else:
                print("✗ Invalid input")

    def _prompt_load(self) -> None:
        """Prompt for house load."""
        try:
            if self.display and self.display.console:
                self.display.console.print(f"\n[cyan]House Load[/cyan] (current: {self.simulator.house_load:.0f}W)")
                self.display.console.print("[white]Enter new value (W): [/white]", end='')
            else:
                print(f"\nHouse Load (current: {self.simulator.house_load:.0f}W)")
                print("Enter new value (W): ", end='', flush=True)

            value = float(input())
            self.simulator.set_house_load(value)

            if self.display and self.display.console:
                self.display.console.print(f"[green]✓ House load set to {self.simulator.house_load:.0f}W[/green]")
            else:
                print(f"✓ House load set to {self.simulator.house_load:.0f}W")

        except (ValueError, EOFError, KeyboardInterrupt):
            if self.display and self.display.console:
                self.display.console.print("[red]✗ Invalid input[/red]")
            else:
                print("✗ Invalid input")

    def _prompt_time_speed(self) -> None:
        """Prompt for time multiplier."""
        try:
            if self.display and self.display.console:
                self.display.console.print(f"\n[cyan]Time Speed[/cyan] (current: {self.simulator.time_multiplier}x)")
                self.display.console.print("[white]Enter new multiplier (0.1-100): [/white]", end='')
            else:
                print(f"\nTime Speed (current: {self.simulator.time_multiplier}x)")
                print("Enter new multiplier (0.1-100): ", end='', flush=True)

            value = float(input())
            self.simulator.set_time_multiplier(value)

            if self.display and self.display.console:
                self.display.console.print(f"[green]✓ Time speed set to {self.simulator.time_multiplier}x[/green]")
            else:
                print(f"✓ Time speed set to {self.simulator.time_multiplier}x")

        except (ValueError, EOFError, KeyboardInterrupt):
            if self.display and self.display.console:
                self.display.console.print("[red]✗ Invalid input[/red]")
            else:
                print("✗ Invalid input")

    def _prompt_battery(self) -> None:
        """Prompt for battery control."""
        try:
            if self.display and self.display.console:
                self.display.console.print("\n[cyan]Battery Control[/cyan]")
                self.display.console.print("[white]1. Auto  2. Charge  3. Discharge  4. Idle[/white]")
                self.display.console.print("[white]Enter choice (1-4): [/white]", end='')
            else:
                print("\nBattery Control")
                print("1. Auto  2. Charge  3. Discharge  4. Idle")
                print("Enter choice (1-4): ", end='', flush=True)

            choice = input().strip()

            if choice == '1':
                self.simulator.set_battery_override(None)
                msg = "✓ Battery set to AUTO mode"

            elif choice == '2':
                if self.display and self.display.console:
                    self.display.console.print("[white]Enter charge power (W): [/white]", end='')
                else:
                    print("Enter charge power (W): ", end='', flush=True)
                power = float(input())
                self.simulator.set_battery_override(abs(power))
                msg = f"✓ Battery charging at {abs(power):.0f}W"

            elif choice == '3':
                if self.display and self.display.console:
                    self.display.console.print("[white]Enter discharge power (W): [/white]", end='')
                else:
                    print("Enter discharge power (W): ", end='', flush=True)
                power = float(input())
                self.simulator.set_battery_override(-abs(power))
                msg = f"✓ Battery discharging at {abs(power):.0f}W"

            elif choice == '4':
                self.simulator.set_battery_override(0)
                msg = "✓ Battery set to IDLE"
            else:
                msg = "✗ Invalid choice"

            if self.display and self.display.console:
                self.display.console.print(f"[green]{msg}[/green]")
            else:
                print(msg)

        except (ValueError, EOFError, KeyboardInterrupt):
            if self.display and self.display.console:
                self.display.console.print("[red]✗ Invalid input[/red]")
            else:
                print("✗ Invalid input")
