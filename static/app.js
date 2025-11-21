// Dashboard JavaScript
let updateInterval = null;
let currentCapabilities = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeControls();
    startUpdates();
    loadRegisters();
    initializeModelSwitcher();
});

// Initialize model switcher
function initializeModelSwitcher() {
    const switchBtn = document.getElementById('switchBtn');
    const modelSelect = document.getElementById('modelSwitcher');
    const protocolSelect = document.getElementById('protocolSwitcher');

    if (switchBtn) {
        switchBtn.addEventListener('click', async () => {
            const profileKey = modelSelect.value;
            const protocol = protocolSelect.value;

            if (confirm(`Switch to ${modelSelect.options[modelSelect.selectedIndex].text} (${protocol.toUpperCase()})?`)) {
                switchBtn.disabled = true;
                switchBtn.textContent = 'Switching...';

                try {
                    const response = await fetch('/api/switch_model', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            profile_key: profileKey,
                            protocol_version: protocol,
                            port: 5020
                        })
                    });

                    const data = await response.json();

                    if (response.ok) {
                        console.log(`Switched to ${data.model}`);
                        // Update will be reflected on next status poll
                        setTimeout(() => {
                            switchBtn.disabled = false;
                            switchBtn.textContent = 'Switch Model';
                        }, 2000);
                    } else {
                        alert(`Error: ${data.error}`);
                        switchBtn.disabled = false;
                        switchBtn.textContent = 'Switch Model';
                    }
                } catch (error) {
                    alert(`Error: ${error.message}`);
                    switchBtn.disabled = false;
                    switchBtn.textContent = 'Switch Model';
                }
            }
        });
    }
}

