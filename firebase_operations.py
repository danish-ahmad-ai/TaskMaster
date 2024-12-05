from typing import Any, Callable, Optional
from firebase_admin import auth, db
from datetime import datetime, timedelta
from collections import deque
import time
from utils import SessionManager

class FirebaseOperations:
    """Handles Firebase operations with automatic token refresh and error handling."""
    
    def __init__(self, session_manager: SessionManager):
        """
        Initialize Firebase operations.
        
        Args:
            session_manager: Session manager instance for token handling
        """
        self.session_manager = session_manager
        
    def execute_operation(self, operation: Callable, *args: Any, **kwargs: Any) -> Any:
        """
        Execute a Firebase operation with automatic token refresh.
        
        Args:
            operation: Firebase operation to execute
            *args: Positional arguments for the operation
            **kwargs: Keyword arguments for the operation
            
        Returns:
            Result of the operation
            
        Raises:
            FirebaseError: If operation fails after retries
        """
        max_retries = 2
        last_error = None
        
        for attempt in range(max_retries):
            try:
                token = self.session_manager.get_valid_token()
                if not token:
                    raise Exception("No valid authentication token")
                    
                return operation(*args, **kwargs, token=token)
                
            except Exception as e:
                last_error = e
                if "Permission denied" in str(e) and attempt < max_retries - 1:
                    # Try refreshing token and retry
                    self.session_manager.refresh_token()
                    continue
                    
        raise last_error  # Re-raise the last error if all retries failed

class RateLimitedFirebaseOperations(FirebaseOperations):
    """Firebase operations with rate limiting."""
    
    def __init__(self, session_manager: SessionManager):
        super().__init__(session_manager)
        self._requests = deque()
        self._max_requests = 100  # Max requests per minute
        self._window = 60  # Time window in seconds
        
    def _check_rate_limit(self):
        """Check if operation should be rate limited."""
        now = datetime.now()
        
        # Remove old requests
        while self._requests and self._requests[0] < now - timedelta(seconds=self._window):
            self._requests.popleft()
            
        # Check if we're over the limit
        if len(self._requests) >= self._max_requests:
            sleep_time = (self._requests[0] + timedelta(seconds=self._window) - now).total_seconds()
            if sleep_time > 0:
                time.sleep(sleep_time)
                
        # Add current request
        self._requests.append(now)
        
    def execute_operation(self, operation: Callable, *args: Any, **kwargs: Any) -> Any:
        """Execute rate-limited operation."""
        self._check_rate_limit()
        return super().execute_operation(operation, *args, **kwargs)