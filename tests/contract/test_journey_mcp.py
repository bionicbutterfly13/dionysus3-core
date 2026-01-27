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
from unittest.mock import AsyncMock, patch, MagicMock

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
# Tool Function Import (Direct testing of the tool logic)
# =============================================================================

@pytest.fixture
def get_or_create_journey():
    """Import the tool function directly for testing."""
    from dionysus_mcp.tools.journey import get_or_create_journey_tool
    return get_or_create_journey_tool


class TestInputContract:
    """Tests the input parameter contract."""

    def test_tool_exists(self):
        """Verify the tool is registered with the correct name."""
        from dionysus_mcp.server import app
        # Manual lookup in tool manager
        tools = app._tool_manager.list_tools()
        tool_names = [t.name for t in tools]
        assert "get_or_create_journey" in tool_names

    async def test_tool_accepts_device_id_parameter(self, get_or_create_journey, new_device_id):
        """Test that tool accepts device_id as a string."""
        # This should not raise an error due to missing parameters
        try:
            await get_or_create_journey(device_id=str(new_device_id))
        except Exception as e:
            # We don't care about database errors here, just parameter validation
            if "missing" in str(e).lower():
                pytest.fail(f"Tool rejected device_id parameter: {e}")

    async def test_tool_requires_device_id(self, get_or_create_journey):
        """Test that tool fails if device_id is missing."""
        with pytest.raises(TypeError):
            await get_or_create_journey()

    async def test_tool_rejects_invalid_uuid(self, get_or_create_journey):
        """Test that tool handles malformed UUID strings gracefully."""
        result = await get_or_create_journey(device_id="not-a-uuid")
        assert "error" in result
        assert "invalid" in result["error"].lower()


# =============================================================================
# Contract: Output Schema
# =============================================================================

class TestOutputContract:
    """Tests the output data structure contract."""

    async def test_tool_returns_all_required_fields(self, get_or_create_journey, new_device_id):
        """Test that tool returns all required output fields."""
        result = await get_or_create_journey(device_id=str(new_device_id))
        
        # Verify schema
        assert "journey_id" in result
        assert "device_id" in result
        assert "created_at" in result
        assert "session_count" in result
        assert "is_new" in result

    async def test_journey_id_is_uuid(self, get_or_create_journey, new_device_id):
        """Test that journey_id is a valid UUID string."""
        result = await get_or_create_journey(device_id=str(new_device_id))
        
        # Should be a valid UUID
        uuid.UUID(result["journey_id"])

    async def test_device_id_matches_input(self, get_or_create_journey, new_device_id):
        """Test that returned device_id matches input device_id."""
        result = await get_or_create_journey(device_id=str(new_device_id))
        assert result["device_id"] == str(new_device_id)

    async def test_created_at_is_valid_datetime(self, get_or_create_journey, new_device_id):
        """Test that created_at is a valid ISO 8601 datetime string."""
        result = await get_or_create_journey(device_id=str(new_device_id))
        # Should be parseable as ISO format
        datetime.fromisoformat(result["created_at"])

    async def test_session_count_is_integer(self, get_or_create_journey, new_device_id):
        """Test that session_count is an integer."""
        result = await get_or_create_journey(device_id=str(new_device_id))
        assert isinstance(result["session_count"], int)

    async def test_is_new_is_boolean(self, get_or_create_journey, new_device_id):
        """Test that is_new is a boolean."""
        result = await get_or_create_journey(device_id=str(new_device_id))
        assert isinstance(result["is_new"], bool)


# =============================================================================
# Behavioral Tests: New Journey
# =============================================================================

