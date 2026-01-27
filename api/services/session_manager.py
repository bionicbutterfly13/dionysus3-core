"""
Session Manager Service
Feature: 001-session-continuity
Tasks: T009, T010

Manages journey tracking across multiple conversation sessions.
Provides operations for creating/retrieving journeys, sessions, and documents.

Database: Neo4j via Graphiti-backed driver
"""

import json
import logging
import time
from datetime import datetime
from typing import Any, Optional
from uuid import UUID, uuid4

from api.models.journey import (
    Journey,
    JourneyWithStats,
    Session,
    SessionSummary,
    JourneyHistoryQuery,
    JourneyHistoryResponse,
    TimelineEntry,
    JourneyTimelineResponse,
)
from api.services.remote_sync import get_neo4j_driver

# =============================================================================
# Logging Setup (T010)
# =============================================================================

logger = logging.getLogger(__name__)

def log_journey_operation(operation: str, journey_id: Any, duration_ms: float = None, **kwargs):
    """Log journey operation with structured fields and optional timing."""
    extra = {
        "journey_id": str(journey_id),
        "operation": operation,
        **kwargs
    }
    if duration_ms is not None:
        extra["duration_ms"] = round(duration_ms, 2)
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


def log_session_operation(operation: str, session_id: Any, journey_id: Any, duration_ms: float = None, **kwargs):
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
    
    def __init__(self, driver=None):
        """
        Initialize session manager.
        
        Args:
            driver: Optional Neo4j driver. If not provided, uses the webhook driver.
        """
        self._driver = driver or get_neo4j_driver()
    
    # =========================================================================
    # Journey Operations (T015)
    # =========================================================================
    
    async def get_or_create_journey(self, device_id: UUID, participant_id: Optional[str] = None) -> JourneyWithStats:
        """
        Get existing journey for device or create new one.

        Args:
            device_id: Device identifier from ~/.dionysus/device_id
            participant_id: Optional human identity identifier

        Returns:
            JourneyWithStats with is_new=True if created, False if existing
        """
        start_time = time.perf_counter()
        
        # Try to MATCH existing journey first
        query_match = """
        MATCH (j:Journey)
        WHERE j.device_id = $device_id OR j.id = $device_id
        WITH j
        OPTIONAL MATCH (j)-[:HAS_SESSION]->(s:Session)
        RETURN j {.*} as journey_data, count(s) as session_count
        """
        
        try:
            result = await self._driver.execute_query(query_match, {"device_id": str(device_id)})
            
            if not result or not result[0].get("journey_data"):
                # Journey doesn't exist, CREATE it
                new_id = str(uuid4())
                query_create = """
                CREATE (j:Journey {
                    device_id: $device_id,
                    id: $id,
                    participant_id: $participant_id,
                    created_at: datetime(),
                    updated_at: datetime(),
                    metadata: '{}',
                    _is_new: true
                })
                RETURN j {.*} as journey_data, 0 as session_count
                """
                result = await self._driver.execute_query(query_create, {
                    "device_id": str(device_id),
                    "id": new_id,
                    "participant_id": participant_id
                })
            
            if not result:
                raise DatabaseUnavailableError("Failed to create journey node in Neo4j")
            
            row = result[0]
            j_data = row["journey_data"]
            session_count = int(row["session_count"])
            is_new = j_data.get("_is_new", False)
            
            operation = "created" if is_new else "retrieved"
            log_journey_operation(
                operation, j_data["id"],
                duration_ms=measure_duration(start_time),
                device_id=str(device_id)
            )
            
            # Helper to handle datetime conversion
            def _to_dt(val):
                if not val: return datetime.utcnow()
                if hasattr(val, 'to_native'): return val.to_native() # Neo4j DateTime
                if isinstance(val, str): return datetime.fromisoformat(val.replace('Z', '+00:00'))
                return val

            return JourneyWithStats(
                id=UUID(j_data["id"]),
                device_id=UUID(j_data["device_id"]),
                created_at=_to_dt(j_data.get("created_at")),
                updated_at=_to_dt(j_data.get("updated_at")),
                metadata=json.loads(j_data.get("metadata", "{}")),
                session_count=session_count,
                is_new=is_new
            )
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            logger.error(f"Error in get_or_create_journey: {e}\n{error_trace}")
            raise DatabaseUnavailableError(f"Database error: {e}")

    async def get_journey(self, journey_id: UUID) -> Optional[Journey]:
        """Get journey by ID."""
        cypher = "MATCH (j:Journey {id: $id}) RETURN j"
        
        try:
            result = await self._driver.execute_query(cypher, {"id": str(journey_id)})
            if not result:
                return None
            
            j_node = result[0]["j"]
            return Journey(
                id=UUID(j_node["id"]),
                device_id=UUID(j_node["device_id"]),
                created_at=datetime.fromisoformat(j_node["created_at"].replace('Z', '+00:00')) if isinstance(j_node["created_at"], str) else j_node["created_at"],
                updated_at=datetime.fromisoformat(j_node["updated_at"].replace('Z', '+00:00')) if isinstance(j_node["updated_at"], str) else j_node["updated_at"],
                metadata=json.loads(j_node.get("metadata", "{}"))
            )
        except Exception as e:
            logger.error(f"Error getting journey: {e}")
            return None
    
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
        """
        session_id = str(uuid4())
        cypher = """
        MATCH (j:Journey {id: $journey_id})
        CREATE (s:Session {
            id: $session_id,
            journey_id: $journey_id,
            created_at: datetime(),
            updated_at: datetime(),
            summary: 'New session',
            messages: '[]',
            confidence_score: 1.0
        })
        CREATE (j)-[:HAS_SESSION]->(s)
        RETURN s
        """
        
        try:
            result = await self._driver.execute_query(cypher, {
                "journey_id": str(journey_id),
                "session_id": session_id
            })
            
            if not result:
                raise ValueError(f"Journey {journey_id} not found")
            
            s_node = result[0]["s"]
            log_session_operation("created", s_node["id"], journey_id)
            
            return Session(
                id=UUID(s_node["id"]),
                journey_id=UUID(s_node["journey_id"]),
                created_at=datetime.fromisoformat(s_node["created_at"].replace('Z', '+00:00')) if isinstance(s_node["created_at"], str) else s_node["created_at"],
                updated_at=datetime.fromisoformat(s_node["updated_at"].replace('Z', '+00:00')) if isinstance(s_node["updated_at"], str) else s_node["updated_at"],
                summary=s_node["summary"],
                messages=[],
                diagnosis=None,
                confidence_score=float(s_node["confidence_score"])
            )
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            raise DatabaseUnavailableError(f"Database error: {e}")

    async def get_session(self, session_id: UUID) -> Optional[Session]:
        """Get session by ID."""
        cypher = "MATCH (s:Session {id: $id}) RETURN s"
        
        try:
            result = await self._driver.execute_query(cypher, {"id": str(session_id)})
            if not result:
                return None
            
            s_node = result[0]["s"]
            return Session(
                id=UUID(s_node["id"]),
                journey_id=UUID(s_node["journey_id"]),
                created_at=datetime.fromisoformat(s_node["created_at"].replace('Z', '+00:00')) if isinstance(s_node["created_at"], str) else s_node["created_at"],
                updated_at=datetime.fromisoformat(s_node["updated_at"].replace('Z', '+00:00')) if isinstance(s_node["updated_at"], str) else s_node["updated_at"],
                summary=s_node["summary"],
                messages=json.loads(s_node.get("messages", "[]")),
                diagnosis=s_node.get("diagnosis"),
                confidence_score=float(s_node.get("confidence_score", 1.0))
            )
        except Exception as e:
            logger.error(f"Error getting session: {e}")
            return None
    
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
        """
        cypher = """
        MATCH (j:Journey {id: $journey_id})
        OPTIONAL MATCH (j)-[:HAS_SESSION]->(s:Session)
        WITH j, s
        ORDER BY s.created_at ASC
        LIMIT $limit
        
        OPTIONAL MATCH (j)-[:HAS_DOCUMENT]->(d:JourneyDocument)
        WITH j, collect(s) as sessions, collect(d) as docs
        RETURN sessions, docs
        """
        
        try:
            result = await self._driver.execute_query(cypher, {
                "journey_id": str(journey_id),
                "limit": limit
            })
            
            if not result:
                return JourneyTimelineResponse(journey_id=journey_id, entries=[], total_entries=0)
            
            row = result[0]
            sessions = row.get("sessions", [])
            docs = row.get("docs", [])
            
            entries: list[TimelineEntry] = []
            
            for s in sessions:
                if s:
                    entries.append(TimelineEntry(
                        entry_type="session",
                        entry_id=UUID(s["id"]),
                        created_at=datetime.fromisoformat(s["created_at"].replace('Z', '+00:00')) if isinstance(s["created_at"], str) else s["created_at"],
                        summary=s["summary"],
                        has_diagnosis=s.get("diagnosis") is not None
                    ))
            
            if include_documents:
                for d in docs:
                    if d:
                        entries.append(TimelineEntry(
                            entry_type="document",
                            entry_id=UUID(d["id"]),
                            created_at=datetime.fromisoformat(d["created_at"].replace('Z', '+00:00')) if isinstance(d["created_at"], str) else d["created_at"],
                            document_type=d["document_type"],
                            title=d["title"]
                        ))
            
            # Sort all entries by created_at
            entries.sort(key=lambda e: e.created_at)
            entries = entries[:limit]
            
            return JourneyTimelineResponse(
                journey_id=journey_id,
                entries=entries,
                total_entries=len(entries)
            )
        except Exception as e:
            logger.error(f"Error getting timeline: {e}")
            return JourneyTimelineResponse(journey_id=journey_id, entries=[], total_entries=0)

    # =========================================================================
    # Query Operations (T026, T027, T028)
    # =========================================================================
    
    async def query_journey_history(
        self, 
        query: JourneyHistoryQuery
    ) -> JourneyHistoryResponse:
        """
        Search journey history. In Neo4j, we use text search on properties.
        """
        cypher = """
        MATCH (j:Journey {id: $journey_id})-[:HAS_SESSION]->(s:Session)
        WHERE ($query IS NULL OR s.summary CONTAINS $query)
        RETURN s
        ORDER BY s.created_at DESC
        LIMIT $limit
        """
        
        try:
            result = await self._driver.execute_query(cypher, {
                "journey_id": str(query.journey_id),
                "query": query.query,
                "limit": query.limit
            })
            
            sessions = [
                SessionSummary(
                    session_id=UUID(row["s"]["id"]),
                    created_at=datetime.fromisoformat(row["s"]["created_at"].replace('Z', '+00:00')) if isinstance(row["s"]["created_at"], str) else row["s"]["created_at"],
                    summary=row["s"]["summary"],
                    has_diagnosis=row["s"].get("diagnosis") is not None,
                    relevance_score=1.0 if query.query else None
                )
                for row in result
            ]
            
            return JourneyHistoryResponse(
                journey_id=query.journey_id,
                sessions=sessions,
                documents=[],
                total_results=len(sessions)
            )
        except Exception as e:
            logger.error(f"Error querying history: {e}")
            return JourneyHistoryResponse(journey_id=query.journey_id, sessions=[], documents=[], total_results=0)

    # =========================================================================
    # Summary Generation (T026)
    # =========================================================================
    
    async def generate_session_summary(self, session_id: UUID) -> Optional[str]:
        """Generate and store session summary."""
        session = await self.get_session(session_id)
        if not session:
            return None
            
        messages = session.messages or []
        summary_parts = []
        for msg in messages[:5]:
            if isinstance(msg, dict) and "content" in msg:
                content = msg["content"][:100]
                summary_parts.append(f"{msg.get('role', 'unknown')}: {content}")
        
        summary = " | ".join(summary_parts) if summary_parts else "Empty session"
        
        cypher = "MATCH (s:Session {id: $id}) SET s.summary = $summary, s.updated_at = datetime()"
        await self._driver.execute_query(cypher, {"id": str(session_id), "summary": summary})
        
        return summary

    # =========================================================================
    # Session ID Management
    # =========================================================================

    DEFAULT_SESSION_FILE = ".claude-session-id"

    async def get_or_create_session_id(self, session_file: Optional[Any] = None) -> str:
        from pathlib import Path
        import uuid
        if session_file is None:
            session_file = Path.home() / self.DEFAULT_SESSION_FILE
        session_file = Path(session_file)
        if session_file.exists():
            sid = session_file.read_text().strip()
            if sid: return sid
        sid = str(uuid.uuid4())
        session_file.write_text(sid)
        return sid

    async def record_session_end(self, session_id: str, started_at: datetime, ended_at: datetime) -> dict:
        cypher = """
        MERGE (sm:SessionMetadata {session_id: $session_id})
        SET sm.started_at = $started_at,
            sm.ended_at = $ended_at
        """
        await self._driver.execute_query(cypher, {
            "session_id": session_id,
            "started_at": started_at.isoformat(),
            "ended_at": ended_at.isoformat()
        })

# =============================================================================
# Singleton Getter
# =============================================================================

_session_manager: Optional[SessionManager] = None

def get_session_manager() -> SessionManager:
    """Get or create singleton SessionManager instance."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
