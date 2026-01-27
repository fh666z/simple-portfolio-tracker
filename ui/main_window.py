"""Main window for Portfolio Tracker."""
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QTabWidget, QPushButton,
    QHBoxLayout, QMessageBox, QStatusBar
)
from PyQt6.QtCore import Qt

from core.models import Portfolio, Holding
from core.calculator import PortfolioCalculator
from core.data_parser import parse_file
from core.ocr_parser import parse_image_file, check_tesseract
from core.persistence import MappingsStore, SettingsStore, PortfolioStore

from .portfolio_tab import PortfolioTab
from .stats_tab import StatsTab
from .currency_tab import CurrencyTab
from .import_dialog import ImportDialog
from .review_dialog import ReviewDialog


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        
        # Initialize stores
        self.mappings_store = MappingsStore()
        self.settings_store = SettingsStore()
        self.portfolio_store = PortfolioStore()
        
        # Initialize calculator with empty or loaded portfolio
        portfolio = self.portfolio_store.load() or Portfolio()
        self.calculator = PortfolioCalculator(portfolio, self.settings_store)
        
        # Apply saved mappings to loaded holdings
        self.mappings_store.apply_mappings(self.calculator.portfolio.holdings)
        
        # Set free cash from settings
        saved_free_cash = self.settings_store.get('free_cash', 0)
        self.calculator.set_free_cash(saved_free_cash)
        
        self.setup_ui()
        self.refresh_all()
    
    def setup_ui(self):
        """Set up the main window UI."""
        self.setWindowTitle("Portfolio Tracker")
        self.setMinimumSize(1100, 650)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Top toolbar with New Input button
        toolbar_layout = QHBoxLayout()
        
        new_input_btn = QPushButton("New Input")
        new_input_btn.setStyleSheet("""
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
        new_input_btn.clicked.connect(self.on_new_input)
        toolbar_layout.addWidget(new_input_btn)
        
        toolbar_layout.addStretch()
        
        layout.addLayout(toolbar_layout)
        
        # Tab widget
        self.tabs = QTabWidget()
        
        # Portfolio tab
        self.portfolio_tab = PortfolioTab(self.calculator, self.settings_store)
        self.portfolio_tab.portfolio_changed.connect(self.on_portfolio_changed)
        self.tabs.addTab(self.portfolio_tab, "Portfolio")
        
        # Stats tab
        self.stats_tab = StatsTab(self.calculator)
        self.tabs.addTab(self.stats_tab, "Statistics")
        
        # Currency Exchange tab
        self.currency_tab = CurrencyTab(self.settings_store)
        self.currency_tab.rates_changed.connect(self.on_rates_changed)
        self.tabs.addTab(self.currency_tab, "Currency Exchange")
        
        layout.addWidget(self.tabs)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.update_status_bar()
        
        # Restore window geometry
        geometry = self.settings_store.get('window_geometry')
        if geometry:
            try:
                self.restoreGeometry(bytes.fromhex(geometry))
            except Exception:
                pass
    
    def closeEvent(self, event):
        """Handle window close event."""
        # Save window geometry
        self.settings_store.set('window_geometry', self.saveGeometry().toHex().data().decode())
        
        # Save portfolio and mappings
        self.save_all()
        
        event.accept()
    
    def refresh_all(self):
        """Refresh all views."""
        self.portfolio_tab.refresh()
        self.stats_tab.refresh()
        self.update_status_bar()
    
    def update_status_bar(self):
        """Update status bar with portfolio info."""
        summary = self.calculator.get_summary()
        self.status_bar.showMessage(
            f"Holdings: {summary['num_holdings']} | "
            f"Total Invested (EUR): €{summary['total_invested_eur']:,.2f} | "
            f"Total (EUR): €{summary['total_eur']:,.2f}"
        )
    
    def save_all(self):
        """Save all data."""
        # Save portfolio
        self.portfolio_store.save(self.calculator.portfolio)
        
        # Save mappings from current holdings
        self.mappings_store.update_from_holdings(self.calculator.portfolio.holdings)
        
        # Save free cash to settings
        self.settings_store.set('free_cash', self.calculator.portfolio.free_cash)
    
    def on_portfolio_changed(self):
        """Handle portfolio data change."""
        self.stats_tab.refresh()
        self.update_status_bar()
        self.save_all()
    
    def on_rates_changed(self):
        """Handle exchange rate change."""
        # Refresh all views to recalculate with new rates
        self.refresh_all()
    
    def on_new_input(self):
        """Handle new input button click."""
        dialog = ImportDialog(self)
        dialog.file_selected.connect(self.process_import_file)
        dialog.exec()
    
    def process_import_file(self, file_path: str):
        """Process an imported file."""
        path = Path(file_path)
        suffix = path.suffix.lower()
        
        try:
            # Parse file based on type
            if suffix in ('.png', '.jpg', '.jpeg'):
                # Check Tesseract availability
                if not check_tesseract():
                    QMessageBox.warning(
                        self,
                        "Tesseract Not Found",
                        "Tesseract OCR is required for image processing.\n\n"
                        "Please install Tesseract:\n"
                        "- Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki\n"
                        "- Make sure to add it to your PATH"
                    )
                    return
                
                holdings = parse_image_file(file_path)
            else:
                holdings = parse_file(file_path)
            
            if not holdings:
                QMessageBox.warning(
                    self,
                    "No Data Found",
                    f"Could not extract any portfolio data from:\n{file_path}"
                )
                return
            
            # Show review dialog
            review_dialog = ReviewDialog(holdings, file_path, self)
            review_dialog.data_confirmed.connect(self.on_data_confirmed)
            review_dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Import Error",
                f"Error importing file:\n{str(e)}"
            )
    
    def on_data_confirmed(self, holdings: list[Holding]):
        """Handle confirmed import data."""
        # Apply existing mappings to new holdings
        self.mappings_store.apply_mappings(holdings)
        
        # Add/update holdings in portfolio
        self.calculator.portfolio.add_or_update_holdings(holdings)
        
        # Refresh views
        self.refresh_all()
        
        # Save
        self.save_all()
        
        # Show success message
        self.status_bar.showMessage(
            f"Imported {len(holdings)} holdings successfully!",
            5000  # Show for 5 seconds
        )
