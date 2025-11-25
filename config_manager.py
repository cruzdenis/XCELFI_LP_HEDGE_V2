"""
Configuration Manager - Multi-Wallet Support
Handles persistent storage of configuration and data for multiple wallets
"""

import json
import os
from datetime import datetime
from pathlib import Path

class ConfigManager:
    def __init__(self, config_dir="/tmp/xcelfi_data"):
        """Initialize config manager with data directory"""
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.config_file = self.config_dir / "config.json"
        self._migrate_to_multi_wallet()
    
    def _migrate_to_multi_wallet(self):
        """Migrate old single-wallet config to new multi-wallet format"""
        if not self.config_file.exists():
            return
        
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            # Check if already in new format
            if "wallets" in config and "active_wallet" in config:
                return  # Already migrated
            
            # Migrate old format to new format
            wallet_address = config.get("wallet_address", "default")
            
            new_config = {
                "version": "2.0",
                "wallets": {
                    wallet_address: {
                        "name": "Wallet Principal",
                        "wallet_address": wallet_address,
                        "api_key": config.get("api_key", ""),
                        "hyperliquid_address": config.get("hyperliquid_address", ""),
                        "hyperliquid_private_key": config.get("hyperliquid_private_key", ""),
                        "enabled_protocols": config.get("enabled_protocols", ["Revert", "Uniswap3", "Uniswap4", "Dhedge"]),
                        "hedge_value_threshold_pct": config.get("hedge_value_threshold_pct", 10.0),
                        "sync_history": [],
                        "execution_history": [],
                        "transactions": []
                    }
                },
                "active_wallet": wallet_address
            }
            
            # Migrate old history files if they exist
            old_history_file = self.config_dir / "history.json"
            if old_history_file.exists():
                with open(old_history_file, 'r') as f:
                    new_config["wallets"][wallet_address]["sync_history"] = json.load(f)
                old_history_file.unlink()  # Remove old file
            
            old_execution_file = self.config_dir / "execution_history.json"
            if old_execution_file.exists():
                with open(old_execution_file, 'r') as f:
                    new_config["wallets"][wallet_address]["execution_history"] = json.load(f)
                old_execution_file.unlink()  # Remove old file
            
            old_transactions_file = self.config_dir / "transactions.json"
            if old_transactions_file.exists():
                with open(old_transactions_file, 'r') as f:
                    new_config["wallets"][wallet_address]["transactions"] = json.load(f)
                old_transactions_file.unlink()  # Remove old file
            
            # Save migrated config
            with open(self.config_file, 'w') as f:
                json.dump(new_config, f, indent=2)
            
            print(f"✅ Migrated config to multi-wallet format. Active wallet: {wallet_address}")
            
        except Exception as e:
            print(f"Error migrating config: {e}")
    
    def load_config(self):
        """Load full multi-wallet configuration"""
        if not self.config_file.exists():
            return {
                "version": "2.0",
                "wallets": {},
                "active_wallet": None
            }
        
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            return {
                "version": "2.0",
                "wallets": {},
                "active_wallet": None
            }
    
    def save_config(self, config):
        """Save full multi-wallet configuration"""
        config["saved_at"] = datetime.now().isoformat()
        
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        return True
    
    def get_active_wallet_id(self):
        """Get the currently active wallet ID"""
        config = self.load_config()
        return config.get("active_wallet")
    
    def set_active_wallet(self, wallet_id):
        """Set the active wallet"""
        config = self.load_config()
        if wallet_id in config.get("wallets", {}):
            config["active_wallet"] = wallet_id
            self.save_config(config)
            return True
        return False
    
    def get_active_wallet_config(self):
        """Get configuration for the active wallet"""
        config = self.load_config()
        active_wallet_id = config.get("active_wallet")
        
        if not active_wallet_id:
            return None
        
        return config.get("wallets", {}).get(active_wallet_id)
    
    def save_wallet_config(self, wallet_id, wallet_config):
        """Save configuration for a specific wallet"""
        config = self.load_config()
        
        if "wallets" not in config:
            config["wallets"] = {}
        
        config["wallets"][wallet_id] = wallet_config
        self.save_config(config)
        return True
    
    def add_wallet(self, wallet_id, name, api_key="", hyperliquid_address="", hyperliquid_private_key=""):
        """Add a new wallet"""
        config = self.load_config()
        
        if "wallets" not in config:
            config["wallets"] = {}
        
        if wallet_id in config["wallets"]:
            return False, "Wallet already exists"
        
        config["wallets"][wallet_id] = {
            "name": name,
            "wallet_address": wallet_id,
            "api_key": api_key,
            "hyperliquid_address": hyperliquid_address,
            "hyperliquid_private_key": hyperliquid_private_key,
            "enabled_protocols": ["Revert", "Uniswap3", "Uniswap4", "Dhedge"],
            "hedge_value_threshold_pct": 10.0,
            "sync_history": [],
            "execution_history": [],
            "transactions": []
        }
        
        # Set as active if it's the first wallet
        if not config.get("active_wallet"):
            config["active_wallet"] = wallet_id
        
        self.save_config(config)
        return True, "Wallet added successfully"
    
    def remove_wallet(self, wallet_id):
        """Remove a wallet"""
        config = self.load_config()
        
        if wallet_id not in config.get("wallets", {}):
            return False, "Wallet not found"
        
        del config["wallets"][wallet_id]
        
        # If removed wallet was active, set another as active
        if config.get("active_wallet") == wallet_id:
            remaining_wallets = list(config.get("wallets", {}).keys())
            config["active_wallet"] = remaining_wallets[0] if remaining_wallets else None
        
        self.save_config(config)
        return True, "Wallet removed successfully"
    
    def get_all_wallets(self):
        """Get all wallets"""
        config = self.load_config()
        return config.get("wallets", {})
    
    def has_config(self):
        """Check if any wallet configuration exists"""
        config = self.load_config()
        return len(config.get("wallets", {})) > 0
    
    # Wallet-specific data methods
    
    def add_sync_history(self, summary, nav_value=None, wallet_id=None):
        """Add sync history entry for a wallet with NAV value"""
        if wallet_id is None:
            wallet_id = self.get_active_wallet_id()
        
        if not wallet_id:
            return False
        
        config = self.load_config()
        wallet = config["wallets"].get(wallet_id)
        
        if not wallet:
            return False
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "summary": summary,
            "nav": nav_value  # Save NAV value with sync history
        }
        
        if "sync_history" not in wallet:
            wallet["sync_history"] = []
        
        wallet["sync_history"].insert(0, entry)
        wallet["sync_history"] = wallet["sync_history"][:50]  # Keep last 50
        
        self.save_config(config)
        return True
    
    def load_history(self, wallet_id=None):
        """Load sync history for a wallet"""
        if wallet_id is None:
            wallet_id = self.get_active_wallet_id()
        
        if not wallet_id:
            return []
        
        config = self.load_config()
        wallet = config["wallets"].get(wallet_id)
        
        if not wallet:
            return []
        
        return wallet.get("sync_history", [])
    
    def get_last_sync(self, wallet_id=None):
        """Get last sync timestamp for a wallet"""
        history = self.load_history(wallet_id)
        if history:
            return history[0].get("timestamp")
        return None
    
    def add_execution_history(self, execution_data, wallet_id=None):
        """Add execution history entry for a wallet"""
        if wallet_id is None:
            wallet_id = self.get_active_wallet_id()
        
        if not wallet_id:
            return False
        
        config = self.load_config()
        wallet = config["wallets"].get(wallet_id)
        
        if not wallet:
            return False
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "execution": execution_data
        }
        
        if "execution_history" not in wallet:
            wallet["execution_history"] = []
        
        wallet["execution_history"].insert(0, entry)
        wallet["execution_history"] = wallet["execution_history"][:200]  # Keep last 200
        
        self.save_config(config)
        return True
    
    def load_execution_history(self, wallet_id=None):
        """Load execution history for a wallet"""
        if wallet_id is None:
            wallet_id = self.get_active_wallet_id()
        
        if not wallet_id:
            return []
        
        config = self.load_config()
        wallet = config["wallets"].get(wallet_id)
        
        if not wallet:
            return []
        
        return wallet.get("execution_history", [])
    
    def add_transaction(self, transaction_type: str, amount_usd: float, description: str = "", custom_date: str = None, wallet_id=None):
        """Add transaction for a wallet"""
        if wallet_id is None:
            wallet_id = self.get_active_wallet_id()
        
        if not wallet_id:
            return False
        
        config = self.load_config()
        wallet = config["wallets"].get(wallet_id)
        
        if not wallet:
            return False
        
        timestamp = custom_date if custom_date else datetime.now().isoformat()
        
        transaction = {
            "timestamp": timestamp,
            "type": transaction_type,
            "amount_usd": amount_usd,
            "description": description
        }
        
        if "transactions" not in wallet:
            wallet["transactions"] = []
        
        wallet["transactions"].append(transaction)
        
        self.save_config(config)
        return True
    
    def load_transactions(self, wallet_id=None):
        """Load transactions for a wallet"""
        if wallet_id is None:
            wallet_id = self.get_active_wallet_id()
        
        if not wallet_id:
            return []
        
        config = self.load_config()
        wallet = config["wallets"].get(wallet_id)
        
        if not wallet:
            return []
        
        return wallet.get("transactions", [])
    
    def delete_transaction(self, index: int, wallet_id=None):
        """Delete a transaction for a wallet"""
        if wallet_id is None:
            wallet_id = self.get_active_wallet_id()
        
        if not wallet_id:
            return False
        
        config = self.load_config()
        wallet = config["wallets"].get(wallet_id)
        
        if not wallet or "transactions" not in wallet:
            return False
        
        if 0 <= index < len(wallet["transactions"]):
            wallet["transactions"].pop(index)
            self.save_config(config)
            return True
        
        return False
    
    def delete_sync_entry(self, timestamp, wallet_id=None):
        """Delete a sync history entry for a wallet"""
        if wallet_id is None:
            wallet_id = self.get_active_wallet_id()
        
        if not wallet_id:
            return False
        
        config = self.load_config()
        wallet = config["wallets"].get(wallet_id)
        
        if not wallet or "sync_history" not in wallet:
            return False
        
        original_len = len(wallet["sync_history"])
        wallet["sync_history"] = [e for e in wallet["sync_history"] if e.get('timestamp') != timestamp]
        
        if len(wallet["sync_history"]) < original_len:
            self.save_config(config)
            return True
        
        return False
    
    def delete_execution_entry(self, timestamp, wallet_id=None):
        """Delete an execution history entry for a wallet"""
        if wallet_id is None:
            wallet_id = self.get_active_wallet_id()
        
        if not wallet_id:
            return False
        
        config = self.load_config()
        wallet = config["wallets"].get(wallet_id)
        
        if not wallet or "execution_history" not in wallet:
            return False
        
        original_len = len(wallet["execution_history"])
        wallet["execution_history"] = [e for e in wallet["execution_history"] if e.get('timestamp') != timestamp]
        
        if len(wallet["execution_history"]) < original_len:
            self.save_config(config)
            return True
        
        return False
    
    def clear_history(self, wallet_id=None):
        """Clear sync history for a wallet"""
        if wallet_id is None:
            wallet_id = self.get_active_wallet_id()
        
        if not wallet_id:
            return False
        
        config = self.load_config()
        wallet = config["wallets"].get(wallet_id)
        
        if not wallet:
            return False
        
        wallet["sync_history"] = []
        self.save_config(config)
        return True
    
    def clear_execution_history(self, wallet_id=None):
        """Clear execution history for a wallet"""
        if wallet_id is None:
            wallet_id = self.get_active_wallet_id()
        
        if not wallet_id:
            return False
        
        config = self.load_config()
        wallet = config["wallets"].get(wallet_id)
        
        if not wallet:
            return False
        
        wallet["execution_history"] = []
        self.save_config(config)
        return True
    
    def clear_transactions(self, wallet_id=None):
        """Clear transactions for a wallet"""
        if wallet_id is None:
            wallet_id = self.get_active_wallet_id()
        
        if not wallet_id:
            return False
        
        config = self.load_config()
        wallet = config["wallets"].get(wallet_id)
        
        if not wallet:
            return False
        
        wallet["transactions"] = []
        self.save_config(config)
        return True
    
    # NAV-related methods
    
    def add_nav_snapshot(self, nav_value: float, custom_date: str = None, wallet_id=None):
        """Add a NAV snapshot for historical tracking"""
        if wallet_id is None:
            wallet_id = self.get_active_wallet_id()
        
        if not wallet_id:
            return False
        
        config = self.load_config()
        wallet = config["wallets"].get(wallet_id)
        
        if not wallet:
            return False
        
        timestamp = custom_date if custom_date else datetime.now().isoformat()
        
        snapshot = {
            "timestamp": timestamp,
            "nav": nav_value
        }
        
        if "nav_snapshots" not in wallet:
            wallet["nav_snapshots"] = []
        
        wallet["nav_snapshots"].append(snapshot)
        
        # Sort by timestamp
        wallet["nav_snapshots"].sort(key=lambda x: x["timestamp"])
        
        self.save_config(config)
        return True
    
    def load_nav_snapshots(self, wallet_id=None):
        """Load NAV snapshots for a wallet"""
        if wallet_id is None:
            wallet_id = self.get_active_wallet_id()
        
        if not wallet_id:
            return []
        
        config = self.load_config()
        wallet = config["wallets"].get(wallet_id)
        
        if not wallet:
            return []
        
        return wallet.get("nav_snapshots", [])
    
    def delete_nav_snapshot(self, index: int, wallet_id=None):
        """Delete a NAV snapshot by index"""
        if wallet_id is None:
            wallet_id = self.get_active_wallet_id()
        
        if not wallet_id:
            return False
        
        config = self.load_config()
        wallet = config["wallets"].get(wallet_id)
        
        if not wallet or "nav_snapshots" not in wallet:
            return False
        
        if 0 <= index < len(wallet["nav_snapshots"]):
            wallet["nav_snapshots"].pop(index)
            self.save_config(config)
            return True
        
        return False
    
    def add_share_transaction(self, transaction_type: str, amount_usd: float, shares: float, nav_per_share: float, description: str = "", custom_date: str = None, wallet_id=None):
        """Add a share transaction (deposit/withdrawal with share calculation)"""
        if wallet_id is None:
            wallet_id = self.get_active_wallet_id()
        
        if not wallet_id:
            return False
        
        config = self.load_config()
        wallet = config["wallets"].get(wallet_id)
        
        if not wallet:
            return False
        
        timestamp = custom_date if custom_date else datetime.now().isoformat()
        
        transaction = {
            "timestamp": timestamp,
            "type": transaction_type,  # "deposit" or "withdrawal"
            "amount_usd": amount_usd,
            "shares": shares,
            "nav_per_share": nav_per_share,
            "description": description
        }
        
        if "share_transactions" not in wallet:
            wallet["share_transactions"] = []
        
        wallet["share_transactions"].append(transaction)
        
        # Sort by timestamp
        wallet["share_transactions"].sort(key=lambda x: x["timestamp"])
        
        self.save_config(config)
        return True
    
    def load_share_transactions(self, wallet_id=None):
        """Load share transactions for a wallet"""
        if wallet_id is None:
            wallet_id = self.get_active_wallet_id()
        
        if not wallet_id:
            return []
        
        config = self.load_config()
        wallet = config["wallets"].get(wallet_id)
        
        if not wallet:
            return []
        
        return wallet.get("share_transactions", [])
    
    def delete_share_transaction(self, index: int, wallet_id=None):
        """Delete a share transaction by index"""
        if wallet_id is None:
            wallet_id = self.get_active_wallet_id()
        
        if not wallet_id:
            return False
        
        config = self.load_config()
        wallet = config["wallets"].get(wallet_id)
        
        if not wallet or "share_transactions" not in wallet:
            return False
        
        if 0 <= index < len(wallet["share_transactions"]):
            wallet["share_transactions"].pop(index)
            self.save_config(config)
            return True
        
        return False
    
    def get_total_shares(self, wallet_id=None):
        """Calculate total shares (deposits - withdrawals)"""
        transactions = self.load_share_transactions(wallet_id)
        
        total_shares = 0
        for txn in transactions:
            if txn["type"] == "deposit":
                total_shares += txn["shares"]
            elif txn["type"] == "withdrawal":
                total_shares -= txn["shares"]
        
        return total_shares
    
    def create_backup(self, wallet_id=None):
        """Create backup for a specific wallet or all wallets"""
        config = self.load_config()
        
        if wallet_id:
            # Backup single wallet
            wallet = config["wallets"].get(wallet_id)
            if not wallet:
                return None
            
            return {
                "backup_version": "3.0",
                "backup_type": "single_wallet",
                "backup_timestamp": datetime.now().isoformat(),
                "wallet_id": wallet_id,
                "wallet_data": wallet
            }
        else:
            # Backup all wallets
            return {
                "backup_version": "3.0",
                "backup_type": "all_wallets",
                "backup_timestamp": datetime.now().isoformat(),
                "config": config
            }
    
    def restore_backup(self, backup_data):
        """Restore backup (supports old and new formats)"""
        try:
            backup_version = backup_data.get("backup_version", "1.0")
            
            if backup_version == "3.0":
                # New multi-wallet backup
                if backup_data.get("backup_type") == "all_wallets":
                    # Restore full config
                    config = backup_data.get("config")
                    if config:
                        self.save_config(config)
                        return True, "All wallets restored successfully"
                elif backup_data.get("backup_type") == "single_wallet":
                    # Restore single wallet
                    wallet_id = backup_data.get("wallet_id")
                    wallet_data = backup_data.get("wallet_data")
                    if wallet_id and wallet_data:
                        self.save_wallet_config(wallet_id, wallet_data)
                        return True, f"Wallet {wallet_id} restored successfully"
            else:
                # Old single-wallet backup (v1.0 or v2.0)
                # Convert to new format
                config_data = backup_data.get("config", {})
                wallet_address = config_data.get("wallet_address", "imported_wallet")
                
                wallet_data = {
                    "name": "Imported Wallet",
                    "wallet_address": wallet_address,
                    "api_key": config_data.get("api_key", ""),
                    "hyperliquid_address": config_data.get("hyperliquid_address", ""),
                    "hyperliquid_private_key": config_data.get("hyperliquid_private_key", ""),
                    "enabled_protocols": config_data.get("enabled_protocols", ["Revert", "Uniswap3", "Uniswap4", "Dhedge"]),
                    "hedge_value_threshold_pct": config_data.get("hedge_value_threshold_pct", 10.0),
                    "sync_history": backup_data.get("sync_history", backup_data.get("history", [])),
                    "execution_history": backup_data.get("execution_history", []),
                    "transactions": backup_data.get("transactions", [])
                }
                
                success, message = self.add_wallet(
                    wallet_address,
                    "Imported Wallet",
                    config_data.get("api_key", ""),
                    config_data.get("hyperliquid_address", ""),
                    config_data.get("hyperliquid_private_key", "")
                )
                
                if success:
                    self.save_wallet_config(wallet_address, wallet_data)
                    return True, "Old backup imported as new wallet"
                else:
                    return False, message
            
            return False, "Invalid backup format"
            
        except Exception as e:
            return False, f"Error restoring backup: {str(e)}"
