# Setup Guide

## Initial Setup

### 1. Generate Password Hash

First, generate a hashed password for authentication:

```python
python3 -c "from core.auth import AuthManager; print(AuthManager.hash_password('your_password_here'))"
```

Copy the output hash.

### 2. Configure Environment

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and configure:

#### Required Settings

```bash
# Authentication
AUTH_USERS_JSON={"admin":"PASTE_YOUR_HASH_HERE"}

# Wallet (required for both modes)
WALLET_PUBLIC_ADDRESS=0xYourWalletAddress
```

#### For Analysis Mode (Read-Only)

That's it! Leave `WALLET_PRIVATE_KEY` and Hyperliquid keys empty.

#### For Execution Mode

```bash
# Wallet Private Key (enables Aerodrome execution)
WALLET_PRIVATE_KEY=your_private_key_here

# Hyperliquid API (enables Hyperliquid execution)
HYPERLIQUID_API_KEY=your_api_key
HYPERLIQUID_API_SECRET=your_api_secret
```

### 3. Configure Base L2 and Aerodrome

```bash
# Base L2 RPC (use a reliable provider)
BASE_RPC_URL=https://mainnet.base.org

# Aerodrome Configuration
AERODROME_SUBGRAPH_URL=https://api.thegraph.com/subgraphs/name/aerodrome-finance/aerodrome-base
AERODROME_ROUTER=0xYourRouterAddress
AERODROME_POOL_ADDRESS=0xYourPoolAddress
```

### 4. Adjust Strategy Parameters (Optional)

```bash
# Monitoring
WATCH_INTERVAL_MIN=10           # Check every 10 minutes
CRON_FULL_CHECK_HOURS=12        # Full check every 12 hours

# LP Range
RANGE_TOTAL=0.30                # ±15% range
RECENTER_TRIGGER=0.01           # Trigger at 1% deviation
HYSTERESIS_REENTRY=0.002        # 0.2% reentry threshold

# Risk Management
SLIPPAGE_BPS=20                 # Max 20 bps (0.2%) slippage
GAS_CAP_NATIVE=0.01             # Max 0.01 ETH per operation
COOLDOWN_HOURS=2                # Min 2 hours between rebalances

# Reserves
ETH_GAS_MIN=0.05                # Minimum 0.05 ETH for gas
ETH_GAS_TARGET=0.10             # Target 0.10 ETH
USDC_CEX_MIN_PCT=0.003          # Min 0.3% of AUM in USDC
USDC_CEX_TARGET_PCT=0.006       # Target 0.6% of AUM

# Allocation
TARGET_LP_PCT=0.74              # 74% in LP
TARGET_SHORT_PCT=0.24           # 24% in shorts
```

## Running the Application

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run application
streamlit run app.py
```

Access at: http://localhost:8501

### Docker

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## First Login

1. Navigate to http://localhost:8501
2. Enter username: `admin`
3. Enter the password you used to generate the hash
4. You should see the dashboard

## Operation Modes

### Analysis Mode

- Only requires `WALLET_PUBLIC_ADDRESS`
- Shows all positions and calculations
- Displays rebalancing suggestions
- **No execution possible**
- Perfect for:
  - Testing the application
  - Validating strategy logic
  - Monitoring without risk

### Execution Mode (Aerodrome Only)

- Requires `WALLET_PUBLIC_ADDRESS` + `WALLET_PRIVATE_KEY`
- Can execute LP operations
- Cannot adjust Hyperliquid shorts
- Use when:
  - You want to manage LP manually
  - Testing execution with limited risk

### Full Execution Mode

- Requires all credentials
- Can execute all operations
- Supports AUTO mode
- Use when:
  - Ready for full automation
  - All safety checks pass

## Safety Checklist

Before enabling AUTO mode:

- [ ] Tested in Analysis mode
- [ ] Verified all calculations
- [ ] Confirmed wallet addresses
- [ ] Set appropriate reserve buffers
- [ ] Configured slippage and gas caps
- [ ] Tested manual execution
- [ ] Reviewed safety check logic
- [ ] Set up monitoring/alerts
- [ ] Started with small capital

## Troubleshooting

### "Invalid username or password"

- Regenerate password hash
- Ensure no extra spaces in `.env`
- Check JSON format in `AUTH_USERS_JSON`

### "Execution mode not enabled"

- Verify `WALLET_PRIVATE_KEY` is set
- Check private key format (no 0x prefix)
- Ensure key matches public address

### "API not responding"

- Check RPC URL is accessible
- Verify Subgraph URL is correct
- Test Hyperliquid API connectivity

### "Safety checks failed"

- Review reserve balances
- Check gas and slippage estimates
- Verify API health status
- Wait for cooldown period

## Monitoring

### Logs

Logs are stored in `data/` directory:

- `executions.jsonl`: Execution history
- `audit.jsonl`: Audit trail
- `errors.jsonl`: Error logs

### Metrics to Watch

- NAV per cota (should grow steadily)
- Funding rate (should be positive)
- LP fees collected
- Gas costs
- Slippage impact

## Backup

Regularly backup:

```bash
# Backup data directory
tar -czf backup_$(date +%Y%m%d).tar.gz data/

# Backup .env (store securely!)
cp .env .env.backup
```

## Security Best Practices

1. **Never commit `.env` to git**
2. **Use strong passwords**
3. **Rotate API keys regularly**
4. **Monitor for unauthorized access**
5. **Keep private keys encrypted at rest**
6. **Use hardware wallet when possible**
7. **Test with small amounts first**

## Getting Help

If you encounter issues:

1. Check logs in `data/errors.jsonl`
2. Review this setup guide
3. Consult README.md
4. Open an issue on GitHub with:
   - Error message
   - Operation mode
   - Steps to reproduce
   - (Sanitized) logs

## Next Steps

After successful setup:

1. Monitor in Analysis mode for 24-48 hours
2. Test manual execution with small amounts
3. Verify all safety checks work correctly
4. Gradually increase capital
5. Enable AUTO mode when confident

---

**Remember**: Start small, test thoroughly, and never risk more than you can afford to lose.
