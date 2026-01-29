"""Statistics view for Portfolio Tracker."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QSplitter, QFrame
)
from PyQt6.QtCore import Qt

import matplotlib
matplotlib.use('QtAgg')  # Use Qt backend
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from core.calculator import PortfolioCalculator
from core.persistence import SettingsStore
from .utils import NumericTableItem, setup_movable_columns, ALIGN_RIGHT_CENTER


class PieChartWidget(QWidget):
    """Widget displaying a pie chart using matplotlib."""
    
    # Color palette for charts
    COLORS = [
        '#4e79a7', '#f28e2c', '#e15759', '#76b7b2', '#59a14f',
        '#edc949', '#af7aa1', '#ff9da7', '#9c755f', '#bab0ab'
    ]
    
    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self.title = title
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the chart widget."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Create matplotlib figure
        self.figure = Figure(figsize=(4, 3), dpi=100)
        self.figure.patch.set_facecolor('none')  # Transparent background
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("background-color: transparent;")
        
        layout.addWidget(self.canvas)
    
    def update_chart(self, data: list[tuple[str, float]]):
        """Update the pie chart with new data.
        
        Args:
            data: List of (label, value) tuples
        """
        self.figure.clear()
        
        # Filter out zero/negative values
        filtered_data = [(label, value) for label, value in data if value > 0.001]
        
        if not filtered_data:
            # Show "No data" message
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, "No data", ha='center', va='center', 
                    fontsize=12, color='#999')
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            self.canvas.draw()
            return
        
        labels, values = zip(*filtered_data)
        colors = self.COLORS[:len(values)]
        
        ax = self.figure.add_subplot(111)
        
        # Create pie chart
        wedges, texts, autotexts = ax.pie(
            values,
            labels=None,  # We'll use legend instead
            autopct=lambda pct: f'{pct:.1f}%' if pct > 3 else '',
            colors=colors,
            startangle=90,
            pctdistance=0.75
        )
        
        # Style the percentage text
        for autotext in autotexts:
            autotext.set_fontsize(8)
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        # Add title
        if self.title:
            ax.set_title(self.title, fontsize=11, fontweight='bold', pad=10)
        
        # Add legend
        ax.legend(
            wedges, 
            [f'{label} ({value*100:.1f}%)' for label, value in filtered_data],
            loc='center left',
            bbox_to_anchor=(1, 0.5),
            fontsize=8
        )
        
        self.figure.tight_layout()
        self.canvas.draw()


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
        
        # Top section: Charts
        charts_frame = QFrame()
        charts_layout = QHBoxLayout(charts_frame)
        charts_layout.setContentsMargins(0, 0, 0, 10)
        
        # Type pie chart
        type_chart_group = QGroupBox("Allocation by Type")
        type_chart_layout = QVBoxLayout(type_chart_group)
        self.type_chart = PieChartWidget()
        type_chart_layout.addWidget(self.type_chart)
        charts_layout.addWidget(type_chart_group)
        
        # Region pie chart
        region_chart_group = QGroupBox("Allocation by Region")
        region_chart_layout = QVBoxLayout(region_chart_group)
        self.region_chart = PieChartWidget()
        region_chart_layout.addWidget(self.region_chart)
        charts_layout.addWidget(region_chart_group)
        
        layout.addWidget(charts_frame)
        
        # Bottom section: Tables
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
        table.setAlternatingRowColors(True)
        columns = ["Category", "Current %", "Current All %", "Target %"]
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels(columns)
        
        # Set header tooltips
        tooltips = [
            "Asset type or region category",
            "Allocation % of invested capital (excludes free cash)",
            "Allocation % of total portfolio (includes free cash)",
            "Sum of target allocations for this category"
        ]
        for i, tooltip in enumerate(tooltips):
            table.horizontalHeaderItem(i).setToolTip(tooltip)
        
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
        table.setAlternatingRowColors(True)
        columns = ["Type", "Region", "Current %", "Current All %", "Target %"]
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels(columns)
        
        # Set header tooltips
        tooltips = [
            "Asset type (Equity, Bonds, etc.)",
            "Geographic region (US, EU, EM, Global)",
            "Allocation % of invested capital (excludes free cash)",
            "Allocation % of total portfolio (includes free cash)",
            "Sum of target allocations for this combination"
        ]
        for i, tooltip in enumerate(tooltips):
            table.horizontalHeaderItem(i).setToolTip(tooltip)
        
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
        """Refresh the type stats table and chart."""
        stats = self.calculator.get_stats_by_type()
        
        # Filter out categories with no allocation
        stats = [s for s in stats if s.current > 0 or s.target > 0]
        
        # Update pie chart
        chart_data = [(s.category, s.current) for s in stats if s.current > 0]
        self.type_chart.update_chart(chart_data)
        
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
        """Refresh the region stats table and chart."""
        stats = self.calculator.get_stats_by_region()
        
        # Filter out categories with no allocation
        stats = [s for s in stats if s.current > 0 or s.target > 0]
        
        # Update pie chart
        chart_data = [(s.category, s.current) for s in stats if s.current > 0]
        self.region_chart.update_chart(chart_data)
        
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
        
        self.detailed_table.setRowCount(len(stats) + 1)  # +1 for total row
        
        total_current = 0
        total_current_all = 0
        total_target = 0
        
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
            total_current += stat.current
            
            # Current All % - numeric sorting
            item = NumericTableItem(f"{stat.current_all * 100:.2f}%", stat.current_all)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item.setTextAlignment(ALIGN_RIGHT_CENTER)
            self.detailed_table.setItem(row, 3, item)
            total_current_all += stat.current_all
            
            # Target % - numeric sorting
            item = NumericTableItem(f"{stat.target * 100:.2f}%", stat.target)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item.setTextAlignment(ALIGN_RIGHT_CENTER)
            self.detailed_table.setItem(row, 4, item)
            total_target += stat.target
        
        # Total row
        total_row = len(stats)
        
        item = QTableWidgetItem("TOTAL")
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        font = item.font()
        font.setBold(True)
        item.setFont(font)
        self.detailed_table.setItem(total_row, 0, item)
        
        # Empty region cell for total row
        item = QTableWidgetItem("")
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.detailed_table.setItem(total_row, 1, item)
        
        for col, value in enumerate([total_current, total_current_all, total_target], 2):
            item = NumericTableItem(f"{value * 100:.2f}%", value)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item.setTextAlignment(ALIGN_RIGHT_CENTER)
            item.setFont(font)
            self.detailed_table.setItem(total_row, col, item)
