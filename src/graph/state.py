"""LangGraph shared state definition.

AgentState is a TypedDict that flows through every node in the pipeline.
Each node reads from and writes back to this single shared dict —
LangGraph merges the returned updates into the running state automatically.

PIPELINE FLOW:
  ingest_node   → Populates: body (cleaned)
  classify_node → Populates: intent, priority, sentiment, confidence,
                             escalate, escalation_reason,
                             followup_required, followup_note
  retrieve_node → Populates: retrieved_docs
  draft_node    → Populates: draft_response
  review_node   → Populates: review_passed, review_feedback, needs_human_review
  escalate_node → Populates: final_response (holding message), escalate=True
  send_node     → Populates: final_response, followup_scheduled_at

All nodes may also write to 'error' to signal a recoverable failure.
"""

from typing import Optional
from typing_extensions import TypedDict


class AgentState(TypedDict):
    # ── Input ─────────────────────────────────────────────────────────────
    # Set by the API layer before the graph is invoked.
    email_id: str       # UUID for the email thread (idempotency key)
    raw_email: str      # Original full email string (From + Subject + body)
    sender: str         # Sender address, e.g. "Jane <jane@example.com>"
    subject: str        # Email subject line
    body: str           # Email body — cleaned by ingest_node

    # ── Classification ────────────────────────────────────────────────────
    # Set by classify_node using structured LLM output (IntentClassification).
    intent: str         # billing | tech_support | account | refund |
                        # complaint | feedback | general_inquiry | urgent
    priority: str       # low | medium | high | urgent
    confidence: float   # 0.0–1.0 — how confident the classifier is
    sentiment: str      # positive | neutral | negative | frustrated

    # ── Escalation ────────────────────────────────────────────────────────
    # If escalate=True after classify_node, the graph skips retrieve/draft/review
    # and goes directly to escalate_node → END.
    escalate: bool
    escalation_reason: str  # Human-readable reason shown in the alert email

    # ── Retrieval ─────────────────────────────────────────────────────────
    # Set by retrieve_node. These strings are injected verbatim into the
    # draft_prompt as "Relevant knowledge base excerpts".
    retrieved_docs: list[str]

    # ── Drafting ──────────────────────────────────────────────────────────
    # Set by draft_node. Contains the LLM-generated reply before review.
    draft_response: str

    # ── Review ────────────────────────────────────────────────────────────
    # Set by review_node using structured LLM output (ReviewResult).
    # If needs_human_review=True OR review_passed=False → escalate_node.
    review_passed: bool
    review_feedback: str        # Actionable QA feedback from the reviewer
    needs_human_review: bool    # True = human must approve before sending

    # ── Output ────────────────────────────────────────────────────────────
    # The approved reply text — set by either send_node or escalate_node.
    # This is what gets returned to the caller in EmailResponse.reply.
    final_response: str

    # ── Follow-up scheduling ──────────────────────────────────────────────
    # Set by classify_node (flagged) and send_node (scheduled).
    # When followup_required=True, send_node calls followup_service.schedule().
    followup_required: bool
    followup_scheduled_at: Optional[str]    # ISO-8601 datetime string
    followup_note: Optional[str]            # What to follow up on

    # ── Meta ──────────────────────────────────────────────────────────────
    # Non-None indicates that a node encountered an exception.
    # The graph continues to the next node rather than crashing.
    error: Optional[str]
