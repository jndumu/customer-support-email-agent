"""Follow-up scheduling service.

FLOW POSITION: Called by send_node (final step of the pipeline) when
the classifier sets followup_required=True in the agent state.

How it works:
  1. classify_node detects whether the email topic warrants a follow-up
     (e.g. order in transit, refund initiated, investigation promised)
     and sets state['followup_required'] = True along with a brief note.
  2. send_node calls followup_service.schedule() which creates a
     FollowUpRecord with a future ISO-8601 timestamp and stores it.
  3. The /api/v1/followups endpoints expose the store so operators can
     list pending follow-ups and mark them complete when actioned.

Production upgrade path:
  Replace _store (dict) with a database table or a Celery Beat task
  to send automated reminder emails on the scheduled date.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from src.core.config import settings
from src.core.logging import logger
from src.schemas.email import FollowUpRecord

# ── In-memory store ───────────────────────────────────────────────────────────
# Maps email_id → FollowUpRecord.
# In production: replace with a DB model (e.g. SQLAlchemy / Tortoise ORM).
_store: dict[str, FollowUpRecord] = {}


def schedule(
    email_id: str,
    sender: str,
    subject: str,
    note: str,
    days_from_now: Optional[int] = None,
) -> FollowUpRecord:
    """Create a follow-up record scheduled N days from now.

    Args:
        email_id:     Unique ID of the processed email thread.
        sender:       Customer email address for reference.
        subject:      Original email subject line.
        note:         What the follow-up should cover (written by the classifier).
        days_from_now: Override default follow-up window (FOLLOWUP_DEFAULT_DAYS).

    Returns:
        The persisted FollowUpRecord.
    """
    days = days_from_now or settings.FOLLOWUP_DEFAULT_DAYS
    scheduled_at = (
        datetime.now(timezone.utc) + timedelta(days=days)
    ).isoformat()

    record = FollowUpRecord(
        email_id=email_id,
        sender=sender,
        subject=subject,
        scheduled_at=scheduled_at,
        note=note,
        completed=False,
    )
    _store[email_id] = record
    logger.info(
        "followup.scheduled",
        email_id=email_id,
        scheduled_at=scheduled_at,
        note=note,
    )
    return record


def mark_complete(email_id: str) -> Optional[FollowUpRecord]:
    """Mark a follow-up as completed (e.g. human agent actioned it).

    Returns the updated record, or None if email_id was not found.
    """
    record = _store.get(email_id)
    if record:
        # Pydantic v2 model_copy creates an updated immutable copy
        _store[email_id] = record.model_copy(update={"completed": True})
        logger.info("followup.completed", email_id=email_id)
    return _store.get(email_id)


def get(email_id: str) -> Optional[FollowUpRecord]:
    """Fetch a single follow-up record by email ID."""
    return _store.get(email_id)


def list_pending() -> list[FollowUpRecord]:
    """Return all follow-ups that have not yet been completed."""
    return [r for r in _store.values() if not r.completed]


def list_all() -> list[FollowUpRecord]:
    """Return every follow-up record regardless of completion status."""
    return list(_store.values())
