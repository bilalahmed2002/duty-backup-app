# Encrypted Configuration Guide

## Overview

For secure distribution to employees, the application supports bundling encrypted configuration files instead of plain `.env` files. This provides reasonable protection for internal use (though not perfect security - determined attackers can still extract the key from the executable).

## How It Works

1. **Encryption**: The `.env` file is encrypted using Fernet (symmetric encryption) to create `config.encrypted`
2. **Bundling**: The encrypted config is bundled into the executable
3. **Decryption**: At runtime, the app automatically decrypts and loads the configuration

## Usage

### Option 1: Automatic Encryption (Recommended)

Simply run the build script with a `.env` file present:

```bash
cd duty-backup-app
python build_standalone.py
```

The build script will automatically:
- Encrypt `.env` → `config.encrypted`
- Bundle `config.encrypted` into the executable
- Users don't need to create their own `.env` file

### Option 2: Manual Encryption

If you want to encrypt manually before building:

```bash
cd duty-backup-app
python -c "from service.encrypted_config import EncryptedConfigManager; EncryptedConfigManager().encrypt_env_file(Path('.env'), Path('config.encrypted'))"
```

### Option 3: Custom Encryption Key

For better security, use a custom encryption key:

```bash
# Generate a new key
python -c "from service.encrypted_config import generate_encryption_key; generate_encryption_key()"

# Set the key as environment variable
export ENCRYPTION_KEY='your_generated_key_here'

# Build (will use the custom key)
python build_standalone.py
```

**Important**: Store the encryption key securely! If you lose it, you cannot decrypt the config.

## Security Notes

⚠️ **Important Security Considerations**:

1. **Not Perfect Security**: The encryption key is embedded in the executable code, so determined attackers can extract it and decrypt the config.

2. **Internal Use Only**: This approach is suitable for:
   - Internal employee distribution
   - Low-to-medium security requirements
   - Convenience over maximum security

3. **For Higher Security**: Consider:
   - Having employees create their own `.env` files from `.env.example`
   - Using Windows Registry (Windows only)
   - Using environment variables set by IT
   - Using a configuration server

## Files

- `.env` - Plain text configuration (DO NOT commit to Git)
- `config.encrypted` - Encrypted configuration (DO NOT commit to Git)
- `.env.example` - Template file (safe to commit, no secrets)

## Troubleshooting

**"Failed to decrypt config"**
- The encryption key doesn't match
- The encrypted file is corrupted
- Solution: Re-encrypt with the correct key

**"cryptography not installed"**
- Install: `pip install cryptography`

**"Configuration file not found"**
- The app will fall back to looking for `.env` file
- Or create `config.encrypted` manually


