"""Local session storage for broker login sessions.

This module handles saving and loading Playwright session states locally,
preventing conflicts with the backend server's session storage in Supabase.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import UUID

logger = logging.getLogger(__name__)

# Import path utility
try:
    from utils.path_utils import get_app_directory
except ImportError:
    # Fallback if utils not available
    import sys
    def get_app_directory() -> Path:
        if getattr(sys, 'frozen', False):
            return Path(sys.executable).parent.resolve()
        else:
            return Path(__file__).parent.parent.resolve()


class LocalSessionStorage:
    """Manages local storage of broker login sessions."""

    def __init__(self, sessions_dir: Optional[Path] = None) -> None:
        """Initialize local session storage.

        Args:
            sessions_dir: Directory to store session files. Defaults to 'sessions/' in app directory.
        """
        if sessions_dir is None:
            # Get the app directory (works for both dev and PyInstaller bundle)
            app_dir = get_app_directory()
            sessions_dir = app_dir / "sessions"
        
        self.sessions_dir = Path(sessions_dir)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Local session storage initialized at: {self.sessions_dir}")

    def get_session_path(self, broker_id: UUID) -> Path:
        """Get the file path for a broker's session.

        Args:
            broker_id: UUID of the broker

        Returns:
            Path to the session file
        """
        return self.sessions_dir / f"broker_{broker_id}.json"

    def save_session(self, broker_id: UUID, session_state: Dict[str, Any]) -> bool:
        """Save a broker's session state to local file.

        Args:
            broker_id: UUID of the broker
            session_state: Playwright session state (cookies, storage, etc.)

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            session_path = self.get_session_path(broker_id)
            
            # Save session state to JSON file
            with open(session_path, 'w') as f:
                json.dump(session_state, f, indent=2)
            
            logger.info(f"Saved session for broker {broker_id} to {session_path}")
            return True
        except Exception as exc:
            logger.error(f"Failed to save session for broker {broker_id}: {exc}", exc_info=True)
            return False

    def load_session(self, broker_id: UUID) -> Optional[Dict[str, Any]]:
        """Load a broker's session state from local file.

        Args:
            broker_id: UUID of the broker

        Returns:
            Session state dictionary if found, None otherwise
        """
        try:
            session_path = self.get_session_path(broker_id)
            
            if not session_path.exists():
                logger.debug(f"No session file found for broker {broker_id}")
                return None
            
            # Load session state from JSON file
            with open(session_path, 'r') as f:
                session_state = json.load(f)
            
            logger.info(f"Loaded session for broker {broker_id} from {session_path}")
            return session_state
        except Exception as exc:
            logger.error(f"Failed to load session for broker {broker_id}: {exc}", exc_info=True)
            return None

    def delete_session(self, broker_id: UUID) -> bool:
        """Delete a broker's session file.

        Args:
            broker_id: UUID of the broker

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            session_path = self.get_session_path(broker_id)
            
            if session_path.exists():
                session_path.unlink()
                logger.info(f"Deleted session for broker {broker_id}")
                return True
            else:
                logger.debug(f"No session file to delete for broker {broker_id}")
                return False
        except Exception as exc:
            logger.error(f"Failed to delete session for broker {broker_id}: {exc}", exc_info=True)
            return False

    def has_session(self, broker_id: UUID) -> bool:
        """Check if a session file exists for a broker.

        Args:
            broker_id: UUID of the broker

        Returns:
            True if session file exists, False otherwise
        """
        session_path = self.get_session_path(broker_id)
        return session_path.exists()

    def clear_all_sessions(self) -> int:
        """Clear all session files.

        Returns:
            Number of sessions deleted
        """
        deleted_count = 0
        try:
            for session_file in self.sessions_dir.glob("broker_*.json"):
                try:
                    session_file.unlink()
                    deleted_count += 1
                except Exception as exc:
                    logger.warning(f"Failed to delete {session_file}: {exc}")
            
            logger.info(f"Cleared {deleted_count} session files")
            return deleted_count
        except Exception as exc:
            logger.error(f"Failed to clear sessions: {exc}", exc_info=True)
            return deleted_count





