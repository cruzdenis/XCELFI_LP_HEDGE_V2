"""
Quota Calculator
Calculates quota values based on deposits, withdrawals, and net worth history
"""

from datetime import datetime
from typing import List, Dict, Tuple

class QuotaCalculator:
    def __init__(self, initial_quota_value: float = 1.0):
        """Initialize quota calculator with initial quota value"""
        self.initial_quota_value = initial_quota_value
    
    def calculate_quota_history(self, sync_history: List[Dict], transactions: List[Dict]) -> List[Dict]:
        """
        Calculate quota values for each sync point
        
        Args:
            sync_history: List of sync entries with timestamp and networth
            transactions: List of deposit/withdrawal transactions
        
        Returns:
            List of quota data points with timestamp, quota_value, total_quotas, net_worth
        """
        if not sync_history:
            return []
        
        # Sort transactions by timestamp
        sorted_transactions = sorted(transactions, key=lambda x: x['timestamp'])
        
        # Sort sync history by timestamp (oldest first)
        sorted_history = sorted(sync_history, key=lambda x: x['timestamp'])
        
        quota_history = []
        total_quotas = 0.0
        transaction_index = 0
        
        for sync in sorted_history:
            sync_time = datetime.fromisoformat(sync['timestamp'])
            net_worth = float(sync['summary'].get('networth', 0))
            
            # Process all transactions up to this sync point
            while transaction_index < len(sorted_transactions):
                trans = sorted_transactions[transaction_index]
                trans_time = datetime.fromisoformat(trans['timestamp'])
                
                if trans_time > sync_time:
                    break  # Future transaction, stop here
                
                # Calculate current quota value before transaction
                if total_quotas > 0:
                    current_quota_value = net_worth / total_quotas
                else:
                    current_quota_value = self.initial_quota_value
                
                # Process transaction
                amount = float(trans['amount_usd'])
                if trans['type'] == 'deposit':
                    # Buy quotas at current price
                    quotas_bought = amount / current_quota_value
                    total_quotas += quotas_bought
                elif trans['type'] == 'withdrawal':
                    # Sell quotas at current price
                    quotas_sold = amount / current_quota_value
                    total_quotas -= quotas_sold
                
                transaction_index += 1
            
            # Calculate quota value at this sync point
            if total_quotas > 0:
                quota_value = net_worth / total_quotas
            else:
                # No quotas yet, use initial value
                quota_value = self.initial_quota_value
                total_quotas = 0
            
            quota_history.append({
                'timestamp': sync['timestamp'],
                'quota_value': quota_value,
                'total_quotas': total_quotas,
                'net_worth': net_worth
            })
        
        return quota_history
    
    def calculate_performance_metrics(self, quota_history: List[Dict], transactions: List[Dict]) -> Dict:
        """
        Calculate performance metrics
        
        Returns:
            Dict with total_return_pct, total_invested, current_value, profit_loss, etc.
        """
        if not quota_history:
            return {
                'total_return_pct': 0.0,
                'total_invested': 0.0,
                'current_value': 0.0,
                'profit_loss': 0.0,
                'initial_quota_value': self.initial_quota_value,
                'current_quota_value': self.initial_quota_value,
                'total_deposits': 0.0,
                'total_withdrawals': 0.0
            }
        
        # Calculate totals
        total_deposits = sum(float(t['amount_usd']) for t in transactions if t['type'] == 'deposit')
        total_withdrawals = sum(float(t['amount_usd']) for t in transactions if t['type'] == 'withdrawal')
        
        # Get current values
        latest = quota_history[-1]
        current_quota_value = latest['quota_value']
        current_net_worth = latest['net_worth']
        
        # Calculate return
        quota_return_pct = ((current_quota_value - self.initial_quota_value) / self.initial_quota_value) * 100
        
        # Calculate profit/loss
        total_invested = total_deposits - total_withdrawals
        profit_loss = current_net_worth - total_invested
        
        return {
            'total_return_pct': quota_return_pct,
            'total_invested': total_invested,
            'current_value': current_net_worth,
            'profit_loss': profit_loss,
            'initial_quota_value': self.initial_quota_value,
            'current_quota_value': current_quota_value,
            'total_deposits': total_deposits,
            'total_withdrawals': total_withdrawals,
            'total_quotas': latest['total_quotas']
        }
