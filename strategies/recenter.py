"""
Recenter strategy module.
Implements the logic for rebalancing LP position and shorts.
"""
from dataclasses import dataclass
from typing import Dict, Optional, Tuple
from integrations.aerodrome import AerodromeClient, LPPosition
from integrations.hyperliquid import HyperliquidClient


@dataclass
class RecenterPlan:
    """Plan for recentering operation."""
    # Current state
    current_lp_value: float
    current_short_btc: float
    current_short_eth: float
    current_price: float
    
    # New range
    new_tick_lower: int
    new_tick_upper: int
    new_range_lower_price: float
    new_range_upper_price: float
    
    # LP adjustments
    liquidity_to_remove: float
    eth_from_lp: float
    btc_from_lp: float
    
    # Swap needed
    swap_needed: bool
    swap_token_in: str
    swap_token_out: str
    swap_amount_in: float
    swap_amount_out: float
    swap_slippage_bps: int
    
    # New LP
    new_eth_amount: float
    new_btc_amount: float
    new_lp_value: float
    
    # Short adjustments
    target_short_btc: float
    target_short_eth: float
    short_btc_adjustment: float
    short_eth_adjustment: float
    
    # Costs
    estimated_gas_eth: float
    estimated_slippage_usd: float
    total_cost_usd: float


