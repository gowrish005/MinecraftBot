from pymongo import MongoClient
import datetime
import random
import time
import threading
import sys
import signal

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['tea_processing']

# Flag to control continuous updates
running = True

# Function to initialize test data
def initialize_data():
    print("Initializing test data...")
    
    # Clear existing data
    db.processes.delete_many({})
    db.machines.delete_many({})
    db.readings.delete_many({})
    
    # Define tea processing stages
    processes = [
        {
            "id": "withering",
            "name": "Withering (Wilting)",
            "description": "First stage where fresh tea leaves lose moisture and become soft and pliable",
            "order": 1
        },
        {
            "id": "rolling",
            "name": "Rolling and Shaping",
            "description": "Process that breaks down leaf cells to release enzymes and essential oils",
            "order": 2
        },
        {
            "id": "fermentation",
            "name": "Fermentation (Oxidation)",
            "description": "Chemical reactions that change leaf color, flavor, and aroma",
            "order": 3
        },
        {
            "id": "drying",
            "name": "Drying (Firing)",
            "description": "Halts oxidation and reduces moisture content to preserve tea",
            "order": 4
        },
        {
            "id": "sorting",
            "name": "Sorting and Grading",
            "description": "Classification of processed tea leaves by size, appearance, and quality",
            "order": 5
        },
        {
            "id": "packing",
            "name": "Packing and Packaging",
            "description": "Final stage where tea is packaged for shipping and consumption",
            "order": 6
        }
    ]
    
    # Insert processes
    db.processes.insert_many(processes)
    print(f"Inserted {len(processes)} tea processing stages")
    
    # Define machines for each process with detailed metrics
    machines = [
        # Withering machines
        {
            "id": "withering-trough-1",
            "name": "Withering Trough 1",
            "process_id": "withering",
            "description": "Main withering machine for black tea",
            "status": "running",
            "capacity": 500,  # kg
            "metrics": [
                "ambient_temperature", 
                "leaf_moisture", 
                "air_flow_rate", 
                "trough_humidity", 
                "fan_speed"
            ],
            "last_updated": datetime.datetime.utcnow().isoformat()
        },
        {
            "id": "withering-trough-2",
            "name": "Withering Trough 2",
            "process_id": "withering",
            "description": "Main withering machine for black tea",
            "status": "running",
            "capacity": 500,  # kg
            "metrics": [
                "ambient_temperature", 
                "leaf_moisture", 
                "air_flow_rate", 
                "trough_humidity", 
                "fan_speed"
            ],
            "last_updated": datetime.datetime.utcnow().isoformat()
        },
        {
            "id": "withering-trough-3",
            "name": "Withering Trough 3",
            "process_id": "withering",
            "description": "Secondary withering machine for green tea",
            "status": "idle",
            "capacity": 450,  # kg
            "metrics": [
                "ambient_temperature", 
                "leaf_moisture", 
                "air_flow_rate", 
                "trough_humidity", 
                "fan_speed"
            ],
            "last_updated": datetime.datetime.utcnow().isoformat()
        },
        
        # Rolling machines
        {
            "id": "orthodox-roller-1",
            "name": "Orthodox Roller 1",
            "process_id": "rolling",
            "description": "Traditional rolling machine for black tea",
            
            "status": "running",
            "capacity": 200,  # kg/hour
            "metrics": [
                "roller_rpm", 
                "pressure_plate_force", 
                "roller_temperature", 
                "motor_load", 
                "leaf_discharge_rate"
            ],
            "last_updated": datetime.datetime.utcnow().isoformat()
        },
        {
            "id": "ctp-machine-1",
            "name": "CTC Machine 1",
            "process_id": "rolling",
            "description": "Cut-Tear-Curl machine for fine leaf tea",
            "status": "maintenance",
            "capacity": 350,  # kg/hour
            "metrics": [
                "cutter_rpm", 
                "feed_roller_speed", 
                "cutter_temperature", 
                "motor_load", 
                "particle_size"
            ],
            "last_updated": datetime.datetime.utcnow().isoformat()
        },
        
        # Fermentation machines
        {
            "id": "ferment-chamber-1",
            "name": "Fermentation Chamber 1",
            "process_id": "fermentation",
            "description": "Main oxidation chamber for black tea",
            "status": "running",
            "capacity": 300,  # kg
            "metrics": [
                "chamber_temperature", 
                "chamber_humidity", 
                "oxygen_concentration", 
                "air_circulation_speed", 
                "enzyme_activity_index"
            ],
            "last_updated": datetime.datetime.utcnow().isoformat()
        },
        {
            "id": "ferment-chamber-2",
            "name": "Fermentation Chamber 2",
            "process_id": "fermentation",
            "description": "Secondary oxidation chamber for oolong tea",
            "status": "fault",
            "capacity": 250,  # kg
            "metrics": [
                "chamber_temperature", 
                "chamber_humidity", 
                "oxygen_concentration", 
                "air_circulation_speed", 
                "enzyme_activity_index"
            ],
            "last_updated": datetime.datetime.utcnow().isoformat()
        },
        
        # Drying machines
        {
            "id": "fluid-bed-dryer-1",
            "name": "Fluid Bed Dryer 1",
            "process_id": "drying",
            "description": "Hot air dryer for black tea",
            "status": "running",
            "capacity": 400,  # kg/hour
            "metrics": [
                "heating_coil_temperature", 
                "outlet_air_temperature", 
                "inlet_air_temperature", 
                "air_flow_velocity", 
                "tea_moisture_content",
                "fuel_consumption"
            ],
            "last_updated": datetime.datetime.utcnow().isoformat()
        },
        {
            "id": "drum-dryer-1",
            "name": "Drum Dryer 1",
            "process_id": "drying",
            "description": "Rotary drum dryer for green tea",
            "status": "idle",
            "capacity": 350,  # kg/hour
            "metrics": [
                "drum_surface_temperature", 
                "drum_rotation_speed", 
                "outlet_moisture_content", 
                "steam_pressure", 
                "tea_residence_time"
            ],
            "last_updated": datetime.datetime.utcnow().isoformat()
        },
        
        # Sorting machines
        {
            "id": "vibro-sifter-1",
            "name": "Vibro Sifter 1",
            "process_id": "sorting",
            "description": "Vibration-based leaf sorter",
            "status": "running",
            "capacity": 600,  # kg/hour
            "metrics": [
                "vibration_amplitude", 
                "vibration_frequency", 
                "feed_rate", 
                "mesh_size", 
                "separation_efficiency"
            ],
            "last_updated": datetime.datetime.utcnow().isoformat()
        },
        {
            "id": "electronic-color-sorter-1",
            "name": "Electronic Color Sorter 1",
            "process_id": "sorting",
            "description": "Camera-based leaf quality sorter",
            "status": "running",
            "capacity": 500,  # kg/hour
            "metrics": [
                "belt_speed", 
                "camera_sensitivity", 
                "ejection_accuracy", 
                "rejection_rate", 
                "throughput_rate"
            ],
            "last_updated": datetime.datetime.utcnow().isoformat()
        },
        
        # Packing machines
        {
            "id": "tea-bagger-1",
            "name": "Tea Bagger 1",
            "process_id": "packing",
            "description": "Tea bag packaging machine",
            "status": "running",
            "capacity": 8000,  # bags/hour
            "metrics": [
                "production_speed", 
                "sealing_temperature", 
                "bag_weight_variance", 
                "tag_attachment_strength", 
                "seal_integrity"
            ],
            "last_updated": datetime.datetime.utcnow().isoformat()
        },
        {
            "id": "bulk-packer-1",
            "name": "Bulk Packer 1",
            "process_id": "packing",
            "description": "Bulk tea packaging machine",
            "status": "idle",
            "capacity": 1200,  # kg/hour
            "metrics": [
                "filling_rate", 
                "packaging_weight_accuracy", 
                "vacuum_pressure", 
                "nitrogen_flush_level", 
                "seal_temperature"
            ],
            "last_updated": datetime.datetime.utcnow().isoformat()
        }
    ]
    
    # Insert machines
    db.machines.insert_many(machines)
    print(f"Inserted {len(machines)} machines")

    # Generate some initial readings
    generate_readings(24)  # Generate readings for the last 24 hours
    
    return machines

