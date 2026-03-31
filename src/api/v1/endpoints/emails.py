"""Email processing API endpoints."""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, status

from src.core.logging import logger
from src.graph.agent_graph import agent_graph
from src.graph.state import AgentState
from src.schemas.email import EmailRequest, EmailResponse, EmailStatusResponse, FollowUpRecord
from src.services import followup_service
from src.utils.text import build_raw_email

router = APIRouter()

# In-memory result store: email_id → EmailResponse
_results: dict[str, EmailResponse] = {}


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
    start_ts = time.monotonic()

    logger.info("api.process_email.start", email_id=email_id, sender=request.sender)

    # Build initial agent state
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

    elapsed_ms = (time.monotonic() - start_ts) * 1000

    response = EmailResponse(
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
        processing_time_ms=round(elapsed_ms, 2),
    )

    _results[email_id] = response

    logger.info(
        "api.process_email.complete",
        email_id=email_id,
        status=response.status,
        intent=response.intent,
        elapsed_ms=round(elapsed_ms, 2),
    )

    return response


@router.get(
    "/{email_id}",
    response_model=EmailResponse,
    summary="Get result for a processed email",
)
async def get_email_result(email_id: str) -> EmailResponse:
    result = _results.get(email_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No result found for email_id '{email_id}'",
        )
    return result


@router.get(
    "",
    response_model=list[EmailStatusResponse],
    summary="List all processed email IDs and statuses",
)
async def list_emails() -> list[EmailStatusResponse]:
    return [
        EmailStatusResponse(
            email_id=r.email_id,
            status=r.status,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        for r in _results.values()
    ]
