"""
Settings Tab - Interface de configurações do aplicativo
Permite ao usuário gerenciar todas as configurações via interface web
"""

import streamlit as st
from core.settings_manager import SettingsManager
from typing import Dict, Any


def render_settings_tab(settings_manager: SettingsManager):
    """
    Renderiza a aba de configurações
    
    Args:
        settings_manager: Instância do gerenciador de configurações
    """
    st.header("⚙️ Configurações do Sistema")
    
    # Carregar configurações atuais
    settings = settings_manager.load_settings()
    
    # Criar tabs para organizar as configurações
    config_tabs = st.tabs([
        "🔐 Credenciais",
        "🎯 Estratégia",
        "⚠️ Gestão de Risco",
        "🤖 Execução",
        "📊 Monitoramento",
        "🔧 Avançado"
    ])
    
    # ===== TAB 1: CREDENCIAIS =====
    with config_tabs[0]:
        render_credentials_section(settings, settings_manager)
    
    # ===== TAB 2: ESTRATÉGIA =====
    with config_tabs[1]:
        render_strategy_section(settings, settings_manager)
    
    # ===== TAB 3: GESTÃO DE RISCO =====
    with config_tabs[2]:
        render_risk_section(settings, settings_manager)
    
    # ===== TAB 4: EXECUÇÃO =====
    with config_tabs[3]:
        render_execution_section(settings, settings_manager)
    
    # ===== TAB 5: MONITORAMENTO =====
    with config_tabs[4]:
        render_monitoring_section(settings, settings_manager)
    
    # ===== TAB 6: AVANÇADO =====
    with config_tabs[5]:
        render_advanced_section(settings, settings_manager)


def render_credentials_section(settings: Dict[str, Any], manager: SettingsManager):
    """Renderiza seção de credenciais"""
    st.subheader("Credenciais e Conectividade")
    
    st.info("💡 **Modo Somente Leitura:** Configure apenas a wallet pública para análise sem execução")
    
    # Status de credenciais
    creds = manager.has_credentials()
    operation_mode = manager.get_operation_mode()
    
    mode_colors = {
        "READ_ONLY": "🔵",
        "PARTIAL": "🟡",
        "FULL": "🟢"
    }
    mode_labels = {
        "READ_ONLY": "Somente Leitura",
        "PARTIAL": "Parcial",
        "FULL": "Completo"
    }
    
    st.metric(
        "Modo de Operação",
        f"{mode_colors.get(operation_mode, '⚪')} {mode_labels.get(operation_mode, 'Desconhecido')}"
    )
    
    st.markdown("---")
    
    # Wallet & Blockchain
    st.markdown("### 🔗 Wallet & Blockchain")
    
    col1, col2 = st.columns(2)
    
    with col1:
        wallet_public = st.text_input(
            "Endereço Público da Wallet",
            value=settings.get("wallet_public_address", ""),
            help="Endereço público da sua wallet (0x...)",
            type="default"
        )
        
        base_rpc = st.text_input(
            "Base RPC URL",
            value=settings.get("base_rpc_url", "https://mainnet.base.org"),
            help="URL do RPC da rede Base"
        )
    
    with col2:
        wallet_private = st.text_input(
            "Chave Privada da Wallet",
            value=settings.get("wallet_private_key", ""),
            help="⚠️ Necessária apenas para execução. Deixe vazio para modo somente leitura",
            type="password"
        )
        
        if wallet_private:
            st.warning("⚠️ Chave privada configurada. Execução habilitada!")
    
    st.markdown("---")
    
    # Aerodrome
    st.markdown("### 🌊 Aerodrome (Base L2)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        aerodrome_subgraph = st.text_input(
            "Subgraph URL",
            value=settings.get("aerodrome_subgraph_url", ""),
            help="URL do subgraph da Aerodrome"
        )
        
        aerodrome_pool = st.text_input(
            "Pool Address",
            value=settings.get("aerodrome_pool_address", ""),
            help="Endereço do pool ETH/BTC na Aerodrome"
        )
    
    with col2:
        aerodrome_router = st.text_input(
            "Router Address",
            value=settings.get("aerodrome_router", ""),
            help="Endereço do router da Aerodrome"
        )
    
    st.markdown("---")
    
    # Hyperliquid
    st.markdown("### ⚡ Hyperliquid")
    
    col1, col2 = st.columns(2)
    
    with col1:
        hyperliquid_base_url = st.text_input(
            "Base URL",
            value=settings.get("hyperliquid_base_url", "https://api.hyperliquid.xyz"),
            help="URL base da API Hyperliquid"
        )
        
        hyperliquid_api_key = st.text_input(
            "API Key",
            value=settings.get("hyperliquid_api_key", ""),
            help="API Key da Hyperliquid (necessária para execução)",
            type="password"
        )
    
    with col2:
        hyperliquid_wallet = st.text_input(
            "Wallet Address",
            value=settings.get("hyperliquid_wallet_address", ""),
            help="Endereço da wallet na Hyperliquid"
        )
        
        hyperliquid_api_secret = st.text_input(
            "API Secret",
            value=settings.get("hyperliquid_api_secret", ""),
            help="API Secret da Hyperliquid (necessária para execução)",
            type="password"
        )
    
    st.markdown("---")
    
    # Botão de salvar
    if st.button("💾 Salvar Credenciais", type="primary", use_container_width=True):
        new_settings = settings.copy()
        new_settings.update({
            "wallet_public_address": wallet_public,
            "wallet_private_key": wallet_private,
            "base_rpc_url": base_rpc,
            "aerodrome_subgraph_url": aerodrome_subgraph,
            "aerodrome_router": aerodrome_router,
            "aerodrome_pool_address": aerodrome_pool,
            "hyperliquid_base_url": hyperliquid_base_url,
            "hyperliquid_api_key": hyperliquid_api_key,
            "hyperliquid_api_secret": hyperliquid_api_secret,
            "hyperliquid_wallet_address": hyperliquid_wallet,
        })
        
        if manager.save_settings(new_settings):
            st.success("✅ Credenciais salvas com sucesso!")
            st.rerun()
        else:
            st.error("❌ Erro ao salvar credenciais")


