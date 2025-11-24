# Dashboard UX Analysis

## Current Tab Structure

1. ⚙️ **Configuração** - Settings
2. 📊 **Dashboard** - Main analysis (OVERCROWDED!)
3. 🏬 **Posições LP** - LP positions
4. 📜 **Histórico** - Sync history
5. 📈 **Execuções** - Execution history
6. 🔐 **Prova de Reservas** - Proof of reserves

## Current Dashboard Sections (Tab 2)

### Main Dashboard has TOO MANY sections:

1. **Sync Button** - Manual sync
2. **Last Sync Info** - Timestamp
3. **Networth Metrics** - Total value, change
4. **💼 Alocação de Capital** - Capital allocation
   - Status (ideal/warning/critical)
   - Pie chart
   - Protocol breakdown table
   - Rebalancing suggestions
5. **📈 Evolução do Net Worth** - NAV chart
6. **📈 Evolução da Cota** - Quota/rentability chart
7. **⚖️ Análise Delta-Neutral** - Hedge analysis
   - Per-token analysis (BTC, ETH, etc.)
   - LP balance vs Short balance
   - Suggestions
   - Execution buttons

## Problems

- Dashboard is TOO LONG (scrolling required)
- Too many different concepts mixed together
- Hard to find specific information
- Overwhelming for users

## Proposed Reorganization

### Option 1: Keep Dashboard, Create New Tabs

**New structure:**
1. ⚙️ Configuração
2. 📊 **Dashboard** (SIMPLIFIED)
   - Networth metrics
   - Quick sync button
   - Summary cards only
3. 💼 **Alocação** (NEW TAB)
   - Capital allocation
   - Protocol breakdown
   - Rebalancing alerts
4. 📈 **Performance** (NEW TAB)
   - NAV evolution chart
   - Quota evolution chart
   - Historical performance
5. ⚖️ **Hedge** (NEW TAB)
   - Delta-neutral analysis
   - Per-token breakdown
   - Execution interface
6. 🏬 Posições LP
7. 📜 Histórico
8. 📈 Execuções
9. 🔐 Prova de Reservas

### Option 2: Consolidate Similar Tabs

**New structure:**
1. ⚙️ Configuração
2. 📊 **Dashboard** (CLEAN)
   - Networth + sync
   - Quick metrics cards
3. 💼 **Análise** (NEW - combines allocation + hedge)
   - Sub-tabs:
     - Capital Allocation
     - Delta-Neutral Hedge
4. 📈 **Performance** (NEW)
   - NAV chart
   - Quota chart
5. 🏬 **Posições** (RENAMED - combines LP + shorts)
   - LP positions
   - Short positions
6. 📜 **Histórico** (EXPANDED - combines sync + exec)
   - Sync history
   - Execution history
7. 🔐 Prova de Reservas

## Recommendation

**Option 2** is cleaner:
- Fewer top-level tabs (7 instead of 9)
- Logical grouping
- Cleaner Dashboard
- Related info together

### Clean Dashboard Content

**Just essentials:**
- 💰 Networth (big metric)
- 🔄 Sync button
- 📊 Quick status cards:
  - Capital allocation status
  - Hedge status
  - Last sync time
- Links to detailed tabs

**Everything else moves to dedicated tabs!**
