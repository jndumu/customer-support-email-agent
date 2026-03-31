"""LangGraph shared state definition."""

from typing import Optional
from typing_extensions import TypedDict


class AgentState(TypedDict):
    # ── Input ─────────────────────────────────────────────────────────────
    email_id: str
    raw_email: str          # original full email string
    sender: str
    subject: str
    body: str               # cleaned body text

    # ── Classification ────────────────────────────────────────────────────
    intent: str             # billing | tech_support | account | refund |
                            # complaint | feedback | general_inquiry | urgent
    priority: str           # low | medium | high | urgent
    confidence: float       # 0.0 – 1.0 classification confidence
    sentiment: str          # positive | neutral | negative | frustrated

    # ── Escalation ────────────────────────────────────────────────────────
    escalate: bool
    escalation_reason: str

    # ── Retrieval ─────────────────────────────────────────────────────────
    retrieved_docs: list[str]

    # ── Drafting ──────────────────────────────────────────────────────────
    draft_response: str

    # ── Review ────────────────────────────────────────────────────────────
    review_passed: bool
    review_feedback: str
    needs_human_review: bool

    # ── Output ────────────────────────────────────────────────────────────
    final_response: str

    # ── Follow-up scheduling ──────────────────────────────────────────────
    followup_required: bool
    followup_scheduled_at: Optional[str]   # ISO-8601 datetime string
    followup_note: Optional[str]

    # ── Meta ──────────────────────────────────────────────────────────────
    error: Optional[str]
