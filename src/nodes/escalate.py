"""Escalate node — TERMINAL branch for complex or sensitive cases.

Triggered by:
  1. classify_node sets escalate=True (legal language, safety, urgency, data breach)
  2. review_node sets needs_human_review=True (draft failed QA or is unsafe)
  3. review_node sets review_passed=False (any other QA failure)

What it does:
  - Generates a warm, professional "holding message" for the customer using
    escalate_prompt. The message:
      * Acknowledges the email and thanks the customer
      * Assures them a specialist will follow up within 1 business day
      * Does NOT disclose internal reasons for escalation
      * Includes the support email for urgent follow-up
  - Calls send_escalation_alert() to email the human review team
    (HUMAN_REVIEW_EMAIL) with full ticket context so they can action it.

Fail-safe:
  On LLM failure, a static fallback holding message is used so the
  customer always receives an acknowledgement.

Input state fields used:  sender, subject, body, escalation_reason,
                          review_feedback, email_id
Output state fields set:  final_response, escalate=True, error
"""

from src.core.config import settings
from src.core.logging import logger
from src.graph.state import AgentState
from src.services.email_service import send_escalation_alert
from src.services.llm import get_llm
from src.utils.prompts import escalate_prompt
from src.utils.text import truncate_text


def escalate_node(state: AgentState) -> AgentState:
    """Generate a holding response for the customer and alert the human team."""
    logger.info(
        "node.escalate.start",
        email_id=state["email_id"],
        reason=state.get("escalation_reason") or state.get("review_feedback", "unknown"),
    )

    try:
        llm = get_llm()
        chain = escalate_prompt | llm

        # The LLM writes a polished holding message the customer will receive
        response = chain.invoke({
            "company_name": settings.COMPANY_NAME,
            "support_email": settings.SUPPORT_EMAIL,
            "sender": state["sender"],
            "subject": state["subject"],
            "body": truncate_text(state["body"], max_chars=1000),
        })

        holding_message = response.content.strip()

        # Notify the human team — they receive the full escalation reason
        escalation_reason = (
            state.get("escalation_reason")
            or state.get("review_feedback", "Requires human review")
        )
        send_escalation_alert(
            email_id=state["email_id"],
            sender=state["sender"],
            subject=state["subject"],
            reason=escalation_reason,
        )

        logger.info(
            "node.escalate.complete",
            email_id=state["email_id"],
            holding_len=len(holding_message),
        )

        return {
            **state,
            "final_response": holding_message,
            "escalate": True,   # ensure status is marked escalated in API response
            "error": None,
        }

    except Exception as exc:
        logger.error("node.escalate.error", email_id=state["email_id"], error=str(exc))
        # Static fallback — customer always gets an acknowledgement
        fallback = (
            f"Dear Customer,\n\n"
            f"Thank you for contacting {settings.COMPANY_NAME}. "
            f"Your request has been received and a member of our team will "
            f"be in touch within 1 business day.\n\n"
            f"For urgent matters please email {settings.SUPPORT_EMAIL}.\n\n"
            f"Kind regards,\n{settings.COMPANY_NAME} Support Team"
        )
        return {
            **state,
            "final_response": fallback,
            "escalate": True,
            "error": f"escalate_node failed: {exc}",
        }
