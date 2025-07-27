from models import get_db
import pprint  # For debugging purposes
import datetime
from flask import render_template, request, redirect, url_for, flash, session
from models import register_user, authenticate_user, logout_user
from functools import wraps

def get_process_data(process_name=None):
    """
    Get data for tea processing stages and their machines
    
    Args:
        process_name (str, optional): If provided, only return data for this process
        
    Returns:
        list: List of processes with their machines and statuses
    """
    print("Starting get_process_data function")
    try:
        print("Attempting to get database connection")
        db = get_db()
        print("Successfully obtained database connection")
        
        # Set a limit on fetch operations to prevent timeouts
        max_time_ms = 5000  # 5 seconds timeout
        
        if process_name:
            # Return data for a specific process with timeout
            process = db.processes.find_one({"name": process_name}, {"_id": 0}, max_time_ms=max_time_ms)
            if not process:
                return {"error": "Process not found"}
            
            # Get all machines for this process
            machines = list(db.machines.find(
                {"process_id": process["id"]}, 
                {"_id": 0}
            ))
            
            # Get latest readings for each machine
            for machine in machines:
                # Ensure image_url is correctly formatted for Flask's url_for
                if "image_url" in machine and machine["image_url"] and not machine["image_url"].startswith("images/"):
                    machine["image_url"] = "images/" + machine["image_url"]
                latest_reading = db.readings.find_one(
                    {"machine_id": machine["id"]},
                    {"_id": 0},
                    sort=[("timestamp", -1)]
                )
                
                # Debug: print reading to console
                print(f"Latest reading for {machine['name']}:")
                if latest_reading:
                    pprint.pprint(latest_reading)
                else:
                    print("No readings found")
                
                # Initialize latest_readings
                machine["latest_readings"] = {}
                
                # Add the original reading data if available
                if latest_reading:
                    # Map specific readings to generic ones based on process type
                    if machine["process_id"] == "withering":
                        machine["latest_readings"] = {
                            "temperature": latest_reading.get("ambient_temperature"),
                            "humidity": latest_reading.get("trough_humidity"),
                            "air_flow": latest_reading.get("air_flow_rate")
                        }
                    elif machine["process_id"] == "rolling":
                        if "orthodox-roller" in machine["id"]:
                            machine["latest_readings"] = {
                                "temperature": latest_reading.get("roller_temperature"),
                                "pressure": latest_reading.get("pressure_plate_force"),
                                "speed": latest_reading.get("roller_rpm")
                            }
                        else:
                            machine["latest_readings"] = {
                                "temperature": latest_reading.get("cutter_temperature"),
                                "speed": latest_reading.get("cutter_rpm"),
                                "feed_rate": latest_reading.get("feed_roller_speed")
                            }
                    elif machine["process_id"] == "fermentation":
                        machine["latest_readings"] = {
                            "temperature": latest_reading.get("chamber_temperature"),
                            "humidity": latest_reading.get("chamber_humidity"),
                            "air_flow": latest_reading.get("air_circulation_speed"),
                            "oxygen": latest_reading.get("oxygen_concentration")
                        }
                    elif machine["process_id"] == "drying":
                        if "fluid-bed" in machine["id"]:
                            machine["latest_readings"] = {
                                "temperature": latest_reading.get("outlet_air_temperature"),
                                "air_flow": latest_reading.get("air_flow_velocity"),
                                "moisture": latest_reading.get("tea_moisture_content")
                            }
                        else:
                            machine["latest_readings"] = {
                                "temperature": latest_reading.get("drum_surface_temperature"),
                                "speed": latest_reading.get("drum_rotation_speed"),
                                "moisture": latest_reading.get("outlet_moisture_content")
                            }
                    elif machine["process_id"] == "sorting":
                        if "vibro" in machine["id"]:
                            machine["latest_readings"] = {
                                "vibration": latest_reading.get("vibration_amplitude"),
                                "frequency": latest_reading.get("vibration_frequency"),
                                "feed_rate": latest_reading.get("feed_rate")
                            }
                        else:
                            machine["latest_readings"] = {
                                "speed": latest_reading.get("belt_speed"),
                                "accuracy": latest_reading.get("ejection_accuracy"),
                                "rejection": latest_reading.get("rejection_rate")
                            }
                    elif machine["process_id"] == "packing":
                        if "tea-bagger" in machine["id"]:
                            machine["latest_readings"] = {
                                "speed": latest_reading.get("production_speed"),
                                "temperature": latest_reading.get("sealing_temperature"),
                                "variance": latest_reading.get("bag_weight_variance")
                            }
                        else:
                            machine["latest_readings"] = {
                                "filling_rate": latest_reading.get("filling_rate"),
                                "accuracy": latest_reading.get("packaging_weight_accuracy"),
                                "temperature": latest_reading.get("seal_temperature")
                            }

                    # Add all raw readings for other metrics
                    for key, value in latest_reading.items():
                        if key not in ["_id", "machine_id", "timestamp"] and key not in machine["latest_readings"]:
                            machine["latest_readings"][key] = value
                
            process["machines"] = machines
            return process
            
        # Return data for all processes
        print("Fetching all processes from database")
        processes = list(db.processes.find({}, {"_id": 0}))
        print(f"Found {len(processes)} processes")
        
        # For each process, get its machines
        for process in processes:
            print(f"Fetching machines for process: {process['name']}")
            machines = list(db.machines.find(
                {"process_id": process["id"]}, 
                {"_id": 0}
            ))
            print(f"Found {len(machines)} machines for {process['name']}")
            
            # Get latest readings for each machine
            for machine in machines:
                # Ensure image_url is correctly formatted for Flask's url_for
                if "image_url" in machine and machine["image_url"] and not machine["image_url"].startswith("images/"):
                    machine["image_url"] = "images/" + machine["image_url"]
                    
                latest_reading = db.readings.find_one(
                    {"machine_id": machine["id"]},
                    {"_id": 0},
                    sort=[("timestamp", -1)]
                )
                
                # Initialize latest_readings
                machine["latest_readings"] = {}
                
                # Add the original reading data if available
                if latest_reading:
                    # Map specific readings to generic ones based on process type
                    if machine["process_id"] == "withering":
                        machine["latest_readings"] = {
                            "temperature": latest_reading.get("ambient_temperature"),
                            "humidity": latest_reading.get("trough_humidity"),
                            "air_flow": latest_reading.get("air_flow_rate")
                        }
                    elif machine["process_id"] == "rolling":
                        if "orthodox-roller" in machine["id"]:
                            machine["latest_readings"] = {
                                "temperature": latest_reading.get("roller_temperature"),
                                "pressure": latest_reading.get("pressure_plate_force"),
                                "speed": latest_reading.get("roller_rpm")
                            }
                        else:
                            machine["latest_readings"] = {
                                "temperature": latest_reading.get("cutter_temperature"),
                                "speed": latest_reading.get("cutter_rpm"),
                                "feed_rate": latest_reading.get("feed_roller_speed")
                            }
                    elif machine["process_id"] == "fermentation":
                        machine["latest_readings"] = {
                            "temperature": latest_reading.get("chamber_temperature"),
                            "humidity": latest_reading.get("chamber_humidity"),
                            "air_flow": latest_reading.get("air_circulation_speed"),
                            "oxygen": latest_reading.get("oxygen_concentration")
                        }
                    elif machine["process_id"] == "drying":
                        if "fluid-bed" in machine["id"]:
                            machine["latest_readings"] = {
                                "temperature": latest_reading.get("outlet_air_temperature"),
                                "air_flow": latest_reading.get("air_flow_velocity"),
                                "moisture": latest_reading.get("tea_moisture_content")
                            }
                        else:
                            machine["latest_readings"] = {
                                "temperature": latest_reading.get("drum_surface_temperature"),
                                "speed": latest_reading.get("drum_rotation_speed"),
                                "moisture": latest_reading.get("outlet_moisture_content")
                            }
                    elif machine["process_id"] == "sorting":
                        if "vibro" in machine["id"]:
                            machine["latest_readings"] = {
                                "vibration": latest_reading.get("vibration_amplitude"),
                                "frequency": latest_reading.get("vibration_frequency"),
                                "feed_rate": latest_reading.get("feed_rate")
                            }
                        else:
                            machine["latest_readings"] = {
                                "speed": latest_reading.get("belt_speed"),
                                "accuracy": latest_reading.get("ejection_accuracy"),
                                "rejection": latest_reading.get("rejection_rate")
                            }
                    elif machine["process_id"] == "packing":
                        if "tea-bagger" in machine["id"]:
                            machine["latest_readings"] = {
                                "speed": latest_reading.get("production_speed"),
                                "temperature": latest_reading.get("sealing_temperature"),
                                "variance": latest_reading.get("bag_weight_variance")
                            }
                        else:
                            machine["latest_readings"] = {
                                "filling_rate": latest_reading.get("filling_rate"),
                                "accuracy": latest_reading.get("packaging_weight_accuracy"),
                                "temperature": latest_reading.get("seal_temperature")
                            }

                    # Add all raw readings for other metrics
                    for key, value in latest_reading.items():
                        if key not in ["_id", "machine_id", "timestamp"] and key not in machine["latest_readings"]:
                            machine["latest_readings"][key] = value
                
            process["machines"] = machines
            process["machine_count"] = len(machines)
        
        print("Successfully processed all data")
        return processes
    except Exception as e:
        print(f"Error in get_process_data: {e}")
        import traceback
        traceback.print_exc()
        # Return empty data in case of error
        if process_name:
            return {"error": f"Database error: {str(e)}"}
        return []

