#!/usr/bin/env python3
"""Build script for creating a standalone executable using PyInstaller."""
import os
import sys
import subprocess
import shutil
from pathlib import Path


def build():
    """Build the standalone executable with size optimizations."""
    script_dir = Path(__file__).parent.absolute()
    
    # Modules to exclude (not needed for this app)
    exclude_modules = [
        # Qt modules we don't use
        'PyQt6.QtWebEngine',
        'PyQt6.QtWebEngineCore', 
        'PyQt6.QtWebEngineWidgets',
        'PyQt6.QtWebChannel',
        'PyQt6.QtNetwork',
        'PyQt6.QtSql',
        'PyQt6.QtTest',
        'PyQt6.QtXml',
        'PyQt6.QtDesigner',
        'PyQt6.QtHelp',
        'PyQt6.QtMultimedia',
        'PyQt6.QtMultimediaWidgets',
        'PyQt6.QtOpenGL',
        'PyQt6.QtOpenGLWidgets',
        'PyQt6.QtPositioning',
        'PyQt6.QtPrintSupport',
        'PyQt6.QtQml',
        'PyQt6.QtQuick',
        'PyQt6.QtQuickWidgets',
        'PyQt6.QtRemoteObjects',
        'PyQt6.QtSensors',
        'PyQt6.QtSerialPort',
        'PyQt6.QtSvg',
        'PyQt6.QtSvgWidgets',
        'PyQt6.QtBluetooth',
        'PyQt6.Qt3DCore',
        'PyQt6.Qt3DRender',
        'PyQt6.Qt3DInput',
        'PyQt6.Qt3DLogic',
        'PyQt6.Qt3DExtras',
        'PyQt6.Qt3DAnimation',
        'PyQt6.QtCharts',
        'PyQt6.QtDataVisualization',
        'PyQt6.QtStateMachine',
        'PyQt6.QtPdf',
        'PyQt6.QtPdfWidgets',
        # Other unused modules
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'tkinter',
        'unittest',
        'email',
        'html',
        'http',
        'xmlrpc',
        'pydoc',
    ]
    
    # Build command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "PortfolioTracker",
        "--onefile",
        "--windowed",
        "--clean",
        "--noconfirm",
        # Exclude unused modules
        *[f"--exclude-module={mod}" for mod in exclude_modules],
        # Hidden imports we DO need
        "--hidden-import", "PyQt6.sip",
        "--hidden-import", "openpyxl",
        "--hidden-import", "PIL",
        # Strip debug symbols (smaller binary)
        "--strip",
        "main.py"
    ]
    
    print("Building Portfolio Tracker executable...")
    print(f"Excluding {len(exclude_modules)} unused modules")
    print()
    
    # Run PyInstaller
    result = subprocess.run(cmd, cwd=script_dir)
    
    if result.returncode == 0:
        exe_path = script_dir / 'dist' / 'PortfolioTracker.exe'
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print()
            print("=" * 50)
            print(f"Build successful!")
            print(f"Executable: {exe_path}")
            print(f"Size: {size_mb:.1f} MB")
            print("=" * 50)
    else:
        print()
        print("Build failed!")
        sys.exit(1)


def build_onedir():
    """
    Build as directory (multiple files, but smaller total and faster startup).
    Use this if you don't need a single .exe file.
    """
    script_dir = Path(__file__).parent.absolute()
    
    exclude_modules = [
        'PyQt6.QtWebEngine', 'PyQt6.QtWebEngineCore', 'PyQt6.QtWebEngineWidgets',
        'PyQt6.QtNetwork', 'PyQt6.QtSql', 'PyQt6.QtMultimedia',
        'PyQt6.QtOpenGL', 'PyQt6.QtQml', 'PyQt6.QtQuick',
        'matplotlib', 'numpy', 'pandas', 'scipy', 'tkinter',
    ]
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "PortfolioTracker",
        "--onedir",  # Multiple files in a folder
        "--windowed",
        "--clean",
        "--noconfirm",
        *[f"--exclude-module={mod}" for mod in exclude_modules],
        "--hidden-import", "PyQt6.sip",
        "--hidden-import", "openpyxl", 
        "--hidden-import", "PIL",
        "--strip",
        "main.py"
    ]
    
    print("Building Portfolio Tracker (directory mode)...")
    result = subprocess.run(cmd, cwd=script_dir)
    
    if result.returncode == 0:
        dist_dir = script_dir / 'dist' / 'PortfolioTracker'
        if dist_dir.exists():
            total_size = sum(f.stat().st_size for f in dist_dir.rglob('*') if f.is_file())
            size_mb = total_size / (1024 * 1024)
            print()
            print("=" * 50)
            print(f"Build successful!")
            print(f"Directory: {dist_dir}")
            print(f"Total size: {size_mb:.1f} MB")
            print("Run: dist/PortfolioTracker/PortfolioTracker.exe")
            print("=" * 50)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--onedir":
        build_onedir()
    else:
        build()
