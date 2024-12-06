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

class PageTitle(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumHeight(70)  # Ensure enough height for the text
        self.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                padding: 15px 0;
                margin: 10px 0;
                background: transparent;
            }
        """)

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
        title_container = QWidget()
        title_layout = QVBoxLayout(title_container)
        title_layout.setSpacing(5)
        title_layout.setContentsMargins(0, 0, 0, 20)

        self.welcome_label = FadeLabel("TaskMaster")
        self.welcome_label.setFont(QFont("Arial", 42, QFont.Weight.ExtraBold))
        self.welcome_label.setStyleSheet("""
            color: #2c3e50;
            margin: 10px;
            letter-spacing: 2px;
        """)
        
        # Add shadow effect to welcome label
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(4)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(2, 2)
        self.welcome_label.setGraphicsEffect(shadow)

        # Add subtitle as clickable link
        subtitle = QLabel()
        subtitle.setText('<a href="https://d-techsolutions.agency" style="color: #ff0000; text-decoration: none;">by D-Tech Solutions</a>')
        subtitle.setOpenExternalLinks(True)
        subtitle.setFont(QFont("Arial", 14, QFont.Weight.Medium))
        subtitle.setStyleSheet("""
            QLabel {
                margin-bottom: 5px;
                letter-spacing: 1px;
            }
            QLabel:hover {
                text-decoration: underline;
            }
        """)
        
        # Add developer credit as clickable link
        dev_credit = QLabel()
        dev_credit.setText('<a href="https://danishahmad.xyz" style="color: #0066cc; text-decoration: none;">And by Danish Ahmad</a>')
        dev_credit.setOpenExternalLinks(True)
        dev_credit.setFont(QFont("Arial", 12, QFont.Weight.Medium))
        dev_credit.setStyleSheet("""
            QLabel {
                margin-bottom: 15px;
                letter-spacing: 1px;
            }
            QLabel:hover {
                text-decoration: underline;
            }
        """)
        
        title_layout.addWidget(self.welcome_label, 0, Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(subtitle, 0, Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(dev_credit, 0, Qt.AlignmentFlag.AlignCenter)
        
        main_layout.addWidget(title_container)
        
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
        login_layout.setContentsMargins(20, 20, 20, 20)
        
        # Create input fields
        self.login_email = ModernLineEdit()
        self.login_email.setPlaceholderText("Enter your email address")
        
        # Create password container with visibility toggle
        password_container = QWidget()
        password_layout = QHBoxLayout(password_container)
        password_layout.setContentsMargins(0, 0, 0, 0)
        password_layout.setSpacing(8)

        self.login_password = ModernLineEdit()
        self.login_password.setPlaceholderText("Enter your password")
        self.login_password.setEchoMode(QLineEdit.EchoMode.Password)
        password_layout.addWidget(self.login_password)
        
        # Add show/hide password button
        self.show_password_btn = ModernButton("👁️", color="#6c757d")
        self.show_password_btn.setFixedHeight(45)  # Match height only
        self.show_password_btn.setFixedWidth(50)   # Reasonable width for the icon
        self.show_password_btn.setStyleSheet("""
            QPushButton {
                padding: 8px;
                border: none;
                border-radius: 8px;
                background-color: #6c757d;
                color: white;
                font-size: 18px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
            QPushButton:pressed {
                background-color: #545b62;
            }
        """)
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
        self.login_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 15px;
                text-align: center;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                min-width: 120px;
                margin: 2px;
            }
            QPushButton:hover {
                background-color: #45a049;
                margin: 0px;
                border: 2px solid #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
                margin: 2px;
            }
        """)
        
        self.guest_button = ModernButton("Continue as Guest")
        self.guest_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 15px;
                text-align: center;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                min-width: 120px;
                margin: 2px;
            }
            QPushButton:hover {
                background-color: #5a6268;
                margin: 0px;
                border: 2px solid #5a6268;
            }
            QPushButton:pressed {
                background-color: #545b62;
                margin: 2px;
            }
        """)
        
        self.switch_to_signup_button = ModernButton("Create New Account")
        self.switch_to_signup_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #2196F3;
                border: 2px solid #2196F3;
                padding: 12px;
                text-align: center;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #2196F3;
                color: white;
            }
            QPushButton:pressed {
                background-color: #1976D2;
                color: white;
            }
        """)
        
        login_layout.addWidget(self.login_button)
        login_layout.addWidget(self.guest_button)
        login_layout.addWidget(self.switch_to_signup_button)
        
        # Add stretch at the bottom
        login_layout.addStretch()
        
        login_widget.setLayout(login_layout)
        self.stacked_widget.addWidget(login_widget)
        
        # Signup Page
        signup_widget = QWidget()
        signup_layout = QVBoxLayout()
        signup_layout.setSpacing(15)
        signup_layout.setContentsMargins(20, 20, 20, 20)
        
        # Create input fields
        self.signup_email = ModernLineEdit()
        self.signup_email.setPlaceholderText("Enter your email address")
        self.signup_password = ModernLineEdit()
        self.signup_password.setPlaceholderText("Create a password (min. 6 characters)")
        self.signup_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.signup_confirm_password = ModernLineEdit()
        self.signup_confirm_password.setPlaceholderText("Confirm your password")
        self.signup_confirm_password.setEchoMode(QLineEdit.EchoMode.Password)
        
        # Create signup password container
        signup_password_container = QWidget()
        signup_password_layout = QHBoxLayout(signup_password_container)
        signup_password_layout.setContentsMargins(0, 0, 0, 0)
        signup_password_layout.setSpacing(8)

        self.signup_password = ModernLineEdit()
        self.signup_password.setPlaceholderText("Create a password (min. 6 characters)")
        self.signup_password.setEchoMode(QLineEdit.EchoMode.Password)
        signup_password_layout.addWidget(self.signup_password)
        
        # Add show/hide password button for signup
        self.show_signup_password_btn = ModernButton("👁️", color="#6c757d")
        self.show_signup_password_btn.setFixedHeight(45)  # Match height only
        self.show_signup_password_btn.setFixedWidth(50)   # Reasonable width for the icon
        self.show_signup_password_btn.setStyleSheet("""
            QPushButton {
                padding: 8px;
                border: none;
                border-radius: 8px;
                background-color: #6c757d;
                color: white;
                font-size: 18px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
            QPushButton:pressed {
                background-color: #545b62;
            }
        """)
        self.show_signup_password_btn.setCheckable(True)
        self.show_signup_password_btn.clicked.connect(self.toggle_signup_password_visibility)
        signup_password_layout.addWidget(self.show_signup_password_btn)
        
        # Add fields to layout
        signup_layout.addWidget(self.signup_email)
        signup_layout.addWidget(signup_password_container)
        signup_layout.addWidget(self.signup_confirm_password)
        
        # Add signup button
        self.signup_button = ModernButton("Sign Up")
        self.signup_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 15px;
                text-align: center;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                min-width: 120px;
                margin: 2px;
            }
            QPushButton:hover {
                background-color: #1976D2;
                margin: 0px;
                border: 2px solid #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
                margin: 2px;
            }
        """)
        
        self.switch_to_login_button = ModernButton("Already have an account? Login")
        self.switch_to_login_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #4CAF50;
                border: 2px solid #4CAF50;
                padding: 12px;
                text-align: center;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #4CAF50;
                color: white;
            }
            QPushButton:pressed {
                background-color: #45a049;
                color: white;
            }
        """)
        
        signup_layout.addWidget(self.signup_button)
        signup_layout.addWidget(self.switch_to_login_button)
        
        # Add stretch
        signup_layout.addStretch()
        
        signup_widget.setLayout(signup_layout)
        self.stacked_widget.addWidget(signup_widget)
        
        main_layout.addWidget(self.stacked_widget)
        self.setLayout(main_layout)
        
        # Connect buttons
        self.login_button.clicked.connect(self.handle_login)
        self.guest_button.clicked.connect(self.handle_guest_login)
        self.switch_to_signup_button.clicked.connect(self.slide_to_signup)
        self.signup_button.clicked.connect(self.handle_signup)
        self.switch_to_login_button.clicked.connect(self.slide_to_login)
        self.forgot_password_btn.clicked.connect(self.handle_forgot_password)

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
        email = self.signup_email.text().strip()
        password = self.signup_password.text().strip()
        confirm_password = self.signup_confirm_password.text().strip()

        if not all([email, password, confirm_password]):
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
            self.show_password_btn.setText("🔒")
        else:
            self.login_password.setEchoMode(QLineEdit.EchoMode.Password)
            self.show_password_btn.setText("👁️")
        # Prevent focus and layout shifts
        self.show_password_btn.clearFocus()
        self.show_password_btn.updateGeometry()

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
            self.show_signup_password_btn.setText("🔒")
        else:
            self.signup_password.setEchoMode(QLineEdit.EchoMode.Password)
            self.signup_confirm_password.setEchoMode(QLineEdit.EchoMode.Password)
            self.show_signup_password_btn.setText("👁️")
        # Prevent focus and layout shifts
        self.show_signup_password_btn.clearFocus()
        self.show_signup_password_btn.updateGeometry()

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
