#!/usr/bin/env python3
"""Build script for creating a standalone executable using PyInstaller."""
import os
import sys
import subprocess
from pathlib import Path


def build():
    """Build the standalone executable."""
    # Get the directory containing this script
    script_dir = Path(__file__).parent.absolute()
    
    # PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "PortfolioTracker",
        "--onefile",  # Single executable
        "--windowed",  # No console window
        "--icon", "assets/icon.ico",  # Application icon
        "--add-data", f"core{os.pathsep}core",
        "--add-data", f"ui{os.pathsep}ui",
        "--hidden-import", "PyQt6.sip",
        "--hidden-import", "openpyxl",
        "--hidden-import", "PIL",
        "--clean",  # Clean cache
        "main.py"
    ]
    
    print("Building Portfolio Tracker executable...")
    print(f"Command: {' '.join(cmd)}")
    print()
    
    # Run PyInstaller
    result = subprocess.run(cmd, cwd=script_dir)
    
    if result.returncode == 0:
        print()
        print("=" * 50)
        print("Build successful!")
        print(f"Executable: {script_dir / 'dist' / 'PortfolioTracker.exe'}")
        print("=" * 50)
    else:
        print()
        print("Build failed!")
        sys.exit(1)


if __name__ == "__main__":
    build()