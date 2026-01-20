"""
Contract Test Fixtures
Feature: 001-session-continuity

Provides mock data for contract tests that validate MCP tool interfaces.
These fixtures override the global empty mocks to return proper test data.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest


# =============================================================================
# Journey Mock Data Factory (Module-level singleton)
# =============================================================================

class JourneyMockFactory:
    """Factory for creating journey mock responses."""

    _instance = None

    @classmethod
    def get_instance(cls):
        """Get or create singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls):
        """Reset singleton for test isolation."""
        if cls._instance:
            cls._instance.clear()
        cls._instance = None

    def __init__(self):
        self._journeys = {}  # device_id -> journey data
        self._sessions = {}  # journey_id -> session count

    def get_or_create(self, device_id: str) -> tuple[dict, bool]:
        """
        Mock the MERGE behavior of get_or_create_journey.
        Returns (journey_node_data, is_new).
        """
        if device_id in self._journeys:
            journey = self._journeys[device_id].copy()
            journey["_is_new"] = False
            return journey, False

        # Create new journey
        journey = {
            "id": str(uuid.uuid4()),
            "device_id": device_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "metadata": "{}",
            "_is_new": True,
        }
        self._journeys[device_id] = journey.copy()
        return journey, True

    def get_session_count(self, journey_id: str) -> int:
        """Get session count for a journey."""
        return self._sessions.get(journey_id, 0)

    def add_session(self, journey_id: str):
        """Add a session to a journey."""
        self._sessions[journey_id] = self._sessions.get(journey_id, 0) + 1

    def clear(self):
        """Reset factory state between tests."""
        self._journeys = {}
        self._sessions = {}


# Module-level factory instance (shared across all test functions in a test)
_factory = None


def get_factory():
    """Get the current test's factory instance."""
    global _factory
    if _factory is None:
        _factory = JourneyMockFactory()
    return _factory


def reset_factory():
    """Reset the factory between tests."""
    global _factory
    if _factory:
        _factory.clear()
    _factory = JourneyMockFactory()


# =============================================================================
# Session Manager Mock
# =============================================================================

@pytest.fixture(autouse=True)
def journey_factory():
    """Provide a journey mock factory for the test."""
    reset_factory()
    yield get_factory()
    reset_factory()


@pytest.fixture(autouse=True)
def mock_session_manager_driver():
    """
    Override the global empty mock with journey-aware mock.
    This fixture provides proper MERGE behavior for journey tests.
    """
    async def mock_execute_query(cypher: str, params: dict = None):
        # Always get current factory (not closure capture)
        factory = get_factory()
        params = params or {}

        # Handle MERGE Journey query
        if "MERGE (j:Journey" in cypher and "device_id" in params:
            device_id = params["device_id"]
            journey, is_new = factory.get_or_create(device_id)

            # Get session count
            session_count = factory.get_session_count(journey["id"])

            return [{
                "j": journey,
                "session_count": session_count
            }]

        # Handle CREATE Session query
        if "CREATE (s:Session" in cypher and "journey_id" in params:
            journey_id = params["journey_id"]
            session_id = params.get("session_id", str(uuid.uuid4()))

            # Track session count using string journey_id
            factory.add_session(str(journey_id))

            session = {
                "id": session_id,
                "journey_id": str(journey_id),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "summary": "New session",
                "messages": "[]",
                "confidence_score": 1.0,
            }
            return [{"s": session}]

        # Handle GET Journey query
        if "MATCH (j:Journey {id:" in cypher and "id" in params:
            journey_id = str(params["id"])
            # Find journey by ID
            for journey in factory._journeys.values():
                if journey["id"] == journey_id:
                    return [{"j": journey}]
            return []

        # Handle GET Session query
        if "MATCH (s:Session {id:" in cypher:
            return []  # No sessions in mock by default

        # Handle timeline query
        if "HAS_SESSION" in cypher and "HAS_DOCUMENT" in cypher:
            return [{"sessions": [], "docs": []}]

        # Handle history query
        if "HAS_SESSION" in cypher and "summary CONTAINS" in cypher:
            return []

        # Default: return empty
        return []

    mock_driver = AsyncMock()
    mock_driver.execute_query = AsyncMock(side_effect=mock_execute_query)

    # Patch at multiple levels to ensure coverage
    with patch('api.services.remote_sync.get_neo4j_driver', return_value=mock_driver), \
         patch('api.services.webhook_neo4j_driver.get_neo4j_driver', return_value=mock_driver), \
         patch('api.services.session_manager.get_neo4j_driver', return_value=mock_driver):
        yield mock_driver


@pytest.fixture(autouse=True)
def reset_session_manager_singleton():
    """Reset SessionManager singleton state between tests."""
    import api.services.session_manager as sm_module
    # Clear any module-level singletons if they exist
    yield


# =============================================================================
# MCP Server Fixtures
# =============================================================================

@pytest.fixture
def mcp_app():
    """Provide the MCP server app for testing."""
    from dionysus_mcp.server import app
    return app
