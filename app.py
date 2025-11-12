"""
XCELFI LP Hedge V3 - Streamlit Dashboard
Delta-Neutral Analysis using Octav.fi API
"""

import streamlit as st
import os
from datetime import datetime
from octav_client import OctavClient
from delta_neutral_analyzer import DeltaNeutralAnalyzer

# Page configuration
st.set_page_config(
    page_title="XCELFI LP Hedge V3",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'config_saved' not in st.session_state:
    st.session_state.config_saved = False

# Sidebar Configuration
with st.sidebar:
    st.title("🎯 XCELFI LP Hedge V3")
    st.markdown("---")
    st.subheader("⚙️ Configuração")
    
    # Check for environment variables first
    env_api_key = os.getenv("OCTAV_API_KEY", "")
    env_wallet = os.getenv("WALLET_ADDRESS", "")
    env_tolerance = float(os.getenv("TOLERANCE_PCT", "5.0"))
    
    # If environment variables exist, use them and auto-save
    if env_api_key and env_wallet:
        if 'api_key' not in st.session_state:
            st.session_state.api_key = env_api_key
            st.session_state.wallet = env_wallet
            st.session_state.tolerance = env_tolerance
            st.session_state.config_saved = True
        
        st.success("✅ Configuração via variáveis de ambiente")
        st.text(f"Wallet: {env_wallet[:10]}...")
        st.text(f"Tolerância: {env_tolerance}%")
        
        if st.button("🔄 Atualizar Dados", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    else:
        # Manual configuration
        api_key = st.text_input(
            "Octav.fi API Key",
            type="password",
            help="Obtenha em https://data.octav.fi"
        )
        
        wallet = st.text_input(
            "Wallet Address",
            value="0xc1E18438Fed146D814418364134fE28cC8622B5C",
            help="Endereço da wallet para monitorar"
        )
        
        tolerance = st.slider(
            "Tolerância (%)",
            min_value=1.0,
            max_value=20.0,
            value=5.0,
            step=0.5,
            help="Diferença percentual aceitável"
        )
        
        # Save button
        if st.button("💾 Salvar e Carregar", use_container_width=True, type="primary"):
            if api_key and wallet:
                st.session_state.api_key = api_key
                st.session_state.wallet = wallet
                st.session_state.tolerance = tolerance
                st.session_state.config_saved = True
                st.cache_data.clear()
                st.success("✅ Salvando...")
                st.rerun()
            else:
                st.error("❌ Preencha todos os campos")
        
        # Show status
        if st.session_state.config_saved:
            st.success("✅ Configuração salva")
            if st.button("🔄 Atualizar", use_container_width=True):
                st.cache_data.clear()
                st.rerun()
        else:
            st.info("ℹ️ Preencha e salve para começar")
    
    st.markdown("---")
    mode = os.getenv("OPERATION_MODE", "ANALYSIS_READONLY")
    if mode == "ANALYSIS_READONLY":
        st.info("📖 Modo: Análise (Read-Only)")

# Main content
st.markdown('<div class="main-header">📊 Delta Neutral LP Hedge Dashboard</div>', unsafe_allow_html=True)

# Check if configuration is saved
if not st.session_state.config_saved:
    st.warning("⚠️ Configure a API Key e Wallet na barra lateral e clique em **Salvar e Carregar**")
    st.info("""
    **Passos:**
    1. Obtenha API Key em https://data.octav.fi
    2. Cole a API Key no campo
    3. Insira o endereço da Wallet
    4. Clique em **💾 Salvar e Carregar**
    """)
    st.stop()

# Get saved configuration
api_key = st.session_state.api_key
wallet_address = st.session_state.wallet
tolerance_pct = st.session_state.tolerance

# Cache function
@st.cache_data(ttl=60, show_spinner=False)
def fetch_portfolio_data(api_key, wallet):
    """Fetch portfolio data from Octav.fi"""
    client = OctavClient(api_key)
    portfolio = client.get_portfolio(wallet)
    
    if not portfolio:
        return None
    
    lp_positions = client.extract_lp_positions(portfolio)
    perp_positions = client.extract_perp_positions(portfolio)
    
    # Aggregate balances
    lp_balances = {}
    for pos in lp_positions:
        symbol = client.normalize_symbol(pos.token_symbol)
        lp_balances[symbol] = lp_balances.get(symbol, 0) + pos.balance
    
    short_balances = {}
    for pos in perp_positions:
        if pos.size < 0:
            symbol = client.normalize_symbol(pos.symbol)
            short_balances[symbol] = short_balances.get(symbol, 0) + abs(pos.size)
    
    return {
        'portfolio': portfolio,
        'lp_positions': lp_positions,
        'perp_positions': perp_positions,
        'lp_balances': lp_balances,
        'short_balances': short_balances
    }

# Load data
with st.spinner("🔄 Carregando dados do Octav.fi..."):
    try:
        data = fetch_portfolio_data(api_key, wallet_address)
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados: {str(e)}")
        st.info("💡 Verifique a API Key e tente clicar em **Atualizar**")
        st.code(str(e))
        st.stop()

if not data:
    st.error("❌ Nenhum dado retornado")
    st.info("""
    **Possíveis causas:**
    - API Key inválida
    - Wallet sem posições
    - Problema de conexão
    
    Clique em **Atualizar** na barra lateral
    """)
    st.stop()

# Display data
portfolio = data['portfolio']
networth = portfolio.get("networth", "0")
st.metric("💰 Net Worth", f"${float(networth):.2f}")

st.markdown("---")

# Tabs
tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "🏦 Posições LP", "📉 Posições Short"])

