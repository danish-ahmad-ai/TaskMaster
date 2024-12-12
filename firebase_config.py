import os
from dotenv import load_dotenv
import pyrebase
import json
from typing import Optional, Dict
import logging
import time
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TokenManager:
    """Manages Firebase authentication tokens."""
    
    def __init__(self):
        self.current_token = None
        self.token_expiry = None
        self.refresh_token = None
        
    def set_token(self, token: str, expiry_minutes: int = 55):
        """Set a new token with expiry time"""
        self.current_token = token
        self.token_expiry = datetime.now() + timedelta(minutes=expiry_minutes)
        
    def set_refresh_token(self, token: str):
        """Set the refresh token"""
        self.refresh_token = token
        
    def clear(self):
        """Clear all token data"""
        self.current_token = None
        self.token_expiry = None
        self.refresh_token = None
        logger.info("Token manager cleared")
        
    def is_token_valid(self) -> bool:
        """Check if current token is valid and not expired"""
        if not self.current_token or not self.token_expiry:
            return False
        return datetime.now() < self.token_expiry
        
    def get_token(self, force_refresh: bool = False) -> Optional[str]:
        """Get current token, refreshing if necessary"""
        if not force_refresh and self.is_token_valid():
            return self.current_token
            
        if self.refresh_token and auth:
            try:
                # Refresh the token
                user = auth.refresh(self.refresh_token)
                self.set_token(user['idToken'])
                return self.current_token
            except Exception as e:
                logger.error(f"Token refresh failed: {e}")
                return None
        return None

def verify_api_key():
    """Verify that the API key is loaded correctly"""
    try:
        config_path = os.path.join("credentials", "firebase_config.json")
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                api_key = config.get("apiKey")
                
                if api_key:
                    # Only log length and first/last few chars for verification
                    key_len = len(api_key)
                    key_preview = f"{api_key[:3]}...{api_key[-3:]}"
                    logger.info(f"API Key found (length: {key_len}, preview: {key_preview})")
                    return True
                else:
                    logger.error("API Key is missing from config!")
                    return False
        else:
            logger.error(f"Config file not found at: {config_path}")
            return False
            
    except Exception as e:
        logger.error(f"Error verifying API key: {e}")
        return False

def initialize_firebase() -> Optional[Dict]:
    """Initialize Firebase with configuration from environment variables or file"""
    try:
        # First verify API key
        if not verify_api_key():
            raise ValueError("Invalid API key configuration")
            
        # First try loading from credentials folder
        config_path = os.path.join("credentials", "firebase_config.json")
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                logger.info("Loaded configuration from firebase_config.json")
        else:
            # Fallback to environment variables
            load_dotenv(os.path.join("credentials", ".env"))
            config = {
                "apiKey": os.getenv("FIREBASE_API_KEY"),
                "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
                "databaseURL": os.getenv("FIREBASE_DATABASE_URL"),
                "projectId": os.getenv("FIREBASE_PROJECT_ID"),
                "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
                "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
                "appId": os.getenv("FIREBASE_APP_ID")
            }
        
        # Verify configuration
        required_fields = ["apiKey", "authDomain", "databaseURL", "projectId"]
        missing_fields = [field for field in required_fields if not config.get(field)]
        
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")
            
        # Log configuration (without sensitive data)
        safe_config = config.copy()
        safe_config["apiKey"] = "***" if config["apiKey"] else None
        logger.info(f"Firebase Configuration: {safe_config}")
        
        # Initialize Firebase
        firebase = pyrebase.initialize_app(config)
        return firebase
        
    except Exception as e:
        logger.error(f"Firebase initialization failed: {str(e)}")
        return None

# Initialize Firebase when module is imported
firebase = initialize_firebase()

# Create token manager instance
token_manager = TokenManager()

# Export these for other modules to use
if firebase:
    auth = firebase.auth()
    db = firebase.database()
    storage = firebase.storage()
    current_user = None
    is_initialized = lambda: True
else:
    auth = None
    db = None
    storage = None
    current_user = None
    is_initialized = lambda: False

# Export all required components
__all__ = ['firebase', 'auth', 'db', 'storage', 'current_user', 'token_manager', 'is_initialized']
