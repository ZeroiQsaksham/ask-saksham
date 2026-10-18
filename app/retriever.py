"""Semantic search over the knowledge base."""
from functools import lru_cache

from app import config
from app.ingest import build_vector_store, get_embeddings


@lru_cache(maxsize=1)
def get_vector_store():
    from langchain_chroma import Chroma

    if not config.CHROMA_DIR.exists():
        # First run (or fresh deploy): build the index automatically.
        return build_vector_store(reset=True)
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
