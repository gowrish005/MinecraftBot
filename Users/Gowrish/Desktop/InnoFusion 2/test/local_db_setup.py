"""
Local MongoDB setup script for Tea Processing AI Monitor
This script checks if a local MongoDB instance is available and provides instructions for setup if not.
Run this script before starting the application to ensure local database availability.
"""

import subprocess
import sys
import time
import os
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
import platform

def check_mongodb_running():
    """Check if MongoDB is running locally"""
    try:
        # Connect with a short timeout
        client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=2000)
        client.admin.command('ping')  # Will throw an exception if not connected
        print("✓ Local MongoDB is running and available")
        return True
    except ServerSelectionTimeoutError:
        print("✗ Local MongoDB is not running")
        return False
    except Exception as e:
        print(f"✗ Error checking MongoDB status: {e}")
        return False

def install_mongodb_instructions():
    """Print instructions for installing MongoDB based on the OS"""
    system = platform.system().lower()
    
    print("\n=== MongoDB Installation Instructions ===\n")
    
    if system == 'windows':
        print("To install MongoDB on Windows:")
        print("1. Download MongoDB Community Server from: https://www.mongodb.com/try/download/community")
        print("2. Run the installer and follow the instructions")
        print("3. Choose 'Complete' installation and install MongoDB Compass (optional)")
        print("4. Select 'Run service as Network Service user'")
        print("5. After installation, MongoDB should start automatically as a Windows service")
    
    elif system == 'darwin':  # macOS
        print("To install MongoDB on macOS using Homebrew:")
        print("1. Install Homebrew if not already installed: /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
        print("2. Run: brew tap mongodb/brew")
        print("3. Run: brew install mongodb-community")
        print("4. Start MongoDB: brew services start mongodb-community")
    
    elif system == 'linux':
        print("To install MongoDB on Linux (Ubuntu):")
        print("1. Import MongoDB public GPG key:")
        print("   curl -fsSL https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -")
        print("2. Create list file for MongoDB:")
        print("   echo \"deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu $(lsb_release -cs)/mongodb-org/6.0 multiverse\" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list")
        print("3. Update package database:")
        print("   sudo apt-get update")
        print("4. Install MongoDB:")
        print("   sudo apt-get install -y mongodb-org")
        print("5. Start MongoDB:")
        print("   sudo systemctl start mongod")
        print("6. Enable MongoDB to start on boot:")
        print("   sudo systemctl enable mongod")
    
    else:
        print("Please visit the MongoDB documentation to install MongoDB on your system:")
        print("https://docs.mongodb.com/manual/installation/")
    
    print("\nAfter installation, run this script again to verify MongoDB is running correctly.")
    print("\n=====================================\n")

def start_mongodb_if_possible():
    """Try to start MongoDB if it's installed but not running"""
    system = platform.system().lower()
    
    try:
        if system == 'windows':
            # Check if MongoDB is installed as a service
            result = subprocess.run(['sc', 'query', 'MongoDB'], 
                                    capture_output=True, 
                                    text=True)
            
            if "RUNNING" not in result.stdout:
                print("Attempting to start MongoDB service...")
                subprocess.run(['net', 'start', 'MongoDB'], 
                               capture_output=True)
                time.sleep(5)  # Wait for service to start
                return check_mongodb_running()
        
        elif system == 'darwin':  # macOS
            print("Attempting to start MongoDB using Homebrew...")
            subprocess.run(['brew', 'services', 'start', 'mongodb-community'], 
                           capture_output=True)
            time.sleep(5)
            return check_mongodb_running()
        
        elif system == 'linux':
            print("Attempting to start MongoDB service...")
            subprocess.run(['sudo', 'systemctl', 'start', 'mongod'], 
                           capture_output=True)
            time.sleep(5)
            return check_mongodb_running()
            
    except Exception as e:
        print(f"Error while trying to start MongoDB: {e}")
    
    return False

def create_test_database():
    """Create a test database to verify everything is working correctly"""
    try:
        client = MongoClient('mongodb://localhost:27017/')
        db = client.tea_processing_test
        
        # Insert a test document
        result = db.test_collection.insert_one({"test": "Local MongoDB is working correctly!"})
        
        # Verify insert worked
        if result.inserted_id:
            print("✓ Successfully created test database and inserted a document")
            
            # Clean up
            db.test_collection.delete_one({"_id": result.inserted_id})
            print("✓ Test database verified and cleaned up")
            return True
        
        return False
    except Exception as e:
        print(f"✗ Error creating test database: {e}")
        return False

def main():
    """Main function"""
    # Check if running on Render.com
    if os.environ.get('RENDER', False):
        print("Running on Render.com - local MongoDB setup skipped")
        sys.exit(0)
        
    print("\n=== Tea Processing AI Monitor - Local MongoDB Setup ===\n")
    
    # Check if MongoDB is running
    mongodb_running = check_mongodb_running()
    
    if not mongodb_running:
        # Try to start MongoDB if it's installed
        started = start_mongodb_if_possible()
        
        if not started:
            # If still not running, show installation instructions
            install_mongodb_instructions()
            sys.exit(1)
    
    # Verify the database by creating a test document
    if create_test_database():
        print("\n✓ Local MongoDB setup is complete and working correctly!")
        print("  The application can now use the local database as a fallback.")
    else:
        print("\n✗ There was an issue with the local MongoDB setup.")
        print("  Please check the MongoDB logs and ensure it has appropriate permissions.")
        sys.exit(1)

if __name__ == "__main__":
    main()
