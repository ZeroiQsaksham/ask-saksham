# Ask Saksham: a personal AI agent

A portfolio website with a built-in AI agent (**XYZ**) that answers visitors' questions about me: my education, skills, projects, experience and how to reach me.

The agent doesn't rely on what an LLM happens to know. It uses **Retrieval-Augmented Generation (RAG)** over a knowledge base of Markdown files I write. When a question comes in, the agent decides (via **tool calling**) to search the knowledge base, retrieves the most relevant passages with **semantic vector search**, and answers only from them. If the answer isn't there, it says so instead of making something up.

> Status: core pipeline, agent and website are built. Next: filling the knowledge base, running the evaluation, and deploying.

## Features

- **RAG pipeline**: Markdown → heading-aware chunking → embeddings → ChromaDB vector store → top-k semantic retrieval
- **Agent with tool calling**: the LLM chooses between `search_knowledge_base`, `get_contact_info` and `leave_message_for_owner`, in a think → act → observe loop
- **Streaming responses**: answers appear token by token
- **Conversation memory**: follow-up questions ("what tech did *it* use?") work
- **Guardrails**: grounded-only answers, "I don't know" fallback, prompt-injection-resistant system prompt, privacy rules, input limits, per-IP rate limiting
- **Free to run**: Llama 3.3 70B on Groq's free tier + local FastEmbed embeddings (no paid embedding API, no PyTorch)
- **Evaluation harness**: measures retrieval hit rate and answer accuracy on a test set
- **No retraining needed**: edit a Markdown file, re-run ingestion, and the agent knows

## Architecture

```
               INGESTION (python -m app.ingest)
knowledge/*.md ──► MarkdownHeaderTextSplitter ──► FastEmbed (bge-small) ──► ChromaDB
                                                                              ▲
               QUERY TIME                                                     │ similarity search
Visitor ──► Website chat widget ──► FastAPI /api/chat ──► Agent loop (LangChain + Groq Llama)
                     ▲                                       │  tool calls:
                     │                                       ├─ search_knowledge_base ──┘
                     └──── streamed answer ◄─────────────────├─ get_contact_info
                                                             └─ leave_message_for_owner
```

## Tech stack

| Layer | Technology |
|---|---|
| LLM | Llama 3.3 70B via **Groq** (`langchain-groq`) |
| Orchestration | **LangChain** (tool calling, messages, text splitters) |
| Embeddings | **FastEmbed**, `BAAI/bge-small-en-v1.5` (runs locally, ONNX) |
| Vector database | **ChromaDB** (`langchain-chroma`) |
| Backend | **FastAPI** + Uvicorn, streaming responses |
| Frontend | HTML, CSS, vanilla JavaScript |
| Deployment | Render (`render.yaml` included) |

## Project structure

```
ask-saksham/
├── app/
│   ├── config.py       # settings from .env
│   ├── ingest.py       # load → chunk → embed → store
│   ├── retriever.py    # semantic search + context formatting
│   ├── tools.py        # tools the agent can call
│   ├── prompts.py      # persona + grounding + safety rules
│   ├── agent.py        # tool-calling agent loop with streaming
│   ├── rate_limit.py   # per-IP rate limiter
│   └── main.py         # FastAPI app (API + website)
├── knowledge/          # the agent's knowledge: one Markdown file per topic
├── static/             # portfolio website + chat widget
├── eval/               # evaluation questions + script
├── requirements.txt
├── .env.example
└── render.yaml
```

## Run it locally

```bash
git clone https://github.com/ZeroiQsaksham/ask-saksham.git
cd ask-saksham
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env        # Windows: copy .env.example .env
# put your free Groq key (https://console.groq.com/keys) in .env

python -m app.ingest        # build the vector index from knowledge/
uvicorn app.main:app --reload
```

Open http://localhost:8000 and click **Ask XYZ**.

## Teaching the agent about me

1. Edit the files in `knowledge/` (one topic per `##` heading works best).
2. Rebuild the index: `python -m app.ingest`
3. Check retrieval: http://localhost:8000/api/search?q=what+are+his+skills

## Evaluation

```bash
python -m eval.run_eval            # retrieval hit rate (no API key needed)
python -m eval.run_eval --answers  # also checks answers against expected keywords
```

## API

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/chat` | `{ "question": "...", "history": [...] }` → streamed text answer |
| `GET` | `/api/search?q=` | Inspect retrieved chunks (debugging) |
| `GET` | `/api/config` | Agent and owner name |
| `GET` | `/api/health` | Health check |

## Deploy

Push to GitHub, create a new **Blueprint** on [Render](https://render.com) from this repo (it reads `render.yaml`), and set `GROQ_API_KEY` in the dashboard. The vector index is built automatically on first start.

## Roadmap

- [ ] Fill in the knowledge base with real details
- [ ] Deploy and add the live link here
- [ ] Email notification when a visitor leaves a message
- [ ] Hybrid search (BM25 + vectors) and re-ranking
- [ ] Source citations shown in the chat UI
- [ ] Analytics on the most-asked questions

## License

MIT
