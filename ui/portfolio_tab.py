"""Portfolio table view for Portfolio Tracker."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QLabel, QLineEdit, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDoubleValidator

from core.calculator import PortfolioCalculator
from core.persistence import SettingsStore


class PortfolioTab(QWidget):
    """Main portfolio table view with holdings and summary."""
    
    # Signal emitted when portfolio data changes
    portfolio_changed = pyqtSignal()
    
    # Column indices for easier reference
    COL_INSTRUMENT = 0
    COL_POSITION = 1
    COL_LAST_PRICE = 2
    COL_MARKET_VALUE = 3
    COL_MARKET_VALUE_EUR = 4
    COL_COST_BASIS = 5
    COL_ALLOCATION = 6
    COL_TARGET = 7
    COL_DIFF_TARGET = 8
    COL_UNREALIZED_PNL = 9
    
    def __init__(self, calculator: PortfolioCalculator, settings_store: SettingsStore, parent=None):
        super().__init__(parent)
        self.calculator = calculator
        self.settings_store = settings_store
        self._updating_free_cash = False  # Guard against double-processing
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        
        # Holdings table
        self.table = QTableWidget()
        self.setup_table()
        layout.addWidget(self.table)
        
        # Summary section
        summary_frame = QFrame()
        summary_frame.setFrameShape(QFrame.Shape.StyledPanel)
        summary_layout = QHBoxLayout(summary_frame)
        
        # Total Invested (read-only) - in EUR
        summary_layout.addWidget(QLabel("Total Invested (EUR):"))
        self.total_invested_label = QLabel("€0.00")
        self.total_invested_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        summary_layout.addWidget(self.total_invested_label)
        
        summary_layout.addSpacing(30)
        
        # Free Cash (editable)
        summary_layout.addWidget(QLabel("Free Cash:"))
        self.free_cash_input = QLineEdit("0.00")
        self.free_cash_input.setValidator(QDoubleValidator(0, 999999999, 2))
        self.free_cash_input.setMaximumWidth(120)
        self.free_cash_input.editingFinished.connect(self.on_free_cash_changed)
        self.free_cash_input.returnPressed.connect(self.on_free_cash_changed)
        summary_layout.addWidget(self.free_cash_input)
        
        summary_layout.addSpacing(30)
        
        # Total (read-only)
        summary_layout.addWidget(QLabel("Total:"))
        self.total_label = QLabel("€0.00")
        self.total_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #2e7d32;")
        summary_layout.addWidget(self.total_label)
        
        summary_layout.addStretch()
        
        layout.addWidget(summary_frame)
    
    def setup_table(self):
        """Set up the holdings table."""
        columns = [
            "Instrument", "Position", "Last Price", "Market Value",
            "Value (EUR)", "Cost Basis", "Allocation %",
            "Target %", "Diff w/ Target", "Unrealized P&L"
        ]
        
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        
        # Set column resize modes
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(self.COL_INSTRUMENT, QHeaderView.ResizeMode.Stretch)
        for i in range(1, len(columns)):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        
        # Enable sorting
        self.table.setSortingEnabled(True)
        
        # Connect cell change signal
        self.table.cellChanged.connect(self.on_cell_changed)
    
    def refresh(self):
        """Refresh the table with current portfolio data."""
        self.table.blockSignals(True)  # Prevent triggering cellChanged
        
        portfolio = self.calculator.portfolio
        allocations = self.calculator.get_allocations()
        
        # Create allocation lookup
        alloc_map = {a.instrument: a for a in allocations}
        
        self.table.setRowCount(len(portfolio.holdings))
        
        for row, holding in enumerate(portfolio.holdings):
            alloc = alloc_map.get(holding.instrument)
            
            # Instrument (editable)
            item = QTableWidgetItem(holding.instrument)
            self.table.setItem(row, self.COL_INSTRUMENT, item)
            
            # Position (editable)
            item = QTableWidgetItem(f"{holding.position:.2f}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, self.COL_POSITION, item)
            
            # Last Price (editable) - in instrument currency
            item = QTableWidgetItem(f"{holding.last_price:.2f}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, self.COL_LAST_PRICE, item)
            
            # Market Value (read-only) - in instrument currency
            currency_symbol = self.get_currency_symbol(holding.currency)
            item = QTableWidgetItem(f"{currency_symbol}{holding.market_value:,.2f}")
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, self.COL_MARKET_VALUE, item)
            
            # Market Value (EUR) - converted
            market_value_eur = self.settings_store.convert_to_eur(holding.market_value, holding.currency)
            item = QTableWidgetItem(f"€{market_value_eur:,.2f}")
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, self.COL_MARKET_VALUE_EUR, item)
            
            # Cost Basis (editable)
            item = QTableWidgetItem(f"{holding.cost_basis:.2f}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, self.COL_COST_BASIS, item)
            
            # Allocation % (read-only, calculated)
            alloc_pct = alloc.allocation_with_cash if alloc else 0
            item = QTableWidgetItem(f"{alloc_pct * 100:.2f}%")
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, self.COL_ALLOCATION, item)
            
            # Target % (editable)
            item = QTableWidgetItem(f"{holding.target_allocation * 100:.1f}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, self.COL_TARGET, item)
            
            # Diff w/ Target (read-only, calculated)
            diff = alloc.diff_with_target if alloc else 0
            diff_text = f"{diff * 100:+.2f}%"
            item = QTableWidgetItem(diff_text)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            # Color based on positive/negative
            if diff > 0.001:
                item.setForeground(Qt.GlobalColor.darkGreen)
            elif diff < -0.001:
                item.setForeground(Qt.GlobalColor.darkRed)
            self.table.setItem(row, self.COL_DIFF_TARGET, item)
            
            # Unrealized P&L (editable)
            item = QTableWidgetItem(f"{holding.unrealized_pnl:.2f}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            if holding.unrealized_pnl > 0:
                item.setForeground(Qt.GlobalColor.darkGreen)
            elif holding.unrealized_pnl < 0:
                item.setForeground(Qt.GlobalColor.darkRed)
            self.table.setItem(row, self.COL_UNREALIZED_PNL, item)
        
        # Update summary
        self.update_summary()
        
        self.table.blockSignals(False)
    
    def get_currency_symbol(self, currency: str) -> str:
        """Get the symbol for a currency."""
        symbols = {
            'EUR': '€',
            'USD': '$',
            'GBP': '£',
            'CNH': '¥',
            'CNY': '¥',
            'JPY': '¥',
            'CHF': 'Fr.',
        }
        return symbols.get(currency, f"{currency} ")
    
    def update_summary(self):
        """Update the summary labels."""
        summary = self.calculator.get_summary()
        self.total_invested_label.setText(f"€{summary['total_invested_eur']:,.2f}")
        self.total_label.setText(f"€{summary['total_eur']:,.2f}")
        
        # Update free cash input if it differs
        current_free_cash = float(self.free_cash_input.text() or 0)
        if abs(current_free_cash - summary['free_cash']) > 0.01:
            self.free_cash_input.blockSignals(True)
            self.free_cash_input.setText(f"{summary['free_cash']:.2f}")
            self.free_cash_input.blockSignals(False)
    
    def on_free_cash_changed(self):
        """Handle free cash input change."""
        if self._updating_free_cash:
            return
        
        try:
            self._updating_free_cash = True
            value = float(self.free_cash_input.text() or 0)
            self.calculator.set_free_cash(value)
            self.refresh()
            self.portfolio_changed.emit()
        except ValueError:
            pass
        finally:
            self._updating_free_cash = False
    
    def on_cell_changed(self, row: int, col: int):
        """Handle cell value change."""
        if row >= len(self.calculator.portfolio.holdings):
            return
        
        item = self.table.item(row, col)
        if not item:
            return
        
        holding = self.calculator.portfolio.holdings[row]
        text = item.text().strip()
        
        try:
            if col == self.COL_INSTRUMENT:
                # Update instrument name
                if text:
                    holding.instrument = text
                    self.portfolio_changed.emit()
            
            elif col == self.COL_POSITION:
                # Update position and recalculate market value
                value = float(text.replace(',', ''))
                holding.position = value
                holding.market_value = holding.position * holding.last_price
                self.refresh()
                self.portfolio_changed.emit()
            
            elif col == self.COL_LAST_PRICE:
                # Update last price and recalculate market value
                value = float(text.replace(',', ''))
                holding.last_price = value
                holding.market_value = holding.position * holding.last_price
                self.refresh()
                self.portfolio_changed.emit()
            
            elif col == self.COL_COST_BASIS:
                # Update cost basis
                value = float(text.replace(',', ''))
                holding.cost_basis = value
                self.refresh()
                self.portfolio_changed.emit()
            
            elif col == self.COL_TARGET:
                # Update target allocation (percentage)
                value = float(text.replace(',', '')) / 100
                holding.target_allocation = value
                self.refresh()
                self.portfolio_changed.emit()
            
            elif col == self.COL_UNREALIZED_PNL:
                # Update unrealized P&L
                value = float(text.replace(',', ''))
                holding.unrealized_pnl = value
                self.refresh()
                self.portfolio_changed.emit()
        
        except ValueError:
            # Invalid input, refresh to show original value
            self.refresh()
