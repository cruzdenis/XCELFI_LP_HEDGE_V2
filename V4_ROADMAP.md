# XCELFI LP Hedge V4 - Development Roadmap

**Status**: 🚀 In Progress
**Base Version**: V3.0 Stable
**Start Date**: 23 de Novembro de 2025

---

## 🎯 V4 Development Guidelines

### Principles
1. **Incremental Development**: Add one feature at a time
2. **Test Before Commit**: Ensure each feature works before moving to next
3. **Maintain V3 Stability**: Don't break existing functionality
4. **Document Changes**: Update this file as features are added
5. **Easy Rollback**: Can always revert to V3 if needed

### Rollback to V3
```bash
# If V4 development breaks something
git checkout v3.0-stable

# Or restore from commit
git checkout c9664fb4185baeb451724fab149702c13f6e711e
```

---

## ✅ Completed Features in V4

### Feature 1: Dashboard Revamp & Priority Hedging
- **Commit**: `2244f63` (initial implementation)
- **Status**: ✅ Completed
- **Description**:
    - Reorganized dashboard with an executive summary at the top (Net Worth, Allocation, Hedge Status, LP/Short counts).
    - Implemented a configurable hedge trigger threshold (0-50%, default 10%) to determine when action is required.
    - Introduced priority-based hedge suggestions:
        - 🔴 **REQUIRED**: When adjustment value is >= threshold % of total capital.
        - 🟡 **OPTIONAL**: When adjustment value is < threshold.
    - Added symbol normalization for price lookups (e.g., WBTC → BTC, WETH → ETH) for consistency.

---

## 🐛 V4 Bugfixes

### Bugfix 1: ETH Hedge Calculation Shows $0.00
- **Commit**: `65efab8`
- **Status**: ✅ **RESOLVED**
- **Description**:
    - **Symptom**: The UI displayed the ETH hedge adjustment as "$0.00 = 0.0% of capital" despite having the correct data (price, LP balance, short balance). BTC and other tokens calculated correctly.
    - **Root Cause**: The `delta_neutral_analyzer.py` has a two-pass system. When the global hedge trigger was activated, a second pass would force "balanced" positions to be re-evaluated. However, this second pass recalculated the `adjustment_amount` but **failed** to recalculate the corresponding `adjustment_value_usd`. ETH was being classified as "balanced" in the first pass, and when forced into an "under-hedged" state in the second pass, its USD value remained the initial zero.
    - **Solution**: The logic in the second pass was updated to correctly recalculate both `adjustment_value_usd` and the `priority` for any position that is forcibly adjusted.

---

## 📋 Feature Ideas (To Be Prioritized)

### Category: User Experience
- [ ] Export history to CSV/Excel
- [ ] Dark mode toggle
- [ ] Email notifications for large imbalances
- [ ] Mobile-responsive design improvements
- [ ] Multi-language support (EN/PT)

### Category: Data & Analytics
- [ ] Alternative data sources (e.g., Uniswap Subgraph as a backup to Octav.fi)
- [ ] Historical performance comparison
- [ ] Profit/Loss tracking per position
- [ ] Risk metrics (Sharpe ratio, max drawdown)
- [ ] Position size recommendations
- [ ] Correlation analysis between assets

### Category: Trading Features
- [ ] Stop-loss automation
- [ ] Take-profit targets
- [ ] Partial position closing
- [ ] Multiple wallet support
- [ ] Batch order execution

### Category: Infrastructure
- [ ] Database integration (PostgreSQL/MongoDB)
- [ ] User authentication system
- [ ] API rate limiting
- [ ] Webhook support for external triggers
- [ ] Backup/restore functionality

### Category: Monitoring
- [ ] Real-time WebSocket price updates
- [ ] Position health indicators
- [ ] Alert system for critical events
- [ ] Performance dashboard
- [ ] System health monitoring

---

## 📝 Notes

- V3 checkpoint: `v3.0-stable` (commit `c9664fb`)
- V4 development branch: `master` (continuing from V3)
- All V3 features remain functional

---

**Maintained by**: Manus AI
