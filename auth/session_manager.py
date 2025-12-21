"""Session manager for storing and managing authentication tokens."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages user authentication session."""

    def __init__(self, session_file: Optional[Path] = None) -> None:
        """Initialize session manager.

        Args:
            session_file: Path to session file. Defaults to .session in app directory.
        """
        if session_file is None:
            # Get the app directory (parent of auth/)
            app_dir = Path(__file__).parent.parent
            session_file = app_dir / ".session"
        
        self.session_file = Path(session_file)
        self._session_data: Optional[dict] = None

    def save_session(self, auth_data: dict) -> bool:
        """Save authentication session.

        Args:
            auth_data: Authentication data containing access_token, refresh_token, user

        Returns:
            True if saved successfully
        """
        try:
            # Store session data
            self._session_data = auth_data.copy()
            
            # Save to file
            with open(self.session_file, 'w') as f:
                json.dump(auth_data, f, indent=2)
            
            logger.info(f"Session saved to {self.session_file}")
            return True
        except Exception as exc:
            logger.error(f"Failed to save session: {exc}", exc_info=True)
            return False

    def load_session(self) -> Optional[dict]:
        """Load authentication session.

        Returns:
            Session data if found, None otherwise
        """
        try:
            if self._session_data:
                return self._session_data
            
            if not self.session_file.exists():
                logger.debug("No session file found")
                return None
            
            with open(self.session_file, 'r') as f:
                session_data = json.load(f)
            
            self._session_data = session_data
            logger.info(f"Session loaded from {self.session_file}")
            return session_data
        except Exception as exc:
            logger.error(f"Failed to load session: {exc}", exc_info=True)
            return None

    def clear_session(self) -> bool:
        """Clear authentication session.

        Returns:
            True if cleared successfully
        """
        try:
            self._session_data = None
            
            if self.session_file.exists():
                self.session_file.unlink()
            
            logger.info("Session cleared")
            return True
        except Exception as exc:
            logger.error(f"Failed to clear session: {exc}", exc_info=True)
            return False

    def get_access_token(self) -> Optional[str]:
        """Get current access token.

        Returns:
            Access token if available, None otherwise
        """
        session = self.load_session()
        if session:
            return session.get("access_token")
        return None

    def get_refresh_token(self) -> Optional[str]:
        """Get current refresh token.

        Returns:
            Refresh token if available, None otherwise
        """
        session = self.load_session()
        if session:
            return session.get("refresh_token")
        return None

    def get_user(self) -> Optional[dict]:
        """Get current user data.

        Returns:
            User data if available, None otherwise
        """
        session = self.load_session()
        if session:
            return session.get("user")
        return None

    def is_authenticated(self) -> bool:
        """Check if user is authenticated.

        Returns:
            True if authenticated, False otherwise
        """
        return self.get_access_token() is not None



