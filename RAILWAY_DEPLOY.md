# Railway Deployment Guide

## Configuração Automática

O repositório já está configurado para deploy automático no Railway.

## Arquivos de Configuração

- `railway.toml` - Configuração do Railway
- `nixpacks.toml` - Configuração do build
- `requirements.txt` - Dependências Python
- `.env.railway.example` - Exemplo de variáveis de ambiente

## Passos para Deploy

### 1. Conectar Repositório ao Railway

1. Acesse [railway.app](https://railway.app)
2. Faça login com sua conta GitHub
3. Clique em "New Project"
4. Selecione "Deploy from GitHub repo"
5. Escolha o repositório: `cruzdenis/XCELFI_LP_HEDGE_V2`

### 2. Configurar Variáveis de Ambiente

No painel do Railway, vá em **Variables** e adicione:

```
OCTAV_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJodHRwczovL2hhc3VyYS5pby9qd3QvY2xhaW1zIjp7IngtaGFzdXJhLWRlZmF1bHQtcm9sZSI6InVzZXIiLCJ4LWhhc3VyYS1hbGxvd2VkLXJvbGVzIjpbInVzZXIiXSwieC1oYXN1cmEtdXNlci1pZCI6InNhbnJlbW8yNjE0MSJ9fQ.0eLf5m4kQPETnUaZbN6LFMoV8hxGwjrdZ598r9o61Yc

WALLET_ADDRESS=0xc1E18438Fed146D814418364134fE28cC8622B5C

OPERATION_MODE=ANALYSIS_READONLY

TOLERANCE_PCT=5.0
```

### 3. Deploy Automático

O Railway irá:
1. Detectar o `railway.toml`
2. Instalar dependências do `requirements.txt`
3. Executar o comando: `streamlit run app.py`
4. Gerar uma URL pública

### 4. Acessar Aplicação

Após o deploy, você receberá uma URL como:
```
https://xcelfi-lp-hedge-v2-production.up.railway.app
```

## Configurações Adicionais

### Domínio Customizado

1. No painel do Railway, vá em **Settings**
2. Em **Domains**, clique em **Generate Domain**
3. Ou adicione seu próprio domínio customizado

### Logs e Monitoramento

- Acesse a aba **Deployments** para ver logs
- Monitore uso de recursos em **Metrics**

### Redeploy Manual

Se necessário, você pode forçar um redeploy:
1. Vá em **Deployments**
2. Clique em **Redeploy**

## Troubleshooting

### Erro: Port not found

Certifique-se de que o `railway.toml` está usando `$PORT`:
```toml
startCommand = "streamlit run app.py --server.port $PORT"
```

### Erro: Module not found

Verifique se todas as dependências estão em `requirements.txt`

### Aplicação não inicia

Verifique os logs em **Deployments** para identificar o erro

## Modo de Operação

### ANALYSIS_READONLY (Padrão)
- Apenas consulta e análise
- Não executa trades
- Seguro para produção

### EXECUTION_AERODROME_ONLY
- Permite execução apenas no Aerodrome
- Requer chaves privadas adicionais

### FULL_EXECUTION
- Execução completa (Aerodrome + Hyperliquid)
- Requer todas as chaves de API

## Segurança

⚠️ **IMPORTANTE**:
- Nunca commite chaves privadas ou API keys no repositório
- Use sempre as variáveis de ambiente do Railway
- Comece sempre em modo `ANALYSIS_READONLY`
- Teste com valores pequenos antes de ativar execução

## Suporte

Para problemas com o deploy:
1. Verifique os logs no Railway
2. Consulte a documentação: https://docs.railway.app
3. Abra uma issue no GitHub
