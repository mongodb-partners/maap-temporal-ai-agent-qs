"""Pydantic models for API."""

from pydantic import BaseModel, Field, field_validator
from typing import Dict, Optional, List, Union
from datetime import datetime
from decimal import Decimal
from database.schemas import TransactionType, TransactionStatus, DecisionType

class TransactionRequest(BaseModel):
    transaction_type: TransactionType
    amount: Union[float, str] = Field(...)  # Accept float or string for decimal
    currency: str = Field(default="USD")
    sender: Dict[str, str] = Field(..., example={
        "name": "John Doe",
        "account": "ACC001",
        "customer_id": "CUST001",
        "country": "US"
    })
    recipient: Dict[str, str] = Field(..., example={
        "name": "Jane Smith",
        "account": "ACC002",
        "country": "GB"
    })
    reference_number: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[Dict] = Field(default={})

    @field_validator('amount')
    def validate_amount(cls, v):
        """Ensure amount can be converted to Decimal."""
        try:
            Decimal(str(v))
            return v
        except:
            raise ValueError('Amount must be a valid decimal number')

class TransactionResponse(BaseModel):
    transaction_id: str
    status: TransactionStatus
    message: str
    workflow_id: Optional[str] = None

class DecisionResponse(BaseModel):
    transaction_id: str
    decision: DecisionType
    confidence: Union[float, str]
    risk_score: Union[float, str]
    reasoning: str
    processing_time_ms: int
    risk_factors: List[str]

class MetricsResponse(BaseModel):
    total_transactions: int
    transactions_by_type: Dict[str, int]
    decisions_breakdown: Dict[str, int]
    average_processing_time_ms: float
    average_confidence: Union[float, str]
    total_amount_processed: Union[float, str]
