"""
Configuration management for XCELFI LP Hedge application.
Handles loading environment variables and determining operation mode.
"""
import os
import json
from typing import Optional, Dict
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()


class AppConfig(BaseModel):
    """Application configuration model."""
    
    # Environment
    app_env: str = Field(default="staging")
    streamlit_secret_key: str = Field(default="default-secret-key")
    
    # Authentication
    auth_users: Dict[str, str] = Field(default_factory=dict)
    
    # Wallet Configuration
    wallet_public_address: str = Field(default="")
    wallet_private_key: Optional[str] = Field(default=None)
    
    # Base L2 Configuration
    base_rpc_url: str = Field(default="https://mainnet.base.org")
    aerodrome_subgraph_url: str = Field(default="")
    aerodrome_router: str = Field(default="")
    aerodrome_pool_address: str = Field(default="")
    
    # Hyperliquid Configuration
    hyperliquid_api_key: Optional[str] = Field(default=None)
    hyperliquid_api_secret: Optional[str] = Field(default=None)
    hyperliquid_base_url: str = Field(default="https://api.hyperliquid.xyz")
    
    # Strategy Parameters
    watch_interval_min: int = Field(default=10)
    cron_full_check_hours: int = Field(default=12)
    range_total: float = Field(default=0.30)
    recenter_trigger: float = Field(default=0.01)
    hysteresis_reentry: float = Field(default=0.002)
    slippage_bps: int = Field(default=20)
    gas_cap_native: float = Field(default=0.01)
    cooldown_hours: int = Field(default=2)
    
    # Buffer Reserves
    reserve_usdc_pct: float = Field(default=0.01)
    reserve_eth_gas_pct: float = Field(default=0.01)
    usdc_cex_min_pct: float = Field(default=0.003)
    usdc_cex_target_pct: float = Field(default=0.006)
    eth_gas_min: float = Field(default=0.05)
    eth_gas_target: float = Field(default=0.10)
    
    # Target Allocation
    target_lp_pct: float = Field(default=0.74)
    target_short_pct: float = Field(default=0.24)
    
    @property
    def is_execution_mode(self) -> bool:
        """Check if application is in execution mode (has private keys)."""
        return bool(self.wallet_private_key)
    
    @property
    def is_hyperliquid_enabled(self) -> bool:
        """Check if Hyperliquid integration is enabled."""
        return bool(self.hyperliquid_api_key and self.hyperliquid_api_secret)
    
    @property
    def operation_mode(self) -> str:
        """Get current operation mode."""
        if self.is_execution_mode and self.is_hyperliquid_enabled:
            return "EXECUTION_FULL"
        elif self.is_execution_mode:
            return "EXECUTION_AERODROME_ONLY"
        else:
            return "ANALYSIS_READONLY"


def load_config() -> AppConfig:
    """Load configuration from environment variables."""
    
    # Parse AUTH_USERS_JSON
    auth_users_json = os.getenv("AUTH_USERS_JSON", "{}")
    try:
        auth_users = json.loads(auth_users_json)
    except json.JSONDecodeError:
        auth_users = {}
    
    # Get optional fields (return None if empty string)
    def get_optional(key: str) -> Optional[str]:
        value = os.getenv(key, "")
        return value if value else None
    
    config = AppConfig(
        app_env=os.getenv("APP_ENV", "staging"),
        streamlit_secret_key=os.getenv("STREAMLIT_SECRET_KEY", "default-secret-key"),
        auth_users=auth_users,
        
        wallet_public_address=os.getenv("WALLET_PUBLIC_ADDRESS", ""),
        wallet_private_key=get_optional("WALLET_PRIVATE_KEY"),
        
        base_rpc_url=os.getenv("BASE_RPC_URL", "https://mainnet.base.org"),
        aerodrome_subgraph_url=os.getenv("AERODROME_SUBGRAPH_URL", ""),
        aerodrome_router=os.getenv("AERODROME_ROUTER", ""),
        aerodrome_pool_address=os.getenv("AERODROME_POOL_ADDRESS", ""),
        
        hyperliquid_api_key=get_optional("HYPERLIQUID_API_KEY"),
        hyperliquid_api_secret=get_optional("HYPERLIQUID_API_SECRET"),
        hyperliquid_base_url=os.getenv("HYPERLIQUID_BASE_URL", "https://api.hyperliquid.xyz"),
        
        watch_interval_min=int(os.getenv("WATCH_INTERVAL_MIN", "10")),
        cron_full_check_hours=int(os.getenv("CRON_FULL_CHECK_HOURS", "12")),
        range_total=float(os.getenv("RANGE_TOTAL", "0.30")),
        recenter_trigger=float(os.getenv("RECENTER_TRIGGER", "0.01")),
        hysteresis_reentry=float(os.getenv("HYSTERESIS_REENTRY", "0.002")),
        slippage_bps=int(os.getenv("SLIPPAGE_BPS", "20")),
        gas_cap_native=float(os.getenv("GAS_CAP_NATIVE", "0.01")),
        cooldown_hours=int(os.getenv("COOLDOWN_HOURS", "2")),
        
        reserve_usdc_pct=float(os.getenv("RESERVE_USDC_PCT", "0.01")),
        reserve_eth_gas_pct=float(os.getenv("RESERVE_ETH_GAS_PCT", "0.01")),
        usdc_cex_min_pct=float(os.getenv("USDC_CEX_MIN_PCT", "0.003")),
        usdc_cex_target_pct=float(os.getenv("USDC_CEX_TARGET_PCT", "0.006")),
        eth_gas_min=float(os.getenv("ETH_GAS_MIN", "0.05")),
        eth_gas_target=float(os.getenv("ETH_GAS_TARGET", "0.10")),
        
        target_lp_pct=float(os.getenv("TARGET_LP_PCT", "0.74")),
        target_short_pct=float(os.getenv("TARGET_SHORT_PCT", "0.24")),
    )
    
    return config


# Global config instance
config = load_config()
