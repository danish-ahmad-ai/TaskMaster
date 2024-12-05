from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QWidget, QGraphicsDropShadowEffect, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from ui.modern_widgets import ModernButton

class ModernDialog(QDialog):
    def __init__(self, title, message, icon="ℹ️", buttons=["OK"], parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setup_ui(title, message, icon, buttons)
        
        # Center the dialog relative to parent
        if parent:
            parent_center = parent.mapToGlobal(parent.rect().center())
            self.move(parent_center.x() - self.width() // 2,
                     parent_center.y() - self.height() // 2)

    def setup_ui(self, title, message, icon, buttons):
        # Main layout with margins
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Create main container
        container = QWidget()
        container.setObjectName("container")
        container.setStyleSheet("""
            QWidget#container {
                background-color: white;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 2)
        container.setGraphicsEffect(shadow)
        
        # Container layout
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(15)
        
        # Title section with icon
        title_layout = QHBoxLayout()
        title_layout.setSpacing(10)
        
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Arial", 18))
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #2c3e50;")
        
        title_layout.addWidget(icon_label)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        # Message
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                font-size: 12px;
            }
        """)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.addStretch()
        
        self.button_results = {}
        
        for button_text in buttons:
            if button_text in ["OK", "Yes"]:
                btn = ModernButton(button_text, color="#4a90e2")
            elif button_text == "No":
                btn = ModernButton(button_text, color="#6c757d")
            elif button_text == "Cancel":
                btn = ModernButton(button_text, color="#dc3545")
            else:
                btn = ModernButton(button_text)
                
            btn.clicked.connect(lambda checked, text=button_text: self.handle_button(text))
            button_layout.addWidget(btn)
        
        # Add all sections to container
        container_layout.addLayout(title_layout)
        container_layout.addWidget(message_label)
        container_layout.addLayout(button_layout)
        
        # Add container to main layout
        layout.addWidget(container)
        
        # Set fixed size with smaller height
        self.setFixedSize(400, 180)
        
    def handle_button(self, button_text):
        self.button_clicked = button_text
        self.accept()

def show_message(parent, title, message, icon="ℹ️", buttons=["OK"]):
    dialog = ModernDialog(title, message, icon, buttons, parent)
    dialog.exec()
    return dialog.button_clicked

def show_error(parent, title, message):
    return show_message(parent, title, message, icon="⚠️")

def show_success(parent, title, message):
    return show_message(parent, title, message, icon="✅")

def show_question(parent, title, message):
    return show_message(parent, title, message, icon="❓", buttons=["Yes", "No"]) 