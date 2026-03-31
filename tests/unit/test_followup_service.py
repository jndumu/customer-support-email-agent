"""Unit tests for the follow-up scheduling service."""

import pytest
from src.services import followup_service


@pytest.fixture(autouse=True)
def clear_store():
    """Reset the in-memory store before each test."""
    followup_service._store.clear()
    yield
    followup_service._store.clear()


class TestSchedule:
    def test_creates_record(self):
        record = followup_service.schedule(
            email_id="email-001",
            sender="alice@example.com",
            subject="Order update",
            note="Check if refund was processed",
        )
        assert record.email_id == "email-001"
        assert record.completed is False
        assert record.note == "Check if refund was processed"

    def test_scheduled_at_is_future(self):
        from datetime import datetime, timezone
        record = followup_service.schedule(
            email_id="email-002",
            sender="bob@example.com",
            subject="Tech issue",
            note="Confirm fix applied",
        )
        scheduled = datetime.fromisoformat(record.scheduled_at)
        assert scheduled > datetime.now(timezone.utc)

    def test_custom_days(self):
        from datetime import datetime, timezone, timedelta
        record = followup_service.schedule(
            email_id="email-003",
            sender="carol@example.com",
            subject="Refund",
            note="Confirm refund received",
            days_from_now=7,
        )
        scheduled = datetime.fromisoformat(record.scheduled_at)
        expected = datetime.now(timezone.utc) + timedelta(days=7)
        diff = abs((scheduled - expected).total_seconds())
        assert diff < 5  # within 5 seconds


class TestMarkComplete:
    def test_marks_as_completed(self):
        followup_service.schedule(
            email_id="email-004",
            sender="dave@example.com",
            subject="Follow-up test",
            note="Test note",
        )
        record = followup_service.mark_complete("email-004")
        assert record is not None
        assert record.completed is True

    def test_returns_none_for_unknown_id(self):
        result = followup_service.mark_complete("nonexistent-id")
        assert result is None


class TestListPending:
    def test_filters_completed(self):
        followup_service.schedule("e1", "a@b.com", "Sub1", "Note1")
        followup_service.schedule("e2", "b@b.com", "Sub2", "Note2")
        followup_service.mark_complete("e1")

        pending = followup_service.list_pending()
        ids = [r.email_id for r in pending]
        assert "e1" not in ids
        assert "e2" in ids

    def test_all_returns_both(self):
        followup_service.schedule("e3", "c@b.com", "Sub3", "Note3")
        followup_service.schedule("e4", "d@b.com", "Sub4", "Note4")
        followup_service.mark_complete("e3")

        all_records = followup_service.list_all()
        assert len(all_records) == 2
