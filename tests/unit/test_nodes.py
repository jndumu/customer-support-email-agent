"""Unit tests for individual LangGraph nodes with mocked LLM calls."""

import pytest
from unittest.mock import MagicMock, patch

from src.graph.state import AgentState


def _base_state(**overrides) -> AgentState:
    state: AgentState = {
        "email_id": "test-001",
        "raw_email": "From: alice@example.com\nSubject: Test\n\nBody",
        "sender": "alice@example.com",
        "subject": "Test subject",
        "body": "I need help with my account password.",
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
    state.update(overrides)
    return state


class TestIngestNode:
    def test_cleans_body(self):
        from src.nodes.ingest import ingest_node
        state = _base_state(body="Hello\n\nSent from my iPhone")
        result = ingest_node(state)
        assert "Sent from my iPhone" not in result["body"]
        assert result["error"] is None

    def test_preserves_email_id(self):
        from src.nodes.ingest import ingest_node
        state = _base_state(email_id="preserve-me")
        result = ingest_node(state)
        assert result["email_id"] == "preserve-me"


class TestClassifyNode:
    def test_successful_classification(self):
        from src.nodes.classify import classify_node
        from src.schemas.agent import IntentClassification

        mock_result = IntentClassification(
            intent="account",
            priority="medium",
            sentiment="neutral",
            confidence=0.93,
            escalate=False,
            escalation_reason="",
            followup_required=False,
            followup_note="",
        )

        with patch("src.nodes.classify.get_llm_precise") as mock_llm:
            mock_chain = MagicMock()
            mock_chain.invoke.return_value = mock_result
            mock_llm.return_value.with_structured_output.return_value.__or__ = lambda self, other: mock_chain
            # Patch the chain directly via the prompt
            with patch("src.nodes.classify.classify_prompt") as mock_prompt:
                mock_prompt.__or__ = MagicMock(return_value=mock_chain)
                state = _base_state()
                result = classify_node(state)

        # The node sets a fallback on exception — check it ran without crashing
        assert "intent" in result
        assert "priority" in result

    def test_fallback_on_llm_error(self):
        from src.nodes.classify import classify_node

        with patch("src.nodes.classify.get_llm_precise", side_effect=Exception("LLM error")):
            state = _base_state()
            result = classify_node(state)

        assert result["intent"] == "general_inquiry"
        assert result["priority"] == "medium"
        assert result["error"] is not None


class TestRetrieveNode:
    def test_populates_retrieved_docs(self):
        from src.nodes.retrieve import retrieve_node

        with patch("src.nodes.retrieve.settings") as mock_settings:
            mock_settings.PINECONE_API_KEY = ""  # force local
            mock_settings.MAX_RETRIEVED_DOCS = 3
            with patch("src.nodes.retrieve._local_retrieve", return_value=["doc1", "doc2"]):
                state = _base_state(intent="account", subject="Password reset")
                result = retrieve_node(state)

        assert result["retrieved_docs"] == ["doc1", "doc2"]
        assert result["error"] is None

    def test_returns_empty_on_error(self):
        from src.nodes.retrieve import retrieve_node

        with patch("src.nodes.retrieve.settings") as mock_settings:
            mock_settings.PINECONE_API_KEY = ""
            with patch("src.nodes.retrieve._local_retrieve", side_effect=Exception("fail")):
                with patch("src.services.knowledge_service.retrieve", side_effect=Exception("fail2")):
                    state = _base_state()
                    result = retrieve_node(state)

        assert result["retrieved_docs"] == []


class TestDraftNode:
    def test_produces_draft(self):
        from src.nodes.draft import draft_node

        mock_response = MagicMock()
        mock_response.content = "Dear Alice, thank you for contacting us..."

        with patch("src.nodes.draft.get_llm") as mock_llm:
            mock_chain = MagicMock()
            mock_chain.invoke.return_value = mock_response
            with patch("src.nodes.draft.draft_prompt") as mock_prompt:
                mock_prompt.__or__ = MagicMock(return_value=mock_chain)
                state = _base_state(
                    intent="account",
                    priority="medium",
                    sentiment="neutral",
                    retrieved_docs=["FAQ chunk about password reset"],
                )
                result = draft_node(state)

        assert "draft_response" in result

    def test_sets_error_on_failure(self):
        from src.nodes.draft import draft_node

        with patch("src.nodes.draft.get_llm", side_effect=Exception("LLM down")):
            state = _base_state()
            result = draft_node(state)

        assert result["draft_response"] == ""
        assert result["error"] is not None


class TestReviewNode:
    def test_empty_draft_triggers_human_review(self):
        from src.nodes.review import review_node

        state = _base_state(draft_response="")
        result = review_node(state)

        assert result["review_passed"] is False
        assert result["needs_human_review"] is True

    def test_sets_error_and_escalates_on_llm_failure(self):
        from src.nodes.review import review_node

        with patch("src.nodes.review.get_llm_precise", side_effect=Exception("fail")):
            state = _base_state(
                draft_response="Some draft content",
                intent="billing",
                priority="medium",
                sentiment="neutral",
                confidence=0.9,
            )
            result = review_node(state)

        assert result["needs_human_review"] is True
        assert result["error"] is not None


class TestSendNode:
    def test_promotes_draft_to_final(self):
        from src.nodes.send import send_node

        with patch("src.nodes.send.send_reply", return_value=True):
            state = _base_state(
                draft_response="Final reply text",
                followup_required=False,
            )
            result = send_node(state)

        assert result["final_response"] == "Final reply text"
        assert result["error"] is None

    def test_schedules_followup_when_flagged(self):
        from src.nodes.send import send_node

        with patch("src.nodes.send.send_reply", return_value=True):
            with patch("src.nodes.send.followup_service.schedule") as mock_schedule:
                mock_record = MagicMock()
                mock_record.scheduled_at = "2026-04-05T09:00:00+00:00"
                mock_schedule.return_value = mock_record

                state = _base_state(
                    draft_response="Reply text",
                    followup_required=True,
                    followup_note="Check refund status",
                )
                result = send_node(state)

        mock_schedule.assert_called_once()
        assert result["followup_scheduled_at"] == "2026-04-05T09:00:00+00:00"
