"""Build script for creating standalone Windows executable."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

# Paths - all relative to duty-backup-app directory
APP_DIR = Path(__file__).parent.resolve()
DIST_DIR = APP_DIR / "dist"
BUILD_DIR = APP_DIR / "build"

def main():
    """Build the standalone executable."""
    print("=" * 60)
    print("Building Duty Backup Application Executable")
    print("=" * 60)
    print("✓ Standalone build - no external backend dependency needed")
    
    # Clean previous builds
    print("\n1. Cleaning previous builds...")
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    
    # Install Playwright browsers
    print("\n2. Installing Playwright browsers...")
    try:
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
        print("✓ Playwright browsers installed")
    except subprocess.CalledProcessError as e:
        print(f"⚠ Warning: Failed to install Playwright browsers: {e}")
        print("  You may need to install them manually: playwright install chromium")
    
    # Encrypt .env if it exists (for employee distribution)
    print("\n3. Preparing configuration...")
    encrypted_config_path = APP_DIR / "config.encrypted"
    env_file = APP_DIR / ".env"
    
    if env_file.exists() and not encrypted_config_path.exists():
        # Encrypt .env and create config.encrypted
        print("   Encrypting .env file for secure bundling...")
        try:
            # Add app directory to path for imports
            sys.path.insert(0, str(APP_DIR))
            from service.encrypted_config import EncryptedConfigManager
            
            encrypted_manager = EncryptedConfigManager()
            encrypted_path = encrypted_manager.encrypt_env_file(env_file, encrypted_config_path)
            print(f"   ✓ Encrypted .env -> {encrypted_config_path}")
        except ImportError:
            print("   ⚠ Warning: cryptography not installed, cannot encrypt .env")
            print("     Install: pip install cryptography")
            print("     Or manually encrypt .env to config.encrypted before building")
        except Exception as e:
            print(f"   ⚠ Warning: Failed to encrypt .env: {e}")
            print("     Continuing without encrypted config...")
    elif encrypted_config_path.exists():
        print(f"   ✓ Found encrypted config: {encrypted_config_path}")
    
    # Create PyInstaller spec
    print("\n4. Creating PyInstaller spec...")
    # Convert paths to use forward slashes for cross-platform compatibility
    main_py_path = str(APP_DIR / "main.py").replace("\\", "/")
    app_dir_path = str(APP_DIR).replace("\\", "/")
    
    # Bundle encrypted config or .env.example
    datas_list = []
    
    # Option 1: Encrypted config (preferred for employee distribution)
    if encrypted_config_path.exists():
        encrypted_str = str(encrypted_config_path.resolve()).replace("\\", "/")
        datas_list.append(f"(r'{encrypted_str}', '.')")
    
    # Option 2: .env.example (template, safe to bundle)
    env_example_path = APP_DIR / ".env.example"
    if env_example_path.exists():
        env_example_str = str(env_example_path.resolve()).replace("\\", "/")
        datas_list.append(f"(r'{env_example_str}', '.')")
    
    datas_str = "[" + ", ".join(datas_list) + "]" if datas_list else "[]"
    
    spec_content = f"""# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Configuration bundling:
# - config.encrypted: Encrypted .env file (for employee distribution)
#   The encryption key is embedded in the code, so this is NOT perfect security,
#   but provides reasonable protection for internal employee distribution.
# - .env.example: Template file (safe to bundle, no secrets)
# NOTE: Plain .env files are NEVER bundled for security reasons

a = Analysis(
    [r'{main_py_path}'],
    pathex=[r'{app_dir_path}'],
    binaries=[],
    datas={datas_str},
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'supabase',
        'playwright',
        'boto3',
        'openpyxl',
        'pypdf',
        'pymupdf',
        'playwright._impl._api_structures',
        'playwright._impl._browser_type',
        'playwright._impl._chromium',
        'playwright._impl._driver',
        'playwright._impl._helper',
        'playwright._impl._network',
        'playwright._impl._page',
        'playwright._impl._path_utils',
        'playwright._impl._transport',
        # Local netchb_duty modules (standalone copies)
        'service.netchb_duty.database_manager',
        'service.netchb_duty.models',
        'service.netchb_duty.playwright_runner',
        'service.netchb_duty.storage',
        'service.netchb_duty.input_parser',
        'service.netchb_duty.otp_manager',
        'utils.s3_storage',
        'utils.playwright_launcher',
        'cryptography',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='duty_backup_app',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here if you have one
)
"""
    
    spec_file = APP_DIR / "duty_backup_app.spec"
    with open(spec_file, 'w') as f:
        f.write(spec_content)
    print(f"✓ Spec file created: {spec_file}")
    
    # Run PyInstaller
    print("\n4. Running PyInstaller...")
    try:
        # Set PYTHONPATH to include app directory
        env = os.environ.copy()
        current_pythonpath = env.get('PYTHONPATH', '')
        pythonpath_parts = [str(APP_DIR)]
        if current_pythonpath:
            pythonpath_parts.append(current_pythonpath)
        env['PYTHONPATH'] = os.pathsep.join(pythonpath_parts)
        
        subprocess.run([
            sys.executable, "-m", "PyInstaller",
            "--clean",
            "--noconfirm",
            str(spec_file)
        ], check=True, cwd=str(APP_DIR), env=env)
        print("✓ PyInstaller build completed")
    except subprocess.CalledProcessError as e:
        print(f"✗ PyInstaller build failed: {e}")
        sys.exit(1)
    
    # Copy .env.example if it exists (NEVER copy .env - it contains secrets!)
    env_example = APP_DIR / ".env.example"
    if env_example.exists():
        shutil.copy(env_example, DIST_DIR / ".env.example")
        print("✓ Copied .env.example (NOT .env - users must create their own)")
    
    # Ensure .env is NOT copied (safety check)
    env_file = APP_DIR / ".env"
    if env_file.exists():
        print("⚠ Warning: .env file exists but will NOT be included in build (contains secrets)")
    
    # Create README in dist
    readme_content = """# Duty Backup Application

## Installation

1. Extract all files to a folder
2. Create a `.env` file with your credentials (see .env.example)
3. Run `duty_backup_app.exe`

## Configuration

Create a `.env` file in the same directory as the executable with:

```
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_S3_BUCKET_NAME=your_bucket_name
AWS_REGION=us-east-1
```

## Usage

1. Launch the application
2. Login with your Supabase credentials
3. Select broker and format
4. Enter MAWB and process
5. View results in the Results tab

## Support

For issues, check the `duty_backup_app.log` file.
"""
    
    readme_file = DIST_DIR / "README.txt"
    with open(readme_file, 'w') as f:
        f.write(readme_content)
    print("✓ Created README.txt")
    
    print("\n" + "=" * 60)
    print("Build completed successfully!")
    print(f"Executable location: {DIST_DIR / 'duty_backup_app.exe'}")
    print("=" * 60)

if __name__ == "__main__":
    main()

