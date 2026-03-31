"""Review node — STEP 5 of the pipeline (skipped if escalated).

Responsibility:
  Act as an automated QA gate. Evaluate the draft response against a
  checklist before it is sent to the customer, and flag cases that
  require a human agent to review or approve.

What it does:
  - Sends the draft + original email + classification context to the LLM
    with review_prompt, which evaluates:
      1. Accuracy — facts match knowledge base, no hallucinated policies
      2. Completeness — fully addresses the customer's question
      3. Tone — matches the customer's sentiment appropriately
      4. Policy compliance — no unsupported promises or commitments
      5. Clarity — jargon-free and appropriately concise
  - Returns a ReviewResult with: passed (bool), needs_human_review (bool),
    feedback (str), confidence (float).
  - Uses get_llm_precise() (temperature=0.0) for consistent judgements.

Routing impact:
  - passed=True AND needs_human_review=False → send_node (approved)
  - needs_human_review=True OR passed=False  → escalate_node (held for human)

Fail-safe:
  Any exception in this node defaults to needs_human_review=True so that
  a broken review never accidentally allows an unsafe draft through.

Input state fields used:  sender, subject, body, draft_response,
                          intent, priority, sentiment, confidence, email_id
Output state fields set:  review_passed, needs_human_review,
                          review_feedback, error
"""

from src.core.config import settings
from src.core.logging import logger
from src.graph.state import AgentState
from src.schemas.agent import ReviewResult
from src.services.llm import get_llm_precise
from src.utils.prompts import review_prompt
from src.utils.text import truncate_text


def review_node(state: AgentState) -> AgentState:
    """Quality-check the draft and decide whether it is safe to send."""
    logger.info("node.review.start", email_id=state["email_id"])

    # Guard: an empty draft (draft_node failed) must be caught immediately
    if not state.get("draft_response"):
        logger.warning("node.review.empty_draft", email_id=state["email_id"])
        return {
            **state,
            "review_passed": False,
            "needs_human_review": True,
            "review_feedback": "Draft was empty — prior node may have failed.",
        }

    try:
        llm = get_llm_precise()
        structured_llm = llm.with_structured_output(ReviewResult)
        chain = review_prompt | structured_llm

        result: ReviewResult = chain.invoke({
            "company_name": settings.COMPANY_NAME,
            "sentiment": state.get("sentiment", "neutral"),
            "sender": state["sender"],
            "subject": state["subject"],
            "body": truncate_text(state["body"], max_chars=1000),
            "draft_response": truncate_text(state["draft_response"], max_chars=1500),
            "intent": state.get("intent", ""),
            "priority": state.get("priority", ""),
            # Low confidence from classify_node is a review escalation trigger
            "confidence": state.get("confidence", 0.0),
        })

        logger.info(
            "node.review.complete",
            email_id=state["email_id"],
            passed=result.passed,
            needs_human_review=result.needs_human_review,
            feedback=result.feedback[:120],
        )

        return {
            **state,
            "review_passed": result.passed,
            "needs_human_review": result.needs_human_review,
            "review_feedback": result.feedback,
            "error": None,
        }

    except Exception as exc:
        logger.error("node.review.error", email_id=state["email_id"], error=str(exc))
        # Fail closed: any review error escalates to human rather than auto-sending
        return {
            **state,
            "review_passed": False,
            "needs_human_review": True,
            "review_feedback": f"Review node error: {exc}",
            "error": f"review_node failed: {exc}",
        }
