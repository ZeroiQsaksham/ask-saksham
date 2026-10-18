# Knowledge base

Every `.md` file in this folder is what the agent knows about Saksham.
The agent answers **only** from these files, so anything not written here it will say it doesn't know.

How to update:
1. Replace every `[placeholder]` with real information (delete lines that don't apply).
2. Keep one topic per `##` heading. Headings become chunk boundaries, so clear headings mean better answers.
3. Rebuild the index: `python -m app.ingest`
4. Test: open `http://localhost:8000/api/search?q=your question` to see what gets retrieved.
