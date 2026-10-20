"""Retrieval for both modes.

- About mode: semantic search over knowledge/*.md
- Astrologer mode: hybrid search (embeddings + BM25 keywords, fused with RRF) over the book
Indexes are rebuilt automatically when their source files change (fingerprint stamps).
"""
import json
import logging
from functools import lru_cache

from app import config
from app.ingest import build_vector_store, get_embeddings

_KNOWLEDGE_STAMP = "knowledge.stamp"
_BOOK_STAMP = "book.stamp"


def _knowledge_fingerprint() -> str:
    files = sorted(config.KNOWLEDGE_DIR.glob("*.md"))
    return "|".join(f"{f.name}:{f.stat().st_size}:{int(f.stat().st_mtime)}" for f in files)


def _book_fingerprint() -> str:
    pdf = config.ASTRO_PDF
    # size + parser settings (not mtime: git checkouts on servers reset mtimes)
    return f"{pdf.name}:{pdf.stat().st_size}:{config.BOOK_CHUNK_CHARS}:v2" if pdf.exists() else "none"


def _stamp_ok(name: str, fingerprint: str) -> bool:
    stamp = config.CHROMA_DIR / name
    return stamp.exists() and stamp.read_text() == fingerprint


def _write_stamp(name: str, fingerprint: str) -> None:
    config.CHROMA_DIR.mkdir(exist_ok=True)
    (config.CHROMA_DIR / name).write_text(fingerprint)


def ensure_indexes(force: bool = False) -> None:
    """Build whichever index is missing or stale. Called at startup and by `python -m app.ingest`."""
    fp = _knowledge_fingerprint()
    if force or not _stamp_ok(_KNOWLEDGE_STAMP, fp):
        build_vector_store(reset=True)
        _write_stamp(_KNOWLEDGE_STAMP, fp)
    fp = _book_fingerprint()
    if config.ASTRO_PDF.exists() and (force or not _stamp_ok(_BOOK_STAMP, fp) or not config.ASTRO_CHUNKS_FILE.exists()):
        try:
            from app.book_ingest import build_book_store

            build_book_store()
            _write_stamp(_BOOK_STAMP, fp)
        except Exception:  # never let the book break "about" mode
            logging.getLogger("uvicorn.error").exception("Building the astrology book index failed")


def _open(collection: str):
    from langchain_chroma import Chroma

    return Chroma(
        collection_name=collection,
        embedding_function=get_embeddings(),
        persist_directory=str(config.CHROMA_DIR),
    )


@lru_cache(maxsize=1)
def get_vector_store():
    ensure_indexes()
    return _open(config.COLLECTION_NAME)


# ---------------- About mode ----------------

def search(query: str, k: int = config.TOP_K) -> list[dict]:
    """Return the top-k knowledge chunks with source, section and similarity score."""
    results = get_vector_store().similarity_search_with_relevance_scores(query, k=k)
    return [
        {
            "content": doc.page_content,
            "source": doc.metadata.get("source", "unknown"),
            "section": doc.metadata.get("section", ""),
            "score": round(float(score), 3),
        }
        for doc, score in results
    ]


def format_context(chunks: list[dict]) -> str:
    if not chunks:
        return "No relevant information found in the knowledge base."
    return "\n\n---\n\n".join(
        f"[source: {c['source']} | {c['section']}]\n{c['content']}" for c in chunks
    )


# ---------------- Astrologer mode ----------------

def book_available() -> bool:
    return config.ASTRO_PDF.exists() and config.ASTRO_CHUNKS_FILE.exists()


@lru_cache(maxsize=1)
def _book_index():
    """Load the book's passages, keyword index and vector store (once per process)."""
    from app.book_ingest import search_text
    from app.hybrid import BM25

    get_vector_store()  # makes sure indexes exist / are fresh
    chunks = json.loads(config.ASTRO_CHUNKS_FILE.read_text(encoding="utf-8"))
    # Section titles ("6.2.9 Navamsa Chart (D-9)") are strong topic signals: weight them 4x for keywords.
    bm25 = BM25([(c["section"] + " ") * 3 + search_text(c) for c in chunks])
    return chunks, bm25, _open(config.ASTRO_COLLECTION)


def search_book(query: str, k: int = config.ASTRO_TOP_K) -> list[dict]:
    """Hybrid search: semantic top-20 + BM25 top-20, merged with Reciprocal Rank Fusion."""
    from app.hybrid import reciprocal_rank_fusion

    chunks, bm25, store = _book_index()
    semantic = [d.metadata["chunk_index"] for d in store.similarity_search(query, k=20)]
    keyword = bm25.top_k(query, 20)
    ranked = reciprocal_rank_fusion([semantic, keyword])[:k]
    return [
        {"citation": chunks[i]["citation"], "content": chunks[i]["text"], "chapter": chunks[i]["chapter"]}
        for i in ranked
    ]


def format_book_context(passages: list[dict]) -> str:
    if not passages:
        return "No relevant passages found in the book."
    return "\n\n---\n\n".join(f"[{p['citation']}]\n{p['content']}" for p in passages)
