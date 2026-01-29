"""Data review dialog for Portfolio Tracker."""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QLabel, QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from core.models import Holding
from .utils import (
    parse_numeric_text, ALIGN_RIGHT_CENTER,
    get_warning_colors
)


class ReviewDialog(QDialog):
    """Dialog for reviewing and editing imported data before confirmation."""
    
    data_confirmed = pyqtSignal(list)  # Emits list of Holdings
    
    # Column definitions
    COLUMNS = [
        ("Instrument", str, False),      # (name, type, is_numeric)
        ("Position", float, True),
        ("Last Price", float, True),
        ("Change %", float, True),
        ("Cost Basis", float, True),
        ("Market Value", float, True),
        ("Avg Price", float, True),
        ("Daily P&L", float, True),
        ("Unrealized P&L", float, True),
    ]
    
    def __init__(self, holdings: list[Holding], source_file: str = "", parent=None):
        super().__init__(parent)
        self.holdings = holdings
        self.source_file = source_file
        self.setWindowTitle("Review Imported Data")
        self.setMinimumSize(900, 500)
        self.setup_ui()
        self.populate_table()
    
    def setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Title and source info
        title_label = QLabel("Review and Edit Imported Data")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title_label)
        
        if self.source_file:
            source_label = QLabel(f"Source: {self.source_file}")
            source_label.setStyleSheet("color: #666; font-style: italic;")
            layout.addWidget(source_label)
        
        info_label = QLabel(
            "Review the imported data below. Edit any cells that were not recognized correctly. "
            "Cells highlighted in yellow may need attention."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #555; margin: 10px 0;")
        layout.addWidget(info_label)
        
        # Table
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.setup_table()
        layout.addWidget(self.table)
        
        # Row count label
        self.row_count_label = QLabel()
        self.row_count_label.setStyleSheet("color: #666;")
        layout.addWidget(self.row_count_label)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 30px;
                font-size: 14px;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        confirm_btn = QPushButton("Confirm")
        confirm_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 30px;
                font-size: 14px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        confirm_btn.clicked.connect(self.on_confirm)
        btn_layout.addWidget(confirm_btn)
        
        layout.addLayout(btn_layout)
    
    def setup_table(self):
        """Set up the review table."""
        self.table.setColumnCount(len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels([col[0] for col in self.COLUMNS])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, len(self.COLUMNS)):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        
        # Enable column reordering (no persistence for review dialog)
        header.setSectionsMovable(True)
    
    def populate_table(self):
        """Populate the table with holdings data."""
        self.table.setRowCount(len(self.holdings))
        
        for row, holding in enumerate(self.holdings):
            # Instrument
            item = QTableWidgetItem(holding.instrument)
            self.table.setItem(row, 0, item)
            
            # Position
            self.set_numeric_cell(row, 1, holding.position)
            
            # Last Price
            self.set_numeric_cell(row, 2, holding.last_price)
            
            # Change %
            self.set_numeric_cell(row, 3, holding.change_pct * 100)  # Display as percentage
            
            # Cost Basis
            self.set_numeric_cell(row, 4, holding.cost_basis)
            
            # Market Value
            self.set_numeric_cell(row, 5, holding.market_value)
            
            # Avg Price
            self.set_numeric_cell(row, 6, holding.avg_price)
            
            # Daily P&L
            self.set_numeric_cell(row, 7, holding.daily_pnl)
            
            # Unrealized P&L
            self.set_numeric_cell(row, 8, holding.unrealized_pnl)
            
            # Highlight potential issues
            self.check_row_issues(row, holding)
        
        self.row_count_label.setText(f"Total: {len(self.holdings)} holdings")
    
    def set_numeric_cell(self, row: int, col: int, value: float):
        """Set a numeric cell value."""
        item = QTableWidgetItem(f"{value:,.2f}")
        item.setTextAlignment(ALIGN_RIGHT_CENTER)
        self.table.setItem(row, col, item)
    
    def check_row_issues(self, row: int, holding: Holding):
        """Check for potential issues in a row and highlight if needed."""
        warning_yellow, warning_red = get_warning_colors()
        
        # Check for zero/missing market value
        if holding.market_value == 0:
            self.highlight_cell(row, 5, warning_yellow)
        
        # Check for zero position
        if holding.position == 0:
            self.highlight_cell(row, 1, warning_yellow)
        
        # Check for suspicious values (negative position, etc.)
        if holding.position < 0:
            self.highlight_cell(row, 1, warning_red)
        
        # Check for missing cost basis when market value exists
        if holding.market_value > 0 and holding.cost_basis == 0:
            self.highlight_cell(row, 4, warning_yellow)
    
    def highlight_cell(self, row: int, col: int, color: QColor):
        """Highlight a cell with the given color."""
        item = self.table.item(row, col)
        if item:
            item.setBackground(color)
    
    def get_edited_holdings(self) -> list[Holding]:
        """Get the holdings with any edits applied."""
        holdings = []
        
        for row in range(self.table.rowCount()):
            try:
                instrument = self.table.item(row, 0).text().strip()
                if not instrument:
                    continue
                
                holding = Holding(
                    instrument=instrument,
                    position=self.parse_cell_float(row, 1),
                    last_price=self.parse_cell_float(row, 2),
                    change_pct=self.parse_cell_float(row, 3) / 100,  # Convert from percentage
                    cost_basis=self.parse_cell_float(row, 4),
                    market_value=self.parse_cell_float(row, 5),
                    avg_price=self.parse_cell_float(row, 6),
                    daily_pnl=self.parse_cell_float(row, 7),
                    unrealized_pnl=self.parse_cell_float(row, 8),
                )
                holdings.append(holding)
            except Exception as e:
                print(f"Warning: Could not parse row {row}: {e}")
                continue
        
        return holdings
    
    def parse_cell_float(self, row: int, col: int) -> float:
        """Parse a float from a table cell."""
        item = self.table.item(row, col)
        if item is None:
            return 0.0
        return parse_numeric_text(item.text())
    
    def on_confirm(self):
        """Handle confirm button click."""
        holdings = self.get_edited_holdings()
        
        if not holdings:
            QMessageBox.warning(
                self,
                "No Data",
                "No valid holdings to import. Please check the data."
            )
            return
        
        self.data_confirmed.emit(holdings)
        self.accept()
