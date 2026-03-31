"""Follow-up management endpoints."""

from fastapi import APIRouter, HTTPException, status

from src.schemas.email import FollowUpRecord
from src.services import followup_service

router = APIRouter()


@router.get(
    "",
    response_model=list[FollowUpRecord],
    summary="List all scheduled follow-ups",
)
async def list_followups(pending_only: bool = False) -> list[FollowUpRecord]:
    if pending_only:
        return followup_service.list_pending()
    return followup_service.list_all()


@router.patch(
    "/{email_id}/complete",
    response_model=FollowUpRecord,
    summary="Mark a follow-up as completed",
)
async def complete_followup(email_id: str) -> FollowUpRecord:
    record = followup_service.mark_complete(email_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No follow-up found for email_id '{email_id}'",
        )
    return record
