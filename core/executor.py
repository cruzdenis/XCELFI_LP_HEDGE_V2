"""
Executor module for managing strategy execution.
Handles both manual and automatic execution modes.
"""
from typing import Dict, Optional
from datetime import datetime
from core.safety import SafetyChecker
from strategies.recenter import RecenterStrategy, RecenterPlan
from utils.logs import LogManager


class Executor:
    """
    Manages execution of rebalancing operations.
    
    Supports both MANUAL and AUTO modes with safety checks.
    """
    
    def __init__(
        self,
        recenter_strategy: RecenterStrategy,
        safety_checker: SafetyChecker,
        log_manager: LogManager,
        config
    ):
        """
        Initialize executor.
        
        Args:
            recenter_strategy: RecenterStrategy instance
            safety_checker: SafetyChecker instance
            log_manager: LogManager instance
            config: Application configuration
        """
        self.strategy = recenter_strategy
        self.safety = safety_checker
        self.logger = log_manager
        self.config = config
        
        self.last_execution_time: Optional[datetime] = None
    
    def can_execute_auto(
        self,
        eth_balance: float,
        usdc_cex_balance: float,
        aum: float,
        plan: RecenterPlan,
        aerodrome_healthy: bool,
        hyperliquid_healthy: bool,
        pool_liquidity_usd: float
    ) -> Dict:
        """
        Check if AUTO execution is allowed.
        
        Args:
            eth_balance: Current ETH balance
            usdc_cex_balance: Current USDC balance on CEX
            aum: Total AUM
            plan: RecenterPlan to execute
            aerodrome_healthy: Whether Aerodrome API is healthy
            hyperliquid_healthy: Whether Hyperliquid API is healthy
            pool_liquidity_usd: Pool liquidity in USD
            
        Returns:
            Dictionary with safety check results
        """
        # Run all safety checks
        safety_results = self.safety.run_all_checks(
            eth_balance=eth_balance,
            usdc_cex_balance=usdc_cex_balance,
            aum=aum,
            estimated_slippage_bps=plan.swap_slippage_bps,
            estimated_gas_eth=plan.estimated_gas_eth,
            aerodrome_healthy=aerodrome_healthy,
            hyperliquid_healthy=hyperliquid_healthy,
            pool_liquidity_usd=pool_liquidity_usd
        )
        
        return safety_results
    
    def execute_manual(
        self,
        plan: RecenterPlan,
        lp_position,
        operation_type: str = "full_recenter"
    ) -> Dict:
        """
        Execute operation manually (with user confirmation).
        
        Args:
            plan: RecenterPlan to execute
            lp_position: Current LP position
            operation_type: Type of operation ("full_recenter", "lp_only", "shorts_only")
            
        Returns:
            Dictionary with execution results
        """
        if not self.config.is_execution_mode:
            return {
                "success": False,
                "error": "Execution mode not enabled - private key required"
            }
        
        try:
            self.logger.log_execution_start(operation_type, "MANUAL")
            
            if operation_type == "full_recenter":
                results = self.strategy.execute_recenter(plan, lp_position)
            elif operation_type == "lp_only":
                # Execute only LP recenter (steps 1-3)
                results = self._execute_lp_only(plan, lp_position)
            elif operation_type == "shorts_only":
                # Execute only short adjustments (step 4)
                results = self._execute_shorts_only(plan)
            else:
                return {
                    "success": False,
                    "error": f"Unknown operation type: {operation_type}"
                }
            
            self.last_execution_time = datetime.now()
            self.logger.log_execution_complete(operation_type, "MANUAL", results)
            
            return {
                "success": True,
                "results": results,
                "timestamp": self.last_execution_time
            }
        
        except Exception as e:
            self.logger.log_execution_error(operation_type, "MANUAL", str(e))
            return {
                "success": False,
                "error": str(e)
            }
    
    def execute_auto(
        self,
        plan: RecenterPlan,
        lp_position,
        safety_results: Dict
    ) -> Dict:
        """
        Execute operation automatically (if safety checks pass).
        
        Args:
            plan: RecenterPlan to execute
            lp_position: Current LP position
            safety_results: Results from safety checks
            
        Returns:
            Dictionary with execution results
        """
        if not self.config.is_execution_mode:
            return {
                "success": False,
                "error": "Execution mode not enabled - private key required"
            }
        
        if not safety_results["auto_mode_allowed"]:
            errors = [r.message for r in safety_results["errors"]]
            return {
                "success": False,
                "error": "Safety checks failed",
                "failed_checks": errors
            }
        
        try:
            self.logger.log_execution_start("full_recenter", "AUTO")
            
            results = self.strategy.execute_recenter(plan, lp_position)
            
            self.last_execution_time = datetime.now()
            self.logger.log_execution_complete("full_recenter", "AUTO", results)
            
            return {
                "success": True,
                "results": results,
                "timestamp": self.last_execution_time
            }
        
        except Exception as e:
            self.logger.log_execution_error("full_recenter", "AUTO", str(e))
            return {
                "success": False,
                "error": str(e)
            }
    
    def _execute_lp_only(self, plan: RecenterPlan, lp_position) -> Dict[str, str]:
        """Execute only LP recenter (no short adjustments)."""
        results = {}
        
        # Remove liquidity
        tx_remove = self.strategy.aerodrome.remove_liquidity(
            token_id=lp_position.token_id,
            liquidity=plan.liquidity_to_remove,
            amount0_min=plan.eth_from_lp * 0.99,
            amount1_min=plan.btc_from_lp * 0.99
        )
        results["remove_liquidity"] = tx_remove
        
        # Swap if needed
        if plan.swap_needed:
            tx_swap = self.strategy.aerodrome.swap(
                token_in=plan.swap_token_in,
                token_out=plan.swap_token_out,
                amount_in=plan.swap_amount_in,
                amount_out_min=plan.swap_amount_out * 0.99
            )
            results["swap"] = tx_swap
        
        # Add liquidity
        tx_add = self.strategy.aerodrome.add_liquidity(
            tick_lower=plan.new_tick_lower,
            tick_upper=plan.new_tick_upper,
            amount0_desired=plan.new_eth_amount,
            amount1_desired=plan.new_btc_amount,
            amount0_min=plan.new_eth_amount * 0.99,
            amount1_min=plan.new_btc_amount * 0.99
        )
        results["add_liquidity"] = tx_add
        
        return results
    
    def _execute_shorts_only(self, plan: RecenterPlan) -> Dict[str, str]:
        """Execute only short adjustments (no LP changes)."""
        results = {}
        
        if not self.strategy.hyperliquid.is_execution_mode:
            return {"error": "Hyperliquid execution not enabled"}
        
        if abs(plan.short_btc_adjustment) > 10:
            tx_btc = self.strategy.hyperliquid.adjust_position(
                symbol="BTC/USDC",
                target_size=plan.target_short_btc / 45000
            )
            results["adjust_btc_short"] = tx_btc
        
        if abs(plan.short_eth_adjustment) > 10:
            tx_eth = self.strategy.hyperliquid.adjust_position(
                symbol="ETH/USDC",
                target_size=plan.target_short_eth / 2500
            )
            results["adjust_eth_short"] = tx_eth
        
        return results
