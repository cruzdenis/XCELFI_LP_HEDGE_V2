#!/usr/bin/env python3
"""
Background Sync Job
Runs periodically to sync portfolio data from Octav.fi
"""

import sys
from datetime import datetime
from octav_client import OctavClient
from delta_neutral_analyzer import DeltaNeutralAnalyzer
from config_manager import ConfigManager

def main():
    """Main sync job function"""
    print(f"[{datetime.now().isoformat()}] Starting sync job...")
    
    # Initialize config manager
    config_mgr = ConfigManager()
    
    # Load configuration
    config = config_mgr.load_config()
    
    if not config:
        print("[ERROR] No configuration found. Please configure the app first.")
        sys.exit(1)
    
    # Check if auto-sync is enabled
    auto_sync_enabled = config.get("auto_sync_enabled", False)
    
    if not auto_sync_enabled:
        print("[INFO] Auto-sync is disabled. Skipping sync.")
        sys.exit(0)
    
    # Get config values
    api_key = config.get("api_key")
    wallet_address = config.get("wallet_address")
    tolerance_pct = config.get("tolerance_pct", 5.0)
    
    if not api_key or not wallet_address:
        print("[ERROR] Missing API key or wallet address in configuration.")
        sys.exit(1)
    
    print(f"[INFO] Syncing data for wallet: {wallet_address}")
    
    try:
        # Initialize Octav client
        client = OctavClient(api_key)
        
        # Fetch portfolio data
        print("[INFO] Fetching portfolio data from Octav.fi...")
        portfolio = client.get_portfolio(wallet_address)
        
        if not portfolio:
            print("[ERROR] Failed to fetch portfolio data.")
            sys.exit(1)
        
        # Extract positions
        lp_positions = client.extract_lp_positions(portfolio)
        perp_positions = client.extract_perp_positions(portfolio)
        
        print(f"[INFO] Found {len(lp_positions)} LP positions and {len(perp_positions)} perp positions")
        
        # Aggregate balances
        lp_balances = {}
        for pos in lp_positions:
            symbol = client.normalize_symbol(pos.token_symbol)
            lp_balances[symbol] = lp_balances.get(symbol, 0) + pos.balance
        
        short_balances = {}
        for pos in perp_positions:
            if pos.size < 0:
                symbol = client.normalize_symbol(pos.symbol)
                short_balances[symbol] = short_balances.get(symbol, 0) + abs(pos.size)
        
        # Perform delta-neutral analysis
        analyzer = DeltaNeutralAnalyzer(tolerance_pct=tolerance_pct)
        suggestions = analyzer.compare_positions(lp_balances, short_balances)
        
        # Calculate summary
        balanced = [s for s in suggestions if s.status == "balanced"]
        under_hedged = [s for s in suggestions if s.status == "under_hedged"]
        over_hedged = [s for s in suggestions if s.status == "over_hedged"]
        
        # Get networth
        networth = float(portfolio.get("networth", "0"))
        
        # Save to history
        summary = {
            "networth": networth,
            "balanced": len(balanced),
            "under_hedged": len(under_hedged),
            "over_hedged": len(over_hedged),
            "total_positions": len(suggestions)
        }
        
        config_mgr.add_sync_history(summary)
        
        print(f"[SUCCESS] Sync completed successfully!")
        print(f"[INFO] Net Worth: ${networth:,.2f}")
        print(f"[INFO] Balanced: {len(balanced)}, Under-hedged: {len(under_hedged)}, Over-hedged: {len(over_hedged)}")
        
        # Print actions needed
        if under_hedged or over_hedged:
            print("[INFO] Actions needed:")
            for s in under_hedged:
                print(f"  - INCREASE SHORT {s.token}: {s.adjustment_amount:.6f}")
            for s in over_hedged:
                print(f"  - DECREASE SHORT {s.token}: {s.adjustment_amount:.6f}")
        else:
            print("[INFO] All positions are balanced!")
        
        sys.exit(0)
        
    except Exception as e:
        print(f"[ERROR] Sync failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