# Function to generate a single reading for a machine
def generate_reading(machine, timestamp):
    reading = {
        "machine_id": machine["id"],
        "timestamp": timestamp.isoformat(),
    }
    
    # Withering machine metrics
    if machine["process_id"] == "withering":
        if "ambient_temperature" in machine.get("metrics", []):
            reading["ambient_temperature"] = round(random.uniform(22, 30), 1)  # °C
        if "leaf_moisture" in machine.get("metrics", []):
            reading["leaf_moisture"] = round(random.uniform(60, 85), 1)  # %
        if "air_flow_rate" in machine.get("metrics", []):
            reading["air_flow_rate"] = round(random.uniform(2.0, 4.5), 2)  # m/s
        if "trough_humidity" in machine.get("metrics", []):
            reading["trough_humidity"] = round(random.uniform(65, 95), 1)  # %
        if "fan_speed" in machine.get("metrics", []):
            if machine["status"] == "running":
                reading["fan_speed"] = round(random.uniform(800, 1200), 0)  # RPM
            else:
                reading["fan_speed"] = 0  # RPM
    
    # Rolling machine metrics
    elif machine["process_id"] == "rolling":
        if "orthodox-roller" in machine["id"]:
            if "roller_rpm" in machine.get("metrics", []):
                if machine["status"] == "running":
                    reading["roller_rpm"] = round(random.uniform(60, 80), 1)
                else:
                    reading["roller_rpm"] = 0
            if "pressure_plate_force" in machine.get("metrics", []):
                reading["pressure_plate_force"] = round(random.uniform(2000, 3000), 1)  # N
            if "roller_temperature" in machine.get("metrics", []):
                reading["roller_temperature"] = round(random.uniform(30, 45), 1)  # °C
            if "motor_load" in machine.get("metrics", []):
                reading["motor_load"] = round(random.uniform(50, 90), 1)  # %
            if "leaf_discharge_rate" in machine.get("metrics", []):
                if machine["status"] == "running":
                    reading["leaf_discharge_rate"] = round(random.uniform(150, 200), 1)  # kg/h
                else:
                    reading["leaf_discharge_rate"] = 0
        else:  # CTC machine
            if "cutter_rpm" in machine.get("metrics", []):
                if machine["status"] == "running":
                    reading["cutter_rpm"] = round(random.uniform(400, 500), 0)
                else:
                    reading["cutter_rpm"] = 0
            if "feed_roller_speed" in machine.get("metrics", []):
                if machine["status"] == "running":
                    reading["feed_roller_speed"] = round(random.uniform(20, 30), 1)  # rpm
                else:
                    reading["feed_roller_speed"] = 0
            if "cutter_temperature" in machine.get("metrics", []):
                reading["cutter_temperature"] = round(random.uniform(35, 50), 1)  # °C
            if "motor_load" in machine.get("metrics", []):
                reading["motor_load"] = round(random.uniform(60, 95), 1)  # %
            if "particle_size" in machine.get("metrics", []):
                reading["particle_size"] = round(random.uniform(0.8, 2.0), 2)  # mm
    
    # Fermentation machine metrics
    elif machine["process_id"] == "fermentation":
        if "chamber_temperature" in machine.get("metrics", []):
            reading["chamber_temperature"] = round(random.uniform(24, 32), 1)  # °C
        if "chamber_humidity" in machine.get("metrics", []):
            reading["chamber_humidity"] = round(random.uniform(85, 95), 1)  # %
        if "oxygen_concentration" in machine.get("metrics", []):
            reading["oxygen_concentration"] = round(random.uniform(18, 21), 1)  # %
        if "air_circulation_speed" in machine.get("metrics", []):
            if machine["status"] == "running":
                reading["air_circulation_speed"] = round(random.uniform(0.5, 1.5), 2)  # m/s
            else:
                reading["air_circulation_speed"] = 0
        if "enzyme_activity_index" in machine.get("metrics", []):
            # Higher for running machines, lower for idle or maintenance
            if machine["status"] == "running":
                reading["enzyme_activity_index"] = round(random.uniform(70, 100), 1)
            elif machine["status"] == "idle":
                reading["enzyme_activity_index"] = round(random.uniform(10, 30), 1)
            else:
                reading["enzyme_activity_index"] = round(random.uniform(0, 10), 1)
    
    # Drying machine metrics
    elif machine["process_id"] == "drying":
        if "fluid-bed" in machine["id"]:
            if "heating_coil_temperature" in machine.get("metrics", []):
                if machine["status"] == "running":
                    reading["heating_coil_temperature"] = round(random.uniform(110, 150), 1)  # °C
                else:
                    reading["heating_coil_temperature"] = round(random.uniform(20, 30), 1)
            if "outlet_air_temperature" in machine.get("metrics", []):
                if machine["status"] == "running":
                    reading["outlet_air_temperature"] = round(random.uniform(70, 90), 1)  # °C
                else:
                    reading["outlet_air_temperature"] = round(random.uniform(20, 30), 1)
            if "inlet_air_temperature" in machine.get("metrics", []):
                if machine["status"] == "running":
                    reading["inlet_air_temperature"] = round(random.uniform(120, 140), 1)  # °C
                else:
                    reading["inlet_air_temperature"] = round(random.uniform(20, 30), 1)
            if "air_flow_velocity" in machine.get("metrics", []):
                if machine["status"] == "running":
                    reading["air_flow_velocity"] = round(random.uniform(3.0, 5.0), 2)  # m/s
                else:
                    reading["air_flow_velocity"] = 0
            if "tea_moisture_content" in machine.get("metrics", []):
                reading["tea_moisture_content"] = round(random.uniform(2.5, 7.0), 1)  # %
            if "fuel_consumption" in machine.get("metrics", []):
                if machine["status"] == "running":
                    reading["fuel_consumption"] = round(random.uniform(15, 25), 1)  # kg/h
                else:
                    reading["fuel_consumption"] = 0
        else:  # Drum dryer
            if "drum_surface_temperature" in machine.get("metrics", []):
                if machine["status"] == "running":
                    reading["drum_surface_temperature"] = round(random.uniform(100, 120), 1)  # °C
                else:
                    reading["drum_surface_temperature"] = round(random.uniform(20, 30), 1)
            if "drum_rotation_speed" in machine.get("metrics", []):
                if machine["status"] == "running":
                    reading["drum_rotation_speed"] = round(random.uniform(4, 8), 1)  # rpm
                else:
                    reading["drum_rotation_speed"] = 0
            if "outlet_moisture_content" in machine.get("metrics", []):
                reading["outlet_moisture_content"] = round(random.uniform(3.0, 8.0), 1)  # %
            if "steam_pressure" in machine.get("metrics", []):
                if machine["status"] == "running":
                    reading["steam_pressure"] = round(random.uniform(3.0, 5.0), 2)  # bar
                else:
                    reading["steam_pressure"] = 0
            if "tea_residence_time" in machine.get("metrics", []):
                reading["tea_residence_time"] = round(random.uniform(15, 25), 1)  # minutes
    
    # Sorting machine metrics
    elif machine["process_id"] == "sorting":
        if "vibro-sifter" in machine["id"]:
            if "vibration_amplitude" in machine.get("metrics", []):
                if machine["status"] == "running":
                    reading["vibration_amplitude"] = round(random.uniform(2.0, 4.0), 2)  # mm
                else:
                    reading["vibration_amplitude"] = 0
            if "vibration_frequency" in machine.get("metrics", []):
                if machine["status"] == "running":
                    reading["vibration_frequency"] = round(random.uniform(15, 25), 1)  # Hz
                else:
                    reading["vibration_frequency"] = 0
            if "feed_rate" in machine.get("metrics", []):
                if machine["status"] == "running":
                    reading["feed_rate"] = round(random.uniform(400, 600), 0)  # kg/h
                else:
                    reading["feed_rate"] = 0
            if "mesh_size" in machine.get("metrics", []):
                reading["mesh_size"] = round(random.choice([0.8, 1.0, 1.2, 1.4, 1.6, 1.8]), 1)  # mm
            if "separation_efficiency" in machine.get("metrics", []):
                if machine["status"] == "running":
                    reading["separation_efficiency"] = round(random.uniform(80, 98), 1)  # %
                else:
                    reading["separation_efficiency"] = 0
        else:  # Electronic color sorter
            if "belt_speed" in machine.get("metrics", []):
                if machine["status"] == "running":
                    reading["belt_speed"] = round(random.uniform(0.5, 1.2), 2)  # m/s
                else:
                    reading["belt_speed"] = 0
            if "camera_sensitivity" in machine.get("metrics", []):
                reading["camera_sensitivity"] = round(random.uniform(80, 95), 1)  # %
            if "ejection_accuracy" in machine.get("metrics", []):
                if machine["status"] == "running":
                    reading["ejection_accuracy"] = round(random.uniform(90, 99), 1)  # %
                else:
                    reading["ejection_accuracy"] = 0
            if "rejection_rate" in machine.get("metrics", []):
                reading["rejection_rate"] = round(random.uniform(1.0, 5.0), 2)  # %
            if "throughput_rate" in machine.get("metrics", []):
                if machine["status"] == "running":
                    reading["throughput_rate"] = round(random.uniform(400, 500), 0)  # kg/h
                else:
                    reading["throughput_rate"] = 0
    
    # Packing machine metrics
    elif machine["process_id"] == "packing":
        if "tea-bagger" in machine["id"]:
            if "production_speed" in machine.get("metrics", []):
                if machine["status"] == "running":
                    reading["production_speed"] = round(random.uniform(6000, 8000), 0)  # bags/h
                else:
                    reading["production_speed"] = 0
            if "sealing_temperature" in machine.get("metrics", []):
                if machine["status"] == "running":
                    reading["sealing_temperature"] = round(random.uniform(170, 190), 1)  # °C
                else:
                    reading["sealing_temperature"] = round(random.uniform(20, 30), 1)
            if "bag_weight_variance" in machine.get("metrics", []):
                reading["bag_weight_variance"] = round(random.uniform(0.05, 0.15), 2)  # g
            if "tag_attachment_strength" in machine.get("metrics", []):
                reading["tag_attachment_strength"] = round(random.uniform(85, 100), 1)  # %
            if "seal_integrity" in machine.get("metrics", []):
                if machine["status"] == "running":
                    reading["seal_integrity"] = round(random.uniform(90, 100), 1)  # %
                elif machine["status"] == "fault":
                    reading["seal_integrity"] = round(random.uniform(60, 85), 1)  # %
                else:
                    reading["seal_integrity"] = 0
        else:  # Bulk packer
            if "filling_rate" in machine.get("metrics", []):
                if machine["status"] == "running":
                    reading["filling_rate"] = round(random.uniform(1000, 1200), 0)  # kg/h
                else:
                    reading["filling_rate"] = 0
            if "packaging_weight_accuracy" in machine.get("metrics", []):
                reading["packaging_weight_accuracy"] = round(random.uniform(98, 101), 1)  # % of target
            if "vacuum_pressure" in machine.get("metrics", []):
                if machine["status"] == "running":
                    reading["vacuum_pressure"] = round(random.uniform(0.8, 0.95), 2)  # bar
                else:
                    reading["vacuum_pressure"] = 0
            if "nitrogen_flush_level" in machine.get("metrics", []):
                if machine["status"] == "running":
                    reading["nitrogen_flush_level"] = round(random.uniform(95, 99), 1)  # %
                else:
                    reading["nitrogen_flush_level"] = 0
            if "seal_temperature" in machine.get("metrics", []):
                if machine["status"] == "running":
                    reading["seal_temperature"] = round(random.uniform(160, 180), 1)  # °C
                else:
                    reading["seal_temperature"] = round(random.uniform(20, 30), 1)
        
    return reading

