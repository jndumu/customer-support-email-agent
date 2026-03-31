"""Send node — STEP 6 / FINAL STEP of the happy path.

Triggered by:
  review_node returning passed=True AND needs_human_review=False.

Responsibility:
  Finalise the approved draft as the official customer response,
  trigger email delivery, and schedule follow-ups when flagged.

What it does:
  1. Promotes draft_response → final_response.
  2. Calls email_service.send_reply() to deliver the reply via SMTP.
     (No-ops silently if SMTP_HOST is not configured — the reply is still
     returned in the API response body for manual sending.)
  3. If followup_required=True (set by classify_node), calls
     followup_service.schedule() to create a FollowUpRecord with a
     future date and the classifier's note about what to follow up on.
     The scheduled date defaults to FOLLOWUP_DEFAULT_DAYS from now.

After this node the graph reaches END and the final state is returned
to the API layer, which serialises it into an EmailResponse.

Input state fields used:  draft_response, sender, subject, email_id,
                          followup_required, followup_note
Output state fields set:  final_response, followup_scheduled_at, error
"""

from src.core.config import settings
from src.core.logging import logger
from src.graph.state import AgentState
from src.services import followup_service
from src.services.email_service import send_reply


def send_node(state: AgentState) -> AgentState:
    """Deliver the approved reply and schedule any required follow-up."""
    logger.info("node.send.start", email_id=state["email_id"])

    try:
        final = state["draft_response"]

        # ── Step 1: Deliver reply ─────────────────────────────────────────
        # send_reply() is a no-op if SMTP_HOST is not configured.
        # The final_response is always returned in the API response regardless.
        send_reply(
            to=state["sender"],
            subject=f"Re: {state['subject']}",
            body=final,
            reply_to_id=state["email_id"],
        )

        # ── Step 2: Schedule follow-up if flagged ─────────────────────────
        # classify_node sets followup_required=True when the email topic
        # warrants a future check-in (e.g. refund in progress, order in transit,
        # investigation promised). The followup_note explains what to follow up on.
        followup_scheduled_at = None
        followup_note = state.get("followup_note")

        if state.get("followup_required") and followup_note:
            record = followup_service.schedule(
                email_id=state["email_id"],
                sender=state["sender"],
                subject=state["subject"],
                note=followup_note,
                days_from_now=settings.FOLLOWUP_DEFAULT_DAYS,
            )
            followup_scheduled_at = record.scheduled_at

        logger.info(
            "node.send.complete",
            email_id=state["email_id"],
            followup_scheduled=bool(followup_scheduled_at),
        )

        return {
            **state,
            "final_response": final,
            "followup_scheduled_at": followup_scheduled_at,
            "error": None,
        }

    except Exception as exc:
        logger.error("node.send.error", email_id=state["email_id"], error=str(exc))
        # Still return the draft as final_response so the API can serve it
        return {
            **state,
            "final_response": state.get("draft_response", ""),
            "error": f"send_node failed: {exc}",
        }
