"""
XCELFI LP Hedge - Simplified Working Version
"""
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime

# Import core modules
from core.config import config
from core.settings_manager import SettingsManager
from integrations.hyperliquid import HyperliquidClient
from integrations.uniswap import UniswapClient
from core.delta_neutral import DeltaNeutralAnalyzer

# Page configuration
st.set_page_config(
    page_title="XCELFI LP Hedge",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize settings manager
if 'settings_manager' not in st.session_state:
    st.session_state.settings_manager = SettingsManager()

settings_manager = st.session_state.settings_manager

# Sidebar
with st.sidebar:
    st.title("🎯 XCELFI LP Hedge")
    st.markdown("---")
    
    # Operation mode indicator
    mode = config.operation_mode
    if mode == "ANALYSIS_READONLY":
        st.info("📖 **Mode:** Analysis (Read-Only)")
    elif mode == "EXECUTION_AERODROME_ONLY":
        st.warning("⚠️ **Mode:** Execution (Aerodrome Only)")
    else:
        st.success("✅ **Mode:** Full Execution")
    
    st.markdown("---")

# Main content
st.title("📊 Delta Neutral LP Hedge Dashboard")

# Create tabs
main_tabs = st.tabs(["📊 Dashboard", "⚙️ Configurações"])

# TAB 1: DASHBOARD
with main_tabs[0]:
    st.subheader("Hyperliquid Positions")
    
    # Load saved settings
    saved_settings = settings_manager.load_settings()
    
    # Use saved settings if available, otherwise use config defaults
    wallet_addr = saved_settings.get("wallet_public_address", config.wallet_public_address)
    hl_key = saved_settings.get("hyperliquid_api_key", config.hyperliquid_api_key)
    hl_secret = saved_settings.get("hyperliquid_api_secret", config.hyperliquid_api_secret)
    
    # Initialize Hyperliquid client
    try:
        hyperliquid_client = HyperliquidClient(
            base_url=config.hyperliquid_base_url,
            wallet_address=wallet_addr,
            api_key=hl_key,
            api_secret=hl_secret
        )
        
        # Get balance
        balance = hyperliquid_client.get_balance()
        
        if balance:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Account Value", f"${balance.get('total_equity', 0):.2f}")
            
            with col2:
                st.metric("Available", f"${balance.get('available_balance', 0):.2f}")
            
            with col3:
                st.metric("Margin Used", f"${balance.get('margin_used', 0):.2f}")
            
            with col4:
                st.metric("Unrealized PnL", f"${balance.get('unrealized_pnl', 0):.2f}")
            
            st.markdown("---")
        
        # Get positions
        positions = hyperliquid_client.get_positions()
        
        if positions:
            st.write(f"**Open Positions:** {len(positions)}")
            
            for pos in positions:
                with st.expander(f"{pos.symbol} - Size: {pos.size:.6f}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Entry Price:** ${pos.entry_price:,.2f}")
                        st.write(f"**Mark Price:** ${pos.mark_price:,.2f}")
                        st.write(f"**Leverage:** {pos.leverage}x")
                    
                    with col2:
                        st.write(f"**Position Value:** ${abs(pos.size * pos.mark_price):,.2f}")
                        st.write(f"**Unrealized PnL:** ${pos.unrealized_pnl:.2f}")
                        st.write(f"**Margin:** ${pos.margin:.2f}")
        else:
            st.info("No open positions found")
    
    except Exception as e:
        st.error(f"Error loading Hyperliquid data: {e}")
        st.info("Make sure you have configured your wallet address in Settings")
    
    st.markdown("---")
    st.markdown("---")
    
    # UNISWAP V3 POSITIONS
    st.subheader("Uniswap V3 LP Positions (Multi-Network)")
    
    try:
        # Get configured networks from settings
        configured_networks = saved_settings.get("uniswap_networks", ["base", "arbitrum", "ethereum", "optimism", "polygon"])
        
        uniswap_client = UniswapClient(
            wallet_address=wallet_addr,
            networks=configured_networks
        )
        
        # Get positions
        uni_positions = uniswap_client.get_positions()
        
        if uni_positions:
            st.write(f"**Active LP Positions:** {len(uni_positions)} across {len(set(p.network for p in uni_positions))} network(s)")
            
            for pos in uni_positions:
                status_emoji = "✅" if pos.in_range else "⚠️"
                with st.expander(f"{status_emoji} [{pos.network}] {pos.token0_symbol}/{pos.token1_symbol} - Fee: {pos.fee_tier}%"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**{pos.token0_symbol} Amount:** {pos.token0_amount:.6f}")
                        st.write(f"**{pos.token1_symbol} Amount:** {pos.token1_amount:.6f}")
                        st.write(f"**Liquidity:** {pos.liquidity:,.0f}")
                    
                    with col2:
                        st.write(f"**Fees {pos.token0_symbol}:** {pos.fees_token0:.6f}")
                        st.write(f"**Fees {pos.token1_symbol}:** {pos.fees_token1:.6f}")
                        st.write(f"**Status:** {'In Range' if pos.in_range else 'Out of Range'}")
                    
                    st.caption(f"Position ID: {pos.id}")
        else:
            st.info(f"No Uniswap V3 positions found on configured networks: {', '.join(configured_networks)}")
            st.caption("Tip: You can configure which networks to monitor in the Settings tab")
    
    except Exception as e:
        st.error(f"Error loading Uniswap data: {e}")
        st.info("Make sure you have configured your wallet address in Settings")
    
    st.markdown("---")
    st.markdown("---")
    
    # DELTA NEUTRAL ANALYSIS
    st.subheader("🎯 Delta Neutral Analysis")
    
    try:
        # Initialize analyzer
        analyzer = DeltaNeutralAnalyzer(tolerance_pct=5.0)
        
        # Extract LP positions (combine all sources)
        all_lp_positions = []
        
        # Add Uniswap positions if available
        if 'uni_positions' in locals() and uni_positions:
            for pos in uni_positions:
                all_lp_positions.append({
                    'token0_symbol': pos.token0_symbol,
                    'token0_amount': pos.token0_amount,
                    'token1_symbol': pos.token1_symbol,
                    'token1_amount': pos.token1_amount
                })
        
        # Extract LP token positions
        lp_token_positions = analyzer.extract_lp_positions(all_lp_positions)
        
        # Extract short positions from Hyperliquid
        hl_positions_dict = []
        if 'positions' in locals() and positions:
            for pos in positions:
                hl_positions_dict.append({
                    'coin': pos.symbol,
                    'szi': pos.size
                })
        
        short_positions = analyzer.extract_short_positions(hl_positions_dict)
        
        # Compare and generate suggestions
        suggestions = analyzer.compare_positions(lp_token_positions, short_positions)
        
        if suggestions:
            # Display summary
            balanced_count = sum(1 for s in suggestions if s.suggested_action == "balanced")
            needs_adjustment_count = len(suggestions) - balanced_count
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Balanced Positions", balanced_count)
            with col2:
                st.metric("Needs Adjustment", needs_adjustment_count)
            
            st.markdown("---")
            
            # Display detailed suggestions
            for suggestion in suggestions:
                if suggestion.suggested_action == "balanced":
                    st.success(f"✅ **{suggestion.token}**: Balanced")
                    st.caption(f"LP: {suggestion.current_lp:.6f} | Short: {suggestion.current_short:.6f}")
                elif suggestion.suggested_action == "increase_short":
                    st.warning(f"⚠️ **{suggestion.token}**: Need to INCREASE SHORT")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Current LP", f"{suggestion.current_lp:.6f}")
                    with col2:
                        st.metric("Current Short", f"{suggestion.current_short:.6f}")
                    with col3:
                        st.metric("Adjustment Needed", f"+{suggestion.adjustment_amount:.6f}", delta=f"+{suggestion.adjustment_amount:.6f}")
                elif suggestion.suggested_action == "decrease_short":
                    st.warning(f"⚠️ **{suggestion.token}**: Need to DECREASE SHORT")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Current LP", f"{suggestion.current_lp:.6f}")
                    with col2:
                        st.metric("Current Short", f"{suggestion.current_short:.6f}")
                    with col3:
                        st.metric("Adjustment Needed", f"-{suggestion.adjustment_amount:.6f}", delta=f"-{suggestion.adjustment_amount:.6f}")
                
                st.markdown("---")
        else:
            st.info("No positions to compare. Configure your wallet and ensure you have both LP positions and Hyperliquid shorts.")
    
    except Exception as e:
        st.error(f"Error in Delta Neutral Analysis: {e}")
        st.info("Make sure you have configured your wallet address and have active positions")

# TAB 2: CONFIGURAÇÕES
with main_tabs[1]:
    st.subheader("⚙️ Configurações")
    
    # Load current settings
    current_settings = settings_manager.load_settings()
    
    st.write("### Wallet Configuration")
    
    wallet_address = st.text_input(
        "Wallet Public Address",
        value=current_settings.get("wallet_public_address", config.wallet_public_address),
        help="Your wallet address to monitor positions",
        key="cfg_wallet_address"
    )
    
    st.write("### Uniswap V3 Networks")
    
    st.write("Select which networks to monitor for LP positions:")
    
    available_networks = ["base", "arbitrum", "ethereum", "optimism", "polygon"]
    current_networks = current_settings.get("uniswap_networks", available_networks)
    
    selected_networks = st.multiselect(
        "Networks",
        options=available_networks,
        default=current_networks,
        help="Select one or more networks to monitor. This is equivalent to what Revert Finance shows.",
        key="cfg_uniswap_networks"
    )
    
    st.caption("💡 Revert Finance aggregates data from these same Uniswap V3 networks. By selecting multiple networks, you'll see all your positions just like in Revert Finance.")
    
    st.markdown("---")
    
    st.write("### Hyperliquid Configuration")
    
    hl_api_key = st.text_input(
        "Hyperliquid API Key (optional)",
        value=current_settings.get("hyperliquid_api_key", config.hyperliquid_api_key or ""),
        type="password",
        help="Required for execution",
        key="cfg_hl_api_key"
    )
    
    hl_api_secret = st.text_input(
        "Hyperliquid API Secret (optional)",
        value=current_settings.get("hyperliquid_api_secret", config.hyperliquid_api_secret or ""),
        type="password",
        help="Required for execution",
        key="cfg_hl_api_secret"
    )
    
    if st.button("💾 Save Configuration"):
        # Update settings
        new_settings = current_settings.copy()
        new_settings["wallet_public_address"] = wallet_address
        new_settings["uniswap_networks"] = selected_networks
        new_settings["hyperliquid_api_key"] = hl_api_key
        new_settings["hyperliquid_api_secret"] = hl_api_secret
        
        # Save to file
        if settings_manager.save_settings(new_settings):
            st.success("✅ Configuration saved successfully!")
            st.info("🔄 Please refresh the page to apply changes.")
        else:
            st.error("❌ Failed to save configuration. Please try again.")
    
    st.markdown("---")
    
    st.write("### System Information")
    
    # Show current saved settings
    display_settings = settings_manager.load_settings()
    
    st.write(f"**Operation Mode:** {config.operation_mode}")
    st.write(f"**Wallet Address:** {display_settings.get('wallet_public_address', 'Not configured')}")
    st.write(f"**Monitored Networks:** {', '.join(display_settings.get('uniswap_networks', []))}")
    st.write(f"**Hyperliquid URL:** {config.hyperliquid_base_url}")
    
    has_api_keys = bool(display_settings.get('hyperliquid_api_key') and display_settings.get('hyperliquid_api_secret'))
    st.write(f"**Has API Keys:** {'Yes' if has_api_keys else 'No'}")
    
    st.caption("💡 Tip: Revert Finance is just a UI that shows Uniswap V3 positions from multiple networks. This app does the same thing directly!")
    
    st.write(f"**Settings File:** data/user_settings.json")

st.markdown("---")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