def render_strategy_section(settings: Dict[str, Any], manager: SettingsManager):
    """Renderiza seção de estratégia"""
    st.subheader("Parâmetros da Estratégia")
    
    st.markdown("### 🎯 Triggers de Rebalanceamento")
    
    col1, col2 = st.columns(2)
    
    with col1:
        recenter_trigger = st.number_input(
            "Trigger de Recentralização (%)",
            min_value=0.1,
            max_value=10.0,
            value=float(settings.get("recenter_trigger_pct", 1.0)),
            step=0.1,
            help="Desvio percentual que dispara rebalanceamento"
        )
    
    with col2:
        recenter_hysteresis = st.number_input(
            "Histerese (%)",
            min_value=0.0,
            max_value=5.0,
            value=float(settings.get("recenter_hysteresis_pct", 0.2)),
            step=0.1,
            help="Margem de segurança para evitar overtrading"
        )
    
    st.markdown("---")
    
    st.markdown("### 📊 Alocação Target (Buffers)")
    
    st.info("💡 A soma das alocações deve ser exatamente 100%")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        target_lp = st.number_input(
            "LP Position (%)",
            min_value=0.0,
            max_value=100.0,
            value=float(settings.get("target_lp_pct", 74.0)),
            step=1.0,
            help="Percentual alocado em LP na Aerodrome"
        )
    
    with col2:
        target_short = st.number_input(
            "Short Position (%)",
            min_value=0.0,
            max_value=100.0,
            value=float(settings.get("target_short_pct", 24.0)),
            step=1.0,
            help="Percentual alocado em shorts na Hyperliquid"
        )
    
    with col3:
        target_eth_gas = st.number_input(
            "ETH Gas (%)",
            min_value=0.0,
            max_value=100.0,
            value=float(settings.get("target_eth_gas_pct", 1.0)),
            step=0.1,
            help="Reserva de ETH para gas fees"
        )
    
    with col4:
        target_usdc_cex = st.number_input(
            "USDC CEX (%)",
            min_value=0.0,
            max_value=100.0,
            value=float(settings.get("target_usdc_cex_pct", 1.0)),
            step=0.1,
            help="Reserva de USDC na CEX"
        )
    
    # Validar soma
    total_allocation = target_lp + target_short + target_eth_gas + target_usdc_cex
    
    if abs(total_allocation - 100.0) > 0.01:
        st.error(f"⚠️ Soma das alocações: {total_allocation:.2f}% (deve ser 100%)")
    else:
        st.success(f"✅ Soma das alocações: {total_allocation:.2f}%")
    
    st.markdown("---")
    
    # Botão de salvar
    if st.button("💾 Salvar Parâmetros de Estratégia", type="primary", use_container_width=True):
        new_settings = settings.copy()
        new_settings.update({
            "recenter_trigger_pct": recenter_trigger,
            "recenter_hysteresis_pct": recenter_hysteresis,
            "target_lp_pct": target_lp,
            "target_short_pct": target_short,
            "target_eth_gas_pct": target_eth_gas,
            "target_usdc_cex_pct": target_usdc_cex,
        })
        
        is_valid, errors = manager.validate_settings(new_settings)
        
        if not is_valid:
            for error in errors:
                st.error(f"❌ {error}")
        else:
            if manager.save_settings(new_settings):
                st.success("✅ Parâmetros salvos com sucesso!")
                st.rerun()
            else:
                st.error("❌ Erro ao salvar parâmetros")


