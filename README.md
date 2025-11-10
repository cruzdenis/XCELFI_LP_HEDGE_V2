# XCELFI LP Hedge V2

**Delta Neutral LP Hedge Strategy** combining Aerodrome Finance (Base L2) liquidity provision with Hyperliquid perpetual shorts.

## 🎯 Overview

XCELFI LP Hedge is a sophisticated DeFi strategy application that maintains a delta-neutral position by:

- Providing liquidity to ETH/BTC pool on Aerodrome (Base L2)
- Hedging with short perpetual positions on Hyperliquid (50% BTC, 50% ETH)
- Automatically rebalancing when price moves outside defined range
- Tracking NAV with professional unit accounting methodology
- Supporting both **Analysis (Read-Only)** and **Execution** modes

## ✨ Key Features

### 📊 Dual Operation Modes

- **Analysis Mode (Read-Only)**: Monitor positions and receive rebalancing suggestions without providing private keys
- **Execution Mode**: Full control with manual and automatic execution capabilities

### 🎯 Strategy Management

- **Continuous Hedging**: Never closes shorts due to negative funding rates
- **Automatic Recentering**: Triggers when price deviates 1% from LP range
- **Buffer Management**: 74% LP / 24% shorts / 1% USDC / 1% ETH allocation
- **Hysteresis Logic**: Prevents ping-pong rebalancing in volatile markets

### 💰 Professional Accounting

- **Unit Accounting**: NAV per cota (unit) starting at 1.00
- **Cash Flow Neutral**: Deposits/withdrawals don't distort performance
- **Performance Tracking**: MTD, YTD, and inception returns
- **Protocol Attribution**: Separate PnL tracking for Aerodrome and Hyperliquid

### 🛡️ Safety First

- **Comprehensive Safety Checks**: Reserve buffers, slippage caps, gas limits
- **API Health Monitoring**: Validates external service availability
- **Cooldown Periods**: Prevents excessive rebalancing
- **Execution Modes**: Manual (with confirmation) and Auto (with safety gates)

## 🏗️ Architecture

```
XCELFI_LP_HEDGE_V2/
├── app.py                      # Main Streamlit application
├── core/
│   ├── auth.py                 # Authentication with bcrypt
│   ├── config.py               # Configuration management
│   ├── nav.py                  # NAV calculation with unit accounting
│   ├── pnl.py                  # PnL tracking and attribution
│   ├── safety.py               # Safety checks
│   └── triggers.py             # Rebalancing triggers
├── integrations/
│   ├── aerodrome.py            # Aerodrome Finance integration
│   └── hyperliquid.py          # Hyperliquid DEX integration
├── strategies/
│   └── recenter.py             # Recentering strategy logic
├── utils/
│   ├── logs.py                 # Logging and audit trail
│   └── ticks.py                # Uniswap V3 tick calculations
└── data/                       # Data storage (logs, history)
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Base L2 RPC access
- Aerodrome Finance pool address
- (Optional) Hyperliquid API credentials for execution

### Installation

1. **Clone the repository**

```bash
git clone https://github.com/YOUR_USERNAME/XCELFI_LP_HEDGE_V2.git
cd XCELFI_LP_HEDGE_V2
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Configure environment**

```bash
cp .env.example .env
# Edit .env with your configuration
```

4. **Run the application**

```bash
streamlit run app.py
```

## ⚙️ Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# Wallet Configuration
WALLET_PUBLIC_ADDRESS=0x...              # Required: Your wallet address
WALLET_PRIVATE_KEY=                      # Optional: For execution mode

# Hyperliquid Configuration
HYPERLIQUID_API_KEY=                     # Optional: For execution mode
HYPERLIQUID_API_SECRET=                  # Optional: For execution mode

# Strategy Parameters
RANGE_TOTAL=0.30                         # LP range width (±15%)
RECENTER_TRIGGER=0.01                    # Trigger at 1% deviation
COOLDOWN_HOURS=2                         # Minimum time between rebalances

# Target Allocation
TARGET_LP_PCT=0.74                       # 74% in LP
TARGET_SHORT_PCT=0.24                    # 24% in shorts
```

### Authentication

Generate password hash for authentication:

```python
from core.auth import AuthManager
hashed = AuthManager.hash_password("your_password")
print(hashed)
```

Add to `.env`:

```bash
AUTH_USERS_JSON={"admin":"$2b$12$..."}
```

## 📖 Usage

### Analysis Mode (Read-Only)

1. Configure only `WALLET_PUBLIC_ADDRESS` in `.env`
2. Launch application
3. View positions, NAV, and rebalancing suggestions
4. No execution possible - perfect for testing and validation

### Execution Mode

1. Configure `WALLET_PUBLIC_ADDRESS` and `WALLET_PRIVATE_KEY`
2. (Optional) Add `HYPERLIQUID_API_KEY` and `HYPERLIQUID_API_SECRET`
3. Launch application
4. Choose between:
   - **Manual Execution**: Review plan and confirm each operation
   - **Auto Execution**: Enable AUTO mode for automatic rebalancing (requires safety checks to pass)

## 🛡️ Safety Checks

Before AUTO execution, the system validates:

- ✅ ETH gas reserve above minimum
- ✅ USDC CEX reserve above minimum
- ✅ Estimated slippage within limits
- ✅ Gas cost within cap
- ✅ Aerodrome API healthy
- ✅ Hyperliquid API healthy
- ✅ Pool liquidity sufficient
- ✅ Cooldown period elapsed

## 📊 NAV Calculation

The system uses **unit accounting** methodology:

- **Initial Cota**: 1.00
- **Deposits**: Issue new units at current NAV per unit
- **Withdrawals**: Redeem units at current NAV per unit
- **Performance**: Measured by change in NAV per unit

Formula:
```
NAV_t = NAV_{t-1} + PnL_t - Fees_t
Units_t = Units_{t-1} + Deposits_t/Price_{t-1} - Withdrawals_t/Price_{t-1}
Price_t = NAV_t / Units_t
```

## 🔧 Development

### Project Structure

- `core/`: Core business logic (auth, config, NAV, safety)
- `integrations/`: External service integrations (Aerodrome, Hyperliquid)
- `strategies/`: Strategy implementation (recenter logic)
- `utils/`: Utility functions (logging, tick math)
- `data/`: Runtime data (logs, history)

### Adding New Features

1. Core logic goes in `core/`
2. External integrations in `integrations/`
3. Strategy modifications in `strategies/`
4. Update `app.py` for UI changes

## 🐳 Docker Deployment

```bash
# Build image
docker build -t xcelfi-lp-hedge .

# Run container
docker run -p 8501:8501 --env-file .env xcelfi-lp-hedge
```

## 📝 License

MIT License - see LICENSE file for details

## ⚠️ Disclaimer

This software is provided for educational and research purposes. Use at your own risk. The authors are not responsible for any financial losses incurred through the use of this application. Always test thoroughly with small amounts before deploying significant capital.

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📞 Support

For issues and questions:
- Open an issue on GitHub
- Review existing documentation
- Check logs in `data/` directory

## 🎯 Roadmap

- [ ] Historical backtesting module
- [ ] Additional DEX integrations (Bybit, HTX)
- [ ] Advanced analytics dashboard
- [ ] Telegram/Discord notifications
- [ ] Multi-wallet support
- [ ] Strategy optimization tools

---

**Built with ❤️ by XCELFI Team**
