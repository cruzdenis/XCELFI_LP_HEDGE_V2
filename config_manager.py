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
    
    def save_config(self, api_key, wallet_address, tolerance_pct=5.0, hyperliquid_private_key=""):
        """Save configuration to file"""
        config = {
            "api_key": api_key,
            "wallet_address": wallet_address,
            "tolerance_pct": tolerance_pct,
            "hyperliquid_private_key": hyperliquid_private_key,
            "saved_at": datetime.now().isoformat()
        }
        
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
