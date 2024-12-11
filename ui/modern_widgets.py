from PyQt6.QtWidgets import (
    QPushButton, QLineEdit, QGraphicsDropShadowEffect,
    QLabel, QWidget
)
from PyQt6.QtCore import QPropertyAnimation, QPoint, Qt, QSize
from PyQt6.QtGui import QColor, QPainter, QPen, QBrush

class ModernButton(QPushButton):
    def __init__(self, text, color="#4a90e2", parent=None):
        super().__init__(text, parent)
        self.default_style = f"""
            QPushButton {{
                padding: 8px 16px;
                border: none;
                border-radius: 6px;
                background-color: {color};
                color: white;
                font-size: 13px;
                font-weight: bold;
                min-width: 80px;
                position: relative;
                outline: none;
            }}
            QPushButton:hover {{
                background-color: {self._adjust_color(color, -20)};
                margin-top: -2px;
                margin-bottom: 2px;
            }}
            QPushButton:pressed {{
                background-color: {self._adjust_color(color, -40)};
                margin-top: 0px;
                margin-bottom: 0px;
            }}
            QPushButton:focus {{
                outline: none;
                border: none;
            }}
        """
        self.setStyleSheet(self.default_style)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
    def enterEvent(self, event):
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        super().leaveEvent(event)
        
    def _adjust_color(self, color, amount):
        # Helper function to darken/lighten color
        color = color.lstrip('#')
        rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        rgb = tuple(max(0, min(255, c + amount)) for c in rgb)
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

class ModernLineEdit(QLineEdit):
    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setFixedHeight(45)
        self.setMinimumWidth(300)
        
        # Create animations
        self.border_animation = QPropertyAnimation(self, b"styleSheet")
        self.border_animation.setDuration(150)
        
        # Common style properties
        self.common_style = """
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                background-color: #f5f5f5;
                font-size: 14px;
                color: #333333;
                selection-background-color: #4a90e2;
                selection-color: white;
            }
            QLineEdit:hover {
                background-color: #f5f5f5;
                border: 1px solid #d0d0d0;
            }
            QLineEdit:focus {
                background-color: #f5f5f5;
                border: 1px solid #d0d0d0;
            }
            QLineEdit::placeholder {
                color: #999999;
                font-size: 13px;
            }
        """
        
        self.setStyleSheet(self.common_style)
        
        # Add subtle shadow effect for depth
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(4)
        shadow.setColor(QColor(0, 0, 0, 10))
        shadow.setOffset(0, 1)
        self.setGraphicsEffect(shadow) 

class NotificationButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.unread_count = 0
        self.setFixedSize(40, 40)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                border: none;
                border-radius: 20px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
        """)
        
        # Create badge label
        self.badge = QLabel(self)
        self.badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.badge.setStyleSheet("""
            QLabel {
                color: white;
                background-color: #dc3545;
                border-radius: 10px;
                padding: 2px 5px;
                margin: 2px;
                font-size: 10px;
                font-weight: bold;
            }
        """)
        self.badge.hide()
        
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw bell icon
        painter.setPen(QPen(QColor("#495057")))
        
        # Simple bell shape
        width = self.width()
        height = self.height()
        bell_width = width * 0.5
        bell_height = height * 0.5
        
        x = (width - bell_width) / 2
        y = (height - bell_height) / 2
        
        # Draw bell body
        painter.drawEllipse(int(x), int(y), int(bell_width), int(bell_height * 0.7))
        painter.drawRect(int(x + bell_width * 0.35), int(y + bell_height * 0.7),
                        int(bell_width * 0.3), int(bell_height * 0.2))
        
    def set_notification_count(self, count):
        self.unread_count = count
        if count > 0:
            self.badge.setText(str(count if count <= 99 else "99+"))
            self.badge.adjustSize()
            self.badge.move(self.width() - self.badge.width(), 0)
            self.badge.show()
        else:
            self.badge.hide()
            
    def get_notification_count(self):
        return self.unread_count