with tab1:
    st.subheader("🎯 Análise Delta-Neutral")
    
    lp_balances = data['lp_balances']
    short_balances = data['short_balances']
    
    analyzer = DeltaNeutralAnalyzer(tolerance_pct=tolerance_pct)
    suggestions = analyzer.compare_positions(lp_balances, short_balances)
    
    if not suggestions:
        st.info("ℹ️ Nenhuma posição encontrada")
    else:
        # Summary
        balanced = [s for s in suggestions if s.status == "balanced"]
        under_hedged = [s for s in suggestions if s.status == "under_hedged"]
        over_hedged = [s for s in suggestions if s.status == "over_hedged"]
        
        col1, col2, col3 = st.columns(3)
        col1.metric("✅ Balanceadas", len(balanced))
        col2.metric("⚠️ Sub-Hedge", len(under_hedged))
        col3.metric("⚠️ Sobre-Hedge", len(over_hedged))
        
        st.markdown("---")
        
        # Details
        for s in suggestions:
            with st.expander(f"**{s.token}** - {s.status.upper().replace('_', ' ')}", expanded=True):
                col1, col2, col3 = st.columns(3)
                col1.metric("LP", f"{s.lp_balance:.6f}")
                col2.metric("Short", f"{s.short_balance:.6f}")
                col3.metric("Diferença", f"{s.difference:+.6f} ({s.difference_pct:.2f}%)")
                
                if s.action != "none":
                    action_text = "AUMENTAR" if s.action == "increase_short" else "DIMINUIR"
                    st.warning(f"➡️ **AÇÃO:** {action_text} SHORT em {s.adjustment_amount:.6f} {s.token}")
                else:
                    st.success("✅ Balanceado")
        
        # Summary
        if under_hedged or over_hedged:
            st.markdown("---")
            st.subheader("📋 Resumo de Ações")
            
            if under_hedged:
                st.markdown("**🔺 AUMENTAR SHORT:**")
                for s in under_hedged:
                    st.write(f"- {s.token}: +{s.adjustment_amount:.6f}")
            
            if over_hedged:
                st.markdown("**🔻 DIMINUIR SHORT:**")
                for s in over_hedged:
                    st.write(f"- {s.token}: -{s.adjustment_amount:.6f}")

with tab2:
    st.subheader("🏦 Posições LP")
    
    lp_positions = data['lp_positions']
    
    if not lp_positions:
        st.info("ℹ️ Nenhuma posição LP")
    else:
        for pos in lp_positions:
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            col1.write(f"**{pos.protocol}** ({pos.chain})")
            col2.write(pos.token_symbol)
            col3.write(f"{pos.balance:.6f}")
            col4.write(f"${pos.value:.2f}")
        
        st.markdown("---")
        st.subheader("📊 Agregado")
        for token, balance in sorted(data['lp_balances'].items()):
            col1, col2 = st.columns([1, 1])
            col1.write(f"**{token}**")
            col2.write(f"{balance:.6f}")

with tab3:
    st.subheader("📉 Posições Short")
    
    perp_positions = data['perp_positions']
    
    if not perp_positions:
        st.info("ℹ️ Nenhuma posição perpétua")
    else:
        for pos in perp_positions:
            direction = "SHORT" if pos.size < 0 else "LONG"
            st.markdown(f"**{pos.symbol} {direction}** ({pos.leverage}x)")
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Size", f"{pos.size:.6f}")
            col2.metric("Mark", f"${pos.mark_price:.2f}")
            col3.metric("Value", f"${pos.position_value:.2f}")
            col4.metric("P&L", f"${pos.open_pnl:.2f}")
            st.markdown("---")
        
        st.subheader("📊 Agregado Short")
        for token, balance in sorted(data['short_balances'].items()):
            col1, col2 = st.columns([1, 1])
            col1.write(f"**{token}**")
            col2.write(f"{balance:.6f}")

# Footer
st.markdown("---")
st.caption(f"XCELFI LP Hedge V3 | Octav.fi API | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