// Initialize control sliders
function initializeControls() {
    const controls = {
        irradiance: document.getElementById('irradiance'),
        cloudCover: document.getElementById('cloudCover'),
        houseLoad: document.getElementById('houseLoad'),
        timeSpeed: document.getElementById('timeSpeed'),
        timeOfDay: document.getElementById('timeOfDay'),
    };

    // Update value displays
    Object.entries(controls).forEach(([key, element]) => {
        if (!element) return;

        const valueSpan = document.getElementById(`${key}Val`);
        element.addEventListener('input', () => {
            if (key === 'timeOfDay') {
                const hours = Math.floor(parseFloat(element.value));
                const minutes = Math.round((parseFloat(element.value) % 1) * 60);
                valueSpan.textContent = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
            } else {
                valueSpan.textContent = element.value;
            }
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
    // Store capabilities
    currentCapabilities = data.capabilities;

    // Update model name
    setValue('modelName', data.model);

    // Update model/protocol selectors
    const modelSelect = document.getElementById('modelSwitcher');
    const protocolSelect = document.getElementById('protocolSwitcher');
    if (modelSelect && data.profile_key) {
        modelSelect.value = data.profile_key;
    }
    if (protocolSelect && data.capabilities) {
        protocolSelect.value = data.capabilities.protocol_version;
    }

    // Apply capability-based visibility
    updateFeatureVisibility(data.capabilities);

    // Header
    setValue('time', data.time);
    setValue('status', data.status);

    // Solar
    setValue('solarValue', formatPower(data.solar.total_power));
    setValue('pv1Power', formatPower(data.solar.pv1_power));
    setValue('pv1Detail', `${data.solar.pv1_voltage.toFixed(1)}V / ${data.solar.pv1_current.toFixed(1)}A`);
    setValue('pv2Power', formatPower(data.solar.pv2_power));
    setValue('pv2Detail', `${data.solar.pv2_voltage.toFixed(1)}V / ${data.solar.pv2_current.toFixed(1)}A`);

    // PV3 (only if available)
    if (data.solar.pv3_power !== null) {
        setValue('pv3Power', formatPower(data.solar.pv3_power));
        setValue('pv3Detail', `${data.solar.pv3_voltage.toFixed(1)}V / ${data.solar.pv3_current.toFixed(1)}A`);
    }

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

    // Update time of day slider
    if (data.time_hour !== undefined) {
        const timeOfDayInput = document.getElementById('timeOfDay');
        const timeOfDayVal = document.getElementById('timeOfDayVal');
        if (timeOfDayInput && timeOfDayInput.value !== data.time_hour.toString()) {
            timeOfDayInput.value = data.time_hour;
            if (timeOfDayVal) {
                const hours = Math.floor(data.time_hour);
                const minutes = Math.round((data.time_hour % 1) * 60);
                timeOfDayVal.textContent = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
            }
        }
    }
}

// Update feature visibility based on capabilities
function updateFeatureVisibility(capabilities) {
    if (!capabilities) return;

    // PV3 visibility
    const pv3Sensor = document.getElementById('pv3Sensor');
    if (pv3Sensor) {
        if (capabilities.has_pv3) {
            pv3Sensor.classList.remove('disabled');
        } else {
            pv3Sensor.classList.add('disabled');
        }
    }

    // Battery sensor visibility
    const batterySensor = document.getElementById('batterySensor');
    if (batterySensor) {
        if (capabilities.has_battery) {
            batterySensor.classList.remove('disabled');
        } else {
            batterySensor.classList.add('disabled');
        }
    }

    // Battery card visibility
    const batteryCards = document.querySelectorAll('.card:has(#batterySoc)');
    batteryCards.forEach(card => {
        if (capabilities.has_battery) {
            card.style.display = 'block';
        } else {
            card.style.opacity = '0.5';
        }
    });
}

// Update energy flow diagram
function updateEnergyFlow(data) {
    const solarPower = data.solar.total_power;
    const gridPower = data.grid.power;
    const housePower = data.load.power;
    const batteryPower = data.battery ? data.battery.power : 0;

    // Update node values
    setValue('solarValue', `${(solarPower / 1000).toFixed(1)} kW`);
    setValue('houseValue', `${(housePower / 1000).toFixed(1)} kW`);

    // Grid value with arrow showing direction
    if (gridPower > 0) {
        setValue('gridValue', `← ${(gridPower / 1000).toFixed(1)} kW`);
    } else if (gridPower < 0) {
        setValue('gridValue', `→ ${(-gridPower / 1000).toFixed(1)} kW`);
    } else {
        setValue('gridValue', `0.0 kW`);
    }

    // Battery (if equipped)
    if (data.battery) {
        setValue('batteryValue', `${data.battery.soc.toFixed(0)}%`);
    }

    // Update line thickness and color based on power flow
    updateFlowLine('lineSolarHome', solarPower * 0.5, '#F59E0B'); // Assume ~50% to home
    updateFlowLine('lineSolarGrid', Math.abs(gridPower), gridPower < 0 ? '#8B5CF6' : '#E5E7EB');

    if (data.battery) {
        updateFlowLine('lineSolarBattery', Math.abs(batteryPower), batteryPower > 0 ? '#10B981' : '#E5E7EB');
    }
}

// Update flow line appearance based on power
function updateFlowLine(lineId, power, activeColor) {
    const line = document.getElementById(lineId);
    if (!line) return;

    const maxPower = 10000; // 10kW max for scaling
    const minWidth = 2;
    const maxWidth = 8;

    // Calculate width based on power (logarithmic scale for better visualization)
    const width = power > 100 ?
        minWidth + (Math.log(power) / Math.log(maxPower)) * (maxWidth - minWidth) :
        minWidth;

    line.setAttribute('stroke-width', width);
    line.setAttribute('stroke', power > 100 ? activeColor : '#E5E7EB');
    line.setAttribute('opacity', power > 100 ? '1' : '0.3');
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

// Clean up on page unload
window.addEventListener('beforeunload', () => {
    if (updateInterval) {
        clearInterval(updateInterval);
    }
});
