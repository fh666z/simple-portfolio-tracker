"""Main window for Portfolio Tracker."""
import csv
import json
from datetime import datetime
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QTabWidget, QPushButton,
    QHBoxLayout, QMessageBox, QStatusBar, QFileDialog, QInputDialog,
    QProgressDialog, QApplication, QMenu
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QShortcut, QKeySequence, QAction

from core.models import Portfolio, Holding
from core.calculator import PortfolioCalculator
from core.data_parser import parse_file
from core.ocr_parser import parse_image_file, check_tesseract
from core.persistence import MappingsStore, SettingsStore, PortfolioStore

from .portfolio_tab import PortfolioTab
from .instrument_config_tab import InstrumentConfigTab
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
        new_input_btn.setToolTip("Import portfolio data from image or spreadsheet (Ctrl+N)")
        new_input_btn.clicked.connect(self.on_new_input)
        toolbar_layout.addWidget(new_input_btn)
        
        toolbar_layout.addStretch()
        
        # Export button with dropdown menu
        export_btn = QPushButton("Export")
        export_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                font-size: 14px;
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton::menu-indicator {
                subcontrol-position: right center;
                subcontrol-origin: padding;
                left: -4px;
            }
        """)
        export_btn.setToolTip("Export portfolio to file (Ctrl+S for JSON)")
        
        # Create export menu
        export_menu = QMenu(self)
        
        export_json_action = QAction("Export to JSON (Ctrl+S)", self)
        export_json_action.triggered.connect(self.on_save_data)
        export_menu.addAction(export_json_action)
        
        export_csv_action = QAction("Export to CSV", self)
        export_csv_action.triggered.connect(self.on_export_csv)
        export_menu.addAction(export_csv_action)
        
        export_excel_action = QAction("Export to Excel", self)
        export_excel_action.triggered.connect(self.on_export_excel)
        export_menu.addAction(export_excel_action)
        
        export_btn.setMenu(export_menu)
        toolbar_layout.addWidget(export_btn)
        
        # Load Data button
        load_btn = QPushButton("Load Data")
        load_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                font-size: 14px;
                background-color: #fd7e14;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #e96b02;
            }
        """)
        load_btn.setToolTip("Load portfolio from a JSON file (Ctrl+O)")
        load_btn.clicked.connect(self.on_load_data)
        toolbar_layout.addWidget(load_btn)
        
        toolbar_layout.addSpacing(30)  # Visual separator
        
        # Reset Data button - placed far right with spacing to prevent accidental clicks
        reset_btn = QPushButton("Reset Data")
        reset_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                font-size: 14px;
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #dc3545;
            }
        """)
        reset_btn.setToolTip("Clear all portfolio data (requires confirmation)")
        reset_btn.clicked.connect(self.on_reset_data)
        toolbar_layout.addWidget(reset_btn)
        
        layout.addLayout(toolbar_layout)
        
        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setMovable(True)  # Enable tab reordering via drag-and-drop
        
        # Tab names for persistence (used as identifiers)
        self.tab_names = []
        
        # Portfolio tab
        self.portfolio_tab = PortfolioTab(self.calculator, self.settings_store)
        self.portfolio_tab.portfolio_changed.connect(self.on_portfolio_changed)
        self.portfolio_tab.import_requested.connect(self.on_new_input)
        self.tabs.addTab(self.portfolio_tab, "Portfolio")
        self.tab_names.append("portfolio")
        
        # Instrument Config tab
        self.config_tab = InstrumentConfigTab(self.calculator, self.settings_store)
        self.config_tab.config_changed.connect(self.on_config_changed)
        self.tabs.addTab(self.config_tab, "Instrument Config")
        self.tab_names.append("instrument_config")
        
        # Stats tab
        self.stats_tab = StatsTab(self.calculator, self.settings_store)
        self.tabs.addTab(self.stats_tab, "Statistics")
        self.tab_names.append("statistics")
        
        # Currency Exchange tab
        self.currency_tab = CurrencyTab(self.settings_store)
        self.currency_tab.rates_changed.connect(self.on_rates_changed)
        self.tabs.addTab(self.currency_tab, "Currency Exchange")
        self.tab_names.append("currency_exchange")
        
        # Connect tab moved signal for persistence
        self.tabs.tabBar().tabMoved.connect(self.on_tab_moved)
        
        # Restore saved tab order
        self.restore_tab_order()
        
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
        
        # Set up keyboard shortcuts
        self.setup_shortcuts()
    
    def setup_shortcuts(self):
        """Set up keyboard shortcuts for common operations."""
        # Ctrl+N: New Input
        shortcut_new = QShortcut(QKeySequence("Ctrl+N"), self)
        shortcut_new.activated.connect(self.on_new_input)
        
        # Ctrl+S: Save Data
        shortcut_save = QShortcut(QKeySequence("Ctrl+S"), self)
        shortcut_save.activated.connect(self.on_save_data)
        
        # Ctrl+O: Load/Open Data
        shortcut_load = QShortcut(QKeySequence("Ctrl+O"), self)
        shortcut_load.activated.connect(self.on_load_data)
        
        # Ctrl+F: Focus search box (if on Portfolio tab)
        shortcut_search = QShortcut(QKeySequence("Ctrl+F"), self)
        shortcut_search.activated.connect(self.focus_search)
    
    def focus_search(self):
        """Focus the search box in the Portfolio tab."""
        # Switch to Portfolio tab if not already there
        portfolio_index = self.tabs.indexOf(self.portfolio_tab)
        if portfolio_index >= 0:
            self.tabs.setCurrentIndex(portfolio_index)
        # Focus the search input
        self.portfolio_tab.search_input.setFocus()
        self.portfolio_tab.search_input.selectAll()
    
    def closeEvent(self, event):
        """Handle window close event."""
        # Save window geometry
        self.settings_store.set('window_geometry', self.saveGeometry().toHex().data().decode())
        
        # Save portfolio and mappings (no feedback needed when closing)
        self.save_all(show_feedback=False)
        
        event.accept()
    
    def refresh_all(self):
        """Refresh all views."""
        self.portfolio_tab.refresh()
        self.config_tab.refresh()
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
    
    def save_all(self, show_feedback: bool = True):
        """Save all data.
        
        Args:
            show_feedback: Whether to show "Changes saved" feedback in status bar
        """
        # Save portfolio
        self.portfolio_store.save(self.calculator.portfolio)
        
        # Save mappings from current holdings
        self.mappings_store.update_from_holdings(self.calculator.portfolio.holdings)
        
        # Save free cash to settings
        self.settings_store.set('free_cash', self.calculator.portfolio.free_cash)
        
        # Show brief feedback and then restore normal status
        if show_feedback:
            self.show_save_feedback()
    
    def show_save_feedback(self):
        """Show brief save feedback, then restore normal status bar."""
        # Show "Changes saved" briefly
        summary = self.calculator.get_summary()
        self.status_bar.showMessage(
            f"Changes saved  |  Holdings: {summary['num_holdings']} | "
            f"Total (EUR): €{summary['total_eur']:,.2f}"
        )
        # Restore normal status bar after 2 seconds
        QTimer.singleShot(2000, self.update_status_bar)
    
    def on_portfolio_changed(self):
        """Handle portfolio data change."""
        self.config_tab.refresh()
        self.stats_tab.refresh()
        self.update_status_bar()
        self.save_all()
    
    def on_config_changed(self):
        """Handle instrument configuration change."""
        self.portfolio_tab.refresh()
        self.stats_tab.refresh()
        self.update_status_bar()
        self.save_all()
    
    def on_rates_changed(self):
        """Handle exchange rate change."""
        # Refresh all views to recalculate with new rates
        self.refresh_all()
    
    def on_tab_moved(self, from_index: int, to_index: int):
        """Handle tab reorder - save new order."""
        # Get current tab order by tab names
        order = []
        for i in range(self.tabs.count()):
            widget = self.tabs.widget(i)
            # Find the tab name based on widget
            if widget == self.portfolio_tab:
                order.append("portfolio")
            elif widget == self.config_tab:
                order.append("instrument_config")
            elif widget == self.stats_tab:
                order.append("statistics")
            elif widget == self.currency_tab:
                order.append("currency_exchange")
        self.settings_store.set_tab_order(order)
    
    def restore_tab_order(self):
        """Restore saved tab order."""
        order = self.settings_store.get_tab_order()
        if not order:
            return
        
        # Map tab names to widgets
        name_to_widget = {
            "portfolio": self.portfolio_tab,
            "instrument_config": self.config_tab,
            "statistics": self.stats_tab,
            "currency_exchange": self.currency_tab,
        }
        
        # Reorder tabs based on saved order
        for target_index, name in enumerate(order):
            widget = name_to_widget.get(name)
            if widget:
                current_index = self.tabs.indexOf(widget)
                if current_index != -1 and current_index != target_index:
                    self.tabs.tabBar().moveTab(current_index, target_index)
    
    def on_new_input(self):
        """Handle new input button click."""
        dialog = ImportDialog(self)
        dialog.file_selected.connect(self.process_import_file)
        dialog.exec()
    
    def on_reset_data(self):
        """Handle reset data button click."""
        # First warning dialog
        reply = QMessageBox.warning(
            self,
            "Reset Portfolio Data",
            "This will erase ALL portfolio data including:\n"
            "  - All holdings\n"
            "  - Free cash balance\n\n"
            "This action cannot be undone.\n\n"
            "Are you sure you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Second confirmation: require typing "DELETE"
        text, ok = QInputDialog.getText(
            self,
            "Confirm Reset",
            "Type DELETE to confirm:",
        )
        
        if ok and text.strip().upper() == "DELETE":
            # Clear all holdings
            self.calculator.portfolio.holdings.clear()
            # Reset free cash
            self.calculator.set_free_cash(0)
            # Refresh all views
            self.refresh_all()
            # Save the empty state
            self.save_all()
            # Show confirmation
            self.status_bar.showMessage("Portfolio data has been reset.", 5000)
        elif ok:
            QMessageBox.information(
                self,
                "Reset Cancelled",
                "Reset was cancelled. You must type 'DELETE' to confirm."
            )
    
    def on_save_data(self):
        """Handle save data button click."""
        # Generate default filename with current date
        today = datetime.now()
        default_filename = f"allocation_data_{today.strftime('%Y.%m.%d')}.json"
        
        # Open save file dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Portfolio Data",
            default_filename,
            "JSON Files (*.json);;All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            # Collect all data
            export_data = {
                "version": "1.0",
                "exported_at": datetime.now().isoformat(),
                "portfolio": {
                    "holdings": [h.to_dict() for h in self.calculator.portfolio.holdings],
                    "free_cash": self.calculator.portfolio.free_cash
                },
                "settings": {
                    "currencies": self.settings_store.get_currencies(),
                    "exchange_rates": self.settings_store.get_exchange_rates()
                },
                "mappings": self.mappings_store.mappings
            }
            
            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2)
            
            self.status_bar.showMessage(f"Data saved to {file_path}", 5000)
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Save Error",
                f"Error saving data:\n{str(e)}"
            )
    
    def on_export_csv(self):
        """Export portfolio data to CSV format."""
        today = datetime.now()
        default_filename = f"portfolio_{today.strftime('%Y.%m.%d')}.csv"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export to CSV",
            default_filename,
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            holdings = self.calculator.portfolio.holdings
            
            if not holdings:
                QMessageBox.warning(self, "No Data", "No holdings to export.")
                return
            
            # Define CSV columns
            columns = [
                'Instrument', 'Position', 'Last Price', 'Currency',
                'Market Value', 'Market Value (EUR)', 'Cost Basis',
                'Target %', 'Allocation %', 'Asset Type', 'Region',
                'Unrealized P&L', 'Daily P&L'
            ]
            
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(columns)
                
                allocations = self.calculator.get_allocations()
                alloc_map = {a.instrument: a for a in allocations}
                
                for holding in holdings:
                    alloc = alloc_map.get(holding.instrument)
                    market_value_eur = self.settings_store.convert_to_eur(
                        holding.market_value, holding.currency
                    )
                    
                    row = [
                        holding.instrument,
                        holding.position,
                        holding.last_price,
                        holding.currency,
                        holding.market_value,
                        market_value_eur,
                        holding.cost_basis,
                        holding.target_allocation * 100,
                        (alloc.allocation_with_cash * 100) if alloc else 0,
                        holding.asset_type.value,
                        holding.region.value,
                        holding.unrealized_pnl,
                        holding.daily_pnl
                    ]
                    writer.writerow(row)
            
            self.status_bar.showMessage(f"Exported to {file_path}", 5000)
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Error",
                f"Error exporting to CSV:\n{str(e)}"
            )
    
    def on_export_excel(self):
        """Export portfolio data to Excel format."""
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, Alignment, PatternFill
        except ImportError:
            QMessageBox.warning(
                self,
                "Missing Dependency",
                "openpyxl is required for Excel export.\n"
                "Install it with: pip install openpyxl"
            )
            return
        
        today = datetime.now()
        default_filename = f"portfolio_{today.strftime('%Y.%m.%d')}.xlsx"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export to Excel",
            default_filename,
            "Excel Files (*.xlsx);;All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            holdings = self.calculator.portfolio.holdings
            
            if not holdings:
                QMessageBox.warning(self, "No Data", "No holdings to export.")
                return
            
            wb = Workbook()
            ws = wb.active
            ws.title = "Portfolio"
            
            # Define columns
            columns = [
                'Instrument', 'Position', 'Last Price', 'Currency',
                'Market Value', 'Market Value (EUR)', 'Cost Basis',
                'Target %', 'Allocation %', 'Asset Type', 'Region',
                'Unrealized P&L', 'Daily P&L'
            ]
            
            # Header styling
            header_font = Font(bold=True)
            header_fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
            header_font_white = Font(bold=True, color='FFFFFF')
            
            # Write headers
            for col, header in enumerate(columns, 1):
                cell = ws.cell(row=1, column=col, value=header)
                cell.font = header_font_white
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal='center')
            
            # Write data
            allocations = self.calculator.get_allocations()
            alloc_map = {a.instrument: a for a in allocations}
            
            for row_idx, holding in enumerate(holdings, 2):
                alloc = alloc_map.get(holding.instrument)
                market_value_eur = self.settings_store.convert_to_eur(
                    holding.market_value, holding.currency
                )
                
                data = [
                    holding.instrument,
                    holding.position,
                    holding.last_price,
                    holding.currency,
                    holding.market_value,
                    market_value_eur,
                    holding.cost_basis,
                    holding.target_allocation * 100,
                    (alloc.allocation_with_cash * 100) if alloc else 0,
                    holding.asset_type.value,
                    holding.region.value,
                    holding.unrealized_pnl,
                    holding.daily_pnl
                ]
                
                for col_idx, value in enumerate(data, 1):
                    cell = ws.cell(row=row_idx, column=col_idx, value=value)
                    # Right-align numeric columns
                    if col_idx > 1:
                        cell.alignment = Alignment(horizontal='right')
            
            # Auto-adjust column widths
            for col in ws.columns:
                max_length = 0
                column = col[0].column_letter
                for cell in col:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                ws.column_dimensions[column].width = min(max_length + 2, 30)
            
            # Add summary row
            summary_row = len(holdings) + 3
            ws.cell(row=summary_row, column=1, value="Total Holdings:").font = Font(bold=True)
            ws.cell(row=summary_row, column=2, value=len(holdings))
            
            summary = self.calculator.get_summary()
            ws.cell(row=summary_row + 1, column=1, value="Total Value (EUR):").font = Font(bold=True)
            ws.cell(row=summary_row + 1, column=2, value=f"€{summary['total_eur']:,.2f}")
            
            wb.save(file_path)
            self.status_bar.showMessage(f"Exported to {file_path}", 5000)
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Error",
                f"Error exporting to Excel:\n{str(e)}"
            )
    
    def on_load_data(self):
        """Handle load data button click."""
        # Open file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Portfolio Data",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if not file_path:
            return
        
        self.status_bar.showMessage("Loading data...")
        QApplication.processEvents()
        
        try:
            # Read and parse file
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # Validate version
            version = import_data.get("version", "1.0")
            if version != "1.0":
                QMessageBox.warning(
                    self,
                    "Version Warning",
                    f"File version {version} may not be fully compatible."
                )
            
            # Load portfolio data
            portfolio_data = import_data.get("portfolio", {})
            holdings = [Holding.from_dict(h) for h in portfolio_data.get("holdings", [])]
            free_cash = float(portfolio_data.get("free_cash", 0))
            
            # Load settings
            settings_data = import_data.get("settings", {})
            if "currencies" in settings_data:
                self.settings_store.set_currencies(settings_data["currencies"])
            if "exchange_rates" in settings_data:
                for currency, rate in settings_data["exchange_rates"].items():
                    self.settings_store.set_exchange_rate(currency, rate)
            
            # Load mappings
            mappings_data = import_data.get("mappings", {})
            if mappings_data:
                self.mappings_store.mappings = mappings_data
                self.mappings_store.save()
            
            # Apply to portfolio
            self.calculator.portfolio.holdings = holdings
            self.calculator.set_free_cash(free_cash)
            
            # Apply mappings to loaded holdings
            self.mappings_store.apply_mappings(self.calculator.portfolio.holdings)
            
            # Refresh all views
            self.refresh_all()
            
            # Save to internal storage
            self.save_all()
            
            self.status_bar.showMessage(
                f"Loaded {len(holdings)} holdings from {file_path}", 5000
            )
            
        except json.JSONDecodeError as e:
            QMessageBox.critical(
                self,
                "Load Error",
                f"Invalid JSON file:\n{str(e)}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Load Error",
                f"Error loading data:\n{str(e)}"
            )
    
    def process_import_file(self, file_path: str):
        """Process an imported file."""
        path = Path(file_path)
        suffix = path.suffix.lower()
        
        # Check Tesseract availability for images before showing progress
        if suffix in ('.png', '.jpg', '.jpeg'):
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
        
        # Show progress dialog
        is_image = suffix in ('.png', '.jpg', '.jpeg')
        progress_text = "Processing image with OCR..." if is_image else "Importing file..."
        
        progress = QProgressDialog(progress_text, None, 0, 0, self)
        progress.setWindowTitle("Importing")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)  # Show immediately
        progress.setValue(0)
        progress.show()
        QApplication.processEvents()  # Ensure dialog is displayed
        
        try:
            # Update status bar
            self.status_bar.showMessage(progress_text)
            
            # Parse file based on type
            if is_image:
                holdings = parse_image_file(file_path)
            else:
                holdings = parse_file(file_path)
            
            progress.close()
            
            if not holdings:
                QMessageBox.warning(
                    self,
                    "No Data Found",
                    f"Could not extract any portfolio data from:\n{file_path}"
                )
                self.status_bar.showMessage("Import failed: no data found", 3000)
                return
            
            self.status_bar.showMessage(f"Found {len(holdings)} holdings", 2000)
            
            # Show review dialog
            review_dialog = ReviewDialog(holdings, file_path, self)
            review_dialog.data_confirmed.connect(self.on_data_confirmed)
            review_dialog.exec()
            
        except Exception as e:
            progress.close()
            self.status_bar.showMessage("Import failed", 3000)
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
