/**
 * Tea Processing Monitor - Main JavaScript
 * Handles dashboard interactions and real-time data updates
 */

// Global variable to store process data
let processData = [];

// Initialize the dashboard when the page loads
document.addEventListener('DOMContentLoaded', () => {
    // Initial data load
    loadDashboardData();
    
    // Set up update interval (every 30 seconds)
    setInterval(loadDashboardData, 30000);
    
    // Set up event listeners
    setupEventListeners();
    
    // Initialize tooltips
    initTooltips();
});

// Load dashboard data from the API
function loadDashboardData() {
    console.log('Fetching dashboard data...');
    fetch('/api/process-data')
        .then(response => {
            console.log('Response received:', response.status);
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Data parsed successfully:', data);
            processData = data;
            updateDashboardUI(data);
            updateStatusCounts(data);
            // Hide loading overlay if it exists
            let loadingOverlay = document.getElementById('loading-overlay');
            if (loadingOverlay && loadingOverlay.parentNode) {
                loadingOverlay.parentNode.removeChild(loadingOverlay);
            }
        })
        .catch(error => {
            console.error('Error fetching dashboard data:', error);
            showErrorNotification('Failed to load dashboard data. Please check your connection.');
            // Hide loading overlay if it exists, even on error
            let loadingOverlay = document.getElementById('loading-overlay');
            if (loadingOverlay && loadingOverlay.parentNode) {
                loadingOverlay.parentNode.removeChild(loadingOverlay);
            }
        });
}

// Update the dashboard UI with the latest data
function updateDashboardUI(processes) {
    console.log("Updating dashboard UI");
    // Skip if we're not on the dashboard page
    if (!document.getElementById('running-count')) {
        console.log("Not on dashboard page - skipping UI update");
        return;
    }
    
    // Check if processes is valid
    if (!processes || !Array.isArray(processes)) {
        console.error("Invalid processes data:", processes);
        return;
    }
    
    console.log(`Updating UI for ${processes.length} processes`);
    processes.forEach(process => {
        if (!process.machines || !Array.isArray(process.machines)) {
            console.error(`Process ${process.name} has invalid machines data:`, process.machines);
            return;
        }
        
        console.log(`Processing ${process.machines.length} machines for ${process.name}`);        process.machines.forEach(machine => {
            // Update machine status indicator and badge
            updateMachineStatus(machine);
            
            // Update machine readings if available
            if (machine.latest_readings) {
                updateMachineReadings(machine, machine.latest_readings);
            }
            // Fallback to readings array if exists
            else if (machine.readings && machine.readings.length > 0) {
                updateMachineReadings(machine, machine.readings[0]);
            }
        });
    });
}

// Update status counts in the system overview
function updateStatusCounts(processes) {
    // Skip if we're not on the dashboard page
    if (!document.getElementById('running-count')) {
        console.log("Missing UI element 'running-count' - not updating status counts");
        return;
    }
    
    if (!processes || !Array.isArray(processes)) {
        console.error("Invalid processes data for status counts:", processes);
        return;
    }
    
    let runningCount = 0;
    let idleCount = 0;
    let maintenanceCount = 0;
    let errorCount = 0;
    
    // Count machines by status
    processes.forEach(process => {
        process.machines.forEach(machine => {
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
                    errorCount++;
                    break;
            }
        });
    });
    
    // Update the count displays
    document.getElementById('running-count').textContent = runningCount;
    document.getElementById('idle-count').textContent = idleCount;
    document.getElementById('maintenance-count').textContent = maintenanceCount;
    document.getElementById('error-count').textContent = errorCount;
}

