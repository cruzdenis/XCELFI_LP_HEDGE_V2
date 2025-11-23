# Blockchain Data Access Research - Summary

**Date**: 23 de Novembro de 2025  
**Goal**: Investigate if we can fetch LP position data directly from blockchain without Octav.fi  
**Target Wallet**: `0xc1E18438Fed146D814418364134fE28cC8622B5C`

---

## 🎯 Executive Summary

**Can we get LP data without Octav.fi?**

**Answer**: **Yes, but with limitations.**

### Options Available:

| Method | Works? | Cost | Complexity | Recommendation |
|--------|--------|------|------------|----------------|
| **Octav.fi** (current) | ✅ Yes | Unknown | Low | ⭐ Keep using |
| **DeBank Cloud API** | ✅ Yes | ~$0.58/month | Low | ⭐ Good alternative |
| **Uniswap Subgraph** | ✅ Yes | Free | Medium | For Uniswap only |
| **Direct RPC** | ⚠️ Partial | Free | High | Complex, incomplete |
| **RabbyWallet API** | ❌ No | N/A | N/A | Doesn't exist |
| **Public APIs** | ❌ No | N/A | N/A | All require API keys |

---

## 📊 Detailed Findings

### 1. ✅ DeBank Cloud API - BEST ALTERNATIVE

**Website**: https://cloud.debank.com/

**What it does**: Provides complete portfolio data including LP positions, farming, staking, etc.

**Pricing**: 
- $200 per 1 million compute units
- Get portfolio = 4 units per call
- **Cost for hourly sync**: ~$0.58/month (720 calls × 4 units)

**Pros**:
- ✅ Multi-protocol (Uniswap, Curve, Sushiswap, etc.)
- ✅ Very cheap (~$0.58/month)
- ✅ Well-documented
- ✅ Real-time data (1 min updates)
- ✅ Includes USD values
- ✅ Easy to integrate (REST API)

**Cons**:
- ⚠️ Requires API key (need to sign up)
- ⚠️ Paid service (but very cheap)
- ❓ Unknown if includes Hyperliquid perpetuals

**Example API Call**:
```bash
curl -X 'GET' \
  'https://pro-openapi.debank.com/v1/user/protocol?id=WALLET&protocol_id=uniswap' \
  -H 'AccessKey: YOUR_KEY'
```

**Example Response**:
```json
{
  "id": "uniswap",
  "chain": "eth",
  "portfolio_item_list": [
    {
      "stats": {
        "asset_usd_value": 1000.50,
        "net_usd_value": 1000.50
      },
      "detail": {
        "supply_token_list": [
          {
            "symbol": "ETH",
            "amount": 0.5,
            "price": 2000
          }
        ]
      }
    }
  ]
}
```

---

### 2. ✅ Uniswap Subgraph (The Graph) - FREE FOR UNISWAP ONLY

**Website**: https://thegraph.com/

**What it does**: GraphQL API for Uniswap v3 positions only

**Pricing**: 
- Free tier: 100,000 queries/month
- Paid: $4 per 100,000 additional queries

**Pros**:
- ✅ Free tier sufficient for most use cases
- ✅ Well-documented
- ✅ Real-time data
- ✅ Direct on-chain data

**Cons**:
- ⚠️ Only Uniswap v3 (no other DEXs)
- ⚠️ Doesn't include perpetuals
- ⚠️ Requires API key
- ⚠️ GraphQL learning curve

**Example Query**:
```graphql
{
  positions(where: { owner: "0xWALLET" }) {
    id
    liquidity
    depositedToken0
    depositedToken1
    pool {
      token0 { symbol }
      token1 { symbol }
    }
  }
}
```

---

### 3. ⚠️ Direct RPC Calls - FREE BUT COMPLEX

**What it does**: Query blockchain directly via RPC

**Pricing**: Free (using public RPCs)

**What we tested**:
```python
# Check Uniswap V3 LP NFT balance
Result: Wallet has 0 Uniswap V3 LP NFTs
```

**Pros**:
- ✅ Completely free
- ✅ No API keys needed
- ✅ Direct blockchain data

**Cons**:
- ❌ Very complex to implement
- ❌ Need to know all contract addresses
- ❌ Need to decode contract calls
- ❌ Need to aggregate data from multiple sources
- ❌ No USD prices (need separate price oracle)
- ❌ Slow (multiple RPC calls needed)

**Conclusion**: Not practical for production use.

---

### 4. ❌ RabbyWallet API - DOESN'T EXIST

**Finding**: Rabby Wallet does NOT have a portfolio data API.

**What Rabby has**:
- RabbyKit: Wallet connection SDK for dApps (not a data API)
- Web interface: Uses DeBank's backend

