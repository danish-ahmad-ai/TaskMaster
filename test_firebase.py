import json
import os
import logging
from firebase_config import initialize_firebase, verify_api_key

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_firebase_connection():
    """Test Firebase configuration and connection"""
    
    # First check API key
    logger.info("Verifying API key...")
    if not verify_api_key():
        logger.error("API key verification failed!")
        return False
        
    # Try to initialize Firebase
    logger.info("Initializing Firebase...")
    firebase = initialize_firebase()
    if not firebase:
        logger.error("Firebase initialization failed!")
        return False
        
    # Try authentication
    try:
        auth = firebase.auth()
        logger.info("Authentication service initialized")
        
        # Try database
        db = firebase.database()
        logger.info("Database service initialized")
        
        logger.info("Firebase connection test successful!")
        return True
        
    except Exception as e:
        logger.error(f"Firebase test failed: {e}")
        return False

if __name__ == "__main__":
    test_firebase_connection() 