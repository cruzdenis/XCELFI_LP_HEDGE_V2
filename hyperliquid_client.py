"""
Hyperliquid Client
Handles trading operations on Hyperliquid exchange
"""

import json
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class OrderResult:
    """Result of an order operation"""
    success: bool
    message: str
    order_id: Optional[int] = None
    filled_size: Optional[float] = None
    avg_price: Optional[float] = None

class HyperliquidClient:
    """Client for Hyperliquid exchange API"""
    
    # Asset name to index mapping (common perpetuals)
    ASSET_MAP = {
        "BTC": 0,
        "ETH": 1,
        "SOL": 2,
        # Add more as needed
    }
    
    def __init__(self, wallet_address: str, private_key: str = None):
        """
        Initialize Hyperliquid client
        
        Args:
            wallet_address: Public wallet address
            private_key: Private key for signing (optional, only for execution)
        """
        self.wallet_address = wallet_address
        self.private_key = private_key
        self.can_execute = bool(private_key)
        
        # Only import SDK if private key is provided
        if self.can_execute:
            try:
                from hyperliquid.exchange import Exchange
                from eth_account import Account
                
                # Create LocalAccount from private key
                wallet = Account.from_key(private_key)
                self.exchange = Exchange(wallet)
            except ImportError:
                self.can_execute = False
                self.exchange = None
                print("Warning: hyperliquid-python-sdk not installed. Execution disabled.")
        else:
            self.exchange = None
    
    def get_account_value(self) -> Optional[float]:
        """
        Get total account value in USD from Hyperliquid
        Returns None if execution is disabled or error occurs
        """
        if not self.can_execute or not self.exchange:
            return None
        
        try:
            # Get user state which includes account value
            user_state = self.exchange.info.user_state(self.wallet_address)
            if user_state and 'marginSummary' in user_state:
                account_value = float(user_state['marginSummary']['accountValue'])
                return account_value
        except Exception as e:
            print(f"Error getting account value: {e}")
        
        return None
    
    def get_asset_index(self, symbol: str) -> Optional[int]:
        """Get asset index for a symbol"""
        # Normalize symbol
        symbol = symbol.upper().replace("WBTC", "BTC").replace("WETH", "ETH")
        return self.ASSET_MAP.get(symbol)
    
    def place_market_order(
        self, 
        symbol: str, 
        size: float, 
        is_buy: bool,
        reduce_only: bool = False
    ) -> OrderResult:
        """
        Place a market order
        
        Args:
            symbol: Asset symbol (e.g., "BTC", "ETH")
            size: Order size (absolute value)
            is_buy: True for buy, False for sell
            reduce_only: If True, order will only reduce position
            
        Returns:
            OrderResult with success status and details
        """
        if not self.can_execute:
            return OrderResult(
                success=False,
                message="Cannot execute: No private key configured"
            )
        
        # Get asset index
        asset_index = self.get_asset_index(symbol)
        if asset_index is None:
            return OrderResult(
                success=False,
                message=f"Unknown asset: {symbol}"
            )
        
        try:
            # Prepare order
            # For market orders, we use a limit order with aggressive price
            # and IOC (Immediate or Cancel) time in force
            order = {
                "a": asset_index,
                "b": is_buy,
                "p": "0" if is_buy else "999999",  # Aggressive price for market execution
                "s": str(abs(size)),
                "r": reduce_only,
                "t": {"limit": {"tif": "Ioc"}}  # Immediate or Cancel
            }
            
            # Place order
            result = self.exchange.order(order)
            
            # Parse result
            if result.get("status") == "ok":
                response = result.get("response", {})
                data = response.get("data", {})
                statuses = data.get("statuses", [])
                
                if statuses:
                    status = statuses[0]
                    
                    # Check if filled
                    if "filled" in status:
                        filled = status["filled"]
                        return OrderResult(
                            success=True,
                            message="Order filled successfully",
                            order_id=filled.get("oid"),
                            filled_size=float(filled.get("totalSz", 0)),
                            avg_price=float(filled.get("avgPx", 0))
                        )
                    
                    # Check if resting (shouldn't happen with IOC)
                    elif "resting" in status:
                        return OrderResult(
                            success=False,
                            message="Order resting (unexpected for market order)",
                            order_id=status["resting"].get("oid")
                        )
                    
                    # Check for error
                    elif "error" in status:
                        return OrderResult(
                            success=False,
                            message=f"Order error: {status['error']}"
                        )
            
            return OrderResult(
                success=False,
                message=f"Unexpected response: {result}"
            )
            
        except Exception as e:
            return OrderResult(
                success=False,
                message=f"Exception: {str(e)}"
            )
    
    def increase_short(self, symbol: str, size: float) -> OrderResult:
        """
        Increase short position (sell)
        
        Args:
            symbol: Asset symbol
            size: Amount to increase short by
            
        Returns:
            OrderResult
        """
        return self.place_market_order(symbol, size, is_buy=False, reduce_only=False)
    
    def decrease_short(self, symbol: str, size: float) -> OrderResult:
        """
        Decrease short position (buy to close)
        
        Args:
            symbol: Asset symbol
            size: Amount to decrease short by
            
        Returns:
            OrderResult
        """
        return self.place_market_order(symbol, size, is_buy=True, reduce_only=True)
    
    def execute_adjustments(self, adjustments: List[Dict]) -> List[Dict]:
        """
        Execute multiple position adjustments
        
        Args:
            adjustments: List of adjustment dicts with keys:
                - token: str
                - action: "increase_short" or "decrease_short"
                - amount: float
                
        Returns:
            List of results with success status
        """
        results = []
        
        for adj in adjustments:
            token = adj["token"]
            action = adj["action"]
            amount = adj["amount"]
            
            if action == "increase_short":
                result = self.increase_short(token, amount)
            elif action == "decrease_short":
                result = self.decrease_short(token, amount)
            else:
                result = OrderResult(
                    success=False,
                    message=f"Unknown action: {action}"
                )
            
            results.append({
                "token": token,
                "action": action,
                "amount": amount,
                "success": result.success,
                "message": result.message,
                "order_id": result.order_id,
                "filled_size": result.filled_size,
                "avg_price": result.avg_price
            })
        
        return results
