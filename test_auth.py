import logging
from firebase_config import auth, db
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_authentication():
    """Test Firebase authentication"""
    try:
        # Test credentials
        email = "test@example.com"  # Replace with your test user
        password = "testpass123"     # Replace with your test password
        
        logger.info("Testing authentication...")
        
        # Try to sign in
        user = auth.sign_in_with_email_and_password(email, password)
        logger.info("Authentication successful!")
        
        # Try to access database
        user_id = user['localId']
        id_token = user['idToken']
        
        # Try to write test data
        test_data = {
            'email': email,
            'updated_at': '2024-01-01T00:00:00'
        }
        
        db.child('users').child(user_id).set(test_data, token=id_token)
        logger.info("Database write successful!")
        
        # Try to read data
        user_data = db.child('users').child(user_id).get(token=id_token)
        logger.info("Database read successful!")
        
        return True
        
    except Exception as e:
        logger.error(f"Authentication test failed: {e}")
        if hasattr(e, 'args') and len(e.args) > 1:
            try:
                error_info = json.loads(e.args[1])
                logger.error(f"Error details: {error_info}")
            except:
                pass
        return False

if __name__ == "__main__":
    test_authentication() 