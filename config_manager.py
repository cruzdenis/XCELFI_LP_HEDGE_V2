"""
Configuration Manager
Handles persistent storage of configuration and sync history
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
        self.history_file = self.config_dir / "history.json"
        self.execution_history_file = self.config_dir / "execution_history.json"
        self.transactions_file = self.config_dir / "transactions.json"
    
    def save_config(self, config):
        """Save configuration to file"""
        # Add timestamp
        config["saved_at"] = datetime.now().isoformat()
        
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        return True
    
    def load_config(self):
        """Load configuration from file"""
        if not self.config_file.exists():
            return None
        
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            return None
    
    def has_config(self):
        """Check if configuration exists"""
        return self.config_file.exists()
    
    def add_sync_history(self, summary):
        """Add a sync entry to history"""
        history = self.load_history()
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "summary": summary
        }
        
        history.insert(0, entry)  # Add to beginning
        
        # Keep only last 50 entries
        history = history[:50]
        
        with open(self.history_file, 'w') as f:
            json.dump(history, f, indent=2)
        
        return True
    
    def load_history(self):
        """Load sync history from file"""
        if not self.history_file.exists():
            return []
        
        try:
            with open(self.history_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading history: {e}")
            return []
    
    def get_last_sync(self):
        """Get timestamp of last sync"""
        history = self.load_history()
        if history:
            return history[0].get("timestamp")
        return None
    
    def clear_config(self):
        """Clear saved configuration"""
        if self.config_file.exists():
            self.config_file.unlink()
        return True
    
    def clear_history(self):
        """Clear sync history"""
        if self.history_file.exists():
            self.history_file.unlink()
        return True
    
    def create_backup(self):
        """Create a backup of all data (config + history + executions + transactions)"""
        backup_data = {
            "backup_version": "2.0",
            "backup_timestamp": datetime.now().isoformat(),
            "config": self.load_config(),
            "sync_history": self.load_history(),
            "execution_history": self.load_execution_history(),
            "transactions": self.load_transactions()
        }
        return backup_data
    
    def restore_backup(self, backup_data):
        """Restore data from backup"""
        try:
            # Validate backup structure
            if not isinstance(backup_data, dict):
                return False, "Invalid backup format"
            
            if "config" not in backup_data:
                return False, "Missing config in backup"
            
            # Restore config
            config = backup_data.get("config")
            if config:
                with open(self.config_file, 'w') as f:
                    json.dump(config, f, indent=2)
            
            # Restore sync history (support both old 'history' and new 'sync_history' keys)
            sync_history = backup_data.get("sync_history") or backup_data.get("history")
            if sync_history:
                with open(self.history_file, 'w') as f:
                    json.dump(sync_history, f, indent=2)
            
            # Restore execution history
            execution_history = backup_data.get("execution_history")
            if execution_history:
                with open(self.execution_history_file, 'w') as f:
                    json.dump(execution_history, f, indent=2)
            
            # Restore transactions
            transactions = backup_data.get("transactions")
            if transactions:
                with open(self.transactions_file, 'w') as f:
                    json.dump(transactions, f, indent=2)
            
            return True, "Backup restored successfully"
            
        except Exception as e:
            return False, f"Error restoring backup: {str(e)}"
    
    def add_execution_history(self, execution_data):
        """Add an execution entry to history"""
        history = self.load_execution_history()
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "execution": execution_data
        }
        
        history.insert(0, entry)  # Add to beginning
        
        # Keep only last 200 entries
        history = history[:200]
        
        with open(self.execution_history_file, 'w') as f:
            json.dump(history, f, indent=2)
        
        return True
    
    def load_execution_history(self):
        """Load execution history from file"""
        if not self.execution_history_file.exists():
            return []
        
        try:
            with open(self.execution_history_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading execution history: {e}")
            return []
    
    def clear_execution_history(self):
        """Clear execution history"""
        if self.execution_history_file.exists():
            self.execution_history_file.unlink()
        return True
    
    def delete_sync_entry(self, timestamp):
        """Delete a specific sync history entry by timestamp"""
        history = self.load_history()
        original_len = len(history)
        history = [entry for entry in history if entry.get('timestamp') != timestamp]
        
        if len(history) < original_len:
            with open(self.history_file, 'w') as f:
                json.dump(history, f, indent=2)
            return True
        return False
    
    def delete_execution_entry(self, timestamp):
        """Delete a specific execution history entry by timestamp"""
        history = self.load_execution_history()
        original_len = len(history)
        history = [entry for entry in history if entry.get('timestamp') != timestamp]
        
        if len(history) < original_len:
            with open(self.execution_history_file, 'w') as f:
                json.dump(history, f, indent=2)
            return True
        return False
    
    def add_transaction(self, transaction_type: str, amount_usd: float, description: str = "", custom_date: str = None):
        """Add a deposit or withdrawal transaction"""
        transactions = self.load_transactions()
        
        # Use custom date if provided, otherwise use current time
        if custom_date:
            timestamp = custom_date
        else:
            timestamp = datetime.now().isoformat()
        
        transaction = {
            "timestamp": timestamp,
            "type": transaction_type,  # "deposit" or "withdrawal"
            "amount_usd": amount_usd,
            "description": description
        }
        
        transactions.append(transaction)
        
        with open(self.transactions_file, 'w') as f:
            json.dump(transactions, f, indent=2)
    
    def load_transactions(self) -> list:
        """Load all transactions"""
        if os.path.exists(self.transactions_file):
            with open(self.transactions_file, 'r') as f:
                return json.load(f)
        return []
    
    def delete_transaction(self, index: int):
        """Delete a transaction by index"""
        transactions = self.load_transactions()
        if 0 <= index < len(transactions):
            transactions.pop(index)
            with open(self.transactions_file, 'w') as f:
                json.dump(transactions, f, indent=2)
    
    def clear_transactions(self):
        """Clear all transactions"""
        with open(self.transactions_file, 'w') as f:
            json.dump([], f)
