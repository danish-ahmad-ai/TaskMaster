from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QLabel, QHeaderView, QFrame, QCheckBox, QInputDialog, QTabWidget, QCalendarWidget, QComboBox, QDialog, QStyledItemDelegate, QLineEdit, QTextEdit
)
from PyQt6.QtCore import Qt, QTimer, QDate
from PyQt6.QtGui import QFont, QColor
from ui.modern_widgets import ModernButton
from ui.custom_widgets import show_error, show_success, show_question, show_message
from datetime import datetime
from typing import Dict, Optional, TYPE_CHECKING
import logging
import html
import re

if TYPE_CHECKING:
    from todolist import ToDoListApp

logger = logging.getLogger(__name__)

# Create a class to manage global state
class GlobalState:
    def __init__(self):
        self.current_user: Optional[Dict] = None
        
    def set_user(self, user_data: Dict):
        self.current_user = user_data
        
    def get_user(self) -> Optional[Dict]:
        return self.current_user
        
    def clear_user(self):
        self.current_user = None

# Create global state instance
global_state = GlobalState()

# Import Firebase modules after global state setup
from firebase_config import db, auth, token_manager
from firebase_operations import FirebaseOperations

class PriorityLevel:
    URGENT = "Urgent ⚡"
    HIGH = "High 🔴"
    MEDIUM = "Medium 🟡"
    LOW = "Low 🟢"
    
    @staticmethod
    def get_priority_value(text):
        priorities = {
            PriorityLevel.URGENT: 1,
            PriorityLevel.HIGH: 2,
            PriorityLevel.MEDIUM: 3,
            PriorityLevel.LOW: 4
        }
        return priorities.get(text, 4)

class DatePickerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Due Date")
        layout = QVBoxLayout(self)
        
        self.calendar = QCalendarWidget()
        layout.addWidget(self.calendar)
        
        self.select_button = ModernButton("Select")
        self.select_button.clicked.connect(self.accept)
        layout.addWidget(self.select_button)

class DateDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        if index.column() != 1:  # Only for date column
            return None
            
        calendar = QCalendarWidget(parent)
        calendar.clicked.connect(calendar.close)
        return calendar
        
    def setEditorData(self, editor, index):
        try:
            date_str = index.model().data(index, Qt.ItemDataRole.DisplayRole)
            date = QDate.fromString(date_str, "yyyy-MM-dd")
            editor.setSelectedDate(date)
        except:
            editor.setSelectedDate(QDate.currentDate())
            
    def setModelData(self, editor, model, index):
        date = editor.selectedDate()
        model.setData(index, date.toString("yyyy-MM-dd"))

class PriorityDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        if index.column() != 2:  # Only for priority column
            return None
            
        combo = QComboBox(parent)
        combo.addItems([
            PriorityLevel.URGENT,
            PriorityLevel.HIGH,
            PriorityLevel.MEDIUM,
            PriorityLevel.LOW
        ])
        return combo
        
    def setEditorData(self, editor, index):
        current_value = index.model().data(index, Qt.ItemDataRole.DisplayRole)
        idx = editor.findText(current_value)
        if idx >= 0:
            editor.setCurrentIndex(idx)
            
    def setModelData(self, editor, model, index):
        value = editor.currentText()
        model.setData(index, value)

