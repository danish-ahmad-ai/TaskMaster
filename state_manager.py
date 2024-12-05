from typing import Optional, Dict
from dataclasses import dataclass
from datetime import datetime

@dataclass
class UserState:
    """User state data container."""
    user_id: str
    email: str
    is_guest: bool
    last_login: datetime
    
class StateManager:
    """Manages global application state."""
    
    def __init__(self):
        """Initialize state manager."""
        self._current_user: Optional[UserState] = None
        self._is_authenticated: bool = False
        
    @property
    def current_user(self) -> Optional[UserState]:
        """Get current user state."""
        return self._current_user
        
    @property
    def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        return self._is_authenticated
        
    def set_user(self, user_data: Dict) -> None:
        """
        Set current user state.
        
        Args:
            user_data: User data dictionary
        """
        if user_data:
            self._current_user = UserState(
                user_id=user_data['localId'],
                email=user_data['email'],
                is_guest=user_data.get('isGuest', False),
                last_login=datetime.now()
            )
            self._is_authenticated = True
        else:
            self.clear_user()
            
    def clear_user(self) -> None:
        """Clear current user state."""
        self._current_user = None
        self._is_authenticated = False

# Create global state instance
state_manager = StateManager() 