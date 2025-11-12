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

# Sidebar
with st.sidebar:
    st.title("🎯 XCELFI LP Hedge V3")
    st.markdown("---")
    
    # Configuration
    st.subheader("⚙️ Configuração")
    
    # Get API key from environment or user input
    octav_api_key = os.getenv("OCTAV_API_KEY", "")
    if not octav_api_key:
        octav_api_key = st.text_input(
            "Octav.fi API Key",
            type="password",
            help="Obtenha em https://data.octav.fi"
        )
    else:
        st.success("✅ API Key configurada")
    
    # Wallet address
    default_wallet = os.getenv("WALLET_ADDRESS", "0xc1E18438Fed146D814418364134fE28cC8622B5C")
    wallet_address = st.text_input(
        "Wallet Address",
        value=default_wallet,
        help="Endereço da wallet para monitorar"
    )
    
    # Tolerance
    default_tolerance = float(os.getenv("TOLERANCE_PCT", "5.0"))
    tolerance_pct = st.slider(
        "Tolerância (%)",
        min_value=1.0,
        max_value=20.0,
        value=default_tolerance,
        step=0.5,
        help="Diferença percentual aceitável para considerar balanceado"
    )
    
    st.markdown("---")
    
    # Mode indicator
    mode = os.getenv("OPERATION_MODE", "ANALYSIS_READONLY")
    if mode == "ANALYSIS_READONLY":
        st.info("📖 **Modo:** Análise (Read-Only)")
    else:
        st.warning("⚠️ **Modo:** Execução Ativa")
    
    st.markdown("---")
    
    # Refresh button
    if st.button("🔄 Atualizar Dados", use_container_width=True):
        st.rerun()

# Main content
st.markdown('<div class="main-header">📊 Delta Neutral LP Hedge Dashboard</div>', unsafe_allow_html=True)

# Check if API key is provided
if not octav_api_key:
    st.warning("⚠️ Por favor, configure a API Key do Octav.fi na barra lateral.")
    st.info("""
    **Como obter a API Key:**
    1. Acesse https://data.octav.fi
    2. Faça login ou crie uma conta
    3. Vá para a seção API
    4. Gere uma nova API key
    5. Cole a chave na barra lateral
    """)
    st.stop()

# Initialize clients
try:
    with st.spinner("🔄 Conectando ao Octav.fi..."):
        octav_client = OctavClient(octav_api_key)
        analyzer = DeltaNeutralAnalyzer(tolerance_pct=tolerance_pct)
    
    # Fetch portfolio data
    with st.spinner("📊 Buscando dados do portfólio..."):
        portfolio = octav_client.get_portfolio(wallet_address)
    
    if not portfolio:
        st.error("❌ Erro ao buscar dados do portfólio. Verifique a API key e o endereço da wallet.")
        st.stop()
    
    # Display net worth
    networth = portfolio.get("networth", "0")
    st.metric("💰 Net Worth", f"${float(networth):.2f}")
    
    st.markdown("---")
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "🏦 Posições LP", "📉 Posições Short"])
    
    with tab1:
        st.subheader("🎯 Análise Delta-Neutral")
        
        # Get balances
        lp_balances = octav_client.get_lp_token_balances(wallet_address)
        short_balances = octav_client.get_short_balances(wallet_address)
        
        # Perform analysis
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
        
        lp_positions = octav_client.extract_lp_positions(portfolio)
        
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
            
            for token, balance in sorted(lp_balances.items()):
                col1, col2 = st.columns([1, 1])
                with col1:
                    st.write(f"**{token}**")
                with col2:
                    st.write(f"{balance:.6f}")
    
    with tab3:
        st.subheader("📉 Posições Short (Hyperliquid)")
        
        perp_positions = octav_client.extract_perp_positions(portfolio)
        
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
            
            for token, balance in sorted(short_balances.items()):
                col1, col2 = st.columns([1, 1])
                with col1:
                    st.write(f"**{token}**")
                with col2:
                    st.write(f"{balance:.6f}")

except Exception as e:
    st.error(f"❌ Erro: {str(e)}")
    st.exception(e)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9rem;">
    <p>XCELFI LP Hedge V3 - Delta Neutral Analysis</p>
    <p>Powered by Octav.fi API | Mode: Analysis (Read-Only)</p>
    <p>Last updated: {}</p>
</div>
""".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")), unsafe_allow_html=True)
