"""Portfolio table view for Portfolio Tracker."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QLabel, QLineEdit, QFrame, QPushButton, QMenu, QMessageBox,
    QStackedWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDoubleValidator, QBrush, QAction

from core.calculator import PortfolioCalculator
from core.models import AssetType, Region
from core.persistence import SettingsStore
from .utils import (
    NumericTableItem, get_currency_symbol, parse_numeric_text,
    get_alternating_row_color, get_highlight_row_color,
    setup_movable_columns, ALIGN_RIGHT_CENTER
)


class PortfolioTab(QWidget):
    """Main portfolio table view with holdings and summary."""
    
    # Signal emitted when portfolio data changes
    portfolio_changed = pyqtSignal()
    # Signal emitted when user requests import from empty state
    import_requested = pyqtSignal()
    
    # Column indices for easier reference
    COL_DELETE = 0
    COL_INSTRUMENT = 1
    COL_POSITION = 2
    COL_LAST_PRICE = 3
    COL_MARKET_VALUE = 4
    COL_MARKET_VALUE_EUR = 5
    COL_COST_BASIS = 6
    COL_ALLOCATION = 7
    COL_TARGET = 8
    COL_DIFF_TARGET_PCT = 9  # Diff w/ Target, %
    COL_DIFF_IN_CASH = 10     # Diff in Cash
    COL_DIFF_IN_SHARES = 11  # Diff in Shares
    COL_UNREALIZED_PNL = 12
    
    # Columns that should be highlighted (target-related)
    HIGHLIGHT_COLUMNS = {COL_DIFF_TARGET_PCT, COL_DIFF_IN_CASH, COL_DIFF_IN_SHARES}
    
    def __init__(self, calculator: PortfolioCalculator, settings_store: SettingsStore, parent=None):
        super().__init__(parent)
        self.calculator = calculator
        self.settings_store = settings_store
        self._updating_free_cash = False  # Guard against double-processing
        self._filter_text = ""  # Current search filter
        self._filter_type = None  # Current type filter (None = all)
        self._filter_region = None  # Current region filter (None = all)
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        
        # Stacked widget to switch between empty state and content
        self.stacked_widget = QStackedWidget()
        
        # === Empty state widget ===
        empty_widget = QWidget()
        empty_layout = QVBoxLayout(empty_widget)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        empty_icon = QLabel("📊")
        empty_icon.setStyleSheet("font-size: 64px;")
        empty_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_icon)
        
        empty_title = QLabel("No Holdings Yet")
        empty_title.setStyleSheet("font-size: 24px; font-weight: bold; color: #333; margin-top: 10px;")
        empty_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_title)
        
        empty_desc = QLabel("Import your portfolio data to get started tracking\nyour investments and allocation targets.")
        empty_desc.setStyleSheet("font-size: 14px; color: #666; margin: 10px 0;")
        empty_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_desc)
        
        import_btn = QPushButton("Import Portfolio Data")
        import_btn.setStyleSheet("""
            QPushButton {
                padding: 15px 30px;
                font-size: 16px;
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                margin-top: 20px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        import_btn.clicked.connect(self.request_import)
        
        btn_container = QHBoxLayout()
        btn_container.addStretch()
        btn_container.addWidget(import_btn)
        btn_container.addStretch()
        empty_layout.addLayout(btn_container)
        
        empty_layout.addStretch()
        
        self.stacked_widget.addWidget(empty_widget)  # Index 0: empty state
        
        # === Content widget (table + filters) ===
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        # Filter bar
        filter_frame = QFrame()
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(0, 0, 0, 5)
        
        # Search input
        filter_layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter by instrument name...")
        self.search_input.setMaximumWidth(250)
        self.search_input.textChanged.connect(self.on_filter_changed)
        self.search_input.setClearButtonEnabled(True)
        filter_layout.addWidget(self.search_input)
        
        filter_layout.addSpacing(20)
        
        # Type filter buttons
        filter_layout.addWidget(QLabel("Type:"))
        self.type_filter_buttons = {}
        
        all_type_btn = QPushButton("All")
        all_type_btn.setCheckable(True)
        all_type_btn.setChecked(True)
        all_type_btn.setStyleSheet(self._get_filter_btn_style())
        all_type_btn.clicked.connect(lambda: self.set_type_filter(None))
        filter_layout.addWidget(all_type_btn)
        self.type_filter_buttons[None] = all_type_btn
        
        for asset_type in [AssetType.EQUITY, AssetType.BONDS, AssetType.COMMODITY, AssetType.THEMATIC, AssetType.REIT]:
            btn = QPushButton(asset_type.value)
            btn.setCheckable(True)
            btn.setStyleSheet(self._get_filter_btn_style())
            btn.clicked.connect(lambda checked, t=asset_type: self.set_type_filter(t))
            filter_layout.addWidget(btn)
            self.type_filter_buttons[asset_type] = btn
        
        filter_layout.addStretch()
        
        # Clear filters button
        clear_btn = QPushButton("Clear Filters")
        clear_btn.setStyleSheet("""
            QPushButton {
                padding: 4px 10px;
                font-size: 12px;
                background-color: transparent;
                color: #666;
                border: 1px solid #ccc;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
                border-color: #999;
            }
        """)
        clear_btn.clicked.connect(self.clear_filters)
        filter_layout.addWidget(clear_btn)
        
        content_layout.addWidget(filter_frame)
        
        # Holdings table
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.setup_table()
        content_layout.addWidget(self.table)
        
        self.stacked_widget.addWidget(content_widget)  # Index 1: content
        
        layout.addWidget(self.stacked_widget)
        
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
        summary_layout.addWidget(QLabel("Free Cash (EUR):"))
        self.free_cash_input = QLineEdit("0.00")
        self.free_cash_input.setValidator(QDoubleValidator(0, 999999999, 2))
        self.free_cash_input.setMaximumWidth(120)
        self.free_cash_input.editingFinished.connect(self.on_free_cash_changed)
        self.free_cash_input.returnPressed.connect(self.on_free_cash_changed)
        summary_layout.addWidget(self.free_cash_input)
        
        summary_layout.addSpacing(30)
        
        # Total (read-only)
        summary_layout.addWidget(QLabel("Total Cash(EUR):"))
        self.total_label = QLabel("€0.00")
        self.total_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #2e7d32;")
        summary_layout.addWidget(self.total_label)
        
        summary_layout.addStretch()
        
        layout.addWidget(summary_frame)
    
    def setup_table(self):
        """Set up the holdings table."""
        columns = [
            "", "Instrument", "Position", "Last Price", "Market Value",
            "Value in (EUR)", "Cost Basis", "Allocation %",
            "Target %", "Diff w/ Target, %", "Diff in Cash", "Diff in Shares",
            "Unrealized P&L"
        ]
        
        # Column tooltips for better UX
        column_tooltips = {
            self.COL_DELETE: "Click to delete this holding",
            self.COL_INSTRUMENT: "Instrument name/ticker symbol",
            self.COL_POSITION: "Number of shares/units held (editable)",
            self.COL_LAST_PRICE: "Current price per share (editable)",
            self.COL_MARKET_VALUE: "Position × Last Price (in original currency)",
            self.COL_MARKET_VALUE_EUR: "Market value converted to EUR",
            self.COL_COST_BASIS: "Total cost of position (editable)",
            self.COL_ALLOCATION: "Current allocation % (excluding free cash)",
            self.COL_TARGET: "Target allocation % (editable)",
            self.COL_DIFF_TARGET_PCT: "Target % minus Current % (positive = underweight)",
            self.COL_DIFF_IN_CASH: "Amount to buy/sell to reach target",
            self.COL_DIFF_IN_SHARES: "Number of shares to buy/sell to reach target",
            self.COL_UNREALIZED_PNL: "Unrealized profit/loss (editable)",
        }
        
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        
        # Set header tooltips
        for col, tooltip in column_tooltips.items():
            self.table.horizontalHeaderItem(col).setToolTip(tooltip)
        
        # Set column resize modes
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(self.COL_DELETE, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(self.COL_DELETE, 40)  # Small fixed width for delete button
        header.setSectionResizeMode(self.COL_INSTRUMENT, QHeaderView.ResizeMode.Stretch)
        for i in range(self.COL_POSITION, len(columns)):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        
        # Enable column reordering with persistence (skip delete column)
        setup_movable_columns(self.table, 'portfolio', self.settings_store)
        
        # Enable sorting
        self.table.setSortingEnabled(True)
        
        # Disable alternating row colors from Qt (we'll do it manually for more control)
        self.table.setAlternatingRowColors(False)
        
        # Connect cell change signal
        self.table.cellChanged.connect(self.on_cell_changed)
        
        # Enable context menu for right-click delete
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
    
    def _get_filter_btn_style(self):
        """Get the stylesheet for filter buttons."""
        return """
            QPushButton {
                padding: 4px 8px;
                font-size: 11px;
                background-color: #f8f9fa;
                color: #495057;
                border: 1px solid #dee2e6;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #adb5bd;
            }
            QPushButton:checked {
                background-color: #2196F3;
                color: white;
                border-color: #1976D2;
            }
        """
    
    def set_type_filter(self, asset_type):
        """Set the type filter and update button states."""
        self._filter_type = asset_type
        for t, btn in self.type_filter_buttons.items():
            btn.setChecked(t == asset_type)
        self.refresh()
    
    def on_filter_changed(self, text):
        """Handle search filter text change."""
        self._filter_text = text.lower().strip()
        self.refresh()
    
    def clear_filters(self):
        """Clear all filters."""
        self._filter_text = ""
        self._filter_type = None
        self._filter_region = None
        self.search_input.clear()
        for t, btn in self.type_filter_buttons.items():
            btn.setChecked(t is None)
        self.refresh()
    
    def request_import(self):
        """Request import from parent window."""
        self.import_requested.emit()
    
    def _holding_matches_filter(self, holding):
        """Check if a holding matches current filters."""
        # Text filter
        if self._filter_text:
            if self._filter_text not in holding.instrument.lower():
                return False
        
        # Type filter
        if self._filter_type is not None:
            if holding.asset_type != self._filter_type:
                return False
        
        # Region filter
        if self._filter_region is not None:
            if holding.region != self._filter_region:
                return False
        
        return True
    
    def get_row_background(self, row: int, col: int):
        """Get background color for a cell based on row and column."""
        # Target-related columns get highlight color
        if col in self.HIGHLIGHT_COLUMNS:
            return get_highlight_row_color(row)
        # Regular alternating colors
        return get_alternating_row_color(row)
    
    def refresh(self):
        """Refresh the table with current portfolio data."""
        portfolio = self.calculator.portfolio
        
        # Switch between empty state and content
        if len(portfolio.holdings) == 0:
            self.stacked_widget.setCurrentIndex(0)  # Show empty state
            self.update_summary()
            return
        else:
            self.stacked_widget.setCurrentIndex(1)  # Show content
        
        self.table.blockSignals(True)  # Prevent triggering cellChanged
        
        allocations = self.calculator.get_allocations()
        
        # Create allocation lookup
        alloc_map = {a.instrument: a for a in allocations}
        
        # Get total portfolio value in EUR for calculating diff in cash
        total_eur = self.calculator.get_total_eur()
        
        # Filter holdings based on current filters
        filtered_holdings = []
        self._row_to_holding_idx = {}  # Map visible row to actual holding index
        
        for idx, holding in enumerate(portfolio.holdings):
            if self._holding_matches_filter(holding):
                self._row_to_holding_idx[len(filtered_holdings)] = idx
                filtered_holdings.append((idx, holding))
        
        self.table.setRowCount(len(filtered_holdings))
        
        for row, (holding_idx, holding) in enumerate(filtered_holdings):
            alloc = alloc_map.get(holding.instrument)
            currency_symbol = get_currency_symbol(holding.currency)
            
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
            
            # Delete button
            delete_btn = QPushButton("×")
            delete_btn.setFixedSize(24, 24)
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #999;
                    border: none;
                    font-size: 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    color: #dc3545;
                    background-color: #fee;
                    border-radius: 12px;
                }
            """)
            delete_btn.setToolTip(f"Delete {holding.instrument}")
            delete_btn.clicked.connect(lambda checked, idx=holding_idx: self.delete_holding_by_idx(idx))
            self.table.setCellWidget(row, self.COL_DELETE, delete_btn)
            
            # Instrument (editable)
            item = QTableWidgetItem(holding.instrument)
            item.setBackground(QBrush(self.get_row_background(row, self.COL_INSTRUMENT)))
            self.table.setItem(row, self.COL_INSTRUMENT, item)
            
            # Position (editable) - numeric sorting
            item = NumericTableItem(f"{holding.position:.2f}", holding.position)
            item.setTextAlignment(ALIGN_RIGHT_CENTER)
            item.setBackground(QBrush(self.get_row_background(row, self.COL_POSITION)))
            self.table.setItem(row, self.COL_POSITION, item)
            
            # Last Price (editable) - numeric sorting
            item = NumericTableItem(f"{holding.last_price:.2f}", holding.last_price)
            item.setTextAlignment(ALIGN_RIGHT_CENTER)
            item.setBackground(QBrush(self.get_row_background(row, self.COL_LAST_PRICE)))
            self.table.setItem(row, self.COL_LAST_PRICE, item)
            
            # Market Value (read-only) - numeric sorting
            item = NumericTableItem(f"{currency_symbol}{holding.market_value:,.2f}", holding.market_value)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item.setTextAlignment(ALIGN_RIGHT_CENTER)
            item.setBackground(QBrush(self.get_row_background(row, self.COL_MARKET_VALUE)))
            self.table.setItem(row, self.COL_MARKET_VALUE, item)
            
            # Market Value (EUR) - numeric sorting
            market_value_eur = self.settings_store.convert_to_eur(holding.market_value, holding.currency)
            item = NumericTableItem(f"€{market_value_eur:,.2f}", market_value_eur)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item.setTextAlignment(ALIGN_RIGHT_CENTER)
            item.setBackground(QBrush(self.get_row_background(row, self.COL_MARKET_VALUE_EUR)))
            self.table.setItem(row, self.COL_MARKET_VALUE_EUR, item)
            
            # Cost Basis (editable) - numeric sorting
            item = NumericTableItem(f"{currency_symbol}{holding.cost_basis:,.2f}", holding.cost_basis)
            item.setTextAlignment(ALIGN_RIGHT_CENTER)
            item.setBackground(QBrush(self.get_row_background(row, self.COL_COST_BASIS)))
            self.table.setItem(row, self.COL_COST_BASIS, item)
            
            # Allocation % (read-only, calculated) - numeric sorting
            alloc_pct = alloc.allocation_with_cash if alloc else 0
            item = NumericTableItem(f"{alloc_pct * 100:.2f}%", alloc_pct)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item.setTextAlignment(ALIGN_RIGHT_CENTER)
            item.setBackground(QBrush(self.get_row_background(row, self.COL_ALLOCATION)))
            self.table.setItem(row, self.COL_ALLOCATION, item)
            
            # Target % (editable) - numeric sorting
            item = NumericTableItem(f"{holding.target_allocation * 100:.1f}", holding.target_allocation)
            item.setTextAlignment(ALIGN_RIGHT_CENTER)
            item.setBackground(QBrush(self.get_row_background(row, self.COL_TARGET)))
            self.table.setItem(row, self.COL_TARGET, item)
            
            # Diff w/ Target, % (read-only, calculated) - HIGHLIGHTED, numeric sorting
            diff_text = f"{diff_pct * 100:+.2f}%"
            item = NumericTableItem(diff_text, diff_pct)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item.setTextAlignment(ALIGN_RIGHT_CENTER)
            item.setBackground(QBrush(self.get_row_background(row, self.COL_DIFF_TARGET_PCT)))
            # Color text based on positive/negative
            if diff_pct > 0.001:
                item.setForeground(Qt.GlobalColor.darkGreen)
            elif diff_pct < -0.001:
                item.setForeground(Qt.GlobalColor.darkRed)
            self.table.setItem(row, self.COL_DIFF_TARGET_PCT, item)
            
            # Diff in Cash (read-only, calculated) - HIGHLIGHTED, numeric sorting
            item = NumericTableItem(f"{currency_symbol}{diff_in_cash:+,.2f}", diff_in_cash)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item.setTextAlignment(ALIGN_RIGHT_CENTER)
            item.setBackground(QBrush(self.get_row_background(row, self.COL_DIFF_IN_CASH)))
            if diff_in_cash > 0.01:
                item.setForeground(Qt.GlobalColor.darkGreen)
            elif diff_in_cash < -0.01:
                item.setForeground(Qt.GlobalColor.darkRed)
            self.table.setItem(row, self.COL_DIFF_IN_CASH, item)
            
            # Diff in Shares (read-only, calculated) - HIGHLIGHTED, numeric sorting
            item = NumericTableItem(f"{diff_in_shares:+,.2f}", diff_in_shares)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item.setTextAlignment(ALIGN_RIGHT_CENTER)
            item.setBackground(QBrush(self.get_row_background(row, self.COL_DIFF_IN_SHARES)))
            if diff_in_shares > 0.01:
                item.setForeground(Qt.GlobalColor.darkGreen)
            elif diff_in_shares < -0.01:
                item.setForeground(Qt.GlobalColor.darkRed)
            self.table.setItem(row, self.COL_DIFF_IN_SHARES, item)
            
            # Unrealized P&L (editable) - numeric sorting
            item = NumericTableItem(f"{holding.unrealized_pnl:.2f}", holding.unrealized_pnl)
            item.setTextAlignment(ALIGN_RIGHT_CENTER)
            item.setBackground(QBrush(self.get_row_background(row, self.COL_UNREALIZED_PNL)))
            if holding.unrealized_pnl > 0:
                item.setForeground(Qt.GlobalColor.darkGreen)
            elif holding.unrealized_pnl < 0:
                item.setForeground(Qt.GlobalColor.darkRed)
            self.table.setItem(row, self.COL_UNREALIZED_PNL, item)
        
        # Update summary
        self.update_summary()
        
        self.table.blockSignals(False)
    
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
        # Get actual holding index from row mapping
        holding_idx = self._row_to_holding_idx.get(row)
        if holding_idx is None or holding_idx >= len(self.calculator.portfolio.holdings):
            return
        
        item = self.table.item(row, col)
        if not item:
            return
        
        holding = self.calculator.portfolio.holdings[holding_idx]
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
                # Update cost basis - strip currency symbol and commas
                value = parse_numeric_text(text)
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
    
    def delete_holding(self, row: int):
        """Delete a holding at the specified visible row."""
        # Get actual holding index from row mapping
        holding_idx = self._row_to_holding_idx.get(row)
        if holding_idx is None:
            return
        self.delete_holding_by_idx(holding_idx)
    
    def delete_holding_by_idx(self, holding_idx: int):
        """Delete a holding by its actual index in the holdings list."""
        if holding_idx >= len(self.calculator.portfolio.holdings):
            return
        
        holding = self.calculator.portfolio.holdings[holding_idx]
        
        reply = QMessageBox.question(
            self,
            "Delete Holding",
            f"Are you sure you want to delete '{holding.instrument}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.calculator.portfolio.holdings.pop(holding_idx)
            self.refresh()
            self.portfolio_changed.emit()
    
    def show_context_menu(self, position):
        """Show context menu for right-click actions."""
        row = self.table.rowAt(position.y())
        holding_idx = self._row_to_holding_idx.get(row)
        if holding_idx is None or holding_idx >= len(self.calculator.portfolio.holdings):
            return
        
        holding = self.calculator.portfolio.holdings[holding_idx]
        
        menu = QMenu(self)
        
        delete_action = QAction(f"Delete '{holding.instrument}'", self)
        delete_action.triggered.connect(lambda: self.delete_holding_by_idx(holding_idx))
        menu.addAction(delete_action)
        
        menu.exec(self.table.viewport().mapToGlobal(position))