// Update a machine's status indicator and badge
function updateMachineStatus(machine) {
    console.log(`Updating machine status for machine ID: ${machine.id}`);
    
    if (!machine || !machine.id) {
        console.error("Invalid machine object:", machine);
        return;
    }
    
    const machineCard = document.querySelector(`.machine-card[data-machine-id="${machine.id}"]`);
    if (!machineCard) {
        console.log(`Machine card element not found for machine ID: ${machine.id}`);
        return;
    }
    
    // Update status indicator
    const statusIndicator = machineCard.querySelector('.status-indicator');
    if (statusIndicator && machine.status) {
        statusIndicator.className = `status-indicator status-${machine.status}`;
    }
    
    // Update status badge
    const statusBadge = machineCard.querySelector('.badge');
    if (statusBadge && machine.status) {
        statusBadge.className = `badge bg-${
            machine.status === 'running' ? 'success' :
            machine.status === 'idle' ? 'warning' :
            machine.status === 'maintenance' ? 'info' : 'danger'
        }`;
        statusBadge.textContent = machine.status.charAt(0).toUpperCase() + machine.status.slice(1);
    }
    
    // Update last updated time
    const updatedElement = machineCard.querySelector(`#updated-${machine.id}`);
    if (updatedElement && machine.last_updated) {
        const updatedTime = new Date(machine.last_updated);
        updatedElement.textContent = updatedTime.toLocaleTimeString();
    }
}

// Update a machine's readings display
function updateMachineReadings(machine, reading) {
    if (!machine || !machine.id || !reading) {
        console.log("Missing machine or reading data:", { machine, reading });
        return;
    }
    
    console.log(`Updating readings for machine ${machine.id}:`, reading);
    
    // Find the machine card
    const machineCard = document.querySelector(`.machine-card[data-machine-id="${machine.id}"]`);
    if (!machineCard) {
        console.log(`Machine card not found for ID: ${machine.id}`);
        return;
    }
    
    // Update temperature if available
    if (reading.temperature) {
        const tempElement = document.getElementById(`temp-${machine.id}`);
        if (tempElement) {
            tempElement.textContent = `${reading.temperature}°C`;
        }
    }
    
    // Update humidity if available
    if (reading.humidity) {
        const humidElement = document.getElementById(`humid-${machine.id}`);
        if (humidElement) {
            humidElement.textContent = `${reading.humidity}%`;
        }
    }
    
    // Update air flow if available
    if (reading.air_flow) {
        const airflowElement = document.getElementById(`airflow-${machine.id}`);
        if (airflowElement) {
            airflowElement.textContent = `${reading.air_flow} m/s`;
        }
    }
    
    // Update rotation speed if available
    if (reading.rotation_speed) {
        const rotationElement = document.getElementById(`rotation-${machine.id}`);
        if (rotationElement) {
            rotationElement.textContent = `${reading.rotation_speed} rpm`;
        }
    }
    
    // Update pressure if available
    if (reading.pressure) {
        const pressureElement = document.getElementById(`pressure-${machine.id}`);
        if (pressureElement) {
            pressureElement.textContent = `${reading.pressure} kPa`;
        }
    }
}

