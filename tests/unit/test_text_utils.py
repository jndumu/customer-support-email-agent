"""Unit tests for src/utils/text.py"""

import pytest
from src.utils.text import clean_email_body, extract_sender_name, truncate_text, build_raw_email


class TestCleanEmailBody:
    def test_strips_quoted_reply_lines(self):
        raw = "Hello\n\n> On Mon, Jan 1 wrote:\n> Previous reply here\n\nActual message"
        result = clean_email_body(raw)
        assert "> On Mon" not in result
        assert "Actual message" in result

    def test_strips_sent_from_signature(self):
        raw = "My question is here.\n\nSent from my iPhone"
        result = clean_email_body(raw)
        assert "Sent from my iPhone" not in result
        assert "My question is here" in result

    def test_strips_double_dash_signature(self):
        raw = "Hi there, I need help.\n\n--\nJohn Smith\njohn@example.com"
        result = clean_email_body(raw)
        assert "John Smith" not in result
        assert "I need help" in result

    def test_collapses_blank_lines(self):
        raw = "Line one\n\n\n\n\nLine two"
        result = clean_email_body(raw)
        assert "\n\n\n" not in result

    def test_empty_string(self):
        assert clean_email_body("") == ""

    def test_no_signature_returns_full_body(self):
        raw = "Simple message with no signature."
        assert clean_email_body(raw) == raw


class TestExtractSenderName:
    def test_extracts_name_from_angle_bracket_format(self):
        assert extract_sender_name("Jane Doe <jane@example.com>") == "Jane Doe"

    def test_extracts_quoted_name(self):
        assert extract_sender_name('"John Smith" <john@example.com>') == "John Smith"

    def test_falls_back_to_local_part(self):
        result = extract_sender_name("john.smith@example.com")
        assert "John" in result

    def test_handles_plain_email(self):
        result = extract_sender_name("support@example.com")
        assert isinstance(result, str)
        assert len(result) > 0


class TestTruncateText:
    def test_short_text_unchanged(self):
        text = "Short text"
        assert truncate_text(text, max_chars=100) == text

    def test_long_text_truncated(self):
        text = "a" * 5000
        result = truncate_text(text, max_chars=3000)
        assert len(result) < 5000
        assert "truncated" in result

    def test_exact_limit_unchanged(self):
        text = "a" * 100
        assert truncate_text(text, max_chars=100) == text


class TestBuildRawEmail:
    def test_includes_all_parts(self):
        result = build_raw_email("alice@example.com", "Test Subject", "Body text")
        assert "alice@example.com" in result
        assert "Test Subject" in result
        assert "Body text" in result
