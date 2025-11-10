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
            # Query Hyperliquid clearinghouse state
            response = requests.post(
                f"{self.base_url}/info",
                json={
                    "type": "clearinghouseState",
                    "user": self.wallet_address
                },
                timeout=10
            )
            
            if response.status_code != 200:
                print(f"[ERROR] Hyperliquid API returned status {response.status_code}")
                return []
            
            data = response.json()
            positions = []
            
            # Parse asset positions
            for asset_pos in data.get("assetPositions", []):
                pos_data = asset_pos.get("position", {})
                
                # Extract position data
                coin = pos_data.get("coin", "")
                szi = float(pos_data.get("szi", 0))
                
                # Skip if no position
                if abs(szi) < 0.0001:
                    continue
                
                entry_px = float(pos_data.get("entryPx", 0))
                position_value = float(pos_data.get("positionValue", 0))
                unrealized_pnl = float(pos_data.get("unrealizedPnl", 0))
                margin_used = float(pos_data.get("marginUsed", 0))
                
                # Calculate mark price from position value and size
                mark_price = abs(position_value / szi) if szi != 0 else entry_px
                
                # Get leverage
                leverage_info = pos_data.get("leverage", {})
                leverage = float(leverage_info.get("value", 1))
                
                positions.append(Position(
                    symbol=coin,
                    size=szi,
                    entry_price=entry_px,
                    mark_price=mark_price,
                    unrealized_pnl=unrealized_pnl,
                    margin=margin_used,
                    leverage=leverage
                ))
            
            return positions
            
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
            # TODO: Implement real Hyperliquid API query
            # For now, return None to indicate no real data available
            print(f"[INFO] Funding info query not implemented for {symbol} - returning None")
            return None
        except Exception as e:
            print(f"Error getting funding info: {e}")
            return None
    
    def get_mark_price(self, symbol: str) -> Optional[float]:
        """
        Get current mark price (read-only).
        
        Args:
            symbol: Trading pair symbol (e.g., "BTC", "ETH")
            
        Returns:
            Mark price or None if error
        """
        try:
            # Query all mids from Hyperliquid
            response = requests.post(
                f"{self.base_url}/info",
                json={"type": "allMids"},
                timeout=10
            )
            
            if response.status_code != 200:
                print(f"[ERROR] Hyperliquid API returned status {response.status_code}")
                return None
            
            mids = response.json()
            
            # Get price for symbol
            price_str = mids.get(symbol)
            if price_str:
                return float(price_str)
            else:
                print(f"[WARNING] Symbol {symbol} not found in mids")
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
            # Query Hyperliquid clearinghouse state
            response = requests.post(
                f"{self.base_url}/info",
                json={
                    "type": "clearinghouseState",
                    "user": self.wallet_address
                },
                timeout=10
            )
            
            if response.status_code != 200:
                print(f"[ERROR] Hyperliquid API returned status {response.status_code}")
                return {}
            
            data = response.json()
            
            # Extract margin summary
            margin_summary = data.get("marginSummary", {})
            
            account_value = float(margin_summary.get("accountValue", 0))
            total_margin_used = float(margin_summary.get("totalMarginUsed", 0))
            total_raw_usd = float(margin_summary.get("totalRawUsd", 0))
            withdrawable = float(data.get("withdrawable", 0))
            
            # Calculate unrealized PnL from positions
            unrealized_pnl = 0.0
            for asset_pos in data.get("assetPositions", []):
                pos_data = asset_pos.get("position", {})
                unrealized_pnl += float(pos_data.get("unrealizedPnl", 0))
            
            return {
                "total_equity": account_value,
                "available_balance": withdrawable,
                "margin_used": total_margin_used,
                "unrealized_pnl": unrealized_pnl,
                "total_raw_usd": total_raw_usd
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
