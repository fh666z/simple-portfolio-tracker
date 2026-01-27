"""Import dialog for Portfolio Tracker."""
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent


class DropZone(QFrame):
    """A frame that accepts drag-and-drop files."""
    
    file_dropped = pyqtSignal(str)  # Emits file path
    
    SUPPORTED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.xlsx', '.xls', '.csv'}
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the drop zone appearance."""
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            DropZone {
                border: 2px dashed #aaa;
                border-radius: 10px;
                background-color: #f9f9f9;
                min-height: 150px;
            }
            DropZone:hover {
                border-color: #666;
                background-color: #f0f0f0;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Icon/text
        icon_label = QLabel("📁")
        icon_label.setStyleSheet("font-size: 48px;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)
        
        text_label = QLabel("Drag & Drop file here")
        text_label.setStyleSheet("font-size: 16px; color: #666;")
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(text_label)
        
        format_label = QLabel("Supported: PNG, JPG, XLSX, CSV")
        format_label.setStyleSheet("font-size: 12px; color: #999;")
        format_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(format_label)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter event."""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                file_path = urls[0].toLocalFile()
                suffix = Path(file_path).suffix.lower()
                if suffix in self.SUPPORTED_EXTENSIONS:
                    event.acceptProposedAction()
                    self.setStyleSheet("""
                        DropZone {
                            border: 2px solid #4CAF50;
                            border-radius: 10px;
                            background-color: #e8f5e9;
                        }
                    """)
                    return
        event.ignore()
    
    def dragLeaveEvent(self, event):
        """Handle drag leave event."""
        self.setStyleSheet("""
            DropZone {
                border: 2px dashed #aaa;
                border-radius: 10px;
                background-color: #f9f9f9;
            }
            DropZone:hover {
                border-color: #666;
                background-color: #f0f0f0;
            }
        """)
    
    def dropEvent(self, event: QDropEvent):
        """Handle drop event."""
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            suffix = Path(file_path).suffix.lower()
            if suffix in self.SUPPORTED_EXTENSIONS:
                self.file_dropped.emit(file_path)
        
        # Reset style
        self.dragLeaveEvent(None)


class ImportDialog(QDialog):
    """Dialog for importing portfolio data from file."""
    
    file_selected = pyqtSignal(str)  # Emits selected file path
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import Portfolio Data")
        self.setMinimumSize(400, 300)
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Import New Portfolio Data")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Drop zone
        self.drop_zone = DropZone()
        self.drop_zone.file_dropped.connect(self.on_file_selected)
        layout.addWidget(self.drop_zone)
        
        # Or separator
        or_layout = QHBoxLayout()
        line1 = QFrame()
        line1.setFrameShape(QFrame.Shape.HLine)
        line1.setStyleSheet("color: #ddd;")
        or_layout.addWidget(line1)
        or_label = QLabel("OR")
        or_label.setStyleSheet("color: #999; padding: 0 10px;")
        or_layout.addWidget(or_label)
        line2 = QFrame()
        line2.setFrameShape(QFrame.Shape.HLine)
        line2.setStyleSheet("color: #ddd;")
        or_layout.addWidget(line2)
        layout.addLayout(or_layout)
        
        # Browse button
        browse_btn = QPushButton("Browse Files...")
        browse_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                font-size: 14px;
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        browse_btn.clicked.connect(self.browse_files)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(browse_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Cancel button
        layout.addSpacing(10)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        cancel_layout = QHBoxLayout()
        cancel_layout.addStretch()
        cancel_layout.addWidget(cancel_btn)
        layout.addLayout(cancel_layout)
    
    def browse_files(self):
        """Open file browser dialog."""
        file_filter = "All Supported Files (*.png *.jpg *.jpeg *.xlsx *.xls *.csv);;"\
                      "Images (*.png *.jpg *.jpeg);;"\
                      "Excel Files (*.xlsx *.xls);;"\
                      "CSV Files (*.csv)"
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Portfolio Data File",
            "",
            file_filter
        )
        
        if file_path:
            self.on_file_selected(file_path)
    
    def on_file_selected(self, file_path: str):
        """Handle file selection."""
        if not Path(file_path).exists():
            QMessageBox.warning(self, "Error", f"File not found: {file_path}")
            return
        
        self.file_selected.emit(file_path)
        self.accept()
