"""Pinecone vector store service.

FLOW POSITION: Called by retrieve_node (STEP 3) when PINECONE_API_KEY is set.

How it works:
  1. ensure_index_exists() checks for the configured index name in Pinecone
     and creates a serverless index (dimension=1536, metric=cosine) if absent.
     This runs once at startup — subsequent calls hit the lru_cache.

  2. get_vector_store() returns a LangChain PineconeVectorStore backed by
     OpenAI's text-embedding-3-small model (1536-dim embeddings). Cached.

  3. upsert_documents() accepts a list of LangChain Document objects,
     embeds them via OpenAI, and upserts the vectors into Pinecone.
     Call this once by running:
         uv run python -m src.scripts.seed_pinecone

  4. similarity_search() embeds the incoming query and retrieves the top-k
     most semantically similar chunks. These are returned as formatted strings
     for injection into draft_prompt.

Dimension note:
  text-embedding-3-small produces 1536-dimensional vectors.
  If you switch to text-embedding-3-large, update the index dimension to 3072
  and recreate the index (Pinecone indexes are fixed-dimension).
"""

from __future__ import annotations

from functools import lru_cache

from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_core.documents import Document
from pinecone import Pinecone, ServerlessSpec

from src.core.config import settings
from src.core.logging import logger


# ── Client initialisation ─────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def get_pinecone_client() -> Pinecone:
    """Return a cached Pinecone client authenticated with PINECONE_API_KEY."""
    return Pinecone(api_key=settings.PINECONE_API_KEY)


@lru_cache(maxsize=1)
def get_embeddings() -> OpenAIEmbeddings:
    """Return a cached OpenAI embeddings model for vectorising text."""
    return OpenAIEmbeddings(
        model=settings.PINECONE_EMBEDDING_MODEL,  # text-embedding-3-small
        api_key=settings.OPENAI_API_KEY,
    )


# ── Index lifecycle ───────────────────────────────────────────────────────────

def ensure_index_exists() -> None:
    """Create the Pinecone serverless index if it does not already exist.

    Index spec: cosine similarity, 1536 dimensions, serverless on AWS us-east-1.
    Change PINECONE_CLOUD / PINECONE_REGION in .env for a different region.
    """
    pc = get_pinecone_client()
    existing = [idx.name for idx in pc.list_indexes()]
    if settings.PINECONE_INDEX_NAME not in existing:
        logger.info("pinecone.create_index", index=settings.PINECONE_INDEX_NAME)
        pc.create_index(
            name=settings.PINECONE_INDEX_NAME,
            dimension=1536,   # matches text-embedding-3-small
            metric="cosine",
            spec=ServerlessSpec(
                cloud=settings.PINECONE_CLOUD,
                region=settings.PINECONE_REGION,
            ),
        )
        logger.info("pinecone.index_created", index=settings.PINECONE_INDEX_NAME)
    else:
        logger.debug("pinecone.index_exists", index=settings.PINECONE_INDEX_NAME)


@lru_cache(maxsize=1)
def get_vector_store() -> PineconeVectorStore:
    """Return a cached LangChain PineconeVectorStore pointing at the support index."""
    ensure_index_exists()
    return PineconeVectorStore(
        index_name=settings.PINECONE_INDEX_NAME,
        embedding=get_embeddings(),
        pinecone_api_key=settings.PINECONE_API_KEY,
    )


# ── Document upsert ───────────────────────────────────────────────────────────

def upsert_documents(documents: list[Document]) -> list[str]:
    """Embed and upsert documents into the Pinecone index.

    Called by seed_pinecone.py to load the dummy knowledge base.
    Each Document is embedded and stored with its metadata (source, heading,
    category) so search results can be labelled in the LLM context window.

    Returns a list of Pinecone vector IDs for the upserted records.
    """
    store = get_vector_store()
    ids = store.add_documents(documents)
    logger.info("pinecone.upsert", count=len(ids))
    return ids


# ── Retrieval ─────────────────────────────────────────────────────────────────

def similarity_search(query: str, top_k: int | None = None) -> list[str]:
    """Retrieve the top-k most semantically similar knowledge base chunks.

    The query is embedded and compared against all stored vectors using
    cosine similarity. Returns formatted strings ready for the LLM prompt:
        "[faq.md — Password Reset]\\nTo reset your password..."

    Called by retrieve_node when PINECONE_API_KEY is present in settings.
    """
    k = top_k or settings.PINECONE_TOP_K
    store = get_vector_store()
    results = store.similarity_search(query, k=k)
    logger.debug("pinecone.search", query=query[:60], results=len(results))
    return [
        f"[{doc.metadata.get('source', 'knowledge_base')} — {doc.metadata.get('heading', '')}]\n{doc.page_content}"
        for doc in results
    ]
