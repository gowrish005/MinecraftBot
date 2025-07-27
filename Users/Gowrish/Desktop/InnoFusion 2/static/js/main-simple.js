/**
 * Tea Processing Monitor - Simple JavaScript for debugging
 * Stripped down version of main.js with minimal functionality
 */

// Global variable to store process data
let processData = [];

// Initialize the dashboard when the page loads
document.addEventListener('DOMContentLoaded', () => {
    console.log('Simple JS loaded - DOM content loaded');
    
    // Initial data load
    loadDashboardData();
    
    // Set up update interval (every 30 seconds)
    setInterval(loadDashboardData, 30000);
});

// Load dashboard data from the API
function loadDashboardData() {
    console.log('Fetching dashboard data from API...');
    
    fetch('/api/process-data')
        .then(response => {
            console.log('API Response status:', response.status);
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('API data received:', data);
            processData = data;
            
            // Check if we're on the dashboard
            if (document.getElementById('running-count')) {
                console.log('Updating dashboard UI with data...');
                updateDashboardUI(data);
                updateStatusCounts(data);
            } else {
                console.log('Not on dashboard page - skipping UI update');
            }
        })
        .catch(error => {
            console.error('Error fetching dashboard data:', error);
            showErrorMessage('Failed to load dashboard data. Please check your connection.');
        });
}

// Update the dashboard UI with the latest data
function updateDashboardUI(processes) {
    console.log('updateDashboardUI called with', processes.length, 'processes');
    
    processes.forEach(process => {
        process.machines.forEach(machine => {
            const machineCard = document.querySelector(`.machine-card[data-machine-id="${machine.id}"]`);
            if (machineCard) {
                console.log('Updating machine card for ID:', machine.id);
                
                // Update status indicator
                const statusIndicator = machineCard.querySelector('.status-indicator');
                if (statusIndicator) {
                    statusIndicator.className = 'status-indicator';
                    statusIndicator.classList.add(`status-${machine.status}`);
                }
                
                // Update temperature
                const tempElement = document.getElementById(`temp-${machine.id}`);
                if (tempElement && machine.latest_readings && machine.latest_readings.temperature) {
                    tempElement.textContent = `${machine.latest_readings.temperature}°C`;
                }
                
                // Update humidity
                const humidElement = document.getElementById(`humid-${machine.id}`);
                if (humidElement && machine.latest_readings && machine.latest_readings.humidity) {
                    humidElement.textContent = `${machine.latest_readings.humidity}%`;
                }
            } else {
                console.log('Machine card not found for ID:', machine.id);
            }
        });
    });
}

// Update status counts in the system overview
function updateStatusCounts(processes) {
    console.log('updateStatusCounts called');
    
    // Get the count elements
    const runningCountElement = document.getElementById('running-count');
    const idleCountElement = document.getElementById('idle-count');
    const maintenanceCountElement = document.getElementById('maintenance-count');
    const errorCountElement = document.getElementById('error-count');
    
    // Check if elements exist
    if (!runningCountElement || !idleCountElement || !maintenanceCountElement || !errorCountElement) {
        console.error('Missing count elements in the DOM:',
            { running: !!runningCountElement, idle: !!idleCountElement, 
              maintenance: !!maintenanceCountElement, error: !!errorCountElement });
        return;
    }
    
    // Count machines by status
    let runningCount = 0;
    let idleCount = 0;
    let maintenanceCount = 0;
    let errorCount = 0;
    
    processes.forEach(process => {
        process.machines.forEach(machine => {
            console.log('Machine status:', machine.status, 'for', machine.name);
            switch (machine.status) {
                case 'running':
                    runningCount++;
                    break;
                case 'idle':
                    idleCount++;
                    break;
                case 'maintenance':
                    maintenanceCount++;
                    break;
                case 'error':
                case 'fault':
                    errorCount++;
                    break;
            }
        });
    });
    
    // Update the count displays
    console.log('Updating counts:', { running: runningCount, idle: idleCount, 
                                      maintenance: maintenanceCount, error: errorCount });
    runningCountElement.textContent = runningCount;
    idleCountElement.textContent = idleCount;
    maintenanceCountElement.textContent = maintenanceCount;
    errorCountElement.textContent = errorCount;
}

// Show error message
function showErrorMessage(message) {
    console.error('Error:', message);
    
    // Create alert div if it doesn't exist
    let alertDiv = document.getElementById('error-alert');
    if (!alertDiv) {
        alertDiv = document.createElement('div');
        alertDiv.id = 'error-alert';
        alertDiv.className = 'alert alert-danger mt-3';
        alertDiv.role = 'alert';
        
        const container = document.querySelector('.container');
        if (container) {
            container.prepend(alertDiv);
        } else {
            document.body.prepend(alertDiv);
        }
    }
    
    // Set message
    alertDiv.textContent = message;
}