// Set up event listeners for interactive elements
function setupEventListeners() {
    // Machine card click handler for control buttons
    document.addEventListener('click', function(event) {
        // Check if the clicked element is a control button
        if (event.target.classList.contains('control-btn') || 
            event.target.parentElement.classList.contains('control-btn')) {
            
            const button = event.target.classList.contains('control-btn') ? 
                event.target : event.target.parentElement;
            
            const machineId = button.getAttribute('data-machine-id');
            showControlDialog(machineId);
        }
    });
    
    // Process section navigation
    const processLinks = document.querySelectorAll('.process-nav-link');
    processLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href').substring(1);
            const targetSection = document.getElementById(targetId);
            
            if (targetSection) {
                // Scroll to the target section with smooth animation
                targetSection.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// Show machine control dialog
function showControlDialog(machineId) {
    // Find machine data
    let machine = null;
    processData.forEach(process => {
        process.machines.forEach(m => {
            if (m.id === machineId) {
                machine = m;
            }
        });
    });
    
    if (!machine) return;
    
    // Create modal dialog
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.id = 'machineControlModal';
    modal.setAttribute('tabindex', '-1');
    modal.setAttribute('aria-labelledby', 'machineControlModalLabel');
    modal.setAttribute('aria-hidden', 'true');
    
    modal.innerHTML = `
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="machineControlModalLabel">
                        <span class="status-indicator status-${machine.status}"></span>
                        ${machine.name} Controls
                    </h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <p>${machine.description}</p>
                    <div class="d-grid gap-2">
                        <button class="btn btn-success control-action" data-action="start" data-machine-id="${machine.id}" ${machine.status === 'running' ? 'disabled' : ''}>
                            <i class="fas fa-play-circle me-2"></i>Start Machine
                        </button>
                        <button class="btn btn-warning control-action" data-action="pause" data-machine-id="${machine.id}" ${machine.status === 'idle' ? 'disabled' : ''}>
                            <i class="fas fa-pause-circle me-2"></i>Pause Machine
                        </button>
                        <button class="btn btn-info control-action" data-action="maintenance" data-machine-id="${machine.id}" ${machine.status === 'maintenance' ? 'disabled' : ''}>
                            <i class="fas fa-tools me-2"></i>Set to Maintenance
                        </button>
                        <button class="btn btn-danger control-action" data-action="emergency-stop" data-machine-id="${machine.id}">
                            <i class="fas fa-stop-circle me-2"></i>Emergency Stop
                        </button>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                </div>
            </div>
        </div>
    `;
    
    // Add modal to document
    document.body.appendChild(modal);
    
    // Initialize and show modal
    const modalInstance = new bootstrap.Modal(modal);
    modalInstance.show();
    
    // Add event listeners for control actions
    modal.querySelectorAll('.control-action').forEach(button => {
        button.addEventListener('click', function() {
            const action = this.getAttribute('data-action');
            const machineId = this.getAttribute('data-machine-id');
            sendControlCommand(machineId, action, modalInstance);
        });
    });
    
    // Clean up modal when hidden
    modal.addEventListener('hidden.bs.modal', function() {
        document.body.removeChild(modal);
    });
}

// Send control command to the server
function sendControlCommand(machineId, action, modalInstance) {
    // Show loading state
    showLoading(true);
    
    fetch(`/api/machine/${machineId}/control`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ action })
    })
    .then(response => response.json())
    .then(result => {
        // Hide loading state
        showLoading(false);
        
        if (result.success) {
            // Close modal
            modalInstance.hide();
            
            // Refresh data
            loadDashboardData();
            
            // Show success notification
            showNotification(`${action.replace('-', ' ')} command sent successfully to the machine.`, 'success');
        } else {
            // Show error message
            showNotification(`Error: ${result.error || 'Unknown error'}`, 'danger');
        }
    })
    .catch(error => {
        // Hide loading state
        showLoading(false);
        
        console.error('Error sending control command:', error);
        showNotification('Failed to send command to the machine.', 'danger');
    });
}

// Show loading indicator
function showLoading(isLoading) {
    // If loading overlay doesn't exist, create it
    let loadingOverlay = document.getElementById('loading-overlay');
    
    if (!loadingOverlay && isLoading) {
        loadingOverlay = document.createElement('div');
        loadingOverlay.id = 'loading-overlay';
        loadingOverlay.innerHTML = `
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p>Loading dashboard data...</p>
        `;
        document.body.appendChild(loadingOverlay);
        
        // Set a timeout to remove loading overlay if it takes too long (10 seconds)
        setTimeout(() => {
            const overlay = document.getElementById('loading-overlay');
            if (overlay) {
                document.body.removeChild(overlay);
                showErrorNotification('Dashboard loading timed out. Please refresh the page to try again.');
            }
        }, 10000);
    } else if (loadingOverlay && !isLoading) {
        document.body.removeChild(loadingOverlay);
    }
}

// Show notification
function showNotification(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    // Create toast container if it doesn't exist
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    // Add toast to container
    toastContainer.appendChild(toast);
    
    // Initialize and show toast
    const toastInstance = new bootstrap.Toast(toast);
    toastInstance.show();
    
    // Remove toast after it's hidden
    toast.addEventListener('hidden.bs.toast', function() {
        toastContainer.removeChild(toast);
    });
}

// Show error notification
function showErrorNotification(message) {
    showNotification(message, 'danger');
}

// Initialize Bootstrap tooltips
function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Export functions for use in other scripts
window.teaMonitor = {
    loadDashboardData,
    showControlDialog,
    sendControlCommand,
    showNotification
};