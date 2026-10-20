# Ask Saksham: a personal AI agent

**Live demo: https://ask-saksham.onrender.com** (free hosting: the first visit after a quiet period can take ~50 seconds to wake up)

A portfolio website with a built-in AI agent, **Saksham** (an AI version of me), that answers visitors' questions about me: my education, skills, projects, experience and how to reach me.

The agent doesn't rely on what an LLM happens to know. It uses **Retrieval-Augmented Generation (RAG)** over a knowledge base of Markdown files I write. When a question comes in, the agent decides (via **tool calling**) to search the knowledge base, retrieves the most relevant passages with **semantic vector search**, and answers only from them. If the answer isn't there, it says so instead of making something up.

> Status: live on Render, knowledge base filled from my resume and GitHub, 15/15 on the evaluation set.

## Two modes

| Mode | Knows | How it answers |
|---|---|---|
| **About Saksham** | `knowledge/*.md` (my resume, projects, skills) | Agent with tool calling: decides when to search my notes, share contact info or save a message |
| **Ask Saksham (Astrologer)** | `books/vedic_astro_textbook.pdf`, *Vedic Astrology: An Integrated Approach* by P.V.R. Narasimha Rao (515 pages, shared freely by the author) | Retrieve-then-generate with **hybrid search** (BM25 + embeddings, fused with Reciprocal Rank Fusion) and chapter/page citations |

### How the book is processed
1. `pypdf` extracts each page in layout mode; running headers are stripped and the printed page number is recorded.
2. Chapter (`16. Vimsottari Dasa`) and section (`16.2 Dasa Computation`) headings are detected, so every passage knows where it came from.
3. Paragraphs are grouped into ~1,100-character passages that never cross a section boundary (about 1,000 passages).
4. Each passage is embedded (FastEmbed) into its own ChromaDB collection **and** indexed with a pure-Python BM25 keyword index, because Sanskrit terms like *Vimsottari*, *Arudha* and *Argala* are matched far better by keywords than by small embedding models.
5. At question time, the top 20 from each ranking are fused with RRF and the best 5 passages go to the LLM with their citations.


- **RAG pipeline**: Markdown → heading-aware chunking → embeddings → ChromaDB vector store → top-k semantic retrieval
- **Agent with tool calling**: the LLM chooses between `search_knowledge_base`, `get_contact_info` and `leave_message_for_owner`, in a think → act → observe loop
- **Streaming responses**: answers appear token by token
- **Conversation memory**: follow-up questions ("what tech did *it* use?") work
- **Guardrails**: grounded-only answers, "I don't know" fallback, prompt-injection-resistant system prompt, privacy rules, input limits, per-IP rate limiting
- **Free to run**: GPT-OSS 120B on Groq's developer tier + local FastEmbed embeddings (no paid embedding API, no PyTorch)
- **Evaluation harness**: measures retrieval hit rate and answer accuracy on a test set
- **No retraining needed**: edit a Markdown file, re-run ingestion, and the agent knows

## Architecture

```
               INGESTION (python -m app.ingest)
knowledge/*.md ──► MarkdownHeaderTextSplitter ──► FastEmbed (bge-small) ──► ChromaDB
                                                                              ▲
               QUERY TIME                                                     │ similarity search
Visitor ──► Website chat widget ──► FastAPI /api/chat ──► Agent loop (LangChain + Groq LLM)
                     ▲                                       │  tool calls:
                     │                                       ├─ search_knowledge_base ──┘
                     └──── streamed answer ◄─────────────────├─ get_contact_info
                                                             └─ leave_message_for_owner
```

## Tech stack

| Layer | Technology |
|---|---|
| LLM | GPT-OSS 120B via **Groq** (`langchain-groq`) |
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
├── scripts/            # setup + end-to-end smoke test
├── launch.bat          # Windows: start the site (installs on first run)
├── install.bat         # Windows: install + self-test
├── publish.bat         # Windows: commit and push to GitHub
├── requirements.txt
├── .env.example
└── render.yaml
```

## Run it locally

**Windows, one click:** put your Groq key in `.env` (copy `.env.example`), then double-click `launch.bat`. The first run calls `install.bat`, which creates a virtual environment, installs everything, builds the index and runs the self-tests (report in `logs/setup.log`), then opens http://localhost:8000. The server auto-reloads when code or knowledge files change.

**Any OS, manual:**

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

Open http://localhost:8000 and click **Ask Saksham**.

## Teaching the agent about me

1. Edit the files in `knowledge/` (one topic per `##` heading works best).
2. Rebuild the index: `python -m app.ingest`
3. Check retrieval: http://localhost:8000/api/search?q=what+are+his+skills

## Evaluation

```bash
python -m eval.run_eval                       # about mode: retrieval hit rate (no API key needed)
python -m eval.run_eval --mode astro          # astrologer mode: is the right chapter retrieved?
python -m eval.run_eval --mode astro --answers --sleep 20   # also checks answers (paced for Groq free tier)
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

- [x] Fill in the knowledge base with real details
- [x] Deploy and add the live link here
- [ ] Email notification when a visitor leaves a message
- [ ] Hybrid search (BM25 + vectors) and re-ranking
- [ ] Source citations shown in the chat UI
- [ ] Analytics on the most-asked questions

## License

MIT
