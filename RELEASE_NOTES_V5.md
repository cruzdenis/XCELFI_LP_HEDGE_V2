# 🎉 Release Notes - Versão 5.0

**Data:** 25 de Novembro de 2025
**Tag Git:** `v5.0-stable`
**Status:** ✅ **ESTÁVEL E PRONTO PARA USO**

## 🚀 Novas Features

### 📈 NAV (Net Asset Value) Tracking
- **Nova Aba "NAV"**: Acompanhe o valor líquido do seu portfólio e a evolução da cotação, desconsiderando aportes e saques.
- **Gráficos Interativos**: NAV Absoluto e NAV per Share (cotação).
- **Sistema de Cotas**: Cálculo automático de shares para aportes/saques, com cota inicial 1:1.
- **Importação de Histórico**: Adicione NAV de períodos anteriores para ter um histórico completo.
- **Auto-Cotização**: Cada "Analisar Hedge" cria um snapshot de NAV automaticamente.

### 👛 Multi-Wallet Support
- **Seletor de Wallet**: Gerencie múltiplas wallets de forma independente.
- **Dados Separados**: Cada wallet tem suas próprias configurações, históricos e transações.
- **Migração Automática**: Dados existentes são migrados para o novo formato sem perda.

### ⚖️ Equalização de Saldo
- **Nova Aba "Equalização de Saldo"**: Monitore a relação entre o saldo da Hyperliquid e o total do portfólio.
- **Alertas por Cor**: Receba alertas visuais sobre o risco de liquidação ou capital ocioso.

### 🎯 Gatilho de Cobertura de Hedge
- **Rebalanceamento Obrigatório**: Se a cobertura de hedge estiver fora do range 98-102%, o sistema força o rebalanceamento completo.

### 📊 Gráfico de NAV no Histórico
- **Visualização Rápida**: A aba "Histórico" agora tem um gráfico mostrando a evolução do NAV a cada sincronização.

## 🐛 Correções de Bugs

- ✅ **Cálculo de Cotação**: Corrigido bug crítico que usava o total de shares atual ao invés das shares na data do snapshot.
- ✅ **Backup/Restore**: Corrigido erro de import `datetime` que impedia a criação de backups.
- ✅ **Duplicatas no NAV**: Adicionada proteção para evitar inserção de dados duplicados.
- ✅ **UI de Exclusão**: Melhorada a UI para deletar registros com um clique.

## 📝 Rollback (se necessário)

Se precisar voltar para V4:
```bash
git checkout v4.0-stable
```

Se precisar voltar para V5:
```bash
git checkout v5.0-stable
```
