"""
EXEMPLO COMPLETO: LONG e SHORT na Hyperliquid com Validações

Este script demonstra:
1. Como executar um LONG (compra)
2. Como executar um SHORT (venda)
3. Como fechar posições
4. Todas as validações necessárias
5. Logging detalhado para debugging

Autor: Manus AI
Data: 23 de Novembro de 2025
"""

from typing import Optional, Dict
from dataclasses import dataclass
from hyperliquid.exchange import Exchange
from hyperliquid.info import Info
from eth_account import Account
from math import log10, floor
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================
# CONFIGURAÇÃO - SUBSTITUA COM SUAS CREDENCIAIS
# ============================================================
WALLET_ADDRESS = "0xYOUR_WALLET_ADDRESS_HERE"
PRIVATE_KEY = "0xYOUR_PRIVATE_KEY_HERE"

# ============================================================
# CLASSES E ESTRUTURAS DE DADOS
# ============================================================

@dataclass
class OrderResult:
    """Resultado da execução de uma ordem."""
    success: bool
    message: str
    order_id: Optional[str] = None
    filled_size: Optional[float] = None
    avg_price: Optional[float] = None
    total_value: Optional[float] = None

# ============================================================
# EXECUTOR ROBUSTO COM VALIDAÇÕES
# ============================================================

