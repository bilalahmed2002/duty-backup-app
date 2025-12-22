"""Supabase data access for NetCHB duty service."""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from supabase import Client, create_client

logger = logging.getLogger(__name__)


class NetChbDutyDatabaseManager:
    """Encapsulates Supabase operations for NetCHB brokers, formats, and results."""

    def __init__(self) -> None:
        self.supabase: Client = self._get_supabase_client()
        self.brokers_table = os.getenv("NETCHB_BROKERS_TABLE", "netchb_brokers")
        self.formats_table = os.getenv("NETCHB_FORMATS_TABLE", "netchb_formats")
        self.results_table = os.getenv("NETCHB_RESULTS_TABLE", "netchb_duty_results")
        self.batches_table = os.getenv("NETCHB_BATCHES_TABLE", "netchb_duty_batches")
        self.batch_items_table = os.getenv("NETCHB_BATCH_ITEMS_TABLE", "netchb_duty_batch_items")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _get_supabase_client(self) -> Client:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        if not supabase_url or not supabase_key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be configured")
        return create_client(supabase_url, supabase_key)

    def _execute(self, query, error_message: str, default=None):
        """
        Execute database query with retry logic for temporary failures.
        
        Handles "Resource temporarily unavailable" errors by retrying with exponential backoff.
        """
        import time
        max_retries = 3
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                response = query.execute()
                data = getattr(response, "data", None)
                if data is None and isinstance(response, dict):
                    data = response.get("data", response)
                return data or default
            except Exception as exc:
                last_exception = exc
                error_str = str(exc)
                error_type = type(exc).__name__
                
                # Check if it's a "Resource temporarily unavailable" error
                is_resource_error = (
                    "Resource temporarily unavailable" in error_str or
                    "Errno 35" in error_str or
                    "temporarily unavailable" in error_str.lower() or
                    "EAGAIN" in error_str or
                    "EWOULDBLOCK" in error_str
                )
                
                # Check for connection/disconnection errors
                is_connection_error = (
                    "Server disconnected" in error_str or
                    "RemoteProtocolError" in error_type or
                    "ConnectionError" in error_type or
                    "disconnected" in error_str.lower() or
                    "connection reset" in error_str.lower() or
                    "connection closed" in error_str.lower()
                )
                
                if (is_resource_error or is_connection_error) and attempt < max_retries - 1:
                    # Exponential backoff: 0.5s, 1s, 2s
                    wait_time = 0.5 * (2 ** attempt)
                    error_type_name = "Connection error" if is_connection_error else "Resource temporarily unavailable"
                    logger.warning(f"{error_message} - {error_type_name} (attempt {attempt + 1}/{max_retries}). Retrying in {wait_time:.1f}s...")
                    
                    # For connection errors, recreate the Supabase client to get a fresh connection
                    if is_connection_error:
                        try:
                            self.supabase = self._get_supabase_client()
                            logger.info("Recreated Supabase client after connection error")
                        except Exception as reconnect_exc:
                            logger.error(f"Failed to recreate Supabase client: {reconnect_exc}")
                    
                    time.sleep(wait_time)
                    continue
                else:
                    # Not a retryable error, or all retries exhausted
                    logger.error("%s: %s", error_message, exc)
                    raise
        
        # All retries exhausted
        logger.error(f"{error_message} - Failed after {max_retries} attempts: {last_exception}")
        return default

    # ------------------------------------------------------------------
    # Brokers
    # ------------------------------------------------------------------
    def list_brokers(self, active_only: bool = False) -> List[Dict[str, Any]]:
        query = self.supabase.table(self.brokers_table).select("*").order("name")
        if active_only:
            query = query.eq("is_active", True)
        return self._execute(query, "Failed to list NetCHB brokers", default=[])

    def get_broker(self, broker_id: UUID) -> Optional[Dict[str, Any]]:
        query = (
            self.supabase.table(self.brokers_table)
            .select("*")
            .eq("id", str(broker_id))
            .limit(1)
        )
        records = self._execute(query, f"Failed to fetch NetCHB broker {broker_id}", default=[])
        return records[0] if records else None

    def update_broker_session(
        self,
        broker_id: UUID,
        session_state: Optional[Dict[str, Any]],
        session_hint_expires_at: Optional[datetime],
        session_last_validated_at: Optional[datetime],
    ) -> Optional[Dict[str, Any]]:
        """
        Update broker's session state, hint expiry, and validation timestamp.
        
        Args:
            broker_id: Broker UUID
            session_state: Playwright storage state (cookies + storage)
            session_hint_expires_at: Hint timestamp calculated from cookie expiry - 5 minutes
            session_last_validated_at: Timestamp when session was last validated
            
        Returns:
            Updated broker record or None
        """
        payload: Dict[str, Any] = {
            "session_state": session_state,
        }
        if session_hint_expires_at:
            payload["session_hint_expires_at"] = session_hint_expires_at.isoformat()
        else:
            payload["session_hint_expires_at"] = None
            
        if session_last_validated_at:
            payload["session_last_validated_at"] = session_last_validated_at.isoformat()
        else:
            payload["session_last_validated_at"] = None
            
        query = (
            self.supabase.table(self.brokers_table)
            .update(payload, returning="representation")
            .eq("id", str(broker_id))
        )
        records = self._execute(
            query,
            f"Failed to update NetCHB broker session {broker_id}",
            default=[],
        )
        return records[0] if records else None

    def clear_broker_session(self, broker_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Clear broker's session state (force re-login on next run).
        
        Args:
            broker_id: Broker UUID
            
        Returns:
            Updated broker record or None
        """
        return self.update_broker_session(broker_id, None, None, None)

    def create_broker(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        query = self.supabase.table(self.brokers_table).insert(
            payload,
            returning="representation",
        )
        records = self._execute(query, "Failed to create NetCHB broker", default=[])
        return records[0] if records else None

    def update_broker(self, broker_id: UUID, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        query = (
            self.supabase.table(self.brokers_table)
            .update(payload, returning="representation")
            .eq("id", str(broker_id))
        )
        records = self._execute(query, f"Failed to update NetCHB broker {broker_id}", default=[])
        return records[0] if records else None

    def delete_broker(self, broker_id: UUID) -> bool:
        query = self.supabase.table(self.brokers_table).delete().eq("id", str(broker_id))
        result = self._execute(query, f"Failed to delete NetCHB broker {broker_id}")
        return bool(result) or result is None

    # ------------------------------------------------------------------
    # Formats
    # ------------------------------------------------------------------
    def list_formats(self, active_only: bool = False) -> List[Dict[str, Any]]:
        query = self.supabase.table(self.formats_table).select("*").order("name")
        if active_only:
            query = query.eq("is_active", True)
        return self._execute(query, "Failed to list NetCHB formats", default=[])

    def get_format(self, format_id: UUID) -> Optional[Dict[str, Any]]:
        query = (
            self.supabase.table(self.formats_table)
            .select("*")
            .eq("id", str(format_id))
            .limit(1)
        )
        records = self._execute(query, f"Failed to fetch NetCHB format {format_id}", default=[])
        return records[0] if records else None

    def create_format(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        query = self.supabase.table(self.formats_table).insert(
            payload,
            returning="representation",
        )
        records = self._execute(query, "Failed to create NetCHB format", default=[])
        return records[0] if records else None

    def update_format(self, format_id: UUID, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        query = (
            self.supabase.table(self.formats_table)
            .update(payload, returning="representation")
            .eq("id", str(format_id))
        )
        records = self._execute(query, f"Failed to update NetCHB format {format_id}", default=[])
        return records[0] if records else None

    def delete_format(self, format_id: UUID) -> bool:
        query = self.supabase.table(self.formats_table).delete().eq("id", str(format_id))
        result = self._execute(query, f"Failed to delete NetCHB format {format_id}")
        return bool(result) or result is None

    # ------------------------------------------------------------------
    # Results
    # ------------------------------------------------------------------
    def list_results(
        self,
        mawb: Optional[str] = None,
        batch_id: Optional[UUID] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        query = self.supabase.table(self.results_table).select("*").order("updated_at", desc=True)
        if mawb:
            query = query.eq("mawb", mawb)
        if batch_id:
            query = query.eq("batch_id", str(batch_id))
        if limit:
            query = query.limit(limit)
        return self._execute(query, "Failed to list NetCHB duty results", default=[])

    def get_result(self, result_id: UUID) -> Optional[Dict[str, Any]]:
        """Get a single result by ID."""
        query = (
            self.supabase.table(self.results_table)
            .select("*")
            .eq("id", str(result_id))
            .limit(1)
        )
        records = self._execute(query, f"Failed to fetch result {result_id}", default=[])
        return records[0] if records else None

    def upsert_result(
        self,
        *,
        mawb: str,
        broker_id: UUID,
        format_id: UUID,
        status: str,
        sections: Optional[Dict[str, bool]] = None,
        summary: Optional[Dict[str, Any]] = None,
        artifact_path: Optional[str] = None,
        artifact_url: Optional[str] = None,
        error_message: Optional[str] = None,
        broker_name: Optional[str] = None,
        airport_code: Optional[str] = None,
        customer: Optional[str] = None,
        batch_id: Optional[UUID] = None,
        template_name: Optional[str] = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
    ) -> Optional[Dict[str, Any]]:
        payload: Dict[str, Any] = {
            "mawb": mawb,
            "broker_id": str(broker_id),
            "format_id": str(format_id),
            "status": status,
            "sections": sections,
            "summary": summary,
            "artifact_path": artifact_path,
            "artifact_url": artifact_url,
            "error_message": error_message,
        }
        if broker_name:
            payload["broker_name"] = broker_name
        if airport_code:
            payload["airport_code"] = airport_code
        if customer:
            payload["customer"] = customer
        if batch_id:
            payload["batch_id"] = str(batch_id)
        if template_name:
            payload["template_name"] = template_name
        if started_at:
            payload["started_at"] = started_at.isoformat()
        if completed_at:
            payload["completed_at"] = completed_at.isoformat()

        # Debug: Log summary payload before upsert
        if summary:
            duty_value = summary.get("7501 Duty") if isinstance(summary, dict) else None
            logger.debug(f"💾 DATABASE UPSERT - 7501 Duty in payload: '{duty_value}'")
            logger.debug(f"💾 DATABASE UPSERT - Summary type: {type(summary)}, Summary keys: {list(summary.keys()) if isinstance(summary, dict) else 'N/A'}")
        
        query = self.supabase.table(self.results_table).upsert(
            payload,
            on_conflict="mawb,broker_id,format_id",
            returning="representation",
        )
        records = self._execute(query, f"Failed to upsert NetCHB result {mawb}", default=[])
        
        # Debug: Log what was returned from database
        if records and records[0]:
            returned_summary = records[0].get("summary")
            if returned_summary:
                if isinstance(returned_summary, str):
                    import json
                    try:
                        returned_summary = json.loads(returned_summary)
                    except:
                        pass
                duty_value = returned_summary.get("7501 Duty") if isinstance(returned_summary, dict) else None
                logger.debug(f"💾 DATABASE RETURNED - 7501 Duty: '{duty_value}'")
        
        return records[0] if records else None

    def update_result_status(
        self,
        *,
        mawb: str,
        broker_id: UUID,
        format_id: UUID,
        status: str,
        error_message: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        payload: Dict[str, Any] = {
            "status": status,
            "error_message": error_message,
        }
        query = (
            self.supabase.table(self.results_table)
            .update(payload, returning="representation")
            .eq("mawb", mawb)
            .eq("broker_id", str(broker_id))
            .eq("format_id", str(format_id))
        )
        records = self._execute(
            query,
            f"Failed to update NetCHB result status for {mawb}",
            default=[],
        )
        return records[0] if records else None

    # ------------------------------------------------------------------
    # Batches
    # ------------------------------------------------------------------
    def create_batch(
        self,
        *,
        batch_name: str,
        sections: Dict[str, bool],
        initiated_by: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Create a new batch (no broker_id/format_id - these are per item)."""
        payload: Dict[str, Any] = {
            "batch_name": batch_name,
            "sections": sections,
            "status": "pending",
        }
        if initiated_by:
            payload["initiated_by"] = initiated_by
        
        query = self.supabase.table(self.batches_table).insert(
            payload,
            returning="representation",
        )
        records = self._execute(query, "Failed to create batch", default=[])
        return records[0] if records else None

    def get_batch(self, batch_id: UUID) -> Optional[Dict[str, Any]]:
        """Get batch by ID."""
        query = (
            self.supabase.table(self.batches_table)
            .select("*")
            .eq("id", str(batch_id))
            .limit(1)
        )
        records = self._execute(query, f"Failed to fetch batch {batch_id}", default=[])
        return records[0] if records else None

    def list_batches(
        self,
        status: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """List batches with optional filters and pagination."""
        query = self.supabase.table(self.batches_table).select("*").order("created_at", desc=True)
        if status:
            query = query.eq("status", status)
        if offset:
            query = query.range(offset, offset + (limit or 100) - 1)
        elif limit:
            query = query.limit(limit)
        return self._execute(query, "Failed to list batches", default=[])

    def count_batches(self) -> int:
        """
        Count total number of batches efficiently using Supabase count feature.
        Used for generating sequential batch names.
        """
        try:
            # Use count="exact" with head=True to get only the count without fetching data
            query = self.supabase.table(self.batches_table).select("*", count="exact", head=True)
            response = query.execute()
            # Supabase returns count in response.count when count="exact" is used
            return response.count if hasattr(response, 'count') and response.count is not None else 0
        except Exception as exc:
            # Fallback: if count feature fails, fetch only id field and count in Python
            logger.warning(f"Failed to get batch count efficiently: {exc}, falling back to fetching IDs")
            query = self.supabase.table(self.batches_table).select("id")
            records = self._execute(query, "Failed to count batches", default=[])
            return len(records)

    def update_batch_status(
        self,
        batch_id: UUID,
        status: str,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        actual_time_seconds: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """Update batch status and timestamps."""
        payload: Dict[str, Any] = {"status": status}
        if started_at:
            payload["started_at"] = started_at.isoformat()
        if completed_at:
            payload["completed_at"] = completed_at.isoformat()
        if actual_time_seconds is not None:
            payload["actual_time_seconds"] = actual_time_seconds
        
        query = (
            self.supabase.table(self.batches_table)
            .update(payload, returning="representation")
            .eq("id", str(batch_id))
        )
        records = self._execute(query, f"Failed to update batch {batch_id}", default=[])
        return records[0] if records else None

    def cancel_batch(self, batch_id: UUID) -> Optional[Dict[str, Any]]:
        """Mark batch as cancelled."""
        return self.update_batch_status(batch_id, "cancelled")

    def add_batch_items(
        self,
        batch_id: UUID,
        items: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Add items to a batch (each item must have broker_id and format_id)."""
        # Get current max position to continue from
        existing_items = self.get_batch_items(batch_id)
        max_position = max((item.get("position") or 0 for item in existing_items), default=0)
        
        # Get set of existing MAWBs to filter duplicates
        existing_mawbs = {item["mawb"] for item in existing_items}
        
        # Filter out duplicates - only keep items with MAWBs that don't already exist
        new_items = [item for item in items if item["mawb"] not in existing_mawbs]
        
        # If all items are duplicates, return empty list
        if not new_items:
            return []
        
        payloads = []
        for idx, item in enumerate(new_items):
            payload: Dict[str, Any] = {
                "batch_id": str(batch_id),
                "mawb": item["mawb"],
                "status": "pending",
                "position": max_position + idx + 1,  # Continue from existing max
                "broker_id": str(item["broker_id"]),  # Required per item
                "format_id": str(item["format_id"]),  # Required per item
            }
            if item.get("airport_code"):
                payload["airport_code"] = item["airport_code"]
            if item.get("customer"):
                payload["customer"] = item["customer"]
            # Save checkbook_hawbs if it exists (even if empty string or "0")
            if "checkbook_hawbs" in item and item["checkbook_hawbs"] is not None:
                payload["checkbook_hawbs"] = item["checkbook_hawbs"]
            payloads.append(payload)
        
        query = self.supabase.table(self.batch_items_table).insert(
            payloads,
            returning="representation",
        )
        records = self._execute(query, f"Failed to add items to batch {batch_id}", default=[])
        return records

    def get_batch_items(self, batch_id: UUID) -> List[Dict[str, Any]]:
        """Get all items for a batch."""
        query = (
            self.supabase.table(self.batch_items_table)
            .select("*")
            .eq("batch_id", str(batch_id))
            .order("position")
        )
        return self._execute(query, f"Failed to get batch items for {batch_id}", default=[])

    def get_batch_item(self, item_id: UUID) -> Optional[Dict[str, Any]]:
        """Get a single batch item by ID."""
        query = (
            self.supabase.table(self.batch_items_table)
            .select("*")
            .eq("id", str(item_id))
            .limit(1)
        )
        records = self._execute(query, f"Failed to get batch item {item_id}", default=[])
        return records[0] if records else None

    def update_batch_item_status(
        self,
        item_id: UUID,
        status: str,
        result_id: Optional[UUID] = None,
        logs: Optional[List[str]] = None,
        processing_time_seconds: Optional[int] = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
    ) -> Optional[Dict[str, Any]]:
        """Update batch item status, logs, timing, and link to result."""
        payload: Dict[str, Any] = {"status": status}
        if result_id:
            payload["result_id"] = str(result_id)
        if logs is not None:
            payload["logs"] = logs
        if processing_time_seconds is not None:
            payload["processing_time_seconds"] = processing_time_seconds
        if started_at:
            payload["started_at"] = started_at.isoformat()
        if completed_at:
            payload["completed_at"] = completed_at.isoformat()
        
        query = (
            self.supabase.table(self.batch_items_table)
            .update(payload, returning="representation")
            .eq("id", str(item_id))
        )
        records = self._execute(query, f"Failed to update batch item {item_id}", default=[])
        return records[0] if records else None

    def cancel_batch_item(self, item_id: UUID) -> Optional[Dict[str, Any]]:
        """Mark batch item as cancelled."""
        return self.update_batch_item_status(item_id, "cancelled")

    def get_batch_logs(self, batch_id: UUID) -> List[Dict[str, Any]]:
        """Get logs for all items in a batch."""
        items = self.get_batch_items(batch_id)
        logs_data = []
        for item in items:
            item_logs = item.get("logs") or []
            if isinstance(item_logs, str):
                import json
                try:
                    item_logs = json.loads(item_logs)
                except Exception:
                    item_logs = []
            logs_data.append({
                "item_id": item["id"],
                "mawb": item["mawb"],
                "logs": item_logs if isinstance(item_logs, list) else [],
            })
        return logs_data

