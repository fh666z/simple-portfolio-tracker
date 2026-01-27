"""Allocation calculator for Portfolio Tracker."""
from collections import defaultdict
from typing import NamedTuple, Callable

from .models import Portfolio, Holding, AssetType, Region, StatsBasic, StatsDetailed


class AllocationResult(NamedTuple):
    """Result of allocation calculation for a single holding."""
    instrument: str
    market_value: float  # In original currency
    market_value_eur: float  # Converted to EUR
    allocation_pct: float  # Without cash
    allocation_with_cash: float  # With cash
    target_allocation: float
    diff_with_target: float


def calculate_allocations(
    portfolio: Portfolio, 
    convert_to_eur: Callable[[float, str], float]
) -> list[AllocationResult]:
    """Calculate allocation percentages for all holdings using EUR values."""
    results = []
    
    # Calculate total in EUR
    total_invested_eur = sum(
        convert_to_eur(h.market_value, h.currency) 
        for h in portfolio.holdings
    )
    total_with_cash_eur = total_invested_eur + portfolio.free_cash
    
    for holding in portfolio.holdings:
        market_value_eur = convert_to_eur(holding.market_value, holding.currency)
        
        alloc_pct = market_value_eur / total_invested_eur if total_invested_eur > 0 else 0
        alloc_with_cash = market_value_eur / total_with_cash_eur if total_with_cash_eur > 0 else 0
        
        results.append(AllocationResult(
            instrument=holding.instrument,
            market_value=holding.market_value,
            market_value_eur=market_value_eur,
            allocation_pct=alloc_pct,
            allocation_with_cash=alloc_with_cash,
            target_allocation=holding.target_allocation,
            diff_with_target=holding.target_allocation - alloc_with_cash,
        ))
    
    return results


def calculate_stats_by_type(
    portfolio: Portfolio,
    convert_to_eur: Callable[[float, str], float]
) -> list[StatsBasic]:
    """Calculate allocation statistics grouped by asset type using EUR values."""
    # Calculate totals in EUR
    total_invested_eur = sum(
        convert_to_eur(h.market_value, h.currency) 
        for h in portfolio.holdings
    )
    total_with_cash_eur = total_invested_eur + portfolio.free_cash
    
    # Group by type
    by_type: dict[AssetType, list[Holding]] = defaultdict(list)
    for holding in portfolio.holdings:
        by_type[holding.asset_type].append(holding)
    
    stats = []
    for asset_type in AssetType:
        holdings = by_type.get(asset_type, [])
        
        type_value_eur = sum(convert_to_eur(h.market_value, h.currency) for h in holdings)
        type_target = sum(h.target_allocation for h in holdings)
        
        current = type_value_eur / total_invested_eur if total_invested_eur > 0 else 0
        current_all = type_value_eur / total_with_cash_eur if total_with_cash_eur > 0 else 0
        
        stats.append(StatsBasic(
            category=asset_type.value,
            current=current,
            current_all=current_all,
            target=type_target,
        ))
    
    return stats


def calculate_stats_by_region(
    portfolio: Portfolio,
    convert_to_eur: Callable[[float, str], float]
) -> list[StatsBasic]:
    """Calculate allocation statistics grouped by region using EUR values."""
    # Calculate totals in EUR
    total_invested_eur = sum(
        convert_to_eur(h.market_value, h.currency) 
        for h in portfolio.holdings
    )
    total_with_cash_eur = total_invested_eur + portfolio.free_cash
    
    # Group by region
    by_region: dict[Region, list[Holding]] = defaultdict(list)
    for holding in portfolio.holdings:
        by_region[holding.region].append(holding)
    
    stats = []
    for region in Region:
        holdings = by_region.get(region, [])
        
        region_value_eur = sum(convert_to_eur(h.market_value, h.currency) for h in holdings)
        region_target = sum(h.target_allocation for h in holdings)
        
        current = region_value_eur / total_invested_eur if total_invested_eur > 0 else 0
        current_all = region_value_eur / total_with_cash_eur if total_with_cash_eur > 0 else 0
        
        stats.append(StatsBasic(
            category=region.value,
            current=current,
            current_all=current_all,
            target=region_target,
        ))
    
    return stats


