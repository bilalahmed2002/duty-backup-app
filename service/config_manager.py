"""Configuration manager for handling Supabase and AWS credentials."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Dict, Optional

from dotenv import load_dotenv

# Try to import encrypted config (may not be available if cryptography not installed)
try:
    from .encrypted_config import EncryptedConfigManager
    ENCRYPTION_AVAILABLE = True
except ImportError:
    ENCRYPTION_AVAILABLE = False
    EncryptedConfigManager = None

logger = logging.getLogger(__name__)

# Import path utility
try:
    from utils.path_utils import get_app_directory
except ImportError:
    # Fallback if utils not available
    def get_app_directory() -> Path:
        if getattr(sys, 'frozen', False):
            return Path(sys.executable).parent.resolve()
        else:
            return Path(__file__).parent.parent.resolve()


class ConfigManager:
    """Manages application configuration and credentials."""

    def __init__(self, env_file: Optional[Path] = None) -> None:
        """Initialize configuration manager.

        Args:
            env_file: Path to .env file. Defaults to .env in app directory.
        """
        if env_file is None:
            # Get the app directory (works for both dev and PyInstaller bundle)
            app_dir = get_app_directory()
            env_file = app_dir / ".env"
        
        self.env_file = Path(env_file)
        self._config: Dict[str, Optional[str]] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from .env file or encrypted config."""
        app_dir = self.env_file.parent
        
        # Check for encrypted config first (for bundled executables)
        encrypted_config_path = app_dir / "config.encrypted"
        if encrypted_config_path.exists() and ENCRYPTION_AVAILABLE:
            try:
                logger.info(f"Found encrypted config, attempting to decrypt...")
                encrypted_manager = EncryptedConfigManager()
                config_dict = encrypted_manager.decrypt_to_dict(encrypted_config_path)
                
                # Set environment variables from decrypted config
                for key, value in config_dict.items():
                    os.environ[key] = value
                
                logger.info(f"✅ Loaded configuration from encrypted config")
                return
            except Exception as exc:
                logger.warning(f"Failed to decrypt config: {exc}, falling back to .env")
        
        # Fall back to regular .env file
        if self.env_file.exists():
            load_dotenv(self.env_file)
            logger.info(f"Loaded configuration from {self.env_file}")
        else:
            logger.warning(f"Configuration file not found: {self.env_file}")

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        # First check environment variables (highest priority)
        value = os.getenv(key)
        if value:
            return value
        
        # Then check cached config
        if key in self._config:
            return self._config[key]
        
        return default

    def set(self, key: str, value: Optional[str]) -> None:
        """Set a configuration value (in memory only).

        Args:
            key: Configuration key
            value: Configuration value
        """
        self._config[key] = value
        os.environ[key] = value or ""

    def save_to_env_file(self) -> bool:
        """Save current configuration to .env file.

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Read existing .env file if it exists
            existing_lines: Dict[str, str] = {}
            if self.env_file.exists():
                with open(self.env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, val = line.split('=', 1)
                            existing_lines[key.strip()] = val.strip()
            
            # Update with current config
            for key, value in self._config.items():
                if value:
                    existing_lines[key] = value
            
            # Write back to file
            with open(self.env_file, 'w') as f:
                for key, value in existing_lines.items():
                    f.write(f"{key}={value}\n")
            
            logger.info(f"Saved configuration to {self.env_file}")
            return True
        except Exception as exc:
            logger.error(f"Failed to save configuration: {exc}", exc_info=True)
            return False

    def validate_required(self) -> tuple[bool, list[str]]:
        """Validate that all required configuration is present.

        Returns:
            Tuple of (is_valid, missing_keys)
        """
        required_keys = [
            "SUPABASE_URL",
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "AWS_S3_BUCKET_NAME",
            "AWS_REGION",
        ]
        
        # Either SUPABASE_ANON_KEY or SUPABASE_SERVICE_ROLE_KEY is required
        optional_keys = [
            ("SUPABASE_ANON_KEY", "SUPABASE_SERVICE_ROLE_KEY"),
        ]
        
        missing = []
        for key in required_keys:
            value = self.get(key)
            if not value:
                missing.append(key)
        
        # Check optional keys (at least one must be present)
        for key_group in optional_keys:
            has_any = any(self.get(key) for key in key_group)
            if not has_any:
                missing.append(f"{key_group[0]} or {key_group[1]}")
        
        return len(missing) == 0, missing

    # Convenience methods for common config values
    @property
    def supabase_url(self) -> Optional[str]:
        """Get Supabase URL."""
        return self.get("SUPABASE_URL")

    @property
    def supabase_service_role_key(self) -> Optional[str]:
        """Get Supabase service role key."""
        return self.get("SUPABASE_SERVICE_ROLE_KEY")

    @property
    def aws_access_key_id(self) -> Optional[str]:
        """Get AWS access key ID."""
        return self.get("AWS_ACCESS_KEY_ID")

    @property
    def aws_secret_access_key(self) -> Optional[str]:
        """Get AWS secret access key."""
        return self.get("AWS_SECRET_ACCESS_KEY")

    @property
    def aws_s3_bucket_name(self) -> Optional[str]:
        """Get AWS S3 bucket name."""
        return self.get("AWS_S3_BUCKET_NAME")

    @property
    def aws_region(self) -> Optional[str]:
        """Get AWS region."""
        return self.get("AWS_REGION", "us-east-1")

