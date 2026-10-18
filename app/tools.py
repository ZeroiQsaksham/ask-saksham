"""Tools the agent can decide to call (LLM function calling)."""
import json
from datetime import datetime, timezone

from langchain_core.tools import tool

from app import config
from app.retriever import format_context, search


@tool
def search_knowledge_base(query: str) -> str:
    """Search Saksham's personal knowledge base (about, education, skills, projects,
    experience, contact, FAQ). Use a focused search query for the visitor's question."""
    return format_context(search(query))


@tool
def get_contact_info() -> str:
    """Get the public ways to contact Saksham (email, LinkedIn, GitHub, resume link)."""
    return format_context(search("contact email LinkedIn GitHub resume link", k=2))


@tool
def leave_message_for_owner(visitor_name: str, visitor_contact: str, message: str) -> str:
    """Save a message from a visitor (e.g. a recruiter) for Saksham to read later.
    Only call this when the visitor explicitly asks to leave a message and has given
    their name, a way to contact them, and the message."""
    config.DATA_DIR.mkdir(exist_ok=True)
    record = {
        "time": datetime.now(timezone.utc).isoformat(),
        "name": visitor_name[:100],
        "contact": visitor_contact[:200],
        "message": message[:2000],
    }
    with open(config.DATA_DIR / "messages.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    return "Message saved. Saksham will see it and get back to the visitor."


TOOLS = [search_knowledge_base, get_contact_info, leave_message_for_owner]
TOOLS_BY_NAME = {t.name: t for t in TOOLS}
