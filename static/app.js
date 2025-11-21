// Dashboard JavaScript
let updateInterval = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeControls();
    startUpdates();
    loadRegisters();
});

// Initialize control sliders
function initializeControls() {
    const controls = {
        irradiance: document.getElementById('irradiance'),
        cloudCover: document.getElementById('cloudCover'),
        houseLoad: document.getElementById('houseLoad'),
        timeSpeed: document.getElementById('timeSpeed'),
    };

    // Update value displays
    Object.entries(controls).forEach(([key, element]) => {
        if (!element) return;

        const valueSpan = document.getElementById(`${key}Val`);
        element.addEventListener('input', () => {
            valueSpan.textContent = element.value;
        });

        element.addEventListener('change', async () => {
            await updateControl(key, parseFloat(element.value));
        });
    });

    // Reset energy button
    const resetBtn = document.getElementById('resetEnergy');
    if (resetBtn) {
        resetBtn.addEventListener('click', async () => {
            await updateControl('reset_energy', true);
        });
    }

    // Stop button
    const stopBtn = document.getElementById('stopBtn');
    if (stopBtn) {
        stopBtn.addEventListener('click', async () => {
            if (confirm('Stop the emulator?')) {
                await fetch('/api/stop', { method: 'POST' });
                window.location.href = '/';
            }
        });
    }
}

// Update control value
async function updateControl(key, value) {
    try {
        await fetch('/api/control', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                [key]: value
            })
        });
    } catch (error) {
        console.error('Error updating control:', error);
    }
}

// Start periodic updates
function startUpdates() {
    updateStatus();
    updateInterval = setInterval(updateStatus, 1000);
}

// Update dashboard status
async function updateStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();

        if (!response.ok) {
            console.error('Status update failed:', data.error);
            return;
        }

        updateDisplay(data);
        updateEnergyFlow(data);
    } catch (error) {
        console.error('Error fetching status:', error);
    }
}

// Update display values
function updateDisplay(data) {
    // Header
    setValue('time', data.time);
    setValue('status', data.status);

    // Solar
    setValue('solarValue', formatPower(data.solar.total_power));
    setValue('pv1Power', formatPower(data.solar.pv1_power));
    setValue('pv1Detail', `${data.solar.pv1_voltage.toFixed(1)}V / ${data.solar.pv1_current.toFixed(1)}A`);
    setValue('pv2Power', formatPower(data.solar.pv2_power));
    setValue('pv2Detail', `${data.solar.pv2_voltage.toFixed(1)}V / ${data.solar.pv2_current.toFixed(1)}A`);
    setValue('totalSolar', formatPower(data.solar.total_power));

    // AC
    setValue('inverterValue', formatPower(data.ac.power));
    setValue('acPower', formatPower(data.ac.power));
    setValue('acVoltage', `${data.ac.voltage.toFixed(1)} V`);
    setValue('acFrequency', `${data.ac.frequency.toFixed(1)} Hz`);

    // Grid
    const gridPower = data.grid.power;
    const gridText = gridPower > 0 ? `Export ${formatPower(gridPower)}` :
                    gridPower < 0 ? `Import ${formatPower(-gridPower)}` : '0 W';
    setValue('gridValue', gridText);

    // House
    setValue('houseValue', formatPower(data.load.power));

    // Battery (if equipped)
    if (data.battery) {
        setValue('batteryValue', `${data.battery.soc.toFixed(0)}%`);
        setValue('batterySoc', `${data.battery.soc.toFixed(0)}%`);
        setValue('batteryPower', formatPower(data.battery.power));
        setValue('batteryVoltage', `${data.battery.voltage.toFixed(1)} V`);
    }

    // Energy
    setValue('energyToday', `${data.energy.today.toFixed(1)} kWh`);
    setValue('energyTotal', `${data.energy.total.toFixed(1)} kWh`);
    setValue('gridToday', `${data.energy.to_grid_today.toFixed(1)} kWh`);

    // Temperatures
    setValue('tempInverter', `${data.temperatures.inverter.toFixed(0)}°C`);
    setValue('tempIpm', `${data.temperatures.ipm.toFixed(0)}°C`);
    setValue('tempBoost', `${data.temperatures.boost.toFixed(0)}°C`);

    // Update control values (without triggering events)
    setControlValue('irradiance', data.controls.irradiance);
    setControlValue('cloudCover', data.controls.cloud_cover);
    setControlValue('timeSpeed', data.controls.time_speed);
}