class TestNewJourneyBehavior:
    """Tests behavior when a new device is registered."""

    async def test_new_device_returns_is_new_true(self, get_or_create_journey, new_device_id):
        """Test that is_new=True for a new device."""
        result = await get_or_create_journey(device_id=str(new_device_id))
        assert result["is_new"] is True

    async def test_new_device_has_zero_sessions(self, get_or_create_journey, new_device_id):
        """Test that a new journey has session_count=0."""
        result = await get_or_create_journey(device_id=str(new_device_id))
        assert result["session_count"] == 0

    async def test_new_device_creates_unique_journey_id(self, get_or_create_journey, new_device_id):
        """Test that each new device gets a unique journey_id."""
        # Create two journeys for different devices
        device_1 = uuid.uuid4()
        device_2 = uuid.uuid4()
        
        result_1 = await get_or_create_journey(device_id=str(device_1))
        result_2 = await get_or_create_journey(device_id=str(device_2))
        
        assert result_1["journey_id"] != result_2["journey_id"]


# =============================================================================
# Behavioral Tests: Existing Journey
# =============================================================================

class TestExistingJourneyBehavior:
    """Tests behavior when an existing device returns."""

    async def test_existing_device_returns_is_new_false(self, get_or_create_journey):
        """Test that is_new=False for an existing device."""
        from api.services.session_manager import get_session_manager
        
        device_id = str(uuid.uuid4())
        
        # 1. Setup mock driver to simulate existing journey
        mock_journey_data = {
            "id": str(uuid.uuid4()),
            "device_id": device_id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "metadata": "{}",
            "_is_new": False
        }
        
        mock_driver = AsyncMock()
        mock_driver.execute_query = AsyncMock(return_value=[{"journey_data": mock_journey_data, "session_count": 5}])
        
        # 2. Patch SessionManager's driver
        manager = get_session_manager()
        original_driver = manager._driver
        manager._driver = mock_driver
        
        try:
            result = await get_or_create_journey(device_id=device_id)
            assert result["is_new"] is False
            assert result["session_count"] == 5
        finally:
            manager._driver = original_driver

    async def test_existing_device_returns_same_journey_id(self, get_or_create_journey):
        """Test that same device_id returns same journey_id."""
        from api.services.session_manager import get_session_manager
        
        device_id = str(uuid.uuid4())
        journey_id = str(uuid.uuid4())
        
        # 1. Setup mock driver
        mock_journey_data = {
            "id": journey_id,
            "device_id": device_id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "metadata": "{}",
            "_is_new": False
        }
        
        mock_driver = AsyncMock()
        mock_driver.execute_query = AsyncMock(return_value=[{"journey_data": mock_journey_data, "session_count": 1}])
        
        manager = get_session_manager()
        original_driver = manager._driver
        manager._driver = mock_driver
        
        try:
            result = await get_or_create_journey(device_id=device_id)
            assert result["journey_id"] == journey_id
        finally:
            manager._driver = original_driver


# =============================================================================
# Error Handling
# =============================================================================

class TestErrorCases:
    """Tests error handling and edge cases."""

    async def test_database_error_raises_exception(self, get_or_create_journey):
        """Test that database errors propagate as exceptions."""
        from api.services.session_manager import DatabaseUnavailableError
        
        # Create a mock session manager that raises on get_or_create_journey
        mock_manager = AsyncMock()
        mock_manager.get_or_create_journey = AsyncMock(side_effect=DatabaseUnavailableError("Database connection failed"))
        
        # Replace the singleton with our mock using patch
        with patch("api.services.session_manager._session_manager", mock_manager):
            with pytest.raises(DatabaseUnavailableError):
                await get_or_create_journey(device_id=str(uuid.uuid4()))


# =============================================================================
# Integration: SessionManager
# =============================================================================

class TestSessionManagerIntegration:
    """Tests integration between MCP tool and SessionManager service."""

    async def test_tool_uses_session_manager(self, get_or_create_journey, new_device_id):
        """Test that tool delegates to SessionManager.get_or_create_journey."""
        from api.services.session_manager import SessionManager
        
        with patch("api.services.session_manager.SessionManager.get_or_create_journey") as mock_method:
            mock_journey = MagicMock()
            mock_journey.id = uuid.uuid4()
            mock_journey.device_id = new_device_id
            mock_journey.created_at = datetime.utcnow()
            mock_journey.session_count = 0
            mock_journey.is_new = True
            
            mock_method.return_value = mock_journey
            
            await get_or_create_journey(device_id=str(new_device_id))
            mock_method.assert_called_once()
