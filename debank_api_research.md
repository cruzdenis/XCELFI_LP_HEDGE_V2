# DeBank API Research - Direct Blockchain Access

**Date**: 23 de Novembro de 2025  
**Goal**: Check if we can fetch LP data directly from blockchain using DeBank API

---

## 🎯 Key Finding: DeBank Cloud API is Available!

DeBank has a **public API** called "DeBank Cloud" that provides portfolio data.

**Website**: https://cloud.debank.com/  
**Docs**: https://docs.cloud.debank.com/

---

## 📊 Relevant Endpoints

### 1. Get User Protocol Positions
**Endpoint**: `GET /v1/user/protocol`

**Parameters**:
- `id`: User wallet address (required)
- `protocol_id`: Protocol ID like `uniswap`, `curve`, `bsc_pancakeswap` (required)

**Returns**: User's positions in a specific protocol including:
- LP positions
- Farming positions
- Token balances
- Rewards

**Example**:
```bash
curl -X 'GET' \
  'https://pro-openapi.debank.com/v1/user/protocol?id=0x5853ed4f26a3fcea565b3fbc698bb19cdf6deb85&protocol_id=bsc_bdollar' \
  -H 'accept: application/json' \
  -H 'AccessKey: YOUR_ACCESSKEY'
```

### 2. Get User Complex Protocol List
**Endpoint**: `GET /v1/user/complex_protocol_list`

**Parameters**:
- `id`: User wallet address (required)

**Returns**: All protocols where user has positions

### 3. Get User All Token List
**Endpoint**: `GET /v1/user/all_token_list`

**Parameters**:
- `id`: User wallet address (required)

**Returns**: All tokens held by user across all chains

### 4. Get User Total Balance
**Endpoint**: `GET /v1/user/total_balance`

**Parameters**:
- `id`: User wallet address (required)

**Returns**: Total portfolio value in USD

---

## 🔑 API Key Required

**Important**: DeBank API requires an **AccessKey** (API key).

**How to get**:
1. Go to https://cloud.debank.com/
2. Sign up for an account
3. Generate an API key

**Pricing**: Not clear from docs (need to check website)

---

## 🧪 Test with Target Wallet

Wallet: `0xc1E18438Fed146D814418364134fE28cC8622B5C`

Let me test if I can access this wallet's data...

---

## 📝 Response Format Example

From the docs, a protocol position response looks like:

```json
{
  "id": "bsc_bdollar",
  "chain": "bsc",
  "name": "bDollar",
  "portfolio_item_list": [
    {
      "stats": {
        "asset_usd_value": 6.914216886417625,
        "debt_usd_value": 0,
        "net_usd_value": 6.914216886417625
      },
      "name": "Farming",
      "detail": {
        "supply_token_list": [
          {
            "id": "0x190b589cf9fb8ddeabbfeae36a813ffb2a702454",
            "chain": "bsc",
            "name": "bDollar",
            "symbol": "BDO",
            "decimals": 18,
            "amount": 438.1464937799965,
            "price": 0
          }
        ],
        "reward_token_list": [...]
      }
    }
  ]
}
```

This includes:
- Token symbols
- Token amounts
- USD values
- LP positions
- Rewards

---

## 🤔 Comparison: DeBank vs Octav.fi

| Feature | DeBank API | Octav.fi |
|---------|------------|----------|
| **Coverage** | Multi-protocol | Multi-protocol |
| **API Key** | Required | Required |
| **Documentation** | Excellent | Unknown |
| **Pricing** | Unknown | Unknown |
| **Data Format** | JSON (well-structured) | Unknown |
| **LP Positions** | ✅ Yes | ✅ Yes |
| **Perpetuals** | ❓ Unknown | ✅ Yes (Hyperliquid) |
| **Real-time** | Near real-time (1 min) | Unknown |

---

## 🔍 Next Steps

1. **Get DeBank API Key** - Sign up at https://cloud.debank.com/
2. **Test with wallet** - Try fetching data for `0xc1E18438Fed146D814418364134fE28cC8622B5C`
3. **Check pricing** - See if it's free or paid
4. **Compare with Octav.fi** - See which has better data

