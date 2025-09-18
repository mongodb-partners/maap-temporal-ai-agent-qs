"""Shared constants and data models for Temporal workflows."""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime

# Task Queue name
TRANSACTION_PROCESSING_TASK_QUEUE = "transaction-processing-queue"

@dataclass
class TransactionDetails:
    """Extended transaction details for processing."""
    transaction_id: str
    transaction_type: str  # Changed from TransactionType enum to str for serialization
    amount: float
    currency: str
    sender: Dict[str, Any]
    recipient: Dict[str, Any]
    reference_number: str
    risk_flags: List[str]
    metadata: Dict[str, Any]

@dataclass
class ProcessingResult:
    """Result of transaction processing."""
    success: bool
    decision: str  # Changed to str for better serialization
    confidence: float
    message: str
    decision_id: Optional[str] = None
    risk_score: Optional[float] = None
    processing_time_ms: Optional[int] = None
    workflow_id: Optional[str] = None

@dataclass
class RiskAssessment:
    """Risk assessment results."""
    risk_score: float
    risk_level: str
    risk_factors: List[str]
    requires_enhanced_diligence: bool
    compliance_checks: Dict[str, bool]

# Exceptions
class InsufficientDataError(Exception):
    """Raised when insufficient data for decision."""
    pass

class SystemError(Exception):
    """Raised for system-level errors."""
    pass