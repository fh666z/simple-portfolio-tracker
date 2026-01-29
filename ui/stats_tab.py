"""Statistics view for Portfolio Tracker."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QSplitter
)
from PyQt6.QtCore import Qt

from core.calculator import PortfolioCalculator
from core.persistence import SettingsStore
from .utils import NumericTableItem, setup_movable_columns, ALIGN_RIGHT_CENTER


class StatsTab(QWidget):
    """Statistics tab showing allocation breakdown by Type and Region."""
    
    def __init__(self, calculator: PortfolioCalculator, settings_store: SettingsStore, parent=None):
        super().__init__(parent)
        self.calculator = calculator
        self.settings_store = settings_store
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        
        # Create splitter for side-by-side tables
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # STATS Basic section
        basic_widget = QWidget()
        basic_layout = QVBoxLayout(basic_widget)
        
        # By Type table
        type_group = QGroupBox("STATS by Type")
        type_layout = QVBoxLayout(type_group)
        self.type_table = self.create_stats_table('stats_type')
        type_layout.addWidget(self.type_table)
        basic_layout.addWidget(type_group)
        
        # By Region table
        region_group = QGroupBox("STATS by Region")
        region_layout = QVBoxLayout(region_group)
        self.region_table = self.create_stats_table('stats_region')
        region_layout.addWidget(self.region_table)
        basic_layout.addWidget(region_group)
        
        splitter.addWidget(basic_widget)
        
        # STATS Detailed section
        detailed_group = QGroupBox("STATS Detailed (Type + Region)")
        detailed_layout = QVBoxLayout(detailed_group)
        self.detailed_table = self.create_detailed_table()
        detailed_layout.addWidget(self.detailed_table)
        
        splitter.addWidget(detailed_group)
        
        # Set initial sizes
        splitter.setSizes([400, 600])
        
        layout.addWidget(splitter)
    
    def create_stats_table(self, table_name: str) -> QTableWidget:
        """Create a basic stats table."""
        table = QTableWidget()
        columns = ["Category", "Current %", "Current All %", "Target %"]
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels(columns)
        
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, len(columns)):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        
        # Enable column reordering with persistence
        setup_movable_columns(table, table_name, self.settings_store)
        
        return table
    
    def create_detailed_table(self) -> QTableWidget:
        """Create the detailed stats table."""
        table = QTableWidget()
        columns = ["Type", "Region", "Current %", "Current All %", "Target %"]
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels(columns)
        
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for i in range(2, len(columns)):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        
        # Enable column reordering with persistence
        setup_movable_columns(table, 'stats_detailed', self.settings_store)
        
        table.setSortingEnabled(True)
        
        return table
    
    def refresh(self):
        """Refresh all stats tables."""
        self.refresh_type_table()
        self.refresh_region_table()
        self.refresh_detailed_table()
    
    def refresh_type_table(self):
        """Refresh the type stats table."""
        stats = self.calculator.get_stats_by_type()
        
        # Filter out categories with no allocation
        stats = [s for s in stats if s.current > 0 or s.target > 0]
        
        self.type_table.setRowCount(len(stats) + 1)  # +1 for total row
        
        total_current = 0
        total_current_all = 0
        total_target = 0
        
        for row, stat in enumerate(stats):
            # Category
            item = QTableWidgetItem(stat.category)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.type_table.setItem(row, 0, item)
            
            # Current % - numeric sorting
            item = NumericTableItem(f"{stat.current * 100:.2f}%", stat.current)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item.setTextAlignment(ALIGN_RIGHT_CENTER)
            self.type_table.setItem(row, 1, item)
            total_current += stat.current
            
            # Current All % - numeric sorting
            item = NumericTableItem(f"{stat.current_all * 100:.2f}%", stat.current_all)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item.setTextAlignment(ALIGN_RIGHT_CENTER)
            self.type_table.setItem(row, 2, item)
            total_current_all += stat.current_all
            
            # Target % - numeric sorting
            item = NumericTableItem(f"{stat.target * 100:.2f}%", stat.target)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item.setTextAlignment(ALIGN_RIGHT_CENTER)
            self.type_table.setItem(row, 3, item)
            total_target += stat.target
        
        # Total row
        total_row = len(stats)
        
        item = QTableWidgetItem("TOTAL")
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        font = item.font()
        font.setBold(True)
        item.setFont(font)
        self.type_table.setItem(total_row, 0, item)
        
        for col, value in enumerate([total_current, total_current_all, total_target], 1):
            item = NumericTableItem(f"{value * 100:.2f}%", value)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item.setTextAlignment(ALIGN_RIGHT_CENTER)
            item.setFont(font)
            self.type_table.setItem(total_row, col, item)
    
    def refresh_region_table(self):
        """Refresh the region stats table."""
        stats = self.calculator.get_stats_by_region()
        
        # Filter out categories with no allocation
        stats = [s for s in stats if s.current > 0 or s.target > 0]
        
        self.region_table.setRowCount(len(stats) + 1)  # +1 for total row
        
        total_current = 0
        total_current_all = 0
        total_target = 0
        
        for row, stat in enumerate(stats):
            # Category
            item = QTableWidgetItem(stat.category)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.region_table.setItem(row, 0, item)
            
            # Current % - numeric sorting
            item = NumericTableItem(f"{stat.current * 100:.2f}%", stat.current)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item.setTextAlignment(ALIGN_RIGHT_CENTER)
            self.region_table.setItem(row, 1, item)
            total_current += stat.current
            
            # Current All % - numeric sorting
            item = NumericTableItem(f"{stat.current_all * 100:.2f}%", stat.current_all)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item.setTextAlignment(ALIGN_RIGHT_CENTER)
            self.region_table.setItem(row, 2, item)
            total_current_all += stat.current_all
            
            # Target % - numeric sorting
            item = NumericTableItem(f"{stat.target * 100:.2f}%", stat.target)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item.setTextAlignment(ALIGN_RIGHT_CENTER)
            self.region_table.setItem(row, 3, item)
            total_target += stat.target
        
        # Total row
        total_row = len(stats)
        
        item = QTableWidgetItem("TOTAL")
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        font = item.font()
        font.setBold(True)
        item.setFont(font)
        self.region_table.setItem(total_row, 0, item)
        
        for col, value in enumerate([total_current, total_current_all, total_target], 1):
            item = NumericTableItem(f"{value * 100:.2f}%", value)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item.setTextAlignment(ALIGN_RIGHT_CENTER)
            item.setFont(font)
            self.region_table.setItem(total_row, col, item)
    
    def refresh_detailed_table(self):
        """Refresh the detailed stats table."""
        stats = self.calculator.get_stats_detailed()
        
        self.detailed_table.setRowCount(len(stats))
        
        for row, stat in enumerate(stats):
            # Type
            item = QTableWidgetItem(stat.asset_type)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.detailed_table.setItem(row, 0, item)
            
            # Region
            item = QTableWidgetItem(stat.region)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.detailed_table.setItem(row, 1, item)
            
            # Current % - numeric sorting
            item = NumericTableItem(f"{stat.current * 100:.2f}%", stat.current)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item.setTextAlignment(ALIGN_RIGHT_CENTER)
            self.detailed_table.setItem(row, 2, item)
            
            # Current All % - numeric sorting
            item = NumericTableItem(f"{stat.current_all * 100:.2f}%", stat.current_all)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item.setTextAlignment(ALIGN_RIGHT_CENTER)
            self.detailed_table.setItem(row, 3, item)
            
            # Target % - numeric sorting
            item = NumericTableItem(f"{stat.target * 100:.2f}%", stat.target)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item.setTextAlignment(ALIGN_RIGHT_CENTER)
            self.detailed_table.setItem(row, 4, item)
