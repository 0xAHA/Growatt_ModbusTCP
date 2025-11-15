"""
Terminal UI Display for Inverter Emulator

Provides a live-updating dashboard showing inverter status and values.
"""

from rich.console import Console, Group
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.live import Live
from datetime import datetime
from typing import Optional


class EmulatorDisplay:
    """Terminal display for emulator status."""

    def __init__(self, simulator):
        """Initialize display.

        Args:
            simulator: InverterSimulator instance
        """
        self.simulator = simulator
        self.console = Console()
        self.live = None

    def create_layout(self) -> Layout:
        """Create the display layout."""
        layout = Layout()

        layout.split_column(
            Layout(name="header", size=1),
            Layout(name="main"),
            Layout(name="controls", size=1),
        )

        layout["main"].split_row(
            Layout(name="left"),
            Layout(name="right"),
        )

        return layout

    def generate_header(self) -> Panel:
        """Generate header panel."""
        sim_time = self.simulator.get_simulation_time()
        status_code = self.simulator._get_status()
        status_names = {0: "Waiting", 1: "Normal", 3: "Fault", 5: "Standby"}
        status = status_names.get(status_code, "Unknown")

        # Color based on status
        status_colors = {0: "yellow", 1: "green", 3: "red", 5: "blue"}
        status_color = status_colors.get(status_code, "white")

        header_text = Text()
        header_text.append(f"⚡ {self.simulator.model.name}", style="bold cyan")
        header_text.append(f" | {sim_time.strftime('%H:%M:%S')}", style="white")
        header_text.append(f" | {self.simulator.time_multiplier}x", style="yellow")
        header_text.append(f" | ", style="white")
        header_text.append(f"{status}", style=f"bold {status_color}")
        header_text.append(f" | Port {self.simulator.port}", style="cyan")

        return Panel(header_text, style="bold", padding=(0, 0))

    def generate_pv_panel(self) -> Panel:
        """Generate PV generation panel."""
        pv = self.simulator.values.get('pv_power', {})
        voltages = self.simulator.values.get('voltages', {})
        currents = self.simulator.values.get('currents', {})

        table = Table(show_header=True, header_style="bold magenta", box=None, padding=(0, 0), collapse_padding=True)
        table.add_column("String", style="cyan", width=6)
        table.add_column("Voltage", justify="right", width=8)
        table.add_column("Current", justify="right", width=8)
        table.add_column("Power", justify="right", width=10)

        # PV String 1
        table.add_row(
            "PV1",
            f"{voltages.get('pv1', 0):.1f}V",
            f"{currents.get('pv1', 0):.2f}A",
            f"[green]{pv.get('pv1', 0):.0f}W[/green]"
        )

        # PV String 2
        table.add_row(
            "PV2",
            f"{voltages.get('pv2', 0):.1f}V",
            f"{currents.get('pv2', 0):.2f}A",
            f"[green]{pv.get('pv2', 0):.0f}W[/green]"
        )

        # PV String 3 (if available)
        if self.simulator.model.has_pv3:
            table.add_row(
                "PV3",
                f"{voltages.get('pv3', 0):.1f}V",
                f"{currents.get('pv3', 0):.2f}A",
                f"[green]{pv.get('pv3', 0):.0f}W[/green]"
            )

        table.add_row(
            "[bold]Total[/bold]",
            "",
            "",
            f"[bold green]{pv.get('total', 0):.0f}W[/bold green]"
        )

        # Add irradiance info below table (compact)
        irradiance_text = Text.from_markup(f"☀️{self.simulator.solar_irradiance:.0f} ☁️{self.simulator.cloud_cover * 100:.0f}%")

        return Panel(
            Group(table, irradiance_text),
            title="[bold]PV[/bold]",
            border_style="green",
            padding=(0, 0)
        )

    def generate_ac_panel(self) -> Panel:
        """Generate AC output panel."""
        voltages = self.simulator.values.get('voltages', {})
        currents = self.simulator.values.get('currents', {})
        ac_power = self.simulator.values.get('ac_power', 0)

        table = Table(show_header=False, box=None, padding=(0, 0), collapse_padding=True)
        table.add_column("Label", style="cyan", width=12)
        table.add_column("Value", justify="right", width=18)

        if self.simulator.model.is_three_phase:
            # Three-phase
            table.add_row("Phase R", f"{voltages.get('ac_r', 0):.1f}V @ {currents.get('ac_r', 0):.2f}A")
            table.add_row("Phase S", f"{voltages.get('ac_s', 0):.1f}V @ {currents.get('ac_s', 0):.2f}A")
            table.add_row("Phase T", f"{voltages.get('ac_t', 0):.1f}V @ {currents.get('ac_t', 0):.2f}A")
            table.add_row("[bold]Total[/bold]", f"[bold yellow]{ac_power:.0f}W[/bold yellow]")
        else:
            # Single-phase
            table.add_row("Voltage", f"{voltages.get('ac', 0):.1f}V")
            table.add_row("Current", f"{currents.get('ac', 0):.2f}A")
            table.add_row("Frequency", "50.0Hz")
            table.add_row("[bold]Power[/bold]", f"[bold yellow]{ac_power:.0f}W[/bold yellow]")

        return Panel(table, title="[bold]AC[/bold]", border_style="yellow", padding=(0, 0))

    def generate_battery_panel(self) -> Optional[Panel]:
        """Generate battery panel (if model has battery)."""
        if not self.simulator.model.has_battery:
            return None

        voltages = self.simulator.values.get('voltages', {})
        currents = self.simulator.values.get('currents', {})
        battery_power = self.simulator.values.get('battery_power', 0)

        table = Table(show_header=False, box=None, padding=(0, 0), collapse_padding=True)
        table.add_column("Label", style="cyan", width=12)
        table.add_column("Value", justify="right", width=18)

        # SOC with bar
        soc = self.simulator.battery_soc
        soc_bar = "█" * int(soc / 10) + "░" * (10 - int(soc / 10))
        soc_color = "green" if soc > 50 else "yellow" if soc > 20 else "red"

        table.add_row("SOC", f"[{soc_color}]{soc_bar}[/{soc_color}] {soc:.0f}%")

        # Power with direction indicator
        if battery_power > 0:
            power_text = f"[green]↑{battery_power:.0f}W[/green]"
        elif battery_power < 0:
            power_text = f"[yellow]↓{abs(battery_power):.0f}W[/yellow]"
        else:
            power_text = "0W"

        table.add_row("Power", power_text)
        table.add_row("Ch/Disch", f"{self.simulator.battery_charge_today:.1f}/{self.simulator.battery_discharge_today:.1f}kWh")

        return Panel(table, title="[bold]Battery[/bold]", border_style="blue", padding=(0, 0))

    def generate_grid_panel(self) -> Panel:
        """Generate grid panel."""
        grid_power = self.simulator.values.get('grid_power', {})

        table = Table(show_header=False, box=None, padding=(0, 0), collapse_padding=True)
        table.add_column("Label", style="cyan", width=12)
        table.add_column("Value", justify="right", width=18)

        grid_net = grid_power.get('grid', 0)
        grid_import = grid_power.get('import', 0)
        grid_export = grid_power.get('export', 0)

        if grid_export > 0:
            status_text = f"[green]↑ Exporting {grid_export:.0f}W[/green]"
        elif grid_import > 0:
            status_text = f"[yellow]↓ Importing {grid_import:.0f}W[/yellow]"
        else:
            status_text = "[white]⚖ Balanced[/white]"

        table.add_row("Status", status_text)
        table.add_row("Import", f"{grid_import:.0f}W")
        table.add_row("Export", f"{grid_export:.0f}W")
        table.add_row("Load", f"[magenta]{self.simulator.house_load:.0f}W[/magenta]")

        return Panel(table, title="[bold]Grid[/bold]", border_style="cyan", padding=(0, 0))

    def generate_energy_panel(self) -> Panel:
        """Generate energy totals panel."""
        table = Table(show_header=True, header_style="bold magenta", box=None, padding=(0, 0), collapse_padding=True)
        table.add_column("Metric", style="cyan", width=16)
        table.add_column("Today", justify="right", width=10)
        table.add_column("Total", justify="right", width=10)

        table.add_row(
            "PV Gen",
            f"{self.simulator.energy_today:.1f}",
            f"{self.simulator.energy_total:.0f}"
        )

        table.add_row(
            "Grid Export",
            f"{self.simulator.energy_to_grid_today:.1f}",
            f"{self.simulator.energy_to_grid_total:.0f}"
        )

        table.add_row(
            "Grid Import",
            f"{self.simulator.grid_import_energy_today:.1f}",
            f"{self.simulator.grid_import_energy_total:.0f}"
        )

        table.add_row(
            "Load",
            f"{self.simulator.load_energy_today:.1f}",
            f"{self.simulator.load_energy_total:.0f}"
        )

        return Panel(table, title="[bold]Energy (kWh)[/bold]", border_style="magenta", padding=(0, 0))

    def generate_temperature_panel(self) -> Panel:
        """Generate temperature panel."""
        temps = self.simulator.values.get('temperatures', {})

        table = Table(show_header=False, box=None, padding=(0, 0), collapse_padding=True)
        table.add_column("Component", style="cyan", width=12)
        table.add_column("Temp", justify="right", width=10)

        inverter_temp = temps.get('inverter', 0)
        temp_color = "green" if inverter_temp < 50 else "yellow" if inverter_temp < 70 else "red"

        table.add_row("Inverter", f"[{temp_color}]{inverter_temp:.0f}°C[/{temp_color}]")
        table.add_row("IPM", f"{temps.get('ipm', 0):.0f}°C")
        table.add_row("Boost", f"{temps.get('boost', 0):.0f}°C")

        return Panel(table, title="[bold]Temp[/bold]", border_style="red", padding=(0, 0))

    def generate_controls_panel(self) -> Panel:
        """Generate controls help panel."""
        controls_text = Text()
        controls_text.append("[I]", style="bold cyan")
        controls_text.append("Irrad ", style="white")
        controls_text.append("[C]", style="bold cyan")
        controls_text.append("Cloud ", style="white")
        controls_text.append("[L]", style="bold cyan")
        controls_text.append("Load ", style="white")
        controls_text.append("[T]", style="bold cyan")
        controls_text.append("Speed ", style="white")

        if self.simulator.model.has_battery:
            controls_text.append("[B]", style="bold cyan")
            controls_text.append("Batt ", style="white")

        controls_text.append("[R]", style="bold cyan")
        controls_text.append("Reset ", style="white")
        controls_text.append("[Q]", style="bold cyan")
        controls_text.append("Quit", style="white")

        return Panel(controls_text, border_style="white", padding=(0, 0))

    def render(self) -> Layout:
        """Render the complete display."""
        layout = self.create_layout()

        # Update simulator before rendering
        self.simulator.update()

        # Header
        layout["header"].update(self.generate_header())

        # Left column
        left_layout = Layout()
        if self.simulator.model.has_battery:
            left_layout.split_column(
                Layout(self.generate_pv_panel()),
                Layout(self.generate_battery_panel()),
                Layout(self.generate_temperature_panel()),
            )
        else:
            left_layout.split_column(
                Layout(self.generate_pv_panel()),
                Layout(self.generate_temperature_panel()),
            )

        layout["left"].update(left_layout)

        # Right column
        right_layout = Layout()
        right_layout.split_column(
            Layout(self.generate_ac_panel()),
            Layout(self.generate_grid_panel()),
            Layout(self.generate_energy_panel()),
        )

        layout["right"].update(right_layout)

        # Controls
        layout["controls"].update(self.generate_controls_panel())

        return layout

    def start_live_display(self):
        """Start live updating display."""
        self.live = Live(self.render(), console=self.console, refresh_per_second=0.5, screen=True)
        return self.live

    def stop_live_display(self):
        """Stop live display."""
        if self.live:
            self.live.stop()

    def pause(self):
        """Pause the live display for user input."""
        if self.live:
            self.live.stop()

    def resume(self):
        """Resume the live display after user input."""
        if self.live:
            self.live.start()