def render_risk_section(settings: Dict[str, Any], manager: SettingsManager):
    """Renderiza seção de gestão de risco"""
    st.subheader("Gestão de Risco")
    
    col1, col2 = st.columns(2)
    
    with col1:
        max_slippage = st.number_input(
            "Slippage Máximo (%)",
            min_value=0.1,
            max_value=10.0,
            value=float(settings.get("max_slippage_pct", 0.5)),
            step=0.1,
            help="Slippage máximo aceito em operações"
        )
        
        min_eth_gas = st.number_input(
            "Saldo Mínimo ETH Gas",
            min_value=0.1,
            max_value=10.0,
            value=float(settings.get("min_eth_gas_balance", 0.5)),
            step=0.1,
            help="Saldo mínimo de ETH para gas fees"
        )
    
    with col2:
        min_usdc_cex = st.number_input(
            "Saldo Mínimo USDC CEX",
            min_value=100.0,
            max_value=50000.0,
            value=float(settings.get("min_usdc_cex_balance", 5000.0)),
            step=100.0,
            help="Saldo mínimo de USDC na CEX"
        )
    
    st.markdown("---")
    
    # Botão de salvar
    if st.button("💾 Salvar Configurações de Risco", type="primary", use_container_width=True):
        new_settings = settings.copy()
        new_settings.update({
            "max_slippage_pct": max_slippage,
            "min_eth_gas_balance": min_eth_gas,
            "min_usdc_cex_balance": min_usdc_cex,
        })
        
        if manager.save_settings(new_settings):
            st.success("✅ Configurações de risco salvas!")
            st.rerun()
        else:
            st.error("❌ Erro ao salvar configurações")


def render_execution_section(settings: Dict[str, Any], manager: SettingsManager):
    """Renderiza seção de execução"""
    st.subheader("Modo de Execução")
    
    st.info("💡 **MANUAL:** Você aprova cada operação | **AUTO:** Sistema executa automaticamente")
    
    execution_mode = st.radio(
        "Modo de Execução",
        options=["MANUAL", "AUTO"],
        index=0 if settings.get("execution_mode", "MANUAL") == "MANUAL" else 1,
        help="Escolha entre execução manual ou automática"
    )
    
    auto_execute = st.checkbox(
        "Habilitar Execução Automática",
        value=settings.get("auto_execute_enabled", False),
        help="⚠️ Atenção: Sistema executará operações automaticamente!"
    )
    
    if auto_execute:
        st.warning("⚠️ **ATENÇÃO:** Execução automática habilitada! Sistema executará operações sem confirmação.")
    
    st.markdown("---")
    
    # Botão de salvar
    if st.button("💾 Salvar Configurações de Execução", type="primary", use_container_width=True):
        new_settings = settings.copy()
        new_settings.update({
            "execution_mode": execution_mode,
            "auto_execute_enabled": auto_execute,
        })
        
        if manager.save_settings(new_settings):
            st.success("✅ Configurações de execução salvas!")
            st.rerun()
        else:
            st.error("❌ Erro ao salvar configurações")


