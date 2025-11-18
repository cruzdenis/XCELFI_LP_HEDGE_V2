"""
XCELFI LP Hedge V3 - Streamlit Dashboard
Delta-Neutral Analysis using Octav.fi API
"""

import streamlit as st
import os
import threading
import time
from datetime import datetime, timedelta
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

# Background sync thread
def background_sync_worker():
    """Background thread that syncs data periodically"""
    while True:
        try:
            config = config_mgr.load_config()
            
            if not config:
                time.sleep(60)  # Wait 1 minute if no config
                continue
            
            auto_sync_enabled = config.get("auto_sync_enabled", False)
            
            if not auto_sync_enabled:
                time.sleep(60)  # Wait 1 minute if disabled
                continue
            
            # Check if sync is needed
            auto_sync_interval_hours = config.get("auto_sync_interval_hours", 1)
            last_sync = config_mgr.get_last_sync()
            
            should_sync = False
            if last_sync:
                last_sync_dt = datetime.fromisoformat(last_sync)
                now = datetime.now()
                time_since_sync = (now - last_sync_dt).total_seconds() / 3600
                should_sync = time_since_sync >= auto_sync_interval_hours
            else:
                should_sync = True  # First sync
            
            if should_sync:
                # Perform sync
                api_key = config.get("api_key")
                wallet_address = config.get("wallet_address")
                tolerance_pct = config.get("tolerance_pct", 5.0)
                
                if api_key and wallet_address:
                    client = OctavClient(api_key)
                    portfolio = client.get_portfolio(wallet_address)
                    
                    if portfolio:
                        lp_positions = client.extract_lp_positions(portfolio)
                        perp_positions = client.extract_perp_positions(portfolio)
                        
                        lp_balances = {}
                        for pos in lp_positions:
                            symbol = client.normalize_symbol(pos.token_symbol)
                            lp_balances[symbol] = lp_balances.get(symbol, 0) + pos.balance
                        
                        short_balances = {}
                        for pos in perp_positions:
                            if pos.size < 0:
                                symbol = client.normalize_symbol(pos.symbol)
                                short_balances[symbol] = short_balances.get(symbol, 0) + abs(pos.size)
                        
                        analyzer = DeltaNeutralAnalyzer(tolerance_pct=tolerance_pct)
                        suggestions = analyzer.compare_positions(lp_balances, short_balances)
                        
                        balanced = [s for s in suggestions if s.status == "balanced"]
                        under_hedged = [s for s in suggestions if s.status == "under_hedged"]
                        over_hedged = [s for s in suggestions if s.status == "over_hedged"]
                        
                        networth = float(portfolio.get("networth", "0"))
                        
                        summary = {
                            "networth": networth,
                            "balanced": len(balanced),
                            "under_hedged": len(under_hedged),
                            "over_hedged": len(over_hedged),
                            "total_positions": len(suggestions)
                        }
                        
                        config_mgr.add_sync_history(summary)
                        print(f"[BACKGROUND SYNC] Completed at {datetime.now().isoformat()}")
                        
                        # Auto-execute adjustments if enabled
                        auto_execute_enabled = config.get("auto_execute_enabled", False)
                        hyperliquid_private_key = config.get("hyperliquid_private_key")
                        
                        if auto_execute_enabled and hyperliquid_private_key and (under_hedged or over_hedged):
                            print(f"[AUTO-EXECUTE] Starting automatic execution...")
                            
                            try:
                                from hyperliquid_client import HyperliquidClient
                                hl_client = HyperliquidClient(wallet_address, hyperliquid_private_key)
                                
                                # Prepare adjustments
                                adjustments = []
                                for s in under_hedged:
                                    adjustments.append({
                                        'token': s.token,
                                        'action': 'increase_short',
                                        'amount': s.adjustment_amount
                                    })
                                for s in over_hedged:
                                    adjustments.append({
                                        'token': s.token,
                                        'action': 'decrease_short',
                                        'amount': s.adjustment_amount
                                    })
                                
                                # Execute adjustments
                                results = hl_client.execute_adjustments(adjustments)
                                
                                # Log each execution
                                for result in results:
                                    execution_data = {
                                        'token': result['token'],
                                        'action': result['action'],
                                        'amount': result['amount'],
                                        'order_value_usd': result.get('order_value_usd', 0),
                                        'success': result['result'].success,
                                        'message': result['result'].message,
                                        'order_id': result['result'].order_id,
                                        'filled_size': result['result'].filled_size,
                                        'avg_price': result['result'].avg_price,
                                        'auto_executed': True
                                    }
                                    config_mgr.add_execution_history(execution_data)
                                
                                success_count = sum(1 for r in results if r['result'].success)
                                print(f"[AUTO-EXECUTE] Completed: {success_count}/{len(results)} successful")
                                
                            except Exception as exec_error:
                                print(f"[AUTO-EXECUTE ERROR] {str(exec_error)}")
                                # Log failed execution
                                config_mgr.add_execution_history({
                                    'token': 'ALL',
                                    'action': 'auto_execute',
                                    'amount': 0,
                                    'success': False,
                                    'message': f"Auto-execution failed: {str(exec_error)}",
                                    'auto_executed': True
                                })
            
            # Sleep for 5 minutes before checking again
            time.sleep(300)
            
        except Exception as e:
            print(f"[BACKGROUND SYNC ERROR] {str(e)}")
            time.sleep(300)  # Wait 5 minutes on error

