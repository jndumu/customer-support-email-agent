"""Integration tests for the /api/v1/followups endpoints."""

import pytest
from src.services import followup_service


@pytest.fixture(autouse=True)
def clear_store():
    followup_service._store.clear()
    yield
    followup_service._store.clear()


class TestFollowupsAPI:
    async def test_list_empty(self, client):
        response = await client.get("/api/v1/followups")
        assert response.status_code == 200
        assert response.json() == []

    async def test_list_after_schedule(self, client):
        followup_service.schedule(
            email_id="fu-001",
            sender="alice@example.com",
            subject="Test",
            note="Check in",
        )
        response = await client.get("/api/v1/followups")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["email_id"] == "fu-001"

    async def test_list_pending_only(self, client):
        followup_service.schedule("fu-002", "a@b.com", "Sub1", "Note1")
        followup_service.schedule("fu-003", "b@b.com", "Sub2", "Note2")
        followup_service.mark_complete("fu-002")

        response = await client.get("/api/v1/followups?pending_only=true")
        data = response.json()
        ids = [r["email_id"] for r in data]
        assert "fu-002" not in ids
        assert "fu-003" in ids

    async def test_complete_followup(self, client):
        followup_service.schedule("fu-004", "c@b.com", "Sub", "Note")
        response = await client.patch("/api/v1/followups/fu-004/complete")
        assert response.status_code == 200
        assert response.json()["completed"] is True

    async def test_complete_nonexistent_returns_404(self, client):
        response = await client.patch("/api/v1/followups/nonexistent/complete")
        assert response.status_code == 404
