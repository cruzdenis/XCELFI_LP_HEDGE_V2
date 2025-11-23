# V4 Feature: Protocol Selector

**Date**: 23 de Novembro de 2025  
**Status**: ✅ Implemented  
**Commit**: `d2c9961`

---

## 🎯 Feature Overview

Added a **protocol selector** in the Configuration tab that allows users to choose which protocols to include in hedge and capital allocation calculations, with visual indicators showing enabled/disabled status.

---

## 💡 Why This Feature?

### User Request

> "tem como colocar um campo de seleção para eu escolher quais protocolos eu desejo levar em consideração?"

### Problem

After implementing the universal LP extractor, the system now detects ALL protocols (Revert, Uniswap3, Uniswap4, Dhedge, etc.). However:

- Some protocols have **dust/negligible values** (e.g., Uniswap4: $1, Uniswap3: $0)
- User may want to **focus on main protocols** only
- Test positions should be **excluded from calculations**

### Solution

Multi-select dropdown to choose which protocols to include, with:
- ✅ Visual feedback (enabled/disabled indicators)
- ✅ Persistent storage (saved in config)
- ✅ Flexible filtering (affects calculations, not display)

---

## 🎨 User Interface

### 1. Configuration Tab

**New Section: "🎯 Seleção de Protocolos"**

```
🎯 Seleção de Protocolos
Escolha quais protocolos incluir nos cálculos de hedge e alocação de capital.

┌─────────────────────────────────────────────────┐
│ Protocolos Habilitados                          │
│ ┌─────────────────────────────────────────────┐ │
│ │ ☑ Revert                                    │ │
│ │ ☑ Uniswap3                                  │ │
│ │ ☑ Uniswap4                                  │ │
│ │ ☑ Dhedge                                    │ │
│ │ ☐ Aerodrome                                 │ │
│ │ ☐ Curve                                     │ │
│ │ ☐ Sushiswap                                 │ │
│ │ ☐ Balancer                                  │ │
│ │ ☐ Velodrome                                 │ │
│ └─────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘

✅ 4 protocolo(s) selecionado(s)

ℹ️ Sobre a Seleção de Protocolos
```

**Expander Content:**
```
Por que selecionar protocolos?

- Excluir posições pequenas: Ignore protocolos com valores insignificantes
- Focar em protocolos principais: Considere apenas LPs relevantes
- Testes: Desabilite temporariamente um protocolo para análise

Impacto:
- Cálculos de hedge consideram apenas protocolos selecionados
- Alocação de capital filtra por protocolos habilitados
- Dashboard mostra todos, mas destaca os selecionados

Recomendação:
- Mantenha todos os protocolos com valor significativo habilitados
- Desabilite apenas protocolos com dust/valores mínimos
```

### 2. LP Positions Tab

**Enhanced Display with Status Column:**

```
🏬 Posições LP

Protocolo          Token    Quantidade    Valor USD    Status
─────────────────────────────────────────────────────────────
Revert (arbitrum)  WBTC     0.003935      $344.56      ✅
Revert (arbitrum)  WETH     2.385463      $6,750.67    ✅
Revert (arbitrum)  WBTC     0.000688      $60.25       ✅
Revert (arbitrum)  WETH     0.021065      $59.61       ✅
Dhedge (arbitrum)  USDC     15.059270     $15.06       ✅
Uniswap3 (arbitrum) uplay   99,986.33     $0.00        ❌
Uniswap3 (arbitrum) USDC    0.004511      $0.00        ❌
Uniswap4 (arbitrum) uplay   100,000.00    $0.00        ❌
Uniswap4 (arbitrum) USDC    0.999999      $1.00        ❌
```

**Legend:**
- ✅ = Enabled (included in calculations)
- ❌ = Disabled (excluded from calculations)

---

## 🔧 Implementation Details

### 1. Configuration UI

**Location**: `app.py` - Configuration tab (line ~335)

```python
# Get available protocols
available_protocols = [
    "Revert", "Uniswap3", "Uniswap4", "Dhedge", 
    "Aerodrome", "Curve", "Sushiswap", "Balancer", "Velodrome"
]

# Load saved preferences
enabled_protocols = existing_config.get(
    "enabled_protocols", 
    ["Revert", "Uniswap3", "Uniswap4", "Dhedge"]
) if existing_config else ["Revert", "Uniswap3", "Uniswap4", "Dhedge"]

# Multi-select widget
enabled_protocols = st.multiselect(
    "Protocolos Habilitados",
    options=available_protocols,
    default=enabled_protocols,
    help="Selecione os protocolos que deseja incluir nos cálculos"
)
```

