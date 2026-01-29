"""Instrument configuration tab for Portfolio Tracker."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal

from core.models import AssetType, Region
from core.calculator import PortfolioCalculator
from core.persistence import SettingsStore


class InstrumentConfigTab(QWidget):
    """Tab for configuring instrument settings (Currency, Type, Region)."""
    
    # Signal emitted when configuration changes
    config_changed = pyqtSignal()
    
    # Column indices
    COL_INSTRUMENT = 0
    COL_CURRENCY = 1
    COL_TYPE = 2
    COL_REGION = 3
    
    def __init__(self, calculator: PortfolioCalculator, settings_store: SettingsStore, parent=None):
        super().__init__(parent)
        self.calculator = calculator
        self.settings_store = settings_store
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        
        # Configuration table
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.setup_table()
        layout.addWidget(self.table)
    
    def setup_table(self):
        """Set up the configuration table."""
        columns = ["Instrument", "Currency", "Type", "Region"]
        
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        
        # Set column resize modes
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(self.COL_INSTRUMENT, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(self.COL_CURRENCY, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_TYPE, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_REGION, QHeaderView.ResizeMode.ResizeToContents)
        
        # Enable sorting
        self.table.setSortingEnabled(True)
    
    def refresh(self):
        """Refresh the table with current portfolio data."""
        self.table.blockSignals(True)
        
        portfolio = self.calculator.portfolio
        currencies = self.settings_store.get_currencies()
        
        self.table.setRowCount(len(portfolio.holdings))
        
        for row, holding in enumerate(portfolio.holdings):
            # Instrument (read-only)
            item = QTableWidgetItem(holding.instrument)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, self.COL_INSTRUMENT, item)
            
            # Currency (editable combo)
            currency_combo = QComboBox()
            for curr in currencies:
                currency_combo.addItem(curr)
            # Add current currency if not in list
            if holding.currency not in currencies:
                currency_combo.addItem(holding.currency)
            currency_combo.setCurrentText(holding.currency)
            currency_combo.currentTextChanged.connect(
                lambda text, r=row: self.on_currency_changed(r, text)
            )
            self.table.setCellWidget(row, self.COL_CURRENCY, currency_combo)
            
            # Type (editable combo)
            type_combo = QComboBox()
            for t in AssetType:
                type_combo.addItem(t.value, t)
            type_combo.setCurrentText(holding.asset_type.value)
            type_combo.currentIndexChanged.connect(
                lambda idx, r=row: self.on_type_changed(r, idx)
            )
            self.table.setCellWidget(row, self.COL_TYPE, type_combo)
            
            # Region (editable combo)
            region_combo = QComboBox()
            for r in Region:
                region_combo.addItem(r.value, r)
            region_combo.setCurrentText(holding.region.value)
            region_combo.currentIndexChanged.connect(
                lambda idx, r=row: self.on_region_changed(r, idx)
            )
            self.table.setCellWidget(row, self.COL_REGION, region_combo)
        
        self.table.blockSignals(False)
    
    def on_currency_changed(self, row: int, currency: str):
        """Handle currency change for a holding."""
        if row < len(self.calculator.portfolio.holdings):
            self.calculator.portfolio.holdings[row].currency = currency
            self.config_changed.emit()
    
    def on_type_changed(self, row: int, index: int):
        """Handle asset type change for a holding."""
        if row < len(self.calculator.portfolio.holdings):
            combo = self.table.cellWidget(row, self.COL_TYPE)
            new_type = combo.currentData()
            self.calculator.portfolio.holdings[row].asset_type = new_type
            self.config_changed.emit()
    
    def on_region_changed(self, row: int, index: int):
        """Handle region change for a holding."""
        if row < len(self.calculator.portfolio.holdings):
            combo = self.table.cellWidget(row, self.COL_REGION)
            new_region = combo.currentData()
            self.calculator.portfolio.holdings[row].region = new_region
            self.config_changed.emit()
