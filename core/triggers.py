"""
Trigger detection module for rebalancing decisions.
Monitors price deviations and determines when recentering is needed.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional


@dataclass
class TriggerState:
    """State of trigger system."""
    needs_recenter: bool
    deviation_pct: float
    current_price: float
    range_lower: float
    range_upper: float
    last_recenter_time: Optional[datetime]
    cooldown_remaining_hours: float
    reason: str


class TriggerMonitor:
    """
    Monitors LP position and detects when recentering is needed.
    
    Implements hysteresis to avoid ping-pong rebalancing.
    """
    
    def __init__(
        self,
        recenter_trigger: float = 0.01,  # 1% deviation
        hysteresis_reentry: float = 0.002,  # 0.2% reentry
        cooldown_hours: int = 2
    ):
        """
        Initialize trigger monitor.
        
        Args:
            recenter_trigger: Deviation threshold to trigger recenter (e.g., 0.01 = 1%)
            hysteresis_reentry: Reentry threshold to avoid ping-pong (e.g., 0.002 = 0.2%)
            cooldown_hours: Minimum hours between recenters
        """
        self.recenter_trigger = recenter_trigger
        self.hysteresis_reentry = hysteresis_reentry
        self.cooldown_hours = cooldown_hours
        
        self.last_recenter_time: Optional[datetime] = None
        self.triggered = False
    
    def check_trigger(
        self,
        current_price: float,
        range_lower: float,
        range_upper: float
    ) -> TriggerState:
        """
        Check if recentering trigger is activated.
        
        Args:
            current_price: Current market price
            range_lower: Lower bound of LP range
            range_upper: Upper bound of LP range
            
        Returns:
            TriggerState with trigger decision and details
        """
        # Calculate range center
        range_center = (range_lower + range_upper) / 2
        
        # Calculate deviation from center
        deviation = abs(current_price - range_center) / range_center
        
        # Check cooldown
        cooldown_remaining = 0.0
        if self.last_recenter_time:
            time_since_last = datetime.now() - self.last_recenter_time
            cooldown_remaining = max(0, self.cooldown_hours - time_since_last.total_seconds() / 3600)
        
        in_cooldown = cooldown_remaining > 0
        
        # Determine if we need to recenter
        needs_recenter = False
        reason = "Within range"
        
        # Check if price is outside range entirely
        if current_price < range_lower or current_price > range_upper:
            needs_recenter = True
            reason = "Price outside LP range"
        # Check deviation with hysteresis
        elif not self.triggered and deviation >= self.recenter_trigger:
            # First time crossing threshold
            self.triggered = True
            needs_recenter = True
            reason = f"Deviation {deviation*100:.2f}% exceeds trigger {self.recenter_trigger*100:.2f}%"
        elif self.triggered and deviation >= self.hysteresis_reentry:
            # Still above reentry threshold
            needs_recenter = True
            reason = f"Deviation {deviation*100:.2f}% still above reentry {self.hysteresis_reentry*100:.2f}%"
        elif self.triggered and deviation < self.hysteresis_reentry:
            # Back within reentry threshold
            self.triggered = False
            reason = "Back within acceptable range"
        
        # Apply cooldown
        if needs_recenter and in_cooldown:
            needs_recenter = False
            reason = f"In cooldown ({cooldown_remaining:.1f}h remaining)"
        
        return TriggerState(
            needs_recenter=needs_recenter,
            deviation_pct=deviation * 100,
            current_price=current_price,
            range_lower=range_lower,
            range_upper=range_upper,
            last_recenter_time=self.last_recenter_time,
            cooldown_remaining_hours=cooldown_remaining,
            reason=reason
        )
    
    def mark_recentered(self):
        """Mark that a recenter has been executed."""
        self.last_recenter_time = datetime.now()
        self.triggered = False
    
    def reset(self):
        """Reset trigger state."""
        self.last_recenter_time = None
        self.triggered = False
