from flask import g, session
import datetime
import random
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
import certifi

# Define technical specifications for each machine type
MACHINE_SPECS = {
    "withering": {
        "model": "DL-6CWD-580",
        "dimensions": "1000×1050×5800 mm",
        "voltage": "380/50 V/Hz",
        "heating_type": "Heating wire",
        "power_set": "15KW / 3 Group",
        "fan_motor_power": "250 W",
        "fan_motor_speed": "2200 r/min",
        "fan_motor_voltage": "220 V",
        "tray_size": "980×5000×200 mm",
        "efficiency": "200 kg/time",
        "manufacturer": "Tea Tech Solutions"
    },
    "rolling": {
        "model": "DL-6CRT-65",
        "dimensions": "1490×1390×1420 mm",
        "voltage": "380/50 V/Hz",
        "disc_diameter": "1210 mm",
        "barrel_diameter": "650 mm",
        "barrel_height": "480 mm",
        "motor_power": "3 kW",
        "motor_speed": "1400 RPM",
        "barrel_speed": "44 RPM",
        "productivity": "120 Kg/h",
        "max_capacity": "40 kg",
        "manufacturer": "Tea Tech Solutions"
    },
    "fermentation": {
        "model": "ZC-6CFJ-60",
        "dimensions": "1130×1100×2040 mm",
        "voltage": "220/50 V/Hz",
        "heating_mode": "Heating wire",
        "heating_power": "6.0 KW",
        "heating_group": "1 Group",
        "fan_motor_power": "85 W",
        "fan_motor_speed": "2200 rpm",
        "fan_motor_voltage": "220 V",
        "tray_size": "720×520×100 mm",
        "tray_quantity": "14 pcs",
        "tray_layers": "7",
        "efficiency": "150 kg/time",
        "manufacturer": "Tea Tech Solutions"
    },
    "drying": {
        "model": "DL-6CHZ-14",
        "dimensions": "1430×1630×2320 mm",
        "voltage": "380/50 V/Hz",
        "heating_element": "Electric heating wire",
        "total_power": "14.5 kW / 3 group",
        "rotary_speed": "6 rpm",
        "rotary_type": "Round",
        "drying_area": "14.5 m²",
        "drying_layers": "16",
        "efficiency": "60-75 kg/time",
        "manufacturer": "Tea Tech Solutions"
    },
    "sorting": {
        "model": "ZC-6CSST-100R",
        "dimensions": "1750×1450×1570 mm",
        "voltage": "380/50 V/Hz",
        "inner_barrel_diameter": "1000 mm",
        "inner_barrel_length": "1000 mm",
        "heating_power": "18 kW",
        "barrel_speed": "36 r/min",
        "sieve_sizes": "2/2.5/3/5/6 mm",
        "manufacturer": "Tea Tech Solutions"
    },
    "packing": {
        "model": "DL-6CND-16",
        "dimensions": "450×560×920 mm",
        "voltage": "220 V",
        "bag_width": "70 mm",
        "bag_length_range": "35-100 mm",
        "endometrial_bag_width": "160 mm",
        "efficiency": "6 kg/h (7g)",
        "manufacturer": "Tea Tech Solutions"
    }
}

def init_db(app):
    """
    Initialize database connection
    
    Args:
        app: Flask application instance
    """
    @app.before_request
    def before_request():
        """Connect to MongoDB before each request"""
        # If we're running on Render, use our get_db function which handles connection details
        # This ensures consistent connection handling between the before_request and other functions
        if hasattr(g, 'db'):  # Already connected
            return
            
        try:
            # Use the proper get_db function to ensure consistent connection handling
            # with the same config and fallback mechanism
            get_db()
            print("Database connection established for request")
        except Exception as e:
            print(f"Error connecting to database in before_request: {e}")
            # Try to establish connection directly to local database as last resort
            try:
                from flask import current_app
                mongo_options = current_app.config.get('MONGO_OPTIONS', {})
                local_mongo_client = MongoClient(current_app.config['LOCAL_MONGO_URI'], **mongo_options)
                local_mongo_client.admin.command('ping')  # Test connection
                
                g.mongo_client = local_mongo_client
                g.db = local_mongo_client.get_database()
                current_app.config['USING_LOCAL_DB'] = True
                print("Emergency fallback to local database successful")
            except Exception as local_error:
                print(f"Emergency local database connection also failed: {local_error}")
                # Even if there's an error, we'll continue to avoid breaking the whole app
    
    @app.teardown_request
    def teardown_request(exception=None):
        """Close MongoDB connection after each request"""
        mongo_client = g.pop('mongo_client', None)
        if mongo_client is not None:
            mongo_client.close()

