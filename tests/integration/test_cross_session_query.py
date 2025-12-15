"""
Integration Tests: Cross-Session Query
Feature: 002-remote-persistence-safety
Phase 4, User Story 2: Cross-Session Context Preservation

T030: Integration test for cross-session query

TDD Test - Write FIRST, verify FAILS before implementation.

Tests querying memories from previous sessions by session_id and date range.
"""

import uuid
from datetime import datetime, timedelta

import pytest


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def sync_service():
    """Get RemoteSyncService instance."""
    from api.services.remote_sync import RemoteSyncService
    return RemoteSyncService()


@pytest.fixture
async def session_with_memories(sync_service):
    """Create a session with test memories, return session_id and memory_ids."""
    session_id = str(uuid.uuid4())
    memory_ids = []

    # Create 3 memories in this session
    topics = ["API rate limiting", "database optimization", "error handling"]
    for i, topic in enumerate(topics):
        memory_id = str(uuid.uuid4())
        await sync_service.sync_memory({
            "id": memory_id,
            "content": f"Discussion about {topic} patterns and best practices",
            "type": "semantic",
            "importance": 0.7,
            "session_id": session_id,
            "created_at": datetime.utcnow().isoformat()
        })
        memory_ids.append(memory_id)

    return {"session_id": session_id, "memory_ids": memory_ids, "topics": topics}


# =============================================================================
# T030: Cross-Session Query Tests
# =============================================================================

class TestCrossSessionQuery:
    """Test querying memories across sessions."""

    async def test_query_memories_by_session_id(self, sync_service, session_with_memories):
        """Test retrieving all memories from a specific session."""
        session_id = session_with_memories["session_id"]
        expected_count = len(session_with_memories["memory_ids"])

        # Query by session_id
        results = await sync_service.query_by_session(session_id=session_id)

        assert len(results) == expected_count
        for memory in results:
            assert memory["session_id"] == session_id

    async def test_query_memories_from_previous_session(self, sync_service):
        """Test querying memories from a previous (ended) session."""
        # Create Session A with memories
        session_a_id = str(uuid.uuid4())
        await sync_service.sync_memory({
            "id": str(uuid.uuid4()),
            "content": "Session A: Important architectural decision",
            "type": "semantic",
            "importance": 0.8,
            "session_id": session_a_id
        })

        # Create Session B (current)
        session_b_id = str(uuid.uuid4())
        await sync_service.sync_memory({
            "id": str(uuid.uuid4()),
            "content": "Session B: Current work",
            "type": "semantic",
            "importance": 0.5,
            "session_id": session_b_id
        })

        # From Session B, query Session A memories
        results = await sync_service.query_by_session(session_id=session_a_id)

        assert len(results) >= 1
        assert any("architectural decision" in m["content"] for m in results)

    async def test_query_with_keyword_across_sessions(self, sync_service):
        """Test keyword search returns memories with session attribution."""
        # Create memories in different sessions
        session_1 = str(uuid.uuid4())
        session_2 = str(uuid.uuid4())

        await sync_service.sync_memory({
            "id": str(uuid.uuid4()),
            "content": "Rate limiting implementation using token bucket algorithm",
            "type": "semantic",
            "importance": 0.7,
            "session_id": session_1
        })

        await sync_service.sync_memory({
            "id": str(uuid.uuid4()),
            "content": "Rate limiting discussion with sliding window approach",
            "type": "semantic",
            "importance": 0.6,
            "session_id": session_2
        })

        # Search for "rate limiting" across all sessions
        results = await sync_service.search_memories(
            query="rate limiting",
            include_session_attribution=True
        )

        assert len(results) >= 2
        # Results should include session_id for attribution
        for memory in results:
            assert "session_id" in memory

        # Should have results from both sessions
        session_ids = {m["session_id"] for m in results}
        assert session_1 in session_ids or session_2 in session_ids


