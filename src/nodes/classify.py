"""Classify node — STEP 2 of the pipeline.

Responsibility:
  Use the LLM to understand the email's intent, severity, and emotional
  tone, then decide whether to escalate immediately or proceed to retrieval.

What it does:
  - Calls the LLM with classify_prompt and requests structured output
    matching the IntentClassification Pydantic schema.
  - The LLM returns: intent, priority, sentiment, confidence,
    escalate (bool), escalation_reason, followup_required, followup_note.
  - Uses get_llm_precise() (temperature=0.0) for deterministic output.

Routing impact:
  - escalate=True  → route_after_classify() sends the graph to escalate_node
                     (skipping retrieve/draft/review entirely)
  - escalate=False → graph continues to retrieve_node

Fail-safe:
  On any LLM error, the node returns a safe default classification
  (general_inquiry / medium / neutral) so the pipeline can still attempt
  to produce a helpful response rather than crashing.

Input state fields used:  sender, subject, body, email_id
Output state fields set:  intent, priority, sentiment, confidence,
                          escalate, escalation_reason,
                          followup_required, followup_note, error
"""

from src.core.config import settings
from src.core.logging import logger
from src.graph.state import AgentState
from src.schemas.agent import IntentClassification
from src.services.llm import get_llm_precise
from src.utils.prompts import classify_prompt
from src.utils.text import truncate_text


def classify_node(state: AgentState) -> AgentState:
    """Classify email intent, priority, and sentiment via structured LLM output."""
    logger.info("node.classify.start", email_id=state["email_id"])

    try:
        llm = get_llm_precise()
        # with_structured_output forces the LLM to return JSON matching
        # the IntentClassification schema — Pydantic validates it automatically
        structured_llm = llm.with_structured_output(IntentClassification)
        chain = classify_prompt | structured_llm

        result: IntentClassification = chain.invoke({
            "company_name": settings.COMPANY_NAME,
            "sender": state["sender"],
            "subject": state["subject"],
            # Truncate to avoid exceeding context window
            "body": truncate_text(state["body"], max_chars=2000),
        })

        logger.info(
            "node.classify.complete",
            email_id=state["email_id"],
            intent=result.intent,
            priority=result.priority,
            sentiment=result.sentiment,
            confidence=result.confidence,
            escalate=result.escalate,
        )

        return {
            **state,
            "intent": result.intent,
            "priority": result.priority,
            "sentiment": result.sentiment,
            "confidence": result.confidence,
            "escalate": result.escalate,
            "escalation_reason": result.escalation_reason,
            "followup_required": result.followup_required,
            "followup_note": result.followup_note if result.followup_note else None,
            "error": None,
        }

    except Exception as exc:
        logger.error("node.classify.error", email_id=state["email_id"], error=str(exc))
        # Fail-safe defaults — pipeline continues with a generic classification
        return {
            **state,
            "intent": "general_inquiry",
            "priority": "medium",
            "sentiment": "neutral",
            "confidence": 0.0,
            "escalate": False,
            "escalation_reason": "",
            "error": f"classify_node failed: {exc}",
        }
