import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
try:
    load_dotenv()
except Exception as e:
    print(f"Warning: Could not load .env file: {e}")
    print("Continuing with default values.")

# Configuration class with default values and environment variable overrides
class Config:
    # MongoDB settings - Primary Cloud MongoDB
    # Add TLS and SSL configuration to fix Render.com SSL handshake issues
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb+srv://gowrish:ftG3flLkxYpdZ0tN@cluster0.el1hbyt.mongodb.net/gowrish?retryWrites=true&w=majority&appName=Cluster0&tls=true&tlsAllowInvalidCertificates=false')
    
    # Local MongoDB fallback
    LOCAL_MONGO_URI = os.getenv('LOCAL_MONGO_URI', 'mongodb://localhost:27017/tea_processing')
    
    # Flag to indicate if we're using local DB as fallback
    USING_LOCAL_DB = False
    
    # MongoDB connection options
    MONGO_OPTIONS = {
        'serverSelectionTimeoutMS': 5000,  # 5 second timeout for server selection
        'connectTimeoutMS': 10000,         # 10 second timeout for connections
        'socketTimeoutMS': 20000,          # 20 second socket timeout 
    }
    
    # Secret key for session
    SECRET_KEY = os.getenv('SECRET_KEY', 'I3BBj0F90y')
    
    # Application settings
    DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 't')
    TESTING = os.getenv('TESTING', 'False').lower() in ('true', '1', 't')
    
    # Set to True to skip database initialization on startup (useful for production)
    SKIP_DB_INIT = os.getenv('SKIP_DB_INIT', 'False').lower() in ('true', '1', 't')
      # Allowed domains for CORS and trusted hosts
    ALLOWED_HOSTS = ['leaf-logic-ai.onrender.com', 'www.leaflogic.pro', 'leaflogic.pro', 'localhost', '127.0.0.1', '0.0.0.0']
    
    # Detect if running on Render.com
    IS_RENDER = os.environ.get('RENDER', False)
      # Render-specific settings
    if IS_RENDER:
        # On Render.com we can't use a local MongoDB fallback
        # So we'll set a longer timeout for the primary database
        MONGO_OPTIONS = {
            'serverSelectionTimeoutMS': 30000,    # 30 seconds for server selection
            'connectTimeoutMS': 30000,            # 30 seconds for connections
            'socketTimeoutMS': 45000,             # 45 seconds socket timeout
            'maxPoolSize': 50,                    # Increase connection pool size
            'minPoolSize': 10,                    # Minimum connections to keep open
            'maxIdleTimeMS': 30000,               # Close idle connections after 30 seconds
            'retryWrites': True,                  # Enable retry for write operations
            'w': 'majority',                      # Write concern for better durability
            'ssl': True,                          # Enable SSL for the connection
            'ssl_cert_reqs': 'CERT_REQUIRED',     # Require certificates
            'tls': True,                          # Enable TLS
            'tlsAllowInvalidCertificates': False, # Don't allow invalid certificates
            'tlsCAFile': '/etc/ssl/certs/ca-certificates.crt'  # Path to CA certs on Render
        }
