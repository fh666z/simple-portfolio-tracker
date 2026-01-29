"""Data models for Portfolio Tracker."""
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class AssetType(Enum):
    """Asset type classification."""
    EQUITY = "Equity"
    BONDS = "Bonds"
    COMMODITY = "Commodity"
    THEMATIC = "Thematic"
    REIT = "REIT"
    UNASSIGNED = "Unassigned"


class Region(Enum):
    """Geographic region classification."""
    US = "US"
    EU = "EU"
    EM = "EM"  # Emerging Markets
    GLOBAL = "Global"
    NON = "Non"  # Non-regional (e.g., commodities)
    UNASSIGNED = "Unassigned"


@dataclass
class Holding:
    """Represents a single portfolio holding."""
    instrument: str
    position: float  # Number of shares/units
    last_price: float
    change_pct: float  # Daily change percentage
    cost_basis: float  # Total cost
    market_value: float  # Current value
    avg_price: float  # Average purchase price
    daily_pnl: float  # Daily profit/loss
    unrealized_pnl: float  # Unrealized profit/loss
    
    # User-editable classification fields
    asset_type: AssetType = AssetType.UNASSIGNED
    region: Region = Region.UNASSIGNED
    target_allocation: float = 0.0  # Target allocation percentage (0-1)
    currency: str = "EUR"  # Currency of the instrument (EUR, USD, GBP, CNY, etc.)
    
    @property
    def allocation_pct(self) -> float:
        """Placeholder - actual allocation calculated by Portfolio."""
        return 0.0
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            'instrument': self.instrument,
            'position': self.position,
            'last_price': self.last_price,
            'change_pct': self.change_pct,
            'cost_basis': self.cost_basis,
            'market_value': self.market_value,
            'avg_price': self.avg_price,
            'daily_pnl': self.daily_pnl,
            'unrealized_pnl': self.unrealized_pnl,
            'asset_type': self.asset_type.value,
            'region': self.region.value,
            'target_allocation': self.target_allocation,
            'currency': self.currency,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Holding':
        """Create Holding from dictionary."""
        return cls(
            instrument=data['instrument'],
            position=float(data['position']),
            last_price=float(data['last_price']),
            change_pct=float(data['change_pct']),
            cost_basis=float(data['cost_basis']),
            market_value=float(data['market_value']),
            avg_price=float(data['avg_price']),
            daily_pnl=float(data['daily_pnl']),
            unrealized_pnl=float(data['unrealized_pnl']),
            asset_type=AssetType(data.get('asset_type', 'Unassigned')),
            region=Region(data.get('region', 'Unassigned')),
            target_allocation=float(data.get('target_allocation', 0.0)),
            currency=data.get('currency', 'EUR'),
        )


@dataclass
class Portfolio:
    """Represents the entire portfolio."""
    holdings: list[Holding] = field(default_factory=list)
    free_cash: float = 0.0
    
    @property
    def total_invested(self) -> float:
        """Sum of all market values."""
        return sum(h.market_value for h in self.holdings)
    
    @property
    def total(self) -> float:
        """Total portfolio value including free cash."""
        return self.total_invested + self.free_cash
    
    def get_allocation(self, holding: Holding, include_cash: bool = False) -> float:
        """Calculate allocation percentage for a holding."""
        divisor = self.total if include_cash else self.total_invested
        if divisor == 0:
            return 0.0
        return holding.market_value / divisor
    
    def update_holding(self, instrument: str, **kwargs) -> bool:
        """Update a holding by instrument name."""
        for h in self.holdings:
            if h.instrument == instrument:
                for key, value in kwargs.items():
                    if hasattr(h, key):
                        setattr(h, key, value)
                return True
        return False
    
    def add_or_update_holdings(self, new_holdings: list[Holding]) -> None:
        """Add new holdings or update existing ones by instrument."""
        existing_instruments = {h.instrument: i for i, h in enumerate(self.holdings)}
        
        for new_h in new_holdings:
            if new_h.instrument in existing_instruments:
                # Update existing - preserve type/region/target/currency if already set
                idx = existing_instruments[new_h.instrument]
                old_h = self.holdings[idx]
                new_h.asset_type = old_h.asset_type if old_h.asset_type != AssetType.UNASSIGNED else new_h.asset_type
                new_h.region = old_h.region if old_h.region != Region.UNASSIGNED else new_h.region
                new_h.target_allocation = old_h.target_allocation if old_h.target_allocation > 0 else new_h.target_allocation
                new_h.currency = old_h.currency  # Preserve currency setting
                self.holdings[idx] = new_h
            else:
                self.holdings.append(new_h)


@dataclass
class StatsBasic:
    """Statistics grouped by a single dimension (Type or Region)."""
    category: str
    current: float  # Current allocation %
    current_all: float  # Allocation % including cash
    target: float  # Target allocation %


@dataclass 
class StatsDetailed:
    """Statistics grouped by Type + Region combination."""
    asset_type: str
    region: str
    current: float
    current_all: float
    target: float