class RecenterStrategy:
    """
    Strategy for recentering LP position and rebalancing shorts.
    
    Implements the full recenter workflow:
    1. Remove LP
    2. Swap to target ratio
    3. Add LP in new range
    4. Adjust shorts
    """
    
    def __init__(
        self,
        aerodrome_client: AerodromeClient,
        hyperliquid_client: HyperliquidClient,
        config
    ):
        """
        Initialize recenter strategy.
        
        Args:
            aerodrome_client: Aerodrome client instance
            hyperliquid_client: Hyperliquid client instance
            config: Application configuration
        """
        self.aerodrome = aerodrome_client
        self.hyperliquid = hyperliquid_client
        self.config = config
    
    def calculate_recenter_plan(
        self,
        current_price: float,
        lp_position: LPPosition,
        aum: float
    ) -> RecenterPlan:
        """
        Calculate recenter plan without executing.
        
        Args:
            current_price: Current ETH/BTC price
            lp_position: Current LP position
            aum: Total AUM in USDC
            
        Returns:
            RecenterPlan with all details
        """
        # Calculate new range (±15% from current price)
        range_pct = self.config.range_total
        new_tick_lower, new_tick_upper = self.aerodrome.calculate_new_range(
            current_price,
            range_pct
        )
        
        # Calculate price bounds (mock calculation)
        half_range = range_pct / 2
        new_range_lower_price = current_price * (1 - half_range)
        new_range_upper_price = current_price * (1 + half_range)
        
        # Current LP value (mock)
        current_lp_value = aum * self.config.target_lp_pct
        
        # Amounts to remove from LP
        eth_from_lp = lp_position.token0_amount
        btc_from_lp = lp_position.token1_amount
        
        # Target amounts for new LP (74% of AUM)
        target_lp_value = aum * self.config.target_lp_pct
        
        # For a balanced LP at current price, we need:
        # eth_amount * eth_price = btc_amount * btc_price
        # Assume ETH price = 2500, BTC price = 45000
        eth_price = 2500.0
        btc_price = 45000.0
        
        # Split LP value 50/50 between ETH and BTC
        target_eth_value = target_lp_value * 0.5
        target_btc_value = target_lp_value * 0.5
        
        target_eth_amount = target_eth_value / eth_price
        target_btc_amount = target_btc_value / btc_price
        
        # Calculate swap needed
        eth_diff = eth_from_lp - target_eth_amount
        btc_diff = btc_from_lp - target_btc_amount
        
        swap_needed = False
        swap_token_in = ""
        swap_token_out = ""
        swap_amount_in = 0.0
        swap_amount_out = 0.0
        swap_slippage_bps = 0
        
        if abs(eth_diff) > 0.01:  # Significant difference
            swap_needed = True
            if eth_diff > 0:
                # Too much ETH, swap to BTC
                swap_token_in = "ETH"
                swap_token_out = "BTC"
                swap_amount_in = abs(eth_diff)
            else:
                # Too much BTC, swap to ETH
                swap_token_in = "BTC"
                swap_token_out = "ETH"
                swap_amount_in = abs(btc_diff)
            
            # Estimate swap
            swap_estimate = self.aerodrome.estimate_swap(
                swap_token_in,
                swap_token_out,
                swap_amount_in
            )
            swap_amount_out = swap_estimate["amount_out"]
            swap_slippage_bps = swap_estimate["price_impact_bps"]
        
        # Calculate target shorts (50% of LP exposure)
        target_short_btc = -target_btc_amount * btc_price * 0.5  # In USDC
        target_short_eth = -target_eth_amount * eth_price * 0.5  # In USDC
        
        # Get current shorts
        positions = self.hyperliquid.get_positions()
        current_short_btc = 0.0
        current_short_eth = 0.0
        
        for pos in positions:
            if "BTC" in pos.symbol:
                current_short_btc = pos.size * pos.mark_price
            elif "ETH" in pos.symbol:
                current_short_eth = pos.size * pos.mark_price
        
        # Calculate adjustments
        short_btc_adjustment = target_short_btc - current_short_btc
        short_eth_adjustment = target_short_eth - current_short_eth
        
        # Estimate costs
        estimated_gas_eth = 0.005  # Mock: 0.005 ETH for all operations
        estimated_slippage_usd = swap_amount_in * (swap_slippage_bps / 10000) * eth_price if swap_needed else 0.0
        total_cost_usd = estimated_gas_eth * eth_price + estimated_slippage_usd
        
        return RecenterPlan(
            current_lp_value=current_lp_value,
            current_short_btc=current_short_btc,
            current_short_eth=current_short_eth,
            current_price=current_price,
            new_tick_lower=new_tick_lower,
            new_tick_upper=new_tick_upper,
            new_range_lower_price=new_range_lower_price,
            new_range_upper_price=new_range_upper_price,
            liquidity_to_remove=lp_position.liquidity,
            eth_from_lp=eth_from_lp,
            btc_from_lp=btc_from_lp,
            swap_needed=swap_needed,
            swap_token_in=swap_token_in,
            swap_token_out=swap_token_out,
            swap_amount_in=swap_amount_in,
            swap_amount_out=swap_amount_out,
            swap_slippage_bps=swap_slippage_bps,
            new_eth_amount=target_eth_amount,
            new_btc_amount=target_btc_amount,
            new_lp_value=target_lp_value,
            target_short_btc=target_short_btc,
            target_short_eth=target_short_eth,
            short_btc_adjustment=short_btc_adjustment,
            short_eth_adjustment=short_eth_adjustment,
            estimated_gas_eth=estimated_gas_eth,
            estimated_slippage_usd=estimated_slippage_usd,
            total_cost_usd=total_cost_usd
        )
    
    def execute_recenter(
        self,
        plan: RecenterPlan,
        lp_position: LPPosition
    ) -> Dict[str, str]:
        """
        Execute recenter plan.
        
        Args:
            plan: RecenterPlan to execute
            lp_position: Current LP position
            
        Returns:
            Dictionary with transaction hashes
        """
        if not self.aerodrome.is_execution_mode:
            raise Exception("Execution mode not enabled - cannot execute recenter")
        
        results = {}
        
        # Step 1: Remove liquidity
        print("Step 1: Removing liquidity...")
        tx_remove = self.aerodrome.remove_liquidity(
            token_id=lp_position.token_id,
            liquidity=plan.liquidity_to_remove,
            amount0_min=plan.eth_from_lp * 0.99,  # 1% slippage tolerance
            amount1_min=plan.btc_from_lp * 0.99
        )
        results["remove_liquidity"] = tx_remove
        
        # Step 2: Swap if needed
        if plan.swap_needed:
            print(f"Step 2: Swapping {plan.swap_amount_in} {plan.swap_token_in} to {plan.swap_token_out}...")
            tx_swap = self.aerodrome.swap(
                token_in=plan.swap_token_in,
                token_out=plan.swap_token_out,
                amount_in=plan.swap_amount_in,
                amount_out_min=plan.swap_amount_out * 0.99
            )
            results["swap"] = tx_swap
        else:
            print("Step 2: No swap needed")
            results["swap"] = None
        
        # Step 3: Add liquidity in new range
        print("Step 3: Adding liquidity in new range...")
        tx_add = self.aerodrome.add_liquidity(
            tick_lower=plan.new_tick_lower,
            tick_upper=plan.new_tick_upper,
            amount0_desired=plan.new_eth_amount,
            amount1_desired=plan.new_btc_amount,
            amount0_min=plan.new_eth_amount * 0.99,
            amount1_min=plan.new_btc_amount * 0.99
        )
        results["add_liquidity"] = tx_add
        
        # Step 4: Adjust shorts
        if self.hyperliquid.is_execution_mode:
            if abs(plan.short_btc_adjustment) > 10:  # > $10 adjustment
                print(f"Step 4a: Adjusting BTC short by ${plan.short_btc_adjustment:.2f}...")
                tx_btc = self.hyperliquid.adjust_position(
                    symbol="BTC/USDC",
                    target_size=plan.target_short_btc / 45000  # Convert USDC to BTC
                )
                results["adjust_btc_short"] = tx_btc
            
            if abs(plan.short_eth_adjustment) > 10:  # > $10 adjustment
                print(f"Step 4b: Adjusting ETH short by ${plan.short_eth_adjustment:.2f}...")
                tx_eth = self.hyperliquid.adjust_position(
                    symbol="ETH/USDC",
                    target_size=plan.target_short_eth / 2500  # Convert USDC to ETH
                )
                results["adjust_eth_short"] = tx_eth
        else:
            print("Step 4: Skipping short adjustments (Hyperliquid not enabled)")
            results["adjust_btc_short"] = None
            results["adjust_eth_short"] = None
        
        print("Recenter complete!")
        return results
