"""Ingest node — STEP 1 of the pipeline.

Responsibility:
  Receive the raw email fields from the API layer and produce a clean,
  normalised body text that downstream nodes can work with reliably.

What it does:
  - Calls clean_email_body() to strip quoted reply blocks (lines starting
    with ">"), common signature delimiters ("--", "Sent from my iPhone", etc.),
    and excessive blank lines.
  - Preserves all other state fields unchanged.

Why it matters:
  Without cleaning, the LLM in classify_node and draft_node would waste
  context window tokens on irrelevant quoted history and boilerplate
  signatures, reducing accuracy and increasing cost.

Input state fields used:  body, email_id
Output state fields set:  body (cleaned), error
"""

from src.core.logging import logger
from src.graph.state import AgentState
from src.utils.text import clean_email_body


def ingest_node(state: AgentState) -> AgentState:
    """Clean and normalise the email body before classification."""
    logger.info("node.ingest.start", email_id=state["email_id"])

    try:
        cleaned_body = clean_email_body(state["body"])

        logger.info(
            "node.ingest.complete",
            email_id=state["email_id"],
            sender=state["sender"],
            subject=state["subject"][:60],
            body_len=len(cleaned_body),
        )

        return {
            **state,
            "body": cleaned_body,
            "error": None,
        }

    except Exception as exc:
        # Non-fatal: return original body so the pipeline can continue
        logger.error("node.ingest.error", email_id=state["email_id"], error=str(exc))
        return {**state, "error": f"ingest_node failed: {exc}"}
