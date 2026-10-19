"""FastAPI app: serves the portfolio website and the /api/chat endpoint.

Run locally:
    uvicorn app.main:app --reload
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app import config
from app.agent import stream_answer
from app.rate_limit import RateLimiter
from app.retriever import get_vector_store, search

limiter = RateLimiter(config.RATE_LIMIT_PER_MINUTE)
logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(_: FastAPI):
    get_vector_store()  # load (or build) the index once at startup
    yield


app = FastAPI(title="ask-saksham", lifespan=lifespan)


class Turn(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=config.MAX_QUESTION_CHARS)
    history: list[Turn] = []


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/config")
def public_config():
    return {"agent_name": config.AGENT_NAME, "owner_name": config.OWNER_NAME}


@app.post("/api/chat")
async def chat(req: ChatRequest, request: Request):
    client_ip = request.client.host if request.client else "unknown"
    if not limiter.allow(client_ip):
        raise HTTPException(status_code=429, detail="Too many questions. Please wait a minute.")

    history = [t.model_dump() for t in req.history]

    async def token_stream():
        try:
            async for token in stream_answer(req.question.strip(), history):
                yield token
        except Exception as exc:
            if "rate_limit" in str(exc).lower() or "429" in str(exc):
                logger.warning("Groq rate limit hit")
                yield "I'm getting a lot of questions right now. Please try again in a few seconds."
                return
            logger.exception("Chat request failed")
            yield "Sorry, something went wrong on my side. Please try again in a moment."

    return StreamingResponse(token_stream(), media_type="text/plain; charset=utf-8")


@app.get("/api/search")
def debug_search(q: str):
    """Inspect what the retriever finds for a query (handy while writing knowledge files)."""
    return search(q)


app.mount("/static", StaticFiles(directory=config.STATIC_DIR), name="static")


@app.get("/")
def index():
    return FileResponse(config.STATIC_DIR / "index.html")
