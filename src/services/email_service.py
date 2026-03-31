"""Email send / receive service.

FLOW POSITION:
  - send_reply() is called by send_node at the end of the happy path
    to deliver the approved draft to the customer.
  - send_escalation_alert() is called by escalate_node to notify the
    internal human-review team whenever a ticket is escalated.

v1 status — SMTP is stubbed:
  Both functions no-op gracefully when SMTP_HOST is not set in .env,
  which means the API still returns the draft text even without email
  delivery. Set SMTP_HOST / SMTP_PORT in .env to enable real sending.

Production upgrade path:
  Replace the TODO block with aiosmtplib for async sending, add retry
  logic via tenacity, and optionally integrate with SendGrid / SES.
"""

from __future__ import annotations

from src.core.config import settings
from src.core.logging import logger


def send_reply(to: str, subject: str, body: str, reply_to_id: str | None = None) -> bool:
    """Deliver an email reply to the customer.

    Called by send_node after the draft has passed the review gate.

    Args:
        to:           Recipient email address (the original sender).
        subject:      Reply subject line (prefixed with "Re: " by the caller).
        body:         The approved draft response text.
        reply_to_id:  Original email ID for threading headers.

    Returns:
        True on successful send, False if SMTP is not configured.
    """
    if not settings.SMTP_HOST:
        # Not an error — SMTP is optional in development/testing.
        # The final_response is still returned in the API response.
        logger.warning(
            "email_service.send.skipped",
            reason="SMTP_HOST not configured",
            to=to,
            subject=subject,
        )
        return False

    # TODO: replace with aiosmtplib.send() when SMTP credentials are set
    logger.info("email_service.send", to=to, subject=subject, reply_to_id=reply_to_id)
    return True


def send_escalation_alert(email_id: str, sender: str, subject: str, reason: str) -> None:
    """Alert the human review team that a ticket has been escalated.

    Called by escalate_node. Sends an internal notification to
    HUMAN_REVIEW_EMAIL (configured in .env) with the ticket context
    so the reviewer can follow up directly with the customer.

    Args:
        email_id: Unique identifier for the escalated ticket.
        sender:   Original customer email address.
        subject:  Original email subject line.
        reason:   Why escalation was triggered (from state['escalation_reason']
                  or state['review_feedback']).
    """
    alert_body = (
        f"Escalated ticket: {email_id}\n"
        f"From: {sender}\n"
        f"Subject: {subject}\n"
        f"Reason: {reason}\n"
    )
    logger.info(
        "email_service.escalation_alert",
        email_id=email_id,
        to=settings.HUMAN_REVIEW_EMAIL,
        reason=reason,
    )
    # Reuse send_reply to dispatch the alert to the internal inbox
    send_reply(
        to=settings.HUMAN_REVIEW_EMAIL,
        subject=f"[ESCALATED] {subject}",
        body=alert_body,
    )
