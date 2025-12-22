"""Standalone duty service layer adapted from backend service.

This service provides read-only access to brokers/formats and uses
local session storage for broker login sessions.
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

# Import from local netchb_duty modules (standalone copy)
from .netchb_duty.database_manager import NetChbDutyDatabaseManager
from .netchb_duty.models import DutyRunRequest, DutySections
from .netchb_duty.playwright_runner import NetChbDutyRunner
from .netchb_duty.storage import NetChbDutyStorageManager
from .netchb_duty.input_parser import parse_mawb_input

from .local_session_storage import LocalSessionStorage

logger = logging.getLogger(__name__)


class StandaloneDutyService:
    """Standalone duty service with local session storage."""

    def __init__(self, supabase_url: str, supabase_service_key: str) -> None:
        """Initialize standalone duty service.

        Args:
            supabase_url: Supabase project URL
            supabase_service_key: Supabase service role key
        """
        # Set environment variables for database manager
        import os
        os.environ["SUPABASE_URL"] = supabase_url
        os.environ["SUPABASE_SERVICE_ROLE_KEY"] = supabase_service_key
        
        self.db = NetChbDutyDatabaseManager()
        self._storage: Optional[NetChbDutyStorageManager] = None
        self.local_sessions = LocalSessionStorage()
        logger.info("Standalone duty service initialized")

    def _ensure_storage(self) -> NetChbDutyStorageManager:
        """Ensure storage manager is initialized."""
        if self._storage is None:
            self._storage = NetChbDutyStorageManager()
        return self._storage

    # ------------------------------------------------------------------
    # Read-only broker operations
    # ------------------------------------------------------------------
    def list_brokers(self, active_only: bool = False) -> List[Dict[str, Any]]:
        """List brokers (read-only).

        Args:
            active_only: Only return active brokers

        Returns:
            List of broker dictionaries
        """
        return self.db.list_brokers(active_only=active_only)

    def get_broker(self, broker_id: UUID) -> Optional[Dict[str, Any]]:
        """Get a broker by ID (read-only).

        Args:
            broker_id: Broker UUID

        Returns:
            Broker dictionary or None
        """
        return self.db.get_broker(broker_id)

    # ------------------------------------------------------------------
    # Read-only format operations
    # ------------------------------------------------------------------
    def list_formats(self, active_only: bool = False) -> List[Dict[str, Any]]:
        """List formats (read-only).

        Args:
            active_only: Only return active formats

        Returns:
            List of format dictionaries
        """
        return self.db.list_formats(active_only=active_only)

    def get_format(self, format_id: UUID) -> Optional[Dict[str, Any]]:
        """Get a format by ID (read-only).

        Args:
            format_id: Format UUID

        Returns:
            Format dictionary or None
        """
        return self.db.get_format(format_id)

    # ------------------------------------------------------------------
    # Results operations
    # ------------------------------------------------------------------
    def list_results(
        self,
        mawb: Optional[str] = None,
        batch_id: Optional[UUID] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """List duty results.

        Args:
            mawb: Filter by MAWB
            batch_id: Filter by batch ID
            limit: Limit results

        Returns:
            List of result dictionaries
        """
        return self.db.list_results(mawb=mawb, batch_id=batch_id, limit=limit)

    # ------------------------------------------------------------------
    # Batch operations
    # ------------------------------------------------------------------
    def create_batch(
        self,
        sections: Dict[str, bool],
        items: List[Dict[str, Any]],
        initiated_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new batch with items.

        Args:
            sections: Sections to process
            items: List of batch items (each with mawb, broker_id, format_id, etc.)
            initiated_by: User email who created the batch

        Returns:
            Created batch dictionary
        """
        from datetime import datetime, timezone
        
        # Generate batch name
        batch_count = self.db.count_batches()
        now = datetime.now(timezone.utc)
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M")
        item_count = len(items)
        batch_name = f"Batch #{batch_count + 1} - {date_str} {time_str} - {item_count} masters"
        
        # Create batch
        batch = self.db.create_batch(
            batch_name=batch_name,
            sections=sections,
            initiated_by=initiated_by,
        )
        
        if not batch:
            raise ValueError("Failed to create batch")
        
        batch_id = UUID(batch["id"])
        self.db.add_batch_items(batch_id, items)
        
        return batch

    def list_batches(
        self,
        status: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """List batches with optional filters.

        Args:
            status: Filter by status (pending, running, completed, failed, cancelled)
            limit: Limit number of results
            offset: Offset for pagination

        Returns:
            List of batch dictionaries
        """
        return self.db.list_batches(status=status, limit=limit, offset=offset)

    def get_batch_status(self, batch_id: UUID) -> Optional[Dict[str, Any]]:
        """Get batch status with item counts.

        Args:
            batch_id: Batch UUID

        Returns:
            Batch status dictionary with counts and items, or None
        """
        batch = self.db.get_batch(batch_id)
        if not batch:
            return None
        
        items = self.db.get_batch_items(batch_id)
        
        item_count = len(items)
        pending_count = sum(1 for item in items if item.get("status") == "pending")
        running_count = sum(1 for item in items if item.get("status") == "running")
        success_count = sum(1 for item in items if item.get("status") == "success")
        failed_count = sum(1 for item in items if item.get("status") == "failed")
        cancelled_count = sum(1 for item in items if item.get("status") == "cancelled")
        
        return {
            "batch": batch,
            "item_count": item_count,
            "pending_count": pending_count,
            "running_count": running_count,
            "success_count": success_count,
            "failed_count": failed_count,
            "cancelled_count": cancelled_count,
            "items": items,
        }

    def start_batch_processing(self, batch_id: UUID) -> bool:
        """Start processing a batch in background.

        Args:
            batch_id: Batch UUID

        Returns:
            True if started successfully
        """
        # This will be implemented to start async batch processing
        # For now, return True and log
        logger.info(f"Batch {batch_id} start requested (background processing not yet implemented)")
        return True

    def cancel_batch(self, batch_id: UUID) -> bool:
        """Cancel a batch.

        Args:
            batch_id: Batch UUID

        Returns:
            True if cancelled successfully
        """
        result = self.db.cancel_batch(batch_id)
        return result is not None

    # ------------------------------------------------------------------
    # Duty processing with local session storage
    # ------------------------------------------------------------------
    async def process_mawb(
        self,
        mawb: str,
        broker_id: UUID,
        format_id: UUID,
        sections: Dict[str, bool],
        on_progress: Optional[callable] = None,
        on_log: Optional[callable] = None,
        airport_code: Optional[str] = None,
        customer: Optional[str] = None,
        checkbook_hawbs: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Process a single MAWB.

        Args:
            mawb: MAWB number (11 digits)
            broker_id: Broker UUID
            format_id: Format UUID
            sections: Sections to process (ams, entries, custom, download_7501_pdf)
            on_progress: Callback for progress updates (message, percentage)
            on_log: Callback for log messages
            airport_code: Optional airport code for file naming
            customer: Optional customer name for file naming
            checkbook_hawbs: Optional checkbook HAWBs for verification

        Returns:
            Result dictionary with summary, logs, etc.
        """
        # Get broker and format
        broker = self.db.get_broker(broker_id)
        if not broker:
            raise ValueError(f"Broker not found: {broker_id}")
        
        format_record = self.db.get_format(format_id)
        if not format_record:
            raise ValueError(f"Format not found: {format_id}")

        if on_log:
            on_log("Starting MAWB processing...")

        # Load local session if available
        local_session = self.local_sessions.load_session(broker_id)
        
        try:
            # Acquire Playwright resource slot
            from utils.resource_coordinator import get_resource_coordinator
            coordinator = get_resource_coordinator()
            
            async with coordinator.playwright_context_async(job_id=mawb, job_type="duty"), \
                       coordinator.long_operation_context_async(job_id=mawb, job_type="duty"):
                async with NetChbDutyRunner() as runner:
                    # Add log callback if provided
                    if on_log:
                        original_log = runner.log
                        def logged_log(message: str):
                            original_log(message)
                            on_log(message)
                        runner.log = logged_log
                    
                    # Session management with local storage
                    session_reused = False
                    if local_session:
                        if on_log:
                            on_log("Attempting to reuse saved session...")
                        try:
                            await runner.load_session_state(local_session)
                            is_valid = await runner.is_session_valid()
                            if is_valid:
                                session_reused = True
                                if on_log:
                                    on_log("✅ Session reused successfully")
                            else:
                                if on_log:
                                    on_log("⚠️ Saved session is invalid - will login fresh")
                        except Exception as exc:
                            if on_log:
                                on_log(f"⚠️ Error loading session: {exc} - will login fresh")
                    
                    # Login if session wasn't reused
                    if not session_reused:
                        if on_log:
                            on_log("Starting login process...")
                        otp_uri = broker.get("otp_uri") if broker.get("is_authentication_required") else None
                        await runner.login(broker["username"], broker["password"], otp_uri=otp_uri)
                        if on_log:
                            on_log("✅ Login completed successfully")
                        
                        # Save new session locally
                        try:
                            new_session_state = await runner.save_session_state()
                            self.local_sessions.save_session(broker_id, new_session_state)
                            if on_log:
                                on_log("✅ Session saved locally for future reuse")
                        except Exception as exc:
                            if on_log:
                                on_log(f"⚠️ Failed to save session: {exc}")
                    
                    # Process MAWB
                    if on_progress:
                        on_progress("Processing MAWB...", 50)
                    
                    duty_result = await runner.process_mawb(
                        mawb,
                        sections=sections,
                        format_identifier=format_record["template_identifier"],
                        format_record=format_record,
                        airport_code=airport_code,
                        customer=customer,
                        checkbook_hawbs=checkbook_hawbs,
                    )
                    
                    # Handle Excel file
                    artifact_path = artifact_url = None
                    if duty_result.summary.get("excel_storage_path") and duty_result.summary.get("excel_download_url"):
                        artifact_path = duty_result.summary.get("excel_storage_path")
                        artifact_url = duty_result.summary.get("excel_download_url")
                    elif duty_result.download_path:
                        storage = self._ensure_storage()
                        template_name = format_record.get("name")
                        artifact_path, artifact_url = storage.upload_excel(
                            duty_result.download_path,
                            duty_result.mawb,
                            airport_code=airport_code,
                            customer=customer,
                            template_name=template_name,
                        )
                        try:
                            duty_result.download_path.unlink()
                        except Exception:
                            pass
                    
                    # Save result to database
                    if on_progress:
                        on_progress("Saving results...", 90)
                    
                    result = self.db.upsert_result(
                        mawb=duty_result.mawb,
                        broker_id=broker_id,
                        format_id=format_id,
                        status="success",
                        sections=sections,
                        summary=duty_result.summary,
                        artifact_path=artifact_path,
                        artifact_url=artifact_url,
                        airport_code=airport_code,  # Save for file naming
                        customer=customer,  # Save for file naming
                    )
                    
                    if on_progress:
                        on_progress("Completed", 100)
                    
                    # Extract PDF path from summary
                    pdf_storage_path = None
                    pdf_url = None
                    if isinstance(duty_result.summary, dict):
                        pdf_url = duty_result.summary.get("7501 Batch PDF URL")
                        # Try to extract storage path from URL or reconstruct it
                        if pdf_url and pdf_url != "N/A" and pdf_url.strip():
                            # If it's a signed URL, try to extract the key from it
                            # Or reconstruct the path from MAWB, airport_code, customer
                            # For now, we'll reconstruct it
                            mawb_clean = duty_result.mawb.replace("/", "-").replace("\\", "-").replace(" ", "").replace("-", "")
                            if len(mawb_clean) == 11:
                                formatted_mawb = f"{mawb_clean[:3]}-{mawb_clean[3:]}"
                            else:
                                formatted_mawb = mawb_clean
                            
                            # Reconstruct path (will be used if URL doesn't work)
                            parts = [formatted_mawb]
                            # Note: airport_code and customer might not be available here
                            # They'll be added from parsed input in the GUI
                            filename = " ".join(parts) + ".pdf"
                            storage = self._ensure_storage()
                            pdf_storage_path = f"{storage.prefix}/7501-batch-pdfs/{filename}"
                    
                    # Build comprehensive result dict
                    result_dict = {
                        "mawb": duty_result.mawb,
                        "broker_id": str(broker_id),
                        "format_id": str(format_id),
                        "broker_name": broker.get("name"),
                        "template_name": format_record.get("name"),
                        "status": "success",
                        "summary": duty_result.summary,
                        "artifact_path": artifact_path,
                        "artifact_url": artifact_url,
                        "pdf_url": pdf_url,
                        "pdf_path": pdf_storage_path,
                        "airport_code": airport_code,  # Include for file naming
                        "customer": customer,  # Include for file naming
                    }
                    
                    return {
                        "success": True,
                        "result": result_dict,
                        "summary": duty_result.summary,
                        "logs": duty_result.logs,
                        "artifact_url": artifact_url,
                        "mawb": duty_result.mawb,
                        "broker_name": broker.get("name"),
                        "template_name": format_record.get("name"),
                        "status": "success",
                        "artifact_path": artifact_path,
                        "pdf_url": pdf_url,
                        "pdf_path": pdf_storage_path,
                        "airport_code": airport_code,  # Include for file naming
                        "customer": customer,  # Include for file naming
                    }
        except Exception as exc:
            error_message = str(exc)
            logger.error(f"Error processing MAWB {mawb}: {error_message}", exc_info=True)
            
            # Save failed result
            self.db.upsert_result(
                mawb=mawb,
                broker_id=broker_id,
                format_id=format_id,
                status="failed",
                sections=sections,
                error_message=error_message,
            )
            
            return {
                "success": False,
                "error": error_message,
                "status": "failed",
                "mawb": mawb,
                "result": {
                    "mawb": mawb,
                    "status": "failed",
                    "error_message": error_message,
                }
            }

    # ------------------------------------------------------------------
    # Download and Export Methods
    # ------------------------------------------------------------------
    def export_results_excel(self, results: List[Dict[str, Any]]) -> bytes:
        """Export results as Excel file with all summary fields.
        
        Args:
            results: List of result dictionaries
            
        Returns:
            Excel file as bytes
        """
        import io
        from openpyxl import Workbook
        
        # Create Excel workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Duty Results"
        
        # Define headers
        summary_fields = [
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
        
        # Currency fields
        currency_fields = {
            "AMS Duty",
            "7501 Duty",
            "Report Duty",
            "Total Informal Duty",
            "Complete Total Duty",
        }
        
        def format_currency(value: any) -> str:
            """Format currency values with $ sign."""
            if value is None or value == "" or value == "N/A":
                return ""
            
            def parse_val(val):
                if isinstance(val, (int, float)):
                    return float(val)
                val_str = str(val).replace("$", "").replace(",", "").strip()
                try:
                    return float(val_str)
                except (ValueError, AttributeError):
                    return 0.0
            
            num_value = parse_val(value)
            if num_value == 0 or num_value is None:
                return "$0.00"
            return f"${num_value:,.2f}"
        
        def format_display_value(field: str, value: any) -> str:
            """Format display value based on field type."""
            if value is None or value == "":
                return ""
            if field in currency_fields:
                return format_currency(value)
            return str(value)
        
        def format_mawb(mawb: str) -> str:
            """Format MAWB as xxx-xxxxxxxx."""
            if not mawb:
                return ""
            digits = "".join(c for c in str(mawb) if c.isdigit())
            if len(digits) == 11:
                return f"{digits[:3]}-{digits[3:]}"
            return mawb
        
        # Headers
        headers = [
            "Airport Code",
            "Customer",
            "Broker Name",
            "Checkbook HAWBs",
            "MAWB",
        ] + summary_fields + [
            "Verification",
            "Template Name",
        ]
        
        ws.append(headers)
        
        # Add data rows
        for result in results:
            # Get result dict (might be nested in 'result' key)
            result_dict = result.get("result", result) if isinstance(result, dict) else result
            
            summary = result_dict.get("summary", {})
            if isinstance(summary, str):
                import json
                try:
                    summary = json.loads(summary)
                except Exception:
                    summary = {}
            
            # Simple verification
            verification_msg = "Verified" if result_dict.get("status") == "success" else "Failed"
            
            # Row
            mawb_raw = result_dict.get("mawb", "")
            row = [
                result_dict.get("airport_code") or "",
                result_dict.get("customer") or "",
                result_dict.get("broker_name") or "",
                summary.get("Checkbook HAWBs") or "",
                format_mawb(mawb_raw),
            ]
            
            # Add summary fields
            for field in summary_fields:
                value = summary.get(field, "")
                row.append(format_display_value(field, value))
            
            # Add verification and template
            row.append(verification_msg)
            row.append(result_dict.get("template_name") or "")
            
            ws.append(row)
        
        # Save to bytes
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return output.read()

    def download_file_from_s3(self, storage_path: str) -> bytes:
        """Download a file from S3 storage.
        
        Args:
            storage_path: S3 key/path to file
            
        Returns:
            File contents as bytes
        """
        storage = self._ensure_storage()
        return storage.download_file(storage_path)

    def download_reports_zip(self, results: List[Dict[str, Any]]) -> bytes:
        """Download all Excel reports as a ZIP file.
        
        Args:
            results: List of result dictionaries
            
        Returns:
            ZIP file as bytes
        """
        import io
        import zipfile
        
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            storage = self._ensure_storage()
            
            for result in results:
                result_dict = result.get("result", result) if isinstance(result, dict) else result
                artifact_path = result_dict.get("artifact_path")
                
                if not artifact_path:
                    continue
                
                try:
                    # Download file from S3
                    file_data = storage.download_file(artifact_path)
                    
                    # Generate filename
                    mawb = result_dict.get("mawb", "")
                    airport_code = result_dict.get("airport_code", "")
                    customer = result_dict.get("customer", "")
                    
                    # Format MAWB
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
                    filename = " ".join(parts) + ".xlsx"
                    
                    zip_file.writestr(filename, file_data)
                except Exception as exc:
                    logger.warning(f"Failed to download report for {result_dict.get('mawb', 'unknown')}: {exc}")
                    continue
        
        zip_buffer.seek(0)
        return zip_buffer.read()

    def download_pdfs_zip(self, results: List[Dict[str, Any]]) -> bytes:
        """Download all 7501 PDFs as a ZIP file.
        
        Args:
            results: List of result dictionaries
            
        Returns:
            ZIP file as bytes
        """
        import io
        import zipfile
        import urllib.parse
        
        zip_buffer = io.BytesIO()
        pdfs_found = 0
        pdfs_downloaded = 0
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            storage = self._ensure_storage()
            
            for result in results:
                result_dict = result.get("result", result) if isinstance(result, dict) else result
                
                # Get PDF URL from summary
                summary = result_dict.get("summary", {})
                if isinstance(summary, str):
                    import json
                    try:
                        summary = json.loads(summary)
                    except:
                        summary = {}
                
                # Try multiple possible keys (like backend does)
                pdf_url = None
                if isinstance(summary, dict):
                    possible_keys = [
                        "7501 Batch PDF URL",
                        "7501_Batch_PDF_URL",
                        "7501BatchPDFURL",
                        "pdf_url",
                        "PDF URL"
                    ]
                    
                    for key in possible_keys:
                        raw_value = summary.get(key)
                        if raw_value is not None:
                            value_str = str(raw_value).strip()
                            if value_str and value_str != "N/A":
                                pdf_url = value_str
                                logger.debug(f"Found PDF URL using key '{key}' for MAWB {result_dict.get('mawb', 'unknown')}")
                                break
                    
                    # If not found, try case-insensitive search
                    if not pdf_url:
                        for key, value in summary.items():
                            if isinstance(key, str):
                                key_lower = key.lower()
                                if ("7501" in key_lower or "pdf" in key_lower) and ("url" in key_lower or "link" in key_lower):
                                    if value is not None:
                                        value_str = str(value).strip()
                                        if value_str and value_str != "N/A":
                                            pdf_url = value_str
                                            logger.debug(f"Found PDF URL using case-insensitive match: key='{key}'")
                                            break
                
                if not pdf_url:
                    logger.debug(f"No PDF URL found for MAWB {result_dict.get('mawb', 'unknown')}. Summary keys: {list(summary.keys()) if isinstance(summary, dict) else 'N/A'}")
                    continue
                
                pdfs_found += 1
                
                # Get MAWB, airport_code, customer for filename
                mawb = result_dict.get("mawb", "")
                airport_code = result_dict.get("airport_code", "")
                customer = result_dict.get("customer", "")
                
                try:
                    # Try to download from signed URL first
                    file_data = None
                    try:
                        import urllib.request
                        logger.debug(f"Attempting to download PDF from URL for MAWB {mawb}")
                        with urllib.request.urlopen(pdf_url, timeout=30) as response:
                            file_data = response.read()
                            if file_data:
                                logger.debug(f"Successfully downloaded PDF from URL for MAWB {mawb} ({len(file_data)} bytes)")
                    except Exception as url_exc:
                        logger.warning(f"Failed to download PDF from URL for MAWB {mawb}: {url_exc}. Trying storage path...")
                        # Fallback: Reconstruct storage path and download from S3
                        # IMPORTANT: PDFs are now uploaded with airport_code and customer (if provided)
                        # So try the full path first, then fallback to MAWB-only
                        mawb_clean = mawb.replace("/", "-").replace("\\", "-").replace(" ", "").replace("-", "")
                        if len(mawb_clean) == 11:
                            formatted_mawb = f"{mawb_clean[:3]}-{mawb_clean[3:]}"
                        else:
                            formatted_mawb = mawb_clean
                        
                        # Try full path with airport_code and customer first (new behavior)
                        if airport_code or customer:
                            parts = [formatted_mawb]
                            if airport_code:
                                safe_airport = airport_code.strip().replace("/", "-").replace("\\", "-")
                                if safe_airport:
                                    parts.append(safe_airport)
                            if customer:
                                safe_customer = customer.strip().replace("/", "-").replace("\\", "-")
                                if safe_customer:
                                    parts.append(safe_customer)
                            
                            filename = " ".join(parts) + ".pdf"
                            full_path = f"{storage.prefix}/7501-batch-pdfs/{filename}"
                            logger.debug(f"Attempting to download PDF from storage path (full path): {full_path}")
                            try:
                                file_data = storage.download_file(full_path)
                                if file_data:
                                    logger.debug(f"Successfully downloaded PDF from full path for MAWB {mawb} ({len(file_data)} bytes)")
                            except (FileNotFoundError, RuntimeError):
                                # Fallback to MAWB-only path (for old files or if upload failed)
                                mawb_only_path = f"{storage.prefix}/7501-batch-pdfs/{formatted_mawb}.pdf"
                                logger.debug(f"Trying fallback path (MAWB only): {mawb_only_path}")
                                try:
                                    file_data = storage.download_file(mawb_only_path)
                                    if file_data:
                                        logger.debug(f"Successfully downloaded PDF from MAWB-only path for MAWB {mawb}")
                                except Exception as fallback_exc:
                                    logger.warning(f"Failed to download PDF from both paths for MAWB {mawb}: {fallback_exc}")
                                    raise
                        else:
                            # No airport_code/customer, try MAWB-only
                            mawb_only_path = f"{storage.prefix}/7501-batch-pdfs/{formatted_mawb}.pdf"
                            logger.debug(f"Attempting to download PDF from storage path (MAWB only): {mawb_only_path}")
                            try:
                                file_data = storage.download_file(mawb_only_path)
                                if file_data:
                                    logger.debug(f"Successfully downloaded PDF from MAWB-only path for MAWB {mawb} ({len(file_data)} bytes)")
                            except Exception as storage_exc:
                                logger.warning(f"Failed to download PDF from storage for MAWB {mawb}: {storage_exc}")
                                raise
                    
                    if not file_data or len(file_data) == 0:
                        logger.warning(f"No file data retrieved for MAWB {mawb}")
                        continue
                    
                    # Generate filename for ZIP
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
                    
                    zip_file.writestr(filename, file_data)
                    pdfs_downloaded += 1
                    logger.info(f"Added PDF to ZIP: {filename} ({len(file_data)} bytes)")
                except Exception as exc:
                    logger.error(f"Failed to download PDF for MAWB {mawb}: {exc}", exc_info=True)
                    continue
        
        zip_buffer.seek(0)
        logger.info(f"PDF ZIP creation complete: {pdfs_found} PDFs found, {pdfs_downloaded} PDFs downloaded")
        if pdfs_downloaded == 0:
            if pdfs_found == 0:
                logger.warning("No PDFs found in results - make sure 'Download 7501 PDF' section was enabled during processing")
            else:
                logger.warning(f"Found {pdfs_found} PDFs but failed to download any - check logs for details")
        return zip_buffer.read()