# Function to generate historical readings
def generate_readings(hours_back):
    print(f"Generating historical data for the past {hours_back} hours...")
    current_time = datetime.datetime.utcnow()
    readings = []
    
    # Get all machines
    machines = list(db.machines.find({}))
    
    # Generate readings for each hour
    for hour_offset in range(hours_back, 0, -1):
        timestamp = current_time - datetime.timedelta(hours=hour_offset)
        
        # Generate readings for each machine
        for machine in machines:
            reading = generate_reading(machine, timestamp)
            readings.append(reading)
    
    # Insert readings
    if readings:
        db.readings.insert_many(readings)
        print(f"Inserted {len(readings)} historical machine readings")

# Function to continuously update machine statuses and readings
def continuous_update(interval=1):
    """
    Continuously update machine statuses and readings
    
    Args:
        interval: Time in seconds between updates
    """
    iteration = 0
    
    try:
        while running:
            iteration += 1
            current_time = datetime.datetime.utcnow()
            
            if iteration % 5 == 0:  # Print status update every 5 iterations
                print(f"\rIteration {iteration} at {current_time.strftime('%H:%M:%S')}", end='', flush=True)
            
            # Get all machines
            machines = list(db.machines.find({}))
            readings = []
            
            # Update each machine
            for machine in machines:
                # Random status updates (2% chance to change status)
                if random.random() < 0.02:
                    new_status = random.choices(
                        ["running", "idle", "maintenance", "fault"],
                        weights=[0.6, 0.2, 0.15, 0.05],
                        k=1
                    )[0]
                    
                    print(f"\nMachine {machine['name']} status changed: {machine.get('status', 'unknown')} → {new_status}")
                    
                    # Update machine status in database
                    db.machines.update_one(
                        {"id": machine["id"]},
                        {"$set": {
                            "status": new_status,
                            "last_updated": current_time.isoformat()
                        }}
                    )
                    
                    # Update the machine object's status for reading generation
                    machine["status"] = new_status
                
                # Generate a new reading for this machine
                reading = generate_reading(machine, current_time)
                readings.append(reading)
            
            # Insert all readings at once
            if readings:
                db.readings.insert_many(readings)
            
            # Clean old readings periodically to prevent database bloat
            if iteration % 300 == 0:  # Every ~5 minutes
                clean_old_readings(max_age_hours=2)  # Keep last 2 hours of readings
                
            # Sleep until next update
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\nContinuous updates stopped by user")

# Function to clean old readings to prevent database bloat
def clean_old_readings(max_age_hours=12):
    """Remove readings older than max_age_hours to prevent database bloat"""
    cutoff_time = datetime.datetime.utcnow() - datetime.timedelta(hours=max_age_hours)
    result = db.readings.delete_many({"timestamp": {"$lt": cutoff_time.isoformat()}})
    if result.deleted_count > 0:
        print(f"\nCleaned {result.deleted_count} readings older than {max_age_hours} hours")

# Signal handler for graceful shutdown
def signal_handler(sig, frame):
    global running
    print("\nShutting down test data generator...")
    running = False

# Main function
def main():
    print("Tea Processing Monitor - Test Data Generator")
    print("===========================================")
    
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    # Initialize data if needed
    if db.machines.count_documents({}) == 0:
        machines = initialize_data()
    else:
        print("Using existing data in database")
        machines = list(db.machines.find({}))
        
    # Clean old readings
    clean_old_readings()
    
    # Start continuous updates
    print("\nStarting continuous updates at 1-second intervals")
    print("Press Ctrl+C to stop the data generator\n")
    continuous_update(interval=1)  # Update every 1 second

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)
    finally:
        print("Test data generator terminated")
