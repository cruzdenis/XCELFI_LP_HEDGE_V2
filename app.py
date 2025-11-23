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
                    
                    # First sync
                    portfolio = client.get_portfolio(wallet_address)
                    
                    if portfolio:
                        # Wait 5 seconds for protocols to update (especially Revert Finance)
                        time.sleep(5)
                        
                        # Second sync for validation
                        portfolio = client.get_portfolio(wallet_address)
                    
                    if portfolio:
                        lp_positions = client.extract_lp_positions(portfolio)
                        perp_positions = client.extract_perp_positions(portfolio)
                        
                        # Filter LP positions by enabled protocols
                        enabled_protocols = config.get("enabled_protocols", ["Revert", "Uniswap3", "Uniswap4", "Dhedge"])
                        filtered_lp_positions = [
                            pos for pos in lp_positions 
                            if any(proto.lower() in pos.protocol.lower() for proto in enabled_protocols)
                        ]
                        
                        lp_balances = {}
                        for pos in filtered_lp_positions:
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
        
        st.markdown("### 🎯 Seleção de Protocolos")
        st.markdown("Escolha quais protocolos incluir nos cálculos de hedge e alocação de capital.")
        
        # Get available protocols from last sync (if any)
        available_protocols = ["Revert", "Uniswap3", "Uniswap4", "Dhedge", "Aerodrome", "Curve", "Sushiswap", "Balancer", "Velodrome"]
        
        # Load saved protocol preferences
        enabled_protocols = existing_config.get("enabled_protocols", ["Revert", "Uniswap3", "Uniswap4", "Dhedge"]) if existing_config else ["Revert", "Uniswap3", "Uniswap4", "Dhedge"]
        
        # Multi-select for protocols
        enabled_protocols = st.multiselect(
            "Protocolos Habilitados",
            options=available_protocols,
            default=enabled_protocols,
            help="Selecione os protocolos que deseja incluir nos cálculos. Protocolos não selecionados serão ignorados."
        )
        
        st.caption(f"✅ {len(enabled_protocols)} protocolo(s) selecionado(s)")
        
        with st.expander("ℹ️ Sobre a Seleção de Protocolos"):
            st.markdown("""
            **Por que selecionar protocolos?**
            
            - **Excluir posições pequenas**: Ignore protocolos com valores insignificantes
            - **Focar em protocolos principais**: Considere apenas LPs relevantes
            - **Testes**: Desabilite temporariamente um protocolo para análise
            
            **Impacto:**
            - Cálculos de hedge consideram apenas protocolos selecionados
            - Alocação de capital filtra por protocolos habilitados
            - Dashboard mostra todos, mas destaca os selecionados
            
            **Recomendação:**
            - Mantenha todos os protocolos com valor significativo habilitados
            - Desabilite apenas protocolos com dust/valores mínimos
            """)
        
        st.markdown("---")
        
        st.markdown("### 💼 Alocação de Capital")
        
        st.markdown("🎯 **Zona Ideal de Alocação de Capital (Faixa 70-90%)**")
        st.markdown("""
        **Nova Lógica:**
        - 🟢 **ZONA IDEAL**: 70-90% em LPs (balanço entre rentabilidade e segurança)
        - 🔴 **RISCO ALTO**: >90% em LPs (risco de liquidação)
        - 🟡 **RISCO MÉDIO**: <70% em LPs (perda de rentabilidade)
        """)
        
        st.markdown("---")
        
        col_min, col_target, col_max = st.columns(3)
        
        with col_min:
            lp_min_ideal = st.slider(
                "LPs Mínimo Ideal (%)",
                min_value=50.0,
                max_value=80.0,
                value=existing_config.get("lp_min_ideal", 70.0) if existing_config else 70.0,
                step=1.0,
                help="Mínimo de LPs para manter rentabilidade adequada",
                key="config_lp_min_ideal"
            )
        
        with col_target:
            lp_target = st.slider(
                "LPs Target (Centro) (%)",
                min_value=60.0,
                max_value=90.0,
                value=existing_config.get("lp_target", 80.0) if existing_config else 80.0,
                step=1.0,
                help="Target ideal no centro da faixa",
                key="config_lp_target"
            )
        
        with col_max:
            lp_max_ideal = st.slider(
                "LPs Máximo Ideal (%)",
                min_value=80.0,
                max_value=95.0,
                value=existing_config.get("lp_max_ideal", 90.0) if existing_config else 90.0,
                step=1.0,
                help="Máximo de LPs antes de risco de liquidação",
                key="config_lp_max_ideal"
            )
        
        # Validate range
        if not (lp_min_ideal < lp_target < lp_max_ideal):
            st.error("⚠️ Erro: Mínimo < Target < Máximo")
        
        # Remove old rebalancing_threshold_pct slider (not needed anymore)
        # Keep it for backward compatibility in config
        rebalancing_threshold_pct = 40.0  # Not used in new logic
        
        with st.expander("ℹ️ Explicação da Faixa Ideal"):
            st.markdown(f"""
            **Como Funciona a Nova Lógica:**
            
            **Faixa Ideal Configurada:** {lp_min_ideal:.0f}% - {lp_max_ideal:.0f}% em LPs
            **Target (Centro):** {lp_target:.0f}%
            
            **Níveis de Risco:**
            
            1. 🟢 **ZONA IDEAL** ({lp_min_ideal:.0f}-{lp_max_ideal:.0f}%)
               - Balanço perfeito entre rentabilidade e segurança
               - Sistema opera com eficiência máxima
               - Margem adequada na Hyperliquid
            
            2. 🔴 **RISCO ALTO - Liquidação** (>{lp_max_ideal:.0f}%)
               - Margem operacional insuficiente
               - Risco de liquidação em movimentos rápidos
               - **REBALANCEAMENTO IMEDIATO NECESSÁRIO**
            
            3. 🟡 **RISCO MÉDIO - Rentabilidade** (<{lp_min_ideal:.0f}%)
               - Capital subutilizado em LPs
               - Perda de potencial de rentabilidade
               - **REBALANCEAMENTO RECOMENDADO**
            
            **Recomendações:**
            - Mínimo: 70% (garante rentabilidade)
            - Target: 80% (balanço ideal)
            - Máximo: 90% (margem de segurança)
            """)
        
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
                    auto_execute_enabled,
                    lp_min_ideal,
                    lp_target,
                    lp_max_ideal,
                    enabled_protocols
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
    
    # Deposit/Withdrawal Management section
    st.subheader("💰 Gestão de Depósitos/Saques")
    st.markdown("Registre depósitos e saques para calcular a rentabilidade real (sistema de cotas).")
    
    col_trans1, col_trans2 = st.columns(2)
    
    with col_trans1:
        st.markdown("**➕ Adicionar Transação**")
        trans_type = st.selectbox(
            "Tipo",
            options=["deposit", "withdrawal"],
            format_func=lambda x: "💵 Depósito" if x == "deposit" else "💸 Saque",
            key="trans_type"
        )
        trans_amount = st.number_input(
            "Valor (USD)",
            min_value=0.01,
            value=100.0,
            step=10.0,
            key="trans_amount"
        )
        trans_desc = st.text_input(
            "Descrição (opcional)",
            placeholder="Ex: Depósito inicial",
            key="trans_desc"
        )
        
        # Custom date option
        use_custom_date = st.checkbox(
            "Usar data customizada (para transações retroativas)",
            value=False,
            key="use_custom_date"
        )
        
        trans_date = None
        if use_custom_date:
            from datetime import date, time
            
            col_date, col_time = st.columns(2)
            with col_date:
                selected_date = st.date_input(
                    "Data",
                    value=date.today(),
                    key="trans_date"
                )
            with col_time:
                selected_time = st.time_input(
                    "Hora",
                    value=time(12, 0),
                    key="trans_time"
                )
            
            # Combine date and time
            from datetime import datetime
            trans_datetime = datetime.combine(selected_date, selected_time)
            trans_date = trans_datetime.isoformat()
        
        if st.button("➕ Adicionar Transação", use_container_width=True, type="primary", key="add_trans"):
            config_mgr.add_transaction(trans_type, trans_amount, trans_desc, trans_date)
            date_info = f" ({trans_date[:10]})" if trans_date else ""
            st.success(f"✅ Transação adicionada: ${trans_amount:.2f}{date_info}")
            st.info("🔄 Recarregue a página para ver a transação na lista")
    
    with col_trans2:
        st.markdown("**📋 Transações Recentes**")
        transactions = config_mgr.load_transactions()
        
        if transactions:
            # Show last 5 transactions
            for i, trans in enumerate(transactions[-5:][::-1]):
                trans_time = trans['timestamp'][:19]
                trans_type_icon = "💵" if trans['type'] == 'deposit' else "💸"
                trans_amount = trans['amount_usd']
                trans_desc = trans.get('description', '')
                
                st.text(f"{trans_type_icon} ${trans_amount:.2f} - {trans_time}")
                if trans_desc:
                    st.caption(trans_desc)
            
            if len(transactions) > 5:
                st.caption(f"... e mais {len(transactions) - 5} transações")
            
            # Clear button
            if st.button("🗑️ Limpar Transações", use_container_width=True, key="clear_trans"):
                config_mgr.clear_transactions()
                st.success("✅ Transações limpas!")
                st.info("🔄 Recarregue a página para atualizar a lista")
        else:
            st.info("ℹ️ Nenhuma transação registrada")
    
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
        
            # Filter LP positions by enabled protocols
            enabled_protocols = config.get("enabled_protocols", ["Revert", "Uniswap3", "Uniswap4", "Dhedge"])
            filtered_lp_positions = [
                pos for pos in lp_positions 
                if any(proto.lower() in pos.protocol.lower() for proto in enabled_protocols)
            ]
            
            # Aggregate balances (using filtered positions)
            lp_balances = {}
            for pos in filtered_lp_positions:
                symbol = client.normalize_symbol(pos.token_symbol)
                lp_balances[symbol] = lp_balances.get(symbol, 0) + pos.balance
        
            short_balances = {}
            for pos in perp_positions:
                if pos.size < 0:
                    symbol = client.normalize_symbol(pos.symbol)
                    short_balances[symbol] = short_balances.get(symbol, 0) + abs(pos.size)
        
            return {
                'portfolio': portfolio,
                'lp_positions': lp_positions,  # All positions (for display)
                'lp_positions_filtered': filtered_lp_positions,  # Filtered positions (for calculations)
                'perp_positions': perp_positions,
                'lp_balances': lp_balances,  # Based on filtered positions
                'short_balances': short_balances,
                'enabled_protocols': enabled_protocols
            }
    
        # Initialize session state for data
        if 'portfolio_data' not in st.session_state or sync_now:
            # Double sync with 5-second delay for protocol data validation
            with st.spinner("🔄 Sincronizando dados do Octav.fi (1ª tentativa)..."):
                try:
                    # First sync
                    data = load_portfolio_data()
                    if not data:
                        st.error("❌ Erro ao carregar dados na 1ª sincronização")
                        st.stop()
                    
                    st.info("⏳ Aguardando 5 segundos para validação de todos os protocolos (especialmente Revert Finance)...")
                    
                except Exception as e:
                    st.error(f"❌ Erro na 1ª sincronização: {str(e)}")
                    st.stop()
            
            # Wait 5 seconds for protocols to update
            time.sleep(5)
            
            # Second sync for validation
            with st.spinner("🔄 Sincronizando dados do Octav.fi (2ª tentativa - validação)..."):
                try:
                    # Second sync to capture all protocols
                    data = load_portfolio_data()
                    if data:
                        st.session_state.portfolio_data = data
                        st.session_state.last_sync_time = datetime.now().isoformat()
                        if should_auto_sync:
                            st.success("✅ Sincronização automática concluída com dupla validação!")
                        else:
                            st.success("✅ Dados sincronizados com sucesso! (Dupla validação realizada)")
                    else:
                        st.error("❌ Erro ao carregar dados na 2ª sincronização")
                        st.stop()
                except Exception as e:
                    st.error(f"❌ Erro na 2ª sincronização: {str(e)}")
                    st.stop()
    
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
        
        # ==================== CAPITAL ALLOCATION SECTION ====================
        st.subheader("💼 Alocação de Capital por Protocolo")
        
        # Import modules
        from capital_allocation_analyzer import CapitalAllocationAnalyzer
        from extract_protocol_balances import extract_protocol_balances, get_wallet_balance
        import plotly.graph_objects as go
        
        # Get capital allocation settings (new range-based logic)
        lp_min_ideal = config.get("lp_min_ideal", 70.0)
        lp_target = config.get("lp_target", 80.0)
        lp_max_ideal = config.get("lp_max_ideal", 90.0)
        
        # Extract protocol balances
        protocol_balances = extract_protocol_balances(portfolio)
        wallet_balance = get_wallet_balance(portfolio)
        
        # Analyze allocation
        cap_analyzer = CapitalAllocationAnalyzer(
            lp_min_ideal=lp_min_ideal,
            lp_max_ideal=lp_max_ideal,
            lp_target=lp_target
        )
        
        allocation_status = cap_analyzer.analyze_allocation(
            protocol_balances=protocol_balances,
            wallet_balance=0.0  # Wallet is already included in protocol_balances
        )
        
        # Display allocation metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "💰 Capital Total",
                f"${allocation_status.total_capital:,.2f}"
            )
        
        with col2:
            # Determine color based on risk level
            if allocation_status.lp_percentage >= lp_min_ideal and allocation_status.lp_percentage <= lp_max_ideal:
                lp_color = "normal"  # Green - in ideal range
            else:
                lp_color = "inverse"  # Red - out of range
            
            st.metric(
                "🏬 LPs",
                f"${allocation_status.lp_total:,.2f}",
                delta=f"{allocation_status.lp_percentage:.1f}% (ideal: {lp_min_ideal:.0f}-{lp_max_ideal:.0f}%)",
                delta_color=lp_color
            )
        
        with col3:
            # Hyperliquid is inverse of LP
            hyperliquid_min_ideal = 100 - lp_max_ideal
            hyperliquid_max_ideal = 100 - lp_min_ideal
            
            if allocation_status.hyperliquid_percentage >= hyperliquid_min_ideal and allocation_status.hyperliquid_percentage <= hyperliquid_max_ideal:
                hl_color = "normal"
            else:
                hl_color = "inverse"
            
            st.metric(
                "⚡ Hyperliquid",
                f"${allocation_status.hyperliquid_total:,.2f}",
                delta=f"{allocation_status.hyperliquid_percentage:.1f}% (ideal: {hyperliquid_min_ideal:.0f}-{hyperliquid_max_ideal:.0f}%)",
                delta_color=hl_color
            )
        
        with col4:
            st.metric(
                "💵 Wallet (Idle)",
                f"${allocation_status.wallet_total:,.2f}",
                delta=f"{allocation_status.wallet_percentage:.1f}%"
            )
        
        # Display risk level and rebalancing alert
        st.markdown("---")
        st.markdown("#### 🎯 Status de Alocação")
        
        # Show risk description
        st.info(allocation_status.risk_description)
        
        # Display rebalancing alert if needed
        if allocation_status.needs_rebalancing:
            # Use different alert types based on risk level
            from capital_allocation_analyzer import RiskLevel
            
            if allocation_status.risk_level == RiskLevel.HIGH_LIQUIDATION:
                st.error(allocation_status.rebalancing_alert)
            else:  # MEDIUM_PROFITABILITY
                st.warning(allocation_status.rebalancing_alert)
            
            if allocation_status.rebalancing_suggestion:
                st.info(f"💡 **Sugestão de Rebalanceamento:**\n\n{allocation_status.rebalancing_suggestion}")
                st.info("⚠️ **ATENÇÃO:** Esta é uma operação manual. Transfira fundos entre protocolos conforme sugerido.")
        else:
            st.success(allocation_status.rebalancing_alert)
        
        # Create two columns: pie chart and protocol breakdown
        col_chart, col_table = st.columns([1, 1])
        
        with col_chart:
            st.markdown("#### 📊 Distribuição de Capital")
            
            # Prepare data for pie chart
            if allocation_status.protocol_balances:
                labels = [pb.protocol_name for pb in allocation_status.protocol_balances]
                values = [pb.usd_value for pb in allocation_status.protocol_balances]
                percentages = [pb.percentage for pb in allocation_status.protocol_balances]
                
                # Color mapping
                colors = []
                for pb in allocation_status.protocol_balances:
                    if "hyperliquid" in pb.protocol_name.lower():
                        colors.append("#FF6B6B")  # Red for Hyperliquid
                    elif "wallet" in pb.protocol_name.lower():
                        colors.append("#95A5A6")  # Gray for wallet
                    else:
                        colors.append("#4ECDC4")  # Teal for LPs
                
                # Create pie chart
                fig = go.Figure(data=[go.Pie(
                    labels=labels,
                    values=values,
                    hole=0.4,
                    marker=dict(colors=colors),
                    textinfo='label+percent',
                    textposition='outside',
                    hovertemplate='<b>%{label}</b><br>$%{value:,.2f}<br>%{percent}<extra></extra>'
                )])
                
                fig.update_layout(
                    showlegend=True,
                    height=400,
                    margin=dict(t=20, b=20, l=20, r=20)
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Sem dados de protocolo para exibir")
        
        with col_table:
            st.markdown("#### 📋 Detalhamento por Protocolo")
            
            if allocation_status.protocol_balances:
                # Create table data
                table_data = []
                for pb in allocation_status.protocol_balances:
                    # Add emoji based on protocol type
                    if "hyperliquid" in pb.protocol_name.lower():
                        emoji = "⚡"
                    elif "wallet" in pb.protocol_name.lower():
                        emoji = "💵"
                    elif "uniswap" in pb.protocol_name.lower():
                        emoji = "🦄"
                    elif "revert" in pb.protocol_name.lower():
                        emoji = "🔄"
                    else:
                        emoji = "🏦"
                    
                    table_data.append({
                        "Protocolo": f"{emoji} {pb.protocol_name}",
                        "Valor USD": f"${pb.usd_value:,.2f}",
                        "Percentual": f"{pb.percentage:.1f}%"
                    })
                
                # Display as dataframe
                import pandas as pd
                df = pd.DataFrame(table_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("Sem dados de protocolo para exibir")
        
        # Display target allocation info
        with st.expander("ℹ️ Sobre a Alocação de Capital"):
            st.markdown(f"""
            **Estratégia de Alocação (Nova Lógica):**
            
            **Faixa Ideal Configurada:** {lp_min_ideal:.0f}% - {lp_max_ideal:.0f}% em LPs
            **Target (Centro):** {lp_target:.0f}%
            
            **Por que essa faixa?**
            
            - **Mínimo {lp_min_ideal:.0f}%**: Garante rentabilidade adequada
              - Abaixo disso: Capital subutilizado
              - Sistema perde efetividade operacional
              
            - **Target {lp_target:.0f}%**: Balanço ideal entre rentabilidade e segurança
              - Centro da faixa ideal
              - Buffer dos dois lados
              
            - **Máximo {lp_max_ideal:.0f}%**: Margem de segurança antes de risco de liquidação
              - Acima disso: Margem insuficiente na Hyperliquid
              - Risco de liquidação em movimentos rápidos
            
            **Configuração:**
            - Ajuste a faixa ideal na aba "⚙️ Configuração"
            - Valores recomendados: Mínimo 70%, Target 80%, Máximo 90%
            """)
        
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
        
        # Quota Evolution Chart
        st.subheader("📈 Evolução da Cota (Rentabilidade Real)")
        
        transactions = config_mgr.load_transactions()
        
        if transactions:
            from quota_calculator import QuotaCalculator
            
            quota_calc = QuotaCalculator(initial_quota_value=1.0)
            quota_history = quota_calc.calculate_quota_history(history, transactions)
            
            if len(quota_history) > 1:
                import plotly.graph_objects as go
                
                # Create quota evolution chart
                timestamps = [datetime.fromisoformat(q['timestamp']) for q in quota_history]
                quota_values = [q['quota_value'] for q in quota_history]
                
                fig_quota = go.Figure()
                
                fig_quota.add_trace(go.Scatter(
                    x=timestamps,
                    y=quota_values,
                    mode='lines+markers',
                    name='Valor da Cota',
                    line=dict(color='#00D9FF', width=3),
                    marker=dict(size=6),
                    hovertemplate='<b>%{x}</b><br>Cota: $%{y:.4f}<extra></extra>'
                ))
                
                # Add reference line at $1.00
                fig_quota.add_hline(
                    y=1.0,
                    line_dash="dash",
                    line_color="gray",
                    annotation_text="Valor Inicial ($1.00)",
                    annotation_position="right"
                )
                
                fig_quota.update_layout(
                    title="Valor da Cota ao Longo do Tempo",
                    xaxis_title="Data",
                    yaxis_title="Valor da Cota (USD)",
                    hovermode='x unified',
                    template='plotly_dark',
                    height=400
                )
                
                st.plotly_chart(fig_quota, use_container_width=True)
                
                # Performance metrics
                metrics = quota_calc.calculate_performance_metrics(quota_history, transactions)
                
                col_perf1, col_perf2, col_perf3, col_perf4 = st.columns(4)
                
                with col_perf1:
                    st.metric(
                        "Rentabilidade",
                        f"{metrics['total_return_pct']:.2f}%",
                        delta=f"{metrics['total_return_pct']:.2f}%"
                    )
                
                with col_perf2:
                    st.metric(
                        "Valor da Cota",
                        f"${metrics['current_quota_value']:.4f}",
                        delta=f"${metrics['current_quota_value'] - metrics['initial_quota_value']:.4f}"
                    )
                
                with col_perf3:
                    st.metric(
                        "Total Investido",
                        f"${metrics['total_invested']:,.2f}"
                    )
                
                with col_perf4:
                    st.metric(
                        "Lucro/Prejuízo",
                        f"${metrics['profit_loss']:+,.2f}",
                        delta=f"{(metrics['profit_loss']/metrics['total_invested']*100) if metrics['total_invested'] > 0 else 0:.2f}%"
                    )
                
                # Detailed info expander
                with st.expander("📊 Detalhes do Sistema de Cotas"):
                    st.markdown(f"""
                    **Como Funciona:**
                    - Valor inicial da cota: ${metrics['initial_quota_value']:.2f}
                    - Valor atual da cota: ${metrics['current_quota_value']:.4f}
                    - Total de cotas: {metrics['total_quotas']:.4f}
                    
                    **Transações:**
                    - Total de depósitos: ${metrics['total_deposits']:,.2f}
                    - Total de saques: ${metrics['total_withdrawals']:,.2f}
                    - Líquido investido: ${metrics['total_invested']:,.2f}
                    
                    **Performance:**
                    - Valor atual: ${metrics['current_value']:,.2f}
                    - Lucro/Prejuízo: ${metrics['profit_loss']:+,.2f}
                    - Rentabilidade: {metrics['total_return_pct']:.2f}%
                    """)
            else:
                st.info("ℹ️ Sincronize mais vezes para visualizar o gráfico de cotas")
        else:
            st.info("ℹ️ Registre depósitos/saques na aba **Configuração** para ativar o sistema de cotas")
        
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
            # First, get prices from LP positions (from Octav.fi)
            token_prices = {}
            for pos in data['lp_positions']:
                # Normalize symbol (BTC, ETH, etc.)
                symbol = pos.token_symbol.upper()
                if symbol.startswith('W'):
                    symbol = symbol[1:]  # WBTC -> BTC, WETH -> ETH
                if pos.price > 0:
                    token_prices[symbol] = pos.price
            
            # Then, try to get prices from Hyperliquid (more up-to-date)
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
                        col1.metric(
                            "LP Balance", 
                            f"{s.lp_balance:.6f} {s.token}",
                            f"${lp_usd:,.2f} USD"
                        )
                        col2.metric(
                            "Short Balance", 
                            f"{s.short_balance:.6f} {s.token}",
                            f"${short_usd:,.2f} USD"
                        )
                        col3.metric(
                            "Diferença", 
                            f"{s.difference:+.6f} {s.token} ({s.difference_pct:.2f}%)",
                            f"${diff_usd:+,.2f} USD"
                        )
                    else:
                        col1.metric("LP Balance", f"{s.lp_balance:.6f} {s.token}")
                        col2.metric("Short Balance", f"{s.short_balance:.6f} {s.token}")
                        col3.metric("Diferença", f"{s.difference:+.6f} {s.token} ({s.difference_pct:.2f}%)")
                
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
            # Get enabled protocols from config
            enabled_protocols = data.get('enabled_protocols', ["Revert", "Uniswap3", "Uniswap4", "Dhedge"])
            
            # Header
            col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 0.5])
            col1.write("**Protocolo**")
            col2.write("**Token**")
            col3.write("**Quantidade**")
            col4.write("**Valor USD**")
            col5.write("**Status**")
            st.markdown("---")
            
            # Display positions
            for pos in lp_positions:
                # Check if protocol is enabled
                is_enabled = any(proto.lower() in pos.protocol.lower() for proto in enabled_protocols)
                
                with st.container():
                    col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 0.5])
                    col1.write(f"**{pos.protocol}** ({pos.chain})")
                    col2.write(pos.token_symbol)
                    col3.write(f"{pos.balance:.6f}")
                    col4.write(f"${pos.value:.2f}")
                    
                    # Show enabled/disabled status
                    if is_enabled:
                        col5.write("✅")  # Enabled
                    else:
                        col5.write("❌")  # Disabled
            
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
            st.info("🔄 Recarregue a página para atualizar")
        
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
                if st.button("❌ Excluir esta entrada", key=f"del_sync_{timestamp}", use_container_width=True):
                    if config_mgr.delete_sync_entry(timestamp):
                        st.success("✅ Entrada excluída")
                        st.info("🔄 Recarregue a página para atualizar a lista")
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
                if config_mgr.clear_execution_history():
                    st.success("✅ Histórico de execuções limpo")
                    st.info("🔄 Recarregue a página para atualizar")
        
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
                if st.button("❌ Excluir esta entrada", key=f"del_exec_{timestamp}", use_container_width=True):
                    if config_mgr.delete_execution_entry(timestamp):
                        st.success("✅ Entrada excluída")
                        st.info("🔄 Recarregue a página para atualizar a lista")
                    else:
                        st.error("❌ Erro ao excluir entrada")

# Footer
st.markdown("---")
st.caption(f"XCELFI LP Hedge V3 | Powered by Octav.fi API | Mode: Analysis (Read-Only)")
