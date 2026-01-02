"""Path utilities for handling both development and PyInstaller bundle paths."""

import sys
from pathlib import Path


def get_app_directory() -> Path:
    """Get the application directory, handling both development and PyInstaller bundle.
    
    In PyInstaller bundles:
    - sys.frozen is True
    - sys.executable points to the .exe file
    - Returns the directory containing the .exe
    
    In development:
    - Returns the directory containing main.py (project root)
    
    Returns:
        Path to the application directory
    """
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller bundle
        # sys.executable is the path to the .exe file
        return Path(sys.executable).parent.resolve()
    else:
        # Running as Python script
        # Get the directory containing main.py
        # This file is in utils/, so go up one level
        return Path(__file__).parent.parent.resolve()