class HyperliquidExecutor:
    """
    Executor robusto de ordens na Hyperliquid.
    
    Implementa todas as validações necessárias:
    - Precisão de tamanho (szDecimals)
    - Precisão de preço (5 dígitos significativos)
    - Valor mínimo ($10 USD)
    - Verificação de resultado
    """
    
    def __init__(self, wallet_address: str, private_key: str):
        """Inicializa o executor e carrega metadados."""
        logger.info("="*60)
        logger.info("INICIALIZANDO HYPERLIQUID EXECUTOR")
        logger.info("="*60)
        
        self.wallet_address = wallet_address
        
        # Criar conexão
        logger.info("Criando conexão com Hyperliquid...")
        wallet = Account.from_key(private_key)
        self.exchange = Exchange(wallet)
        self.info = Info()
        logger.info(f"✅ Conectado! Wallet: {wallet_address}")
        
        # Carregar metadados
        logger.info("Carregando metadados dos ativos...")
        self.asset_meta = self._load_asset_metadata()
        logger.info(f"✅ Metadados carregados para {len(self.asset_meta)} ativos")
        logger.info("")
    
    def _load_asset_metadata(self) -> Dict:
        """Carrega metadados de todos os ativos (szDecimals, maxLeverage)."""
        try:
            meta = self.info.meta()
            asset_data = {}
            
            if meta and 'universe' in meta:
                for asset_info in meta['universe']:
                    name = asset_info.get('name')
                    if name:
                        asset_data[name] = {
                            'szDecimals': asset_info.get('szDecimals', 3),
                            'maxLeverage': asset_info.get('maxLeverage', 1)
                        }
                        logger.debug(f"  {name}: szDecimals={asset_data[name]['szDecimals']}")
            
            return asset_data
            
        except Exception as e:
            logger.warning(f"Erro ao carregar metadados: {e}")
            logger.warning("Usando valores padrão para ativos comuns")
            
            # Defaults para ativos comuns
            return {
                'BTC': {'szDecimals': 4, 'maxLeverage': 50},
                'ETH': {'szDecimals': 3, 'maxLeverage': 50},
                'SOL': {'szDecimals': 2, 'maxLeverage': 20}
            }
    
    def _round_size(self, size: float, symbol: str) -> float:
        """
        Arredonda tamanho para szDecimals do ativo.
        
        Exemplo: BTC (szDecimals=4) → 0.00151234 → 0.0015
        """
        sz_decimals = self.asset_meta.get(symbol, {}).get('szDecimals', 3)
        rounded = round(size, sz_decimals)
        
        logger.debug(f"  [SIZE] {size:.10f} → {rounded} (szDecimals={sz_decimals})")
        return rounded
    
    def _round_price(self, price: float, symbol: str) -> float:
        """
        Arredonda preço para 5 dígitos significativos.
        
        Regras da Hyperliquid:
        1. Máximo 5 dígitos significativos
        2. Máximo (6 - szDecimals) casas decimais
        3. Remover zeros à direita
        """
        if price == 0:
            return 0.0
        
        sz_decimals = self.asset_meta.get(symbol, {}).get('szDecimals', 3)
        
        # Passo 1: 5 dígitos significativos
        magnitude = floor(log10(abs(price)))
        sig_fig_decimals = 5 - magnitude - 1
        price_5sig = round(price, sig_fig_decimals)
        
        # Passo 2: Limite de casas decimais
        max_decimals = 6 - sz_decimals
        final_price = round(price_5sig, max_decimals)
        
        # Passo 3: Remover zeros à direita
        formatted = f"{final_price:.{max_decimals}f}".rstrip('0').rstrip('.')
        validated_price = float(formatted)
        
        logger.debug(f"  [PRICE] {price:.6f} → {validated_price} (5 sig figs, max {max_decimals} decimals)")
        return validated_price
    
    def _validate_order_value(self, order_size: float, current_price: float, 
                              min_value_usd: float = 10.0) -> tuple[bool, float]:
        """
        Valida se o valor da ordem atinge o mínimo exigido ($10 USD).
        
        Returns:
            Tupla (is_valid, actual_value)
        """
        actual_value = order_size * current_price
        is_valid = actual_value >= min_value_usd
        
        logger.debug(f"  [VALUE] {order_size} * ${current_price:,.2f} = ${actual_value:.2f}")
        logger.debug(f"  [VALUE] Mínimo: ${min_value_usd:.2f} | Válido: {is_valid}")
        
        return is_valid, actual_value
    
    def execute_short(self, symbol: str, order_value_usd: float) -> OrderResult:
        """
        Executa uma ordem SHORT (venda) com todas as validações.
        
        SHORT = Apostar na queda do preço
        - is_buy = False (vender)
        - reduce_only = False (abrir posição)
        - limit_px = preço atual * 0.95 (5% abaixo)
        
        Args:
            symbol: Símbolo do ativo (ex: "BTC", "ETH")
            order_value_usd: Valor da ordem em USD
            
        Returns:
            OrderResult com detalhes da execução
        """
        logger.info("="*60)
        logger.info(f"EXECUTANDO SHORT: {symbol}")
        logger.info(f"Valor desejado: ${order_value_usd:.2f} USD")
        logger.info("="*60)
        
        try:
            # PASSO 1: Obter preço atual
            logger.info("[1/6] Obtendo preço atual...")
            all_mids = self.info.all_mids()
            
            if symbol not in all_mids:
                error_msg = f"Ativo {symbol} não encontrado"
                logger.error(f"❌ {error_msg}")
                return OrderResult(False, error_msg)
            
            current_price = float(all_mids[symbol])
            logger.info(f"  ✅ Preço atual: ${current_price:,.2f}")
            
            # PASSO 2: Calcular tamanho
            logger.info("[2/6] Calculando tamanho da ordem...")
            raw_size = order_value_usd / current_price
            order_size = self._round_size(raw_size, symbol)
            logger.info(f"  ✅ Tamanho: {order_size} {symbol}")
            
            # PASSO 3: Validar valor mínimo
            logger.info("[3/6] Validando valor mínimo...")
            is_valid, actual_value = self._validate_order_value(order_size, current_price)
            
            if not is_valid:
                error_msg = f"Valor da ordem ${actual_value:.2f} abaixo do mínimo $10.00"
                logger.error(f"❌ {error_msg}")
                return OrderResult(False, error_msg)
            
            logger.info(f"  ✅ Valor real: ${actual_value:.2f} USD")
            
            # PASSO 4: Calcular preço limite
            logger.info("[4/6] Calculando preço limite...")
            slippage = 0.05  # 5%
            limit_price_raw = current_price * (1 - slippage)  # SHORT = vender abaixo
            limit_price = self._round_price(limit_price_raw, symbol)
            logger.info(f"  ✅ Preço limite: ${limit_price:,.2f} (5% abaixo)")
            
            # PASSO 5: Executar ordem
            logger.info("[5/6] Executando ordem SHORT...")
            logger.info(f"  Parâmetros:")
            logger.info(f"    - name: {symbol}")
            logger.info(f"    - is_buy: False (SHORT)")
            logger.info(f"    - sz: {order_size}")
            logger.info(f"    - limit_px: {limit_price}")
            logger.info(f"    - order_type: Ioc (Market)")
            logger.info(f"    - reduce_only: False (Abrir posição)")
            
            result = self.exchange.order(
                name=symbol,
                is_buy=False,  # SHORT
                sz=order_size,
                limit_px=limit_price,
                order_type={"limit": {"tif": "Ioc"}},
                reduce_only=False
            )
            
            # PASSO 6: Verificar resultado
            logger.info("[6/6] Verificando resultado...")
            
            if result.get("status") == "ok":
                response = result.get("response", {})
                data = response.get("data", {})
                statuses = data.get("statuses", [])
                
                if statuses and "filled" in statuses[0]:
                    filled = statuses[0]["filled"]
                    
                    order_id = filled.get("oid")
                    filled_size = float(filled.get("totalSz", 0))
                    avg_price = float(filled.get("avgPx", 0))
                    total_value = filled_size * avg_price
                    
                    logger.info("="*60)
                    logger.info("✅ SHORT EXECUTADO COM SUCESSO!")
                    logger.info(f"  Order ID: {order_id}")
                    logger.info(f"  Tamanho: {filled_size} {symbol}")
                    logger.info(f"  Preço médio: ${avg_price:,.2f}")
                    logger.info(f"  Valor total: ${total_value:.2f} USD")
                    logger.info("="*60)
                    
                    return OrderResult(
                        success=True,
                        message="Ordem executada com sucesso",
                        order_id=order_id,
                        filled_size=filled_size,
                        avg_price=avg_price,
                        total_value=total_value
                    )
                else:
                    error_msg = f"Ordem não executada: {statuses}"
                    logger.warning(f"⚠️ {error_msg}")
                    return OrderResult(False, error_msg)
            else:
                error_msg = f"Erro da API: {result}"
                logger.error(f"❌ {error_msg}")
                return OrderResult(False, error_msg)
                
        except Exception as e:
            error_msg = f"Exceção: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return OrderResult(False, error_msg)
    
    def execute_long(self, symbol: str, order_value_usd: float) -> OrderResult:
        """
        Executa uma ordem LONG (compra) com todas as validações.
        
        LONG = Apostar na alta do preço
        - is_buy = True (comprar)
        - reduce_only = False (abrir posição)
        - limit_px = preço atual * 1.05 (5% acima)
        
        Args:
            symbol: Símbolo do ativo (ex: "BTC", "ETH")
            order_value_usd: Valor da ordem em USD
            
        Returns:
            OrderResult com detalhes da execução
        """
        logger.info("="*60)
        logger.info(f"EXECUTANDO LONG: {symbol}")
        logger.info(f"Valor desejado: ${order_value_usd:.2f} USD")
        logger.info("="*60)
        
        try:
            # PASSO 1: Obter preço atual
            logger.info("[1/6] Obtendo preço atual...")
            all_mids = self.info.all_mids()
            
            if symbol not in all_mids:
                error_msg = f"Ativo {symbol} não encontrado"
                logger.error(f"❌ {error_msg}")
                return OrderResult(False, error_msg)
            
            current_price = float(all_mids[symbol])
            logger.info(f"  ✅ Preço atual: ${current_price:,.2f}")
            
            # PASSO 2: Calcular tamanho
            logger.info("[2/6] Calculando tamanho da ordem...")
            raw_size = order_value_usd / current_price
            order_size = self._round_size(raw_size, symbol)
            logger.info(f"  ✅ Tamanho: {order_size} {symbol}")
            
            # PASSO 3: Validar valor mínimo
            logger.info("[3/6] Validando valor mínimo...")
            is_valid, actual_value = self._validate_order_value(order_size, current_price)
            
            if not is_valid:
                error_msg = f"Valor da ordem ${actual_value:.2f} abaixo do mínimo $10.00"
                logger.error(f"❌ {error_msg}")
                return OrderResult(False, error_msg)
            
            logger.info(f"  ✅ Valor real: ${actual_value:.2f} USD")
            
            # PASSO 4: Calcular preço limite
            logger.info("[4/6] Calculando preço limite...")
            slippage = 0.05  # 5%
            limit_price_raw = current_price * (1 + slippage)  # LONG = comprar acima
            limit_price = self._round_price(limit_price_raw, symbol)
            logger.info(f"  ✅ Preço limite: ${limit_price:,.2f} (5% acima)")
            
            # PASSO 5: Executar ordem
            logger.info("[5/6] Executando ordem LONG...")
            logger.info(f"  Parâmetros:")
            logger.info(f"    - name: {symbol}")
            logger.info(f"    - is_buy: True (LONG)")
            logger.info(f"    - sz: {order_size}")
            logger.info(f"    - limit_px: {limit_price}")
            logger.info(f"    - order_type: Ioc (Market)")
            logger.info(f"    - reduce_only: False (Abrir posição)")
            
            result = self.exchange.order(
                name=symbol,
                is_buy=True,  # LONG
                sz=order_size,
                limit_px=limit_price,
                order_type={"limit": {"tif": "Ioc"}},
                reduce_only=False
            )
            
            # PASSO 6: Verificar resultado
            logger.info("[6/6] Verificando resultado...")
            
            if result.get("status") == "ok":
                response = result.get("response", {})
                data = response.get("data", {})
                statuses = data.get("statuses", [])
                
                if statuses and "filled" in statuses[0]:
                    filled = statuses[0]["filled"]
                    
                    order_id = filled.get("oid")
                    filled_size = float(filled.get("totalSz", 0))
                    avg_price = float(filled.get("avgPx", 0))
                    total_value = filled_size * avg_price
                    
                    logger.info("="*60)
                    logger.info("✅ LONG EXECUTADO COM SUCESSO!")
                    logger.info(f"  Order ID: {order_id}")
                    logger.info(f"  Tamanho: {filled_size} {symbol}")
                    logger.info(f"  Preço médio: ${avg_price:,.2f}")
                    logger.info(f"  Valor total: ${total_value:.2f} USD")
                    logger.info("="*60)
                    
                    return OrderResult(
                        success=True,
                        message="Ordem executada com sucesso",
                        order_id=order_id,
                        filled_size=filled_size,
                        avg_price=avg_price,
                        total_value=total_value
                    )
                else:
                    error_msg = f"Ordem não executada: {statuses}"
                    logger.warning(f"⚠️ {error_msg}")
                    return OrderResult(False, error_msg)
            else:
                error_msg = f"Erro da API: {result}"
                logger.error(f"❌ {error_msg}")
                return OrderResult(False, error_msg)
                
        except Exception as e:
            error_msg = f"Exceção: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return OrderResult(False, error_msg)
    
    def close_position(self, symbol: str, position_size: float, is_short: bool) -> OrderResult:
        """
        Fecha uma posição existente.
        
        Args:
            symbol: Símbolo do ativo
            position_size: Tamanho da posição a fechar
            is_short: True se for fechar SHORT, False se for fechar LONG
            
        Returns:
            OrderResult com detalhes da execução
        """
        action = "SHORT" if is_short else "LONG"
        logger.info("="*60)
        logger.info(f"FECHANDO POSIÇÃO {action}: {symbol}")
        logger.info(f"Tamanho: {position_size}")
        logger.info("="*60)
        
        try:
            # Obter preço atual
            all_mids = self.info.all_mids()
            current_price = float(all_mids[symbol])
            
            # Para fechar SHORT: comprar (is_buy=True)
            # Para fechar LONG: vender (is_buy=False)
            is_buy = is_short
            
            # Calcular preço limite
            slippage = 0.05
            if is_buy:
                limit_price_raw = current_price * (1 + slippage)
            else:
                limit_price_raw = current_price * (1 - slippage)
            
            limit_price = self._round_price(limit_price_raw, symbol)
            
            logger.info(f"Executando ordem para fechar {action}...")
            result = self.exchange.order(
                name=symbol,
                is_buy=is_buy,
                sz=position_size,
                limit_px=limit_price,
                order_type={"limit": {"tif": "Ioc"}},
                reduce_only=True  # Apenas fechar, não abrir posição oposta
            )
            
            if result.get("status") == "ok":
                statuses = result["response"]["data"]["statuses"]
                if statuses and "filled" in statuses[0]:
                    filled = statuses[0]["filled"]
                    logger.info(f"✅ Posição {action} fechada com sucesso!")
                    return OrderResult(
                        success=True,
                        message=f"Posição {action} fechada",
                        order_id=filled.get("oid"),
                        filled_size=float(filled.get("totalSz", 0)),
                        avg_price=float(filled.get("avgPx", 0))
                    )
            
            return OrderResult(False, f"Erro ao fechar posição: {result}")
            
        except Exception as e:
            return OrderResult(False, f"Exceção: {str(e)}")

