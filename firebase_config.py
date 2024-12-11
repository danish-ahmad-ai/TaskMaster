import os
from dotenv import load_dotenv
import pyrebase
import json
from typing import Optional, Dict
import logging
import sys
from pathlib import Path

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

def get_firebase_config():
    """Get Firebase configuration from file or environment."""
    try:
        # If running as executable
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
            
        config_path = os.path.join(base_path, 'firebase_config.json')
        logger.info(f"Looking for config at: {config_path}")
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                logger.info("Successfully loaded Firebase config from file")
                return config
                
        logger.warning("Config file not found, trying environment variables")
        
        # Try environment variables
        load_dotenv()  # Load .env file if exists
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
            
        logger.error("Failed to load Firebase configuration from both file and environment")
        return None
            
    except Exception as e:
        logger.error(f"Error loading Firebase config: {str(e)}")
        return None

# Initialize Firebase with secure configuration
try:
    config = get_firebase_config()
    if not config:
        raise ValueError("Could not load Firebase configuration")
    
    # Initialize Firebase
    firebase = pyrebase.initialize_app(config)
    auth = firebase.auth()
    db = firebase.database()
    storage = firebase.storage()
    
    # Test the connection
    try:
        auth._request('get', 'https://www.googleapis.com/identitytoolkit/v3/relyingparty/getAccountInfo')
        logger.info("Firebase connection successful")
    except:
        logger.info("Firebase initialized (authentication will be tested at login)")
    
except Exception as e:
    logger.error(f"Error initializing Firebase: {str(e)}")
    auth = None
    db = None
    storage = None

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