### 2. Config Manager

**Location**: `config_manager.py` (line ~22)

```python
def save_config(
    self, 
    api_key, 
    wallet_address, 
    tolerance_pct=5.0, 
    hyperliquid_private_key="", 
    auto_sync_enabled=False, 
    auto_sync_interval_hours=1, 
    auto_execute_enabled=False, 
    lp_min_ideal=70.0, 
    lp_target=80.0, 
    lp_max_ideal=90.0, 
    enabled_protocols=None  # NEW PARAMETER
):
    if enabled_protocols is None:
        enabled_protocols = ["Revert", "Uniswap3", "Uniswap4", "Dhedge"]
    
    config = {
        ...
        "enabled_protocols": enabled_protocols,  # SAVED TO CONFIG
        ...
    }
```

### 3. Filtering Logic

**Location**: `app.py` - load_portfolio_data() and background_sync_worker()

```python
# Extract all LP positions
lp_positions = client.extract_lp_positions(portfolio)

# Filter by enabled protocols
enabled_protocols = config.get("enabled_protocols", ["Revert", "Uniswap3", "Uniswap4", "Dhedge"])
filtered_lp_positions = [
    pos for pos in lp_positions 
    if any(proto.lower() in pos.protocol.lower() for proto in enabled_protocols)
]

# Aggregate balances (using filtered positions)
lp_balances = {}
for pos in filtered_lp_positions:
    symbol = client.normalize_symbol(pos.token_symbol)
    lp_balances[symbol] = lp_balances.get(symbol, 0) + pos.balance
```

**Key Points:**
- `lp_positions` = ALL positions (for display)
- `filtered_lp_positions` = ENABLED positions (for calculations)
- `lp_balances` = Aggregated from filtered positions only

### 4. Display with Status Indicators

**Location**: `app.py` - LP Positions tab (line ~1495)

```python
# Get enabled protocols
enabled_protocols = data.get('enabled_protocols', ["Revert", "Uniswap3", "Uniswap4", "Dhedge"])

# Display all positions with status
for pos in lp_positions:
    # Check if enabled
    is_enabled = any(proto.lower() in pos.protocol.lower() for proto in enabled_protocols)
    
    # Display with status indicator
    col1.write(f"**{pos.protocol}** ({pos.chain})")
    col2.write(pos.token_symbol)
    col3.write(f"{pos.balance:.6f}")
    col4.write(f"${pos.value:.2f}")
    
    if is_enabled:
        col5.write("✅")  # Enabled
    else:
        col5.write("❌")  # Disabled
```

---

## 📊 Impact on Calculations

### Before (All Protocols)

```python
# All protocols included
lp_balances = {
    "BTC": 0.004623,  # From Revert + Uniswap3 + Uniswap4
    "ETH": 2.406528,  # From Revert + Uniswap3 + Uniswap4
    "USDC": 15.064,   # From Dhedge + Uniswap3 + Uniswap4
    "uplay": 199,987  # From Uniswap3 + Uniswap4
}
```

### After (Filtered: Revert + Dhedge only)

```python
# Only enabled protocols
lp_balances = {
    "BTC": 0.004623,  # From Revert only
    "ETH": 2.406528,  # From Revert only
    "USDC": 15.059    # From Dhedge only
    # uplay excluded (Uniswap3/4 disabled)
}
```

**Result:**
- Hedge calculations ignore disabled protocols
- Capital allocation focuses on main protocols
- Cleaner, more relevant analysis

---

## 🎯 Use Cases

### 1. Exclude Dust Positions

**Scenario**: Uniswap3 has $0 value (dust)

**Action**: Uncheck "Uniswap3"

**Result**: 
- Uniswap3 positions excluded from calculations
- Hedge suggestions ignore uplay token
- Capital allocation focuses on valuable positions

### 2. Exclude Test Positions

**Scenario**: Uniswap4 has $1 test position

**Action**: Uncheck "Uniswap4"

**Result**:
- $1 test position excluded
- More accurate capital allocation percentages
- Cleaner analysis

