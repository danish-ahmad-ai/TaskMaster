from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QMessageBox,
    QFormLayout, QLineEdit, QFileDialog, QFrame, QDialog, QTabWidget, QScrollArea
)
from PyQt6.QtCore import Qt, QBuffer, QByteArray
from PyQt6.QtGui import QPixmap, QPainter, QPainterPath, QFont
from firebase_config import auth, db, current_user, storage
from ui.modern_widgets import ModernButton, ModernLineEdit
from ui.custom_widgets import show_error, show_success, show_question, ModernDialog
import json
from datetime import datetime
import os
import requests
from PyQt6.QtWidgets import QGraphicsDropShadowEffect
from PyQt6.QtGui import QColor
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ui.main_ui import TaskManager

class AccountManager(QWidget):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self.user_id = None
        
        # Get session data
        session = self.app.session_manager.load_session()
        if session and session.get('user_id'):
            self.user_id = session['user_id']
            
        self.init_ui()
        
        # Load user data after UI is initialized
        if self.user_id:
            try:
                # Get user data from Firebase
                user_data = db.child('users').child(self.user_id).get(token=session['idToken']).val()
                if user_data:
                    self.set_user_data(user_data)
                else:
                    # If no user data exists, create initial data
                    user_data = {
                        'email': session.get('email', ''),
                        'username': '',
                        'updated_at': datetime.now().isoformat()
                    }
                    db.child('users').child(self.user_id).set(user_data, token=session['idToken'])
                    self.set_user_data(user_data)
            except Exception as e:
                print(f"Error loading user data: {str(e)}")
                show_error(self, "Error", "Failed to load account data. Please try again!")
                self.close()

    def init_ui(self):
        self.setWindowTitle("My Account")
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Profile section
        profile_container = QWidget()
        profile_container.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 15px;
            }
        """)
        profile_layout = QVBoxLayout(profile_container)

        # Profile picture section
        pic_container = QWidget()
        pic_layout = QHBoxLayout(pic_container)
        
        self.profile_pic = QLabel()
        self.profile_pic.setFixedSize(150, 150)
        self.profile_pic.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border-radius: 75px;
                border: 2px solid #e0e0e0;
            }
        """)
        self.set_default_profile_picture()

        pic_buttons = QVBoxLayout()
        self.upload_pic_btn = ModernButton("Upload Picture 📸", color="#4a90e2")
        self.remove_pic_btn = ModernButton("Remove Picture ❌", color="#dc3545")
        pic_buttons.addWidget(self.upload_pic_btn)
        pic_buttons.addWidget(self.remove_pic_btn)

        # Add some styling to make them more visible
        self.upload_pic_btn.setStyleSheet(self.upload_pic_btn.styleSheet() + """
            QPushButton {
                font-weight: bold;
                border: 2px solid #4a90e2;
            }
        """)
        self.remove_pic_btn.setStyleSheet(self.remove_pic_btn.styleSheet() + """
            QPushButton {
                font-weight: bold;
                border: 2px solid #dc3545;
            }
        """)

        pic_layout.addWidget(self.profile_pic)
        pic_layout.addLayout(pic_buttons)
        pic_layout.addStretch()

        profile_layout.addWidget(pic_container)

        # User info form with modern styling
        form_container = QWidget()
        form_layout = QFormLayout(form_container)
        form_layout.setSpacing(15)

        self.username_input = ModernLineEdit()
        self.email_input = ModernLineEdit()
        self.email_input.setReadOnly(True)

        form_layout.addRow("Username:", self.username_input)
        form_layout.addRow("Email:", self.email_input)

        profile_layout.addWidget(form_container)
        main_layout.addWidget(profile_container)

        # Buttons
        button_container = QWidget()
        button_container.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        button_layout = QHBoxLayout(button_container)
        button_layout.setSpacing(15)
        button_layout.setContentsMargins(15, 10, 15, 10)
        
        # Create a central widget to hold buttons
        central_widget = QWidget()
        central_layout = QHBoxLayout(central_widget)
        central_layout.setSpacing(15)
        central_layout.setContentsMargins(0, 0, 0, 0)

        # Create buttons with shorter text
        self.save_changes_btn = ModernButton("Save 💾", color="#28a745")
        self.change_password_btn = ModernButton("Password 🔑", color="#ffc107")
        self.delete_account_btn = ModernButton("Delete ⚠️", color="#dc3545")
        self.back_btn = ModernButton("Back ↩️", color="#6c757d")
        self.app_info_btn = ModernButton("About ℹ️", color="#4a90e2")

        # Add buttons with equal spacing and height
        for button in [self.save_changes_btn, self.change_password_btn, 
                      self.delete_account_btn, self.back_btn, self.app_info_btn]:
            button.setFixedWidth(120)  # Fixed width
            button.setFixedHeight(35)  # Fixed height
            central_layout.addWidget(button)

        # Add central widget to main button layout with stretches on both sides
        button_layout.addStretch(1)
        button_layout.addWidget(central_widget)
        button_layout.addStretch(1)

        main_layout.addWidget(button_container)
        self.setLayout(main_layout)

        # Connect buttons
        self.upload_pic_btn.clicked.connect(self.upload_profile_picture)
        self.remove_pic_btn.clicked.connect(self.remove_profile_picture)
        self.save_changes_btn.clicked.connect(self.save_changes)
        self.change_password_btn.clicked.connect(self.change_password)
        self.delete_account_btn.clicked.connect(self.delete_account)
        self.back_btn.clicked.connect(self.go_back)
        self.app_info_btn.clicked.connect(self.show_app_info)

    def set_user_data(self, user_data):
        """Set the user data in the form"""
        if user_data:
            try:
                self.username_input.setText(user_data.get('username', ''))
                self.email_input.setText(user_data.get('email', ''))
                
                # Load profile picture with timeout and better error handling
                profile_url = user_data.get('profile_picture_url')
                if profile_url:
                    try:
                        # Set timeout and headers for better reliability
                        headers = {
                            'User-Agent': 'Mozilla/5.0',
                            'Accept': 'image/webp,image/*,*/*;q=0.8'
                        }
                        response = requests.get(
                            profile_url, 
                            headers=headers,
                            timeout=10  # 10 seconds timeout
                        )
                        
                        if response.status_code == 200:
                            pixmap = QPixmap()
                            pixmap.loadFromData(response.content)
                            
                            # Process image
                            size = 150
                            scaled_pixmap = pixmap.scaled(
                                size, size,
                                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                Qt.TransformationMode.SmoothTransformation
                            )
                            
                            # Create mask
                            final_pixmap = QPixmap(size, size)
                            final_pixmap.fill(Qt.GlobalColor.transparent)
                            
                            painter = QPainter(final_pixmap)
                            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                            path = QPainterPath()
                            path.addEllipse(0, 0, size, size)
                            painter.setClipPath(path)
                            
                            # Center and draw
                            x = (scaled_pixmap.width() - size) // 2
                            y = (scaled_pixmap.height() - size) // 2
                            painter.drawPixmap(-x, -y, scaled_pixmap)
                            painter.end()
                            
                            self.profile_pic.setPixmap(final_pixmap)
                            self.profile_pic.setStyleSheet("""
                                QLabel {
                                    background-color: transparent;
                                    border-radius: 75px;
                                    border: 2px solid #e0e0e0;
                                }
                            """)
                        else:
                            print(f"Failed to load profile picture: {response.status_code}")
                            self.set_default_profile_picture()
                            
                    except requests.Timeout:
                        print("Profile picture loading timed out")
                        self.set_default_profile_picture()
                        
                    except requests.ConnectionError:
                        print("Connection error loading profile picture")
                        self.set_default_profile_picture()
                        
                    except Exception as e:
                        print(f"Error loading profile picture: {str(e)}")
                        self.set_default_profile_picture()
                else:
                    self.set_default_profile_picture()
                    
            except Exception as e:
                print(f"Error setting user data: {str(e)}")
                show_error(self, "Error", "Failed to load account data. Please try again! 😅")
                self.app.switch_to_task_manager(self.user_id)

    def set_default_profile_picture(self):
        """Set a default profile picture"""
        self.profile_pic.setText("👤")
        self.profile_pic.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.profile_pic.setStyleSheet("""
            QLabel {
                background-color: #f0f0f0;
                border-radius: 50px;
                border: 2px solid #ddd;
                font-size: 40px;
            }
        """)

    def upload_profile_picture(self):
        """Upload a new profile picture using ImgBB"""
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Select Profile Picture", "",
            "Image Files (*.png *.jpg *.jpeg)"
        )
        if file_name:
            try:
                session = self.app.session_manager.load_session()
                if not session or not session.get('idToken'):
                    show_error(self, "Error", "Please log in to continue! 🔑")
                    return

                # Process image in memory
                pixmap = QPixmap(file_name)
                size = 150
                square_pixmap = QPixmap(size, size)
                square_pixmap.fill(Qt.GlobalColor.transparent)
                
                scaled_pixmap = pixmap.scaled(
                    size, size,
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation
                )
                
                # Create circular mask in memory
                painter = QPainter(square_pixmap)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                path = QPainterPath()
                path.addEllipse(0, 0, size, size)
                painter.setClipPath(path)
                painter.drawPixmap(0, 0, scaled_pixmap)
                painter.end()

                # Save to bytes and encode as base64
                byte_array = QByteArray()
                buffer = QBuffer(byte_array)
                buffer.open(QBuffer.OpenModeFlag.WriteOnly)
                square_pixmap.save(buffer, "PNG")
                
                # Convert to base64
                import base64
                image_data = base64.b64encode(byte_array.data()).decode('utf-8')

                # Upload to ImgBB
                url = "https://api.imgbb.com/1/upload"
                payload = {
                    'key': '5729755a91d2006b103bc300a8ab124e',
                    'image': image_data
                }
                
                response = requests.post(url, payload)
                
                if response.status_code == 200:
                    image_url = response.json()['data']['url']
                    
                    # Store URL in Firebase database
                    db.child('users').child(session['user_id']).update({
                        'profile_picture_url': image_url,
                        'updated_at': datetime.now().isoformat()
                    }, token=session['idToken'])

                    # Update UI
                    self.profile_pic.setPixmap(square_pixmap)
                    self.profile_pic.setStyleSheet("""
                        QLabel {
                            background-color: transparent;
                            border-radius: 75px;
                            border: 2px solid #e0e0e0;
                        }
                    """)
                    show_success(self, "Success", "Profile picture updated! ✨")
                else:
                    print(f"ImgBB API Error: {response.text}")
                    raise Exception("Failed to upload image")

            except Exception as e:
                print(f"Error uploading profile picture: {str(e)}")
                show_error(self, "Error", "Failed to upload profile picture. Please try again! 😅")

    def remove_profile_picture(self):
        """Remove the profile picture"""
        self.set_default_profile_picture()
        # TODO: Remove from Firebase Storage

    def save_changes(self):
        """Save user changes"""
        try:
            # First try to get session data
            session = self.app.session_manager.load_session()
            
            # Check if we have a valid session
            if not session or not session.get('idToken'):
                print("No valid session found")
                self.app.switch_to_login()
                return
            
            user_data = {
                'username': self.username_input.text().strip(),
                'updated_at': datetime.now().isoformat()
            }
            
            # Use session data for the update
            user_id = session.get('user_id')
            token = session.get('idToken')
            
            if not user_id or not token:
                raise Exception("Missing user ID or token")
            
            print(f"Attempting to update profile for user: {user_id}")
            
            # Update the database
            db.child('users').child(user_id).update(
                user_data, 
                token=token
            )
            
            QMessageBox.information(self, "Success", "Profile updated successfully! 🎉")
            
        except Exception as e:
            print(f"Error updating profile: {str(e)}")
            error_msg = str(e)
            if "not authenticated" in error_msg.lower() or "invalid token" in error_msg.lower():
                print("Authentication error - redirecting to login")
                QMessageBox.warning(
                    self, 
                    "Session Expired", 
                    "Your session has expired. Please log in again."
                )
                self.app.switch_to_login()
            else:
                QMessageBox.warning(
                    self, 
                    "Error", 
                    "Failed to update profile. Please try again!"
                )

    def change_password(self):
        """Send password reset email"""
        try:
            auth.send_password_reset_email(self.email_input.text())
            QMessageBox.information(
                self, 
                "Password Reset", 
                "Password reset link sent to your email! ✉️"
            )
        except Exception as e:
            print(f"Error sending reset email: {str(e)}")
            QMessageBox.warning(
                self, 
                "Error", 
                "Failed to send reset email. Please try again!"
            )

    def delete_account(self):
        """Delete user account"""
        try:
            session = self.app.session_manager.load_session()
            if not session or not session.get('idToken'):
                show_error(self, "Error", "Please log in again to delete your account")
                self.app.switch_to_login()
                return
            
            reply = show_question(
                self, 
                "Delete Account", 
                "Are you sure you want to delete your account? This cannot be undone! ⚠️"
            )
            
            if reply == "Yes":
                try:
                    # Delete user data from Firestore
                    db.child('users').child(session['user_id']).remove(token=session['idToken'])
                    db.child('tasks').child(session['user_id']).remove(token=session['idToken'])
                    
                    # Delete user authentication
                    auth.delete_user_account(session['idToken'])
                    
                    show_success(self, "Account Deleted", "Your account has been deleted. We're sad to see you go! 👋")
                    
                    # Clear session and switch to login
                    self.app.session_manager.clear_session()
                    self.app.switch_to_login()
                    
                except Exception as e:
                    print(f"Error during account deletion: {e}")
                    show_error(self, "Error", "Failed to delete account completely. Some data might remain.")
                    
        except Exception as e:
            print(f"Error initiating account deletion: {e}")
            show_error(self, "Error", "Failed to start account deletion process. Please try again.")

    def go_back(self):
        """Return to task manager"""
        try:
            # Get the task manager widget (it should be at index 1)
            task_manager = self.app.widget_stack.widget(1)
            if task_manager:
                self.app.widget_stack.setCurrentWidget(task_manager)
        except Exception as e:
            print(f"Error returning to task manager: {e}")
            # Fallback - try to switch to widget at index 1
            if self.app.widget_stack.count() > 1:
                self.app.widget_stack.setCurrentWidget(self.app.widget_stack.widget(1))

    def show_app_info(self):
        """Show the welcome/about dialog with tabs"""
        # Define content for each tab
        about_text = """
        <div style='text-align: center;'>
            <h2 style='color: #4a90e2; margin-bottom: 15px;'>✨ TaskMaster Pro ✨</h2>
            
            <p style='font-size: 14px; color: #2c3e50; margin: 10px 0;'>
                Your Ultimate Task Management Solution
            </p>
            
            <p style='font-size: 13px; color: #34495e; line-height: 1.6;'>
                Streamline your productivity with TaskMaster Pro's powerful features,
                intuitive interface, and secure cloud synchronization.
            </p>
            
            <div style='margin-top: 20px; padding-top: 15px; border-top: 1px solid #eee;'>
                <p style='font-size: 13px; color: #7f8c8d;'>
                    Version 1.0.0<br>
                    Developed by <b>Danish Ahmad</b><br>
                    <a href='https://danishahmad.xyz' style='color: #4a90e2; text-decoration: none;'>Portfolio</a> | 
                    <a href='https://github.com/danish-ahmad-ai' style='color: #4a90e2; text-decoration: none;'>GitHub</a> |
                    <a href='https://d-techsolutions.agency' style='color: #4a90e2; text-decoration: none;'>D-Tech Solutions</a>
                </p>
            </div>
        </div>
        """

        features_text = """
        <div style='padding: 10px;'>
            <h3 style='color: #4a90e2; margin-bottom: 15px;'>🔐 Core Features</h3>
            <ul style='list-style-type: none; padding-left: 20px; color: #34495e;'>
                <li style='margin: 8px 0;'>• Smart Task Organization with Priority Levels</li>
                <li style='margin: 8px 0;'>• Real-time Cloud Synchronization</li>
                <li style='margin: 8px 0;'>• Secure User Authentication</li>
                <li style='margin: 8px 0;'>• Customizable Task Categories</li>
                <li style='margin: 8px 0;'>• Due Date Reminders & Notifications</li>
            </ul>
            
            <h3 style='color: #4a90e2; margin: 20px 0 15px 0;'>🛡️ Security Features</h3>
            <ul style='list-style-type: none; padding-left: 20px; color: #34495e;'>
                <li style='margin: 8px 0;'>• End-to-End Data Encryption</li>
                <li style='margin: 8px 0;'>• Secure Token Management</li>
                <li style='margin: 8px 0;'>• Automatic Session Handling</li>
                <li style='margin: 8px 0;'>• Regular Security Updates</li>
            </ul>
            
            <h3 style='color: #4a90e2; margin: 20px 0 15px 0;'>💫 User Experience</h3>
            <ul style='list-style-type: none; padding-left: 20px; color: #34495e;'>
                <li style='margin: 8px 0;'>• Modern & Intuitive Interface</li>
                <li style='margin: 8px 0;'>• Customizable User Profiles</li>
                <li style='margin: 8px 0;'>• Cross-Platform Compatibility</li>
                <li style='margin: 8px 0;'>• Offline Support</li>
            </ul>
        </div>
        """

        updates_text = """
        <div style='padding: 10px;'>
            <h3 style='color: #4a90e2; margin-bottom: 15px;'>💻 Coming Soon</h3>
            <ul style='list-style-type: none; padding-left: 20px; color: #34495e;'>
                <li style='margin: 12px 0;'>
                    <b>🌙 Dark Mode</b><br>
                    <span style='font-size: 12px; color: #666;'>Enhanced visual comfort with dark theme support</span>
                </li>
                <li style='margin: 12px 0;'>
                    <b>📱 Mobile App</b><br>
                    <span style='font-size: 12px; color: #666;'>Native iOS and Android applications</span>
                </li>
                <li style='margin: 12px 0;'>
                    <b>🤝 Team Collaboration</b><br>
                    <span style='font-size: 12px; color: #666;'>Share and collaborate on tasks with team members</span>
                </li>
                <li style='margin: 12px 0;'>
                    <b>📊 Advanced Analytics</b><br>
                    <span style='font-size: 12px; color: #666;'>Detailed insights into your productivity patterns</span>
                </li>
                <li style='margin: 12px 0;'>
                    <b>🔄 Integration Support</b><br>
                    <span style='font-size: 12px; color: #666;'>Connect with popular productivity tools</span>
                </li>
            </ul>
            
            <p style='color: #7f8c8d; font-style: italic; margin-top: 20px; text-align: center;'>
                We're constantly improving! Stay tuned for these exciting features. 🚀<br>
                <span style='font-size: 12px;'>Have suggestions? Email us at mrdanishkhb@gmail.com</span>
            </p>
        </div>
        """

        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        dialog.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Create main container
        container = QWidget()
        container.setObjectName("container")
        container.setStyleSheet("""
            QWidget#container {
                background-color: white;
                border-radius: 10px;
                padding: 10px;
            }
            QTabWidget::pane {
                border: none;
                background: white;
                padding: 10px;
            }
            QTabWidget::tab-bar {
                alignment: center;
            }
            /* Hide all corner widgets and buttons */
            QTabWidget::right-corner,
            QTabWidget::left-corner {
                width: 0px;
                border: none;
                background: transparent;
            }
            QTabBar::scroller,
            QTabBar QToolButton,
            QTabBar::tear,
            QTabBar::tear:left,
            QTabBar::tear:right {
                width: 0px;
                height: 0px;
                border: none;
                background: transparent;
            }
            QTabBar::tab {
                padding: 8px 16px;
                margin: 4px 2px;
                background: #f8f9fa;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                min-width: 80px;
                font-size: 13px;
                color: #2c3e50;
                font-weight: 500;
            }
            QTabBar::tab:selected {
                background: #4a90e2;
                color: white;
                font-weight: bold;
                border: none;
            }
            QTabBar::tab:hover:!selected {
                background: #e9ecef;
                color: #4a90e2;
                border: 1px solid #4a90e2;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 8px;
                border-radius: 4px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #a0a0a0;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QLabel {
                font-size: 13px;
                line-height: 1.5;
                padding: 10px;
                color: #2c3e50;
            }
        """)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 2)
        container.setGraphicsEffect(shadow)
        
        container_layout = QVBoxLayout(container)
        
        # Create tab widget
        tab_widget = QTabWidget()
        tab_widget.setDocumentMode(True)
        tab_widget.setMovable(False)
        tab_widget.setTabBarAutoHide(False)
        tab_widget.setCornerWidget(None)  # Remove corner widget
        tab_widget.setUsesScrollButtons(False)  # Disable scroll buttons
        
        # Create scrollable areas for each tab
        for tab_name, content in [
            ("About", about_text),
            ("Features", features_text),
            ("Updates", updates_text)
        ]:
            # Create scroll area
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            
            # Create content widget
            content_widget = QWidget()
            content_layout = QVBoxLayout(content_widget)
            
            # Add content label
            label = QLabel(content)
            label.setWordWrap(True)
            label.setTextFormat(Qt.TextFormat.RichText)
            label.setStyleSheet("""
                QLabel {
                    padding: 20px;
                    background: #ffffff;
                    border-radius: 8px;
                    border: 1px solid #e0e0e0;
                }
            """)
            label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            
            content_layout.addWidget(label)
            content_layout.addStretch()
            
            # Set scroll widget
            scroll.setWidget(content_widget)
            
            # Add to tab widget
            tab_widget.addTab(scroll, tab_name)
        
        container_layout.addWidget(tab_widget)
        
        # Add close button
        close_btn = ModernButton("Close", color="#6c757d")
        close_btn.clicked.connect(dialog.accept)
        close_btn.setFixedWidth(100)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        container_layout.addLayout(button_layout)
        
        layout.addWidget(container)
        
        # Set size
        dialog.setFixedSize(400, 500)
        
        # Center dialog
        if self.parent():
            center = self.parent().mapToGlobal(self.parent().rect().center())
            dialog.move(center.x() - dialog.width() // 2,
                       center.y() - dialog.height() // 2)
        
        dialog.exec() 