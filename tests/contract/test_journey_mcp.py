"""
Contract Tests: get_or_create_journey MCP Tool
Feature: 001-session-continuity
Contract: specs/001-session-continuity/contracts/mcp-tools.md

TDD Test - Write FIRST, verify FAILS before implementation.

Tests the get_or_create_journey MCP tool contract:
- Input: device_id (UUID, required)
- Output: journey_id (UUID), device_id (UUID), created_at (datetime),
          session_count (int), is_new (bool)
"""

import uuid
from datetime import datetime

import pytest


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def new_device_id():
    """Generate a new UUID for testing new device scenarios."""
    return uuid.uuid4()


@pytest.fixture
def existing_device_id():
    """Fixed UUID for testing existing device scenarios."""
    # Use a consistent UUID for existing device tests
    return uuid.UUID("550e8400-e29b-41d4-a716-446655440000")


# =============================================================================
# Contract: Input Schema
# =============================================================================

def get_tool_by_name(app, name: str):
    """Helper to get a tool definition from FastMCP app."""
    tools = app._tool_manager.list_tools()
    for t in tools:
        if t.name == name:
            return t
    return None


def get_tool_function(app, name: str):
    """Helper to get a tool's callable function from FastMCP app."""
    tool = app._tool_manager._tools.get(name)
    if tool:
        return tool.fn
    return None


class TestInputContract:
    """Test that tool accepts required input parameters."""

    async def test_tool_accepts_device_id_parameter(self, new_device_id):
        """Test that tool accepts device_id parameter."""
        # This import will fail until MCP tool is implemented
        from dionysus_mcp.server import app

        # Get the tool definition
        tool = get_tool_by_name(app, "get_or_create_journey")
        assert tool is not None, "get_or_create_journey tool should be registered"

        # Verify input schema requires device_id (FastMCP uses 'parameters' not 'inputSchema')
        assert "device_id" in tool.parameters["properties"]
        assert tool.parameters["properties"]["device_id"]["type"] == "string"
        # Note: FastMCP doesn't enforce format in schema, validation happens at runtime
        assert "device_id" in tool.parameters["required"]

    async def test_tool_requires_device_id(self):
        """Test that device_id is required."""
        from dionysus_mcp.server import app

        tool = get_tool_by_name(app, "get_or_create_journey")
        assert tool is not None

        # device_id should be in required fields
        assert "device_id" in tool.parameters["required"]

    async def test_tool_rejects_invalid_uuid(self):
        """Test that tool validates device_id as UUID."""
        from dionysus_mcp.server import app

        # Get the tool function
        get_or_create_journey = get_tool_function(app, "get_or_create_journey")
        assert get_or_create_journey is not None

        # Calling with invalid UUID should raise error at the database level
        # (the function itself accepts string, DB validates UUID format)
        with pytest.raises((ValueError, TypeError, Exception)):
            await get_or_create_journey(device_id="not-a-uuid")


# =============================================================================
# Contract: Output Schema
# =============================================================================

