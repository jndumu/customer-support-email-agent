"""Application configuration via pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # ── App ───────────────────────────────────────────────────────────────
    APP_ENV: str = "development"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    APP_DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # ── Company ───────────────────────────────────────────────────────────
    COMPANY_NAME: str = "Acme Support"
    HUMAN_REVIEW_EMAIL: str = "support-team@example.com"
    SUPPORT_EMAIL: str = "support@example.com"

    # ── OpenAI ────────────────────────────────────────────────────────────
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_TEMPERATURE: float = 0.2

    # ── Email (IMAP / SMTP) ───────────────────────────────────────────────
    EMAIL_HOST: str = ""
    EMAIL_PORT: int = 993
    EMAIL_USERNAME: str = ""
    EMAIL_PASSWORD: str = ""
    EMAIL_USE_TLS: bool = True
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587

    # ── Agent behaviour ───────────────────────────────────────────────────
    CLASSIFICATION_CONFIDENCE_THRESHOLD: float = 0.6
    MAX_RETRIEVED_DOCS: int = 5
    FOLLOWUP_DEFAULT_DAYS: int = 3    # default days before follow-up

    # ── Pinecone ──────────────────────────────────────────────────────────
    PINECONE_API_KEY: str = ""
    PINECONE_INDEX_NAME: str = "customer-support"
    PINECONE_CLOUD: str = "aws"
    PINECONE_REGION: str = "us-east-1"
    PINECONE_EMBEDDING_MODEL: str = "text-embedding-3-small"
    PINECONE_TOP_K: int = 5

    # ── LangSmith (optional tracing) ─────────────────────────────────────
    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_API_KEY: str = ""
    LANGCHAIN_PROJECT: str = "customer-support-email-agent"


settings = Settings()
