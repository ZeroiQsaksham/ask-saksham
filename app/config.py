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
BOOKS_DIR = BASE_DIR / "books"

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

AGENT_NAME = os.getenv("AGENT_NAME", "Saksham")
OWNER_NAME = os.getenv("OWNER_NAME", "Saksham")

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
COLLECTION_NAME = "knowledge_base"
TOP_K = int(os.getenv("TOP_K", "6"))

# Astrologer mode: answers from a book (PDF) using hybrid search
ASTRO_NAME = os.getenv("ASTRO_NAME", "Ask Saksham (Astrologer)")
ASTRO_PDF = BOOKS_DIR / os.getenv("ASTRO_PDF", "vedic_astro_textbook.pdf")
ASTRO_BOOK_TITLE = os.getenv("ASTRO_BOOK_TITLE", "Vedic Astrology: An Integrated Approach")
ASTRO_BOOK_AUTHOR = os.getenv("ASTRO_BOOK_AUTHOR", "P.V.R. Narasimha Rao")
ASTRO_COLLECTION = "astrology_book"
ASTRO_CHUNKS_FILE = CHROMA_DIR / "astrology_chunks.json"  # cached parsed passages for keyword search
ASTRO_TOP_K = int(os.getenv("ASTRO_TOP_K", "5"))
BOOK_CHUNK_CHARS = 1100

# Chunking
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100

# Guardrails
MAX_QUESTION_CHARS = 1000
MAX_HISTORY_MESSAGES = 10
MAX_TOOL_ROUNDS = 3
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "15"))
