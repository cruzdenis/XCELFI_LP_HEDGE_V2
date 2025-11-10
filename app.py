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
from integrations.octav import OctavClient
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
        # Check if Octav.fi should be used
        use_octav = saved_settings.get("use_octav", True)
        octav_api_key = saved_settings.get("octav_api_key", "")
        
        uni_positions = []
        
        if use_octav and octav_api_key:
            # Use Octav.fi API
            st.info("📡 Fetching positions via Octav.fi API...")
            octav_client = OctavClient(api_key=octav_api_key)
            octav_positions = octav_client.get_positions(wallet_addr)
            
            # Convert Octav positions to our format
            # (Octav returns dict, we need to convert to Position objects or use dict directly)
            uni_positions = octav_positions
        else:
            # Use direct Subgraph queries
            configured_networks = saved_settings.get("uniswap_networks", ["base", "arbitrum", "ethereum", "optimism", "polygon"])
            graph_api_key = saved_settings.get("graph_api_key", "")
            
            uniswap_client = UniswapClient(
                wallet_address=wallet_addr,
                networks=configured_networks,
                graph_api_key=graph_api_key if graph_api_key else None
            )
            
            # Get positions
            uni_positions = uniswap_client.get_positions()
        
        if uni_positions:
            # Handle both dict and object formats
            networks = set()
            for p in uni_positions:
                if isinstance(p, dict):
                    networks.add(p.get('network', 'Unknown'))
                else:
                    networks.add(p.network)
            
            st.write(f"**Active LP Positions:** {len(uni_positions)} across {len(networks)} network(s)")
            
            for pos in uni_positions:
                # Support both dict and object
                if isinstance(pos, dict):
                    in_range = pos.get('in_range', True)
                    network = pos.get('network', 'Unknown')
                    token0 = pos.get('token0_symbol', '')
                    token1 = pos.get('token1_symbol', '')
                    fee_tier = pos.get('fee_tier', '')
                    token0_amt = pos.get('token0_amount', 0)
                    token1_amt = pos.get('token1_amount', 0)
                    liquidity = pos.get('liquidity', 0)
                    value_usd = pos.get('value_usd', 0)
                    uncollected_fees = pos.get('uncollected_fees_usd', 0)
                    pos_id = pos.get('id', '')
                else:
                    in_range = pos.in_range
                    network = pos.network
                    token0 = pos.token0_symbol
                    token1 = pos.token1_symbol
                    fee_tier = pos.fee_tier
                    token0_amt = pos.token0_amount
                    token1_amt = pos.token1_amount
                    liquidity = pos.liquidity
                    value_usd = getattr(pos, 'value_usd', 0)
                    uncollected_fees = getattr(pos, 'uncollected_fees_usd', 0)
                    pos_id = pos.id
                
                status_emoji = "✅" if in_range else "⚠️"
                with st.expander(f"{status_emoji} [{network}] {token0}/{token1} - Fee: {fee_tier}%"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**{token0} Amount:** {token0_amt:.6f}")
                        st.write(f"**{token1} Amount:** {token1_amt:.6f}")
                        st.write(f"**Liquidity:** {liquidity:,.0f}")
                        if value_usd > 0:
                            st.write(f"**Value USD:** ${value_usd:,.2f}")
                    
                    with col2:
                        if uncollected_fees > 0:
                            st.write(f"**Uncollected Fees:** ${uncollected_fees:.2f}")
                        st.write(f"**Status:** {'In Range' if in_range else 'Out of Range'}")
                    
                    st.caption(f"Position ID: {pos_id}")
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
    
    st.write("### The Graph API Key")
    
    graph_api_key = st.text_input(
        "The Graph API Key",
        value=current_settings.get("graph_api_key", ""),
        type="password",
        help="Required for Arbitrum, Optimism, and Polygon networks. Get your free API key at https://thegraph.com/studio/",
        key="cfg_graph_api_key"
    )
    
    if not graph_api_key and any(net in selected_networks for net in ["arbitrum", "optimism", "polygon"]):
        st.warning("⚠️ Arbitrum, Optimism, and Polygon require The Graph API key. Positions from these networks won't be shown without it.")
    
    if graph_api_key:
        st.success("✅ The Graph API key configured! All networks will be accessible.")
    
    st.caption("🔗 [Get your free API key at The Graph Studio](https://thegraph.com/studio/) (100k queries/month free)")
    
    st.markdown("---")
    
    st.write("### Octav.fi API (Recommended)")
    
    use_octav = st.checkbox(
        "Use Octav.fi API",
        value=current_settings.get("use_octav", True),
        help="Octav.fi provides a reliable API to fetch LP positions from all networks. Recommended over direct Subgraph queries.",
        key="cfg_use_octav"
    )
    
    octav_api_key = st.text_input(
        "Octav.fi API Key",
        value=current_settings.get("octav_api_key", ""),
        type="password",
        help="Get your API key at https://data.octav.fi/",
        key="cfg_octav_api_key"
    )
    
    if use_octav and octav_api_key:
        st.success("✅ Octav.fi API configured! Positions from all networks will be fetched reliably.")
    elif use_octav and not octav_api_key:
        st.warning("⚠️ Octav.fi is enabled but API key is missing. Please add your API key.")
    
    st.caption("🔗 [Get your free API key at Octav.fi](https://data.octav.fi/)")
    
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
        new_settings["graph_api_key"] = graph_api_key
        new_settings["use_octav"] = use_octav
        new_settings["octav_api_key"] = octav_api_key
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
