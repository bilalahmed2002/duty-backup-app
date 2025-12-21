"""Duty processing GUI widget."""

from __future__ import annotations

import logging
import json
from pathlib import Path
from typing import Optional, List, Dict
from uuid import UUID

from PyQt6.QtCore import Qt, pyqtSignal, QThread

# Debug logging
DEBUG_LOG_PATH = Path(__file__).parent.parent.parent / ".cursor" / "debug.log"
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QTextEdit,
    QCheckBox,
    QProgressBar,
    QGroupBox,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
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

# Import MAWB parser
mawb_parser_path = _app_dir / "utils" / "mawb_parser.py"
spec2 = importlib.util.spec_from_file_location("mawb_parser", mawb_parser_path)
mawb_parser_module = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(mawb_parser_module)
parse_mawb_input = mawb_parser_module.parse_mawb_input

logger = logging.getLogger(__name__)


class ProcessingThread(QThread):
    """Thread for running duty processing asynchronously."""
    
    progress = pyqtSignal(str, int)  # message, percentage
    log_message = pyqtSignal(str)
    finished = pyqtSignal(dict)  # result
    error = pyqtSignal(str)  # error message

    def __init__(self, duty_service, mawb: str, broker_id: UUID, format_id: UUID, sections: dict, airport_code: Optional[str] = None, customer: Optional[str] = None, checkbook_hawbs: Optional[str] = None):
        super().__init__()
        self.duty_service = duty_service
        self.mawb = mawb
        self.broker_id = broker_id
        self.format_id = format_id
        self.sections = sections
        self.airport_code = airport_code
        self.customer = customer
        self.checkbook_hawbs = checkbook_hawbs

    def run(self):
        """Run the processing."""
        import asyncio
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(
                self.duty_service.process_mawb(
                    self.mawb,
                    self.broker_id,
                    self.format_id,
                    self.sections,
                    on_progress=lambda msg, pct: self.progress.emit(msg, pct),
                    on_log=lambda msg: self.log_message.emit(msg),
                    airport_code=self.airport_code,
                    customer=self.customer,
                    checkbook_hawbs=self.checkbook_hawbs,
                )
            )
            # Add airport_code and customer to result for file naming
            if self.airport_code:
                result['airport_code'] = self.airport_code
            if self.customer:
                result['customer'] = self.customer
            self.finished.emit(result)
        except Exception as exc:
            self.error.emit(str(exc))
        finally:
            if 'loop' in locals():
                loop.close()


