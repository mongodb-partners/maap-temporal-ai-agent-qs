"""Account schemas for financial transactions."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum
import uuid

class AccountType(str, Enum):
    """Account types."""
    CHECKING = "checking"
    SAVINGS = "savings"
    BUSINESS = "business"
    INVESTMENT = "investment"

class AccountStatus(str, Enum):
    """Account status."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    FROZEN = "frozen"
    CLOSED = "closed"

class Account(BaseModel):
    """Account model for financial transactions."""
    account_number: str
    account_type: AccountType = AccountType.CHECKING
    customer_id: str
    customer_name: str
    balance: float = Field(ge=0, description="Current account balance")
    available_balance: float = Field(ge=0, description="Available balance (considering holds)")
    currency: str = "USD"
    status: AccountStatus = AccountStatus.ACTIVE
    
    # Limits
    daily_withdrawal_limit: float = 10000.0
    daily_transfer_limit: float = 50000.0
    overdraft_limit: float = 0.0  # Allow negative balance up to this amount
    
    # Statistics
    total_deposits: float = 0.0
    total_withdrawals: float = 0.0
    transaction_count: int = 0
    last_transaction_at: Optional[datetime] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    kyc_verified: bool = False
    risk_score: float = 0.0
    
    # Holds
    holds: List[Dict[str, Any]] = Field(default_factory=list)  # List of transaction holds
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class BalanceHold(BaseModel):
    """Hold on account balance for pending transactions."""
    hold_id: str = Field(default_factory=lambda: f"HOLD_{uuid.uuid4().hex[:8].upper()}")
    account_number: str
    transaction_id: str
    amount: float
    reason: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    released: bool = False
    released_at: Optional[datetime] = None

class BalanceUpdate(BaseModel):
    """Record of balance update."""
    update_id: str = Field(default_factory=lambda: f"UPD_{uuid.uuid4().hex[:8].upper()}")
    account_number: str
    transaction_id: str
    operation: str  # "debit" or "credit"
    amount: float
    previous_balance: float
    new_balance: float
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    session_id: Optional[str] = None  # MongoDB session ID for ACID transactions
    
class TransactionJournal(BaseModel):
    """Double-entry bookkeeping journal entry."""
    journal_id: str = Field(default_factory=lambda: f"JRN_{uuid.uuid4().hex[:8].upper()}")
    transaction_id: str
    
    # Debit entry
    debit_account: str
    debit_amount: float
    
    # Credit entry
    credit_account: str
    credit_amount: float
    
    description: str
    status: str = "pending"  # pending, completed, failed, reversed
    
    # ACID transaction tracking
    session_id: Optional[str] = None
    committed: bool = False
    
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }