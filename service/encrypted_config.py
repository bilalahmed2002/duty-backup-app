"""Encrypted configuration manager for bundling credentials in executable.

This module provides encryption/decryption of .env files for secure distribution
to employees. Uses Fernet (symmetric encryption) for simplicity and security.

WARNING: This is NOT perfect security - determined attackers can still extract
the encryption key from the executable. However, it provides reasonable protection
for internal employee distribution.
"""

from __future__ import annotations

import base64
import logging
import os
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

# Default encryption key (can be overridden via environment variable)
# In production, generate a unique key: Fernet.generate_key()
# Store it securely and pass via environment variable during build
# WARNING: This default key is NOT secure - change it for production!
_DEFAULT_KEY_STR = os.getenv(
    "ENCRYPTION_KEY",
    "default_key_change_me_in_production_use_generate_encryption_key"
)


class EncryptedConfigManager:
    """Manages encrypted configuration for bundled executables."""

    def __init__(self, encryption_key: Optional[bytes | str] = None) -> None:
        """Initialize encrypted config manager.

        Args:
            encryption_key: Fernet encryption key (base64-encoded string or bytes).
                          If None, uses default from environment or hardcoded default.
        """
        if encryption_key is None:
            # Use key from environment or default
            key_str = os.getenv("ENCRYPTION_KEY", _DEFAULT_KEY_STR)
        elif isinstance(encryption_key, bytes):
            # Convert bytes to string (assuming it's already base64-encoded)
            key_str = encryption_key.decode('utf-8')
        else:
            key_str = encryption_key

        # Try to use key as-is (should be base64-encoded Fernet key)
        try:
            self.fernet = Fernet(key_str.encode() if isinstance(key_str, str) else key_str)
        except Exception:
            # If key is not valid Fernet key, generate one from it
            # Use the key string as seed, pad/truncate to 32 bytes
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.backends import default_backend
            
            # Hash the key string to get consistent 32 bytes
            digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
            digest.update(key_str.encode() if isinstance(key_str, str) else key_str)
            key_bytes = digest.finalize()
            
            # Encode to base64 for Fernet
            key_b64 = base64.urlsafe_b64encode(key_bytes)
            self.fernet = Fernet(key_b64)

        logger.info("EncryptedConfigManager initialized")

    def encrypt_env_file(self, env_file: Path, output_file: Optional[Path] = None) -> Path:
        """Encrypt a .env file.

        Args:
            env_file: Path to .env file to encrypt
            output_file: Path to save encrypted file. Defaults to {env_file}.encrypted

        Returns:
            Path to encrypted file
        """
        if output_file is None:
            output_file = env_file.parent / f"{env_file.name}.encrypted"

        # Read .env file
        with open(env_file, 'rb') as f:
            env_data = f.read()

        # Encrypt
        encrypted_data = self.fernet.encrypt(env_data)

        # Save encrypted file
        with open(output_file, 'wb') as f:
            f.write(encrypted_data)

        logger.info(f"Encrypted {env_file} -> {output_file}")
        return output_file

    def decrypt_to_env_file(
        self,
        encrypted_file: Path,
        output_file: Optional[Path] = None,
    ) -> Path:
        """Decrypt an encrypted config file to .env format.

        Args:
            encrypted_file: Path to encrypted file
            output_file: Path to save decrypted .env. Defaults to .env in same directory

        Returns:
            Path to decrypted .env file
        """
        if output_file is None:
            output_file = encrypted_file.parent / ".env"

        # Read encrypted file
        with open(encrypted_file, 'rb') as f:
            encrypted_data = f.read()

        # Decrypt
        try:
            decrypted_data = self.fernet.decrypt(encrypted_data)
        except Exception as exc:
            logger.error(f"Failed to decrypt {encrypted_file}: {exc}")
            raise ValueError(f"Invalid encryption key or corrupted file: {exc}")

        # Save decrypted .env file
        with open(output_file, 'wb') as f:
            f.write(decrypted_data)

        logger.info(f"Decrypted {encrypted_file} -> {output_file}")
        return output_file

    def decrypt_to_dict(self, encrypted_file: Path) -> dict[str, str]:
        """Decrypt config file and return as dictionary.

        Args:
            encrypted_file: Path to encrypted file

        Returns:
            Dictionary of key=value pairs
        """
        # Read encrypted file
        with open(encrypted_file, 'rb') as f:
            encrypted_data = f.read()

        # Decrypt
        try:
            decrypted_data = self.fernet.decrypt(encrypted_data)
        except Exception as exc:
            logger.error(f"Failed to decrypt {encrypted_file}: {exc}")
            raise ValueError(f"Invalid encryption key or corrupted file: {exc}")

        # Parse as .env format
        config = {}
        for line in decrypted_data.decode('utf-8').splitlines():
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                config[key.strip()] = value.strip()

        return config


def generate_encryption_key() -> bytes:
    """Generate a new Fernet encryption key.

    Returns:
        Base64-encoded Fernet key (bytes)
    """
    key = Fernet.generate_key()
    print(f"\n🔑 Generated encryption key:")
    print(f"   {key.decode()}")
    print(f"\n💡 Save this key securely and use it during build:")
    print(f"   export ENCRYPTION_KEY='{key.decode()}'")
    print(f"   python build_standalone.py\n")
    return key

