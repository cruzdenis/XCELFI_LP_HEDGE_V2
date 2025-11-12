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


class DeltaNeutralAnalyzer:
    """Analyzes positions and suggests adjustments for delta neutral strategy"""
    
    def __init__(self, tolerance_pct: float = 5.0):
        """
        Initialize analyzer
        
        Args:
            tolerance_pct: Tolerance percentage for considering positions balanced (default: 5%)
        """
        self.tolerance_pct = tolerance_pct
    
    def compare_positions(
        self,
        lp_balances: Dict[str, float],
        short_balances: Dict[str, float]
    ) -> List[DeltaNeutralSuggestion]:
        """
        Compare LP and short positions and generate suggestions
        
        Args:
            lp_balances: Dictionary of token balances in LP positions
            short_balances: Dictionary of short position sizes
            
        Returns:
            List of suggestions for each token
        """
        suggestions = []
        
        # Get all unique tokens from both LP and shorts
        all_tokens = set(lp_balances.keys()) | set(short_balances.keys())
        
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
            
            suggestion = DeltaNeutralSuggestion(
                token=token,
                lp_balance=lp_bal,
                short_balance=short_bal,
                difference=difference,
                difference_pct=diff_pct,
                status=status,
                action=action,
                adjustment_amount=adjustment
            )
            
            suggestions.append(suggestion)
        
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
