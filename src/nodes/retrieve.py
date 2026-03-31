"""Retrieve node — STEP 3 of the pipeline (skipped if escalated).

Responsibility:
  Search the knowledge base for the most relevant information chunks
  so the draft_node can ground its response in verified content.

What it does:
  - Builds a composite query from: intent + subject + first 300 chars of body.
  - Sends the query to Pinecone (semantic search) if PINECONE_API_KEY is set,
    otherwise falls back to the local BM25 keyword retrieval service.
  - Stores top-k results in state['retrieved_docs'] as formatted strings.

Why two retrieval backends:
  - Pinecone (primary): semantic/embedding-based — finds conceptually similar
    content even when exact words differ. Requires seeding via seed_pinecone.py.
  - Local BM25 (fallback): keyword-based — works without any external service,
    suitable for development or when Pinecone is not configured.

Fail-safe:
  On Pinecone failure, the node retries with local BM25 before giving up.
  An empty retrieved_docs list is valid — draft_node handles it gracefully
  by telling the LLM to use general best practices.

Input state fields used:  intent, subject, body, email_id
Output state fields set:  retrieved_docs, error
"""

from src.core.config import settings
from src.core.logging import logger
from src.graph.state import AgentState


def _pinecone_retrieve(query: str) -> list[str]:
    """Semantic similarity search via Pinecone vector store."""
    from src.services.pinecone_service import similarity_search
    return similarity_search(query, top_k=settings.PINECONE_TOP_K)


def _local_retrieve(query: str) -> list[str]:
    """BM25 keyword retrieval from local .md knowledge base files."""
    from src.services.knowledge_service import retrieve
    return retrieve(query, top_k=settings.MAX_RETRIEVED_DOCS)


def retrieve_node(state: AgentState) -> AgentState:
    """Search knowledge base and populate retrieved_docs in agent state."""
    logger.info("node.retrieve.start", email_id=state["email_id"])

    try:
        # Composite query: intent provides category context, subject + body
        # provide the specific problem vocabulary for better matching
        query = " ".join(filter(None, [
            state.get("intent", ""),
            state.get("subject", ""),
            state.get("body", "")[:300],
        ]))

        if settings.PINECONE_API_KEY:
            logger.debug("node.retrieve.using_pinecone", email_id=state["email_id"])
            docs = _pinecone_retrieve(query)
        else:
            logger.debug("node.retrieve.using_local", email_id=state["email_id"])
            docs = _local_retrieve(query)

        logger.info(
            "node.retrieve.complete",
            email_id=state["email_id"],
            docs_found=len(docs),
            backend="pinecone" if settings.PINECONE_API_KEY else "local",
        )

        return {**state, "retrieved_docs": docs, "error": None}

    except Exception as exc:
        logger.error("node.retrieve.error", email_id=state["email_id"], error=str(exc))
        # Fallback to local retrieval on Pinecone failure
        try:
            from src.services.knowledge_service import retrieve
            docs = retrieve(" ".join([state.get("intent", ""), state.get("subject", "")]))
            return {**state, "retrieved_docs": docs, "error": None}
        except Exception:
            # Return empty docs — draft_node will handle missing context gracefully
            return {**state, "retrieved_docs": [], "error": f"retrieve_node failed: {exc}"}
