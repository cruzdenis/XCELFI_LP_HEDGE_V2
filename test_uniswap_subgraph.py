"""
Test Script: Uniswap Subgraph API

This script tests fetching LP position data from Uniswap v3 Subgraph via The Graph.

Note: The old hosted service endpoint is deprecated.
You need to use the decentralized network endpoint with an API key.

To get an API key:
1. Go to https://thegraph.com/studio/
2. Create an account
3. Create an API key (free tier available)
"""

import requests
import json

# ============================================================
# CONFIGURATION
# ============================================================

# NOTE: The hosted service has been deprecated!
# You MUST get an API key from https://thegraph.com/studio/ (free tier available)
# Then use: https://gateway.thegraph.com/api/<YOUR_API_KEY>/subgraphs/id/5zvR82QoaXYFyDEKLZ9t6v9adgnptxYpKpSbxtgVENFV

# PLACEHOLDER - Replace with your API key
THE_GRAPH_API_KEY = "YOUR_API_KEY_HERE"  # Get from https://thegraph.com/studio/

if THE_GRAPH_API_KEY == "YOUR_API_KEY_HERE":
    print("⚠️ WARNING: You need to set THE_GRAPH_API_KEY!")
    print("   1. Go to https://thegraph.com/studio/")
    print("   2. Create an account (free)")
    print("   3. Generate an API key")
    print("   4. Replace THE_GRAPH_API_KEY in this script")
    print("")
    UNISWAP_V3_SUBGRAPH_URL = "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3"  # Will fail
else:
    UNISWAP_V3_SUBGRAPH_URL = f"https://gateway.thegraph.com/api/{THE_GRAPH_API_KEY}/subgraphs/id/5zvR82QoaXYFyDEKLZ9t6v9adgnptxYpKpSbxtgVENFV"

# Example wallet address (replace with your own)
WALLET_ADDRESS = "0xc1E18438Fed146D814418364134fE28cC8622B5C"

# ============================================================
# GRAPHQL QUERIES
# ============================================================

# Query 1: Get global Uniswap v3 stats
QUERY_GLOBAL_STATS = """
{
  factory(id: "0x1F98431c8aD98523631AE4a59f267346ea31F984") {
    poolCount
    txCount
    totalVolumeUSD
    totalValueLockedUSD
  }
}
"""

# Query 2: Get LP positions for a wallet
QUERY_POSITIONS_BY_WALLET = """
query GetPositions($owner: String!) {
  positions(
    where: { owner: $owner }
    first: 100
  ) {
    id
    owner
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
      sqrtPrice
      liquidity
    }
  }
}
"""

# Query 3: Get top pools by liquidity
QUERY_TOP_POOLS = """
{
  pools(
    first: 10
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
  }
}
"""

# ============================================================
# FUNCTIONS
# ============================================================

