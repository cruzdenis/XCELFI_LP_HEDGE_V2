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
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .balanced {
        color: #28a745;
        font-weight: bold;
    }
    .under-hedge {
        color: #ffc107;
        font-weight: bold;
    }
    .over-hedge {
        color: #dc3545;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for saved configuration
if 'config_saved' not in st.session_state:
    st.session_state.config_saved = False
if 'saved_api_key' not in st.session_state:
    st.session_state.saved_api_key = os.getenv("OCTAV_API_KEY", "")
if 'saved_wallet' not in st.session_state:
    st.session_state.saved_wallet = os.getenv("WALLET_ADDRESS", "0xc1E18438Fed146D814418364134fE28cC8622B5C")
if 'saved_tolerance' not in st.session_state:
    st.session_state.saved_tolerance = float(os.getenv("TOLERANCE_PCT", "5.0"))

# Sidebar
with st.sidebar:
    st.title("🎯 XCELFI LP Hedge V3")
    st.markdown("---")
    
    # Configuration
    st.subheader("⚙️ Configuração")
    
    # Get API key from environment or user input
    default_api_key = os.getenv("OCTAV_API_KEY", "")
    if default_api_key:
        st.success("✅ API Key (ambiente)")
        api_key_input = default_api_key
        wallet_input = os.getenv("WALLET_ADDRESS", "0xc1E18438Fed146D814418364134fE28cC8622B5C")
        tolerance_input = float(os.getenv("TOLERANCE_PCT", "5.0"))
        
        # Auto-save environment config
        if not st.session_state.config_saved:
            st.session_state.saved_api_key = api_key_input
            st.session_state.saved_wallet = wallet_input
            st.session_state.saved_tolerance = tolerance_input
            st.session_state.config_saved = True
    else:
        # Manual input
        api_key_input = st.text_input(
            "Octav.fi API Key",
            value=st.session_state.saved_api_key if st.session_state.config_saved else "",
            type="password",
            help="Obtenha em https://data.octav.fi",
            key="api_key_input"
        )
        
        wallet_input = st.text_input(
            "Wallet Address",
            value=st.session_state.saved_wallet if st.session_state.config_saved else "0xc1E18438Fed146D814418364134fE28cC8622B5C",
            help="Endereço da wallet para monitorar",
            key="wallet_input"
        )
        
        tolerance_input = st.slider(
            "Tolerância (%)",
            min_value=1.0,
            max_value=20.0,
            value=st.session_state.saved_tolerance if st.session_state.config_saved else 5.0,
            step=0.5,
            help="Diferença percentual aceitável para considerar balanceado",
            key="tolerance_input"
        )
        
        # Save button
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Salvar", use_container_width=True, type="primary"):
                if api_key_input and wallet_input:
                    st.session_state.saved_api_key = api_key_input
                    st.session_state.saved_wallet = wallet_input
                    st.session_state.saved_tolerance = tolerance_input
                    st.session_state.config_saved = True
                    st.toast("✅ Configuração salva! Carregando dados...", icon="✅")
                    st.cache_data.clear()  # Clear cache to force fresh data
                    st.rerun()
                else:
                    st.error("❌ Preencha API Key e Wallet")
        
        with col2:
            if st.button("🔄 Atualizar", use_container_width=True):
                if st.session_state.config_saved:
                    st.toast("🔄 Atualizando dados...", icon="🔄")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.warning("⚠️ Salve a configuração primeiro")
    
    st.markdown("---")
    
    # Show saved configuration status
    if st.session_state.config_saved:
        st.success("✅ Configuração ativa")
        with st.expander("📋 Ver configuração"):
            st.text(f"Wallet: {st.session_state.saved_wallet[:10]}...")
            st.text(f"Tolerância: {st.session_state.saved_tolerance}%")
    else:
        st.info("ℹ️ Configure e salve para começar")
    
    st.markdown("---")
    
    # Mode indicator
    mode = os.getenv("OPERATION_MODE", "ANALYSIS_READONLY")
    if mode == "ANALYSIS_READONLY":
        st.info("📖 **Modo:** Análise (Read-Only)")
    else:
        st.warning("⚠️ **Modo:** Execução Ativa")

# Main content
st.markdown('<div class="main-header">📊 Delta Neutral LP Hedge Dashboard</div>', unsafe_allow_html=True)

# Check if configuration is saved
if not st.session_state.config_saved:
    st.warning("⚠️ Por favor, configure a API Key e Wallet na barra lateral e clique em **Salvar**.")
    st.info("""
    **Como obter a API Key:**
    1. Acesse https://data.octav.fi
    2. Faça login ou crie uma conta
    3. Vá para a seção API
    4. Gere uma nova API key
    5. Cole a chave na barra lateral
    6. **Clique em Salvar** 💾
    """)
    st.stop()

# Use saved configuration
octav_api_key = st.session_state.saved_api_key
wallet_address = st.session_state.saved_wallet
tolerance_pct = st.session_state.saved_tolerance

# Cache portfolio data to avoid multiple API calls
@st.cache_data(ttl=60, show_spinner=False)
def fetch_portfolio_data(api_key, wallet):
    """Fetch and cache portfolio data"""
    try:
        client = OctavClient(api_key)
        portfolio = client.get_portfolio(wallet)
        if not portfolio:
            return None
        
        # Extract all data in one go
        lp_positions = client.extract_lp_positions(portfolio)
        perp_positions = client.extract_perp_positions(portfolio)
        lp_balances = {}
        short_balances = {}
        
        # Aggregate LP balances
        for pos in lp_positions:
            symbol = client.normalize_symbol(pos.token_symbol)
            if symbol in lp_balances:
                lp_balances[symbol] += pos.balance
            else:
                lp_balances[symbol] = pos.balance
        
        # Aggregate short balances
        for pos in perp_positions:
            if pos.size < 0:  # Short position
                symbol = client.normalize_symbol(pos.symbol)
                abs_size = abs(pos.size)
                if symbol in short_balances:
                    short_balances[symbol] += abs_size
                else:
                    short_balances[symbol] = abs_size
        
        return {
            'portfolio': portfolio,
            'lp_positions': lp_positions,
            'perp_positions': perp_positions,
            'lp_balances': lp_balances,
            'short_balances': short_balances
        }
    except Exception as e:
        st.error(f"❌ Erro ao buscar dados: {str(e)}")
        return None

# Fetch data with loading indicator
try:
    with st.spinner("🔄 Carregando dados do Octav.fi..."):
        data = fetch_portfolio_data(octav_api_key, wallet_address)
    
    if not data:
        st.error("❌ Erro ao buscar dados do portfólio.")
        st.info("""
        **Possíveis causas:**
        - API key inválida ou expirada
        - Wallet address incorreto
        - Wallet sem posições ativas
        - Problema de conexão com Octav.fi
        
        **Solução:**
        1. Verifique a API key em https://data.octav.fi
        2. Confirme o endereço da wallet
        3. Tente clicar em Atualizar
        """)
        st.stop()
except Exception as e:
    st.error(f"❌ Erro inesperado: {str(e)}")
    st.info("💡 Tente clicar em **Atualizar** na barra lateral.")
    st.stop()

# Display net worth
portfolio = data['portfolio']
networth = portfolio.get("networth", "0")
st.metric("💰 Net Worth", f"${float(networth):.2f}")

st.markdown("---")

# Create tabs
tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "🏦 Posições LP", "📉 Posições Short"])

