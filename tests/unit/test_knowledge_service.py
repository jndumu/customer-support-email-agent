"""Unit tests for the local BM25 knowledge retrieval service."""

import pytest
from src.services.knowledge_service import retrieve, _tokenise, _score_chunk


class TestTokenise:
    def test_basic_tokenisation(self):
        tokens = _tokenise("How do I reset my password?")
        assert "reset" in tokens
        assert "password" in tokens

    def test_filters_short_words(self):
        tokens = _tokenise("I am at my PC")
        # single-char words should be filtered (length < 2)
        assert "I" not in tokens
        assert "a" not in tokens

    def test_lowercases(self):
        tokens = _tokenise("BILLING Invoice PAYMENT")
        assert "billing" in tokens
        assert "invoice" in tokens


class TestScoreChunk:
    def test_relevant_chunk_scores_higher(self):
        query_tokens = _tokenise("reset password account login")
        relevant = _tokenise("To reset your password click Forgot Password on the login page")
        irrelevant = _tokenise("We accept Visa MasterCard and PayPal for all billing payments")
        doc_freq = {"reset": 2, "password": 3, "login": 2}

        score_rel = _score_chunk(query_tokens, relevant, doc_freq, total_docs=20)
        score_irrel = _score_chunk(query_tokens, irrelevant, doc_freq, total_docs=20)
        assert score_rel > score_irrel

    def test_zero_score_for_no_overlap(self):
        query_tokens = _tokenise("completely unrelated query xyz")
        chunk_tokens = _tokenise("billing invoice payment method credit card")
        doc_freq = {}
        score = _score_chunk(query_tokens, chunk_tokens, doc_freq, total_docs=10)
        assert score == 0.0


class TestRetrieve:
    def test_returns_list(self):
        results = retrieve("password reset account")
        assert isinstance(results, list)

    def test_returns_non_empty_for_common_query(self):
        results = retrieve("billing payment subscription")
        assert len(results) > 0

    def test_respects_top_k(self):
        results = retrieve("password login account", top_k=2)
        assert len(results) <= 2

    def test_result_strings_are_non_empty(self):
        results = retrieve("refund cancel subscription")
        for r in results:
            assert isinstance(r, str)
            assert len(r) > 10

    def test_empty_query_returns_empty(self):
        results = retrieve("")
        assert results == []