# ============================================================
# FUNÇÃO PRINCIPAL DE DEMONSTRAÇÃO
# ============================================================

def main():
    """
    Demonstra o uso do executor para LONG e SHORT.
    
    ATENÇÃO: Este código está desabilitado por padrão.
    Para executar de verdade, descomente o bloco de confirmação.
    """
    
    print("\n" + "="*60)
    print("EXEMPLO COMPLETO: LONG E SHORT NA HYPERLIQUID")
    print("="*60)
    print()
    
    # Criar executor
    executor = HyperliquidExecutor(WALLET_ADDRESS, PRIVATE_KEY)
    
    # ========================================
    # EXEMPLO 1: SHORT de $100 em BTC
    # ========================================
    print("\n📊 EXEMPLO 1: SHORT de $100 em BTC")
    print("   (Apostar na queda do preço)")
    print()
    
    # DESCOMENTE PARA EXECUTAR DE VERDADE:
    # confirmation = input("Digite 'SIM' para executar SHORT: ")
    # if confirmation == "SIM":
    #     result = executor.execute_short("BTC", 100.0)
    #     if result.success:
    #         print(f"\n✅ SHORT executado! Order ID: {result.order_id}")
    #     else:
    #         print(f"\n❌ Falha: {result.message}")
    # else:
    #     print("❌ Execução cancelada")
    
    print("🛑 EXECUÇÃO DESABILITADA - Descomente o código acima para executar")
    
    # ========================================
    # EXEMPLO 2: LONG de $50 em ETH
    # ========================================
    print("\n📊 EXEMPLO 2: LONG de $50 em ETH")
    print("   (Apostar na alta do preço)")
    print()
    
    # DESCOMENTE PARA EXECUTAR DE VERDADE:
    # confirmation = input("Digite 'SIM' para executar LONG: ")
    # if confirmation == "SIM":
    #     result = executor.execute_long("ETH", 50.0)
    #     if result.success:
    #         print(f"\n✅ LONG executado! Order ID: {result.order_id}")
    #     else:
    #         print(f"\n❌ Falha: {result.message}")
    # else:
    #     print("❌ Execução cancelada")
    
    print("🛑 EXECUÇÃO DESABILITADA - Descomente o código acima para executar")
    
    # ========================================
    # EXEMPLO 3: Fechar posição SHORT
    # ========================================
    print("\n📊 EXEMPLO 3: Fechar posição SHORT de 0.001 BTC")
    print()
    
    # DESCOMENTE PARA EXECUTAR DE VERDADE:
    # confirmation = input("Digite 'SIM' para fechar SHORT: ")
    # if confirmation == "SIM":
    #     result = executor.close_position("BTC", 0.001, is_short=True)
    #     if result.success:
    #         print(f"\n✅ Posição fechada! Order ID: {result.order_id}")
    #     else:
    #         print(f"\n❌ Falha: {result.message}")
    # else:
    #     print("❌ Execução cancelada")
    
    print("🛑 EXECUÇÃO DESABILITADA - Descomente o código acima para executar")
    
    print("\n" + "="*60)
    print("FIM DOS EXEMPLOS")
    print("="*60)
    print()
    print("💡 Para executar de verdade:")
    print("   1. Substitua WALLET_ADDRESS e PRIVATE_KEY no topo do arquivo")
    print("   2. Descomente os blocos de confirmação nos exemplos")
    print("   3. Execute: python3 example_long_short_complete.py")
    print()

if __name__ == "__main__":
    main()