with tab1:
    st.subheader("🎯 Análise Delta-Neutral")
    
    # Get balances from cached data
    lp_balances = data['lp_balances']
    short_balances = data['short_balances']
    
    # Perform analysis
    analyzer = DeltaNeutralAnalyzer(tolerance_pct=tolerance_pct)
    suggestions = analyzer.compare_positions(lp_balances, short_balances)
    
    if not suggestions:
        st.info("ℹ️ Nenhuma posição encontrada para comparar.")
    else:
        # Summary metrics
        balanced = [s for s in suggestions if s.status == "balanced"]
        under_hedged = [s for s in suggestions if s.status == "under_hedged"]
        over_hedged = [s for s in suggestions if s.status == "over_hedged"]
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("✅ Balanceadas", len(balanced))
        with col2:
            st.metric("⚠️ Sub-Hedge", len(under_hedged))
        with col3:
            st.metric("⚠️ Sobre-Hedge", len(over_hedged))
        
        st.markdown("---")
        
        # Detailed analysis
        for s in suggestions:
            with st.expander(f"**{s.token}** - {s.status.upper().replace('_', ' ')}", expanded=True):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("LP Balance", f"{s.lp_balance:.6f}")
                with col2:
                    st.metric("Short Balance", f"{s.short_balance:.6f}")
                with col3:
                    st.metric("Diferença", f"{s.difference:+.6f} ({s.difference_pct:.2f}%)")
                
                if s.action != "none":
                    if s.action == "increase_short":
                        st.warning(f"➡️ **AÇÃO:** AUMENTAR SHORT em {s.adjustment_amount:.6f} {s.token}")
                    else:
                        st.warning(f"➡️ **AÇÃO:** DIMINUIR SHORT em {s.adjustment_amount:.6f} {s.token}")
                else:
                    st.success("✅ Posição balanceada - nenhuma ação necessária")
        
        # Action summary
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
            
            st.info("⚠️ **NOTA:** Execução via Hyperliquid API requer configuração adicional")