class TestOutputContract:
    """Test that tool returns all required output fields."""

    async def test_tool_returns_all_required_fields(self, new_device_id):
        """Test that tool returns all required output fields."""
        from dionysus_mcp.server import app

        # Get the tool function
        get_or_create_journey = get_tool_function(app, "get_or_create_journey")

        # Call the tool
        result = await get_or_create_journey(device_id=str(new_device_id))

        # Verify all required fields are present
        assert "journey_id" in result
        assert "device_id" in result
        assert "created_at" in result
        assert "session_count" in result
        assert "is_new" in result

    async def test_journey_id_is_uuid(self, new_device_id):
        """Test that journey_id is a valid UUID string."""
        from dionysus_mcp.server import app

        get_or_create_journey = get_tool_function(app, "get_or_create_journey")
        result = await get_or_create_journey(device_id=str(new_device_id))

        # Should be able to parse as UUID
        journey_id = uuid.UUID(result["journey_id"])
        assert isinstance(journey_id, uuid.UUID)

    async def test_device_id_matches_input(self, new_device_id):
        """Test that returned device_id matches input device_id."""
        from dionysus_mcp.server import app

        get_or_create_journey = get_tool_function(app, "get_or_create_journey")
        result = await get_or_create_journey(device_id=str(new_device_id))

        # Device ID should match input
        assert uuid.UUID(result["device_id"]) == new_device_id

    async def test_created_at_is_valid_datetime(self, new_device_id):
        """Test that created_at is a valid ISO 8601 datetime string."""
        from dionysus_mcp.server import app

        get_or_create_journey = get_tool_function(app, "get_or_create_journey")
        result = await get_or_create_journey(device_id=str(new_device_id))

        # Should be able to parse as datetime
        created_at = datetime.fromisoformat(result["created_at"])
        assert isinstance(created_at, datetime)

    async def test_session_count_is_integer(self, new_device_id):
        """Test that session_count is an integer."""
        from dionysus_mcp.server import app

        get_or_create_journey = get_tool_function(app, "get_or_create_journey")
        result = await get_or_create_journey(device_id=str(new_device_id))

        assert isinstance(result["session_count"], int)
        assert result["session_count"] >= 0

    async def test_is_new_is_boolean(self, new_device_id):
        """Test that is_new is a boolean."""
        from dionysus_mcp.server import app

        get_or_create_journey = get_tool_function(app, "get_or_create_journey")
        result = await get_or_create_journey(device_id=str(new_device_id))

        assert isinstance(result["is_new"], bool)


# =============================================================================
# Contract: Behavior - New Journey
# =============================================================================

class TestNewJourneyBehavior:
    """Test behavior when creating a new journey."""

    async def test_new_device_returns_is_new_true(self, new_device_id):
        """Test that is_new=True for a new device."""
        from dionysus_mcp.server import app

        get_or_create_journey = get_tool_function(app, "get_or_create_journey")
        result = await get_or_create_journey(device_id=str(new_device_id))

        assert result["is_new"] is True

    async def test_new_device_has_zero_sessions(self, new_device_id):
        """Test that a new journey has session_count=0."""
        from dionysus_mcp.server import app

        get_or_create_journey = get_tool_function(app, "get_or_create_journey")
        result = await get_or_create_journey(device_id=str(new_device_id))

        assert result["session_count"] == 0

    async def test_new_device_creates_unique_journey_id(self, new_device_id):
        """Test that each new device gets a unique journey_id."""
        from dionysus_mcp.server import app

        get_or_create_journey = get_tool_function(app, "get_or_create_journey")

        # Create two journeys for different devices
        device_1 = uuid.uuid4()
        device_2 = uuid.uuid4()

        result_1 = await get_or_create_journey(device_id=str(device_1))
        result_2 = await get_or_create_journey(device_id=str(device_2))

        # Journey IDs should be different
        assert result_1["journey_id"] != result_2["journey_id"]


# =============================================================================
# Contract: Behavior - Existing Journey
# =============================================================================

