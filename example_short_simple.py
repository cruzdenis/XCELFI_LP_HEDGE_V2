"""
EXEMPLO SIMPLIFICADO: SHORT de $10 USD em BTC na Hyperliquid

Este é o código MÍNIMO necessário para executar uma ordem.
"""

from hyperliquid.exchange import Exchange
from hyperliquid.info import Info
from eth_account import Account

# ============================================================
# SUAS CREDENCIAIS
# ============================================================
WALLET_ADDRESS = "0xYOUR_WALLET_ADDRESS"
PRIVATE_KEY = "0xYOUR_PRIVATE_KEY"

# ============================================================
# PARÂMETROS DA ORDEM
# ============================================================
SYMBOL = "BTC"
ORDER_VALUE_USD = 10.0  # $10 USD

# ============================================================
# EXECUTAR SHORT
# ============================================================

# 1. Conectar
wallet = Account.from_key(PRIVATE_KEY)
exchange = Exchange(wallet)
info = Info()

# 2. Obter preço atual
all_mids = info.all_mids()
current_price = float(all_mids[SYMBOL])

# 3. Calcular tamanho
# BTC tem szDecimals=4, então arredondar para 4 casas
order_size = round(ORDER_VALUE_USD / current_price, 4)

# 4. Calcular preço limite (5% de slippage)
limit_price = round(current_price * 0.95, 2)  # SHORT = vender abaixo

# 5. Executar ordem
result = exchange.order(
    name=SYMBOL,
    is_buy=False,  # False = SHORT (vender)
    sz=order_size,
    limit_px=limit_price,
    order_type={"limit": {"tif": "Ioc"}},  # Market order
    reduce_only=False  # False = abrir posição
)

# 6. Verificar resultado
print(f"Status: {result.get('status')}")
if result.get("status") == "ok":
    response = result.get("response", {})
    data = response.get("data", {})
    statuses = data.get("statuses", [])
    
    if statuses and "filled" in statuses[0]:
        filled = statuses[0]["filled"]
        print(f"✅ Ordem executada!")
        print(f"   Order ID: {filled.get('oid')}")
        print(f"   Tamanho: {filled.get('totalSz')} {SYMBOL}")
        print(f"   Preço médio: ${filled.get('avgPx')}")
    else:
        print(f"⚠️ Ordem não executada: {statuses}")
else:
    print(f"❌ Erro: {result}")
