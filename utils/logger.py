"""Centralized logging for Transaction Processing System."""

import logging
import sys
from datetime import datetime
import json
from pathlib import Path
from typing import Optional, Dict, Any

class TransactionLogger:
    """Centralized logging for Transaction Processing System."""
    
    def __init__(self, name: str = "transaction-processor", level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup logging handlers."""
        # Console handler with colors
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handlers for different log levels
        try:
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            
            # General log file
            file_handler = logging.FileHandler(log_dir / 'transaction_processor.log')
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
            
            # Error log file
            error_handler = logging.FileHandler(log_dir / 'transaction_errors.log')
            error_handler.setLevel(logging.ERROR)
            error_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s\n%(exc_info)s'
            )
            error_handler.setFormatter(error_formatter)
            self.logger.addHandler(error_handler)
            
            # Transaction audit log
            audit_handler = logging.FileHandler(log_dir / 'transaction_audit.log')
            audit_formatter = logging.Formatter('%(message)s')
            audit_handler.setFormatter(audit_formatter)
            self.audit_logger = logging.getLogger('audit')
            self.audit_logger.setLevel(logging.INFO)
            self.audit_logger.addHandler(audit_handler)
            
            print(f"📝 Logging initialized:")
            print(f"   - General: {log_dir / 'transaction_processor.log'}")
            print(f"   - Errors: {log_dir / 'transaction_errors.log'}")
            print(f"   - Audit: {log_dir / 'transaction_audit.log'}")
            
        except Exception as e:
            self.logger.warning(f"Could not create file handlers: {e}")
    
    def get_logger(self):
        """Get the logger instance."""
        return self.logger
    
    def log_transaction(
        self, 
        transaction_id: str, 
        event: str, 
        details: Dict[str, Any],
        level: str = "INFO"
    ):
        """Log transaction-specific events."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "transaction_id": transaction_id,
            "event": event,
            "details": details
        }
        
        # Log to main logger
        log_method = getattr(self.logger, level.lower())
        log_method(f"Transaction {transaction_id}: {event} - {json.dumps(details)}")
        
        # Log to audit trail
        if hasattr(self, 'audit_logger'):
            self.audit_logger.info(json.dumps(log_entry))
    
    def log_workflow(
        self,
        workflow_id: str,
        event: str,
        details: Dict[str, Any],
        level: str = "INFO"
    ):
        """Log workflow-specific events."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "workflow_id": workflow_id,
            "event": event,
            "details": details
        }
        
        log_method = getattr(self.logger, level.lower())
        log_method(f"Workflow {workflow_id}: {event} - {json.dumps(details)}")
    
    def log_balance_update(
        self,
        account_number: str,
        transaction_id: str,
        old_balance: float,
        new_balance: float,
        amount: float,
        operation: str
    ):
        """Log balance updates for audit trail."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "account_number": account_number,
            "transaction_id": transaction_id,
            "operation": operation,
            "amount": amount,
            "old_balance": old_balance,
            "new_balance": new_balance,
            "balance_change": new_balance - old_balance
        }
        
        self.logger.info(f"Balance update for {account_number}: {operation} ${amount:.2f} (${old_balance:.2f} -> ${new_balance:.2f})")
        
        if hasattr(self, 'audit_logger'):
            self.audit_logger.info(json.dumps(log_entry))
    
    def log_insufficient_funds(
        self,
        account_number: str,
        transaction_id: str,
        requested_amount: float,
        available_balance: float
    ):
        """Log insufficient funds events."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": "INSUFFICIENT_FUNDS",
            "account_number": account_number,
            "transaction_id": transaction_id,
            "requested_amount": requested_amount,
            "available_balance": available_balance,
            "shortfall": requested_amount - available_balance
        }
        
        self.logger.warning(f"Insufficient funds for {account_number}: Requested ${requested_amount:.2f}, Available ${available_balance:.2f}")
        
        if hasattr(self, 'audit_logger'):
            self.audit_logger.info(json.dumps(log_entry))
    
    def log_acid_transaction(
        self,
        session_id: str,
        operation: str,
        status: str,
        details: Dict[str, Any]
    ):
        """Log ACID transaction operations."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": session_id,
            "operation": operation,
            "status": status,
            "details": details
        }
        
        # Use ERROR only for actual failures
        if status in ["FAILED", "ERROR", "ROLLBACK", "INSUFFICIENT_FUNDS"]:
            level = "ERROR"
        else:
            level = "INFO"
        log_method = getattr(self.logger, level.lower())
        log_method(f"ACID Transaction {session_id}: {operation} - {status}")
        
        if hasattr(self, 'audit_logger'):
            self.audit_logger.info(json.dumps(log_entry))

# Global logger instance
logger = TransactionLogger().get_logger()
transaction_logger = TransactionLogger()