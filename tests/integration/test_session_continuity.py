"""
Integration Tests: Session Continuity (User Story 1)
Feature: 001-session-continuity
Tasks: T012, T013, T014

Tests the core journey tracking functionality:
1. T012: New device creates journey on first session
2. T013: Existing device links session to existing journey
3. T014: Journey timeline returns sessions in chronological order

Database: PostgreSQL (via DATABASE_URL environment variable)
"""

import os
import uuid
from datetime import datetime, timedelta

import pytest
import asyncpg
from dotenv import load_dotenv

from api.services.session_manager import SessionManager
from api.models.journey import JourneyWithStats, Session, SessionSummary

load_dotenv()


# Database configuration
# Requires DATABASE_URL to be set explicitly (typically via test command)
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL environment variable required for tests. "
        "Use: DATABASE_URL=postgresql://dionysus:dionysus2024@localhost:5434/dionysus_test pytest"
    )


@pytest.fixture
async def db_pool():
    """Create database connection pool for tests."""
    pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)
    yield pool
    await pool.close()


@pytest.fixture
async def session_manager(db_pool):
    """Create SessionManager instance with test database pool."""
    return SessionManager(pool=db_pool)


@pytest.fixture
async def cleanup_test_data(db_pool):
    """Cleanup test data before and after each test."""
    # Cleanup before test
    async with db_pool.acquire() as conn:
        # Store existing device IDs to avoid deleting production data
        test_device_prefix = "00000000-0000-0000-0000"
        await conn.execute(
            """
            DELETE FROM sessions
            WHERE journey_id IN (
                SELECT id FROM journeys
                WHERE CAST(device_id AS TEXT) LIKE $1
            )
            """,
            f"{test_device_prefix}%"
        )
        await conn.execute(
            "DELETE FROM journeys WHERE CAST(device_id AS TEXT) LIKE $1",
            f"{test_device_prefix}%"
        )

    yield

    # Cleanup after test
    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            DELETE FROM sessions
            WHERE journey_id IN (
                SELECT id FROM journeys
                WHERE CAST(device_id AS TEXT) LIKE $1
            )
            """,
            f"{test_device_prefix}%"
        )
        await conn.execute(
            "DELETE FROM journeys WHERE CAST(device_id AS TEXT) LIKE $1",
            f"{test_device_prefix}%"
        )


@pytest.fixture
def test_device_id():
    """Generate a test device ID with recognizable prefix."""
    # Using a specific prefix for easy cleanup
    return uuid.UUID("00000000-0000-0000-0000-" + uuid.uuid4().hex[:12])


class TestSessionContinuity:
    """
    Test suite for User Story 1: Session Continuity

    Verifies that the system correctly tracks journeys across multiple sessions,
    linking conversations to a persistent device identifier.
    """

    @pytest.mark.asyncio
    async def test_new_device_creates_journey_on_first_session(
        self,
        session_manager: SessionManager,
        test_device_id: uuid.UUID,
        cleanup_test_data
    ):
        """
        T012: New device creates journey on first session

        When get_or_create_journey is called with a new device_id,
        it should create a new journey and return is_new=True.
        """
        # Act: Call get_or_create_journey with new device_id
        journey = await session_manager.get_or_create_journey(test_device_id)

        # Assert: Journey was created
        assert isinstance(journey, JourneyWithStats)
        assert journey.is_new is True, "Expected is_new=True for newly created journey"
        assert journey.device_id == test_device_id
        assert journey.session_count == 0, "New journey should have 0 sessions"

        # Assert: Journey has required fields
        assert journey.id is not None
        assert journey.created_at is not None
        assert journey.updated_at is not None
        assert isinstance(journey.metadata, dict)

        # Verify journey was persisted to database
        journey_check = await session_manager.get_journey(journey.id)
        assert journey_check is not None
        assert journey_check.device_id == test_device_id

    @pytest.mark.asyncio
    async def test_existing_device_links_session_to_existing_journey(
        self,
        session_manager: SessionManager,
        test_device_id: uuid.UUID,
        cleanup_test_data
    ):
        """
        T013: Existing device links session to existing journey

        When get_or_create_journey is called with the same device_id twice,
        it should return the same journey with is_new=False on the second call.
        """
        # Arrange: Create initial journey
        journey1 = await session_manager.get_or_create_journey(test_device_id)
        assert journey1.is_new is True
        first_journey_id = journey1.id

        # Create a session to increment session_count
        session1 = await session_manager.create_session(journey1.id)
        assert session1.journey_id == first_journey_id

        # Act: Call get_or_create_journey again with same device_id
        journey2 = await session_manager.get_or_create_journey(test_device_id)

        # Assert: Same journey returned
        assert journey2.is_new is False, "Expected is_new=False for existing journey"
        assert journey2.id == first_journey_id, "Should return same journey ID"
        assert journey2.device_id == test_device_id
        assert journey2.session_count == 1, "Should reflect the created session"

        # Create another session
        session2 = await session_manager.create_session(journey2.id)
        assert session2.journey_id == first_journey_id

        # Act: Call get_or_create_journey a third time
        journey3 = await session_manager.get_or_create_journey(test_device_id)

        # Assert: Still same journey
        assert journey3.is_new is False
        assert journey3.id == first_journey_id
        assert journey3.session_count == 2, "Should reflect both sessions"

    @pytest.mark.asyncio
    async def test_journey_timeline_returns_sessions_in_chronological_order(
        self,
        session_manager: SessionManager,
        test_device_id: uuid.UUID,
        db_pool: asyncpg.Pool,
        cleanup_test_data
    ):
        """
        T014: Journey timeline returns sessions in chronological order

        When get_journey_timeline is called, it should return all sessions
        for the journey ordered by created_at (oldest first).
        """
        # Arrange: Create journey
        journey = await session_manager.get_or_create_journey(test_device_id)

        # Create multiple sessions with different timestamps
        session_ids = []
        session_timestamps = []

        # Create 5 sessions
        for i in range(5):
            session = await session_manager.create_session(journey.id)
            session_ids.append(session.id)

            # Manually set different created_at times to ensure chronological order
            # (going backwards in time for each session to test sorting)
            timestamp = datetime.utcnow() - timedelta(hours=5-i)
            async with db_pool.acquire() as conn:
                await conn.execute(
                    "UPDATE sessions SET created_at = $1 WHERE id = $2",
                    timestamp,
                    session.id
                )
            session_timestamps.append(timestamp)

        # Act: Get journey timeline
        timeline = await session_manager.get_journey_timeline(journey.id, limit=50)

        # Assert: Timeline contains all sessions
        assert len(timeline) == 5, f"Expected 5 sessions, got {len(timeline)}"
        assert isinstance(timeline, list)
        assert all(isinstance(item, SessionSummary) for item in timeline)

        # Assert: Sessions are in chronological order (oldest first)
        for i in range(len(timeline)):
            assert timeline[i].session_id == session_ids[i], \
                f"Session {i} out of order: expected {session_ids[i]}, got {timeline[i].session_id}"

            # Verify timestamps are in ascending order
            if i > 0:
                assert timeline[i].created_at > timeline[i-1].created_at, \
                    f"Session {i} timestamp should be after session {i-1}"

        # Assert: Each session summary has required fields
        for session_summary in timeline:
            assert session_summary.session_id is not None
            assert session_summary.created_at is not None
            assert session_summary.has_diagnosis is False  # No diagnosis set
            assert session_summary.summary is None  # No summary generated

    @pytest.mark.asyncio
    async def test_journey_timeline_respects_limit(
        self,
        session_manager: SessionManager,
        test_device_id: uuid.UUID,
        cleanup_test_data
    ):
        """
        Test that get_journey_timeline respects the limit parameter.

        This is an additional test to verify the limit functionality works correctly.
        """
        # Arrange: Create journey with 10 sessions
        journey = await session_manager.get_or_create_journey(test_device_id)

        for _ in range(10):
            await session_manager.create_session(journey.id)

        # Act: Get timeline with limit=5
        timeline = await session_manager.get_journey_timeline(journey.id, limit=5)

        # Assert: Only 5 sessions returned
        assert len(timeline) == 5, f"Expected 5 sessions with limit=5, got {len(timeline)}"

        # Assert: Still in chronological order
        for i in range(1, len(timeline)):
            assert timeline[i].created_at > timeline[i-1].created_at

    @pytest.mark.asyncio
    async def test_journey_timeline_empty_for_new_journey(
        self,
        session_manager: SessionManager,
        test_device_id: uuid.UUID,
        cleanup_test_data
    ):
        """
        Test that get_journey_timeline returns empty list for journey with no sessions.
        """
        # Arrange: Create journey without sessions
        journey = await session_manager.get_or_create_journey(test_device_id)

        # Act: Get timeline
        timeline = await session_manager.get_journey_timeline(journey.id)

        # Assert: Empty list returned
        assert timeline == [], "Expected empty list for journey with no sessions"
        assert isinstance(timeline, list)
