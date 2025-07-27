"""
Views module for Tea Processing Monitor application
Contains functions to render HTML templates with necessary data
"""

from flask import render_template, g, current_app
from controllers import get_process_data, get_machine_data
from pymongo import MongoClient
import traceback

def dashboard_view():
    """
    Render the main dashboard view
    
    Returns:
        rendered HTML template with dashboard data
    """
    print("Starting dashboard_view function")
    
    # Create a dedicated MongoDB connection for this view
    try:
        # Create a direct database connection
        mongo_client = MongoClient(current_app.config['MONGO_URI'])
        db = mongo_client.get_database()
        
        # Make db available to the get_process_data function via flask global
        g.db = db
        
        try:
            # Get data for all processes and their machines
            processes_data = get_process_data()
            print(f"Retrieved {len(processes_data) if isinstance(processes_data, list) else 'ERROR'} processes")
            
            # Calculate overview counts
            running = 0
            idle = 0
            maintenance = 0
            fault = 0
            
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
            
            # Return rendered template with data
            return render_template(
                'dashboard.html',
                title='Tea Processing Monitor',
                processes=processes_data,
                overview=overview_data
            )
        
        except Exception as e:
            print(f"Error processing dashboard data: {e}")
            traceback.print_exc()
            # Return error template or empty dashboard
            return render_template(
                'dashboard.html',
                title='Tea Processing Monitor - Error',
                processes=[],
                overview={'running': 0, 'idle': 0, 'maintenance': 0, 'fault': 0},
                error_message=f"Failed to load dashboard data: {str(e)}"
            )
        
        finally:
            # Always close the MongoDB connection
            mongo_client.close()
            print("MongoDB connection closed in dashboard_view")
    
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        traceback.print_exc()
        # Return error template if MongoDB connection fails
        return render_template(
            'dashboard.html',
            title='Tea Processing Monitor - Database Error',
            processes=[],
            overview={'running': 0, 'idle': 0, 'maintenance': 0, 'fault': 0},
            error_message="Failed to connect to database. Please check your MongoDB configuration."
        )


def machine_view(process_name, machine_id):
    """
    Render the machine detail view
    
    Args:
        process_name (str): Name of the process the machine belongs to
        machine_id (str): ID of the machine to display
        
    Returns:
        rendered HTML template with machine details
    """
    print(f"Starting machine_view function for {machine_id} in process {process_name}")
    
    # Create a dedicated MongoDB connection for this view
    try:
        # Create a direct database connection
        mongo_client = MongoClient(current_app.config['MONGO_URI'])
        db = mongo_client.get_database()
        
        # Make db available to the controller functions via flask global
        g.db = db
        
        try:
            # Get detailed data for the specific machine
            machine_data = get_machine_data(machine_id)
            
            # Get process data to access process details
            processes_data = get_process_data()
            process = next((p for p in processes_data if p['name'] == process_name), None)
            
            if not process:
                print(f"Process {process_name} not found")
                # Return error page if process not found
                return render_template(
                    'machine_detail.html',
                    title='Machine Not Found',
                    process=None,
                    machine=None,
                    error_message=f"Process {process_name} not found"
                )
            
            if 'error' in machine_data:
                print(f"Machine error: {machine_data['error']}")
                # Return error page if machine data has an error
                return render_template(
                    'machine_detail.html',
                    title='Machine Error',
                    process=process,
                    machine=None,
                    error_message=machine_data['error']
                )
            
            return render_template(
                'machine_detail.html',
                title=f"{machine_data['name']} - {process_name}",
                process=process,
                machine=machine_data
            )
            
        except Exception as e:
            print(f"Error processing machine data: {e}")
            traceback.print_exc()
            # Return error template if data processing fails
            return render_template(
                'machine_detail.html',
                title='Machine View - Error',
                process=None,
                machine=None,
                error_message=f"Failed to load machine data: {str(e)}"
            )
            
        finally:
            # Always close the MongoDB connection
            mongo_client.close()
            print("MongoDB connection closed in machine_view")
            
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        traceback.print_exc()
        # Return error template if MongoDB connection fails
        return render_template(
            'machine_detail.html',
            title='Machine View - Database Error',
            process=None,
            machine=None,
            error_message="Failed to connect to database. Please check your MongoDB configuration."
        )
