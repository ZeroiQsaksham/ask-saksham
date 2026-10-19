"""Central configuration, loaded from environment variables (.env)."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
CHROMA_DIR = BASE_DIR / ".chroma"
DATA_DIR = BASE_DIR / "data"
STATIC_DIR = BASE_DIR / "static"

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

AGENT_NAME = os.getenv("AGENT_NAME", "Saksham")
OWNER_NAME = os.getenv("OWNER_NAME", "Saksham")

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
COLLECTION_NAME = "knowledge_base"
TOP_K = int(os.getenv("TOP_K", "6"))

# Chunking
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100

# Guardrails
MAX_QUESTION_CHARS = 1000
MAX_HISTORY_MESSAGES = 10
MAX_TOOL_ROUNDS = 3
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "15"))
