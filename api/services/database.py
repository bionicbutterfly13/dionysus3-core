"""
Database connection service for Supabase PostgreSQL.

Uses psycopg2 (sync) - works reliably with Supabase pooler.
"""

import os
import json
from typing import Optional
from contextlib import contextmanager

from dotenv import load_dotenv
import psycopg2

load_dotenv()
from psycopg2.extras import RealDictCursor

# Global connection
_conn = None


def init_db():
    """Initialize database connection."""
    global _conn
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL environment variable not set")

    _conn = psycopg2.connect(database_url)
    _conn.autocommit = True

    # Ensure sessions table exists
    with _conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ias_sessions (
                id TEXT PRIMARY KEY,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                data JSONB NOT NULL DEFAULT '{}'
            )
        """)

    print("Database connection initialized")


def close_db():
    """Close database connection."""
    global _conn
    if _conn:
        _conn.close()
        _conn = None
        print("Database connection closed")


@contextmanager
def get_connection():
    """Get database connection."""
    global _conn
    if not _conn:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    yield _conn


# =============================================================================
# SESSION PERSISTENCE (async wrappers for FastAPI compatibility)
# =============================================================================

async def save_session(session_id: str, data: dict) -> None:
    """Save session to database."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO ias_sessions (id, data, updated_at)
                VALUES (%s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (id) DO UPDATE SET
                    data = %s,
                    updated_at = CURRENT_TIMESTAMP
            """, (session_id, json.dumps(data), json.dumps(data)))


async def load_session(session_id: str) -> Optional[dict]:
    """Load session from database."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT data FROM ias_sessions WHERE id = %s",
                (session_id,)
            )
            row = cur.fetchone()
            if row:
                return json.loads(row['data']) if isinstance(row['data'], str) else row['data']
            return None


async def delete_session(session_id: str) -> None:
    """Delete session from database."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM ias_sessions WHERE id = %s",
                (session_id,)
            )


async def list_sessions(limit: int = 50) -> list[dict]:
    """List recent sessions."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, created_at, updated_at, data
                FROM ias_sessions
                ORDER BY updated_at DESC
                LIMIT %s
            """, (limit,))
            rows = cur.fetchall()
            return [
                {
                    "id": row['id'],
                    "created_at": row['created_at'].isoformat(),
                    "updated_at": row['updated_at'].isoformat(),
                    "data": json.loads(row['data']) if isinstance(row['data'], str) else row['data']
                }
                for row in rows
            ]


# =============================================================================
# MEMORY SEARCH (lightweight fallback when MCP not used)
# =============================================================================

async def search_memories_text(query: str, limit: int = 10) -> list[dict]:
    """Simple text search over memories table using Postgres full-text rank.

    This is a fallback until MCP memory search is fully wired. It uses
    plainto_tsquery over content and returns recent matches ordered by rank.
    """
    pattern = f"%{query}%"
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                    type,
                    content,
                    created_at,
                    COALESCE(
                        ts_rank_cd(
                            to_tsvector('english', content),
                            plainto_tsquery('english', %s)
                        ),
                        0
                    ) AS relevance
                FROM memories
                WHERE content ILIKE %s
                ORDER BY relevance DESC, created_at DESC
                LIMIT %s
                """,
                (query, pattern, limit)
            )
            rows = cur.fetchall()
            return [
                {
                    "type": row["type"],
                    "content": row["content"],
                    "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                    "relevance": float(row["relevance"]),
                }
                for row in rows
            ]


async def search_memories_similar(query: str, limit: int = 10) -> list[dict]:
    """Vector similarity search via search_similar_memories() DB function.

    This relies on the database function and embedding provider configured in the
    DB. If it fails (e.g., missing pgvector/http), callers should catch and
    fallback to text search.
    """
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT memory_id, content, type, similarity, importance
                FROM search_similar_memories(%s, %s)
                """,
                (query, limit),
            )
            rows = cur.fetchall()
            return [
                {
                    "memory_id": str(row["memory_id"]),
                    "type": row["type"],
                    "content": row["content"],
                    "similarity": float(row["similarity"]),
                    "importance": float(row["importance"]),
                }
                for row in rows
            ]
