"""Ingestion pipeline: Markdown files -> chunks -> embeddings -> Chroma vector store.

Run manually after editing anything in knowledge/:
    python -m app.ingest
"""
import shutil
from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

from app import config

HEADERS_TO_SPLIT_ON = [("#", "h1"), ("##", "h2"), ("###", "h3")]


def load_markdown_files(folder: Path = config.KNOWLEDGE_DIR) -> list[tuple[str, str]]:
    """Return (filename, text) for every .md file in the knowledge folder."""
    files = sorted(f for f in folder.glob("*.md") if f.name.lower() != "readme.md")
    return [(f.name, f.read_text(encoding="utf-8")) for f in files]


def chunk_markdown(filename: str, text: str) -> list[Document]:
    """Split one Markdown file by headings, then by size, keeping metadata."""
    header_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=HEADERS_TO_SPLIT_ON, strip_headers=False
    )
    size_splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE, chunk_overlap=config.CHUNK_OVERLAP
    )
    sections = header_splitter.split_text(text)
    chunks = size_splitter.split_documents(sections)

    for i, chunk in enumerate(chunks):
        headings = [chunk.metadata.get(k) for k in ("h1", "h2", "h3") if chunk.metadata.get(k)]
        chunk.metadata["source"] = filename
        chunk.metadata["section"] = " > ".join(headings) or filename
        chunk.metadata["chunk_id"] = f"{filename}#{i}"
    return [c for c in chunks if c.page_content.strip()]


def build_documents() -> list[Document]:
    docs: list[Document] = []
    for filename, text in load_markdown_files():
        docs.extend(chunk_markdown(filename, text))
    return docs


def get_embeddings():
    # FastEmbed runs a small ONNX model locally: free, no API key, no PyTorch.
    from langchain_community.embeddings.fastembed import FastEmbedEmbeddings

    return FastEmbedEmbeddings(model_name=config.EMBEDDING_MODEL)


def build_vector_store(reset: bool = True):
    """(Re)build the Chroma index from the knowledge folder."""
    from langchain_chroma import Chroma

    if reset and config.CHROMA_DIR.exists():
        shutil.rmtree(config.CHROMA_DIR)

    docs = build_documents()
    if not docs:
        raise RuntimeError(f"No Markdown files found in {config.KNOWLEDGE_DIR}")

    store = Chroma.from_documents(
        documents=docs,
        embedding=get_embeddings(),
        collection_name=config.COLLECTION_NAME,
        persist_directory=str(config.CHROMA_DIR),
        ids=[d.metadata["chunk_id"] for d in docs],
    )
    print(f"Indexed {len(docs)} chunks from {config.KNOWLEDGE_DIR.name}/")
    return store


if __name__ == "__main__":
    build_vector_store(reset=True)
