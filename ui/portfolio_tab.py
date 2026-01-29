"""Portfolio table view for Portfolio Tracker."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QLabel, QLineEdit, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDoubleValidator, QColor, QBrush

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
    COL_DIFF_TARGET_PCT = 8  # Renamed: Diff w/ Target, %
    COL_DIFF_IN_CASH = 9     # New: Diff in Cash
    COL_DIFF_IN_SHARES = 10  # New: Diff in Shares
    COL_UNREALIZED_PNL = 11
    
    # Colors for alternating rows
    ROW_COLOR_EVEN = QColor(255, 255, 255)  # White
    ROW_COLOR_ODD = QColor(245, 245, 250)   # Light gray-blue
    
    # Highlight color for target-related columns
    TARGET_HIGHLIGHT_COLOR = QColor(255, 250, 230)  # Light yellow/cream
    
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
            "Target %", "Diff w/ Target, %", "Diff in Cash", "Diff in Shares",
            "Unrealized P&L"
        ]
        
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        
        # Set column resize modes
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(self.COL_INSTRUMENT, QHeaderView.ResizeMode.Stretch)
        for i in range(1, len(columns)):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        
        # Enable column reordering via drag-and-drop
        header.setSectionsMovable(True)
        header.sectionMoved.connect(self.on_column_moved)
        
        # Enable sorting
        self.table.setSortingEnabled(True)
        
        # Disable alternating row colors from Qt (we'll do it manually for more control)
        self.table.setAlternatingRowColors(False)
        
        # Connect cell change signal
        self.table.cellChanged.connect(self.on_cell_changed)
        
        # Restore saved column order
        self.restore_column_order()
    
    def on_column_moved(self, logical_index: int, old_visual: int, new_visual: int):
        """Handle column reorder - save new order."""
        header = self.table.horizontalHeader()
        order = [header.logicalIndex(i) for i in range(header.count())]
        self.settings_store.set_column_order('portfolio', order)
    
    def restore_column_order(self):
        """Restore saved column order."""
        order = self.settings_store.get_column_order('portfolio')
        if order:
            header = self.table.horizontalHeader()
            for visual_index, logical_index in enumerate(order):
                current_visual = header.visualIndex(logical_index)
                if current_visual != visual_index:
                    header.moveSection(current_visual, visual_index)
    
    def get_row_background(self, row: int, col: int) -> QColor:
        """Get background color for a cell based on row and column."""
        # Target-related columns get highlight color
        if col in (self.COL_DIFF_TARGET_PCT, self.COL_DIFF_IN_CASH, self.COL_DIFF_IN_SHARES):
            # Blend highlight with alternating color
            if row % 2 == 0:
                return QColor(255, 248, 220)  # Light yellow for even rows
            else:
                return QColor(250, 243, 210)  # Slightly darker yellow for odd rows
        
        # Regular alternating colors
        if row % 2 == 0:
            return self.ROW_COLOR_EVEN
        else:
            return self.ROW_COLOR_ODD
    
    def refresh(self):
        """Refresh the table with current portfolio data."""
        self.table.blockSignals(True)  # Prevent triggering cellChanged
        
        portfolio = self.calculator.portfolio
        allocations = self.calculator.get_allocations()
        
        # Create allocation lookup
        alloc_map = {a.instrument: a for a in allocations}
        
        # Get total portfolio value in EUR for calculating diff in cash
        total_eur = self.calculator.get_total_eur()
        
        self.table.setRowCount(len(portfolio.holdings))
        
        for row, holding in enumerate(portfolio.holdings):
            alloc = alloc_map.get(holding.instrument)
            currency_symbol = self.get_currency_symbol(holding.currency)
            
            # Calculate diff values
            diff_pct = alloc.diff_with_target if alloc else 0
            
            # Diff in cash: (target_allocation - current_allocation) * total_portfolio_EUR * (1/exchange_rate)
            # This gives the amount in the instrument's currency
            exchange_rate = self.settings_store.get_exchange_rate(holding.currency)
            if exchange_rate > 0:
                diff_in_cash_eur = diff_pct * total_eur
                diff_in_cash = diff_in_cash_eur / exchange_rate  # Convert to instrument currency
            else:
                diff_in_cash = 0
            
            # Diff in shares: diff_in_cash / last_price
            if holding.last_price > 0:
                diff_in_shares = diff_in_cash / holding.last_price
            else:
                diff_in_shares = 0
            
            # Instrument (editable)
            item = QTableWidgetItem(holding.instrument)
            item.setBackground(QBrush(self.get_row_background(row, self.COL_INSTRUMENT)))
            self.table.setItem(row, self.COL_INSTRUMENT, item)
            
            # Position (editable)
            item = QTableWidgetItem(f"{holding.position:.2f}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            item.setBackground(QBrush(self.get_row_background(row, self.COL_POSITION)))
            self.table.setItem(row, self.COL_POSITION, item)
            
            # Last Price (editable) - in instrument currency
            item = QTableWidgetItem(f"{holding.last_price:.2f}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            item.setBackground(QBrush(self.get_row_background(row, self.COL_LAST_PRICE)))
            self.table.setItem(row, self.COL_LAST_PRICE, item)
            
            # Market Value (read-only) - in instrument currency
            item = QTableWidgetItem(f"{currency_symbol}{holding.market_value:,.2f}")
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            item.setBackground(QBrush(self.get_row_background(row, self.COL_MARKET_VALUE)))
            self.table.setItem(row, self.COL_MARKET_VALUE, item)
            
            # Market Value (EUR) - converted
            market_value_eur = self.settings_store.convert_to_eur(holding.market_value, holding.currency)
            item = QTableWidgetItem(f"€{market_value_eur:,.2f}")
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            item.setBackground(QBrush(self.get_row_background(row, self.COL_MARKET_VALUE_EUR)))
            self.table.setItem(row, self.COL_MARKET_VALUE_EUR, item)
            
            # Cost Basis (editable)
            item = QTableWidgetItem(f"{holding.cost_basis:.2f}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            item.setBackground(QBrush(self.get_row_background(row, self.COL_COST_BASIS)))
            self.table.setItem(row, self.COL_COST_BASIS, item)
            
            # Allocation % (read-only, calculated)
            alloc_pct = alloc.allocation_with_cash if alloc else 0
            item = QTableWidgetItem(f"{alloc_pct * 100:.2f}%")
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            item.setBackground(QBrush(self.get_row_background(row, self.COL_ALLOCATION)))
            self.table.setItem(row, self.COL_ALLOCATION, item)
            
            # Target % (editable)
            item = QTableWidgetItem(f"{holding.target_allocation * 100:.1f}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            item.setBackground(QBrush(self.get_row_background(row, self.COL_TARGET)))
            self.table.setItem(row, self.COL_TARGET, item)
            
            # Diff w/ Target, % (read-only, calculated) - HIGHLIGHTED
            diff_text = f"{diff_pct * 100:+.2f}%"
            item = QTableWidgetItem(diff_text)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            item.setBackground(QBrush(self.get_row_background(row, self.COL_DIFF_TARGET_PCT)))
            # Color text based on positive/negative
            if diff_pct > 0.001:
                item.setForeground(Qt.GlobalColor.darkGreen)
            elif diff_pct < -0.001:
                item.setForeground(Qt.GlobalColor.darkRed)
            self.table.setItem(row, self.COL_DIFF_TARGET_PCT, item)
            
            # Diff in Cash (read-only, calculated) - HIGHLIGHTED
            item = QTableWidgetItem(f"{currency_symbol}{diff_in_cash:+,.2f}")
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            item.setBackground(QBrush(self.get_row_background(row, self.COL_DIFF_IN_CASH)))
            if diff_in_cash > 0.01:
                item.setForeground(Qt.GlobalColor.darkGreen)
            elif diff_in_cash < -0.01:
                item.setForeground(Qt.GlobalColor.darkRed)
            self.table.setItem(row, self.COL_DIFF_IN_CASH, item)
            
            # Diff in Shares (read-only, calculated) - HIGHLIGHTED
            item = QTableWidgetItem(f"{diff_in_shares:+,.2f}")
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            item.setBackground(QBrush(self.get_row_background(row, self.COL_DIFF_IN_SHARES)))
            if diff_in_shares > 0.01:
                item.setForeground(Qt.GlobalColor.darkGreen)
            elif diff_in_shares < -0.01:
                item.setForeground(Qt.GlobalColor.darkRed)
            self.table.setItem(row, self.COL_DIFF_IN_SHARES, item)
            
            # Unrealized P&L (editable)
            item = QTableWidgetItem(f"{holding.unrealized_pnl:.2f}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            item.setBackground(QBrush(self.get_row_background(row, self.COL_UNREALIZED_PNL)))
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
