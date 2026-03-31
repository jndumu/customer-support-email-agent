"""LLM client factory with retry logic."""

from functools import lru_cache

from langchain_openai import ChatOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.config import settings


@lru_cache(maxsize=1)
def get_llm() -> ChatOpenAI:
    """Return a cached ChatOpenAI instance."""
    return ChatOpenAI(
        model=settings.OPENAI_MODEL,
        temperature=settings.OPENAI_TEMPERATURE,
        api_key=settings.OPENAI_API_KEY,
        max_retries=3,
    )


@lru_cache(maxsize=1)
def get_llm_precise() -> ChatOpenAI:
    """Lower-temperature model for structured classification tasks."""
    return ChatOpenAI(
        model=settings.OPENAI_MODEL,
        temperature=0.0,
        api_key=settings.OPENAI_API_KEY,
        max_retries=3,
    )