def calculate_stats_detailed(
    portfolio: Portfolio,
    convert_to_eur: Callable[[float, str], float]
) -> list[StatsDetailed]:
    """Calculate allocation statistics grouped by Type + Region combination using EUR values."""
    # Calculate totals in EUR
    total_invested_eur = sum(
        convert_to_eur(h.market_value, h.currency) 
        for h in portfolio.holdings
    )
    total_with_cash_eur = total_invested_eur + portfolio.free_cash
    
    # Group by (type, region)
    by_combo: dict[tuple[AssetType, Region], list[Holding]] = defaultdict(list)
    for holding in portfolio.holdings:
        key = (holding.asset_type, holding.region)
        by_combo[key].append(holding)
    
    stats = []
    
    # Generate all meaningful combinations (skip if both are unassigned)
    for asset_type in AssetType:
        for region in Region:
            if asset_type == AssetType.UNASSIGNED and region == Region.UNASSIGNED:
                continue
            
            key = (asset_type, region)
            holdings = by_combo.get(key, [])
            
            if not holdings:
                continue  # Skip empty combinations
            
            combo_value_eur = sum(convert_to_eur(h.market_value, h.currency) for h in holdings)
            combo_target = sum(h.target_allocation for h in holdings)
            
            current = combo_value_eur / total_invested_eur if total_invested_eur > 0 else 0
            current_all = combo_value_eur / total_with_cash_eur if total_with_cash_eur > 0 else 0
            
            stats.append(StatsDetailed(
                asset_type=asset_type.value,
                region=region.value,
                current=current,
                current_all=current_all,
                target=combo_target,
            ))
    
    return stats


class PortfolioCalculator:
    """Main calculator class that holds portfolio state and computes stats."""
    
    def __init__(self, portfolio: Portfolio = None, settings_store=None):
        self.portfolio = portfolio or Portfolio()
        self.settings_store = settings_store
    
    def set_portfolio(self, portfolio: Portfolio) -> None:
        """Set the portfolio to calculate stats for."""
        self.portfolio = portfolio
    
    def set_settings_store(self, settings_store) -> None:
        """Set the settings store for currency conversion."""
        self.settings_store = settings_store
    
    def set_free_cash(self, amount: float) -> None:
        """Set free cash amount."""
        self.portfolio.free_cash = amount
    
    def convert_to_eur(self, amount: float, currency: str) -> float:
        """Convert amount to EUR using settings store rates."""
        if self.settings_store is None:
            # Default: assume everything is EUR
            return amount if currency == "EUR" else amount
        return self.settings_store.convert_to_eur(amount, currency)
    
    def get_total_invested_eur(self) -> float:
        """Get total invested value in EUR."""
        return sum(
            self.convert_to_eur(h.market_value, h.currency)
            for h in self.portfolio.holdings
        )
    
    def get_total_eur(self) -> float:
        """Get total portfolio value in EUR (including free cash)."""
        return self.get_total_invested_eur() + self.portfolio.free_cash
    
    def get_allocations(self) -> list[AllocationResult]:
        """Get allocation results for all holdings."""
        return calculate_allocations(self.portfolio, self.convert_to_eur)
    
    def get_stats_by_type(self) -> list[StatsBasic]:
        """Get stats grouped by asset type."""
        return calculate_stats_by_type(self.portfolio, self.convert_to_eur)
    
    def get_stats_by_region(self) -> list[StatsBasic]:
        """Get stats grouped by region."""
        return calculate_stats_by_region(self.portfolio, self.convert_to_eur)
    
    def get_stats_detailed(self) -> list[StatsDetailed]:
        """Get stats grouped by type + region."""
        return calculate_stats_detailed(self.portfolio, self.convert_to_eur)
    
    def get_summary(self) -> dict:
        """Get portfolio summary."""
        total_invested_eur = self.get_total_invested_eur()
        return {
            'total_invested': self.portfolio.total_invested,  # Original currencies
            'total_invested_eur': total_invested_eur,  # In EUR
            'free_cash': self.portfolio.free_cash,
            'total': self.portfolio.total,  # Original currencies
            'total_eur': total_invested_eur + self.portfolio.free_cash,  # In EUR
            'num_holdings': len(self.portfolio.holdings),
        }
