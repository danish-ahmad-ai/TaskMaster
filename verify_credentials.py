import os
import json
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_credentials():
    """Verify Firebase credentials"""
    creds_path = Path("credentials")
    
    # Check credentials directory
    if not creds_path.exists():
        logger.error("Credentials directory not found!")
        return False
        
    # Check firebase_config.json
    config_path = creds_path / "firebase_config.json"
    if not config_path.exists():
        logger.error("firebase_config.json not found!")
        return False
        
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            
        # Verify required fields
        required_fields = ["apiKey", "authDomain", "databaseURL", "projectId"]
        for field in required_fields:
            if not config.get(field):
                logger.error(f"Missing {field} in firebase_config.json")
                return False
            
        # Verify API key format
        api_key = config.get("apiKey", "")
        if not api_key or api_key == "your-api-key" or len(api_key) < 20:
            logger.error("Invalid API key format")
            return False
            
        logger.info("Credentials verification passed!")
        return True
        
    except Exception as e:
        logger.error(f"Error verifying credentials: {e}")
        return False

if __name__ == "__main__":
    verify_credentials() 