// Update energy flow diagram
function updateEnergyFlow(data) {
    const solarPower = data.solar.total_power;
    const gridPower = data.grid.power;
    const housePower = data.load.power;
    const batteryPower = data.battery ? data.battery.power : 0;

    // Update flow values
    setValue('flowSolarValue', formatPower(solarPower));

    if (gridPower > 0) {
        setValue('flowGridValue', `${formatPower(gridPower)} →`);
        updateArrow('flowInverterGrid', true);
    } else if (gridPower < 0) {
        setValue('flowGridValue', `← ${formatPower(-gridPower)}`);
        updateArrow('flowInverterGrid', false);
    } else {
        setValue('flowGridValue', '0 W');
    }

    setValue('flowHouseValue', formatPower(housePower));

    if (data.battery) {
        if (batteryPower > 0) {
            setValue('flowBatteryValue', `${formatPower(batteryPower)} ↓`);
        } else if (batteryPower < 0) {
            setValue('flowBatteryValue', `↑ ${formatPower(-batteryPower)}`);
        } else {
            setValue('flowBatteryValue', '0 W');
        }
    }

    // Update arrow thickness based on power
    updateArrowThickness('flowSolarInverter', solarPower);
    updateArrowThickness('flowInverterGrid', Math.abs(gridPower));
    updateArrowThickness('flowInverterHouse', housePower);
    if (data.battery) {
        updateArrowThickness('flowBattery', Math.abs(batteryPower));
    }

    // Update colors based on status
    updateStatusColor('solar', solarPower > 100);
    updateStatusColor('inverter', solarPower > 100);
    updateStatusColor('grid', Math.abs(gridPower) > 100);
    updateStatusColor('house', housePower > 0);
    if (data.battery) {
        updateStatusColor('battery', data.battery.soc > 10);
    }
}

// Load and display registers
async function loadRegisters() {
    try {
        const response = await fetch('/api/registers');
        const registers = await response.json();

        if (!response.ok) {
            console.error('Failed to load registers:', registers.error);
            return;
        }

        const registersList = document.getElementById('registersList');
        registersList.innerHTML = Object.values(registers)
            .map(reg => `
                <div class="register">
                    <div class="register-addr">${reg.address}</div>
                    <div class="register-name">${reg.name}</div>
                    <div class="register-value">${reg.scaled_value.toFixed(1)}</div>
                    <div class="register-unit">${reg.unit}</div>
                </div>
            `).join('');

    } catch (error) {
        console.error('Error loading registers:', error);
    }
}

// Helper functions
function setValue(id, value) {
    const element = document.getElementById(id);
    if (element) {
        element.textContent = value;
    }
}

function setControlValue(id, value) {
    const element = document.getElementById(id);
    const valueSpan = document.getElementById(`${id}Val`);

    if (element && element.value !== value.toString()) {
        element.value = value;
        if (valueSpan) {
            valueSpan.textContent = value;
        }
    }
}

function formatPower(watts) {
    if (watts >= 1000) {
        return `${(watts / 1000).toFixed(2)} kW`;
    }
    return `${watts.toFixed(0)} W`;
}

function updateArrow(id, forward) {
    const arrow = document.getElementById(id);
    if (arrow) {
        if (forward) {
            arrow.setAttribute('marker-end', 'url(#arrowhead)');
            arrow.setAttribute('marker-start', '');
        } else {
            arrow.setAttribute('marker-start', 'url(#arrowhead)');
            arrow.setAttribute('marker-end', '');
        }
    }
}

function updateArrowThickness(id, power) {
    const arrow = document.getElementById(id);
    if (arrow) {
        const thickness = Math.min(Math.max(power / 500, 2), 8);
        arrow.setAttribute('stroke-width', thickness);

        // Update opacity based on power
        const opacity = power > 100 ? 1 : 0.3;
        arrow.setAttribute('opacity', opacity);
    }
}

function updateStatusColor(id, active) {
    const element = document.getElementById(id);
    if (element) {
        element.style.opacity = active ? '1' : '0.5';
    }
}

// Clean up on page unload
window.addEventListener('beforeunload', () => {
    if (updateInterval) {
        clearInterval(updateInterval);
    }
});
