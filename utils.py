import json
import os
from pathlib import Path
from firebase_config import current_user, db, token_manager, auth
from typing import Optional, Dict
import logging
from cryptography.fernet import Fernet
import base64

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SessionManager:
    """Manages user session data and token handling."""
    
    def __init__(self):
        """Initialize session manager with required paths."""
        self.app_data_dir = Path.home() / '.todoapp'
        self.session_file = self.app_data_dir / 'session.json'
        self.token_manager = token_manager
        self._ensure_app_directory()
        
    def _ensure_app_directory(self) -> None:
        """Create application directory if it doesn't exist."""
        try:
            self.app_data_dir.mkdir(exist_ok=True)
            logger.info(f"Directory ensured at: {self.app_data_dir}")
        except Exception as e:
            logger.error(f"Failed to create directory: {e}")
            raise RuntimeError(f"Cannot create app directory: {e}")

    def save_session(self, user_id: str, email: str, 
                    token: Optional[str] = None, 
                    refresh_token: Optional[str] = None, 
                    is_guest: bool = False) -> None:
        """
        Save user session data securely.
        
        Args:
            user_id: User's unique identifier
            email: User's email address
            token: Authentication token
            refresh_token: Token for refreshing authentication
            is_guest: Whether this is a guest session
        """
        try:
            session_data = {
                'user_id': user_id,
                'email': email,
                'logged_in': True,
                'idToken': token,
                'refreshToken': refresh_token,
                'is_guest': is_guest
            }
            
            with open(self.session_file, 'w') as f:
                json.dump(session_data, f)
                
            logger.info(f"Session saved for user: {email}")
            
        except Exception as e:
            logger.error(f"Failed to save session: {e}")
            raise RuntimeError(f"Cannot save session data: {e}")

    def load_session(self) -> Optional[Dict]:
        """
        Load user session data.
        
        Returns:
            Session data dictionary or None if no session exists
        """
        try:
            if not self.session_file.exists():
                return None
                
            with open(self.session_file, 'r') as f:
                return json.load(f)
                
        except json.JSONDecodeError:
            logger.error("Corrupted session file detected")
            self.clear_session()
            return None
            
        except Exception as e:
            logger.error(f"Failed to load session: {e}")
            return None

    def clear_session(self):
        """Clear user session data"""
        if self.session_file.exists():
            try:
                # Check if it's a guest session
                session = self.load_session()
                if session and session.get('is_guest'):
                    # Clear guest data from Firebase if needed
                    if current_user:
                        try:
                            db.child('tasks').child(session['user_id']).remove()
                        except:
                            pass  # Ignore errors when clearing guest data
            except:
                pass
            self.session_file.unlink()

    def get_valid_token(self):
        """Get a valid token, refreshing if necessary"""
        session = self.load_session()
        if not session:
            return None
            
        # Set refresh token in token manager
        self.token_manager.set_refresh_token(session.get('refreshToken'))
        
        # Try to get token, forcing refresh if needed
        token = self.token_manager.get_token(force_refresh=True)
        
        if token:
            # Update session with new token
            self.save_session(
                user_id=session.get('user_id'),
                email=session.get('email'),
                token=token,
                refresh_token=session.get('refreshToken'),
                is_guest=session.get('is_guest', False)
            )
            return token
            
        return None

class SecureSessionManager(SessionManager):
    """Manages encrypted user session data."""
    
    def __init__(self):
        super().__init__()
        self._key = self._get_or_create_key()
        self._fernet = Fernet(self._key)
        
    def _get_or_create_key(self) -> bytes:
        """Get or create encryption key."""
        key_file = self.app_data_dir / '.key'
        if key_file.exists():
            return key_file.read_bytes()
        else:
            key = Fernet.generate_key()
            key_file.write_bytes(key)
            return key
            
    def save_session(self, user_id: str, email: str, 
                    token: Optional[str] = None, 
                    refresh_token: Optional[str] = None, 
                    is_guest: bool = False) -> None:
        """Save encrypted session data."""
        try:
            session_data = {
                'user_id': user_id,
                'email': email,
                'logged_in': True,
                'idToken': token,
                'refreshToken': refresh_token,
                'is_guest': is_guest
            }
            
            # Encrypt session data
            encrypted_data = self._fernet.encrypt(
                json.dumps(session_data).encode()
            )
            
            with open(self.session_file, 'wb') as f:
                f.write(encrypted_data)
                
            logger.info(f"Encrypted session saved for user: {email}")
            
        except Exception as e:
            logger.error(f"Failed to save encrypted session: {e}")
            raise RuntimeError(f"Cannot save session data: {e}")
            
    def load_session(self) -> Optional[Dict]:
        """Load and decrypt session data."""
        try:
            if not self.session_file.exists():
                return None
                
            with open(self.session_file, 'rb') as f:
                encrypted_data = f.read()
                
            decrypted_data = self._fernet.decrypt(encrypted_data)
            return json.loads(decrypted_data)
            
        except Exception as e:
            logger.error(f"Failed to load encrypted session: {e}")
            self.clear_session()
            return None