def get_db():
    """
    Get the database connection from the flask global object.
    Will try to connect to the primary MongoDB first, and if that fails,
    will fall back to a local MongoDB instance (except on Render.com).
    
    Returns:
        pymongo.database.Database: MongoDB database connection
        
    Raises:
        RuntimeError: If neither default nor local database connection is available
    """
    if not hasattr(g, 'db'):
        from flask import current_app, has_request_context, has_app_context
        
        # If we're in a request context or app context, we can establish a DB connection
        if has_request_context() or has_app_context():
            # Check if we're already configured to use local database
            # If so, skip the primary connection attempts to avoid SSL errors
            mongo_options = current_app.config.get('MONGO_OPTIONS', {})
            is_render = current_app.config.get('IS_RENDER', False)
            using_local_db = current_app.config.get('USING_LOCAL_DB', False)
            
            # If we're already configured to use local DB, go straight to local connection
            if using_local_db and not is_render:
                print("Using cached local database configuration")
                try:
                    local_mongo_client = MongoClient(current_app.config['LOCAL_MONGO_URI'], **mongo_options)
                    local_mongo_client.admin.command('ping')  # Test connection
                    
                    g.mongo_client = local_mongo_client
                    g.db = local_mongo_client.get_database()
                    return g.db
                    
                except Exception as local_error:
                    print(f"Cached local database connection failed: {local_error}")
                    # Fall through to try primary connection
                    using_local_db = False
                    current_app.config['USING_LOCAL_DB'] = False
            
            # Try primary database connection
            max_retries = 3 if is_render else 1
            retry_delay = 2  # Start with 2 seconds, will be doubled each retry
            
            primary_error = None
            for attempt in range(max_retries):
                try:
                    # Import SSL modules to configure them properly
                    import ssl
                    import certifi
                    
                    # Try primary MongoDB connection with adjusted TLS settings
                    # Use system CA certificates on Render.com, otherwise use certifi
                    if is_render:
                        mongo_client = MongoClient(current_app.config['MONGO_URI'], **mongo_options)
                    else:
                        # For local development, use certifi's certificates
                        mongo_client = MongoClient(
                            current_app.config['MONGO_URI'],
                            tls=True,
                            tlsCAFile=certifi.where(),
                            **mongo_options
                        )
                    
                    mongo_client.admin.command('ping')  # Test connection
                    
                    g.mongo_client = mongo_client
                    g.db = mongo_client.get_database()
                    current_app.config['USING_LOCAL_DB'] = False
                    
                    if attempt > 0:  # Only log success after retries
                        print(f"Connected to primary MongoDB database after {attempt+1} attempts")
                    
                    return g.db
                
                except Exception as e:
                    primary_error = e
                    if attempt < max_retries - 1:
                        print(f"Connection attempt {attempt+1} failed: {e}. Retrying in {retry_delay}s...")
                        import time
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                    else:
                        print(f"All {max_retries} connection attempts to primary database failed.")
            
            # Only attempt local fallback if NOT on Render.com
            if not is_render:
                print(f"Error connecting to primary database: {primary_error}")
                print("Attempting to connect to local MongoDB fallback...")
                
                try:
                    local_mongo_client = MongoClient(current_app.config['LOCAL_MONGO_URI'], **mongo_options)
                    local_mongo_client.admin.command('ping')  # Test connection
                    
                    g.mongo_client = local_mongo_client
                    g.db = local_mongo_client.get_database()
                    current_app.config['USING_LOCAL_DB'] = True
                    print("Connected to local MongoDB database as fallback")
                    
                except Exception as local_error:
                    print(f"Error connecting to local database fallback: {local_error}")
                    raise RuntimeError(f"Failed to establish any database connection. Primary: {primary_error}, Local: {local_error}")
            else:
                # On Render.com, we don't have a local fallback option
                raise RuntimeError(f"Failed to establish database connection on Render.com: {primary_error}")
        else:
            # We're not in a request context or app context and have no DB
            raise RuntimeError("Database connection not available outside Flask context")
            
    return g.db

def clean_database():
    """
    Clean all collections in the database
    """
    db = get_db()
    # Drop all collectionss
    db.processes.drop()
    db.machines.drop()
    db.withering_data.drop()
    db.rolling_data.drop()
    db.fermentation_data.drop()
    db.drying_data.drop()
    db.sorting_data.drop()
    db.packing_data.drop()
    print("Database cleaned successfully")