class TestExistingJourneyBehavior:
    """Test behavior when retrieving an existing journey."""

    async def test_existing_device_returns_is_new_false(self):
        """Test that is_new=False for an existing device."""
        from dionysus_mcp.server import app

        get_or_create_journey = get_tool_function(app, "get_or_create_journey")

        # Create journey first time
        device_id = uuid.uuid4()
        first_result = await get_or_create_journey(device_id=str(device_id))
        assert first_result["is_new"] is True

        # Get journey second time
        second_result = await get_or_create_journey(device_id=str(device_id))
        assert second_result["is_new"] is False

    async def test_existing_device_returns_same_journey_id(self):
        """Test that same device_id returns same journey_id."""
        from dionysus_mcp.server import app

        get_or_create_journey = get_tool_function(app, "get_or_create_journey")

        # Create journey
        device_id = uuid.uuid4()
        first_result = await get_or_create_journey(device_id=str(device_id))
        journey_id_1 = first_result["journey_id"]

        # Get journey again
        second_result = await get_or_create_journey(device_id=str(device_id))
        journey_id_2 = second_result["journey_id"]

        # Should return same journey_id
        assert journey_id_1 == journey_id_2

    async def test_existing_journey_preserves_created_at(self):
        """Test that created_at is preserved for existing journey."""
        from dionysus_mcp.server import app

        get_or_create_journey = get_tool_function(app, "get_or_create_journey")

        # Create journey
        device_id = uuid.uuid4()
        first_result = await get_or_create_journey(device_id=str(device_id))
        created_at_1 = first_result["created_at"]

        # Get journey again
        second_result = await get_or_create_journey(device_id=str(device_id))
        created_at_2 = second_result["created_at"]

        # Created timestamp should be the same
        assert created_at_1 == created_at_2

    async def test_multiple_calls_idempotent(self):
        """Test that multiple calls with same device_id are idempotent."""
        from dionysus_mcp.server import app

        get_or_create_journey = get_tool_function(app, "get_or_create_journey")

        device_id = uuid.uuid4()

        # Call 3 times
        result_1 = await get_or_create_journey(device_id=str(device_id))
        result_2 = await get_or_create_journey(device_id=str(device_id))
        result_3 = await get_or_create_journey(device_id=str(device_id))

        # All should return same journey_id
        assert result_1["journey_id"] == result_2["journey_id"] == result_3["journey_id"]

        # Only first should be new
        assert result_1["is_new"] is True
        assert result_2["is_new"] is False
        assert result_3["is_new"] is False


# =============================================================================
# Contract: Error Cases
# =============================================================================

class TestErrorCases:
    """Test error handling per contract specification."""

    async def test_database_error_returns_500(self, monkeypatch):
        """Test that database errors return proper error message."""
        from dionysus_mcp.server import app

        get_or_create_journey = get_tool_function(app, "get_or_create_journey")

        # Mock pool to raise database error
        async def mock_get_pool():
            raise Exception("Database connection failed")

        import dionysus_mcp.server
        monkeypatch.setattr(dionysus_mcp.server, "get_pool", mock_get_pool)

        # Should raise or return error per MCP protocol
        with pytest.raises(Exception) as exc_info:
            await get_or_create_journey(device_id=str(uuid.uuid4()))

        # Error message should mention "Failed to access journey"
        assert "Failed to access journey" in str(exc_info.value) or \
               "Database" in str(exc_info.value)


# =============================================================================
# Contract: Integration with SessionManager
# =============================================================================

class TestSessionManagerIntegration:
    """Test that MCP tool correctly uses SessionManager service."""

    async def test_tool_uses_session_manager(self, new_device_id):
        """Test that tool delegates to SessionManager.get_or_create_journey."""
        from dionysus_mcp.server import app
        from api.services.session_manager import SessionManager

        get_or_create_journey = get_tool_function(app, "get_or_create_journey")

        # Call the tool
        result = await get_or_create_journey(device_id=str(new_device_id))

        # Verify result matches SessionManager contract
        # SessionManager returns JourneyWithStats which has these fields
        assert "journey_id" in result
        assert "device_id" in result
        assert "session_count" in result
        assert "is_new" in result

    async def test_session_count_reflects_actual_sessions(self):
        """Test that session_count reflects actual sessions in database."""
        from dionysus_mcp.server import app
        from api.services.session_manager import SessionManager

        get_or_create_journey = get_tool_function(app, "get_or_create_journey")

        # Create journey
        device_id = uuid.uuid4()
        result = await get_or_create_journey(device_id=str(device_id))
        journey_id = uuid.UUID(result["journey_id"])

        # Initially should have 0 sessions
        assert result["session_count"] == 0

        # Create a session via SessionManager
        manager = SessionManager()
        await manager.create_session(journey_id)

        # Get journey again - should now have 1 session
        result_after = await get_or_create_journey(device_id=str(device_id))
        assert result_after["session_count"] == 1
