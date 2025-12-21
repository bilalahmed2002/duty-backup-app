"""Main GUI window with tabs for Process, Results, and Settings."""

from __future__ import annotations

import logging
from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QMainWindow,
    QTabWidget,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QMenuBar,
    QMenu,
)

# Import styles - use importlib to import from app's utils explicitly
import sys
import importlib.util
from pathlib import Path
_app_dir = Path(__file__).parent.parent.resolve()
styles_path = _app_dir / "utils" / "styles.py"
spec = importlib.util.spec_from_file_location("duty_backup_styles", styles_path)
styles_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(styles_module)
DARK_THEME_STYLESHEET = styles_module.DARK_THEME_STYLESHEET

from gui.duty_runner import DutyRunnerWidget
from gui.results_viewer import ResultsViewerWidget
from gui.search_tab import SearchTabWidget

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main application window."""

    # Signal emitted when user wants to logout
    logout_requested = pyqtSignal()

    def __init__(self, duty_service, user_data: dict, parent: Optional[QWidget] = None) -> None:
        """Initialize main window.

        Args:
            duty_service: StandaloneDutyService instance
            user_data: User data from authentication
            parent: Parent widget
        """
        super().__init__(parent)
        self.duty_service = duty_service
        self.user_data = user_data
        
        self.setWindowTitle("FTE Operations - Duty Service")
        self.setMinimumSize(1200, 800)
        self.setStyleSheet(DARK_THEME_STYLESHEET)
        
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the UI components."""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        central_widget.setLayout(main_layout)
        
        # Header bar
        header = self._create_header()
        main_layout.addWidget(header)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid rgba(255, 255, 255, 0.1);
                background-color: rgba(255, 255, 255, 0.05);
                border-radius: 8px;
            }
            QTabBar::tab {
                background-color: rgba(255, 255, 255, 0.05);
                color: rgba(255, 255, 255, 0.7);
                border: none;
                padding: 12px 24px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-size: 14px;
            }
            QTabBar::tab:selected {
                background-color: rgba(255, 255, 255, 0.1);
                color: #f59e0b;
                font-weight: 600;
            }
            QTabBar::tab:hover {
                background-color: rgba(255, 255, 255, 0.08);
            }
        """)
        
        # Process tab
        self.process_tab = DutyRunnerWidget(self.duty_service)
        self.tab_widget.addTab(self.process_tab, "Process")
        
        # Results tab
        self.results_tab = ResultsViewerWidget(self.duty_service)
        self.tab_widget.addTab(self.results_tab, "Results")
        
        # Search tab
        search_tab = SearchTabWidget(self.duty_service)
        self.tab_widget.addTab(search_tab, "Search")
        
        # Wire up signal: when processing completes, update results tab
        self.process_tab.processing_complete.connect(self.results_tab.update_session_results)
        
        main_layout.addWidget(self.tab_widget)

    def _create_header(self) -> QWidget:
        """Create header bar with logo and user menu."""
        header = QWidget()
        header.setFixedHeight(60)
        header.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 0.05);
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)
        
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(20, 0, 20, 0)
        header_layout.setSpacing(20)
        
        # Logo/Title
        title = QLabel("FTE Operations")
        title.setStyleSheet("color: #f59e0b; font-size: 20px; font-weight: 700;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # User info
        user_email = self.user_data.get("email", "User")
        user_label = QLabel(user_email)
        user_label.setStyleSheet("color: rgba(255, 255, 255, 0.7); font-size: 14px;")
        header_layout.addWidget(user_label)
        
        # Logout button
        logout_btn = QPushButton("Logout")
        logout_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(239, 68, 68, 0.2);
                color: #ef4444;
                border: 1px solid rgba(239, 68, 68, 0.3);
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: rgba(239, 68, 68, 0.3);
            }
        """)
        logout_btn.clicked.connect(self._on_logout)
        header_layout.addWidget(logout_btn)
        
        header.setLayout(header_layout)
        return header

    def _on_logout(self) -> None:
        """Handle logout button click."""
        self.logout_requested.emit()

    def refresh_results(self) -> None:
        """Refresh results tab."""
        # Results tab is now managed via signals from Process tab
        pass


