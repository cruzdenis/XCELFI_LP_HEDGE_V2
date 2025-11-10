"""
XCELFI LP Hedge - Simplified Working Version
"""
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime

# Import core modules
from core.config import config
from core.auth import AuthManager, render_login_page
from core.settings_manager import SettingsManager
from integrations.hyperliquid import HyperliquidClient

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

# Initialize auth manager with fallback
try:
    auth_users = config.auth_users if config.auth_users else {
        "admin": "$2b$12$vtRzZekTfubVv2u9G1ol3uV6UyUIGdskgTwtGhSpDmjh099inFtpW"
    }
    auth_manager = AuthManager(auth_users)
    
    # Check authentication
    if not auth_manager.is_authenticated():
        render_login_page(auth_manager)
        st.stop()
except Exception as e:
    st.error(f"Authentication error: {e}")
    st.stop()

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
    
    # User info
    current_user = auth_manager.get_current_user()
    st.write(f"👤 **User:** {current_user}")
    
    if st.button("🚪 Logout"):
        auth_manager.logout()
        st.rerun()

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
    st.write(f"**Hyperliquid URL:** {config.hyperliquid_base_url}")
    
    has_api_keys = bool(display_settings.get('hyperliquid_api_key') and display_settings.get('hyperliquid_api_secret'))
    st.write(f"**Has API Keys:** {'Yes' if has_api_keys else 'No'}")
    
    st.write(f"**Settings File:** data/user_settings.json")

st.markdown("---")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
