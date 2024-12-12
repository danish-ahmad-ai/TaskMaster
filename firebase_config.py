import os
from dotenv import load_dotenv
import pyrebase
import json
from typing import Optional, Dict
import logging
import sys
from pathlib import Path
import shutil

# Initialize logger
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.expanduser('~'), 'taskmaster.log')),
        logging.StreamHandler()
    ]
)

def verify_json_file(path: Path) -> bool:
    """Verify if a file is valid JSON and has required fields"""
    try:
        print(f"\nAttempting to read file: {path}")
        
        # First check if file exists
        if not path.exists():
            print(f"File does not exist: {path}")
            return False
            
        # Try to read the file content
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"File content length: {len(content)}")
            print(f"First 100 characters: {content[:100]}")
            
            # Try to parse JSON
            data = json.loads(content)
            print("Successfully parsed JSON")
            
            # Check required fields
            if path.name == 'firebase_config.json':
                required_fields = [
                    'apiKey', 'authDomain', 'databaseURL', 'projectId',
                    'storageBucket', 'messagingSenderId', 'appId'
                ]
            elif path.name == 'serviceAccountKey.json':
                required_fields = [
                    'type', 'project_id', 'private_key_id', 'private_key',
                    'client_email', 'client_id'
                ]
            else:
                print(f"Unknown file type: {path.name}")
                return False
                
            missing = [field for field in required_fields if field not in data]
            if missing:
                print(f"Missing fields: {', '.join(missing)}")
                return False
                
            print("All required fields present")
            return True
            
    except json.JSONDecodeError as e:
        print(f"Invalid JSON: {str(e)}")
        return False
    except Exception as e:
        print(f"Error reading file: {str(e)}")
        return False

def get_firebase_config():
    """Get Firebase configuration from file or environment."""
    try:
        # First try secure credentials folder
        secure_path = get_credentials_path()
        config_path = secure_path / 'firebase_config.json'
        
        logger.info(f"Looking for config at: {config_path}")
        
        if config_path.exists():
            logger.info("Found config file in secure path")
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                logger.info("Successfully loaded Firebase config from secure path")
                return config
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing config file: {str(e)}")
                raise
        else:
            logger.warning(f"Config file not found at: {config_path}")
                
        # If not found in secure path, try local path
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
            
        local_config_path = os.path.join(base_path, 'firebase_config.json')
        
        if os.path.exists(local_config_path):
            with open(local_config_path, 'r') as f:
                config = json.load(f)
                logger.info("Successfully loaded Firebase config from local path")
                return config
                
        # Try environment variables as last resort
        logger.warning("Config files not found, trying environment variables")
        load_dotenv()
        
        config = {
            "apiKey": os.getenv("FIREBASE_API_KEY"),
            "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
            "databaseURL": os.getenv("FIREBASE_DATABASE_URL"),
            "projectId": os.getenv("FIREBASE_PROJECT_ID"),
            "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
            "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
            "appId": os.getenv("FIREBASE_APP_ID")
        }
        
        if all(config.values()):
            logger.info("Successfully loaded Firebase config from environment")
            return config
            
        raise ValueError("No valid configuration found")
            
    except Exception as e:
        logger.error(f"Error loading Firebase config: {str(e)}")
        return None

def get_credentials_path():
    """Get path to secure credentials folder"""
    secure_path = os.getenv('TASKMASTER_CREDENTIALS_PATH', 
                           r'C:\Users\E-TIME\PycharmProjects\LiteProjs\credentials')
    return Path(secure_path)

def verify_credentials():
    """Verify all required credentials exist"""
    secure_path = get_credentials_path()
    print(f"\nChecking credentials in: {secure_path}")
    print(f"Directory exists: {secure_path.exists()}")
    
    if secure_path.exists():
        print("Files in directory:")
        for file in secure_path.iterdir():
            print(f"  - {file.name}")
    
    required_files = ['firebase_config.json', 'serviceAccountKey.json', '.env']
    
    # Check each file
    for file in required_files:
        file_path = secure_path / file
        print(f"\nChecking {file}:")
        print(f"Exists: {file_path.exists()}")
        if file_path.exists():
            print(f"Size: {file_path.stat().st_size} bytes")
            
            # For JSON files, verify content
            if file.endswith('.json'):
                verify_json_file(file_path)
                
            # For .env file, check content
            elif file == '.env':
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        print(f"First line of .env: {content.split('\n')[0]}")
                except Exception as e:
                    print(f"Error reading .env: {str(e)}")
    
    return True

