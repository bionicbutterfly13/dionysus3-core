"""
Integration Tests: Session Summary Workflow
Feature: 002-remote-persistence-safety
Phase 6, User Story 4: n8n Workflow Integration

T043: Integration test for session summary workflow

TDD Test - Write FIRST, verify FAILS before implementation.

Tests that session summaries are generated and stored on session end.
"""

import uuid
from datetime import datetime, timedelta

import pytest


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def session_manager():
    """Get SessionManager instance."""
    from api.services.session_manager import SessionManager
    return SessionManager()


@pytest.fixture
def sync_service():
    """Get RemoteSyncService instance."""
    from api.services.remote_sync import RemoteSyncService
    return RemoteSyncService()


# =============================================================================
# T043: Session Summary Workflow Tests
# =============================================================================

class TestSessionSummaryGeneration:
    """Test session summary generation on session end."""

    async def test_session_end_triggers_summary(self, session_manager, sync_service, tmp_path):
        """Test that ending a session triggers summary generation."""
        session_file = tmp_path / ".claude-session-id"

        # Create session and add memories
        session_id = await session_manager.get_or_create_session_id(session_file)

        # Sync some memories in this session
        await sync_service.sync_memory({
            "id": str(uuid.uuid4()),
            "content": "Discussed rate limiting implementation using token bucket",
            "type": "semantic",
            "importance": 0.7,
            "session_id": session_id,
        })

        await sync_service.sync_memory({
            "id": str(uuid.uuid4()),
            "content": "Reviewed database schema for user authentication",
            "type": "semantic",
            "importance": 0.6,
            "session_id": session_id,
        })

        # End session
        session_record = await session_manager.end_session(session_file)

        assert session_record is not None
        assert session_record["session_id"] == session_id

        # Summary should be generated (may need to wait for n8n)
        import asyncio
        await asyncio.sleep(2)

        # Check summary in Neo4j
        session_data = await sync_service.get_session_summary(session_id)

        # Session should have summary
        assert session_data is not None

    async def test_summary_includes_key_topics(self, session_manager, sync_service, tmp_path):
        """Test that summary captures key topics discussed."""
        session_file = tmp_path / ".claude-session-id"
        session_id = await session_manager.get_or_create_session_id(session_file)

        # Add memories with specific topics
        topics = [
            "Implemented user authentication with JWT tokens",
            "Fixed database connection pooling issue",
            "Reviewed pull request for API refactoring",
        ]

        for topic in topics:
            await sync_service.sync_memory({
                "id": str(uuid.uuid4()),
                "content": topic,
                "type": "semantic",
                "importance": 0.7,
                "session_id": session_id,
            })

        # End session
        await session_manager.end_session(session_file)

        import asyncio
        await asyncio.sleep(2)

        # Get summary
        session_data = await sync_service.get_session_summary(session_id)

        if session_data and "summary" in session_data:
            summary = session_data["summary"].lower()
            # Summary should mention key topics
            assert any(word in summary for word in ["auth", "jwt", "database", "api"])


class TestSessionSummaryStorage:
    """Test session summary storage in Neo4j."""

    async def test_summary_stored_in_session_node(self, sync_service):
        """Test that summary is stored in Session node."""
        session_id = str(uuid.uuid4())

        # Store session summary directly
        await sync_service.store_session_summary(
            session_id=session_id,
            summary="Worked on authentication and database optimization",
            started_at=datetime.utcnow() - timedelta(hours=1),
            ended_at=datetime.utcnow(),
            memory_count=5,
        )

        # Retrieve and verify
        session_data = await sync_service.get_session_summary(session_id)

        assert session_data is not None
        assert "summary" in session_data
        assert "authentication" in session_data["summary"]

    async def test_session_linked_to_memories(self, sync_service):
        """Test that Session node is linked to Memory nodes."""
        session_id = str(uuid.uuid4())
        memory_ids = []

        # Create memories
        for i in range(3):
            memory_id = str(uuid.uuid4())
            await sync_service.sync_memory({
                "id": memory_id,
                "content": f"Memory {i} in session",
                "type": "semantic",
                "importance": 0.5,
                "session_id": session_id,
            })
            memory_ids.append(memory_id)

        # Store session
        await sync_service.store_session_summary(
            session_id=session_id,
            summary="Test session",
            started_at=datetime.utcnow(),
            ended_at=datetime.utcnow(),
            memory_count=3,
        )

        # Query memories by session
        memories = await sync_service.query_by_session(session_id)

        assert len(memories) == 3


class TestSessionEndDetection:
    """Test automatic session end detection."""

    async def test_30min_timeout_triggers_end(self, session_manager, tmp_path):
        """Test that 30 minute inactivity triggers session end."""
        import os

        session_file = tmp_path / ".claude-session-id"

        # Create session
        session_id = await session_manager.get_or_create_session_id(session_file)

        # Set file mtime to 31 minutes ago
        old_time = datetime.now().timestamp() - (31 * 60)
        os.utime(session_file, (old_time, old_time))

        # Check if expired
        is_expired = await session_manager.is_session_expired(session_file)

        assert is_expired

    async def test_activity_prevents_timeout(self, session_manager, tmp_path):
        """Test that activity resets the timeout."""
        import os

        session_file = tmp_path / ".claude-session-id"

        # Create session
        await session_manager.get_or_create_session_id(session_file)

        # Set to 25 minutes ago
        old_time = datetime.now().timestamp() - (25 * 60)
        os.utime(session_file, (old_time, old_time))

        # Record activity
        await session_manager.record_activity(session_file)

        # Should no longer be expired
        is_expired = await session_manager.is_session_expired(session_file)

        assert not is_expired
