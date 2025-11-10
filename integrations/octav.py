"""
Octav.fi API Integration
Fetches LP positions from multiple networks using Octav.fi API
"""

import requests
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class OctavClient:
    """Client for Octav.fi API"""
    
    def __init__(self, api_key: str):
        """
        Initialize Octav client
        
        Args:
            api_key: Octav.fi API key (JWT token)
        """
        self.api_key = api_key
        self.base_url = "https://data.octav.fi/api"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def get_positions(self, wallet_address: str) -> List[Dict]:
        """
        Get all LP positions for a wallet across all networks
        
        Args:
            wallet_address: Ethereum address
            
        Returns:
            List of position dictionaries with standardized format
        """
        try:
            # Octav.fi endpoint for positions
            # Note: This is a placeholder - need to check actual API docs
            url = f"{self.base_url}/positions"
            
            params = {
                "address": wallet_address.lower()
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Parse and standardize the response
            positions = self._parse_positions(data)
            
            logger.info(f"Found {len(positions)} positions via Octav.fi for {wallet_address}")
            return positions
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching positions from Octav.fi: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in Octav.fi integration: {e}")
            return []
    
    def _parse_positions(self, data: Dict) -> List[Dict]:
        """
        Parse Octav.fi API response into standardized format
        
        Args:
            data: Raw API response
            
        Returns:
            List of standardized position dictionaries
        """
        positions = []
        
        # This is a placeholder - actual parsing depends on Octav.fi API structure
        # We'll need to adjust based on the real API response format
        
        if isinstance(data, dict) and "positions" in data:
            for pos in data.get("positions", []):
                try:
                    # Extract relevant fields
                    position = {
                        "id": pos.get("id", ""),
                        "protocol": pos.get("protocol", "Unknown"),
                        "network": pos.get("network", pos.get("chain", "Unknown")),
                        "pool_address": pos.get("pool_address", ""),
                        "token0_symbol": pos.get("token0", {}).get("symbol", ""),
                        "token1_symbol": pos.get("token1", {}).get("symbol", ""),
                        "token0_amount": float(pos.get("token0", {}).get("amount", 0)),
                        "token1_amount": float(pos.get("token1", {}).get("amount", 0)),
                        "liquidity": float(pos.get("liquidity", 0)),
                        "value_usd": float(pos.get("value_usd", 0)),
                        "fee_tier": pos.get("fee_tier", ""),
                        "in_range": pos.get("in_range", True),
                        "uncollected_fees_usd": float(pos.get("uncollected_fees_usd", 0))
                    }
                    positions.append(position)
                except (KeyError, ValueError, TypeError) as e:
                    logger.warning(f"Error parsing position: {e}")
                    continue
        
        return positions
    
    def get_portfolio_summary(self, wallet_address: str) -> Optional[Dict]:
        """
        Get portfolio summary for a wallet
        
        Args:
            wallet_address: Ethereum address
            
        Returns:
            Portfolio summary dictionary or None
        """
        try:
            url = f"{self.base_url}/portfolio"
            
            params = {
                "address": wallet_address.lower()
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            summary = {
                "total_value_usd": data.get("net_worth", 0),
                "protocols_count": len(data.get("protocols", [])),
                "networks": data.get("networks", [])
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error fetching portfolio summary: {e}")
            return None
