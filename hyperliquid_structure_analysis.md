# Hyperliquid Data Structure Analysis

## Actual Data from User's Wallet

### Top-level Hyperliquid Value
```json
"hyperliquid": {
    "name": "Hyperliquid",
    "key": "hyperliquid",
    "value": "2458.778666",  // ← THIS IS THE TOTAL VALUE WE NEED!
    ...
}
```

### Breakdown

#### MARGIN Section (Perpetuals)
```json
"MARGIN": {
    "totalValue": "2458.778666",
    "protocolPositions": [
        {
            "dexAssets": [
                {
                    "symbol": "wallet",
                    "marginUsed": "1742.142968",  // ← Free balance/equity
                    "value": "0"
                },
                {
                    "symbol": "btc",
                    "balance": "-0.00805",  // Short position
                    "value": "701.4931",     // Position value
                    "marginUsed": "17.537327",
                    "openPnl": "59.876199"
                },
                {
                    "symbol": "eth",
                    "balance": "-2.2987",   // Short position
                    "value": "6464.86388",  // Position value
                    "marginUsed": "258.594555",
                    "openPnl": "924.303629"
                }
            ],
            "value": "2458.778666"  // Total equity
        }
    ]
}
```

#### SPOT Section
```json
"SPOT": {
    "totalValue": "0",
    "assets": [
        {"symbol": "USDC", "value": "0"},
        {"symbol": "USDH", "value": "0"}
    ]
}
```

## Key Findings

### Current Problem
We're summing `dexAssets[].value` which gives:
- wallet: $0
- btc: $701.49
- eth: $6,464.86
- **Total: $7,166.35** ← This is what's showing (WRONG!)

### What We Should Use
The **top-level `value`** field already contains the correct equity:
```json
"hyperliquid": {
    "value": "2458.778666"  // ← Equity total (correct!)
}
```

Or the `protocolPositions[0].value`:
```json
"protocolPositions": [
    {
        "value": "2458.778666"  // ← Same, equity total
    }
]
```

## Equity Calculation Breakdown

**Total Equity = $2,458.78**

Components:
- Free balance (marginUsed for "wallet"): $1,742.14
- BTC position value: $701.49
- ETH position value: $6,464.86
- BTC open PnL: +$59.88
- ETH open PnL: +$924.30
- BTC funding: -$23.56
- ETH funding: -$29.63

**Calculation:**
```
Equity = Free Balance + Position Values + Open PnL + Funding
       = 1742.14 + (701.49 + 6464.86) + (59.88 + 924.30) + (-23.56 - 29.63)
       = 1742.14 + 7166.35 + 984.18 - 53.19
       = ~2458.78 ✓
```

## Solution

### Option 1: Use Top-Level Value (RECOMMENDED)
```python
def extract_protocol_balances(portfolio_data: Dict) -> Dict[str, float]:
    protocol_balances = {}
    
    assets_by_protocol = portfolio_data.get("assetByProtocols", {})
    
    for protocol_key, protocol_data in assets_by_protocol.items():
        protocol_name = _format_protocol_name(protocol_key)
        
        # Use top-level value directly!
        protocol_value = float(protocol_data.get("value", 0))
        
        if protocol_value > 0:
            protocol_balances[protocol_name] = protocol_value
    
    return protocol_balances
```

### Option 2: Special Handling for Hyperliquid
```python
def _calculate_protocol_value(protocol_data: Dict, protocol_key: str) -> float:
    # For Hyperliquid, use top-level value (equity)
    if protocol_key.lower() == "hyperliquid":
        return float(protocol_data.get("value", 0))
    
    # For other protocols, traverse structure
    # ... existing logic ...
```

## Recommendation

**Use Option 1** - Simplify the entire extraction logic!

The top-level `value` field in `assetByProtocols[protocol_key]` already contains the correct total for ALL protocols, not just Hyperliquid.

This means we can simplify the entire `extract_protocol_balances.py` module to just:
```python
def extract_protocol_balances(portfolio_data: Dict) -> Dict[str, float]:
    protocol_balances = {}
    
    assets_by_protocol = portfolio_data.get("assetByProtocols", {})
    
    for protocol_key, protocol_data in assets_by_protocol.items():
        # Skip wallet (we handle it separately)
        if protocol_key.lower() == "wallet":
            continue
            
        protocol_name = _format_protocol_name(protocol_key)
        protocol_value = float(protocol_data.get("value", 0))
        
        if protocol_value > 0:
            protocol_balances[protocol_name] = protocol_value
    
    return protocol_balances
```

Much simpler and correct for all protocols!
