"""
Vector memory service.

Priority:
  1. ChromaDB (PersistentClient) — best semantic search, requires chromadb installed
  2. SQLite FTS5 fallback — keyword full-text search, zero extra dependencies
  3. No-op — if SQLite FTS5 not available (rare)
"""

import os
import logging
import uuid
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Storage Directory ─────────────────────────────────────────────────────────
VECTOR_DB_DIR = Path("./.vectordb")
VECTOR_DB_DIR.mkdir(exist_ok=True)

# ── Try ChromaDB (modern PersistentClient API) ────────────────────────────────
_chroma_collection = None

try:
    import chromadb

    _chroma_client = chromadb.PersistentClient(path=str(VECTOR_DB_DIR / "chroma"))
    _chroma_collection = _chroma_client.get_or_create_collection(
        name="conversations",
        metadata={"hnsw:space": "cosine"},
    )
    logger.info(f"ChromaDB initialised at {VECTOR_DB_DIR}/chroma — vector memory enabled.")

except Exception as e:
    logger.warning(f"ChromaDB unavailable ({type(e).__name__}: {e}). Using SQLite FTS5 fallback.")

# ── SQLite FTS5 Fallback ──────────────────────────────────────────────────────
_FTS_DB_PATH = str(VECTOR_DB_DIR / "fts_memory.db")
_fts_available = False

if _chroma_collection is None:
    try:
        _fts_conn = sqlite3.connect(_FTS_DB_PATH, check_same_thread=False)
        _fts_conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS messages
            USING fts5(user_id UNINDEXED, message, tokenize='porter unicode61')
        """)
        _fts_conn.commit()
        _fts_available = True
        logger.info("SQLite FTS5 vector memory fallback ready.")
    except Exception as e:
        logger.warning(f"SQLite FTS5 also unavailable: {e}. Vector memory disabled.")


# ── Public API ────────────────────────────────────────────────────────────────

def store_message(user_id: str, message: str) -> None:
    """Store a user message for later semantic retrieval."""
    if _chroma_collection is not None:
        try:
            _chroma_collection.add(
                documents=[message],
                metadatas=[{"user_id": user_id}],
                ids=[f"{user_id}_{uuid.uuid4().hex}"],
            )
            return
        except Exception as e:
            logger.warning(f"ChromaDB write failed: {e}")

    if _fts_available:
        try:
            _fts_conn.execute(
                "INSERT INTO messages(user_id, message) VALUES (?, ?)",
                (user_id, message),
            )
            _fts_conn.commit()
        except Exception as e:
            logger.warning(f"FTS5 write failed: {e}")


def search_similar(user_id: str, query: str, n_results: int = 5) -> list:
    """Retrieve past messages similar to the query for contextual AI responses."""
    if _chroma_collection is not None:
        try:
            results = _chroma_collection.query(
                query_texts=[query],
                n_results=n_results,
                where={"user_id": user_id},
            )
            return results.get("documents", [[]])[0]
        except Exception as e:
            logger.warning(f"ChromaDB query failed: {e}")

    if _fts_available:
        try:
            cur = _fts_conn.execute(
                """
                SELECT message FROM messages
                WHERE user_id = ? AND messages MATCH ?
                ORDER BY rank
                LIMIT ?
                """,
                (user_id, query, n_results),
            )
            return [row[0] for row in cur.fetchall()]
        except Exception as e:
            logger.warning(f"FTS5 query failed: {e}")

    return []
