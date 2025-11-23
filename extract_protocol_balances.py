"""
Helper functions to extract protocol balances from Octav.fi portfolio data
"""

from typing import Dict

def extract_protocol_balances(portfolio_data: Dict) -> Dict[str, float]:
    """
    Extract USD value by protocol from portfolio data.
    
    Args:
        portfolio_data: Portfolio data from Octav.fi API
        
    Returns:
        Dict mapping protocol names to USD values
        Example: {
            "Wallet": 1000.0,
            "Uniswap V3": 5000.0,
            "Revert Finance": 3000.0,
            "Hyperliquid": 2000.0
        }
    """
    protocol_balances = {}
    
    if not portfolio_data:
        return protocol_balances
    
    # Extract wallet balance (idle capital)
    wallet_balance = float(portfolio_data.get("walletBalance", 0))
    if wallet_balance > 0:
        protocol_balances["Wallet"] = wallet_balance
    
    # Extract protocol balances from assetByProtocols
    assets_by_protocol = portfolio_data.get("assetByProtocols", {})
    
    for protocol_key, protocol_data in assets_by_protocol.items():
        protocol_name = _format_protocol_name(protocol_key)
        protocol_value = _calculate_protocol_value(protocol_data)
        
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
        "pancakeswap": "PancakeSwap"
    }
    
    return protocol_names.get(protocol_key.lower(), protocol_key.title())

def _calculate_protocol_value(protocol_data: Dict) -> float:
    """
    Calculate total USD value for a protocol.
    
    Traverses the protocol data structure and sums all asset values.
    """
    total_value = 0.0
    
    if not protocol_data:
        return total_value
    
    # Protocol data structure:
    # {
    #   "chains": {
    #     "ethereum": {
    #       "protocolPositions": {
    #         "POSITION_TYPE": {
    #           "protocolPositions": [
    #             {
    #               "supplyAssets": [...],
    #               "rewardAssets": [...],
    #               "dexAssets": [...]
    #             }
    #           ]
    #         }
    #       }
    #     }
    #   }
    # }
    
    chains = protocol_data.get("chains", {})
    
    for chain_key, chain_data in chains.items():
        protocol_positions = chain_data.get("protocolPositions", {})
        
        for position_type_key, position_type_data in protocol_positions.items():
            proto_positions = position_type_data.get("protocolPositions", [])
            
            for proto_pos in proto_positions:
                # Sum supply assets
                supply_assets = proto_pos.get("supplyAssets", [])
                for asset in supply_assets:
                    total_value += float(asset.get("value", 0))
                
                # Sum reward assets
                reward_assets = proto_pos.get("rewardAssets", [])
                for asset in reward_assets:
                    total_value += float(asset.get("value", 0))
                
                # Sum dex assets (for perpetuals)
                dex_assets = proto_pos.get("dexAssets", [])
                for asset in dex_assets:
                    # For perpetuals, use position value
                    value = float(asset.get("value", 0))
                    
                    # If value is 0, try to calculate from balance * price
                    if value == 0:
                        balance = float(asset.get("balance", 0))
                        price = float(asset.get("price", 0))
                        value = abs(balance * price)
                    
                    total_value += value
                
                # Sum borrow assets (debt) - subtract from value
                borrow_assets = proto_pos.get("borrowAssets", [])
                for asset in borrow_assets:
                    total_value -= float(asset.get("value", 0))
    
    return total_value

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
    
    return float(portfolio_data.get("walletBalance", 0))

# Example usage
if __name__ == "__main__":
    # Example portfolio data structure
    example_portfolio = {
        "walletBalance": 1000.0,
        "networth": 11000.0,
        "assetByProtocols": {
            "revert": {
                "chains": {
                    "ethereum": {
                        "protocolPositions": {
                            "LP": {
                                "protocolPositions": [
                                    {
                                        "supplyAssets": [
                                            {
                                                "symbol": "ETH",
                                                "balance": 1.5,
                                                "price": 2000.0,
                                                "value": 3000.0
                                            }
                                        ]
                                    }
                                ]
                            }
                        }
                    }
                }
            },
            "hyperliquid": {
                "chains": {
                    "arbitrum": {
                        "protocolPositions": {
                            "MARGIN": {
                                "protocolPositions": [
                                    {
                                        "dexAssets": [
                                            {
                                                "symbol": "BTC",
                                                "balance": -0.1,
                                                "price": 50000.0,
                                                "value": 5000.0
                                            }
                                        ]
                                    }
                                ]
                            }
                        }
                    }
                }
            }
        }
    }
    
    balances = extract_protocol_balances(example_portfolio)
    print("Protocol Balances:")
    for protocol, value in balances.items():
        print(f"  {protocol}: ${value:,.2f}")
    
    wallet = get_wallet_balance(example_portfolio)
    print(f"\nWallet Balance: ${wallet:,.2f}")