def query_subgraph(query: str, variables: dict = None):
    """
    Execute a GraphQL query against the Uniswap v3 subgraph.
    
    Args:
        query: GraphQL query string
        variables: Optional variables for the query
        
    Returns:
        Response JSON or error
    """
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    
    try:
        response = requests.post(
            UNISWAP_V3_SUBGRAPH_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def print_result(title: str, result: dict):
    """Pretty print a result."""
    print("\n" + "="*60)
    print(f"📊 {title}")
    print("="*60)
    print(json.dumps(result, indent=2))

# ============================================================
# TESTS
# ============================================================

def test_global_stats():
    """Test: Fetch global Uniswap v3 statistics."""
    print("\n🧪 TEST 1: Global Uniswap v3 Statistics")
    result = query_subgraph(QUERY_GLOBAL_STATS)
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return False
    
    if "errors" in result:
        print(f"❌ GraphQL Error: {result['errors']}")
        return False
    
    if "data" in result and "factory" in result["data"]:
        factory = result["data"]["factory"]
        print(f"✅ Success!")
        print(f"   Total Pools: {factory['poolCount']}")
        print(f"   Total Transactions: {factory['txCount']}")
        print(f"   Total Volume: ${float(factory['totalVolumeUSD']):,.2f}")
        print(f"   Total Value Locked: ${float(factory['totalValueLockedUSD']):,.2f}")
        return True
    else:
        print(f"❌ Unexpected response: {result}")
        return False

def test_positions_by_wallet():
    """Test: Fetch LP positions for a wallet."""
    print(f"\n🧪 TEST 2: LP Positions for Wallet {WALLET_ADDRESS}")
    
    result = query_subgraph(
        QUERY_POSITIONS_BY_WALLET,
        variables={"owner": WALLET_ADDRESS.lower()}
    )
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return False
    
    if "errors" in result:
        print(f"❌ GraphQL Error: {result['errors']}")
        return False
    
    if "data" in result and "positions" in result["data"]:
        positions = result["data"]["positions"]
        print(f"✅ Success! Found {len(positions)} positions")
        
        if len(positions) > 0:
            print("\n📋 Position Details:")
            for i, pos in enumerate(positions[:5], 1):  # Show first 5
                pool = pos["pool"]
                token0 = pool["token0"]["symbol"]
                token1 = pool["token1"]["symbol"]
                liquidity = pos["liquidity"]
                
                print(f"\n   Position {i}:")
                print(f"   • Pool: {token0}/{token1}")
                print(f"   • Liquidity: {liquidity}")
                print(f"   • Deposited {token0}: {pos['depositedToken0']}")
                print(f"   • Deposited {token1}: {pos['depositedToken1']}")
                print(f"   • Fees {token0}: {pos['collectedFeesToken0']}")
                print(f"   • Fees {token1}: {pos['collectedFeesToken1']}")
        else:
            print("   No positions found for this wallet")
        
        return True
    else:
        print(f"❌ Unexpected response: {result}")
        return False

def test_top_pools():
    """Test: Fetch top pools by TVL."""
    print("\n🧪 TEST 3: Top 10 Pools by TVL")
    
    result = query_subgraph(QUERY_TOP_POOLS)
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return False
    
    if "errors" in result:
        print(f"❌ GraphQL Error: {result['errors']}")
        return False
    
    if "data" in result and "pools" in result["data"]:
        pools = result["data"]["pools"]
        print(f"✅ Success! Found {len(pools)} pools")
        
        print("\n📋 Top Pools:")
        for i, pool in enumerate(pools, 1):
            token0 = pool["token0"]["symbol"]
            token1 = pool["token1"]["symbol"]
            tvl = float(pool["totalValueLockedUSD"])
            volume = float(pool["volumeUSD"])
            
            print(f"   {i}. {token0}/{token1}")
            print(f"      TVL: ${tvl:,.2f} | Volume: ${volume:,.2f}")
        
        return True
    else:
        print(f"❌ Unexpected response: {result}")
        return False

# ============================================================
# MAIN
# ============================================================

def main():
    print("="*60)
    print("🧪 UNISWAP V3 SUBGRAPH API TEST")
    print("="*60)
    print(f"\nEndpoint: {UNISWAP_V3_SUBGRAPH_URL}")
    print(f"Wallet: {WALLET_ADDRESS}")
    
    # Run tests
    results = []
    results.append(("Global Stats", test_global_stats()))
    results.append(("Positions by Wallet", test_positions_by_wallet()))
    results.append(("Top Pools", test_top_pools()))
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    total_passed = sum(1 for _, passed in results if passed)
    print(f"\nTotal: {total_passed}/{len(results)} tests passed")
    
    if total_passed == len(results):
        print("\n🎉 All tests passed! Uniswap Subgraph API is working!")
    else:
        print("\n⚠️ Some tests failed. Check the errors above.")
        print("\nNote: The hosted service endpoint may be deprecated.")
        print("For production, get an API key from https://thegraph.com/studio/")

if __name__ == "__main__":
    main()
