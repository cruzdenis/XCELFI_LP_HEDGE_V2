"""
Capital Allocation Analyzer

Monitors capital distribution across protocols and alerts when rebalancing is needed.

NEW LOGIC:
- 🟢 ZONA IDEAL: 70-90% em LPs
- 🔴 RISCO ALTO (Liquidação): >90% em LPs - Margem insuficiente na Hyperliquid
- 🟡 RISCO MÉDIO (Rentabilidade): <70% em LPs - Perda de potencial de rentabilidade

Target allocation (center of ideal range):
- 80% in LPs (Uniswap, Revert, etc.)
- 20% in Hyperliquid (for operational margin)
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum

class ProtocolType(Enum):
    """Protocol categories for capital allocation"""
    WALLET = "wallet"  # Idle capital in wallet
    LP = "lp"  # Liquidity Provider positions
    HYPERLIQUID = "hyperliquid"  # Perpetuals exchange

class RiskLevel(Enum):
    """Risk levels for capital allocation"""
    IDEAL = "ideal"  # 70-90% in LPs
    HIGH_LIQUIDATION = "high_liquidation"  # >90% in LPs - risk of liquidation
    MEDIUM_PROFITABILITY = "medium_profitability"  # <70% in LPs - loss of profitability

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
    
    # Ideal range (not single target)
    lp_min_ideal: float  # 70%
    lp_max_ideal: float  # 90%
    lp_target: float  # 80% (center)
    
    risk_level: RiskLevel
    risk_description: str
    
    needs_rebalancing: bool
    rebalancing_alert: str
    rebalancing_suggestion: Optional[str]
    
    protocol_balances: List[ProtocolBalance]

class CapitalAllocationAnalyzer:
    """Analyzes capital allocation across protocols"""
    
    def __init__(
        self,
        lp_min_ideal: float = 70.0,
        lp_max_ideal: float = 90.0,
        lp_target: float = 80.0
    ):
        """
        Initialize analyzer.
        
        Args:
            lp_min_ideal: Minimum ideal LP percentage (default 70%)
            lp_max_ideal: Maximum ideal LP percentage (default 90%)
            lp_target: Target LP percentage, center of range (default 80%)
        """
        self.lp_min_ideal = lp_min_ideal
        self.lp_max_ideal = lp_max_ideal
        self.lp_target = lp_target
        
        # Hyperliquid targets derived from LP targets
        self.hyperliquid_target = 100.0 - lp_target
        self.hyperliquid_min_ideal = 100.0 - lp_max_ideal
        self.hyperliquid_max_ideal = 100.0 - lp_min_ideal
    
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
        
        # Determine risk level
        risk_level, risk_description = self._assess_risk(lp_pct, hyperliquid_pct)
        
        # Check if rebalancing is needed
        needs_rebalancing = (risk_level != RiskLevel.IDEAL)
        
        # Generate alert and suggestion
        alert, suggestion = self._generate_rebalancing_message(
            lp_pct, hyperliquid_pct, lp_total, hyperliquid_total, 
            total_capital, risk_level
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
            lp_min_ideal=self.lp_min_ideal,
            lp_max_ideal=self.lp_max_ideal,
            lp_target=self.lp_target,
            risk_level=risk_level,
            risk_description=risk_description,
            needs_rebalancing=needs_rebalancing,
            rebalancing_alert=alert,
            rebalancing_suggestion=suggestion,
            protocol_balances=protocol_balance_objects
        )
    
    def _assess_risk(self, lp_pct: float, hyperliquid_pct: float) -> tuple[RiskLevel, str]:
        """
        Assess risk level based on LP percentage.
        
        Returns:
            (RiskLevel, description)
        """
        if lp_pct > self.lp_max_ideal:
            # >90% in LPs - High risk of liquidation
            return (
                RiskLevel.HIGH_LIQUIDATION,
                f"🔴 RISCO ALTO: {lp_pct:.1f}% em LPs (>{self.lp_max_ideal:.0f}%) - "
                f"Margem operacional insuficiente na Hyperliquid. "
                f"Risco de liquidação em movimentos rápidos de mercado!"
            )
        elif lp_pct < self.lp_min_ideal:
            # <70% in LPs - Medium risk of lost profitability
            return (
                RiskLevel.MEDIUM_PROFITABILITY,
                f"🟡 RISCO MÉDIO: {lp_pct:.1f}% em LPs (<{self.lp_min_ideal:.0f}%) - "
                f"Capital subutilizado. Perda de potencial de rentabilidade!"
            )
        else:
            # 70-90% in LPs - Ideal range
            return (
                RiskLevel.IDEAL,
                f"🟢 ZONA IDEAL: {lp_pct:.1f}% em LPs ({self.lp_min_ideal:.0f}-{self.lp_max_ideal:.0f}%) - "
                f"Alocação balanceada entre rentabilidade e segurança operacional."
            )
    
    def _generate_rebalancing_message(
        self,
        lp_pct: float,
        hyperliquid_pct: float,
        lp_total: float,
        hyperliquid_total: float,
        total_capital: float,
        risk_level: RiskLevel
    ) -> tuple[str, Optional[str]]:
        """Generate alert message and rebalancing suggestion"""
        
        if risk_level == RiskLevel.IDEAL:
            return (
                f"✅ Alocação dentro da zona ideal ({self.lp_min_ideal:.0f}-{self.lp_max_ideal:.0f}% em LPs)",
                None
            )
        
        suggestions = []
        
        if risk_level == RiskLevel.HIGH_LIQUIDATION:
            # >90% in LPs - Need to move to Hyperliquid URGENTLY
            target_lp_pct = self.lp_max_ideal  # Bring down to 90%
            excess_pct = lp_pct - target_lp_pct
            excess_usd = (excess_pct / 100) * total_capital
            
            alert = (
                f"🔴 REBALANCEAMENTO IMEDIATO NECESSÁRIO!\n\n"
                f"**RISCO ALTO DE LIQUIDAÇÃO**\n"
                f"LPs: {lp_pct:.1f}% (>{self.lp_max_ideal:.0f}%) | "
                f"Hyperliquid: {hyperliquid_pct:.1f}% (<{self.hyperliquid_min_ideal:.0f}%)\n\n"
                f"Margem operacional insuficiente. Em movimentos rápidos de alta no mercado, "
                f"posições short podem ser liquidadas!"
            )
            
            suggestions.append(
                f"**AÇÃO URGENTE:**\n"
                f"Transferir **${excess_usd:,.2f}** das LPs para Hyperliquid "
                f"para reduzir LPs para {target_lp_pct:.0f}% e aumentar margem de segurança."
            )
        
        elif risk_level == RiskLevel.MEDIUM_PROFITABILITY:
            # <70% in LPs - Need to move to LPs
            target_lp_pct = self.lp_min_ideal  # Bring up to 70%
            shortage_pct = target_lp_pct - lp_pct
            shortage_usd = (shortage_pct / 100) * total_capital
            
            alert = (
                f"🟡 REBALANCEAMENTO RECOMENDADO\n\n"
                f"**RISCO MÉDIO - Perda de Rentabilidade**\n"
                f"LPs: {lp_pct:.1f}% (<{self.lp_min_ideal:.0f}%) | "
                f"Hyperliquid: {hyperliquid_pct:.1f}% (>{self.hyperliquid_max_ideal:.0f}%)\n\n"
                f"Capital subutilizado em LPs. Sistema perde efetividade operacional e "
                f"potencial de rentabilidade!"
            )
            
            suggestions.append(
                f"**AÇÃO RECOMENDADA:**\n"
                f"Transferir **${shortage_usd:,.2f}** da Hyperliquid para LPs "
                f"para aumentar LPs para {target_lp_pct:.0f}% e maximizar rentabilidade."
            )
        
        suggestion = "\n\n".join(suggestions) if suggestions else None
        
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
            lp_min_ideal=self.lp_min_ideal,
            lp_max_ideal=self.lp_max_ideal,
            lp_target=self.lp_target,
            risk_level=RiskLevel.IDEAL,
            risk_description="ℹ️ Sem dados de capital para analisar",
            needs_rebalancing=False,
            rebalancing_alert="ℹ️ Sem dados de capital para analisar",
            rebalancing_suggestion=None,
            protocol_balances=[]
        )

# Example usage
if __name__ == "__main__":
    analyzer = CapitalAllocationAnalyzer(
        lp_min_ideal=70.0,
        lp_max_ideal=90.0,
        lp_target=80.0
    )
    
    print("=" * 60)
    print("TESTE 1: Alocação Ideal (80% LPs)")
    print("=" * 60)
    status = analyzer.analyze_allocation({
        "revert_finance": 8000.0,
        "hyperliquid": 2000.0
    })
    print(f"LPs: {status.lp_percentage:.1f}% | Hyper: {status.hyperliquid_percentage:.1f}%")
    print(f"Risk: {status.risk_level.value}")
    print(f"Description: {status.risk_description}")
    print(f"Alert: {status.rebalancing_alert}")
    print()
    
    print("=" * 60)
    print("TESTE 2: Risco Alto - Liquidação (95% LPs)")
    print("=" * 60)
    status = analyzer.analyze_allocation({
        "revert_finance": 9500.0,
        "hyperliquid": 500.0
    })
    print(f"LPs: {status.lp_percentage:.1f}% | Hyper: {status.hyperliquid_percentage:.1f}%")
    print(f"Risk: {status.risk_level.value}")
    print(f"Description: {status.risk_description}")
    print(f"Alert: {status.rebalancing_alert}")
    if status.rebalancing_suggestion:
        print(f"Suggestion:\n{status.rebalancing_suggestion}")
    print()
    
    print("=" * 60)
    print("TESTE 3: Risco Médio - Rentabilidade (60% LPs)")
    print("=" * 60)
    status = analyzer.analyze_allocation({
        "revert_finance": 6000.0,
        "hyperliquid": 4000.0
    })
    print(f"LPs: {status.lp_percentage:.1f}% | Hyper: {status.hyperliquid_percentage:.1f}%")
    print(f"Risk: {status.risk_level.value}")
    print(f"Description: {status.risk_description}")
    print(f"Alert: {status.rebalancing_alert}")
    if status.rebalancing_suggestion:
        print(f"Suggestion:\n{status.rebalancing_suggestion}")
