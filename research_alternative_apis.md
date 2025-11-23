# Research: Alternative APIs for LP Position Data

**Date**: 23 de Novembro de 2025  
**Goal**: Investigate if we can fetch LP position data directly from Revert Finance or Uniswap without using Octav.fi API

---

## 🔍 Findings Summary

### ✅ Uniswap Subgraph (The Graph) - VIABLE
**Status**: ✅ **Recommended - Best Option**

The Uniswap v3 Subgraph provides comprehensive GraphQL API access to all LP position data.

#### Key Information
- **API Type**: GraphQL via The Graph Network
- **Endpoint**: `https://gateway.thegraph.com/api/<YOUR_API_KEY>/subgraphs/id/5zvR82QoaXYFyDEKLZ9t6v9adgnptxYpKpSbxtgVENFV`
- **API Key**: Required (free tier available at https://thegraph.com/studio/)
- **Documentation**: https://docs.uniswap.org/api/subgraph/guides/v3-examples
- **Cost**: Free tier available, paid plans for higher usage

#### Available Data
- ✅ LP positions by wallet address
- ✅ Position liquidity amounts
- ✅ Token0 and Token1 balances
- ✅ Collected fees
- ✅ Pool information
- ✅ Historical data
- ✅ Real-time updates

#### Example Query - Get Positions by Wallet
```graphql
{
  positions(where: { owner: "0xYOUR_WALLET_ADDRESS" }) {
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
    }
  }
}
```

#### Pros
- ✅ Direct access to on-chain data
- ✅ No intermediary API needed
- ✅ Free tier available
- ✅ Well-documented
- ✅ GraphQL = flexible queries
- ✅ Supports multiple chains (Mainnet, Arbitrum, Optimism, Polygon, etc.)
- ✅ Real-time data
- ✅ Historical queries possible

#### Cons
- ⚠️ Requires API key (easy to get)
- ⚠️ GraphQL learning curve (but well-documented)
- ⚠️ Rate limits on free tier
- ⚠️ Only Uniswap v3 positions (not other DEXs)

---

### ❌ Revert Finance API - NOT AVAILABLE
**Status**: ❌ **No Public API**

#### Findings
- Revert Finance is a **frontend analytics tool** for LP management
- **No public API** for programmatic access
- They have a separate product called "Revert.dev" which is a different company (integration API, not DeFi)
- The Revert Finance platform (revert.finance) does not expose API endpoints
- Data is fetched client-side from blockchain/subgraphs

#### What Revert Finance Offers
- Web-based analytics dashboard
- Auto-compounder for LP positions
- Position management tools
- But **no API for external developers**

#### Conclusion
Cannot use Revert Finance as an API source.

---

## 📊 Comparison: Octav.fi vs Uniswap Subgraph

| Feature | Octav.fi API | Uniswap Subgraph |
|---------|--------------|------------------|
| **API Type** | REST | GraphQL |
| **Coverage** | Multi-protocol (Uniswap, Sushiswap, etc.) | Uniswap only |
| **API Key** | Required | Required |
| **Cost** | Unknown (proprietary) | Free tier + paid |
| **Documentation** | Limited | Excellent |
| **Data Freshness** | Real-time | Real-time |
| **Ease of Use** | Simple REST | GraphQL (flexible) |
| **Perpetual Positions** | ✅ Yes (Hyperliquid) | ❌ No (only LP) |
| **Multi-chain** | ✅ Yes | ✅ Yes |

---

## 🎯 Recommendation

### Option 1: Switch to Uniswap Subgraph (Recommended for V4)
**Use Case**: If you only need Uniswap v3 LP positions

**Pros**:
- Free tier available
- Well-documented
- Direct on-chain data
- No dependency on third-party API service

**Cons**:
- Only Uniswap (no Sushiswap, Curve, etc.)
- Need to implement GraphQL client
- Still need Octav.fi or another source for Hyperliquid perpetual positions

### Option 2: Keep Octav.fi + Add Uniswap Subgraph (Hybrid)
**Use Case**: Best of both worlds

**Pros**:
- Octav.fi for multi-protocol LP + perpetuals
- Uniswap Subgraph as backup/validation
- Redundancy if one API fails

**Cons**:
- More complex code
- Two API keys to manage

### Option 3: Keep Octav.fi Only (Current V3)
**Use Case**: If Octav.fi meets all needs

**Pros**:
- Already implemented
- Multi-protocol support
- Single API to manage

**Cons**:
- Dependency on single third-party service
- Unknown pricing/limits

---

## 💻 Implementation Plan for Uniswap Subgraph

If you want to switch to Uniswap Subgraph in V4, here's the plan:

### Step 1: Get API Key
1. Go to https://thegraph.com/studio/
2. Create account
3. Generate API key (free tier)

### Step 2: Create Uniswap Client
```python
import requests

class UniswapSubgraphClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.endpoint = f"https://gateway.thegraph.com/api/{api_key}/subgraphs/id/5zvR82QoaXYFyDEKLZ9t6v9adgnptxYpKpSbxtgVENFV"
    
    def query(self, query: str):
        response = requests.post(
            self.endpoint,
            json={'query': query}
        )
        return response.json()
    
    def get_positions(self, wallet_address: str):
        query = f"""
        {{
          positions(where: {{ owner: "{wallet_address.lower()}" }}) {{
            id
            liquidity
            pool {{
              token0 {{
                symbol
                decimals
              }}
              token1 {{
                symbol
                decimals
              }}
            }}
            depositedToken0
            depositedToken1
          }}
        }}
        """
        return self.query(query)
```

### Step 3: Parse Response
```python
def extract_lp_positions(response):
    positions = response['data']['positions']
    lp_balances = {}
    
    for pos in positions:
        # Calculate actual token amounts from liquidity
        token0_symbol = pos['pool']['token0']['symbol']
        token1_symbol = pos['pool']['token1']['symbol']
        
        # Normalize symbols (WBTC -> BTC, WETH -> ETH)
        token0_symbol = normalize_symbol(token0_symbol)
        token1_symbol = normalize_symbol(token1_symbol)
        
        # Add to balances
        lp_balances[token0_symbol] = lp_balances.get(token0_symbol, 0) + float(pos['depositedToken0'])
        lp_balances[token1_symbol] = lp_balances.get(token1_symbol, 0) + float(pos['depositedToken1'])
    
    return lp_balances
```

### Step 4: Integration
Replace `octav_client.get_portfolio()` with `uniswap_client.get_positions()` in the sync flow.

---

## 🚀 Next Steps

### For V4 Development:

**Option A: Add Uniswap Subgraph as Alternative**
1. Create `uniswap_subgraph_client.py`
2. Add toggle in config: "Use Uniswap Subgraph" vs "Use Octav.fi"
3. Keep both implementations
4. User chooses which to use

**Option B: Hybrid Approach**
1. Use Uniswap Subgraph for LP positions
2. Keep Octav.fi for perpetual positions
3. Merge data from both sources

**Option C: Stay with Octav.fi**
1. Keep current implementation
2. Document Uniswap Subgraph as alternative for future

---

## 📝 Conclusion

**Yes, you can get LP data directly from Uniswap without Octav.fi!**

The **Uniswap Subgraph via The Graph** is a viable, well-documented, and free alternative for fetching Uniswap v3 LP positions.

However, note that:
- ✅ Uniswap Subgraph = LP positions only (Uniswap v3)
- ❌ Does NOT include perpetual positions (Hyperliquid)
- ❌ Does NOT include other DEXs (Sushiswap, Curve, etc.)

If you need **only Uniswap v3 LP** data, Uniswap Subgraph is perfect.

If you need **multi-protocol LP + perpetuals**, Octav.fi is still better (or use hybrid approach).

---

**Sources**:
- Uniswap Docs: https://docs.uniswap.org/api/subgraph/overview
- The Graph: https://thegraph.com/
- Revert Finance: https://revert.finance/ (no API)