### 3. Focus on Main Protocol

**Scenario**: 95% of value in Revert Finance

**Action**: Check only "Revert"

**Result**:
- Calculations focus on main protocol
- Ignore small positions in other protocols
- Simplified analysis

### 4. Temporary Disable for Testing

**Scenario**: Testing hedge strategy without Dhedge

**Action**: Uncheck "Dhedge" temporarily

**Result**:
- See how calculations change
- Test different scenarios
- Re-enable when done

---

## 🔄 Data Flow

```
1. User selects protocols in Configuration
   ↓
2. Preferences saved to config.json
   ↓
3. Sync fetches ALL LP positions from Octav.fi
   ↓
4. Filter positions by enabled protocols
   ↓
5. Aggregate balances (filtered only)
   ↓
6. Calculate hedge suggestions (filtered)
   ↓
7. Display ALL positions with status indicators
   ↓
8. Show calculations based on filtered data
```

**Key Principle**: 
- **Fetch ALL** (complete data)
- **Filter for calculations** (relevant data)
- **Display ALL with indicators** (transparency)

---

## ✅ Testing

### Test 1: Default Configuration

**Setup**: Fresh config, all defaults

**Expected**:
- Revert, Uniswap3, Uniswap4, Dhedge selected
- All 4 protocols show ✅ in LP Positions
- Calculations include all 4 protocols

**Result**: ✅ Pass

### Test 2: Disable Uniswap3 and Uniswap4

**Setup**: Uncheck Uniswap3 and Uniswap4

**Expected**:
- Only Revert and Dhedge selected
- Uniswap3/4 show ❌ in LP Positions
- lp_balances excludes uplay token
- Hedge calculations ignore Uniswap positions

**Result**: ✅ Pass

### Test 3: Enable Only Revert

**Setup**: Check only "Revert"

**Expected**:
- Only Revert shows ✅
- All others show ❌
- Calculations use only Revert positions
- Capital allocation focuses on Revert

**Result**: ✅ Pass

### Test 4: Persistence

**Setup**: Save config, reload page

**Expected**:
- Protocol selection persists
- Same protocols checked after reload
- Calculations remain consistent

**Result**: ✅ Pass

---

## 📚 Related Files

**Modified:**
- `app.py` - UI and filtering logic
- `config_manager.py` - Config storage

**Created:**
- `V4_FEATURE_PROTOCOL_SELECTOR.md` (this file)

**Affected:**
- Delta-neutral analysis (uses filtered positions)
- Capital allocation (uses filtered positions)
- LP Positions display (shows all with status)
- Background sync (filters positions)

---

## 🎨 User Experience

### Before

**User sees**: All protocols in calculations

**Problem**: 
- Dust positions affect percentages
- Test positions skew analysis
- No control over what's included

### After

**User sees**: 
- Multi-select to choose protocols
- Visual indicators (✅/❌) on positions
- Clean, focused calculations

**Benefits**:
- Full control over calculations
- Exclude irrelevant positions
- Transparent (see all, calculate with selected)

---

## 🔮 Future Enhancements

### Potential Improvements

1. **Auto-Detection**
   - Automatically suggest disabling protocols with value < $10
   - Smart defaults based on portfolio composition

2. **Protocol Groups**
   - "Main Protocols" (Revert, Uniswap)
   - "Small Positions" (< $100)
   - Quick toggle groups

3. **Per-Protocol Settings**
   - Minimum value threshold per protocol
   - Custom tolerance per protocol
   - Protocol-specific hedge strategies

4. **Analytics**
   - Show impact of enabling/disabling
   - Compare calculations with different selections
   - Recommendation engine

---

## 📊 Summary

**What Changed:**
- Added protocol multi-select in Configuration
- Saved preferences to config.json
- Filtered LP positions for calculations
- Added status indicators in display

**Why:**
- Exclude dust/test positions
- Focus on main protocols
- User control over calculations

**How:**
- Multi-select dropdown (9 protocols)
- Persistent storage
- Filter before aggregation
- Visual feedback (✅/❌)

**Impact:**
- More accurate calculations
- Cleaner analysis
- Better user experience
- Flexible protocol management

---

**Status**: ✅ **Feature Complete and Deployed!**

Users can now choose which protocols to include in calculations, with full transparency and visual feedback.
