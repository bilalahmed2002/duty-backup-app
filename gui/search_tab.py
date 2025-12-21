"""Search tab for finding historical MAWB results."""

from __future__ import annotations

import logging
from typing import Optional, List, Dict
from pathlib import Path
from datetime import datetime

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QFileDialog,
)

# Import styles
import sys
import importlib.util
from pathlib import Path
_app_dir = Path(__file__).parent.parent.resolve()
styles_path = _app_dir / "utils" / "styles.py"
spec = importlib.util.spec_from_file_location("duty_backup_styles", styles_path)
styles_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(styles_module)
DARK_THEME_STYLESHEET = styles_module.DARK_THEME_STYLESHEET

logger = logging.getLogger(__name__)


class SearchTabWidget(QWidget):
    """Widget for searching MAWBs and viewing historical results."""

    def __init__(self, duty_service, parent: Optional[QWidget] = None) -> None:
        """Initialize search tab widget.

        Args:
            duty_service: StandaloneDutyService instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.duty_service = duty_service
        
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the UI components."""
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title = QLabel("Search MAWB")
        title.setStyleSheet("color: #ffffff; font-size: 24px; font-weight: 700;")
        layout.addWidget(title)
        
        # Search input
        search_layout = QHBoxLayout()
        search_label = QLabel("MAWB:")
        search_label.setStyleSheet("color: #ffffff; font-size: 14px; min-width: 100px;")
        search_layout.addWidget(search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter 11-digit MAWB number")
        self.search_input.setStyleSheet(DARK_THEME_STYLESHEET)
        self.search_input.returnPressed.connect(self._on_search_clicked)
        search_layout.addWidget(self.search_input)
        
        search_btn = QPushButton("Search")
        search_btn.setStyleSheet("""
            QPushButton {
                background-color: #f59e0b;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #fbbf24;
            }
        """)
        search_btn.clicked.connect(self._on_search_clicked)
        search_layout.addWidget(search_btn)
        
        layout.addLayout(search_layout)
        
        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(7)
        self.results_table.setHorizontalHeaderLabels([
            "Broker",
            "Format",
            "Status",
            "Date",
            "Excel Report",
            "PDF",
            "Actions",
        ])
        self.results_table.horizontalHeader().setStyleSheet("""
            QHeaderView::section {
                background-color: rgba(255, 255, 255, 0.1);
                color: #ffffff;
                padding: 10px;
                border: none;
                font-weight: 600;
            }
        """)
        self.results_table.setStyleSheet("""
            QTableWidget {
                background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                gridline-color: rgba(255, 255, 255, 0.1);
                color: #ffffff;
            }
            QTableWidget::item {
                padding: 8px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: rgba(245, 158, 11, 0.2);
                color: #ffffff;
            }
        """)
        self.results_table.horizontalHeader().setStretchLastSection(True)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setVisible(False)
        layout.addWidget(self.results_table)
        
        # Status label
        self.status_label = QLabel("Enter a MAWB number and click Search to find historical results.")
        self.status_label.setStyleSheet("color: rgba(255, 255, 255, 0.7); font-size: 14px; padding: 20px;")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        self.setLayout(layout)

    def _on_search_clicked(self) -> None:
        """Handle search button click."""
        mawb = self.search_input.text().strip()
        mawb_digits = "".join(c for c in mawb if c.isdigit())
        
        if len(mawb_digits) != 11:
            QMessageBox.warning(self, "Invalid MAWB", "MAWB must contain exactly 11 digits.")
            return
        
        try:
            # Search for all results matching this MAWB
            results = self.duty_service.list_results(mawb=mawb_digits, limit=None)
            
            if not results:
                self.status_label.setText(f"No results found for MAWB: {mawb_digits}")
                self.status_label.setVisible(True)
                self.results_table.setVisible(False)
                QMessageBox.information(self, "No Results", f"No historical results found for MAWB: {mawb_digits}")
                return
            
            # Show results
            self.status_label.setVisible(False)
            self.results_table.setVisible(True)
            self._populate_table(results)
            
        except Exception as exc:
            logger.error(f"Error searching MAWB: {exc}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to search MAWB:\n\n{exc}")

    def _populate_table(self, results: List[Dict]) -> None:
        """Populate table with search results."""
        self.results_table.setRowCount(len(results))
        
        for row, result in enumerate(results):
            col = 0
            
            # Broker
            broker_item = QTableWidgetItem(result.get("broker_name") or "—")
            self.results_table.setItem(row, col, broker_item)
            col += 1
            
            # Format
            format_item = QTableWidgetItem(result.get("template_name") or "—")
            self.results_table.setItem(row, col, format_item)
            col += 1
            
            # Status
            status = result.get("status", "unknown")
            status_item = QTableWidgetItem(status.upper())
            if status == "success":
                status_item.setForeground(Qt.GlobalColor.green)
            elif status == "failed":
                status_item.setForeground(Qt.GlobalColor.red)
            else:
                status_item.setForeground(Qt.GlobalColor.yellow)
            self.results_table.setItem(row, col, status_item)
            col += 1
            
            # Date
            completed_at = result.get("completed_at", "")
            if completed_at:
                try:
                    if isinstance(completed_at, str):
                        dt = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
                    else:
                        dt = completed_at
                    date_text = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    date_text = str(completed_at)[:16]
            else:
                date_text = "—"
            date_item = QTableWidgetItem(date_text)
            self.results_table.setItem(row, col, date_item)
            col += 1
            
            # Excel Report
            artifact_url = result.get("artifact_url")
            artifact_path = result.get("artifact_path")
            has_excel = bool(artifact_url or artifact_path)
            
            excel_widget = QWidget()
            excel_layout = QHBoxLayout()
            excel_layout.setContentsMargins(4, 4, 4, 4)
            excel_layout.setSpacing(0)
            excel_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            if has_excel:
                excel_btn = QPushButton("Download")
                excel_btn.setStyleSheet("""
                    QPushButton {
                        background-color: rgba(16, 185, 129, 0.25);
                        color: #10b981;
                        border: 1px solid rgba(16, 185, 129, 0.5);
                        border-radius: 6px;
                        padding: 6px 12px;
                        font-size: 12px;
                        font-weight: 600;
                        min-width: 80px;
                        max-width: 80px;
                    }
                    QPushButton:hover {
                        background-color: rgba(16, 185, 129, 0.4);
                        border-color: rgba(16, 185, 129, 0.7);
                    }
                    QPushButton:pressed {
                        background-color: rgba(16, 185, 129, 0.5);
                    }
                """)
                excel_btn.clicked.connect(lambda checked, r=result: self._download_excel(r))
                excel_layout.addWidget(excel_btn)
                excel_layout.addStretch()
            else:
                excel_label = QLabel("N/A")
                excel_label.setStyleSheet("color: rgba(255, 255, 255, 0.5); font-size: 13px; padding: 8px;")
                excel_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                excel_layout.addWidget(excel_label)
            
            excel_widget.setLayout(excel_layout)
            self.results_table.setCellWidget(row, col, excel_widget)
            col += 1
            
            # PDF - check summary for PDF URL
            summary = result.get("summary", {})
            if isinstance(summary, str):
                import json
                try:
                    summary = json.loads(summary)
                except:
                    summary = {}
            
            pdf_url = summary.get("7501 Batch PDF URL") if isinstance(summary, dict) else None
            pdf_path = result.get("pdf_path")  # May also have direct path
            has_pdf = bool(pdf_url and pdf_url != "N/A" and pdf_url.strip()) or bool(pdf_path)
            
            pdf_widget = QWidget()
            pdf_layout = QHBoxLayout()
            pdf_layout.setContentsMargins(4, 4, 4, 4)
            pdf_layout.setSpacing(0)
            pdf_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            if has_pdf:
                pdf_btn = QPushButton("Download")
                pdf_btn.setStyleSheet("""
                    QPushButton {
                        background-color: rgba(239, 68, 68, 0.25);
                        color: #ef4444;
                        border: 1px solid rgba(239, 68, 68, 0.5);
                        border-radius: 6px;
                        padding: 6px 12px;
                        font-size: 12px;
                        font-weight: 600;
                        min-width: 80px;
                        max-width: 80px;
                    }
                    QPushButton:hover {
                        background-color: rgba(239, 68, 68, 0.4);
                        border-color: rgba(239, 68, 68, 0.7);
                    }
                    QPushButton:pressed {
                        background-color: rgba(239, 68, 68, 0.5);
                    }
                """)
                pdf_btn.clicked.connect(lambda checked, r=result: self._download_pdf(r))
                pdf_layout.addWidget(pdf_btn)
                pdf_layout.addStretch()
            else:
                pdf_label = QLabel("N/A")
                pdf_label.setStyleSheet("color: rgba(255, 255, 255, 0.5); font-size: 13px; padding: 8px;")
                pdf_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                pdf_layout.addWidget(pdf_label)
            
            pdf_widget.setLayout(pdf_layout)
            self.results_table.setCellWidget(row, col, pdf_widget)
            col += 1
            
            # Actions (view details)
            view_widget = QWidget()
            view_layout = QHBoxLayout()
            view_layout.setContentsMargins(4, 4, 4, 4)
            view_layout.setSpacing(0)
            view_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            view_btn = QPushButton("View")
            view_btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(255, 255, 255, 0.15);
                    color: #ffffff;
                    border: 1px solid rgba(255, 255, 255, 0.3);
                    border-radius: 6px;
                    padding: 6px 12px;
                    font-size: 12px;
                    font-weight: 600;
                    min-width: 70px;
                    max-width: 70px;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.25);
                    border-color: rgba(255, 255, 255, 0.4);
                }
                QPushButton:pressed {
                    background-color: rgba(255, 255, 255, 0.3);
                }
            """)
            view_btn.clicked.connect(lambda checked, r=result: self._view_details(r))
            view_layout.addWidget(view_btn)
            view_layout.addStretch()
            
            view_widget.setLayout(view_layout)
            self.results_table.setCellWidget(row, col, view_widget)
            col += 1
        
        self.results_table.resizeColumnsToContents()
        # Set appropriate column widths - compact for buttons, wider for text
        self.results_table.setColumnWidth(0, max(100, self.results_table.columnWidth(0)))  # Broker
        self.results_table.setColumnWidth(1, max(100, self.results_table.columnWidth(1)))  # Format
        self.results_table.setColumnWidth(2, max(70, self.results_table.columnWidth(2)))   # Status
        self.results_table.setColumnWidth(3, max(130, self.results_table.columnWidth(3)))   # Date
        self.results_table.setColumnWidth(4, 100)  # Excel Report - fixed width for button
        self.results_table.setColumnWidth(5, 100)  # PDF - fixed width for button
        self.results_table.setColumnWidth(6, 90)  # Actions - fixed width for button

    def _download_excel(self, result: Dict) -> None:
        """Download Excel report for a result."""
        artifact_url = result.get("artifact_url")
        artifact_path = result.get("artifact_path")
        
        if not artifact_url and not artifact_path:
            QMessageBox.warning(self, "No File", "No Excel report available for this result.")
            return
        
        try:
            # Generate filename
            mawb = result.get("mawb", "")
            airport_code = result.get("airport_code", "")
            customer = result.get("customer", "")
            
            # Format MAWB
            if len(mawb) == 11:
                formatted_mawb = f"{mawb[:3]}-{mawb[3:]}"
            else:
                formatted_mawb = mawb
            
            parts = [formatted_mawb]
            if airport_code:
                parts.append(airport_code)
            if customer:
                parts.append(customer)
            default_filename = " ".join(parts) + ".xlsx"
            
            # Get save location
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Excel File",
                default_filename,
                "Excel Files (*.xlsx)"
            )
            
            if not file_path:
                return
            
            # Download file
            if artifact_path:
                file_data = self.duty_service.download_file_from_s3(artifact_path)
            elif artifact_url:
                # Try to download from URL (might be signed URL)
                import urllib.request
                with urllib.request.urlopen(artifact_url) as response:
                    file_data = response.read()
            else:
                raise ValueError("No file path or URL available")
            
            with open(file_path, 'wb') as f:
                f.write(file_data)
            
            QMessageBox.information(self, "Success", f"Excel file saved to:\n{file_path}")
            
        except Exception as exc:
            logger.error(f"Error downloading Excel: {exc}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to download Excel:\n\n{exc}")

    def _download_pdf(self, result: Dict) -> None:
        """Download PDF for a result."""
        # Get PDF URL from summary
        summary = result.get("summary", {})
        if isinstance(summary, str):
            import json
            try:
                summary = json.loads(summary)
            except:
                summary = {}
        
        pdf_url = summary.get("7501 Batch PDF URL") if isinstance(summary, dict) else None
        pdf_path = result.get("pdf_path")  # May also have direct storage path
        
        if not pdf_url or pdf_url == "N/A" or not pdf_url.strip():
            if not pdf_path:
                QMessageBox.warning(self, "No File", "No PDF available for this result.")
                return
        
        try:
            # Generate filename
            mawb = result.get("mawb", "")
            airport_code = result.get("airport_code", "")
            customer = result.get("customer", "")
            
            # Format MAWB
            if len(mawb) == 11:
                formatted_mawb = f"{mawb[:3]}-{mawb[3:]}"
            else:
                formatted_mawb = mawb
            
            parts = [formatted_mawb]
            if airport_code:
                parts.append(airport_code)
            if customer:
                parts.append(customer)
            default_filename = " ".join(parts) + ".pdf"
            
            # Get save location
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save PDF File",
                default_filename,
                "PDF Files (*.pdf)"
            )
            
            if not file_path:
                return
            
            # Download file - try URL first, then storage path
            try:
                if pdf_url and pdf_url != "N/A" and pdf_url.strip():
                    # Try downloading from signed URL
                    import urllib.request
                    with urllib.request.urlopen(pdf_url) as response:
                        file_data = response.read()
                elif pdf_path:
                    # Fallback to storage path
                    file_data = self.duty_service.download_file_from_s3(pdf_path)
                else:
                    raise ValueError("No PDF URL or path available")
                
                with open(file_path, 'wb') as f:
                    f.write(file_data)
                
                QMessageBox.information(self, "Success", f"PDF file saved to:\n{file_path}")
            except Exception as url_exc:
                # If URL download fails, try reconstructing storage path
                try:
                    mawb = result.get("mawb", "")
                    airport_code = result.get("airport_code", "")
                    customer = result.get("customer", "")
                    
                    # Reconstruct storage path
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
                    
                    # Get storage prefix
                    import os
                    prefix = os.getenv("NETCHB_DUTY_STORAGE_PREFIX", "netchb-duty")
                    pdf_storage_path = f"{prefix}/7501-batch-pdfs/{filename}"
                    
                    file_data = self.duty_service.download_file_from_s3(pdf_storage_path)
                    
                    with open(file_path, 'wb') as f:
                        f.write(file_data)
                    
                    QMessageBox.information(self, "Success", f"PDF file saved to:\n{file_path}")
                except Exception as storage_exc:
                    logger.error(f"Error downloading PDF: {storage_exc}", exc_info=True)
                    QMessageBox.critical(self, "Error", f"Failed to download PDF:\n\n{storage_exc}")
            
        except Exception as exc:
            logger.error(f"Error downloading PDF: {exc}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to download PDF:\n\n{exc}")

    def _view_details(self, result: Dict) -> None:
        """View result details."""
        import json
        
        summary = result.get("summary", {})
        if isinstance(summary, str):
            try:
                summary = json.loads(summary)
            except:
                summary = {}
        
        details = f"""
MAWB: {result.get('mawb', 'Unknown')}
Broker: {result.get('broker_name', 'Unknown')}
Format: {result.get('template_name', 'Unknown')}
Status: {result.get('status', 'Unknown')}
Airport: {result.get('airport_code', '—')}
Customer: {result.get('customer', '—')}
Completed: {result.get('completed_at', '—')}

Summary:
{json.dumps(summary, indent=2) if summary else 'No summary available'}
        """
        
        msg = QMessageBox()
        msg.setWindowTitle("Result Details")
        msg.setText(details)
        msg.exec()


