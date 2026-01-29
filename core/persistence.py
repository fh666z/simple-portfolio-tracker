"""Persistence layer for Portfolio Tracker."""
import json
from pathlib import Path
from typing import Optional

from .models import Portfolio, Holding, AssetType, Region


def get_data_dir() -> Path:
    """Get the data directory for storing app data."""
    # Use user's home directory
    data_dir = Path.home() / ".portfolio-tracker"
    data_dir.mkdir(exist_ok=True)
    return data_dir


def get_mappings_file() -> Path:
    """Get the path to the mappings file."""
    return get_data_dir() / "mappings.json"


def get_settings_file() -> Path:
    """Get the path to the settings file."""
    return get_data_dir() / "settings.json"


def get_portfolio_file() -> Path:
    """Get the path to the portfolio file."""
    return get_data_dir() / "portfolio.json"


class MappingsStore:
    """Store for instrument -> type/region mappings."""
    
    def __init__(self):
        self.mappings: dict[str, dict] = {}
        self.load()
    
    def load(self):
        """Load mappings from file."""
        file_path = get_mappings_file()
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.mappings = json.load(f)
            except Exception as e:
                print(f"Warning: Could not load mappings: {e}")
                self.mappings = {}
    
    def save(self):
        """Save mappings to file."""
        file_path = get_mappings_file()
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.mappings, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save mappings: {e}")
    
    def get_mapping(self, instrument: str) -> Optional[dict]:
        """Get mapping for an instrument."""
        return self.mappings.get(instrument)
    
    def set_mapping(self, instrument: str, asset_type: AssetType, region: Region, 
                     target: float = 0.0, currency: str = "EUR"):
        """Set mapping for an instrument."""
        self.mappings[instrument] = {
            'asset_type': asset_type.value,
            'region': region.value,
            'target_allocation': target,
            'currency': currency,
        }
        self.save()
    
    def apply_mappings(self, holdings: list[Holding]) -> None:
        """Apply stored mappings to holdings."""
        for holding in holdings:
            mapping = self.get_mapping(holding.instrument)
            if mapping:
                try:
                    holding.asset_type = AssetType(mapping.get('asset_type', 'Unassigned'))
                    holding.region = Region(mapping.get('region', 'Unassigned'))
                    holding.target_allocation = float(mapping.get('target_allocation', 0))
                    holding.currency = mapping.get('currency', 'EUR')
                except (ValueError, KeyError):
                    pass
    
    def update_from_holdings(self, holdings: list[Holding]) -> None:
        """Update mappings from current holdings."""
        for holding in holdings:
            if holding.asset_type != AssetType.UNASSIGNED or holding.region != Region.UNASSIGNED or holding.currency != "EUR":
                self.set_mapping(
                    holding.instrument,
                    holding.asset_type,
                    holding.region,
                    holding.target_allocation,
                    holding.currency
                )