def initialize_models():
    """
    Initialize the database with tea processing models
    """
    db = get_db()
    
    # Define tea processing stages
    processes = [
        {
            "id": "withering",
            "name": "Withering (Wilting)",
            "description": "First stage where fresh tea leaves lose moisture and become soft and pliable",
            "order": 1,
            "data_collection": "withering_data"
        },
        {
            "id": "rolling",
            "name": "Rolling and Shaping",
            "description": "Process that breaks down leaf cells to release enzymes and essential oils",
            "order": 2,
            "data_collection": "rolling_data"
        },
        {
            "id": "fermentation",
            "name": "Fermentation (Oxidation)",
            "description": "Chemical reactions that change leaf color, flavor, and aroma",
            "order": 3,
            "data_collection": "fermentation_data"
        },
        {
            "id": "drying",
            "name": "Drying (Firing)",
            "description": "Halts oxidation and reduces moisture content to preserve tea",
            "order": 4,
            "data_collection": "drying_data"
        },
        {
            "id": "sorting",
            "name": "Sorting and Grading",
            "description": "Classification of processed tea leaves by size, appearance, and quality",
            "order": 5,
            "data_collection": "sorting_data"
        },
        {
            "id": "packing",
            "name": "Packing and Packaging",
            "description": "Final stage where tea is packaged for shipping and consumption",
            "order": 6,
            "data_collection": "packing_data"
        }
    ]
    
    # Define machines for each process with detailed metrics and proper image URLs
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
            "image_url": "images/WitheringTrough.png",
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
            "image_url": "images/WitheringTrough.png",
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
            "image_url": "images/WitheringTrough.png",
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
            "image_url": "images/Orthodox Roller.png",
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
            "image_url": "images/CTC Machine.png",
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
            "image_url": "images/Fermentation Chamber.png",
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
            "image_url": "images/Fermentation Chamber.png",
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
            "image_url": "images/Fluid Bed Dryer.png",
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
            "image_url": "images/Drum Dryer.png",
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
            "image_url": "images/Vibro Sifter.png",
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
            "image_url": "images/Electronic Color Sorter.png",
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
            "image_url": "images/Tea Bagger.png",
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
            "image_url": "images/Bulk Packer.png",
            "last_updated": datetime.datetime.utcnow().isoformat()
        }
    ]
    
    # Insert processes and machines
    if db.processes.count_documents({}) == 0:
        db.processes.insert_many(processes)
        print(f"Inserted {len(processes)} tea processing stages")
    
    if db.machines.count_documents({}) == 0:
        db.machines.insert_many(machines)
        print(f"Inserted {len(machines)} machines")
    
    return processes, machines

# Function to generate a single reading for a machine
def generate_reading(machine):
    """
    Generate a single reading for a given machine
    
    Args:
        machine (dict): The machine to generate a reading for
        
    Returns:
        dict: The generated reading
    """
    timestamp = datetime.datetime.utcnow()
    reading = {
        "machine_id": machine["id"],
        "timestamp": timestamp.isoformat(),
    }
    
    # Add common metrics for all machines
    # Voltage reading - based on machine specs voltage (380V or 220V)
    voltage_base = 380 if machine["process_id"] in ["withering", "rolling", "drying", "sorting"] else 220
    voltage_variation = random.uniform(-5, 5)  # ±5V variation
    reading["voltage"] = round(voltage_base + voltage_variation, 1)  # V
    
    # Heating wire temperature - for machines that use heating elements
    if machine["process_id"] in ["withering", "fermentation", "drying"]:
        # Base temperature varies by process
        if machine["process_id"] == "withering":
            temp_base = 80  # °C
            temp_variation = random.uniform(-3, 3)
        elif machine["process_id"] == "fermentation":
            temp_base = 60  # °C  
            temp_variation = random.uniform(-2, 2)
        elif machine["process_id"] == "drying":
            temp_base = 120  # °C
            temp_variation = random.uniform(-5, 5)
            
        reading["heating_wire_temperature"] = round(temp_base + temp_variation, 1)  # °C
    
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

def generate_readings():
    """Generate readings for all machines and store them in their respective process collections"""
    db = get_db()
    machines = list(db.machines.find({}, {"_id": 0}))
    processes = {p["id"]: p for p in db.processes.find({}, {"_id": 0})}
    
    readings_by_process = {
        "withering": [],
        "rolling": [],
        "fermentation": [],
        "drying": [],
        "sorting": [],
        "packing": []
    }
    
    # Generate readings for each machine
    for machine in machines:
        reading = generate_reading(machine)
        process_id = machine["process_id"]
        readings_by_process[process_id].append(reading)
    
    # Insert readings into respective process collections
    for process_id, readings in readings_by_process.items():
        if readings:
            collection_name = processes[process_id]["data_collection"]
            db[collection_name].insert_many(readings)
            from flask import current_app
            if getattr(current_app, 'testing', True):
                print(f"Generated {len(readings)} readings for {process_id}")
    
    return True

