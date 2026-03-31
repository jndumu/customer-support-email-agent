"""Email request / response Pydantic schemas."""

from typing import Literal, Optional
from pydantic import BaseModel, Field


class EmailRequest(BaseModel):
    sender: str = Field(..., description="Sender email address")
    subject: str = Field(..., description="Email subject line")
    body: str = Field(..., description="Full email body text")
    email_id: Optional[str] = Field(
        default=None,
        description="Optional idempotency ID; generated if omitted",
    )


class EmailResponse(BaseModel):
    email_id: str
    status: Literal["processed", "escalated", "error"]
    intent: str
    priority: str
    sentiment: str
    confidence: float
    reply: str
    escalated: bool
    escalation_reason: Optional[str]
    followup_scheduled: bool
    followup_date: Optional[str]
    followup_note: Optional[str]
    processing_time_ms: float


class EmailStatusResponse(BaseModel):
    email_id: str
    status: str
    created_at: str


class FollowUpRecord(BaseModel):
    email_id: str
    sender: str
    subject: str
    scheduled_at: str
    note: str
    completed: bool = False


class InboxEmailRecord(BaseModel):
    """Full email record: original email + all agent pipeline outputs."""

    email_id: str
    received_at: str

    sender: str
    subject: str
    body: str

    status: Literal["processed", "escalated", "error"]
    intent: str
    priority: str
    sentiment: str
    confidence: float

    escalated: bool
    escalation_reason: Optional[str]

    retrieved_docs: list[str]

    draft_response: str
    review_passed: bool
    review_feedback: str
    needs_human_review: bool

    final_response: str

    followup_scheduled: bool
    followup_date: Optional[str]
    followup_note: Optional[str]

    processing_time_ms: float
