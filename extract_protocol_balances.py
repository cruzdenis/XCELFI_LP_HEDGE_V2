"""
Helper functions to extract protocol balances from Octav.fi portfolio data
SIMPLIFIED VERSION - Uses top-level value field from API response
"""

from typing import Dict

def extract_protocol_balances(portfolio_data: Dict) -> Dict[str, float]:
    """
    Extract USD value by protocol from portfolio data.
    
    Uses the top-level 'value' field from each protocol in assetByProtocols,
    which already contains the correct total (equity for Hyperliquid, 
    total value for other protocols).
    
    Args:
        portfolio_data: Portfolio data from Octav.fi API
        
    Returns:
        Dict mapping protocol names to USD values
        Example: {
            "Wallet": 1000.0,
            "Uniswap V3": 5000.0,
            "Revert Finance": 3000.0,
            "Hyperliquid": 2458.78  # ← Now shows equity, not position value!
        }
    """
    protocol_balances = {}
    
    if not portfolio_data:
        return protocol_balances
    
    # Extract protocol balances from assetByProtocols
    # Each protocol has a top-level "value" field that contains the total
    assets_by_protocol = portfolio_data.get("assetByProtocols", {})
    
    for protocol_key, protocol_data in assets_by_protocol.items():
        # Skip wallet - we handle it separately
        if protocol_key.lower() == "wallet":
            wallet_value = float(protocol_data.get("value", 0))
            if wallet_value > 0:
                protocol_balances["Wallet"] = wallet_value
            continue
        
        # Get protocol name
        protocol_name = _format_protocol_name(protocol_key)
        
        # Get value directly from top-level field
        # For Hyperliquid: this is equity (free balance + positions + PnL + funding)
        # For other protocols: this is total value
        protocol_value = float(protocol_data.get("value", 0))
        
        if protocol_value > 0:
            protocol_balances[protocol_name] = protocol_value
    
    return protocol_balances

def _format_protocol_name(protocol_key: str) -> str:
    """Format protocol key to human-readable name"""
    protocol_names = {
        "revert": "Revert Finance",
        "hyperliquid": "Hyperliquid",
        "uniswap": "Uniswap V3",
        "uniswap_v3": "Uniswap V3",
        "curve": "Curve",
        "sushiswap": "SushiSwap",
        "aave": "Aave",
        "compound": "Compound",
        "balancer": "Balancer",
        "pancakeswap": "PancakeSwap",
        "wallet": "Wallet"
    }
    
    return protocol_names.get(protocol_key.lower(), protocol_key.title())

def get_wallet_balance(portfolio_data: Dict) -> float:
    """
    Extract wallet balance (idle capital) from portfolio data.
    
    Args:
        portfolio_data: Portfolio data from Octav.fi API
        
    Returns:
        USD value of wallet balance
    """
    if not portfolio_data:
        return 0.0
    
    # Wallet balance is in assetByProtocols.wallet.value
    assets_by_protocol = portfolio_data.get("assetByProtocols", {})
    wallet_data = assets_by_protocol.get("wallet", {})
    
    return float(wallet_data.get("value", 0))

# Example usage and testing
if __name__ == "__main__":
    # Example portfolio data structure (simplified)
    example_portfolio = {
        "networth": "8757.29",
        "assetByProtocols": {
            "wallet": {
                "name": "Wallet",
                "key": "wallet",
                "value": "6.37"  # ← Idle capital
            },
            "revert": {
                "name": "Revert Finance",
                "key": "revert",
                "value": "6276.08"  # ← Total LP value
            },
            "hyperliquid": {
                "name": "Hyperliquid",
                "key": "hyperliquid",
                "value": "2458.78"  # ← Equity (NOT position value!)
            }
        }
    }
    
    balances = extract_protocol_balances(example_portfolio)
    print("Protocol Balances:")
    for protocol, value in balances.items():
        print(f"  {protocol}: ${value:,.2f}")
    
    print(f"\nTotal: ${sum(balances.values()):,.2f}")
    
    wallet = get_wallet_balance(example_portfolio)
    print(f"Wallet Balance: ${wallet:,.2f}")
    
    # Verify
    expected_total = 6.37 + 6276.08 + 2458.78
    actual_total = sum(balances.values())
    print(f"\nExpected: ${expected_total:,.2f}")
    print(f"Actual: ${actual_total:,.2f}")
    print(f"Match: {abs(expected_total - actual_total) < 0.01}")
