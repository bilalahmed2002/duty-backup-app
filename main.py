"""Main entry point for duty backup application."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt

# Ensure app directory is in path for imports
import sys
from pathlib import Path

# Get app directory (handles both dev and PyInstaller bundle)
if getattr(sys, 'frozen', False):
    # PyInstaller bundle
    _app_dir = Path(sys.executable).parent.resolve()
else:
    # Development
    _app_dir = Path(__file__).parent.resolve()

if str(_app_dir) not in sys.path:
    sys.path.insert(0, str(_app_dir))

from auth.login_window import LoginWindow
from auth.auth_service import AuthService
from auth.session_manager import SessionManager
from service.config_manager import ConfigManager
from service.duty_service import StandaloneDutyService
from gui.main_window import MainWindow

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('duty_backup_app.log'),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)


class DutyBackupApp:
    """Main application class."""

    def __init__(self) -> None:
        """Initialize application."""
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("FTE Operations - Duty Service")
        self.app.setStyle("Fusion")  # Use Fusion style for better cross-platform appearance
        
        # Initialize managers
        self.config_manager = ConfigManager()
        self.session_manager = SessionManager()
        
        # Check configuration
        is_valid, missing = self.config_manager.validate_required()
        if not is_valid:
            self._show_config_error(missing)
            sys.exit(1)
        
        # Initialize auth service
        supabase_url = self.config_manager.supabase_url
        
        # For authentication, use ANON key (preferred) or service role key as fallback
        auth_key = self.config_manager.get("SUPABASE_ANON_KEY") or self.config_manager.supabase_service_role_key
        
        # For duty service (database queries), MUST use SERVICE_ROLE_KEY to bypass RLS
        # The service role key has full access to read brokers/formats
        duty_service_key = self.config_manager.supabase_service_role_key
        
        if not supabase_url:
            QMessageBox.critical(
                None,
                "Configuration Error",
                "Supabase URL not configured. Please check your .env file."
            )
            sys.exit(1)
        
        if not auth_key:
            QMessageBox.critical(
                None,
                "Configuration Error",
                "Supabase authentication key not configured.\n\n"
                "Required: SUPABASE_ANON_KEY (preferred) or SUPABASE_SERVICE_ROLE_KEY"
            )
            sys.exit(1)
        
        if not duty_service_key:
            QMessageBox.critical(
                None,
                "Configuration Error",
                "Supabase SERVICE_ROLE_KEY not configured.\n\n"
                "Required for database access: SUPABASE_SERVICE_ROLE_KEY"
            )
            sys.exit(1)
        
        self.auth_service = AuthService(supabase_url, auth_key)
        # Use SERVICE_ROLE_KEY for duty service to bypass RLS and access brokers/formats
        self.duty_service = StandaloneDutyService(supabase_url, duty_service_key)
        
        self.login_window = None
        self.main_window = None
        
        # Check for existing session
        session = self.session_manager.load_session()
        if session and self.session_manager.is_authenticated():
            # Auto-login with existing session
            self._show_main_window(session.get("user", {}))
        else:
            # Show login window
            self._show_login_window()

    def _show_config_error(self, missing_keys: list) -> None:
        """Show configuration error dialog."""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("Configuration Error")
        msg.setText("Missing required configuration:")
        msg.setDetailedText("\n".join(f"- {key}" for key in missing_keys))
        msg.setInformativeText("Please create a .env file with the required credentials.")
        msg.exec()

    def _show_login_window(self) -> None:
        """Show login window."""
        login_window = LoginWindow()
        login_window.login_successful.connect(self._on_login_successful)
        
        # Override login button to handle authentication
        def handle_login_click():
            email = login_window.email_input.text().strip()
            password = login_window.password_input.text()
            
            if not email:
                login_window.set_login_result(False, None, "Please enter your email address")
                return
            
            if not password:
                login_window.set_login_result(False, None, "Please enter your password")
                return
            
            # Disable button
            login_window.login_button.setEnabled(False)
            login_window.login_button.setText("Signing in...")
            login_window._hide_error()
            
            # Perform login
            try:
                success, auth_data, error = self.auth_service.login(email, password)
                login_window.set_login_result(success, auth_data, error)
            except Exception as exc:
                logger.error(f"Login error: {exc}", exc_info=True)
                login_window.set_login_result(False, None, f"Login failed: {exc}")
        
        # Replace button click handler
        login_window.login_button.clicked.disconnect(login_window._on_login_clicked)
        login_window.login_button.clicked.connect(handle_login_click)
        
        # Also handle Enter key
        def handle_enter():
            handle_login_click()
        login_window.password_input.returnPressed.disconnect()
        login_window.password_input.returnPressed.connect(handle_enter)
        
        login_window.show()
        # Store reference to login window
        self.login_window = login_window

    def _on_login_successful(self, auth_data: dict) -> None:
        """Handle successful login."""
        # Save session
        self.session_manager.save_session(auth_data)
        
        # Close login window
        if self.login_window is not None:
            self.login_window.close()
            self.login_window = None
        
        # Show main window
        self._show_main_window(auth_data.get("user", {}))

    def _show_main_window(self, user_data: dict) -> None:
        """Show main window."""
        if self.main_window is not None:
            self.main_window.close()
        self.main_window = MainWindow(self.duty_service, user_data)
        self.main_window.logout_requested.connect(self._on_logout)
        self.main_window.show()

    def _on_logout(self) -> None:
        """Handle logout."""
        # Clear session
        self.session_manager.clear_session()
        
        # Close main window
        if self.main_window is not None:
            self.main_window.close()
            self.main_window = None
        
        # Show login window again (will create new instance)
        self._show_login_window()


def main() -> None:
    """Main entry point."""
    try:
        app = DutyBackupApp()
        # Start event loop once for the entire application
        # (Windows are already shown in __init__)
        sys.exit(app.app.exec())
    except Exception as exc:
        logger.error(f"Application error: {exc}", exc_info=True)
        QMessageBox.critical(
            None,
            "Application Error",
            f"An error occurred: {exc}\n\nCheck duty_backup_app.log for details."
        )
        sys.exit(1)


if __name__ == "__main__":
    main()