# Start background sync thread (only once)
if 'background_sync_started' not in st.session_state:
    sync_thread = threading.Thread(target=background_sync_worker, daemon=True)
    sync_thread.start()
    st.session_state.background_sync_started = True

# Keep-alive thread to prevent hibernation
def keep_alive_worker():
    """Keep the app alive by performing lightweight operations"""
    import requests
    while True:
        try:
            # Self-ping every 10 minutes
            time.sleep(600)  # 10 minutes
            
            # Try to get Railway URL from environment
            railway_url = os.environ.get('RAILWAY_PUBLIC_DOMAIN')
            if railway_url:
                try:
                    requests.get(f"https://{railway_url}", timeout=5)
                    print(f"[KEEP-ALIVE] Pinged at {datetime.now().isoformat()}")
                except:
                    pass
            else:
                # Just log to keep thread active
                print(f"[KEEP-ALIVE] Active at {datetime.now().isoformat()}")
                
        except Exception as e:
            print(f"[KEEP-ALIVE ERROR] {str(e)}")
            time.sleep(600)

# Start keep-alive thread (only once)
if 'keep_alive_started' not in st.session_state:
    keepalive_thread = threading.Thread(target=keep_alive_worker, daemon=True)
    keepalive_thread.start()
    st.session_state.keep_alive_started = True

# Header
st.markdown('<div class="main-header">🎯 XCELFI LP Hedge V3</div>', unsafe_allow_html=True)
st.markdown('<div class="last-sync">Delta-Neutral LP Hedge Dashboard</div>', unsafe_allow_html=True)