---

## 💡 About RabbyWallet

**Finding**: Rabby Wallet does NOT have a portfolio API.

RabbyKit is just a wallet connection SDK for dApps, not a data API.

Rabby likely uses **DeBank's backend** for portfolio data (they're related projects).

---

## 🎯 Conclusion So Far

**Yes, you can get LP data directly!**

Options:
1. **DeBank API** - Public API, well-documented, requires API key
2. **Uniswap Subgraph** - Free, but only Uniswap v3
3. **Direct blockchain** - Possible but complex (need to query contracts directly)

**Best option**: DeBank API seems like a good alternative to Octav.fi.

**Need to test**: Get API key and test with your wallet to see actual data.


---

## 💰 DeBank API Pricing (Updated)

**Pricing Model**: Pay-per-use based on "Compute Units"

**Unit Price**: **$200 USD per 1 million units**

### API Costs (Units per Call)

| API Endpoint | Units per Call | Description |
|--------------|----------------|-------------|
| **Get user's portfolio details from any protocol** | 4 units | Get LP positions, farming, etc. |
| **Get a user's total balance** | 30 units | Total net worth across all chains |
| **Enhanced transaction pre-execution** | 50 units | Simulate transactions |

### Cost Calculation Example

**Scenario**: Sync portfolio every hour for 1 month

```
API: Get user's portfolio details = 4 units per call
Calls per month: 24 hours × 30 days = 720 calls
Total units: 720 × 4 = 2,880 units

Cost: 2,880 / 1,000,000 × $200 = $0.58 USD/month
```

**Conclusion**: Very affordable for our use case! Less than $1/month for hourly syncs.

---

## 🆚 Cost Comparison

| Service | Estimated Monthly Cost | Notes |
|---------|------------------------|-------|
| **DeBank API** | ~$0.58/month | 4 units × 720 calls |
| **The Graph (Uniswap)** | $0 (free tier) | 100k queries/month free |
| **Octav.fi** | Unknown | No public pricing |

---

## 📊 DeBank API Examples from Website

### Example 1: Get User's Total Balance
```json
{
  "total_usd_value": 27654.142997146177,
  "chain_list": [
    {
      "id": "eth",
      "community_id": 1,
      "name": "Ethereum",
      "usd_value": 11937.702345945296
    }
  ]
}
```

**Units cost**: 30 per call

### Example 2: Get User's Portfolio from Protocol
```json
{
  "id": "bsc_bdollar",
  "chain": "bsc",
  "name": "bDollar",
  "tvl": 223306.13569669172,
  "portfolio_item_list": [
    {
      "stats": {
        "asset_usd_value": 6.914216886417625,
        "debt_usd_value": 0,
        "net_usd_value": 6.914216886417625
      },
      "name": "Farming",
      "detail": {
        "supply_token_list": [...],
        "reward_token_list": [...]
      }
    }
  ]
}
```

**Units cost**: 4 per call

---

## ✅ Key Advantages of DeBank API

1. **Very Cheap**: ~$0.58/month for hourly syncs
2. **Multi-protocol**: Covers Uniswap, Curve, Sushiswap, etc.
3. **Well-documented**: Clear API reference
4. **Real-time**: Data updated within 1 minute
5. **Comprehensive**: Includes LP, farming, staking, lending
6. **USD values**: Automatically calculates USD values

---

## ⚠️ Potential Limitations

1. **Requires API key**: Need to sign up
2. **Paid service**: Not free (but very cheap)
3. **Perpetuals**: Unknown if includes Hyperliquid perpetual positions
4. **Rate limits**: Unknown (need to check after signup)

---

## 🎯 Updated Recommendation

**DeBank API is an excellent alternative to Octav.fi!**

**Why?**
- ✅ Super cheap (~$0.58/month)
- ✅ Multi-protocol support
- ✅ Well-documented
- ✅ Real-time data
- ✅ Includes USD values

**When to use?**
- If Octav.fi is expensive or unreliable
- If you want more control over data source
- If you need multi-protocol LP tracking

**Next step**: Test with your wallet to see actual data quality.
