"""
Octav.fi API Client
Fetches portfolio data including LP positions and Hyperliquid perpetual positions
"""

import requests
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class LPPosition:
    """Liquidity Provider position"""
    protocol: str
    token_symbol: str
    balance: float
    price: float
    value: float
    chain: str


@dataclass
class PerpPosition:
    """Perpetual position (Hyperliquid)"""
    symbol: str
    size: float  # Negative for short
    mark_price: float
    position_value: float
    margin_value: float
    entry_price: float
    open_pnl: float
    funding: float
    leverage: str


class OctavClient:
    """Client for Octav.fi API"""
    
    def __init__(self, api_key: str):
        """
        Initialize Octav client
        
        Args:
            api_key: Octav.fi API key (Bearer token)
        """
        self.api_key = api_key
        self.base_url = "https://api.octav.fi/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def get_portfolio(self, wallet_address: str) -> Dict:
        """
        Get complete portfolio data for a wallet
        
        Args:
            wallet_address: Ethereum wallet address
            
        Returns:
            Portfolio data dictionary
        """
        try:
            url = f"{self.base_url}/portfolio"
            params = {
                "addresses": wallet_address,
                "includeImages": "false",
                "waitForSync": "false"
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # API returns a list with one object per wallet
            if isinstance(data, list) and len(data) > 0:
                return data[0]
            
            return data
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching portfolio from Octav.fi: {e}")
            return {}
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return {}
    
    def extract_lp_positions(self, portfolio_data: Dict) -> List[LPPosition]:
        """
        Extract LP positions from portfolio data
        
        Args:
            portfolio_data: Portfolio data from API
            
        Returns:
            List of LP positions
        """
        lp_positions = []
        
        if not portfolio_data:
            return lp_positions
        
        # Get assetByProtocols
        assets_by_protocol = portfolio_data.get("assetByProtocols", {})
        
        # Look for Revert Finance, Uniswap V3, and other DEX protocols
        lp_protocols = ["revert", "uniswap_v3", "uniswap_v2", "aerodrome", "velodrome"]
        
        for protocol_key, protocol_data in assets_by_protocol.items():
            # Check if this is an LP protocol
            if any(lp_proto in protocol_key.lower() for lp_proto in lp_protocols):
                protocol_name = protocol_data.get("name", protocol_key)
                assets = protocol_data.get("assets", [])
                
                for asset in assets:
                    position = LPPosition(
                        protocol=protocol_name,
                        token_symbol=asset.get("symbol", ""),
                        balance=float(asset.get("balance", 0)),
                        price=float(asset.get("price", 0)),
                        value=float(asset.get("value", 0)),
                        chain=asset.get("chain", "unknown")
                    )
                    lp_positions.append(position)
        
        return lp_positions
    
    def extract_perp_positions(self, portfolio_data: Dict) -> List[PerpPosition]:
        """
        Extract perpetual positions from Hyperliquid
        
        Args:
            portfolio_data: Portfolio data from API
            
        Returns:
            List of perpetual positions
        """
        perp_positions = []
        
        if not portfolio_data:
            return perp_positions
        
        # Get assetByProtocols
        assets_by_protocol = portfolio_data.get("assetByProtocols", {})
        
        # Look for Hyperliquid protocol
        for protocol_key, protocol_data in assets_by_protocol.items():
            if "hyperliquid" in protocol_key.lower():
                # Hyperliquid positions are in the assets array
                # But we need more detailed data - this is a limitation of the Portfolio endpoint
                # For now, we'll extract basic info from assets
                assets = protocol_data.get("assets", [])
                
                for asset in assets:
                    # Note: The Portfolio endpoint doesn't give us detailed perp data
                    # We would need a different endpoint or parse from the web interface
                    # For now, create basic position info
                    symbol = asset.get("symbol", "")
                    balance = float(asset.get("balance", 0))
                    
                    # Negative balance indicates short position
                    if balance != 0:
                        position = PerpPosition(
                            symbol=symbol,
                            size=balance,
                            mark_price=float(asset.get("price", 0)),
                            position_value=float(asset.get("value", 0)),
                            margin_value=0.0,  # Not available in portfolio endpoint
                            entry_price=0.0,  # Not available in portfolio endpoint
                            open_pnl=0.0,  # Not available in portfolio endpoint
                            funding=0.0,  # Not available in portfolio endpoint
                            leverage="N/A"  # Not available in portfolio endpoint
                        )
                        perp_positions.append(position)
        
        return perp_positions
    
    def get_lp_token_balances(self, wallet_address: str) -> Dict[str, float]:
        """
        Get aggregated token balances from LP positions
        
        Args:
            wallet_address: Wallet address
            
        Returns:
            Dictionary mapping token symbol to total balance
        """
        portfolio = self.get_portfolio(wallet_address)
        lp_positions = self.extract_lp_positions(portfolio)
        
        # Aggregate by token symbol
        token_balances = {}
        for pos in lp_positions:
            symbol = self.normalize_symbol(pos.token_symbol)
            if symbol in token_balances:
                token_balances[symbol] += pos.balance
            else:
                token_balances[symbol] = pos.balance
        
        return token_balances
    
    def get_short_balances(self, wallet_address: str) -> Dict[str, float]:
        """
        Get short position balances from Hyperliquid
        
        Args:
            wallet_address: Wallet address
            
        Returns:
            Dictionary mapping token symbol to short size (absolute value)
        """
        portfolio = self.get_portfolio(wallet_address)
        perp_positions = self.extract_perp_positions(portfolio)
        
        # Aggregate short positions (negative size)
        short_balances = {}
        for pos in perp_positions:
            if pos.size < 0:  # Short position
                symbol = self.normalize_symbol(pos.symbol)
                abs_size = abs(pos.size)
                if symbol in short_balances:
                    short_balances[symbol] += abs_size
                else:
                    short_balances[symbol] = abs_size
        
        return short_balances
    
    @staticmethod
    def normalize_symbol(symbol: str) -> str:
        """
        Normalize token symbols for comparison
        
        Args:
            symbol: Token symbol
            
        Returns:
            Normalized symbol
        """
        symbol = symbol.upper()
        
        # Map wrapped tokens to base tokens
        mapping = {
            'WETH': 'ETH',
            'WBTC': 'BTC',
            'WMATIC': 'MATIC',
            'WAVAX': 'AVAX'
        }
        
        return mapping.get(symbol, symbol)
