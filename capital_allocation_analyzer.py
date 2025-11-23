"""
Capital Allocation Analyzer

Monitors capital distribution across protocols and alerts when rebalancing is needed.

Target allocation:
- 85% in LPs (Uniswap, Revert, etc.)
- 15% in Hyperliquid (for operational margin)

Alerts when deviation exceeds threshold (default 40%).
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum

class ProtocolType(Enum):
    """Protocol categories for capital allocation"""
    WALLET = "wallet"  # Idle capital in wallet
    LP = "lp"  # Liquidity Provider positions
    HYPERLIQUID = "hyperliquid"  # Perpetuals exchange

@dataclass
class ProtocolBalance:
    """Balance in a specific protocol"""
    protocol_name: str
    protocol_type: ProtocolType
    usd_value: float
    percentage: float

@dataclass
class AllocationStatus:
    """Capital allocation status and recommendations"""
    total_capital: float
    lp_total: float
    lp_percentage: float
    hyperliquid_total: float
    hyperliquid_percentage: float
    wallet_total: float
    wallet_percentage: float
    
    target_lp_percentage: float
    target_hyperliquid_percentage: float
    
    lp_deviation: float  # Deviation from target (percentage points)
    hyperliquid_deviation: float
    
    needs_rebalancing: bool
    rebalancing_alert: str
    rebalancing_suggestion: Optional[str]
    
    protocol_balances: List[ProtocolBalance]

class CapitalAllocationAnalyzer:
    """Analyzes capital allocation across protocols"""
    
    def __init__(
        self,
        target_lp_pct: float = 85.0,
        target_hyperliquid_pct: float = 15.0,
        deviation_threshold_pct: float = 40.0
    ):
        """
        Initialize analyzer.
        
        Args:
            target_lp_pct: Target percentage for LP positions (default 85%)
            target_hyperliquid_pct: Target percentage for Hyperliquid (default 15%)
            deviation_threshold_pct: Alert threshold for deviation (default 40%)
        """
        self.target_lp_pct = target_lp_pct
        self.target_hyperliquid_pct = target_hyperliquid_pct
        self.deviation_threshold_pct = deviation_threshold_pct
    
    def analyze_allocation(
        self,
        protocol_balances: Dict[str, float],
        wallet_balance: float = 0.0
    ) -> AllocationStatus:
        """
        Analyze capital allocation across protocols.
        
        Args:
            protocol_balances: Dict mapping protocol names to USD values
                Example: {
                    "uniswap_v3": 10000.0,
                    "revert_finance": 5000.0,
                    "hyperliquid": 2000.0
                }
            wallet_balance: USD value of idle capital in wallet
            
        Returns:
            AllocationStatus with analysis and recommendations
        """
        # Calculate totals
        lp_total = 0.0
        hyperliquid_total = 0.0
        protocol_breakdown = []
        
        for protocol_name, usd_value in protocol_balances.items():
            protocol_name_lower = protocol_name.lower()
            
            # Categorize protocol
            if "hyperliquid" in protocol_name_lower:
                protocol_type = ProtocolType.HYPERLIQUID
                hyperliquid_total += usd_value
            else:
                # Everything else is LP (uniswap, revert, curve, etc.)
                protocol_type = ProtocolType.LP
                lp_total += usd_value
            
            protocol_breakdown.append({
                "name": protocol_name,
                "type": protocol_type,
                "value": usd_value
            })
        
        # Add wallet balance
        wallet_total = wallet_balance
        
        # Calculate total capital
        total_capital = lp_total + hyperliquid_total + wallet_total
        
        if total_capital == 0:
            # No capital to analyze
            return self._create_empty_status()
        
        # Calculate percentages
        lp_pct = (lp_total / total_capital) * 100
        hyperliquid_pct = (hyperliquid_total / total_capital) * 100
        wallet_pct = (wallet_total / total_capital) * 100
        
        # Calculate deviations from target
        lp_deviation = lp_pct - self.target_lp_pct
        hyperliquid_deviation = hyperliquid_pct - self.target_hyperliquid_pct
        
        # Check if rebalancing is needed
        lp_deviation_abs = abs(lp_deviation)
        hyperliquid_deviation_abs = abs(hyperliquid_deviation)
        
        # Deviation threshold is percentage of target
        # Example: 40% deviation on 85% target = 34% threshold
        lp_threshold = self.target_lp_pct * (self.deviation_threshold_pct / 100)
        hyperliquid_threshold = self.target_hyperliquid_pct * (self.deviation_threshold_pct / 100)
        
        needs_rebalancing = (
            lp_deviation_abs > lp_threshold or
            hyperliquid_deviation_abs > hyperliquid_threshold
        )
        
        # Generate alert and suggestion
        alert, suggestion = self._generate_rebalancing_message(
            lp_pct, hyperliquid_pct, lp_deviation, hyperliquid_deviation,
            lp_total, hyperliquid_total, total_capital,
            needs_rebalancing
        )
        
        # Create protocol balance objects with percentages
        protocol_balance_objects = []
        
        for pb in protocol_breakdown:
            protocol_balance_objects.append(ProtocolBalance(
                protocol_name=pb["name"],
                protocol_type=pb["type"],
                usd_value=pb["value"],
                percentage=(pb["value"] / total_capital) * 100
            ))
        
        # Add wallet if non-zero
        if wallet_total > 0:
            protocol_balance_objects.append(ProtocolBalance(
                protocol_name="Wallet (Idle)",
                protocol_type=ProtocolType.WALLET,
                usd_value=wallet_total,
                percentage=wallet_pct
            ))
        
        # Sort by USD value descending
        protocol_balance_objects.sort(key=lambda x: x.usd_value, reverse=True)
        
        return AllocationStatus(
            total_capital=total_capital,
            lp_total=lp_total,
            lp_percentage=lp_pct,
            hyperliquid_total=hyperliquid_total,
            hyperliquid_percentage=hyperliquid_pct,
            wallet_total=wallet_total,
            wallet_percentage=wallet_pct,
            target_lp_percentage=self.target_lp_pct,
            target_hyperliquid_percentage=self.target_hyperliquid_pct,
            lp_deviation=lp_deviation,
            hyperliquid_deviation=hyperliquid_deviation,
            needs_rebalancing=needs_rebalancing,
            rebalancing_alert=alert,
            rebalancing_suggestion=suggestion,
            protocol_balances=protocol_balance_objects
        )
    
    def _generate_rebalancing_message(
        self,
        lp_pct: float,
        hyperliquid_pct: float,
        lp_deviation: float,
        hyperliquid_deviation: float,
        lp_total: float,
        hyperliquid_total: float,
        total_capital: float,
        needs_rebalancing: bool
    ) -> tuple[str, Optional[str]]:
        """Generate alert message and rebalancing suggestion"""
        
        if not needs_rebalancing:
            return (
                "✅ Alocação de capital dentro dos parâmetros ideais",
                None
            )
        
        # Determine primary issue
        issues = []
        suggestions = []
        
        # Check LP allocation
        if lp_pct < self.target_lp_pct:
            shortage_pct = self.target_lp_pct - lp_pct
            shortage_usd = (shortage_pct / 100) * total_capital
            issues.append(f"LPs abaixo do target ({lp_pct:.1f}% vs {self.target_lp_pct:.1f}%)")
            suggestions.append(
                f"Transferir ~${shortage_usd:,.2f} da Hyperliquid para LPs "
                f"para atingir {self.target_lp_pct:.0f}%"
            )
            
            # Risk warning
            if lp_pct < 70:  # Critical level
                issues.append("⚠️ RISCO: Efetividade operacional comprometida!")
        
        elif lp_pct > self.target_lp_pct:
            excess_pct = lp_pct - self.target_lp_pct
            excess_usd = (excess_pct / 100) * total_capital
            issues.append(f"LPs acima do target ({lp_pct:.1f}% vs {self.target_lp_pct:.1f}%)")
            suggestions.append(
                f"Transferir ~${excess_usd:,.2f} das LPs para Hyperliquid "
                f"para atingir {self.target_lp_pct:.0f}%"
            )
        
        # Check Hyperliquid allocation
        if hyperliquid_pct < self.target_hyperliquid_pct:
            shortage_pct = self.target_hyperliquid_pct - hyperliquid_pct
            shortage_usd = (shortage_pct / 100) * total_capital
            issues.append(f"Hyperliquid abaixo do target ({hyperliquid_pct:.1f}% vs {self.target_hyperliquid_pct:.1f}%)")
            
            # Risk warning
            if hyperliquid_pct < 10:  # Critical level
                issues.append("⚠️ RISCO DE LIQUIDAÇÃO: Margem operacional muito baixa!")
        
        elif hyperliquid_pct > self.target_hyperliquid_pct:
            excess_pct = hyperliquid_pct - self.target_hyperliquid_pct
            excess_usd = (excess_pct / 100) * total_capital
            issues.append(f"Hyperliquid acima do target ({hyperliquid_pct:.1f}% vs {self.target_hyperliquid_pct:.1f}%)")
        
        alert = "⚠️ REBALANCEAMENTO NECESSÁRIO: " + " | ".join(issues)
        suggestion = "\n".join(suggestions) if suggestions else None
        
        return alert, suggestion
    
    def _create_empty_status(self) -> AllocationStatus:
        """Create empty status when no capital to analyze"""
        return AllocationStatus(
            total_capital=0.0,
            lp_total=0.0,
            lp_percentage=0.0,
            hyperliquid_total=0.0,
            hyperliquid_percentage=0.0,
            wallet_total=0.0,
            wallet_percentage=0.0,
            target_lp_percentage=self.target_lp_pct,
            target_hyperliquid_percentage=self.target_hyperliquid_pct,
            lp_deviation=0.0,
            hyperliquid_deviation=0.0,
            needs_rebalancing=False,
            rebalancing_alert="ℹ️ Sem dados de capital para analisar",
            rebalancing_suggestion=None,
            protocol_balances=[]
        )

# Example usage
if __name__ == "__main__":
    analyzer = CapitalAllocationAnalyzer(
        target_lp_pct=85.0,
        target_hyperliquid_pct=15.0,
        deviation_threshold_pct=40.0
    )
    
    # Example: Balanced allocation
    protocol_balances = {
        "uniswap_v3": 8500.0,
        "revert_finance": 0.0,
        "hyperliquid": 1500.0
    }
    
    status = analyzer.analyze_allocation(protocol_balances, wallet_balance=0.0)
    
    print(f"Total Capital: ${status.total_capital:,.2f}")
    print(f"LP: ${status.lp_total:,.2f} ({status.lp_percentage:.1f}%)")
    print(f"Hyperliquid: ${status.hyperliquid_total:,.2f} ({status.hyperliquid_percentage:.1f}%)")
    print(f"Needs Rebalancing: {status.needs_rebalancing}")
    print(f"Alert: {status.rebalancing_alert}")
    if status.rebalancing_suggestion:
        print(f"Suggestion: {status.rebalancing_suggestion}")
