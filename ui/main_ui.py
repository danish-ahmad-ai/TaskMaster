from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, 
    QLabel, QHeaderView, QFrame, QCheckBox, QInputDialog, QTabWidget, QCalendarWidget, QComboBox, 
    QDialog, QStyledItemDelegate, QLineEdit
)
from PyQt6.QtCore import Qt, QTimer, QDate, QEvent
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
            
    def editorEvent(self, event, model, option, index):
        if event.type() == QEvent.Type.MouseButtonDblClick:
            # Create a custom dialog for the calendar
            dialog = QDialog()
            dialog.setWindowTitle("Select Due Date")
            dialog.setStyleSheet("""
                QDialog {
                    background-color: white;
                    border-radius: 10px;
                    border: 1px solid #e0e0e0;
                }
            """)
            
            # Create layout
            layout = QVBoxLayout(dialog)
            
            # Add calendar widget
            calendar = QCalendarWidget(dialog)
            calendar.setMinimumDate(QDate.currentDate())
            calendar.setStyleSheet("""
                QCalendarWidget {
                    background-color: white;
                    border: none;
                }
                QCalendarWidget QToolButton {
                    color: #2d3748;
                    background-color: transparent;
                    border: none;
                    border-radius: 4px;
                    padding: 4px;
                }
                QCalendarWidget QToolButton:hover {
                    background-color: #e9ecef;
                }
                QCalendarWidget QMenu {
                    background-color: white;
                    border: 1px solid #e0e0e0;
                    border-radius: 4px;
                }
                QCalendarWidget QSpinBox {
                    border: 1px solid #e0e0e0;
                    border-radius: 4px;
                    padding: 2px;
                }
            """)
            layout.addWidget(calendar)
            
            # Add buttons
            button_layout = QHBoxLayout()
            ok_button = ModernButton("Select", color="#4a90e2")
            cancel_button = ModernButton("Cancel", color="#6c757d")
            
            ok_button.clicked.connect(dialog.accept)
            cancel_button.clicked.connect(dialog.reject)
            
            button_layout.addWidget(cancel_button)
            button_layout.addWidget(ok_button)
            layout.addLayout(button_layout)
            
            # Center the dialog on screen
            screen = QApplication.primaryScreen().geometry()
            dialog_size = dialog.sizeHint()
            x = screen.center().x() - dialog_size.width() // 2
            y = screen.center().y() - dialog_size.height() // 2
            dialog.move(x, y)

            if dialog.exec() == QDialog.DialogCode.Accepted:
                selected_date = calendar.selectedDate().toString("yyyy-MM-dd")
                model.setData(index, selected_date)
                return True
        return False

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

class TaskNameDelegate(QStyledItemDelegate):
    def __init__(self, task_manager, parent=None):
        super().__init__(parent)
        self.task_manager = task_manager

    def createEditor(self, parent, option, index):
        return None  # Disable direct editing
        
    def editorEvent(self, event, model, option, index):
        if event.type() == QEvent.Type.MouseButtonDblClick:
            self.task_manager.update_task()
            return True
        return False

