"""Semantic search over the knowledge base."""
from functools import lru_cache

from app import config
from app.ingest import build_vector_store, get_embeddings


def _knowledge_fingerprint() -> str:
    files = sorted(config.KNOWLEDGE_DIR.glob("*.md"))
    return "|".join(f"{f.name}:{f.stat().st_size}:{int(f.stat().st_mtime)}" for f in files)


@lru_cache(maxsize=1)
def get_vector_store():
    from langchain_chroma import Chroma

    stamp = config.CHROMA_DIR / "knowledge.stamp"
    fingerprint = _knowledge_fingerprint()
    if not config.CHROMA_DIR.exists() or not stamp.exists() or stamp.read_text() != fingerprint:
        # First run, fresh deploy, or knowledge files changed: (re)build the index.
        store = build_vector_store(reset=True)
        stamp.write_text(fingerprint)
        return store
    return Chroma(
        collection_name=config.COLLECTION_NAME,
        embedding_function=get_embeddings(),
        persist_directory=str(config.CHROMA_DIR),
    )


def search(query: str, k: int = config.TOP_K) -> list[dict]:
    """Return the top-k chunks with source, section and similarity score."""
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