def render_monitoring_section(settings: Dict[str, Any], manager: SettingsManager):
    """Renderiza seção de monitoramento"""
    st.subheader("Monitoramento e Notificações")
    
    col1, col2 = st.columns(2)
    
    with col1:
        watch_interval = st.number_input(
            "Intervalo de Monitoramento (min)",
            min_value=1,
            max_value=60,
            value=int(settings.get("watch_interval_min", 10)),
            step=1,
            help="Intervalo de atualização dos dados"
        )
    
    with col2:
        enable_notifications = st.checkbox(
            "Habilitar Notificações",
            value=settings.get("enable_notifications", False),
            help="Enviar notificações sobre eventos importantes"
        )
    
    if enable_notifications:
        notification_webhook = st.text_input(
            "Webhook URL (Discord/Slack/Telegram)",
            value=settings.get("notification_webhook", ""),
            help="URL do webhook para enviar notificações"
        )
    else:
        notification_webhook = ""
    
    st.markdown("---")
    
    # Botão de salvar
    if st.button("💾 Salvar Configurações de Monitoramento", type="primary", use_container_width=True):
        new_settings = settings.copy()
        new_settings.update({
            "watch_interval_min": watch_interval,
            "enable_notifications": enable_notifications,
            "notification_webhook": notification_webhook,
        })
        
        if manager.save_settings(new_settings):
            st.success("✅ Configurações de monitoramento salvas!")
            st.rerun()
        else:
            st.error("❌ Erro ao salvar configurações")


def render_advanced_section(settings: Dict[str, Any], manager: SettingsManager):
    """Renderiza seção avançada"""
    st.subheader("Configurações Avançadas")
    
    col1, col2 = st.columns(2)
    
    with col1:
        enable_debug = st.checkbox(
            "Habilitar Logs de Debug",
            value=settings.get("enable_debug_logs", False),
            help="Ativar logs detalhados para debugging"
        )
        
        max_retries = st.number_input(
            "Máximo de Tentativas",
            min_value=1,
            max_value=10,
            value=int(settings.get("max_retries", 3)),
            step=1,
            help="Número máximo de tentativas em caso de falha"
        )
    
    with col2:
        retry_delay = st.number_input(
            "Delay entre Tentativas (seg)",
            min_value=1,
            max_value=60,
            value=int(settings.get("retry_delay_sec", 5)),
            step=1,
            help="Tempo de espera entre tentativas"
        )
    
    st.markdown("---")
    
    st.markdown("### 🔧 Ações do Sistema")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📥 Exportar Configurações", use_container_width=True):
            export_path = "data/settings_backup.json"
            if manager.export_settings(export_path):
                st.success(f"✅ Exportado para {export_path}")
            else:
                st.error("❌ Erro ao exportar")
    
    with col2:
        if st.button("🔄 Resetar para Padrão", use_container_width=True):
            if manager.reset_to_defaults():
                st.success("✅ Configurações resetadas!")
                st.rerun()
            else:
                st.error("❌ Erro ao resetar")
    
    with col3:
        if st.button("💾 Salvar Avançado", type="primary", use_container_width=True):
            new_settings = settings.copy()
            new_settings.update({
                "enable_debug_logs": enable_debug,
                "max_retries": max_retries,
                "retry_delay_sec": retry_delay,
            })
            
            if manager.save_settings(new_settings):
                st.success("✅ Configurações avançadas salvas!")
                st.rerun()
            else:
                st.error("❌ Erro ao salvar")
