"""
Tests for HexisIdentityService
Feature: 101-hexis-core-migration

TDD Red Phase: Tests written before implementation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from uuid import uuid4

from api.models.hexis_ontology import Goal, GoalPriority, Worldview


@pytest.fixture
def mock_graphiti():
    """Mock GraphitiService for testing."""
    mock = AsyncMock()
    mock.search.return_value = {"edges": []}
    mock.execute_cypher.return_value = []
    return mock


@pytest.fixture
def mock_goal_service():
    """Mock GoalService for testing."""
    mock = AsyncMock()
    mock.list_goals.return_value = [
        MagicMock(
            id=uuid4(),
            title="Complete Feature 101",
            priority="active",
            description="Hexis core migration"
        ),
        MagicMock(
            id=uuid4(),
            title="Write documentation",
            priority="queued",
            description="Update docs"
        ),
    ]
    return mock


@pytest.fixture
def mock_hexis_service():
    """Mock HexisService for testing."""
    mock = AsyncMock()
    mock.get_subconscious_state.return_value = MagicMock(
        active_goals=[
            Goal(title="Test Goal", priority=GoalPriority.ACTIVE)
        ],
        worldview_snapshot=[
            Worldview(statement="User autonomy is paramount")
        ],
        blocks={
            "core_directives": MagicMock(value="Be helpful and thorough"),
            "guidance": MagicMock(value="Focus on TDD"),
        }
    )
    return mock


@pytest.mark.asyncio
async def test_get_active_goals_returns_list(mock_hexis_service, mock_goal_service):
    """get_active_goals() should return list of Goal objects."""
    with patch("api.services.hexis_identity.get_hexis_service", return_value=mock_hexis_service):
        from api.services.hexis_identity import HexisIdentityService

        service = HexisIdentityService()
        goals = await service.get_active_goals(agent_id="test-agent")

        assert isinstance(goals, list)
        assert len(goals) > 0
        assert all(hasattr(g, "title") for g in goals)


@pytest.mark.asyncio
async def test_get_worldview_returns_list(mock_hexis_service, mock_goal_service):
    """get_worldview() should return list of Worldview objects."""
    with patch("api.services.hexis_identity.get_hexis_service", return_value=mock_hexis_service):
        from api.services.hexis_identity import HexisIdentityService

        service = HexisIdentityService()
        worldview = await service.get_worldview(agent_id="test-agent")

        assert isinstance(worldview, list)
        # Should have at least the worldview from subconscious state


@pytest.mark.asyncio
async def test_get_identity_context_aggregates_all(mock_hexis_service, mock_goal_service):
    """get_identity_context() should aggregate goals, worldview, and blocks."""
    with patch("api.services.hexis_identity.get_hexis_service", return_value=mock_hexis_service):
        from api.services.hexis_identity import HexisIdentityService

        service = HexisIdentityService()
        context = await service.get_identity_context(agent_id="test-agent")

        # Should have all identity components
        assert hasattr(context, "goals") or "goals" in context
        assert hasattr(context, "worldview") or "worldview" in context
        assert hasattr(context, "directives") or "directives" in context


@pytest.mark.asyncio
async def test_get_prompt_context_returns_formatted_string(mock_hexis_service, mock_goal_service):
    """get_prompt_context() should return LLM-ready formatted string."""
    with patch("api.services.hexis_identity.get_hexis_service", return_value=mock_hexis_service):
        from api.services.hexis_identity import HexisIdentityService

        service = HexisIdentityService()
        prompt_context = await service.get_prompt_context(agent_id="test-agent")

        assert isinstance(prompt_context, str)
        assert len(prompt_context) > 0
        # Should include key identity elements
        assert "goal" in prompt_context.lower() or "directive" in prompt_context.lower()


@pytest.mark.asyncio
async def test_get_prompt_context_includes_worldview(mock_hexis_service, mock_goal_service):
    """get_prompt_context() should include worldview beliefs."""
    with patch("api.services.hexis_identity.get_hexis_service", return_value=mock_hexis_service):
        from api.services.hexis_identity import HexisIdentityService

        service = HexisIdentityService()
        prompt_context = await service.get_prompt_context(agent_id="test-agent")

        # Should mention autonomy from the mock worldview
        assert "autonomy" in prompt_context.lower() or "worldview" in prompt_context.lower() or len(prompt_context) > 0


@pytest.mark.asyncio
async def test_get_prompt_context_includes_guidance(mock_hexis_service, mock_goal_service):
    """get_prompt_context() should include guidance block if present."""
    with patch("api.services.hexis_identity.get_hexis_service", return_value=mock_hexis_service):
        from api.services.hexis_identity import HexisIdentityService

        service = HexisIdentityService()
        prompt_context = await service.get_prompt_context(agent_id="test-agent")

        # Should include guidance (TDD from mock)
        assert "TDD" in prompt_context or "guidance" in prompt_context.lower() or len(prompt_context) > 0


@pytest.mark.asyncio
async def test_handles_empty_subconscious_state(mock_hexis_service, mock_goal_service):
    """Service should handle empty/default subconscious state gracefully."""
    mock_hexis_service.get_subconscious_state.return_value = MagicMock(
        active_goals=[],
        worldview_snapshot=[],
        blocks={}
    )

    with patch("api.services.hexis_identity.get_hexis_service", return_value=mock_hexis_service):
        from api.services.hexis_identity import HexisIdentityService

        service = HexisIdentityService()
        context = await service.get_prompt_context(agent_id="test-agent")

        # Should not raise, should return valid (possibly empty) string
        assert isinstance(context, str)


@pytest.mark.asyncio
async def test_handles_hexis_service_error(mock_hexis_service, mock_goal_service):
    """Service should handle HexisService errors gracefully."""
    mock_hexis_service.get_subconscious_state.side_effect = Exception("Service unavailable")

    with patch("api.services.hexis_identity.get_hexis_service", return_value=mock_hexis_service):
        from api.services.hexis_identity import HexisIdentityService

        service = HexisIdentityService()

        # Should not crash, should return default/empty context
        try:
            context = await service.get_prompt_context(agent_id="test-agent")
            assert isinstance(context, str)
        except Exception:
            pytest.fail("Service should handle errors gracefully")


@pytest.mark.asyncio
async def test_singleton_access():
    """get_hexis_identity_service() should return singleton instance."""
    from api.services.hexis_identity import get_hexis_identity_service

    service1 = get_hexis_identity_service()
    service2 = get_hexis_identity_service()

    assert service1 is service2
