"""Results viewer GUI widget."""

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
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QFileDialog,
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

logger = logging.getLogger(__name__)


class ResultsViewerWidget(QWidget):
    """Widget for viewing duty processing results from current session."""

    def __init__(self, duty_service, parent: Optional[QWidget] = None) -> None:
        """Initialize results viewer widget.

        Args:
            duty_service: StandaloneDutyService instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.duty_service = duty_service
        self.session_results: List[Dict] = []  # Store session results
        
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the UI components."""
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title and controls
        header_layout = QHBoxLayout()
        title = QLabel("Results")
        title.setStyleSheet("color: #ffffff; font-size: 24px; font-weight: 700;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Download buttons
        self.export_excel_btn = QPushButton("Export Excel")
        self.export_excel_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(16, 185, 129, 0.2);
                color: #10b981;
                border: 1px solid rgba(16, 185, 129, 0.4);
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(16, 185, 129, 0.3);
            }
            QPushButton:disabled {
                opacity: 0.5;
            }
        """)
        self.export_excel_btn.clicked.connect(self._on_export_excel)
        self.export_excel_btn.setEnabled(False)
        header_layout.addWidget(self.export_excel_btn)
        
        self.download_reports_btn = QPushButton("Download Reports")
        self.download_reports_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(59, 130, 246, 0.2);
                color: #3b82f6;
                border: 1px solid rgba(59, 130, 246, 0.4);
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(59, 130, 246, 0.3);
            }
            QPushButton:disabled {
                opacity: 0.5;
            }
        """)
        self.download_reports_btn.clicked.connect(self._on_download_reports)
        self.download_reports_btn.setEnabled(False)
        header_layout.addWidget(self.download_reports_btn)
        
        self.download_pdfs_btn = QPushButton("Download PDFs")
        self.download_pdfs_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(239, 68, 68, 0.2);
                color: #ef4444;
                border: 1px solid rgba(239, 68, 68, 0.4);
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(239, 68, 68, 0.3);
            }
            QPushButton:disabled {
                opacity: 0.5;
            }
        """)
        self.download_pdfs_btn.clicked.connect(self._on_download_pdfs)
        self.download_pdfs_btn.setEnabled(False)
        header_layout.addWidget(self.download_pdfs_btn)
        
        layout.addLayout(header_layout)
        
        # Status label
        self.status_label = QLabel("No results yet. Process MAWBs in the Process tab to see results here.")
        self.status_label.setStyleSheet("color: rgba(255, 255, 255, 0.7); font-size: 14px; padding: 20px;")
        layout.addWidget(self.status_label)
        
        # Results table - matching frontend columns
        SUMMARY_FIELDS = [
            "AMS Total HAWBs",
            "AMS Duty",
            "AMS Total T-11 Entries",
            "AMS Entries Accepted",
            "Rejected Entries",
            "7501 Total T-11 Entries",
            "7501 Total Houses",
            "7501 Duty",
            "Report Duty",
            "Report Total House",
            "Total Informal Duty",
            "Complete Total Duty",
            "Entry Date",
            "Cargo Release Date",
        ]
        
        self.results_table = QTableWidget()
        # Columns: Broker, Airport, Customer, MAWB, Status, Summary fields (14), Template, Report
        self.results_table.setColumnCount(8 + len(SUMMARY_FIELDS))
        headers = [
            "Broker Name",
            "Airport Code",
            "Customer",
            "MAWB",
            "Status",
        ] + SUMMARY_FIELDS + [
            "Template Name",
            "Report",
        ]
        self.results_table.setHorizontalHeaderLabels(headers)
        self.SUMMARY_FIELDS = SUMMARY_FIELDS
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
        
        self.setLayout(layout)

    def update_session_results(self, results: List[Dict]) -> None:
        """Update results from current session.
        
        Args:
            results: List of result dictionaries from processing
        """
        self.session_results = results
        if results:
            self.status_label.setVisible(False)
            self.results_table.setVisible(True)
            self._populate_table(results)
            # Enable download buttons
            self.export_excel_btn.setEnabled(True)
            self.download_reports_btn.setEnabled(True)
            self.download_pdfs_btn.setEnabled(True)
        else:
            self.status_label.setVisible(True)
            self.results_table.setVisible(False)
            self.export_excel_btn.setEnabled(False)
            self.download_reports_btn.setEnabled(False)
            self.download_pdfs_btn.setEnabled(False)

    def _populate_table(self, results: list) -> None:
        """Populate table with results matching frontend format."""
        self.results_table.setRowCount(len(results))
        
        for row, result in enumerate(results):
            col = 0
            
            # Broker Name
            broker_item = QTableWidgetItem(result.get("broker_name") or "—")
            broker_item.setForeground(Qt.GlobalColor.white)
            self.results_table.setItem(row, col, broker_item)
            col += 1
            
            # Airport Code
            airport_item = QTableWidgetItem(result.get("airport_code") or "—")
            self.results_table.setItem(row, col, airport_item)
            col += 1
            
            # Customer
            customer_item = QTableWidgetItem(result.get("customer") or "—")
            self.results_table.setItem(row, col, customer_item)
            col += 1
            
            # MAWB (formatted: XXX-XXXXXXXX)
            mawb = result.get("mawb", "")
            if len(mawb) == 11:
                mawb_formatted = f"{mawb[:3]}-{mawb[3:]}"
            else:
                mawb_formatted = mawb
            mawb_item = QTableWidgetItem(mawb_formatted)
            mawb_item.setForeground(Qt.GlobalColor.white)
            self.results_table.setItem(row, col, mawb_item)
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
            
            # Summary fields
            summary = result.get("summary", {})
            if isinstance(summary, str):
                import json
                try:
                    summary = json.loads(summary)
                except:
                    summary = {}
            
            for field in self.SUMMARY_FIELDS:
                value = summary.get(field) if isinstance(summary, dict) else None
                summary_item = QTableWidgetItem(str(value) if value is not None else "—")
                self.results_table.setItem(row, col, summary_item)
                col += 1
            
            # Template Name
            template_item = QTableWidgetItem(result.get("template_name") or "—")
            self.results_table.setItem(row, col, template_item)
            col += 1
            
            # Report (artifact URL)
            artifact_url = result.get("artifact_url")
            if artifact_url:
                report_item = QTableWidgetItem("Available")
                report_item.setForeground(Qt.GlobalColor.cyan)
                report_item.setData(Qt.ItemDataRole.UserRole, artifact_url)  # Store URL
            else:
                report_item = QTableWidgetItem("N/A")
            self.results_table.setItem(row, col, report_item)
            col += 1
        
        self.results_table.resizeColumnsToContents()

    def _on_export_excel(self) -> None:
        """Handle export Excel button click."""
        if not self.session_results:
            QMessageBox.warning(self, "No Results", "No results to export.")
            return
        
        # Get save location
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"duty_results_{timestamp}.xlsx"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Excel File",
            default_filename,
            "Excel Files (*.xlsx)"
        )
        
        if not file_path:
            return
        
        try:
            excel_data = self.duty_service.export_results_excel(self.session_results)
            with open(file_path, 'wb') as f:
                f.write(excel_data)
            QMessageBox.information(self, "Success", f"Excel file saved to:\n{file_path}")
        except Exception as exc:
            logger.error(f"Error exporting Excel: {exc}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to export Excel:\n\n{exc}")

    def _on_download_reports(self) -> None:
        """Handle download reports button click."""
        if not self.session_results:
            QMessageBox.warning(self, "No Results", "No results to download.")
            return
        
        # Get save location
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"duty_reports_{timestamp}.zip"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Reports ZIP",
            default_filename,
            "ZIP Files (*.zip)"
        )
        
        if not file_path:
            return
        
        try:
            zip_data = self.duty_service.download_reports_zip(self.session_results)
            with open(file_path, 'wb') as f:
                f.write(zip_data)
            QMessageBox.information(self, "Success", f"Reports ZIP saved to:\n{file_path}")
        except Exception as exc:
            logger.error(f"Error downloading reports: {exc}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to download reports:\n\n{exc}")

    def _on_download_pdfs(self) -> None:
        """Handle download PDFs button click."""
        if not self.session_results:
            QMessageBox.warning(self, "No Results", "No results to download.")
            return
        
        # Check if any results have PDFs
        pdf_count = 0
        for result in self.session_results:
            summary = result.get("summary", {})
            if isinstance(summary, str):
                import json
                try:
                    summary = json.loads(summary)
                except:
                    summary = {}
            
            if isinstance(summary, dict):
                # Check multiple possible keys
                pdf_url = None
                for key in ["7501 Batch PDF URL", "7501_Batch_PDF_URL", "7501BatchPDFURL", "pdf_url", "PDF URL"]:
                    value = summary.get(key)
                    if value and str(value).strip() and str(value).strip() != "N/A":
                        pdf_url = str(value).strip()
                        break
                
                # Also try case-insensitive search
                if not pdf_url:
                    for key, value in summary.items():
                        if isinstance(key, str):
                            key_lower = key.lower()
                            if ("7501" in key_lower or "pdf" in key_lower) and ("url" in key_lower or "link" in key_lower):
                                if value and str(value).strip() and str(value).strip() != "N/A":
                                    pdf_url = str(value).strip()
                                    break
                
                if pdf_url:
                    pdf_count += 1
        
        if pdf_count == 0:
            # Check if PDF section was enabled in any result
            pdf_section_enabled = False
            for result in self.session_results:
                sections = result.get("sections", {})
                if isinstance(sections, str):
                    import json
                    try:
                        sections = json.loads(sections)
                    except:
                        sections = {}
                if isinstance(sections, dict) and sections.get("download_7501_pdf"):
                    pdf_section_enabled = True
                    break
            
            if pdf_section_enabled:
                msg = (
                    "No PDFs found in the results, but PDF section was enabled.\n\n"
                    "Possible reasons:\n"
                    "- PDFs failed to download during processing\n"
                    "- PDF URLs expired\n"
                    "- Check the processing logs for PDF download errors"
                )
            else:
                msg = (
                    "No PDFs found in the results.\n\n"
                    "The 'Download 7501 PDF' section was not enabled during processing.\n\n"
                    "To get PDFs:\n"
                    "1. Go to Process tab\n"
                    "2. Enable 'Download 7501 PDF' checkbox\n"
                    "3. Process your MAWBs again"
                )
            
            QMessageBox.warning(self, "No PDFs Available", msg)
            return
        
        # Get save location
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"duty_pdfs_{timestamp}.zip"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save PDFs ZIP",
            default_filename,
            "ZIP Files (*.zip)"
        )
        
        if not file_path:
            return
        
        try:
            zip_data = self.duty_service.download_pdfs_zip(self.session_results)
            
            if len(zip_data) == 0:
                # Check if PDFs were found but failed to download
                pdf_urls_found = 0
                for result in self.session_results:
                    summary = result.get("summary", {})
                    if isinstance(summary, str):
                        import json
                        try:
                            summary = json.loads(summary)
                        except:
                            summary = {}
                    if isinstance(summary, dict):
                        for key in ["7501 Batch PDF URL", "7501_Batch_PDF_URL", "7501BatchPDFURL", "pdf_url", "PDF URL"]:
                            value = summary.get(key)
                            if value and str(value).strip() and str(value).strip() != "N/A":
                                pdf_urls_found += 1
                                break
                
                if pdf_urls_found > 0:
                    msg = (
                        f"The ZIP file is empty, but {pdf_urls_found} PDF URL(s) were found.\n\n"
                        "Possible reasons:\n"
                        "- PDF URLs have expired (signed URLs expire after 1 hour)\n"
                        "- Storage path reconstruction failed\n"
                        "- Network issues preventing download\n\n"
                        "Try processing the MAWBs again to get fresh PDF URLs, or check the application logs for detailed error messages."
                    )
                else:
                    msg = (
                        "The ZIP file is empty. No PDFs could be downloaded.\n\n"
                        "Check the application logs for details."
                    )
                
                QMessageBox.warning(self, "Empty ZIP", msg)
                return
            
            with open(file_path, 'wb') as f:
                f.write(zip_data)
            
            # Check ZIP contents
            import zipfile
            import io
            with zipfile.ZipFile(io.BytesIO(zip_data), 'r') as z:
                file_count = len(z.namelist())
            
            QMessageBox.information(
                self,
                "Success",
                f"PDFs ZIP saved to:\n{file_path}\n\n"
                f"Contains {file_count} PDF file(s)."
            )
        except Exception as exc:
            logger.error(f"Error downloading PDFs: {exc}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to download PDFs:\n\n{exc}")
