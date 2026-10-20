"""Astrologer mode: classic retrieve-then-generate RAG over the astrology book.

Unlike "about" mode (where the LLM decides when to call tools), every astrology question
needs the book, so we always retrieve first and make ONE LLM call. That halves latency and
token usage, which matters on Groq's free tier (~8K tokens/minute).
"""
from collections.abc import AsyncIterator
from functools import lru_cache

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app import config
from app.prompts import ASTRO_SYSTEM_PROMPT
from app.retriever import format_book_context, search_book


@lru_cache(maxsize=1)
def get_plain_llm():
    from langchain_groq import ChatGroq

    if not config.GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is not set.")
    return ChatGroq(model=config.GROQ_MODEL, api_key=config.GROQ_API_KEY, temperature=0.2, max_retries=3)


def retrieval_query(question: str, history: list[dict]) -> str:
    """Short follow-ups ("and for Venus?") need the previous question for context."""
    if len(question.split()) <= 6:
        previous = [t["content"] for t in history if t.get("role") == "user"]
        if previous:
            return f"{previous[-1]} {question}"
    return question


async def stream_astro_answer(question: str, history: list[dict]) -> AsyncIterator[str]:
    passages = search_book(retrieval_query(question, history))
    messages = [SystemMessage(content=ASTRO_SYSTEM_PROMPT)]
    for turn in history[-6:]:  # short memory keeps token usage low
        content = str(turn.get("content", ""))[:1500]
        if turn.get("role") == "user":
            messages.append(HumanMessage(content=content))
        elif turn.get("role") == "assistant":
            messages.append(AIMessage(content=content))
    messages.append(
        HumanMessage(
            content=f"Book passages:\n\n{format_book_context(passages)}\n\n---\n\nQuestion: {question}"
        )
    )
    async for chunk in get_plain_llm().astream(messages):
        if chunk.content:
            yield chunk.content
    # Always show where the answer came from (deterministic, not left to the LLM)
    sources = list(dict.fromkeys(p["citation"] for p in passages[:3]))
    if sources:
        yield "\n\n**Sources from the book:** " + " ".join(f"({s})" for s in sources)
