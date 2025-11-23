# Hyperliquid Balance Investigation

## Problem

User reports that the system is showing **position value** instead of **total balance** for Hyperliquid.

**Current behavior:**
- Showing: $7,166.36 (53.3%) - This appears to be the value of open positions
- Need: Total balance (free balance + margin used)

## API Response Structure

From Octav.fi API docs:

```json
{
  "address": "<string>",
  "networth": "<string>",
  "cashBalance": "<string>",
  "assetByProtocols": {},
  "chains": {}
}
```

## Current Implementation

File: `extract_protocol_balances.py`

```python
def _calculate_protocol_value(protocol_data: Dict) -> float:
    # Currently sums:
    # - supplyAssets (LP deposits)
    # - rewardAssets (rewards)
    # - dexAssets (perpetual positions) ← PROBLEM HERE
    # - borrowAssets (debt)
```

For Hyperliquid, we're summing `dexAssets` which contains:
- Open position values (e.g., short BTC worth $7,166)

But we need:
- **Total account balance** (cash + margin)

## Hypothesis

Hyperliquid data in Octav.fi likely has:
1. `dexAssets` - Open positions (what we're currently using)
2. `supplyAssets` or similar - Account balance/margin

## Next Steps

1. ✅ Get actual portfolio response from user's wallet
2. Inspect the Hyperliquid section structure
3. Find where the total balance is stored
4. Update extraction logic

## Possible Solutions

### Option 1: Use supplyAssets for Hyperliquid
If Hyperliquid stores balance in `supplyAssets`:
```python
if protocol_key == "hyperliquid":
    # Use supplyAssets instead of dexAssets
    for asset in supply_assets:
        total_value += float(asset.get("value", 0))
```

### Option 2: Look for specific balance field
If there's a dedicated balance field:
```python
if protocol_key == "hyperliquid":
    # Look for balance field
    balance = protocol_data.get("balance", 0)
    total_value += float(balance)
```

### Option 3: Sum both balance and positions
If we need both:
```python
if protocol_key == "hyperliquid":
    # Balance (supplyAssets)
    for asset in supply_assets:
        total_value += float(asset.get("value", 0))
    
    # Don't include dexAssets (positions) for allocation
    # Those are hedges, not capital allocation
```

## Questions for User

1. What does "total balance" mean in your context?
   - Free cash + margin used?
   - Just free cash?
   - Account equity?

2. Should we include position value at all?
   - Or just the collateral/margin?

## Testing Plan

1. Get sample portfolio response
2. Print out Hyperliquid section structure
3. Identify correct field
4. Update extraction logic
5. Verify with user
