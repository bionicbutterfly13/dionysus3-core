"""
Session Manager Service
Feature: 001-session-continuity
Tasks: T009, T010

Manages journey tracking across multiple conversation sessions.
Provides operations for creating/retrieving journeys, sessions, and documents.

Database: PostgreSQL via asyncpg
"""

import logging
import os
import time
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

import asyncpg

from api.models.journey import (
    Journey,
    JourneyCreate,
    JourneyWithStats,
    Session,
    SessionCreate,
    SessionSummary,
    JourneyDocument,
    JourneyDocumentCreate,
    DocumentSummary,
    JourneyHistoryQuery,
    JourneyHistoryResponse,
    TimelineEntry,
    JourneyTimelineResponse,
)

# =============================================================================
# Configuration
# =============================================================================

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://dionysus:dionysus2024@localhost:5432/dionysus"
)

# =============================================================================
# Logging Setup (T010)
# =============================================================================

logger = logging.getLogger(__name__)

# Configure structured logging for journey operations
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def log_journey_operation(operation: str, journey_id: UUID, duration_ms: float = None, **kwargs):
    """Log journey operation with structured fields and optional timing."""
    extra = {
        "journey_id": str(journey_id),
        "operation": operation,
        **kwargs
    }
    if duration_ms is not None:
        extra["duration_ms"] = round(duration_ms, 2)
        # Warn if exceeding performance targets
        if operation in ("created", "retrieved") and duration_ms > 50:
            logger.warning(
                f"journey.{operation} exceeded 50ms target: {duration_ms:.2f}ms",
                extra=extra
            )
            return
        elif operation in ("history_queried", "timeline_queried") and duration_ms > 200:
            logger.warning(
                f"journey.{operation} exceeded 200ms target: {duration_ms:.2f}ms",
                extra=extra
            )
            return
    logger.info(f"journey.{operation}", extra=extra)


def log_session_operation(operation: str, session_id: UUID, journey_id: UUID, duration_ms: float = None, **kwargs):
    """Log session operation with structured fields and optional timing."""
    extra = {
        "session_id": str(session_id),
        "journey_id": str(journey_id),
        "operation": operation,
        **kwargs
    }
    if duration_ms is not None:
        extra["duration_ms"] = round(duration_ms, 2)
    logger.info(f"session.{operation}", extra=extra)


def measure_duration(start_time: float) -> float:
    """Calculate duration in milliseconds from start time."""
    return (time.perf_counter() - start_time) * 1000


# =============================================================================
# Exception Classes (T041)
# =============================================================================

class SessionManagerError(Exception):
    """Base exception for SessionManager errors."""
    pass


class DatabaseUnavailableError(SessionManagerError):
    """Raised when database is unavailable."""
    pass


class JourneyNotFoundError(SessionManagerError):
    """Raised when journey doesn't exist."""
    pass


# =============================================================================
# Database Pool Management
# =============================================================================

_pool: Optional[asyncpg.Pool] = None


async def get_pool() -> asyncpg.Pool:
    """Get or create database connection pool.

    Raises:
        DatabaseUnavailableError: If database connection fails
    """
    global _pool
    if _pool is None:
        try:
            _pool = await asyncpg.create_pool(
                DATABASE_URL,
                min_size=2,
                max_size=10,
                command_timeout=30,
            )
            logger.info("Database pool created for session_manager")
        except (asyncpg.PostgresError, OSError, ConnectionRefusedError) as e:
            logger.error(f"Failed to create database pool: {e}")
            raise DatabaseUnavailableError(f"Database unavailable: {e}") from e
    return _pool


