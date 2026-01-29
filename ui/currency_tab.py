"""Currency Exchange tab for Portfolio Tracker."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QLabel, QPushButton, QLineEdit, QMessageBox, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDoubleValidator

from core.persistence import SettingsStore
from .utils import setup_movable_columns, ALIGN_RIGHT_CENTER


class CurrencyTab(QWidget):
    """Tab for managing currency exchange rates."""
    
    # Signal emitted when exchange rates change
    rates_changed = pyqtSignal()
    
    def __init__(self, settings_store: SettingsStore, parent=None):
        super().__init__(parent)
        self.settings_store = settings_store
        self.setup_ui()
        self.refresh()
    
    def setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        
        # Title and description
        title_label = QLabel("Currency Exchange Rates")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title_label)
        
        desc_label = QLabel(
            "Enter the exchange rate for each currency to EUR. "
            "Rate meaning: 1 [Currency] = [Rate] EUR"
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(desc_label)
        
        # Exchange rates table
        rates_group = QGroupBox("Exchange Rates")
        rates_layout = QVBoxLayout(rates_group)
        
        self.rates_table = QTableWidget()
        self.rates_table.setColumnCount(2)
        self.rates_table.setHorizontalHeaderLabels(["Currency", "Rate to EUR"])
        
        header = self.rates_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        # Enable column reordering with persistence
        setup_movable_columns(self.rates_table, 'currency_rates', self.settings_store)
        
        self.rates_table.cellChanged.connect(self.on_rate_changed)
        
        rates_layout.addWidget(self.rates_table)
        layout.addWidget(rates_group)
        
        # Add currency section
        add_group = QGroupBox("Add New Currency")
        add_layout = QHBoxLayout(add_group)
        
        add_layout.addWidget(QLabel("Currency Code:"))
        self.new_currency_input = QLineEdit()
        self.new_currency_input.setPlaceholderText("e.g., JPY")
        self.new_currency_input.setMaximumWidth(100)
        add_layout.addWidget(self.new_currency_input)
        
        add_layout.addWidget(QLabel("Rate to EUR:"))
        self.new_rate_input = QLineEdit()
        self.new_rate_input.setPlaceholderText("e.g., 0.0062")
        self.new_rate_input.setValidator(QDoubleValidator(0, 999999, 6))
        self.new_rate_input.setMaximumWidth(100)
        add_layout.addWidget(self.new_rate_input)
        
        add_btn = QPushButton("Add Currency")
        add_btn.clicked.connect(self.on_add_currency)
        add_layout.addWidget(add_btn)
        
        add_layout.addStretch()
        
        layout.addWidget(add_group)
        
        # Info section
        info_label = QLabel(
            "Note: EUR always has a rate of 1.0 and cannot be modified. "
            "All portfolio values are converted to EUR for allocation calculations."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #888; font-style: italic; margin-top: 10px;")
        layout.addWidget(info_label)
        
        layout.addStretch()
    
    def refresh(self):
        """Refresh the exchange rates table."""
        self.rates_table.blockSignals(True)
        
        currencies = self.settings_store.get_currencies()
        rates = self.settings_store.get_exchange_rates()
        
        self.rates_table.setRowCount(len(currencies))
        
        for row, currency in enumerate(currencies):
            # Currency name (read-only)
            item = QTableWidgetItem(currency)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            if currency == "EUR":
                item.setBackground(Qt.GlobalColor.lightGray)
            self.rates_table.setItem(row, 0, item)
            
            # Rate (editable, except EUR)
            rate = rates.get(currency, 1.0)
            item = QTableWidgetItem(f"{rate:.6f}")
            item.setTextAlignment(ALIGN_RIGHT_CENTER)
            
            if currency == "EUR":
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                item.setBackground(Qt.GlobalColor.lightGray)
            
            self.rates_table.setItem(row, 1, item)
        
        self.rates_table.blockSignals(False)
    
    def on_rate_changed(self, row: int, col: int):
        """Handle rate value change."""
        if col != 1:  # Only rate column
            return
        
        currency_item = self.rates_table.item(row, 0)
        rate_item = self.rates_table.item(row, 1)
        
        if not currency_item or not rate_item:
            return
        
        currency = currency_item.text()
        
        # Don't allow EUR rate change
        if currency == "EUR":
            self.refresh()
            return
        
        try:
            rate = float(rate_item.text())
            if rate <= 0:
                raise ValueError("Rate must be positive")
            
            self.settings_store.set_exchange_rate(currency, rate)
            self.rates_changed.emit()
        except ValueError:
            # Revert to stored value
            self.refresh()
            QMessageBox.warning(
                self,
                "Invalid Rate",
                "Please enter a valid positive number for the exchange rate."
            )
    
    def on_add_currency(self):
        """Handle add currency button click."""
        currency = self.new_currency_input.text().strip().upper()
        rate_text = self.new_rate_input.text().strip()
        
        if not currency:
            QMessageBox.warning(self, "Error", "Please enter a currency code.")
            return
        
        if len(currency) > 5:
            QMessageBox.warning(self, "Error", "Currency code should be 3-5 characters.")
            return
        
        if not rate_text:
            QMessageBox.warning(self, "Error", "Please enter an exchange rate.")
            return
        
        try:
            rate = float(rate_text)
            if rate <= 0:
                raise ValueError()
        except ValueError:
            QMessageBox.warning(self, "Error", "Please enter a valid positive exchange rate.")
            return
        
        # Check if currency already exists
        currencies = self.settings_store.get_currencies()
        if currency in currencies:
            QMessageBox.warning(self, "Error", f"Currency '{currency}' already exists.")
            return
        
        # Add currency and rate
        self.settings_store.add_currency(currency)
        self.settings_store.set_exchange_rate(currency, rate)
        
        # Clear inputs
        self.new_currency_input.clear()
        self.new_rate_input.clear()
        
        # Refresh table
        self.refresh()
        self.rates_changed.emit()
