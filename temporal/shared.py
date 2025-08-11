"""Shared constants and data models for the money transfer application."""

from dataclasses import dataclass
from typing import Optional

# Task Queue name used by both the Worker and starter
MONEY_TRANSFER_TASK_QUEUE_NAME = "money-transfer-task-queue"

@dataclass
class PaymentDetails:
    """Data class representing payment details for money transfer."""
    
    source_account: str
    target_account: str
    amount: int  # Amount in cents to avoid floating point precision issues
    reference_id: str

@dataclass 
class TransferResult:
    """Data class representing the result of a money transfer."""
    
    success: bool
    message: str
    withdraw_transaction_id: Optional[str] = None
    deposit_transaction_id: Optional[str] = None

class InvalidAccountError(Exception):
    """Raised when an invalid account is encountered."""
    pass

class InsufficientFundsError(Exception):
    """Raised when there are insufficient funds for withdrawal."""
    pass
