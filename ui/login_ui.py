from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QLabel, QMessageBox,
    QStackedWidget, QHBoxLayout, QFrame, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QPoint, Qt, QTimer, QRect
from PyQt6.QtGui import QPalette, QColor, QFont
from firebase_config import auth, db, current_user
from ui.modern_widgets import ModernButton, ModernLineEdit
from ui.custom_widgets import show_error, show_success, show_question, ModernDialog
import json
from datetime import datetime
from pathlib import Path
import logging
import sys
import os

# Initialize logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class FadeLabel(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.opacity = QPropertyAnimation(self, b"windowOpacity")
        self.opacity.setDuration(1000)
        self.opacity.setStartValue(0)
        self.opacity.setEndValue(1)
        self.opacity.setEasingCurve(QEasingCurve.Type.InOutQuad)
        QTimer.singleShot(100, self.opacity.start)

class LoginWindow(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.init_ui()
        
        # Check if this is first launch
        settings_file = Path.home() / '.todoapp' / 'settings.json'
        try:
            if not settings_file.exists():
                # Show welcome notice for first-time users
                self.show_welcome_notice()
        except Exception as e:
            logger.error(f"Error checking welcome notice state: {e}")

    def handle_login(self):
        """Handle login button click"""
        from firebase_config import is_initialized, auth, db
        
        if not is_initialized():
            show_error(self, "Error", "Firebase initialization failed. Please restart the application.")
            return
        
        email = self.login_email.text().strip()
        password = self.login_password.text().strip()
        
        if not email or not password:
            show_error(self, "Error", "Please enter both email and password! 📝")
            return
        
        try:
            # Sign in with Firebase
            user = auth.sign_in_with_email_and_password(email, password)
            
            # Save session (without password)
            self.app.session_manager.save_session(
                user_id=user['localId'],
                email=email,
                token=user['idToken'],
                refresh_token=user.get('refreshToken')
            )
            
            # Update current user
            global current_user
            current_user = user
            
            print("Login successful!")
            self.app.switch_to_task_manager(user['localId'], email)
            self.clear_fields()
            
        except Exception as e:
            print(f"Login error: {str(e)}")
            show_error(self, "Error", "Invalid email or password! Please try again. 😕")

__all__ = ['LoginWindow']