class SettingsStore:
    """Store for application settings."""
    
    # Default currencies available in the app
    DEFAULT_CURRENCIES = ["EUR", "USD", "GBP", "CNH"]
    
    # Default exchange rates (from EUR)
    # Rate meaning: 1 EUR = [rate] [currency]
    # E.g., 1 EUR = 1.09 USD, 1 EUR = 7.69 CNH
    DEFAULT_EXCHANGE_RATES = {
        "EUR": 1.0,
        "USD": 1.09,
        "GBP": 0.85,
        "CNH": 7.69,
    }
    
    def __init__(self):
        self.settings: dict = {
            'free_cash': 0.0,
            'last_import_path': '',
            'window_geometry': None,
            'currencies': self.DEFAULT_CURRENCIES.copy(),
            'exchange_rates': self.DEFAULT_EXCHANGE_RATES.copy(),
        }
        self.load()
    
    def load(self):
        """Load settings from file."""
        file_path = get_settings_file()
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    self.settings.update(loaded)
            except Exception as e:
                print(f"Warning: Could not load settings: {e}")
    
    def save(self):
        """Save settings to file."""
        file_path = get_settings_file()
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save settings: {e}")
    
    def get(self, key: str, default=None):
        """Get a setting value."""
        return self.settings.get(key, default)
    
    def set(self, key: str, value):
        """Set a setting value."""
        self.settings[key] = value
        self.save()
    
    # Currency-specific methods
    def get_currencies(self) -> list[str]:
        """Get list of available currencies."""
        return self.settings.get('currencies', self.DEFAULT_CURRENCIES.copy())
    
    def set_currencies(self, currencies: list[str]):
        """Set the list of available currencies."""
        # Ensure EUR is always included
        if 'EUR' not in currencies:
            currencies = ['EUR'] + currencies
        self.settings['currencies'] = currencies
        self.save()
    
    def add_currency(self, currency: str):
        """Add a new currency if not already present."""
        currencies = self.get_currencies()
        if currency not in currencies:
            currencies.append(currency)
            self.set_currencies(currencies)
    
    def get_exchange_rates(self) -> dict[str, float]:
        """Get exchange rates dict (currency -> EUR rate)."""
        return self.settings.get('exchange_rates', self.DEFAULT_EXCHANGE_RATES.copy())
    
    def set_exchange_rate(self, currency: str, rate: float):
        """Set exchange rate for a currency."""
        rates = self.get_exchange_rates()
        rates[currency] = rate
        self.settings['exchange_rates'] = rates
        self.save()
    
    def get_exchange_rate(self, currency: str) -> float:
        """Get exchange rate for a currency (units per 1 EUR). Returns 1.0 for EUR or unknown currencies."""
        if currency == 'EUR':
            return 1.0
        rates = self.get_exchange_rates()
        return rates.get(currency, 1.0)
    
    def convert_to_eur(self, amount: float, currency: str) -> float:
        """Convert an amount from given currency to EUR.
        
        Rate represents how many units of currency equal 1 EUR.
        So: EUR = amount / rate
        """
        rate = self.get_exchange_rate(currency)
        if rate == 0:
            return amount  # Avoid division by zero
        return amount / rate
    
    # Column order methods
    def get_column_order(self, table_name: str) -> Optional[list[int]]:
        """Get saved column order for a table. Returns None if not saved."""
        column_orders = self.settings.get('column_orders', {})
        return column_orders.get(table_name)
    
    def set_column_order(self, table_name: str, order: list[int]):
        """Save column order for a table."""
        if 'column_orders' not in self.settings:
            self.settings['column_orders'] = {}
        self.settings['column_orders'][table_name] = order
        self.save()
    
    # Tab order methods
    def get_tab_order(self) -> Optional[list[str]]:
        """Get saved tab order. Returns None if not saved."""
        return self.settings.get('tab_order')
    
    def set_tab_order(self, order: list[str]):
        """Save tab order."""
        self.settings['tab_order'] = order
        self.save()


class PortfolioStore:
    """Store for portfolio data."""
    
    def __init__(self):
        self.portfolio: Optional[Portfolio] = None
    
    def load(self) -> Optional[Portfolio]:
        """Load portfolio from file."""
        file_path = get_portfolio_file()
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            holdings = [Holding.from_dict(h) for h in data.get('holdings', [])]
            self.portfolio = Portfolio(
                holdings=holdings,
                free_cash=float(data.get('free_cash', 0))
            )
            return self.portfolio
        except Exception as e:
            print(f"Warning: Could not load portfolio: {e}")
            return None
    
    def save(self, portfolio: Portfolio):
        """Save portfolio to file."""
        file_path = get_portfolio_file()
        try:
            data = {
                'holdings': [h.to_dict() for h in portfolio.holdings],
                'free_cash': portfolio.free_cash,
            }
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            self.portfolio = portfolio
        except Exception as e:
            print(f"Warning: Could not save portfolio: {e}")
