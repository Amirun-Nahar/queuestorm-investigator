"""
Schema definitions for the QueueStorm Investigator.

All Enums and Pydantic models are defined here to ensure strict
compliance with the expected API contract.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class CaseType(str, Enum):
    """Classification of the complaint category."""
    wrong_transfer = "wrong_transfer"
    payment_failed = "payment_failed"
    phishing_or_social_engineering = "phishing_or_social_engineering"
    account_takeover = "account_takeover"
    unauthorized_transaction = "unauthorized_transaction"
    service_complaint = "service_complaint"
    other = "other"


class Department(str, Enum):
    """Target department for ticket routing."""
    customer_support = "customer_support"
    dispute_resolution = "dispute_resolution"
    fraud_risk = "fraud_risk"
    compliance = "compliance"
    technical_support = "technical_support"


class EvidenceVerdict(str, Enum):
    """Result of evidence cross-referencing."""
    consistent = "consistent"
    inconsistent = "inconsistent"
    insufficient_data = "insufficient_data"


class Priority(str, Enum):
    """Ticket urgency level."""
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


# ---------------------------------------------------------------------------
# Request Model
# ---------------------------------------------------------------------------

class TransactionRecord(BaseModel):
    """A single entry from the customer's transaction history."""
    transaction_id: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    timestamp: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None
    merchant: Optional[str] = None
    description: Optional[str] = None


class AnalyzeTicketRequest(BaseModel):
    """Incoming support ticket to be analyzed."""
    ticket_id: str = Field(..., description="Unique identifier for the support ticket")
    complaint: str = Field(..., description="The customer's complaint text")
    transaction_history: Optional[list[dict]] = Field(
        default=None,
        description="Optional list of transaction records for cross-referencing",
    )


# ---------------------------------------------------------------------------
# Response Model
# ---------------------------------------------------------------------------

class AnalyzeTicketResponse(BaseModel):
    """Structured analysis result returned by the investigator engine."""
    ticket_id: str = Field(..., description="Echo of the incoming ticket ID")
    case_type: CaseType = Field(..., description="Classified case type")
    department: Department = Field(..., description="Recommended routing department")
    priority: Priority = Field(..., description="Urgency level")
    relevant_transaction_id: Optional[str] = Field(
        default=None,
        description="Transaction ID most relevant to the complaint, or null",
    )
    evidence_verdict: EvidenceVerdict = Field(
        ...,
        description="Whether the transaction history supports the complaint",
    )
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Model confidence in the analysis (0.0 – 1.0)",
    )
    reasoning: str = Field(
        ...,
        description="Brief investigator reasoning for the verdict",
    )
    customer_reply: str = Field(
        ...,
        description="Professional reply to send back to the customer",
    )
    human_review_required: bool = Field(
        ...,
        description="Whether the ticket must be escalated for human review",
    )
