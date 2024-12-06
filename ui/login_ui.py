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
import requests.exceptions

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

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Login or Signup")
        main_layout = QVBoxLayout()
        
        # Add welcome message with fade animation
        self.welcome_label = FadeLabel("Welcome to TaskMaster ")
        self.welcome_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        self.welcome_label.setStyleSheet("color: #2c3e50; margin: 20px;")
        main_layout.addWidget(self.welcome_label)
        
        # Create stacked widget with sliding animation
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet("""
            QStackedWidget {
                background-color: white;
                border-radius: 15px;
                padding: 20px;
            }
        """)
        
        # Login Page
        login_widget = QWidget()
        login_layout = QVBoxLayout()
        login_layout.setSpacing(15)
        
        # Add login form title
        login_title = QLabel("Login to Your Account")
        login_title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        login_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        login_title.setStyleSheet("color: #2c3e50; margin: 20px 0;")
        login_layout.addWidget(login_title)
        
        # Create input fields
        self.login_email = ModernLineEdit(placeholder="Enter your email")
        self.login_password = ModernLineEdit(placeholder="Enter your password")
        self.login_password.setEchoMode(QLineEdit.EchoMode.Password)
        
        # Create password container with visibility toggle
        password_container = QWidget()
        password_layout = QHBoxLayout(password_container)
        password_layout.setContentsMargins(0, 0, 0, 0)
        password_layout.setSpacing(10)
        
        # Add password field to container
        password_layout.addWidget(self.login_password)
        
        # Add show/hide password button
        self.show_password_btn = ModernButton("", color="#6c757d")
        self.show_password_btn.setFixedWidth(50)
        self.show_password_btn.setCheckable(True)
        self.show_password_btn.clicked.connect(self.toggle_password_visibility)
        password_layout.addWidget(self.show_password_btn)
        
        # Add fields to layout
        login_layout.addWidget(self.login_email)
        login_layout.addWidget(password_container)
        
        # Add forgot password button
        forgot_container = QWidget()
        forgot_layout = QHBoxLayout(forgot_container)
        forgot_layout.setContentsMargins(0, 0, 0, 0)
        
        self.forgot_password_btn = QPushButton("Forgot Password? ")
        self.forgot_password_btn.setStyleSheet("""
            QPushButton {
                border: none;
                color: #4a90e2;
                font-size: 13px;
                text-decoration: underline;
                padding: 0;
                text-align: left;
                max-width: 150px;
            }
            QPushButton:hover {
                color: #357abd;
            }
        """)
        forgot_layout.addWidget(self.forgot_password_btn)
        forgot_layout.addStretch()
        
        login_layout.addWidget(forgot_container)
        
        # Add buttons
        self.login_button = ModernButton("Login")
        self.guest_button = ModernButton("Continue as Guest ", color="#6c757d")
        self.signup_button = ModernButton("Need an account? Sign up", color="#28a745")
        
        login_layout.addWidget(self.login_button)
        login_layout.addWidget(self.guest_button)
        login_layout.addWidget(self.signup_button)
        
        # Add stretch at the bottom
        login_layout.addStretch()
        
        login_widget.setLayout(login_layout)
        self.stacked_widget.addWidget(login_widget)
        
        # Signup Page
        signup_widget = QWidget()
        signup_layout = QVBoxLayout()
        signup_layout.setSpacing(15)
        
        # Add signup form title
        signup_title = QLabel("Create New Account")
        signup_title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        signup_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        signup_title.setStyleSheet("color: #2c3e50; margin: 20px 0;")
        signup_layout.addWidget(signup_title)
        
        # Create input fields
        self.signup_username = ModernLineEdit(placeholder="Choose a username")
        self.signup_email = ModernLineEdit(placeholder="Enter your email")
        self.signup_password = ModernLineEdit(placeholder="Choose a password")
        self.signup_confirm_password = ModernLineEdit(placeholder="Confirm your password")
        
        self.signup_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.signup_confirm_password.setEchoMode(QLineEdit.EchoMode.Password)
        
        # Add password visibility toggle for signup
        signup_password_container = QWidget()
        signup_password_layout = QHBoxLayout(signup_password_container)
        signup_password_layout.setContentsMargins(0, 0, 0, 0)
        signup_password_layout.setSpacing(10)
        
        signup_password_layout.addWidget(self.signup_password)
        self.show_signup_password_btn = ModernButton("", color="#6c757d")
        self.show_signup_password_btn.setFixedWidth(50)
        self.show_signup_password_btn.setCheckable(True)
        self.show_signup_password_btn.clicked.connect(self.toggle_signup_password_visibility)
        signup_password_layout.addWidget(self.show_signup_password_btn)
        
        # Add fields to layout
        signup_layout.addWidget(self.signup_username)
        signup_layout.addWidget(self.signup_email)
        signup_layout.addWidget(signup_password_container)
        signup_layout.addWidget(self.signup_confirm_password)
        
        # Add signup button
        self.create_account_btn = ModernButton("Create Account", color="#28a745")
        self.back_to_login_btn = ModernButton("Back to Login", color="#6c757d")
        
        signup_layout.addWidget(self.create_account_btn)
        signup_layout.addWidget(self.back_to_login_btn)
        
        # Add stretch
        signup_layout.addStretch()
        
        signup_widget.setLayout(signup_layout)
        self.stacked_widget.addWidget(signup_widget)
        
        main_layout.addWidget(self.stacked_widget)
        self.setLayout(main_layout)
        
        # Connect buttons
        self.login_button.clicked.connect(self.handle_login)
        self.guest_button.clicked.connect(self.handle_guest_login)
        self.signup_button.clicked.connect(self.slide_to_signup)
        self.forgot_password_btn.clicked.connect(self.handle_forgot_password)
        self.create_account_btn.clicked.connect(self.handle_signup)
        self.back_to_login_btn.clicked.connect(self.slide_to_login)

    def handle_guest_login(self):
        """Handle guest login"""
        try:
            guest_id = f"guest_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            guest_user = {
                'localId': guest_id,
                'email': 'guest@temporary.user',
                'idToken': 'guest_token',
                'refreshToken': None,
                'isGuest': True
            }
            
            global current_user
            current_user = guest_user
            
            self.app.session_manager.save_session(
                user_id=guest_id,
                email='guest@temporary.user',
                token='guest_token',
                refresh_token=None,
                is_guest=True
            )
            
            show_success(self, "Guest Mode", "Welcome! Your tasks will be temporary. ")
            self.app.switch_to_task_manager(guest_id, 'guest@temporary.user')
            
        except Exception as e:
            print(f"Guest login error: {str(e)}")
            show_error(self, "Error", "Failed to start guest session. Please try again! ")

    def handle_signup(self):
        """Handle signup attempt"""
        username = self.signup_username.text().strip()
        email = self.signup_email.text().strip()
        password = self.signup_password.text().strip()
        confirm_password = self.signup_confirm_password.text().strip()

        if not all([username, email, password, confirm_password]):
            show_error(self, "Error", "Please fill in all fields.")
            return

        if password != confirm_password:
            show_error(self, "Error", "Passwords do not match.")
            return

        if len(password) < 6:
            show_error(self, "Error", "Password must be at least 6 characters long.")
            return

        try:
            print(f"Attempting signup with email: {email}")
            user = auth.create_user_with_email_and_password(email, password)
            print("User created successfully:", user)
            
            global current_user
            current_user = user
            
            user_data = {
                'username': username,
                'email': email,
                'created_at': datetime.now().isoformat()
            }
            
            # Store user data in database
            db.child('users').child(user['localId']).set(user_data, token=user['idToken'])
            print("User data stored in database")
            
            # Show success message and clear fields
            show_success(self, "Success", "Account created successfully! You can now log in. ")
            self.clear_fields()
            
            # Switch to login page
            QTimer.singleShot(1500, self.slide_to_login)
            
        except requests.exceptions.ConnectionError:
            print("Network error during signup")
            show_error(self, "Connection Error", "Unable to connect to the server. Please check your internet connection! ")
        except requests.exceptions.Timeout:
            print("Signup request timed out")
            show_error(self, "Timeout Error", "Request timed out. Please check your internet connection and try again! ")
        except Exception as e:
            error_message = "Failed to create account."
            print(f"Full signup error: {str(e)}")
            if hasattr(e, 'args') and len(e.args) > 0:
                try:
                    error_data = json.loads(e.args[1])
                    if 'error' in error_data:
                        error_code = error_data['error'].get('message', '')
                        if error_code == 'EMAIL_EXISTS':
                            error_message = "This email is already registered. Please try logging in instead. "
                        elif error_code == 'INVALID_EMAIL':
                            error_message = "Invalid email format. Please check your email address. "
                        elif error_code == 'WEAK_PASSWORD':
                            error_message = "Password is too weak. Please use a stronger password with at least 6 characters. "
                        elif error_code == 'OPERATION_NOT_ALLOWED':
                            error_message = "Email/password registration is not enabled. Please contact support. "
                        elif error_code == 'TOO_MANY_ATTEMPTS_TRY_LATER':
                            error_message = "Too many attempts. Please try again later. "
                except:
                    pass
            show_error(self, "Error", error_message)

    def clear_fields(self):
        """Clear all input fields"""
        self.login_email.clear()
        self.login_password.clear()
        self.signup_username.clear()
        self.signup_email.clear()
        self.signup_password.clear()
        self.signup_confirm_password.clear()

    def show_welcome_notice(self):
        """Show welcome notice for first-time users"""
        welcome_text = """
        Welcome to TaskMaster!

        Your Personal Task Management Solution

        TaskMaster helps you stay organized with:
        
        Secure Cloud Storage
        • Your tasks are safely stored and synced
        • Access from anywhere, anytime
        
        Smart Task Management
        • Organize tasks efficiently
        • Track completion status
        • Auto-cleanup after 20 days
        
        Ready to get organized? Let's begin! 
        """
        
        dialog = ModernDialog(
            "Welcome to TaskMaster ",
            welcome_text,
            icon="",
            buttons=["Let's Begin!"],
            parent=self
        )
        dialog.exec()
        
        # Save that welcome notice has been shown
        settings_file = Path.home() / '.todoapp' / 'settings.json'
        try:
            settings = {'welcome_shown': True}
            settings_file.parent.mkdir(exist_ok=True)
            with open(settings_file, 'w') as f:
                json.dump(settings, f)
        except Exception as e:
            logger.error(f"Failed to save welcome notice state: {e}")

    def handle_login(self):
        """Handle login button click"""
        from firebase_config import is_initialized, auth, db
        
        if not is_initialized():
            show_error(self, "Error", "Firebase initialization failed. Please restart the application.")
            return
        
        email = self.login_email.text().strip()
        password = self.login_password.text().strip()
        
        if not email or not password:
            show_error(self, "Error", "Please enter both email and password! ")
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
            
        except requests.exceptions.ConnectionError:
            print("Network error during login")
            show_error(self, "Connection Error", "Unable to connect to the server. Please check your internet connection! ")
        except requests.exceptions.Timeout:
            print("Login request timed out")
            show_error(self, "Timeout Error", "Request timed out. Please check your internet connection and try again! ")
        except Exception as e:
            print(f"Login error: {str(e)}")
            error_message = "Invalid email or password! Please try again. "
            if hasattr(e, 'args') and len(e.args) > 0:
                try:
                    error_data = json.loads(e.args[1])
                    if 'error' in error_data:
                        error_code = error_data['error'].get('message', '')
                        if error_code == 'INVALID_EMAIL':
                            error_message = "Invalid email format. Please check your email address. "
                        elif error_code == 'EMAIL_NOT_FOUND':
                            error_message = "Email not found. Please check your email or sign up for a new account. "
                        elif error_code == 'INVALID_PASSWORD':
                            error_message = "Incorrect password. Please try again. "
                        elif error_code == 'TOO_MANY_ATTEMPTS_TRY_LATER':
                            error_message = "Too many failed attempts. Please try again later. "
                except:
                    pass
            show_error(self, "Error", error_message)

    def toggle_password_visibility(self):
        """Toggle password visibility"""
        if self.show_password_btn.isChecked():
            self.login_password.setEchoMode(QLineEdit.EchoMode.Normal)
            self.show_password_btn.setText("")
        else:
            self.login_password.setEchoMode(QLineEdit.EchoMode.Password)
            self.show_password_btn.setText("")

    def handle_forgot_password(self):
        """Handle forgot password request"""
        email = self.login_email.text().strip()
        
        if not email:
            show_error(self, "Error", "Please enter your email address first! ")
            return
        
        try:
            auth.send_password_reset_email(email)
            show_success(self, "Reset Link Sent", 
                        "Check your email! We've sent you a password reset link! ")
        except Exception as e:
            print(f"Error sending reset email: {str(e)}")
            show_error(self, "Error", 
                      "Could not send reset email. Please check your email address.")

    def toggle_signup_password_visibility(self):
        """Toggle signup password visibility"""
        if self.show_signup_password_btn.isChecked():
            self.signup_password.setEchoMode(QLineEdit.EchoMode.Normal)
            self.signup_confirm_password.setEchoMode(QLineEdit.EchoMode.Normal)
            self.show_signup_password_btn.setText("")
        else:
            self.signup_password.setEchoMode(QLineEdit.EchoMode.Password)
            self.signup_confirm_password.setEchoMode(QLineEdit.EchoMode.Password)
            self.show_signup_password_btn.setText("")

    def slide_to_login(self):
        """Animate transition to login page"""
        self.stacked_widget.setCurrentIndex(0)
        self.animate_transition(False)

    def slide_to_signup(self):
        """Animate transition to signup page"""
        self.stacked_widget.setCurrentIndex(1)
        self.animate_transition(True)

    def animate_transition(self, forward=True):
        """Create sliding animation between pages"""
        # Get the current and next widgets
        current_widget = self.stacked_widget.currentWidget()
        next_index = 1 if forward else 0
        next_widget = self.stacked_widget.widget(next_index)
        
        # Calculate start and end positions
        width = self.stacked_widget.width()
        start_x = width if not forward else -width
        end_x = 0
        
        # Set initial position for next widget
        next_widget.setGeometry(start_x, 0, width, self.stacked_widget.height())
        
        # Create and configure animation for next widget
        anim = QPropertyAnimation(next_widget, b"geometry", self)
        anim.setDuration(300)
        anim.setStartValue(QRect(start_x, 0, width, self.stacked_widget.height()))
        anim.setEndValue(QRect(end_x, 0, width, self.stacked_widget.height()))
        anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        
        # When animation finishes, update the stacked widget
        def on_finished():
            self.stacked_widget.setCurrentIndex(next_index)
            next_widget.setGeometry(0, 0, width, self.stacked_widget.height())
        
        anim.finished.connect(on_finished)
        anim.start()

__all__ = ['LoginWindow']
