"""
Hyperliquid integration module.
Handles reading positions and executing trades on Hyperliquid DEX.
"""
import requests
import hmac
import hashlib
import time
from typing import Optional, Dict, List
from dataclasses import dataclass


@dataclass
class Position:
    """Perpetual position data."""
    symbol: str
    size: float  # Positive for long, negative for short
    entry_price: float
    mark_price: float
    unrealized_pnl: float
    margin: float
    leverage: float


@dataclass
class FundingInfo:
    """Funding rate information."""
    symbol: str
    funding_rate: float  # Current funding rate
    funding_rate_24h: float  # 24h average
    next_funding_time: int  # Unix timestamp


class HyperliquidClient:
    """
    Client for interacting with Hyperliquid DEX.
    
    Supports both read-only (public) and execution (API keys) modes.
    """
    
    def __init__(
        self,
        base_url: str,
        wallet_address: str,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None
    ):
        """
        Initialize Hyperliquid client.
        
        Args:
            base_url: Hyperliquid API base URL
            wallet_address: User wallet address
            api_key: Optional API key for execution mode
            api_secret: Optional API secret for execution mode
        """
        self.base_url = base_url
        self.wallet_address = wallet_address
        self.api_key = api_key
        self.api_secret = api_secret
        
        # Check if in execution mode
        self.is_execution_mode = bool(api_key and api_secret)
    
    def _sign_request(self, method: str, endpoint: str, params: Dict) -> Dict[str, str]:
        """
        Sign request for authenticated endpoints.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Request parameters
            
        Returns:
            Headers with signature
        """
        if not self.is_execution_mode:
            raise Exception("Execution mode not enabled - API keys required")
        
        # Create signature (implementation depends on Hyperliquid's auth scheme)
        timestamp = str(int(time.time() * 1000))
        message = f"{timestamp}{method}{endpoint}"
        
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return {
            "X-API-KEY": self.api_key,
            "X-TIMESTAMP": timestamp,
            "X-SIGNATURE": signature
        }
    
    def is_healthy(self) -> bool:
        """
        Check if Hyperliquid API is healthy.
        
        Returns:
            True if API is responding, False otherwise
        """
        try:
            response = requests.get(
                f"{self.base_url}/info",
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def get_positions(self) -> List[Position]:
        """
        Get open positions for wallet (read-only).
        
        Returns:
            List of Position objects
        """
        try:
            # In a real implementation, this would query Hyperliquid API
            # For now, return mock data
            
            return [
                Position(
                    symbol="BTC/USDC",
                    size=-0.5,  # Short 0.5 BTC
                    entry_price=45000.0,
                    mark_price=44500.0,
                    unrealized_pnl=250.0,
                    margin=5000.0,
                    leverage=4.5
                ),
                Position(
                    symbol="ETH/USDC",
                    size=-5.0,  # Short 5 ETH
                    entry_price=2500.0,
                    mark_price=2480.0,
                    unrealized_pnl=100.0,
                    margin=2500.0,
                    leverage=5.0
                )
            ]
        except Exception as e:
            print(f"Error getting positions: {e}")
            return []
    
    def get_funding_info(self, symbol: str) -> Optional[FundingInfo]:
        """
        Get funding rate information (read-only).
        
        Args:
            symbol: Trading pair symbol (e.g., "BTC/USDC")
            
        Returns:
            FundingInfo or None if error
        """
        try:
            # In a real implementation, this would query Hyperliquid API
            # For now, return mock data
            
            if "BTC" in symbol:
                return FundingInfo(
                    symbol=symbol,
                    funding_rate=0.0001,  # 0.01% per 8h
                    funding_rate_24h=0.0003,  # 0.03% per day
                    next_funding_time=int(time.time()) + 3600
                )
            elif "ETH" in symbol:
                return FundingInfo(
                    symbol=symbol,
                    funding_rate=0.00008,
                    funding_rate_24h=0.00024,
                    next_funding_time=int(time.time()) + 3600
                )
            else:
                return None
        except Exception as e:
            print(f"Error getting funding info: {e}")
            return None
    
    def get_mark_price(self, symbol: str) -> Optional[float]:
        """
        Get current mark price (read-only).
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            Mark price or None if error
        """
        try:
            # In a real implementation, this would query Hyperliquid API
            # For now, return mock data
            
            if "BTC" in symbol:
                return 45000.0
            elif "ETH" in symbol:
                return 2500.0
            else:
                return None
        except Exception as e:
            print(f"Error getting mark price: {e}")
            return None
    
    def get_balance(self) -> Dict[str, float]:
        """
        Get account balance (read-only).
        
        Returns:
            Dictionary with balance info
        """
        try:
            # In a real implementation, this would query Hyperliquid API
            # For now, return mock data
            
            return {
                "total_equity": 15000.0,
                "available_balance": 7500.0,
                "margin_used": 7500.0,
                "unrealized_pnl": 350.0
            }
        except Exception as e:
            print(f"Error getting balance: {e}")
            return {}
    
    # Execution functions (require API keys)
    
    def open_short(
        self,
        symbol: str,
        size: float,
        leverage: float = 1.0,
        order_type: str = "MARKET"
    ) -> Optional[str]:
        """
        Open short position (execution mode only).
        
        Args:
            symbol: Trading pair symbol
            size: Position size (positive number)
            leverage: Leverage multiplier
            order_type: Order type ("MARKET" or "LIMIT")
            
        Returns:
            Order ID or None if error
        """
        if not self.is_execution_mode:
            raise Exception("Execution mode not enabled - API keys required")
        
        try:
            # In a real implementation, this would:
            # 1. Build order request
            # 2. Sign request
            # 3. Send to Hyperliquid API
            # 4. Return order ID
            
            print(f"[MOCK] Opening short: {size} {symbol} at {leverage}x leverage")
            return "mock_order_id_short"
        except Exception as e:
            print(f"Error opening short: {e}")
            return None
    
    def close_position(
        self,
        symbol: str,
        size: Optional[float] = None
    ) -> Optional[str]:
        """
        Close position (execution mode only).
        
        Args:
            symbol: Trading pair symbol
            size: Size to close (None = close all)
            
        Returns:
            Order ID or None if error
        """
        if not self.is_execution_mode:
            raise Exception("Execution mode not enabled - API keys required")
        
        try:
            # In a real implementation, this would:
            # 1. Get current position
            # 2. Build closing order
            # 3. Sign and send request
            # 4. Return order ID
            
            size_str = f"{size}" if size else "all"
            print(f"[MOCK] Closing position: {size_str} {symbol}")
            return "mock_order_id_close"
        except Exception as e:
            print(f"Error closing position: {e}")
            return None
    
    def adjust_position(
        self,
        symbol: str,
        target_size: float
    ) -> Optional[str]:
        """
        Adjust position to target size (execution mode only).
        
        Args:
            symbol: Trading pair symbol
            target_size: Target position size (negative for short)
            
        Returns:
            Order ID or None if error
        """
        if not self.is_execution_mode:
            raise Exception("Execution mode not enabled - API keys required")
        
        try:
            # Get current position
            positions = self.get_positions()
            current_size = 0.0
            
            for pos in positions:
                if pos.symbol == symbol:
                    current_size = pos.size
                    break
            
            # Calculate adjustment needed
            adjustment = target_size - current_size
            
            if abs(adjustment) < 0.001:
                print(f"[MOCK] Position already at target: {symbol}")
                return None
            
            # In a real implementation, this would execute the adjustment
            print(f"[MOCK] Adjusting position: {symbol} from {current_size} to {target_size} (delta: {adjustment})")
            return "mock_order_id_adjust"
        except Exception as e:
            print(f"Error adjusting position: {e}")
            return None