class TestDateRangeQuery:
    """Test querying memories by date range."""

    async def test_query_memories_by_date_range(self, sync_service):
        """Test filtering memories by date range."""
        session_id = str(uuid.uuid4())
        now = datetime.utcnow()

        # Create memory "yesterday"
        yesterday = now - timedelta(days=1)
        await sync_service.sync_memory({
            "id": str(uuid.uuid4()),
            "content": "Yesterday's discussion",
            "type": "semantic",
            "importance": 0.5,
            "session_id": session_id,
            "created_at": yesterday.isoformat()
        })

        # Create memory "today"
        await sync_service.sync_memory({
            "id": str(uuid.uuid4()),
            "content": "Today's discussion",
            "type": "semantic",
            "importance": 0.5,
            "session_id": session_id,
            "created_at": now.isoformat()
        })

        # Query for today only
        results = await sync_service.query_by_date_range(
            from_date=now.replace(hour=0, minute=0, second=0),
            to_date=now
        )

        # Should only get today's memory
        assert len(results) >= 1
        assert any("Today's" in m["content"] for m in results)

    async def test_query_last_7_days(self, sync_service):
        """Test querying memories from the last 7 days."""
        session_id = str(uuid.uuid4())
        now = datetime.utcnow()

        # Create memory from 3 days ago
        three_days_ago = now - timedelta(days=3)
        await sync_service.sync_memory({
            "id": str(uuid.uuid4()),
            "content": "Memory from 3 days ago",
            "type": "semantic",
            "importance": 0.5,
            "session_id": session_id,
            "created_at": three_days_ago.isoformat()
        })

        # Create memory from 10 days ago (should not appear)
        ten_days_ago = now - timedelta(days=10)
        await sync_service.sync_memory({
            "id": str(uuid.uuid4()),
            "content": "Memory from 10 days ago",
            "type": "semantic",
            "importance": 0.5,
            "session_id": session_id,
            "created_at": ten_days_ago.isoformat()
        })

        # Query last 7 days
        results = await sync_service.query_by_date_range(
            from_date=now - timedelta(days=7),
            to_date=now
        )

        contents = [m["content"] for m in results]
        assert any("3 days ago" in c for c in contents)
        assert not any("10 days ago" in c for c in contents)


class TestSessionAttribution:
    """Test session attribution in query results."""

    async def test_results_include_session_metadata(self, sync_service):
        """Test that query results include session start/end times."""
        from api.services.session_manager import SessionManager

        session_manager = SessionManager()

        # Create a complete session with start and end
        session_id = str(uuid.uuid4())
        started_at = datetime.utcnow()

        await sync_service.sync_memory({
            "id": str(uuid.uuid4()),
            "content": "Memory in tracked session",
            "type": "semantic",
            "importance": 0.5,
            "session_id": session_id
        })

        # Record session end
        ended_at = datetime.utcnow()
        await session_manager.record_session_end(
            session_id=session_id,
            started_at=started_at,
            ended_at=ended_at
        )

        # Query with session attribution
        results = await sync_service.query_by_session(
            session_id=session_id,
            include_session_metadata=True
        )

        assert len(results) >= 1
        # First result should have session metadata
        assert "session_metadata" in results[0]
        assert results[0]["session_metadata"]["started_at"] is not None

    async def test_what_did_we_discuss_query(self, sync_service):
        """Test natural language style query: 'What did we discuss in previous session?'"""
        # Create previous session with specific content
        prev_session_id = str(uuid.uuid4())
        await sync_service.sync_memory({
            "id": str(uuid.uuid4()),
            "content": "We discussed implementing a retry mechanism with exponential backoff",
            "type": "semantic",
            "importance": 0.8,
            "session_id": prev_session_id
        })

        # Query previous session
        results = await sync_service.query_by_session(
            session_id=prev_session_id,
            query="retry mechanism"
        )

        assert len(results) >= 1
        assert any("exponential backoff" in m["content"] for m in results)
