"""
Octav.fi API Client V3
UNIVERSAL PROTOCOL SUPPORT - Extracts LP positions from ALL protocols
"""

import requests
from typing import Dict, List
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
    position_type: str  # 'supply', 'reward', 'asset', etc.


@dataclass
class PerpPosition:
    """Perpetual position (Hyperliquid)"""
    symbol: str
    size: float  # Negative for short
    mark_price: float
    position_value: float
    margin_used: float
    entry_price: float
    open_pnl: float
    funding_all_time: float
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
        Extract LP positions from ALL protocols (universal extractor)
        
        Supports: Uniswap, Aerodrome, Revert Finance, Curve, Sushiswap, etc.
        
        Args:
            portfolio_data: Portfolio data from API
            
        Returns:
            List of LP positions from all protocols
        """
        lp_positions = []
        
        if not portfolio_data:
            return lp_positions
        
        # Get assetByProtocols
        assets_by_protocol = portfolio_data.get("assetByProtocols", {})
        
        # Skip these protocols (not LP protocols)
        skip_protocols = ["wallet", "hyperliquid"]
        
        # Iterate through ALL protocols
        for protocol_key, protocol_data in assets_by_protocol.items():
            # Skip non-LP protocols
            if protocol_key.lower() in skip_protocols:
                continue
            
            # Get protocol display name
            protocol_name = protocol_key.replace("_", " ").title()
            
            # Get chains
            chains = protocol_data.get("chains", {})
            
            for chain_key, chain_data in chains.items():
                # Get protocol positions
                protocol_positions = chain_data.get("protocolPositions", {})
                
                # Iterate through position types (LIQUIDITYPOOL, LENDING, etc.)
                for position_type_key, position_type_data in protocol_positions.items():
                    # Get protocol positions array
                    positions_array = position_type_data.get("protocolPositions", [])
                    
                    for position_item in positions_array:
                        # Extract from multiple possible fields
                        
                        # 1. supplyAssets (Revert Finance style)
                        supply_assets = position_item.get("supplyAssets", [])
                        for asset in supply_assets:
                            position = self._create_lp_position(
                                protocol_name, asset, chain_key, "supply"
                            )
                            if position:
                                lp_positions.append(position)
                        
                        # 2. rewardAssets (Revert Finance style)
                        reward_assets = position_item.get("rewardAssets", [])
                        for asset in reward_assets:
                            position = self._create_lp_position(
                                protocol_name, asset, chain_key, "reward"
                            )
                            if position:
                                lp_positions.append(position)
                        
                        # 3. assets (Uniswap style)
                        assets = position_item.get("assets", [])
                        for asset in assets:
                            position = self._create_lp_position(
                                protocol_name, asset, chain_key, "asset"
                            )
                            if position:
                                lp_positions.append(position)
                        
                        # 4. dexAssets (some protocols)
                        dex_assets = position_item.get("dexAssets", [])
                        for asset in dex_assets:
                            position = self._create_lp_position(
                                protocol_name, asset, chain_key, "dex"
                            )
                            if position:
                                lp_positions.append(position)
        
        return lp_positions
    
    def _create_lp_position(
        self, 
        protocol: str, 
        asset: Dict, 
        chain: str, 
        position_type: str
    ) -> LPPosition:
        """
        Create LPPosition from asset data
        
        Args:
            protocol: Protocol name
            asset: Asset dictionary
            chain: Chain key
            position_type: Type of position
            
        Returns:
            LPPosition or None if invalid
        """
        try:
            balance = float(asset.get("balance", 0))
            price = float(asset.get("price", 0))
            value = float(asset.get("value", 0))
            symbol = asset.get("symbol", "")
            
            # Skip zero balances and values
            if balance == 0 and value == 0:
                return None
            
            # Skip if no symbol
            if not symbol:
                return None
            
            return LPPosition(
                protocol=protocol,
                token_symbol=symbol,
                balance=balance,
                price=price,
                value=value,
                chain=chain,
                position_type=position_type
            )
        except (ValueError, TypeError):
            return None
    
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
        hl_data = assets_by_protocol.get("hyperliquid", {})
        if hl_data:
            chains = hl_data.get("chains", {})
            for chain_key, chain_data in chains.items():
                protocol_positions = chain_data.get("protocolPositions", {})
                margin_data = protocol_positions.get("MARGIN", {})
                
                # Get protocol positions (which contain dexAssets)
                proto_positions = margin_data.get("protocolPositions", [])
                for proto_pos in proto_positions:
                    dex_assets = proto_pos.get("dexAssets", [])
                    for asset in dex_assets:
                        balance = float(asset.get("balance", 0))
                        symbol = asset.get("symbol", "")
                        
                        # Skip wallet entry and zero balances
                        if symbol.lower() == "wallet" or balance == 0:
                            continue
                        
                        position = PerpPosition(
                            symbol=symbol,
                            size=balance,
                            mark_price=float(asset.get("price", 0)),
                            position_value=float(asset.get("value", 0)),
                            margin_used=float(asset.get("marginUsed", 0)),
                            entry_price=float(asset.get("entryPrice", 0)),
                            open_pnl=float(asset.get("openPnl", 0)),
                            funding_all_time=float(asset.get("fundingAllTime", 0)),
                            leverage=asset.get("leverage", "N/A")
                        )
                        perp_positions.append(position)
        
        return perp_positions
    
    @staticmethod
    def normalize_symbol(symbol: str) -> str:
        """
        Normalize token symbol for comparison
        
        Args:
            symbol: Token symbol (e.g., 'WBTC', 'weth', 'BTC')
            
        Returns:
            Normalized symbol (e.g., 'BTC', 'ETH')
        """
        symbol = symbol.upper()
        
        # Remove 'W' prefix for wrapped tokens
        if symbol.startswith('W') and len(symbol) > 1:
            return symbol[1:]  # WBTC -> BTC, WETH -> ETH
        
        return symbol


# Example usage and testing
if __name__ == "__main__":
    import json
    
    # Test with real data
    API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJodHRwczovL2hhc3VyYS5pby9qd3QvY2xhaW1zIjp7IngtaGFzdXJhLWRlZmF1bHQtcm9sZSI6InVzZXIiLCJ4LWhhc3VyYS1hbGxvd2VkLXJvbGVzIjpbInVzZXIiXSwieC1oYXN1cmEtdXNlci1pZCI6InNhbnJlbW8yNjE0MSJ9fQ.0eLf5m4kQPETnUaZbN6LFMoV8hxGwjrdZ598r9o61Yc"
    WALLET = "0x85963d266B718006375feC16649eD18c954cf213"
    
    client = OctavClient(API_KEY)
    portfolio = client.get_portfolio(WALLET)
    
    print("=" * 60)
    print("TESTING UNIVERSAL LP EXTRACTOR")
    print("=" * 60)
    
    lp_positions = client.extract_lp_positions(portfolio)
    
    print(f"\nFound {len(lp_positions)} LP positions across all protocols:\n")
    
    # Group by protocol
    by_protocol = {}
    for pos in lp_positions:
        if pos.protocol not in by_protocol:
            by_protocol[pos.protocol] = []
        by_protocol[pos.protocol].append(pos)
    
    for protocol, positions in by_protocol.items():
        total_value = sum(p.value for p in positions)
        print(f"\n{protocol}: ${total_value:,.2f}")
        for pos in positions:
            print(f"  └─ {pos.token_symbol}: {pos.balance:.6f} @ ${pos.price:.2f} = ${pos.value:.2f} ({pos.position_type})")
    
    print("\n" + "=" * 60)
    print("COMPARISON WITH OLD EXTRACTOR")
    print("=" * 60)
    
    # Import old client
    import sys
    sys.path.insert(0, "/home/ubuntu/XCELFI_LP_HEDGE_V2")
    from octav_client import OctavClient as OldClient
    
    old_client = OldClient(API_KEY)
    old_positions = old_client.extract_lp_positions(portfolio)
    
    print(f"\nOld extractor: {len(old_positions)} positions (Revert only)")
    print(f"New extractor: {len(lp_positions)} positions (All protocols)")
    print(f"Improvement: +{len(lp_positions) - len(old_positions)} positions")
