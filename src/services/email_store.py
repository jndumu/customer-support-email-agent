"""In-memory inbox store for all processed emails.

Stores InboxEmailRecord (full pipeline data) and a pre-built EmailResponse
(lightweight API response) per email_id. Capping at MAX_INBOX_SIZE with
oldest-first eviction to prevent unbounded memory growth.

Production upgrade: replace dicts with a database (SQLAlchemy / Tortoise).
"""

from __future__ import annotations

from collections import OrderedDict
from typing import Optional

from src.schemas.email import EmailResponse, InboxEmailRecord

MAX_INBOX_SIZE = 1_000

# OrderedDict preserves insertion order — evict from the front (oldest).
_inbox: OrderedDict[str, InboxEmailRecord] = OrderedDict()
_responses: dict[str, EmailResponse] = {}


def save(record: InboxEmailRecord, response: EmailResponse) -> None:
    """Persist a completed email record and its pre-built API response."""
    if len(_inbox) >= MAX_INBOX_SIZE:
        oldest_id, _ = _inbox.popitem(last=False)
        _responses.pop(oldest_id, None)
    _inbox[record.email_id] = record
    _responses[record.email_id] = response


def get(email_id: str) -> Optional[InboxEmailRecord]:
    return _inbox.get(email_id)


def get_response(email_id: str) -> Optional[EmailResponse]:
    """Return the pre-built EmailResponse — avoids re-mapping on every GET."""
    return _responses.get(email_id)


def list_all() -> list[InboxEmailRecord]:
    """Return all records newest-first."""
    return list(reversed(_inbox.values()))


def get_stats() -> dict:
    """Compute inbox summary stats in a single pass."""
    total = escalated = followups = total_ms = 0
    for r in _inbox.values():
        total += 1
        if r.escalated:
            escalated += 1
        if r.followup_scheduled:
            followups += 1
        total_ms += r.processing_time_ms
    return {
        "total": total,
        "processed": total - escalated,
        "escalated": escalated,
        "pending_followups": followups,
        "avg_processing_ms": round(total_ms / total, 1) if total else 0.0,
    }
