"""
Logging utilities for audit trail and debugging.
"""
import json
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path


class LogManager:
    """
    Manages application logs and audit trail.
    """
    
    def __init__(self, log_dir: str = "data"):
        """
        Initialize log manager.
        
        Args:
            log_dir: Directory for log files
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        self.execution_log_file = self.log_dir / "executions.jsonl"
        self.audit_log_file = self.log_dir / "audit.jsonl"
        self.error_log_file = self.log_dir / "errors.jsonl"
    
    def _write_log(self, log_file: Path, entry: Dict):
        """Write log entry to file."""
        with open(log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
    
    def log_execution_start(self, operation_type: str, mode: str):
        """
        Log start of execution.
        
        Args:
            operation_type: Type of operation
            mode: Execution mode (MANUAL or AUTO)
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event": "execution_start",
            "operation_type": operation_type,
            "mode": mode
        }
        self._write_log(self.execution_log_file, entry)
    
    def log_execution_complete(
        self,
        operation_type: str,
        mode: str,
        results: Dict[str, Any]
    ):
        """
        Log completion of execution.
        
        Args:
            operation_type: Type of operation
            mode: Execution mode
            results: Execution results
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event": "execution_complete",
            "operation_type": operation_type,
            "mode": mode,
            "results": results
        }
        self._write_log(self.execution_log_file, entry)
    
    def log_execution_error(
        self,
        operation_type: str,
        mode: str,
        error: str
    ):
        """
        Log execution error.
        
        Args:
            operation_type: Type of operation
            mode: Execution mode
            error: Error message
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event": "execution_error",
            "operation_type": operation_type,
            "mode": mode,
            "error": error
        }
        self._write_log(self.error_log_file, entry)
    
    def log_audit_event(
        self,
        event_type: str,
        user: str,
        details: Dict[str, Any]
    ):
        """
        Log audit event.
        
        Args:
            event_type: Type of event
            user: Username
            details: Event details
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "user": user,
            "details": details
        }
        self._write_log(self.audit_log_file, entry)
    
    def get_recent_executions(self, limit: int = 10) -> List[Dict]:
        """
        Get recent execution logs.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of log entries
        """
        if not self.execution_log_file.exists():
            return []
        
        entries = []
        with open(self.execution_log_file, "r") as f:
            for line in f:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        
        return entries[-limit:]
    
    def get_recent_errors(self, limit: int = 10) -> List[Dict]:
        """
        Get recent error logs.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of error entries
        """
        if not self.error_log_file.exists():
            return []
        
        entries = []
        with open(self.error_log_file, "r") as f:
            for line in f:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        
        return entries[-limit:]
