"""
XCELFI LP Hedge V3 - Streamlit Dashboard
Delta-Neutral Analysis using Octav.fi API
"""

import streamlit as st
import os
from datetime import datetime
from octav_client import OctavClient
from delta_neutral_analyzer import DeltaNeutralAnalyzer
from config_manager import ConfigManager

# Page configuration
st.set_page_config(
    page_title="XCELFI LP Hedge V3",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .last-sync {
        text-align: center;
        color: #666;
        font-size: 0.9rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize config manager
config_mgr = ConfigManager()

# Header
st.markdown('<div class="main-header">🎯 XCELFI LP Hedge V3</div>', unsafe_allow_html=True)
st.markdown('<div class="last-sync">Delta-Neutral LP Hedge Dashboard</div>', unsafe_allow_html=True)

# Main tabs
tab1, tab2, tab3, tab4 = st.tabs(["⚙️ Configuração", "📊 Dashboard", "🏦 Posições LP", "📜 Histórico"])

# ==================== TAB 1: CONFIGURAÇÃO ====================
with tab1:
    st.subheader("⚙️ Configuração")
    st.markdown("Configure sua API Key e Wallet Address. As configurações serão salvas permanentemente.")
    
    st.markdown("---")
    
    # Load existing config
    existing_config = config_mgr.load_config()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🔑 API Configuration")
        
        api_key = st.text_input(
            "Octav.fi API Key",
            value=existing_config.get("api_key", "") if existing_config else "",
            type="password",
            help="Obtenha em https://data.octav.fi",
            key="config_api_key"
        )
        
        wallet = st.text_input(
            "Wallet Address",
            value=existing_config.get("wallet_address", "") if existing_config else "0xc1E18438Fed146D814418364134fE28cC8622B5C",
            help="Endereço da wallet para monitorar",
            key="config_wallet"
        )
        
        st.markdown("### 🔐 Hyperliquid Execution (Opcional)")
        
        hyperliquid_key = st.text_input(
            "Hyperliquid Private Key",
            value=existing_config.get("hyperliquid_private_key", "") if existing_config else "",
            type="password",
            help="Private key da API wallet da Hyperliquid para execução automática. Deixe em branco para modo somente análise.",
            key="config_hyperliquid_key"
        )
        
        if hyperliquid_key:
            st.success("✅ Execução automática habilitada")
        else:
            st.info("ℹ️ Modo somente análise (sem execução)")
    
    with col2:
        st.markdown("### ⚙️ Parâmetros")
        
        tolerance = st.slider(
            "Tolerância (%)",
            min_value=1.0,
            max_value=20.0,
            value=existing_config.get("tolerance_pct", 5.0) if existing_config else 5.0,
            step=0.5,
            help="Diferença percentual aceitável para considerar balanceado",
            key="config_tolerance"
        )
        
        st.markdown("### 📊 Status")
        if existing_config:
            st.success("✅ Configuração salva")
            saved_at = existing_config.get("saved_at", "")
            if saved_at:
                st.caption(f"Salvo em: {saved_at[:19]}")
        else:
            st.info("ℹ️ Nenhuma configuração salva")
    
    st.markdown("---")
    
    # Save button
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("💾 Salvar Configuração", use_container_width=True, type="primary"):
            if api_key and wallet:
                config_mgr.save_config(api_key, wallet, tolerance, hyperliquid_key)
                st.success("✅ Configuração salva com sucesso! Vá para a aba Dashboard.")
                st.balloons()
                
                # Validate Hyperliquid API if private key provided
                if hyperliquid_key:
                    with st.spinner("🔍 Validando Hyperliquid API..."):
                        try:
                            from hyperliquid_client import HyperliquidClient
                            client = HyperliquidClient(wallet, hyperliquid_key)
                            account_value = client.get_account_value()
                            
                            if account_value is not None:
                                st.success(f"✅ Hyperliquid conectado! Saldo: ${account_value:,.2f}")
                            else:
                                st.warning("⚠️ Não foi possível obter saldo da Hyperliquid. Verifique a private key.")
                        except Exception as e:
                            st.error(f"❌ Erro ao validar Hyperliquid: {str(e)}")
            else:
                st.error("❌ Preencha API Key e Wallet Address")
    
    with col2:
        if st.button("🗑️ Limpar Configuração", use_container_width=True):
            config_mgr.clear_config()
            st.success("✅ Configuração removida")
    
    st.markdown("---")
    
    # Instructions
    with st.expander("📖 Como obter a API Key"):
        st.markdown("""
        1. Acesse https://data.octav.fi
        2. Faça login ou crie uma conta
        3. Vá para a seção API
        4. Gere uma nova API key
        5. Cole a chave acima e clique em **Salvar Configuração**
        """)

# ==================== TAB 2: DASHBOARD ====================
with tab2:
    st.subheader("📊 Dashboard - Análise Delta-Neutral")
    
    # Check if config exists
    config = config_mgr.load_config()
    
    if not config:
        st.warning("⚠️ Configure a API Key e Wallet na aba **Configuração** primeiro")
    else:
        # Get config values
        api_key = config["api_key"]
        wallet_address = config["wallet_address"]
        tolerance_pct = config["tolerance_pct"]
    
        # Last sync info
        last_sync = config_mgr.get_last_sync()
        if last_sync:
            st.markdown(f'<div class="last-sync">Última sincronização: {last_sync[:19]}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="last-sync">Nenhuma sincronização realizada</div>', unsafe_allow_html=True)
    
        # Sync button
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            sync_now = st.button("🔄 Sincronizar Agora", use_container_width=True, type="primary")
    
        st.markdown("---")
    
        # Load data function
        def load_portfolio_data():
            """Load portfolio data from Octav.fi"""
            client = OctavClient(api_key)
            portfolio = client.get_portfolio(wallet_address)
        
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
    
        # Initialize session state for data
        if 'portfolio_data' not in st.session_state or sync_now:
            with st.spinner("🔄 Sincronizando dados do Octav.fi..."):
                try:
                    data = load_portfolio_data()
                    if data:
                        st.session_state.portfolio_data = data
                        st.session_state.last_sync_time = datetime.now().isoformat()
                        st.success("✅ Dados sincronizados com sucesso!")
                    else:
                        st.error("❌ Erro ao carregar dados")
                        pass
                except Exception as e:
                    st.error(f"❌ Erro: {str(e)}")
                    pass
    
        # Check if data exists
        if 'portfolio_data' not in st.session_state:
            st.info("ℹ️ Clique em **Sincronizar Agora** para carregar os dados")
            pass
    
        data = st.session_state.portfolio_data
    
        # Display net worth
        portfolio = data['portfolio']
        networth = portfolio.get("networth", "0")
    
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("💰 Net Worth", f"${float(networth):.2f}")
        with col2:
            st.metric("🏦 Posições LP", len(data['lp_positions']))
        with col3:
            st.metric("📉 Posições Short", len([p for p in data['perp_positions'] if p.size < 0]))
    
        st.markdown("---")
    
        # Perform analysis
        lp_balances = data['lp_balances']
        short_balances = data['short_balances']
    
        analyzer = DeltaNeutralAnalyzer(tolerance_pct=tolerance_pct)
        suggestions = analyzer.compare_positions(lp_balances, short_balances)
    
        if not suggestions:
            st.info("ℹ️ Nenhuma posição encontrada para comparar")
        else:
            # Summary metrics
            balanced = [s for s in suggestions if s.status == "balanced"]
            under_hedged = [s for s in suggestions if s.status == "under_hedged"]
            over_hedged = [s for s in suggestions if s.status == "over_hedged"]
        
            # Save to history
            if sync_now:
                summary = {
                    "networth": float(networth),
                    "balanced": len(balanced),
                    "under_hedged": len(under_hedged),
                    "over_hedged": len(over_hedged),
                    "total_positions": len(suggestions)
                }
                config_mgr.add_sync_history(summary)
        
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
                status_emoji = "✅" if s.status == "balanced" else "⚠️"
                with st.expander(f"{status_emoji} **{s.token}** - {s.status.upper().replace('_', ' ')}", expanded=(s.status != "balanced")):
                    col1, col2, col3 = st.columns(3)
                    col1.metric("LP Balance", f"{s.lp_balance:.6f}")
                    col2.metric("Short Balance", f"{s.short_balance:.6f}")
                    col3.metric("Diferença", f"{s.difference:+.6f} ({s.difference_pct:.2f}%)")
                
                    if s.action != "none":
                        action_text = "AUMENTAR" if s.action == "increase_short" else "DIMINUIR"
                        st.warning(f"➡️ **AÇÃO:** {action_text} SHORT em {s.adjustment_amount:.6f} {s.token}")
                    else:
                        st.success("✅ Posição balanceada - nenhuma ação necessária")
        
            # Action summary
            if under_hedged or over_hedged:
                st.markdown("---")
                st.subheader("📋 Resumo de Ações Necessárias")
            
                if under_hedged:
                    st.markdown("**🔺 AUMENTAR SHORT:**")
                    for s in under_hedged:
                        st.write(f"- {s.token}: +{s.adjustment_amount:.6f}")
            
                if over_hedged:
                    st.markdown("**🔻 DIMINUIR SHORT:**")
                    for s in over_hedged:
                        st.write(f"- {s.token}: -{s.adjustment_amount:.6f}")
                
                st.markdown("---")
                
                # Execution button
                hyperliquid_key = config.get("hyperliquid_private_key", "")
                
                if hyperliquid_key:
                    st.markdown("### ⚡ Execução Automática")
                    st.info("🚨 **ATENÇÃO:** Isso irá executar ordens reais na Hyperliquid!")
                    
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        if st.button("⚡ Executar Ajustes", type="primary", use_container_width=True):
                            st.session_state.confirm_execution = True
                    
                    # Confirmation dialog
                    if st.session_state.get('confirm_execution', False):
                        st.warning("⚠️ **CONFIRMAÇÃO NECESSÁRIA**")
                        st.write("Você está prestes a executar as seguintes operações:")
                        
                        # Show what will be executed
                        for s in under_hedged:
                            st.write(f"• **{s.token}**: SELL {s.adjustment_amount:.6f} (aumentar short)")
                        for s in over_hedged:
                            st.write(f"• **{s.token}**: BUY {s.adjustment_amount:.6f} (diminuir short)")
                        
                        col1, col2, col3 = st.columns([1, 1, 2])
                        with col1:
                            if st.button("✅ Confirmar e Executar", type="primary"):
                                # Execute trades
                                from hyperliquid_client import HyperliquidClient
                                
                                client = HyperliquidClient(
                                    wallet_address=wallet_address,
                                    private_key=hyperliquid_key
                                )
                                
                                if not client.can_execute:
                                    st.error("❌ Erro: Não foi possível inicializar cliente Hyperliquid. Verifique se o SDK está instalado.")
                                else:
                                    # Prepare adjustments
                                    adjustments = []
                                    for s in under_hedged:
                                        adjustments.append({
                                            "token": s.token,
                                            "action": "increase_short",
                                            "amount": s.adjustment_amount
                                        })
                                    for s in over_hedged:
                                        adjustments.append({
                                            "token": s.token,
                                            "action": "decrease_short",
                                            "amount": s.adjustment_amount
                                        })
                                    
                                    with st.spinner("🔄 Executando operações..."):
                                        results = client.execute_adjustments(adjustments)
                                    
                                    # Display results
                                    st.markdown("### 📋 Resultados da Execução")
                                    
                                    success_count = sum(1 for r in results if r['result'].success)
                                    total_count = len(results)
                                    
                                    if success_count == total_count:
                                        st.success(f"✅ Todas as {total_count} operações foram executadas com sucesso!")
                                    else:
                                        st.warning(f"⚠️ {success_count}/{total_count} operações executadas com sucesso")
                                    
                                    for r in results:
                                        result = r['result']
                                        status_emoji = "✅" if result.success else "❌"
                                        with st.expander(f"{status_emoji} {r['token']} - {r['action']}"):
                                            st.write(f"**Amount:** {r['amount']:.6f}")
                                            st.write(f"**Status:** {result.message}")
                                            if result.order_id:
                                                st.write(f"**Order ID:** {result.order_id}")
                                            if result.filled_size:
                                                st.write(f"**Filled Size:** {result.filled_size:.6f}")
                                            if result.avg_price:
                                                st.write(f"**Avg Price:** ${result.avg_price:.2f}")
                                    
                                    # Clear confirmation state
                                    st.session_state.confirm_execution = False
                                    
                                    # Suggest re-sync
                                    st.info("🔄 Recomenda-se sincronizar novamente para ver as posições atualizadas")
                        
                        with col2:
                            if st.button("❌ Cancelar"):
                                st.session_state.confirm_execution = False
                                st.rerun()
                else:
                    st.markdown("### ⚡ Execução Automática")
                    st.warning("⚠️ Configure a **Hyperliquid Private Key** na aba **Configuração** para habilitar a execução automática")
                    st.info("🛡️ **Modo Seguro:** Atualmente em modo somente análise (read-only)")
            else:
                st.success("🎉 Todas as posições estão balanceadas! Nenhuma ação necessária.")

# ==================== TAB 3: POSIÇÕES LP ====================
    with tab3:
        st.subheader("🏦 Posições LP (Liquidity Provider)")
    
    if 'portfolio_data' not in st.session_state:
        st.info("ℹ️ Sincronize os dados na aba **Dashboard** primeiro")
        pass
    
    data = st.session_state.portfolio_data
    lp_positions = data['lp_positions']
    
    if not lp_positions:
        st.info("ℹ️ Nenhuma posição LP encontrada")
    else:
        # Display positions
        for pos in lp_positions:
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                col1.write(f"**{pos.protocol}** ({pos.chain})")
                col2.write(pos.token_symbol)
                col3.write(f"{pos.balance:.6f}")
                col4.write(f"${pos.value:.2f}")
        
        st.markdown("---")
        
        # Aggregated balances
        st.subheader("📊 Balanços Agregados")
        for token, balance in sorted(data['lp_balances'].items()):
            col1, col2 = st.columns([1, 1])
            col1.write(f"**{token}**")
            col2.write(f"{balance:.6f}")
        
        # Perp positions
        st.markdown("---")
        st.subheader("📉 Posições Short (Hyperliquid)")
        
        perp_positions = data['perp_positions']
        
        if not perp_positions:
            st.info("ℹ️ Nenhuma posição perpétua encontrada")
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

# ==================== TAB 4: HISTÓRICO ====================
with tab4:
    st.subheader("📜 Histórico de Sincronizações")
    
    history = config_mgr.load_history()
    
    if not history:
        st.info("ℹ️ Nenhuma sincronização realizada ainda")
    else:
        st.caption(f"Total de sincronizações: {len(history)}")
        
        # Clear history button
        if st.button("🗑️ Limpar Histórico"):
            config_mgr.clear_history()
            st.success("✅ Histórico limpo")
            st.rerun()
        
        st.markdown("---")
        
        # Display history
        for entry in history:
            timestamp = entry.get("timestamp", "")
            summary = entry.get("summary", {})
            
            with st.expander(f"🕐 {timestamp[:19]}", expanded=False):
                col1, col2, col3, col4 = st.columns(4)
                
                col1.metric("💰 Net Worth", f"${summary.get('networth', 0):.2f}")
                col2.metric("✅ Balanceadas", summary.get('balanced', 0))
                col3.metric("⚠️ Sub-Hedge", summary.get('under_hedged', 0))
                col4.metric("⚠️ Sobre-Hedge", summary.get('over_hedged', 0))

# Footer
st.markdown("---")
st.caption(f"XCELFI LP Hedge V3 | Powered by Octav.fi API | Mode: Analysis (Read-Only)")
