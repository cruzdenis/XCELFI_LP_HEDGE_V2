"""
NAV (Net Asset Value) calculation module with unit accounting.
Implements professional fund accounting methodology.
"""
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass
import pandas as pd


@dataclass
class NAVSnapshot:
    """Snapshot of NAV at a point in time."""
    timestamp: datetime
    nav_total: float  # Total NAV in USDC
    nav_operational: float  # 98% operational
    nav_reserve: float  # 2% reserve
    units: float  # Total units outstanding
    price_per_unit: float  # NAV per unit (cota)
    
    # Breakdown
    lp_value: float
    short_value: float
    usdc_balance: float
    eth_balance: float
    
    # Performance
    funding_24h: float
    lp_fees_24h: float
    pnl_24h: float


class NAVCalculator:
    """
    NAV calculator with unit accounting.
    
    Unit accounting ensures that cash flows (deposits/withdrawals) don't
    distort performance measurement.
    """
    
    def __init__(self, initial_nav: float = 0.0, initial_units: float = 0.0):
        """
        Initialize NAV calculator.
        
        Args:
            initial_nav: Initial NAV in USDC
            initial_units: Initial units (0 for new fund)
        """
        self.history: List[NAVSnapshot] = []
        self.current_nav = initial_nav
        self.current_units = initial_units if initial_units > 0 else (1.0 if initial_nav > 0 else 0.0)
        
        # If starting fresh, set initial price to 1.00
        if initial_nav == 0.0:
            self.current_units = 0.0
    
    def calculate_nav(
        self,
        lp_value: float,
        short_value: float,
        usdc_balance: float,
        eth_balance: float,
        eth_price_usd: float,
        funding_24h: float = 0.0,
        lp_fees_24h: float = 0.0
    ) -> NAVSnapshot:
        """
        Calculate current NAV from component values.
        
        Args:
            lp_value: Value of LP position in USDC
            short_value: Value of short positions in USDC (negative)
            usdc_balance: USDC balance
            eth_balance: ETH balance
            eth_price_usd: Current ETH price in USD
            funding_24h: Funding received in last 24h
            lp_fees_24h: LP fees collected in last 24h
            
        Returns:
            NAVSnapshot with current state
        """
        # Calculate total NAV
        eth_value = eth_balance * eth_price_usd
        nav_total = lp_value + short_value + usdc_balance + eth_value
        
        # Split operational vs reserve (98% vs 2%)
        nav_operational = nav_total * 0.98
        nav_reserve = nav_total * 0.02
        
        # Calculate price per unit
        if self.current_units > 0:
            price_per_unit = nav_total / self.current_units
        else:
            # First deposit - initialize at 1.00
            price_per_unit = 1.0
            if nav_total > 0:
                self.current_units = nav_total / price_per_unit
        
        # Calculate 24h PnL
        pnl_24h = funding_24h + lp_fees_24h
        
        # Create snapshot
        snapshot = NAVSnapshot(
            timestamp=datetime.now(),
            nav_total=nav_total,
            nav_operational=nav_operational,
            nav_reserve=nav_reserve,
            units=self.current_units,
            price_per_unit=price_per_unit,
            lp_value=lp_value,
            short_value=short_value,
            usdc_balance=usdc_balance,
            eth_balance=eth_value,
            funding_24h=funding_24h,
            lp_fees_24h=lp_fees_24h,
            pnl_24h=pnl_24h
        )
        
        # Update current state
        self.current_nav = nav_total
        self.history.append(snapshot)
        
        return snapshot
    
    def process_deposit(self, amount_usd: float) -> float:
        """
        Process a deposit (cash in).
        
        Args:
            amount_usd: Deposit amount in USD
            
        Returns:
            Number of units issued
        """
        if self.current_units == 0:
            # First deposit - issue units at 1.00
            units_issued = amount_usd / 1.0
            self.current_units = units_issued
            self.current_nav = amount_usd
        else:
            # Issue units at current price
            price_per_unit = self.current_nav / self.current_units
            units_issued = amount_usd / price_per_unit
            self.current_units += units_issued
            self.current_nav += amount_usd
        
        return units_issued
    
    def process_withdrawal(self, amount_usd: float) -> float:
        """
        Process a withdrawal (cash out).
        
        Args:
            amount_usd: Withdrawal amount in USD
            
        Returns:
            Number of units redeemed
        """
        if self.current_units == 0:
            return 0.0
        
        price_per_unit = self.current_nav / self.current_units
        units_redeemed = amount_usd / price_per_unit
        
        # Ensure we don't redeem more than available
        units_redeemed = min(units_redeemed, self.current_units)
        
        self.current_units -= units_redeemed
        self.current_nav -= amount_usd
        
        return units_redeemed
    
    def get_performance_metrics(self) -> Dict[str, float]:
        """
        Calculate performance metrics.
        
        Returns:
            Dictionary with MTD, YTD, and other metrics
        """
        if len(self.history) < 2:
            return {
                "mtd": 0.0,
                "ytd": 0.0,
                "inception": 0.0,
                "total_funding": 0.0,
                "total_lp_fees": 0.0
            }
        
        current = self.history[-1]
        
        # Find start of month
        current_month_start = current.timestamp.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_start_snapshot = None
        for snap in reversed(self.history):
            if snap.timestamp < current_month_start:
                month_start_snapshot = snap
                break
        
        # Find start of year
        current_year_start = current.timestamp.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        year_start_snapshot = None
        for snap in reversed(self.history):
            if snap.timestamp < current_year_start:
                year_start_snapshot = snap
                break
        
        # Calculate returns
        mtd = 0.0
        if month_start_snapshot:
            mtd = (current.price_per_unit / month_start_snapshot.price_per_unit - 1.0) * 100
        
        ytd = 0.0
        if year_start_snapshot:
            ytd = (current.price_per_unit / year_start_snapshot.price_per_unit - 1.0) * 100
        
        inception = (current.price_per_unit / 1.0 - 1.0) * 100
        
        # Sum funding and fees
        total_funding = sum(snap.funding_24h for snap in self.history)
        total_lp_fees = sum(snap.lp_fees_24h for snap in self.history)
        
        return {
            "mtd": mtd,
            "ytd": ytd,
            "inception": inception,
            "total_funding": total_funding,
            "total_lp_fees": total_lp_fees
        }
    
    def get_history_df(self) -> pd.DataFrame:
        """
        Get history as pandas DataFrame.
        
        Returns:
            DataFrame with NAV history
        """
        if not self.history:
            return pd.DataFrame()
        
        data = []
        for snap in self.history:
            data.append({
                "timestamp": snap.timestamp,
                "nav_total": snap.nav_total,
                "price_per_unit": snap.price_per_unit,
                "units": snap.units,
                "lp_value": snap.lp_value,
                "short_value": snap.short_value,
                "usdc_balance": snap.usdc_balance,
                "eth_balance": snap.eth_balance,
                "funding_24h": snap.funding_24h,
                "lp_fees_24h": snap.lp_fees_24h,
                "pnl_24h": snap.pnl_24h
            })
        
        return pd.DataFrame(data)
