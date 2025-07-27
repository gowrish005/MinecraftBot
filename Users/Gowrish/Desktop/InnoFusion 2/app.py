from flask import Flask, request
from routes import register_routes
from models import init_db, clean_database, initialize_models, generate_readings
from controllers import get_process_data
import threading
import time
import os
from pymongo import MongoClient
from config import Config

app = Flask(__name__, 
            static_url_path='', 
            static_folder='static',
            template_folder='templates')

# Add custom domains to trusted hosts
@app.before_request
def validate_host():
    if request.host not in Config.ALLOWED_HOSTS:
        allowed_hosts = ', '.join(Config.ALLOWED_HOSTS)
        print(f"Warning: Request with unknown host: {request.host}. Allowed hosts: {allowed_hosts}")

# Load configuration from Config class
app.config.from_object(Config)

# Toggle this to enable/disable test/console output
app.testing = Config.TESTING

# Initialize database
init_db(app)

# Background data generation thread
def background_data_generation():
    """Generate data in the background every 30 seconds"""
    with app.app_context():
        while True:
            try:
                # Use the get_db() function which handles fallback to local MongoDB
                from flask import g
                from models import get_db
                
                try:
                    # Get database with fallback mechanism
                    db = get_db()
                          # Generate new readings with timeout guard (platform-specific)
                    import platform
                    
                    if platform.system() != "Windows":  # signal.SIGALRM not available on Windows
                        import signal
                        
                        def timeout_handler(signum, frame):
                            raise TimeoutError("Readings generation timed out")
                            
                        # Set a 20 second timeout for this operation
                        signal.signal(signal.SIGALRM, timeout_handler)
                        signal.alarm(20)
                    
                    generate_readings()
                    
                    # Cancel the timeout if not on Windows
                    if platform.system() != "Windows":
                        signal.alarm(0)
                    
                    # If it was a successful operation and we're using local DB, try to sync
                    if app.config.get('USING_LOCAL_DB', False):
                        from models import sync_local_to_primary_db
                        try:
                            sync_local_to_primary_db()
                        except Exception as sync_error:
                            print(f"Background sync error: {sync_error}")
                    
                except TimeoutError as e:
                    print(f"Timeout error in background data generation: {e}")
                finally:
                    # Make sure we close the connection if it exists
                    if hasattr(g, 'mongo_client'):
                        g.mongo_client.close()
                
            except Exception as e:
                if getattr(app, 'testing', True):
                    print(f"Error in background data generation: {e}")
            
            # Sleep for 30 seconds before next cycle
            time.sleep(30)

# Add context processor to make processes data available to all templates
@app.context_processor
def inject_processes():
    """Make processes data available to all templates"""    
    try:
        # Use our get_db function which handles fallback
        from flask import g
        from models import get_db
        
        try:
            # Get database with fallback mechanism
            db = get_db()
              # Get the process data with a timeout guard (platform-specific)
            import platform
            
            if platform.system() != "Windows":  # signal.SIGALRM not available on Windows
                import signal
                
                def timeout_handler(signum, frame):
                    raise TimeoutError("Process data retrieval timed out")
                    
                # Set a 10 second timeout for this operation
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(10)
            
            processes = get_process_data()
            
            # Cancel the timeout if not on Windows
            if platform.system() != "Windows":
                signal.alarm(0)
            
            return {'processes': processes}
        except TimeoutError as e:
            if getattr(app, 'testing', True):
                print(f"Timeout error: {e}")
            if hasattr(g, 'mongo_client'):
                g.mongo_client.close()
            return {'processes': []}
        except Exception as e:
            if getattr(app, 'testing', True):
                print(f"Error getting process data in context processor: {e}")
                import traceback
                traceback.print_exc()
            # Close the connection if error
            if hasattr(g, 'mongo_client'):
                g.mongo_client.close()
            return {'processes': []}
    except Exception as e:
        # In case of error, return an empty list to prevent the app from crashing
        if getattr(app, 'testing', True):
            print(f"Error in inject_processes context processor: {e}")
            import traceback
            traceback.print_exc()
        return {'processes': []}

# Register routes
register_routes(app)

if __name__ == '__main__':
    # Clean and initialize database on startup if not skipped
    if not app.config.get('SKIP_DB_INIT', False):
        with app.app_context():
            try:
                # Use our get_db function which handles fallback
                from flask import g
                from models import get_db
                
                try:
                    # Get database connection with fallback
                    db = get_db()
                    
                    # Initialize the database
                    clean_database()
                    initialize_models()
                    generate_readings()  # Generate initial readings
                    
                    print(f"Database initialized successfully. Using {'local' if app.config.get('USING_LOCAL_DB', False) else 'primary'} database.")
                    
                except Exception as e:
                    print(f"Error in database operations: {e}")
                    import traceback
                    traceback.print_exc()
                finally:
                    # Close the connection if it exists
                    if hasattr(g, 'mongo_client'):
                        g.mongo_client.close()
                        
            except Exception as e:
                print(f"Error initializing database: {e}")
                print("Continuing without database initialization.")
      # Start background data generation
    bg_thread = threading.Thread(target=background_data_generation)
    bg_thread.daemon = True  # Thread will exit when main thread exits
    bg_thread.start()
    
    # Get port from environment variable or use default
    port = int(os.environ.get('PORT', 5000))
    
    # Run the app
    app.run(host='0.0.0.0', port=port, debug=app.config['DEBUG'])