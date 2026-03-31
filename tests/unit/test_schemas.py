"""Unit tests for Pydantic schemas."""

import pytest
from pydantic import ValidationError

from src.schemas.email import EmailRequest, EmailResponse, FollowUpRecord
from src.schemas.agent import IntentClassification, ReviewResult


class TestEmailRequest:
    def test_valid_request(self):
        req = EmailRequest(
            sender="alice@example.com",
            subject="Help needed",
            body="I need help with my account.",
        )
        assert req.sender == "alice@example.com"
        assert req.email_id is None

    def test_email_id_provided(self):
        req = EmailRequest(
            sender="alice@example.com",
            subject="Test",
            body="Body",
            email_id="abc-123",
        )
        assert req.email_id == "abc-123"

    def test_missing_required_fields(self):
        with pytest.raises(ValidationError):
            EmailRequest(sender="alice@example.com")  # missing subject and body


class TestIntentClassification:
    def test_valid_classification(self):
        obj = IntentClassification(
            intent="billing",
            priority="medium",
            sentiment="neutral",
            confidence=0.92,
            escalate=False,
            escalation_reason="",
            followup_required=False,
            followup_note="",
        )
        assert obj.intent == "billing"
        assert obj.confidence == 0.92

    def test_confidence_out_of_range(self):
        with pytest.raises(ValidationError):
            IntentClassification(
                intent="billing",
                priority="medium",
                sentiment="neutral",
                confidence=1.5,  # > 1.0
                escalate=False,
                escalation_reason="",
                followup_required=False,
                followup_note="",
            )

    def test_negative_confidence_rejected(self):
        with pytest.raises(ValidationError):
            IntentClassification(
                intent="billing",
                priority="medium",
                sentiment="neutral",
                confidence=-0.1,
                escalate=False,
                escalation_reason="",
                followup_required=False,
                followup_note="",
            )


class TestReviewResult:
    def test_valid_review(self):
        obj = ReviewResult(
            passed=True,
            needs_human_review=False,
            feedback="Response is accurate and complete.",
            confidence=0.88,
        )
        assert obj.passed is True
        assert obj.needs_human_review is False

    def test_failed_review(self):
        obj = ReviewResult(
            passed=False,
            needs_human_review=True,
            feedback="Draft contains unverified claim about refund timeline.",
            confidence=0.55,
        )
        assert obj.passed is False
        assert obj.needs_human_review is True


class TestFollowUpRecord:
    def test_defaults_to_not_completed(self):
        record = FollowUpRecord(
            email_id="abc-123",
            sender="alice@example.com",
            subject="Order follow-up",
            scheduled_at="2026-04-05T09:00:00+00:00",
            note="Check if refund was received",
        )
        assert record.completed is False
