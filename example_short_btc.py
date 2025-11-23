"""
Exemplo: Como executar um SHORT de $10 USD em BTC na Hyperliquid

Este script demonstra como:
1. Conectar à API da Hyperliquid
2. Calcular o tamanho da ordem baseado no valor em USD
3. Executar uma ordem SHORT (venda) com precisão correta
4. Verificar o resultado da execução
"""

from hyperliquid.exchange import Exchange
from hyperliquid.info import Info
from eth_account import Account
from math import log10, floor

# ============================================================
# CONFIGURAÇÃO - SUBSTITUA COM SUAS CREDENCIAIS
# ============================================================
WALLET_ADDRESS = "0xYOUR_WALLET_ADDRESS_HERE"
PRIVATE_KEY = "0xYOUR_PRIVATE_KEY_HERE"  # Private key da API wallet

# Parâmetros da ordem
SYMBOL = "BTC"              # Ativo a operar
ORDER_VALUE_USD = 10.0      # Valor da ordem em USD
ACTION = "SHORT"            # SHORT (venda) ou LONG (compra)

# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def round_size(size: float, sz_decimals: int) -> float:
    """
    Arredonda o tamanho da ordem de acordo com szDecimals do ativo
    
    Exemplos:
    - BTC tem szDecimals=4 → 0.0001 BTC
    - ETH tem szDecimals=3 → 0.001 ETH
    """
    return round(size, sz_decimals)


def round_price(price: float, sz_decimals: int) -> float:
    """
    Arredonda o preço de acordo com as regras da Hyperliquid:
    - Máximo 5 dígitos significativos
    - Máximo (6 - szDecimals) casas decimais para perps
    
    Exemplos:
    - BTC (szDecimals=4): preço 95432.123456 → 95432 (5 sig figs, 2 decimais max)
    - ETH (szDecimals=3): preço 3456.789123 → 3456.8 (5 sig figs, 3 decimals max)
    """
    if price == 0:
        return 0.0
    
    # Limitar a 5 dígitos significativos
    magnitude = floor(log10(abs(price)))
    sig_fig_decimals = 5 - magnitude - 1  # 5 = max sig figs
    price_5sig = round(price, sig_fig_decimals)
    
    # Aplicar limite de casas decimais
    max_decimals = 6 - sz_decimals  # Regra para perps
    final_price = round(price_5sig, max_decimals)
    
    # Formatar removendo zeros à direita (necessário para assinatura)
    formatted = f"{final_price:.{max_decimals}f}".rstrip('0').rstrip('.')
    return float(formatted)


def get_asset_metadata(info: Info, symbol: str) -> dict:
    """
    Obtém metadados do ativo (szDecimals, maxLeverage, etc)
    """
    try:
        meta = info.meta()
        if meta and 'universe' in meta:
            for asset_info in meta['universe']:
                if asset_info.get('name') == symbol:
                    return {
                        'szDecimals': asset_info.get('szDecimals', 3),
                        'maxLeverage': asset_info.get('maxLeverage', 1)
                    }
    except Exception as e:
        print(f"⚠️ Erro ao obter metadata: {e}")
    
    # Defaults para ativos comuns
    defaults = {
        'BTC': {'szDecimals': 4, 'maxLeverage': 50},
        'ETH': {'szDecimals': 3, 'maxLeverage': 50},
        'SOL': {'szDecimals': 2, 'maxLeverage': 20}
    }
    return defaults.get(symbol, {'szDecimals': 3, 'maxLeverage': 1})


# ============================================================
# EXECUÇÃO PRINCIPAL
# ============================================================

