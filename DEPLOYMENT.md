# Deployment Guide - Streamlit Cloud

## 🚀 Deploy to Streamlit Cloud

### Prerequisites

- GitHub account (already done ✅)
- Streamlit Cloud account (free at https://streamlit.io/cloud)

### Step 1: Sign up for Streamlit Cloud

1. Go to https://share.streamlit.io/
2. Click "Sign up" or "Continue with GitHub"
3. Authorize Streamlit to access your GitHub repositories

### Step 2: Deploy the App

1. Click "New app" button
2. Select:
   - **Repository:** `cruzdenis/XCELFI_LP_HEDGE_V2`
   - **Branch:** `master`
   - **Main file path:** `app.py`
3. Click "Advanced settings"
4. Set **Python version:** `3.11`

### Step 3: Configure Secrets

In the "Advanced settings" section, add the following to the **Secrets** text area:

```toml
# Application Environment
APP_ENV = "production"
STREAMLIT_SECRET_KEY = "your-random-secret-key-here"

# Authentication - IMPORTANT: Generate hash first!
# Run: python3 -c "from core.auth import AuthManager; print(AuthManager.hash_password('your_password'))"
AUTH_USERS_JSON = '{"admin":"$2b$12$YOUR_HASHED_PASSWORD_HERE"}'

# Wallet Configuration (DEMO MODE - Read-only)
WALLET_PUBLIC_ADDRESS = "0x0000000000000000000000000000000000000000"
WALLET_PRIVATE_KEY = ""

# Base L2 Configuration
BASE_RPC_URL = "https://mainnet.base.org"
AERODROME_SUBGRAPH_URL = "https://api.thegraph.com/subgraphs/name/aerodrome-finance/aerodrome-base"
AERODROME_ROUTER = "0x0000000000000000000000000000000000000000"
AERODROME_POOL_ADDRESS = "0x0000000000000000000000000000000000000000"

# Hyperliquid Configuration (Optional - leave empty for demo)
HYPERLIQUID_API_KEY = ""
HYPERLIQUID_API_SECRET = ""
HYPERLIQUID_BASE_URL = "https://api.hyperliquid.xyz"

# Strategy Parameters
WATCH_INTERVAL_MIN = "10"
CRON_FULL_CHECK_HOURS = "12"
RANGE_TOTAL = "0.30"
RECENTER_TRIGGER = "0.01"
HYSTERESIS_REENTRY = "0.002"
SLIPPAGE_BPS = "20"
GAS_CAP_NATIVE = "0.01"
COOLDOWN_HOURS = "2"

# Buffer Reserves
RESERVE_USDC_PCT = "0.01"
RESERVE_ETH_GAS_PCT = "0.01"
USDC_CEX_MIN_PCT = "0.003"
USDC_CEX_TARGET_PCT = "0.006"
ETH_GAS_MIN = "0.05"
ETH_GAS_TARGET = "0.10"

# Target Allocation
TARGET_LP_PCT = "0.74"
TARGET_SHORT_PCT = "0.24"
```

### Step 4: Deploy

1. Click "Deploy!"
2. Wait for deployment (usually 2-5 minutes)
3. Your app will be available at: `https://[your-app-name].streamlit.app`

## 🔐 Security Configuration

### Generate Password Hash

Before deploying, generate a secure password hash:

```bash
# Clone the repo locally
git clone https://github.com/cruzdenis/XCELFI_LP_HEDGE_V2.git
cd XCELFI_LP_HEDGE_V2

# Install dependencies
pip install bcrypt

# Generate hash
python3 -c "from core.auth import AuthManager; print(AuthManager.hash_password('YOUR_SECURE_PASSWORD'))"
```

Copy the output and use it in the `AUTH_USERS_JSON` secret.

### Demo Mode vs Production Mode

**Demo Mode (Recommended for public deployment):**
- Leave `WALLET_PRIVATE_KEY` empty
- Use placeholder addresses
- App runs in Analysis (Read-Only) mode
- Safe to share publicly

**Production Mode (Private deployment):**
- Add real `WALLET_PRIVATE_KEY`
- Add real Hyperliquid API keys
- **⚠️ NEVER share the URL publicly**
- Consider making the GitHub repo private

## 🎯 Post-Deployment

### Test the App

1. Visit your app URL
2. Login with username: `admin` and your password
3. Verify the app loads correctly
4. Check that it's in "Analysis (Read-Only)" mode

### Update Configuration

To update secrets after deployment:

1. Go to your app dashboard on Streamlit Cloud
2. Click the "⚙️" settings icon
3. Select "Secrets"
4. Edit and save
5. App will automatically restart

### Monitor the App

- **Logs:** Available in the Streamlit Cloud dashboard
- **Analytics:** Built-in usage stats
- **Alerts:** Set up email notifications for errors

## 🔄 Update the App

To deploy updates:

```bash
# Make changes locally
git add .
git commit -m "Your update message"
git push origin master
```

Streamlit Cloud will automatically redeploy!

## 💡 Tips

1. **Start in Demo Mode:** Deploy with placeholder values first
2. **Test Thoroughly:** Verify all features work before adding real credentials
3. **Monitor Usage:** Check logs regularly for errors
4. **Secure Credentials:** Never commit secrets to git
5. **Use Private Repo:** For production with real keys, make the repo private

## 🆘 Troubleshooting

### "Module not found" error

- Check that `requirements.txt` is complete
- Verify Python version is set to 3.11

### "Secrets not found" error

- Ensure all required secrets are configured
- Check for typos in secret names
- Verify TOML format is correct

### App crashes on startup

- Check logs in Streamlit Cloud dashboard
- Verify all dependencies are installed
- Test locally first with `streamlit run app.py`

## 📞 Support

- **Streamlit Docs:** https://docs.streamlit.io/streamlit-community-cloud
- **GitHub Issues:** https://github.com/cruzdenis/XCELFI_LP_HEDGE_V2/issues

---

**Ready to deploy? Let's go! 🚀**
