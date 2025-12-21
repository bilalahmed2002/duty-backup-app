"""Authentication service for connecting to Supabase Auth."""

from __future__ import annotations

import logging
from typing import Optional

from supabase import create_client, Client

logger = logging.getLogger(__name__)


class AuthService:
    """Handles authentication with Supabase."""

    def __init__(self, supabase_url: str, supabase_key: str) -> None:
        """Initialize auth service.

        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase key (can be anon key or service role key for auth)
        """
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.client: Optional[Client] = None
        self._init_client()

    def _init_client(self) -> None:
        """Initialize Supabase client."""
        try:
            self.client = create_client(self.supabase_url, self.supabase_key)
            logger.info("Supabase auth client initialized")
        except Exception as exc:
            logger.error(f"Failed to initialize Supabase client: {exc}", exc_info=True)
            raise

    def login(self, email: str, password: str) -> tuple[bool, Optional[dict], Optional[str]]:
        """Authenticate user with email and password.

        Args:
            email: User email
            password: User password

        Returns:
            Tuple of (success, auth_data, error_message)
            auth_data contains: access_token, refresh_token, user
        """
        try:
            if not self.client:
                return False, None, "Supabase client not initialized"

            response = self.client.auth.sign_in_with_password({
                "email": email,
                "password": password,
            })

            if response.user and response.session:
                auth_data = {
                    "access_token": response.session.access_token,
                    "refresh_token": response.session.refresh_token,
                    "user": {
                        "id": response.user.id,
                        "email": response.user.email,
                        "role": response.user.user_metadata.get("role", "user"),
                    },
                }
                logger.info(f"User {email} logged in successfully")
                return True, auth_data, None
            else:
                return False, None, "Invalid credentials"
        except Exception as exc:
            error_msg = str(exc)
            logger.error(f"Login failed for {email}: {error_msg}", exc_info=True)
            return False, None, error_msg

    def logout(self, access_token: str) -> bool:
        """Logout user.

        Args:
            access_token: Current access token

        Returns:
            True if logged out successfully
        """
        try:
            if not self.client:
                return False

            # Set the session with the access token
            self.client.auth.set_session(access_token, "")
            # Sign out
            self.client.auth.sign_out()
            logger.info("User logged out successfully")
            return True
        except Exception as exc:
            logger.error(f"Logout failed: {exc}", exc_info=True)
            return False

    def refresh_token(self, refresh_token: str) -> tuple[bool, Optional[dict], Optional[str]]:
        """Refresh access token.

        Args:
            refresh_token: Refresh token

        Returns:
            Tuple of (success, auth_data, error_message)
        """
        try:
            if not self.client:
                return False, None, "Supabase client not initialized"

            response = self.client.auth.refresh_session(refresh_token)

            if response.user and response.session:
                auth_data = {
                    "access_token": response.session.access_token,
                    "refresh_token": response.session.refresh_token,
                    "user": {
                        "id": response.user.id,
                        "email": response.user.email,
                        "role": response.user.user_metadata.get("role", "user"),
                    },
                }
                logger.info("Token refreshed successfully")
                return True, auth_data, None
            else:
                return False, None, "Failed to refresh token"
        except Exception as exc:
            error_msg = str(exc)
            logger.error(f"Token refresh failed: {error_msg}", exc_info=True)
            return False, None, error_msg