# Main tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["⚙️ Configuração", "📊 Dashboard", "🏬 Posições LP", "📜 Histórico", "📈 Execuções"])

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
            min_value=0.0,
            max_value=100.0,
            value=existing_config.get("tolerance_pct", 5.0) if existing_config else 5.0,
            step=0.5,
            help="Diferença percentual aceitável para considerar balanceado",
            key="config_tolerance"
        )
        
        st.markdown("### 🔄 Sincronização Automática")
        
        auto_sync_enabled = st.checkbox(
            "Ativar sincronização automática",
            value=existing_config.get("auto_sync_enabled", False) if existing_config else False,
            help="Sincroniza dados automaticamente em intervalos regulares",
            key="config_auto_sync_enabled"
        )
        
        auto_sync_interval = st.selectbox(
            "Intervalo de sincronização",
            options=[1, 2, 4, 6, 12, 24],
            index=[1, 2, 4, 6, 12, 24].index(existing_config.get("auto_sync_interval_hours", 1) if existing_config else 1),
            format_func=lambda x: f"{x} hora{'s' if x > 1 else ''}",
            help="Frequência de sincronização automática",
            disabled=not auto_sync_enabled,
            key="config_auto_sync_interval"
        )
        
        if auto_sync_enabled:
            st.info(f"🔄 Sincronização automática a cada {auto_sync_interval}h")
        
        st.markdown("### ⚡ Execução Automática")
        
        auto_execute_enabled = st.checkbox(
            "Ativar execução automática de ajustes",
            value=existing_config.get("auto_execute_enabled", False) if existing_config else False,
            help="Executa ajustes automaticamente após cada sincronização (requer Hyperliquid Private Key)",
            disabled=not existing_config.get("hyperliquid_private_key") if existing_config else True,
            key="config_auto_execute_enabled"
        )
        
        if auto_execute_enabled:
            st.warning("⚠️ Execução automática ATIVADA! Ordens serão executadas automaticamente.")
        else:
            st.info("🔒 Execução manual - você controla quando executar")
        
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
                config_mgr.save_config(
                    api_key, 
                    wallet, 
                    tolerance, 
                    hyperliquid_key,
                    auto_sync_enabled,
                    auto_sync_interval,
                    auto_execute_enabled
                )
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
    
    # Backup and Restore section
    st.subheader("💾 Backup & Restore")
    st.markdown("Faça backup de todas as suas configurações e histórico, ou restaure de um backup anterior.")
    
    col_backup1, col_backup2 = st.columns(2)
    
    with col_backup1:
        st.markdown("**📥 Download Backup**")
        if st.button("📥 Baixar Backup", use_container_width=True):
            backup_data = config_mgr.create_backup()
            
            if backup_data.get("config") or backup_data.get("history"):
                import json
                backup_json = json.dumps(backup_data, indent=2)
                
                # Create download button
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"xcelfi_backup_{timestamp}.json"
                
                st.download_button(
                    label="⬇️ Download Arquivo",
                    data=backup_json,
                    file_name=filename,
                    mime="application/json",
                    use_container_width=True
                )
                st.success("✅ Backup criado! Clique para baixar.")
            else:
                st.warning("⚠️ Nenhum dado para fazer backup")
    
    with col_backup2:
        st.markdown("**📤 Upload Backup**")
        uploaded_file = st.file_uploader(
            "Selecione arquivo de backup",
            type=["json"],
            help="Arquivo .json gerado pelo botão de backup",
            key="backup_uploader"
        )
        
        if uploaded_file is not None:
            try:
                import json
                backup_data = json.load(uploaded_file)
                
                # Show backup info
                backup_time = backup_data.get("backup_timestamp", "Unknown")
                st.info(f"📅 Backup de: {backup_time[:19]}")
                
                if st.button("🔄 Restaurar Backup", use_container_width=True, type="primary"):
                    success, message = config_mgr.restore_backup(backup_data)
                    
                    if success:
                        st.success(f"✅ {message}")
                        st.balloons()
                        st.info("🔄 Recarregue a página para ver as alterações")
                    else:
                        st.error(f"❌ {message}")
                        
            except Exception as e:
                st.error(f"❌ Erro ao ler arquivo: {str(e)}")
    
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
    
        # Auto-sync logic
        auto_sync_enabled = config.get("auto_sync_enabled", False)
        auto_sync_interval_hours = config.get("auto_sync_interval_hours", 1)
        
        # Check if auto-sync should trigger
        should_auto_sync = False
        if auto_sync_enabled:
            last_sync = config_mgr.get_last_sync()
            if last_sync:
                from datetime import datetime, timedelta
                last_sync_dt = datetime.fromisoformat(last_sync)
                now = datetime.now()
                time_since_sync = (now - last_sync_dt).total_seconds() / 3600  # hours
                should_auto_sync = time_since_sync >= auto_sync_interval_hours
            else:
                should_auto_sync = True  # First sync
        
        # Last sync info with auto-sync status
        col_sync1, col_sync2 = st.columns([3, 1])
        with col_sync1:
            last_sync = config_mgr.get_last_sync()
            if last_sync:
                st.markdown(f'<div class="last-sync">Última sincronização: {last_sync[:19]}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="last-sync">Nenhuma sincronização realizada</div>', unsafe_allow_html=True)
        
        with col_sync2:
            if auto_sync_enabled:
                st.markdown(f'<div class="last-sync">🔄 Auto-sync: {auto_sync_interval_hours}h</div>', unsafe_allow_html=True)
    
        # Sync button
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            sync_now = st.button("🔄 Sincronizar Agora", use_container_width=True, type="primary")
        
        # Trigger auto-sync if needed (without rerun to avoid loop)
        if should_auto_sync and not sync_now:
            sync_now = True
            st.info(f"🔄 Sincronização automática em andamento... ({auto_sync_interval_hours}h)")
    
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
                        if should_auto_sync:
                            st.success("✅ Sincronização automática concluída!")
                        else:
                            st.success("✅ Dados sincronizados com sucesso!")
                    else:
                        st.error("❌ Erro ao carregar dados")
                        st.stop()  # Stop immediately after sync failure
                except Exception as e:
                    st.error(f"❌ Erro: {str(e)}")
                    st.stop()  # Stop immediately after exception
    
        # Check if data exists
        if 'portfolio_data' not in st.session_state:
            st.info("ℹ️ Clique em **Sincronizar Agora** para carregar os dados")
            st.stop()  # Stop execution here
    
        data = st.session_state.portfolio_data
    
        # Display net worth
        portfolio = data['portfolio']
        networth = portfolio.get("networth", "0")
    
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("💰 Net Worth", f"${float(networth):.2f}")
        with col2:
            st.metric("🏬 Posições LP", len(data['lp_positions']))
        with col3:
            st.metric("📉 Posições Short", len([p for p in data['perp_positions'] if p.size < 0]))
    
        st.markdown("---")
        
        # NAV Evolution Chart
        st.subheader("📈 Evolução do Net Worth")
        
        history = config_mgr.load_history()
        
        if len(history) > 1:
            import plotly.graph_objects as go
            from datetime import datetime, timedelta
            
            # Period filter
            col_filter1, col_filter2 = st.columns([3, 1])
            with col_filter2:
                period_filter = st.selectbox(
                    "Período",
                    options=["1d", "7d", "30d", "90d", "365d", "total"],
                    format_func=lambda x: {
                        "1d": "1 dia",
                        "7d": "7 dias",
                        "30d": "30 dias",
                        "90d": "90 dias",
                        "365d": "365 dias",
                        "total": "Total"
                    }[x],
                    index=2,  # Default to 30 days
                    key="nav_period_filter"
                )
            
            # Filter history by period
            now = datetime.now()
            if period_filter != "total":
                days = int(period_filter[:-1])
                cutoff_date = now - timedelta(days=days)
                filtered_history = [
                    h for h in history 
                    if datetime.fromisoformat(h["timestamp"]) >= cutoff_date
                ]
            else:
                filtered_history = history
            
            if len(filtered_history) > 0:
                # Extract data
                timestamps = [datetime.fromisoformat(h["timestamp"]) for h in filtered_history]
                networth_values = [h["summary"].get("networth", 0) for h in filtered_history]
                
                # Reverse to show oldest first
                timestamps.reverse()
                networth_values.reverse()
                
                # Create chart
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=timestamps,
                    y=networth_values,
                    mode='lines+markers',
                    name='Net Worth',
                    line=dict(color='#1f77b4', width=2),
                    marker=dict(size=6)
                ))
                
                fig.update_layout(
                    title=None,
                    xaxis_title="Data",
                    yaxis_title="Net Worth (USD)",
                    hovermode='x unified',
                    height=400,
                    margin=dict(l=0, r=0, t=20, b=0)
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Stats
                if len(networth_values) > 1:
                    first_value = networth_values[0]
                    last_value = networth_values[-1]
                    change = last_value - first_value
                    change_pct = (change / first_value * 100) if first_value > 0 else 0
                    
                    col_stat1, col_stat2, col_stat3 = st.columns(3)
                    with col_stat1:
                        st.metric("Início do Período", f"${first_value:,.2f}")
                    with col_stat2:
                        st.metric("Fim do Período", f"${last_value:,.2f}")
                    with col_stat3:
                        st.metric("Variação", f"${change:+,.2f}", f"{change_pct:+.2f}%")
            else:
                st.info(f"ℹ️ Nenhum dado disponível para o período selecionado")
        else:
            st.info("ℹ️ Sincronize mais vezes para visualizar o gráfico de evolução")
        
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
        
            # Check if trigger is activated (any position exceeds tolerance)
            trigger_activated = any(s.difference_pct > tolerance_pct for s in suggestions)
            
            if trigger_activated:
                st.warning("⚡ **GATILHO ACIONADO!** Pelo menos uma posição excedeu a tolerância de {}%. **TODAS as posições serão ajustadas** para rebalanceamento completo.".format(tolerance_pct))
            else:
                st.success("✅ Todas as posições estão dentro da tolerância de {}%".format(tolerance_pct))
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("✅ Balanceadas", len(balanced))
            with col2:
                st.metric("⚠️ Sub-Hedge", len(under_hedged))
            with col3:
                st.metric("⚠️ Sobre-Hedge", len(over_hedged))
        
            st.markdown("---")
        
            # Fetch current prices for USD conversion
            token_prices = {}
            try:
                if config_mgr.config.get('hyperliquid_private_key'):
                    from hyperliquid_client import HyperliquidClient
                    hl_client = HyperliquidClient(
                        wallet_address=config_mgr.config.get('wallet_address'),
                        private_key=config_mgr.config.get('hyperliquid_private_key')
                    )
                    all_mids = hl_client.exchange.info.all_mids()
                    for token in [s.token for s in suggestions]:
                        if token in all_mids:
                            token_prices[token] = float(all_mids[token])
            except:
                pass
            
            # Detailed analysis
            for s in suggestions:
                status_emoji = "✅" if s.status == "balanced" else "⚠️"
                with st.expander(f"{status_emoji} **{s.token}** - {s.status.upper().replace('_', ' ')}", expanded=(s.status != "balanced")):
                    col1, col2, col3 = st.columns(3)
                    
                    # Get price for USD conversion
                    price = token_prices.get(s.token, 0)
                    lp_usd = s.lp_balance * price
                    short_usd = s.short_balance * price
                    diff_usd = s.difference * price
                    
                    # Display with USD values
                    if price > 0:
                        col1.metric("LP Balance", f"{s.lp_balance:.6f}", f"${lp_usd:.2f}")
                        col2.metric("Short Balance", f"{s.short_balance:.6f}", f"${short_usd:.2f}")
                        col3.metric("Diferença", f"{s.difference:+.6f} ({s.difference_pct:.2f}%)", f"${diff_usd:+.2f}")
                    else:
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
                                    skipped_count = sum(1 for r in results if not r['result'].success and 'below minimum' in r['result'].message)
                                    failed_count = sum(1 for r in results if not r['result'].success and 'below minimum' not in r['result'].message)
                                    total_count = len(results)
                                    
                                    if success_count == total_count:
                                        st.success(f"✅ Todas as {total_count} operações foram executadas com sucesso!")
                                    elif skipped_count > 0:
                                        st.warning(f"⚠️ {success_count}/{total_count} operações executadas com sucesso")
                                        st.info(f"ℹ️ {skipped_count} operações ignoradas (valor < $10 USD)")
                                    else:
                                        st.warning(f"⚠️ {success_count}/{total_count} operações executadas com sucesso")
                                    
                                    for r in results:
                                        result = r['result']
                                        order_value = r.get('order_value_usd', 0)
                                        
                                        # Determine status emoji
                                        if result.success:
                                            status_emoji = "✅"
                                        elif 'below minimum' in result.message:
                                            status_emoji = "⏸️"  # Skipped
                                        else:
                                            status_emoji = "❌"  # Failed
                                        
                                        with st.expander(f"{status_emoji} {r['token']} - {r['action']}"):
                                            st.write(f"**Amount:** {r['amount']:.6f}")
                                            st.write(f"**Order Value:** ${order_value:.2f} USD")
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
    else:
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
        if st.button("🗑️ Limpar Histórico", key="clear_sync_history"):
            config_mgr.clear_history()
            st.success("✅ Histórico limpo")
            st.rerun()
        
        st.markdown("---")
        
        # Display history
        for idx, entry in enumerate(history):
            timestamp = entry.get("timestamp", "")
            summary = entry.get("summary", {})
            
            with st.expander(f"🕐 {timestamp[:19]}", expanded=False):
                col1, col2, col3, col4 = st.columns(4)
                
                col1.metric("💰 Net Worth", f"${summary.get('networth', 0):.2f}")
                col2.metric("✅ Balanceadas", summary.get('balanced', 0))
                col3.metric("⚠️ Sub-Hedge", summary.get('under_hedged', 0))
                col4.metric("⚠️ Sobre-Hedge", summary.get('over_hedged', 0))
                
                # Delete button
                if st.button("❌ Excluir esta entrada", key=f"del_sync_{idx}", use_container_width=True):
                    if config_mgr.delete_sync_entry(idx):
                        st.success("✅ Entrada excluída")
                        st.rerun()
                    else:
                        st.error("❌ Erro ao excluir entrada")

# ==================== TAB 5: EXECUÇÕES ====================
with tab5:
    st.subheader("📈 Histórico de Execuções")
    
    execution_history = config_mgr.load_execution_history()
    
    if not execution_history:
        st.info("ℹ️ Nenhuma execução registrada ainda")
    else:
        st.caption(f"Total de execuções: {len(execution_history)}")
        
        # Filters
        col_filter1, col_filter2, col_filter3 = st.columns(3)
        
        with col_filter1:
            filter_status = st.selectbox(
                "Status",
                options=["Todos", "Sucesso", "Falha", "Ignorado"],
                key="exec_filter_status"
            )
        
        with col_filter2:
            all_tokens = list(set([e['execution'].get('token', 'N/A') for e in execution_history]))
            filter_token = st.selectbox(
                "Token",
                options=["Todos"] + sorted(all_tokens),
                key="exec_filter_token"
            )
        
        with col_filter3:
            filter_auto = st.selectbox(
                "Tipo",
                options=["Todos", "Automático", "Manual"],
                key="exec_filter_auto"
            )
        
        # Clear history button
        col_clear1, col_clear2 = st.columns([1, 3])
        with col_clear1:
            if st.button("🗑️ Limpar Histórico", key="clear_execution_history"):
                config_mgr.clear_execution_history()
                st.success("✅ Histórico de execuções limpo")
                st.rerun()
        
        st.markdown("---")
        
        # Filter executions
        filtered_executions = execution_history
        
        if filter_status != "Todos":
            if filter_status == "Sucesso":
                filtered_executions = [e for e in filtered_executions if e['execution'].get('success', False)]
            elif filter_status == "Falha":
                filtered_executions = [e for e in filtered_executions if not e['execution'].get('success', False) and 'below minimum' not in e['execution'].get('message', '')]
            elif filter_status == "Ignorado":
                filtered_executions = [e for e in filtered_executions if 'below minimum' in e['execution'].get('message', '')]
        
        if filter_token != "Todos":
            filtered_executions = [e for e in filtered_executions if e['execution'].get('token') == filter_token]
        
        if filter_auto != "Todos":
            if filter_auto == "Automático":
                filtered_executions = [e for e in filtered_executions if e['execution'].get('auto_executed', False)]
            else:
                filtered_executions = [e for e in filtered_executions if not e['execution'].get('auto_executed', False)]
        
        st.caption(f"Mostrando {len(filtered_executions)} de {len(execution_history)} execuções")
        
        # Display executions
        # Need to track original indices for deletion
        for filtered_idx, entry in enumerate(filtered_executions):
            # Find original index in full history
            original_idx = execution_history.index(entry)
            timestamp = entry.get("timestamp", "")
            execution = entry.get("execution", {})
            
            # Determine status emoji
            if execution.get('success'):
                status_emoji = "✅"
                status_color = "green"
            elif 'below minimum' in execution.get('message', ''):
                status_emoji = "⏸️"
                status_color = "blue"
            else:
                status_emoji = "❌"
                status_color = "red"
            
            # Auto/Manual badge
            exec_type = "🤖 AUTO" if execution.get('auto_executed', False) else "👤 MANUAL"
            
            with st.expander(f"{status_emoji} {exec_type} | {execution.get('token', 'N/A')} - {execution.get('action', 'N/A')} | {timestamp[:19]}", expanded=False):
                col1, col2, col3, col4 = st.columns(4)
                
                col1.metric("Token", execution.get('token', 'N/A'))
                col2.metric("Ação", execution.get('action', 'N/A').replace('_', ' ').title())
                col3.metric("Amount", f"{execution.get('amount', 0):.6f}")
                col4.metric("Valor USD", f"${execution.get('order_value_usd', 0):.2f}")
                
                st.markdown(f"**Status:** {execution.get('message', 'N/A')}")
                
                if execution.get('order_id'):
                    st.markdown(f"**Order ID:** `{execution.get('order_id')}`")
                
                if execution.get('filled_size'):
                    st.markdown(f"**Filled Size:** {execution.get('filled_size'):.6f}")
                
                if execution.get('avg_price'):
                    st.markdown(f"**Avg Price:** ${execution.get('avg_price'):.2f}")
                
                # Delete button
                if st.button("❌ Excluir esta entrada", key=f"del_exec_{original_idx}_{filtered_idx}", use_container_width=True):
                    if config_mgr.delete_execution_entry(original_idx):
                        st.success("✅ Entrada excluída")
                        st.rerun()
                    else:
                        st.error("❌ Erro ao excluir entrada")

# Footer
st.markdown("---")
st.caption(f"XCELFI LP Hedge V3 | Powered by Octav.fi API | Mode: Analysis (Read-Only)")