def main():
    print("=" * 60)
    print("🎯 HYPERLIQUID - EXEMPLO DE ORDEM SHORT")
    print("=" * 60)
    print()
    
    # 1. CRIAR CONEXÃO COM A HYPERLIQUID
    print("📡 Conectando à Hyperliquid...")
    try:
        # Criar conta local a partir da private key
        wallet = Account.from_key(PRIVATE_KEY)
        
        # Criar objetos Exchange e Info
        exchange = Exchange(wallet)
        info = Info()
        
        print(f"✅ Conectado! Wallet: {WALLET_ADDRESS}")
        print()
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        return
    
    # 2. OBTER METADADOS DO ATIVO
    print(f"📊 Obtendo metadados de {SYMBOL}...")
    asset_meta = get_asset_metadata(info, SYMBOL)
    sz_decimals = asset_meta['szDecimals']
    max_leverage = asset_meta['maxLeverage']
    
    print(f"   • szDecimals: {sz_decimals}")
    print(f"   • Max Leverage: {max_leverage}x")
    print()
    
    # 3. OBTER PREÇO ATUAL
    print(f"💰 Obtendo preço atual de {SYMBOL}...")
    try:
        all_mids = info.all_mids()
        current_price = float(all_mids.get(SYMBOL, 0))
        
        if current_price == 0:
            print(f"❌ Não foi possível obter o preço de {SYMBOL}")
            return
        
        print(f"   • Preço atual: ${current_price:,.2f}")
        print()
    except Exception as e:
        print(f"❌ Erro ao obter preço: {e}")
        return
    
    # 4. CALCULAR TAMANHO DA ORDEM
    print(f"🧮 Calculando tamanho da ordem para ${ORDER_VALUE_USD} USD...")
    
    # Tamanho = Valor USD / Preço
    raw_size = ORDER_VALUE_USD / current_price
    
    # Arredondar de acordo com szDecimals
    order_size = round_size(raw_size, sz_decimals)
    
    # Valor real da ordem após arredondamento
    actual_value = order_size * current_price
    
    print(f"   • Tamanho bruto: {raw_size:.8f} {SYMBOL}")
    print(f"   • Tamanho arredondado: {order_size} {SYMBOL}")
    print(f"   • Valor real: ${actual_value:.2f} USD")
    print()
    
    # Verificar mínimo de $10 USD
    if actual_value < 10.0:
        print(f"⚠️ AVISO: Valor da ordem (${actual_value:.2f}) está abaixo do mínimo de $10 USD")
        print(f"   A Hyperliquid pode rejeitar esta ordem!")
        print()
    
    # 5. CALCULAR PREÇO LIMITE COM SLIPPAGE
    print("📈 Calculando preço limite com slippage...")
    
    # Para SHORT (venda): usar preço 5% abaixo do mercado
    # Para LONG (compra): usar preço 5% acima do mercado
    slippage = 0.05  # 5%
    
    if ACTION == "SHORT":
        is_buy = False
        limit_price_raw = current_price * (1 - slippage)
    else:  # LONG
        is_buy = True
        limit_price_raw = current_price * (1 + slippage)
    
    # Arredondar preço de acordo com as regras
    limit_price = round_price(limit_price_raw, sz_decimals)
    
    print(f"   • Preço limite bruto: ${limit_price_raw:,.2f}")
    print(f"   • Preço limite arredondado: ${limit_price:,.2f}")
    print(f"   • Slippage: {slippage * 100}%")
    print()
    
    # 6. PREPARAR ORDEM
    print("📝 Preparando ordem...")
    print(f"   • Ativo: {SYMBOL}")
    print(f"   • Ação: {ACTION} ({'SELL' if not is_buy else 'BUY'})")
    print(f"   • Tamanho: {order_size} {SYMBOL}")
    print(f"   • Preço limite: ${limit_price:,.2f}")
    print(f"   • Tipo: Market (IOC - Immediate or Cancel)")
    print()
    
    # 7. EXECUTAR ORDEM
    print("🚀 Executando ordem...")
    print("⚠️  ATENÇÃO: Esta é uma ordem REAL que será executada!")
    print()
    
    # DESCOMENTE AS LINHAS ABAIXO PARA EXECUTAR DE VERDADE
    # confirmation = input("Digite 'SIM' para confirmar a execução: ")
    # if confirmation != "SIM":
    #     print("❌ Execução cancelada pelo usuário")
    #     return
    
    print("🛑 EXECUÇÃO DESABILITADA - Este é apenas um exemplo!")
    print("   Para executar de verdade, descomente as linhas acima.")
    print()
    
    # CÓDIGO DE EXECUÇÃO (descomentado para referência)
    """
    try:
        # Tipo de ordem: Market com IOC (Immediate or Cancel)
        order_type = {"limit": {"tif": "Ioc"}}
        
        # Executar ordem
        result = exchange.order(
            name=SYMBOL,
            is_buy=is_buy,
            sz=order_size,
            limit_px=limit_price,
            order_type=order_type,
            reduce_only=False  # False = abrir/aumentar posição, True = apenas fechar
        )
        
        # Processar resultado
        print("📊 Resultado da execução:")
        print(f"   • Status: {result.get('status')}")
        
        if result.get("status") == "ok":
            response = result.get("response", {})
            data = response.get("data", {})
            statuses = data.get("statuses", [])
            
            if statuses:
                status = statuses[0]
                
                if "filled" in status:
                    filled = status["filled"]
                    order_id = filled.get("oid")
                    filled_size = float(filled.get("totalSz", 0))
                    avg_price = float(filled.get("avgPx", 0))
                    
                    print(f"✅ ORDEM EXECUTADA COM SUCESSO!")
                    print(f"   • Order ID: {order_id}")
                    print(f"   • Tamanho executado: {filled_size} {SYMBOL}")
                    print(f"   • Preço médio: ${avg_price:,.2f}")
                    print(f"   • Valor total: ${filled_size * avg_price:,.2f} USD")
                else:
                    print(f"⚠️ Ordem não executada: {status}")
        else:
            print(f"❌ Erro na execução: {result}")
            
    except Exception as e:
        print(f"❌ Exceção durante execução: {e}")
    """
    
    # 8. RESUMO
    print("=" * 60)
    print("📋 RESUMO DO EXEMPLO")
    print("=" * 60)
    print(f"Ativo: {SYMBOL}")
    print(f"Ação: {ACTION}")
    print(f"Valor desejado: ${ORDER_VALUE_USD} USD")
    print(f"Preço atual: ${current_price:,.2f}")
    print(f"Tamanho calculado: {order_size} {SYMBOL}")
    print(f"Valor real: ${actual_value:.2f} USD")
    print(f"Preço limite: ${limit_price:,.2f}")
    print()
    print("💡 Para executar de verdade:")
    print("   1. Substitua WALLET_ADDRESS e PRIVATE_KEY")
    print("   2. Descomente o código de confirmação")
    print("   3. Descomente o bloco de execução")
    print("   4. Execute: python3 example_short_btc.py")
    print()


if __name__ == "__main__":
    main()
