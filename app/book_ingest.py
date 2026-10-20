"""Book ingestion: PDF -> clean page text -> passages with chapter/section/page -> Chroma.

Run (together with the knowledge base):  python -m app.ingest
"""
import json
import re

from app import config

# Page header lines, e.g. "216   Vedic Astrology: An Integrated Approach" or "Part 1: Chart Analysis   9"
_HEADER = re.compile(r"^\s*(?:(\d{1,3})\s+Vedic Astrology: An Integrated Approach|Part \d+:[^\n]*?\s(\d{1,3}))\s*$")
_CHAPTER = re.compile(r"^(\d{1,2})\.\s+([A-Z][A-Za-z ,:’'&()-]{2,60})$")
_SECTION = re.compile(r"^(\d{1,2}(?:\.\d{1,2}){1,3})\s+([A-Z“\"][^\n]{1,80})$")
_PART = re.compile(r"^(Part \d+: [A-Za-z -]+)$")


def extract_pages(pdf_path=config.ASTRO_PDF) -> list[dict]:
    """Return [{pdf_page, printed_page, text}] using pypdf's layout-preserving extraction."""
    from pypdf import PdfReader

    pages = []
    for i, page in enumerate(PdfReader(str(pdf_path)).pages):
        try:
            raw = page.extract_text(extraction_mode="layout") or ""
        except Exception:  # some pages (blank separators) have no content stream
            raw = ""
        lines, printed = raw.split("\n"), None
        for j, line in enumerate(lines[:4]):
            m = _HEADER.match(line)
            if m:
                printed = int(m.group(1) or m.group(2))
                lines = lines[:j] + lines[j + 1 :]
                break
        body = "\n".join(re.sub(r"[ \t]{2,}", " ", ln).strip() for ln in lines)
        body = re.sub(r"\n{3,}", "\n\n", body).strip()
        pages.append({"pdf_page": i + 1, "printed_page": printed, "text": body})
    return pages


def _split_long(paragraph: str, limit: int) -> list[str]:
    if len(paragraph) <= limit:
        return [paragraph]
    parts, current = [], ""
    for sentence in re.split(r"(?<=[.!?])\s+|\n", paragraph):
        if current and len(current) + len(sentence) > limit:
            parts.append(current)
            current = ""
        current = f"{current}\n{sentence}".strip() if "\n" in paragraph else f"{current} {sentence}".strip()
    if current:
        parts.append(current)
    return parts


def chunk_pages(pages: list[dict], limit: int = config.BOOK_CHUNK_CHARS) -> list[dict]:
    """Group paragraphs into ~1,100-char passages that never cross a section boundary."""
    chunks: list[dict] = []
    state = {"chapter": "Front matter: preface and contents", "chapter_no": 0, "section": "", "part": ""}
    buf: list[str] = []
    buf_pages: list = []

    def flush():
        text = "\n".join(buf).strip()
        if len(text) > 80:
            chunks.append({**state, "page_start": buf_pages[0], "page_end": buf_pages[-1], "text": text})
        buf.clear()
        buf_pages.clear()

    for page in pages:
        page_label = page["printed_page"] if page["printed_page"] else f"front {page['pdf_page']}"
        for para in re.split(r"\n\s*\n", page["text"]):
            para = para.strip()
            if not para:
                continue
            first = para.split("\n")[0].strip()
            if _PART.match(first) and len(para) < 80:
                flush()
                state["part"] = first
                continue
            m = _CHAPTER.match(first)
            if m and int(m.group(1)) == state["chapter_no"] + 1:
                flush()
                state.update(chapter_no=int(m.group(1)), chapter=f"Chapter {m.group(1)}: {m.group(2).strip()}", section="")
                para = para[len(first):].strip()
                if not para:
                    continue
                first = para.split("\n")[0].strip()
            m = _SECTION.match(first)
            if m and m.group(1).split(".")[0] == str(state["chapter_no"]):
                flush()
                state["section"] = f"{m.group(1)} {m.group(2).strip()}"
            for piece in _split_long(para, limit):
                if buf and sum(len(b) for b in buf) + len(piece) > limit:
                    flush()
                buf.append(piece)
                buf_pages.append(page_label)
    flush()
    for i, c in enumerate(chunks):
        c["id"] = f"book-{i}"
        c["citation"] = format_citation(c)
    return chunks


def format_citation(c: dict) -> str:
    start, end = str(c["page_start"]), str(c["page_end"]).replace("front ", "")
    pages = start if start.replace("front ", "") == end else f"{start}-{end}"  # e.g. "210-211", "front 8-9"
    sec = f", section {c['section'].split(' ')[0]}" if c["section"] else ""
    return f"{c['chapter']}{sec}, p. {pages}"


def search_text(c: dict) -> str:
    """Text that gets embedded / keyword-indexed: topic breadcrumb + passage."""
    return f"{c['chapter']} > {c['section']}\n{c['text']}" if c["section"] else f"{c['chapter']}\n{c['text']}"


def build_book_store():
    """Parse the PDF, cache passages as JSON, and (re)build the book's Chroma collection."""
    from langchain_chroma import Chroma
    from langchain_core.documents import Document

    from app.ingest import get_embeddings

    if not config.ASTRO_PDF.exists():
        print(f"No book found at {config.ASTRO_PDF} - astrologer mode disabled.")
        return None
    chunks = chunk_pages(extract_pages())
    config.CHROMA_DIR.mkdir(exist_ok=True)
    config.ASTRO_CHUNKS_FILE.write_text(json.dumps(chunks), encoding="utf-8")

    store = Chroma(
        collection_name=config.ASTRO_COLLECTION,
        embedding_function=get_embeddings(),
        persist_directory=str(config.CHROMA_DIR),
    )
    store.delete_collection()  # start fresh (keeps other collections intact)
    store = Chroma(
        collection_name=config.ASTRO_COLLECTION,
        embedding_function=get_embeddings(),
        persist_directory=str(config.CHROMA_DIR),
    )
    docs = [
        Document(page_content=search_text(c), metadata={"chunk_index": i, "citation": c["citation"]})
        for i, c in enumerate(chunks)
    ]
    for start in range(0, len(docs), 128):  # batches keep memory low on small servers
        batch = docs[start : start + 128]
        store.add_documents(batch, ids=[chunks[d.metadata["chunk_index"]]["id"] for d in batch])
    print(f"Indexed {len(chunks)} passages from {config.ASTRO_PDF.name}")
    return store
