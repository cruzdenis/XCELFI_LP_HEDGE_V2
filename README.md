# XCELFI LP Hedge V3

Sistema simplificado de análise delta-neutral usando Octav.fi API para consultar posições LP e Hyperliquid.

## Arquitetura

### Consulta de Dados (Read-Only)
- **Octav.fi API**: Consulta posições LP (Revert, Uniswap V3, etc.) e posições Hyperliquid
- **Modo Análise**: Apenas leitura, sem necessidade de chaves privadas

### Execução (Opcional)
- **Hyperliquid API**: Execução de ordens short/long (requer API keys)

## Estrutura do Projeto

```
xcelfi_v3/
├── octav_client.py              # Cliente Octav.fi API
├── delta_neutral_analyzer.py    # Análise delta-neutral
├── test_app.py                  # Aplicação de teste
├── requirements.txt             # Dependências Python
└── README.md                    # Este arquivo
```

## Instalação

```bash
# Instalar dependências
pip install -r requirements.txt
```

## Configuração

### 1. Obter API Key do Octav.fi

1. Acesse: https://data.octav.fi
2. Crie uma conta ou faça login
3. Vá para API section
4. Gere uma nova API key
5. Copie a chave

### 2. Configurar Variável de Ambiente

```bash
export OCTAV_API_KEY='sua_chave_aqui'
```

## Uso

### Teste Básico

```bash
python test_app.py
```

### Exemplo de Saída

```
================================================================================
XCELFI LP HEDGE V3 - TEST APPLICATION
================================================================================

📍 Wallet Address: 0xc1E18438Fed146D814418364134fE28cC8622B5C
🔑 Octav API Key: eyJhbGciO...

🔄 Inicializando Octav.fi client...
🔄 Inicializando Delta Neutral Analyzer...

--------------------------------------------------------------------------------
📊 BUSCANDO DADOS DO PORTFÓLIO...
--------------------------------------------------------------------------------

💰 Net Worth: $102.70

--------------------------------------------------------------------------------
🏦 POSIÇÕES LP (Liquidity Provider)
--------------------------------------------------------------------------------

   Revert (arbitrum):
      WBTC: 0.000400 @ $103188.39 = $43.20
      WETH: 0.012500 @ $3445.93 = $43.22

   📊 Balanços Agregados LP:
      BTC: 0.000400
      ETH: 0.012500

--------------------------------------------------------------------------------
📉 POSIÇÕES SHORT (Hyperliquid)
--------------------------------------------------------------------------------

   BTC SHORT:
      Size: -0.000400
      Mark Price: $103159.00
      Position Value: $40.23

   ETH SHORT:
      Size: -0.013300
      Mark Price: $3439.20
      Position Value: $45.74

   📊 Balanços Agregados Short:
      BTC: 0.000400
      ETH: 0.013300

--------------------------------------------------------------------------------
🎯 ANÁLISE DELTA NEUTRAL
--------------------------------------------------------------------------------

================================================================================
ANÁLISE DELTA NEUTRAL - SUGESTÕES DE AJUSTE
================================================================================

📊 RESUMO:
   ✅ Posições Balanceadas: 1
   ⚠️  Posições Sub-Hedge: 0
   ⚠️  Posições Sobre-Hedge: 1

--------------------------------------------------------------------------------

✅ POSIÇÕES BALANCEADAS (dentro da tolerância de 5.0%)

   BTC:
      LP: 0.000400
      Short: 0.000400
      Diferença: +0.000000 (0.00%)

⚠️  POSIÇÕES SOBRE-HEDGE (precisa diminuir short)

   ETH:
      LP: 0.012500
      Short Atual: 0.013300
      Short Alvo: 0.012500
      ➡️  AÇÃO: DIMINUIR SHORT em 0.000800 ETH
      Diferença: 6.40%

--------------------------------------------------------------------------------

📋 AÇÕES NECESSÁRIAS:

   • DIMINUIR SHORT ETH: 0.000800

================================================================================

--------------------------------------------------------------------------------
📋 RESUMO DE AÇÕES PARA HYPERLIQUID API
--------------------------------------------------------------------------------

   DIMINUIR SHORT:
      • ETH: -0.000800

   ⚠️  NOTA: Execução via Hyperliquid API requer configuração adicional

================================================================================
✅ TESTE CONCLUÍDO COM SUCESSO!
================================================================================
```

## Funcionalidades

### ✅ Implementado

- [x] Cliente Octav.fi API
- [x] Extração de posições LP (Revert, Uniswap V3, etc.)
- [x] Extração de posições Hyperliquid
- [x] Normalização de símbolos (WETH → ETH, WBTC → BTC)
- [x] Agregação de balanços por token
- [x] Análise delta-neutral
- [x] Sugestões de ajuste
- [x] Relatório formatado

### 🔜 Próximos Passos

- [ ] Cliente Hyperliquid API para execução
- [ ] Interface web (Streamlit)
- [ ] Histórico de ajustes
- [ ] Alertas automáticos
- [ ] Modo de execução automática

## Limitações Atuais

### Octav.fi Portfolio Endpoint

O endpoint `/v1/portfolio` do Octav.fi retorna informações básicas sobre posições Hyperliquid, mas **não inclui**:
- Leverage detalhado
- Entry price
- Open P&L
- Funding rate

Para obter esses dados detalhados, existem duas opções:
1. Usar a API própria do Hyperliquid (recomendado para execução)
2. Usar um endpoint mais específico do Octav.fi (se disponível)

## Estratégia Delta-Neutral

### Conceito

Manter exposição zero ao preço dos ativos:
- **LP Positions**: Contêm tokens (ETH, BTC) → Exposição LONG
- **Short Positions**: Posições short na Hyperliquid → Exposição SHORT
- **Delta Neutral**: LP Balance = Short Balance para cada token

### Tolerância

- **Padrão**: 5% de diferença é aceitável
- **Balanceado**: Diferença ≤ 5%
- **Sub-Hedge**: LP > Short (precisa aumentar short)
- **Sobre-Hedge**: LP < Short (precisa diminuir short)

### Exemplo

```
LP: 1.0 ETH
Short: 1.05 ETH
Diferença: -0.05 ETH (5%)
Status: Balanceado (dentro de 5%)

LP: 1.0 ETH
Short: 1.10 ETH
Diferença: -0.10 ETH (10%)
Status: Sobre-Hedge
Ação: Diminuir short em 0.10 ETH
```

## Segurança

### Modo Análise (Atual)
- ✅ Apenas leitura via Octav.fi API
- ✅ Não requer chaves privadas
- ✅ Não pode executar trades
- ✅ Seguro para testes e validação

### Modo Execução (Futuro)
- ⚠️ Requer Hyperliquid API keys
- ⚠️ Pode executar trades reais
- ⚠️ Implementar safety checks
- ⚠️ Começar com valores pequenos

## Suporte

Para questões ou problemas:
1. Verifique a documentação do Octav.fi: https://docs.octav.fi
2. Verifique os logs de erro
3. Teste com valores pequenos primeiro

## Licença

MIT License
