# XCELFI LP Hedge V4 - Guia Completo para Programadores

**Versão**: V4 (Novembro 2025)  
**Autor**: Sistema de hedge automático para LPs  
**Stack**: Python 3.11 + Streamlit + Octav.fi API + Hyperliquid API

---

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Arquitetura](#arquitetura)
3. [Estrutura de Arquivos](#estrutura-de-arquivos)
4. [Instalação e Setup](#instalação-e-setup)
5. [Configuração](#configuração)
6. [Funcionalidades Principais](#funcionalidades-principais)
7. [APIs e Integrações](#apis-e-integrações)
8. [Fluxo de Dados](#fluxo-de-dados)
9. [Deploy](#deploy)
10. [Troubleshooting](#troubleshooting)
11. [Changelog V4](#changelog-v4)

---

## 🎯 Visão Geral

### O que é este sistema?

Sistema automatizado de **hedge delta-neutral** para posições de Liquidity Provider (LP) em protocolos DeFi, usando shorts na Hyperliquid para neutralizar exposição a preço.

### Problema que resolve

Quando você fornece liquidez em pools (ex: WBTC/USDC no Uniswap), você fica exposto a **impermanent loss** se o preço do BTC mudar. Este sistema:

1. **Monitora** suas posições LP em múltiplos protocolos (Revert, Uniswap, etc.)
2. **Calcula** quanto de cada token você tem exposto
3. **Sugere** (ou executa) shorts na Hyperliquid para neutralizar
4. **Gerencia** alocação de capital entre LPs (85%) e margem Hyperliquid (15%)

### Tecnologias Principais

- **Frontend**: Streamlit (Python web framework)
- **APIs**: Octav.fi (portfolio data), Hyperliquid (perpetuals trading)
- **Deploy**: Railway (PaaS)
- **Storage**: JSON files (config, history)

---

## 🏗️ Arquitetura

### Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────┐
│                    STREAMLIT UI                         │
│  (app.py - 1500+ linhas)                                │
│  - Dashboard                                            │
│  - Configuração                                         │
│  - Posições LP                                          │
│  - Histórico                                            │
└─────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Octav Client │  │ Hyperliquid  │  │ Config Mgr   │
│              │  │ Client       │  │              │
│ - Get LP     │  │ - Get shorts │  │ - Save/Load  │
│   positions  │  │ - Execute    │  │ - History    │
│ - Universal  │  │   orders     │  │ - Quota      │
│   extractor  │  │ - Account    │  │              │
└──────────────┘  └──────────────┘  └──────────────┘
        │                 │                 │
        ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Octav.fi API │  │ Hyperliquid  │  │ /tmp/        │
│              │  │ API          │  │ xcelfi_data/ │
│ - Portfolio  │  │ - Perps      │  │              │
│ - Multi-     │  │ - Margin     │  │ - config.json│
│   protocol   │  │ - Prices     │  │ - history    │
└──────────────┘  └──────────────┘  └──────────────┘
```

### Componentes Core

| Arquivo | Função | Linhas |
|---------|--------|--------|
| `app.py` | Interface principal Streamlit | ~1500 |
| `octav_client.py` | Cliente Octav.fi (V3 - universal) | ~350 |
| `hyperliquid_client.py` | Cliente Hyperliquid | ~200 |
| `config_manager.py` | Gerenciamento de configuração | ~300 |
| `delta_neutral_analyzer.py` | Análise de hedge | ~150 |
| `capital_allocation_analyzer.py` | Análise de capital | ~200 |
| `quota_calculator.py` | Sistema de cotas (NAV) | ~100 |

---

## 📁 Estrutura de Arquivos

```
XCELFI_LP_HEDGE_V2/
│
├── app.py                          # ⭐ Aplicação principal Streamlit
├── requirements.txt                # Dependências Python
├── railway.toml                    # Config Railway deploy
├── nixpacks.toml                   # Build config
│
├── octav_client.py                 # ⭐ Cliente Octav.fi (V3 - universal)
├── octav_client_v2_backup.py       # Backup versão anterior
├── octav_client_old.py             # Versão original
│
├── hyperliquid_client.py           # ⭐ Cliente Hyperliquid
├── config_manager.py               # ⭐ Gerenciamento de config
├── delta_neutral_analyzer.py       # ⭐ Análise de hedge
├── capital_allocation_analyzer.py  # ⭐ Análise de capital
├── quota_calculator.py             # Sistema de cotas/NAV
│
├── example_short_btc.py            # Exemplo: short BTC
├── example_short_simple.py         # Exemplo: versão simples
├── example_long_short_complete.py  # Exemplo: completo
│
├── .streamlit/
│   └── config.toml                 # Config Streamlit
│
├── core/                           # Módulos auxiliares (não usados atualmente)
│   ├── auth.py
│   ├── config.py
│   ├── delta_neutral.py
│   ├── executor.py
│   ├── nav.py
│   ├── pnl.py
│   ├── safety.py
│   └── triggers.py
│
├── integrations/                   # Integrações (não usadas atualmente)
│   ├── aerodrome.py
│   ├── hyperliquid.py
│   ├── octav.py
│   └── uniswap.py
│
├── strategies/                     # Estratégias (não usadas atualmente)
│   └── recenter.py
│
├── ui/                             # UI components (não usados atualmente)
│   ├── __init__.py
│   └── settings_tab.py
│
├── utils/                          # Utilidades (não usadas atualmente)
│   ├── logs.py
│   └── ticks.py
│
└── DOCUMENTAÇÃO/
    ├── README.md                   # README principal
    ├── SETUP.md                    # Guia de setup
    ├── DEPLOYMENT.md               # Guia de deploy
    ├── RAILWAY_DEPLOY.md           # Deploy Railway
    ├── VERSION_HISTORY.md          # Histórico V3
    ├── V4_ROADMAP.md               # Roadmap V4
    │
    ├── V4_FEATURE_*.md             # Docs de features V4
    │   ├── V4_FEATURE_DOUBLE_SYNC.md
    │   ├── V4_FEATURE_CAPITAL_ALLOCATION.md
    │   ├── V4_FEATURE_RANGE_BASED_ALLOCATION.md
    │   ├── V4_FEATURE_UNIVERSAL_LP_EXTRACTOR.md
    │   └── V4_FEATURE_PROTOCOL_SELECTOR.md
    │
    ├── V4_BUGFIX_*.md              # Docs de bugfixes
    │   └── V4_BUGFIX_HYPERLIQUID_EQUITY.md
    │
    └── HYPERLIQUID_*.md            # Docs Hyperliquid
        ├── HYPERLIQUID_EXAMPLES.md
        └── HYPERLIQUID_TECHNICAL_GUIDE.md
```

### Arquivos Importantes

**⭐ Essenciais (não deletar):**
- `app.py` - Aplicação principal
- `octav_client.py` - Cliente Octav.fi
- `hyperliquid_client.py` - Cliente Hyperliquid
- `config_manager.py` - Config persistente
- `delta_neutral_analyzer.py` - Lógica de hedge
- `capital_allocation_analyzer.py` - Lógica de capital
- `requirements.txt` - Dependências

**📚 Documentação:**
- Todos os `.md` são documentação
- Podem ser lidos mas não são executados

**🗑️ Podem ser deletados:**
- `core/`, `integrations/`, `strategies/`, `ui/`, `utils/` (não usados)
- `app_*.py` (backups antigos)
- `test_*.py` (scripts de teste)
- `*_old.py`, `*_backup.py` (backups)

---

## 🚀 Instalação e Setup

### Requisitos

- Python 3.11+
- pip (gerenciador de pacotes Python)
- Git (opcional, para clone)

### Passo 1: Clone ou Baixe

```bash
# Opção 1: Git clone
git clone https://github.com/cruzdenis/XCELFI_LP_HEDGE_V2.git
cd XCELFI_LP_HEDGE_V2

# Opção 2: Baixar ZIP
# Extrair e entrar na pasta
```

### Passo 2: Criar Virtual Environment (Recomendado)

```bash
# Criar venv
python3.11 -m venv venv

# Ativar (Linux/Mac)
source venv/bin/activate

# Ativar (Windows)
venv\Scripts\activate
```

### Passo 3: Instalar Dependências

```bash
pip install -r requirements.txt
```

**Dependências principais:**
```
streamlit==1.31.0
requests==2.31.0
hyperliquid-python-sdk==0.4.0
eth-account==0.11.0
pandas==2.2.0
plotly==5.18.0
```

### Passo 4: Executar Localmente

```bash
streamlit run app.py
```

**Acesse**: http://localhost:8501

---

## ⚙️ Configuração

### 1. Octav.fi API Key

**Como obter:**
1. Acesse https://app.octav.fi/
2. Faça login
3. Vá em Settings → API
4. Gere uma nova API key
5. Cole no campo "Octav.fi API Key" na aba Configuração

**Formato**: JWT token (longo)

**Exemplo**:
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJodHRwczovL2hhc3VyYS5pby9qd3QvY2xhaW1zIjp7IngtaGFzdXJhLWRlZmF1bHQtcm9sZSI6InVzZXIiLCJ4LWhhc3VyYS1hbGxvd2VkLXJvbGVzIjpbInVzZXIiXSwieC1oYXN1cmEtdXNlci1pZCI6InNhbnJlbW8yNjE0MSJ9fQ.0eLf5m4kQPETnUaZbN6LFMoV8hxGwjrdZ598r9o61Yc
```

### 2. Wallet Address

**Formato**: Ethereum address (0x...)

**Exemplo**:
```
0x85963d266B718006375feC16649eD18c954cf213
```

### 3. Hyperliquid Private Key (Opcional)

**⚠️ IMPORTANTE**: Apenas para execução automática

**Como obter:**
- Private key da wallet Ethereum que usa na Hyperliquid
- **NUNCA compartilhe** esta chave
- **NUNCA commite** no git

**Formato**: 0x... (64 caracteres hex)

### 4. Configurações Avançadas

**Tolerância de Hedge**: 5% (padrão)
- Quanto de desvio aceitar antes de sugerir rebalanceamento

**Auto-Sync**: Desabilitado (padrão)
- Sincronização automática a cada X horas

**Auto-Execute**: Desabilitado (padrão)
- ⚠️ Executa ordens automaticamente (CUIDADO!)

**Alocação de Capital**: 70-90% LPs (padrão)
- Faixa ideal de capital em LPs vs Hyperliquid

**Protocolos Habilitados**: Revert, Uniswap3, Uniswap4, Dhedge (padrão)
- Quais protocolos incluir nos cálculos

---

## 🎯 Funcionalidades Principais

### 1. Sincronização de Portfolio

**O que faz:**
- Busca posições LP de TODOS os protocolos via Octav.fi
- Busca posições short da Hyperliquid
- Calcula balanços agregados por token
- Salva histórico de sincronizações

**Como funciona:**
1. Primeira sincronização: busca dados do Octav.fi
2. Aguarda 5 segundos (para protocolos atualizarem)
3. Segunda sincronização: valida dados completos
4. Processa e agrega posições
5. Salva no histórico

**Código**: `app.py` - função `load_portfolio_data()`

### 2. Análise Delta-Neutral

**O que faz:**
- Compara LP balances vs Short balances
- Identifica tokens over-hedged, under-hedged, balanced
- Sugere ações de rebalanceamento

**Lógica:**
```python
if short_balance == 0:
    status = "under_hedged"  # Precisa abrir short
elif abs(lp_balance - short_balance) / lp_balance <= tolerance:
    status = "balanced"  # Está OK
elif short_balance > lp_balance:
    status = "over_hedged"  # Precisa fechar short
else:
    status = "under_hedged"  # Precisa aumentar short
```

**Código**: `delta_neutral_analyzer.py`

### 3. Alocação de Capital

**O que faz:**
- Calcula distribuição de capital por protocolo
- Verifica se está na faixa ideal (70-90% LPs)
- Alerta sobre riscos (liquidação ou rentabilidade)

**Níveis de Risco:**
- 🟢 **ZONA IDEAL** (70-90% LPs): Balanço perfeito
- 🔴 **RISCO ALTO** (>90% LPs): Risco de liquidação
- 🟡 **RISCO MÉDIO** (<70% LPs): Perda de rentabilidade

**Código**: `capital_allocation_analyzer.py`

### 4. Execução de Ordens (Manual)

**O que faz:**
- Permite executar ordens sugeridas manualmente
- Valida parâmetros (tamanho, preço, margem)
- Executa via Hyperliquid API
- Registra no histórico

**Fluxo:**
1. Sistema sugere: "DIMINUIR SHORT em 0.003257 BTC"
2. Usuário clica em "Executar"
3. Sistema valida: tamanho, preço, margem disponível
4. Executa ordem market na Hyperliquid
5. Registra resultado no histórico

**Código**: `app.py` - seção de execução

### 5. Sistema de Cotas (NAV)

**O que faz:**
- Calcula NAV (Net Asset Value) por cota
- Rastreia depósitos/saques
- Calcula rentabilidade real

**Fórmula:**
```
NAV = Networth Total / Número de Cotas
Rentabilidade = (NAV Atual / NAV Inicial - 1) * 100%
```

**Código**: `quota_calculator.py`

### 6. Seletor de Protocolos

**O que faz:**
- Permite escolher quais protocolos incluir nos cálculos
- Filtra posições LP por protocolo habilitado
- Mostra status visual (✅/❌) nas posições

**Uso:**
- Excluir dust (Uniswap3: $0)
- Excluir testes (Uniswap4: $1)
- Focar em protocolos principais

**Código**: `app.py` - configuração e filtragem

---

## 🔌 APIs e Integrações

### Octav.fi API

**Endpoint**: `https://api.octav.fi/v1/portfolio`

**Headers**:
```python
{
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}
```

**Params**:
```python
{
    "addresses": "0x...",
    "includeImages": "false",
    "waitForSync": "false"
}
```

**Response**: JSON com portfolio completo
- `networth`: Valor total
- `assetByProtocols`: Posições por protocolo
  - `wallet`: Saldos em wallets
  - `revert`: Revert Finance
  - `uniswap3`: Uniswap V3
  - `uniswap4`: Uniswap V4
  - `dhedge`: Dhedge
  - `hyperliquid`: Hyperliquid
  - etc.

**Código**: `octav_client.py` - método `get_portfolio()`

### Hyperliquid API

**SDK**: `hyperliquid-python-sdk`

**Inicialização**:
```python
from hyperliquid.exchange import Exchange
from hyperliquid.info import Info
from eth_account import Account

wallet = Account.from_key(private_key)
exchange = Exchange(wallet)
info = Info()
```

**Operações:**

1. **Get Account Value**:
```python
account_value = exchange.get_account_value()
```

2. **Get Positions**:
```python
positions = exchange.get_positions()
```

3. **Get Prices**:
```python
all_mids = info.all_mids()
btc_price = float(all_mids["BTC"])
```

4. **Execute Order**:
```python
result = exchange.order(
    coin="BTC",
    is_buy=False,  # False = short
    sz=0.001,  # Size em BTC
    limit_px=current_price * 0.95,  # Slippage 5%
    reduce_only=False  # False = abrir, True = fechar
)
```

**Código**: `hyperliquid_client.py`

---

## 🔄 Fluxo de Dados

### Sincronização Manual

```
1. Usuário clica "Sincronizar Agora"
   ↓
2. load_portfolio_data() executado
   ↓
3. Octav.fi API: 1ª chamada
   ↓
4. Aguarda 5 segundos
   ↓
5. Octav.fi API: 2ª chamada (validação)
   ↓
6. extract_lp_positions() - extrai LPs de TODOS protocolos
   ↓
7. Filtra por protocolos habilitados
   ↓
8. extract_perp_positions() - extrai shorts Hyperliquid
   ↓
9. Agrega balances por token
   ↓
10. Salva em st.session_state
   ↓
11. Salva histórico em config_manager
   ↓
12. Dashboard atualizado
```

### Auto-Sync (Background Thread)

```
1. Thread background iniciado no app.py
   ↓
2. Loop infinito: while True
   ↓
3. Verifica se auto_sync_enabled
   ↓
4. Aguarda intervalo (ex: 1 hora)
   ↓
5. Executa mesma lógica de sync manual
   ↓
6. Salva histórico
   ↓
7. Volta ao passo 2
```

### Execução de Ordem

```
1. Usuário clica "Executar" em sugestão
   ↓
2. Valida se Hyperliquid key configurada
   ↓
3. Cria HyperliquidClient
   ↓
4. Busca preço atual (info.all_mids())
   ↓
5. Calcula tamanho e preço com slippage
   ↓
6. Valida margem disponível
   ↓
7. Executa ordem (exchange.order())
   ↓
8. Verifica resultado (status == "ok")
   ↓
9. Registra no execution_history
   ↓
10. Mostra resultado ao usuário
```

---

## 🚢 Deploy

### Railway (Recomendado)

**Passo 1**: Criar conta no Railway
- https://railway.app/

**Passo 2**: Conectar GitHub repo
- New Project → Deploy from GitHub repo
- Selecionar `XCELFI_LP_HEDGE_V2`

**Passo 3**: Configurar
- Railway detecta automaticamente `railway.toml` e `nixpacks.toml`
- Build command: `pip install -r requirements.txt`
- Start command: `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`

**Passo 4**: Deploy
- Railway faz deploy automático
- URL gerada: `https://xcelfi-lp-hedge-v2-production.up.railway.app/`

**Arquivos de Config:**
- `railway.toml`: Config Railway
- `nixpacks.toml`: Build config
- `.streamlit/config.toml`: Config Streamlit

### Local (Desenvolvimento)

```bash
streamlit run app.py
```

**Acesse**: http://localhost:8501

---

## 🐛 Troubleshooting

### Erro: "ModuleNotFoundError: No module named 'streamlit'"

**Solução**:
```bash
pip install -r requirements.txt
```

### Erro: "❌ Erro ao carregar dados do Octav.fi"

**Causas possíveis:**
1. API key inválida
2. Wallet address inválida
3. Octav.fi API offline

**Solução**:
- Verificar API key no Octav.fi
- Verificar wallet address (0x...)
- Tentar novamente após alguns minutos

### Erro: "NameError: name 'X' is not defined"

**Causa**: Variável não definida (bug de código)

**Solução**:
- Verificar commit mais recente
- Reportar issue no GitHub
- Reverter para V3: `git checkout v3.0-stable`

### Erro: Hyperliquid não conecta

**Causas possíveis:**
1. Private key inválida
2. Wallet sem saldo na Hyperliquid
3. Hyperliquid API offline

**Solução**:
- Verificar private key (64 caracteres hex)
- Verificar saldo na Hyperliquid
- Testar em https://app.hyperliquid.xyz/

### Performance lenta

**Causas possíveis:**
1. Muitas posições LP
2. Sincronização dupla (5s delay)
3. Railway free tier (limitado)

**Solução**:
- Desabilitar protocolos com dust
- Aumentar intervalo de auto-sync
- Upgrade Railway plan

---

## 📝 Changelog V4

### V4 Features (Novembro 2025)

#### 1. Sincronização Dupla
- **Commit**: `ac1c88a`
- **O que**: Dupla sincronização com 5s delay
- **Por quê**: Revert Finance precisa de tempo para atualizar
- **Doc**: `V4_FEATURE_DOUBLE_SYNC.md`

#### 2. Alocação de Capital
- **Commit**: `2742da8`
- **O que**: Monitoramento de capital por protocolo
- **Por quê**: Prevenir liquidação e maximizar rentabilidade
- **Doc**: `V4_FEATURE_CAPITAL_ALLOCATION.md`

#### 3. Alocação Baseada em Faixa
- **Commit**: `13e59f8`
- **O que**: Faixa 70-90% LPs ao invés de target único
- **Por quê**: Mais flexível e intuitivo
- **Doc**: `V4_FEATURE_RANGE_BASED_ALLOCATION.md`

#### 4. Extrator Universal de LPs
- **Commit**: `0b93cee`
- **O que**: Extrai de TODOS os protocolos automaticamente
- **Por quê**: Não perder nenhuma posição LP
- **Doc**: `V4_FEATURE_UNIVERSAL_LP_EXTRACTOR.md`

#### 5. Seletor de Protocolos
- **Commit**: `d2c9961`
- **O que**: Escolher quais protocolos incluir nos cálculos
- **Por quê**: Excluir dust e focar em principais
- **Doc**: `V4_FEATURE_PROTOCOL_SELECTOR.md`

### V4 Bugfixes

#### 1. Hyperliquid Equity
- **Commit**: `960ca66`
- **O que**: Corrigido valor Hyperliquid (equity vs positions)
- **Por quê**: Mostrava valor das posições ao invés do equity
- **Doc**: `V4_BUGFIX_HYPERLIQUID_EQUITY.md`

---

## 📚 Documentação Adicional

### Para Usuários

- `README.md` - Visão geral do projeto
- `SETUP.md` - Guia de instalação
- `DEPLOYMENT.md` - Guia de deploy

### Para Desenvolvedores

- `VERSION_HISTORY.md` - Histórico V3
- `V4_ROADMAP.md` - Roadmap V4
- `V4_FEATURE_*.md` - Docs de features
- `HYPERLIQUID_TECHNICAL_GUIDE.md` - Guia técnico Hyperliquid

### Exemplos de Código

- `example_short_btc.py` - Exemplo completo de short BTC
- `example_short_simple.py` - Exemplo simples
- `example_long_short_complete.py` - Exemplo com LONG e SHORT

---

## 🔐 Segurança

### Dados Sensíveis

**NUNCA commitar:**
- Private keys
- API keys
- Wallet addresses

**Onde estão:**
- `/tmp/xcelfi_data/config.json` (local)
- Variáveis de ambiente (Railway)

### Boas Práticas

1. **Use .gitignore**:
```
/tmp/
*.json
*.log
__pycache__/
.env
```

2. **Variáveis de Ambiente** (Railway):
- Não armazenar secrets no código
- Usar environment variables

3. **Validação**:
- Sempre validar inputs do usuário
- Verificar saldos antes de executar
- Confirmar operações sensíveis

---

## 🤝 Contribuindo

### Como Contribuir

1. Fork o repositório
2. Crie uma branch: `git checkout -b feature/nova-feature`
3. Commit: `git commit -m "feat: Adiciona nova feature"`
4. Push: `git push origin feature/nova-feature`
5. Abra Pull Request

### Convenções de Commit

- `feat:` - Nova feature
- `fix:` - Bugfix
- `docs:` - Documentação
- `refactor:` - Refatoração
- `test:` - Testes
- `chore:` - Manutenção

---

## 📞 Suporte

### Problemas Técnicos

- **GitHub Issues**: https://github.com/cruzdenis/XCELFI_LP_HEDGE_V2/issues
- **Email**: (adicionar email de suporte)

### Recursos

- **Octav.fi Docs**: https://docs.octav.fi/
- **Hyperliquid Docs**: https://hyperliquid.gitbook.io/
- **Streamlit Docs**: https://docs.streamlit.io/

---

## 📄 Licença

(Adicionar licença se aplicável)

---

## 🎓 Glossário

**LP (Liquidity Provider)**: Fornecedor de liquidez em pools DeFi

**Impermanent Loss**: Perda temporária ao fornecer liquidez quando preços mudam

**Delta-Neutral**: Estratégia que neutraliza exposição a preço

**Short**: Posição vendida (aposta na queda do preço)

**Hedge**: Proteção contra risco de preço

**Perpetual**: Contrato futuro sem data de expiração

**Margin**: Margem/colateral para posições alavancadas

**NAV (Net Asset Value)**: Valor líquido de ativos

**Networth**: Patrimônio total

**Equity**: Capital próprio (saldo + PnL + funding)

---

**Última Atualização**: Novembro 2025  
**Versão**: V4  
**Status**: ✅ Produção
