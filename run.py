from todolist import ToDoListApp
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
import os
from pathlib import Path
import json

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def get_credentials_path():
    """Get path to secure credentials folder"""
    # You can set this as an environment variable
    secure_path = os.getenv('TASKMASTER_CREDENTIALS_PATH', 
                           r'C:\Users\E-TIME\PycharmProjects\LiteProjs\credentials')
    return Path(secure_path)

def load_firebase_config():
    
    """Load Firebase configuration"""
    try:
        # First try secure location
        config_path = get_credentials_path() / 'firebase_config.json'
        if config_path.exists():
            return config_path
            
        # Fallback to local config for production
        local_path = Path('firebase_config.json')
        if local_path.exists():
            return local_path
            
    except Exception as e:
        print(f"Error loading config: {e}")
        return None

def check_credentials():
    """Check all credential files before starting the app"""
    cred_path = Path(r'C:\Users\E-TIME\PycharmProjects\LiteProjs\credentials')
    required_files = ['firebase_config.json', 'serviceAccountKey.json', '.env']
    
    print("\nChecking credential files:")
    for file in required_files:
        file_path = cred_path / file
        if file_path.exists():
            print(f"✓ {file} exists ({file_path.stat().st_size} bytes)")
            
            # For JSON files, verify they can be parsed
            if file.endswith('.json'):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        json.load(f)
                    print(f"  ✓ Valid JSON format")
                except Exception as e:
                    print(f"  ✗ Invalid JSON: {e}")
        else:
            print(f"✗ {file} missing!")
    print()

def main():
    check_credentials()
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
    
    # Add debug logging
    credentials_path = Path(r'C:\Users\E-TIME\PycharmProjects\LiteProjs\credentials')
    print(f"Checking credentials at: {credentials_path}")
    print(f"Exists: {credentials_path.exists()}")
    if credentials_path.exists():
        print("Files in credentials directory:")
        for file in credentials_path.iterdir():
            print(f"  - {file.name}")
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main()) 