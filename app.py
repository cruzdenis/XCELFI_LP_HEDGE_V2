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
                        
                        networth = float(portfolio.get("networth", "0"))
                        hedge_value_threshold_pct = config.get("hedge_value_threshold_pct", 10.0)
                        
                        # Extract token prices from LP positions (normalize symbols using same method as balances)
                        token_prices = {}
                        for pos in lp_positions:
                            symbol = client.normalize_symbol(pos.token_symbol)
                            token_prices[symbol] = pos.price
                        
                        analyzer = DeltaNeutralAnalyzer(
                            hedge_value_threshold_pct=hedge_value_threshold_pct,
                            total_capital=networth
                        )
                        suggestions = analyzer.compare_positions(lp_balances, short_balances, token_prices)
                        
                        balanced = [s for s in suggestions if s.status == "balanced"]
                        under_hedged = [s for s in suggestions if s.status == "under_hedged"]
                        over_hedged = [s for s in suggestions if s.status == "over_hedged"]
                        
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
                                for s in suggestions:
                                    if s.action != 'none':
                                        adjustments.append({
                                            'token': s.token,
                                            'action': s.action,
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
                # Add https if not present
                if not railway_url.startswith('http'):
                    railway_url = f"https://{railway_url}"
                requests.get(railway_url, timeout=10)
                print(f"[KEEP-ALIVE] Self-pinged at {datetime.now().isoformat()}")

        except Exception as e:
            print(f"[KEEP-ALIVE ERROR] {str(e)}")

if 'keep_alive_started' not in st.session_state:
    keep_alive_thread = threading.Thread(target=keep_alive_worker, daemon=True)
    keep_alive_thread.start()
    st.session_state.keep_alive_started = True

# --- Main App ---
def main():
    """Main Streamlit application"""
    
    st.markdown("<h1 class=\"main-header\">🎯 XCELFI LP Hedge V3</h1>", unsafe_allow_html=True)
    st.markdown("<p class=\"last-sync\">Delta-Neutral LP Hedge Dashboard</p>", unsafe_allow_html=True)

    # --- Tabs ---
    tab_config, tab_dashboard, tab_lp_positions, tab_history, tab_executions, tab_proof_of_reserves = st.tabs([
        "⚙️ Configuração", 
        "📊 Dashboard", 
        "🏬 Posições LP", 
        "📜 Histórico", 
        "📈 Execuções",
        "🔐 Prova de Reservas"
    ])

    # --- Config Tab ---
    with tab_config:
        st.header("⚙️ Configuração")
        
        existing_config = config_mgr.load_config()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🔑 Chaves de API")
            api_key = st.text_input("Octav.fi API Key", value=existing_config.get("api_key", "") if existing_config else "", type="password")
            wallet_address = st.text_input("Endereço da Carteira", value=existing_config.get("wallet_address", "") if existing_config else "")
            hyperliquid_private_key = st.text_input("Chave Privada Hyperliquid (para execução)", value=existing_config.get("hyperliquid_private_key", "") if existing_config else "", type="password")
            
            st.markdown("### 🔄 Sincronização Automática")
            auto_sync_enabled = st.checkbox("Ativar Auto-Sync", value=existing_config.get("auto_sync_enabled", False) if existing_config else False)
            auto_sync_interval_hours = st.number_input("Intervalo de Auto-Sync (horas)", min_value=1, max_value=24, value=existing_config.get("auto_sync_interval_hours", 4) if existing_config else 4)

            st.markdown("###  execution Automática")
            auto_execute_enabled = st.checkbox("Ativar Execução Automática", value=existing_config.get("auto_execute_enabled", False) if existing_config else False)
            if auto_execute_enabled:
                st.warning("🚨 ATENÇÃO: A execução automática irá realizar ordens reais na Hyperliquid sem confirmação manual!")
            else:
                st.info("ℹ️ Modo somente análise (sem execução)")
    
        with col2:
            st.markdown("### ⚙️ Parâmetros")
            
            hedge_value_threshold_pct = st.slider(
                "Gatilho de Hedge (% do Capital)", 
                min_value=0.0, 
                max_value=50.0, 
                value=existing_config.get("hedge_value_threshold_pct", 10.0) if existing_config else 10.0,
                step=0.5,
                help="Valor mínimo (como % do patrimônio total) que um ajuste deve ter para ser considerado 'OBRIGATÓRIO'. Ativa o rebalanceamento completo."
            )

            st.markdown("###  protocols Habilitados")
            all_protocols = ["Revert", "Uniswap3", "Uniswap4", "Dhedge"]
            enabled_protocols = st.multiselect(
                "Selecione os protocolos para incluir na análise",
                options=all_protocols,
                default=existing_config.get("enabled_protocols", all_protocols) if existing_config else all_protocols
            )

        if st.button("Salvar Configuração"):
            config = {
                "api_key": api_key,
                "wallet_address": wallet_address,
                "hyperliquid_private_key": hyperliquid_private_key,
                "auto_sync_enabled": auto_sync_enabled,
                "auto_sync_interval_hours": auto_sync_interval_hours,
                "auto_execute_enabled": auto_execute_enabled,
                "hedge_value_threshold_pct": hedge_value_threshold_pct,
                "enabled_protocols": enabled_protocols
            }
            config_mgr.save_config(config)
            st.success("✅ Configuração salva com sucesso!")

    # --- Dashboard Tab ---
    with tab_dashboard:
        st.header("📊 Dashboard - Análise Delta-Neutral")
        
        last_sync = config_mgr.get_last_sync()
        if last_sync:
            last_sync_dt = datetime.fromisoformat(last_sync)
            st.markdown(f"<p class=\"last-sync\">Última sincronização: {last_sync_dt.strftime('%Y-%m-%d %H:%M:%S')}</p>", unsafe_allow_html=True)
        
        config = config_mgr.load_config()
        if not config or not config.get("api_key") or not config.get("wallet_address"):
            st.warning("🚨 Por favor, configure sua API Key e endereço da carteira na aba 'Configuração'.")
            st.stop()

        if st.button("🔄 Analisar Hedge Agora"):
            with st.spinner("Buscando dados do portfólio na Octav.fi..."):
                client = OctavClient(config["api_key"])
                
                # First sync
                portfolio = client.get_portfolio(config["wallet_address"])
                
                if portfolio:
                    st.spinner("Aguardando 5 segundos para validação de todos os protocolos (especialmente Revert Finance)...")
                    time.sleep(5)
                    # Second sync for validation
                    portfolio = client.get_portfolio(config["wallet_address"])
                
                if not portfolio:
                    st.error("❌ Falha ao buscar dados do portfólio. Verifique sua API key e endereço.")
                    st.stop()
                
                st.success("✅ Sincronização manual concluída com dupla validação!")
                
                # Save data to session state
                st.session_state.portfolio_data = portfolio
                config_mgr.add_sync_history({"manual_sync": True})

        if 'portfolio_data' in st.session_state:
            data = st.session_state.portfolio_data
            
            # --- Executive Summary ---
            networth = float(data.get("networth", "0"))
            lp_value = float(data.get("total_lp_value", "0"))
            hyperliquid_value = float(data.get("total_perp_value", "0"))
            
            lp_allocation_pct = (lp_value / networth * 100) if networth > 0 else 0
            
            client = OctavClient(config["api_key"])
            lp_positions = client.extract_lp_positions(data)
            perp_positions = client.extract_perp_positions(data)
            
            lp_balances = {}
            for pos in lp_positions:
                symbol = OctavClient.normalize_symbol(pos.token_symbol)
                lp_balances[symbol] = lp_balances.get(symbol, 0) + pos.balance
            
            short_balances = {}
            for pos in perp_positions:
                if pos.size < 0:
                    symbol = OctavClient.normalize_symbol(pos.symbol)
                    short_balances[symbol] = short_balances.get(symbol, 0) + abs(pos.size)
            
            hedge_value_threshold_pct = config.get("hedge_value_threshold_pct", 10.0)
            
            analyzer = DeltaNeutralAnalyzer(
                hedge_value_threshold_pct=hedge_value_threshold_pct,
                total_capital=networth
            )
            suggestions = analyzer.compare_positions(lp_balances, short_balances, {p.token_symbol: p.price for p in lp_positions})
            
            # --- Display Executive Summary Cards ---
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("💰 Patrimônio Líquido Total", f"${networth:,.2f}")
            with col2:
                st.metric("💼 Alocação Ideal (LPs)", f"{lp_allocation_pct:.1f}%", delta=f"{lp_allocation_pct-80:.1f}% vs 80%", delta_color="inverse")
            with col3:
                st.metric("⚖️ Hedge Delta-Neutral", f"{len(suggestions)} tokens", help="Número de tokens sendo monitorados para hedge.")
            with col4:
                st.metric("📉 Shorts Ativos", len(short_balances), help="Número de posições short na Hyperliquid.")

            st.markdown("--- ")
            
            # --- Detailed Analysis ---
            st.subheader("📊 Análise Detalhada")
            
            # Check if trigger is activated based on priority
            trigger_activated = any(s.priority == "required" for s in suggestions)
            
            if trigger_activated:
                st.warning(f"⚡ **GATILHO DE REBALANCEAMENTO ACIONADO!** Pelo menos uma posição tem ajuste **OBRIGATÓRIO** (valor maior que o gatilho de {hedge_value_threshold_pct}%). **TODAS as posições com desvio serão ajustadas**.")
            else:
                st.success("✅ Nenhuma posição requer ajuste obrigatório.")

            # Display suggestions
            if not suggestions:
                st.info("✅ Nenhuma posição para analisar ou todas as posições estão perfeitamente balanceadas.")
            else:
                # Separate by status
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
            
                # Fetch current prices for USD conversion
                token_prices = {}
                for pos in lp_positions:
                    symbol = OctavClient.normalize_symbol(pos.token_symbol)
                    token_prices[symbol] = pos.price

                for s in sorted(suggestions, key=lambda x: x.priority, reverse=True):
                    st.markdown(f"#### {s.token} - {s.status.upper().replace('_', ' ')}")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    lp_value_usd = s.lp_balance * token_prices.get(s.token, 0)
                    short_value_usd = s.short_balance * token_prices.get(s.token, 0)
                    diff_usd = s.difference * token_prices.get(s.token, 0)

                    col1.metric("LP Balance", f"{s.lp_balance:.6f} {s.token}", f"${lp_value_usd:,.2f} USD")
                    col2.metric("Short Balance", f"{s.short_balance:.6f} {s.token}", f"${short_value_usd:,.2f} USD")
                    col3.metric("Diferença", f"{s.difference:+.6f} {s.token} ({s.difference_pct:.2f}%)", f"${diff_usd:+,.2f} USD")
                
                    if s.action != "none":
                        action_text = "AUMENTAR" if s.action == "increase_short" else "DIMINUIR"
                        
                        # Show priority based on value threshold
                        priority_emoji = "🔴" if s.priority == "required" else "🟡"
                        priority_text = "OBRIGATÓRIO" if s.priority == "required" else "OPCIONAL"
                        
                        value_pct_of_capital = (s.adjustment_value_usd / networth * 100) if networth > 0 else 0
                        
                        st.info(f"{priority_emoji} **{priority_text}**: {action_text} SHORT em **{s.adjustment_amount:.6f} {s.token}** (${s.adjustment_value_usd:,.2f} = {value_pct_of_capital:.1f}% do capital)")

                    st.markdown("<br>", unsafe_allow_html=True)

            # --- Action Summary & Execution ---
            st.subheader("📋 Resumo de Ações Necessárias")
            
            action_summary = analyzer.get_action_summary(suggestions)
            increase_actions = action_summary.get("increase_short", {})
            decrease_actions = action_summary.get("decrease_short", {})
            
            if not increase_actions and not decrease_actions:
                st.success("✅ Nenhuma ação de hedge necessária no momento.")
            else:
                col1, col2 = st.columns(2)
                with col1:
                    if increase_actions:
                        st.markdown("**🔺 AUMENTAR SHORT:**")
                        for token, amount in increase_actions.items():
                            st.markdown(f"- **{token}**: `+{amount:.6f}`")
                with col2:
                    if decrease_actions:
                        st.markdown("**🔻 DIMINUIR SHORT:**")
                        for token, amount in decrease_actions.items():
                            st.markdown(f"- **{token}**: `-{amount:.6f}`")

                st.subheader("⚡ Execução Automática")
                st.warning("🚨 ATENÇÃO: Isso irá executar ordens reais na Hyperliquid!")
                
                if st.button("Executar Todos os Ajustes", key="exec_all"):
                    hyperliquid_private_key = config.get("hyperliquid_private_key")
                    if not hyperliquid_private_key:
                        st.error("❌ Chave privada da Hyperliquid não configurada.")
                        st.stop()
                    
                    with st.spinner("Executando ajustes na Hyperliquid..."):
                        from hyperliquid_client import HyperliquidClient
                        hl_client = HyperliquidClient(config["wallet_address"], hyperliquid_private_key)
                        
                        adjustments_to_exec = []
                        for token, amount in increase_actions.items():
                            adjustments_to_exec.append({"token": token, "action": "increase_short", "amount": amount})
                        for token, amount in decrease_actions.items():
                            adjustments_to_exec.append({"token": token, "action": "decrease_short", "amount": amount})
                        
                        results = hl_client.execute_adjustments(adjustments_to_exec)
                        
                        st.success("✅ Execução concluída!")
                        
                        # Log and display results
                        for result in results:
                            if result['result'].success:
                                st.write(f"- **{result['token']}**: {result['action'].replace('_', ' ').title()} de {result['amount']:.6f} - ✅ SUCESSO (Ordem {result['result'].order_id})")
                                config_mgr.add_execution_history({
                                    'token': result['token'],
                                    'action': result['action'],
                                    'amount': result['amount'],
                                    'order_value_usd': result.get('order_value_usd', 0),
                                    'success': True,
                                    'message': f"Order ID: {result['result'].order_id}",
                                    'order_id': result['result'].order_id,
                                    'filled_size': result['result'].filled_size,
                                    'avg_price': result['result'].avg_price,
                                    'auto_executed': False
                                })
                            else:
                                st.write(f"- **{result['token']}**: {result['action'].replace('_', ' ').title()} de {result['amount']:.6f} - ❌ FALHA: {result['result'].message}")
                                config_mgr.add_execution_history({
                                    'token': result['token'],
                                    'action': result['action'],
                                    'amount': result['amount'],
                                    'success': False,
                                    'message': result['result'].message,
                                    'auto_executed': False
                                })

    # --- LP Positions Tab ---
    with tab_lp_positions:
        st.header("🏬 Posições LP")
        if 'portfolio_data' in st.session_state:
            client = OctavClient(config["api_key"])
            lp_positions = client.extract_lp_positions(st.session_state.portfolio_data)
            
            if not lp_positions:
                st.info("Nenhuma posição LP encontrada.")
            else:
                # Display LP positions in a table
                import pandas as pd
                df_lp = pd.DataFrame([{
                    "Protocolo": pos.protocol,
                    "Token": pos.token_symbol,
                    "Quantidade": pos.balance,
                    "Valor USD": f"${pos.balance * pos.price:,.2f}",
                    "Range": f"{pos.min_range:.2f} - {pos.max_range:.2f}"
                } for pos in lp_positions])
                st.dataframe(df_lp, use_container_width=True)

                # Aggregated balances
                st.subheader("📊 Balanços Agregados")
                lp_balances = {}
                for pos in lp_positions:
                    symbol = OctavClient.normalize_symbol(pos.token_symbol)
                    lp_balances[symbol] = lp_balances.get(symbol, 0) + pos.balance
                
                df_agg = pd.DataFrame(lp_balances.items(), columns=["Token", "Quantidade"])
                st.dataframe(df_agg, use_container_width=True)

    # --- History Tab ---
    with tab_history:
        st.header("📜 Histórico de Sincronização")
        history = config_mgr.get_sync_history()
        if not history:
            st.info("Nenhum histórico de sincronização encontrado.")
        else:
            import pandas as pd
            df_history = pd.DataFrame(history)
            df_history['timestamp'] = pd.to_datetime(df_history['timestamp'])
            st.dataframe(df_history, use_container_width=True)

    # --- Executions Tab ---
    with tab_executions:
        st.header("📈 Histórico de Execuções")
        executions = config_mgr.get_execution_history()
        if not executions:
            st.info("Nenhum histórico de execução encontrado.")
        else:
            import pandas as pd
            df_exec = pd.DataFrame(executions)
            df_exec['timestamp'] = pd.to_datetime(df_exec['timestamp'])
            st.dataframe(df_exec, use_container_width=True)

    # --- Proof of Reserves Tab ---
    with tab_proof_of_reserves:
        st.header("🔐 Prova de Reservas (Hyperliquid)")
        if 'portfolio_data' in st.session_state:
            client = OctavClient(config["api_key"])
            perp_positions = client.extract_perp_positions(st.session_state.portfolio_data)
            
            if not perp_positions:
                st.info("Nenhuma posição perpétua encontrada na Hyperliquid.")
            else:
                import pandas as pd
                df_perp = pd.DataFrame([{
                    "Token": pos.symbol,
                    "Tamanho": pos.size,
                    "Valor USD": f"${pos.position_value:,.2f}",
                    "P&L": f"${pos.unrealized_pnl:,.2f}",
                    "Margem": f"${pos.margin_used:,.2f}",
                    "Alavancagem": f"{pos.leverage:.2f}x"
                } for pos in perp_positions])
                st.dataframe(df_perp, use_container_width=True)

    # --- Footer ---
    st.markdown("---")
    st.markdown("XCELFI LP Hedge V3 | Powered by Octav.fi API | Mode: Analysis (Read-Only)")
    st.markdown("Made with [Streamlit](https://streamlit.io)")

if __name__ == "__main__":
    main()
