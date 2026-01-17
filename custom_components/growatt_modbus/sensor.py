"""Sensor platform for Growatt Modbus Integration."""
import logging
from datetime import datetime, timezone
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.helpers.entity import EntityCategory
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    CONF_INVERTER_SERIES,
    CONF_INVERT_GRID_POWER,
    get_device_type_for_sensor,
    get_entity_category,
)
from .coordinator import GrowattModbusCoordinator
from .device_profiles import get_sensors_for_profile

_LOGGER = logging.getLogger(__name__)


SENSOR_DEFINITIONS = {
    # Solar Input Sensors - PV1
    "pv1_voltage": {
        "name": "PV1 Voltage",
        "icon": "mdi:lightning-bolt",
        "device_class": SensorDeviceClass.VOLTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfElectricPotential.VOLT,
        "attr": "pv1_voltage",
    },
    "pv1_current": {
        "name": "PV1 Current", 
        "icon": "mdi:current-dc",
        "device_class": SensorDeviceClass.CURRENT,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfElectricCurrent.AMPERE,
        "attr": "pv1_current",
    },
    "pv1_power": {
        "name": "PV1 Power",
        "icon": "mdi:solar-panel",
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfPower.WATT,
        "attr": "pv1_power",
    },
    
    # Solar Input Sensors - PV2
    "pv2_voltage": {
        "name": "PV2 Voltage",
        "icon": "mdi:lightning-bolt",
        "device_class": SensorDeviceClass.VOLTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfElectricPotential.VOLT,
        "attr": "pv2_voltage",
    },
    "pv2_current": {
        "name": "PV2 Current",
        "icon": "mdi:current-dc", 
        "device_class": SensorDeviceClass.CURRENT,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfElectricCurrent.AMPERE,
        "attr": "pv2_current",
    },
    "pv2_power": {
        "name": "PV2 Power",
        "icon": "mdi:solar-panel",
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfPower.WATT,
        "attr": "pv2_power",
    },
    
    # Solar Input Sensors - PV3
    "pv3_voltage": {
        "name": "PV3 Voltage",
        "icon": "mdi:lightning-bolt",
        "device_class": SensorDeviceClass.VOLTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfElectricPotential.VOLT,
        "attr": "pv3_voltage",
        "condition": lambda data: data.pv3_voltage > 0 or data.pv3_power > 0,
    },
    "pv3_current": {
        "name": "PV3 Current",
        "icon": "mdi:current-dc", 
        "device_class": SensorDeviceClass.CURRENT,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfElectricCurrent.AMPERE,
        "attr": "pv3_current",
        "condition": lambda data: data.pv3_voltage > 0 or data.pv3_power > 0,
    },
    "pv3_power": {
        "name": "PV3 Power",
        "icon": "mdi:solar-panel",
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfPower.WATT,
        "attr": "pv3_power",
        "condition": lambda data: data.pv3_voltage > 0 or data.pv3_power > 0,
    },
    
    # Solar Total
    "pv_total_power": {
        "name": "Solar Total Power",
        "icon": "mdi:solar-power",
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfPower.WATT,
        "attr": "pv_total_power",
    },
    
    # AC Output Sensors
    "ac_voltage": {
        "name": "AC Voltage",
        "icon": "mdi:lightning-bolt",
        "device_class": SensorDeviceClass.VOLTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfElectricPotential.VOLT,
        "attr": "ac_voltage",
    },
    "ac_current": {
        "name": "AC Current",
        "icon": "mdi:current-ac",
        "device_class": SensorDeviceClass.CURRENT,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfElectricCurrent.AMPERE,
        "attr": "ac_current",
    },
    "ac_power": {
        "name": "AC Power",
        "icon": "mdi:power-plug",
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfPower.WATT,
        "attr": "ac_power",
    },
    "system_output_power": {
        "name": "System Output Power",
        "icon": "mdi:power-plug",
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfPower.WATT,
        "attr": "system_output_power",
    },
    "ac_frequency": {
        "name": "AC Frequency",
        "icon": "mdi:sine-wave",
        "device_class": SensorDeviceClass.FREQUENCY,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfFrequency.HERTZ,
        "attr": "ac_frequency",
    },

    # Three-Phase AC Voltages
    "ac_voltage_r": {
        "name": "AC Voltage R",
        "icon": "mdi:lightning-bolt",
        "device_class": SensorDeviceClass.VOLTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfElectricPotential.VOLT,
        "attr": "ac_voltage_r",
    },
    "ac_voltage_s": {
        "name": "AC Voltage S",
        "icon": "mdi:lightning-bolt",
        "device_class": SensorDeviceClass.VOLTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfElectricPotential.VOLT,
        "attr": "ac_voltage_s",
    },
    "ac_voltage_t": {
        "name": "AC Voltage T",
        "icon": "mdi:lightning-bolt",
        "device_class": SensorDeviceClass.VOLTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfElectricPotential.VOLT,
        "attr": "ac_voltage_t",
    },

    # Three-Phase AC Currents
    "ac_current_r": {
        "name": "AC Current Phase R",
        "icon": "mdi:current-ac",
        "device_class": SensorDeviceClass.CURRENT,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfElectricCurrent.AMPERE,
        "attr": "ac_current_r",
    },
    "ac_current_s": {
        "name": "AC Current Phase S",
        "icon": "mdi:current-ac",
        "device_class": SensorDeviceClass.CURRENT,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfElectricCurrent.AMPERE,
        "attr": "ac_current_s",
    },
    "ac_current_t": {
        "name": "AC Current Phase T",
        "icon": "mdi:current-ac",
        "device_class": SensorDeviceClass.CURRENT,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfElectricCurrent.AMPERE,
        "attr": "ac_current_t",
    },

    # Three-Phase AC Powers
    "ac_power_r": {
        "name": "AC Power Phase R",
        "icon": "mdi:power-plug",
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfPower.WATT,
        "attr": "ac_power_r",
    },
    "ac_power_s": {
        "name": "AC Power Phase S",
        "icon": "mdi:power-plug",
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfPower.WATT,
        "attr": "ac_power_s",
    },
    "ac_power_t": {
        "name": "AC Power Phase T",
        "icon": "mdi:power-plug",
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfPower.WATT,
        "attr": "ac_power_t",
    },
    
    # Grid Power Sensors
    "grid_power": {
        "name": "Grid Power",
        "icon": "mdi:transmission-tower",
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfPower.WATT,
        "attr": "calculated",
    },
    "grid_export_power": {
        "name": "Grid Export Power",
        "icon": "mdi:transmission-tower-export",
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfPower.WATT,
        "attr": "calculated",
    },
    "grid_import_power": {
        "name": "Grid Import Power",
        "icon": "mdi:transmission-tower-import", 
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfPower.WATT,
        "attr": "calculated",
    },
    
    # Power Flow Sensors (from registers - storage/hybrid models)
    "power_to_grid": {
        "name": "Power to Grid",
        "icon": "mdi:transmission-tower-export",
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfPower.WATT,
        "attr": "power_to_grid",
        "condition": lambda data: data.power_to_grid > 0,
    },
    "power_to_load": {
        "name": "Power to Load",
        "icon": "mdi:home-lightning-bolt",
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfPower.WATT,
        "attr": "power_to_load",
        "condition": lambda data: data.power_to_load > 0,
    },
    "power_to_user": {
        "name": "Power to User",
        "icon": "mdi:home-import-outline",
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfPower.WATT,
        "attr": "power_to_user",
        "condition": lambda data: data.power_to_user > 0,
    },
    
    # Consumption Sensors
    "self_consumption": {
        "name": "Self Consumption",
        "icon": "mdi:home-lightning-bolt-outline",
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfPower.WATT,
        "attr": "calculated",
    },
    "self_consumption_percentage": {
        "name": "Self Consumption Percentage",
        "icon": "mdi:percent",
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": PERCENTAGE,
        "attr": "calculated",
    },
    "house_consumption": {
        "name": "House Consumption",
        "icon": "mdi:home-lightning-bolt",
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfPower.WATT,
        "attr": "calculated",
    },
    
    # Energy Sensors
    "energy_today": {
        "name": "Energy Today",
        "icon": "mdi:calendar-today",
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "unit": UnitOfEnergy.KILO_WATT_HOUR,
        "attr": "energy_today",
    },
    "energy_total": {
        "name": "Energy Total",
        "icon": "mdi:counter",
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "unit": UnitOfEnergy.KILO_WATT_HOUR,
        "attr": "energy_total",
    },
    
    # Energy Breakdown (storage/hybrid models)
    "grid_energy_today": {
        "name": "Grid Energy Today",
        "icon": "mdi:transmission-tower",
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.TOTAL,
        "unit": UnitOfEnergy.KILO_WATT_HOUR,
        "attr": "calculated",
        "condition": lambda data: data.load_energy_today > 0 or data.energy_to_grid_today > 0,
    },
    "grid_energy_total": {
        "name": "Grid Energy Total",
        "icon": "mdi:transmission-tower",
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.TOTAL,
        "unit": UnitOfEnergy.KILO_WATT_HOUR,
        "attr": "calculated",
        "condition": lambda data: data.load_energy_total > 0 or data.energy_to_grid_total > 0,
    },
    "energy_to_grid_today": {
        "name": "Energy to Grid Today",
        "icon": "mdi:transmission-tower-export",
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "unit": UnitOfEnergy.KILO_WATT_HOUR,
        "attr": "energy_to_grid_today",
        "condition": lambda data: data.energy_to_grid_today > 0,
    },
    "energy_to_grid_total": {
        "name": "Energy to Grid Total",
        "icon": "mdi:transmission-tower-export",
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "unit": UnitOfEnergy.KILO_WATT_HOUR,
        "attr": "energy_to_grid_total",
        "condition": lambda data: data.energy_to_grid_total > 0,
    },
    "grid_import_energy_today": {
        "name": "Grid Import Energy Today",
        "icon": "mdi:transmission-tower-import",
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "unit": UnitOfEnergy.KILO_WATT_HOUR,
        "attr": "calculated",
        "condition": lambda data: data.load_energy_today > 0,
    },
    "grid_import_energy_total": {
        "name": "Grid Import Energy Total",
        "icon": "mdi:transmission-tower-import",
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "unit": UnitOfEnergy.KILO_WATT_HOUR,
        "attr": "calculated",
        "condition": lambda data: data.load_energy_total > 0,
    },
    "load_energy_today": {
        "name": "Load Energy Today",
        "icon": "mdi:home-lightning-bolt",
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "unit": UnitOfEnergy.KILO_WATT_HOUR,
        "attr": "load_energy_today",
        "condition": lambda data: data.load_energy_today > 0,
    },
    "load_energy_total": {
        "name": "Load Energy Total",
        "icon": "mdi:home-lightning-bolt",
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "unit": UnitOfEnergy.KILO_WATT_HOUR,
        "attr": "load_energy_total",
        "condition": lambda data: data.load_energy_total > 0,
    },
    
    # Temperature Sensors
    "inverter_temp": {
        "name": "Inverter Temperature",
        "icon": "mdi:thermometer",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfTemperature.CELSIUS,
        "attr": "inverter_temp",
    },
    "ipm_temp": {
        "name": "IPM Temperature",
        "icon": "mdi:thermometer",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfTemperature.CELSIUS,
        "attr": "ipm_temp",
        "condition": lambda data: data.ipm_temp > 0,
    },
    "boost_temp": {
        "name": "Boost Temperature",
        "icon": "mdi:thermometer",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfTemperature.CELSIUS,
        "attr": "boost_temp",
        "condition": lambda data: data.boost_temp > 0,
    },
    "dcdc_temp": {
        "name": "DC-DC Temperature",
        "icon": "mdi:thermometer",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfTemperature.CELSIUS,
        "attr": "dcdc_temp",
        "condition": lambda data: hasattr(data, 'dcdc_temp') and data.dcdc_temp > 0,
    },
    "buck1_temp": {
        "name": "Buck1 Temperature",
        "icon": "mdi:thermometer",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfTemperature.CELSIUS,
        "attr": "buck1_temp",
        "condition": lambda data: hasattr(data, 'buck1_temp'),
    },
    "buck2_temp": {
        "name": "Buck2 Temperature",
        "icon": "mdi:thermometer",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfTemperature.CELSIUS,
        "attr": "buck2_temp",
        "condition": lambda data: hasattr(data, 'buck2_temp'),
    },

    # Battery Sensors
    "battery_voltage": {
        "name": "Battery Voltage",
        "icon": "mdi:battery-charging",
        "device_class": SensorDeviceClass.VOLTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfElectricPotential.VOLT,
        "attr": "battery_voltage",
        "condition": lambda data: data.battery_voltage > 0,
    },
    "battery_current": {
        "name": "Battery Current",
        "icon": "mdi:current-dc",
        "device_class": SensorDeviceClass.CURRENT,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfElectricCurrent.AMPERE,
        "attr": "battery_current",
        "condition": lambda data: hasattr(data, 'battery_current') and data.battery_voltage > 0,
    },
    "battery_soc": {
        "name": "Battery SOC",
        "icon": "mdi:battery",
        "device_class": SensorDeviceClass.BATTERY,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": PERCENTAGE,
        "attr": "battery_soc",
        "condition": lambda data: data.battery_soc > 0,
    },
    "battery_temp": {
        "name": "Battery Temperature",
        "icon": "mdi:thermometer",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfTemperature.CELSIUS,
        "attr": "battery_temp",
        "condition": lambda data: hasattr(data, 'battery_temp'),
    },
    "battery_power": {
        "name": "Battery Power",
        "icon": "mdi:battery-charging",
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfPower.WATT,
        "attr": "calculated",
    },
    "battery_charge_power": {
        "name": "Battery Charge Power",
        "icon": "mdi:battery-plus",
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfPower.WATT,
        "attr": "charge_power",
        "condition": lambda data: hasattr(data, 'charge_power'),
    },
    "battery_discharge_power": {
        "name": "Battery Discharge Power",
        "icon": "mdi:battery-minus",
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfPower.WATT,
        "attr": "discharge_power",
        "condition": lambda data: hasattr(data, 'discharge_power'),
    },
    "battery_charge_today": {
        "name": "Battery Charge Today",
        "icon": "mdi:battery-plus",
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "unit": UnitOfEnergy.KILO_WATT_HOUR,
        "attr": "charge_energy_today",
        "condition": lambda data: hasattr(data, 'charge_energy_today') and data.charge_energy_today > 0,
    },
    "battery_discharge_today": {
        "name": "Battery Discharge Today",
        "icon": "mdi:battery-minus",
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "unit": UnitOfEnergy.KILO_WATT_HOUR,
        "attr": "discharge_energy_today",
        "condition": lambda data: hasattr(data, 'discharge_energy_today') and data.discharge_energy_today > 0,
    },
    "battery_charge_total": {
        "name": "Battery Charge Total",
        "icon": "mdi:battery-plus",
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "unit": UnitOfEnergy.KILO_WATT_HOUR,
        "attr": "charge_energy_total",
        "condition": lambda data: hasattr(data, 'charge_energy_total') and data.charge_energy_total > 0,
    },
    "battery_discharge_total": {
        "name": "Battery Discharge Total",
        "icon": "mdi:battery-minus",
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "unit": UnitOfEnergy.KILO_WATT_HOUR,
        "attr": "discharge_energy_total",
        "condition": lambda data: hasattr(data, 'discharge_energy_total') and data.discharge_energy_total > 0,
    },
    "ac_charge_energy_today": {
        "name": "AC Charge Energy Today",
        "icon": "mdi:battery-charging-50",
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "unit": UnitOfEnergy.KILO_WATT_HOUR,
        "attr": "ac_charge_energy_today",
        "condition": lambda data: hasattr(data, 'ac_charge_energy_today') and data.ac_charge_energy_today > 0,
    },
    "ac_discharge_energy_today": {
        "name": "AC Discharge Energy Today",
        "icon": "mdi:battery-charging-outline",
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "unit": UnitOfEnergy.KILO_WATT_HOUR,
        "attr": "ac_discharge_energy_today",
        "condition": lambda data: hasattr(data, 'ac_discharge_energy_today') and data.ac_discharge_energy_today > 0,
    },

    # System Sensors
    "status": {
        "name": "Status",
        "icon": "mdi:information",
        "attr": "status",
    },
    "last_update": {
        "name": "Last Update",
        "icon": "mdi:clock-outline",
        "device_class": SensorDeviceClass.TIMESTAMP,
        "attr": "calculated",
    },
    "derating_mode": {
        "name": "Derating Mode",
        "icon": "mdi:speedometer-slow",
        "attr": "derating_mode",
        "condition": lambda data: data.derating_mode > 0,
    },
    "fault_code": {
        "name": "Fault Code",
        "icon": "mdi:alert-circle",
        "attr": "fault_code",
        "condition": lambda data: data.fault_code > 0,
    },
    "warning_code": {
        "name": "Warning Code",
        "icon": "mdi:alert",
        "attr": "warning_code",
        "condition": lambda data: data.warning_code > 0,
    },

    # Load Sensors (SPF Off-Grid)
    "load_percentage": {
        "name": "Load Percentage",
        "icon": "mdi:gauge",
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": PERCENTAGE,
        "attr": "load_percentage",
        "condition": lambda data: hasattr(data, 'load_percentage'),
    },

    # Fan Speed Sensors (SPF Off-Grid)
    "mppt_fan_speed": {
        "name": "MPPT Fan Speed",
        "icon": "mdi:fan",
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": PERCENTAGE,
        "attr": "mppt_fan_speed",
        "condition": lambda data: hasattr(data, 'mppt_fan_speed'),
    },
    "inverter_fan_speed": {
        "name": "Inverter Fan Speed",
        "icon": "mdi:fan",
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": PERCENTAGE,
        "attr": "inverter_fan_speed",
        "condition": lambda data: hasattr(data, 'inverter_fan_speed'),
    },
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Growatt Modbus sensors."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    # Wait for first data to determine which sensors to create
    if coordinator.data is None:
        _LOGGER.warning("No data available from coordinator during sensor setup")
        return
    
    # Get the inverter series profile
    inverter_series = config_entry.data.get(CONF_INVERTER_SERIES, "min_7000_10000_tl_x")
    available_sensors = get_sensors_for_profile(inverter_series)
    
    _LOGGER.info(
        "Setting up sensors for %s - %d sensors available in profile",
        inverter_series,
        len(available_sensors)
    )
    
    entities = []
    
    # Create sensors based on available data and conditions
    for sensor_key, sensor_def in SENSOR_DEFINITIONS.items():
        # Check if sensor is supported by this inverter profile
        if sensor_key not in available_sensors:
            _LOGGER.debug("Skipping sensor %s - not in profile %s", sensor_key, inverter_series)
            continue
        
        # Check if sensor should be created based on condition
        if "condition" in sensor_def:
            try:
                if not sensor_def["condition"](coordinator.data):
                    _LOGGER.debug("Skipping sensor %s - condition not met", sensor_key)
                    continue
            except (AttributeError, TypeError) as e:
                _LOGGER.debug("Skipping sensor %s - error checking condition: %s", sensor_key, e)
                continue
        
        entities.append(
            GrowattModbusSensor(
                coordinator,
                config_entry,
                sensor_key,
                sensor_def,
            )
        )
    
    _LOGGER.info("Created %d sensors for %s", len(entities), inverter_series)
    async_add_entities(entities)


class GrowattModbusSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Growatt Modbus sensor."""

    def __init__(
        self,
        coordinator: GrowattModbusCoordinator,
        config_entry: ConfigEntry,
        sensor_key: str,
        sensor_def: dict[str, Any],
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

        self._config_entry = config_entry
        self._sensor_key = sensor_key
        self._sensor_def = sensor_def
        self._attr_name = f"{config_entry.data['name']} {sensor_def['name']}"
        self._attr_unique_id = f"{config_entry.entry_id}_{sensor_key}"

        # Determine which device this sensor belongs to
        self._device_type = get_device_type_for_sensor(sensor_key)

        # Set entity category (None for main sensors, "diagnostic" for technical details)
        entity_category = get_entity_category(sensor_key)
        if entity_category == "diagnostic":
            self._attr_entity_category = EntityCategory.DIAGNOSTIC

        # Set sensor attributes based on definition
        if "device_class" in sensor_def:
            self._attr_device_class = sensor_def["device_class"]
        if "state_class" in sensor_def:
            self._attr_state_class = sensor_def["state_class"]
        if "unit" in sensor_def:
            self._attr_native_unit_of_measurement = sensor_def["unit"]
        if "icon" in sensor_def:
            self._attr_icon = sensor_def["icon"]

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return self.coordinator.get_device_info(self._device_type)

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None
        
        data = self.coordinator.data
        
        # Get invert grid power option
        invert_grid_power = self._config_entry.options.get(CONF_INVERT_GRID_POWER, False)
        
        # Special handling for calculated sensors
        if self._sensor_def.get("attr") == "calculated":
            if self._sensor_key == "grid_power":
                # Bidirectional grid power (signed value)
                # Positive = export, Negative = import
                export = getattr(data, "power_to_grid", 0)
                solar = getattr(data, "pv_total_power", 0)
                load = getattr(data, "power_to_load", 0)
                charge = getattr(data, "charge_power", 0)
                discharge = getattr(data, "discharge_power", 0)
                
                # Prefer inverter grid register (signed). When it's 0 or unavailable,
                # fall back to net flow: (solar + battery discharge) - (load + battery charge)
                grid_power = export if export != 0 else (solar + discharge) - (load + charge)
                
                # Apply inversion if configured (CT clamp backwards)
                if invert_grid_power:
                    grid_power = -grid_power
                
                raw_value = round(grid_power, 1)
                
                # Apply offline behavior
                return self.coordinator.get_sensor_value(self._sensor_key, raw_value)
                
            elif self._sensor_key == "grid_export_power":
                # Export power (always positive or 0)
                export = getattr(data, "power_to_grid", 0)
                solar = getattr(data, "pv_total_power", 0)
                load = getattr(data, "power_to_load", 0)
                charge = getattr(data, "charge_power", 0)
                discharge = getattr(data, "discharge_power", 0)

                # Calculate grid power (IEC standard: positive = export)
                grid_power = export if export != 0 else (solar + discharge) - (load + charge)

                # Apply inversion if configured (for HA convention: negative = export)
                if invert_grid_power:
                    grid_power = -grid_power

                # After inversion for HA: negative = export, so take negative part and make positive
                raw_value = round(max(0, -grid_power), 1)
                return self.coordinator.get_sensor_value(self._sensor_key, raw_value)

            elif self._sensor_key == "grid_import_power":
                # Import power (always positive or 0)
                export = getattr(data, "power_to_grid", 0)
                solar = getattr(data, "pv_total_power", 0)
                load = getattr(data, "power_to_load", 0)
                charge = getattr(data, "charge_power", 0)
                discharge = getattr(data, "discharge_power", 0)

                # Calculate grid power (IEC standard: positive = export)
                grid_power = export if export != 0 else (solar + discharge) - (load + charge)

                # Apply inversion if configured (for HA convention: positive = import)
                if invert_grid_power:
                    grid_power = -grid_power

                # After inversion for HA: positive = import, so take positive part
                raw_value = round(max(0, grid_power), 1)
                return self.coordinator.get_sensor_value(self._sensor_key, raw_value)
                
            elif self._sensor_key == "self_consumption":
                # Self consumption = solar used directly
                solar = getattr(data, "pv_total_power", 0)
                export = getattr(data, "power_to_grid", 0)
                load = getattr(data, "power_to_load", 0)
                
                if export > 0:
                    self_consumption = solar - export
                elif load > 0:
                    self_consumption = min(solar, load)
                else:
                    self_consumption = solar
                
                raw_value = round(max(0, self_consumption), 1)
                return self.coordinator.get_sensor_value(self._sensor_key, raw_value)
            
            elif self._sensor_key == "self_consumption_percentage":
                # Percentage of solar self-consumed
                solar = getattr(data, "pv_total_power", 0)
                export = getattr(data, "power_to_grid", 0)
                load = getattr(data, "power_to_load", 0)
                
                if solar == 0:
                    raw_value = 0
                else:
                    if export > 0:
                        self_consumption = solar - export
                    elif load > 0:
                        self_consumption = min(solar, load)
                    else:
                        self_consumption = solar
                    
                    percentage = (max(0, self_consumption) / solar) * 100
                    raw_value = round(percentage, 1)
                
                return self.coordinator.get_sensor_value(self._sensor_key, raw_value)
                
            elif self._sensor_key == "house_consumption":
                # House consumption
                load = getattr(data, "power_to_load", 0)
                
                if load == 0:
                    solar = getattr(data, "pv_total_power", 0)
                    export = getattr(data, "power_to_grid", 0)
                    if export > 0:
                        load = max(0, solar - export)
                    else:
                        load = solar
                
                raw_value = round(max(0, load), 1)
                return self.coordinator.get_sensor_value(self._sensor_key, raw_value)
            
            elif self._sensor_key == "battery_power":
                # Battery power: positive = charging, negative = discharging
                charge_power = getattr(data, "charge_power", 0)
                discharge_power = getattr(data, "discharge_power", 0)
                
                if charge_power > 0:
                    raw_value = round(charge_power, 1)  # Positive for charging
                elif discharge_power > 0:
                    raw_value = round(-discharge_power, 1)  # Negative for discharging
                else:
                    raw_value = 0
                
                return self.coordinator.get_sensor_value(self._sensor_key, raw_value)
            
            
            elif self._sensor_key == "grid_energy_today":
                # Combined grid energy: positive=export, negative=import
                # Net grid energy = export - import
                export_energy = getattr(data, "energy_to_grid_today", 0)
                load_energy = getattr(data, "load_energy_today", 0)
                solar_energy = getattr(data, "energy_today", 0)
                
                # Import = load - solar + export
                import_energy = max(0, load_energy - solar_energy + export_energy)
                
                # Net: positive when more export than import
                net_energy = export_energy - import_energy
                
                # Apply inversion if configured
                if invert_grid_power:
                    net_energy = -net_energy
                
                raw_value = round(net_energy, 2)
                return self.coordinator.get_sensor_value(self._sensor_key, raw_value)
            
            elif self._sensor_key == "grid_energy_total":
                # Combined grid energy: positive=export, negative=import
                # Net grid energy = export - import
                export_energy = getattr(data, "energy_to_grid_total", 0)
                load_energy = getattr(data, "load_energy_total", 0)
                solar_energy = getattr(data, "energy_total", 0)
                
                # Import = load - solar + export
                import_energy = max(0, load_energy - solar_energy + export_energy)
                
                # Net: positive when more export than import
                net_energy = export_energy - import_energy
                
                # Apply inversion if configured
                if invert_grid_power:
                    net_energy = -net_energy
                
                raw_value = round(net_energy, 2)
                return self.coordinator.get_sensor_value(self._sensor_key, raw_value)

            elif self._sensor_key == "grid_import_energy_today":
                # Grid import energy - must be calculated for most inverters
                # Only inverters with separate hardware import registers can use inversion shortcut

                # Check if inverter has hardware import energy register
                has_hardware_import = hasattr(data, "energy_from_grid_today")

                if invert_grid_power and has_hardware_import:
                    # CT clamp backwards AND inverter has hardware import register
                    raw_value = getattr(data, "energy_to_grid_today", 0)
                else:
                    # Always calculate for inverters without hardware import registers (MIN, etc.)
                    # Or calculate normally when inversion is off
                    load_energy = getattr(data, "load_energy_today", 0)
                    solar_energy = getattr(data, "energy_today", 0)
                    export_energy = getattr(data, "energy_to_grid_today", 0)
                    raw_value = max(0, load_energy - solar_energy + export_energy)

                raw_value = round(raw_value, 2)
                return self.coordinator.get_sensor_value(self._sensor_key, raw_value)

            elif self._sensor_key == "grid_import_energy_total":
                # Grid import energy - must be calculated for most inverters
                # Only inverters with separate hardware import registers can use inversion shortcut

                # Check if inverter has hardware import energy register
                has_hardware_import = hasattr(data, "energy_from_grid_total")

                if invert_grid_power and has_hardware_import:
                    # CT clamp backwards AND inverter has hardware import register
                    raw_value = getattr(data, "energy_to_grid_total", 0)
                else:
                    # Always calculate for inverters without hardware import registers (MIN, etc.)
                    # Or calculate normally when inversion is off
                    load_energy = getattr(data, "load_energy_total", 0)
                    solar_energy = getattr(data, "energy_total", 0)
                    export_energy = getattr(data, "energy_to_grid_total", 0)
                    raw_value = max(0, load_energy - solar_energy + export_energy)

                raw_value = round(raw_value, 2)
                return self.coordinator.get_sensor_value(self._sensor_key, raw_value)
            
            elif self._sensor_key == "last_update":
                # Get the last successful update time from coordinator
                if hasattr(self.coordinator, 'last_update_success_time') and self.coordinator.last_update_success_time:
                    # Make sure datetime is timezone-aware (UTC)
                    dt = self.coordinator.last_update_success_time
                    if dt.tzinfo is None:
                        # If naive datetime, assume UTC and make it aware
                        dt = dt.replace(tzinfo=timezone.utc)
                    return dt
                return None
            
            return None
        
        # Regular sensor - get value from data attribute
        value = getattr(data, self._sensor_def["attr"], None)
        
        if value is None:
            return None
        
        # Special handling for status sensor
        if self._sensor_key == "status":
            from .const import STATUS_CODES

            # If offline, show "Offline"
            if not self.coordinator.is_online:
                return "Offline"

            status_info = STATUS_CODES.get(value, {"name": f"Unknown ({value})"})
            return status_info["name"]

        # Special handling for derating_mode sensor
        if self._sensor_key == "derating_mode":
            from .const import get_derating_name
            return get_derating_name(int(value))

        # Round numeric values to reasonable precision
        if isinstance(value, float):
            if self._sensor_def.get("unit") == UnitOfPower.WATT:
                raw_value = round(value, 1)
            elif self._sensor_def.get("unit") == UnitOfElectricPotential.VOLT:
                raw_value = round(value, 1)
            elif self._sensor_def.get("unit") == UnitOfElectricCurrent.AMPERE:
                raw_value = round(value, 2)
            elif self._sensor_def.get("unit") == UnitOfFrequency.HERTZ:
                raw_value = round(value, 2)
            elif self._sensor_def.get("unit") == UnitOfTemperature.CELSIUS:
                raw_value = round(value, 1)
            elif self._sensor_def.get("unit") == UnitOfEnergy.KILO_WATT_HOUR:
                raw_value = round(value, 2)
            else:
                raw_value = value
        else:
            raw_value = value
        
        # Apply offline behavior for this sensor
        return self.coordinator.get_sensor_value(self._sensor_key, raw_value)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional state attributes."""
        # No attributes on sensors - all info is in device_info or other sensors
        return None
