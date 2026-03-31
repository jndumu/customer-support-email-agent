"""Agent classification and review Pydantic schemas."""

from pydantic import BaseModel, Field


class IntentClassification(BaseModel):
    intent: str = Field(
        ...,
        description=(
            "One of: billing, tech_support, account, refund, complaint, "
            "feedback, general_inquiry, urgent"
        ),
    )
    priority: str = Field(
        ...,
        description="One of: low, medium, high, urgent",
    )
    sentiment: str = Field(
        ...,
        description="One of: positive, neutral, negative, frustrated",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Classification confidence between 0.0 and 1.0",
    )
    escalate: bool = Field(
        ...,
        description=(
            "True if the email should be immediately routed to a human "
            "agent before drafting a response"
        ),
    )
    escalation_reason: str = Field(
        default="",
        description="Reason for escalation if escalate is True",
    )
    followup_required: bool = Field(
        default=False,
        description="True if a follow-up should be scheduled after reply",
    )
    followup_note: str = Field(
        default="",
        description="Brief note describing what the follow-up should cover",
    )


class ReviewResult(BaseModel):
    passed: bool = Field(
        ...,
        description="True if the draft meets quality and policy standards",
    )
    needs_human_review: bool = Field(
        ...,
        description="True if a human agent must review before sending",
    )
    feedback: str = Field(
        ...,
        description="Specific feedback on the draft quality",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Reviewer confidence in the assessment",
    )
