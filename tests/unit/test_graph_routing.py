"""Unit tests for LangGraph conditional routing logic."""

import pytest
from src.graph.agent_graph import route_after_classify, route_after_review
from src.graph.state import AgentState


def _state(**kwargs) -> AgentState:
    base: AgentState = {
        "email_id": "test",
        "raw_email": "",
        "sender": "",
        "subject": "",
        "body": "",
        "intent": "general_inquiry",
        "priority": "medium",
        "confidence": 0.9,
        "sentiment": "neutral",
        "escalation": False,
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
    base.update(kwargs)
    return base


class TestRouteAfterClassify:
    def test_routes_to_retrieve_normally(self):
        assert route_after_classify(_state(escalate=False)) == "retrieve"

    def test_routes_to_escalate_when_flagged(self):
        assert route_after_classify(_state(escalate=True)) == "escalation"


class TestRouteAfterReview:
    def test_routes_to_send_when_passed(self):
        result = route_after_review(_state(review_passed=True, needs_human_review=False))
        assert result == "send"

    def test_routes_to_escalate_when_human_review_needed(self):
        result = route_after_review(_state(review_passed=True, needs_human_review=True))
        assert result == "escalation"

    def test_routes_to_escalate_when_review_failed(self):
        result = route_after_review(_state(review_passed=False, needs_human_review=False))
        assert result == "escalation"

    def test_routes_to_escalate_when_both_failed(self):
        result = route_after_review(_state(review_passed=False, needs_human_review=True))
        assert result == "escalation"
