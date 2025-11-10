"""
Settings Manager - Gerenciamento de configurações persistentes
Permite salvar e carregar configurações do usuário em arquivo JSON
"""

import json
import os
from typing import Dict, Any, Optional
from pathlib import Path
import streamlit as st


class SettingsManager:
    """Gerencia configurações persistentes do aplicativo"""
    
    def __init__(self, settings_file: str = "data/user_settings.json"):
        """
        Inicializa o gerenciador de configurações
        
        Args:
            settings_file: Caminho para o arquivo de configurações
        """
        self.settings_file = settings_file
        self._ensure_data_dir()
        
    def _ensure_data_dir(self):
        """Garante que o diretório de dados existe"""
        data_dir = os.path.dirname(self.settings_file)
        if data_dir and not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)
    
    def load_settings(self) -> Dict[str, Any]:
        """
        Carrega configurações do arquivo
        
        Returns:
            Dict com configurações ou dict vazio se arquivo não existir
        """
        if not os.path.exists(self.settings_file):
            return self._get_default_settings()
        
        try:
            with open(self.settings_file, 'r') as f:
                settings = json.load(f)
            return settings
        except Exception as e:
            st.error(f"Erro ao carregar configurações: {e}")
            return self._get_default_settings()
    
    def save_settings(self, settings: Dict[str, Any]) -> bool:
        """
        Salva configurações no arquivo
        
        Args:
            settings: Dict com configurações para salvar
            
        Returns:
            True se salvou com sucesso, False caso contrário
        """
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
            return True
        except Exception as e:
            st.error(f"Erro ao salvar configurações: {e}")
            return False
    
    def update_setting(self, key: str, value: Any) -> bool:
        """
        Atualiza uma configuração específica
        
        Args:
            key: Chave da configuração
            value: Novo valor
            
        Returns:
            True se atualizou com sucesso
        """
        settings = self.load_settings()
        settings[key] = value
        return self.save_settings(settings)
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """
        Obtém uma configuração específica
        
        Args:
            key: Chave da configuração
            default: Valor padrão se não encontrar
            
        Returns:
            Valor da configuração ou default
        """
        settings = self.load_settings()
        return settings.get(key, default)
    
    def _get_default_settings(self) -> Dict[str, Any]:
        """
        Retorna configurações padrão
        
        Returns:
            Dict com configurações padrão
        """
        return {
            # Wallet & Blockchain
            "wallet_public_address": "",
            "wallet_private_key": "",  # Criptografado ou vazio
            "base_rpc_url": "https://mainnet.base.org",
            
            # Aerodrome
            "aerodrome_subgraph_url": "https://api.thegraph.com/subgraphs/name/aerodrome-finance/aerodrome-base",
            "aerodrome_router": "0xcF77a3Ba9A5CA399B7c97c74d54e5b1Beb874E43",
            "aerodrome_pool_address": "",
            
            # Hyperliquid
            "hyperliquid_base_url": "https://api.hyperliquid.xyz",
            "hyperliquid_api_key": "",
            "hyperliquid_api_secret": "",
            "hyperliquid_wallet_address": "",
            
            # Strategy Parameters
            "recenter_trigger_pct": 1.0,
            "recenter_hysteresis_pct": 0.2,
            "target_lp_pct": 74.0,
            "target_short_pct": 24.0,
            "target_eth_gas_pct": 1.0,
            "target_usdc_cex_pct": 1.0,
            
            # Risk Management
            "max_slippage_pct": 0.5,
            "min_eth_gas_balance": 0.5,
            "min_usdc_cex_balance": 5000.0,
            
            # Execution Mode
            "execution_mode": "MANUAL",  # MANUAL ou AUTO
            "auto_execute_enabled": False,
            
            # Monitoring
            "watch_interval_min": 10,
            "enable_notifications": False,
            "notification_webhook": "",
            
            # Advanced
            "enable_debug_logs": False,
            "max_retries": 3,
            "retry_delay_sec": 5,
        }
    
    def reset_to_defaults(self) -> bool:
        """
        Reseta todas as configurações para valores padrão
        
        Returns:
            True se resetou com sucesso
        """
        return self.save_settings(self._get_default_settings())
    
    def export_settings(self, export_path: str) -> bool:
        """
        Exporta configurações para um arquivo
        
        Args:
            export_path: Caminho para exportar
            
        Returns:
            True se exportou com sucesso
        """
        settings = self.load_settings()
        try:
            with open(export_path, 'w') as f:
                json.dump(settings, f, indent=2)
            return True
        except Exception as e:
            st.error(f"Erro ao exportar configurações: {e}")
            return False
    
    def import_settings(self, import_path: str) -> bool:
        """
        Importa configurações de um arquivo
        
        Args:
            import_path: Caminho do arquivo para importar
            
        Returns:
            True se importou com sucesso
        """
        try:
            with open(import_path, 'r') as f:
                settings = json.load(f)
            return self.save_settings(settings)
        except Exception as e:
            st.error(f"Erro ao importar configurações: {e}")
            return False
    
    def validate_settings(self, settings: Dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Valida configurações
        
        Args:
            settings: Dict com configurações para validar
            
        Returns:
            Tupla (is_valid, list_of_errors)
        """
        errors = []
        
        # Validar percentuais de alocação
        total_allocation = (
            settings.get("target_lp_pct", 0) +
            settings.get("target_short_pct", 0) +
            settings.get("target_eth_gas_pct", 0) +
            settings.get("target_usdc_cex_pct", 0)
        )
        
        if abs(total_allocation - 100.0) > 0.01:
            errors.append(f"Soma das alocações deve ser 100%, atual: {total_allocation}%")
        
        # Validar trigger e hysteresis
        trigger = settings.get("recenter_trigger_pct", 0)
        hysteresis = settings.get("recenter_hysteresis_pct", 0)
        
        if trigger <= 0:
            errors.append("Trigger de recentralização deve ser > 0%")
        
        if hysteresis < 0:
            errors.append("Histerese não pode ser negativa")
        
        if hysteresis >= trigger:
            errors.append("Histerese deve ser menor que o trigger")
        
        # Validar slippage
        slippage = settings.get("max_slippage_pct", 0)
        if slippage <= 0 or slippage > 10:
            errors.append("Slippage máximo deve estar entre 0% e 10%")
        
        # Validar watch interval
        watch_interval = settings.get("watch_interval_min", 0)
        if watch_interval < 1:
            errors.append("Intervalo de monitoramento deve ser >= 1 minuto")
        
        return (len(errors) == 0, errors)
    
    def get_execution_mode(self) -> str:
        """
        Retorna o modo de execução atual
        
        Returns:
            "MANUAL" ou "AUTO"
        """
        return self.get_setting("execution_mode", "MANUAL")
    
    def is_auto_execute_enabled(self) -> bool:
        """
        Verifica se execução automática está habilitada
        
        Returns:
            True se auto-execução está habilitada
        """
        return self.get_setting("auto_execute_enabled", False)
    
    def has_credentials(self) -> Dict[str, bool]:
        """
        Verifica quais credenciais estão configuradas
        
        Returns:
            Dict com status de cada credencial
        """
        settings = self.load_settings()
        
        return {
            "wallet_public": bool(settings.get("wallet_public_address")),
            "wallet_private": bool(settings.get("wallet_private_key")),
            "hyperliquid_api": bool(
                settings.get("hyperliquid_api_key") and 
                settings.get("hyperliquid_api_secret")
            ),
            "aerodrome_pool": bool(settings.get("aerodrome_pool_address")),
        }
    
    def get_operation_mode(self) -> str:
        """
        Determina o modo de operação baseado nas credenciais
        
        Returns:
            "READ_ONLY", "PARTIAL", ou "FULL"
        """
        creds = self.has_credentials()
        
        if not creds["wallet_public"]:
            return "READ_ONLY"
        
        if creds["wallet_private"] and creds["hyperliquid_api"]:
            return "FULL"
        
        return "PARTIAL"
