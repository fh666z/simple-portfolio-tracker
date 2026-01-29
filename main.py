#!/usr/bin/env python3
"""Portfolio Tracker - Main Entry Point."""
import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

from ui.main_window import MainWindow


def _resource_path(relative_path: str) -> Path:
    """Return path to a resource, works when running or frozen (PyInstaller)."""
    if getattr(sys, "frozen", False):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).resolve().parent
    return base / relative_path


def main():
    """Main entry point for the application."""
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    app.setApplicationName("Portfolio Tracker")
    app.setOrganizationName("PortfolioTracker")
    
    # Set application style
    app.setStyle("Fusion")
    
    # Set application icon (window title bar, taskbar)
    icon_path = _resource_path("assets/icon.ico")
    if icon_path.exists():
        app_icon = QIcon(str(icon_path))
        app.setWindowIcon(app_icon)
    
    # Create and show main window
    window = MainWindow()
    if icon_path.exists():
        window.setWindowIcon(app_icon)
    window.show()
    
    # Run event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