def update_machine_statuses():
    """Randomly update some machine statuses"""
    db = get_db()
    machines = list(db.machines.find({}))
    current_time = datetime.datetime.utcnow()
    
    for machine in machines:
        # 2% chance to change status
        if random.random() < 0.02:
            new_status = random.choices(
                ["running", "idle", "maintenance", "fault"],
                weights=[0.6, 0.2, 0.15, 0.05],
                k=1
            )[0]
            
            db.machines.update_one(
                {"_id": machine["_id"]},
                {"$set": {
                    "status": new_status,
                    "last_updated": current_time.isoformat()
                }}
            )
            print(f"Machine {machine['name']} status updated to {new_status}")

def get_latest_readings(machine_id):
    """
    Get the latest readings for a machine from the appropriate process collection
    
    Args:
        machine_id (str): The ID of the machine
        
    Returns:
        dict: The latest reading
    """
    db = get_db()
    machine = db.machines.find_one({"id": machine_id}, {"_id": 0})
    
    if not machine:
        return None
    
    process = db.processes.find_one({"id": machine["process_id"]}, {"_id": 0})
    collection_name = process["data_collection"]
    
    reading = db[collection_name].find_one(
        {"machine_id": machine_id},
        {"_id": 0},
        sort=[("timestamp", -1)]
    )
    
    return reading

def get_historical_readings(machine_id, limit=100):
    """
    Get historical readings for a machine from the appropriate process collection
    
    Args:
        machine_id (str): The ID of the machine
        limit (int): Maximum number of readings to return
        
    Returns:
        list: Historical readings
    """
    db = get_db()
    machine = db.machines.find_one({"id": machine_id}, {"_id": 0})
    
    if not machine:
        return []
    
    process = db.processes.find_one({"id": machine["process_id"]}, {"_id": 0})
    collection_name = process["data_collection"]
    
    readings = list(db[collection_name].find(
        {"machine_id": machine_id},
        {"_id": 0},
        sort=[("timestamp", -1)],
        limit=limit
    ))
    
    return readings

def register_user(email, password):
    db = get_db()
    if db.users.find_one({"email": email}):
        return False, "Email already registered."
    hashed_password = generate_password_hash(password)
    db.users.insert_one({"email": email, "password": hashed_password})
    return True, "Registration successful."

def authenticate_user(email, password):
    db = get_db()
    user = db.users.find_one({"email": email})
    if user and check_password_hash(user["password"], password):
        session['user_id'] = str(user['_id'])
        
        # If we're using the local database, try to sync with primary DB
        from flask import current_app
        if current_app.config.get('USING_LOCAL_DB', False):
            try:
                sync_success = sync_local_to_primary_db()
                if sync_success:
                    return True, "Login successful. Local data has been synchronized with cloud database."
            except Exception as e:
                print(f"Error during database sync attempt: {e}")
                # Continue with login even if sync fails
        
        return True, "Login successful."
    return False, "Invalid email or password."

def logout_user():
    session.pop('user_id', None)

def sync_local_to_primary_db():
    """
    Synchronize data from local MongoDB to primary MongoDB.
    This function should be called when:
    1. A user logs in successfully
    2. The application detects that it's been using the local database
    3. The primary database is now available
    
    Returns:
        bool: True if synchronization was successful, False otherwise
    """
    from flask import current_app
    
    # Only attempt sync if we're currently using the local database
    if not current_app.config.get('USING_LOCAL_DB', False):
        print("Not using local DB, no sync needed")
        return False
    
    try:
        # Connect to local database (our current connection)
        local_db = get_db()
        
        # Try to connect to the primary database
        mongo_options = current_app.config.get('MONGO_OPTIONS', {})
        primary_client = MongoClient(current_app.config['MONGO_URI'], **mongo_options)
        
        # Test the connection to the primary database
        primary_client.admin.command('ping')
        primary_db = primary_client.get_database()
        
        # Collections to sync
        collections = ['processes', 'machines', 'readings', 'users', 'alerts']
        
        for collection_name in collections:
            if collection_name not in local_db.list_collection_names():
                continue
                
            print(f"Syncing {collection_name} collection...")
            
            # Get all documents from local collection
            local_docs = list(local_db[collection_name].find({}))
            
            if not local_docs:
                continue
                
            # For each document in local collection, upsert to primary
            for doc in local_docs:
                # Use the _id as the unique identifier for upsert
                if '_id' in doc:
                    primary_db[collection_name].replace_one(
                        {'_id': doc['_id']}, 
                        doc, 
                        upsert=True
                    )
        
        print("Database synchronization completed successfully")
        
        # Switch to the primary database connection
        g.mongo_client.close()  # Close local connection
        g.mongo_client = primary_client
        g.db = primary_db
        current_app.config['USING_LOCAL_DB'] = False
        
        return True
        
    except Exception as e:
        print(f"Error during database synchronization: {e}")
        import traceback
        traceback.print_exc()
        return False