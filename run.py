from todolist import ToDoListApp
import sys
from PyQt6.QtWidgets import QApplication

def main():
    # Create QApplication first
    app = QApplication(sys.argv)
    
    # Continue with normal startup
    todo_app = ToDoListApp(sys.argv)
    return app.exec()

if __name__ == "__main__":
    sys.exit(main()) 