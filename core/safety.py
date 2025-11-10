"""
Safety checks module for execution validation.
Ensures all conditions are met before allowing AUTO execution.
"""
from dataclasses import dataclass
from typing import List, Dict
from datetime import datetime


@dataclass
class SafetyCheckResult:
    """Result of a safety check."""
    passed: bool
    check_name: str
    message: str
    severity: str  # "error", "warning", "info"


class SafetyChecker:
    """
    Performs safety checks before execution.
    
    All checks must pass for AUTO mode to be enabled.
    """
    
    def __init__(self, config):
        """
        Initialize safety checker.
        
        Args:
            config: Application configuration
        """
        self.config = config
    
    def check_reserves(
        self,
        eth_balance: float,
        usdc_cex_balance: float,
        aum: float
    ) -> List[SafetyCheckResult]:
        """
        Check if reserve buffers are adequate.
        
        Args:
            eth_balance: Current ETH balance on Base
            usdc_cex_balance: Current USDC balance on Hyperliquid
            aum: Total AUM in USDC
            
        Returns:
            List of safety check results
        """
        results = []
        
        # Check ETH gas reserve
        eth_min = self.config.eth_gas_min
        eth_target = self.config.eth_gas_target
        
        if eth_balance < eth_min:
            results.append(SafetyCheckResult(
                passed=False,
                check_name="ETH Gas Reserve",
                message=f"ETH balance {eth_balance:.4f} below minimum {eth_min:.4f}",
                severity="error"
            ))
        elif eth_balance < eth_target:
            results.append(SafetyCheckResult(
                passed=True,
                check_name="ETH Gas Reserve",
                message=f"ETH balance {eth_balance:.4f} below target {eth_target:.4f} but above minimum",
                severity="warning"
            ))
        else:
            results.append(SafetyCheckResult(
                passed=True,
                check_name="ETH Gas Reserve",
                message=f"ETH balance {eth_balance:.4f} OK (target: {eth_target:.4f})",
                severity="info"
            ))
        
        # Check USDC CEX reserve
        usdc_min_pct = self.config.usdc_cex_min_pct
        usdc_target_pct = self.config.usdc_cex_target_pct
        
        usdc_min = aum * usdc_min_pct
        usdc_target = aum * usdc_target_pct
        
        if usdc_cex_balance < usdc_min:
            results.append(SafetyCheckResult(
                passed=False,
                check_name="USDC CEX Reserve",
                message=f"USDC balance ${usdc_cex_balance:.2f} below minimum ${usdc_min:.2f} ({usdc_min_pct*100:.2f}% of AUM)",
                severity="error"
            ))
        elif usdc_cex_balance < usdc_target:
            results.append(SafetyCheckResult(
                passed=True,
                check_name="USDC CEX Reserve",
                message=f"USDC balance ${usdc_cex_balance:.2f} below target ${usdc_target:.2f} but above minimum",
                severity="warning"
            ))
        else:
            results.append(SafetyCheckResult(
                passed=True,
                check_name="USDC CEX Reserve",
                message=f"USDC balance ${usdc_cex_balance:.2f} OK (target: ${usdc_target:.2f})",
                severity="info"
            ))
        
        return results
    
    def check_slippage(
        self,
        estimated_slippage_bps: int
    ) -> SafetyCheckResult:
        """
        Check if estimated slippage is within acceptable range.
        
        Args:
            estimated_slippage_bps: Estimated slippage in basis points
            
        Returns:
            Safety check result
        """
        max_slippage = self.config.slippage_bps
        
        if estimated_slippage_bps > max_slippage:
            return SafetyCheckResult(
                passed=False,
                check_name="Slippage Check",
                message=f"Estimated slippage {estimated_slippage_bps} bps exceeds maximum {max_slippage} bps",
                severity="error"
            )
        else:
            return SafetyCheckResult(
                passed=True,
                check_name="Slippage Check",
                message=f"Estimated slippage {estimated_slippage_bps} bps within limit {max_slippage} bps",
                severity="info"
            )
    
    def check_gas_cost(
        self,
        estimated_gas_eth: float
    ) -> SafetyCheckResult:
        """
        Check if estimated gas cost is within acceptable range.
        
        Args:
            estimated_gas_eth: Estimated gas cost in ETH
            
        Returns:
            Safety check result
        """
        max_gas = self.config.gas_cap_native
        
        if estimated_gas_eth > max_gas:
            return SafetyCheckResult(
                passed=False,
                check_name="Gas Cost Check",
                message=f"Estimated gas {estimated_gas_eth:.4f} ETH exceeds cap {max_gas:.4f} ETH",
                severity="error"
            )
        else:
            return SafetyCheckResult(
                passed=True,
                check_name="Gas Cost Check",
                message=f"Estimated gas {estimated_gas_eth:.4f} ETH within cap {max_gas:.4f} ETH",
                severity="info"
            )
    
    def check_api_health(
        self,
        aerodrome_healthy: bool,
        hyperliquid_healthy: bool
    ) -> List[SafetyCheckResult]:
        """
        Check if external APIs are healthy.
        
        Args:
            aerodrome_healthy: Whether Aerodrome API is responding
            hyperliquid_healthy: Whether Hyperliquid API is responding
            
        Returns:
            List of safety check results
        """
        results = []
        
        if not aerodrome_healthy:
            results.append(SafetyCheckResult(
                passed=False,
                check_name="Aerodrome API Health",
                message="Aerodrome API is not responding",
                severity="error"
            ))
        else:
            results.append(SafetyCheckResult(
                passed=True,
                check_name="Aerodrome API Health",
                message="Aerodrome API is healthy",
                severity="info"
            ))
        
        if not hyperliquid_healthy:
            results.append(SafetyCheckResult(
                passed=False,
                check_name="Hyperliquid API Health",
                message="Hyperliquid API is not responding",
                severity="error"
            ))
        else:
            results.append(SafetyCheckResult(
                passed=True,
                check_name="Hyperliquid API Health",
                message="Hyperliquid API is healthy",
                severity="info"
            ))
        
        return results
    
    def check_liquidity(
        self,
        pool_liquidity_usd: float,
        min_liquidity_usd: float = 100000
    ) -> SafetyCheckResult:
        """
        Check if pool has sufficient liquidity.
        
        Args:
            pool_liquidity_usd: Current pool liquidity in USD
            min_liquidity_usd: Minimum required liquidity
            
        Returns:
            Safety check result
        """
        if pool_liquidity_usd < min_liquidity_usd:
            return SafetyCheckResult(
                passed=False,
                check_name="Pool Liquidity",
                message=f"Pool liquidity ${pool_liquidity_usd:,.0f} below minimum ${min_liquidity_usd:,.0f}",
                severity="error"
            )
        else:
            return SafetyCheckResult(
                passed=True,
                check_name="Pool Liquidity",
                message=f"Pool liquidity ${pool_liquidity_usd:,.0f} sufficient",
                severity="info"
            )
    
    def run_all_checks(
        self,
        eth_balance: float,
        usdc_cex_balance: float,
        aum: float,
        estimated_slippage_bps: int,
        estimated_gas_eth: float,
        aerodrome_healthy: bool,
        hyperliquid_healthy: bool,
        pool_liquidity_usd: float
    ) -> Dict:
        """
        Run all safety checks.
        
        Returns:
            Dictionary with results and overall pass/fail
        """
        all_results = []
        
        # Reserve checks
        all_results.extend(self.check_reserves(eth_balance, usdc_cex_balance, aum))
        
        # Slippage check
        all_results.append(self.check_slippage(estimated_slippage_bps))
        
        # Gas check
        all_results.append(self.check_gas_cost(estimated_gas_eth))
        
        # API health checks
        all_results.extend(self.check_api_health(aerodrome_healthy, hyperliquid_healthy))
        
        # Liquidity check
        all_results.append(self.check_liquidity(pool_liquidity_usd))
        
        # Determine overall pass/fail
        all_passed = all(r.passed for r in all_results)
        errors = [r for r in all_results if not r.passed]
        warnings = [r for r in all_results if r.passed and r.severity == "warning"]
        
        return {
            "all_passed": all_passed,
            "results": all_results,
            "errors": errors,
            "warnings": warnings,
            "auto_mode_allowed": all_passed
        }