def get_machine_data(machine_id):
    """
    Get detailed data for a specific machine
    
    Args:
        machine_id (str): The ID of the machine
        
    Returns:
        dict: Machine data including status and readings
    """
    try:
        from models import MACHINE_SPECS
        db = get_db()
        
        # Get base machine info
        machine = db.machines.find_one({"id": machine_id}, {"_id": 0})
        if not machine:
            return {"error": "Machine not found"}
            
        # Ensure image_url is correctly formatted for Flask's url_for
        if "image_url" in machine and machine["image_url"] and not machine["image_url"].startswith("images/"):
            machine["image_url"] = "images/" + machine["image_url"]
        
        # Add technical specifications to the machine data
        process_id = machine.get("process_id")
        if process_id and process_id in MACHINE_SPECS:
            machine["specs"] = MACHINE_SPECS[process_id]
        
        # Get the latest readings for this machine
        latest_readings = list(db.readings.find(
            {"machine_id": machine_id}, 
            {"_id": 0}
        ).sort("timestamp", -1).limit(100))
        
        machine["readings"] = latest_readings
        
        # Prepare chart data for voltage and heating wire temperature
        voltage_data = []
        temperature_data = []
        labels = []
        
        # Process readings in reverse to get chronological order
        for reading in reversed(latest_readings[:24]):  # Limit to last 24 readings
            if 'timestamp' in reading:
                # Format timestamp for chart labels
                dt = datetime.datetime.fromisoformat(reading['timestamp'].replace('Z', '+00:00'))
                time_label = dt.strftime('%H:%M')
                labels.append(time_label)
                
                # Get voltage readings
                if 'voltage' in reading:
                    voltage_data.append(reading['voltage'])
                else:
                    voltage_data.append(None)  # Use None for missing data
                    
                # Get heating wire temperature readings for applicable machines
                if process_id in ["withering", "fermentation", "drying"] and 'heating_wire_temperature' in reading:
                    temperature_data.append(reading['heating_wire_temperature'])
                else:
                    temperature_data.append(None)  # Use None for missing data
        
        # Add chart data to machine object
        machine["chart_data"] = {
            "labels": labels,
            "voltage": voltage_data,
            "heating_wire_temperature": temperature_data
        }
        
        # Initialize latest_readings
        machine["latest_readings"] = {}
        
        # Add the most recent reading if available
        if latest_readings:
            # Map specific readings to generic ones based on process type
            if machine["process_id"] == "withering":
                machine["latest_readings"] = {
                    "temperature": latest_readings[0].get("ambient_temperature"),
                    "humidity": latest_readings[0].get("trough_humidity"),
                    "air_flow": latest_readings[0].get("air_flow_rate")
                }
            elif machine["process_id"] == "rolling":
                if "orthodox-roller" in machine["id"]:
                    machine["latest_readings"] = {
                        "temperature": latest_readings[0].get("roller_temperature"),
                        "pressure": latest_readings[0].get("pressure_plate_force"),
                        "speed": latest_readings[0].get("roller_rpm")
                    }
                else:
                    machine["latest_readings"] = {
                        "temperature": latest_readings[0].get("cutter_temperature"),
                        "speed": latest_readings[0].get("cutter_rpm"),
                        "feed_rate": latest_readings[0].get("feed_roller_speed")
                    }
            elif machine["process_id"] == "fermentation":
                machine["latest_readings"] = {
                    "temperature": latest_readings[0].get("chamber_temperature"),
                    "humidity": latest_readings[0].get("chamber_humidity"),
                    "air_flow": latest_readings[0].get("air_circulation_speed"),
                    "oxygen": latest_readings[0].get("oxygen_concentration")
                }
            elif machine["process_id"] == "drying":
                if "fluid-bed" in machine["id"]:
                    machine["latest_readings"] = {
                        "temperature": latest_readings[0].get("outlet_air_temperature"),
                        "air_flow": latest_readings[0].get("air_flow_velocity"),
                        "moisture": latest_readings[0].get("tea_moisture_content")
                    }
                else:
                    machine["latest_readings"] = {
                        "temperature": latest_readings[0].get("drum_surface_temperature"),
                        "speed": latest_readings[0].get("drum_rotation_speed"),
                        "moisture": latest_readings[0].get("outlet_moisture_content")
                    }
            elif machine["process_id"] == "sorting":
                if "vibro" in machine["id"]:
                    machine["latest_readings"] = {
                        "vibration": latest_readings[0].get("vibration_amplitude"),
                        "frequency": latest_readings[0].get("vibration_frequency"),
                        "feed_rate": latest_readings[0].get("feed_rate")
                    }
                else:
                    machine["latest_readings"] = {
                        "speed": latest_readings[0].get("belt_speed"),
                        "accuracy": latest_readings[0].get("ejection_accuracy"),
                        "rejection": latest_readings[0].get("rejection_rate")
                    }
            elif machine["process_id"] == "packing":
                if "tea-bagger" in machine["id"]:
                    machine["latest_readings"] = {
                        "speed": latest_readings[0].get("production_speed"),
                        "temperature": latest_readings[0].get("sealing_temperature"),
                        "variance": latest_readings[0].get("bag_weight_variance")
                    }
                else:
                    machine["latest_readings"] = {
                        "filling_rate": latest_readings[0].get("filling_rate"),
                        "accuracy": latest_readings[0].get("packaging_weight_accuracy"),
                        "temperature": latest_readings[0].get("seal_temperature")
                    }
                    
            # Add all raw readings for other metrics
            for key, value in latest_readings[0].items():
                if key not in ["_id", "machine_id", "timestamp"] and key not in machine["latest_readings"]:
                    machine["latest_readings"][key] = value
            
        return machine
    except Exception as e:
        print(f"Error in get_machine_data: {e}")
        import traceback
        traceback.print_exc()
        return {"error": f"Database error: {str(e)}"}