class TaskManager(QWidget):
    """Main task management interface."""
    
    def __init__(self, app: 'ToDoListApp'):
        """Initialize TaskManager."""
        try:
            super().__init__()
            self.app = app
            self.user_id = None
            self.firebase_ops = FirebaseOperations(app.session_manager)
            
            print("Initializing TaskManager...")
            self.init_ui()
            print("TaskManager initialization complete")
            
        except Exception as e:
            print(f"Error in TaskManager initialization: {str(e)}")
            raise  # Re-raise to see the full traceback

    def init_ui(self):
        """Initialize the user interface."""
        try:
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

            # Create tables first
            self.task_table = ModernTable()
            self.completed_table = ModernTable()
            
            # Setup tables with columns and formatting
            for table in [self.task_table, self.completed_table]:
                table.setColumnCount(3)
                table.setHorizontalHeaderLabels(["Task Name", "Due Date", "Priority"])
                
                # Set column widths
                header = table.horizontalHeader()
                header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
                header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
                header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
                table.setColumnWidth(1, 120)
                table.setColumnWidth(2, 120)
                
                # Enable word wrap and adjust row heights
                table.setWordWrap(True)
                table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
                
                # Connect double-click handler only for active tasks table
                if table == self.task_table:
                    table.cellDoubleClicked.connect(self.handle_cell_double_click)

            # Remove the setup_tables call since we're doing it here
            self.setup_delegates()

            # Add tab widget with improved styling
            self.tab_widget = QTabWidget()
            self.tab_widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # Disable focus
            self.tab_widget.setStyleSheet("""
                QTabWidget::pane {
                    border: none;
                    border-radius: 10px;
                    background: white;
                    padding: 10px;
                }
                QTabWidget::tab-bar {
                    alignment: left;
                }
                QTabBar {
                    background: transparent;
                }
                QTabBar::tab {
                    padding: 10px 20px;
                    margin: 4px 2px;
                    background: #f8f9fa;
                    border: none;
                    border-radius: 6px;
                    min-width: 120px;
                    font-size: 13px;
                    color: #4a5568;
                    outline: none;
                    text-decoration: none;
                }
                QTabBar::tab:selected {
                    background: #4a90e2;
                    color: white;
                    font-weight: bold;
                    border: none;
                    outline: none;
                }
                QTabBar::tab:hover:!selected {
                    background: #e9ecef;
                    color: #2d3748;
                }
                QTabBar::tab:focus {
                    outline: none;
                    border: none;
                }
                QTabBar::tab:selected:focus {
                    outline: none;
                    border: none;
                }
                QTabBar QToolButton {
                    border: none;
                    outline: none;
                }
            """)

            # Create tabs
            self.active_tab = QWidget()
            self.completed_tab = QWidget()
            
            # Set focus policy for the tabs
            self.active_tab.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            self.completed_tab.setFocusPolicy(Qt.FocusPolicy.NoFocus)

            # Setup active tab
            active_layout = QVBoxLayout(self.active_tab)
            active_layout.setContentsMargins(10, 10, 10, 10)
            active_layout.setSpacing(10)
            active_layout.addWidget(self.task_table)

            # Setup completed tab
            completed_layout = QVBoxLayout(self.completed_tab)
            completed_layout.setContentsMargins(10, 10, 10, 10)
            completed_layout.setSpacing(10)
            
            # Add buttons for completed tasks
            completed_buttons_layout = QHBoxLayout()
            self.clear_all_btn = ModernButton("Clear All", color="#dc3545")
            self.delete_selected_btn = ModernButton("Delete Selected", color="#dc3545")
            
            self.clear_all_btn.clicked.connect(self.clear_all_completed_tasks)
            self.delete_selected_btn.clicked.connect(self.delete_selected_completed_tasks)
            
            completed_buttons_layout.addWidget(self.clear_all_btn)
            completed_buttons_layout.addWidget(self.delete_selected_btn)
            completed_buttons_layout.addStretch()
            
            completed_layout.addLayout(completed_buttons_layout)
            completed_layout.addWidget(self.completed_table)

            # Add tabs to tab widget with icons
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

            # Action buttons
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

            print("UI initialization completed successfully")

        except Exception as e:
            print(f"Error initializing UI: {str(e)}")
            raise  # Re-raise the exception to see the full traceback

    def set_user_id(self, user_id):
        """Set the current user ID and refresh the task list."""
        try:
            print(f"Setting user ID to: {user_id}")
            self.user_id = user_id
            if user_id:
                # Load tasks silently without showing alerts
                self.load_initial_tasks()
                
        except Exception as e:
            print(f"Error in set_user_id: {str(e)}")

    def load_initial_tasks(self):
        """Load tasks from Firebase"""
        try:
            session = self.app.session_manager.load_session()
            if not session or not session.get('idToken'):
                show_error(self, "Error", "Please log in to view tasks")
                return
            
            # Clear existing tasks
            self.task_table.setRowCount(0)
            self.completed_table.setRowCount(0)
            
            # Get tasks from Firebase
            tasks = db.child('tasks').child(self.user_id).get(token=session['idToken'])
            
            if not tasks:
                self.show_empty_state(self.task_table, "No active tasks")
                self.show_empty_state(self.completed_table, "No completed tasks")
                return
            
            active_row = 0
            completed_row = 0
            
            # Block signals during loading
            self.task_table.blockSignals(True)
            self.completed_table.blockSignals(True)
            
            for task in tasks.each() or []:
                try:
                    task_data = task.val()
                    if not task_data:
                        continue
                    
                    # Add key to task data
                    task_data['key'] = task.key()
                    
                    # Determine which table to use
                    is_completed = task_data.get('completed', False)
                    target_table = self.completed_table if is_completed else self.task_table
                    current_row = completed_row if is_completed else active_row
                    
                    # Add row and load task
                    target_table.insertRow(current_row)
                    self.load_task_to_table(target_table, task_data, current_row)
                    
                    # Update counter
                    if is_completed:
                        completed_row += 1
                    else:
                        active_row += 1
                    
                except Exception as e:
                    print(f"Error loading task: {str(e)}")
                    continue
                
            # Re-enable signals
            self.task_table.blockSignals(False)
            self.completed_table.blockSignals(False)
            
            print(f"Successfully loaded {active_row} active and {completed_row} completed tasks")
            
        except Exception as e:
            print(f"Error loading initial tasks: {str(e)}")
            show_error(self, "Error", "Failed to load tasks")

    def setup_delegates(self):
        """Set up delegates for table columns"""
        try:
            # Disconnect any existing connections first
            try:
                self.task_table.itemChanged.disconnect()
            except:
                pass
            
            # For active tasks table only (not completed table)
            date_delegate = DateDelegate(self.task_table)
            priority_delegate = PriorityDelegate(self.task_table)
            
            # Remove the task name delegate to prevent direct editing
            self.task_table.setItemDelegateForColumn(1, date_delegate)
            self.task_table.setItemDelegateForColumn(2, priority_delegate)
            
            # Make task name column non-editable
            for row in range(self.task_table.rowCount()):
                if self.task_table.item(row, 0):
                    self.task_table.item(row, 0).setFlags(
                        self.task_table.item(row, 0).flags() & ~Qt.ItemFlag.ItemIsEditable
                    )
            
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
                    
                # Reload tasks silently
                self.load_initial_tasks()
                
            except Exception as e:
                print(f"Error updating task: {e}")
                show_error(self, "Error", "Failed to update task")
                self.load_initial_tasks()  # Refresh to revert changes
                
            finally:
                # Always unblock signals
                self.task_table.blockSignals(False)
                
        except Exception as e:
            print(f"Error in handle_item_change: {e}")
            self.load_initial_tasks()  # Refresh to revert changes

    def setup_table(self, table):
        """Setup table columns and formatting"""
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Task Name", "Due Date", "Priority"])
        
        # Set column sizes
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        table.setColumnWidth(1, 120)
        table.setColumnWidth(2, 120)
        
        # Set row height
        table.verticalHeader().setDefaultSectionSize(45)
        table.verticalHeader().setVisible(False)  # Hide row numbers
        
        # Additional styling
        table.setStyleSheet("""
            QTableWidget {
                gridline-color: #f0f0f0;
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 10px;
                padding: 5px;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #edf2f7;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 8px;
                border: none;
                font-weight: bold;
                color: #2d3748;
            }
        """)

        # Enable alternating row colors
        table.setAlternatingRowColors(True)
        
        # Enable selection of entire rows
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

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
        """Sort tasks by priority"""
        try:
            rows = self.task_table.rowCount()
            tasks = []
            
            # Collect all tasks
            for row in range(rows):
                task_name = self.task_table.item(row, 0).text()
                due_date = self.task_table.item(row, 1).text()
                priority = self.task_table.item(row, 2).text()
                task_key = self.task_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
                priority_value = PriorityLevel.get_priority_value(priority)
                
                tasks.append({
                    'row': row,
                    'task_name': task_name,
                    'due_date': due_date,
                    'priority': priority,
                    'priority_value': priority_value,
                    'key': task_key
                })
            
            # Sort by priority value
            tasks.sort(key=lambda x: x['priority_value'])
            
            # Reorder table
            for new_row, task in enumerate(tasks):
                old_row = task['row']
                if new_row != old_row:
                    self.task_table.insertRow(new_row)
                    for col in range(self.task_table.columnCount()):
                        self.task_table.setItem(
                            new_row, 
                            col, 
                            self.task_table.takeItem(old_row + (1 if old_row > new_row else 0), col))
                    self.task_table.removeRow(old_row + (1 if old_row > new_row else 0))
            
        except Exception as e:
            print(f"Error sorting tasks: {str(e)}")

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

    def handle_cell_double_click(self, row, column):
        """Handle double-click on table cells"""
        try:
            # Only handle double-clicks in the task name column (column 0) for active tasks
            if column == 0 and self.tab_widget.currentWidget() == self.active_tab:
                # Get the item safely
                current_item = self.task_table.item(row, 0)
                if not current_item:
                    return
                
                # Store the task key before any operations
                task_key = current_item.data(Qt.ItemDataRole.UserRole)
                if not task_key:
                    return
                
                # Get the text content safely
                task_text = current_item.text()
                if not task_text:
                    return
                
                # Split into lines and get task name and notes
                lines = task_text.split('\n')
                task_name = lines[0] if lines else ""
                notes = '\n'.join(line.lstrip('• ') for line in lines[1:] if line.strip())
                
                # Get current task data
                task_data = {
                    'task_name': task_name,
                    'due_date': self.task_table.item(row, 1).text(),
                    'priority': self.task_table.item(row, 2).text(),
                    'notes': notes
                }
                
                # Show update dialog
                updated_data = self.show_task_dialog(task_data)
                if updated_data:
                    self.update_task_data(row, task_key, updated_data)
                
        except Exception as e:
            print(f"Error handling cell double-click: {str(e)}")

    def add_note(self, row):
        """Add a note to the selected task"""
        try:
            task_key = self.task_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            if not task_key:
                return
            
            current_item = self.task_table.item(row, 0)
            if not current_item:
                return
            
            current_text = current_item.text().replace('+ Add Note', '').strip()
            task_name = current_text.split('\n')[0]
            
            # Create small popup dialog
            dialog = QDialog(self)
            dialog.setWindowTitle("Add Note")
            dialog.setFixedWidth(300)
            layout = QVBoxLayout(dialog)
            
            # Note input
            note_input = QLineEdit()
            note_input.setPlaceholderText("Enter note (max 100 characters)")
            note_input.setMaxLength(100)
            layout.addWidget(note_input)
            
            # Buttons
            button_layout = QHBoxLayout()
            add_btn = ModernButton("Add", color="#4a90e2")
            cancel_btn = ModernButton("Cancel", color="#6c757d")
            
            button_layout.addWidget(cancel_btn)
            button_layout.addWidget(add_btn)
            layout.addLayout(button_layout)
            
            add_btn.clicked.connect(dialog.accept)
            cancel_btn.clicked.connect(dialog.reject)
            
            if dialog.exec() == QDialog.DialogCode.Accepted:
                note_text = note_input.text().strip()
                if note_text:
                    # Get existing notes
                    notes = [line for line in current_text.split('\n')[1:] 
                            if line and line != '+ Add Note']
                    notes.append(f"• {note_text}")
                    
                    # Update in Firebase
                    session = self.app.session_manager.load_session()
                    if session and session.get('idToken'):
                        db.child('tasks').child(self.user_id).child(task_key).update({
                            'notes': '\n'.join(notes),
                            'updated_at': datetime.now().isoformat()
                        }, token=session['idToken'])
                        
                        # Update UI
                        new_text = task_name + '\n' + '\n'.join(notes)
                        current_item.setText(new_text)
                        self.task_table.resizeRowToContents(row)
                        
        except Exception as e:
            print(f"Error adding note: {str(e)}")
            show_error(self, "Error", "Failed to add note")

    def load_task_to_table(self, table, task_data, row):
        """Load task data into table"""
        try:
            # Get task name and notes
            task_name = task_data.get('task_name', '')
            notes = task_data.get('notes', '')
            
            # Create items
            name_item = QTableWidgetItem()
            date_item = QTableWidgetItem(task_data.get('due_date', 'N/A'))
            priority_item = QTableWidgetItem(task_data.get('priority', 'Low'))
            
            # Build display text
            if table == self.completed_table:
                # For completed tasks - apply strikethrough to everything
                font = QFont()
                font.setStrikeOut(True)
                
                # Format task name and notes with strikethrough
                display_text = task_name
                if notes:
                    notes_list = [note.strip() for note in notes.split('\n') if note.strip()]
                    if notes_list:
                        display_text += '\n' + '\n'.join(f"• {note}" for note in notes_list)
                
                # Apply strikethrough font to all items
                name_item.setFont(font)
                date_item.setFont(font)
                priority_item.setFont(font)
                
                # Set gray color for completed items
                gray_color = QColor("#6c757d")
                name_item.setForeground(gray_color)
                date_item.setForeground(gray_color)
                priority_item.setForeground(gray_color)
                
            else:
                # For active tasks
                display_text = task_name
                if notes:
                    notes_list = [note.strip() for note in notes.split('\n') if note.strip()]
                    if notes_list:
                        display_text += '\n' + '\n'.join(f"• {note}" for note in notes_list)
                
                # Make task name bold for active tasks
                font = QFont()
                font.setBold(True)
                name_item.setFont(font)
            
            # Set the text
            name_item.setText(display_text)
            
            # Store task key
            name_item.setData(Qt.ItemDataRole.UserRole, task_data.get('key'))
            
            # Make task name non-editable
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            
            # Set items in table
            table.setItem(row, 0, name_item)
            table.setItem(row, 1, date_item)
            table.setItem(row, 2, priority_item)
            
            # Adjust row height
            table.resizeRowToContents(row)
            
        except Exception as e:
            print(f"Error loading task to table: {str(e)}")

    def add_task(self):
        """Add a new task"""
        try:
            task_data = self.show_task_dialog()
            if task_data:
                session = self.app.session_manager.load_session()
                if not session or not session.get('idToken'):
                    show_error(self, "Error", "Please log in to add tasks")
                    return
                    
                # Ensure all required fields are present for Firebase validation
                task_data.update({
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat(),
                    'user_id': self.user_id,
                    'completed': False
                })
                
                try:
                    # Save to Firebase
                    task_ref = db.child('tasks').child(self.user_id).push(
                        task_data,
                        token=session['idToken']
                    )
                    
                    if task_ref and task_ref.get('name'):
                        task_data['key'] = task_ref['name']
                        row = self.task_table.rowCount()
                        self.task_table.insertRow(row)
                        self.load_task_to_table(self.task_table, task_data, row)
                        self.sort_tasks_by_priority()
                        show_success(self, "Success", "Task added! 🎯")
                    else:
                        show_error(self, "Error", "Failed to save task")
                        
                except Exception as firebase_error:
                    if "401" in str(firebase_error) or "Permission denied" in str(firebase_error):
                        show_error(self, "Error", "Session expired. Please log in again.")
                        self.app.switch_to_login()
                    else:
                        raise firebase_error
                    
        except Exception as e:
            print(f"Error adding task: {str(e)}")
            show_error(self, "Error", "Failed to add task")

    def sanitize_input(self, text):
        """Sanitize user input"""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Escape special characters
        text = html.escape(text)
        # Limit length
        return text[:200]  # Limit to 200 characters

    def sort_tasks_by_priority(self):
        """Sort tasks by priority"""
        try:
            rows = self.task_table.rowCount()
            tasks = []
            
            # Collect all tasks
            for row in range(rows):
                task_name = self.task_table.item(row, 0).text()
                due_date = self.task_table.item(row, 1).text()
                priority = self.task_table.item(row, 2).text()
                task_key = self.task_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
                priority_value = PriorityLevel.get_priority_value(priority)
                
                tasks.append({
                    'row': row,
                    'task_name': task_name,
                    'due_date': due_date,
                    'priority': priority,
                    'priority_value': priority_value,
                    'key': task_key
                })
            
            # Sort by priority value
            tasks.sort(key=lambda x: x['priority_value'])
            
            # Reorder table
            for new_row, task in enumerate(tasks):
                old_row = task['row']
                if new_row != old_row:
                    self.task_table.insertRow(new_row)
                    for col in range(self.task_table.columnCount()):
                        self.task_table.setItem(
                            new_row, 
                            col, 
                            self.task_table.takeItem(old_row + (1 if old_row > new_row else 0), col))
                    self.task_table.removeRow(old_row + (1 if old_row > new_row else 0))
            
        except Exception as e:
            print(f"Error sorting tasks: {str(e)}")

    def update_task(self):
        """Update the selected task"""
        try:
            # Get selected row
            current_row = self.task_table.currentRow()
            if current_row < 0:
                show_error(self, "Error", "Please select a task to update")
                return
            
            # Get task data
            task_key = self.task_table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
            current_name = self.task_table.item(current_row, 0).text().split('\n')[0]  # Get just the task name
            current_date = self.task_table.item(current_row, 1).text()
            current_priority = self.task_table.item(current_row, 2).text()
            
            # Get new task name
            task_name, ok = QInputDialog.getText(
                self, 'Update Task', 'Enter new task name:',
                QLineEdit.EchoMode.Normal, current_name
            )
            
            if ok and task_name.strip():
                # Get new due date
                date_dialog = DatePickerDialog(self)
                current_qdate = QDate.fromString(current_date, "yyyy-MM-dd")
                if current_qdate.isValid():
                    date_dialog.calendar.setSelectedDate(current_qdate)
                
                if date_dialog.exec() == QDialog.DialogCode.Accepted:
                    due_date = date_dialog.calendar.selectedDate().toString("yyyy-MM-dd")
                    
                    # Get new priority
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
                    index = priority_combo.findText(current_priority)
                    if index >= 0:
                        priority_combo.setCurrentIndex(index)
                    
                    layout.addWidget(priority_combo)
                    
                    update_button = ModernButton("Update")
                    update_button.clicked.connect(priority_dialog.accept)
                    layout.addWidget(update_button)
                    
                    if priority_dialog.exec() == QDialog.DialogCode.Accepted:
                        priority = priority_combo.currentText()
                        
                        # Get current notes
                        current_text = self.task_table.item(current_row, 0).text()
                        notes = '\n'.join(line for line in current_text.split('\n')[1:] 
                                        if line and line != '+ Add Note')
                        
                        # Create updated task data
                        task_data = {
                            'task_name': self.sanitize_input(task_name),
                            'due_date': due_date,
                            'priority': priority,
                            'priority_value': PriorityLevel.get_priority_value(priority),
                            'notes': notes,
                            'updated_at': datetime.now().isoformat()
                        }
                        
                        # Update in Firebase
                        session = self.app.session_manager.load_session()
                        if not session or not session.get('idToken'):
                            show_error(self, "Error", "Please log in to update tasks")
                            return
                        
                        db.child('tasks').child(self.user_id).child(task_key).update(
                            task_data,
                            token=session['idToken']
                        )
                        
                        # Update UI
                        task_data['key'] = task_key
                        self.load_task_to_table(self.task_table, task_data, current_row)
                        
                        # Sort tasks
                        self.sort_tasks_by_priority()
                        show_success(self, "Success", "Task updated! 🎯")
                    
        except Exception as e:
            print(f"Error updating task: {str(e)}")
            show_error(self, "Error", "Failed to update task")

    def toggle_task_completion(self):
        """Toggle task completion status"""
        try:
            # Get selected row
            current_row = self.task_table.currentRow()
            if current_row < 0:
                show_error(self, "Error", "Please select a task to toggle")
                return
            
            # Get task data
            task_key = self.task_table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
            task_name = self.task_table.item(current_row, 0).text().split('\n')[0]  # Get just the task name
            due_date = self.task_table.item(current_row, 1).text()
            priority = self.task_table.item(current_row, 2).text()
            
            # Get notes if any
            current_text = self.task_table.item(current_row, 0).text()
            notes = '\n'.join(line for line in current_text.split('\n')[1:] 
                             if line and line != '+ Add Note')
            
            # Create task data
            task_data = {
                'task_name': task_name,
                'due_date': due_date,
                'priority': priority,
                'priority_value': PriorityLevel.get_priority_value(priority),
                'completed': True,  # Mark as completed
                'notes': notes,
                'updated_at': datetime.now().isoformat()
            }
            
            # Update in Firebase
            session = self.app.session_manager.load_session()
            if not session or not session.get('idToken'):
                show_error(self, "Error", "Please log in to update tasks")
                return
            
            db.child('tasks').child(self.user_id).child(task_key).update(
                task_data,
                token=session['idToken']
            )
            
            # Move task to completed table
            task_data['key'] = task_key
            new_row = self.completed_table.rowCount()
            self.completed_table.insertRow(new_row)
            self.load_task_to_table(self.completed_table, task_data, new_row)
            
            # Remove from active tasks
            self.task_table.removeRow(current_row)
            
            # Show success message
            show_success(self, "Success", "Task completed! 🎉")
            
            # Update empty states if needed
            if self.task_table.rowCount() == 0:
                self.show_empty_state(self.task_table, "No active tasks")
            
        except Exception as e:
            print(f"Error toggling task completion: {str(e)}")
            show_error(self, "Error", "Failed to update task status")

    def show_empty_state(self, table, message="No tasks"):
        """Show empty state message in table"""
        table.setRowCount(1)
        empty_item = QTableWidgetItem(message)
        empty_item.setFlags(Qt.ItemFlag.NoItemFlags)  # Make it non-editable
        empty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Apply styling
        font = QFont()
        font.setItalic(True)
        empty_item.setFont(font)
        empty_item.setForeground(QColor("#6c757d"))  # Gray color
        
        table.setItem(0, 0, empty_item)
        table.setSpan(0, 0, 1, table.columnCount())  # Merge all columns

    def logout(self):
        """Handle user logout"""
        try:
            # Confirm logout
            response = show_question(self, "Logout", "Are you sure you want to logout?")
            if response == "Yes":
                print("Switching to login and clearing session...")
                
                # Clear user ID
                self.set_user_id(None)
                
                # Clear tables
                self.task_table.setRowCount(0)
                self.completed_table.setRowCount(0)
                self.show_empty_state(self.task_table, "Please log in to view tasks")
                self.show_empty_state(self.completed_table, "Please log in to view tasks")
                
                # Clear Firebase token
                token_manager.clear()
                
                # Clear session
                self.app.session_manager.clear_session()
                
                # Switch to login window
                self.app.switch_to_login()
                
        except Exception as e:
            print(f"Error during logout: {str(e)}")
            show_error(self, "Error", "Failed to logout properly")

    def show_account(self):
        """Show account management window"""
        try:
            from ui.account_ui import AccountManager
            
            # Check if user is logged in
            session = self.app.session_manager.load_session()
            if not session or not session.get('idToken'):
                show_error(self, "Error", "Please log in to access account settings")
                return
            
            # Create and show account manager
            account_manager = AccountManager(self.app, self)
            account_manager.show()
            
        except Exception as e:
            print(f"Error showing account window: {str(e)}")
            show_error(self, "Error", "Failed to open account settings")

    def show_task_dialog(self, task_data=None):
        """Show dialog for adding/updating task with notes"""
        try:
            is_update = task_data is not None
            dialog = QDialog(self)
            dialog.setWindowTitle("Update Task" if is_update else "Add New Task")
            dialog.setFixedWidth(400)
            layout = QVBoxLayout(dialog)
            
            # Task name section
            name_label = QLabel("Task Name:")
            name_input = QLineEdit()
            if is_update:
                name_input.setText(task_data.get('task_name', ''))
            layout.addWidget(name_label)
            layout.addWidget(name_input)
            
            # Due date
            date_label = QLabel("Due Date:")
            calendar = QCalendarWidget()
            if is_update:
                current_date = QDate.fromString(task_data.get('due_date', ''), "yyyy-MM-dd")
                if current_date.isValid():
                    calendar.setSelectedDate(current_date)
            layout.addWidget(date_label)
            layout.addWidget(calendar)
            
            # Priority
            priority_label = QLabel("Priority:")
            priority_combo = QComboBox()
            priority_combo.addItems([
                PriorityLevel.URGENT,
                PriorityLevel.HIGH,
                PriorityLevel.MEDIUM,
                PriorityLevel.LOW
            ])
            if is_update:
                index = priority_combo.findText(task_data.get('priority', ''))
                if index >= 0:
                    priority_combo.setCurrentIndex(index)
            layout.addWidget(priority_label)
            layout.addWidget(priority_combo)
            
            # Notes section
            notes_label = QLabel("Notes:")
            layout.addWidget(notes_label)
            
            notes_layout = QVBoxLayout()
            note_inputs = []
            
            def add_note_input(text=''):
                note_container = QWidget()
                note_layout = QHBoxLayout(note_container)
                note_layout.setContentsMargins(0, 0, 0, 0)
                
                note_input = QLineEdit()
                note_input.setPlaceholderText("Add a note (max 100 characters)")
                note_input.setMaxLength(100)
                note_input.setText(text)
                
                remove_btn = ModernButton("×", color="#dc3545")
                remove_btn.setFixedSize(30, 30)
                
                note_layout.addWidget(note_input)
                note_layout.addWidget(remove_btn)
                
                notes_layout.addWidget(note_container)
                note_inputs.append((note_container, note_input))
                
                remove_btn.clicked.connect(lambda: remove_note_input(note_container))
            
            def remove_note_input(container):
                container.deleteLater()
                for i, (cont, _) in enumerate(note_inputs):
                    if cont == container:
                        note_inputs.pop(i)
                        break
            
            # Add existing notes
            if is_update and task_data.get('notes'):
                for note in task_data.get('notes').split('\n'):
                    if note.strip():
                        add_note_input(note.strip())
            
            if not note_inputs:
                add_note_input()
            
            layout.addLayout(notes_layout)
            
            # Add note button
            add_note_btn = ModernButton("+ Add Another Note", color="#28a745")
            add_note_btn.clicked.connect(lambda: add_note_input())
            layout.addWidget(add_note_btn)
            
            # Buttons layout
            button_layout = QHBoxLayout()
            
            # Add delete button for existing tasks
            if is_update:
                delete_btn = ModernButton("Delete Task", color="#dc3545")
                delete_btn.clicked.connect(lambda: self.delete_task(task_data.get('key'), dialog))
                button_layout.addWidget(delete_btn)
            
            cancel_btn = ModernButton("Cancel", color="#6c757d")
            save_btn = ModernButton("Update" if is_update else "Add Task", color="#4a90e2")
            
            button_layout.addWidget(cancel_btn)
            button_layout.addWidget(save_btn)
            layout.addLayout(button_layout)
            
            cancel_btn.clicked.connect(dialog.reject)
            save_btn.clicked.connect(dialog.accept)
            
            if dialog.exec() == QDialog.DialogCode.Accepted:
                task_name = name_input.text().strip()
                if task_name:
                    notes = [input.text().strip() for _, input in note_inputs if input.text().strip()]
                    
                    return {
                        'task_name': self.sanitize_input(task_name),
                        'due_date': calendar.selectedDate().toString("yyyy-MM-dd"),
                        'priority': priority_combo.currentText(),
                        'priority_value': PriorityLevel.get_priority_value(priority_combo.currentText()),
                        'notes': '\n'.join(notes),
                        'completed': False,
                        'updated_at': datetime.now().isoformat(),
                        'created_at': task_data.get('created_at', datetime.now().isoformat()) if is_update else datetime.now().isoformat()
                    }
            return None
            
        except Exception as e:
            print(f"Error in task dialog: {str(e)}")
            show_error(self, "Error", "Failed to process task dialog")
            return None

    def delete_task(self, task_key, dialog=None):
        """Delete a task"""
        try:
            response = show_question(self, "Delete Task", "Are you sure you want to delete this task?")
            if response == "Yes":
                session = self.app.session_manager.load_session()
                if not session or not session.get('idToken'):
                    show_error(self, "Error", "Please log in to delete tasks")
                    return
                
                # Delete from Firebase
                db.child('tasks').child(self.user_id).child(task_key).remove(token=session['idToken'])
                
                # Reload tasks
                self.load_initial_tasks()
                
                show_success(self, "Success", "Task deleted successfully")
                
                # Close the dialog if it exists
                if dialog:
                    dialog.reject()
                
        except Exception as e:
            print(f"Error deleting task: {str(e)}")
            show_error(self, "Error", "Failed to delete task")

    def update_task_data(self, row, task_key, updated_data):
        """Update task data in Firebase and UI"""
        try:
            # Get session
            session = self.app.session_manager.load_session()
            if not session or not session.get('idToken'):
                show_error(self, "Error", "Please log in to update tasks")
                return

            # Ensure required fields are present for Firebase validation
            updated_data.update({
                'updated_at': datetime.now().isoformat(),
                'user_id': self.user_id,
                # Preserve existing fields
                'created_at': self.get_task_created_at(task_key) or datetime.now().isoformat(),
                'task_name': updated_data.get('task_name') or self.task_table.item(row, 0).text().split('\n')[0]
            })

            try:
                # Update in Firebase
                db.child('tasks').child(self.user_id).child(task_key).update(
                    updated_data,
                    token=session['idToken']
                )
                
                # Update UI
                updated_data['key'] = task_key
                self.load_task_to_table(self.task_table, updated_data, row)
                
                # Sort if priority changed
                current_priority = self.task_table.item(row, 2).text()
                if current_priority != updated_data.get('priority'):
                    self.sort_tasks_by_priority()
                
                show_success(self, "Success", "Task updated! 🎯")
                
            except Exception as firebase_error:
                if "401" in str(firebase_error) or "Permission denied" in str(firebase_error):
                    show_error(self, "Error", "Session expired. Please log in again.")
                    self.app.switch_to_login()
                else:
                    raise firebase_error
                
        except Exception as e:
            print(f"Error updating task data: {str(e)}")
            show_error(self, "Error", "Failed to update task")

    def get_task_created_at(self, task_key):
        """Get the created_at timestamp for an existing task"""
        try:
            session = self.app.session_manager.load_session()
            if session and session.get('idToken'):
                task = db.child('tasks').child(self.user_id).child(task_key).get(token=session['idToken'])
                if task and task.val():
                    return task.val().get('created_at')
        except:
            pass
        return None

    def clear_all_completed_tasks(self):
        """Delete all completed tasks"""
        try:
            # Confirm deletion
            response = show_question(self, "Clear All", "Are you sure you want to delete all completed tasks?")
            if response != "Yes":
                return
                
            session = self.app.session_manager.load_session()
            if not session or not session.get('idToken'):
                show_error(self, "Error", "Please log in to delete tasks")
                return
                
            # Get all completed tasks
            tasks = db.child('tasks').child(self.user_id).get(token=session['idToken'])
            if tasks:
                for task in tasks.each() or []:
                    task_data = task.val()
                    if task_data and task_data.get('completed'):
                        # Delete the task
                        db.child('tasks').child(self.user_id).child(task.key()).remove(
                            token=session['idToken']
                        )
                
            # Clear the completed table
            self.completed_table.setRowCount(0)
            self.show_empty_state(self.completed_table, "No completed tasks")
            show_success(self, "Success", "All completed tasks deleted! 🗑️")
            
        except Exception as e:
            print(f"Error clearing completed tasks: {str(e)}")
            show_error(self, "Error", "Failed to clear completed tasks")

    def delete_selected_completed_tasks(self):
        """Delete selected completed tasks"""
        try:
            # Get selected rows
            selected_rows = set(item.row() for item in self.completed_table.selectedItems())
            if not selected_rows:
                show_error(self, "Error", "Please select tasks to delete")
                return
                
            # Confirm deletion
            response = show_question(self, "Delete Selected", 
                                  f"Are you sure you want to delete {len(selected_rows)} selected task(s)?")
            if response != "Yes":
                return
                
            session = self.app.session_manager.load_session()
            if not session or not session.get('idToken'):
                show_error(self, "Error", "Please log in to delete tasks")
                return
                
            # Delete tasks from Firebase and table
            for row in sorted(selected_rows, reverse=True):
                task_key = self.completed_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
                if task_key:
                    # Delete from Firebase
                    db.child('tasks').child(self.user_id).child(task_key).remove(
                        token=session['idToken']
                    )
                    # Remove from table
                    self.completed_table.removeRow(row)
                    
            # Show empty state if no tasks left
            if self.completed_table.rowCount() == 0:
                self.show_empty_state(self.completed_table, "No completed tasks")
                
            show_success(self, "Success", "Selected tasks deleted! 🗑️")
            
        except Exception as e:
            print(f"Error deleting selected tasks: {str(e)}")
            show_error(self, "Error", "Failed to delete selected tasks")

# Add this new class for modern table styling
class ModernTable(QTableWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QTableWidget {
                background-color: #f5f7fa;
                border: 1px solid #e1e8ed;
                border-radius: 8px;
                gridline-color: #e1e8ed;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #e1e8ed;
                color: #2c3e50;
                font-size: 13px;
            }
            QTableWidget::item:selected {
                background-color: #edf2f7;
                color: #2c3e50;
            }
            QTableWidget::item:hover {
                background-color: #edf2f7;
            }
            QTableWidget QHeaderView::section {
                background-color: #f8f9fa;
                color: #2c3e50;
                padding: 10px;
                border: none;
                border-bottom: 2px solid #e1e8ed;
                font-weight: bold;
                font-size: 13px;
            }
            QTableWidget QHeaderView::section:hover {
                background-color: #edf2f7;
            }
        """)
        
        self.setAlternatingRowColors(False)  # Disable alternating colors
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(True)
        self.setWordWrap(True)

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
