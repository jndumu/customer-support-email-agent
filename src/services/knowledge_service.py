"""Knowledge base retrieval service.

FLOW POSITION: Called by retrieve_node (step 3 of the pipeline).

How it works:
  1. On first call, _build_index() reads all .md files from knowledge_base/
     and splits each file into heading-level chunks (e.g. "## Refund Policy"
     becomes one chunk). The index is cached in memory for the lifetime of
     the process.
  2. retrieve() tokenises the incoming query and scores every chunk using a
     BM25-inspired TF-IDF formula — chunks that share more rare terms with
     the query rank higher.
  3. The top-k chunks are returned as formatted strings and injected into
     the draft_prompt by draft_node.

Swap for Pinecone (semantic search) by setting PINECONE_API_KEY in .env.
The retrieve_node will automatically prefer Pinecone when the key is present.
"""

from __future__ import annotations

import math
import re
from pathlib import Path
from functools import lru_cache

from src.core.config import settings
from src.core.logging import logger

# Path to the knowledge_base/ directory relative to this file
_KB_DIR = Path(__file__).parent.parent / "knowledge_base"


# ── Step 1: Document loading & chunking ──────────────────────────────────────
# Each .md file is split at heading boundaries (##, ###) so the LLM receives
# focused, section-level excerpts rather than entire documents.

def _load_documents() -> list[dict]:
    """Read every .md file in knowledge_base/ and split into heading chunks."""
    chunks: list[dict] = []
    for md_file in sorted(_KB_DIR.glob("*.md")):
        text = md_file.read_text(encoding="utf-8")
        file_chunks = _split_by_headings(text, source=md_file.name)
        chunks.extend(file_chunks)
        logger.debug("knowledge_base.loaded", file=md_file.name, chunks=len(file_chunks))
    return chunks


def _split_by_headings(text: str, source: str) -> list[dict]:
    """Split a markdown document into chunks at each heading (# / ## / ###).

    Each chunk carries the source filename and heading title as metadata
    so the retrieval result can be labelled for the LLM context window.
    """
    heading_re = re.compile(r"^(#{1,3})\s+(.+)$", re.MULTILINE)
    chunks: list[dict] = []
    matches = list(heading_re.finditer(text))

    if not matches:
        # No headings — treat the whole document as a single chunk
        return [{"source": source, "heading": source, "content": text.strip()}]

    for i, match in enumerate(matches):
        start = match.start()
        # Each chunk ends where the next heading begins (or at EOF)
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        chunk_text = text[start:end].strip()
        if len(chunk_text) < 20:
            continue  # skip trivially short chunks
        chunks.append({
            "source": source,
            "heading": match.group(2).strip(),
            "content": chunk_text,
        })

    return chunks


# ── Step 2: BM25-style relevance scoring ─────────────────────────────────────
# BM25 penalises very long chunks (length normalisation via parameter b) and
# rewards rare terms (IDF), avoiding the bias of pure term-frequency matching.

def _tokenise(text: str) -> list[str]:
    """Lowercase and extract all words of 2+ characters."""
    return re.findall(r"\b[a-z]{2,}\b", text.lower())


def _score_chunk(
    query_tokens: list[str],
    chunk_tokens: list[str],
    doc_freq: dict[str, int],
    total_docs: int,
) -> float:
    """Score a single chunk against the query using BM25 (k1=1.5, b=0.75).

    Higher scores = more relevant to the query.
    Returns 0.0 when the chunk shares no tokens with the query.
    """
    k1, b = 1.5, 0.75
    avg_len = 200           # approximate average chunk length in tokens
    chunk_len = len(chunk_tokens)

    # Build term-frequency map for this chunk
    freq: dict[str, int] = {}
    for t in chunk_tokens:
        freq[t] = freq.get(t, 0) + 1

    score = 0.0
    for token in set(query_tokens):
        if token not in freq:
            continue
        tf = freq[token]
        # IDF: rare tokens across the corpus get a higher weight
        idf = math.log((total_docs + 1) / (doc_freq.get(token, 0) + 1)) + 1
        # Length-normalised TF
        tf_norm = tf * (k1 + 1) / (tf + k1 * (1 - b + b * chunk_len / avg_len))
        score += idf * tf_norm
    return score


# ── Step 3: Index construction (cached) ──────────────────────────────────────
# Built once on first retrieval call; avoids repeated file I/O on every email.

@lru_cache(maxsize=1)
def _build_index() -> tuple[list[dict], dict[str, int]]:
    """Load all chunks and compute corpus-level document frequency map."""
    chunks = _load_documents()
    doc_freq: dict[str, int] = {}
    for chunk in chunks:
        # Each term counted once per chunk (document frequency, not term freq)
        tokens = set(_tokenise(chunk["content"]))
        for t in tokens:
            doc_freq[t] = doc_freq.get(t, 0) + 1
    return chunks, doc_freq


# ── Public interface ──────────────────────────────────────────────────────────

def retrieve(query: str, top_k: int | None = None) -> list[str]:
    """Return the top-k most relevant knowledge base chunks for *query*.

    Called by retrieve_node when PINECONE_API_KEY is not set (local fallback).
    Returns formatted strings like:
        "[faq.md — Password Reset]\\nTo reset your password..."
    """
    k = top_k or settings.MAX_RETRIEVED_DOCS
    chunks, doc_freq = _build_index()
    total = len(chunks)

    query_tokens = _tokenise(query)
    if not query_tokens:
        return []  # nothing to match against

    # Score every chunk and keep the top-k
    scored = []
    for chunk in chunks:
        chunk_tokens = _tokenise(chunk["content"])
        score = _score_chunk(query_tokens, chunk_tokens, doc_freq, total)
        if score > 0:
            scored.append((score, chunk))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:k]

    logger.debug("knowledge_service.retrieved", query=query[:60], results=len(top))
    # Format for injection into the LLM prompt
    return [f"[{c['source']} — {c['heading']}]\n{c['content']}" for _, c in top]
