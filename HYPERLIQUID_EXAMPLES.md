# 🎯 Guia Completo: Executar Ordens na Hyperliquid

## 📋 Índice

1. [Conceitos Básicos](#conceitos-básicos)
2. [Exemplo Simples: SHORT $10 em BTC](#exemplo-simples)
3. [Exemplo Completo com Validações](#exemplo-completo)
4. [Parâmetros Importantes](#parâmetros-importantes)
5. [Tipos de Ordem](#tipos-de-ordem)
6. [Tratamento de Erros](#tratamento-de-erros)
7. [Referência Rápida](#referência-rápida)

---

## 🎓 Conceitos Básicos

### O que é SHORT?
- **SHORT** = Vender um ativo que você não possui (apostar na queda)
- **LONG** = Comprar um ativo (apostar na alta)

### O que é REDUCE_ONLY?
- `reduce_only=False` → Abre ou aumenta uma posição
- `reduce_only=True` → Apenas fecha/reduz uma posição existente

### Precisão de Preços e Tamanhos
A Hyperliquid tem regras específicas:

| Ativo | szDecimals | Exemplo de Tamanho | Max Decimais Preço |
|-------|------------|-------------------|-------------------|
| BTC   | 4          | 0.0001 BTC        | 2 (ex: 95432.12)  |
| ETH   | 3          | 0.001 ETH         | 3 (ex: 3456.789)  |
| SOL   | 2          | 0.01 SOL          | 4 (ex: 123.4567)  |

**Regras:**
- **Tamanho**: Arredondar para `szDecimals` casas decimais
- **Preço**: Máximo 5 dígitos significativos E máximo `(6 - szDecimals)` casas decimais

---

## 🚀 Exemplo Simples

### SHORT de $10 USD em BTC

```python
from hyperliquid.exchange import Exchange
from hyperliquid.info import Info
from eth_account import Account

# 1. CONFIGURAÇÃO
WALLET_ADDRESS = "0xYOUR_WALLET_ADDRESS"
PRIVATE_KEY = "0xYOUR_PRIVATE_KEY"
SYMBOL = "BTC"
ORDER_VALUE_USD = 10.0

# 2. CONECTAR
wallet = Account.from_key(PRIVATE_KEY)
exchange = Exchange(wallet)
info = Info()

# 3. OBTER PREÇO ATUAL
all_mids = info.all_mids()
current_price = float(all_mids[SYMBOL])
print(f"Preço atual de {SYMBOL}: ${current_price:,.2f}")

# 4. CALCULAR TAMANHO
# BTC tem szDecimals=4
order_size = round(ORDER_VALUE_USD / current_price, 4)
print(f"Tamanho da ordem: {order_size} {SYMBOL}")

# 5. CALCULAR PREÇO LIMITE
# SHORT = vender, então usar preço abaixo (5% slippage)
limit_price = round(current_price * 0.95, 2)
print(f"Preço limite: ${limit_price:,.2f}")

# 6. EXECUTAR ORDEM SHORT
result = exchange.order(
    name=SYMBOL,
    is_buy=False,  # False = SHORT (vender)
    sz=order_size,
    limit_px=limit_price,
    order_type={"limit": {"tif": "Ioc"}},  # Market order
    reduce_only=False  # Abrir posição
)

# 7. VERIFICAR RESULTADO
if result.get("status") == "ok":
    response = result.get("response", {})
    data = response.get("data", {})
    statuses = data.get("statuses", [])
    
    if statuses and "filled" in statuses[0]:
        filled = statuses[0]["filled"]
        print(f"✅ SHORT executado!")
        print(f"   Order ID: {filled.get('oid')}")
        print(f"   Tamanho: {filled.get('totalSz')} {SYMBOL}")
        print(f"   Preço médio: ${filled.get('avgPx')}")
    else:
        print(f"⚠️ Ordem não executada: {statuses}")
else:
    print(f"❌ Erro: {result}")
```

---

## 📊 Exemplo Completo

### Com Validações e Tratamento de Erros

```python
from hyperliquid.exchange import Exchange
from hyperliquid.info import Info
from eth_account import Account
from math import log10, floor

def round_size(size: float, sz_decimals: int) -> float:
    """Arredonda tamanho de acordo com szDecimals"""
    return round(size, sz_decimals)

def round_price(price: float, sz_decimals: int) -> float:
    """Arredonda preço com 5 dígitos significativos"""
    if price == 0:
        return 0.0
    
    # 5 dígitos significativos
    magnitude = floor(log10(abs(price)))
    sig_fig_decimals = 5 - magnitude - 1
    price_5sig = round(price, sig_fig_decimals)
    
    # Limite de casas decimais
    max_decimals = 6 - sz_decimals
    final_price = round(price_5sig, max_decimals)
    
    # Remover zeros à direita
    formatted = f"{final_price:.{max_decimals}f}".rstrip('0').rstrip('.')
    return float(formatted)

def execute_short(wallet_address: str, private_key: str, 
                  symbol: str, order_value_usd: float):
    """
    Executa um SHORT com validações completas
    """
    try:
        # 1. Conectar
        print("📡 Conectando à Hyperliquid...")
        wallet = Account.from_key(private_key)
        exchange = Exchange(wallet)
        info = Info()
        print(f"✅ Conectado! Wallet: {wallet_address}")
        
        # 2. Obter metadados do ativo
        print(f"\n📊 Obtendo metadados de {symbol}...")
        meta = info.meta()
        asset_meta = None
        
        if meta and 'universe' in meta:
            for asset_info in meta['universe']:
                if asset_info.get('name') == symbol:
                    asset_meta = {
                        'szDecimals': asset_info.get('szDecimals', 3),
                        'maxLeverage': asset_info.get('maxLeverage', 1)
                    }
                    break
        
        if not asset_meta:
            # Defaults
            defaults = {
                'BTC': {'szDecimals': 4, 'maxLeverage': 50},
                'ETH': {'szDecimals': 3, 'maxLeverage': 50}
            }
            asset_meta = defaults.get(symbol, {'szDecimals': 3, 'maxLeverage': 1})
        
        sz_decimals = asset_meta['szDecimals']
        print(f"   • szDecimals: {sz_decimals}")
        print(f"   • Max Leverage: {asset_meta['maxLeverage']}x")
        
        # 3. Obter preço atual
        print(f"\n💰 Obtendo preço atual de {symbol}...")
        all_mids = info.all_mids()
        
        if symbol not in all_mids:
            print(f"❌ Ativo {symbol} não encontrado!")
            return None
        
        current_price = float(all_mids[symbol])
        print(f"   • Preço atual: ${current_price:,.2f}")
        
        # 4. Calcular tamanho
        print(f"\n🧮 Calculando tamanho da ordem...")
        raw_size = order_value_usd / current_price
        order_size = round_size(raw_size, sz_decimals)
        actual_value = order_size * current_price
        
        print(f"   • Tamanho bruto: {raw_size:.8f} {symbol}")
        print(f"   • Tamanho arredondado: {order_size} {symbol}")
        print(f"   • Valor real: ${actual_value:.2f} USD")
        
        # Verificar mínimo
        if actual_value < 10.0:
            print(f"\n⚠️ AVISO: Valor ${actual_value:.2f} abaixo do mínimo $10 USD")
            print("   A ordem pode ser rejeitada!")
        
        # 5. Calcular preço limite
        print(f"\n📈 Calculando preço limite...")
        slippage = 0.05  # 5%
        limit_price_raw = current_price * (1 - slippage)  # SHORT = vender abaixo
        limit_price = round_price(limit_price_raw, sz_decimals)
        
        print(f"   • Preço limite: ${limit_price:,.2f}")
        print(f"   • Slippage: {slippage * 100}%")
        
        # 6. Confirmar execução
        print(f"\n📝 Resumo da ordem:")
        print(f"   • Ativo: {symbol}")
        print(f"   • Ação: SHORT (vender)")
        print(f"   • Tamanho: {order_size} {symbol}")
        print(f"   • Preço limite: ${limit_price:,.2f}")
        print(f"   • Valor: ${actual_value:.2f} USD")
        
        confirmation = input("\n⚠️  Digite 'SIM' para confirmar: ")
        if confirmation != "SIM":
            print("❌ Execução cancelada")
            return None
        
        # 7. Executar ordem
        print("\n🚀 Executando ordem SHORT...")
        result = exchange.order(
            name=symbol,
            is_buy=False,  # SHORT = vender
            sz=order_size,
            limit_px=limit_price,
            order_type={"limit": {"tif": "Ioc"}},
            reduce_only=False
        )
        
        # 8. Processar resultado
        print("\n📊 Resultado:")
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
                
                print(f"✅ ORDEM EXECUTADA COM SUCESSO!")
                print(f"   • Order ID: {order_id}")
                print(f"   • Tamanho executado: {filled_size} {symbol}")
                print(f"   • Preço médio: ${avg_price:,.2f}")
                print(f"   • Valor total: ${total_value:.2f} USD")
                
                return {
                    'success': True,
                    'order_id': order_id,
                    'filled_size': filled_size,
                    'avg_price': avg_price,
                    'total_value': total_value
                }
            else:
                print(f"⚠️ Ordem não executada: {statuses}")
                return {'success': False, 'message': str(statuses)}
        else:
            print(f"❌ Erro na execução: {result}")
            return {'success': False, 'message': str(result)}
            
    except Exception as e:
        print(f"❌ Exceção: {e}")
        return {'success': False, 'message': str(e)}

# USO:
if __name__ == "__main__":
    WALLET_ADDRESS = "0xYOUR_WALLET_ADDRESS"
    PRIVATE_KEY = "0xYOUR_PRIVATE_KEY"
    
    result = execute_short(
        wallet_address=WALLET_ADDRESS,
        private_key=PRIVATE_KEY,
        symbol="BTC",
        order_value_usd=10.0
    )
    
    if result and result.get('success'):
        print(f"\n🎉 SHORT de BTC executado com sucesso!")
    else:
        print(f"\n❌ Falha na execução")
```

---

## ⚙️ Parâmetros Importantes

### `exchange.order()` - Parâmetros

```python
result = exchange.order(
    name="BTC",              # Símbolo do ativo
    is_buy=False,            # True = LONG (comprar), False = SHORT (vender)
    sz=0.0001,               # Tamanho da ordem (arredondado para szDecimals)
    limit_px=95000.0,        # Preço limite (arredondado com 5 sig figs)
    order_type={             # Tipo de ordem
        "limit": {
            "tif": "Ioc"     # Ioc = Immediate or Cancel (market)
        }
    },
    reduce_only=False        # False = abrir, True = apenas fechar
)
```

### Tipos de Ordem (`order_type`)

| Tipo | Descrição | Uso |
|------|-----------|-----|
| `{"limit": {"tif": "Ioc"}}` | Market order (executa imediatamente ou cancela) | Ordens rápidas |
| `{"limit": {"tif": "Gtc"}}` | Limit order (fica no book até executar) | Ordens com preço específico |
| `{"limit": {"tif": "Alo"}}` | Add Liquidity Only (só maker) | Evitar taxas de taker |

### Ações Comuns

| Ação | `is_buy` | `reduce_only` | Descrição |
|------|----------|---------------|-----------|
| Abrir SHORT | `False` | `False` | Vender para abrir posição short |
| Fechar SHORT | `True` | `True` | Comprar para fechar posição short |
| Abrir LONG | `True` | `False` | Comprar para abrir posição long |
| Fechar LONG | `False` | `True` | Vender para fechar posição long |

---

## 🔄 Tipos de Ordem

### 1. Market Order (Execução Imediata)

```python
# Executa ao melhor preço disponível
result = exchange.order(
    name="BTC",
    is_buy=False,
    sz=0.0001,
    limit_px=current_price * 0.95,  # 5% slippage
    order_type={"limit": {"tif": "Ioc"}},  # Immediate or Cancel
    reduce_only=False
)
```

### 2. Limit Order (Preço Específico)

```python
# Fica no order book até executar
result = exchange.order(
    name="BTC",
    is_buy=False,
    sz=0.0001,
    limit_px=95000.0,  # Preço exato
    order_type={"limit": {"tif": "Gtc"}},  # Good til Cancel
    reduce_only=False
)
```

### 3. Maker-Only Order

```python
# Apenas adiciona liquidez (sem pagar taxa de taker)
result = exchange.order(
    name="BTC",
    is_buy=False,
    sz=0.0001,
    limit_px=95000.0,
    order_type={"limit": {"tif": "Alo"}},  # Add Liquidity Only
    reduce_only=False
)
```

---

## ❌ Tratamento de Erros

### Erros Comuns

| Erro | Causa | Solução |
|------|-------|---------|
| "Order value too small" | Ordem < $10 USD | Aumentar tamanho |
| "Invalid size precision" | Tamanho com decimais errados | Usar `round(size, szDecimals)` |
| "Invalid price precision" | Preço com muitos dígitos | Usar função `round_price()` |
| "Insufficient margin" | Saldo insuficiente | Depositar mais fundos |
| "Position limit exceeded" | Posição muito grande | Reduzir tamanho |

### Exemplo de Tratamento

```python
try:
    result = exchange.order(...)
    
    if result.get("status") == "ok":
        # Sucesso
        response = result.get("response", {})
        data = response.get("data", {})
        statuses = data.get("statuses", [])
        
        if statuses and "filled" in statuses[0]:
            print("✅ Ordem executada!")
        else:
            print(f"⚠️ Ordem não executada: {statuses}")
    else:
        # Erro da API
        print(f"❌ Erro: {result}")
        
except Exception as e:
    # Exceção Python
    print(f"❌ Exceção: {e}")
```

---

## 📚 Referência Rápida

### SHORT $10 em BTC (1 linha)

```python
exchange.order("BTC", False, round(10/float(info.all_mids()["BTC"]), 4), round(float(info.all_mids()["BTC"])*0.95, 2), {"limit":{"tif":"Ioc"}}, False)
```

### LONG $10 em ETH

```python
exchange.order("ETH", True, round(10/float(info.all_mids()["ETH"]), 3), round(float(info.all_mids()["ETH"])*1.05, 3), {"limit":{"tif":"Ioc"}}, False)
```

### Fechar SHORT de 0.0001 BTC

```python
exchange.order("BTC", True, 0.0001, round(float(info.all_mids()["BTC"])*1.05, 2), {"limit":{"tif":"Ioc"}}, True)
```

### Obter Posições Abertas

```python
user_state = exchange.info.user_state(WALLET_ADDRESS)
positions = user_state.get('assetPositions', [])
for pos in positions:
    print(f"{pos['position']['coin']}: {pos['position']['szi']} @ ${pos['position']['entryPx']}")
```

### Obter Saldo da Conta

```python
user_state = exchange.info.user_state(WALLET_ADDRESS)
account_value = float(user_state['marginSummary']['accountValue'])
print(f"Saldo: ${account_value:,.2f}")
```

---

## 🎯 Checklist de Execução

Antes de executar uma ordem, verifique:

- [ ] Private key está correta
- [ ] Wallet address está correto
- [ ] Símbolo do ativo está correto (BTC, ETH, etc)
- [ ] Tamanho está arredondado para `szDecimals`
- [ ] Preço está arredondado com 5 dígitos significativos
- [ ] Valor da ordem é >= $10 USD
- [ ] `is_buy` está correto (False = SHORT, True = LONG)
- [ ] `reduce_only` está correto (False = abrir, True = fechar)
- [ ] Slippage é adequado (5% para market orders)
- [ ] Você tem saldo suficiente na conta

---

## 📞 Suporte

- **Documentação oficial**: https://hyperliquid.gitbook.io/hyperliquid-docs/
- **SDK Python**: https://github.com/hyperliquid-dex/hyperliquid-python-sdk
- **Discord**: https://discord.gg/hyperliquid

---

**⚠️ AVISO**: Trading de derivativos envolve risco significativo. Use apenas fundos que você pode perder. Este guia é apenas para fins educacionais.
