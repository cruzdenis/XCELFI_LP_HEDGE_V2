from typing import Optional, Dict
from dataclasses import dataclass

@dataclass
class OrderResult:
    success: bool
    message: str
    order_id: Optional[str] = None
    filled_size: Optional[float] = None
    avg_price: Optional[float] = None

class HyperliquidClient:
    """Client for Hyperliquid API operations"""
    
    # Asset mapping
    ASSET_MAP = {
        "BTC": "BTC",
        "ETH": "ETH",
        "SOL": "SOL",
        "ARB": "ARB",
        "AVAX": "AVAX",
        "OP": "OP",
    }
    
    def __init__(self, wallet_address: str, private_key: Optional[str] = None):
        """
        Initialize Hyperliquid client
        
        Args:
            wallet_address: Ethereum wallet address
            private_key: Private key for signing transactions (optional)
        """
        self.wallet_address = wallet_address
        self.can_execute = private_key is not None
        
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
        
        # Normalize symbol
        symbol = symbol.upper().replace("WBTC", "BTC").replace("WETH", "ETH")
        
        try:
            # Use market order with IOC (Immediate or Cancel)
            order_type = {"limit": {"tif": "Ioc"}}
            
            # For market orders, use aggressive price
            # Get mid price first
            all_mids = self.exchange.info.all_mids()
            if symbol not in all_mids:
                return OrderResult(
                    success=False,
                    message=f"Unknown asset: {symbol}"
                )
            
            mid_price = float(all_mids[symbol])
            
            # Apply 5% slippage for market execution
            slippage = 0.05
            limit_px = mid_price * (1 + slippage) if is_buy else mid_price * (1 - slippage)
            
            # Round size to appropriate precision
            # BTC/ETH typically use 4 decimal places for size
            # Round to 5 significant figures to avoid rounding errors
            rounded_size = round(abs(size), 5)
            
            # Place order using correct SDK method signature
            result = self.exchange.order(
                name=symbol,
                is_buy=is_buy,
                sz=rounded_size,
                limit_px=limit_px,
                order_type=order_type,
                reduce_only=reduce_only
            )
            
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
                    else:
                        # Order placed but not filled
                        return OrderResult(
                            success=False,
                            message=f"Order not filled: {status}"
                        )
            
            return OrderResult(
                success=False,
                message=f"Order failed: {result}"
            )
            
        except Exception as e:
            return OrderResult(
                success=False,
                message=f"Exception: {str(e)}"
            )
    
    def increase_short(self, symbol: str, amount: float) -> OrderResult:
        """
        Increase short position (sell)
        
        Args:
            symbol: Asset symbol
            amount: Amount to short (positive value)
            
        Returns:
            OrderResult
        """
        return self.place_market_order(symbol, amount, is_buy=False, reduce_only=False)
    
    def decrease_short(self, symbol: str, amount: float) -> OrderResult:
        """
        Decrease short position (buy to close)
        
        Args:
            symbol: Asset symbol
            amount: Amount to close (positive value)
            
        Returns:
            OrderResult
        """
        return self.place_market_order(symbol, amount, is_buy=True, reduce_only=True)
    
    def execute_adjustments(self, adjustments: list) -> list:
        """
        Execute multiple adjustments
        
        Args:
            adjustments: List of dicts with 'token', 'action', 'amount'
                        action can be 'increase_short' or 'decrease_short'
        
        Returns:
            List of OrderResult objects
        """
        results = []
        
        for adj in adjustments:
            token = adj['token']
            action = adj['action']
            amount = adj['amount']
            
            if action == 'increase_short':
                result = self.increase_short(token, amount)
            elif action == 'decrease_short':
                result = self.decrease_short(token, amount)
            else:
                result = OrderResult(
                    success=False,
                    message=f"Unknown action: {action}"
                )
            
            results.append({
                'token': token,
                'action': action,
                'amount': amount,
                'result': result
            })
        
        return results
