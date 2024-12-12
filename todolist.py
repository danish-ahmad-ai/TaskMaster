import sys
from PyQt6.QtWidgets import QApplication, QStackedWidget
from ui.login_ui import LoginWindow
from ui.main_ui import TaskManager
from utils import SessionManager
from ui.account_ui import AccountManager
from firebase_config import current_user, token_manager
from pathlib import Path
import logging
from PyQt6.QtGui import QIcon
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Main application
class ToDoListApp(QApplication):
    """Main application class."""
    
    def __init__(self, sys_argv):
        super().__init__(sys_argv)
        self.widget_stack = QStackedWidget()
        self.session_manager = SessionManager()
        
        # Set application icon
        if getattr(sys, 'frozen', False):
            # If running as exe
            base_path = sys._MEIPASS
        else:
            # If running as script
            base_path = os.path.dirname(os.path.abspath(__file__))
            
        icon_path = os.path.join(base_path, 'todolist.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            # Also set icon for all windows
            self.widget_stack.setWindowIcon(QIcon(icon_path))
        
        # Clear any existing session on startup
        self.session_manager.clear_session()
        
        self.init_ui()
        
        # Handle application exit
        self.aboutToQuit.connect(self.cleanup)
        
    def init_ui(self):
        # Add Login Window to the stack
        self.login_window = LoginWindow(self)
        self.widget_stack.addWidget(self.login_window)

        # Add Task Manager Window to the stack
        self.task_manager = TaskManager(self)
        self.widget_stack.addWidget(self.task_manager)

        # Add Account Manager to the stack
        self.account_manager = AccountManager(self, self.widget_stack)
        self.widget_stack.addWidget(self.account_manager)

        # Check for existing session
        session = self.session_manager.load_session()
        if session and session.get('logged_in'):
            self.task_manager.set_user_id(session['user_id'])
            self.widget_stack.setCurrentWidget(self.task_manager)
        else:
            self.widget_stack.setCurrentWidget(self.login_window)

        self.widget_stack.setFixedSize(800, 600)
        self.widget_stack.show()

    def switch_to_task_manager(self, user_id, email=None):
        """Switch to task manager view"""
        print(f"\n=== Switching to Task Manager ===")
        print(f"Current user state: {current_user}")
        
        try:
            # Set user ID first
            self.task_manager.set_user_id(user_id)
            
            # Then switch to task manager widget
            self.widget_stack.setCurrentWidget(self.task_manager)
            
            print("Successfully switched to task manager")
        except Exception as e:
            print(f"Error switching to task manager: {e}")

    def switch_to_login(self):
        """Switch to login and clear session"""
        global current_user
        
        logger.info("Switching to login and clearing session...")
        
        try:
            # Clear any existing session data
            self.session_manager.clear_session()
            
            # Reset current_user
            current_user = None
            
            # Clear token manager
            token_manager.clear()
            
            # Reset task manager state
            self.task_manager.set_user_id(None)
            
            # Switch to login window
            self.widget_stack.setCurrentWidget(self.login_window)
            
            logger.info("Successfully switched to login")
        except Exception as e:
            logger.error(f"Error switching to login: {e}")
            # Continue with logout even if there's an error
            self.widget_stack.setCurrentWidget(self.login_window)

    def cleanup(self) -> None:
        """Perform cleanup operations before exit."""
        try:
            # Clear session if it was a guest session
            session = self.session_manager.load_session()
            if session and session.get('is_guest'):
                self.session_manager.clear_session()
                
            # Clear any temporary files
            temp_dir = Path.home() / '.todoapp' / 'temp'
            if temp_dir.exists():
                for file in temp_dir.glob('*'):
                    try:
                        file.unlink()
                    except Exception as e:
                        logger.error(f"Failed to delete temp file {file}: {e}")
                        
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

# Main entry point
if __name__ == "__main__":
    app = ToDoListApp(sys.argv)
    sys.exit(app.exec())
