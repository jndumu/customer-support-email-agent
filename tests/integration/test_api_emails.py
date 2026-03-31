"""Integration tests for the /api/v1/emails endpoints.

These tests mock the agent graph to avoid real LLM calls.
To run against the real LLM (requires OPENAI_API_KEY), remove the mock.
"""

import pytest
from unittest.mock import AsyncMock, patch


PROCESSED_GRAPH_OUTPUT = {
    "email_id": "test-001",
    "raw_email": "",
    "sender": "alice@example.com",
    "subject": "Cannot log in",
    "body": "I need help resetting my password.",
    "intent": "account",
    "priority": "medium",
    "confidence": 0.92,
    "sentiment": "neutral",
    "escalate": False,
    "escalation_reason": "",
    "retrieved_docs": ["[faq.md — Password Reset]\nTo reset..."],
    "draft_response": "Dear Alice, to reset your password please click Forgot Password...",
    "review_passed": True,
    "review_feedback": "Response is accurate and complete.",
    "needs_human_review": False,
    "final_response": "Dear Alice, to reset your password please click Forgot Password...",
    "followup_required": False,
    "followup_scheduled_at": None,
    "followup_note": None,
    "error": None,
}

ESCALATED_GRAPH_OUTPUT = {
    **PROCESSED_GRAPH_OUTPUT,
    "intent": "urgent",
    "priority": "urgent",
    "escalate": True,
    "escalation_reason": "Legal language detected",
    "final_response": "Dear Customer, your case has been escalated...",
}


class TestProcessEmail:
    async def test_successful_processing(self, client, sample_email_payload):
        with patch(
            "src.api.v1.endpoints.emails.agent_graph.ainvoke",
            new_callable=AsyncMock,
            return_value=PROCESSED_GRAPH_OUTPUT,
        ):
            response = await client.post("/api/v1/emails/process", json=sample_email_payload)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processed"
        assert data["intent"] == "account"
        assert data["escalated"] is False
        assert "reply" in data
        assert data["processing_time_ms"] >= 0

    async def test_escalated_email(self, client, urgent_email_payload):
        with patch(
            "src.api.v1.endpoints.emails.agent_graph.ainvoke",
            new_callable=AsyncMock,
            return_value=ESCALATED_GRAPH_OUTPUT,
        ):
            response = await client.post("/api/v1/emails/process", json=urgent_email_payload)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "escalated"
        assert data["escalated"] is True

    async def test_missing_required_fields(self, client):
        response = await client.post("/api/v1/emails/process", json={"sender": "alice@example.com"})
        assert response.status_code == 422

    async def test_graph_error_returns_500(self, client, sample_email_payload):
        with patch(
            "src.api.v1.endpoints.emails.agent_graph.ainvoke",
            new_callable=AsyncMock,
            side_effect=Exception("Graph crashed"),
        ):
            response = await client.post("/api/v1/emails/process", json=sample_email_payload)

        assert response.status_code == 500

    async def test_idempotency_with_email_id(self, client, sample_email_payload):
        payload = {**sample_email_payload, "email_id": "fixed-id-999"}
        with patch(
            "src.api.v1.endpoints.emails.agent_graph.ainvoke",
            new_callable=AsyncMock,
            return_value={**PROCESSED_GRAPH_OUTPUT, "email_id": "fixed-id-999"},
        ):
            response = await client.post("/api/v1/emails/process", json=payload)

        assert response.status_code == 200
        assert response.json()["email_id"] == "fixed-id-999"


class TestGetEmailResult:
    async def test_get_existing_result(self, client, sample_email_payload):
        with patch(
            "src.api.v1.endpoints.emails.agent_graph.ainvoke",
            new_callable=AsyncMock,
            return_value=PROCESSED_GRAPH_OUTPUT,
        ):
            post_response = await client.post("/api/v1/emails/process", json=sample_email_payload)

        email_id = post_response.json()["email_id"]
        get_response = await client.get(f"/api/v1/emails/{email_id}")
        assert get_response.status_code == 200
        assert get_response.json()["email_id"] == email_id

    async def test_get_nonexistent_returns_404(self, client):
        response = await client.get("/api/v1/emails/does-not-exist")
        assert response.status_code == 404

    async def test_list_emails(self, client, sample_email_payload):
        with patch(
            "src.api.v1.endpoints.emails.agent_graph.ainvoke",
            new_callable=AsyncMock,
            return_value=PROCESSED_GRAPH_OUTPUT,
        ):
            await client.post("/api/v1/emails/process", json=sample_email_payload)

        response = await client.get("/api/v1/emails")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestHealthEndpoint:
    async def test_health_returns_ok(self, client):
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
