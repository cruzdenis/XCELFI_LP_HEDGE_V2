"""
Test Script: Fetch Wallet LP Data Without API Keys

This script attempts to fetch LP position data for a wallet using various methods:
1. Direct blockchain queries (via public RPC)
2. Public APIs (if available)
3. Web scraping (last resort)

Target wallet: 0xc1E18438Fed146D814418364134fE28cC8622B5C
"""

import requests
import json
from typing import Dict, List

WALLET_ADDRESS = "0xc1E18438Fed146D814418364134fE28cC8622B5C"

# ============================================================
# METHOD 1: Try DeBank Public API (no auth)
# ============================================================

def test_debank_public():
    """
    Test if DeBank has any public endpoints that don't require API key.
    """
    print("\n" + "="*60)
    print("🧪 TEST 1: DeBank Public API (No Auth)")
    print("="*60)
    
    # Try the old public endpoint (may be deprecated)
    url = f"https://api.debank.com/user/addr?addr={WALLET_ADDRESS}"
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Got data:")
            print(json.dumps(data, indent=2)[:500])
            return data
        else:
            print(f"❌ Failed: {response.text[:200]}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

# ============================================================
# METHOD 2: Try Etherscan API (free tier)
# ============================================================

def test_etherscan():
    """
    Test Etherscan API to get token balances.
    Note: Requires API key but has free tier.
    """
    print("\n" + "="*60)
    print("🧪 TEST 2: Etherscan API (Token Balances)")
    print("="*60)
    
    # Using demo API key (rate limited)
    url = f"https://api.etherscan.io/api?module=account&action=tokentx&address={WALLET_ADDRESS}&startblock=0&endblock=99999999&sort=asc&apikey=YourApiKeyToken"
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "1":
                print(f"✅ Success! Found {len(data.get('result', []))} transactions")
                print(f"Sample: {json.dumps(data['result'][:2], indent=2)[:500]}")
                return data
            else:
                print(f"⚠️ API returned: {data.get('message')}")
                return None
        else:
            print(f"❌ Failed: {response.text[:200]}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

# ============================================================
# METHOD 3: Try Zerion API (public)
# ============================================================

def test_zerion():
    """
    Test Zerion's public API endpoints.
    """
    print("\n" + "="*60)
    print("🧪 TEST 3: Zerion API")
    print("="*60)
    
    url = f"https://api.zerion.io/v1/wallets/{WALLET_ADDRESS}/positions/"
    
    headers = {
        "accept": "application/json",
        "authorization": "Basic emVyaW9uOmFwaS56ZXJpb24uaW8="  # Public demo key
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Got data:")
            print(json.dumps(data, indent=2)[:500])
            return data
        else:
            print(f"❌ Failed: {response.text[:200]}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

# ============================================================
# METHOD 4: Try Zapper API
# ============================================================

def test_zapper():
    """
    Test Zapper's API endpoints.
    """
    print("\n" + "="*60)
    print("🧪 TEST 4: Zapper API")
    print("="*60)
    
    url = f"https://api.zapper.fi/v2/balances?addresses[]={WALLET_ADDRESS}"
    
    headers = {
        "accept": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Got data:")
            print(json.dumps(data, indent=2)[:500])
            return data
        else:
            print(f"❌ Failed: {response.text[:200]}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

# ============================================================
# METHOD 5: Try Covalent API (has free tier)
# ============================================================

def test_covalent():
    """
    Test Covalent API (has generous free tier).
    """
    print("\n" + "="*60)
    print("🧪 TEST 5: Covalent API")
    print("="*60)
    
    # Ethereum mainnet chain ID = 1
    url = f"https://api.covalenthq.com/v1/1/address/{WALLET_ADDRESS}/balances_v2/"
    
    # Demo key (limited)
    params = {
        "key": "ckey_docs"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("data"):
                items = data["data"].get("items", [])
                print(f"✅ Success! Found {len(items)} tokens")
                print(f"Sample: {json.dumps(items[:2], indent=2)[:500]}")
                return data
            else:
                print(f"⚠️ No data: {data}")
                return None
        else:
            print(f"❌ Failed: {response.text[:200]}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

# ============================================================
# METHOD 6: Try direct RPC call to get NFT positions (Uniswap V3)
# ============================================================

def test_direct_rpc():
    """
    Try to query Uniswap V3 NFT positions directly via RPC.
    """
    print("\n" + "="*60)
    print("🧪 TEST 6: Direct RPC Call (Uniswap V3 Positions)")
    print("="*60)
    
    # Public Ethereum RPC
    rpc_url = "https://eth.llamarpc.com"
    
    # Uniswap V3 NonfungiblePositionManager contract
    contract_address = "0xC36442b4a4522E871399CD717aBDD847Ab11FE88"
    
    # Function: balanceOf(address)
    # Selector: 0x70a08231
    data = f"0x70a08231000000000000000000000000{WALLET_ADDRESS[2:].lower()}"
    
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_call",
        "params": [{
            "to": contract_address,
            "data": data
        }, "latest"],
        "id": 1
    }
    
    try:
        response = requests.post(rpc_url, json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if "result" in data:
                balance_hex = data["result"]
                balance = int(balance_hex, 16)
                print(f"✅ Success! Wallet has {balance} Uniswap V3 LP NFTs")
                return {"balance": balance}
            else:
                print(f"❌ No result: {data}")
                return None
        else:
            print(f"❌ Failed: {response.text[:200]}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

# ============================================================
# MAIN
# ============================================================

def main():
    print("="*60)
    print("🔍 WALLET LP DATA FETCHING TEST")
    print("="*60)
    print(f"\nTarget Wallet: {WALLET_ADDRESS}")
    print("\nTrying multiple methods to fetch LP position data...")
    
    results = []
    
    # Test all methods
    results.append(("DeBank Public", test_debank_public()))
    results.append(("Etherscan", test_etherscan()))
    results.append(("Zerion", test_zerion()))
    results.append(("Zapper", test_zapper()))
    results.append(("Covalent", test_covalent()))
    results.append(("Direct RPC", test_direct_rpc()))
    
    # Summary
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    
    for method, result in results:
        status = "✅ SUCCESS" if result else "❌ FAILED"
        print(f"{status} - {method}")
    
    successful = [m for m, r in results if r]
    
    if successful:
        print(f"\n🎉 {len(successful)} method(s) worked!")
        print(f"   Working methods: {', '.join(successful)}")
    else:
        print("\n⚠️ No methods worked without API keys.")
        print("\nRecommendations:")
        print("1. Get DeBank Cloud API key ($0.58/month)")
        print("2. Get The Graph API key (free tier)")
        print("3. Use Octav.fi (current solution)")

if __name__ == "__main__":
    main()
