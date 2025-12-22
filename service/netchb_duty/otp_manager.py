"""TOTP (Time-based One-Time Password) manager for NetCHB 2FA authentication."""

from __future__ import annotations

import logging
import time
import urllib.parse
from typing import Optional, Tuple

import pyotp

logger = logging.getLogger(__name__)


class OTPManager:
    """Manages TOTP code generation from otpauth:// URIs."""

    @staticmethod
    def parse_otp_uri(otp_uri: str) -> Tuple[str, int, int, str]:
        """
        Parse an otpauth://totp/ URI and extract TOTP parameters.

        Args:
            otp_uri: OTP URI in format: otpauth://totp/...?secret=...&period=30&digits=6&algorithm=SHA1

        Returns:
            Tuple of (secret, period, digits, algorithm)

        Raises:
            ValueError: If URI is invalid or missing required parameters
        """
        if not otp_uri or not otp_uri.startswith("otpauth://totp/"):
            raise ValueError(f"Invalid OTP URI format. Must start with 'otpauth://totp/': {otp_uri}")

        try:
            parsed = urllib.parse.urlparse(otp_uri)
            query_params = urllib.parse.parse_qs(parsed.query)

            secret = query_params.get("secret")
            if not secret or not secret[0]:
                raise ValueError("Missing 'secret' parameter in OTP URI")

            period = int(query_params.get("period", ["30"])[0])
            digits = int(query_params.get("digits", ["6"])[0])
            algorithm = query_params.get("algorithm", ["SHA1"])[0]

            return secret[0], period, digits, algorithm.upper()

        except (ValueError, KeyError, IndexError) as exc:
            raise ValueError(f"Failed to parse OTP URI: {exc}") from exc

    @staticmethod
    def get_current_otp(otp_uri: str) -> Optional[str]:
        """
        Generate the current TOTP code from an OTP URI.

        Args:
            otp_uri: OTP URI string

        Returns:
            Current 6-digit TOTP code, or None if generation fails
        """
        if not otp_uri:
            return None

        try:
            secret, period, digits, algorithm = OTPManager.parse_otp_uri(otp_uri)
            totp = pyotp.TOTP(secret, interval=period, digits=digits, digest=algorithm.lower())
            code = totp.now()
            logger.debug(f"Generated TOTP code: {code} (period={period}s, digits={digits})")
            return code
        except Exception as exc:
            logger.error(f"Failed to generate TOTP code: {exc}")
            return None

    @staticmethod
    def get_otp_with_timing(otp_uri: str) -> Tuple[Optional[str], int]:
        """
        Generate current TOTP code and return seconds remaining in the current period.

        Args:
            otp_uri: OTP URI string

        Returns:
            Tuple of (current_code, seconds_remaining)
            Returns (None, 0) if generation fails
        """
        if not otp_uri:
            return None, 0

        try:
            secret, period, digits, algorithm = OTPManager.parse_otp_uri(otp_uri)
            totp = pyotp.TOTP(secret, interval=period, digits=digits, digest=algorithm.lower())

            current_code = totp.now()
            current_time = int(time.time())
            seconds_remaining = period - (current_time % period)

            logger.debug(f"TOTP code: {current_code}, {seconds_remaining}s remaining")
            return current_code, seconds_remaining

        except Exception as exc:
            logger.error(f"Failed to generate TOTP with timing: {exc}")
            return None, 0

    @staticmethod
    def get_fresh_otp(otp_uri: str, min_seconds_remaining: int = 5) -> Optional[str]:
        """
        Wait for a fresh TOTP code with sufficient time remaining before expiration.

        This ensures the code won't expire during form submission.

        Args:
            otp_uri: OTP URI string
            min_seconds_remaining: Minimum seconds remaining before returning code (default: 5)

        Returns:
            TOTP code with at least min_seconds_remaining seconds left, or None if generation fails
        """
        if not otp_uri:
            return None

        max_wait = 35  # Maximum wait time (slightly more than one period)
        waited = 0

        while waited < max_wait:
            current_code, seconds_remaining = OTPManager.get_otp_with_timing(otp_uri)

            if current_code is None:
                logger.error("Failed to generate TOTP code")
                return None

            if seconds_remaining >= min_seconds_remaining:
                logger.info(f"Fresh TOTP code generated with {seconds_remaining}s remaining")
                return current_code

            # Wait until the next period starts
            sleep_time = seconds_remaining + 1
            logger.debug(f"Waiting {sleep_time}s for fresh TOTP code (current has {seconds_remaining}s remaining)")
            time.sleep(sleep_time)
            waited += sleep_time

        # Fallback: return current code even if time is short
        logger.warning(f"Timeout waiting for fresh TOTP, returning current code")
        return OTPManager.get_current_otp(otp_uri)

