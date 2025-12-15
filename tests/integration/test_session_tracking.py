"""
Integration Tests: Session Boundary Tracking
Feature: 002-remote-persistence-safety
Phase 4, User Story 2: Cross-Session Context Preservation

TDD Test - Write FIRST, verify FAILS before implementation.

Tests session_id generation, persistence, and boundary tracking.
"""

import os
import uuid
from pathlib import Path
from datetime import datetime, timedelta

import pytest


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def temp_session_file(tmp_path):
    """Create a temporary directory for session file testing."""
    return tmp_path / ".claude-session-id"


@pytest.fixture
def session_manager():
    """Get SessionManager instance for testing."""
    from api.services.session_manager import SessionManager
    return SessionManager()


# =============================================================================
# T029: Session Boundary Tracking Tests
# =============================================================================

class TestSessionBoundaryTracking:
    """Test session_id generation and boundary tracking."""

    async def test_new_session_generates_uuid(self, session_manager, temp_session_file):
        """Test that starting a new session generates a valid UUID."""
        # Override session file location for testing
        session_id = await session_manager.get_or_create_session_id(
            session_file=temp_session_file
        )

        # Should be a valid UUID
        parsed = uuid.UUID(session_id)
        assert isinstance(parsed, uuid.UUID)

        # File should be created
        assert temp_session_file.exists()
        assert temp_session_file.read_text().strip() == session_id

    async def test_existing_session_returns_same_id(self, session_manager, temp_session_file):
        """Test that existing session file returns same session_id."""
        # Create session first time
        session_id_1 = await session_manager.get_or_create_session_id(
            session_file=temp_session_file
        )

        # Get session second time
        session_id_2 = await session_manager.get_or_create_session_id(
            session_file=temp_session_file
        )

        # Should return same ID
        assert session_id_1 == session_id_2

    async def test_end_session_removes_file(self, session_manager, temp_session_file):
        """Test that ending session removes the session file."""
        # Create session
        await session_manager.get_or_create_session_id(
            session_file=temp_session_file
        )
        assert temp_session_file.exists()

        # End session
        await session_manager.end_session(session_file=temp_session_file)

        # File should be removed
        assert not temp_session_file.exists()

    async def test_end_session_creates_session_record(self, session_manager, temp_session_file):
        """Test that ending session stores session metadata in database."""
        # Create session
        session_id = await session_manager.get_or_create_session_id(
            session_file=temp_session_file
        )

        # End session
        session_record = await session_manager.end_session(
            session_file=temp_session_file
        )

        # Should return session record with metadata
        assert session_record is not None
        assert session_record["session_id"] == session_id
        assert "started_at" in session_record
        assert "ended_at" in session_record
        assert session_record["ended_at"] is not None

    async def test_new_session_after_end_generates_new_id(self, session_manager, temp_session_file):
        """Test that new session after end gets a different ID."""
        # Create first session
        session_id_1 = await session_manager.get_or_create_session_id(
            session_file=temp_session_file
        )

        # End session
        await session_manager.end_session(session_file=temp_session_file)

        # Create new session
        session_id_2 = await session_manager.get_or_create_session_id(
            session_file=temp_session_file
        )

        # Should be different
        assert session_id_1 != session_id_2


class TestSessionTimeout:
    """Test session timeout detection (30 minute inactivity)."""

    async def test_session_expires_after_30_minutes(self, session_manager, temp_session_file):
        """Test that session is considered expired after 30 min inactivity."""
        # Create session
        session_id = await session_manager.get_or_create_session_id(
            session_file=temp_session_file
        )

        # Check if expired (should not be)
        is_expired = await session_manager.is_session_expired(
            session_file=temp_session_file,
            timeout_minutes=30
        )
        assert not is_expired

        # Manually set file mtime to 31 minutes ago
        old_time = datetime.now().timestamp() - (31 * 60)
        os.utime(temp_session_file, (old_time, old_time))

        # Now should be expired
        is_expired = await session_manager.is_session_expired(
            session_file=temp_session_file,
            timeout_minutes=30
        )
        assert is_expired

    async def test_activity_resets_timeout(self, session_manager, temp_session_file):
        """Test that activity updates file mtime to reset timeout."""
        # Create session
        await session_manager.get_or_create_session_id(
            session_file=temp_session_file
        )

        # Set file to old time
        old_time = datetime.now().timestamp() - (31 * 60)
        os.utime(temp_session_file, (old_time, old_time))

        # Record activity (should update mtime)
        await session_manager.record_activity(session_file=temp_session_file)

        # Should no longer be expired
        is_expired = await session_manager.is_session_expired(
            session_file=temp_session_file,
            timeout_minutes=30
        )
        assert not is_expired


class TestMemorySessionTagging:
    """Test that memories are tagged with session_id."""

    async def test_memory_tagged_with_session_id(self, session_manager, temp_session_file):
        """Test that new memories include session_id."""
        from api.services.remote_sync import RemoteSyncService

        # Create session
        session_id = await session_manager.get_or_create_session_id(
            session_file=temp_session_file
        )

        # Create memory with session context
        sync_service = RemoteSyncService()
        memory_data = {
            "content": "Test memory for session tagging",
            "type": "semantic",
            "importance": 0.5
        }

        # Tag with session
        tagged_memory = await sync_service.tag_with_session(
            memory_data,
            session_id=session_id
        )

        assert tagged_memory["session_id"] == session_id

    async def test_synced_memory_has_session_in_neo4j(self, session_manager, temp_session_file):
        """Test that synced memory in Neo4j has session_id property."""
        from api.services.remote_sync import RemoteSyncService

        # Create session
        session_id = await session_manager.get_or_create_session_id(
            session_file=temp_session_file
        )

        # Create and sync memory
        sync_service = RemoteSyncService()
        memory_id = str(uuid.uuid4())

        result = await sync_service.sync_memory({
            "id": memory_id,
            "content": "Test memory for Neo4j session check",
            "type": "semantic",
            "importance": 0.5,
            "session_id": session_id
        })

        # Verify in Neo4j
        assert result["success"]

        # Query Neo4j to verify session_id
        neo4j_memory = await sync_service.get_memory_from_neo4j(memory_id)
        assert neo4j_memory is not None
        assert neo4j_memory["session_id"] == session_id
