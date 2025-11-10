"""
Delta Neutral Comparison Module
Compares LP positions with Hyperliquid shorts and suggests adjustments
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class TokenPosition:
    """Represents a token position"""
    symbol: str
    amount: float
    value_usd: float


@dataclass
class DeltaNeutralSuggestion:
    """Represents a suggestion to adjust positions"""
    token: str
    current_lp: float
    current_short: float
    difference: float
    suggested_action: str  # "increase_short", "decrease_short", "balanced"
    adjustment_amount: float


class DeltaNeutralAnalyzer:
    """Analyzes LP and short positions to maintain delta neutral"""
    
    def __init__(self, tolerance_pct: float = 5.0):
        """
        Initialize analyzer
        
        Args:
            tolerance_pct: Tolerance percentage for considering positions balanced
        """
        self.tolerance_pct = tolerance_pct
    
    def extract_lp_positions(self, uniswap_positions: List[Dict]) -> Dict[str, TokenPosition]:
        """
        Extract token positions from Uniswap LP positions
        
        Args:
            uniswap_positions: List of Uniswap positions
            
        Returns:
            Dictionary mapping token symbol to TokenPosition
        """
        token_positions = {}
        
        for position in uniswap_positions:
            # Extract token0
            token0_symbol = position.get('token0_symbol', '').upper()
            token0_amount = float(position.get('token0_amount', 0))
            
            # Extract token1
            token1_symbol = position.get('token1_symbol', '').upper()
            token1_amount = float(position.get('token1_amount', 0))
            
            # Aggregate by symbol
            if token0_symbol and token0_amount > 0:
                if token0_symbol in token_positions:
                    token_positions[token0_symbol].amount += token0_amount
                else:
                    token_positions[token0_symbol] = TokenPosition(
                        symbol=token0_symbol,
                        amount=token0_amount,
                        value_usd=0  # Will be calculated later
                    )
            
            if token1_symbol and token1_amount > 0:
                if token1_symbol in token_positions:
                    token_positions[token1_symbol].amount += token1_amount
                else:
                    token_positions[token1_symbol] = TokenPosition(
                        symbol=token1_symbol,
                        amount=token1_amount,
                        value_usd=0  # Will be calculated later
                    )
        
        return token_positions
    
    def extract_short_positions(self, hyperliquid_positions: List[Dict]) -> Dict[str, float]:
        """
        Extract short positions from Hyperliquid
        
        Args:
            hyperliquid_positions: List of Hyperliquid positions
            
        Returns:
            Dictionary mapping token symbol to short amount (absolute value)
        """
        short_positions = {}
        
        for position in hyperliquid_positions:
            coin = position.get('coin', '').upper()
            size = float(position.get('szi', 0))
            
            # Only consider short positions (negative size)
            if size < 0:
                # Store absolute value
                short_positions[coin] = abs(size)
        
        return short_positions
    
    def normalize_token_symbols(self, symbol: str) -> str:
        """
        Normalize token symbols for comparison
        
        Args:
            symbol: Token symbol
            
        Returns:
            Normalized symbol
        """
        # Remove common prefixes/suffixes
        symbol = symbol.upper()
        
        # Map wrapped tokens to base tokens
        mapping = {
            'WETH': 'ETH',
            'WBTC': 'BTC',
            'WMATIC': 'MATIC',
            'WAVAX': 'AVAX'
        }
        
        return mapping.get(symbol, symbol)
    
    def compare_positions(
        self,
        lp_positions: Dict[str, TokenPosition],
        short_positions: Dict[str, float]
    ) -> List[DeltaNeutralSuggestion]:
        """
        Compare LP and short positions and generate suggestions
        
        Args:
            lp_positions: Dictionary of LP token positions
            short_positions: Dictionary of short positions
            
        Returns:
            List of suggestions
        """
        suggestions = []
        
        # Normalize all symbols
        normalized_lp = {}
        for symbol, position in lp_positions.items():
            norm_symbol = self.normalize_token_symbols(symbol)
            if norm_symbol in normalized_lp:
                normalized_lp[norm_symbol].amount += position.amount
            else:
                normalized_lp[norm_symbol] = TokenPosition(
                    symbol=norm_symbol,
                    amount=position.amount,
                    value_usd=position.value_usd
                )
        
        normalized_shorts = {}
        for symbol, amount in short_positions.items():
            norm_symbol = self.normalize_token_symbols(symbol)
            if norm_symbol in normalized_shorts:
                normalized_shorts[norm_symbol] += amount
            else:
                normalized_shorts[norm_symbol] = amount
        
        # Get all unique tokens
        all_tokens = set(normalized_lp.keys()) | set(normalized_shorts.keys())
        
        for token in all_tokens:
            lp_amount = normalized_lp.get(token, TokenPosition(token, 0, 0)).amount
            short_amount = normalized_shorts.get(token, 0)
            
            # Calculate difference
            difference = lp_amount - short_amount
            
            # Calculate percentage difference
            if lp_amount > 0:
                pct_diff = abs(difference / lp_amount) * 100
            else:
                pct_diff = 100 if short_amount > 0 else 0
            
            # Determine action
            if pct_diff <= self.tolerance_pct:
                action = "balanced"
                adjustment = 0
            elif difference > 0:
                # Need more shorts
                action = "increase_short"
                adjustment = difference
            else:
                # Need less shorts
                action = "decrease_short"
                adjustment = abs(difference)
            
            suggestion = DeltaNeutralSuggestion(
                token=token,
                current_lp=lp_amount,
                current_short=short_amount,
                difference=difference,
                suggested_action=action,
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
            Formatted text
        """
        if not suggestions:
            return "No positions to compare."
        
        lines = ["## Delta Neutral Analysis\n"]
        
        balanced = [s for s in suggestions if s.suggested_action == "balanced"]
        needs_adjustment = [s for s in suggestions if s.suggested_action != "balanced"]
        
        if balanced:
            lines.append("### ✅ Balanced Positions\n")
            for s in balanced:
                lines.append(f"- **{s.token}**: LP {s.current_lp:.6f} ≈ Short {s.current_short:.6f}\n")
        
        if needs_adjustment:
            lines.append("\n### ⚠️ Positions Needing Adjustment\n")
            for s in needs_adjustment:
                if s.suggested_action == "increase_short":
                    lines.append(
                        f"- **{s.token}**: Need to **INCREASE SHORT** by {s.adjustment_amount:.6f}\n"
                        f"  - Current LP: {s.current_lp:.6f}\n"
                        f"  - Current Short: {s.current_short:.6f}\n"
                        f"  - Target Short: {s.current_lp:.6f}\n"
                    )
                elif s.suggested_action == "decrease_short":
                    lines.append(
                        f"- **{s.token}**: Need to **DECREASE SHORT** by {s.adjustment_amount:.6f}\n"
                        f"  - Current LP: {s.current_lp:.6f}\n"
                        f"  - Current Short: {s.current_short:.6f}\n"
                        f"  - Target Short: {s.current_lp:.6f}\n"
                    )
        
        if not needs_adjustment:
            lines.append("\n### 🎯 All positions are balanced!\n")
        
        return "".join(lines)