# Initialize Firebase with secure configuration
try:
    if not verify_credentials():
        raise ValueError("Missing required credential files")
    
    config = get_firebase_config()
    if not config:
        raise ValueError("Could not load Firebase configuration")
    
    # Add service account credentials to config
    service_account_path = get_credentials_path() / 'serviceAccountKey.json'
    with open(service_account_path, 'r') as f:
        service_account = json.load(f)
    
    config['serviceAccount'] = service_account
    
    # Log configuration (safely)
    logger.info(f"Loaded API Key: {config.get('apiKey', 'Not found')[:5]}...")
    logger.info(f"Loaded Project ID: {config.get('projectId', 'Not found')}")
    
    # Initialize Firebase
    firebase = pyrebase.initialize_app(config)
    auth = firebase.auth()
    db = firebase.database()
    
    # Try to initialize storage, but don't fail if it's not available
    try:
        storage = firebase.storage()
        logger.info("Firebase Storage initialized")
    except Exception as e:
        logger.warning(f"Firebase Storage not available: {str(e)}")
        storage = None
    
    # Test the connection differently
    try:
        # Try a simple database read as connection test
        db.child("connection_test").get(token=None)
        logger.info("Firebase connection successful")
    except Exception as e:
        logger.error(f"Firebase connection test failed: {str(e)}")
        raise
    
except Exception as e:
    logger.error(f"Error initializing Firebase: {str(e)}")
    auth = None
    db = None
    storage = None
    raise  # Re-raise to ensure application knows initialization failed

# Global user state
current_user = None

# Token Manager
class TokenManager:
    def __init__(self):
        self.user_token = None
        self.refresh_token = None
        
    def set_token(self, token):
        self.user_token = token
        
    def get_token(self, force_refresh=False):
        if force_refresh and self.refresh_token:
            try:
                # Refresh the token using Firebase Auth
                refresh_result = auth.refresh(self.refresh_token)
                if refresh_result:
                    self.user_token = refresh_result['idToken']
                    logger.info("Token refreshed successfully")
            except Exception as e:
                logger.error(f"Error refreshing token: {e}")
                return None
        return self.user_token
        
    def set_refresh_token(self, refresh_token):
        self.refresh_token = refresh_token
        
    def clear(self):
        self.user_token = None
        self.refresh_token = None
        logger.info("Token manager cleared")

token_manager = TokenManager()

def is_initialized():
    """Check if Firebase is properly initialized"""
    return all([auth, db, storage])

def prepare_build():
    """Prepare files for build"""
    # Get paths
    secure_path = Path(r'C:\Users\E-TIME\PycharmProjects\LiteProjs\credentials')
    build_path = Path('build_temp')
    
    # Create build directory
    build_path.mkdir(exist_ok=True)
    
    # Copy secure files
    shutil.copy(secure_path / 'firebase_config.json', build_path)
    shutil.copy(secure_path / 'serviceAccountKey.json', build_path)
    shutil.copy(secure_path / '.env', build_path)

def debug_credentials():
    """Debug function to check credential files"""
    secure_path = get_credentials_path()
    logger.info(f"\nChecking credentials in: {secure_path}")
    
    files_to_check = [
        'firebase_config.json',
        'serviceAccountKey.json',
        '.env'
    ]
    
    for file_name in files_to_check:
        file_path = secure_path / file_name
        logger.info(f"\nChecking {file_name}:")
        logger.info(f"Exists: {file_path.exists()}")
        
        if file_path.exists():
            try:
                if file_name.endswith('.json'):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = json.load(f)
                        logger.info(f"Valid JSON: Yes")
                        logger.info(f"Keys: {list(content.keys())}")
                else:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        logger.info(f"Content length: {len(content)}")
                        logger.info(f"First line: {content.split('\n')[0]}")
            except Exception as e:
                logger.error(f"Error reading file: {str(e)}")

# Add this at the end of the file
if __name__ == "__main__":
    debug_credentials()
