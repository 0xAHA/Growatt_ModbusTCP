"""
Inverter Simulation Engine

Simulates realistic inverter behavior including:
- Solar generation with day/night cycles
- Battery charge/discharge
- Grid import/export
- Temperature variations
- Power calculations
"""

import math
import time
import random
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from .models import InverterModel


class InverterSimulator:
    """Simulates a Growatt inverter with realistic behavior."""

    def __init__(self, model: InverterModel, port: int = 502):
        """Initialize simulator.

        Args:
            model: InverterModel instance
            port: Modbus TCP port
        """
        self.model = model
        self.port = port

        # Simulation state
        self.running = True
        self.paused = False  # Pause simulation updates
        self.start_time = time.time()
        self.simulation_time = datetime.now().replace(hour=12, minute=0, second=0)  # Start at noon
        self.time_multiplier = 1.0  # Real-time by default

        # User-adjustable parameters
        self.solar_irradiance = 800.0  # W/m² (0-1000)
        self.cloud_cover = 0.0  # 0-1 (0=clear, 1=overcast)
        self.house_load = 2000.0  # W
        self.battery_override = None  # None=auto, or specific W value

        # Static parameters
        self.serial_number = self._generate_serial()
        self.firmware_version = "1.39"

        # State variables
        self.battery_soc = 50.0  # %
        self.battery_capacity_kwh = 10.0 if model.has_battery else 0.0
        self.energy_today = 0.0  # kWh
        self.energy_total = 1234.5  # kWh (start with some history)
        self.last_update = time.time()

        # Battery energy tracking
        self.battery_charge_today = 0.0  # kWh
        self.battery_discharge_today = 0.0  # kWh
        self.battery_charge_total = 567.8  # kWh (historical)
        self.battery_discharge_total = 456.2  # kWh (historical)

        # Grid energy tracking
        self.grid_import_energy_today = 0.0
        self.grid_import_energy_total = 234.5
        self.energy_to_grid_today = 0.0
        self.energy_to_grid_total = 456.7
        self.load_energy_today = 0.0
        self.load_energy_total = 987.6

        # Midnight reset tracking
        self.last_midnight = datetime.now().date()

        # Current values (calculated each update)
        self.values = {}

        # Initial calculation
        self.update()

    def _generate_serial(self) -> str:
        """Generate a realistic serial number."""
        return f"GRW{random.randint(1000, 9999)}{random.randint(10000, 99999)}"

    def get_simulation_time(self) -> datetime:
        """Get current simulation time."""
        elapsed = time.time() - self.start_time
        return self.simulation_time + timedelta(seconds=elapsed * self.time_multiplier)

    def update(self) -> None:
        """Update all simulated values based on current state."""
        # Skip updates if paused
        if self.paused:
            return

        now = time.time()
        dt = now - self.last_update  # Time delta in seconds
        sim_time = self.get_simulation_time()

        # Check for midnight reset
        if sim_time.date() > self.last_midnight:
            self._reset_daily_totals()
            self.last_midnight = sim_time.date()

        # Calculate solar generation
        pv_power = self._calculate_pv_generation(sim_time)

        # Calculate battery state
        battery_power = self._calculate_battery_power(pv_power, dt * self.time_multiplier)

        # Calculate grid interaction
        grid_power = self._calculate_grid_power(pv_power, battery_power)

        # Calculate AC output
        ac_power = pv_power['total'] + battery_power  # Total output to grid/load

        # Calculate temperatures
        temps = self._calculate_temperatures(ac_power)

        # Calculate voltages and currents
        voltages = self._calculate_voltages()
        currents = self._calculate_currents(pv_power, ac_power, battery_power)

        # Update energy totals
        self._update_energy_totals(pv_power, battery_power, grid_power, dt * self.time_multiplier)

        # Store all values
        self.values = {
            'pv_power': pv_power,
            'battery_power': battery_power,
            'grid_power': grid_power,
            'ac_power': ac_power,
            'temperatures': temps,
            'voltages': voltages,
            'currents': currents,
            'sim_time': sim_time,
            'status': self._get_status(),
        }

        self.last_update = now

    def _calculate_pv_generation(self, sim_time: datetime) -> Dict[str, float]:
        """Calculate PV generation based on time of day and irradiance.

        Args:
            sim_time: Current simulation time

        Returns:
            Dict with pv1_power, pv2_power, pv3_power (if applicable), and total
        """
        # Calculate sun position (simplified model)
        hour = sim_time.hour + sim_time.minute / 60.0

        # Sun elevation: 0 at midnight/noon, peaks around 12:00
        # Using sine wave from 6:00 to 18:00
        if 6 <= hour <= 18:
            # Normalize to 0-1, peaks at solar noon (13:00 typically)
            sun_angle = math.sin((hour - 6) * math.pi / 12)
            sun_elevation = max(0, sun_angle)
        else:
            sun_elevation = 0

        # Apply irradiance and cloud cover
        effective_irradiance = self.solar_irradiance * sun_elevation * (1 - self.cloud_cover * 0.8)

        # Add small random variations (clouds, etc.)
        variation = random.uniform(0.95, 1.05)
        effective_irradiance *= variation

        # Calculate power for each string
        # Distribute total capacity across strings
        max_power = self.model.max_power_kw * 1000  # Convert to W
        power_per_string = max_power / self.model.num_pv_strings

        # Each string can generate based on irradiance (1000 W/m² = 100% capacity)
        base_power = (effective_irradiance / 1000.0) * power_per_string

        # Add small variations between strings (different orientations, shading)
        pv1_power = base_power * random.uniform(0.95, 1.05)
        pv2_power = base_power * random.uniform(0.95, 1.05)
        pv3_power = base_power * random.uniform(0.95, 1.05) if self.model.has_pv3 else 0.0

        total_power = pv1_power + pv2_power + pv3_power

        return {
            'pv1': max(0, pv1_power),
            'pv2': max(0, pv2_power),
            'pv3': max(0, pv3_power),
            'total': max(0, total_power),
        }

    def _calculate_battery_power(self, pv_power: Dict[str, float], dt: float) -> float:
        """Calculate battery charge/discharge power.

        Positive = charging, Negative = discharging

        Args:
            pv_power: PV generation dict
            dt: Time delta in seconds

        Returns:
            Battery power in watts (+ charging, - discharging)
        """
        if not self.model.has_battery:
            return 0.0

        # User override
        if self.battery_override is not None:
            power = self.battery_override
        else:
            # Auto mode: charge from excess PV, discharge when PV < load
            excess_pv = pv_power['total'] - self.house_load

            if excess_pv > 0:
                # Charge from excess (limit by battery capacity and SOC)
                max_charge = 5000.0  # 5kW max charge rate
                if self.battery_soc >= 95:
                    power = 0  # Stop charging near full
                elif self.battery_soc >= 90:
                    power = min(excess_pv * 0.3, max_charge * 0.5)  # Trickle charge
                else:
                    power = min(excess_pv * 0.9, max_charge)  # Charge at 90% efficiency
            else:
                # Discharge to cover shortfall
                shortfall = -excess_pv
                max_discharge = 5000.0  # 5kW max discharge rate

                if self.battery_soc <= 10:
                    power = 0  # Stop discharging when low
                elif self.battery_soc <= 20:
                    power = -min(shortfall * 0.3, max_discharge * 0.5)  # Reduce discharge
                else:
                    power = -min(shortfall * 0.9, max_discharge)

        # Update battery SOC
        if dt > 0:
            # Convert power to energy: P(W) * t(s) / 3600 = Wh, / 1000 = kWh
            energy_kwh = (power * dt) / (3600 * 1000)
            soc_change = (energy_kwh / self.battery_capacity_kwh) * 100
            self.battery_soc = max(5, min(100, self.battery_soc + soc_change))

        return power

    def _calculate_grid_power(self, pv_power: Dict[str, float], battery_power: float) -> Dict[str, float]:
        """Calculate grid import/export.

        Args:
            pv_power: PV generation dict
            battery_power: Battery power (+ charge, - discharge)

        Returns:
            Dict with grid_power, import_power, export_power
        """
        # Total generation available
        total_generation = pv_power['total'] - battery_power  # Subtract battery charging

        # Net grid power (negative = export, positive = import)
        net_power = self.house_load - total_generation

        if net_power > 0:
            # Importing from grid
            grid_import = net_power
            grid_export = 0
        else:
            # Exporting to grid
            grid_import = 0
            grid_export = -net_power

        return {
            'grid': -net_power,  # Negative = export, positive = import (Growatt convention)
            'import': grid_import,
            'export': grid_export,
        }

    def _calculate_temperatures(self, ac_power: float) -> Dict[str, float]:
        """Calculate inverter temperatures based on load.

        Args:
            ac_power: AC output power

        Returns:
            Dict with inverter_temp, ipm_temp, boost_temp
        """
        # Ambient temperature
        ambient = 25.0

        # Temperature rise based on load percentage
        load_percent = ac_power / (self.model.max_power_kw * 1000)
        temp_rise = load_percent * 30.0  # Up to 30°C rise at full load

        # Add small random variations
        inverter_temp = ambient + temp_rise + random.uniform(-2, 2)
        ipm_temp = inverter_temp + random.uniform(3, 7)  # IPM runs hotter
        boost_temp = inverter_temp + random.uniform(2, 5)  # Boost converter heat

        return {
            'inverter': round(inverter_temp, 1),
            'ipm': round(ipm_temp, 1),
            'boost': round(boost_temp, 1),
        }

    def _calculate_voltages(self) -> Dict[str, float]:
        """Calculate all voltage values.

        Returns:
            Dict with all voltage measurements
        """
        voltages = {}

        # PV string voltages (higher when generating, around MPP voltage)
        base_pv_voltage = 380.0  # Typical MPP voltage
        voltages['pv1'] = base_pv_voltage + random.uniform(-10, 10)
        voltages['pv2'] = base_pv_voltage + random.uniform(-10, 10)
        if self.model.has_pv3:
            voltages['pv3'] = base_pv_voltage + random.uniform(-10, 10)

        # AC voltage (grid voltage)
        if self.model.is_three_phase:
            # Three-phase voltages (230V phase, 400V line-to-line)
            voltages['ac_r'] = 230.0 + random.uniform(-5, 5)
            voltages['ac_s'] = 230.0 + random.uniform(-5, 5)
            voltages['ac_t'] = 230.0 + random.uniform(-5, 5)
            # Line-to-line voltages
            voltages['ac_rs'] = 400.0 + random.uniform(-8, 8)
            voltages['ac_st'] = 400.0 + random.uniform(-8, 8)
            voltages['ac_tr'] = 400.0 + random.uniform(-8, 8)
        else:
            # Single-phase voltage
            voltages['ac'] = 240.0 + random.uniform(-5, 5)

        # Battery voltage
        if self.model.has_battery:
            # Typical Li-ion: 48V nominal, varies with SOC
            base_voltage = 48.0
            # Voltage varies from ~45V (empty) to ~54V (full)
            voltages['battery'] = base_voltage + (self.battery_soc - 50) * 0.12 + random.uniform(-0.5, 0.5)

        # Backup voltage (for hybrid models)
        if self.model.has_battery:
            voltages['backup'] = 240.0 + random.uniform(-3, 3)

        return voltages

    def _calculate_currents(self, pv_power: Dict[str, float], ac_power: float, battery_power: float) -> Dict[str, float]:
        """Calculate all current values from power and voltage.

        Args:
            pv_power: PV power dict
            ac_power: AC output power
            battery_power: Battery power

        Returns:
            Dict with all current measurements
        """
        currents = {}
        voltages = self.values.get('voltages', self._calculate_voltages())

        # PV currents: I = P / V
        currents['pv1'] = pv_power['pv1'] / voltages['pv1'] if voltages['pv1'] > 0 else 0
        currents['pv2'] = pv_power['pv2'] / voltages['pv2'] if voltages['pv2'] > 0 else 0
        if self.model.has_pv3:
            currents['pv3'] = pv_power['pv3'] / voltages['pv3'] if voltages['pv3'] > 0 else 0

        # AC currents
        if self.model.is_three_phase:
            # Distribute power across 3 phases
            power_per_phase = ac_power / 3
            currents['ac_r'] = power_per_phase / voltages['ac_r'] if voltages['ac_r'] > 0 else 0
            currents['ac_s'] = power_per_phase / voltages['ac_s'] if voltages['ac_s'] > 0 else 0
            currents['ac_t'] = power_per_phase / voltages['ac_t'] if voltages['ac_t'] > 0 else 0
        else:
            currents['ac'] = ac_power / voltages['ac'] if voltages['ac'] > 0 else 0

        # Battery current
        if self.model.has_battery:
            currents['battery'] = battery_power / voltages['battery'] if voltages['battery'] > 0 else 0

        # Backup current
        if self.model.has_battery:
            # Assume load is on backup output
            currents['backup'] = self.house_load / voltages['backup'] if voltages['backup'] > 0 else 0

        return currents

    def _update_energy_totals(self, pv_power: Dict[str, float], battery_power: float, grid_power: Dict[str, float], dt: float) -> None:
        """Update energy totals.

        Args:
            pv_power: PV power dict
            battery_power: Battery power (W)
            grid_power: Grid power dict
            dt: Time delta in seconds
        """
        if dt <= 0:
            return

        # Convert to kWh: P(W) * t(s) / 3600 / 1000
        factor = dt / 3600000.0

        # PV energy generated
        pv_energy = pv_power['total'] * factor
        self.energy_today += pv_energy
        self.energy_total += pv_energy

        # Battery energy
        if battery_power > 0:
            # Charging
            energy = battery_power * factor
            self.battery_charge_today += energy
            self.battery_charge_total += energy
        elif battery_power < 0:
            # Discharging
            energy = abs(battery_power) * factor
            self.battery_discharge_today += energy
            self.battery_discharge_total += energy

        # Grid energy
        if grid_power['import'] > 0:
            energy = grid_power['import'] * factor
            self.grid_import_energy_today += energy
            self.grid_import_energy_total += energy
        if grid_power['export'] > 0:
            energy = grid_power['export'] * factor
            self.energy_to_grid_today += energy
            self.energy_to_grid_total += energy

        # Load energy (total consumption)
        load_energy = self.house_load * factor
        self.load_energy_today += load_energy
        self.load_energy_total += load_energy

    def _reset_daily_totals(self) -> None:
        """Reset daily energy totals at midnight."""
        self.energy_today = 0.0
        self.battery_charge_today = 0.0
        self.battery_discharge_today = 0.0
        self.grid_import_energy_today = 0.0
        self.energy_to_grid_today = 0.0
        self.load_energy_today = 0.0

    def _get_status(self) -> int:
        """Get inverter status code.

        Returns:
            Status code (0=Waiting, 1=Normal, 3=Fault, 5=Standby)
        """
        pv_power = self.values.get('pv_power', {}).get('total', 0)

        if pv_power < 50:
            return 0  # Waiting (night or low light)
        elif pv_power < 100:
            return 5  # Standby
        else:
            return 1  # Normal operation

    def get_register_value(self, register_type: str, address: int) -> Optional[int]:
        """Get raw register value for Modbus server.

        Args:
            register_type: 'input' or 'holding'
            address: Register address

        Returns:
            16-bit register value or None
        """
        # Get register definition
        if register_type == 'input':
            registers = self.model.get_input_registers()
        else:
            registers = self.model.get_holding_registers()

        if address not in registers:
            return None

        reg_def = registers[address]
        reg_name = reg_def['name']

        # Map register name to simulated value
        return self._map_register_to_value(reg_name, reg_def)

    def _map_register_to_value(self, reg_name: str, reg_def: Dict[str, Any]) -> int:
        """Map a register name to its simulated value.

        Args:
            reg_name: Register name
            reg_def: Register definition dict

        Returns:
            Raw 16-bit register value
        """
        scale = reg_def.get('scale', 1)
        is_signed = reg_def.get('signed', False)

        # Status
        if 'status' in reg_name:
            return self._get_status()

        # PV values
        elif reg_name == 'pv1_voltage':
            return round(self.values['voltages']['pv1'] / scale)
        elif reg_name == 'pv2_voltage':
            return round(self.values['voltages']['pv2'] / scale)
        elif reg_name == 'pv3_voltage' and self.model.has_pv3:
            return round(self.values['voltages']['pv3'] / scale)
        elif reg_name == 'pv1_current':
            return round(self.values['currents']['pv1'] / scale)
        elif reg_name == 'pv2_current':
            return round(self.values['currents']['pv2'] / scale)
        elif reg_name == 'pv3_current' and self.model.has_pv3:
            return round(self.values['currents']['pv3'] / scale)

        # PV power (32-bit pairs)
        elif 'pv1_power_high' in reg_name:
            combined_scale = reg_def.get('combined_scale', 0.1)
            power_raw = int(self.values['pv_power']['pv1'] / combined_scale)
            return (power_raw >> 16) & 0xFFFF
        elif 'pv1_power_low' in reg_name:
            combined_scale = reg_def.get('combined_scale', 0.1)
            power_raw = int(self.values['pv_power']['pv1'] / combined_scale)
            return power_raw & 0xFFFF
        elif 'pv2_power_high' in reg_name:
            combined_scale = reg_def.get('combined_scale', 0.1)
            power_raw = int(self.values['pv_power']['pv2'] / combined_scale)
            return (power_raw >> 16) & 0xFFFF
        elif 'pv2_power_low' in reg_name:
            combined_scale = reg_def.get('combined_scale', 0.1)
            power_raw = int(self.values['pv_power']['pv2'] / combined_scale)
            return power_raw & 0xFFFF
        elif 'pv3_power_high' in reg_name and self.model.has_pv3:
            combined_scale = reg_def.get('combined_scale', 0.1)
            power_raw = int(self.values['pv_power']['pv3'] / combined_scale)
            return (power_raw >> 16) & 0xFFFF
        elif 'pv3_power_low' in reg_name and self.model.has_pv3:
            combined_scale = reg_def.get('combined_scale', 0.1)
            power_raw = int(self.values['pv_power']['pv3'] / combined_scale)
            return power_raw & 0xFFFF
        elif 'pv_total_power_high' in reg_name:
            combined_scale = reg_def.get('combined_scale', 0.1)
            power_raw = int(self.values['pv_power']['total'] / combined_scale)
            return (power_raw >> 16) & 0xFFFF
        elif 'pv_total_power_low' in reg_name:
            combined_scale = reg_def.get('combined_scale', 0.1)
            power_raw = int(self.values['pv_power']['total'] / combined_scale)
            return power_raw & 0xFFFF

        # AC values
        elif reg_name == 'ac_voltage':
            return round(self.values['voltages']['ac'] / scale)
        elif reg_name == 'ac_current':
            return round(self.values['currents']['ac'] / scale)
        elif reg_name == 'ac_frequency':
            return round(50.0 / scale)  # 50 Hz
        elif 'ac_power_high' in reg_name:
            combined_scale = reg_def.get('combined_scale', 0.1)
            power_raw = int(self.values['ac_power'] / combined_scale)
            return (power_raw >> 16) & 0xFFFF
        elif 'ac_power_low' in reg_name:
            combined_scale = reg_def.get('combined_scale', 0.1)
            power_raw = int(self.values['ac_power'] / combined_scale)
            return power_raw & 0xFFFF

        # Three-phase AC
        elif reg_name in ['ac_voltage_r', 'ac_voltage_s', 'ac_voltage_t']:
            phase = reg_name.split('_')[-1]
            return round(self.values['voltages'][f'ac_{phase}'] / scale)
        elif reg_name in ['ac_current_r', 'ac_current_s', 'ac_current_t']:
            phase = reg_name.split('_')[-1]
            return round(self.values['currents'][f'ac_{phase}'] / scale)
        elif reg_name in ['ac_power_r', 'ac_power_s', 'ac_power_t']:
            phase = reg_name.split('_')[-1]
            power = self.values['ac_power'] / 3  # Distribute across phases
            return round(power / scale)
        # Three-phase AC power (32-bit pairs)
        elif reg_name in ['ac_power_r_high', 'ac_power_s_high', 'ac_power_t_high']:
            combined_scale = reg_def.get('combined_scale', 0.1)
            power = self.values['ac_power'] / 3  # Distribute across phases
            power_raw = int(power / combined_scale)
            return (power_raw >> 16) & 0xFFFF
        elif reg_name in ['ac_power_r_low', 'ac_power_s_low', 'ac_power_t_low']:
            combined_scale = reg_def.get('combined_scale', 0.1)
            power = self.values['ac_power'] / 3  # Distribute across phases
            power_raw = int(power / combined_scale)
            return power_raw & 0xFFFF
        elif reg_name in ['ac_voltage_rs', 'ac_voltage_st', 'ac_voltage_tr']:
            phases = reg_name.split('_')[-1]
            return round(self.values['voltages'][f'ac_{phases}'] / scale)

        # Battery
        elif reg_name == 'battery_voltage' and self.model.has_battery:
            return round(self.values['voltages']['battery'] / scale)
        elif reg_name == 'battery_current' and self.model.has_battery:
            current = self.values['currents']['battery']
            if is_signed:
                return self._to_signed_16bit(round(current / scale))
            return round(abs(current) / scale)
        elif reg_name == 'battery_power' and self.model.has_battery:
            power = self.values['battery_power']
            if is_signed:
                return self._to_signed_16bit(round(power / scale))
            return round(abs(power) / scale)
        elif reg_name == 'battery_soc' and self.model.has_battery:
            return round(self.battery_soc)
        elif reg_name == 'battery_temp' and self.model.has_battery:
            return round(30.0 / scale)  # Fixed battery temp

        # Temperatures
        elif reg_name == 'inverter_temp':
            return round(self.values['temperatures']['inverter'] / scale)
        elif reg_name == 'ipm_temp':
            return round(self.values['temperatures']['ipm'] / scale)
        elif reg_name == 'boost_temp':
            return round(self.values['temperatures']['boost'] / scale)

        # Energy (32-bit pairs)
        elif 'energy_today_high' in reg_name:
            combined_scale = reg_def.get('combined_scale', 0.1)
            energy_raw = int(self.energy_today / combined_scale)
            return (energy_raw >> 16) & 0xFFFF
        elif 'energy_today_low' in reg_name:
            combined_scale = reg_def.get('combined_scale', 0.1)
            energy_raw = int(self.energy_today / combined_scale)
            return energy_raw & 0xFFFF
        elif 'energy_total_high' in reg_name:
            combined_scale = reg_def.get('combined_scale', 0.1)
            energy_raw = int(self.energy_total / combined_scale)
            return (energy_raw >> 16) & 0xFFFF
        elif 'energy_total_low' in reg_name:
            combined_scale = reg_def.get('combined_scale', 0.1)
            energy_raw = int(self.energy_total / combined_scale)
            return energy_raw & 0xFFFF

        # Grid/load power
        elif 'grid_power' in reg_name or 'power_to_grid' in reg_name:
            # Handle 32-bit pairs for power_to_grid
            if '_high' in reg_name:
                combined_scale = reg_def.get('combined_scale', 0.1)
                # Positive = export, handle sign in 32-bit value
                power_raw = int(self.values['grid_power']['export'] / combined_scale)
                return (power_raw >> 16) & 0xFFFF
            elif '_low' in reg_name:
                combined_scale = reg_def.get('combined_scale', 0.1)
                power_raw = int(self.values['grid_power']['export'] / combined_scale)
                return power_raw & 0xFFFF
            else:
                # Single register
                power = self.values['grid_power']['grid']
                if is_signed:
                    return self._to_signed_16bit(round(power / scale))
                return round(abs(power) / scale)

        elif 'load_power' in reg_name or 'power_to_load' in reg_name:
            # Handle 32-bit pairs for power_to_load
            if '_high' in reg_name:
                combined_scale = reg_def.get('combined_scale', 0.1)
                power_raw = int(self.house_load / combined_scale)
                return (power_raw >> 16) & 0xFFFF
            elif '_low' in reg_name:
                combined_scale = reg_def.get('combined_scale', 0.1)
                power_raw = int(self.house_load / combined_scale)
                return power_raw & 0xFFFF
            else:
                # Single register
                return round(self.house_load / scale)

        # Battery charge/discharge power (SPH TL3 specific)
        elif reg_name == 'discharge_power_high' and self.model.has_battery:
            combined_scale = reg_def.get('combined_scale', 0.1)
            discharge = abs(min(0, self.values['battery_power']))  # Only negative values
            power_raw = int(discharge / combined_scale)
            return (power_raw >> 16) & 0xFFFF
        elif reg_name == 'discharge_power_low' and self.model.has_battery:
            combined_scale = reg_def.get('combined_scale', 0.1)
            discharge = abs(min(0, self.values['battery_power']))
            power_raw = int(discharge / combined_scale)
            return power_raw & 0xFFFF
        elif reg_name == 'charge_power_high' and self.model.has_battery:
            combined_scale = reg_def.get('combined_scale', 0.1)
            charge = max(0, self.values['battery_power'])  # Only positive values
            power_raw = int(charge / combined_scale)
            return (power_raw >> 16) & 0xFFFF
        elif reg_name == 'charge_power_low' and self.model.has_battery:
            combined_scale = reg_def.get('combined_scale', 0.1)
            charge = max(0, self.values['battery_power'])
            power_raw = int(charge / combined_scale)
            return power_raw & 0xFFFF

        # Power flow (SPH TL3 specific)
        elif 'power_to_user' in reg_name:
            # Power to user = PV - battery charge
            power_to_user = self.values['pv_power']['total'] - max(0, self.values['battery_power'])
            if '_high' in reg_name:
                combined_scale = reg_def.get('combined_scale', 0.1)
                power_raw = int(power_to_user / combined_scale)
                return (power_raw >> 16) & 0xFFFF
            elif '_low' in reg_name:
                combined_scale = reg_def.get('combined_scale', 0.1)
                power_raw = int(power_to_user / combined_scale)
                return power_raw & 0xFFFF

        # Self consumption (SPH TL3 specific)
        elif 'self_consumption_power' in reg_name:
            # Self consumption = load - grid import
            self_consumption = self.house_load - self.values['grid_power']['import']
            if '_high' in reg_name:
                combined_scale = reg_def.get('combined_scale', 0.1)
                power_raw = int(max(0, self_consumption) / combined_scale)
                return (power_raw >> 16) & 0xFFFF
            elif '_low' in reg_name:
                combined_scale = reg_def.get('combined_scale', 0.1)
                power_raw = int(max(0, self_consumption) / combined_scale)
                return power_raw & 0xFFFF
        elif reg_name == 'self_consumption_percentage':
            if self.house_load > 0:
                self_consumption = self.house_load - self.values['grid_power']['import']
                percentage = (max(0, self_consumption) / self.house_load) * 100
                return round(min(100, percentage))
            return 0

        # Energy to user/grid (SPH TL3 specific)
        elif 'energy_to_user' in reg_name:
            # Use the same as PV generation for now
            if 'today' in reg_name:
                if '_high' in reg_name:
                    combined_scale = reg_def.get('combined_scale', 0.1)
                    energy_raw = int(self.energy_today / combined_scale)
                    return (energy_raw >> 16) & 0xFFFF
                elif '_low' in reg_name:
                    combined_scale = reg_def.get('combined_scale', 0.1)
                    energy_raw = int(self.energy_today / combined_scale)
                    return energy_raw & 0xFFFF
            elif 'total' in reg_name:
                if '_high' in reg_name:
                    combined_scale = reg_def.get('combined_scale', 0.1)
                    energy_raw = int(self.energy_total / combined_scale)
                    return (energy_raw >> 16) & 0xFFFF
                elif '_low' in reg_name:
                    combined_scale = reg_def.get('combined_scale', 0.1)
                    energy_raw = int(self.energy_total / combined_scale)
                    return energy_raw & 0xFFFF

        elif 'energy_to_grid' in reg_name:
            if 'today' in reg_name:
                if '_high' in reg_name:
                    combined_scale = reg_def.get('combined_scale', 0.1)
                    energy_raw = int(self.energy_to_grid_today / combined_scale)
                    return (energy_raw >> 16) & 0xFFFF
                elif '_low' in reg_name:
                    combined_scale = reg_def.get('combined_scale', 0.1)
                    energy_raw = int(self.energy_to_grid_today / combined_scale)
                    return energy_raw & 0xFFFF
            elif 'total' in reg_name:
                if '_high' in reg_name:
                    combined_scale = reg_def.get('combined_scale', 0.1)
                    energy_raw = int(self.energy_to_grid_total / combined_scale)
                    return (energy_raw >> 16) & 0xFFFF
                elif '_low' in reg_name:
                    combined_scale = reg_def.get('combined_scale', 0.1)
                    energy_raw = int(self.energy_to_grid_total / combined_scale)
                    return energy_raw & 0xFFFF

        # Battery charge/discharge energy (SPH TL3 specific)
        elif 'discharge_energy' in reg_name and self.model.has_battery:
            if 'today' in reg_name:
                if '_high' in reg_name:
                    combined_scale = reg_def.get('combined_scale', 0.1)
                    energy_raw = int(self.battery_discharge_today / combined_scale)
                    return (energy_raw >> 16) & 0xFFFF
                elif '_low' in reg_name:
                    combined_scale = reg_def.get('combined_scale', 0.1)
                    energy_raw = int(self.battery_discharge_today / combined_scale)
                    return energy_raw & 0xFFFF
            elif 'total' in reg_name:
                if '_high' in reg_name:
                    combined_scale = reg_def.get('combined_scale', 0.1)
                    energy_raw = int(self.battery_discharge_total / combined_scale)
                    return (energy_raw >> 16) & 0xFFFF
                elif '_low' in reg_name:
                    combined_scale = reg_def.get('combined_scale', 0.1)
                    energy_raw = int(self.battery_discharge_total / combined_scale)
                    return energy_raw & 0xFFFF

        elif 'charge_energy' in reg_name and self.model.has_battery:
            if 'today' in reg_name:
                if '_high' in reg_name:
                    combined_scale = reg_def.get('combined_scale', 0.1)
                    energy_raw = int(self.battery_charge_today / combined_scale)
                    return (energy_raw >> 16) & 0xFFFF
                elif '_low' in reg_name:
                    combined_scale = reg_def.get('combined_scale', 0.1)
                    energy_raw = int(self.battery_charge_today / combined_scale)
                    return energy_raw & 0xFFFF
            elif 'total' in reg_name:
                if '_high' in reg_name:
                    combined_scale = reg_def.get('combined_scale', 0.1)
                    energy_raw = int(self.battery_charge_total / combined_scale)
                    return (energy_raw >> 16) & 0xFFFF
                elif '_low' in reg_name:
                    combined_scale = reg_def.get('combined_scale', 0.1)
                    energy_raw = int(self.battery_charge_total / combined_scale)
                    return energy_raw & 0xFFFF

        # Load energy (SPH TL3 specific)
        elif 'load_energy' in reg_name:
            if 'today' in reg_name:
                if '_high' in reg_name:
                    combined_scale = reg_def.get('combined_scale', 0.1)
                    energy_raw = int(self.load_energy_today / combined_scale)
                    return (energy_raw >> 16) & 0xFFFF
                elif '_low' in reg_name:
                    combined_scale = reg_def.get('combined_scale', 0.1)
                    energy_raw = int(self.load_energy_today / combined_scale)
                    return energy_raw & 0xFFFF
            elif 'total' in reg_name:
                if '_high' in reg_name:
                    combined_scale = reg_def.get('combined_scale', 0.1)
                    energy_raw = int(self.load_energy_total / combined_scale)
                    return (energy_raw >> 16) & 0xFFFF
                elif '_low' in reg_name:
                    combined_scale = reg_def.get('combined_scale', 0.1)
                    energy_raw = int(self.load_energy_total / combined_scale)
                    return energy_raw & 0xFFFF

        # System work mode
        elif reg_name == 'system_work_mode':
            return 1  # 1 = Normal operation

        # Battery type
        elif reg_name == 'battery_type':
            return 1  # 1 = Li-ion

        # Backup output
        elif reg_name == 'backup_voltage':
            return round(self.values['voltages'].get('backup', 240.0) / scale)
        elif reg_name == 'backup_current':
            return round(self.values['currents'].get('backup', 0) / scale)
        elif reg_name == 'backup_power':
            return round(self.house_load / scale)
        elif reg_name == 'backup_frequency':
            return round(50.0 / scale)

        # Default
        return 0

    def _to_signed_16bit(self, value: int) -> int:
        """Convert to signed 16-bit integer.

        Args:
            value: Integer value

        Returns:
            16-bit signed integer
        """
        if value < 0:
            return (1 << 16) + value
        return value & 0xFFFF

    def set_irradiance(self, irradiance: float) -> None:
        """Set solar irradiance (0-1000 W/m²)."""
        self.solar_irradiance = max(0, min(1000, irradiance))

    def set_cloud_cover(self, cover: float) -> None:
        """Set cloud cover (0-1)."""
        self.cloud_cover = max(0, min(1, cover))

    def set_house_load(self, load: float) -> None:
        """Set house load in watts."""
        self.house_load = max(0, load)

    def set_battery_override(self, power: Optional[float]) -> None:
        """Set battery override power (None for auto)."""
        self.battery_override = power

    def set_time_multiplier(self, multiplier: float) -> None:
        """Set time acceleration multiplier."""
        self.time_multiplier = max(0.1, min(100, multiplier))

    def toggle_pause(self) -> bool:
        """Toggle pause state.

        Returns:
            New pause state (True if now paused)
        """
        self.paused = not self.paused
        return self.paused

    def pause(self) -> None:
        """Pause the simulation."""
        self.paused = True

    def resume(self) -> None:
        """Resume the simulation."""
        self.paused = False