# Update machine status function
def update_machine_status(machine_id, data):
    """
    Update the status of a machine
    
    Args:
        machine_id (str): The ID of the machine
        data (dict): The data to update
        
    Returns:
        dict: Result of the operation
    """
    try:
        db = get_db()
        
        # Validate the machine exists
        machine = db.machines.find_one({"id": machine_id})
        if not machine:
            return {"success": False, "error": "Machine not found"}
        
        # Update machine status
        result = db.machines.update_one(
            {"id": machine_id},
            {"$set": {
                "status": data.get("status"),
                "last_updated": data.get("timestamp")
            }}
        )
        
        # Insert a new reading if provided
        if "readings" in data:
            for reading in data["readings"]:
                reading["machine_id"] = machine_id
                db.readings.insert_one(reading)
        
        return {
            "success": True,
            "updated": result.modified_count > 0
        }
    except Exception as e:
        print(f"Error in update_machine_status: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

def login_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return view_func(*args, **kwargs)
    return wrapped_view

def register_routes(app):
    from flask import render_template, request, redirect, url_for, flash, session
    from models import register_user, authenticate_user, logout_user

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            email = request.form['email']
            password = request.form['password']
            success, message = register_user(email, password)
            if success:
                flash(message, 'success')
                return redirect(url_for('login'))
            else:
                flash(message, 'danger')
        return render_template('register.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form['email']
            password = request.form['password']
            success, message = authenticate_user(email, password)
            if success:
                flash(message, 'success')
                return redirect(url_for('index'))
            else:
                flash(message, 'danger')
        return render_template('login.html')

    @app.route('/logout')
    def logout():
        logout_user()
        flash('Logged out successfully.', 'info')
        return redirect(url_for('login'))

    @app.route('/')
    @login_required
    def index():
        # ...existing dashboard logic...
        return render_template('dashboard.html')
