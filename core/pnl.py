"""
PnL (Profit and Loss) tracking module.
Tracks performance attribution by protocol and source.
"""
from dataclasses import dataclass
from typing import Dict, List
from datetime import datetime
import pandas as pd


@dataclass
class PnLEntry:
    """Single PnL entry."""
    timestamp: datetime
    protocol: str  # "aerodrome" or "hyperliquid"
    source: str  # "lp_fees", "funding", "impermanent_loss", "trading"
    amount_usd: float
    description: str


class PnLTracker:
    """
    Tracks PnL by protocol and source.
    
    Provides attribution analysis for performance.
    """
    
    def __init__(self):
        """Initialize PnL tracker."""
        self.entries: List[PnLEntry] = []
    
    def add_entry(
        self,
        protocol: str,
        source: str,
        amount_usd: float,
        description: str = ""
    ):
        """
        Add a PnL entry.
        
        Args:
            protocol: Protocol name ("aerodrome" or "hyperliquid")
            source: PnL source
            amount_usd: Amount in USD (positive = profit, negative = loss)
            description: Optional description
        """
        entry = PnLEntry(
            timestamp=datetime.now(),
            protocol=protocol,
            source=source,
            amount_usd=amount_usd,
            description=description
        )
        self.entries.append(entry)
    
    def get_total_by_protocol(self) -> Dict[str, float]:
        """
        Get total PnL by protocol.
        
        Returns:
            Dictionary of protocol -> total PnL
        """
        totals = {}
        for entry in self.entries:
            if entry.protocol not in totals:
                totals[entry.protocol] = 0.0
            totals[entry.protocol] += entry.amount_usd
        return totals
    
    def get_total_by_source(self) -> Dict[str, float]:
        """
        Get total PnL by source.
        
        Returns:
            Dictionary of source -> total PnL
        """
        totals = {}
        for entry in self.entries:
            if entry.source not in totals:
                totals[entry.source] = 0.0
            totals[entry.source] += entry.amount_usd
        return totals
    
    def get_attribution(self) -> Dict[str, Dict[str, float]]:
        """
        Get PnL attribution matrix (protocol x source).
        
        Returns:
            Nested dictionary: protocol -> source -> amount
        """
        attribution = {}
        for entry in self.entries:
            if entry.protocol not in attribution:
                attribution[entry.protocol] = {}
            if entry.source not in attribution[entry.protocol]:
                attribution[entry.protocol][entry.source] = 0.0
            attribution[entry.protocol][entry.source] += entry.amount_usd
        return attribution
    
    def get_history_df(self) -> pd.DataFrame:
        """
        Get PnL history as DataFrame.
        
        Returns:
            DataFrame with all PnL entries
        """
        if not self.entries:
            return pd.DataFrame()
        
        data = []
        for entry in self.entries:
            data.append({
                "timestamp": entry.timestamp,
                "protocol": entry.protocol,
                "source": entry.source,
                "amount_usd": entry.amount_usd,
                "description": entry.description
            })
        
        return pd.DataFrame(data)
    
    def get_summary(self) -> Dict:
        """
        Get summary statistics.
        
        Returns:
            Dictionary with summary metrics
        """
        if not self.entries:
            return {
                "total_pnl": 0.0,
                "by_protocol": {},
                "by_source": {},
                "entry_count": 0
            }
        
        return {
            "total_pnl": sum(e.amount_usd for e in self.entries),
            "by_protocol": self.get_total_by_protocol(),
            "by_source": self.get_total_by_source(),
            "entry_count": len(self.entries)
        }
