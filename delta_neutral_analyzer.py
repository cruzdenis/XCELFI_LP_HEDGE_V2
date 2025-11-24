"""
Delta Neutral Analyzer
Compares LP positions with short positions and suggests adjustments
"""

from typing import Dict, List
from dataclasses import dataclass


@dataclass
class DeltaNeutralSuggestion:
    """Suggestion for adjusting positions to maintain delta neutral"""
    token: str
    lp_balance: float
    short_balance: float
    difference: float
    difference_pct: float
    status: str  # "balanced", "under_hedged", "over_hedged"
    action: str  # "none", "increase_short", "decrease_short"
    adjustment_amount: float
    adjustment_value_usd: float = 0.0  # Value of adjustment in USD
    priority: str = "optional"  # "required", "optional"


class DeltaNeutralAnalyzer:
    """Analyzes positions and suggests adjustments for delta neutral strategy"""
    
    def __init__(self, tolerance_pct: float = 5.0, hedge_value_threshold_pct: float = 10.0, total_capital: float = 0.0):
        """
        Initialize analyzer
        
        Args:
            tolerance_pct: Tolerance percentage for considering positions balanced (default: 5%)
            hedge_value_threshold_pct: Minimum value (% of total capital) to require hedge action (default: 10%)
            total_capital: Total portfolio value in USD for value-based threshold calculation
        """
        self.tolerance_pct = tolerance_pct
        self.hedge_value_threshold_pct = hedge_value_threshold_pct
        self.total_capital = total_capital
    
    def compare_positions(
        self,
        lp_balances: Dict[str, float],
        short_balances: Dict[str, float],
        token_prices: Dict[str, float] = None
    ) -> List[DeltaNeutralSuggestion]:
        """
        Compare LP and short positions and generate suggestions
        
        IMPORTANT: If ANY position exceeds tolerance, ALL positions will be adjusted.
        This ensures complete portfolio rebalancing when triggered.
        
        Args:
            lp_balances: Dictionary of token balances in LP positions
            short_balances: Dictionary of short position sizes
            token_prices: Dictionary of token prices in USD (optional, for value-based priority)
            
        Returns:
            List of suggestions for each token
        """
        if token_prices is None:
            token_prices = {}
        suggestions = []
        
        # Get all unique tokens from both LP and shorts
        all_tokens = set(lp_balances.keys()) | set(short_balances.keys())
        
        # First pass: calculate all differences and check if trigger is activated
        trigger_activated = False
        temp_suggestions = []
        
        for token in sorted(all_tokens):
            lp_bal = lp_balances.get(token, 0.0)
            short_bal = short_balances.get(token, 0.0)
            
            # Calculate difference (positive = need more shorts, negative = too many shorts)
            difference = lp_bal - short_bal
            
            # Calculate percentage difference relative to LP balance
            if lp_bal > 0:
                diff_pct = abs(difference / lp_bal) * 100
            else:
                # No LP position but has shorts
                diff_pct = 100.0 if short_bal > 0 else 0.0
            
            # Determine status and action
            if diff_pct <= self.tolerance_pct:
                status = "balanced"
                action = "none"
                adjustment = 0.0
            elif difference > 0:
                # Need more shorts (under-hedged)
                status = "under_hedged"
                action = "increase_short"
                adjustment = difference
            else:
                # Too many shorts (over-hedged)
                status = "over_hedged"
                action = "decrease_short"
                adjustment = abs(difference)
            
            # Calculate adjustment value in USD
            token_price = token_prices.get(token, 0.0)
            adjustment_value_usd = adjustment * token_price
            
            # DEBUG
            print(f"DEBUG ANALYZER - Token: {token}, Price: {token_price}, Adjustment: {adjustment}, Value USD: {adjustment_value_usd}")
            
            # Determine priority based on value threshold
            priority = "optional"
            if self.total_capital > 0 and token_price > 0:
                value_pct_of_capital = (adjustment_value_usd / self.total_capital) * 100
                if value_pct_of_capital >= self.hedge_value_threshold_pct:
                    priority = "required"
            
            suggestion = DeltaNeutralSuggestion(
                token=token,
                lp_balance=lp_bal,
                short_balance=short_bal,
                difference=difference,
                difference_pct=diff_pct,
                status=status,
                action=action,
                adjustment_amount=adjustment,
                adjustment_value_usd=adjustment_value_usd,
                priority=priority
            )
            
            temp_suggestions.append(suggestion)
            
            # Check if this position triggers full rebalancing
            if diff_pct > self.tolerance_pct:
                trigger_activated = True
        
        # Second pass: if trigger activated, adjust ALL positions
        if trigger_activated:
            for s in temp_suggestions:
                # Force adjustment for ALL positions, even balanced ones
                if s.status == "balanced" and s.difference != 0:
                    # Recalculate as if it needs adjustment
                    if s.difference > 0:
                        s.status = "under_hedged"
                        s.action = "increase_short"
                        s.adjustment_amount = s.difference
                    else:
                        s.status = "over_hedged"
                        s.action = "decrease_short"
                        s.adjustment_amount = abs(s.difference)
                
                suggestions.append(s)
        else:
            # No trigger, return original suggestions
            suggestions = temp_suggestions
        
        return suggestions
    
    def format_suggestions(self, suggestions: List[DeltaNeutralSuggestion]) -> str:
        """
        Format suggestions as human-readable text
        
        Args:
            suggestions: List of suggestions
            
        Returns:
            Formatted text report
        """
        if not suggestions:
            return "Nenhuma posição encontrada para comparar."
        
        lines = []
        lines.append("=" * 80)
        lines.append("ANÁLISE DELTA NEUTRAL - SUGESTÕES DE AJUSTE")
        lines.append("=" * 80)
        lines.append("")
        
        # Separate by status
        balanced = [s for s in suggestions if s.status == "balanced"]
        under_hedged = [s for s in suggestions if s.status == "under_hedged"]
        over_hedged = [s for s in suggestions if s.status == "over_hedged"]
        
        # Summary
        lines.append(f"📊 RESUMO:")
        lines.append(f"   ✅ Posições Balanceadas: {len(balanced)}")
        lines.append(f"   ⚠️  Posições Sub-Hedge: {len(under_hedged)}")
        lines.append(f"   ⚠️  Posições Sobre-Hedge: {len(over_hedged)}")
        lines.append("")
        lines.append("-" * 80)
        
        # Balanced positions
        if balanced:
            lines.append("")
            lines.append("✅ POSIÇÕES BALANCEADAS (dentro da tolerância de {}%)".format(self.tolerance_pct))
            lines.append("")
            for s in balanced:
                lines.append(f"   {s.token}:")
                lines.append(f"      LP: {s.lp_balance:.6f}")
                lines.append(f"      Short: {s.short_balance:.6f}")
                lines.append(f"      Diferença: {s.difference:+.6f} ({s.difference_pct:.2f}%)")
                lines.append("")
        
        # Under-hedged positions
        if under_hedged:
            lines.append("")
            lines.append("⚠️  POSIÇÕES SUB-HEDGE (precisa aumentar short)")
            lines.append("")
            for s in under_hedged:
                lines.append(f"   {s.token}:")
                lines.append(f"      LP: {s.lp_balance:.6f}")
                lines.append(f"      Short Atual: {s.short_balance:.6f}")
                lines.append(f"      Short Alvo: {s.lp_balance:.6f}")
                lines.append(f"      ➡️  AÇÃO: AUMENTAR SHORT em {s.adjustment_amount:.6f} {s.token}")
                lines.append(f"      Diferença: {s.difference_pct:.2f}%")
                lines.append("")
        
        # Over-hedged positions
        if over_hedged:
            lines.append("")
            lines.append("⚠️  POSIÇÕES SOBRE-HEDGE (precisa diminuir short)")
            lines.append("")
            for s in over_hedged:
                lines.append(f"   {s.token}:")
                lines.append(f"      LP: {s.lp_balance:.6f}")
                lines.append(f"      Short Atual: {s.short_balance:.6f}")
                lines.append(f"      Short Alvo: {s.lp_balance:.6f}")
                lines.append(f"      ➡️  AÇÃO: DIMINUIR SHORT em {s.adjustment_amount:.6f} {s.token}")
                lines.append(f"      Diferença: {s.difference_pct:.2f}%")
                lines.append("")
        
        # Overall status
        lines.append("-" * 80)
        if not under_hedged and not over_hedged:
            lines.append("")
            lines.append("🎯 TODAS AS POSIÇÕES ESTÃO BALANCEADAS!")
            lines.append("")
        else:
            lines.append("")
            lines.append("📋 AÇÕES NECESSÁRIAS:")
            lines.append("")
            for s in under_hedged:
                lines.append(f"   • AUMENTAR SHORT {s.token}: {s.adjustment_amount:.6f}")
            for s in over_hedged:
                lines.append(f"   • DIMINUIR SHORT {s.token}: {s.adjustment_amount:.6f}")
            lines.append("")
        
        lines.append("=" * 80)
        
        return "\n".join(lines)
    
    def get_action_summary(self, suggestions: List[DeltaNeutralSuggestion]) -> Dict[str, float]:
        """
        Get a summary of actions needed
        
        Args:
            suggestions: List of suggestions
            
        Returns:
            Dictionary with action summary
        """
        actions = {
            "increase_short": {},
            "decrease_short": {}
        }
        
        for s in suggestions:
            if s.action == "increase_short":
                actions["increase_short"][s.token] = s.adjustment_amount
            elif s.action == "decrease_short":
                actions["decrease_short"][s.token] = s.adjustment_amount
        
        return actions
