"""
Uniswap Subgraph Client

Alternative to Octav.fi API for fetching Uniswap v3 LP positions.

Requirements:
- API key from https://thegraph.com/studio/ (free tier available)
- requests library

Usage:
    client = UniswapSubgraphClient(api_key="YOUR_API_KEY")
    positions = client.get_lp_positions("0xWALLET_ADDRESS")
"""

import requests
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class LPPosition:
    """Represents a Uniswap v3 LP position."""
    position_id: str
    token0_symbol: str
    token1_symbol: str
    token0_balance: float
    token1_balance: float
    token0_decimals: int
    token1_decimals: int
    liquidity: str
    pool_address: str
    fee_tier: int
    collected_fees_token0: float
    collected_fees_token1: float

class UniswapSubgraphClient:
    """Client for querying Uniswap v3 data via The Graph subgraph."""
    
    # Subgraph ID for Uniswap v3 on Ethereum Mainnet
    SUBGRAPH_ID = "5zvR82QoaXYFyDEKLZ9t6v9adgnptxYpKpSbxtgVENFV"
    
    # Symbol normalization mapping
    SYMBOL_MAP = {
        "WBTC": "BTC",
        "WETH": "ETH",
        "USDC": "USDC",
        "USDT": "USDT",
        "DAI": "DAI",
    }
    
    def __init__(self, api_key: str, chain: str = "mainnet"):
        """
        Initialize the Uniswap Subgraph client.
        
        Args:
            api_key: API key from https://thegraph.com/studio/
            chain: Blockchain network (default: "mainnet")
        """
        self.api_key = api_key
        self.chain = chain
        self.endpoint = f"https://gateway.thegraph.com/api/{api_key}/subgraphs/id/{self.SUBGRAPH_ID}"
    
    def query(self, query: str, variables: Optional[Dict] = None) -> Dict:
        """
        Execute a GraphQL query against the subgraph.
        
        Args:
            query: GraphQL query string
            variables: Optional query variables
            
        Returns:
            Response data dictionary
            
        Raises:
            Exception: If the query fails
        """
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        
        try:
            response = requests.post(
                self.endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Check for GraphQL errors
            if "errors" in data:
                raise Exception(f"GraphQL errors: {data['errors']}")
            
            return data
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {str(e)}")
    
    def get_lp_positions(self, wallet_address: str) -> List[LPPosition]:
        """
        Get all LP positions for a wallet address.
        
        Args:
            wallet_address: Ethereum wallet address
            
        Returns:
            List of LPPosition objects
        """
        query = """
        query GetPositions($owner: String!) {
          positions(
            where: { owner: $owner, liquidity_gt: "0" }
            first: 1000
          ) {
            id
            liquidity
            depositedToken0
            depositedToken1
            withdrawnToken0
            withdrawnToken1
            collectedFeesToken0
            collectedFeesToken1
            pool {
              id
              token0 {
                id
                symbol
                decimals
              }
              token1 {
                id
                symbol
                decimals
              }
              feeTier
            }
          }
        }
        """
        
        result = self.query(query, variables={"owner": wallet_address.lower()})
        
        positions = []
        for pos_data in result.get("data", {}).get("positions", []):
            pool = pos_data["pool"]
            
            # Calculate current token balances
            # (deposited - withdrawn)
            token0_balance = (
                float(pos_data["depositedToken0"]) - 
                float(pos_data["withdrawnToken0"])
            )
            token1_balance = (
                float(pos_data["depositedToken1"]) - 
                float(pos_data["withdrawnToken1"])
            )
            
            # Skip positions with zero balance
            if token0_balance <= 0 and token1_balance <= 0:
                continue
            
            position = LPPosition(
                position_id=pos_data["id"],
                token0_symbol=pool["token0"]["symbol"],
                token1_symbol=pool["token1"]["symbol"],
                token0_balance=token0_balance,
                token1_balance=token1_balance,
                token0_decimals=int(pool["token0"]["decimals"]),
                token1_decimals=int(pool["token1"]["decimals"]),
                liquidity=pos_data["liquidity"],
                pool_address=pool["id"],
                fee_tier=int(pool["feeTier"]),
                collected_fees_token0=float(pos_data["collectedFeesToken0"]),
                collected_fees_token1=float(pos_data["collectedFeesToken1"])
            )
            
            positions.append(position)
        
        return positions
    
    def normalize_symbol(self, symbol: str) -> str:
        """
        Normalize token symbols (e.g., WBTC -> BTC, WETH -> ETH).
        
        Args:
            symbol: Original token symbol
            
        Returns:
            Normalized symbol
        """
        return self.SYMBOL_MAP.get(symbol, symbol)
    
    def extract_lp_balances(self, wallet_address: str) -> Dict[str, float]:
        """
        Extract LP balances aggregated by token symbol.
        
        This is compatible with the existing delta_neutral_analyzer format.
        
        Args:
            wallet_address: Ethereum wallet address
            
        Returns:
            Dictionary mapping token symbols to total balances
            Example: {"BTC": 0.5, "ETH": 2.3, "USDC": 10000.0}
        """
        positions = self.get_lp_positions(wallet_address)
        
        balances = {}
        
        for pos in positions:
            # Normalize symbols
            token0 = self.normalize_symbol(pos.token0_symbol)
            token1 = self.normalize_symbol(pos.token1_symbol)
            
            # Adjust for decimals
            token0_amount = pos.token0_balance / (10 ** pos.token0_decimals)
            token1_amount = pos.token1_balance / (10 ** pos.token1_decimals)
            
            # Aggregate balances
            balances[token0] = balances.get(token0, 0) + token0_amount
            balances[token1] = balances.get(token1, 0) + token1_amount
        
        return balances
    
    def get_pool_info(self, pool_address: str) -> Dict:
        """
        Get detailed information about a specific pool.
        
        Args:
            pool_address: Pool contract address
            
        Returns:
            Pool information dictionary
        """
        query = """
        query GetPool($poolId: ID!) {
          pool(id: $poolId) {
            id
            token0 {
              symbol
              decimals
            }
            token1 {
              symbol
              decimals
            }
            feeTier
            sqrtPrice
            liquidity
            volumeUSD
            totalValueLockedUSD
          }
        }
        """
        
        result = self.query(query, variables={"poolId": pool_address.lower()})
        return result.get("data", {}).get("pool", {})
    
    def get_top_pools(self, limit: int = 10) -> List[Dict]:
        """
        Get top pools by TVL.
        
        Args:
            limit: Number of pools to return (max 1000)
            
        Returns:
            List of pool dictionaries
        """
        query = """
        query GetTopPools($limit: Int!) {
          pools(
            first: $limit
            orderBy: totalValueLockedUSD
            orderDirection: desc
          ) {
            id
            token0 {
              symbol
            }
            token1 {
              symbol
            }
            totalValueLockedUSD
            volumeUSD
            feeTier
          }
        }
        """
        
        result = self.query(query, variables={"limit": limit})
        return result.get("data", {}).get("pools", [])

# ============================================================
# EXAMPLE USAGE
# ============================================================

if __name__ == "__main__":
    import sys
    
    print("="*60)
    print("Uniswap Subgraph Client - Example Usage")
    print("="*60)
    
    # Check if API key is provided
    if len(sys.argv) < 2:
        print("\n⚠️ Usage: python3 uniswap_subgraph_client.py <API_KEY> [WALLET_ADDRESS]")
        print("\nGet your API key from: https://thegraph.com/studio/")
        sys.exit(1)
    
    api_key = sys.argv[1]
    wallet_address = sys.argv[2] if len(sys.argv) > 2 else "0xc1E18438Fed146D814418364134fE28cC8622B5C"
    
    print(f"\nAPI Key: {api_key[:10]}...")
    print(f"Wallet: {wallet_address}")
    
    # Initialize client
    client = UniswapSubgraphClient(api_key)
    
    # Test 1: Get LP positions
    print("\n" + "-"*60)
    print("📊 Fetching LP Positions...")
    print("-"*60)
    
    try:
        positions = client.get_lp_positions(wallet_address)
        print(f"✅ Found {len(positions)} active positions")
        
        for i, pos in enumerate(positions, 1):
            print(f"\n  Position {i}:")
            print(f"    Pool: {pos.token0_symbol}/{pos.token1_symbol}")
            print(f"    {pos.token0_symbol} Balance: {pos.token0_balance / (10 ** pos.token0_decimals):.6f}")
            print(f"    {pos.token1_symbol} Balance: {pos.token1_balance / (10 ** pos.token1_decimals):.6f}")
            print(f"    Liquidity: {pos.liquidity}")
            print(f"    Fee Tier: {pos.fee_tier / 10000}%")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Get aggregated balances
    print("\n" + "-"*60)
    print("💰 Aggregated LP Balances")
    print("-"*60)
    
    try:
        balances = client.extract_lp_balances(wallet_address)
        print(f"✅ Aggregated balances:")
        
        for token, amount in balances.items():
            print(f"  {token}: {amount:.6f}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Get top pools
    print("\n" + "-"*60)
    print("🏆 Top 5 Pools by TVL")
    print("-"*60)
    
    try:
        top_pools = client.get_top_pools(limit=5)
        print(f"✅ Top pools:")
        
        for i, pool in enumerate(top_pools, 1):
            token0 = pool["token0"]["symbol"]
            token1 = pool["token1"]["symbol"]
            tvl = float(pool["totalValueLockedUSD"])
            print(f"  {i}. {token0}/{token1} - TVL: ${tvl:,.2f}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "="*60)
    print("✅ Example completed!")
    print("="*60)
