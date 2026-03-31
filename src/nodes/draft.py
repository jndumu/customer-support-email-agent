"""Draft node — STEP 4 of the pipeline (skipped if escalated).

Responsibility:
  Generate a professional, empathetic, policy-grounded email reply
  using the retrieved knowledge base excerpts and classification context.

What it does:
  - Injects retrieved_docs, intent, priority, and sentiment into draft_prompt.
  - The prompt instructs the LLM to:
      * Adjust tone based on sentiment (e.g. open with apology if frustrated)
      * Ground all factual claims in the provided knowledge base excerpts
      * Never invent policies, prices, or timelines
      * Keep the reply under 250 words and sign off as Support Team
  - Uses get_llm() (temperature=0.2) for natural but consistent language.

The resulting draft is NOT sent to the customer yet — it goes to review_node
for a quality check before being approved or escalated.

Input state fields used:  sender, subject, body, intent, priority,
                          sentiment, retrieved_docs, email_id
Output state fields set:  draft_response, error
"""

from src.core.config import settings
from src.core.logging import logger
from src.graph.state import AgentState
from src.services.llm import get_llm
from src.utils.prompts import draft_prompt
from src.utils.text import truncate_text


def draft_node(state: AgentState) -> AgentState:
    """Generate a grounded, tone-appropriate draft reply via the LLM."""
    logger.info("node.draft.start", email_id=state["email_id"])

    try:
        llm = get_llm()
        chain = draft_prompt | llm

        # Format retrieved docs for the system prompt
        # If retrieval found nothing, tell the LLM to use general best practices
        docs = state.get("retrieved_docs", [])
        if docs:
            docs_text = "\n\n---\n\n".join(docs)
        else:
            docs_text = "No specific documentation found. Use general customer support best practices."

        response = chain.invoke({
            "company_name": settings.COMPANY_NAME,
            "support_email": settings.SUPPORT_EMAIL,
            # Truncate docs to stay within the LLM's context budget
            "retrieved_docs": truncate_text(docs_text, max_chars=3000),
            "intent": state.get("intent", "general_inquiry"),
            "priority": state.get("priority", "medium"),
            "sentiment": state.get("sentiment", "neutral"),
            "sender": state["sender"],
            "subject": state["subject"],
            "body": truncate_text(state["body"], max_chars=1500),
        })

        draft = response.content.strip()

        logger.info(
            "node.draft.complete",
            email_id=state["email_id"],
            draft_len=len(draft),
        )

        return {**state, "draft_response": draft, "error": None}

    except Exception as exc:
        logger.error("node.draft.error", email_id=state["email_id"], error=str(exc))
        # Empty draft triggers human review in review_node
        return {**state, "draft_response": "", "error": f"draft_node failed: {exc}"}