async def close_pool():
    """Close database connection pool."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        logger.info("Database pool closed for session_manager")


# =============================================================================
# Session Manager Service (T009)
# =============================================================================

class SessionManager:
    """
    Manages journey tracking across multiple conversation sessions.
    
    A journey represents a device's complete interaction history.
    Sessions are individual conversations within a journey.
    Documents are artifacts (WOOP plans, uploads, etc.) linked to journeys.
    
    Usage:
        manager = SessionManager()
        journey = await manager.get_or_create_journey(device_id)
        session = await manager.create_session(journey.id)
        timeline = await manager.get_journey_timeline(journey.id)
    """
    
    def __init__(self, pool: Optional[asyncpg.Pool] = None):
        """
        Initialize session manager.
        
        Args:
            pool: Optional connection pool. If not provided, uses global pool.
        """
        self._pool = pool
    
    async def _get_pool(self) -> asyncpg.Pool:
        """Get connection pool."""
        if self._pool:
            return self._pool
        return await get_pool()
    
    # =========================================================================
    # Journey Operations (T015)
    # =========================================================================
    
    async def get_or_create_journey(self, device_id: UUID) -> JourneyWithStats:
        """
        Get existing journey for device or create new one.

        Args:
            device_id: Device identifier from ~/.dionysus/device_id

        Returns:
            JourneyWithStats with is_new=True if created, False if existing
        """
        start_time = time.perf_counter()
        pool = await self._get_pool()

        async with pool.acquire() as conn:
            # Try to get existing journey
            row = await conn.fetchrow(
                """
                SELECT j.*,
                       (SELECT COUNT(*) FROM sessions s WHERE s.journey_id = j.id) as session_count
                FROM journeys j
                WHERE j.device_id = $1
                """,
                device_id
            )

            if row:
                log_journey_operation(
                    "retrieved", row["id"],
                    duration_ms=measure_duration(start_time),
                    device_id=str(device_id)
                )
                return JourneyWithStats(
                    id=row["id"],
                    device_id=row["device_id"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    metadata=row["metadata"] or {},
                    session_count=row["session_count"],
                    is_new=False
                )

            # Create new journey with race condition protection (T042)
            # Uses ON CONFLICT to handle concurrent inserts gracefully
            row = await conn.fetchrow(
                """
                INSERT INTO journeys (device_id, metadata)
                VALUES ($1, $2)
                ON CONFLICT (device_id) DO UPDATE SET updated_at = CURRENT_TIMESTAMP
                RETURNING *, (xmax = 0) as was_inserted
                """,
                device_id,
                {}
            )

            # Check if this was a new insert or an update due to conflict
            is_new = row.get("was_inserted", True)

            operation = "created" if is_new else "retrieved_after_conflict"
            log_journey_operation(
                operation, row["id"],
                duration_ms=measure_duration(start_time),
                device_id=str(device_id)
            )

            # Get session count for existing journey (conflict case)
            session_count = 0
            if not is_new:
                count_row = await conn.fetchrow(
                    "SELECT COUNT(*) as cnt FROM sessions WHERE journey_id = $1",
                    row["id"]
                )
                session_count = count_row["cnt"] if count_row else 0

            return JourneyWithStats(
                id=row["id"],
                device_id=row["device_id"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                metadata=row["metadata"] or {},
                session_count=session_count,
                is_new=is_new
            )
    
    async def get_journey(self, journey_id: UUID) -> Optional[Journey]:
        """Get journey by ID."""
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM journeys WHERE id = $1",
                journey_id
            )
            
            if not row:
                return None
            
            return Journey(
                id=row["id"],
                device_id=row["device_id"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                metadata=row["metadata"] or {}
            )
    
    # =========================================================================
    # Session Operations (T016)
    # =========================================================================
    
    async def create_session(self, journey_id: UUID) -> Session:
        """
        Create a new session linked to a journey.
        
        Args:
            journey_id: Journey to link session to
            
        Returns:
            Created session
            
        Raises:
            ValueError: If journey_id doesn't exist
        """
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            # Verify journey exists
            journey = await conn.fetchrow(
                "SELECT id FROM journeys WHERE id = $1",
                journey_id
            )
            if not journey:
                raise ValueError(f"Journey {journey_id} not found")
            
            # Create session
            row = await conn.fetchrow(
                """
                INSERT INTO sessions (journey_id, messages)
                VALUES ($1, $2)
                RETURNING *
                """,
                journey_id,
                []
            )
            
            log_session_operation("created", row["id"], journey_id)
            return Session(
                id=row["id"],
                journey_id=row["journey_id"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                summary=row["summary"],
                messages=[],
                diagnosis=None,
                confidence_score=row["confidence_score"]
            )
    
    async def get_session(self, session_id: UUID) -> Optional[Session]:
        """Get session by ID."""
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM sessions WHERE id = $1",
                session_id
            )
            
            if not row:
                return None
            
            return Session(
                id=row["id"],
                journey_id=row["journey_id"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                summary=row["summary"],
                messages=row["messages"] or [],
                diagnosis=row["diagnosis"],
                confidence_score=row["confidence_score"]
            )
    
    # =========================================================================
    # Timeline Operations (T017)
    # =========================================================================
    
    async def get_journey_timeline(
        self,
        journey_id: UUID,
        limit: int = 50,
        include_documents: bool = False
    ) -> JourneyTimelineResponse:
        """
        Get sessions (and optionally documents) in chronological order.

        Args:
            journey_id: Journey to get timeline for
            limit: Max entries to return
            include_documents: Whether to include documents interleaved (T037)

        Returns:
            JourneyTimelineResponse with entries in chronological order
        """
        pool = await self._get_pool()
        entries: list[TimelineEntry] = []

        async with pool.acquire() as conn:
            # Fetch sessions
            session_rows = await conn.fetch(
                """
                SELECT id, created_at, summary, diagnosis IS NOT NULL as has_diagnosis
                FROM sessions
                WHERE journey_id = $1
                ORDER BY created_at ASC
                """,
                journey_id
            )

            for row in session_rows:
                entries.append(TimelineEntry(
                    entry_type="session",
                    entry_id=row["id"],
                    created_at=row["created_at"],
                    summary=row["summary"],
                    has_diagnosis=row["has_diagnosis"]
                ))

            # Fetch documents if requested
            if include_documents:
                doc_rows = await conn.fetch(
                    """
                    SELECT id, created_at, document_type, title
                    FROM journey_documents
                    WHERE journey_id = $1
                    ORDER BY created_at ASC
                    """,
                    journey_id
                )

                for row in doc_rows:
                    entries.append(TimelineEntry(
                        entry_type="document",
                        entry_id=row["id"],
                        created_at=row["created_at"],
                        document_type=row["document_type"],
                        title=row["title"]
                    ))

            # Sort all entries by created_at for interleaved timeline
            entries.sort(key=lambda e: e.created_at)

            # Apply limit after sorting
            entries = entries[:limit]

            log_journey_operation(
                "timeline_queried",
                journey_id,
                entry_count=len(entries),
                include_documents=include_documents
            )

            return JourneyTimelineResponse(
                journey_id=journey_id,
                entries=entries,
                total_entries=len(entries)
            )
    
    # =========================================================================
    # Query Operations (T026, T027, T028)
    # =========================================================================
    
    async def query_journey_history(
        self, 
        query: JourneyHistoryQuery
    ) -> JourneyHistoryResponse:
        """
        Search journey history by keyword, time range, or metadata.
        
        Uses full-text search on session summaries with pg_trgm GIN index.
        
        Args:
            query: Query parameters
            
        Returns:
            Matching sessions and optionally documents
        """
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            # Build query with optional filters
            sql = """
                SELECT id, created_at, summary, diagnosis IS NOT NULL as has_diagnosis,
                       CASE WHEN $2::text IS NOT NULL 
                            THEN ts_rank(to_tsvector('english', COALESCE(summary, '')), 
                                        plainto_tsquery('english', $2))
                            ELSE 0 END as relevance_score
                FROM sessions
                WHERE journey_id = $1
            """
            params: list[Any] = [query.journey_id, query.query]
            param_idx = 3
            
            # Keyword filter
            if query.query:
                sql += f" AND to_tsvector('english', COALESCE(summary, '')) @@ plainto_tsquery('english', ${param_idx})"
                params.append(query.query)
                param_idx += 1
            
            # Date range filters
            if query.from_date:
                sql += f" AND created_at >= ${param_idx}"
                params.append(query.from_date)
                param_idx += 1
            
            if query.to_date:
                sql += f" AND created_at <= ${param_idx}"
                params.append(query.to_date)
                param_idx += 1
            
            # Order by relevance if keyword search, else by date
            if query.query:
                sql += " ORDER BY relevance_score DESC, created_at DESC"
            else:
                sql += " ORDER BY created_at DESC"
            
            sql += f" LIMIT ${param_idx}"
            params.append(query.limit)
            
            rows = await conn.fetch(sql, *params)
            
            sessions = [
                SessionSummary(
                    session_id=row["id"],
                    created_at=row["created_at"],
                    summary=row["summary"],
                    has_diagnosis=row["has_diagnosis"],
                    relevance_score=row["relevance_score"] if query.query else None
                )
                for row in rows
            ]
            
            # Optionally include documents (T037)
            documents = []
            if query.include_documents:
                doc_rows = await conn.fetch(
                    """
                    SELECT id, document_type, title, created_at
                    FROM journey_documents
                    WHERE journey_id = $1
                    ORDER BY created_at DESC
                    LIMIT $2
                    """,
                    query.journey_id,
                    query.limit
                )
                documents = [
                    DocumentSummary(
                        document_id=row["id"],
                        document_type=row["document_type"],
                        title=row["title"],
                        created_at=row["created_at"]
                    )
                    for row in doc_rows
                ]
            
            log_journey_operation(
                "history_queried", 
                query.journey_id,
                query_text=query.query,
                result_count=len(sessions)
            )
            
            return JourneyHistoryResponse(
                journey_id=query.journey_id,
                sessions=sessions,
                documents=documents,
                total_results=len(sessions)
            )
    
    # =========================================================================
    # Document Operations (T035, T036)
    # =========================================================================
    
    async def add_document_to_journey(
        self, 
        document: JourneyDocumentCreate
    ) -> JourneyDocument:
        """
        Add a document or artifact to a journey.
        
        Args:
            document: Document to add
            
        Returns:
            Created document
            
        Raises:
            ValueError: If journey_id doesn't exist
        """
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            # Verify journey exists
            journey = await conn.fetchrow(
                "SELECT id FROM journeys WHERE id = $1",
                document.journey_id
            )
            if not journey:
                raise ValueError(f"Journey {document.journey_id} not found")
            
            row = await conn.fetchrow(
                """
                INSERT INTO journey_documents 
                    (journey_id, document_type, title, content, metadata)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING *
                """,
                document.journey_id,
                document.document_type,
                document.title,
                document.content,
                document.metadata
            )
            
            logger.info(
                f"document.created",
                extra={
                    "document_id": str(row["id"]),
                    "journey_id": str(document.journey_id),
                    "document_type": document.document_type
                }
            )
            
            return JourneyDocument(
                id=row["id"],
                journey_id=row["journey_id"],
                document_type=row["document_type"],
                title=row["title"],
                content=row["content"],
                metadata=row["metadata"] or {},
                created_at=row["created_at"]
            )
    
    async def delete_journey_document(self, document_id: UUID) -> bool:
        """
        Delete a document from a journey.
        
        Args:
            document_id: Document to delete
            
        Returns:
            True if deleted, False if not found
        """
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM journey_documents WHERE id = $1",
                document_id
            )
            
            deleted = result == "DELETE 1"
            if deleted:
                logger.info(
                    f"document.deleted",
                    extra={"document_id": str(document_id)}
                )
            
            return deleted
    
    # =========================================================================
    # Summary Generation (T026)
    # =========================================================================
    
    async def generate_session_summary(self, session_id: UUID) -> Optional[str]:
        """
        Generate and store a summary for a session.
        
        This is a placeholder - actual implementation would use an LLM.
        For now, it concatenates the first few messages.
        
        Args:
            session_id: Session to summarize
            
        Returns:
            Generated summary or None if session not found
        """
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT messages FROM sessions WHERE id = $1",
                session_id
            )
            
            if not row:
                return None
            
            messages = row["messages"] or []
            
            # Simple summary: first few messages
            summary_parts = []
            for msg in messages[:5]:
                if isinstance(msg, dict) and "content" in msg:
                    content = msg["content"][:100]
                    summary_parts.append(f"{msg.get('role', 'unknown')}: {content}")
            
            summary = " | ".join(summary_parts) if summary_parts else "Empty session"
            
            # Store summary
            await conn.execute(
                "UPDATE sessions SET summary = $1 WHERE id = $2",
                summary,
                session_id
            )
            
            log_session_operation("summary_generated", session_id, session_id)
            return summary

    # =========================================================================
    # Session ID File Management (T031, T032 - 002-remote-persistence-safety)
    # =========================================================================

    DEFAULT_SESSION_FILE = ".claude-session-id"

    async def get_or_create_session_id(
        self,
        session_file: Optional["Path"] = None
    ) -> str:
        """
        Get existing session ID from file or create a new one.

        Args:
            session_file: Path to session file. Defaults to .claude-session-id

        Returns:
            Session ID (UUID string)
        """
        from pathlib import Path
        import uuid

        if session_file is None:
            session_file = Path.home() / self.DEFAULT_SESSION_FILE

        session_file = Path(session_file)

        # Check for existing session
        if session_file.exists():
            session_id = session_file.read_text().strip()
            if session_id:
                logger.debug(f"Returning existing session_id: {session_id}")
                return session_id

        # Create new session ID
        session_id = str(uuid.uuid4())
        session_file.write_text(session_id)
        logger.info(f"Created new session_id: {session_id}")

        return session_id

    async def end_session(
        self,
        session_file: Optional["Path"] = None,
        trigger_summary: bool = True
    ) -> Optional[dict]:
        """
        End the current session: remove file, record metadata, and trigger summary.

        Args:
            session_file: Path to session file. Defaults to .claude-session-id
            trigger_summary: If True, trigger n8n workflow to generate summary

        Returns:
            Session record with metadata, or None if no session existed
        """
        from pathlib import Path
        from datetime import datetime

        if session_file is None:
            session_file = Path.home() / self.DEFAULT_SESSION_FILE

        session_file = Path(session_file)

        if not session_file.exists():
            return None

        session_id = session_file.read_text().strip()
        if not session_id:
            session_file.unlink()
            return None

        # Get file creation time as session start
        stat = session_file.stat()
        started_at = datetime.fromtimestamp(stat.st_ctime)
        ended_at = datetime.utcnow()

        # Remove the file
        session_file.unlink()
        logger.info(f"Ended session: {session_id}")

        # Record session end in database
        session_record = await self.record_session_end(
            session_id=session_id,
            started_at=started_at,
            ended_at=ended_at
        )

        # Trigger session summary generation via n8n (T047)
        if trigger_summary:
            try:
                from api.services.remote_sync import RemoteSyncService
                sync_service = RemoteSyncService()

                # Get memories for this session
                memories = await sync_service.query_by_session(session_id)

                if memories:
                    # Trigger n8n workflow to generate summary via Ollama
                    summary_result = await sync_service.trigger_session_summary(
                        session_id=session_id,
                        memories=memories
                    )
                    session_record["summary_triggered"] = summary_result.get("success", False)
                    if summary_result.get("summary"):
                        session_record["summary"] = summary_result["summary"]
                else:
                    logger.info(f"No memories found for session {session_id}, skipping summary")
                    session_record["summary_triggered"] = False

            except Exception as e:
                logger.warning(f"Failed to trigger session summary: {e}")
                session_record["summary_triggered"] = False
                session_record["summary_error"] = str(e)

        return session_record

    async def is_session_expired(
        self,
        session_file: Optional["Path"] = None,
        timeout_minutes: int = 30
    ) -> bool:
        """
        Check if session has expired due to inactivity.

        Args:
            session_file: Path to session file
            timeout_minutes: Inactivity timeout in minutes (default: 30)

        Returns:
            True if session is expired, False otherwise
        """
        from pathlib import Path
        from datetime import datetime

        if session_file is None:
            session_file = Path.home() / self.DEFAULT_SESSION_FILE

        session_file = Path(session_file)

        if not session_file.exists():
            return True

        # Check mtime for last activity
        stat = session_file.stat()
        last_activity = datetime.fromtimestamp(stat.st_mtime)
        now = datetime.now()
        elapsed_minutes = (now - last_activity).total_seconds() / 60

        return elapsed_minutes > timeout_minutes

    async def record_activity(
        self,
        session_file: Optional["Path"] = None
    ) -> None:
        """
        Record activity by touching the session file (updates mtime).

        Args:
            session_file: Path to session file
        """
        from pathlib import Path

        if session_file is None:
            session_file = Path.home() / self.DEFAULT_SESSION_FILE

        session_file = Path(session_file)

        if session_file.exists():
            session_file.touch()

    async def record_session_end(
        self,
        session_id: str,
        started_at: "datetime",
        ended_at: "datetime"
    ) -> dict:
        """
        Record session end metadata in database.

        Args:
            session_id: Session UUID string
            started_at: When session started
            ended_at: When session ended

        Returns:
            Session record dict
        """
        pool = await self._get_pool()

        async with pool.acquire() as conn:
            # Store in a session_metadata table or update existing sessions table
            await conn.execute(
                """
                INSERT INTO session_metadata (session_id, started_at, ended_at)
                VALUES ($1, $2, $3)
                ON CONFLICT (session_id) DO UPDATE SET ended_at = $3
                """,
                session_id, started_at, ended_at
            )

        logger.info(f"Recorded session end: {session_id}")

        return {
            "session_id": session_id,
            "started_at": started_at.isoformat(),
            "ended_at": ended_at.isoformat()
        }
