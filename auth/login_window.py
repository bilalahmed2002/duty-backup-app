"""Login window GUI matching frontend design."""

from __future__ import annotations

import logging
from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QMessageBox,
)

# Import styles - use importlib to import from app's utils explicitly
import sys
import importlib.util
from pathlib import Path
_app_dir = Path(__file__).parent.parent.resolve()
# Import styles.py directly without going through package system
styles_path = _app_dir / "utils" / "styles.py"
spec = importlib.util.spec_from_file_location("duty_backup_styles", styles_path)
styles_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(styles_module)
DARK_THEME_STYLESHEET = styles_module.DARK_THEME_STYLESHEET

logger = logging.getLogger(__name__)


class LoginWindow(QDialog):
    """Login window with dark theme matching frontend design."""

    # Signal emitted when login is successful
    login_successful = pyqtSignal(dict)  # Emits auth_data

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize login window."""
        super().__init__(parent)
        self.setWindowTitle("FTE Operations - Login")
        self.setFixedSize(450, 500)
        self.setStyleSheet(DARK_THEME_STYLESHEET)
        
        self._setup_ui()
        self._error_message: Optional[str] = None

    def _setup_ui(self) -> None:
        """Setup the UI components."""
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(40, 40, 40, 40)
        
        # Card container (glassmorphism effect)
        card = QWidget()
        card.setObjectName("card")
        card.setStyleSheet("""
            QWidget#card {
                background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 16px;
                padding: 30px;
            }
        """)
        card_layout = QVBoxLayout()
        card_layout.setSpacing(24)
        card.setLayout(card_layout)
        
        # Title
        title = QLabel("Welcome Back")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title.setFont(title_font)
        card_layout.addWidget(title)
        
        # Description
        description = QLabel("Sign in to your FTE OPERATIONS account")
        description.setObjectName("description")
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(description)
        
        # Email input
        email_layout = QVBoxLayout()
        email_layout.setSpacing(8)
        email_label = QLabel("Email")
        email_label.setStyleSheet("color: #ffffff; font-size: 14px;")
        email_layout.addWidget(email_label)
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter your email")
        self.email_input.setStyleSheet("""
            QLineEdit {
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 10px 12px;
                color: #ffffff;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid rgba(245, 158, 11, 0.5);
                background-color: rgba(255, 255, 255, 0.15);
            }
            QLineEdit::placeholder {
                color: rgba(255, 255, 255, 0.4);
            }
        """)
        email_layout.addWidget(self.email_input)
        card_layout.addLayout(email_layout)
        
        # Password input
        password_layout = QVBoxLayout()
        password_layout.setSpacing(8)
        password_label = QLabel("Password")
        password_label.setStyleSheet("color: #ffffff; font-size: 14px;")
        password_layout.addWidget(password_label)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet("""
            QLineEdit {
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 10px 12px;
                color: #ffffff;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid rgba(245, 158, 11, 0.5);
                background-color: rgba(255, 255, 255, 0.15);
            }
            QLineEdit::placeholder {
                color: rgba(255, 255, 255, 0.4);
            }
        """)
        password_layout.addWidget(self.password_input)
        card_layout.addLayout(password_layout)
        
        # Error message label
        self.error_label = QLabel()
        self.error_label.setObjectName("error")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setWordWrap(True)
        self.error_label.setStyleSheet("color: #ef4444; font-size: 12px;")
        self.error_label.hide()
        card_layout.addWidget(self.error_label)
        
        # Login button
        self.login_button = QPushButton("Sign In")
        self.login_button.setStyleSheet("""
            QPushButton {
                background-color: #f59e0b;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #fbbf24;
            }
            QPushButton:pressed {
                background-color: #d97706;
            }
            QPushButton:disabled {
                background-color: rgba(245, 158, 11, 0.5);
                color: rgba(255, 255, 255, 0.5);
            }
        """)
        self.login_button.clicked.connect(self._on_login_clicked)
        card_layout.addWidget(self.login_button)
        
        # Connect Enter key to login
        self.password_input.returnPressed.connect(self._on_login_clicked)
        
        card_layout.addStretch()
        main_layout.addWidget(card)
        main_layout.addStretch()
        
        self.setLayout(main_layout)
        
        # Set background
        self.setStyleSheet("""
            QDialog {
                background-color: #0f172a;
            }
        """)
        
        # Initialize login request tracking
        self.login_requested = False
        self.login_email = ""
        self.login_password = ""

    def _on_login_clicked(self) -> None:
        """Handle login button click."""
        email = self.email_input.text().strip()
        password = self.password_input.text()
        
        if not email:
            self._show_error("Please enter your email address")
            return
        
        if not password:
            self._show_error("Please enter your password")
            return
        
        # Disable button during login
        self.login_button.setEnabled(False)
        self.login_button.setText("Signing in...")
        self._hide_error()
        
        # Emit signal for parent to handle authentication
        # The parent will call set_login_result when done
        self.login_requested = True
        self.login_email = email
        self.login_password = password

    def set_login_result(self, success: bool, auth_data: Optional[dict] = None, error_message: Optional[str] = None) -> None:
        """Set login result from authentication service.

        Args:
            success: Whether login was successful
            auth_data: Authentication data if successful
            error_message: Error message if failed
        """
        self.login_button.setEnabled(True)
        self.login_button.setText("Sign In")
        
        if success and auth_data:
            self.login_successful.emit(auth_data)
        else:
            self._show_error(error_message or "Login failed. Please check your credentials and try again.")

    def _show_error(self, message: str) -> None:
        """Show error message."""
        self.error_label.setText(message)
        self.error_label.show()

    def _hide_error(self) -> None:
        """Hide error message."""
        self.error_label.hide()

    def clear_inputs(self) -> None:
        """Clear input fields."""
        self.email_input.clear()
        self.password_input.clear()
        self._hide_error()

