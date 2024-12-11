from todolist import ToDoListApp
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
import os

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def main():
    # Create QApplication first
    app = QApplication(sys.argv)
    
    # Set application name and icon
    app.setApplicationName("TaskMaster Pro")
    
    # Set icon using resource path
    icon_path = get_resource_path("todolist.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    else:
        print(f"Icon not found at: {icon_path}")
    
    # Continue with normal startup
    todo_app = ToDoListApp(sys.argv)
    return app.exec()

if __name__ == "__main__":
    sys.exit(main()) 