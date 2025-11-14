# Railway Cron Job Setup Guide

## 📋 Overview

This project includes automatic background synchronization using Railway's Cron Job feature (Pro Plan required).

## 🚀 Setup Instructions

### Step 1: Deploy Main Service

The main Streamlit app is already deployed and running.

### Step 2: Create Cron Service

1. Go to your Railway project dashboard
2. Click **"+ New Service"**
3. Select **"GitHub Repo"** (same repo: `XCELFI_LP_HEDGE_V2`)
4. Name it: `xcelfi-sync-cron`

### Step 3: Configure Cron Service

1. In the new service settings, go to **"Settings"** tab
2. Under **"Deploy"**, set:
   - **Start Command**: `python3 sync_job.py`
   - **Cron Schedule**: Choose your interval (see below)

### Step 4: Set Cron Schedule

Railway uses standard cron syntax. Choose one:

| Interval | Cron Expression | Description |
|----------|----------------|-------------|
| 1 hour   | `0 * * * *`    | Every hour at minute 0 |
| 2 hours  | `0 */2 * * *`  | Every 2 hours |
| 4 hours  | `0 */4 * * *`  | Every 4 hours |
| 6 hours  | `0 */6 * * *`  | Every 6 hours |
| 12 hours | `0 */12 * * *` | Every 12 hours |
| 24 hours | `0 0 * * *`    | Every day at midnight |

### Step 5: Enable Cron Mode

1. In service settings, go to **"Variables"** tab
2. Add environment variable:
   - **Key**: `RAILWAY_CRON_MODE`
   - **Value**: `true`

### Step 6: Share Data Directory

Both services need to access the same data directory:

1. In the cron service, go to **"Volumes"** tab
2. Mount volume:
   - **Mount Path**: `/tmp/xcelfi_data`
   - **Volume Name**: `xcelfi-data` (create if doesn't exist)

3. Do the same for the main web service

## 🔍 Monitoring

### View Logs

1. Go to cron service in Railway dashboard
2. Click **"Logs"** tab
3. You'll see sync job execution logs

### Expected Log Output

```
[2025-11-14T12:00:00] Starting sync job...
[INFO] Syncing data for wallet: 0xc1E18438Fed146D814418364134fE28cC8622B5C
[INFO] Fetching portfolio data from Octav.fi...
[INFO] Found 2 LP positions and 2 perp positions
[SUCCESS] Sync completed successfully!
[INFO] Net Worth: $10,245.50
[INFO] Balanced: 0, Under-hedged: 1, Over-hedged: 1
[INFO] Actions needed:
  - INCREASE SHORT ETH: 0.137380
  - DECREASE SHORT BTC: 0.004488
```

## ⚙️ Configuration

The cron job uses the same configuration as the main app:
- API Key from `/tmp/xcelfi_data/config.json`
- Auto-sync settings (enabled/disabled, interval)
- Tolerance percentage

**Important**: Configure the app first before enabling cron job!

## 🛠️ Troubleshooting

### Cron job not running

1. Check if `auto_sync_enabled` is `true` in app configuration
2. Verify cron schedule syntax
3. Check Railway service logs for errors

### Data not syncing

1. Verify both services share the same volume
2. Check API key is valid
3. Review sync job logs for error messages

### Duplicate syncs

If you have both client-side auto-sync and cron job enabled, you may get duplicate syncs. Recommendation:
- **Disable client-side auto-sync** in app configuration
- **Use only Railway cron job** for background sync

## 📊 Benefits

✅ **24/7 Automatic Sync** - No need to keep browser open
✅ **Reliable Scheduling** - Railway handles execution
✅ **Centralized Logs** - All sync logs in Railway dashboard
✅ **Resource Efficient** - Runs only when needed
✅ **Shared Data** - Main app shows latest synced data

## 💡 Recommended Setup

For optimal performance:
1. **Disable** client-side auto-sync in app settings
2. **Enable** Railway cron job with your preferred interval
3. **Set interval** based on your needs:
   - Active trading: 1-2 hours
   - Regular monitoring: 6-12 hours
   - Daily check: 24 hours

## 🔐 Security

- Configuration is stored in Railway volumes (not in code)
- API keys are never exposed in logs
- Private keys are encrypted in Railway environment

---

**Need Help?** Check Railway documentation or contact support.
