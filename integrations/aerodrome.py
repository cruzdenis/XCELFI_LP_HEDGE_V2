"""
Aerodrome Finance integration module.
Handles reading LP positions and executing transactions on Base L2.
"""
import requests
from typing import Optional, Dict, Tuple
from web3 import Web3
from eth_account import Account
from dataclasses import dataclass


@dataclass
class LPPosition:
    """LP position data."""
    token_id: Optional[int]
    liquidity: float
    token0_amount: float
    token1_amount: float
    tick_lower: int
    tick_upper: int
    unclaimed_fees0: float
    unclaimed_fees1: float
    token0_symbol: str
    token1_symbol: str


@dataclass
class PoolInfo:
    """Pool information."""
    address: str
    token0: str
    token1: str
    fee: int
    tick: int
    sqrt_price_x96: int
    liquidity: float
    token0_symbol: str
    token1_symbol: str


class AerodromeClient:
    """
    Client for interacting with Aerodrome Finance.
    
    Supports both read-only (public) and execution (private key) modes.
    """
    
    def __init__(
        self,
        rpc_url: str,
        subgraph_url: str,
        router_address: str,
        pool_address: str,
        wallet_address: str,
        private_key: Optional[str] = None
    ):
        """
        Initialize Aerodrome client.
        
        Args:
            rpc_url: Base L2 RPC URL
            subgraph_url: Aerodrome subgraph URL
            router_address: Aerodrome router contract address
            pool_address: ETH/BTC pool address
            wallet_address: User wallet address
            private_key: Optional private key for execution mode
        """
        self.rpc_url = rpc_url
        self.subgraph_url = subgraph_url
        self.router_address = router_address
        self.pool_address = pool_address
        self.wallet_address = wallet_address
        self.private_key = private_key
        
        # Initialize Web3
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        # Check if in execution mode
        self.is_execution_mode = bool(private_key)
        
        if self.is_execution_mode:
            self.account = Account.from_key(private_key)
    
    def is_healthy(self) -> bool:
        """
        Check if Aerodrome API is healthy.
        
        Returns:
            True if API is responding, False otherwise
        """
        try:
            # Check RPC
            if not self.w3.is_connected():
                return False
            
            # Check subgraph
            if self.subgraph_url:
                response = requests.post(
                    self.subgraph_url,
                    json={"query": "{ _meta { block { number } } }"},
                    timeout=5
                )
                if response.status_code != 200:
                    return False
            
            return True
        except Exception:
            return False
    
    def get_pool_info(self) -> Optional[PoolInfo]:
        """
        Get pool information.
        
        Returns:
            PoolInfo or None if error
        """
        try:
            # TODO: Implement real pool contract query
            # For now, return None to indicate no real data available
            print("[INFO] Pool info not implemented - returning None")
            return None
        except Exception as e:
            print(f"Error getting pool info: {e}")
            return None
    
    def get_lp_position(self) -> Optional[LPPosition]:
        """
        Get LP position for wallet (read-only).
        
        Returns:
            LPPosition or None if no position or error
        """
        try:
            # TODO: Implement real position query via subgraph and contracts
            # For now, return None to indicate no real data available
            print(f"[INFO] LP position query not implemented for wallet {self.wallet_address} - returning None")
            return None
        except Exception as e:
            print(f"Error getting LP position: {e}")
            return None
    
    def get_balances(self) -> Dict[str, float]:
        """
        Get token balances for wallet (read-only).
        
        Returns:
            Dictionary of token symbol -> balance
        """
        try:
            # TODO: Implement real balance query via token contracts
            # For now, return empty dict to indicate no real data available
            print(f"[INFO] Balance query not implemented for wallet {self.wallet_address} - returning empty")
            return {}
        except Exception as e:
            print(f"Error getting balances: {e}")
            return {}
    
    def calculate_new_range(
        self,
        current_price: float,
        range_pct: float = 0.30
    ) -> Tuple[int, int]:
        """
        Calculate new tick range centered on current price.
        
        Args:
            current_price: Current price (token1/token0)
            range_pct: Range width as percentage (e.g., 0.30 = ±15%)
            
        Returns:
            Tuple of (tick_lower, tick_upper)
        """
        # In a real implementation, this would convert price to ticks
        # using the Uniswap V3 tick math
        
        # Mock calculation
        half_range = range_pct / 2
        tick_lower = -int(half_range * 100000)
        tick_upper = int(half_range * 100000)
        
        return (tick_lower, tick_upper)
    
    def estimate_swap(
        self,
        token_in: str,
        token_out: str,
        amount_in: float
    ) -> Dict:
        """
        Estimate swap output (read-only).
        
        Args:
            token_in: Input token symbol
            token_out: Output token symbol
            amount_in: Input amount
            
        Returns:
            Dictionary with amount_out and price_impact
        """
        try:
            # In a real implementation, this would use quoter contract
            # For now, return mock data
            
            # Mock: assume 1 ETH = 20 BTC and 0.1% price impact
            if token_in == "ETH" and token_out == "BTC":
                amount_out = amount_in / 20
            elif token_in == "BTC" and token_out == "ETH":
                amount_out = amount_in * 20
            else:
                amount_out = amount_in
            
            return {
                "amount_out": amount_out,
                "price_impact_bps": 10  # 0.1%
            }
        except Exception as e:
            print(f"Error estimating swap: {e}")
            return {"amount_out": 0.0, "price_impact_bps": 0}
    
    # Execution functions (require private key)
    
    def remove_liquidity(
        self,
        token_id: int,
        liquidity: float,
        amount0_min: float,
        amount1_min: float
    ) -> Optional[str]:
        """
        Remove liquidity from position (execution mode only).
        
        Args:
            token_id: NFT token ID
            liquidity: Amount of liquidity to remove
            amount0_min: Minimum amount of token0 to receive
            amount1_min: Minimum amount of token1 to receive
            
        Returns:
            Transaction hash or None if error
        """
        if not self.is_execution_mode:
            raise Exception("Execution mode not enabled - private key required")
        
        try:
            # In a real implementation, this would:
            # 1. Build transaction to NonfungiblePositionManager.decreaseLiquidity
            # 2. Sign with private key
            # 3. Send transaction
            # 4. Return tx hash
            
            print(f"[MOCK] Removing liquidity: token_id={token_id}, liquidity={liquidity}")
            return "0xmock_tx_hash_remove_liquidity"
        except Exception as e:
            print(f"Error removing liquidity: {e}")
            return None
    
    def add_liquidity(
        self,
        tick_lower: int,
        tick_upper: int,
        amount0_desired: float,
        amount1_desired: float,
        amount0_min: float,
        amount1_min: float
    ) -> Optional[str]:
        """
        Add liquidity to new position (execution mode only).
        
        Args:
            tick_lower: Lower tick
            tick_upper: Upper tick
            amount0_desired: Desired amount of token0
            amount1_desired: Desired amount of token1
            amount0_min: Minimum amount of token0
            amount1_min: Minimum amount of token1
            
        Returns:
            Transaction hash or None if error
        """
        if not self.is_execution_mode:
            raise Exception("Execution mode not enabled - private key required")
        
        try:
            # In a real implementation, this would:
            # 1. Build transaction to NonfungiblePositionManager.mint
            # 2. Sign with private key
            # 3. Send transaction
            # 4. Return tx hash
            
            print(f"[MOCK] Adding liquidity: ticks=[{tick_lower}, {tick_upper}], amounts=[{amount0_desired}, {amount1_desired}]")
            return "0xmock_tx_hash_add_liquidity"
        except Exception as e:
            print(f"Error adding liquidity: {e}")
            return None
    
    def swap(
        self,
        token_in: str,
        token_out: str,
        amount_in: float,
        amount_out_min: float
    ) -> Optional[str]:
        """
        Execute swap (execution mode only).
        
        Args:
            token_in: Input token symbol
            token_out: Output token symbol
            amount_in: Input amount
            amount_out_min: Minimum output amount
            
        Returns:
            Transaction hash or None if error
        """
        if not self.is_execution_mode:
            raise Exception("Execution mode not enabled - private key required")
        
        try:
            # In a real implementation, this would:
            # 1. Build transaction to Router.exactInputSingle
            # 2. Sign with private key
            # 3. Send transaction
            # 4. Return tx hash
            
            print(f"[MOCK] Swapping: {amount_in} {token_in} -> {token_out} (min: {amount_out_min})")
            return "0xmock_tx_hash_swap"
        except Exception as e:
            print(f"Error executing swap: {e}")
            return None