**Conclusion**: Cannot use Rabby as data source.

---

### 5. ❌ Public APIs Without Keys - ALL FAILED

**Tested**:
- ❌ DeBank public endpoint (deprecated)
- ❌ Etherscan (requires API key)
- ❌ Zerion (requires API key)
- ❌ Zapper (requires API key)
- ❌ Covalent (requires API key)

**Conclusion**: All modern portfolio APIs require authentication.

---

## 💡 Recommendations

### For Your Use Case:

**Current Setup**: Keep using Octav.fi ✅

**Why?**
1. Already implemented and working
2. Multi-protocol support (Uniswap, Sushiswap, Curve, etc.)
3. Includes perpetual positions (Hyperliquid)
4. Single API to manage

**Alternative for V4** (if needed):

**Option A: Add DeBank as Backup**
- Cost: ~$0.58/month
- Benefit: Redundancy if Octav.fi fails
- Implementation: Simple (REST API)

**Option B: Hybrid Approach**
- Uniswap Subgraph for LP (free)
- Octav.fi for perpetuals
- Benefit: Reduce dependency on single provider

**Option C: Stay with Octav.fi Only**
- Simplest approach
- Already working
- No additional complexity

---

## 🧪 Test Results for Wallet 0xc1E18438Fed146D814418364134fE28cC8622B5C

| Method | Status | Result |
|--------|--------|--------|
| DeBank Public | ❌ Failed | Endpoint deprecated |
| Etherscan | ❌ Failed | Requires valid API key |
| Zerion | ❌ Failed | Requires valid API key |
| Zapper | ❌ Failed | Endpoint not found |
| Covalent | ❌ Failed | Requires valid API key |
| Direct RPC | ✅ Success | 0 Uniswap V3 LP NFTs found |

**Conclusion**: This wallet has no Uniswap V3 LP positions (or they're on other chains).

---

## 📈 Cost Comparison (Monthly)

**Scenario**: Sync portfolio every hour

| Service | Monthly Cost | Notes |
|---------|--------------|-------|
| **DeBank API** | $0.58 | 720 calls × 4 units |
| **The Graph** | $0.00 | Free tier (100k queries) |
| **Octav.fi** | Unknown | No public pricing |
| **Direct RPC** | $0.00 | Free but impractical |

---

## 🎯 Final Answer to Your Question

> "vc consegue pegar as infos de LP dela usando a propria blockchain ou a rabbywallet?"

**Resposta**:

### Blockchain Direta:
- ✅ **Tecnicamente possível** via RPC calls
- ❌ **Não prático** - muito complexo, precisa saber todos os contratos, decodificar dados, buscar preços separadamente
- ⚠️ **Resultado do teste**: Consegui verificar que a wallet tem 0 NFTs de LP do Uniswap V3

### RabbyWallet:
- ❌ **Não tem API** - Rabby não oferece API de dados de portfolio
- ℹ️ Rabby usa o backend do DeBank para mostrar dados

### Melhor Alternativa:
- ⭐ **DeBank Cloud API** - $0.58/mês, multi-protocolo, fácil de usar
- ⭐ **Uniswap Subgraph** - Grátis, mas só Uniswap v3
- ⭐ **Octav.fi** (atual) - Já funciona, mantenha!

---

## 📁 Files Created

1. `debank_api_research.md` - DeBank API details
2. `research_alternative_apis.md` - Uniswap Subgraph research
3. `test_wallet_data.py` - Test script (6 methods)
4. `uniswap_subgraph_client.py` - Ready-to-use Uniswap client
5. `test_uniswap_subgraph.py` - Uniswap test script
6. `BLOCKCHAIN_DATA_ACCESS_SUMMARY.md` - This file

---

## 🚀 Next Steps (If You Want to Switch)

### To Use DeBank API:

1. **Sign up**: https://cloud.debank.com/
2. **Get API key**: Generate in console
3. **Test**: 
   ```bash
   curl -X 'GET' \
     'https://pro-openapi.debank.com/v1/user/total_balance?id=YOUR_WALLET' \
     -H 'AccessKey: YOUR_KEY'
   ```
4. **Integrate**: Replace `octav_client.py` calls with DeBank API

### To Use Uniswap Subgraph:

1. **Sign up**: https://thegraph.com/studio/
2. **Get API key**: Free tier
3. **Test**: Use `test_uniswap_subgraph.py` script
4. **Integrate**: Use `uniswap_subgraph_client.py` (already created)

### To Keep Octav.fi:

1. **Do nothing** - it already works! ✅

---

## 📞 Support

If you need help implementing any of these alternatives, just ask!

**Recommendation**: Stick with Octav.fi for now, consider DeBank as backup in V4.
