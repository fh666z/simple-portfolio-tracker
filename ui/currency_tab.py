"""Currency Exchange tab for Portfolio Tracker."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QLabel, QPushButton, QLineEdit, QMessageBox, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QDoubleValidator

from core.persistence import SettingsStore
from core.rates_fetcher import fetch_rates
from .utils import setup_movable_columns, ALIGN_RIGHT_CENTER


class RatesFetchThread(QThread):
    """Worker thread that fetches exchange rates from the internet."""
    # Emits (rates_dict, date_str, error_msg). On success error_msg is ""; on failure rates and date are empty.
    fetch_finished = pyqtSignal(dict, str, str)

    def __init__(self, currencies: list[str], parent=None):
        super().__init__(parent)
        self.currencies = currencies

    def run(self):
        rates, date_str, error = fetch_rates(self.currencies)
        self.fetch_finished.emit(rates or {}, date_str or "", error or "")


class CurrencyTab(QWidget):
    """Tab for managing currency exchange rates."""
    
    # Signal emitted when exchange rates change
    rates_changed = pyqtSignal()
    
    def __init__(self, settings_store: SettingsStore, parent=None):
        super().__init__(parent)
        self.settings_store = settings_store
        self._fetch_thread = None
        self.setup_ui()
        self.refresh()
        self._refresh_last_updated_label()
    
    def setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        
        # Title and description
        title_label = QLabel("Currency Exchange Rates")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title_label)
        
        desc_label = QLabel(
            "Enter how many units of each currency you get for 1 EUR.\n"
            "Examples: USD rate 1.09 means €1 = $1.09  |  CNY rate 7.69 means €1 = ¥7.69"
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(desc_label)
        
        # Exchange rates table
        rates_group = QGroupBox("Exchange Rates")
        rates_layout = QVBoxLayout(rates_group)
        
        # Update from internet row
        update_row = QHBoxLayout()
        self.update_rates_btn = QPushButton("Update rates from internet")
        self.update_rates_btn.clicked.connect(self.on_update_rates_from_internet)
        update_row.addWidget(self.update_rates_btn)
        self.last_updated_label = QLabel("")
        self.last_updated_label.setStyleSheet("color: #666;")
        update_row.addWidget(self.last_updated_label)
        update_row.addStretch()
        rates_layout.addLayout(update_row)
        
        self.rates_table = QTableWidget()
        self.rates_table.setAlternatingRowColors(True)
        self.rates_table.setColumnCount(2)
        self.rates_table.setHorizontalHeaderLabels(["Currency", "Rate (per 1 EUR)"])
        
        # Set header tooltips
        self.rates_table.horizontalHeaderItem(0).setToolTip("Currency code (e.g., USD, GBP)")
        self.rates_table.horizontalHeaderItem(1).setToolTip(
            "How many units of this currency equal 1 EUR\n"
            "Example: 1.09 for USD means €1 = $1.09"
        )
        
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
        
        add_layout.addWidget(QLabel("Rate (per 1 EUR):"))
        self.new_rate_input = QLineEdit()
        self.new_rate_input.setPlaceholderText("e.g., 160.5")
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
            "Note: EUR is the base currency (rate = 1.0) and cannot be modified. "
            "All portfolio values are converted to EUR for allocation calculations.\n"
            "Tip: You can find current exchange rates at xe.com or Google."
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
        self._refresh_last_updated_label()

    def _refresh_last_updated_label(self):
        """Update the 'Last updated' label from settings."""
        date_str = self.settings_store.get_rates_last_updated()
        if date_str:
            self.last_updated_label.setText(f"Last updated: {date_str}")
        else:
            self.last_updated_label.setText("")

    def on_update_rates_from_internet(self):
        """Start fetching rates from the internet in a background thread."""
        if self._fetch_thread is not None and self._fetch_thread.isRunning():
            return
        currencies = self.settings_store.get_currencies()
        self.update_rates_btn.setEnabled(False)
        self.update_rates_btn.setText("Updating…")
        self._fetch_thread = RatesFetchThread(currencies, self)
        self._fetch_thread.fetch_finished.connect(self._on_fetch_finished)
        self._fetch_thread.finished.connect(self._on_fetch_thread_finished)
        self._fetch_thread.start()

    def _on_fetch_thread_finished(self):
        """Re-enable the update button after the thread ends."""
        self.update_rates_btn.setEnabled(True)
        self.update_rates_btn.setText("Update rates from internet")

    def _on_fetch_finished(self, rates: dict, date_str: str, error_msg: str):
        """Handle fetch result: apply rates or show error."""
        if error_msg:
            QMessageBox.warning(
                self,
                "Could not update rates",
                f"{error_msg}\n\nYour existing rates were not changed.",
            )
            return
        if not rates:
            return
        current = dict(self.settings_store.get_exchange_rates())
        for currency, rate in rates.items():
            current[currency] = rate
        self.settings_store.update_exchange_rates(current)
        if date_str:
            self.settings_store.set_rates_last_updated(date_str)
        self._refresh_last_updated_label()
        self.refresh()
        self.rates_changed.emit()
    
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