class TaskManager(QWidget):
    """Main task management interface."""
    
    def __init__(self, app: 'ToDoListApp'):
        super().__init__()
        self.app = app
        self.user_id: Optional[str] = None
        self.firebase_ops = FirebaseOperations(app.session_manager)
        self.init_ui()
        
        # Remove the setup_delegates call from here
        # We'll call it after UI initialization

    def init_ui(self):
        self.setWindowTitle("TaskMaster")
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Top bar with account button and welcome message
        top_bar = QHBoxLayout()
        
        # Welcome message
        welcome_label = QLabel("My Tasks")
        welcome_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        welcome_label.setStyleSheet("color: #2c3e50;")
        
        # Account button
        self.account_button = ModernButton("My Account 👤", color="#6c757d")
        self.account_button.setFixedWidth(150)
        
        top_bar.addWidget(welcome_label)
        top_bar.addStretch()
        top_bar.addWidget(self.account_button)
        main_layout.addLayout(top_bar)

        # Add tab widget with improved styling
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #e0e0e0;
                border-radius: 10px;
                background: white;
                padding: 10px;
            }
            QTabBar::tab {
                padding: 10px 20px;
                margin: 4px 2px;
                background: #f8f9fa;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                min-width: 120px;
                font-size: 13px;
                color: #4a5568;
            }
            QTabBar::tab:selected {
                background: #4a90e2;
                color: white;
                font-weight: bold;
            }
            QTabBar::tab:hover:!selected {
                background: #e9ecef;
                color: #2d3748;
            }
        """)

        # Create tables first
        self.task_table = ModernTable()
        self.completed_table = ModernTable()

        # Create tabs first before setting up tables
        self.active_tab = QWidget()
        self.completed_tab = QWidget()

        # Setup active tab
        active_layout = QVBoxLayout(self.active_tab)
        active_layout.setContentsMargins(10, 10, 10, 10)
        active_layout.setSpacing(10)
        
        # Add label for active tasks
        active_label = QLabel("Active Tasks")
        active_label.setStyleSheet("font-size: 16px; color: #2d3748; margin-bottom: 10px;")
        active_layout.addWidget(active_label)

        # Setup completed tab
        completed_layout = QVBoxLayout(self.completed_tab)
        completed_layout.setContentsMargins(10, 10, 10, 10)
        completed_layout.setSpacing(10)
        
        # Add label for completed tasks
        completed_label = QLabel("Completed Tasks")
        completed_label.setStyleSheet("font-size: 16px; color: #2d3748; margin-bottom: 10px;")
        completed_layout.addWidget(completed_label)

        # Now setup tables after tabs are created
        self.setup_tables()
        
        # Add tables to their respective layouts
        active_layout.addWidget(self.task_table)
        completed_layout.addWidget(self.completed_table)

        # Add tabs to tab widget
        self.tab_widget.addTab(self.active_tab, "Active Tasks 📝")
        self.tab_widget.addTab(self.completed_tab, "Completed Tasks ✅")
        main_layout.addWidget(self.tab_widget)

        # Button container
        button_container = QWidget()
        button_container.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        button_layout = QHBoxLayout(button_container)
        button_layout.setSpacing(10)
        button_layout.setContentsMargins(10, 5, 10, 5)

        # Action buttons (removed delete button)
        self.add_task_button = ModernButton("Add Task ➕", color="#28a745")
        self.update_task_button = ModernButton("Update Task 📝", color="#ffc107")
        self.toggle_task_button = ModernButton("Complete Task ✓", color="#4a90e2")
        self.logout_button = ModernButton("Logout 👋", color="#6c757d")

        # Add buttons
        for button in [self.add_task_button, self.update_task_button, 
                      self.toggle_task_button, self.logout_button]:
            button_layout.addWidget(button)
            button.setMinimumWidth(120)

        main_layout.addWidget(button_container)
        self.setLayout(main_layout)

        # Connect signals
        self.add_task_button.clicked.connect(self.add_task)
        self.update_task_button.clicked.connect(self.update_task)
        self.toggle_task_button.clicked.connect(self.toggle_task_completion)
        self.logout_button.clicked.connect(self.logout)
        self.account_button.clicked.connect(self.show_account)

    def set_user_id(self, user_id):
        """Set the current user ID and refresh the task list."""
        print(f"Setting user ID to: {user_id}")
        self.user_id = user_id
        if user_id:
            # Use QTimer to ensure UI is ready
            QTimer.singleShot(500, self.refresh_task_list)  # Increased delay

    def refresh_task_list(self):
        """Load tasks from Firebase and display them in appropriate tables."""
        try:
            self.task_table.setRowCount(0)
            self.completed_table.setRowCount(0)
            
            if not self.user_id:
                self.show_empty_state(self.task_table, "Please log in to see your tasks")
                self.show_empty_state(self.completed_table, "Please log in to see your tasks")
                return
            
            session = self.app.session_manager.load_session()
            if not session or not session.get('idToken'):
                return
            
            # Get tasks from Firebase
            tasks = db.child('tasks').child(self.user_id).get(token=session['idToken'])
            
            active_row = 0
            completed_row = 0
            
            if tasks and tasks.each():
                for task in tasks.each():
                    task_data = task.val()
                    if task_data:
                        # Determine which table to use
                        is_completed = task_data.get('completed', False)
                        target_table = self.completed_table if is_completed else self.task_table
                        current_row = completed_row if is_completed else active_row
                        
                        # Insert new row
                        target_table.insertRow(current_row)
                        
                        # Create items
                        name = task_data.get('task_name', '')
                        due_date = task_data.get('due_date', 'N/A')
                        priority = task_data.get('priority', 'Low')
                        
                        # Create table items
                        task_name_item = QTableWidgetItem(name)
                        due_date_item = QTableWidgetItem(due_date)
                        priority_item = QTableWidgetItem(priority)
                        
                        # Store task key in first column
                        task_name_item.setData(Qt.ItemDataRole.UserRole, task.key())
                        
                        # Set items in table
                        target_table.setItem(current_row, 0, task_name_item)
                        target_table.setItem(current_row, 1, due_date_item)
                        target_table.setItem(current_row, 2, priority_item)
                        
                        # Update row counter
                        if is_completed:
                            completed_row += 1
                        else:
                            active_row += 1
            
            # Show empty state if no tasks
            if self.task_table.rowCount() == 0:
                self.show_empty_state(self.task_table, "No active tasks")
            if self.completed_table.rowCount() == 0:
                self.show_empty_state(self.completed_table, "No completed tasks")
                
        except Exception as e:
            print(f"Error refreshing task list: {e}")

    def sanitize_input(self, text: str) -> str:
        """Sanitize user input."""
        # Remove HTML tags
        text = html.escape(text)
        
        # Remove potentially dangerous characters
        text = re.sub(r'[^\w\s-]', '', text)
        
        # Limit length
        return text[:200]  # Limit to 200 characters
        
    def add_task(self):
        """Add a new task with date picker and priority"""
        # Create a custom dialog for task input
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Task")
        layout = QVBoxLayout(dialog)

        # Task name input with character counter
        layout.addWidget(QLabel("Task Name:"))
        task_input = QLineEdit()  # Using QLineEdit instead of QTextEdit
        task_input.setMaxLength(50)  # Set maximum character limit
        task_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                background-color: white;
                font-size: 13px;
                min-height: 30px;
            }
            QLineEdit:focus {
                border: 1px solid #4a90e2;
            }
        """)

        # Add character counter label
        char_counter = QLabel("50 characters remaining")
        char_counter.setStyleSheet("color: #666; font-size: 11px;")
        
        # Update character counter as user types
        def update_counter():
            remaining = 50 - len(task_input.text())
            char_counter.setText(f"{remaining} characters remaining")
            if remaining < 10:
                char_counter.setStyleSheet("color: #dc3545; font-size: 11px;")
            else:
                char_counter.setStyleSheet("color: #666; font-size: 11px;")

        task_input.textChanged.connect(update_counter)
        
        layout.addWidget(task_input)
        layout.addWidget(char_counter)

    def update_task(self):
        """Update selected task"""
        try:
            selected_items = self.task_table.selectedItems()
            if not selected_items:
                show_error(self, "Error", "Please select a task to update")
                return
            
            row = selected_items[0].row()
            task_key = self.task_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            
            # Get current values
            current_name = self.task_table.item(row, 0).text()
            current_date = self.task_table.item(row, 1).text()
            current_priority = self.task_table.item(row, 2).text()
            
            # Create update dialog
            update_dialog = QDialog(self)
            update_dialog.setWindowTitle("Update Task")
            update_dialog.setMinimumWidth(400)
            layout = QVBoxLayout(update_dialog)
            
            # Task name input with character limit
            layout.addWidget(QLabel("Task Name:"))
            name_input = QLineEdit()
            name_input.setText(current_name)
            name_input.setMaxLength(50)
            name_input.setStyleSheet("""
                QLineEdit {
                    padding: 8px;
                    border: 1px solid #e0e0e0;
                    border-radius: 6px;
                    background-color: white;
                    font-size: 13px;
                    min-height: 30px;
                    color: #2d3748;
                }
                QLineEdit:focus {
                    border: 1px solid #4a90e2;
                }
            """)

            # Add character counter
            char_counter = QLabel(f"{50 - len(current_name)} characters remaining")
            char_counter.setStyleSheet("color: #666; font-size: 11px;")
            
            def update_counter():
                remaining = 50 - len(name_input.text())
                char_counter.setText(f"{remaining} characters remaining")
                if remaining < 10:
                    char_counter.setStyleSheet("color: #dc3545; font-size: 11px;")
                else:
                    char_counter.setStyleSheet("color: #666; font-size: 11px;")

            name_input.textChanged.connect(update_counter)
            
            layout.addWidget(name_input)
            layout.addWidget(char_counter)
            
            # Date picker
            layout.addWidget(QLabel("Due Date:"))
            date_picker = QCalendarWidget()
            try:
                current_qdate = QDate.fromString(current_date, "yyyy-MM-dd")
                if current_qdate.isValid():
                    date_picker.setSelectedDate(current_qdate)
            except:
                date_picker.setSelectedDate(QDate.currentDate())
            layout.addWidget(date_picker)
            
            # Priority dropdown
            layout.addWidget(QLabel("Priority:"))
            priority_combo = QComboBox()
            priority_combo.addItems([
                PriorityLevel.URGENT,
                PriorityLevel.HIGH,
                PriorityLevel.MEDIUM,
                PriorityLevel.LOW
            ])
            index = priority_combo.findText(current_priority)
            if index >= 0:
                priority_combo.setCurrentIndex(index)
            layout.addWidget(priority_combo)
            
            # Update button
            update_btn = ModernButton("Update Task")
            update_btn.clicked.connect(update_dialog.accept)
            layout.addWidget(update_btn)
            
            if update_dialog.exec() == QDialog.DialogCode.Accepted:
                # Get session
                session = self.app.session_manager.load_session()
                if not session or not session.get('idToken'):
                    show_error(self, "Error", "Please log in again to update task")
                    return
                    
                # Get new values
                new_name = name_input.text().strip()
                new_date = date_picker.selectedDate().toString("yyyy-MM-dd")
                new_priority = priority_combo.currentText()
                
                # Update in Firebase
                db.child('tasks').child(self.user_id).child(task_key).update({
                    'task_name': new_name,
                    'due_date': new_date,
                    'priority': new_priority,
                    'priority_value': PriorityLevel.get_priority_value(new_priority),
                    'updated_at': datetime.now().isoformat()
                }, token=session['idToken'])
                
                # Refresh task list
                self.refresh_task_list()
                show_success(self, "Success", "Task updated successfully! ✨")
                
        except Exception as e:
            print(f"Error updating task: {e}")
            show_error(self, "Error", "Failed to update task")

    def logout(self):
        """Logout and switch to the login screen."""
        self.app.switch_to_login()

    def show_account(self):
        """Switch to account management"""
        try:
            session = self.app.session_manager.load_session()
            if not session or not session.get('idToken'):
                show_error(self, "Error", "Please log in to view your account! 🔑")
                self.app.switch_to_login()
                return

            # First check if it's a guest user
            if session.get('is_guest'):
                show_error(
                    self, 
                    "Guest Mode", 
                    "This area is for registered users only! Please sign up to access your account. "
                )
                return

            try:
                # Get user data with timeout
                user_data = db.child('users').child(session['user_id']).get(token=session['idToken']).val()
                
                if user_data:
                    print("Successfully loaded user data")
                    self.app.account_manager.set_user_data(user_data)
                    self.app.widget_stack.setCurrentWidget(self.app.account_manager)
                else:
                    show_error(self, "Error", "Could not load account data. Please try again! ")
                    
            except Exception as e:
                print(f"Error loading account data: {str(e)}")
                show_error(self, "Error", "Failed to load account data. Please try again! 😅")

        except Exception as e:
            print(f"Error in show_account: {str(e)}")
            show_error(self, "Error", "Something went wrong. Please try again! 😅")

    def debug_print(self):
        """Debug function to print current state"""
        print("\n=== DEBUG INFO ===")
        print(f"Current user: {global_state.get_user()}")
        if global_state.get_user():
            print(f"Token exists: {'idToken' in global_state.get_user()}")
            print(f"Token value: {global_state.get_user().get('idToken', 'None')[:20]}..." if global_state.get_user().get('idToken') else "No token")
        print(f"User ID: {self.user_id}")
        
        session = self.app.session_manager.load_session()
        print("\nSession data:")
        if session:
            print(f"- User ID: {session.get('user_id')}")
            print(f"- Email: {session.get('email')}")
            print(f"- Logged in: {session.get('logged_in')}")
            print(f"- Token exists: {session.get('idToken') is not None}")
            if session.get('idToken'):
                print(f"- Token value: {session['idToken'][:20]}...")
        else:
            print("No session found")

    def toggle_task_completion(self):
        """Move task to completed tab"""
        current_row = self.task_table.currentRow()
        if current_row < 0:
            show_error(self, "Error", "Please select a task first! ✓")
            return

        try:
            # Get task data
            task_item = self.task_table.item(current_row, 0)  # Task name column
            if not task_item:
                return

            task_key = task_item.data(Qt.ItemDataRole.UserRole)
            
            # Get session
            session = self.app.session_manager.load_session()
            if not session:
                show_error(self, "Error", "Please log in to continue! 🔑")
                self.app.switch_to_login()
                return

            token = session.get('idToken')
            if not token:
                show_error(self, "Error", "Please log in again! 🔑")
                self.app.switch_to_login()
                return

            # Update task as completed with timestamp
            update_data = {
                'completed': True,
                'completed_at': datetime.now().isoformat()
            }
            
            # Update in Firebase
            db.child('tasks').child(self.user_id).child(task_key).update(update_data, token=token)
            
            # Switch to completed tab
            self.tab_widget.setCurrentWidget(self.completed_tab)
            
            # Refresh tables
            self.refresh_task_list()
            
            # Show success message
            show_success(self, "Success", "Task marked as completed! 🎉")

        except Exception as e:
            print(f"Error completing task: {str(e)}")
            show_error(self, "Error", "Something went wrong. Please try again! 😅")

    def get_valid_token(self):
        """Get a valid token for Firebase operations"""
        try:
            # First try to get token from current user
            if global_state.get_user() and global_state.get_user().get('idToken'):
                return global_state.get_user()['idToken']
            
            # Then try to get from session
            session = self.app.session_manager.load_session()
            if session and session.get('idToken'):
                return session['idToken']
            
            # No valid token found
            show_error(self, "Error", "Please log in to continue! 🔑")
            self.app.switch_to_login()
            return None
            
        except Exception as e:
            print(f"Error getting token: {str(e)}")
            return None

    def refresh_token(self):
        """Refresh the authentication token"""
        try:
            session = self.app.session_manager.load_session()
            if not session:
                return None

            refresh_token = session.get('refreshToken')
            if not refresh_token:
                return None

            # Try to refresh the token
            try:
                user = auth.refresh(refresh_token)
                if not user or not user.get('idToken'):
                    return None

                # Update session with new token
                new_token = user['idToken']
                self.app.session_manager.save_session(
                    user_id=session.get('user_id'),
                    email=session.get('email'),
                    token=new_token,
                    refresh_token=refresh_token
                )

                # Update current_user
                global_state.set_user({
                    'localId': session.get('user_id'),
                    'email': session.get('email'),
                    'idToken': new_token,
                    'refreshToken': refresh_token,
                    'isGuest': session.get('is_guest', False)
                })

                print("Token refreshed successfully")
                return new_token

            except Exception as e:
                print(f"Error refreshing token: {str(e)}")
                return None

        except Exception as e:
            print(f"Error in refresh_token: {str(e)}")
            return None

    def setup_tables(self):
        """Setup both tables with their configurations"""
        # Setup active tasks table
        self.setup_table(self.task_table)
        
        # Disable all editing in tables
        self.task_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.completed_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Remove the double-click connection if it exists
        try:
            self.task_table.itemDoubleClicked.disconnect()
        except:
            pass
        
        # Connect double-click to update_task instead
        self.task_table.itemDoubleClicked.connect(lambda _: self.update_task())

    def setup_delegates(self):
        """Set up delegates for table columns"""
        try:
            # Disconnect any existing connections first
            try:
                self.task_table.itemChanged.disconnect()
            except:
                pass
                
            # For active tasks table
            self.task_table.setItemDelegateForColumn(1, DateDelegate(self.task_table))
            self.task_table.setItemDelegateForColumn(2, PriorityDelegate(self.task_table))
            
            # Connect to cell change events - only once
            self.task_table.itemChanged.connect(self.handle_item_change)
            
        except Exception as e:
            print(f"Error setting up delegates: {e}")

    def handle_item_change(self, item):
        """Handle changes to table items"""
        try:
            if not item or not self.user_id:
                return
                
            row = item.row()
            column = item.column()
            new_value = item.text()
            
            # Get task key
            task_key = self.task_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            if not task_key:
                return
                
            # Get session
            session = self.app.session_manager.load_session()
            if not session or not session.get('idToken'):
                show_error(self, "Error", "Please log in again to update task")
                return
                
            # Block signals temporarily to prevent recursive updates
            self.task_table.blockSignals(True)
            
            try:
                # Update based on column
                if column == 0:  # Task name
                    db.child('tasks').child(self.user_id).child(task_key).update({
                        'task_name': new_value,
                        'updated_at': datetime.now().isoformat()
                    }, token=session['idToken'])
                    
                elif column == 1:  # Due date
                    db.child('tasks').child(self.user_id).child(task_key).update({
                        'due_date': new_value,
                        'updated_at': datetime.now().isoformat()
                    }, token=session['idToken'])
                    
                elif column == 2:  # Priority
                    db.child('tasks').child(self.user_id).child(task_key).update({
                        'priority': new_value,
                        'priority_value': PriorityLevel.get_priority_value(new_value),
                        'updated_at': datetime.now().isoformat()
                    }, token=session['idToken'])
                    self.sort_tasks_by_priority()
                    
                show_success(self, "Success", "Task updated successfully! ✨")
                
            finally:
                # Always unblock signals
                self.task_table.blockSignals(False)
                
        except Exception as e:
            print(f"Error updating task: {e}")
            show_error(self, "Error", "Failed to update task")
            self.refresh_task_list()  # Refresh to revert changes

    def setup_table(self, table):
        """Setup table columns and formatting"""
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Task Name", "Due Date", "Priority"])
        
        # Set column sizes
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        table.setColumnWidth(1, 120)
        table.setColumnWidth(2, 120)
        
        # Set row height
        table.verticalHeader().setDefaultSectionSize(45)
        
        # Additional styling
        table.setStyleSheet(table.styleSheet() + """
            QTableWidget {
                gridline-color: #f0f0f0;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #edf2f7;
                white-space: normal;
            }
        """)

        # Add info label for completed tasks tab if this is the completed table
        if table == self.completed_table:
            info_label = QLabel("✨ Completed tasks are automatically deleted after 20 days")
            info_label.setStyleSheet("""
                QLabel {
                    color: #666;
                    font-size: 12px;
                    font-style: italic;
                    padding: 5px;
                    background: #f8f9fa;
                    border-radius: 4px;
                    margin-top: 5px;
                }
            """)
            info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Add the label to the completed tab layout
            self.completed_tab.layout().addWidget(info_label)

    def show_empty_state(self, table, message="No tasks found"):
        """Show empty state message in table"""
        table.setRowCount(1)
        empty_item = QTableWidgetItem(message)
        empty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_item.setFlags(Qt.ItemFlag.NoItemFlags)  # Make non-selectable
        empty_item.setForeground(QColor("#a0aec0"))
        
        # Span all columns
        table.setSpan(0, 0, 1, table.columnCount())
        table.setItem(0, 0, empty_item)

    def check_old_completed_tasks(self):
        """Check and delete completed tasks older than 20 days"""
        try:
            session = self.app.session_manager.load_session()
            if not session or not session.get('idToken'):
                return
            
            tasks = db.child('tasks').child(self.user_id).get(token=session['idToken'])
            if tasks and tasks.each():
                current_time = datetime.now()
                
                for task in tasks.each():
                    task_data = task.val()
                    if task_data and task_data.get('completed'):
                        completed_at = task_data.get('completed_at')
                        if completed_at:
                            completed_date = datetime.fromisoformat(completed_at)
                            days_old = (current_time - completed_date).days
                            
                            if days_old >= 20:
                                # Delete the old completed task
                                db.child('tasks').child(self.user_id).child(task.key()).remove(
                                    token=session['idToken']
                                )
        except Exception as e:
            print(f"Error checking old completed tasks: {str(e)}")

    def handle_error(self, error: Exception, 
                    title: str = "Error", 
                    message: Optional[str] = None) -> None:
        """
        Handle and display errors to user.
        
        Args:
            error: Exception that occurred
            title: Error dialog title
            message: Optional custom error message
        """
        logger.error(f"Error in TaskManager: {error}")
        
        if "auth" in str(error).lower():
            show_error(self, "Session Expired", 
                      "Please log in again to continue.")
            self.app.switch_to_login()
        else:
            show_error(self, title, 
                      message or f"An error occurred: {str(error)}")

    def sort_tasks_by_priority(self):
        """Sort tasks by priority value"""
        rows = self.task_table.rowCount()
        items = []
        
        # Collect all rows
        for row in range(rows):
            items.append({
                'name': self.task_table.item(row, 0).text(),
                'date': self.task_table.item(row, 1).text(),
                'priority': self.task_table.item(row, 2).text(),
                'priority_value': PriorityLevel.get_priority_value(
                    self.task_table.item(row, 2).text()
                ),
                'key': self.task_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            })
        
        # Sort by priority value
        items.sort(key=lambda x: x['priority_value'])
        
        # Repopulate table
        self.task_table.setRowCount(0)
        for item in items:
            row = self.task_table.rowCount()
            self.task_table.insertRow(row)
            
            name_item = QTableWidgetItem(item['name'])
            date_item = QTableWidgetItem(item['date'])
            priority_item = QTableWidgetItem(item['priority'])
            
            name_item.setData(Qt.ItemDataRole.UserRole, item['key'])
            
            self.task_table.setItem(row, 0, name_item)
            self.task_table.setItem(row, 1, date_item)
            self.task_table.setItem(row, 2, priority_item)

    def handle_item_double_click(self, item):
        """Handle double-click on table items"""
        try:
            # Get the table that was clicked
            table = item.tableWidget()
            
            # Don't allow editing in completed table
            if table == self.completed_table:
                return
            
            column = table.column(item)
            row = table.row(item)
            
            # Get task key
            task_key = table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            if not task_key:
                return
            
            if column == 0:  # Task name
                # Allow direct editing
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                table.editItem(item)
            elif column == 1:  # Due date
                self.show_date_picker(row, task_key)
            elif column == 2:  # Priority
                self.show_priority_selector(row, task_key)
            
        except Exception as e:
            print(f"Error handling double click: {e}")
            show_error(self, "Error", "Failed to handle item edit")

    def show_date_picker(self, row, task_key):
        """Show date picker dialog for updating due date"""
        try:
            date_dialog = DatePickerDialog(self)
            if date_dialog.exec() == QDialog.DialogCode.Accepted:
                new_date = date_dialog.calendar.selectedDate().toString("yyyy-MM-dd")
                
                # Update in Firebase
                session = self.app.session_manager.load_session()
                if not session or not session.get('idToken'):
                    show_error(self, "Error", "Please log in again to update task")
                    return
                    
                db.child('tasks').child(self.user_id).child(task_key).update({
                    'due_date': new_date,
                    'updated_at': datetime.now().isoformat()
                }, token=session['idToken'])
                
                # Update table
                self.task_table.item(row, 1).setText(new_date)
                show_success(self, "Success", "Due date updated! 📅")
                
        except Exception as e:
            print(f"Error updating due date: {e}")
            show_error(self, "Error", "Failed to update due date")

    def show_priority_selector(self, row, task_key):
        """Show priority selector dialog for updating priority"""
        try:
            priority_dialog = QDialog(self)
            priority_dialog.setWindowTitle("Update Priority")
            layout = QVBoxLayout(priority_dialog)
            
            priority_combo = QComboBox()
            priority_combo.addItems([
                PriorityLevel.URGENT,
                PriorityLevel.HIGH,
                PriorityLevel.MEDIUM,
                PriorityLevel.LOW
            ])
            
            # Set current priority
            current_priority = self.task_table.item(row, 2).text()
            index = priority_combo.findText(current_priority)
            if index >= 0:
                priority_combo.setCurrentIndex(index)
                
            layout.addWidget(priority_combo)
            
            select_button = ModernButton("Update")
            select_button.clicked.connect(priority_dialog.accept)
            layout.addWidget(select_button)
            
            if priority_dialog.exec() == QDialog.DialogCode.Accepted:
                new_priority = priority_combo.currentText()
                
                # Update in Firebase
                session = self.app.session_manager.load_session()
                if not session or not session.get('idToken'):
                    show_error(self, "Error", "Please log in again to update task")
                    return
                    
                db.child('tasks').child(self.user_id).child(task_key).update({
                    'priority': new_priority,
                    'priority_value': PriorityLevel.get_priority_value(new_priority),
                    'updated_at': datetime.now().isoformat()
                }, token=session['idToken'])
                
                # Update table
                self.task_table.item(row, 2).setText(new_priority)
                
                # Resort tasks
                self.sort_tasks_by_priority()
                show_success(self, "Success", "Priority updated! 🎯")
                
        except Exception as e:
            print(f"Error updating priority: {e}")
            show_error(self, "Error", "Failed to update priority")

# Add this new class for modern table styling
class ModernTable(QTableWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 10px;
                gridline-color: #edf2f7;
                outline: none;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #edf2f7;
                color: #2d3748;
                background-color: #ffffff;
            }
            QTableWidget::item:alternate {
                background-color: #f8fafc;
            }
            QTableWidget::item:selected {
                background-color: #3b82f6;
                color: white;
                border: none;
            }
            QTableWidget::item:hover:!selected {
                background-color: #e5e7eb;
                color: #1a202c;
            }
        """)
        
        # Table settings
        self.setAlternatingRowColors(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        # Set row height
        self.verticalHeader().setDefaultSectionSize(45)

    def mousePressEvent(self, event):
        """Handle mouse press events"""
        item = self.itemAt(event.pos())
        if not item:
            self.clearSelection()
            self.setCurrentItem(None)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """Handle mouse release events"""
        super().mouseReleaseEvent(event)
        if not self.selectedItems():
            self.clearSelection()

__all__ = ['TaskManager']
