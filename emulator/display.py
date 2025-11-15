"""
Terminal UI Display for Inverter Emulator

Provides a live-updating ASCII dashboard showing inverter status and values.
"""

from rich.console import Console
from rich.text import Text
from rich.live import Live
from datetime import datetime
from typing import Optional, Dict, Any
import time


class EmulatorDisplay:
    """Terminal display for emulator status - ASCII top-like interface."""

    def __init__(self, simulator):
        """Initialize display.

        Args:
            simulator: InverterSimulator instance
        """
        self.simulator = simulator
        self.console = Console()
        self.live = None
        self.start_time = datetime.now()

        # Get register map from the model's profile
        self.register_map = self._get_register_map()

    def _get_register_map(self) -> Dict[int, Dict[str, Any]]:
        """Get the register map for the current inverter model."""
        # Get the register map directly from the model
        # The model already has loaded the register map from the profile
        return self.simulator.model.get_input_registers()

    def _get_register_info(self, entity_name: str) -> tuple:
        """Get register address(es) for an entity name.

        Returns:
            Tuple of (register_str, entity_display_name)
        """
        # Find register(s) for this entity
        regs = []
        for reg_addr, reg_info in self.register_map.items():
            name = reg_info.get('name', '')
            # Match entity name patterns
            if name == entity_name:
                regs.append(reg_addr)
            elif name.endswith('_high') and entity_name == name.replace('_high', ''):
                # For 32-bit pairs, show both registers
                regs.append(reg_addr)
                if 'pair' in reg_info:
                    regs.append(reg_info['pair'])

        if regs:
            if len(regs) == 2:
                return f"[{min(regs):>3d}-{max(regs):<3d}]", entity_name
            else:
                return f"[{regs[0]:>6d}]", entity_name

        # No register found, return placeholder
        return "[  n/a  ]", entity_name

    def _format_uptime(self) -> str:
        """Format uptime as HH:MM:SS."""
        uptime = datetime.now() - self.start_time
        hours = int(uptime.total_seconds() // 3600)
        minutes = int((uptime.total_seconds() % 3600) // 60)
        seconds = int(uptime.total_seconds() % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def render(self) -> Text:
        """Render the complete display as ASCII text."""
        # Update simulator before rendering
        self.simulator.update()

        output = Text()

        # Header
        sim_time = self.simulator.get_simulation_time()
        status_code = self.simulator._get_status()
        status_names = {0: "Waiting", 1: "Normal", 3: "Fault", 5: "Standby"}
        status = status_names.get(status_code, "Unknown")
        status_colors = {0: "yellow", 1: "green", 3: "red", 5: "blue"}
        status_color = status_colors.get(status_code, "white")

        output.append(f"Growatt Inverter Emulator - {self.simulator.model.name}", style="bold cyan")
        output.append(f"{'':>20}Port: ", style="white")
        output.append(f"{self.simulator.port}\n", style="cyan")

        output.append(f"Time: ", style="white")
        output.append(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", style="cyan")
        output.append(" | Simulated: ", style="white")
        output.append(f"{sim_time.strftime('%Y-%m-%d %H:%M:%S')}", style="yellow")
        output.append(f" ({self.simulator.time_multiplier}x speed)\n", style="yellow")

        output.append("Status: ", style="white")
        output.append(f"{status}", style=f"bold {status_color}")
        output.append(" | Uptime: ", style="white")
        output.append(f"{self._format_uptime()}\n", style="cyan")

        output.append("=" * 100 + "\n", style="white")

        # PV Generation Section
        self._render_pv_section(output)

        # AC Output Section
        self._render_ac_section(output)

        # Grid & Battery Section
        self._render_grid_battery_section(output)

        # Energy Totals Section
        self._render_energy_section(output)

        # Bottom separator and controls
        output.append("=" * 100 + "\n", style="white")
        self._render_controls(output)

        return output

    def _render_pv_section(self, output: Text):
        """Render PV generation section."""
        output.append("\nPV GENERATION\n", style="bold green")
        output.append("-" * 100 + "\n", style="green")

        pv = self.simulator.values.get('pv_power', {})
        voltages = self.simulator.values.get('voltages', {})
        currents = self.simulator.values.get('currents', {})

        # Header
        output.append(f"{'String':<8}", style="cyan bold")
        output.append(f"{'Register':<12}", style="white bold")
        output.append(f"{'Entity':<25}", style="white bold")
        output.append(f"{'Voltage':>12}", style="white bold")
        output.append(f"{'Current':>12}", style="white bold")
        output.append(f"{'Power':>15}\n", style="white bold")

        # PV1
        v_reg, _ = self._get_register_info('pv1_voltage')
        i_reg, _ = self._get_register_info('pv1_current')
        p_reg, _ = self._get_register_info('pv1_power')

        output.append(f"{'PV1':<8}", style="cyan")
        output.append(f"{v_reg:<12}", style="blue")
        output.append(f"{'pv1_voltage':<25}", style="white")
        output.append(f"{voltages.get('pv1', 0):>10.1f}V", style="yellow")
        output.append(f"{i_reg:>12}", style="blue")
        output.append(f"{currents.get('pv1', 0):>10.2f}A\n", style="yellow")

        output.append(f"{'':8}", style="cyan")
        output.append(f"{p_reg:<12}", style="blue")
        output.append(f"{'pv1_power':<25}", style="white")
        output.append(f"{'':>12}", style="white")
        output.append(f"{'':>12}", style="white")
        output.append(f"{pv.get('pv1', 0):>13.0f}W\n", style="green")

        # PV2
        v_reg, _ = self._get_register_info('pv2_voltage')
        i_reg, _ = self._get_register_info('pv2_current')
        p_reg, _ = self._get_register_info('pv2_power')

        output.append(f"{'PV2':<8}", style="cyan")
        output.append(f"{v_reg:<12}", style="blue")
        output.append(f"{'pv2_voltage':<25}", style="white")
        output.append(f"{voltages.get('pv2', 0):>10.1f}V", style="yellow")
        output.append(f"{i_reg:>12}", style="blue")
        output.append(f"{currents.get('pv2', 0):>10.2f}A\n", style="yellow")

        output.append(f"{'':8}", style="cyan")
        output.append(f"{p_reg:<12}", style="blue")
        output.append(f"{'pv2_power':<25}", style="white")
        output.append(f"{'':>12}", style="white")
        output.append(f"{'':>12}", style="white")
        output.append(f"{pv.get('pv2', 0):>13.0f}W\n", style="green")

        # PV3 if available
        if self.simulator.model.has_pv3:
            v_reg, _ = self._get_register_info('pv3_voltage')
            i_reg, _ = self._get_register_info('pv3_current')
            p_reg, _ = self._get_register_info('pv3_power')

            output.append(f"{'PV3':<8}", style="cyan")
            output.append(f"{v_reg:<12}", style="blue")
            output.append(f"{'pv3_voltage':<25}", style="white")
            output.append(f"{voltages.get('pv3', 0):>10.1f}V", style="yellow")
            output.append(f"{i_reg:>12}", style="blue")
            output.append(f"{currents.get('pv3', 0):>10.2f}A\n", style="yellow")

            output.append(f"{'':8}", style="cyan")
            output.append(f"{p_reg:<12}", style="blue")
            output.append(f"{'pv3_power':<25}", style="white")
            output.append(f"{'':>12}", style="white")
            output.append(f"{'':>12}", style="white")
            output.append(f"{pv.get('pv3', 0):>13.0f}W\n", style="green")

        # Total
        total_reg, _ = self._get_register_info('pv_total_power')
        output.append(f"{'TOTAL':<8}", style="bold cyan")
        output.append(f"{total_reg:<12}", style="blue")
        output.append(f"{'pv_total_power':<25}", style="white")
        output.append(f"{'':>12}", style="white")
        output.append(f"{'':>12}", style="white")
        output.append(f"{pv.get('total', 0):>13.0f}W\n", style="bold green")

        # Solar conditions
        output.append(f"\nSolar Irradiance: ", style="white")
        output.append(f"{self.simulator.solar_irradiance:.0f} W/m²", style="yellow")
        output.append(" | Cloud Cover: ", style="white")
        output.append(f"{self.simulator.cloud_cover * 100:.0f}%\n", style="cyan")

    def _render_ac_section(self, output: Text):
        """Render AC output section."""
        output.append("\nAC OUTPUT\n", style="bold yellow")
        output.append("-" * 100 + "\n", style="yellow")

        voltages = self.simulator.values.get('voltages', {})
        currents = self.simulator.values.get('currents', {})
        ac_power = self.simulator.values.get('ac_power', 0)

        # Header
        output.append(f"{'Parameter':<15}", style="cyan bold")
        output.append(f"{'Register':<12}", style="white bold")
        output.append(f"{'Entity':<30}", style="white bold")
        output.append(f"{'Value':>20}\n", style="white bold")

        if self.simulator.model.is_three_phase:
            # Three-phase output
            # Phase R
            v_reg, _ = self._get_register_info('grid_voltage_r')
            i_reg, _ = self._get_register_info('grid_current_r')
            p_reg, _ = self._get_register_info('grid_power_r')

            output.append(f"{'Phase R':<15}", style="cyan")
            output.append(f"{v_reg:<12}", style="blue")
            output.append(f"{'grid_voltage_r / grid_current_r':<30}", style="white")
            output.append(f"{voltages.get('ac_r', 0):>10.1f}V @ {currents.get('ac_r', 0):.2f}A\n", style="yellow")

            output.append(f"{'':15}", style="cyan")
            output.append(f"{p_reg:<12}", style="blue")
            output.append(f"{'grid_power_r':<30}", style="white")
            output.append(f"{ac_power / 3:>18.0f}W\n", style="green")

            # Phase S
            v_reg, _ = self._get_register_info('grid_voltage_s')
            i_reg, _ = self._get_register_info('grid_current_s')
            p_reg, _ = self._get_register_info('grid_power_s')

            output.append(f"{'Phase S':<15}", style="cyan")
            output.append(f"{v_reg:<12}", style="blue")
            output.append(f"{'grid_voltage_s / grid_current_s':<30}", style="white")
            output.append(f"{voltages.get('ac_s', 0):>10.1f}V @ {currents.get('ac_s', 0):.2f}A\n", style="yellow")

            output.append(f"{'':15}", style="cyan")
            output.append(f"{p_reg:<12}", style="blue")
            output.append(f"{'grid_power_s':<30}", style="white")
            output.append(f"{ac_power / 3:>18.0f}W\n", style="green")

            # Phase T
            v_reg, _ = self._get_register_info('grid_voltage_t')
            i_reg, _ = self._get_register_info('grid_current_t')
            p_reg, _ = self._get_register_info('grid_power_t')

            output.append(f"{'Phase T':<15}", style="cyan")
            output.append(f"{v_reg:<12}", style="blue")
            output.append(f"{'grid_voltage_t / grid_current_t':<30}", style="white")
            output.append(f"{voltages.get('ac_t', 0):>10.1f}V @ {currents.get('ac_t', 0):.2f}A\n", style="yellow")

            output.append(f"{'':15}", style="cyan")
            output.append(f"{p_reg:<12}", style="blue")
            output.append(f"{'grid_power_t':<30}", style="white")
            output.append(f"{ac_power / 3:>18.0f}W\n", style="green")

            # Frequency and Total
            f_reg, _ = self._get_register_info('grid_frequency')
            output.append(f"{'Frequency':<15}", style="cyan")
            output.append(f"{f_reg:<12}", style="blue")
            output.append(f"{'grid_frequency':<30}", style="white")
            output.append(f"{50.0:>18.2f}Hz\n", style="yellow")

            total_reg, _ = self._get_register_info('output_power')
            output.append(f"{'TOTAL POWER':<15}", style="bold cyan")
            output.append(f"{total_reg:<12}", style="blue")
            output.append(f"{'output_power':<30}", style="white")
            output.append(f"{ac_power:>18.0f}W\n", style="bold green")

        else:
            # Single-phase output
            v_reg, _ = self._get_register_info('ac_voltage')
            i_reg, _ = self._get_register_info('ac_current')
            f_reg, _ = self._get_register_info('ac_frequency')
            p_reg, _ = self._get_register_info('ac_power')

            output.append(f"{'Voltage':<15}", style="cyan")
            output.append(f"{v_reg:<12}", style="blue")
            output.append(f"{'ac_voltage':<30}", style="white")
            output.append(f"{voltages.get('ac', 0):>18.1f}V\n", style="yellow")

            output.append(f"{'Current':<15}", style="cyan")
            output.append(f"{i_reg:<12}", style="blue")
            output.append(f"{'ac_current':<30}", style="white")
            output.append(f"{currents.get('ac', 0):>18.2f}A\n", style="yellow")

            output.append(f"{'Frequency':<15}", style="cyan")
            output.append(f"{f_reg:<12}", style="blue")
            output.append(f"{'ac_frequency':<30}", style="white")
            output.append(f"{50.0:>18.2f}Hz\n", style="yellow")

            output.append(f"{'POWER':<15}", style="bold cyan")
            output.append(f"{p_reg:<12}", style="blue")
            output.append(f"{'ac_power':<30}", style="white")
            output.append(f"{ac_power:>18.0f}W\n", style="bold green")

    def _render_grid_battery_section(self, output: Text):
        """Render grid and battery section."""
        output.append("\nGRID & BATTERY\n", style="bold cyan")
        output.append("-" * 100 + "\n", style="cyan")

        grid_power = self.simulator.values.get('grid_power', {})

        # Header
        output.append(f"{'Parameter':<15}", style="cyan bold")
        output.append(f"{'Register':<12}", style="white bold")
        output.append(f"{'Entity':<30}", style="white bold")
        output.append(f"{'Value':>20}\n", style="white bold")

        # Grid section
        grid_net = grid_power.get('grid', 0)
        grid_import = grid_power.get('import', 0)
        grid_export = grid_power.get('export', 0)

        # Note: Grid power registers may not be in all profiles, show as n/a
        output.append(f"{'Grid Import':<15}", style="cyan")
        output.append(f"{'[  n/a  ]':<12}", style="blue")
        output.append(f"{'grid_import_power':<30}", style="white")
        if grid_import > 0:
            output.append(f"{grid_import:>18.0f}W", style="yellow")
        else:
            output.append(f"{0:>18.0f}W", style="white")
        output.append(" (importing)\n" if grid_import > 0 else "\n", style="yellow")

        output.append(f"{'Grid Export':<15}", style="cyan")
        output.append(f"{'[  n/a  ]':<12}", style="blue")
        output.append(f"{'grid_export_power':<30}", style="white")
        if grid_export > 0:
            output.append(f"{grid_export:>18.0f}W", style="green")
        else:
            output.append(f"{0:>18.0f}W", style="white")
        output.append(" (exporting)\n" if grid_export > 0 else "\n", style="green")

        output.append(f"{'Net Grid Power':<15}", style="cyan")
        output.append(f"{'[  n/a  ]':<12}", style="blue")
        output.append(f"{'grid_power':<30}", style="white")
        grid_color = "yellow" if grid_net > 0 else "green" if grid_net < 0 else "white"
        output.append(f"{grid_net:>18.0f}W\n", style=grid_color)

        # Load
        load_reg, _ = self._get_register_info('load_power')
        output.append(f"{'Load Power':<15}", style="cyan")
        output.append(f"{load_reg:<12}", style="blue")
        output.append(f"{'load_power':<30}", style="white")
        output.append(f"{self.simulator.house_load:>18.0f}W\n", style="magenta")

        # Battery section (if available)
        if self.simulator.model.has_battery:
            output.append("\n", style="white")

            battery_power = self.simulator.values.get('battery_power', 0)
            voltages = self.simulator.values.get('voltages', {})
            currents = self.simulator.values.get('currents', {})
            soc = self.simulator.battery_soc

            soc_reg, _ = self._get_register_info('battery_soc')
            output.append(f"{'Battery SOC':<15}", style="cyan")
            output.append(f"{soc_reg:<12}", style="blue")
            output.append(f"{'battery_soc':<30}", style="white")

            # SOC bar
            bar_length = 20
            filled = int(soc / 100 * bar_length)
            bar = "█" * filled + "░" * (bar_length - filled)
            soc_color = "green" if soc > 50 else "yellow" if soc > 20 else "red"
            output.append(f"{soc:>5.0f}% [{bar}]\n", style=soc_color)

            p_reg, _ = self._get_register_info('battery_power')
            output.append(f"{'Battery Power':<15}", style="cyan")
            output.append(f"{p_reg:<12}", style="blue")
            output.append(f"{'battery_power':<30}", style="white")
            if battery_power > 0:
                output.append(f"{battery_power:>18.0f}W", style="green")
                output.append(" (charging)\n", style="green")
            elif battery_power < 0:
                output.append(f"{abs(battery_power):>18.0f}W", style="yellow")
                output.append(" (discharging)\n", style="yellow")
            else:
                output.append(f"{0:>18.0f}W\n", style="white")

            v_reg, _ = self._get_register_info('battery_voltage')
            output.append(f"{'Battery Voltage':<15}", style="cyan")
            output.append(f"{v_reg:<12}", style="blue")
            output.append(f"{'battery_voltage':<30}", style="white")
            output.append(f"{voltages.get('battery', 0):>18.1f}V\n", style="yellow")

            i_reg, _ = self._get_register_info('battery_current')
            output.append(f"{'Battery Current':<15}", style="cyan")
            output.append(f"{i_reg:<12}", style="blue")
            output.append(f"{'battery_current':<30}", style="white")
            output.append(f"{currents.get('battery', 0):>18.2f}A\n", style="yellow")

            output.append(f"{'Charge Today':<15}", style="cyan")
            output.append(f"{'[  n/a  ]':<12}", style="blue")
            output.append(f"{'battery_charge_today':<30}", style="white")
            output.append(f"{self.simulator.battery_charge_today:>17.1f}kWh\n", style="green")

            output.append(f"{'Discharge Today':<15}", style="cyan")
            output.append(f"{'[  n/a  ]':<12}", style="blue")
            output.append(f"{'battery_discharge_today':<30}", style="white")
            output.append(f"{self.simulator.battery_discharge_today:>17.1f}kWh\n", style="yellow")

    def _render_energy_section(self, output: Text):
        """Render energy totals section."""
        output.append("\nENERGY TOTALS (kWh)\n", style="bold magenta")
        output.append("-" * 100 + "\n", style="magenta")

        # Header
        output.append(f"{'Metric':<20}", style="cyan bold")
        output.append(f"{'Register':<12}", style="white bold")
        output.append(f"{'Entity':<35}", style="white bold")
        output.append(f"{'Today':>15}", style="white bold")
        output.append(f"{'Total':>15}\n", style="white bold")

        # PV Generation
        today_reg, _ = self._get_register_info('energy_today')
        total_reg, _ = self._get_register_info('energy_total')

        output.append(f"{'PV Generation':<20}", style="cyan")
        output.append(f"{today_reg:<12}", style="blue")
        output.append(f"{'energy_today / energy_total':<35}", style="white")
        output.append(f"{self.simulator.energy_today:>14.1f}", style="green")
        output.append(f"{self.simulator.energy_total:>15.0f}\n", style="green")

        # Grid Export
        output.append(f"{'Grid Export':<20}", style="cyan")
        output.append(f"{'[  n/a  ]':<12}", style="blue")
        output.append(f"{'energy_to_grid_today / total':<35}", style="white")
        output.append(f"{self.simulator.energy_to_grid_today:>14.1f}", style="green")
        output.append(f"{self.simulator.energy_to_grid_total:>15.0f}\n", style="green")

        # Grid Import
        output.append(f"{'Grid Import':<20}", style="cyan")
        output.append(f"{'[  n/a  ]':<12}", style="blue")
        output.append(f"{'grid_import_energy_today / total':<35}", style="white")
        output.append(f"{self.simulator.grid_import_energy_today:>14.1f}", style="yellow")
        output.append(f"{self.simulator.grid_import_energy_total:>15.0f}\n", style="yellow")

        # Load Consumption
        output.append(f"{'Load Consumption':<20}", style="cyan")
        output.append(f"{'[  n/a  ]':<12}", style="blue")
        output.append(f"{'load_energy_today / load_energy_total':<35}", style="white")
        output.append(f"{self.simulator.load_energy_today:>14.1f}", style="magenta")
        output.append(f"{self.simulator.load_energy_total:>15.0f}\n", style="magenta")

    def _render_controls(self, output: Text):
        """Render control keys."""
        output.append("CONTROLS: ", style="bold white")
        output.append("[I]", style="bold cyan")
        output.append("rradiance  ", style="white")
        output.append("[C]", style="bold cyan")
        output.append("loud  ", style="white")
        output.append("[L]", style="bold cyan")
        output.append("oad  ", style="white")
        output.append("[T]", style="bold cyan")
        output.append("ime Speed  ", style="white")

        if self.simulator.model.has_battery:
            output.append("[B]", style="bold cyan")
            output.append("attery  ", style="white")

        output.append("[R]", style="bold cyan")
        output.append("eset  ", style="white")
        output.append("[Q]", style="bold cyan")
        output.append("uit\n", style="white")

    def start_live_display(self):
        """Start live updating display."""
        self.live = Live(
            self.render(),
            console=self.console,
            refresh_per_second=0.5,
            screen=True,
            auto_refresh=True
        )
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