with tab2:
    st.subheader("🏦 Posições LP (Liquidity Provider)")
    
    lp_positions = data['lp_positions']
    
    if not lp_positions:
        st.info("ℹ️ Nenhuma posição LP encontrada.")
    else:
        for pos in lp_positions:
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                with col1:
                    st.write(f"**{pos.protocol}** ({pos.chain})")
                with col2:
                    st.write(f"{pos.token_symbol}")
                with col3:
                    st.write(f"{pos.balance:.6f}")
                with col4:
                    st.write(f"${pos.value:.2f}")
        
        st.markdown("---")
        st.subheader("📊 Balanços Agregados")
        
        for token, balance in sorted(data['lp_balances'].items()):
            col1, col2 = st.columns([1, 1])
            with col1:
                st.write(f"**{token}**")
            with col2:
                st.write(f"{balance:.6f}")

with tab3:
    st.subheader("📉 Posições Short (Hyperliquid)")
    
    perp_positions = data['perp_positions']
    
    if not perp_positions:
        st.info("ℹ️ Nenhuma posição perpétua encontrada.")
    else:
        for pos in perp_positions:
            direction = "SHORT" if pos.size < 0 else "LONG"
            color = "red" if pos.size < 0 else "green"
            
            with st.container():
                st.markdown(f"**{pos.symbol} {direction}** (Leverage: {pos.leverage}x)")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Size", f"{pos.size:.6f}")
                with col2:
                    st.metric("Mark Price", f"${pos.mark_price:.2f}")
                with col3:
                    st.metric("Position Value", f"${pos.position_value:.2f}")
                with col4:
                    pnl_color = "normal" if pos.open_pnl >= 0 else "inverse"
                    st.metric("Open P&L", f"${pos.open_pnl:.2f}", delta_color=pnl_color)
                
                st.markdown("---")
        
        st.subheader("📊 Balanços Agregados Short")
        
        for token, balance in sorted(data['short_balances'].items()):
            col1, col2 = st.columns([1, 1])
            with col1:
                st.write(f"**{token}**")
            with col2:
                st.write(f"{balance:.6f}")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9rem;">
    <p>XCELFI LP Hedge V3 - Delta Neutral Analysis</p>
    <p>Powered by Octav.fi API | Mode: Analysis (Read-Only)</p>
    <p>Last updated: {}</p>
</div>
""".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")), unsafe_allow_html=True)
