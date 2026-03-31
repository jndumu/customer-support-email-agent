"""Seed script — embeds dummy documents and upserts them into Pinecone.

Usage:
    uv run python -m src.scripts.seed_pinecone

Prerequisites:
    - PINECONE_API_KEY set in .env
    - OPENAI_API_KEY set in .env
    - uv sync (dependencies installed)
"""

import sys
import time

from src.core.config import settings
from src.core.logging import configure_logging, logger
from src.knowledge_base.dummy_documents import DUMMY_DOCUMENTS
from src.services.pinecone_service import ensure_index_exists, upsert_documents


def main() -> None:
    configure_logging()

    if not settings.PINECONE_API_KEY:
        logger.error("seed.missing_pinecone_key")
        print("ERROR: PINECONE_API_KEY is not set in your .env file.")
        sys.exit(1)

    if not settings.OPENAI_API_KEY:
        logger.error("seed.missing_openai_key")
        print("ERROR: OPENAI_API_KEY is not set in your .env file.")
        sys.exit(1)

    print(f"\n Seeding Pinecone index: '{settings.PINECONE_INDEX_NAME}'")
    print(f" Documents to upsert : {len(DUMMY_DOCUMENTS)}")
    print(f" Embedding model     : {settings.PINECONE_EMBEDDING_MODEL}\n")

    # Step 1 — ensure index exists
    print("Step 1/2 — Ensuring index exists...")
    ensure_index_exists()

    # Brief pause to allow serverless index to become ready
    time.sleep(2)

    # Step 2 — upsert documents
    print("Step 2/2 — Embedding and upserting documents...")
    ids = upsert_documents(DUMMY_DOCUMENTS)

    print(f"\n Done! {len(ids)} document chunks upserted into '{settings.PINECONE_INDEX_NAME}'.")
    print(" You can now run the API and queries will use Pinecone for retrieval.\n")


if __name__ == "__main__":
    main()
