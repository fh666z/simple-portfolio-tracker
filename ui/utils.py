"""Shared UI utilities for Portfolio Tracker."""
import re
from PyQt6.QtWidgets import QTableWidgetItem, QTableWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor


# =============================================================================
# UI Color Constants
# =============================================================================

# Alternating row colors
ROW_COLOR_EVEN = QColor(255, 255, 255)  # White
ROW_COLOR_ODD = QColor(245, 245, 250)   # Light gray-blue

# Highlight colors for special columns
HIGHLIGHT_COLOR_EVEN = QColor(255, 248, 220)  # Light yellow for even rows
HIGHLIGHT_COLOR_ODD = QColor(250, 243, 210)   # Slightly darker yellow for odd rows

# Warning/attention colors
WARNING_COLOR_YELLOW = QColor(255, 255, 200)  # Light yellow
WARNING_COLOR_RED = QColor(255, 200, 200)     # Light red

# Common text alignment
ALIGN_RIGHT_CENTER = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter


# =============================================================================
# Currency Utilities
# =============================================================================

CURRENCY_SYMBOLS = {
    'EUR': '€',
    'USD': '$',
    'GBP': '£',
    'CNH': '¥',
    'CNY': '¥',
    'JPY': '¥',
    'CHF': 'Fr.',
}


def get_currency_symbol(currency: str) -> str:
    """Get the display symbol for a currency code.
    
    Args:
        currency: Currency code (e.g., 'USD', 'EUR')
        
    Returns:
        Currency symbol (e.g., '$', '€') or the currency code with space if unknown
    """
    return CURRENCY_SYMBOLS.get(currency, f"{currency} ")


# =============================================================================
# Numeric Parsing Utilities
# =============================================================================

def parse_numeric_text(text: str) -> float:
    """Parse a numeric value from formatted text.
    
    Strips currency symbols, commas, and other non-numeric characters.
    
    Args:
        text: Text that may contain a number with formatting
        
    Returns:
        Parsed float value, or 0.0 if parsing fails
    """
    if not text:
        return 0.0
    
    # Remove everything except digits, decimal point, and minus sign
    numeric_text = re.sub(r'[^\d.\-]', '', text.strip())
    
    try:
        return float(numeric_text) if numeric_text else 0.0
    except ValueError:
        return 0.0


# =============================================================================
# Custom Table Items
# =============================================================================

class NumericTableItem(QTableWidgetItem):
    """QTableWidgetItem that sorts by numeric value instead of string.
    
    Use this for columns displaying formatted numbers (with currency symbols,
    percentages, etc.) to ensure proper numeric sorting.
    """
    
    def __init__(self, display_text: str, sort_value: float):
        """Initialize with display text and sort value.
        
        Args:
            display_text: Text to display in the cell
            sort_value: Numeric value used for sorting
        """
        super().__init__(display_text)
        self._sort_value = sort_value
    
    def __lt__(self, other):
        if isinstance(other, NumericTableItem):
            return self._sort_value < other._sort_value
        return super().__lt__(other)


# =============================================================================
# Column Order Management
# =============================================================================

def save_column_order(table: QTableWidget, table_name: str, settings_store) -> None:
    """Save the current column order for a table.
    
    Args:
        table: The QTableWidget whose column order to save
        table_name: Unique identifier for the table in settings
        settings_store: SettingsStore instance for persistence
    """
    header = table.horizontalHeader()
    order = [header.logicalIndex(i) for i in range(header.count())]
    settings_store.set_column_order(table_name, order)


def restore_column_order(table: QTableWidget, table_name: str, settings_store) -> None:
    """Restore saved column order for a table.
    
    Args:
        table: The QTableWidget whose column order to restore
        table_name: Unique identifier for the table in settings
        settings_store: SettingsStore instance for persistence
    """
    order = settings_store.get_column_order(table_name)
    if order:
        header = table.horizontalHeader()
        for visual_index, logical_index in enumerate(order):
            if logical_index < header.count():
                current_visual = header.visualIndex(logical_index)
                if current_visual != visual_index:
                    header.moveSection(current_visual, visual_index)


def setup_movable_columns(table: QTableWidget, table_name: str, settings_store) -> None:
    """Enable movable columns with automatic save/restore.
    
    Args:
        table: The QTableWidget to configure
        table_name: Unique identifier for the table in settings
        settings_store: SettingsStore instance for persistence
    """
    header = table.horizontalHeader()
    header.setSectionsMovable(True)
    header.sectionMoved.connect(
        lambda l, o, n: save_column_order(table, table_name, settings_store)
    )
    restore_column_order(table, table_name, settings_store)


# =============================================================================
# Row Styling Utilities
# =============================================================================

def get_alternating_row_color(row: int) -> QColor:
    """Get the background color for alternating rows.
    
    Args:
        row: Row index (0-based)
        
    Returns:
        QColor for the row background
    """
    return ROW_COLOR_EVEN if row % 2 == 0 else ROW_COLOR_ODD


def get_highlight_row_color(row: int) -> QColor:
    """Get the highlighted background color for alternating rows.
    
    Use for columns that need visual emphasis (e.g., target-related columns).
    
    Args:
        row: Row index (0-based)
        
    Returns:
        QColor for the highlighted row background
    """
    return HIGHLIGHT_COLOR_EVEN if row % 2 == 0 else HIGHLIGHT_COLOR_ODD
