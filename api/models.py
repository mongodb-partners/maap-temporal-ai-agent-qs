"""Pydantic models for API."""

from pydantic import BaseModel, Field
from typing import Dict, Optional, List
from datetime import datetime
from database.schemas import TransactionType, TransactionStatus, DecisionType

class TransactionRequest(BaseModel):
    transaction_type: TransactionType
    amount: float = Field(..., gt=0, le=10000000)
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

class TransactionResponse(BaseModel):
    transaction_id: str
    status: TransactionStatus
    message: str
    workflow_id: Optional[str] = None

class DecisionResponse(BaseModel):
    transaction_id: str
    decision: DecisionType
    confidence: float
    risk_score: float
    reasoning: str
    processing_time_ms: int
    risk_factors: List[str]

class MetricsResponse(BaseModel):
    total_transactions: int
    transactions_by_type: Dict[str, int]
    decisions_breakdown: Dict[str, int]
    average_processing_time_ms: float
    average_confidence: float
    total_amount_processed: float
