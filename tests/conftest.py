"""Shared pytest fixtures."""

import pytest
from httpx import AsyncClient, ASGITransport

from src.main import app


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest.fixture
def sample_email_payload():
    return {
        "sender": "Jane Doe <jane.doe@example.com>",
        "subject": "Cannot log in to my account",
        "body": (
            "Hi Support,\n\n"
            "I have been trying to log in to my account for the past hour but keep getting "
            "an error saying my account is locked. I haven't changed my password recently. "
            "Can you please help me unlock it?\n\n"
            "Thanks,\nJane"
        ),
    }


@pytest.fixture
def billing_email_payload():
    return {
        "sender": "john.smith@company.com",
        "subject": "Incorrect charge on my invoice",
        "body": (
            "Hello,\n\n"
            "I was charged $99 this month but I am on the $49 plan. "
            "Please review invoice #INV-20240315 and issue a refund for the difference.\n\n"
            "Regards,\nJohn Smith"
        ),
    }


@pytest.fixture
def urgent_email_payload():
    return {
        "sender": "legal@bigcorp.com",
        "subject": "Legal notice — GDPR data breach",
        "body": (
            "To whom it may concern,\n\n"
            "We have reason to believe our company data has been exposed due to a breach "
            "in your systems. We are prepared to involve our legal team if this is not "
            "resolved within 24 hours. Please contact us immediately.\n\n"
            "Big Corp Legal Team"
        ),
    }
