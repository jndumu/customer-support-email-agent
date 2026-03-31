"""Email processing API endpoints.

Routes:
  POST /api/v1/emails/process             → run full agent pipeline
  GET  /api/v1/emails/inbox               → list all emails (inbox UI)
  GET  /api/v1/emails/inbox/stats         → dashboard stats
  GET  /api/v1/emails/{email_id}/details  → full record for detail view
  GET  /api/v1/emails/{email_id}          → lightweight response
  GET  /api/v1/emails                     → list email IDs and statuses
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, status

from src.core.logging import logger
from src.graph.agent_graph import agent_graph
from src.graph.state import AgentState
from src.schemas.email import (
    EmailRequest,
    EmailResponse,
    EmailStatusResponse,
    InboxEmailRecord,
)
from src.services import email_store
from src.utils.text import build_raw_email

router = APIRouter()


# ── Factory helpers ───────────────────────────────────────────────────────────

def _build_response(email_id: str, final_state: dict[str, Any], elapsed_ms: float) -> EmailResponse:
    """Map final agent state → lightweight EmailResponse."""
    return EmailResponse(
        email_id=email_id,
        status="escalated" if final_state.get("escalate") else "processed",
        intent=final_state.get("intent", ""),
        priority=final_state.get("priority", ""),
        sentiment=final_state.get("sentiment", ""),
        confidence=final_state.get("confidence", 0.0),
        reply=final_state.get("final_response", ""),
        escalated=bool(final_state.get("escalate")),
        escalation_reason=final_state.get("escalation_reason") or None,
        followup_scheduled=bool(final_state.get("followup_scheduled_at")),
        followup_date=final_state.get("followup_scheduled_at"),
        followup_note=final_state.get("followup_note"),
        processing_time_ms=elapsed_ms,
    )


def _build_inbox_record(
    email_id: str,
    received_at: str,
    request: EmailRequest,
    final_state: dict[str, Any],
    response: EmailResponse,
    elapsed_ms: float,
) -> InboxEmailRecord:
    """Map final agent state + pre-built response → InboxEmailRecord.

    Re-uses response fields rather than re-extracting from final_state
    to avoid duplicate .get() calls for the overlapping fields.
    """
    return InboxEmailRecord(
        email_id=email_id,
        received_at=received_at,
        sender=request.sender,
        subject=request.subject,
        body=final_state.get("body", request.body),
        status=response.status,
        intent=response.intent,
        priority=response.priority,
        sentiment=response.sentiment,
        confidence=response.confidence,
        escalated=response.escalated,
        escalation_reason=response.escalation_reason,
        retrieved_docs=final_state.get("retrieved_docs", []),
        draft_response=final_state.get("draft_response", ""),
        review_passed=bool(final_state.get("review_passed")),
        review_feedback=final_state.get("review_feedback", ""),
        needs_human_review=bool(final_state.get("needs_human_review")),
        final_response=final_state.get("final_response", ""),
        followup_scheduled=response.followup_scheduled,
        followup_date=response.followup_date,
        followup_note=response.followup_note,
        processing_time_ms=elapsed_ms,
    )


# ── Process email ─────────────────────────────────────────────────────────────

@router.post(
    "/process",
    response_model=EmailResponse,
    status_code=status.HTTP_200_OK,
    summary="Process a customer support email",
    description=(
        "Runs the full LangGraph pipeline: ingest → classify → retrieve → "
        "draft → review → (escalate | send). Returns the final reply and metadata."
    ),
)
async def process_email(request: EmailRequest) -> EmailResponse:
    email_id = request.email_id or str(uuid.uuid4())
    received_at = datetime.now(timezone.utc).isoformat()
    start_ts = time.monotonic()

    logger.info("api.process_email.start", email_id=email_id, sender=request.sender)

    initial_state: AgentState = {
        "email_id": email_id,
        "raw_email": build_raw_email(request.sender, request.subject, request.body),
        "sender": request.sender,
        "subject": request.subject,
        "body": request.body,
        "intent": "",
        "priority": "",
        "confidence": 0.0,
        "sentiment": "",
        "escalate": False,
        "escalation_reason": "",
        "retrieved_docs": [],
        "draft_response": "",
        "review_passed": False,
        "review_feedback": "",
        "needs_human_review": False,
        "final_response": "",
        "followup_required": False,
        "followup_scheduled_at": None,
        "followup_note": None,
        "error": None,
    }

    try:
        final_state: dict[str, Any] = await agent_graph.ainvoke(initial_state)
    except Exception as exc:
        logger.error("api.process_email.graph_error", email_id=email_id, error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent graph execution failed: {exc}",
        )

    elapsed_ms = round((time.monotonic() - start_ts) * 1000, 2)

    response = _build_response(email_id, final_state, elapsed_ms)
    record = _build_inbox_record(email_id, received_at, request, final_state, response, elapsed_ms)
    email_store.save(record, response)

    logger.info(
        "api.process_email.complete",
        email_id=email_id,
        status=response.status,
        intent=response.intent,
        elapsed_ms=elapsed_ms,
    )

    return response


# ── Inbox routes (defined BEFORE /{email_id} to avoid routing conflict) ───────

@router.get("/inbox/stats", summary="Get inbox dashboard statistics")
async def get_inbox_stats() -> dict:
    return email_store.get_stats()


@router.get(
    "/inbox",
    response_model=list[InboxEmailRecord],
    summary="List all processed emails (full records for inbox UI)",
)
async def list_inbox() -> list[InboxEmailRecord]:
    return email_store.list_all()


# ── Single email routes ───────────────────────────────────────────────────────

@router.get(
    "/{email_id}/details",
    response_model=InboxEmailRecord,
    summary="Get full pipeline details for a processed email",
)
async def get_email_details(email_id: str) -> InboxEmailRecord:
    record = email_store.get(email_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"No record found for email_id '{email_id}'")
    return record


@router.get(
    "/{email_id}",
    response_model=EmailResponse,
    summary="Get lightweight result for a processed email",
)
async def get_email_result(email_id: str) -> EmailResponse:
    response = email_store.get_response(email_id)
    if not response:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"No result found for email_id '{email_id}'")
    return response


@router.get("", response_model=list[EmailStatusResponse], summary="List all email IDs and statuses")
async def list_emails() -> list[EmailStatusResponse]:
    return [
        EmailStatusResponse(email_id=r.email_id, status=r.status, created_at=r.received_at)
        for r in email_store.list_all()
    ]
