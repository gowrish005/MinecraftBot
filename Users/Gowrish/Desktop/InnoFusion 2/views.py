from flask import render_template
from controllers import get_process_data, get_machine_data

def dashboard_view():
    """Render the main dashboard view"""
    print("Starting dashboard_view function")
    try:
        # Get data for all processes and their machines
        processes_data = get_process_data()
        print(f"Retrieved {len(processes_data) if isinstance(processes_data, list) else 'ERROR'} processes")
        
        # Calculate overview counts
        running = 0
        idle = 0
        maintenance = 0
        fault = 0
    except Exception as e:
        print(f"Error in dashboard_view when getting process data: {e}")
        import traceback
        traceback.print_exc()
        processes_data = []
    
    # Loop through all processes and machines to count status
    for process in processes_data:
        for machine in process.get('machines', []):
            status = machine.get('status', '').lower()
            if status == 'running':
                running += 1
            elif status == 'idle':
                idle += 1
            elif status == 'maintenance':
                maintenance += 1
            elif status in ['fault', 'error']:
                fault += 1
    
    # Create overview data
    overview_data = {
        'running': running,
        'idle': idle,
        'maintenance': maintenance,
        'fault': fault
    }
    
    return render_template(
        'dashboard.html',
        title='Tea Processing Monitor',
        processes=processes_data,
        overview=overview_data
    )

def machine_view(process_name, machine_id):
    """Render the machine detail view"""
    # Get detailed data for the specific machine
    machine_data = get_machine_data(machine_id)
    
    # Get process data to access process details
    processes_data = get_process_data()
    process = next((p for p in processes_data if p['name'] == process_name), None)
    
    return render_template(
        'machine_detail.html',
        title=f'{machine_data["name"]} | {process_name}',
        machine=machine_data,
        process=process,
        process_name=process_name
    )