class DutyRunnerWidget(QWidget):
    """Widget for processing duty requests."""

    # Signal emitted when processing is complete with session results
    processing_complete = pyqtSignal(list)  # List of result dictionaries

    def __init__(self, duty_service, parent: Optional[QWidget] = None) -> None:
        """Initialize duty runner widget.

        Args:
            duty_service: StandaloneDutyService instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.duty_service = duty_service
        self.parsed_items: List[Dict] = []  # Store parsed items
        self.session_results: List[Dict] = []  # Store results from current session
        self.processing_threads: List[ProcessingThread] = []
        self.current_processing_index = 0
        
        self._setup_ui()
        # Load brokers and formats immediately
        self._load_brokers_and_formats()

    def _setup_ui(self) -> None:
        """Setup the UI components."""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("Process Duty Request")
        title.setStyleSheet("color: #ffffff; font-size: 24px; font-weight: 700; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Top row: Configuration and Sections side by side
        top_row = QHBoxLayout()
        top_row.setSpacing(15)
        
        # Configuration group
        config_group = QGroupBox("Configuration")
        config_group.setStyleSheet("""
            QGroupBox {
                background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                padding: 15px;
                margin-top: 10px;
            }
            QGroupBox::title {
                color: #f59e0b;
                font-size: 14px;
                font-weight: 600;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        config_layout = QVBoxLayout()
        config_layout.setSpacing(12)
        config_layout.setContentsMargins(5, 5, 5, 5)
        
        # Broker selection
        broker_layout = QHBoxLayout()
        broker_layout.setSpacing(10)
        broker_label = QLabel("Broker:")
        broker_label.setStyleSheet("color: #ffffff; font-size: 13px; min-width: 70px;")
        broker_layout.addWidget(broker_label)
        self.broker_combo = QComboBox()
        self.broker_combo.setStyleSheet(DARK_THEME_STYLESHEET)
        self.broker_combo.setMinimumHeight(32)
        broker_layout.addWidget(self.broker_combo)
        config_layout.addLayout(broker_layout)
        
        # Format selection
        format_layout = QHBoxLayout()
        format_layout.setSpacing(10)
        format_label = QLabel("Format:")
        format_label.setStyleSheet("color: #ffffff; font-size: 13px; min-width: 70px;")
        format_layout.addWidget(format_label)
        self.format_combo = QComboBox()
        self.format_combo.setStyleSheet(DARK_THEME_STYLESHEET)
        self.format_combo.setMinimumHeight(32)
        format_layout.addWidget(self.format_combo)
        
        # Add reload button
        reload_btn = QPushButton("🔄 Reload")
        reload_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                color: #ffffff;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 11px;
                min-height: 32px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """)
        reload_btn.setToolTip("Reload brokers and formats from database")
        reload_btn.clicked.connect(self._load_brokers_and_formats)
        format_layout.addWidget(reload_btn)
        
        config_layout.addLayout(format_layout)
        config_group.setLayout(config_layout)
        top_row.addWidget(config_group)
        
        # Sections group
        sections_group = QGroupBox("Sections")
        sections_group.setStyleSheet(config_group.styleSheet())
        sections_layout = QVBoxLayout()
        sections_layout.setSpacing(8)
        sections_layout.setContentsMargins(5, 5, 5, 5)
        
        self.ams_checkbox = QCheckBox("AMS")
        self.ams_checkbox.setChecked(True)
        self.ams_checkbox.setStyleSheet(DARK_THEME_STYLESHEET)
        sections_layout.addWidget(self.ams_checkbox)
        
        self.entries_checkbox = QCheckBox("Entries")
        self.entries_checkbox.setChecked(True)
        self.entries_checkbox.setStyleSheet(DARK_THEME_STYLESHEET)
        sections_layout.addWidget(self.entries_checkbox)
        
        self.custom_checkbox = QCheckBox("Custom Report")
        self.custom_checkbox.setChecked(True)
        self.custom_checkbox.setStyleSheet(DARK_THEME_STYLESHEET)
        sections_layout.addWidget(self.custom_checkbox)
        
        self.pdf_checkbox = QCheckBox("Download 7501 PDF")
        self.pdf_checkbox.setChecked(False)
        self.pdf_checkbox.setStyleSheet(DARK_THEME_STYLESHEET)
        sections_layout.addWidget(self.pdf_checkbox)
        
        sections_group.setLayout(sections_layout)
        top_row.addWidget(sections_group)
        
        # Set equal stretch for both groups
        top_row.setStretch(0, 2)
        top_row.setStretch(1, 1)
        
        layout.addLayout(top_row)
        
        # Bulk Input Area - Horizontal layout with input on left, table on right
        bulk_group = QGroupBox("MAWB Input & Parsed Items")
        bulk_group.setStyleSheet(config_group.styleSheet())
        bulk_layout = QHBoxLayout()  # Changed to horizontal
        bulk_layout.setSpacing(15)
        bulk_layout.setContentsMargins(10, 10, 10, 10)
        
        # Left side: Input area
        input_container = QVBoxLayout()
        input_container.setSpacing(10)
        
        # Input header with label and buttons
        input_header = QHBoxLayout()
        input_header.setSpacing(10)
        
        bulk_label = QLabel("Paste MAWBs (format: Port, Customer, Broker, HAWBs, Master or MAWB-only)")
        bulk_label.setStyleSheet("color: rgba(255, 255, 255, 0.7); font-size: 12px;")
        input_header.addWidget(bulk_label)
        
        input_header.addStretch()
        
        parse_btn = QPushButton("Parse & Add")
        parse_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(245, 158, 11, 0.2);
                color: #f59e0b;
                border: 1px solid rgba(245, 158, 11, 0.4);
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 13px;
                min-height: 28px;
            }
            QPushButton:hover {
                background-color: rgba(245, 158, 11, 0.3);
            }
            QPushButton:disabled {
                opacity: 0.5;
            }
        """)
        parse_btn.clicked.connect(self._on_parse_clicked)
        input_header.addWidget(parse_btn)
        
        clear_btn = QPushButton("Clear All")
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                color: #ffffff;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 13px;
                min-height: 28px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.15);
            }
        """)
        clear_btn.clicked.connect(self._on_clear_clicked)
        input_header.addWidget(clear_btn)
        
        input_container.addLayout(input_header)
        
        self.bulk_input = QTextEdit()
        self.bulk_input.setPlaceholderText(
            "ORD\tMZZ\tBrokerName\t4250\t235-94731221\n"
            "ORD\tWIN\tBrokerName\t1234\t112-00810176\n"
            "235-94731221 ORD WIN\n"
            "or just: 23594731221"
        )
        self.bulk_input.setStyleSheet("""
            QTextEdit {
                background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 10px;
                color: #ffffff;
                font-family: 'Courier New', monospace;
                font-size: 12px;
            }
            QScrollBar:vertical {
                background-color: rgba(255, 255, 255, 0.05);
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: rgba(255, 255, 255, 0.3);
            }
            QScrollBar:horizontal {
                background-color: rgba(255, 255, 255, 0.05);
                height: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal {
                background-color: rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                min-width: 30px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: rgba(255, 255, 255, 0.3);
            }
        """)
        self.bulk_input.setMinimumHeight(200)
        self.bulk_input.setMaximumHeight(400)  # Increased max height
        self.bulk_input.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)  # Allow horizontal scrolling
        input_container.addWidget(self.bulk_input)
        
        # Add input container to left side
        input_widget = QWidget()
        input_widget.setLayout(input_container)
        bulk_layout.addWidget(input_widget, 1)  # Stretch factor 1
        
        # Right side: Parsed items table
        table_container = QVBoxLayout()
        table_container.setSpacing(10)
        
        # Items count label
        table_header = QHBoxLayout()
        table_header.setSpacing(10)
        
        self.items_count_label = QLabel("0 items ready")
        self.items_count_label.setStyleSheet("color: rgba(255, 255, 255, 0.7); font-size: 12px; font-weight: 500;")
        table_header.addWidget(self.items_count_label)
        table_header.addStretch()
        
        table_container.addLayout(table_header)
        
        # Parsed items table
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(4)
        self.items_table.setHorizontalHeaderLabels(["MAWB", "Airport", "Customer", "HAWBs"])
        self.items_table.horizontalHeader().setStretchLastSection(True)
        self.items_table.setStyleSheet("""
            QTableWidget {
                background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                gridline-color: rgba(255, 255, 255, 0.1);
                color: #ffffff;
            }
            QTableWidget::item {
                padding: 6px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: rgba(245, 158, 11, 0.2);
                color: #ffffff;
            }
            QHeaderView::section {
                background-color: rgba(255, 255, 255, 0.1);
                color: #ffffff;
                padding: 8px;
                border: none;
                font-weight: 600;
                font-size: 12px;
            }
            QScrollBar:vertical {
                background-color: rgba(255, 255, 255, 0.05);
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: rgba(255, 255, 255, 0.3);
            }
            QScrollBar:horizontal {
                background-color: rgba(255, 255, 255, 0.05);
                height: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal {
                background-color: rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                min-width: 30px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: rgba(255, 255, 255, 0.3);
            }
        """)
        # Use fixed height to ensure scrollbar works properly when content exceeds
        self.items_table.setFixedHeight(400)  # Fixed height allows scrolling when content exceeds
        self.items_table.setVisible(True)  # Always visible now
        self.items_table.setAlternatingRowColors(True)
        self.items_table.verticalHeader().setVisible(False)  # Hide row numbers
        # Enable scrolling when content exceeds visible area (this is the default, but explicit is better)
        self.items_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.items_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        table_container.addWidget(self.items_table)
        
        # Add table container to right side
        table_widget = QWidget()
        table_widget.setLayout(table_container)
        bulk_layout.addWidget(table_widget, 1)  # Stretch factor 1
        
        bulk_group.setLayout(bulk_layout)
        layout.addWidget(bulk_group)
        
        # Start Processing button and progress
        action_row = QHBoxLayout()
        action_row.setSpacing(15)
        
        # Progress and status on left
        progress_container = QVBoxLayout()
        progress_container.setSpacing(5)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet(DARK_THEME_STYLESHEET)
        self.progress_bar.setVisible(False)
        self.progress_bar.setMinimumHeight(24)
        progress_container.addWidget(self.progress_bar)
        
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: rgba(255, 255, 255, 0.7); font-size: 12px;")
        self.status_label.setVisible(False)
        progress_container.addWidget(self.status_label)
        
        action_row.addLayout(progress_container)
        action_row.addStretch()
        
        # Start button on right
        self.start_processing_btn = QPushButton("Start Processing")
        self.start_processing_btn.setStyleSheet("""
            QPushButton {
                background-color: #f59e0b;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 10px 24px;
                font-size: 14px;
                font-weight: 600;
                min-height: 40px;
            }
            QPushButton:hover {
                background-color: #fbbf24;
            }
            QPushButton:disabled {
                background-color: rgba(245, 158, 11, 0.5);
            }
        """)
        self.start_processing_btn.clicked.connect(self._on_start_processing_clicked)
        self.start_processing_btn.setEnabled(False)
        action_row.addWidget(self.start_processing_btn)
        
        layout.addLayout(action_row)
        
        # Logs
        logs_group = QGroupBox("Logs")
        logs_group.setStyleSheet(config_group.styleSheet())
        logs_layout = QVBoxLayout()
        logs_layout.setContentsMargins(5, 5, 5, 5)
        logs_layout.setSpacing(5)
        
        self.logs_text = QTextEdit()
        self.logs_text.setReadOnly(True)
        self.logs_text.setStyleSheet("""
            QTextEdit {
                background-color: rgba(0, 0, 0, 0.3);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 10px;
                color: #cbd5e1;
                font-family: 'Courier New', monospace;
                font-size: 12px;
            }
        """)
        self.logs_text.setMaximumHeight(180)
        logs_layout.addWidget(self.logs_text)
        logs_group.setLayout(logs_layout)
        layout.addWidget(logs_group)
        
        layout.addStretch()
        self.setLayout(layout)

    def _load_brokers_and_formats(self) -> None:
        """Load brokers and formats from Supabase."""
        try:
            # Try loading active brokers first
            brokers = self.duty_service.list_brokers(active_only=True)
            logger.info(f"Loaded {len(brokers)} active brokers from database")
            
            # If no active brokers, try loading all brokers
            if not brokers:
                brokers = self.duty_service.list_brokers(active_only=False)
                logger.info(f"Loaded {len(brokers)} total brokers (including inactive) from database")
                if brokers:
                    self._log("⚠️ No active brokers found, showing all brokers (including inactive)")
            
            self.broker_combo.clear()
            if not brokers:
                self.broker_combo.addItem("No brokers available", None)
                self._log("⚠️ No brokers found in database")
            else:
                for broker in brokers:
                    broker_name = broker.get("name", "Unknown")
                    broker_id = broker.get("id")
                    is_active = broker.get("is_active", True)
                    # Show inactive brokers with a marker
                    display_name = broker_name if is_active else f"{broker_name} (inactive)"
                    self.broker_combo.addItem(display_name, broker_id)
                    logger.debug(f"Added broker: {display_name} (id: {broker_id}, active: {is_active})")
            
            # Try loading active formats first
            formats = self.duty_service.list_formats(active_only=True)
            logger.info(f"Loaded {len(formats)} active formats from database")
            
            # If no active formats, try loading all formats
            if not formats:
                formats = self.duty_service.list_formats(active_only=False)
                logger.info(f"Loaded {len(formats)} total formats (including inactive) from database")
                if formats:
                    self._log("⚠️ No active formats found, showing all formats (including inactive)")
            
            self.format_combo.clear()
            if not formats:
                self.format_combo.addItem("No formats available", None)
                self._log("⚠️ No formats found in database")
            else:
                for format_item in formats:
                    format_name = format_item.get("name", "Unknown")
                    format_id = format_item.get("id")
                    is_active = format_item.get("is_active", True)
                    # Show inactive formats with a marker
                    display_name = format_name if is_active else f"{format_name} (inactive)"
                    self.format_combo.addItem(display_name, format_id)
                    logger.debug(f"Added format: {display_name} (id: {format_id}, active: {is_active})")
            
            if brokers and formats:
                self._log(f"✅ Loaded {len(brokers)} brokers and {len(formats)} formats from database")
            elif not brokers and not formats:
                self._log("⚠️ No brokers or formats found in database. Please check Supabase.")
                QMessageBox.warning(
                    self, 
                    "No Data", 
                    "No brokers or formats found in the database.\n\n"
                    "Please ensure brokers and formats are configured in Supabase.\n\n"
                    "You can manage them through the main web application."
                )
        except Exception as exc:
            logger.error(f"Error loading brokers/formats: {exc}", exc_info=True)
            self._log(f"❌ Error loading brokers/formats: {exc}")
            QMessageBox.critical(self, "Error", f"Failed to load brokers/formats:\n\n{exc}")

    def _on_parse_clicked(self) -> None:
        """Handle parse button click."""
        broker_id = self.broker_combo.currentData()
        format_id = self.format_combo.currentData()
        
        if not broker_id or not format_id:
            QMessageBox.warning(
                self,
                "Configuration Required",
                "Please select both a broker and format before parsing."
            )
            return
        
        input_text = self.bulk_input.toPlainText().strip()
        # #region agent log
        try:
            with open(DEBUG_LOG_PATH, 'a') as f:
                f.write(json.dumps({
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "GUI",
                    "location": "duty_runner.py:_on_parse_clicked:input",
                    "message": "Input text from QTextEdit",
                    "data": {
                        "input_length": len(input_text),
                        "input_preview": input_text[:200],
                        "input_repr": repr(input_text[:200]),
                        "has_tab": "\t" in input_text,
                        "tab_count": input_text.count("\t"),
                        "line_count": len(input_text.split("\n"))
                    },
                    "timestamp": __import__('time').time() * 1000
                }) + "\n")
        except: pass
        # #endregion
        
        if not input_text:
            QMessageBox.warning(self, "No Input", "Please enter MAWBs to parse.")
            return
        
        # Parse MAWBs
        parsed = parse_mawb_input(input_text)
        
        # #region agent log
        try:
            with open(DEBUG_LOG_PATH, 'a') as f:
                f.write(json.dumps({
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "GUI",
                    "location": "duty_runner.py:_on_parse_clicked:parsed",
                    "message": "Parsed results",
                    "data": {
                        "parsed_count": len(parsed),
                        "parsed_items": [{"mawb": p.get("mawb"), "airport": p.get("airport_code"), "customer": p.get("customer"), "hawbs": p.get("checkbook_hawbs")} for p in parsed[:5]]
                    },
                    "timestamp": __import__('time').time() * 1000
                }) + "\n")
        except: pass
        # #endregion
        if not parsed:
            QMessageBox.warning(
                self,
                "No Valid MAWBs",
                "Could not parse any valid 11-digit MAWBs from the input."
            )
            return
        
        # Debug: Log what was parsed
        logger.debug(f"Parsed {len(parsed)} items:")
        for item in parsed:
            logger.debug(f"  - MAWB: {item.get('mawb')}, Airport: {item.get('airport_code')}, Customer: {item.get('customer')}, HAWBs: {item.get('checkbook_hawbs')}")
        
        # Add broker_id and format_id to each item
        for item in parsed:
            item['broker_id'] = str(broker_id)
            item['format_id'] = str(format_id)
        
        # Merge with existing items (avoid duplicates)
        existing_mawbs = {item['mawb'] for item in self.parsed_items}
        new_items = [item for item in parsed if item['mawb'] not in existing_mawbs]
        self.parsed_items.extend(new_items)
        
        # #region agent log
        try:
            with open(DEBUG_LOG_PATH, 'a') as f:
                f.write(json.dumps({
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "GUI",
                    "location": "duty_runner.py:_on_parse_clicked:after_add",
                    "message": "After adding to parsed_items",
                    "data": {
                        "total_items": len(self.parsed_items),
                        "new_items_count": len(new_items),
                        "new_items": [{"mawb": p.get("mawb"), "airport": p.get("airport_code"), "customer": p.get("customer"), "hawbs": p.get("checkbook_hawbs")} for p in new_items[:5]]
                    },
                    "timestamp": __import__('time').time() * 1000
                }) + "\n")
        except: pass
        # #endregion
        
        # Clear input
        self.bulk_input.clear()
        
        # Update UI - force update
        self._update_items_table()
        
        # Log success with details
        if new_items:
            self._log(f"✅ Parsed {len(parsed)} MAWBs ({len(new_items)} new, {len(parsed) - len(new_items)} duplicates skipped)")
            # Show preview of added items with all details
            preview_items = []
            for item in new_items[:3]:
                mawb = item['mawb']
                mawb_fmt = f"{mawb[:3]}-{mawb[3:]}" if len(mawb) == 11 else mawb
                airport = item.get('airport_code', '—')
                customer = item.get('customer', '—')
                preview_items.append(f"{mawb_fmt} ({airport}/{customer})")
            preview = ", ".join(preview_items)
            if len(new_items) > 3:
                preview += f" ... and {len(new_items) - 3} more"
            self._log(f"   Added: {preview}")
        else:
            self._log(f"⚠️ All {len(parsed)} MAWBs were duplicates")

    def _on_clear_clicked(self) -> None:
        """Handle clear button click."""
        self.parsed_items.clear()
        self.bulk_input.clear()
        self._update_items_table()
        self._log("Cleared all items")

    def _update_items_table(self) -> None:
        """Update the parsed items table."""
        logger.debug(f"Updating items table with {len(self.parsed_items)} items")
        
        # #region agent log
        try:
            with open(DEBUG_LOG_PATH, 'a') as f:
                f.write(json.dumps({
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "GUI",
                    "location": "duty_runner.py:_update_items_table:entry",
                    "message": "Table update entry",
                    "data": {
                        "parsed_items_count": len(self.parsed_items),
                        "table_visible_before": self.items_table.isVisible(),
                        "table_row_count_before": self.items_table.rowCount()
                    },
                    "timestamp": __import__('time').time() * 1000
                }) + "\n")
        except: pass
        # #endregion
        
        # Always keep table visible, just show empty if no items
        self.items_table.setVisible(True)
        
        if not self.parsed_items:
            self.items_table.setRowCount(0)
            self.items_count_label.setText("0 items ready")
            self.start_processing_btn.setEnabled(False)
            logger.debug("No items, showing empty table")
            return
        
        # Show table and update
        logger.debug(f"Showing table with {len(self.parsed_items)} items")
        self.items_table.setVisible(True)
        self.items_table.setRowCount(len(self.parsed_items))
        
        for row, item in enumerate(self.parsed_items):
            logger.debug(f"Row {row}: {item}")
            
            # MAWB (format as XXX-XXXXXXXX)
            mawb = item.get('mawb', '')
            if len(mawb) == 11:
                mawb_formatted = f"{mawb[:3]}-{mawb[3:]}"
            else:
                mawb_formatted = mawb
            mawb_item = QTableWidgetItem(mawb_formatted)
            mawb_item.setForeground(Qt.GlobalColor.white)
            self.items_table.setItem(row, 0, mawb_item)
            
            # Airport
            airport_code = item.get('airport_code')
            airport_display = str(airport_code) if airport_code else '—'
            airport_item = QTableWidgetItem(airport_display)
            airport_item.setForeground(Qt.GlobalColor.white)
            self.items_table.setItem(row, 1, airport_item)
            
            # Customer
            customer = item.get('customer')
            customer_display = str(customer) if customer else '—'
            customer_item = QTableWidgetItem(customer_display)
            customer_item.setForeground(Qt.GlobalColor.white)
            self.items_table.setItem(row, 2, customer_item)
            
            # HAWBs
            hawbs = item.get('checkbook_hawbs')
            hawbs_display = str(hawbs) if hawbs else '—'
            hawbs_item = QTableWidgetItem(hawbs_display)
            hawbs_item.setForeground(Qt.GlobalColor.white)
            self.items_table.setItem(row, 3, hawbs_item)
        
        # Resize columns to fit content
        self.items_table.resizeColumnsToContents()
        # Ensure minimum column widths
        self.items_table.setColumnWidth(0, max(130, self.items_table.columnWidth(0)))  # MAWB
        self.items_table.setColumnWidth(1, max(90, self.items_table.columnWidth(1)))   # Airport
        self.items_table.setColumnWidth(2, max(120, self.items_table.columnWidth(2)))  # Customer
        self.items_table.setColumnWidth(3, max(90, self.items_table.columnWidth(3)))   # HAWBs
        
        # Update count label with color
        count_text = f"{len(self.parsed_items)} item{'s' if len(self.parsed_items) != 1 else ''} ready"
        self.items_count_label.setText(count_text)
        self.items_count_label.setStyleSheet("color: #10b981; font-size: 13px; font-weight: 600; padding: 5px 0px;")
        self.start_processing_btn.setEnabled(len(self.parsed_items) > 0)
        
        # Force table to show and update
        self.items_table.show()
        self.items_table.update()
        self.items_table.repaint()
        
        # Scroll to bottom to show new items (scrollbar will appear automatically if needed)
        if len(self.parsed_items) > 0:
            self.items_table.scrollToBottom()
        
        # #region agent log
        try:
            with open(DEBUG_LOG_PATH, 'a') as f:
                f.write(json.dumps({
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "GUI",
                    "location": "duty_runner.py:_update_items_table:exit",
                    "message": "Table update exit",
                    "data": {
                        "table_visible_after": self.items_table.isVisible(),
                        "table_row_count_after": self.items_table.rowCount(),
                        "table_hidden_after": self.items_table.isHidden(),
                        "table_enabled_after": self.items_table.isEnabled()
                    },
                    "timestamp": __import__('time').time() * 1000
                }) + "\n")
        except: pass
        # #endregion
        
        logger.debug(f"Table updated: visible={self.items_table.isVisible()}, rows={self.items_table.rowCount()}")

    def _on_start_processing_clicked(self) -> None:
        """Handle start processing button click."""
        if not self.parsed_items:
            QMessageBox.warning(self, "No Items", "Please parse and add items first.")
            return
        
        # Get sections
        sections = {
            "ams": self.ams_checkbox.isChecked(),
            "entries": self.entries_checkbox.isChecked(),
            "custom": self.custom_checkbox.isChecked(),
            "download_7501_pdf": self.pdf_checkbox.isChecked(),
        }
        
        if not any(sections.values()):
            QMessageBox.warning(self, "No Sections", "Please select at least one section to process.")
            return
        
        # Validate all items have broker_id and format_id
        invalid_items = [item for item in self.parsed_items if not item.get('broker_id') or not item.get('format_id')]
        if invalid_items:
            QMessageBox.warning(
                self,
                "Invalid Items",
                f"{len(invalid_items)} items are missing broker or format. Please parse them again."
            )
            return
        
        # Clear previous session results
        self.session_results.clear()
        
        # Clear logs
        self.logs_text.clear()
        self._log(f"Starting processing for {len(self.parsed_items)} MAWB(s)...")
        
        # Disable button and show progress
        self.start_processing_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setVisible(True)
        self.status_label.setText(f"Processing 0/{len(self.parsed_items)}...")
        
        # Process items sequentially
        self.current_processing_index = 0
        self._process_next_item(sections)

    def _process_next_item(self, sections: dict) -> None:
        """Process the next item in the queue."""
        if self.current_processing_index >= len(self.parsed_items):
            # All items processed
            self._on_all_processing_complete()
            return
        
        item = self.parsed_items[self.current_processing_index]
        mawb = item['mawb']
        broker_id = UUID(item['broker_id'])
        format_id = UUID(item['format_id'])
        airport_code = item.get('airport_code')
        customer = item.get('customer')
        checkbook_hawbs = item.get('checkbook_hawbs')
        
        self._log(f"Processing MAWB {self.current_processing_index + 1}/{len(self.parsed_items)}: {mawb}")
        if checkbook_hawbs:
            self._log(f"  Checkbook HAWBs: {checkbook_hawbs}")
        self.status_label.setText(f"Processing {self.current_processing_index + 1}/{len(self.parsed_items)}: {mawb}")
        
        # Create and start processing thread
        thread = ProcessingThread(
            self.duty_service,
            mawb,
            broker_id,
            format_id,
            sections,
            airport_code=airport_code,
            customer=customer,
            checkbook_hawbs=checkbook_hawbs,
        )
        thread.progress.connect(self._on_progress)
        thread.log_message.connect(self._log)
        thread.finished.connect(lambda result: self._on_item_finished(result, sections))
        thread.error.connect(lambda error: self._on_item_error(error, sections))
        thread.start()
        
        self.processing_threads.append(thread)

    def _on_progress(self, message: str, percentage: int) -> None:
        """Handle progress update."""
        # Calculate overall progress
        total_items = len(self.parsed_items)
        if total_items > 0:
            base_progress = int((self.current_processing_index / total_items) * 100)
            item_progress = int((percentage / 100) * (1 / total_items) * 100)
            overall_progress = base_progress + item_progress
            self.progress_bar.setValue(min(overall_progress, 100))
        else:
            self.progress_bar.setValue(percentage)

    def _on_item_finished(self, result: dict, sections: dict) -> None:
        """Handle single item processing finished."""
        # Merge result with item data (airport_code, customer from parsed input)
        item = self.parsed_items[self.current_processing_index]
        result_dict = result.get("result", result)
        
        # Add airport_code and customer from parsed input if not in result
        if "airport_code" not in result_dict or not result_dict.get("airport_code"):
            result_dict["airport_code"] = item.get("airport_code")
        if "customer" not in result_dict or not result_dict.get("customer"):
            result_dict["customer"] = item.get("customer")
        
        # Extract PDF URL from summary if available
        summary = result_dict.get("summary", {})
        if isinstance(summary, str):
            import json
            try:
                summary = json.loads(summary)
            except:
                summary = {}
        
        if isinstance(summary, dict):
            pdf_url = summary.get("7501 Batch PDF URL")
            if pdf_url and pdf_url != "N/A" and pdf_url.strip():
                result_dict["pdf_url"] = pdf_url
                # Also try to set pdf_path if we can reconstruct it
                if not result_dict.get("pdf_path"):
                    mawb = result_dict.get("mawb", "")
                    airport_code = result_dict.get("airport_code", "")
                    customer = result_dict.get("customer", "")
                    
                    mawb_clean = mawb.replace("/", "-").replace("\\", "-").replace(" ", "").replace("-", "")
                    if len(mawb_clean) == 11:
                        formatted_mawb = f"{mawb_clean[:3]}-{mawb_clean[3:]}"
                    else:
                        formatted_mawb = mawb_clean
                    
                    parts = [formatted_mawb]
                    if airport_code:
                        parts.append(airport_code)
                    if customer:
                        parts.append(customer)
                    filename = " ".join(parts) + ".pdf"
                    
                    import os
                    prefix = os.getenv("NETCHB_DUTY_STORAGE_PREFIX", "netchb-duty")
                    result_dict["pdf_path"] = f"{prefix}/7501-batch-pdfs/{filename}"
        
        # Use result_dict as the main result
        final_result = result_dict.copy()
        final_result.update(result)  # Add any additional fields from result
        
        self.session_results.append(final_result)
        self.current_processing_index += 1
        
        # Update progress
        total_items = len(self.parsed_items)
        progress = int((self.current_processing_index / total_items) * 100) if total_items > 0 else 100
        self.progress_bar.setValue(progress)
        
        mawb = result.get('mawb', 'Unknown')
        self._log(f"✅ Completed: {mawb}")
        
        # Process next item
        self._process_next_item(sections)

    def _on_item_error(self, error: str, sections: dict) -> None:
        """Handle single item processing error."""
        self.current_processing_index += 1
        self._log(f"❌ Error: {error}")
        
        # Add error result to session results
        error_result = {
            'mawb': self.parsed_items[self.current_processing_index - 1].get('mawb', 'Unknown'),
            'status': 'failed',
            'error_message': error,
        }
        self.session_results.append(error_result)
        
        # Update progress
        total_items = len(self.parsed_items)
        progress = int((self.current_processing_index / total_items) * 100) if total_items > 0 else 100
        self.progress_bar.setValue(progress)
        
        # Process next item
        self._process_next_item(sections)

    def _on_all_processing_complete(self) -> None:
        """Handle all processing complete."""
        self.start_processing_btn.setEnabled(True)
        self.progress_bar.setValue(100)
        self.status_label.setText(f"Completed: {len(self.session_results)} result(s)")
        
        success_count = sum(1 for r in self.session_results if r.get('status') == 'success')
        failed_count = len(self.session_results) - success_count
        
        self._log(f"✅ All processing complete! Success: {success_count}, Failed: {failed_count}")
        
        # Emit signal to notify Results tab
        self.processing_complete.emit(self.session_results)
        
        QMessageBox.information(
            self,
            "Processing Complete",
            f"Processing completed!\n\n"
            f"Success: {success_count}\n"
            f"Failed: {failed_count}\n\n"
            f"View results in the Results tab."
        )

    def _log(self, message: str) -> None:
        """Add log message."""
        self.logs_text.append(message)
